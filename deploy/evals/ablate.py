#!/usr/bin/env python3
"""The ablation harness: retrieval only, no model in the loop, against the frozen golden set.

    python deploy/evals/ablate.py --project PROJECT              # the 43 anchored rows, four arms (~3 min)
    python deploy/evals/ablate.py --project PROJECT --limit 5    # a wiring check, under a minute
    python deploy/evals/ablate.py --project PROJECT --arms all   # the four and the managed arm (P9.6: needs the mirror)
    make ablate PROJECT=...                                      # the same, from deploy/ (ABLATE_ARGS="--arms all")
    python deploy/evals/ablate.py --project PROJECT --arms dense20 --rewrite --paraphrases deploy/evals/paraphrases.jsonl
                                     # workshop lesson 2.5: the lane's arm and the same with the question rewritten first,
                                     # on the golden rows and their paraphrases (make ablate ABLATE_ARGS="--rewrite ...")

One knob per arm, everything else held (lesson 4.8, Part 5):

    dense 5, no reranker          Firestore find_nearest with the tenant pre-filter, top 5 as returned
    dense 20 -> rerank 5          the lane's own path on this profile (retriever.py -> Rank API)
    dense 50 -> rerank 5          the same reranker over a deeper candidate list
    hybrid 20 -> rerank 5         4.5's RRF over the dense ids and a BM25 leg (alpha 0.7) - which the
                                  Firestore rung does NOT wire: hybrid.py rides Vector Search only
    rag_engine 20 -> rerank 5     P9.4's backend from outside it (13 September 2026): 4.3's corpus - the
                                  mirror's, one RagFile per version named by its doc_key - queried by text,
                                  each context's doc_key resolved to its source through the kit's own rows.
                                  Behind --arms all (or --arms rag_engine): a lane without the mirror has
                                  no corpus, and an arm that cannot run is a finding, not the harness's exit
    vertex_search 20 -> rerank 5  R4's backend from outside it: 4.4's data store ranks the tenant's documents and
                                  the kit's own rows of those versions are the passages (22 October 2026: a
                                  standard-edition store refuses segments and its snippets stop short); a store
                                  that ranks nothing is the kit's nearest rows, counted on a line under the arm
    rewrite -> dense 20 -> rerank 5   workshop lesson 2.5's stage from outside rag-api, behind --rewrite (never an
                                  --arms key): shared/query_rewrite.py's rewrite is what the Firestore rung
                                  searches and the question as asked is what the reranker orders; a rewrite the
                                  literal guard refuses, or one that failed, searches the question, so the row
                                  differs from the lane's only where a rewrite was accepted. The line under it
                                  counts the outcomes and prices the calls

Scored on the golden rows that carry `must_retrieve` anchors, by recall and MRR against source
file + text (the way run_eval.py matches: the worker's chunk ids name neither the clause nor
the document). Next to every reranked number is the recall at the candidate depth, because a
reranker can only reorder what the retriever returned - if recall@20 did not move, no reranker
setting will. Run 5 of the first live loop was exactly that case.

--paraphrases FILE scores FILE's same:true rows too (evals/paraphrases.jsonl: 24 golden questions in other words),
each on the anchors of the golden row it rewords; under each arm's line, the golden rows and the paraphrases apart.

Under each arm's line is its miss list - the rows that cost a point and where the anchor went:
"ranked out" (in the candidates, not the five: the reranker's) or "not retrieved at depth N" (the
retriever's, or the corpus's). A row that fails twice is counted and printed, never scored.

Cost: about four query embeddings and three Rank API requests per row, and the Firestore reads
of each tenant's text (no embeddings are fetched). Not one generation call. Exit code 0 is a
measurement, not a verdict; it is 1 only when an arm could not run a single row.
--rewrite adds one generation call per question (gemini-3.1-flash-lite on global, kept, so a retried row is not
asked twice) and an embedding for each rewrite it searches.

Measured on 8 Sept 2026 from Cloud Shell, 43 rows: dense 5 alone 0.91 recall@5 / 0.81 MRR; the
lane's dense 20 -> rerank 5 0.96 / 0.91; dense 50 -> rerank 5 0.99 / 0.94 at four times the
latency; hybrid 20 -> rerank 5 identical to the lane's row at alpha 0.5 and (ACME's 36 rows) 0.7.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import sys
import time

ARM_KEYS = ("dense5", "dense20", "dense50", "hybrid", "rag_engine", "vertex_search")
DEFAULT_ARMS = ("dense5", "dense20", "dense50", "hybrid")

HERE = os.path.dirname(os.path.abspath(__file__))
GOLDEN = os.path.join(HERE, "golden.jsonl")


# ------------------------------------------------------------------ pure parts (testable offline)
def tokens(text: str) -> list:
    return re.findall(r"[a-z0-9\-]+", text.lower())


def rrf(dense_ids: list, sparse_ids: list, alpha: float = 0.7, k: int = 60) -> list:
    """Reciprocal Rank Fusion, hybrid.py's semantics: alpha=1 dense only, 0 sparse only."""
    fused = {}
    for rank, cid in enumerate(dense_ids):
        fused[cid] = fused.get(cid, 0.0) + alpha / (k + rank + 1)
    for rank, cid in enumerate(sparse_ids):
        fused[cid] = fused.get(cid, 0.0) + (1 - alpha) / (k + rank + 1)
    return [cid for cid, _ in sorted(fused.items(), key=lambda kv: -kv[1])]


