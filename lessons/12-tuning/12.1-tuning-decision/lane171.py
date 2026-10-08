"""The stand-in lane for lesson 12.1's build. Under it the kit's own code runs unchanged: evals/make_trainset.py for
make trainset (main(), from the corpus mirrors to the frozen files and the upload), and the page's cells that read
Cloud Logging and the datasets bucket. (The gate's run, make eval-live, is the kit's run_eval.live() over a stub API in
build.py itself, as lesson 4.2's build runs it.)

What is stood in, and how:
  Gemini         make_trainset's one structured call per chunk: a question, an answer, a quote and an unanswerable
                 question, derived from the passage (its title and first sentence; the quote is the sentence's
                 first words, copied with the line breaks collapsed, as the live model copies them). For --style
                 helpdesk (step 7) the teacher's pair as well: a verdict (the first quantity the passage states),
                 its first prose sentence as the reason, the clause it prints, and the Hinglish twin - with one
                 passage in 29 quoting what it does not say and one in 31 answering the twin in English.
  DLP            shared/pii.inspect_many: an Indian PAN, GSTIN, Aadhaar or mobile number, or an email address, is a
                 finding - lesson 12.2's list, since v3 scans the chunks and both lanes must drop the same rows.
  Cloud Storage  a JSON file of objects: the datasets bucket make trainset uploads to.
  Cloud Logging  a JSON file of entries: the API's usage rows for the last week and the generator's own events;
                 gcloud logging read filters them (clauses joined by AND, newest first).
"""
import base64
import datetime as dt
import json
import os
import re
import subprocess
import sys
import types
from types import SimpleNamespace

PATHS = {k: os.environ[f"LANE171_{k.upper()}"] for k in ("gcs", "logs")}


def _load(name: str) -> dict:
    try:
        with open(PATHS[name], encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save(name: str, state: dict) -> None:
    tmp = PATHS[name] + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, PATHS[name])


# ---- the clock: each process starts at LANE171_NOW
_DATETIME = dt.datetime
_T0 = _DATETIME.fromisoformat(os.environ.get("LANE171_NOW", "2026-09-24T08:00:00+00:00"))


def freeze() -> None:
    class _Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            return _T0.astimezone(tz) if tz else _T0.replace(tzinfo=None)

        @classmethod
        def utcnow(cls):
            return _T0.replace(tzinfo=None)

    class _Date(dt.date):
        @classmethod
        def today(cls):
            return _T0.date()
    dt.datetime, dt.date = _Frozen, _Date


# ---- Cloud Storage
class Blob:
    def __init__(self, bucket: str, name: str):
        self.bucket_name, self.name = bucket, name

    def upload_from_filename(self, path, **kw):
        with open(path, "rb") as f:
            self.upload_from_string(f.read())

    def upload_from_string(self, data, content_type=None, **kw):
        st = _load("gcs")
        raw = data.encode("utf-8") if isinstance(data, str) else bytes(data)
        st.setdefault(self.bucket_name, {})[self.name] = base64.b64encode(raw).decode()
        _save("gcs", st)

    def exists(self, **kw):
        return self.name in _load("gcs").get(self.bucket_name, {})

    def download_as_bytes(self, **kw):
        v = _load("gcs").get(self.bucket_name, {}).get(self.name)
        if v is None:
            from google.api_core.exceptions import NotFound
            raise NotFound(f"gs://{self.bucket_name}/{self.name}")
        return base64.b64decode(v)

    def download_as_text(self, encoding="utf-8", **kw):
        return self.download_as_bytes().decode(encoding)


class Bucket:
    def __init__(self, name: str):
        self.name = name

    def blob(self, name, **kw):
        return Blob(self.name, name)

    def list_blobs(self, prefix=None, **kw):
        return [Blob(self.name, n) for n in sorted(_load("gcs").get(self.name, {})) if not prefix or n.startswith(prefix)]


class GCSClient:
    def __init__(self, *a, **kw):
        pass

    def bucket(self, name):
        return Bucket(name)


