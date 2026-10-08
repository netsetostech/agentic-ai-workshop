"""Lesson 1.1 behavior regressions: all cloud responses are fakes, never credentials."""
from copy import deepcopy
from dataclasses import replace
import importlib.util
from io import BytesIO
import json
import os
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch
from urllib.error import HTTPError

from workshop_helpers.artifacts import write_json
from workshop_helpers.config import load_config
from workshop_helpers.lesson31 import (LessonCloud, poll_until, prepare_cache, require_fresh_vector,
                                       restore_cache, version_ready)
from workshop_helpers.session import DemoSession

KIT = Path(__file__).resolve().parents[2]
LESSON = KIT / "workshop_demos/module_01/lesson_1_1"


def load_demo(relative):
    """Import definitions only, just as the offline whole-course checker does."""
    spec = importlib.util.spec_from_file_location("lesson31_test_demo", LESSON / relative)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class VersionEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.expected = dict(tenant="acme", name="acme/example.md", uri="gs://example/acme/example.md",
                             generation="42", sha256="abc", doc_key="acme_abc")
        self.source = {**self.expected, "tenant_id": "acme", "gcs_uri": self.expected["uri"], "status": "indexed", "chunks": 1}
        self.claim = {"tenant_id": "acme", "gcs_uri": self.expected["uri"], "status": "indexed", "chunks": 1, "generation": "40"}
        self.chunks = {"acme:abc#0": dict(current=True, tenant_id="acme", doc_key="acme_abc", source_uri=self.expected["uri"])}

    def test_exact_current_source_not_old_content_claim_generation(self):
        self.assertTrue(version_ready(self.expected, self.source, self.claim, self.chunks))

    def test_stale_unrelated_missing_queued_and_incomplete_never_pass(self):
        for changes in ({"generation": "41"}, {"doc_key": "acme_old"}, {"sha256": "other"},
                        {"tenant_id": "zeta"}, {"status": "retired"}, {"chunks": 2}, {"name": "acme/other.md"}):
            with self.subTest(source=changes):
                self.assertFalse(version_ready(self.expected, {**self.source, **changes}, self.claim, self.chunks))
        for claim in ({}, {**self.claim, "status": "queued"}, {**self.claim, "gcs_uri": "gs://other"}):
            self.assertFalse(version_ready(self.expected, self.source, claim, self.chunks))
        bad = deepcopy(self.chunks)
        bad["acme:abc#0"]["current"] = False
        self.assertFalse(version_ready(self.expected, self.source, self.claim, bad))
        self.assertFalse(version_ready(self.expected, self.source, self.claim, {}))

    def test_poll_transitions_and_deadline(self):
        clock = Mock(side_effect=[0, 0, 1, 2])
        read = Mock(side_effect=[{"summary": "queued"}, {"summary": "indexed"}])
        sleep = Mock()
        result = poll_until(read, lambda r: r["summary"] == "indexed", 2, 1, clock=clock, sleep=sleep)
        self.assertEqual(result["summary"], "indexed")
        sleep.assert_called_once_with(1)
        with self.assertRaisesRegex(TimeoutError, "queued"):
            poll_until(lambda: {"summary": "queued"}, lambda _: False, 2, 1,
                       clock=Mock(side_effect=[0, 0, 1, 2]), sleep=Mock())

    def test_cache_and_firestore_fallback_cannot_claim_vector_proof(self):
        good = {"cache_hit": "none", "stages": {"retrieval_backend": "vector", "pool": 20, "vector_chunks": 20}}
        require_fresh_vector(good)
        for answer in ({**good, "cache_hit": "semantic"},
                       {**good, "stages": {**good["stages"], "vector_chunks": 0}},
                       {**good, "stages": {**good["stages"], "retrieval_backend": "rag_engine"}}, {}):
            with self.assertRaises(RuntimeError):
                require_fresh_vector(answer)


