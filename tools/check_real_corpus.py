#!/usr/bin/env python3
"""Can the corpus, chunked the way the notebooks chunk it, actually answer the golden set?

    python tools/check_real_corpus.py            # offline, no credentials, no third-party packages
    python tools/check_real_corpus.py --show lk-14

run_eval.py's offline half proves the golden set is SOUND: every figure it asserts is in the
right tenant's documents. This proves the documents are RETRIEVABLE once they are chunks: it
loads deploy/evals/corpus/ through deploy/shared/documind_corpus.py - the loader lessons 4.2 and
4.5 paste verbatim, so these are the notebooks' own chunk boundaries and chunk ids - and, for
every golden row, checks

  intact     each must_contain phrase survives chunking whole, in at least one chunk of the
             row's tenant (a window cut through "twenty-six weeks" would make the row
             unanswerable by any retriever, and no live score would say why);
  anchors    each must_retrieve anchor is a substring of at least one chunk id of that tenant,
             because that is the rule 4.7's recall_at_k applies to retrieved ids;
  recall@5   a lexical retriever (BM25, implemented below so the gate needs nothing installed)
             over the tenant's chunks puts a chunk carrying every anchor in its top 5, and a
             chunk carrying every must_contain phrase too. Dense retrieval on a live project can
             only do better on a paraphrase and cannot be run here; a lexical hit is the floor.

It exits 1 if any phrase is not intact, any anchor unmatched, or recall@5 falls under the
floor below. The floor is set from the measured value and a drop is a chunker or corpus
regression, not noise - BM25 is deterministic. Two measurements, because the corpus grew:

  2026-09-05, six Acts, 465 ACME chunks        30 of 31 scorable rows
  2026-09-06, thirteen documents, 1,624 chunks  38 of 43 scorable rows

The five misses on the big corpus are what a lexical top-5 loses on a 236-page Act: lk-27's
ceiling sits in one sentence of the CGST Act while "rate", "central" and "tax" sit in hundreds;
lk-23 and lk-26 lose to the ministry's handbook and the IT Act, which use the question's words
more often than the section that answers it; jn-10 needs the 1972 Act beside the 2020 Code that
repeats it. That is the case for dense retrieval and a reranker (4.5), stated as a number.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "deploy"))
from shared import documind_corpus as dc  # noqa: E402

EVALS = os.path.join(ROOT, "deploy", "evals")
RECALL_FLOOR = 0.85
K = 5
TOKEN = re.compile(r"[a-z0-9][a-z0-9.,'-]*")


def tok(s: str) -> list[str]:
    return [t.strip(".,'") for t in TOKEN.findall(s.lower())]


class BM25:
    """Okapi BM25, the textbook form. Same idea as rank_bm25.BM25Okapi in lesson 4.5."""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1, self.b, self.docs = k1, b, docs
        self.avgdl = sum(map(len, docs)) / max(1, len(docs))
        df: dict[str, int] = {}
        for d in docs:
            for t in set(d):
                df[t] = df.get(t, 0) + 1
        n = len(docs)
        self.idf = {t: math.log(1 + (n - f + 0.5) / (f + 0.5)) for t, f in df.items()}
        self.tf = [{t: d.count(t) for t in set(d)} for d in docs]

    def scores(self, query: list[str]) -> list[float]:
        out = []
        for d, tf in zip(self.docs, self.tf):
            s = 0.0
            for q in query:
                if q in tf:
                    f = tf[q]
                    s += self.idf[q] * f * (self.k1 + 1) / (f + self.k1 * (1 - self.b + self.b * len(d) / self.avgdl))
            out.append(s)
        return out


def load_chunks(tenant: str) -> list[dict]:
    docs = dc.load_documents(tenant, EVALS, "documind-ai-YOUR-ID")
    return [c for d in docs for c in dc.chunk_document(d, tenant)]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", help="print the top-5 chunk ids for one row id")
    a = ap.parse_args()
    golden = [json.loads(l) for l in open(os.path.join(EVALS, "golden.jsonl"), encoding="utf-8") if l.strip()]
    tenants = sorted({r["tenant"] for r in golden})
    chunks = {t: load_chunks(t) for t in tenants}
    index = {t: BM25([tok(c["text"]) for c in chunks[t]]) for t in tenants}
    for t in tenants:
        print(f"  {t:7} {len(chunks[t]):4d} chunks from {len({c['source_uri'] for c in chunks[t]})} documents")
    print()

    problems, scored, hits = [], 0, 0
    per_shape: dict[str, list[int]] = {}
    for row in golden:
        t, cs = row["tenant"], chunks[row["tenant"]]
        low = [c["text"].lower() for c in cs]
        for want in row.get("must_contain", []):
            if not any(want.lower() in x for x in low):
                problems.append(f"{row['id']}: must_contain {want!r} is in no chunk of {t} - chunking cut it")
        for anchor in row.get("must_retrieve", []):
            if not any(anchor.lower() in c["chunk_id"].lower() for c in cs):
                problems.append(f"{row['id']}: anchor {anchor!r} is in no chunk id of {t}")
        if not row.get("must_retrieve") and not row.get("must_contain"):
            continue                                     # a refusal or a refusing isolation row: nothing to retrieve
        sc = index[t].scores(tok(row["question"]))
        top = sorted(range(len(cs)), key=lambda i: -sc[i])[:K]
        top_ids = [cs[i]["chunk_id"].lower() for i in top]
        top_txt = [low[i] for i in top]
        ok_anchor = all(any(anc.lower() in cid for cid in top_ids) for anc in row.get("must_retrieve", []))
        ok_phrase = all(any(w.lower() in x for x in top_txt) for w in row.get("must_contain", []))
        hit = ok_anchor and ok_phrase
        scored += 1
        hits += hit
        per_shape.setdefault(row["shape"], []).append(hit)
        if a.show == row["id"]:
            print(f"  {row['id']} [{t}] {row['question']}")
            for i in top:
                print(f"     {sc[i]:6.2f}  {cs[i]['chunk_id']:48} {cs[i]['text'][:70]!r}")
            print()
        if not hit:
            print(f"  miss  {row['id']:6} {row['shape']:9} anchors={'ok' if ok_anchor else 'MISSING'} "
                  f"phrase={'ok' if ok_phrase else 'MISSING'}  top: {', '.join(top_ids[:3])}")

    recall = hits / max(1, scored)
    print(f"\n  intact/anchors : {'PASS' if not problems else 'FAIL'}")
    for shape, v in sorted(per_shape.items()):
        print(f"  recall@{K} {shape:9}: {sum(v)}/{len(v)}")
    print(f"  recall@{K} overall  : {hits}/{scored} = {recall:.2f}  (floor {RECALL_FLOOR})")
    for p in problems:
        print("  -", p)
    if problems or recall < RECALL_FLOOR:
        print("\nNOT CLEAN")
        return 1
    print("\nCLEAN - every golden figure survives chunking, every anchor is a chunk id, and a plain "
          "lexical retriever finds them")
    return 0


if __name__ == "__main__":
    sys.exit(main())