def hay(chunk: dict) -> str:
    return (chunk.get("source_uri", "") + " " + chunk.get("text", "")).lower()


def recall_at(chunks: list, anchors: list, k: int) -> float:
    found = [hay(c) for c in chunks[:k]]
    return sum(1 for a in anchors if any(a.lower() in h for h in found)) / len(anchors)


def mrr(chunks: list, anchors: list) -> float:
    for i, c in enumerate(chunks, 1):
        if any(a.lower() in hay(c) for a in anchors):
            return 1.0 / i
    return 0.0


def p95(values: list) -> float:
    return sorted(values)[int(0.95 * (len(values) - 1))] if values else 0.0


# ------------------------------------------------------------------ the lane, from outside it
class Lane:
    """The three services the API's retriever calls, with the same settings, from outside it."""

    def __init__(self, project: str, region: str, alpha: float = 0.7, current_only: bool = True):
        from google import genai
        from google.cloud import discoveryengine_v1 as discoveryengine
        from google.cloud import firestore
        self.project, self.alpha = project, alpha
        # 12 September 2026: the lane retrieves only rows the ledger marks current (RETRIEVAL_CURRENT_ONLY=on,
        # retriever.py) - a retired version's chunk is not a hit there, so it is not a hit here either. The
        # review of the rag_prod plan found this harness counting retired chunks the API would never serve.
        self.current_only = current_only
        self.embed_client = genai.Client(enterprise=True, project=project, location=region)   # embeddings: regional
        self.db = firestore.Client(project=project, database="(default)")
        self.ranker = discoveryengine.RankServiceClient()
        self.ranking_config = self.ranker.ranking_config_path(
            project=project, location="global", ranking_config="default_ranking_config")
        self._tenant = {}
        self._rag_module, self._corpora, self._sources = None, {}, {}

    def embed_query(self, q: str) -> list:
        from google.genai import types
        return self.embed_client.models.embed_content(
            model="text-embedding-005", contents=q,
            config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY", output_dimensionality=768),
        ).embeddings[0].values

    def tenant_corpus(self, tenant: str):
        """One tenant's text chunks (no embeddings: 768 floats each) and a BM25 index - the sparse leg."""
        if tenant not in self._tenant:
            from google.cloud.firestore_v1.base_query import FieldFilter
            from rank_bm25 import BM25Okapi
            rows = []
            for d in (self._current(self.db.collection("chunks").where(filter=FieldFilter("tenant_id", "==", tenant)))
                      .select(["text", "source_uri"]).stream()):
                x = d.to_dict()
                rows.append({"chunk_id": d.id, "text": x.get("text", ""), "source_uri": x.get("source_uri", "")})
            self._tenant[tenant] = (rows, {r["chunk_id"]: r for r in rows}, BM25Okapi([tokens(r["text"]) for r in rows]))
        return self._tenant[tenant]

    def _current(self, query):
        """The ledger's pre-filter, when the lane applies it: the tenant_id + current + embedding index serves it."""
        from google.cloud.firestore_v1.base_query import FieldFilter
        return query.where(filter=FieldFilter("current", "==", True)) if self.current_only else query

    def dense(self, question: str, tenant: str, k: int) -> list:
        """The lane's Firestore rung: find_nearest with the tenant pre-filter and the ledger's."""
        from google.cloud.firestore_v1.base_query import FieldFilter
        from google.cloud.firestore_v1.base_vector_query import DistanceMeasure
        from google.cloud.firestore_v1.vector import Vector
        docs = (self._current(self.db.collection("chunks").where(filter=FieldFilter("tenant_id", "==", tenant)))
                .find_nearest(vector_field="embedding", query_vector=Vector(self.embed_query(question)),
                              distance_measure=DistanceMeasure.COSINE, limit=k, distance_result_field="d")
                .get())
        out = []
        for d in docs:
            x = d.to_dict()
            out.append({"chunk_id": d.id, "text": x.get("text", ""), "source_uri": x.get("source_uri", ""), "doc_key": x.get("doc_key")})
        return out

    def hybrid(self, question: str, tenant: str, k: int) -> list:
        rows, by_id, bm25 = self.tenant_corpus(tenant)
        dense_ids = [c["chunk_id"] for c in self.dense(question, tenant, k)]
        scores = bm25.get_scores(tokens(question))
        sparse_ids = [rows[i]["chunk_id"] for i in sorted(range(len(rows)), key=lambda i: -scores[i])[:k] if scores[i] > 0]
        return [by_id[cid] for cid in rrf(dense_ids, sparse_ids, self.alpha)[:k] if cid in by_id]

    def rag(self, location: str = "us-central1"):
        """vertexai.rag on the corpora's region (serverless corpora: us-central1 only), initialised once."""
        if self._rag_module is None:
            import vertexai
            from vertexai import rag
            vertexai.init(project=self.project, location=os.environ.get("RAG_LOCATION", location))
            self._rag_module = rag
        return self._rag_module

    def corpus(self, tenant: str) -> str:
        """The tenant's corpus by the mirror's name (documind-{tenant}); a tenant without one fails the row."""
        if tenant not in self._corpora:
            want = "documind-" + re.sub(r"[^a-z0-9-]+", "-", tenant.lower()).strip("-")
            name = next((c.name for c in self.rag().list_corpora() if c.display_name == want), None)
            if name is None:
                raise RuntimeError(f"no RAG Engine corpus {want!r}: make rag-corpus TENANT={tenant}, then MANAGED_MIRROR=rag_engine")
            self._corpora[tenant] = name
        return self._corpora[tenant]

    def source_of(self, tenant: str, doc_key: str) -> str:
        """A context names its version (the RagFile's display name is the doc_key); the kit's rows name the source."""
        if doc_key not in self._sources:
            from google.cloud.firestore_v1.base_query import FieldFilter
            snap = next(iter(self.db.collection("chunks").where(filter=FieldFilter("tenant_id", "==", tenant))
                             .where(filter=FieldFilter("doc_key", "==", doc_key)).select(["source_uri"]).limit(1).stream()), None)
            self._sources[doc_key] = (snap.to_dict() or {}).get("source_uri", "") if snap else ""
        return self._sources[doc_key]

    def rag_engine(self, question: str, tenant: str, k: int) -> list:
        """P9.4's backend from outside it: 4.3's corpus queried by text (4.3's distance threshold), the contexts as
        chunks with the source the ledger knows - what retriever._managed_retrieve() serves, without the API."""
        rag = self.rag()
        resp = rag.retrieval_query(
            rag_resources=[rag.RagResource(rag_corpus=self.corpus(tenant))], text=question,
            rag_retrieval_config=rag.RagRetrievalConfig(top_k=k, filter=rag.Filter(vector_distance_threshold=0.5)))
        out = []
        for i, ctx in enumerate(resp.contexts.contexts):
            key = getattr(ctx, "source_display_name", "") or ""
            out.append({"chunk_id": f"{tenant}:{key}#rag-{i}", "text": getattr(ctx, "text", "") or "",
                        "source_uri": self.source_of(tenant, key) if key else ""})
        return out

    def vertex_search(self, question: str, tenant: str, k: int) -> list:
        """R4's backend from outside it, as retriever._search_retrieve() serves it: 4.4's data store (documind-{tenant},
        managed.tf) ranks the tenant's documents by text through its default serving config, and the passages are the
        kit's own rows of those versions - the dense rung's nearest, three times k deep, kept when the store ranked
        their version. A standard-edition store's own text is a snippet that stops short of the figure, and its
        extractive segments are refused (22 October 2026). A store that ranks no document is the dense rung's k
        nearest, as the API serves it; the question is kept in store_empty, and the arm's line counts them. A tenant
        with no data store raises (MANAGED_SEARCH=true make up declares one per `any` tenant), like the corpus arm."""
        from google.cloud import discoveryengine_v1 as discoveryengine
        client = discoveryengine.SearchServiceClient()
        store = "documind-" + re.sub(r"[^a-z0-9-]+", "-", tenant.lower()).strip("-")
        serving = (f"projects/{self.project}/locations/global/collections/default_collection/dataStores/{store}"
                   f"/servingConfigs/default_search")
        ranked = {r.document.id for r in client.search(request=discoveryengine.SearchRequest(
            serving_config=serving, query=question, page_size=k)) if r.document.id}
        if not ranked:
            self.store_empty = getattr(self, "store_empty", set()) | {(tenant, question)}
            return self.dense(question, tenant, k)
        return [c for c in self.dense(question, tenant, 3 * k) if c.get("doc_key") in ranked][:k]

    def rerank(self, question: str, chunks: list, top_n: int = 5) -> list:
        from google.cloud import discoveryengine_v1 as discoveryengine
        if not chunks:
            return chunks
        records = [discoveryengine.RankingRecord(id=str(i), title=c["source_uri"].rsplit("/", 1)[-1],
                                                 content=c["text"][:4000]) for i, c in enumerate(chunks)]
        resp = self.ranker.rank(request=discoveryengine.RankRequest(
            ranking_config=self.ranking_config, model="semantic-ranker-fast-004",
            top_n=top_n, query=question, records=records))
        return [chunks[int(r.id)] for r in resp.records]