# ---- Gemini: make_trainset's pair, from the passage. LANE171_TITLES maps a passage's sha256 to its document's title
# and, where the passage has one, a section heading - what a reader of the page would name it by.
STOP = set("the a an of and or to in on for by with as at from this that these those is are be shall any such which "
           "who under section act code it its his her their than other all".split())


def _pair(body: str, title: str, heading: str) -> dict:
    flat = re.sub(r"\s+", " ", body).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.;:])\s+", flat) if len(s.strip()) > 60]
    first = sentences[0] if sentences else flat[:240]
    words = first.split()
    if heading:
        topic = heading
    else:
        content = [w.strip(".,;:()[]\"'") for w in words if w.lower().strip(".,;:()[]\"'") not in STOP and len(w) > 3 and w.isalpha()]
        topic = " ".join(content[:2]).lower() or "this passage"
    return {"question": f"What does {title} say about {topic}?",
            "answer": (" ".join(words[:40]) + ("..." if len(words) > 40 else "")),
            "quote": " ".join(words[:min(len(words), 22)]),
            "unanswerable_question": f"Does {title} set a time limit for {topic}?"}


_TITLES = {}
CLAUSE = re.compile(r"\b([A-Z]{2,4}(?:-[A-Z]{2,4})?-\d{2,3})\b")
NUMBER = re.compile(r"\b(\d[\d,.]*\s*(?:per cent|%|days?|weeks?|months?|years?|hours?|crore|lakh|rupees|workers|employees)|"
                    r"(?:one|two|three|five|six|seven|eight|ten|twelve|fifteen|twenty|thirty|forty|fifty|sixty|ninety|hundred)"
                    r"(?:[ -][a-z]+)?\s+(?:per cent|days?|weeks?|months?|years?|hours?|workers|employees))\b", re.I)


def _helpdesk(body: str, title: str, heading: str, sha: str) -> dict:
    """The teacher's helpdesk pair, derived from the passage as _pair derives the plain one: the verdict is the first
    quantity the passage states (else what it is about), the reason its first sentence, the clause the label it prints.
    One passage in 29 comes back with a quote that is not in it, and one in 31 with a 'Hinglish' twin in English - the
    two ways a live teacher's answer fails the kit's checks."""
    p = _pair(body, title, heading)
    flat = re.sub(r"\s+", " ", body).strip()
    sentences = [s.strip() for s in re.split(r"(?<=[.;:])\s+", flat) if len(s.strip()) > 60]
    prose = [s for s in sentences if re.search(r"\b(shall|means|is|are|may|be)\b", s)
             and sum(ch.isupper() for ch in s) < 0.2 * sum(ch.isalpha() for ch in s)]
    first = (prose or sentences or [flat[:240]])[0]
    words = first.split()
    why = " ".join(words[:30]).rstrip(",;:-")
    num = NUMBER.search(first)
    topic = heading or "this passage"
    section = re.search(r"\(section (\d+[A-Z]?)\)", topic)
    code = CLAUSE.search(flat[:400])
    clause = f"Section {section.group(1)}" if section else (code.group(1) if code else "")
    verdict = num.group(1).strip() if num else (f"Set out in {clause}" if clause else topic[:1].upper() + topic[1:])
    quote = p["quote"]
    n = int(sha[:8], 16)
    if n % 29 == 0:
        quote = quote.lower().replace(" the ", " a ", 1) + " as amended"
    cap = title[:1].upper() + title[1:]
    hinglish_q = f"{cap} mein {topic} ke baare mein kya likha hai?"
    if n % 31 == 0:
        hinglish_q = p["question"]
    return {"question": p["question"], "verdict": " ".join(verdict.split()[:8]), "why": why, "clause": clause, "quote": quote,
            "unanswerable_question": p["unanswerable_question"], "question_hinglish": hinglish_q, "verdict_hinglish": " ".join(verdict.split()[:8]),
            "why_hinglish": f"{cap} ke is hisse mein likha hai: {why}", "unanswerable_question_hinglish": f"Kya {title} mein {topic} ki koi time limit di gayi hai?"}


