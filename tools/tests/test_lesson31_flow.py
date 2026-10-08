"""Lesson 1.1's page is its own source (no build.py), so nothing rebuilds its "services behind the stages" diagram when
the kit changes. This holds each fact the diagram states to the kit file that decides it."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[2]
KIT = ROOT / "deploy"
PAGE = (ROOT / "lessons/01-rag-foundation/1.1-contracts/Netsetos_GCP_Capstone_1.1_Contracts_WIX.html").read_text(encoding="utf-8")


def kit(path):
    return (KIT / path).read_text(encoding="utf-8")


class ServicesBehindTheStages(unittest.TestCase):
    def test_the_diagram_is_on_the_page_in_both_drawings(self):
        self.assertIn("<h4>The services behind the stages</h4>", PAGE)
        self.assertEqual(PAGE.count('<svg viewBox="0 0 680 946"'), 1)
        self.assertEqual(PAGE.count('<svg viewBox="0 0 360 800"'), 1)

    def test_the_trigger_the_retries_and_the_dead_letters(self):
        ev = kit("terraform/eventarc.tf")
        self.assertIn('resource "google_storage_notification" "uploads"', ev)           # the bucket announces uploads
        self.assertIn('{ name = "documind-ingest" }', ev)
        self.assertIn("Pub/Sub topic: documind-ingest", PAGE)
        self.assertIn("ack_deadline_seconds = 600", ev)
        self.assertIn("calls the worker, 600 s", PAGE)
        self.assertIn("max_delivery_attempts = 12", ev)
        self.assertIn('{ name = "documind-ingest-dlq" }', ev)
        self.assertIn("documind-ingest-dlq, after 12 tries", PAGE)
        self.assertIn('service_name="documind-ingest"', kit("terraform/alerts.tf"))
        self.assertIn("Cloud Run: documind-ingest", PAGE)

    def test_the_worker_steps_and_the_stores(self):
        ing, idx, idem = kit("services/ingest/main.py"), kit("services/ingest/indexer.py"), kit("services/ingest/idempotency.py")
        self.assertIn("MAX_INLINE_PAGES = 250", ing)
        self.assertIn("over 250 pages: the batch job", PAGE)
        body = ing[ing.index("def index_document("):]
        self.assertLess(body.index("pii_inspect_many("), body.index("upsert(INDEX_NAME"))  # scanned before indexed
        self.assertIn('audit_emit("doc.upload"', ing)
        self.assertIn("mirror_to_bigquery(", ing)
        self.assertIn('EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL", "text-embedding-005")', idx)
        self.assertIn("text-embedding-005, 768 numbers", PAGE)
        vec = kit("terraform/vector.tf")
        self.assertIn("dimensions                  = 768", vec)
        self.assertIn('display_name = "documind-chunks"', vec)
        self.assertIn("documind-chunks: upsert, remove", PAGE)
        for coll in ("documents", "sources", "ledger"):
            self.assertIn(f'collection("{coll}")', idem)
        self.assertIn('chunks_collection: str = "chunks"', idx)
        self.assertIn("documind-{tenant}", kit("services/ingest/managed.py"))
        self.assertIn("documind-acme; if mirror is on", PAGE)

    def test_the_stores_a_question_can_read(self):
        self.assertIn('RETRIEVAL_BACKENDS = ("vector", "firestore", "rag_engine", "vertex_search")', kit("shared/tenancy.py"))
        self.assertIn("vector (Firestore as its fallback), firestore, rag_engine or vertex_search", PAGE)


if __name__ == "__main__":
    unittest.main()
