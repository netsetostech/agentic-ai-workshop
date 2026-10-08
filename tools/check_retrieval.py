#!/usr/bin/env python3
"""Offline checks for P4 of the RAG production plan - retrieval, reranking, packing - and the token half of 6.2.

    python tools/check_retrieval.py

No credential and no network: the library calls are replaced by fakes at the seam, and the functions under test
are lifted from their files with ast, so the modules' top-level imports (google.cloud.*, google.genai, fastapi)
need not be installed. Each check names the code change that would turn it red (12 September 2026, R06 / R08):

  hybrid.py       hybrid_find_neighbors returns the ONE query's neighbour list and [] when there is none
                  (find_neighbors answers a list per query); the tenant restrict is in the query whatever the
                  caller passed, and the dense path's restricts ride along.
  retriever.py    _firestore_fallback applies the tenant, the ledger's `current` and the caller's filters as
                  where() predicates; retrieve() sends the same restricts to hybrid, reads an empty outer list as
                  an empty pool (never the chaos rung) and hands the filters to the fallback; rerank() calls the
                  Ranking API with a deadline and, when it raises, returns the pool by retrieval score cut to k,
                  the rows marked, rerank_fallback logged with the tenant and the error type.
                  A doc_type list means any of its classes on every path: one restrict's allow_tokens, Firestore's
                  `in`, the store's ANY(), matches() on the rows a path checks itself, and Chroma's $in on the local
                  lane (shared/documind_tools.py).
  config.py       RETRIEVAL_MODE=hybrid with RETRIEVAL_BACKEND=firestore is refused when Settings is built, and
                  the message names the fix; an unknown value is refused too; RERANK_TIMEOUT_S is a setting.
                  RETRIEVAL_GRAPH (13 September 2026, 4.6's graph on the lane) is off | on | auto, refused otherwise;
                  retrieve() walks the tenant's graph (shared/documind_graph.FirestoreGraph) only when the switch
                  says so - auto asks choose_mode(), no model - and puts the walk's chunks, fetched by id and checked
                  by the same tenant / filters / current predicates, in front of the dense pool, cut to TOP_K_RETRIEVE.
  main.py         an unknown filter key is a 400 on both routes, before any work; an empty pool is a refusal on
                  both routes with no rerank, no model call and no cache store, answerable=False on the row;
                  a doc_type list (workshop lesson 10.6) is 1 to 5 non-empty strings made canonical in place, so
                  scope_of hashes one form per set, and a kind list is a 400 that says so;
                  /v1/stream cites the packed set generate_stream hands it, never the reranked pool; a cache hit
                  still cites the stored answer; rerank_fallback reaches the answer's stages and the row.
                  /v1/passages (workshop lesson 10.6) is the retrieval half: the same checks before retrieval, each
                  chunk's full text, no model call, no answer cache, a row with event passages and no cost; and
                  shared/documind_tools.retrieve(passages=True) asks it, or Chroma on the local lane.
  generator.py    generate_stream's first event is ("packed", packed), once, even when a tier falls back; the
                  chunk budget is max_context_tokens less the estimate of the fixed parts (TokenBudget.fit), and
                  the prompt never exceeds the total; the tokens of a truncated first attempt and the thinking
                  tokens are on the answer, in generate() and in the stream alike; cached tokens stay separate.
"""
from __future__ import annotations

import ast
import importlib.util
import json
import os
import re
import subprocess
import sys
import time
import types
from contextlib import contextmanager, nullcontext
from types import SimpleNamespace

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = os.path.join(ROOT, "deploy", "services", "rag-api")
sys.path.insert(0, os.path.join(ROOT, "deploy"))          # shared/ - the contract schemas.py imports
PASSED, SKIPPED = [], []


def ok(msg):
    PASSED.append(msg)
    print(f"  ok   {msg}")


def skip(msg):
    SKIPPED.append(msg)
    print(f"  skip {msg}")


def read(rel: str) -> str:
    return open(os.path.join(ROOT, rel), encoding="utf-8").read()


def load(path: str, name: str):
    """A pure module (no cloud import at the top), compiled from its SOURCE under a private name - never from
    __pycache__: a bytecode file written while a line was being tried and restored inside one second passes
    Python's mtime-and-size check and would test the wrong text."""
    mod = types.ModuleType(name)
    mod.__file__ = path
    sys.modules[name] = mod                  # a dataclass under `from __future__ import annotations` looks itself up here
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), mod.__dict__)
    return mod


def lift(src: str, ns: dict, names=None, bare=(), assigns=()):
    """exec the named functions and classes of a source file into ns - their globals - decorators kept unless the
    name is in `bare` (a FastAPI route), plus the module-level assignments in `assigns`."""
    for node in ast.parse(src).body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)) and (names is None or node.name in names):
            if node.name in bare:
                node.decorator_list = []
            exec(ast.unparse(node), ns)
        elif isinstance(node, ast.Assign) and any(getattr(t, "id", None) in assigns for t in node.targets):
            exec(ast.unparse(node), ns)


class _Namespace:
    """aiplatform's Namespace: a restrict on the query."""
    def __init__(self, name, allow_tokens=None, deny_tokens=None):
        self.name, self.allow_tokens, self.deny_tokens = name, list(allow_tokens or []), list(deny_tokens or [])

    def __repr__(self):
        return f"Namespace({self.name}, {self.allow_tokens})"


class _HybridQuery:
    def __init__(self, **kw):
        self.kw = kw


class _Endpoint:
    """MatchingEngineIndexEndpoint: find_neighbors answers what it was built with, or raises it."""
    def __init__(self, answer):
        self.answer, self.calls = answer, []

    def find_neighbors(self, **kw):
        self.calls.append(kw)
        if isinstance(self.answer, Exception):
            raise self.answer
        return self.answer


class _HTTPException(Exception):
    def __init__(self, status_code, detail=""):
        super().__init__(detail)
        self.status_code, self.detail = status_code, detail


def _sse(chunks: list[str]) -> list[tuple[str, dict]]:
    out = []
    for s in chunks:
        m = re.match(r"event: (\w+)\ndata: (.*)\n\n$", s, re.S)
        assert m, f"not an SSE frame: {s[:80]!r}"
        out.append((m.group(1), json.loads(m.group(2))))
    return out