class IOTests(unittest.TestCase):
    def setUp(self):
        self.cloud = LessonCloud.__new__(LessonCloud)
        self.cloud.session = SimpleNamespace(config=load_config(), identity_token=Mock(return_value="not-to-be-saved"))
        self.cloud.save = Mock()

    def test_full_large_response_saved_before_display(self):
        response = BytesIO(json.dumps({"sources": ["a" * 1000] * 1000}).encode())
        response.code, response.headers = 200, {"Content-Type": "application/json"}
        with patch.dict(os.environ, API="https://example.invalid"), patch("workshop_helpers.lesson31.urlopen", return_value=response):
            result = self.cloud.request("large", "/v1/sources")
        self.assertEqual(len(result["json"]["sources"]), 1000)
        self.assertNotIn("not-to-be-saved", str(self.cloud.save.call_args))

    def test_expected_html_refusal_and_unexpected_http_error(self):
        def response():
            return HTTPError("https://example.invalid", 403, "Forbidden", {"Content-Type": "text/html"}, BytesIO(b"<html>Forbidden</html>"))
        with patch.dict(os.environ, API="https://example.invalid"), patch("workshop_helpers.lesson31.urlopen", side_effect=response()):
            got = self.cloud.request("anonymous", "/v1/query", {}, identity="none", expected_status=403)
        self.assertIsNone(got["json"])
        self.cloud.session.identity_token.assert_not_called()
        with patch.dict(os.environ, API="https://example.invalid"), patch("workshop_helpers.lesson31.urlopen", side_effect=response()):
            with self.assertRaisesRegex(RuntimeError, "expected HTTP 200"):
                self.cloud.request("member", "/v1/query", {})

    def test_fixture_ui_required_no_overwrite_identical_reused_new_guarded(self):
        class NotFound(Exception):
            pass
        fake = {"google.api_core.exceptions": SimpleNamespace(NotFound=NotFound)}
        blob = Mock(size=3, generation=42)
        blob.download_as_bytes.return_value = b"abc"
        self.cloud.bucket = SimpleNamespace(name="example", blob=Mock(return_value=blob))
        with patch.dict(sys.modules, fake), patch.object(sys, "path", [str(KIT), *sys.path]):
            row = self.cloud.fixture("acme", "example.md", b"abc", upload=True)
            self.assertEqual(row["generation"], "42")
            blob.upload_from_string.assert_not_called()
            blob.download_as_bytes.return_value = b"xyz"
            with self.assertRaisesRegex(RuntimeError, "differs"):
                self.cloud.fixture("acme", "example.md", b"abc", upload=True)
            blob.upload_from_string.assert_not_called()
            blob.reload.side_effect = NotFound()
            with self.assertRaisesRegex(RuntimeError, "Upload evals/demo"):
                self.cloud.fixture("acme", "example.md", b"abc", upload=False)
            blob.upload_from_string.assert_not_called()
            blob.download_as_bytes.return_value = b"abc"
            self.cloud.fixture("zeta", "example.md", b"abc", upload=True)
            self.assertEqual(blob.upload_from_string.call_args.kwargs["if_generation_match"], 0)

    def test_log_filter_uses_all_three_exact_identifiers(self):
        expected = {"tenant": "zeta", "doc_key": "zeta_abc", "generation": "42"}
        with patch("workshop_helpers.lesson31.gcloud", return_value="[]") as command:
            self.cloud.worker_logs(expected)
        query = command.call_args.args[2]
        for field, value in (("tenant", "zeta"), ("doc_key", "zeta_abc"), ("generation", "42")):
            self.assertIn(f'jsonPayload.{field}="{value}"', query)


