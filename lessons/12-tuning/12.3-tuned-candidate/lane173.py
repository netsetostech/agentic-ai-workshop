"""The stand-in lane for lesson 12.3's build. Under it the kit's own code runs unchanged: evals/run_eval.py for both
gates, evals/judge.py for the pairwise judge, evals/usage_rows.py for the usage rows, evals/make_trainset.py (to leave
the datasets bucket as lesson 12.1 leaves it), and the page's cells.

What is stood in, and how:
  The API         two revisions of documind-api answering the golden rows. The live one (gemini-3.6-flash) misses
                  lesson 12.1's two rows and puts a [N] mark on every claim. The candidate (the tuned endpoint) writes
                  no [N] marks, as its training rows taught; it states both figures jn-06 needs, and gives one of the
                  two figures on jn-03 and jn-09. Under LANE173_CANDIDATE=v3 the candidate is v3's endpoint (steps 7
                  and 8): the house style with its marks, the same join misses; under LANE173_DEMO step 8's three
                  questions get the answers DEMO holds.
  Cloud Run       gcloud run services / revisions describe: two revisions' settings, from LANE173_RUN.
  Cloud Logging   gcloud logging read: the usage rows those answers leave, priced by the kit's cost.price() in the build.
  Evaluation      vertexai.evaluation.EvalTask: groundedness, instruction following and the pairwise choice, decided by
                  the gate's own facts (each row's must_contain phrases, normalised as run_eval normalises them), and
                  the SDK's win-rate arithmetic (a tie counts for neither side).
  Firestore       chunks (the cited chunks' text, for the judge) and tenant_caches (none).
  Cloud Storage   the datasets bucket; Gemini and DLP for make_trainset, as lesson 12.1's stand-in writes them.
"""
import base64
import datetime as dt
import hashlib
import json
import os
import re
import subprocess
import sys
import time
import types
from types import SimpleNamespace

ENV = os.environ.get


def _path(name: str) -> str:
    return os.environ[f"LANE173_{name.upper()}"]