def arms(lane: Lane, keys=DEFAULT_ARMS) -> list:
    every = {  # key: (name, candidates(question, tenant), reranked to 5?)
        "dense5": ("dense 5, no reranker", lambda q, t: lane.dense(q, t, 5), False),
        "dense20": ("dense 20 -> rerank 5   (the lane)", lambda q, t: lane.dense(q, t, 20), True),
        "dense50": ("dense 50 -> rerank 5", lambda q, t: lane.dense(q, t, 50), True),
        "hybrid": ("hybrid 20 -> rerank 5  (4.5, not wired)", lambda q, t: lane.hybrid(q, t, 20), True),
        "rag_engine": ("rag_engine 20 -> rerank 5  (4.3's corpus, P9.4)", lambda q, t: lane.rag_engine(q, t, 20), True),
        "vertex_search": ("vertex_search 20 -> rerank 5  (4.4's data store, R4)", lambda q, t: lane.vertex_search(q, t, 20), True),
    }
    return [every[k] for k in keys]


def parse_arms(spec: str) -> tuple:
    """--arms: `all`, or a comma-separated list of arm keys; the default is the four the lane can always run."""
    if not spec or spec == "default":
        return DEFAULT_ARMS
    if spec == "all":
        return ARM_KEYS
    keys = tuple(k.strip() for k in spec.split(",") if k.strip())
    unknown = [k for k in keys if k not in ARM_KEYS]
    if unknown:
        raise ValueError(f"unknown arm(s) {unknown}: one of {', '.join(ARM_KEYS)} or all")
    return keys


