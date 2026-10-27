"""Offline tests for shared/documind_schemas.resolve(): one Citation per chunk, and one for every source the answer
cites (21 October 2026). The two failure shapes come from a live lane: an answer that cited [1, 2] with one entry in
its citations array (lesson 1.3), and an answer whose array named the same chunk three times (lesson 1.1).

Run with ``python -m unittest discover -s evals/tests -p test_resolve_citations.py`` from deploy/. Needs pydantic,
which CI installs for evals/tests; nothing reaches a network.
"""
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from shared.documind_schemas import DraftCitation, ModelDraft, cited_numbers, resolve  # noqa: E402


def packed(n):
    return [{"chunk_id": f"acme:hr_policy_2026#{i}", "text": f"clause {i}", "source_uri": "gs://b/acme/hr_policy_2026.md",
             "page_start": 1, "score": 0.5} for i in range(1, n + 1)]


def draft(answer, *cites):
    return ModelDraft(answer=answer, citations=[DraftCitation(source=s, quote=q) for s, q in cites],
                      confidence="high", answerable=True)


class ResolveTests(unittest.TestCase):
    def test_every_source_the_answer_cites_gets_a_citation(self):
        out = resolve(draft("Ninety days [1, 2].", (1, "90 days")), packed(3))
        self.assertEqual([(c.chunk_id, c.quote) for c in out.citations],
                         [("acme:hr_policy_2026#1", "90 days"), ("acme:hr_policy_2026#2", "clause 2")])

    def test_one_citation_per_chunk_keeping_the_first_quote(self):
        out = resolve(draft("Page nine [3].", (3, "first"), (3, "second"), (3, "third")), packed(3))
        self.assertEqual([(c.chunk_id, c.quote) for c in out.citations], [("acme:hr_policy_2026#3", "first")])

    def test_out_of_range_numbers_are_dropped_and_the_prose_is_kept(self):
        answer = "See [Source 2], the [2026] act and [9]."
        out = resolve(draft(answer, (7, "not seen")), packed(3))
        self.assertEqual([c.chunk_id for c in out.citations], ["acme:hr_policy_2026#2"])
        self.assertEqual(out.answer, answer)

    def test_cited_numbers_reads_every_marker_form_once(self):
        self.assertEqual(cited_numbers("a [1] b [2, 3] c [Source 4] d [1] e [Source 5, Source 6]"), [1, 2, 3, 4, 5, 6])
        self.assertEqual(cited_numbers(""), [])


if __name__ == "__main__":
    unittest.main()