def _load(name: str) -> dict:
    try:
        with open(_path(name), encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return {}


def _save(name: str, state: dict) -> None:
    tmp = _path(name) + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(state, f)
    os.replace(tmp, _path(name))


# ---- the clock
_DATETIME = dt.datetime
_REAL_STRFTIME = time.strftime


def _t0() -> float:
    return _DATETIME.fromisoformat(ENV("LANE173_NOW", "2026-09-24T10:40:00+00:00")).timestamp()


def freeze() -> None:
    """Freeze the build clock after pandas initializes its native datetime types.

    Example: call ``freeze()`` before ``install()`` in a lesson build process.
    Importing pandas after replacing datetime.date can crash its native loader
    on Windows. Initialize it first; the lesson's timestamps remain deterministic.
    """
    import pandas  # noqa: F401 -- initialize native date types before patching

    t0 = _t0()

    class _Frozen(dt.datetime):
        @classmethod
        def now(cls, tz=None):
            t = _DATETIME.fromtimestamp(t0, dt.timezone.utc)
            return t.astimezone(tz) if tz else t.replace(tzinfo=None)

    class _Date(dt.date):
        @classmethod
        def today(cls):
            return _DATETIME.fromtimestamp(t0, dt.timezone.utc).date()
    dt.datetime, dt.date = _Frozen, _Date
    time.strftime = lambda fmt, t=None: _REAL_STRFTIME(fmt, t if t is not None else time.gmtime(t0))


# ---- the revisions' answers: the live one, the v2 candidate (steps 4 to 6) and the v3 candidate (steps 7 and 8)
NOFIG = {"jn-06": "EMEA revenue fell in FY2026 [1]."}
PARTIAL = {"jn-03": "45 days of the earned leave are encashed.", "jn-09": "The minimum bonus is 8.33 per cent of the salary or wage."}
# v3 answers in the house style its rows teach, marks included, and keeps the v2 candidate's join misses: each of its rows
# still answers from one source, so the stand-in does not credit it with the second figure a join needs
PARTIAL3 = {"jn-03": "**Answer:** 45 days.\n**Why:** At most 45 days of earned leave are encashed on exit [1].\n**Clause:** LV-07, hr_policy_2026.md",
            "jn-09": "**Answer:** 8.33 per cent.\n**Why:** The minimum bonus is 8.33 per cent of the salary or wage [1].\n**Clause:** Section 10, payment_of_bonus_act_1965.pdf"}
HOUSE_REFUSAL = "**Answer:** Not in the documents.\n**Why:** None of the sources states this, so there is nothing to cite."
LIVE_MISS = {"lk-27": "refused", "jn-06": "nofig"}
CAND_MISS = {"lk-27": "refused", "jn-03": "partial", "jn-09": "partial"}
NP03 = {"chunk_id": "acme:hr_policy_2026#NP-03", "source_uri": "gs://lesson/acme/hr_policy_2026.md",
        "quote": "Unused earned leave may not be set off against the notice period.", "kind": "text"}
LV07 = {"chunk_id": "acme:hr_policy_2026#LV-07", "source_uri": "gs://lesson/acme/hr_policy_2026.md",
        "quote": "Leave cannot be encashed during probation and cannot be used to shorten notice.", "kind": "text"}
# Step 8's three questions (LANE173_DEMO): an answer (golden jn-02), the same question in Hinglish, and one the documents do not answer.
# The live revision answers the way gemini-3.6-flash writes; whether it answers Hinglish in Hinglish is the lane's to show, and here it
# answers in English. The v3 candidate answers the way v3's rows teach.
DEMO = {
    "Can unused leave shorten my notice period?": {
        "live": ("No. Unused earned leave may not be set off against the notice period [1], and leave cannot be used to shorten notice [2].", [NP03, LV07]),
        "cand3": ("**Answer:** No.\n**Why:** Unused earned leave may not be set off against the notice period [1].\n**Clause:** NP-03, hr_policy_2026.md", [NP03])},
    "Kya main apni bachi hui leave se notice period chhota kar sakta hoon?": {
        "live": ("No. Unused earned leave may not be set off against the notice period [1], and leave cannot be used to shorten notice [2].", [NP03, LV07]),
        "cand3": ("**Answer:** Nahi.\n**Why:** Bachi hui earned leave ko notice period ke against set off nahi kiya ja sakta [1].\n"
                  "**Clause:** NP-03, hr_policy_2026.md", [NP03])},
    "How much is ACME's referral bonus?": {
        "live": ("The documents do not say. The handbook has a section headed Referral bonus, but it states no amount.", []),
        "cand3": (HOUSE_REFUSAL, [])},
}


def _golden() -> list:
    sys.path[:0] = [p for p in ("evals",) if p not in sys.path]
    import run_eval
    return run_eval.load_golden()


def _body(answer: str, cites: list, answerable: bool, rev: str) -> dict:
    model = {"live": "gemini-3.6-flash", "cand": ENV("LANE173_ENDPOINT", ""), "cand3": ENV("LANE173_ENDPOINT_V3", "")}[rev]
    return {"answer": answer, "citations": cites, "answerable": answerable, "confidence": "high" if answerable else "low",
            "model": model, "backend": "vertex", "cache_hit": "none", "tokens_in": 7400,
            "tokens_out": len(answer) // 4 + (150 if rev == "live" else 20),        # the served model thinks at LOW; the tuned lite barely
            "stages": {"retrieve_ms": 400, "rerank_ms": 200, "generate_ms": 1500 if rev == "live" else 900, "pool": 12}}


def reply(row: dict, rev: str) -> tuple:
    """(status, body) for one golden row from one revision."""
    t, mc = row["tenant"], row.get("must_contain", [])
    cand = rev != "live"
    outcome = (CAND_MISS if cand else LIVE_MISS).get(row["id"], "ok")

    def cite():
        return {"chunk_id": f"{t}:{row['id']}#0", "source_uri": f"gs://lesson/{t}/doc.md", "quote": mc[0] if mc else "lesson",
                "kind": row.get("must_cite_kind") or "text"}
    mark = "" if rev == "cand" else " [1]"
    if not row["answerable"] or outcome == "refused":
        answer, cites, answerable = (HOUSE_REFUSAL if rev == "cand3" else "The documents do not say."), [], False
    elif outcome == "nofig":
        answer, cites, answerable = NOFIG[row["id"]], [cite()], True
    elif outcome == "partial":
        answer, cites, answerable = (PARTIAL3 if rev == "cand3" else PARTIAL)[row["id"]], [cite()], True
    elif rev == "cand3":
        said = " and ".join(mc)
        answer, cites, answerable = f"**Answer:** {said}.\n**Why:** The source states {said}{mark}.\n**Clause:** {row['id'].upper()}, doc.md", [cite()], True
    else:
        answer, cites, answerable = " and ".join(mc) + mark + ".", [cite()], True
    return 200, _body(answer, cites, answerable, rev)


def ask(api_url, question, tenant, email, token, retries=1):
    """run_eval.ask and judge.py's collection, answered by the revision the URL names (the candidate is v3's under LANE173_CANDIDATE=v3)."""
    if email == ENV("DOCUMIND_OUTSIDER_EMAIL", "outsider@not-a-tenant.invalid"):
        return 403, {}, 120
    rev = "live"
    if api_url.startswith("https://candidate---"):
        rev = "cand3" if ENV("LANE173_CANDIDATE") == "v3" else "cand"
    if ENV("LANE173_DEMO") and question in DEMO:
        answer, cites = DEMO[question][rev]
        return 200, _body(answer, cites, bool(cites), rev), 2100 if rev == "live" else 1000
    row = next(r for r in _golden() if r["question"] == question and r["tenant"] == tenant)
    status, body = reply(row, rev)
    return status, body, 2100 if rev == "live" else 1000


def chunk_text(chunk_id: str) -> str:
    """The text a stand-in citation's chunk holds: the phrases its row must contain, in a sentence."""
    rid = chunk_id.split(":", 1)[1].split("#", 1)[0]
    row = next(r for r in _golden() if r["id"] == rid)
    return f"{row['id']}: " + "; ".join(row.get("must_contain", []) or ["the clause"]) + "."


# ---- Cloud Run and Cloud Logging, through gcloud
def gcloud(cmd: list) -> str:
    if cmd[1:3] == ["auth", "print-identity-token"]:
        return "stand-in-token\n"                                   # step 8's cell mints the UI's token, as tok() does
    run = _load("run")
    opts = {c.split("=", 1)[0]: c.split("=", 1)[1] for c in cmd if c.startswith("--") and "=" in c}
    if cmd[1:4] == ["run", "services", "describe"]:
        env = [{"name": k, "value": v} for k, v in run["live"].items()]
        return json.dumps({"spec": {"template": {"spec": {"containers": [{"env": env}]}}},
                           "status": {"traffic": [{"revisionName": run["revs"][0], "percent": 100},
                                                  {"revisionName": run["revs"][1], "tag": "candidate", "url": run["cand_url"]}],
                                      "latestCreatedRevisionName": run["revs"][1]}})
    if cmd[1:4] == ["run", "revisions", "describe"]:
        env = run["live"] if cmd[4] == run["revs"][0] else run["cand"]
        return json.dumps({"spec": {"containers": [{"env": [{"name": k, "value": v} for k, v in env.items()]}]}})
    if cmd[1:3] == ["logging", "read"]:
        since = re.search(r'timestamp>="([^"]+)"', cmd[3]).group(1)
        limit = int(cmd[cmd.index("--limit") + 1]) if "--limit" in cmd else int(opts.get("--limit", 1000))
        rows = [e for e in _load("logs").get("entries", []) if e["timestamp"] >= since
                and e["jsonPayload"].get("event") in ("query", "stream", "media")]
        return json.dumps(sorted(rows, key=lambda e: e["timestamp"], reverse=True)[:limit])
    raise SystemExit(f"the stand-in has no answer for {' '.join(cmd[:5])}")


def fake_cli() -> None:
    real = subprocess.run

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "gcloud":
            return subprocess.CompletedProcess(list(cmd), 0, gcloud(list(cmd)), "")
        return real(cmd, *a, **kw)
    subprocess.run = run


# ---- Vertex AI Evaluation
def _evaluation_modules() -> None:
    import pandas as pd
    vx, ev = types.ModuleType("vertexai"), types.ModuleType("vertexai.evaluation")
    vx.init = lambda **kw: None

    class _Template:
        def __init__(self, name):
            self.metric_prompt_template = f"{name}: the stand-in's template"

    class _Pointwise:
        GROUNDEDNESS = _Template("groundedness")
        INSTRUCTION_FOLLOWING = _Template("instruction_following")

    class MetricPromptTemplateExamples:
        Pointwise = _Pointwise

        @staticmethod
        def get_prompt_template(name):
            return f"{name}: the stand-in's template"

    class PairwiseMetric:
        def __init__(self, metric, metric_prompt_template):
            self.metric_name = metric

    class EvalTask:
        def __init__(self, dataset, metrics, experiment=None, **kw):
            self.df, self.metrics = dataset, metrics

        def evaluate(self, experiment_run_name=None):
            import run_eval
            gold = {r["id"]: r for r in run_eval.load_golden()}
            has = lambda text, p: run_eval.normalise(p) in run_eval.normalise(text or "")  # noqa: E731
            refusal = lambda text: "do not say" in (text or "").lower()                   # noqa: E731
            rows = []
            pair = any(isinstance(m, PairwiseMetric) for m in self.metrics) and "baseline_model_response" in self.df
            for _, r in self.df.iterrows():
                must = gold[r["id"]].get("must_contain", [])
                said = [p for p in must if has(r["response"], p)]
                grounded = 1.0 if refusal(r["response"]) or all(has(r["prompt"], p) for p in said) else 0.0
                follow = (5.0 if (must and len(said) == len(must)) or (not must and refusal(r["response"]))
                          else 3.0 if said else 1.0)
                out = {"id": r["id"], "shape": r["shape"], "groundedness/score": grounded, "instruction_following/score": follow}
                if pair:
                    b = sum(has(r["baseline_model_response"], p) for p in must)
                    out["pairwise_question_answering_quality/pairwise_choice"] = (
                        "TIE" if not must or len(said) == b else "CANDIDATE" if len(said) > b else "BASELINE")
                rows.append(out)
            table = pd.DataFrame(rows)
            summary = {"row_count": len(table)}
            for m in ("groundedness", "instruction_following"):
                summary[f"{m}/mean"], summary[f"{m}/std"] = float(table[f"{m}/score"].mean()), float(table[f"{m}/score"].std())
            if pair:
                col = table["pairwise_question_answering_quality/pairwise_choice"]
                summary["pairwise_question_answering_quality/candidate_model_win_rate"] = float((col == "CANDIDATE").mean())
                summary["pairwise_question_answering_quality/baseline_model_win_rate"] = float((col == "BASELINE").mean())
            return SimpleNamespace(summary_metrics=summary, metrics_table=table)

    ev.EvalTask, ev.MetricPromptTemplateExamples, ev.PairwiseMetric = EvalTask, MetricPromptTemplateExamples, PairwiseMetric
    vx.evaluation = ev
    sys.modules["vertexai"], sys.modules["vertexai.evaluation"] = vx, ev


# ---- Cloud Storage and Firestore
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

    def download_as_bytes(self, **kw):
        v = _load("gcs").get(self.bucket_name, {}).get(self.name)
        if v is None:
            from google.api_core.exceptions import NotFound
            raise NotFound(f"gs://{self.bucket_name}/{self.name}")
        return base64.b64decode(v)

    def download_as_text(self, encoding="utf-8", **kw):
        return self.download_as_bytes().decode(encoding)


class GCSClient:
    def __init__(self, *a, **kw):
        pass

    def bucket(self, name):
        return SimpleNamespace(name=name, blob=lambda n, **kw: Blob(name, n))


class _Snap:
    def __init__(self, sid, doc):
        self.id, self.exists, self._doc = sid, doc is not None, doc

    def to_dict(self):
        return dict(self._doc) if self._doc is not None else None


class _Ref:
    def __init__(self, coll, sid):
        self.coll, self.id = coll, sid

    def get(self, **kw):
        return _Snap(self.id, {"text": chunk_text(self.id)} if self.coll == "chunks" else None)   # no tenant_caches record


class FSClient:
    def __init__(self, *a, **kw):
        pass

    def collection(self, name):
        return SimpleNamespace(document=lambda sid: _Ref(name, sid))

    def get_all(self, refs):
        return [r.get() for r in refs]


# ---- Gemini and DLP for make_trainset: lesson 12.1's stand-in, unchanged
STOP = set("the a an of and or to in on for by with as at from this that these those is are be shall any such which "
           "who under section act code it its his her their than other all".split())
_TITLES = {}


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


class _Models:
    def generate_content(self, model, contents, config=None):
        body = (contents if isinstance(contents, str) else contents[0]).split("\n\nPassage:\n", 1)[-1]
        if not _TITLES and ENV("LANE173_TITLES"):
            with open(ENV("LANE173_TITLES"), encoding="utf-8") as f:
                _TITLES.update(json.load(f))
        t = _TITLES.get(hashlib.sha256(body.encode("utf-8")).hexdigest(), {})
        p = _pair(body, t.get("title", "the document"), t.get("heading", ""))
        return SimpleNamespace(parsed=SimpleNamespace(**p), text=json.dumps(p))


class GenaiClient:
    def __init__(self, *a, **kw):
        self.models = _Models()


PII = [("INDIA_PAN_INDIVIDUAL", re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")), ("INDIA_AADHAAR_INDIVIDUAL", re.compile(r"\b\d{4} \d{4} \d{4}\b")),
       ("PHONE_NUMBER", re.compile(r"(?:\+91[\s-]?)?\b[6-9]\d{9}\b"))]


def install() -> None:
    """The stand-ins, for the kit's scripts and the page's cells."""
    sys.path[:0] = [p for p in (".", "evals") if p not in sys.path]
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
    pii.inspect_many = lambda texts: [[{"info_type": n} for n, rx in PII if rx.search(t)] for t in texts]
    sys.modules["shared.pii"] = pii
    shared.pii = pii
    import run_eval
    run_eval.ask = ask
    run_eval.fetch_current_shas = lambda *a, **k: set()
    _evaluation_modules()
    fake_cli()