# ------------------------------------------------------------------ workshop lesson 2.5: the rewrite arm and the paraphrases
def _shared():
    """shared/, beside evals/: query_rewrite and prices, imported only by a run that asks for the rewrite."""
    deploy = os.path.dirname(HERE)
    if deploy not in sys.path:
        sys.path.insert(0, deploy)
    from shared import prices, query_rewrite
    return query_rewrite, prices


def rewrite_arm(lane: Lane, rewrite=None, depth: int = 20) -> tuple:
    """--rewrite's arm: built beside arms(), never an ARM_KEYS entry, so --arms all is what it was. The lane's dense 20 ->
    rerank 5 with the question rewritten first by shared/query_rewrite.py, as rag-api's /v1/query does under
    QUERY_REWRITE=on: the rewrite is what dense() searches, and main()'s loop reranks the question as asked. A rewrite
    the literal guard refuses, or one that failed, searches the question, so the arm differs from the lane's only where
    a rewrite was accepted. One call per question - gemini-3.1-flash-lite on global, unless `rewrite` is given - kept,
    so a retried row is not asked twice. Returns (the arm, its tally: calls, outcomes, errors, tokens, cost_usd)."""
    if rewrite is None:
        query_rewrite, _ = _shared()
        from google import genai
        client = genai.Client(enterprise=True, project=lane.project, location="global")   # Gemini 3.x: global only

        def rewrite(q):
            return query_rewrite.rewrite(client, q)
    kept, tally = {}, {"calls": 0, "outcomes": {}, "errors": {}, "tokens_in": 0, "tokens_out": 0, "cost_usd": 0.0}

    def search(question: str) -> str:
        if question not in kept:
            got = rewrite(question)
            kept[question] = got["query"]
            tally["calls"] += 1
            tally["outcomes"][got["outcome"]] = tally["outcomes"].get(got["outcome"], 0) + 1
            if got.get("error"):
                tally["errors"][got["error"]] = tally["errors"].get(got["error"], 0) + 1
            tally["tokens_in"] += got["tokens_in"]
            tally["tokens_out"] += got["tokens_out"]
            tally["cost_usd"] += got["cost_usd"]
        return kept[question]
    return (f"rewrite -> dense {depth} -> rerank 5  (2.5)", lambda q, t: lane.dense(search(q), t, depth), True), tally