def main() -> int:
    n1 = SimpleNamespace(id="acme#1", distance=0.9)
    n2 = SimpleNamespace(id="acme#2", distance=0.8)

    # ------------------------------------------------------------------ hybrid.py: one query, one list; the restricts
    leaf = "google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint"
    for name in ("google", "google.cloud", "google.cloud.aiplatform", "google.cloud.aiplatform.matching_engine"):
        sys.modules.setdefault(name, types.ModuleType(name))
    stub = types.ModuleType(leaf)
    stub.HybridQuery, stub.Namespace = _HybridQuery, _Namespace
    sys.modules[leaf] = stub
    hyb = load(os.path.join(API, "hybrid.py"), "hybrid_under_test")
    ep = _Endpoint([[n1, n2]])
    got = hyb.hybrid_find_neighbors(ep, "dep", [0.1, 0.2], "notice period", "acme", k=20, alpha=0.7)
    assert got == [n1, n2], "hybrid must return the one query's neighbour list, not find_neighbors' list of lists"
    assert hyb.hybrid_find_neighbors(_Endpoint([]), "dep", [0.1], "q", "acme") == [], "no answer is an empty pool"
    assert hyb.hybrid_find_neighbors(_Endpoint([[]]), "dep", [0.1], "q", "acme") == [], "an empty inner list is an empty pool"
    call = ep.calls[0]
    assert [(r.name, r.allow_tokens) for r in call["filter"]] == [("tenant_id", ["acme"])] and call["num_neighbors"] == 20
    assert call["deployed_index_id"] == "dep" and call["queries"][0].kw["rrf_ranking_alpha"] == 0.7 and call["queries"][0].kw["dense_embedding"] == [0.1, 0.2]
    ep = _Endpoint([[n1]])
    hyb.hybrid_find_neighbors(ep, "dep", [0.1], "q", "acme", restricts=[
        _Namespace("tenant_id", ["acme"]), _Namespace("current", ["true"]), _Namespace("doc_type", ["policy"])])
    assert [(r.name, r.allow_tokens) for r in ep.calls[-1]["filter"]] == [("tenant_id", ["acme"]), ("current", ["true"]), ("doc_type", ["policy"])], \
        "the dense path's restricts must reach the hybrid query, the tenant once"
    hyb.hybrid_find_neighbors(ep, "dep", [0.1], "q", "acme", restricts=[_Namespace("kind", ["figure"])])
    assert [r.name for r in ep.calls[-1]["filter"]] == ["tenant_id", "kind"], "the tenant restrict is never dropped"
    hyb.hybrid_find_neighbors(ep, "dep", [0.1], "notice period", "acme", alpha=0.0)
    assert "dense_embedding" not in ep.calls[-1]["queries"][0].kw and "rrf_ranking_alpha" not in ep.calls[-1]["queries"][0].kw, \
        "alpha 0 is a sparse-only query: 0.0 never reaches the index, which then answers in the dense order"
    assert hyb.rrf_fuse(["a", "b"], ["b", "c"], alpha=0.5)[0][0] == "b"
    ok("hybrid.py: hybrid_find_neighbors returns the one query's neighbour list and [] for nothing; the tenant restrict is in every query and the current / doc_type / kind restricts ride along")

    # ------------------------------------------------------------------ retriever.py: the same predicates on every path
    ret_src = read("deploy/services/rag-api/retriever.py")
    logs, fs_seen, fb_calls, hyd_calls = [], [], [], []

    class _Snap:
        def __init__(self, id, d): self.id, self._d = id, d
        def to_dict(self): return dict(self._d)

    class _FQuery:
        def __init__(self, wheres=()): self.wheres = list(wheres)
        def where(self, f, op, v): return _FQuery(self.wheres + [(f, op, v)])
        def find_nearest(self, field, vec, distance_measure=None, limit=None, distance_result_field="d"):
            fs_seen.append({"wheres": self.wheres, "field": field, "limit": limit})
            return SimpleNamespace(get=lambda: [_Snap("acme#1", {"tenant_id": "acme", "text": "sixty days", "embedding": [1.0], "d": 0.2,
                                                                    "source_uri": "gs://b/acme/hr.md", "doc_type": "policy"})])

    rows = {"acme#1": {"tenant_id": "acme", "text": "sixty days", "source_uri": "gs://b/acme/hr.md"},
            "acme#2": {"tenant_id": "acme", "text": "ninety days", "source_uri": "gs://b/acme/old.md"}}
    settings = SimpleNamespace(chunks_collection="chunks", retrieval_current_only="on", retrieval_backend="vector", retrieval_mode="dense",
                               top_k_retrieve=20, vector_deployed_index="dep", project_id="demo", rerank_model="semantic-ranker-fast-004",
                               rerank_timeout_s=5.0, retrieval_graph="off", graph_hops=1, graph_cap=20, graph_backend="firestore", graph_seed_k=5, graph_seed_distance=0.4,
                               rag_location="us-central1", rag_distance_threshold=0.5, search_location="global", search_segments=3)
    graph_calls, graph_answer = [], {"seeds": [], "nodes": []}

    class _FakeGraph:
        """shared/documind_graph.FirestoreGraph at the seam: seed() and expand() answer what the test set."""
        def __init__(self, db): graph_calls.append(("init", db))
        def seed(self, question, tenant_id, limit=5):
            graph_calls.append(("seed", question, tenant_id)); return list(graph_answer["seeds"])
        def expand(self, seed_ids, tenant_id, hops=1, cap=20):
            graph_calls.append(("expand", list(seed_ids), tenant_id, hops, cap)); return list(graph_answer["nodes"])
    class _FakeSpannerGraph(_FakeGraph):
        """shared/documind_graph.SpannerGraph at the seam: seeds by meaning, the same answers as the Firestore fake."""
        def seed_by_vector(self, vec, tenant_id, k=5, max_distance=0.4):
            graph_calls.append(("seed_by_vector", list(vec), tenant_id, k, max_distance)); return list(graph_answer["seeds"])
    graph_ns = {"re": re, "__builtins__": __builtins__}
    lift(read("deploy/shared/documind_graph.py"), graph_ns, names=("choose_mode",))      # the notebook's router, as the kit carries it
    rns = {"json": json, "re": re, "hashlib": __import__("hashlib"), "settings": settings, "Namespace": _Namespace, "Vector": list, "DistanceMeasure": SimpleNamespace(COSINE="cosine"),
           "logging": SimpleNamespace(warning=lambda s: logs.append(json.loads(s)), info=lambda s: logs.append(json.loads(s))),
           "_fs": lambda: SimpleNamespace(collection=lambda name: _FQuery() if name == "chunks" else None),
           "embed_query": lambda q: [0.1], "discoveryengine": SimpleNamespace(RankingRecord=lambda **kw: kw, RankRequest=lambda **kw: kw),
           "FirestoreGraph": _FakeGraph, "SpannerGraph": _FakeSpannerGraph, "_spanner_db": lambda: "spanner-db",
           "embed_for_graph": lambda q: graph_calls.append(("embed_for_graph", q)) or [0.9, 0.1],
           "choose_mode": graph_ns["choose_mode"], "__builtins__": __builtins__}
    lift(ret_src, rns, names=("matches", "_firestore_fallback", "newest_per_source", "prefer_current", "_dense_retrieve", "graph_candidates", "retrieve", "_graph_store",
                              "_by_retrieval_score", "rerank_fell_back", "rerank", "_rag_corpus", "_version_row", "_page_span", "_search_serving_config", "_search_filter", "_search_texts", "_search_retrieve",
                              "_media_rows", "_managed_retrieve"), assigns=("_corpora",))
    fb = rns["_firestore_fallback"]
    out = fb([0.1], "acme", 20, {"doc_type": "policy"})
    assert fs_seen[-1]["wheres"] == [("tenant_id", "==", "acme"), ("current", "==", True), ("doc_type", "==", "policy")], fs_seen[-1]
    assert fs_seen[-1]["limit"] == 20 and out[0]["id"] == "acme#1" and out[0]["score"] == 0.8 and "embedding" not in out[0]
    fb([0.1], "acme", 20)
    assert fs_seen[-1]["wheres"] == [("tenant_id", "==", "acme"), ("current", "==", True)], "no filters, no extra predicate"
    settings.retrieval_current_only = "off"
    fb([0.1], "acme", 20, {"kind": "figure"})
    assert fs_seen[-1]["wheres"] == [("tenant_id", "==", "acme"), ("kind", "==", "figure")], fs_seen[-1]
    settings.retrieval_current_only = "on"
    fb([0.1], "acme", 20, {"doc_type": ["guidance", "statute"], "kind": "text"})
    assert fs_seen[-1]["wheres"] == [("tenant_id", "==", "acme"), ("current", "==", True), ("doc_type", "in", ["guidance", "statute"]), ("kind", "==", "text")], \
        "a doc_type list is one `in` pre-filter on the Firestore rung (workshop lesson 10.6); kind stays an equality"
    ok("retriever._firestore_fallback: the tenant, the ledger's current (when on) and the caller's doc_type / kind filters are where() predicates on the vector query, a doc_type list as `in`; the score is 1 - cosine and the embedding never ships")

    m = rns["matches"]
    assert m({"doc_type": "statute", "kind": "text"}, {"doc_type": ["guidance", "statute"]}) and not m({"doc_type": "policy"}, {"doc_type": ["guidance", "statute"]})
    assert m({"doc_type": "policy"}, {"doc_type": "policy"}) and not m({"doc_type": "policy"}, {"doc_type": "invoice"}) and m({"doc_type": "x"}, None) and m({}, {})
    assert m({"doc_type": "statute", "kind": "text"}, {"doc_type": ["statute"], "kind": "text"}) and not m({"doc_type": "statute", "kind": "figure"}, {"doc_type": ["statute"], "kind": "text"})
    assert not m({}, {"doc_type": ["statute"]}) and not m({"doc_type": None}, {"doc_type": "statute"}), "a row without the field never matches a filter on it"
    ret_fns = {n.name: ast.unparse(n) for n in ast.parse(ret_src).body if isinstance(n, ast.FunctionDef)}
    assert all("matches(d, filters)" in ret_fns[f] or "matches(chunk, filters)" in ret_fns[f] for f in ("_media_rows", "_managed_retrieve", "_search_retrieve", "graph_candidates")) \
        and not any(re.search(r"\.get\((k|'doc_type')\) != ", body) for body in ret_fns.values()), \
        "one helper for the row checks: the media rows, the two managed mappings and the graph's fetched rows - no scalar compare left beside it"
    ok("retriever.matches: a doc_type list is any of its classes, every other value one equality, a missing field never matches; it is the one row check on the media, rag_engine, vertex_search and graph paths")

    real_fb = rns["_firestore_fallback"]
    rns["_firestore_fallback"] = lambda vec, tenant_id, top_k, filters=None: fb_calls.append((vec, tenant_id, top_k, filters)) or real_fb(vec, tenant_id, top_k, filters)
    rns["_hydrate"] = lambda ids, scores: hyd_calls.append(list(ids)) or [{**rows[i], "id": i, "score": scores[i]} for i in ids if i in rows]
    ep = _Endpoint([])
    rns["_index_endpoint"] = lambda: ep
    assert rns["retrieve"]("q", "acme", 5, {"doc_type": "policy"}, vec=[0.1]) == [] and not fb_calls, \
        "an empty outer list from find_neighbors is an empty pool, not the chaos rung"
    assert [(r.name, r.allow_tokens) for r in ep.calls[-1]["filter"]] == [("tenant_id", ["acme"]), ("current", ["true"]), ("doc_type", ["policy"])]
    assert hyd_calls == [[]] or not hyd_calls
    rns["retrieve"]("q", "acme", 5, {"doc_type": ["guidance", "statute"]}, vec=[0.1])
    assert [(r.name, r.allow_tokens) for r in ep.calls[-1]["filter"]] == [("tenant_id", ["acme"]), ("current", ["true"]), ("doc_type", ["guidance", "statute"])], \
        "a doc_type list is ONE restrict whose allow_tokens are the classes - any of them - never one restrict per class, which would AND them to nothing"
    ep = _Endpoint([[n2, n1]])
    got = rns["retrieve"]("q", "acme", 5, None, vec=[0.1])
    assert [c["id"] for c in got] == ["acme#2", "acme#1"] and got[0]["score"] == 0.8, "the dense path hydrates in Vector Search's order"
    assert all(c["found_by"] == "vector" for c in got), "the dense path stamps found_by=vector, so a fallback cannot pass for a hit (16 September 2026)"
    rns["_index_endpoint"] = lambda: _Endpoint(RuntimeError("index undeployed"))
    got = rns["retrieve"]("q", "acme", 5, {"doc_type": "policy"}, vec=[0.1])
    assert fb_calls[-1] == ([0.1], "acme", 20, {"doc_type": "policy"}) and logs[-1]["event"] == "vector_search_fallback" and got[0]["id"] == "acme#1", \
        "an outage falls back to Firestore WITH the caller's filters"
    assert all(c["found_by"] == "firestore" for c in got), "the rung beneath says so on the chunk as well as in the log"
    hy_calls = []
    fake_hybrid = types.ModuleType("hybrid")
    fake_hybrid.hybrid_find_neighbors = lambda *a, **k: hy_calls.append((a, k)) or [n1]
    sys.modules["hybrid"] = fake_hybrid
    try:
        settings.retrieval_mode = "hybrid"
        rns["_index_endpoint"] = lambda: _Endpoint([[n1]])
        got = rns["retrieve"]("notice period", "acme", 5, {"doc_type": "policy"}, vec=[0.1])
        a, k = hy_calls[-1]
        assert [(r.name, r.allow_tokens) for r in k["restricts"]] == [("tenant_id", ["acme"]), ("current", ["true"]), ("doc_type", ["policy"])], \
            "the hybrid query must carry the same restricts as the dense one"
        assert a[3] == "notice period" and a[4] == "acme" and a[5] == 20 and k["alpha"] == 0.7 and [c["id"] for c in got] == ["acme#1"]
        rns["retrieve"]("notice period", "acme", 5, {"doc_type": ["guidance", "statute"]}, vec=[0.1])
        assert [(r.name, r.allow_tokens) for r in hy_calls[-1][1]["restricts"]][-1] == ("doc_type", ["guidance", "statute"]), "the hybrid query carries the list restrict too"
        fake_hybrid.hybrid_find_neighbors = lambda *a, **k: []
        assert rns["retrieve"]("q", "acme", 5, None, vec=[0.1]) == [] and fb_calls[-1][3] == {"doc_type": "policy"}, "an empty hybrid answer is an empty pool"
        fake_hybrid.hybrid_find_neighbors = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("index undeployed"))
        rns["retrieve"]("q", "acme", 5, {"kind": "table"}, vec=[0.1])
        assert fb_calls[-1][3] == {"kind": "table"} and logs[-1]["event"] == "vector_search_fallback", "hybrid takes the chaos rung too, filters included"
    finally:
        sys.modules.pop("hybrid", None)
        settings.retrieval_mode = "dense"
    settings.retrieval_backend = "firestore"
    got = rns["retrieve"]("q", "acme", 5, {"doc_type": "invoice"}, vec=[0.1])
    assert fb_calls[-1] == ([0.1], "acme", 20, {"doc_type": "invoice"}), "the Firestore backend hands the filters to Firestore"
    assert all(c["found_by"] == "firestore" for c in got), "chosen or fallen into, the Firestore rung stamps the same found_by"
    settings.retrieval_backend = "vector"
    ok("retriever.retrieve: the dense, the hybrid and the Firestore paths carry the same tenant / current / filter predicates, a doc_type list as one restrict's allow_tokens; an empty neighbour list is an empty pool; an outage on either mode falls back with the filters; every chunk says which rung found it (found_by vector | firestore)")

    # ------------------------------------------------------------------ 4.6's graph on the lane (13 September 2026)
    assert not any(c[0] == "seed" for c in graph_calls), "RETRIEVAL_GRAPH=off: every retrieval above touched no graph"
    chunk_docs = {"acme:hr#a": {"tenant_id": "acme", "text": "the standard supersedes STD-011", "source_uri": "gs://b/acme/hr.md", "doc_type": "policy", "current": True, "embedding": [1.0]},
                  "acme:it#c": {"tenant_id": "acme", "text": "payroll is owned by finance", "source_uri": "gs://b/acme/it.md", "doc_type": "runbook", "current": True},
                  "acme:old#z": {"tenant_id": "acme", "text": "retired words", "source_uri": "gs://b/acme/hr.md", "doc_type": "policy", "current": False},
                  "zeta:hr#q": {"tenant_id": "zeta", "text": "another tenant", "source_uri": "gs://b/zeta/hr.md", "doc_type": "policy", "current": True}}

    class _GDoc:
        def __init__(self, cid): self.exists, self._d = cid in chunk_docs, chunk_docs.get(cid)
        def to_dict(self): return dict(self._d) if self._d else None

    class _GColl(_FQuery):
        def document(self, cid): return SimpleNamespace(get=lambda: _GDoc(cid))
    rns["_fs"] = lambda: SimpleNamespace(collection=lambda name: _GColl() if name == "chunks" else None)
    dense_pool = [{"id": "acme:hr#a", "score": 0.4, "tenant_id": "acme", "source_uri": "gs://b/acme/hr.md", "current": True},
                  {"id": "acme:hr#b", "score": 0.3, "tenant_id": "acme", "source_uri": "gs://b/acme/hr.md", "current": True}]
    real_dense = rns["_dense_retrieve"]                    # restored for the managed-backend tests below
    rns["_dense_retrieve"] = lambda query, tenant_id, top_k, filters=None, vec=None, backend=None: [dict(c) for c in dense_pool]
    graph_answer["seeds"] = [{"node_id": "n_retention", "name": "Data Retention Standard", "kind": "policy"}]
    graph_answer["nodes"] = [{"node_id": "n_retention", "name": "Data Retention Standard", "kind": "policy", "chunk_ids": ["acme:hr#a", "acme:old#z", "nope#0"]},
                             {"node_id": "n_payroll", "name": "Payroll System", "kind": "system", "chunk_ids": ["acme:it#c", "zeta:hr#q"]}]
    q_rel = "Which policies does the Data Retention Standard supersede?"
    settings.retrieval_graph = "on"
    settings.retrieval_current_only = "off"
    got = rns["retrieve"](q_rel, "acme", 5, None, vec=[0.1])
    assert [c["id"] for c in got] == ["acme:hr#a", "acme:it#c", "acme:hr#b"], [c["id"] for c in got]
    assert got[0]["found_by"] == "graph" and got[0]["score"] == 1.0 and "embedding" not in got[0] and "found_by" not in got[2], got
    assert graph_calls[-1] == ("expand", ["n_retention"], "acme", 1, 20) and graph_calls[-2] == ("seed", q_rel, "acme")
    ok("retriever.retrieve(RETRIEVAL_GRAPH=on): the walk's chunks come first (fetched by id, score 1.0, found_by graph, no embedding), a dense chunk already there is not repeated, the rest of the pool follows; another tenant's id, a retired row and an unknown id are dropped")
    got = rns["retrieve"](q_rel, "acme", 5, {"doc_type": "policy"}, vec=[0.1])
    assert [c["id"] for c in got] == ["acme:hr#a", "acme:hr#b"], "the caller's filters apply to the walk's chunks as to every path"
    got = rns["retrieve"](q_rel, "acme", 5, {"doc_type": ["policy", "runbook"]}, vec=[0.1])
    assert [c["id"] for c in got] == ["acme:hr#a", "acme:it#c", "acme:hr#b"], "a doc_type list keeps the walk's rows of any of its classes"
    settings.retrieval_current_only = "on"
    chunk_docs["acme:it#c"]["current"] = None
    got = rns["retrieve"](q_rel, "acme", 5, None, vec=[0.1])
    assert [c["id"] for c in got] == ["acme:hr#a", "acme:hr#b"], "with the ledger's pre-filter on, a row not marked current is not fetched from the graph either"
    chunk_docs["acme:it#c"]["current"] = True
    settings.top_k_retrieve = 2
    assert [c["id"] for c in rns["retrieve"](q_rel, "acme", 5, None, vec=[0.1])] == ["acme:hr#a", "acme:it#c"], "the pool is still cut to TOP_K_RETRIEVE"
    settings.top_k_retrieve = 20
    settings.retrieval_graph = "auto"
    n = len(graph_calls)
    got = rns["retrieve"]("What is the notice period?", "acme", 5, None, vec=[0.1])
    assert [c["id"] for c in got] == ["acme:hr#a", "acme:hr#b"] and [c for c in graph_calls[n:] if c[0] != "init"] == [("seed", "What is the notice period?", "acme")], \
        "auto: a question with no relational word is dense only - seeded, never expanded, no model asked"
    got = rns["retrieve"](q_rel, "acme", 5, None, vec=[0.1])
    assert [c["id"] for c in got] == ["acme:hr#a", "acme:it#c", "acme:hr#b"] and graph_calls[-1][0] == "expand", "auto: relational AND seeded walks"
    graph_answer["seeds"] = []
    n = len(graph_calls)
    got = rns["retrieve"](q_rel, "acme", 5, None, vec=[0.1])
    assert [c["id"] for c in got] == ["acme:hr#a", "acme:hr#b"] and graph_calls[n:][-1][0] == "seed", "a tenant with no graph, or no seed, is the dense answer - never an error"
    settings.retrieval_graph = "on"
    assert [c["id"] for c in rns["retrieve"](q_rel, "acme", 5, None, vec=[0.1])] == ["acme:hr#a", "acme:hr#b"]
    settings.retrieval_graph = "off"
    n = len(graph_calls)
    rns["retrieve"](q_rel, "acme", 5, None, vec=[0.1])
    assert len(graph_calls) == n, "off touches nothing"
    ok("retriever.retrieve(RETRIEVAL_GRAPH=auto): choose_mode() decides from the question and the seeds alone; no seed or no graph is the dense answer; off never constructs the store")

    # GRAPH_BACKEND=spanner (16 September 2026): the same route, seeded by meaning - the question is embedded the graph's
    # way and handed to seed_by_vector with the deployment's k and threshold; containment seed() is never asked. A
    # question about nothing in the graph (no seed within the threshold) is the dense answer, as before.
    settings.graph_backend, settings.retrieval_graph = "spanner", "auto"
    graph_answer["seeds"] = [{"node_id": "n_retention", "name": "Data Retention Standard", "kind": "policy"}]
    n = len(graph_calls)
    got = rns["retrieve"](q_rel, "acme", 5, None, vec=[0.1])
    calls = graph_calls[n:]
    assert calls[0] == ("init", "spanner-db") and calls[1] == ("embed_for_graph", q_rel) and calls[2] == ("seed_by_vector", [0.9, 0.1], "acme", 5, 0.4), calls
    assert not any(c[0] == "seed" for c in calls) and calls[-1][0] == "expand" and [c["id"] for c in got][0] == "acme:hr#a", calls
    graph_answer["seeds"] = []
    n = len(graph_calls)
    assert [c["id"] for c in rns["retrieve"](q_rel, "acme", 5, None, vec=[0.1])] == ["acme:hr#a", "acme:hr#b"] and graph_calls[n:][-1][0] == "seed_by_vector", "no seed within the threshold: dense only"
    graph_answer["seeds"] = [{"node_id": "n_retention", "name": "Data Retention Standard", "kind": "policy"}]
    settings.graph_backend, settings.retrieval_graph = "firestore", "off"
    ok("retriever.graph_candidates(GRAPH_BACKEND=spanner): the Spanner store is built from _spanner_db, the question is embedded for the graph and seeded by meaning with GRAPH_SEED_K / GRAPH_SEED_DISTANCE, containment is never asked, and an empty meaning-seed is the dense answer")

    # ------------------------------------------------------------------ RETRIEVAL_BACKEND=rag_engine (P9.4, 13 September 2026)
    # 4.3's corpus as the retrieval stage: the contexts come back naming their version (the RagFile's display name is the
    # doc_key), the kit's own rows give each one its source, type and a fresh `current`, and the pool is the kit's contract.
    rag_calls, corpora = [], [SimpleNamespace(name="projects/p/locations/us-central1/ragCorpora/7", display_name="documind-acme")]
    contexts = []

    class _Ctx:
        def __init__(self, doc_key, text, distance, pages=None):
            self.source_display_name, self.text, self.score, self.source_uri = doc_key, text, distance, ""
            self.chunk = SimpleNamespace(page_span=SimpleNamespace(first_page=pages[0], last_page=pages[1])) if pages else None

    def _retrieval_query(rag_resources=None, text=None, rag_retrieval_config=None):
        rag_calls.append({"corpus": rag_resources[0].kw["rag_corpus"], "text": text, "config": rag_retrieval_config.kw})
        if isinstance(contexts, Exception):
            raise contexts
        return SimpleNamespace(contexts=SimpleNamespace(contexts=list(contexts)))
    fake_rag = SimpleNamespace(list_corpora=lambda: list(corpora), retrieval_query=_retrieval_query,
                               RagResource=lambda **kw: SimpleNamespace(kw=kw), Filter=lambda **kw: SimpleNamespace(kw=kw),
                               RagRetrievalConfig=lambda **kw: SimpleNamespace(kw={"top_k": kw["top_k"], "threshold": kw["filter"].kw["vector_distance_threshold"]}))
    version_rows = {"acme_s2": {"source_uri": "gs://b/acme/hr.md", "doc_type": "policy", "effective_from": "2026-04-01", "indexed_at": 5, "current": True},
                    "acme_it": {"source_uri": "gs://b/acme/it.md", "doc_type": "runbook", "indexed_at": 4, "current": True},
                    "acme_old": {"source_uri": "gs://b/acme/hr.md", "doc_type": "policy", "indexed_at": 1, "current": False}}
    media_hits = [_Snap("acme:m#0", {"tenant_id": "acme", "text": "a figure of the org chart", "kind": "figure", "doc_type": "figure",
                                      "source_uri": "gs://b/acme/org.png", "current": True, "embedding": [1.0], "d": 0.35})]
    m_seen = []

    class _MQuery:
        def __init__(self, wheres=()): self.wheres = list(wheres)
        def where(self, f, op, v): return _MQuery(self.wheres + [(f, op, v)])
        def limit(self, n): return self
        def stream(self):
            key = next((v for f, op, v in self.wheres if f == "doc_key"), None)
            return [SimpleNamespace(to_dict=lambda k=key: dict(version_rows[k]))] if key in version_rows else []
        def find_nearest(self, field, vec, distance_measure=None, limit=None, distance_result_field="d"):
            m_seen.append({"wheres": self.wheres, "limit": limit})
            return SimpleNamespace(get=lambda: [_Snap(h.id, dict(h._d)) for h in media_hits])
    rns["_fs"] = lambda: SimpleNamespace(collection=lambda name: _MQuery() if name == "chunks" else None)
    rns["_rag"] = lambda: fake_rag
    rns["_dense_retrieve"] = real_dense                    # the real pool again: the backend switch lives in it
    rns["_corpora"].clear()
    fb_calls.clear(); logs.clear()
    settings.retrieval_backend, settings.retrieval_current_only = "rag_engine", "on"
    contexts[:] = [_Ctx("acme_s2", "sixty days of notice", 0.10, (7, 7)), _Ctx("acme_it", "restart the payroll job", 0.30),
                   _Ctx("acme_old", "ninety days of notice", 0.20), _Ctx("acme_s2", "", 0.05), _Ctx("acme_ghost", "a file the ledger never saw", 0.15),
                   _Ctx("acme_s2", "sixty days of notice", 0.10)]
    got = rns["retrieve"]("what is the notice period", "acme", 5, None, vec=[0.1])
    assert rag_calls[-1] == {"corpus": "projects/p/locations/us-central1/ragCorpora/7", "text": "what is the notice period", "config": {"top_k": 20, "threshold": 0.5}}, rag_calls[-1]
    assert [c["id"] for c in got] == ["acme:acme_s2#rag-" + __import__("hashlib").sha256(b"sixty days of notice").hexdigest()[:12],
                                      "acme:acme_s2#rag-" + __import__("hashlib").sha256(b"sixty days of notice").hexdigest()[:12],
                                      "acme:acme_it#rag-" + __import__("hashlib").sha256(b"restart the payroll job").hexdigest()[:12], "acme:m#0"], [c["id"] for c in got]
    top = got[0]
    assert top["found_by"] == "rag_engine" and top["source_uri"] == "gs://b/acme/hr.md" and top["doc_type"] == "policy" and top["doc_key"] == "acme_s2" \
        and top["kind"] == "text" and top["effective_from"] == "2026-04-01" and top["locator"] == "p7" and abs(top["score"] - 0.9) < 1e-9 and top["current"] is True, top
    assert got[3]["kind"] == "figure" and abs(got[3]["score"] - 0.65) < 1e-9 and "embedding" not in got[3], "figures join from the kit's index, scored on the same scale"
    assert m_seen[-1]["wheres"] == [("tenant_id", "==", "acme"), ("current", "==", True), ("kind", "in", ["figure", "segment"])] and m_seen[-1]["limit"] == 5, m_seen[-1]
    assert not fb_calls and not any(l["event"] == "rag_engine_fallback" for l in logs)
    ok("retriever._managed_retrieve: the tenant's corpus by the mirror's name, queried with TOP_K_RETRIEVE and 4.3's threshold; each context becomes a chunk of the contract through its version's row (source, type, date, a fresh current), with a stable id, a page locator and 1 - distance as the score; a retired version, an empty context and a file the ledger never saw are dropped; figures and segments join from the kit's index under the current + kind index")
    got = rns["retrieve"]("q", "acme", 5, {"doc_type": "policy"}, vec=[0.1])
    assert [c["doc_key"] for c in got if c.get("found_by") == "rag_engine"] == ["acme_s2", "acme_s2"] and not any(c.get("kind") == "figure" for c in got), \
        "the caller's doc_type applies to the store's chunks and to the media rows alike"
    got = rns["retrieve"]("q", "acme", 5, {"doc_type": ["figure", "runbook"]}, vec=[0.1])
    assert [c["doc_key"] for c in got if c.get("found_by") == "rag_engine"] == ["acme_it"] and [c["id"] for c in got if c.get("kind") == "figure"] == ["acme:m#0"], \
        "a doc_type list keeps the store's chunks and the media rows of any of its classes"
    m_seen.clear()
    got = rns["retrieve"]("q", "acme", 5, {"kind": "text"}, vec=[0.1])
    assert all(c["kind"] == "text" for c in got) and not m_seen, "kind=text: the store alone, no media query"
    got = rns["retrieve"]("q", "acme", 5, {"kind": "figure"}, vec=[0.1])
    assert [c["id"] for c in got] == ["acme:m#0"] and m_seen[-1]["wheres"][-1] == ("kind", "==", "figure") and m_seen[-1]["limit"] == 20, \
        "kind=figure: the store has none, the kit's index answers alone at full depth"
    settings.top_k_retrieve = 2
    got = rns["retrieve"]("q", "acme", 5, None, vec=[0.1])
    assert len(got) == 2 and rag_calls[-1]["config"]["top_k"] == 2, "the pool is cut to TOP_K_RETRIEVE, which is also what the store is asked for"
    settings.top_k_retrieve = 20
    ok("retriever._managed_retrieve: doc_type and kind filters apply to the store's chunks and the media rows as on every path; kind=text asks no media, kind=figure asks the store nothing; the pool is cut to TOP_K_RETRIEVE")
    corpora.clear(); rns["_corpora"].clear(); logs.clear()
    got = rns["retrieve"]("q", "zeta", 5, {"doc_type": "policy"}, vec=[0.1])
    assert fb_calls[-1] == ([0.1], "zeta", 20, {"doc_type": "policy"}) and logs[-1]["event"] == "rag_engine_fallback" and "make rag-corpus TENANT=zeta" in logs[-1]["reason"], \
        "a tenant without a corpus is the Firestore rung with the filters, and the line says how to get a corpus"
    corpora.append(SimpleNamespace(name="projects/p/locations/us-central1/ragCorpora/7", display_name="documind-acme"))
    contexts = RuntimeError("503 RAG Engine is unavailable")
    logs.clear()
    got = rns["retrieve"]("q", "acme", 5, None, vec=[0.1])
    assert fb_calls[-1] == ([0.1], "acme", 20, None) and logs[-1]["event"] == "rag_engine_fallback" and "503" in logs[-1]["error"], "a store that will not answer is the Firestore rung, logged"
    contexts = []
    ok("retriever._managed_retrieve: no corpus for the tenant, or a store that raises, is the Firestore fallback with the caller's filters and one rag_engine_fallback line - never an empty pool that reads as a refusal")

    # ------------------------------------------------------------------ RETRIEVAL_BACKEND=vertex_search (R4, 13 September 2026 evening)
    # 4.4's data store as the retrieval stage: the store ranks and extracts (segments when it serves them, else the snippet),
    # the kit's own rows give each result its source, type and a fresh `current`, and the pool is the kit's contract.
    search_calls, search_results = [], []

    class _SpecObj:
        def __init__(self, **kw): self.kw = kw

    class _CSS(_SpecObj):
        SnippetSpec, ExtractiveContentSpec = _SpecObj, _SpecObj

    class _SR(_SpecObj):
        ContentSearchSpec = _CSS

    class _SDoc:
        def __init__(self, id, derived): self.id, self._d = id, {"id": id, "derived_struct_data": derived}
        @staticmethod
        def to_dict(d): return dict(d._d)

    def _search_fn(request=None):
        search_calls.append(request.kw)
        if isinstance(search_results, Exception):
            raise search_results
        return iter([SimpleNamespace(document=d) for d in search_results])
    rns["discoveryengine"] = SimpleNamespace(RankingRecord=lambda **kw: kw, RankRequest=lambda **kw: kw, SearchRequest=_SR, Document=_SDoc)
    rns["_search"] = lambda: SimpleNamespace(search=_search_fn)
    fb_calls.clear(); logs.clear(); m_seen.clear()
    settings.retrieval_backend = "vertex_search"
    vs = lambda key, text: f"acme:{key}#vs-" + __import__("hashlib").sha256(text.encode()).hexdigest()[:12]
    search_results[:] = [_SDoc("acme_s2", {"extractive_segments": [{"content": "sixty days of notice", "pageNumber": "7"}, {"content": "  ", "pageNumber": "8"}, {"content": "ninety for directors", "pageNumber": "9"}]}),
                         _SDoc("acme_it", {"snippets": [{"snippet": "restart the <b>payroll</b> job", "snippet_status": "SUCCESS"}]}),
                         _SDoc("acme_ghost", {"snippets": [{"snippet": "a file the ledger never saw"}]}),
                         _SDoc("acme_old", {"snippets": [{"snippet": "ninety days of notice"}]}),
                         _SDoc("acme_s2", {}), _SDoc("", {"snippets": [{"snippet": "no id"}]})]
    got = rns["retrieve"]("what is the notice period", "acme", 5, None, vec=[0.1])
    req = search_calls[-1]
    assert req["serving_config"] == "projects/demo/locations/global/collections/default_collection/dataStores/documind-acme/servingConfigs/default_search" \
        and req["query"] == "what is the notice period" and req["page_size"] == 20 and req["filter"] == "", req
    assert req["content_search_spec"].kw["snippet_spec"].kw == {"return_snippet": True} and req["content_search_spec"].kw["extractive_content_spec"].kw == {"max_extractive_segment_count": 3}, "snippets and segments both asked, as 4.4's cell asks"
    assert [c["id"] for c in got] == [vs("acme_s2", "sixty days of notice"), vs("acme_s2", "ninety for directors"), vs("acme_it", "restart the payroll job"), "acme:m#0"], [c["id"] for c in got]
    top = got[0]
    assert top["found_by"] == "vertex_search" and top["source_uri"] == "gs://b/acme/hr.md" and top["doc_type"] == "policy" and top["doc_key"] == "acme_s2" and top["kind"] == "text" \
        and top["effective_from"] == "2026-04-01" and top["locator"] == "p7" and top["score"] == 1.0 and top["current"] is True, top
    assert got[1]["locator"] == "p9" and abs(got[1]["score"] - 0.99) < 1e-9 and got[2]["text"] == "restart the payroll job" and got[2]["locator"] == "" and abs(got[2]["score"] - 0.98) < 1e-9, "segments in the store's order, the snippet's markup stripped, the rank as the score"
    assert got[3]["kind"] == "figure" and m_seen[-1]["limit"] == 5 and not fb_calls and not logs, "figures join from the kit's index; the store answered, so no fallback"
    ok("retriever._search_retrieve: the tenant's data store by the mirror's id through its default serving config, asked for TOP_K_RETRIEVE results with snippets and extractive segments; each segment (else the snippet, markup stripped) becomes a chunk of the contract through its version's row; an unknown document, a retired version and a result without an id are dropped; media joins from the kit's index")
    got = rns["retrieve"]("q", "acme", 5, {"doc_type": "policy"}, vec=[0.1])
    assert search_calls[-1]["filter"] == 'doc_type: ANY("policy")' and [c["doc_key"] for c in got if c.get("found_by") == "vertex_search"] == ["acme_s2", "acme_s2"] and not any(c.get("kind") == "figure" for c in got), \
        "the caller's doc_type goes to the store as a filter expression and applies to the mapped chunks and the media rows alike"
    got = rns["retrieve"]("q", "acme", 5, {"doc_type": ["policy", "runbook"], "kind": "text"}, vec=[0.1])
    assert search_calls[-1]["filter"] == 'doc_type: ANY("policy", "runbook")' and [c["doc_key"] for c in got] == ["acme_s2", "acme_s2", "acme_it"], \
        "a doc_type list is one ANY() of its classes at the store, and the same set on the mapped chunks"
    assert rns["_search_filter"]({"doc_type": ['a"b', "c"]}) == 'doc_type: ANY("a\\"b", "c")' and rns["_search_filter"]({"doc_type": 'a"b'}) == 'doc_type: ANY("a\\"b")', "a quote inside a class is escaped, listed or not"
    assert rns["_search_filter"]({"doc_type": ["a\\", "b"]}) == 'doc_type: ANY("a\\\\", "b")', "a backslash is escaped first, so it cannot eat the closing quote and run into the next class"
    m_seen.clear()
    got = rns["retrieve"]("q", "acme", 5, {"kind": "text"}, vec=[0.1])
    assert search_calls[-1]["filter"] == "" and all(c["kind"] == "text" for c in got) and not m_seen, "kind never reaches the store; kind=text asks no media"
    n = len(search_calls)
    got = rns["retrieve"]("q", "acme", 5, {"kind": "figure"}, vec=[0.1])
    assert [c["id"] for c in got] == ["acme:m#0"] and len(search_calls) == n and m_seen[-1]["limit"] == 20, "kind=figure: the store is not asked, the kit's index answers alone at full depth"
    search_results[:] = []
    got = rns["retrieve"]("q", "acme", 5, {"kind": "text"}, vec=[0.1])
    assert got == [] and not fb_calls and not any(l["event"] == "vertex_search_fallback" for l in logs), "no results is an empty pool: the store answered"
    settings.top_k_retrieve = 2
    search_results[:] = [_SDoc("acme_s2", {"extractive_segments": [{"content": "a"}, {"content": "b"}, {"content": "c"}]})]
    got = rns["retrieve"]("q", "acme", 5, {"kind": "text"}, vec=[0.1])
    assert search_calls[-1]["page_size"] == 2 and len(got) == 2, "the pool is cut to TOP_K_RETRIEVE, which is also what the store is asked for"
    settings.top_k_retrieve = 20
    search_results = RuntimeError("404 data store documind-zeta not found")
    logs.clear()
    got = rns["retrieve"]("q", "zeta", 5, {"doc_type": "policy"}, vec=[0.1])
    assert fb_calls[-1] == ([0.1], "zeta", 20, {"doc_type": "policy"}) and logs[-1]["event"] == "vertex_search_fallback" and "404" in logs[-1]["error"] and "MANAGED_SEARCH=true" in logs[-1]["hint"], \
        "a tenant with no data store, or a store that will not answer, is the Firestore rung with the filters, and the line says how to get a store"
    search_results = []
    ok("retriever._search_retrieve: doc_type (a class, or a list as one ANY()) as a filter expression and once more on the chunks; kind is the kit's; no results is an empty pool; the pool is cut to TOP_K_RETRIEVE; no store or an error is the Firestore fallback with the filters and one vertex_search_fallback line")
    settings.retrieval_backend, settings.retrieval_current_only = "vector", "on"
    rns["_fs"] = lambda: SimpleNamespace(collection=lambda name: _GColl() if name == "chunks" else None)

    class _RankClient:
        def __init__(self, fail=None): self.fail, self.calls = fail, []
        def ranking_config_path(self, **kw): return "projects/demo/locations/global/rankingConfigs/default_ranking_config"
        def rank(self, request=None, timeout=None):
            self.calls.append({"timeout": timeout, "request": request})
            if self.fail:
                raise self.fail
            return SimpleNamespace(records=[SimpleNamespace(id="1", score=0.9), SimpleNamespace(id="0", score=0.4)])

    pool = [{"id": "a", "text": "A", "score": 0.5}, {"id": "b", "text": "B", "score": 0.9}, {"id": "c", "text": "C", "score": 0.7}]
    client = _RankClient()
    rns["_ranker"] = lambda: client
    out = rns["rerank"]("q", [dict(c) for c in pool], 2, tenant_id="acme")
    assert [c["id"] for c in out] == ["b", "a"] and out[0]["rerank_score"] == 0.9 and not rns["rerank_fell_back"](out)
    assert client.calls[-1]["timeout"] == 5.0, "the Ranking API call must carry settings.rerank_timeout_s as gapic's timeout"
    assert client.calls[-1]["request"]["top_n"] == 2 and client.calls[-1]["request"]["model"] == "semantic-ranker-fast-004"
    client = _RankClient(fail=TimeoutError("Deadline of 5.0s exceeded"))
    rns["_ranker"] = lambda: client
    out = rns["rerank"]("q", [dict(c) for c in pool], 2, tenant_id="acme")
    assert [c["id"] for c in out] == ["b", "c"], "the fallback is the pool by retrieval score, cut to k"
    assert rns["rerank_fell_back"](out) and all(c.get("rerank_fallback") is True and "rerank_score" not in c for c in out)
    assert logs[-1] == {"event": "rerank_fallback", "tenant": "acme", "error": "TimeoutError"}, logs[-1]
    rns["_ranker"] = lambda: (_ for _ in ()).throw(ImportError("no discoveryengine"))
    out = rns["rerank"]("q", [dict(c) for c in pool], 5, tenant_id="acme")
    assert [c["id"] for c in out] == ["b", "c", "a"] and logs[-1]["error"] == "ImportError", "a client that will not build is the same fallback"
    assert rns["rerank"]("q", [], 5) == [] and not rns["rerank_fell_back"]([])
    ok("retriever.rerank: the Ranking API call has the configured deadline; a deadline, a quota or a missing client returns the pool by retrieval score cut to k with every row marked, and logs rerank_fallback with the tenant and the error type")

    # ------------------------------------------------------------------ config.py: hybrid needs Vector Search, at startup
    import pydantic
    cfg_src = read("deploy/services/rag-api/config.py")
    fake_ps = types.ModuleType("pydantic_settings")
    fake_ps.BaseSettings, fake_ps.SettingsConfigDict = pydantic.BaseModel, (lambda **kw: {"extra": kw.get("extra", "ignore")})
    real_ps = sys.modules.get("pydantic_settings")
    sys.modules["pydantic_settings"] = fake_ps           # the same class, the same validator, without the env layer
    cns = {}
    try:
        for node in ast.parse(cfg_src).body:
            if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "settings" for t in node.targets):
                continue                                 # settings = Settings() needs the environment; the class is enough
            exec(ast.get_source_segment(cfg_src, node), cns)
    finally:
        if real_ps is not None:
            sys.modules["pydantic_settings"] = real_ps
        else:
            sys.modules.pop("pydantic_settings", None)
    S = cns["Settings"]
    assert S(GOOGLE_CLOUD_PROJECT="demo").retrieval_mode == "dense" and S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_BACKEND="firestore").retrieval_backend == "firestore"
    assert S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_BACKEND="vector", retrieval_mode="hybrid").retrieval_mode == "hybrid"
    # P9.4: the managed backend is refused with hybrid (no sparse leg to fuse). NOT refused by a residency variable since
    # 13 September 2026 (evening): whether a tenant may be served from the store is its data_region, judged per request
    assert S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_BACKEND="rag_engine").retrieval_backend == "rag_engine"
    assert S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_BACKEND="rag_engine", RAG_LOCATION="us-central1", RAG_DISTANCE_THRESHOLD="0.4").rag_distance_threshold == 0.4
    try:
        S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_BACKEND="rag_engine", retrieval_mode="hybrid")
        raise AssertionError("rag_engine with hybrid was accepted")
    except pydantic.ValidationError as e:
        assert "RETRIEVAL_MODE=dense" in str(e), str(e)
    assert S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_BACKEND="rag_engine", RESIDENCY="india").retrieval_backend == "rag_engine" \
        and not hasattr(S(GOOGLE_CLOUD_PROJECT="demo"), "residency"), "residency is the tenant's policy, not a startup refusal or a setting"
    assert "residency" not in cns["check_retrieval_modes"].__code__.co_varnames[:cns["check_retrieval_modes"].__code__.co_argcount]
    # R4: the fourth backend, 4.4's data store, with the same hybrid refusal and its own two settings
    assert S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_BACKEND="vertex_search").retrieval_backend == "vertex_search" and S(GOOGLE_CLOUD_PROJECT="demo").search_location == "global" \
        and S(GOOGLE_CLOUD_PROJECT="demo", SEARCH_SEGMENTS="5").search_segments == 5 and cns["MANAGED_BACKENDS"] == ("rag_engine", "vertex_search")
    try:
        S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_BACKEND="vertex_search", retrieval_mode="hybrid")
        raise AssertionError("vertex_search with hybrid was accepted")
    except pydantic.ValidationError as e:
        assert "RETRIEVAL_MODE=dense" in str(e), str(e)
    try:
        S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_BACKEND="firestore", retrieval_mode="hybrid")
        raise AssertionError("RETRIEVAL_MODE=hybrid on the Firestore backend was accepted - it runs dense and reports hybrid")
    except pydantic.ValidationError as e:
        assert "RETRIEVAL_BACKEND=vector" in str(e) and "RETRIEVAL_MODE=dense" in str(e), "the refusal must name the fix"
    try:
        S(GOOGLE_CLOUD_PROJECT="demo", retrieval_mode="hybird")
        raise AssertionError("an unknown RETRIEVAL_MODE was accepted - it runs dense")
    except pydantic.ValidationError as e:
        assert "dense|hybrid" in str(e)
    # 4.6's graph switch (13 September 2026): off by default, on | auto accepted, anything else refused with the three named
    assert S(GOOGLE_CLOUD_PROJECT="demo").retrieval_graph == "off" and S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_GRAPH="auto").retrieval_graph == "auto"
    assert S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_GRAPH="on", GRAPH_HOPS="2", GRAPH_CAP="10").graph_hops == 2 and S(GOOGLE_CLOUD_PROJECT="demo").graph_cap == 20
    try:
        S(GOOGLE_CLOUD_PROJECT="demo", RETRIEVAL_GRAPH="yes")
        raise AssertionError("an unknown RETRIEVAL_GRAPH was accepted - it would run dense and report a graph")
    except pydantic.ValidationError as e:
        assert "off|on|auto" in str(e) and "choose_mode" in str(e), "the refusal names the three modes and what auto does"
    assert S(GOOGLE_CLOUD_PROJECT="demo").rerank_timeout_s == 5.0 and S(GOOGLE_CLOUD_PROJECT="demo", RERANK_TIMEOUT_S="2.5").rerank_timeout_s == 2.5
    assert 'rerank_timeout_s: float = Field(5.0, alias="RERANK_TIMEOUT_S")' in cfg_src
    if importlib.util.find_spec("pydantic_settings"):
        r = subprocess.run([sys.executable, "-c", "import config"], cwd=API, capture_output=True, text=True,
                           env={**os.environ, "GOOGLE_CLOUD_PROJECT": "demo", "RETRIEVAL_BACKEND": "firestore", "RETRIEVAL_MODE": "hybrid"})
        assert r.returncode != 0 and "RETRIEVAL_BACKEND=vector" in r.stderr, "the service started with hybrid on the Firestore backend"
        r = subprocess.run([sys.executable, "-c", "import config"], cwd=API, capture_output=True, text=True,
                           env={**os.environ, "GOOGLE_CLOUD_PROJECT": "demo", "RETRIEVAL_BACKEND": "firestore", "RETRIEVAL_MODE": "dense"})
        assert r.returncode == 0, r.stderr[-300:]
        ok("config.py, from the environment: RETRIEVAL_BACKEND=firestore RETRIEVAL_MODE=hybrid fails the import with the fix in the message; dense starts")
    else:
        skip("pydantic-settings not installed: config.py's refusal exercised on the class, not from the environment")
    main_src = read("deploy/services/rag-api/main.py")
    fns = {n.name: ast.unparse(n) for n in ast.parse(main_src).body if isinstance(n, ast.FunctionDef)}
    assert "'retrieval_mode': settings.retrieval_mode" in fns["version"] and "'retrieval_graph': settings.retrieval_graph" in fns["version"], "/version reports the effective mode and the graph switch"
    assert "'retrieval_backend': settings.retrieval_backend" in fns["version"] and "'retrieval_backend': retrieval_backend or settings.retrieval_backend" in fns["usage_row"] \
        and "'managed_chunks': stages.get('managed_chunks', 0)" in fns["usage_row"] and "'policy_fallback': stages.get('policy_fallback', 0)" in fns["usage_row"], \
        "/version says the default store; the row says the store that served the pool and whether the tenant's policy chose it"
    ok("config.py: Settings refuses RETRIEVAL_MODE=hybrid with RETRIEVAL_BACKEND=firestore, an unknown mode and an unknown RETRIEVAL_GRAPH, naming the fix; RERANK_TIMEOUT_S, GRAPH_HOPS and GRAPH_CAP are settings; /version reports the mode and the switch that passed")

    # ------------------------------------------------------------------ main.py: the handlers, lifted, against fakes
    schemas = load(os.path.join(API, "schemas.py"), "schemas_under_test")
    assert schemas.FILTER_KEYS == ("doc_type", "kind") and schemas.RAGResponse.model_fields["cached_tokens"].default == 0
    mlog, stored, recorded, calls, gen_seen, gs_seen = [], [], [], {"rerank": 0, "generate": 0, "stream": 0}, [], []
    msettings = SimpleNamespace(semantic_cache="off", armor="off", generator_model="gemini-3.6-flash", model_backend="vertex",
                                prompt_id="documind-rag", prompt_version="v3", retrieval_mode="dense", retrieval_graph="off", retrieval_backend="firestore")
    cache = SimpleNamespace(lookup=lambda *a, **k: None, store=lambda *a, **k: stored.append(a), scope_of=lambda f, k, v: "scope")
    mns = {"time": time, "json": json, "contextmanager": contextmanager, "HTTPException": _HTTPException, "Depends": lambda f: None,
           "verify_iap": None, "StreamingResponse": lambda gen, media_type=None: gen, "QueryRequest": schemas.QueryRequest,
           "tracer": SimpleNamespace(start_as_current_span=lambda name: nullcontext()),
           "FILTER_KEYS": schemas.FILTER_KEYS, "RAGResponse": schemas.RAGResponse, "RAGAnswer": schemas.RAGAnswer, "settings": msettings,
           "MANAGED_BACKENDS": cns["MANAGED_BACKENDS"],
           "log": SimpleNamespace(info=lambda s: mlog.append(json.loads(s)), warning=lambda s: mlog.append(json.loads(s))),
           "price": lambda model, i, o, cached=0: {"usd": ((i - cached) * 1.5 + cached * 0.15 + o * 7.5) / 1e6},
           "enforce_membership": lambda email, tenant: None, "choose_for": lambda req: ("vertex", "gemini-3.6-flash", "firestore"),
           "retrieval_backend_for": lambda tenant_id, backend: (backend, 0),
           "screen_prompt": lambda q, t: "off", "screen_response": lambda text, guard: (guard, ""), "_fingerprint": lambda t: "fp1",
           "embed_query": lambda q: [0.1, 0.2], "_record": lambda usd: recorded.append(usd), "_fs": lambda: None, "semantic_cache": cache,
           "rerank_fell_back": rns["rerank_fell_back"], "__builtins__": __builtins__}
    lift(main_src, mns, names=("_ms", "stage", "modality_of", "check_filters", "empty_pool_answer", "usage_row", "_semantic_hit", "_semantic_store", "query", "stream", "passages"),
         bare=("query", "stream", "passages"), assigns=("EMPTY_POOL_ANSWER",))
    user = {"email": "a@acme.example"}
    req = schemas.QueryRequest(query="what is the notice period?", tenant_id="acme")

    cf = mns["check_filters"]
    for good in (None, {}, {"doc_type": "policy"}, {"kind": "figure"}, {"doc_type": "invoice", "kind": "table"}):
        cf(good)
    for bad in ({"tenant_id": "zeta"}, {"current": "true"}, {"doctype": "policy"}, {"doc_type": "policy", "owner": "x"}):
        try:
            cf(bad)
            raise AssertionError(f"filters {bad} were accepted")
        except _HTTPException as e:
            assert e.status_code == 400 and "doc_type" in e.detail and "kind" in e.detail, (bad, e.detail)
    try:
        cf({"doc_type": 3})
        raise AssertionError("a non-string filter value was accepted")
    except _HTTPException as e:
        assert e.status_code == 400
    # A doc_type list (workshop lesson 10.6): 1 to 5 non-empty strings, made canonical in place - sorted, de-duplicated,
    # one class as its string - so scope_of, which sorts keys and not list values, hashes one form for one set.
    for sent, canon in (({"doc_type": ["statute", "guidance"]}, {"doc_type": ["guidance", "statute"]}),
                        ({"doc_type": ["guidance", "statute", "guidance"], "kind": "text"}, {"doc_type": ["guidance", "statute"], "kind": "text"}),
                        ({"doc_type": ["policy"]}, {"doc_type": "policy"}), ({"doc_type": ["policy", "policy"]}, {"doc_type": "policy"}),
                        ({"doc_type": ["a", "b", "c", "d", "e"]}, {"doc_type": ["a", "b", "c", "d", "e"]})):
        cf(sent)
        assert sent == canon, (sent, canon)
    sc_ns = {"hashlib": __import__("hashlib"), "json": json}
    lift(read("deploy/services/rag-api/semantic_cache.py"), sc_ns, names=("scope_of",))
    scopes = set()
    for sent in ({"doc_type": ["guidance", "statute"]}, {"doc_type": ["statute", "guidance"]}, {"doc_type": ["statute", "guidance", "statute"]}):
        cf(sent)
        scopes.add(sc_ns["scope_of"](sent, 5, "v3"))
    one, scalar = {"doc_type": ["policy"]}, {"doc_type": "policy"}
    cf(one); cf(scalar)
    assert len(scopes) == 1 and sc_ns["scope_of"](one, 5, "v3") == sc_ns["scope_of"](scalar, 5, "v3") != scopes.pop(), \
        "one set of classes is one cache scope, in any order or repetition; a one-class list is the scalar's scope"
    for bad in ({"doc_type": ["a", "b", "c", "d", "e", "f"]}, {"doc_type": []}, {"doc_type": ["statute", 3]}, {"doc_type": ["statute", ""]},
                {"doc_type": ["statute", None]}, {"doc_type": [["statute"]]}, {"doc_type": ""}):
        try:
            cf(bad)
            raise AssertionError(f"filters {bad} were accepted")
        except _HTTPException as e:
            assert e.status_code == 400 and e.detail == "filter doc_type must be a non-empty string or a list of 1 to 5 of them", (bad, e.detail)
    for bad in ({"kind": ["figure"]}, {"kind": ["figure", "segment"]}, {"doc_type": ["statute"], "kind": ["text"]}):
        try:
            cf(bad)
            raise AssertionError(f"filters {bad} were accepted")
        except _HTTPException as e:
            assert e.status_code == 400 and e.detail == "filter kind takes one string, not a list: only doc_type takes a list", (bad, e.detail)
    try:
        cf({"kind": 3})
        raise AssertionError("a non-string kind was accepted")
    except _HTTPException as e:
        assert e.status_code == 400 and e.detail == "filter kind must be a non-empty string", e.detail
    for handler in ("query", "stream"):
        try:
            mns[handler](schemas.QueryRequest(query="q", tenant_id="acme", filters={"tenant_id": "zeta"}), user=user)
            raise AssertionError(f"{handler} served a request with an unknown filter key")
        except _HTTPException as e:
            assert e.status_code == 400
        assert "check_filters(req.filters)" in fns[handler] and fns[handler].index("check_filters(") < fns[handler].index("embed_query("), handler
    ok("main.py: an unknown filter key (tenant_id, current, a typo) or a non-string value is a 400 on /v1/query and /v1/stream before any work; doc_type and kind pass")
    ok("main.check_filters: a doc_type list of 1 to 5 non-empty strings passes, made canonical in place (sorted, de-duplicated, one class as its string) so scope_of hashes one form per set; six classes, an empty list or a non-string member is a 400; a kind list is a 400 that says only doc_type takes a list")

    msettings.semantic_cache = "on"                  # the store path runs for real: it must refuse the refusal on its own
    mns["retrieve"] = lambda *a, **k: []
    mns["rerank"] = lambda q, chunks, k, tenant_id=None: calls.__setitem__("rerank", calls["rerank"] + 1) or chunks[:k]
    mns["generate"] = lambda *a, **k: calls.__setitem__("generate", calls["generate"] + 1)
    mns["generate_stream"] = lambda *a, **k: calls.__setitem__("stream", calls["stream"] + 1) or iter(())
    ans = mns["query"](req, user=user)
    assert calls == {"rerank": 0, "generate": 0, "stream": 0}, "an empty pool reached the reranker or the model"
    assert ans.answerable is False and ans.citations == [] and ans.confidence == "low" and ans.backend == "none" and ans.cache_hit == "none"
    assert ans.tokens_in == 0 and ans.tokens_out == 0 and ans.cost_usd == 0.0 and "nothing" in ans.answer.lower()
    assert ans.stages["pool"] == 0 and ans.stages["rerank_ms"] == 0 and ans.stages["generate_ms"] == 0 and "retrieve_ms" in ans.stages
    assert not stored, "a refusal was stored in the answer cache"
    row = mlog[-1]
    assert row["event"] == "query" and row["answerable"] is False and row["unanswerable_flag"] == 1 and row["cost_usd"] == 0 and row["tokens_in"] == 0
    assert row["model_backend"] == "none" and row["rerank_fallback"] == 0 and row["pool"] == 0 and recorded[-1] == 0.0
    events = _sse(list(mns["stream"](req, user=user)))
    assert calls == {"rerank": 0, "generate": 0, "stream": 0}, "the stream's empty pool reached the reranker or the model"
    assert [e for e, _ in events] == ["token", "done"] and "nothing" in events[0][1]["t"].lower(), [e for e, _ in events]
    done = events[-1][1]
    assert done["backend"] == "none" and done["cache_hit"] == "none" and done["tokens_in"] == 0 and done["tokens_out"] == 0 and done["cost_usd"] == 0.0
    assert done["stages"]["pool"] == 0 and done["stages"]["rerank_ms"] == 0 and done["stages"]["generate_ms"] == 0 and "retrieve_ms" in done["stages"]
    row = mlog[-1]
    assert row["event"] == "stream" and row["answerable"] is False and row["unanswerable_flag"] == 1 and row["cost_usd"] == 0 and row["model_backend"] == "none"
    assert not stored and recorded[-1] == 0.0
    ok("main.py: an empty pool is a refusal on both routes - no rerank, no model call, no cache store, backend none, zero tokens and cost, rerank_ms / generate_ms 0; the stream sends one token then done; both rows say answerable=False")
    seen_f, real_retrieve = [], mns["retrieve"]
    mns["retrieve"] = lambda q, t, k, filters=None, **kw: seen_f.append(filters) or []
    mns["query"](schemas.QueryRequest(query="q", tenant_id="acme", filters={"doc_type": ["statute", "guidance", "statute"]}), user=user)
    list(mns["stream"](schemas.QueryRequest(query="q", tenant_id="acme", filters={"doc_type": ["guidance"]}), user=user))
    assert seen_f == [{"doc_type": ["guidance", "statute"]}, {"doc_type": "guidance"}], seen_f
    mns["retrieve"] = real_retrieve
    ok("main.py: both routes hand retrieve() the canonical doc_type set check_filters made, the one the cache scope hashed")

    # ------------------------------------------------------------------ main.py: /v1/passages (workshop lesson 10.6)
    # The retrieval half of /v1/query: the full text of each passage, no model call, no answer cache, no month counter.
    clause = "Either party may end the employment with sixty days' written notice, served on the last working day of a month. "
    pool = [{"id": "acme:hr#np03", "text": clause * 3, "source_uri": "gs://b/acme/hr_policy_2026.md", "page_start": None, "doc_type": "policy",
             "kind": "text", "section": "NP-03 Notice period", "found_by": "vector"},
            {"id": "acme:hr#lv01", "text": "Leave accrues monthly.", "source_uri": "gs://b/acme/hr_policy_2026.md", "page_start": 2, "doc_type": "policy",
             "kind": "text", "found_by": "firestore"}]
    pfns = fns["passages"]
    assert pfns.index("check_filters(") < pfns.index("retrieve(") and pfns.index("screen_prompt(") < pfns.index("retrieve(") \
        and pfns.index("enforce_membership(") < pfns.index("check_filters("), "membership, filters and the prompt screen before any retrieval"
    assert not any(w in pfns for w in ("generate(", "generate_stream(", "_semantic", "_fingerprint", "embed_query", "_record(")), "no model, no answer cache, no month counter"
    calls.update(rerank=0, generate=0, stream=0)
    stored.clear()
    seen_p, n_rec = [], len(recorded)
    mns["retrieve"] = lambda q, t, k, filters=None, **kw: seen_p.append((filters, kw.get("backend"))) or [dict(c) for c in pool]
    mns["rerank"] = lambda q, chunks, k, tenant_id=None: calls.__setitem__("rerank", calls["rerank"] + 1) or chunks[:k]
    got = mns["passages"](schemas.QueryRequest(query="what is the notice period?", tenant_id="acme", filters={"doc_type": ["policy", "policy"]}), user=user)
    first = got["passages"][0]
    assert calls == {"rerank": 1, "generate": 0, "stream": 0} and not stored and len(recorded) == n_rec, (calls, stored)
    assert seen_p[-1] == ({"doc_type": "policy"}, "firestore"), seen_p[-1]
    assert [p["n"] for p in got["passages"]] == [1, 2] and set(first) == {"n", "chunk_id", "source_uri", "page", "doc_type", "kind", "section", "text"}
    assert first["text"] == clause * 3 and len(first["text"].split()) > 25 and len(first["text"]) > 240, "the whole chunk, longer than a quote"
    assert (first["chunk_id"], first["section"], got["passages"][1]["section"], got["passages"][1]["page"]) == ("acme:hr#np03", "NP-03 Notice period", None, 2)
    assert "answer" not in got and got["answerable"] is True
    assert got["usage"]["tokens_in"] == got["usage"]["tokens_out"] == 0 and got["usage"]["cost_usd"] == 0.0 and got["usage"]["model"] == "none"
    assert got["usage"]["stages"]["pool"] == 2 and got["usage"]["stages"]["generate_ms"] == 0 and "rerank_ms" in got["usage"]["stages"]
    row = mlog[-1]
    assert row["event"] == "passages" and row["surface"] == "passages" and row["tokens_out"] == 0 and row["cost_usd"] == 0 and row["model"] == "none"
    assert row["model_backend"] == "none" and row["answerable"] is True and row["unanswerable_flag"] == 0 and row["pool"] == 2 and row["retrieval_backend"] == "firestore"
    mns["retrieve"] = lambda *a, **k: []
    got = mns["passages"](req, user=user)
    assert got["passages"] == [] and got["answerable"] is False and calls["rerank"] == 1 and mlog[-1]["answerable"] is False, "an empty pool: nothing to rank"
    try:
        mns["retrieve"] = lambda *a, **k: (_ for _ in ()).throw(AssertionError("retrieved with a bad filter"))
        mns["passages"](schemas.QueryRequest(query="q", tenant_id="acme", filters={"tenant_id": "zeta"}), user=user)
        raise AssertionError("passages served a request with an unknown filter key")
    except _HTTPException as e:
        assert e.status_code == 400
    mns["retrieve"], mns["rerank"] = real_retrieve, (lambda q, chunks, k, tenant_id=None: chunks[:k])
    ok("main.py: /v1/passages checks membership, filters and the prompt before retrieval, ranks the pool and returns each chunk's full text (n, chunk_id, "
       "source_uri, page, doc_type, kind, section, text) with no model call, no answer cache and no month counter; the row is event passages, 0 tokens, Rs 0; "
       "an empty pool is passages [] and answerable False")

    # ------------------------------------------------------------------ the per-tenant backend and the data-region policy (13 September 2026, evening)
    # choose_for honours tenant_settings.retrieval_backend; retrieval_backend_for holds it against data_region: a managed
    # store for a tenant whose text may not leave India is the kit's own index with policy_fallback=1 - never the store,
    # never a 500 - and the row carries the backend that served. The policy's normalisation is shared/tenancy.policy_of.
    tdocs, treads, tlog = {"acme": {"data_region": "any", "retrieval_backend": "rag_engine"}, "globex": {"data_region": "in", "retrieval_backend": "rag_engine"},
                            "zeta": {"data_region": "any"}, "typo": {"data_region": "ANY ", "retrieval_backend": "bogus"}}, [], []

    class _TSnap:
        def __init__(self, tid): self.exists, self._d = tid in tdocs, tdocs.get(tid, {})
        def to_dict(self): return dict(self._d)

    class _TDoc:
        def __init__(self, tid): self.tid = tid
        def get(self):
            treads.append(self.tid)
            if self.tid == "broken":
                raise RuntimeError("Firestore unavailable")
            return _TSnap(self.tid)
    tns = {"time": time, "json": json, "settings": msettings, "choose_model_for": lambda q: "gemini-3.6-flash",
           "RETRIEVAL_BACKENDS": cns["RETRIEVAL_BACKENDS"], "MANAGED_BACKENDS": cns["MANAGED_BACKENDS"],
           "log": SimpleNamespace(info=lambda s: tlog.append(json.loads(s)), warning=lambda s: tlog.append(json.loads(s))),
           "_fs": lambda: SimpleNamespace(collection=lambda name: SimpleNamespace(document=_TDoc) if name == "tenant_settings" else None), "__builtins__": __builtins__}
    lift(read("deploy/shared/tenancy.py"), tns, names=("policy_of",), assigns=("DATA_REGIONS",))
    tns["_TENANT_SETTINGS"] = {}                      # main.py's `_TENANT_SETTINGS: dict = {}` is an annotated assignment, which lift() leaves alone
    lift(main_src, tns, names=("tenant_settings", "choose_for", "retrieval_backend_for"))
    assert tns["policy_of"]({"data_region": "any"}) == "any" and tns["policy_of"]({"data_region": " Any"}) == "any" and tns["policy_of"]({}) == "in" \
        and tns["policy_of"](None) == "in" and tns["policy_of"]({"data_region": "us"}) == "in", "absent, unknown or no document is `in`"
    cf, rbf = tns["choose_for"], tns["retrieval_backend_for"]
    Q = lambda t: schemas.QueryRequest(query="q", tenant_id=t)
    msettings.retrieval_backend, msettings.retrieval_mode = "firestore", "dense"
    assert cf(Q("acme")) == ("vertex", "gemini-3.6-flash", "rag_engine") and rbf("acme", "rag_engine") == ("rag_engine", 0), "the pin honoured; any permits the store"
    assert cf(Q("globex"))[2] == "rag_engine" and rbf("globex", "rag_engine") == ("firestore", 1), "an in-tenant's managed pin is the kit's index with the flag"
    assert cf(Q("zeta"))[2] == "firestore" and rbf("zeta", "firestore") == ("firestore", 0), "no pin is the deployment's default; the kit's own index needs no policy"
    assert cf(Q("nobody"))[2] == "firestore" and rbf("nobody", "rag_engine") == ("firestore", 1) and rbf("broken", "rag_engine") == ("firestore", 1), "no document and a failed read are the strict policy"
    assert cf(Q("typo"))[2] == "firestore" and tlog[-1]["event"] == "retrieval_pin_ignored" and tlog[-1]["retrieval_backend"] == "bogus" and rbf("typo", "rag_engine") == ("rag_engine", 0), "an unknown pin is ignored with a line; data_region is normalised"
    msettings.retrieval_backend = "rag_engine"
    assert rbf("globex", "rag_engine") == ("firestore", 1) and rbf("acme", "rag_engine") == ("rag_engine", 0), "a managed default falls back to Firestore, which holds every embedding"
    msettings.retrieval_backend = "vector"
    assert rbf("globex", "rag_engine") == ("vector", 1), "the deployment's own backend is the fallback when it has one"
    msettings.retrieval_mode = "hybrid"
    tlog.clear()
    assert cf(Q("acme"))[2] == "vector" and tlog[-1]["event"] == "retrieval_pin_ignored" and tlog[-1]["retrieval_backend"] == "rag_engine", "a managed pin under hybrid is the pair config.py refuses: ignored, not served"
    msettings.retrieval_backend, msettings.retrieval_mode = "firestore", "dense"
    n = len(treads); cf(Q("acme")); cf(Q("acme")); rbf("acme", "rag_engine")
    assert len(treads) == n, "tenant_settings is read once a minute per tenant, for the pins and the policy alike"
    # through the handlers: the row carries the backend that served and the flag, and retrieve() is asked for that backend
    mns["choose_for"], mns["retrieval_backend_for"] = cf, rbf
    asked = []
    mns["retrieve"] = lambda *a, **k: asked.append(k.get("backend")) or []
    for tenant, want, flag in (("acme", "rag_engine", 0), ("globex", "firestore", 1), ("zeta", "firestore", 0)):
        for handler in ("query", "stream"):
            out = mns[handler](Q(tenant), user=user)
            if handler == "stream":
                list(out)
            row = mlog[-1]
            assert row["event"] == handler and row["retrieval_backend"] == want and row["policy_fallback"] == flag and asked[-1] == want, (tenant, handler, row["retrieval_backend"], row["policy_fallback"], asked[-1])
    ans = mns["query"](Q("globex"), user=user)
    assert ans.stages["policy_fallback"] == 1, "the caller's stages say the policy chose the kit's index"
    mns["choose_for"], mns["retrieval_backend_for"] = (lambda req: ("vertex", "gemini-3.6-flash", "firestore")), (lambda tenant_id, backend: (backend, 0))
    ok("main.py: tenant_settings.retrieval_backend pins a tenant's store (an unknown pin, or a managed one under hybrid, is ignored with a line); "
       "data_region is held against it per request - a managed backend for an `in` tenant (absent and unreadable too) is the kit's own index with "
       "policy_fallback=1, `any` keeps the store; both routes retrieve with the backend chosen and put it on the row, one read a minute per tenant")

    src = [{"id": "acme#1", "tenant_id": "acme", "text": "notice period is sixty days", "source_uri": "gs://b/acme/hr.md", "page_start": 2, "score": 0.7, "effective_from": "2026-04-01"},
           {"id": "acme#2", "tenant_id": "acme", "text": "ninety days for directors", "source_uri": "gs://b/acme/hr.md", "page_start": 3, "score": 0.9},
           {"id": "acme#3", "tenant_id": "acme", "text": "figure 2: attrition by quarter", "source_uri": "gs://b/acme/hr.md", "page_start": 9, "score": 0.6,
            "kind": "figure", "media_url": "gs://b/acme/hr/fig2.png"}]
    mns["retrieve"] = lambda *a, **k: [dict(c) for c in src]
    mns["rerank"] = lambda q, chunks, k, tenant_id=None: rns["_by_retrieval_score"](chunks, k)      # the reranker fell back

    def fake_generate(q, chunks, tenant_id, model=None, backend=None):
        gen_seen.append([c["id"] for c in chunks])
        return schemas.RAGResponse(answer="Sixty days.", citations=[schemas.Citation(chunk_id=chunks[0]["id"], source_uri=chunks[0]["source_uri"], page=2, quote="sixty days", score=0.9)],
                                   confidence="high", answerable=True, model=model, backend=backend, tokens_in=1200, tokens_out=40, cached_tokens=1000, latency_ms=0)

    mns["generate"] = fake_generate
    ans = mns["query"](req, user=user)
    assert gen_seen[-1] == ["acme#2", "acme#1", "acme#3"] and ans.stages["rerank_fallback"] == 1 and mlog[-1]["rerank_fallback"] == 1, "a reranker fallback must reach the answer's stages and the row"
    assert mlog[-1]["cached_tokens"] == 1000 and mlog[-1]["tokens_in"] == 1200 and stored, "the answer's cached_tokens reach the row; an answerable, cited answer fills the cache"
    mns["rerank"] = lambda q, chunks, k, tenant_id=None: chunks[:k]
    ans = mns["query"](req, user=user)
    assert "rerank_fallback" not in ans.stages and mlog[-1]["rerank_fallback"] == 0
    ok("main.py: /v1/query puts rerank_fallback=1 in the answer's stages and on the row when the pool stood in for the Ranking API, 0 otherwise; the generator's cached_tokens reach the row")

    # The ANN tier's share, on the answer (16 September 2026): the pool above carried no found_by, so the tier gave none of it;
    # stamp two of three `vector` and the count follows. The backend chosen for the request rides beside it, the same value
    # usage_row has always carried - so a caller can tell a Firestore fallback from a Vector Search hit without the log.
    assert ans.stages["vector_chunks"] == 0 and ans.stages["retrieval_backend"] == mlog[-1]["retrieval_backend"], (ans.stages, mlog[-1]["retrieval_backend"])
    mns["retrieve"] = lambda *a, **k: [dict(c, found_by="vector") if c["id"] != "acme#3" else dict(c, found_by="firestore") for c in src]
    ans = mns["query"](req, user=user)
    assert ans.stages["vector_chunks"] == 2 and ans.stages["pool"] == 3, ans.stages
    mns["retrieve"] = lambda *a, **k: [dict(c) for c in src]
    ok("main.py: /v1/query puts the ANN tier's share of the pool (vector_chunks) and the backend chosen for the request (retrieval_backend) in the answer's stages, the row's value")

    def fake_stream(q, chunks, tenant_id, model=None, backend=None):
        gs_seen.append([c["id"] for c in chunks])
        yield "packed", [chunks[0], chunks[2]]                      # the budget dropped acme#1
        yield "token", "Ninety"
        yield "token", " days."
        yield "usage", {"tokens_in": 900, "tokens_out": 30, "cached_tokens": 0, "model": "gemini-3.6-flash"}

    mns["generate_stream"] = fake_stream
    mns["rerank"] = lambda q, chunks, k, tenant_id=None: rns["_by_retrieval_score"](chunks, k)
    events = _sse(list(mns["stream"](req, user=user)))
    kinds = [e for e, _ in events]
    assert kinds == ["citation", "citation", "token", "token", "done"], kinds
    cits = [d for e, d in events if e == "citation"]
    assert [c["chunk_id"] for c in cits] == ["acme#2", "acme#3"], "the stream cited a chunk the budget dropped (or the reranked pool instead of the packed set)"
    assert [c["n"] for c in cits] == [1, 2] and set(cits[0]) == {"n", "chunk_id", "source", "page", "quote", "kind", "media_url", "start", "end", "effective_from"}
    assert cits[1]["kind"] == "figure" and cits[1]["media_url"] == "gs://b/acme/hr/fig2.png" and cits[0]["page"] == 3 and cits[0]["quote"] == "ninety days for directors"
    done = events[-1][1]
    assert done["tokens_in"] == 900 and done["stages"]["rerank_fallback"] == 1 and done["cache_hit"] == "none" and done["backend"] == "vertex"
    row = mlog[-1]
    assert row["event"] == "stream" and row["rerank_fallback"] == 1 and row["modality"] == "image" and row["tokens_in"] == 900 and row["answerable"] is True
    cache.lookup = lambda *a, **k: {"answer": {"answer": "Sixty days.", "citations": [{"chunk_id": "acme#1", "source_uri": "gs://b/acme/hr.md", "page": 2, "quote": "sixty days", "score": 0.9}],
                                              "confidence": "high", "answerable": True}, "model": "gemini-3.6-flash"}
    before = len(gs_seen)
    events = _sse(list(mns["stream"](req, user=user)))
    assert [e for e, _ in events] == ["citation", "token", "done"] and len(gs_seen) == before, "a cache hit must not stream the model"
    assert events[0][1]["chunk_id"] == "acme#1" and events[1][1]["t"] == "Sixty days." and events[-1][1]["cache_hit"] == "semantic" and events[-1][1]["backend"] == "cache"
    cache.lookup = lambda *a, **k: None
    assert "if kind == 'packed':" in fns["stream"] and "for i, c in enumerate(chunks, 1)" not in fns["stream"], "the stream must cite from generate_stream's packed event, not the reranked pool"
    ok("main.py: /v1/stream emits its citation events from generate_stream's packed payload (a dropped chunk is never cited; the event keeps kind / media_url / start / end / effective_from) before the first token; a cache hit cites the stored answer as before")

    # ------------------------------------------------------------------ generator.py: the packed event, the budget, the tokens
    cb = load(os.path.join(API, "context_budget.py"), "context_budget_under_test")
    gen_src = read("deploy/services/rag-api/generator.py")
    glog, seen = [], {}

    class _APIError(Exception):
        code = None

    class _TenantCacheManager:
        def __init__(self, *a, **k): pass
        def generate_config_kwargs(self, tenant, model=None): return {}

    gsettings = SimpleNamespace(project_id="demo", region="us-central1", generator_model="gemini-3.6-flash", model_backend="vertex",
                                max_context_tokens=8000, max_answer_tokens=2048, generator_location="", litellm_url="", gateway_timeout_s=90.0)
    gns = {"json": json, "logging": __import__("logging"), "re": re, "time": time, "SimpleNamespace": SimpleNamespace, "httpx": SimpleNamespace(),
           "HTTPException": _HTTPException, "ValidationError": pydantic.ValidationError, "lru_cache": __import__("functools").lru_cache,
           "genai": SimpleNamespace(Client=lambda **kw: SimpleNamespace(models=None)), "errors": SimpleNamespace(APIError=_APIError),
           "types": SimpleNamespace(GenerateContentConfig=lambda **kw: kw, ThinkingConfig=lambda **kw: kw, Part=SimpleNamespace(from_uri=lambda **kw: kw)),
           "DraftCitation": schemas.DraftCitation, "ModelDraft": schemas.ModelDraft, "RAGResponse": schemas.RAGResponse, "resolve": schemas.resolve,
           "settings": gsettings, "pack_chunks": cb.pack_chunks, "estimate_tokens": cb.estimate_tokens, "TokenBudget": cb.TokenBudget,
           "TenantCacheManager": _TenantCacheManager, "__builtins__": __builtins__}
    lift(gen_src, gns, assigns=("SYSTEM", "DATED_RULE", "GATEWAY_JSON_RULE", "GATEWAY_ROUTES", "_gateway_token", "_client", "log"))
    gns["log"] = SimpleNamespace(info=lambda s: glog.append(json.loads(s)), warning=lambda s: glog.append(json.loads(s)), error=lambda s: glog.append(json.loads(s)))
    SYSTEM, DATED_RULE = gns["SYSTEM"], gns["DATED_RULE"]
    q = "what is the notice period?"
    b = gns["_budget"](q)
    fixed = cb.estimate_tokens(f"{SYSTEM}{DATED_RULE}\n\nContext:\n\n\nQuestion: {q}")
    assert isinstance(b, cb.TokenBudget) and 0 < fixed < 8000 and b.system == fixed and b.chunks == 8000 - fixed and b.input_total == 8000 and b.answer == 2048, b
    assert cb.TokenBudget.fit(100, "x" * 800).chunks == 0 and cb.TokenBudget.fit(1000, "abcd" * 10, lambda s: 7).chunks == 993, "fit: never below zero; the counter is injectable"

    class _Models:
        def __init__(self, parts): self.parts = parts
        def generate_content_stream(self, model, contents, config):
            seen["model"], seen["contents"], seen["config"] = model, contents, config
            out = self.parts.pop(0)
            if isinstance(out, Exception):
                raise out
            return iter(out)

    models = _Models([[SimpleNamespace(text="ok", usage_metadata=None)]])
    gns["_client_for"] = lambda model: SimpleNamespace(models=models)
    evs = list(gns["generate_stream"](q, []))
    prompt = seen["contents"][0]
    assert b.system == cb.estimate_tokens(SYSTEM + DATED_RULE + prompt[len(SYSTEM):]), "the budget's fixed text drifted from the prompt generate_stream sends"
    recorded_budget = []
    real_pack = gns["pack_chunks"]
    gns["pack_chunks"] = lambda chunks, budget, count_fn=None: recorded_budget.append(budget) or real_pack(chunks, budget, count_fn)
    models.parts.append([SimpleNamespace(text="ok", usage_metadata=None)])
    list(gns["generate_stream"](q, []))
    assert recorded_budget[-1] == b.chunks < gsettings.max_context_tokens, "pack_chunks must be given what is left after the fixed parts, not max_context_tokens itself"
    big = [{"id": f"acme#{i}", "text": "x" * 10600, "source_uri": "gs://b/acme/h.md", "effective_from": "2026-04-01"} for i in range(4)]
    models.parts.append([SimpleNamespace(text="ok", usage_metadata=None)])
    evs = list(gns["generate_stream"](q, big))
    assert evs[0][0] == "packed" and [c["id"] for c in evs[0][1]] == ["acme#0", "acme#1"], "three 2,650-token blocks fit 8,000 but not what is left after the fixed parts"
    assert cb.estimate_tokens(seen["contents"][0]) <= 8000, "the packed prompt exceeds max_context_tokens"
    assert DATED_RULE in seen["contents"][0] and glog[-1] == {"event": "context_budget_drop", "packed": 2, "dropped": 2}
    ok("generator._budget / TokenBudget.fit: the chunk budget is max_context_tokens less the estimate of SYSTEM, the dated rule and the question; pack_chunks receives it, and the packed prompt never exceeds the total (4 x 2,650-token chunks: 2 packed, 2 dropped, logged)")

    parts = [SimpleNamespace(text="Sixty", usage_metadata=None), SimpleNamespace(text=" days.", usage_metadata=SimpleNamespace(
        prompt_token_count=100, candidates_token_count=20, thoughts_token_count=15, cached_content_token_count=30))]
    models.parts.append(parts)
    evs = list(gns["generate_stream"](q, [src[0]], "acme"))
    assert [k for k, _ in evs] == ["packed", "token", "token", "usage"], [k for k, _ in evs]
    assert evs[0][1][0] is not None and evs[0][1][0]["id"] == "acme#1" and evs[-1][1] == {"tokens_in": 100, "tokens_out": 35, "cached_tokens": 30, "model": "gemini-3.6-flash"}, \
        "the stream's usage must add thoughts_token_count to tokens_out and keep cached_tokens beside tokens_in"
    quota = _APIError("quota")
    quota.code = 429
    models.parts += [quota, [SimpleNamespace(text="ok", usage_metadata=SimpleNamespace(prompt_token_count=10, candidates_token_count=2, thoughts_token_count=None, cached_content_token_count=None))]]
    evs = list(gns["generate_stream"](q, [src[0]], "acme", model="gemini-3.1-pro-preview"))
    assert [k for k, _ in evs] == ["packed", "token", "usage"] and evs[-1][1]["model"] == "gemini-3.6-flash" and evs[-1][1]["tokens_out"] == 2, \
        "a tier fallback must not yield a second packed event"
    assert glog[-1]["event"] == "tier_exhausted"
    ok("generator.generate_stream: the first event is ('packed', packed), exactly once even when an exhausted tier falls back; the usage adds the thinking tokens to tokens_out and carries cached_tokens")

    seen_max = []
    truncated = SimpleNamespace(parsed=None, text='{"answer": "Sixty', candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="MAX_TOKENS"))], prompt_feedback=None,
                                usage_metadata=SimpleNamespace(prompt_token_count=1000, candidates_token_count=50, thoughts_token_count=300, cached_content_token_count=200))
    whole = SimpleNamespace(parsed=schemas.ModelDraft(answer="Sixty days.", citations=[schemas.DraftCitation(source=1, quote="sixty days")], confidence="high", answerable=True),
                            text="", candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))], prompt_feedback=None,
                            usage_metadata=SimpleNamespace(prompt_token_count=1000, candidates_token_count=120, thoughts_token_count=400, cached_content_token_count=200))
    replies = [truncated, whole]
    gns["_call_or_fallback"] = lambda prompt, packed, tenant_id, max_tokens, model: seen_max.append(max_tokens) or (replies.pop(0), model)
    ans = gns["generate"](q, [src[0]], "acme")
    assert seen_max == [2048, 6144] and glog[-1]["event"] == "generation_truncated", (seen_max, glog[-1:])
    assert ans.tokens_in == 2000 and ans.tokens_out == 870 and ans.cached_tokens == 400 and ans.cost_usd is None, \
        f"the row must carry both attempts, thinking included: {ans.tokens_in} / {ans.tokens_out} / {ans.cached_tokens}"
    assert ans.answerable and ans.citations[0].chunk_id == "acme#1" and ans.model == "gemini-3.6-flash"
    replies[:] = [whole]
    ans = gns["generate"](q, [src[0]], "acme")
    assert (ans.tokens_in, ans.tokens_out, ans.cached_tokens) == (1000, 520, 200), "one attempt, one bill"
    gw1 = gns["_GatewayReply"]({"choices": [{"message": {"content": '{"answer": "Sixty'}, "finish_reason": "length"}], "usage": {"prompt_tokens": 800, "completion_tokens": 40}}, 0.001, "documind-general")
    gw2 = gns["_GatewayReply"]({"choices": [{"message": {"content": json.dumps({"answer": "Sixty days.", "citations": [{"source": 1, "quote": "sixty days"}], "confidence": "high", "answerable": True})}}],
                                "usage": {"prompt_tokens": 800, "completion_tokens": 90}}, 0.002, "documind-general")
    gw = [gw1, gw2]
    gns["_gateway_call"] = lambda prompt, packed, tenant_id, max_tokens, model: gw.pop(0)
    ans = gns["generate"](q, [src[0]], "acme", backend="gateway")
    assert (ans.tokens_in, ans.tokens_out, ans.cached_tokens) == (1600, 130, 0) and abs(ans.cost_usd - 0.003) < 1e-9 and ans.backend == "gateway", \
        "the gateway's two priced attempts must be summed"
    assert gns["_usage"](SimpleNamespace(usage_metadata=None)) == {"tokens_in": 0, "tokens_out": 0, "cached_tokens": 0}
    ok("generator.generate: a truncated first attempt's prompt, candidates, thinking and cached tokens are added to the retry's on the answer (2000 in / 870 out / 400 cached), the gateway's two prices summed; one attempt is one bill")

    # ------------------------------------------------------------------ shared/documind_tools.py: the local lane's Chroma where (workshop lesson 10.6)
    import shared.documind_tools as dt
    import shared.profile as profile
    wheres, real_build, real_profile = [], profile.build_store, dt.PROFILE

    class _Chroma:
        _collection = SimpleNamespace(count=lambda: 1)
        def get(self, where=None, include=None):
            wheres.append(where)
            return {"documents": ["the notice period is sixty days"], "metadatas": [{"chunk_id": "acme#1", "source_uri": "gs://b/acme/hr.md", "page": 1}]}
    profile.build_store, dt.PROFILE = (lambda embeddings=None: _Chroma()), "local"
    try:
        for doc_type, want in ((None, {"tenant_id": "acme"}),
                               ("statute", {"$and": [{"tenant_id": "acme"}, {"doc_type": "statute"}]}),
                               (["guidance", "statute"], {"$and": [{"tenant_id": "acme"}, {"doc_type": {"$in": ["guidance", "statute"]}}]})):
            dt.retrieve("notice period", tenant_id="acme", top_k=5, doc_type=doc_type)
            assert wheres[-1] == want, (doc_type, wheres[-1])
        for doc_type in (("statute", "guidance"), ["statute", "guidance", "statute"]):
            dt.retrieve("notice period", tenant_id="acme", top_k=5, doc_type=doc_type)
            assert wheres[-1] == {"$and": [{"tenant_id": "acme"}, {"doc_type": {"$in": ["guidance", "statute"]}}]}, (doc_type, wheres[-1])
        dt.retrieve("notice period", tenant_id="acme", top_k=5, doc_type=["statute", "statute"])
        assert wheres[-1] == {"$and": [{"tenant_id": "acme"}, {"doc_type": "statute"}]}, "one class is its string, as rag-api makes it"
        n = len(wheres)
        rule = {"error": "filter doc_type must be a non-empty string or a list of 1 to 5 of them", "citations": [], "answerable": False, "confidence": "low"}
        for bad in ([], (), ["a", "b", "c", "d", "e", "f"], ["statute", 3], ["statute", ""], [["statute"]]):
            got = dt.retrieve("notice period", tenant_id="acme", top_k=5, doc_type=bad)
            assert got == rule, (bad, got)
        assert len(wheres) == n, "a malformed doc_type list - an empty one included - never reaches the store"
        dt.PROFILE = "gcp"                                  # the gcp lane: the same rule, checked before the token or the post
        real_post, real_token = dt.requests.post, dt._id_token
        dt.requests.post = dt._id_token = lambda *a, **k: (_ for _ in ()).throw(AssertionError("posted a malformed doc_type"))
        try:
            for bad in ([], ["a", "b", "c", "d", "e", "f"], ["statute", 3]):
                assert dt.retrieve("notice period", tenant_id="acme", top_k=5, doc_type=bad) == rule, bad
        finally:
            dt.requests.post, dt._id_token = real_post, real_token
        # retrieve(passages=True) (workshop lesson 10.6): /v1/passages on the gcp lane - the same payload and headers, the
        # door's reply passed on, a failure as data - and the same shape from Chroma on the local lane, the whole text.
        posted, replies = [], []

        class _Resp:
            def __init__(self, body):
                self.body = body
            def raise_for_status(self):
                if isinstance(self.body, Exception):
                    raise self.body
            def json(self):
                return self.body
        dt.requests.post, dt._id_token = (lambda url, json=None, headers=None, timeout=None: posted.append((url, json, headers)) or _Resp(replies.pop(0))), (lambda aud: "tok")
        dt.logger.disabled = True                           # the 503 below is meant; its warning line is not a failure
        try:
            whole = {"n": 1, "chunk_id": "acme:hr#np03", "source_uri": "gs://b/acme/hr.md", "page": None, "doc_type": "policy", "kind": "text",
                     "section": "NP-03", "text": "Either party may end the employment with sixty days' written notice.", "score": 0.9}
            replies.append({"passages": [whole], "answerable": True, "usage": {"model": "none", "tokens_in": 0, "tokens_out": 0, "cached_tokens": 0, "cost_usd": 0.0, "latency_ms": 12}})
            got = dt.retrieve("notice period", tenant_id="acme", top_k=4, doc_type=["policy"], assertion="jwt", brain="langgraph", passages=True)
            url, body, headers = posted[-1]
            assert url.endswith("/v1/passages") and body == {"query": "notice period", "tenant_id": "acme", "user_id": "agent", "top_k": 4, "stream": False,
                                                             "filters": {"doc_type": "policy"}, "brain": "langgraph"}, (url, body)
            assert headers == {"Authorization": "Bearer tok", dt.ASSERTION_HEADER: "jwt"}, headers
            assert got == {"passages": [{k: whole[k] for k in dt.PASSAGE_KEYS}], "answerable": True,
                           "usage": {"model": "none", "tokens_in": 0, "tokens_out": 0, "cached_tokens": 0, "cost_usd": 0.0}}, got
            replies.append({"passages": [], "answer": "DocuMind did not search for an answer.", "answerable": False,
                            "usage": {"model": "none", "tokens_in": 0, "tokens_out": 0, "cached_tokens": 0, "cost_usd": 0.0}})
            got = dt.retrieve("I want to talk to a person", tenant_id="acme", passages=True)
            assert got["passages"] == [] and got["answerable"] is False and got["answer"] == "DocuMind did not search for an answer.", got
            replies.append(dt.requests.HTTPError("503"))
            got = dt.retrieve("notice period", tenant_id="acme", passages=True)
            assert got == {"error": "document retrieval is unavailable", "passages": [], "answerable": False}, got
            replies.append({"answer": "Sixty days.", "citations": [], "answerable": True, "confidence": "high"})
            dt.retrieve("notice period", tenant_id="acme")
            assert posted[-1][0].endswith("/v1/query"), "without passages, retrieve() still asks /v1/query"
        finally:
            dt.requests.post, dt._id_token, dt.logger.disabled = real_post, real_token, False
        dt.PROFILE = "local"
        got = dt.retrieve("notice period", tenant_id="acme", top_k=5, passages=True)
        assert got == {"passages": [{"n": 1, "chunk_id": "acme#1", "source_uri": "gs://b/acme/hr.md", "page": 1, "doc_type": None, "kind": "text",
                                     "section": None, "text": "the notice period is sixty days"}], "answerable": True}, got
        assert dt.retrieve("quarterly revenue forecast", tenant_id="acme", top_k=5, passages=True) == {"passages": [], "answerable": False}
    finally:
        profile.build_store, dt.PROFILE = real_build, real_profile
    ok("documind_tools.retrieve(passages=True): /v1/passages with /v1/query's payload and headers, the passages' fields kept and the door's answer passed on, "
       "a failure as data, /v1/query still without it; the local lane returns the same shape from Chroma with each chunk's whole text")
    ok("documind_tools.retrieve: a doc_type list or tuple is Chroma's $in (sorted, de-duplicated, one class as its string) under the tenant's $and, a class is an equality, none is the tenant alone; an empty list, six classes or a non-string member is rag-api's error text as data on both lanes, before the store is read or rag-api is called")

    print(f"\n{len(PASSED)} passed, {len(SKIPPED)} skipped")
    return 0


if __name__ == "__main__":
    sys.exit(main())