class Models:
    def generate_content(self, model, contents, config=None):
        passage = contents if isinstance(contents, str) else contents[0]
        body = passage.split("\n\nPassage:\n", 1)[-1]
        if not _TITLES and os.environ.get("LANE171_TITLES"):
            with open(os.environ["LANE171_TITLES"], encoding="utf-8") as f:
                _TITLES.update(json.load(f))
        import hashlib
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        t = _TITLES.get(sha, {})
        if "again in Hinglish" in passage:                         # make_trainset.ask_helpdesk's call: --style helpdesk
            p = _helpdesk(body, t.get("title", "the document"), t.get("heading", ""), sha)
        else:
            p = _pair(body, t.get("title", "the document"), t.get("heading", ""))
        return SimpleNamespace(parsed=SimpleNamespace(**p), text=json.dumps(p))


class GenaiClient:
    def __init__(self, *a, **kw):
        self.models = Models()


# ---- DLP: shared/pii.inspect_many's contract - a list of findings per text, never the matched value
PII = [("INDIA_GST_INDIVIDUAL", re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b")),      # lesson 12.2's list: v3 scans every
       ("INDIA_PAN_INDIVIDUAL", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")),                              # chunk, so both lanes must find the
       ("INDIA_AADHAAR_INDIVIDUAL", re.compile(r"\b\d{4} \d{4} \d{4}\b")),                              # same things in the same chunks
       ("PHONE_NUMBER", re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b")),
       ("EMAIL_ADDRESS", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b"))]


def inspect_many(texts):
    return [[{"info_type": name} for name, rx in PII if rx.search(t)] for t in texts]


def install() -> None:
    """Gemini, DLP and Cloud Storage, for make_trainset.py and the page's cells."""
    import google.genai
    google.genai.Client = GenaiClient
    m = types.ModuleType("google.cloud.storage")
    m.Client = GCSClient
    sys.modules["google.cloud.storage"] = m
    import google.cloud
    google.cloud.storage = m
    import shared
    pii = types.ModuleType("shared.pii")
    pii.inspect_many = inspect_many
    sys.modules["shared.pii"] = pii
    shared.pii = pii


# ---- Cloud Logging, read by gcloud logging read
def _stamp(s: str):
    return _DATETIME.fromisoformat(s.replace("Z", "+00:00"))


def logging_read(cmd: list) -> str:
    opts = dict(c[2:].split("=", 1) for c in cmd[4:] if c.startswith("--") and "=" in c)
    clauses = [c.strip() for c in cmd[3].split(" AND ")]

    def value(e, path):
        cur = e
        for p in path.split("."):
            cur = cur.get(p) if isinstance(cur, dict) else None
        return cur

    def holds(e) -> bool:
        for c in clauses:
            m = re.fullmatch(r'([\w.]+)\s*(>=|=)\s*"([^"]*)"', c)
            if not m:
                raise SystemExit(f"the stand-in cannot read the filter clause {c!r}")
            path, op, want = m.groups()
            got = value(e, path)
            if op == "=" and str(got) != want:
                return False
            if op == ">=" and not (got and _stamp(str(got)) >= _stamp(want)):
                return False
        return True
    rows = sorted((e for e in _load("logs").get("entries", []) if holds(e)), key=lambda e: _stamp(e["timestamp"]), reverse=True)
    return json.dumps(rows[:int(opts.get("limit", 10))])


def fake_cli() -> None:
    real_run = subprocess.run

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and list(cmd[:3]) == ["gcloud", "logging", "read"]:
            return subprocess.CompletedProcess(list(cmd), 0, logging_read(list(cmd)), "")
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "gcloud":
            raise SystemExit(f"the stand-in has no answer for {cmd[:4]}")
        return real_run(cmd, *a, **kw)
    subprocess.run = run