def rewrite_summary(tally: dict) -> str:
    """The line under the rewrite arm: what the rewrites were, and what they cost at list price."""
    _, prices = _shared()
    o = tally["outcomes"]
    errors = ", ".join(f"{k} {v}" for k, v in sorted(tally["errors"].items()))
    return (f"rewrite: {tally['calls']} question{'' if tally['calls'] == 1 else 's'} - {o.get('rewritten', 0)} rewritten, "
            f"{o.get('same', 0)} given back as asked, "
            f"{o.get('rejected', 0)} refused by the literal guard, {o.get('fallback', 0)} fell back" + (f" ({errors})" if errors else "")
            + f"; {tally['tokens_in']:,} tokens in, {tally['tokens_out']:,} out, Rs {prices.inr(tally['cost_usd']):.2f} at list price")


def paraphrase_rows(path: str, golden: list) -> list:
    """--paraphrases: FILE's same:true rows (evals/paraphrases.jsonl: 24), each scored on the anchors of the golden row it
    rewords (`of`), in that row's tenant. A same:false row asks something else - another grade, another figure - and is
    never scored on its original's anchors; nor is a row whose original carries none, or names another tenant."""
    by_id = {r["id"]: r for r in golden}
    with open(path, encoding="utf-8") as f:
        rows = [json.loads(line) for line in f if line.strip()]
    out = []
    for p in rows:
        src = by_id.get(p.get("of"))
        if p.get("same") is True and src and src.get("must_retrieve") and p.get("tenant", src["tenant"]) == src["tenant"]:
            out.append({"id": p["id"], "of": src["id"], "question": p["question"], "tenant": src["tenant"],
                        "must_retrieve": src["must_retrieve"], "paraphrase": True})
    return out


