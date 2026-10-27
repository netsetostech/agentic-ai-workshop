"""Offline checks for the managed mirror's repair (22 October 2026).

An undo's upload to RAG Engine failed on one 429 from RAG Engine's own embedding calls. The mirror logged it and, as
it must, failed nothing, then took the superseded version out: acme's corpus held no handbook, and nothing put it back.
These check that RagEngineStore.upsert tries a 429 again and nothing else, and that sync() uploads the text versions a
store lacks and leaves a picture missing. No Google packages or network.
"""
import importlib.util
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch

DEPLOY = Path(__file__).resolve().parents[2]


def load_managed():
    sys.path.insert(0, str(DEPLOY))
    spec = importlib.util.spec_from_file_location("managed_under_test", DEPLOY / "services/ingest/managed.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class FakeRag:
    """vertexai.rag as RagEngineStore calls it: one corpus, files by display name, and uploads that fail as scripted."""

    def __init__(self, failures):
        self.failures, self.files, self.uploads = list(failures), [], 0

    def list_files(self, corpus_name):
        return list(self.files)

    def delete_file(self, name, corpus_name):
        self.files = [f for f in self.files if f.name != name]

    def upload_file(self, corpus_name, path, display_name, description, transformation_config):
        self.uploads += 1
        f = SimpleNamespace(name=f"{corpus_name}/ragFiles/{self.uploads}", display_name=display_name)
        self.files.append(f)                       # RAG Engine keeps a file whose indexing failed: the next try deletes it
        if self.failures:
            raise self.failures.pop(0)
        return f

    TransformationConfig = staticmethod(lambda **k: k)
    ChunkingConfig = staticmethod(lambda **k: k)


class RagEngineRetryTests(unittest.TestCase):
    def store(self, rag):
        managed = load_managed()
        store = managed.RagEngineStore("demo", rag=rag)
        store.corpus = lambda tenant_id: "projects/demo/locations/us-central1/ragCorpora/1"
        return managed, store

    def test_a_429_is_tried_again_and_one_file_is_left(self):
        rag = FakeRag([RuntimeError("Failed in indexing the RagFile due to: ", {"code": 8, "message": "429 Resource exhausted"})])
        managed, store = self.store(rag)
        with patch.object(managed.time, "sleep") as slept:
            name = store.upsert("acme", "acme_k1", "gs://b/acme/hr.md", "the handbook", {})
        self.assertEqual(rag.uploads, 2)
        self.assertEqual([f.display_name for f in rag.files], ["acme_k1"])
        self.assertEqual(name, rag.files[0].name)
        slept.assert_called_once_with(managed.UPLOAD_BACKOFF_S)

    def test_another_error_is_not_tried_again(self):
        rag = FakeRag([RuntimeError("Failed in indexing the RagFile due to: 403 Permission denied")])
        managed, store = self.store(rag)
        with patch.object(managed.time, "sleep") as slept, self.assertRaises(RuntimeError):
            store.upsert("acme", "acme_k1", "gs://b/acme/hr.md", "the handbook", {})
        self.assertEqual(rag.uploads, 1)
        slept.assert_not_called()

    def test_a_429_every_time_raises_after_the_last_try(self):
        boom = RuntimeError("Failed in indexing the RagFile due to: 429 Resource exhausted")
        managed, store = self.store(FakeRag([boom] * 5))
        with patch.object(managed.time, "sleep"), self.assertRaises(RuntimeError):
            store.upsert("acme", "acme_k1", "gs://b/acme/hr.md", "the handbook", {})


class Snap:
    def __init__(self, id, data):
        self.id, self._data = id, data

    def to_dict(self):
        return dict(self._data)

    def get(self):
        return self


class Collection:
    def __init__(self, rows, filters=()):
        self.rows, self.filters = rows, filters

    def where(self, field, op, value):
        return Collection(self.rows, self.filters + ((field, value),))

    def stream(self):
        return [Snap(k, v) for k, v in self.rows.items() if all(v.get(f) == x for f, x in self.filters)]

    def document(self, key):
        return Snap(key, self.rows.get(key, {}))


class FakeDb:
    def __init__(self, **collections):
        self.collections = collections

    def collection(self, name):
        return Collection(self.collections.get(name, {}))


class FakeStore:
    name, region = "rag_engine", "us-central1"

    def __init__(self, held):
        self.held, self.uploaded = set(held), []

    def listing(self, tenant_id):
        return {k: {} for k in self.held}

    def upsert(self, tenant_id, doc_key, source_uri, text, meta):
        self.uploaded.append((doc_key, source_uri, text))
        self.held.add(doc_key)
        return f"file-{doc_key}"


class SyncTests(unittest.TestCase):
    def test_the_missing_text_version_is_uploaded_and_the_picture_left(self):
        managed = load_managed()
        db = FakeDb(
            sources={"acme~hr.md": {"tenant_id": "acme", "doc_key": "acme_hr", "status": "indexed"},
                     "acme~fig.png": {"tenant_id": "acme", "doc_key": "acme_fig", "status": "indexed"},
                     "acme~old.md": {"tenant_id": "acme", "doc_key": "acme_old", "status": "retired"},
                     "acme~held.md": {"tenant_id": "acme", "doc_key": "acme_held", "status": "indexed"}},
            chunks={"acme:hr#1": {"tenant_id": "acme", "doc_key": "acme_hr", "text": "Notice: 60 days.", "kind": "text"},
                    "acme:hr#0": {"tenant_id": "acme", "doc_key": "acme_hr", "text": "# Handbook", "kind": "text"},
                    "acme:fig#0": {"tenant_id": "acme", "doc_key": "acme_fig", "text": "a figure", "kind": "figure"}},
            documents={"acme_hr": {"gcs_uri": "gs://b/acme/hr.md"}})
        store = FakeStore(held={"acme_held"})
        mirror = managed.Mirror(db, [store], "rag_engine", policy_for=lambda t: "any", audit=lambda *a, **k: None)
        lines = managed.sync(mirror)
        self.assertEqual(store.uploaded, [("acme_hr", "gs://b/acme/hr.md", "# Handbook\n\nNotice: 60 days.")])
        self.assertEqual(lines, [{"tenant": "acme", "store": "rag_engine", "missing": 2, "uploaded": 1,
                                  "failed_or_not_permitted": [], "pictures": 1}])

    def test_a_tenant_kept_home_uploads_nothing(self):
        managed = load_managed()
        db = FakeDb(sources={"globex~msa.md": {"tenant_id": "globex", "doc_key": "globex_msa", "status": "indexed"}},
                    chunks={"globex:msa#0": {"tenant_id": "globex", "doc_key": "globex_msa", "text": "MSA", "kind": "text"}},
                    documents={"globex_msa": {"gcs_uri": "gs://b/globex/msa.md"}})
        store = FakeStore(held=())
        mirror = managed.Mirror(db, [store], "rag_engine", policy_for=lambda t: "in", audit=lambda *a, **k: None)
        lines = managed.sync(mirror, "globex")
        self.assertEqual(store.uploaded, [])
        self.assertEqual(lines[0]["failed_or_not_permitted"], ["globex_msa"])


if __name__ == "__main__":
    unittest.main()
