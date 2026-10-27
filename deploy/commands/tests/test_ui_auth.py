"""The UI's and the admin console's IAP check (21 October 2026): a Streamlit tab carries the assertion IAP signed when
it opened, good for ten minutes. The UI verifies it on every rerun, because the API verifies the same forwarded
assertion on every call, and an expired one asks for a reload instead of "Contact admin". The admin console forwards
it to nothing, so it verifies a token once, keeps the identity for the session, verifies any other token afresh, and
reads the admin list on every rerun.

Both auth.py files are loaded against a stand-in streamlit module; the signature check itself is replaced, so no key
or network is needed. Skipped where PyJWT or google-auth is not installed; DOCUMIND_REQUIRE_LIBS=1 turns the skip
into a failure.
"""
import importlib.util
import os
from pathlib import Path
import sys
import types
import unittest
from unittest import mock

SERVICES = Path(__file__).resolve().parents[2] / "services"
HAVE = all(importlib.util.find_spec(m) is not None for m in ("jwt", "google.oauth2"))
if os.environ.get("DOCUMIND_REQUIRE_LIBS") == "1" and not HAVE:
    raise RuntimeError("DOCUMIND_REQUIRE_LIBS=1 but PyJWT or google-auth is missing")


class Stop(Exception):
    """st.stop()"""


def fake_streamlit(token: str):
    st = types.ModuleType("streamlit")
    st.session_state, st.errors = {}, []
    st.context = types.SimpleNamespace(headers={"x-goog-iap-jwt-assertion": token})
    st.error = st.errors.append
    st.stop = lambda: (_ for _ in ()).throw(Stop())
    st.title = st.button = lambda *a, **k: None
    st.cache_resource = lambda **k: (lambda f: f)
    return st


def load(path: Path, st):
    spec = importlib.util.spec_from_file_location(f"auth_under_test_{path.parent.name}", path)
    module = importlib.util.module_from_spec(spec)
    with mock.patch.dict(sys.modules, {"streamlit": st}):
        spec.loader.exec_module(module)
    return module


@unittest.skipUnless(HAVE, "PyJWT and google-auth are not installed here")
class FrontendTests(unittest.TestCase):
    def setUp(self):
        os.environ["AUTH_MODE"] = "iap"
        self.st = fake_streamlit("tok-1")
        self.auth = load(SERVICES / "frontend/auth.py", self.st)
        self.calls = []

    def tearDown(self):
        os.environ.pop("AUTH_MODE", None)

    def verify(self, token, audience):
        self.calls.append(token)
        return {"email": "asha@acme.example", "sub": "123"}

    def test_the_token_is_verified_on_every_rerun(self):
        # the API checks the same forwarded assertion on every call: a UI that kept the email answered with 401s
        with mock.patch.object(self.auth, "_verify_iap_jwt", self.verify):
            first, second = self.auth.current_user(), self.auth.current_user()
        self.assertEqual(first, second)
        self.assertEqual(first["email"], "asha@acme.example")
        self.assertEqual(self.calls, ["tok-1", "tok-1"])

    def test_an_expired_token_asks_for_a_reload_not_an_admin(self):
        def expired(token, audience):
            raise self.auth.jwt.ExpiredSignatureError("Signature has expired")
        with mock.patch.object(self.auth, "_verify_iap_jwt", expired):
            with self.assertRaises(Stop):
                self.auth.login_gate()
        self.assertEqual(self.st.errors, ["This tab's sign-in has expired: reload the page to sign in again."])

    def test_a_forged_token_is_still_refused(self):
        def bad(token, audience):
            raise self.auth.jwt.InvalidSignatureError("Signature verification failed")
        with mock.patch.object(self.auth, "_verify_iap_jwt", bad):
            self.assertFalse(self.auth.current_user()["is_logged_in"])
        self.assertTrue(self.st.errors[0].startswith("IAP JWT verification failed"))


@unittest.skipUnless(HAVE, "PyJWT and google-auth are not installed here")
class AdminTests(unittest.TestCase):
    def setUp(self):
        env = {"IAP_AUDIENCE": "/projects/1/locations/asia-south1/services/documind-admin", "ADMIN_EMAILS": "ops@acme.example"}
        self.env = mock.patch.dict(os.environ, env)
        self.env.start()
        self.st = fake_streamlit("tok-1")
        self.auth = load(SERVICES / "admin/auth.py", self.st)
        self.calls = []

    def tearDown(self):
        self.env.stop()

    def verify(self, token, request, audience, certs_url):
        self.calls.append(token)
        return {"email": "ops@acme.example", "sub": "9"}

    def test_verified_once_and_the_admin_list_read_every_rerun(self):
        with mock.patch.object(self.auth.id_token, "verify_token", self.verify):
            self.assertEqual(self.auth.current_user()["email"], "ops@acme.example")
            self.auth.ADMIN_EMAILS = ["someone-else@acme.example"]          # taken off the list mid-session
            with self.assertRaises(Stop):
                self.auth.current_user()
        self.assertEqual(self.calls, ["tok-1"])
        self.assertEqual(self.st.errors, ["403 - Admins only"])

    def test_an_expired_token_says_reload(self):
        def expired(*a, **k):
            raise ValueError("Token expired")
        with mock.patch.object(self.auth.id_token, "verify_token", expired):
            with self.assertRaises(Stop):
                self.auth.current_user()
        self.assertIn("reload the page", self.st.errors[0])


if __name__ == "__main__":
    unittest.main()
