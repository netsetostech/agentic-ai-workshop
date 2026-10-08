#!/usr/bin/env python3
"""Does the Rs 0 lane answer the golden set the way production must - and refuse the way it must?

    python tools/check_local_lane.py             # offline, no credentials, no Chroma needed
    python tools/check_local_lane.py --show iso-06

shared/local_corpus.py seeds DocuMind's corpus into the local Chroma store, and
documind_tools._retrieve_local() answers from it with BM25 and a gate instead of an embedding
(the local embedding is a deterministic fake). This runs every row of deploy/evals/golden.jsonl
through that exact code path over the exact chunks local_corpus would write - Chroma is stood
in for by a dict that honours the same get(where=...) filter - and scores:

  answerable rows   the top 5 citations carry every must_retrieve anchor (in an id or a quote)
                    and every must_contain phrase - the lane found the clause, not a neighbour;
  refusal rows      answerable=False - no citation at all, which is what the answer contract
                    turns into "I don't have that" instead of a confident wrong answer;
  isolation rows    no citation quotes a must_not_contain value. This one is structural (the
                    tenant filter reaches the store) and it is the row that must never go red.

Floors are set from measurement so a regression in the gate, the chunker or the corpus shows
here as a number, not a feeling. Two measurements, because the corpus grew:

  2026-09-05  six Acts, 465 ACME chunks, 43 rows          27/31 found, 9/12 refused, 0 leaks
  2026-09-06  thirteen documents, 1,624 chunks, 59 rows   33/43 found, 5/16 refused, 0 leaks
  2026-09-12  the same corpus, 65 rows (the media and version rows)   36/47 found, 4/18 refused, 0 leaks

The second line is what volume costs a lexical lane. With a thousand statute chunks per tenant
nearly every content word of a question appears somewhere, so a word-overlap gate can no longer
tell "the corpus talks about this" from "the corpus answers this": iso-08 asked of Zeta finds
"rate", "central" and "tax" in the Code on Wages and answers from it - without leaking, which is
the row's actual assertion. The gate was gridded (evidence over the retrieved set or the top
chunk; floors 0.5 / 0.6 / 0.7): a top-chunk gate refuses 10 of 16 but loses four joins; the
set gate at 0.5 keeps the joins. Retrieval recall is the lane's job and the leak count its
guarantee; refusal, at this volume, is the model's job from the quotes it is handed, and dense
retrieval's on a project. The other misses are the ones a lexical lane cannot close: a
comparison across two tenants' contracts (jn-04), a paraphrase sharing no content word with the
clause (jn-07), a figure in a sentence with none of the question's words (lk-14, jn-08), and
refusals only meaning can see (rf-06's paternity leave of the Maternity Benefit Act). The third line
is the two unanswerable rows that arrived with Module 9 and the ledger: rf-07 asks a GST rate the Act
leaves to notifications, in the Act's own words, and mm-05 asks about a figure the report never
references, in the report's own words - a lexical gate finds both, and only meaning refuses them. The
refusal floor is set from that measurement (0.2); the found floor and the leak floor did not move.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import types

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "deploy"))
from shared import documind_tools as dt  # noqa: E402
from shared import local_corpus as lc  # noqa: E402
import shared.profile as profile  # noqa: E402

GOLDEN = os.path.join(ROOT, "deploy", "evals", "golden.jsonl")
FLOORS = {"answerable_hit": 0.75, "refusal": 0.20, "leak": 0.0}


class DictStore:
    """Chroma's get() over the rows local_corpus.seed() would write, metadata included."""

    def __init__(self, tenants):
        self.rows = [c for t in tenants for c in lc.chunks_for(t)]
        self._collection = types.SimpleNamespace(count=lambda: len(self.rows))

    def get(self, where=None, include=None):
        conds = [where] if "$and" not in (where or {}) else where["$and"]
        keep = [c for c in self.rows if all(c.get(k) == v for cond in conds for k, v in cond.items())]
        return {"ids": [c["chunk_id"] for c in keep],
                "documents": [c["text"] for c in keep],
                "metadatas": [{"tenant_id": c["tenant_id"], "doc_type": c["doc_type"], "page": c["page_start"],
                               "source_uri": c["source_uri"], "chunk_id": c["chunk_id"]} for c in keep]}


