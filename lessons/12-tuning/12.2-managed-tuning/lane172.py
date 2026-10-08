"""The stand-in lane for lesson 12.2's build. Under it the kit's own code runs unchanged: evals/make_trainset.py (to
leave the datasets bucket as lesson 12.1 leaves it), evals/tune.py for make tune and its poll, and the page's cells that
validate the frozen file and call the tuned endpoint.

What is stood in, and how:
  Gemini          make_trainset's pair call and its --style helpdesk teacher (as lesson 12.1's lane writes them, so v2
                  and v3 here are v2 and v3 there); the tuning service, which takes a validation file, with Google's rules
                  for the two tunable Gemini 3 bases (tuning in us-central1 or europe-west4, adapter sizes 1, 2, 4, 8
                  and 16, the endpoint served from the `us` multi-region); the tuned endpoint, which answers only where
                  its path says it lives and 404s elsewhere, as the first live one did on 10 September 2026.
  DLP             shared/pii.inspect_many: an Indian PAN, GSTIN, Aadhaar or mobile number, or an email address, is a
                  finding (never the value); PERSON_NAME and DATE_OF_BIRTH are not modelled.
  Cloud Storage   a JSON file of objects: the datasets bucket.
  Firestore       tenant_settings, as the kit's lane seeds it: acme and zeta `any`, globex `in`.
  The clock       each process starts at LANE172_NOW; time.sleep moves the clock, not the process.
"""
import base64
import datetime as dt
import hashlib
import json
import os
import re
import sys
import time
import types
from types import SimpleNamespace

PATHS = {k: os.environ[f"LANE172_{k.upper()}"] for k in ("gcs", "jobs")}


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


# ---- the clock
_DATETIME = dt.datetime
_T0 = _DATETIME.fromisoformat(os.environ.get("LANE172_NOW", "2026-09-24T09:00:00+00:00"))
_EPOCH0 = _T0.timestamp()
_SLEPT = [0.0]
_REAL_STRFTIME = time.strftime


def now() -> float:
    return _EPOCH0 + _SLEPT[0]


def freeze() -> None:
    class _Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            t = _DATETIME.fromtimestamp(now(), dt.timezone.utc)
            return t.astimezone(tz) if tz else t.replace(tzinfo=None)

        @classmethod
        def utcnow(cls):
            return _DATETIME.fromtimestamp(now(), dt.timezone.utc).replace(tzinfo=None)

    class _Date(dt.date):
        @classmethod
        def today(cls):
            return _DATETIME.fromtimestamp(now(), dt.timezone.utc).date()
    dt.datetime, dt.date = _Frozen, _Date

    def _sleep(s):
        _SLEPT[0] += float(s)

    def _strftime(fmt, t=None):
        return _REAL_STRFTIME(fmt, t if t is not None else time.gmtime(now()))      # Cloud Shell's clock is UTC
    time.sleep, time.time, time.strftime = _sleep, now, _strftime


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


def _object(uri: str):
    bucket, _, name = uri[len("gs://"):].partition("/")
    v = _load("gcs").get(bucket, {}).get(name)
    return None if v is None else base64.b64decode(v)


# ---- Firestore: tenant_settings only
TENANT_SETTINGS = {"acme": {"data_region": "any"}, "zeta": {"data_region": "any", "retrieval_backend": "vertex_search"},
                   "globex": {"data_region": "in"}}


class _Snap:
    def __init__(self, doc):
        self.exists, self._doc = doc is not None, doc

    def to_dict(self):
        return dict(self._doc) if self._doc is not None else None


class _Doc:
    def __init__(self, coll, name):
        self.coll, self.name = coll, name

    def get(self, **kw):
        return _Snap(TENANT_SETTINGS.get(self.name) if self.coll == "tenant_settings" else None)


class _Coll:
    def __init__(self, name):
        self.name = name

    def document(self, name):
        return _Doc(self.name, name)


class FSClient:
    def __init__(self, *a, **kw):
        pass

    def collection(self, name):
        return _Coll(name)


# ---- Gemini: make_trainset's pair (lesson 12.1's stand-in, unchanged), the tuning service, the tuned endpoint
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


CLAUSE = re.compile(r"\b([A-Z]{2,4}(?:-[A-Z]{2,4})?-\d{2,3})\b")
NUMBER = re.compile(r"\b(\d[\d,.]*\s*(?:per cent|%|days?|weeks?|months?|years?|hours?|crore|lakh|rupees|workers|employees)|"
                    r"(?:one|two|three|five|six|seven|eight|ten|twelve|fifteen|twenty|thirty|forty|fifty|sixty|ninety|hundred)"
                    r"(?:[ -][a-z]+)?\s+(?:per cent|days?|weeks?|months?|years?|hours?|workers|employees))\b", re.I)