def _share(r5: list, rr: list, idx: list) -> str:
    """recall@5, MRR and rows at 1.0 over some of an arm's scored rows."""
    return (f"{len(idx)} rows, recall@5 {statistics.mean(r5[i] for i in idx):.2f}, mrr {statistics.mean(rr[i] for i in idx):.2f}, "
            f"{sum(1 for i in idx if r5[i] == 1.0)} at 1.0")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--project", default=os.environ.get("PROJECT") or os.environ.get("GOOGLE_CLOUD_PROJECT"),
                    help="the project the lane runs in (default: $PROJECT)")
    ap.add_argument("--region", default="us-central1", help="where text-embedding-005 is served (regional)")
    ap.add_argument("--golden", default=GOLDEN)
    ap.add_argument("--limit", type=int, default=0, help="run only the first N anchored rows (a wiring check)")
    ap.add_argument("--tenant", help="only this tenant's rows")
    ap.add_argument("--alpha", type=float, default=0.7, help="RRF weight of the dense leg in the hybrid arm")
    ap.add_argument("--all-versions", action="store_true",
                    help="retrieve retired rows too (the lane does not: RETRIEVAL_CURRENT_ONLY=on); for a corpus that predates the ledger")
    ap.add_argument("--ledger", help="append one JSON line per arm to this file (the loop's memory)")
    ap.add_argument("--arms", default="default",
                    help="which arms: all, or a comma list of " + ", ".join(ARM_KEYS) + " (default: the four the lane always has)")
    ap.add_argument("--rewrite", action="store_true",
                    help="add workshop lesson 2.5's arm: the lane's dense 20 -> rerank 5 with the question rewritten first "
                         "(one gemini-3.1-flash-lite call per question, on global)")
    ap.add_argument("--paraphrases", metavar="FILE",
                    help="score FILE's same:true rows too (evals/paraphrases.jsonl), each on the anchors of the golden row it rewords")
    a = ap.parse_args()
    try:
        keys = parse_arms(a.arms)
    except ValueError as e:
        print(e, file=sys.stderr)
        return 2
    if not a.project:
        print("--project (or $PROJECT) is required", file=sys.stderr)
        return 2

    with open(a.golden, encoding="utf-8") as f:
        golden = [json.loads(l) for l in f if l.strip()]
    rows = [r for r in golden if r.get("must_retrieve") and (not a.tenant or r["tenant"] == a.tenant)]
    if a.paraphrases:                                   # workshop lesson 2.5: the same questions in other words
        rows += [p for p in paraphrase_rows(a.paraphrases, golden) if not a.tenant or p["tenant"] == a.tenant]
    if a.limit:
        rows = rows[:a.limit]
    lane = Lane(a.project, a.region, a.alpha, current_only=not a.all_versions)
    rw_arm, rw_tally = rewrite_arm(lane) if a.rewrite else (None, None)
    n_pp = sum(1 for r in rows if r.get("paraphrase"))
    print(f"{len(rows)} rows with anchors, {sum(len(r['must_retrieve']) for r in rows)} anchors, one knob per arm "
          f"(project {a.project}, embeddings in {a.region}, ranker on global)\n"
          + (f"  {n_pp} of them paraphrases ({a.paraphrases}): golden questions in other words, on their originals' anchors\n" if n_pp else ""))
    print(f"{'arm':44} {'recall@depth':>12} {'recall@5':>9} {'mrr':>6} {'rows@1.0':>8} {'p95 ms':>7}")
    failed = 0
    for name, cands, do_rerank in arms(lane, keys) + ([rw_arm] if rw_arm else []):
        r_depth, r5, rr, ms, errors, misses, para = [], [], [], [], [], [], []
        for row in rows:
            t0, c, top = time.time(), None, None
            for attempt in (1, 2):                      # one retry: a dropped stream is the network, not the lane
                try:
                    c = cands(row["question"], row["tenant"])
                    top = lane.rerank(row["question"], c) if do_rerank else c[:5]
                    break
                except Exception as e:                  # one row must not stop the arm
                    c = None
                    if attempt == 2:
                        errors.append(f"{row['id']}: {type(e).__name__}: {str(e)[:120]}")
                    else:
                        time.sleep(2)
            if c is None:
                continue
            ms.append((time.time() - t0) * 1000)
            r_depth.append(recall_at(c, row["must_retrieve"], len(c)))     # this arm's ceiling
            r5.append(recall_at(top, row["must_retrieve"], 5))
            rr.append(mrr(top, row["must_retrieve"]))
            para.append(bool(row.get("paraphrase")))
            if r5[-1] < 1.0:                            # the miss list: the rows that cost a point, and WHERE the anchor went
                got = [hay(x) for x in top]
                missing = [a for a in row["must_retrieve"] if not any(a.lower() in h for h in got)]
                deeper = [a for a in missing if any(a.lower() in hay(x) for x in c)]
                misses.append(f"{row['id']}: {', '.join(missing)} - "
                              + ("ranked out (in the candidates, not the five)" if deeper and len(deeper) == len(missing)
                                 else f"not retrieved at depth {len(c)}" if not deeper
                                 else f"{', '.join(deeper)} ranked out; the rest not retrieved at depth {len(c)}"))
        if not r5:
            print(f"{name:44} {'every row failed':>12}"); failed += 1
            for e in errors[:3]:
                print("      ", e)
            continue
        line = {"arm": name, "rows": len(r5), "recall_at_depth": round(statistics.mean(r_depth), 3),
                "recall_at_5": round(statistics.mean(r5), 3), "mrr": round(statistics.mean(rr), 3),
                "rows_at_1": sum(1 for x in r5 if x == 1.0), "p95_ms": round(p95(ms)), "errors": len(errors),
                "misses": misses}
        print(f"{name:44} {line['recall_at_depth']:12.2f} {line['recall_at_5']:9.2f} {line['mrr']:6.2f} "
              f"{line['rows_at_1']:8d} {line['p95_ms']:7d}" + (f"   ({len(errors)} rows failed)" if errors else ""))
        if any(para):                                   # --paraphrases: the two kinds of row apart
            idx = {k: [i for i, x in enumerate(para) if x == (k == "paraphrases")] for k in ("golden", "paraphrases")}
            print("       " + " | ".join(f"{k} {_share(r5, rr, v)}" for k, v in idx.items() if v))
            line.update({k: {"rows": len(v), "recall_at_5": round(statistics.mean(r5[i] for i in v), 3),
                             "mrr": round(statistics.mean(rr[i] for i in v), 3)} for k, v in idx.items() if v})
        if rw_arm and name == rw_arm[0]:                # --rewrite: what the rewrites were, and what they cost
            print("       " + rewrite_summary(rw_tally))
            line["rewrite"] = dict(rw_tally)
        for e in errors[:3]:
            print("      ", e)
        if name.startswith("vertex_search") and getattr(lane, "store_empty", None):
            line["store_empty"] = len(lane.store_empty)    # the rows the kit's own rows answered: the store ranked nothing
            print(f"       the store ranked no document for {len(lane.store_empty)} of {len(r5)} rows: the kit's nearest rows "
                  f"answered them, as the API does")
        for m_ in misses:
            print("       lost:", m_)
        if a.ledger:
            with open(os.path.expanduser(a.ledger), "a", encoding="utf-8") as f:
                f.write(json.dumps({"at": time.strftime("%Y-%m-%dT%H:%M:%S"), "project": a.project, **line}) + "\n")
    print("\nRead it in this order: recall@depth is the reranker's ceiling - if the 20 and 50 rows agree, depth is not the knob;"
          "\nrecall@5 of the lane's row minus the first row is the reranker's lift, and p95 is what it costs;"
          "\nthe hybrid row says whether a BM25 leg is worth wiring - twenty of the anchors are clause codes, its home ground;"
          "\nthe rag_engine row (--arms all) is 4.3's corpus against the lane's own rows - a managed chunk that splits a clause from its code shows up as a miss.")
    if rw_arm:
        print("the rewrite row (--rewrite) is the lane's row with the question rewritten first: its recall@5 minus the lane's is the rewrite's lift,"
              "\nand a row equal to the lane's says the rewrite is not the knob on these questions; the line under it is what the calls cost.")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