class FakeCloudRun:
    """Revisions, the service configuration and traffic, answering the gcloud calls the cache helpers make.

    Traffic is pinned to a revision by name, as the kit leaves it after every deploy (F44).
    """

    def __init__(self):
        self.revisions, self.calls = {}, []
        self.copy_digest = self.fail_update = None
        self.serving = self.latest = self.add("documind-api-r1", "on")

    def add(self, name, cache, **extra_env):
        env = [{"name": "RETRIEVAL_BACKEND", "value": "vector"}, {"name": "SEMANTIC_CACHE", "value": cache}]
        env += [{"name": key, "value": value} for key, value in extra_env.items()]
        self.revisions[name] = {"spec": {"serviceAccountName": "documind-api-sa@p.iam.gserviceaccount.com",
                                         "containers": [{"image": "asia-south1-docker.pkg.dev/p/documind/api:abc",
                                                         "resources": {"limits": {"cpu": "2", "memory": "1Gi"}}, "env": env}]},
                                "status": {"imageDigest": "asia-south1-docker.pkg.dev/p/documind/api@sha256:aaa"}}
        return name

    def gcloud(self, *args, timeout=90):
        verb = " ".join(args[:3])
        self.calls.append(verb)
        if verb == "run services describe":
            return json.dumps({"status": {"latestCreatedRevisionName": self.latest, "latestReadyRevisionName": self.latest}})
        if verb == "run revisions describe":
            return json.dumps(self.revisions[args[3]])
        if verb == "run services update":
            if self.fail_update:
                raise self.fail_update
            assert "--no-traffic" in args and "--update-env-vars=SEMANTIC_CACHE=off" in args, args
            copy = deepcopy(self.revisions[self.latest])          # Cloud Run builds from the configuration
            copy["spec"]["containers"][0]["env"][1]["value"] = "off"
            if self.copy_digest:
                copy["status"]["imageDigest"] = self.copy_digest
            self.latest = f"documind-api-r{len(self.revisions) + 1}"
            self.revisions[self.latest] = copy
            return ""
        if verb == "run services update-traffic":
            target, percent = next(a for a in args if a.startswith("--to-revisions=")).split("=", 1)[1].split("=")
            assert percent == "100", args
            self.serving = target
            return ""
        raise AssertionError(args)

    def read_serving(self, config, service):
        env = {row["name"]: row["value"] for row in self.revisions[self.serving]["spec"]["containers"][0]["env"]}
        return SimpleNamespace(revision=self.serving, environment=env)

    def patched(self):
        return patch.multiple("workshop_helpers.lesson31", gcloud=self.gcloud, read_serving=self.read_serving)


