"""rag-api's handler for a model 429 (21 October 2026): the default model's quota running out leaves /v1/query as a 429
with a reason and a Retry-After, not a bare 500 in plain text; every other model error still leaves as a 500, which
lesson 11.3's gate relies on (a typo in GENERATOR_MODEL must fail it).

The handler block of services/rag-api/main.py is run on a bare FastAPI app with two routes that raise google-genai's
own errors, so neither the API's settings nor a network is needed. Skipped where fastapi or google-genai is not
installed; DOCUMIND_REQUIRE_LIBS=1 turns the skip into a failure, as the chat-pins CI job sets it.
"""
import importlib.util
import json
import logging
import os
from pathlib import Path
import unittest

MAIN = Path(__file__).resolve().parents[2] / "services/rag-api/main.py"
HAVE = all(importlib.util.find_spec(m) is not None for m in ("fastapi", "google.genai", "httpx"))
if os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1" and not HAVE:
    raise RuntimeError("DOCUMIND_REQUIRE_LIBS=1 but fastapi, google-genai or httpx is missing")


@unittest.skipUnless(HAVE, "fastapi and google-genai are not installed here")
class ModelQuotaTests(unittest.TestCase):
    def setUp(self):
        from fastapi import FastAPI, Request
        from fastapi.testclient import TestClient
        from google.genai import errors
        src = MAIN.read_text(encoding="utf-8")
        block = src[src.index("# A 429 from the default model is the caller's to see"):
                    src.index("# verify_iap and enforce_membership live in auth.py")]
        app = FastAPI()
        exec(block, {"app": app, "log": logging.getLogger("test"), "json": json, "Request": Request})

        @app.get("/quota")
        def quota():
            raise errors.ClientError(429, {"error": {"code": 429, "message": "Resource exhausted", "status": "RESOURCE_EXHAUSTED"}})

        @app.get("/typo")
        def typo():
            raise errors.ClientError(404, {"error": {"code": 404, "message": "model not found", "status": "NOT_FOUND"}})

        self.client = TestClient(app, raise_server_exceptions=False)

    def test_a_model_429_leaves_as_a_429_with_its_reason(self):
        r = self.client.get("/quota")
        self.assertEqual((r.status_code, r.headers.get("retry-after")), (429, "30"))
        self.assertIn("RESOURCE_EXHAUSTED", r.json()["detail"])

    def test_any_other_model_error_still_leaves_as_a_500(self):
        self.assertEqual(self.client.get("/typo").status_code, 500)


if __name__ == "__main__":
    unittest.main()
