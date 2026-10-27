"""Offline checks for the Vertex AI Search mirror's bucket and the ledger stamp (21 October 2026).

The mirror staged each version's text in the audit bucket, whose retention policy refuses every delete and overwrite:
a retire left the staged copy, a restore could not rewrite it, and stamp() merged `mirrored`, so the row still named
the store. These check that the store stages in <project>-search (or SEARCH_BUCKET), never in AUDIT_BUCKET, and that
stamp() replaces `mirrored` with the stores that confirmed this version. No Google packages or network.
"""
import importlib.util
import os
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import patch

DEPLOY = Path(__file__).resolve().parents[2]


def load_managed():
    sys.path.insert(0, str(DEPLOY))
    spec = importlib.util.spec_from_file_location("managed_under_test", DEPLOY / "services/ingest/managed.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class SearchBucketTests(unittest.TestCase):
    def store(self, **env):
        managed = load_managed()
        with patch.dict(os.environ, {"MANAGED_MIRROR": "vertex_search", "GOOGLE_CLOUD_PROJECT": "demo",
                                     "AUDIT_BUCKET": "demo-audit", **env}, clear=False):
            if "SEARCH_BUCKET" not in env:
                os.environ.pop("SEARCH_BUCKET", None)          # restored when patch.dict exits
            mirror = managed.Mirror.from_env(db=None, policy_for=lambda tenant: "any")
        return mirror.stores[0]

    def test_the_text_is_staged_in_the_search_bucket_not_the_audit_bucket(self):
        self.assertEqual(self.store().bucket, "demo-search")

    def test_search_bucket_names_another(self):
        self.assertEqual(self.store(SEARCH_BUCKET="elsewhere").bucket, "elsewhere")


class StampTests(unittest.TestCase):
    def test_mirrored_is_replaced_not_merged(self):
        managed = load_managed()
        writes = []

        class Doc:
            def set(self, data, merge):
                writes.append((data, merge))

        db = SimpleNamespace(collection=lambda name: SimpleNamespace(document=lambda key: Doc()))
        mirror = managed.Mirror(db, [], "off", policy_for=lambda tenant: "any")
        firestore = ModuleType("google.cloud.firestore")
        firestore.SERVER_TIMESTAMP = object()
        cloud = ModuleType("google.cloud")
        cloud.firestore = firestore
        with patch.dict(sys.modules, {"google": ModuleType("google"), "google.cloud": cloud, "google.cloud.firestore": firestore}):
            mirror.stamp("acme", "acme/note.md", "acme_abc", {"rag_engine": "us-central1"})
        data, merge = writes[0]
        self.assertEqual(data["mirrored"], {"rag_engine": "us-central1"})
        self.assertIn("mirrored", merge)            # field paths: the map is replaced, so a store that failed drops out
        self.assertIsNot(merge, True)


if __name__ == "__main__":
    unittest.main()
