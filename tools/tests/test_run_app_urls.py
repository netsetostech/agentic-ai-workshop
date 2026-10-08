"""A Cloud Run service answers on two run.app URLs: gcloud's status.url, generally the hashed ...a.run.app one, and the
deterministic documind-X-NUMBER.REGION.run.app one - each service's SELF_URL, the only audience its bearer tokens are
verified for (shared/iap.py). Lesson 2.1's preflight demanded API == status.url and stopped on a correct lane; lesson
4.2 minted the judge's chat token for status.url (26 September 2026). These tests run the pages' own code."""
import html
import os
import re
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[2]
LESSONS = ROOT / "lessons"


def page(glob):
    return html.unescape(next(LESSONS.glob(glob)).read_text(encoding="utf-8"))


PAGE51 = page("02-retrieval/2.1-*/Netsetos_*_WIX.html")
CHECK = re.search(r"^urls = .*?\n    raise SystemExit\(.*?\)\n", PAGE51, re.M | re.S).group(0)
HASHED = "https://documind-api-abcdefghij-el.a.run.app"
DETERMINISTIC = "https://documind-api-123456789012.asia-south1.run.app"


def run_check(api, status_url):
    with mock.patch.dict(os.environ, {"API": api, "NUMBER": "123456789012"}):
        exec(CHECK, {"os": os, "service": {"status": {"url": status_url}}, "region": "asia-south1"})


class Lesson51Preflight(unittest.TestCase):
    def test_the_deterministic_url_passes_when_status_url_is_the_hashed_one(self):
        run_check(DETERMINISTIC, HASHED)

    def test_status_url_itself_passes(self):
        run_check(HASHED + "/", HASHED)

    def test_any_other_url_stops_and_names_both(self):
        with self.assertRaises(SystemExit) as stop:
            run_check("https://candidate---documind-api-123456789012.asia-south1.run.app", HASHED)
        self.assertIn(DETERMINISTIC, stop.exception.code)
        self.assertIn(HASHED, stop.exception.code)


class Lesson72ChatToken(unittest.TestCase):
    def test_the_judge_calls_the_chat_service_at_its_self_url(self):
        chat_self_url = re.search(r"SELF_URL=(https://documind-chat-\S+?\.run\.app)",
                                  (ROOT / "deploy/commands/lesson-12.8.sh").read_text(encoding="utf-8")).group(1)
        self.assertEqual(chat_self_url, "https://documind-chat-$PROJECT_NUMBER.${REGION:-us-central1}.run.app")
        self.assertIn('CHAT_URL="https://documind-chat-$NUMBER.$REGION.run.app"', page("04-evals-safety/4.2-*/Netsetos_*_WIX.html"))


class NoAddressFromStatusUrl(unittest.TestCase):
    def test_no_page_takes_a_service_address_from_status_url(self):
        offenders = [p.name for p in LESSONS.glob("*/*/Netsetos_*_WIX.html")
                     if re.search(r"\$\(gcloud run services describe[^\n]*value\(status\.url\)",
                                  html.unescape(p.read_text(encoding="utf-8")))]
        self.assertEqual(offenders, [])


if __name__ == "__main__":
    unittest.main()