class PreparationTests(unittest.TestCase):
    def setUp(self):
        self.session = SimpleNamespace(config=load_config(), state={}, save=Mock())
        self.cloud = FakeCloudRun()

    def test_no_cache_update_when_already_off_or_opted_out(self):
        self.cloud.revisions["documind-api-r1"]["spec"]["containers"][0]["env"][1]["value"] = "off"
        with self.cloud.patched():
            prepare_cache(self.session)
        self.assertEqual(self.cloud.calls, [])
        self.cloud.revisions["documind-api-r1"]["spec"]["containers"][0]["env"][1]["value"] = "on"
        with self.cloud.patched(), self.assertRaisesRegex(RuntimeError, "DISABLE_ANSWER_CACHE"):
            prepare_cache(self.session, disable=False)

    def test_traffic_pinned_by_name_moves_to_a_cache_off_copy_and_back(self):
        with self.cloud.patched():
            prepare_cache(self.session)
            self.assertEqual(self.cloud.serving, "documind-api-r2")
            self.assertEqual(self.cloud.read_serving(None, None).environment["SEMANTIC_CACHE"], "off")
            self.assertEqual(self.session.state["lesson31_cache"], {"previous": "on", "restore_required": True,
                                                                    "revision_before": "documind-api-r1",
                                                                    "revision_after": "documind-api-r2"})
            restore_cache(self.session)
        self.assertEqual(self.cloud.serving, "documind-api-r1")
        self.assertFalse(self.session.state["lesson31_cache"]["restore_required"])
        self.assertEqual(self.cloud.calls.count("run services update"), 1)       # restoring rebuilds nothing

    def test_an_earlier_lessons_copy_is_reused(self):
        self.cloud.latest = self.cloud.add("documind-api-r2", "off")
        with self.cloud.patched():
            prepare_cache(self.session)
        self.assertNotIn("run services update", self.cloud.calls)
        self.assertEqual(self.cloud.serving, "documind-api-r2")

    def test_a_candidates_configuration_refuses_before_any_change(self):
        self.cloud.latest = self.cloud.add("documind-api-r3", "on", RETRIEVAL_MODE="hybrid")
        with self.cloud.patched(), self.assertRaisesRegex(RuntimeError, "candidate"):
            prepare_cache(self.session)
        self.assertEqual(self.cloud.serving, "documind-api-r1")
        self.assertFalse({"run services update", "run services update-traffic"} & set(self.cloud.calls))
        self.assertFalse(self.session.state)

    def test_a_copy_on_another_image_never_gets_traffic(self):
        self.cloud.copy_digest = "asia-south1-docker.pkg.dev/p/documind/api@sha256:bbb"   # the tag moved since
        with self.cloud.patched():
            with self.assertRaisesRegex(RuntimeError, "traffic was not moved"):
                prepare_cache(self.session)
            self.assertNotIn("run services update-traffic", self.cloud.calls)
            restore_cache(self.session)                     # nothing moved, so nothing to route back
        self.assertEqual(self.cloud.serving, "documind-api-r1")
        self.assertFalse(self.session.state["lesson31_cache"]["restore_required"])

    def test_failed_deployment_retains_original_then_cleanup_recovers(self):
        self.cloud.fail_update = TimeoutError("deployment pending")
        with self.cloud.patched():
            with self.assertRaises(TimeoutError):
                prepare_cache(self.session)
            self.assertEqual(self.session.state["lesson31_cache"],
                             {"previous": "on", "restore_required": True, "revision_before": "documind-api-r1"})
            restore_cache(self.session)
        self.assertFalse(self.session.state["lesson31_cache"]["restore_required"])
        self.assertNotIn("run services update-traffic", self.cloud.calls)

    def test_restore_refuses_when_someone_else_moved_traffic(self):
        with self.cloud.patched():
            prepare_cache(self.session)
            self.cloud.serving = self.cloud.add("documind-api-r9", "off", RETRIEVAL_MODE="hybrid")
            calls = len(self.cloud.calls)
            with self.assertRaisesRegex(RuntimeError, "documind-api-r1"):
                restore_cache(self.session)
        self.assertNotIn("run services update-traffic", self.cloud.calls[calls:])
        self.assertTrue(self.session.state["lesson31_cache"]["restore_required"])

    def test_finish_attempts_backend_even_when_cache_restore_fails(self):
        finish = load_demo("setup/finish.py")
        self.session.state["backend_restore_required"] = True
        self.session.restore_backend = Mock()
        with patch.object(finish, "restore_cache", side_effect=RuntimeError("cache failed")):
            with self.assertRaisesRegex(RuntimeError, "cache failed"):
                finish.demonstrate(self.session)
        self.session.restore_backend.assert_called_once()
        self.assertNotIn("lesson31_closed", self.session.state)

    def test_nested_setup_and_order_with_real_session(self):
        with tempfile.TemporaryDirectory() as tmp:
            config = replace(load_config(), project="test-project", results_dir=Path(tmp))
            with DemoSession(LESSON / "setup/prepare.py", live=False, config=config):
                pass
            with self.assertRaisesRegex(RuntimeError, "prerequisite"):
                with DemoSession(LESSON / "demo_05_version_the_bytes_decide_and_the_same_file_in_two_tenants_proves_it.py", live=False, config=config):
                    pass
            with DemoSession(LESSON / "setup/finish.py", live=False, config=config):
                pass

    def test_actual_kit_local_validators(self):
        with patch.object(sys, "path", [str(KIT), *sys.path]):
            load_demo("demo_08_why_it_is_built_this_way_the_failures_behind_each_rule.py").prove_local_contract_rules()


if __name__ == "__main__":
    unittest.main()