def _helpdesk(body: str, title: str, heading: str, sha: str) -> dict:
    """Lesson 12.1's stand-in teacher for --style helpdesk, unchanged, so v3 here is v3 there, byte for byte."""
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


_TITLES = {}
TUNABLE = {"gemini-3.5-flash", "gemini-3.1-flash-lite"}          # Google's pricing page lists SFT for both (24 September 2026)
TUNING_REGIONS = {"us-central1", "europe-west4"}                  # "Supported endpoint for model tuning" for both
ADAPTERS = {"ADAPTER_SIZE_ONE", "ADAPTER_SIZE_TWO", "ADAPTER_SIZE_FOUR", "ADAPTER_SIZE_EIGHT", "ADAPTER_SIZE_SIXTEEN"}
SERVE_AT = "us"                                                   # "us and eu multi-region endpoints only"; a US tuning region serves from us
PENDING_S, RUNNING_S = 180, 38 * 60                               # the stand-in job: three minutes queued, 38 minutes in all
# The one question the page's step 6 asks the tuned endpoint, answered the way the training rows are written (no [N] mark)
REPLIES = {"Is withholding an employee's increment a deduction from wages under the Code on Wages?": {
    "answer": "No. A loss of wages from withholding an increment for a good and sufficient cause is not deemed a deduction from "
              "wages, where the employer's provisions meet the requirements the appropriate Government notifies.",
    "citations": [{"source": 1, "quote": "the withholding of increment or promotion, including the stoppage of an increment"}],
    "confidence": "high", "answerable": True}}


def _err(code: int, status: str, message: str):
    from google.genai import errors
    return errors.ClientError(code, {"error": {"code": code, "message": message, "status": status}})


def _digits(*parts) -> str:
    return str(int(hashlib.sha256("|".join(parts).encode()).hexdigest(), 16))[:19]