def measure(golden: list, store: "DictStore", show: str | None = None, quiet: bool = False) -> dict:
    """Run every row through documind_tools.retrieve() on the local profile; return the rates."""
    profile.build_store = lambda embeddings=None: store
    dt.PROFILE = "local"
    a = types.SimpleNamespace(show=show)
    hits = refused = leaks = 0
    answerable_rows = [r for r in golden if r["answerable"]]
    refusal_rows = [r for r in golden if not r["answerable"]]
    for row in golden:
        out = dt.retrieve(row["question"], tenant_id=row["tenant"], top_k=5)
        ids = [c["chunk_id"].lower() for c in out["citations"]]
        quotes = " ".join(c["quote"].lower() for c in out["citations"])
        hay = " ".join(ids) + " " + quotes
        if a.show == row["id"]:
            print(f"  {row['id']} [{row['tenant']}] {row['question']}  -> answerable={out['answerable']} {out['confidence']}")
            for c in out["citations"]:
                print(f"     {c['score']:5.3f} {c['chunk_id']:46} {c['quote'][:70]!r}")
            print()
        if row["answerable"]:
            ok = (all(anc.lower() in hay for anc in row.get("must_retrieve", []))
                  and all(w.lower() in quotes for w in row.get("must_contain", [])))
            hits += ok
            if not ok and not quiet:
                print(f"  miss   {row['id']:6} {row['shape']:9} answerable={out['answerable']!s:5} top={ids[:2]}")
        else:
            refused += not out["answerable"]
            if out["answerable"] and not quiet:
                print(f"  answer {row['id']:6} {row['shape']:9} (should refuse) top={ids[:2]}")
        for never in row.get("must_not_contain", []):
            if never.lower() in quotes:
                leaks += 1
                print(f"  LEAK   {row['id']:6} quoted {never!r} to tenant {row['tenant']}")

    return {"answerable_hit": hits / max(1, len(answerable_rows)), "refusal": refused / max(1, len(refusal_rows)),
            "leak": leaks / max(1, len(golden)), "hits": hits, "refused": refused, "leaks": leaks,
            "n_answerable": len(answerable_rows), "n_refusal": len(refusal_rows)}


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--show", help="print the citations for one row id")
    a = ap.parse_args()
    golden = [json.loads(l) for l in open(GOLDEN, encoding="utf-8") if l.strip()]
    store = DictStore(sorted({r["tenant"] for r in golden}))
    print(f"  {len(store.rows)} chunks in the stand-in store, {len(golden)} golden rows\n")
    rates = measure(golden, store, show=a.show)
    hits, refused, leaks = rates["hits"], rates["refused"], rates["leaks"]
    answerable_rows, refusal_rows = range(rates["n_answerable"]), range(rates["n_refusal"])
    print()
    print(f"  answerable rows found (anchor + figure in top 5): {hits}/{len(answerable_rows)} = {rates['answerable_hit']:.2f}  (floor {FLOORS['answerable_hit']})")
    print(f"  refusal/isolation rows refused               : {refused}/{len(refusal_rows)} = {rates['refusal']:.2f}  (floor {FLOORS['refusal']})")
    print(f"  cross-tenant leaks                           : {leaks}  (floor {FLOORS['leak']:.0f})")
    bad = (rates["answerable_hit"] < FLOORS["answerable_hit"] or rates["refusal"] < FLOORS["refusal"]
           or leaks > FLOORS["leak"])
    print("\nNOT CLEAN" if bad else "\nCLEAN - the Rs 0 lane answers what the corpus answers, refuses what it does not, and leaks nothing")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
