"""Lesson 2.2's "one sentence, two vectors" explainer embeds the kit's sparse arithmetic when the page is built. CI does
not rebuild pages, so this holds the embedded numbers to the kit: a change to the encoder or to the corpus fails here
until the page is rebuilt (26 September 2026)."""
import json
import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "deploy"))
from shared import documind_corpus as dc  # noqa: E402
from shared.sparse_encoder import SPARSE_DIMS, sparse_encode  # noqa: E402

LESSON = ROOT / "lessons/02-retrieval/2.2-hybrid"
PAGE = (LESSON / "Netsetos_GCP_Capstone_2.2_Hybrid_WIX.html").read_text(encoding="utf-8")
DV = json.loads(re.search(r"var DV = (\{.*?\});\n", PAGE, re.S).group(1))
TARGETS = {"code": ("hr_policy_2026.md", "NP-03"), "para": ("hr_policy_2026.md", "NP-03"), "inv": ("inv_2026_0412.md", None)}


def chunk_text(source, locator):
    path = ROOT / "deploy/evals/corpus/acme" / source
    chunks = dc.chunk_document({"slug": path.stem, "doc_type": "policy", "source_uri": f"gs://x/acme/{source}",
                                "text": path.read_text(encoding="utf-8")}, "acme")
    return next(c["text"] for c in chunks if locator is None or c.get("locator") == locator)


def dot(a, b):
    va, vb = dict(zip(a[1], a[0])), dict(zip(b[1], b[0]))
    return sum(w * vb.get(d, 0.0) for d, w in va.items())


class TwoVectors(unittest.TestCase):
    def test_the_slots_and_weights_are_the_encoders(self):
        self.assertEqual(DV["dims"], SPARSE_DIMS)
        for key, (source, locator) in TARGETS.items():
            values, dims = sparse_encode(chunk_text(source, locator))
            by_slot = {}
            for _, s, w in DV["q"][key]["docToks"]:
                by_slot[s] = by_slot.get(s, 0.0) + w
            self.assertEqual(sorted(by_slot), dims, key)
            self.assertEqual([by_slot[d] for d in dims], values, key)

    def test_each_score_is_the_dot_product_the_index_computes(self):
        for key, (source, locator) in TARGETS.items():
            q = DV["q"][key]
            score = dot(sparse_encode(q["q"]), sparse_encode(chunk_text(source, locator)))
            self.assertAlmostEqual(q["score"], round(score, 2), msg=key)
            self.assertAlmostEqual(q["score"], sum(a * b for _, a, b in q["shared"]), msg=key)

    def test_the_paraphrase_shares_no_word_and_the_code_one(self):
        self.assertEqual(DV["q"]["para"]["shared"], [])
        self.assertEqual([s[0] for s in DV["q"]["code"]["shared"]], ["np-03"])

    def test_the_invoices_dense_rank_is_step_4s_lane_output(self):
        self.assertEqual(DV["q"]["inv"]["dense"], 1)
        self.assertIn("dense  first five (anchor at rank 1 of 20)", (LESSON / "parts/b.html").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