class Models:
    def __init__(self, location: str):
        self.location = location

    def generate_content(self, model, contents, config=None):
        text = contents if isinstance(contents, str) else contents[0]
        if model.startswith("projects/"):                            # a tuned endpoint: only where its path says
            m = re.search(r"/locations/([^/]+)/endpoints/", model)
            if not m or m.group(1) != self.location or model not in {j.get("endpoint") for j in _load("jobs").values()}:
                raise _err(404, "NOT_FOUND", "Endpoint not found.")
            q = text.rsplit("\n\nQuestion: ", 1)[-1].strip()
            draft = REPLIES.get(q) or {"answer": "The provided context does not answer this question.", "citations": [],
                                       "confidence": "low", "answerable": False}
            out = json.dumps(draft, ensure_ascii=False)
            return SimpleNamespace(text=out, parsed=None, usage_metadata=SimpleNamespace(
                prompt_token_count=len(text) // 4, candidates_token_count=len(out) // 4, thoughts_token_count=0))
        body = text.split("\n\nPassage:\n", 1)[-1]                   # make_trainset's pair call
        if not _TITLES and os.environ.get("LANE172_TITLES"):
            with open(os.environ["LANE172_TITLES"], encoding="utf-8") as f:
                _TITLES.update(json.load(f))
        sha = hashlib.sha256(body.encode("utf-8")).hexdigest()
        t = _TITLES.get(sha, {})
        if "again in Hinglish" in text:                              # make_trainset.ask_helpdesk: lesson 12.1's v3
            p = _helpdesk(body, t.get("title", "the document"), t.get("heading", ""), sha)
        else:
            p = _pair(body, t.get("title", "the document"), t.get("heading", ""))
        return SimpleNamespace(parsed=SimpleNamespace(**p), text=json.dumps(p))


class Tunings:
    def __init__(self, location: str):
        self.location = location

    def tune(self, base_model, training_dataset, config=None):
        from google.genai import types
        if self.location not in TUNING_REGIONS:
            raise _err(400, "INVALID_ARGUMENT", f"Tuning is not supported in {self.location}.")
        if base_model not in TUNABLE:
            raise _err(400, "INVALID_ARGUMENT", f"Base model {base_model} is not supported for tuning.")
        size = str(getattr(config, "adapter_size", "") or "").rsplit(".", 1)[-1]
        if size and size not in ADAPTERS:
            raise _err(400, "INVALID_ARGUMENT", f"Adapter size {size} is not supported for {base_model}.")
        data = _object(training_dataset.gcs_uri)
        if data is None:
            raise _err(400, "INVALID_ARGUMENT", f"Dataset {training_dataset.gcs_uri} not found.")
        rows = [json.loads(line) for line in data.decode("utf-8").splitlines()]
        assert all([c["role"] for c in r["contents"]] == ["user", "model"] for r in rows)
        held = getattr(config, "validation_dataset", None)          # scored as the job trains, never trained on
        held_rows = 0
        if held is not None:
            vdata = _object(held.gcs_uri)
            if vdata is None:
                raise _err(400, "INVALID_ARGUMENT", f"Validation dataset {held.gcs_uri} not found.")
            held_rows = len(vdata.decode("utf-8").splitlines())
        jid = _digits(training_dataset.gcs_uri, str(getattr(config, "tuned_model_display_name", "")), str(now()))
        name = f"projects/NUMBER/locations/{self.location}/tuningJobs/{jid}"
        jobs = _load("jobs")
        jobs[name] = {"created": now(), "base": base_model, "dataset": training_dataset.gcs_uri, "validation_rows": held_rows,
                      "display": getattr(config, "tuned_model_display_name", None), "rows": len(rows),
                      "model": f"projects/NUMBER/locations/{SERVE_AT}/models/{_digits(name, 'model')}@1",
                      "endpoint": f"projects/NUMBER/locations/{SERVE_AT}/endpoints/{_digits(name, 'endpoint')}"}
        _save("jobs", jobs)
        return self.get(name=name)

    def get(self, name):
        from google.genai import types
        j = _load("jobs").get(name)
        if j is None:
            raise _err(404, "NOT_FOUND", f"Tuning job {name} not found.")
        age = now() - j["created"]
        created = _DATETIME.fromtimestamp(j["created"], dt.timezone.utc)
        if age < PENDING_S:
            return types.TuningJob(name=name, state=types.JobState.JOB_STATE_PENDING, base_model=j["base"], create_time=created,
                                   tuned_model_display_name=j["display"])
        if age < RUNNING_S:
            return types.TuningJob(name=name, state=types.JobState.JOB_STATE_RUNNING, base_model=j["base"], create_time=created,
                                   tuned_model_display_name=j["display"])
        return types.TuningJob(name=name, state=types.JobState.JOB_STATE_SUCCEEDED, base_model=j["base"], create_time=created,
                               tuned_model_display_name=j["display"],
                               tuned_model=types.TunedModel(model=j["model"], endpoint=j["endpoint"]))


class GenaiClient:
    def __init__(self, *a, location="global", **kw):
        self.models, self.tunings = Models(location), Tunings(location)


# ---- DLP: shared/pii.inspect_many's contract - findings per text, an info type and an offset, never the value
PII = [("INDIA_GST_INDIVIDUAL", re.compile(r"\b\d{2}[A-Z]{5}\d{4}[A-Z][0-9A-Z]Z[0-9A-Z]\b")),
       ("INDIA_PAN_INDIVIDUAL", re.compile(r"\b[A-Z]{3}P[A-Z][0-9]{4}[A-Z]\b")),
       ("INDIA_AADHAAR_INDIVIDUAL", re.compile(r"\b\d{4} \d{4} \d{4}\b")),
       ("PHONE_NUMBER", re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b")),
       ("EMAIL_ADDRESS", re.compile(r"\b[\w.+-]+@[\w-]+(?:\.[\w-]+)*\.[A-Za-z]{2,}\b"))]


def inspect_many(texts):
    return [[{"info_type": name, "likelihood": "VERY_LIKELY", "offset": m.start()} for name, rx in PII for m in rx.finditer(t)]
            for t in texts]


def install() -> None:
    """Gemini, DLP, Cloud Storage and Firestore, for the kit's scripts and the page's cells."""
    import google.genai
    google.genai.Client = GenaiClient
    import google.cloud
    for name, cls in (("storage", GCSClient), ("firestore", FSClient)):
        m = types.ModuleType(f"google.cloud.{name}")
        m.Client = cls
        sys.modules[f"google.cloud.{name}"] = m
        setattr(google.cloud, name, m)
    import shared
    pii = types.ModuleType("shared.pii")
    pii.inspect_many, pii.LOCATION, pii.MIN_LIKELIHOOD = inspect_many, "asia-south1", "LIKELY"
    sys.modules["shared.pii"] = pii
    shared.pii = pii
