"""Build lesson 6.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

What the answer cache buys and what it risks, measured. Offline: evals/cache_threshold.py embeds the 42 labelled
paraphrase pairs and prints, for each candidate threshold, the hit rate on the pairs that ask the same fact and the
false-hit rate on the pairs one word away with a different answer. Online: a candidate with SEMANTIC_CACHE=on at the
kit's 0.95 is asked every golden question the pairs name and then every pair, so the live false hits can be set
beside the curve's. Then the usage rows turn the hits into avoided calls in rupees and a p95 beside the misses'.

The lane has no recorded measurement, so the page's example similarities are INVENTED and labelled so; the curve
cell's printing is the kit's own main() over stand-in embeddings built to reproduce them, and the widget reads the
learner's own report when it is pasted. The widget's curve and recommendation are the kit's curve() and recommend(),
checked in node on the example and on random sets. The replay runs against a local stub of the API, the savings
cell against a fake gcloud, and make usage's table is usage_rows.main()'s own over the same rows.
"""
import contextlib
import html
import importlib.util
import io
import json
import math
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "6.4"
title = "<title>Lesson 6.4 Measure latency, avoided calls and false cache hits - the threshold on labelled pairs, the same pairs asked live, and what the hits saved | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
CAND = "https://candidate---documind-api-NUMBER.asia-south1.run.app"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in input{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.th-strip{position:relative;height:74px;margin:8px 0 4px;border-bottom:1px solid var(--border);}
.th-dot{position:absolute;width:10px;height:10px;border-radius:50%;transform:translate(-50%,0);}
.th-dot.same{background:#0d9488;}.th-dot.diff{background:#dc2626;}
.th-line{position:absolute;top:0;bottom:0;width:2px;background:var(--navy);}
.th-axis{display:flex;justify-content:space-between;font-family:var(--mono);font-size:11px;color:var(--slate);}
.th-range{width:100%;min-height:44px;}
.th-paste{width:100%;min-height:88px;font-family:var(--mono);font-size:16px;border:1px solid var(--border);border-radius:8px;padding:6px;box-sizing:border-box;}
.th-btn{font:inherit;font-size:13px;min-height:44px;padding:6px 12px;border-radius:8px;border:1px solid var(--border);background:var(--card);cursor:pointer;color:var(--navy);margin-top:6px;}
.pc-steps{margin:6px 0 0;padding-left:20px;}
.pc-steps li{margin:3px 0;}
.pc-steps li.no{color:#991b1b;}.pc-steps li.ok{color:#065f46;}.pc-steps li.skip{color:#94a3b8;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
CT, PAIRS_F, SC, UR = "evals/cache_threshold.py", "evals/paraphrases.jsonl", "services/rag-api/semantic_cache.py", "evals/usage_rows.py"
EXCERPTS = {
    "pairs": ("evals/paraphrases.jsonl - two of the 42 pairs: the same fact in other words, and one grade away",
              block(PAIRS_F, '{"id": "pp-06",', n=1) + "\n...\n" + block(PAIRS_F, '{"id": "pp-25",', n=1)),
    "check": ("evals/cache_threshold.py - check_pairs(): the pairs can judge a threshold only if they are what they say",
              block(CT, "def check_pairs(pairs: list[dict], golden: dict[str, dict]) -> list[str]:", end="def cosine(")),
    "curve": ("evals/cache_threshold.py - curve() and recommend(): hits and false hits per threshold, and the lowest safe one",
              block(CT, "def curve(sims: list[tuple[bool, float]]) -> list[dict]:", end="def embed_all(")),
    "near": ("services/rag-api/semantic_cache.py - the near rung: the five nearest, and the first at the threshold that is alive",
             block(SC, '    hits = (db.collection("answer_cache")', end="def store(")),
    "p95": ("evals/usage_rows.py - p95(): the 95th position of the sorted latencies",
            block(UR, "def p95(values: list[int]) -> int:", n=5)),
}
assert "pp-06" in EXCERPTS["pairs"][1] and '"same": false' in EXCERPTS["pairs"][1]
assert EXCERPTS["check"][1].rstrip().endswith("return bad")
assert EXCERPTS["curve"][1].rstrip().endswith("return min(safe) if safe else None")
assert "(1.0 - d.get(\"d\", 1.0)) < THRESHOLD" in EXCERPTS["near"][1] and EXCERPTS["near"][1].rstrip().endswith("return None")
assert EXCERPTS["p95"][1].rstrip().endswith("return s[max(0, int(round(0.95 * len(s))) - 1)]")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
ct_src, sc_src = (KIT / CT).read_text(encoding="utf-8"), (KIT / SC).read_text(encoding="utf-8")
CANDIDATES = [0.85, 0.88, 0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98]
assert "CANDIDATES = (0.85, 0.88, 0.90, 0.92, 0.94, 0.95, 0.96, 0.97, 0.98)" in ct_src
assert 'model="text-embedding-005"' in ct_src and 'task_type="RETRIEVAL_QUERY", output_dimensionality=768' in ct_src   # hard-coded
assert 'embed_model: str = Field("text-embedding-005", alias="EMBEDDING_MODEL")' in (KIT / "services/rag-api/config.py").read_text(encoding="utf-8")
assert 'THRESHOLD = float(os.environ.get("SEMANTIC_CACHE_THRESHOLD", "0.95"))' in sc_src and "CANDIDATES = 5" in sc_src
mk = (KIT / "Makefile").read_text(encoding="utf-8")
assert "SEMANTIC_CACHE_THRESHOLD" not in mk + "".join(p.read_text(encoding="utf-8") for p in (KIT / "mk").glob("*.mk"))   # make cannot set it
assert "$(PY) evals/usage_rows.py --project $(PROJECT) --hours $${HOURS:-24}" in mk
tf = {p.name: p.read_text(encoding="utf-8") for p in (KIT / "terraform").glob("*.tf")}
assert 'cache_hit_low = "documind/cache_hit_rate < 0.30 for 1h"' in tf["quota.tf"]
assert sum(t.count("documind_alerts") for t in tf.values()) == 1                       # a map nothing reads
assert not any("cache_hit_rate" in t for n, t in tf.items() if n != "quota.tf")      # and no such metric
PAIRS = [json.loads(line) for line in (KIT / PAIRS_F).read_text(encoding="utf-8").splitlines() if line.strip()]
GOLDEN = {r["id"]: r for r in (json.loads(line) for line in (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
N_SAME, N_DIFF = sum(p["same"] for p in PAIRS), sum(not p["same"] for p in PAIRS)
ORIGINALS = sorted({p["of"] for p in PAIRS})
assert (len(PAIRS), N_SAME, N_DIFF, len(ORIGINALS)) == (42, 24, 18, 23)


def load(rel: str, name: str):
    spec = importlib.util.spec_from_file_location(name, KIT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ct = load(CT, "ct93")
ur = load(UR, "ur93")
assert not ct.check_pairs(PAIRS, GOLDEN)

# ------------------------------------------------------------------ the example similarities: INVENTED, labelled so on the page
rnd = random.Random(93)
SIM = {p["id"]: round(rnd.uniform(0.89, 0.985) if p["same"] else rnd.uniform(0.82, 0.935), 3) for p in PAIRS}
SIM.update({"pp-25": 0.962, "pp-31": 0.955, "pp-37": 0.947, "pp-35": 0.941})   # one token apart: a grade, a zero, min/max, before/after
assert {p["id"] for p in PAIRS if not p["same"]} >= {"pp-25", "pp-31", "pp-37", "pp-35"}


def fake_embed(project, region, texts):
    """Stand-in embeddings that reproduce SIM exactly: each golden question a basis vector, each pair s*e_o + sqrt(1-s^2)*e_own."""
    dim, out = 768, []
    for t in texts:
        v = [0.0] * dim
        if t in ORIG_IDX:
            v[ORIG_IDX[t]] = 1.0
        else:
            p = PAIR_BY_Q[t]
            s = SIM[p["id"]]
            v[ORIG_IDX[GOLDEN[p["of"]]["question"]]] = s
            v[len(ORIGINALS) + PAIR_IDX[p["id"]]] = math.sqrt(1 - s * s)
        out.append(v)
    return out


ORIG_IDX = {GOLDEN[o]["question"]: i for i, o in enumerate(ORIGINALS)}
PAIR_BY_Q = {p["question"]: p for p in PAIRS}
PAIR_IDX = {p["id"]: i for i, p in enumerate(PAIRS)}
T = Path(tempfile.mkdtemp(prefix="lesson93-"))
report = T / "cache93_curve.json"
ct.embed_all = fake_embed
buf, old_argv = io.StringIO(), sys.argv
sys.argv = ["cache_threshold.py", "--project", PROJ, "--report", str(report)]
try:
    with contextlib.redirect_stdout(buf):
        assert ct.main() == 0
finally:
    sys.argv = old_argv
REPORT = json.loads(report.read_text(encoding="utf-8"))
OUT = {"curve": buf.getvalue().replace(str(report), "/home/you/cache93_curve.json")}
assert all(abs(p["similarity"] - SIM[p["id"]]) < 1e-9 for p in REPORT["pairs"]) and REPORT["recommended"] == 0.97, REPORT["recommended"]
AT95 = next(r for r in REPORT["curve"] if r["threshold"] == 0.95)
assert (AT95["false_hits"], AT95["hits"]) == (2, sum(SIM[p["id"]] >= 0.95 for p in PAIRS if p["same"]))

# ------------------------------------------------------------------ the widget: curve() and recommend() ported, checked in node
CURVE_JS = r"""var CANDS = %s;
  function curve(sims){                                              /* cache_threshold.curve() over the candidate list */
    return CANDS.map(function(t){
      var tr = sims.filter(function(x){ return x[0]; }), fa = sims.filter(function(x){ return !x[0]; });
      var h = tr.filter(function(x){ return x[1] >= t; }).length, f = fa.filter(function(x){ return x[1] >= t; }).length;
      return {threshold: t, hit_rate: tr.length ? h / tr.length : 0, false_hit_rate: fa.length ? f / fa.length : 0, hits: h, false_hits: f}; }); }
  function recommend(rows){                                          /* cache_threshold.recommend(): the lowest with no false hit */
    var safe = rows.filter(function(r){ return r.false_hits === 0; }).map(function(r){ return r.threshold; });
    return safe.length ? Math.min.apply(null, safe) : null; }""" % json.dumps(CANDIDATES)
TESTS = [[[p["same"], SIM[p["id"]]] for p in PAIRS]]
for _ in range(60):
    n = rnd.randint(2, 40)
    TESTS.append([[rnd.random() < 0.55, round(rnd.uniform(0.78, 1.0), 3)] for _ in range(n)])
KIT_CURVES = [[ct.curve([(bool(a), b) for a, b in s]), ct.recommend(ct.curve([(bool(a), b) for a, b in s]))] for s in TESTS]
test_js = ("'use strict';\n" + CURVE_JS.replace("\n  ", "\n") + "\n" + f"var T = {json.dumps(TESTS)};\n"
           "console.log(JSON.stringify(T.map(function(s){ var c = curve(s); return [c, recommend(c)]; })));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson93-js-")) / "curve.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-600:]
for s, kit, js in zip(TESTS, KIT_CURVES, json.loads(node.stdout)):
    assert kit[1] == js[1], (s, kit[1], js[1])
    for a, b in zip(kit[0], js[0]):
        assert all(abs(a[k] - b[k]) < 1e-12 for k in ("threshold", "hit_rate", "false_hit_rate", "hits", "false_hits")), (a, b)

# ------------------------------------------------------------------ the cells
REPLAY_PY = """import json, os, time, urllib.error, urllib.request
URL, TOKEN = os.environ["CAND"], os.environ["TOKEN"]
gold = {r["id"]: r for r in (json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip())}
pairs = [json.loads(l) for l in open("evals/paraphrases.jsonl", encoding="utf-8") if l.strip()]
retried, failed = [], []
def ask(q, tenant):
    body = json.dumps({"query": q, "tenant_id": tenant, "top_k": 6}).encode()
    for attempt in range(2):                     # a 5xx or a timeout gets one more try, as run_eval.py gives it
        if attempt:
            time.sleep(2)
        req = urllib.request.Request(URL + "/v1/query", data=body, method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
        try:
            a = json.load(urllib.request.urlopen(req, timeout=120))
            if attempt:
                retried.append(why)
            return a["backend"], a["answer"], a["latency_ms"]
        except urllib.error.HTTPError as e:
            why = f"HTTP {e.code}"
            if e.code < 500:
                break
        except OSError as e:                     # a timeout or a dropped connection
            why = type(e).__name__
    failed.append(f"{tenant} {q[:50]!r}: {why}")
    return "error", None, 0
first = {of: ask(gold[of]["question"], gold[of]["tenant"]) for of in sorted({p["of"] for p in pairs})}   # misses, stored when answerable
out = []
for p in pairs:
    backend, answer, ms = ask(p["question"], p["tenant"])
    src = next((of for of, (_, a, _) in first.items() if a is not None and a == answer), None) if backend == "cache" else None
    verdict = ("error" if backend == "error" else "miss" if backend != "cache" else "right hit" if p["same"] and src == p["of"]
               else "FALSE HIT" if src == p["of"] else f"hit from {src}")
    out.append({**p, "backend": backend, "ms": ms, "served_from": src, "verdict": verdict})
    if verdict not in ("miss", "error"):
        print(f"  {p['id']} {'same' if p['same'] else 'diff'} {verdict:12} {ms:>5} ms  {p['question'][:52]}")
json.dump(out, open(os.path.expanduser("~/cache93_replay.json"), "w", encoding="utf-8"), indent=1)
for same in (True, False):
    grp = [o for o in out if o["same"] is same]
    print(f"  {'same-fact' if same else 'different'} pairs served from the cache: {sum(o['backend'] == 'cache' for o in grp)} of {len(grp)}")
if retried:
    print(f"  {len(retried)} question(s) answered on a second try ({', '.join(sorted(set(retried)))} the first time): a blip, not an outage")
if failed:
    print(f"  {len(failed)} question(s) got no answer after a second try - the cell below reads the API's traceback:")
    for f in failed[:5]:
        print(f"    {f}")"""

SAVE_PY = """import json, os, subprocess
rev = open(".candidate-revision").read().strip()
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" '
     f'AND resource.labels.revision_name="{rev}" AND timestamp>="{os.environ["SINCE93"]}"')
rows = [e["jsonPayload"] for e in json.loads(subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"],
        "--limit", "500", "--format", "json"], capture_output=True, text=True, check=True).stdout or "[]")]
hits, miss = [r for r in rows if r["model_backend"] == "cache"], [r for r in rows if r["model_backend"] != "cache"]
p95 = lambda v: sorted(v)[max(0, int(round(0.95 * len(v))) - 1)] if v else 0
rs = sum(r["cost_usd"] for r in miss) / len(miss) * 85 if miss else 0.0
wrong = [o["id"] for o in json.load(open(os.path.expanduser("~/cache93_replay.json"), encoding="utf-8")) if o["verdict"] == "FALSE HIT"]
print(f"  {len(rows)} answers on the candidate: {len(hits)} from the answer cache, {len(miss)} from the model")
print(f"  p95 latency: {p95([r['latency_ms'] for r in hits])} ms for a hit, {p95([r['latency_ms'] for r in miss])} ms for a model answer")
print(f"  a model answer cost Rs {rs:.4f} on average: the hits avoided {len(hits)} calls, about Rs {len(hits) * rs:.2f}")
print(f"  of those hits, {len(wrong)} served a wrong answer: {', '.join(wrong) or 'none'}")"""


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


CELLS = {
    "curve": 'python evals/cache_threshold.py --project "$PROJECT" --report ~/cache93_curve.json',
    "candidate": ('make candidate PROJECT="$PROJECT" SEMANTIC_CACHE=on\n'
                  'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app" SINCE93="$(date -u +%FT%TZ)"; echo "CAND=$CAND"'),
    "replay": heredoc(REPLAY_PY, 'TOKEN="$(tok "$API")" '),
    "trace": ("gcloud logging read 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"documind-api\" AND textPayload:\"Traceback\"' "
              "--project \"$PROJECT\" --freshness=30m --limit 3 --format='value(timestamp,resource.labels.revision_name,textPayload)'"),
    "save": heredoc(SAVE_PY),
    "usage": "make usage PROJECT=\"$PROJECT\" HOURS=1 | sed -n '/by model and backend/,/^$/p'",
    "clean": ('gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate\n'
              'rm -f .candidate-revision      # make promote would otherwise flip traffic to the recorded revision'),
}

# the replay, against a local stub that answers the way the API would at 0.95 with the example similarities
ANSWER = {o: f"[the answer to {o}] ..." for o in ORIGINALS}
PAIR_OF = {p["question"]: p for p in PAIRS}
Q_ORIG = {GOLDEN[o]["question"]: o for o in ORIGINALS}
LAT = iter(rnd.randint(2100, 3300) for _ in range(10_000))
HITLAT = iter(rnd.randint(150, 240) for _ in range(10_000))


STUB = {"blip": 0, "fail": set(), "fixed": False}      # the error path's test: requests that fail once, questions that always fail


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, status: int, data: bytes, ctype: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        q = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))["query"]
        if STUB["blip"] or q in STUB["fail"]:
            STUB["blip"] = max(0, STUB["blip"] - 1)
            return self.reply(500, b"Internal Server Error", "text/plain")
        lat = (lambda it: 1000) if STUB["fixed"] else next    # the error test leaves the page's latencies alone
        if q in Q_ORIG:
            obj = {"backend": "vertex", "answer": ANSWER[Q_ORIG[q]], "latency_ms": lat(LAT)}
        else:
            p = PAIR_OF[q]
            obj = ({"backend": "cache", "answer": ANSWER[p["of"]], "latency_ms": lat(HITLAT)} if SIM[p["id"]] >= 0.95
                   else {"backend": "vertex", "answer": f"[a fresh answer to {p['id']}] ...", "latency_ms": lat(LAT)})
        self.reply(200, json.dumps(obj).encode(), "application/json")


srv = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=srv.serve_forever, daemon=True).start()
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "TOKEN": "TOKEN",
       "CAND": f"http://127.0.0.1:{srv.server_address[1]}", "SINCE93": "YYYY-MM-DDTHH:MM:SSZ", "HOME": str(T), "USERPROFILE": str(T)}


def run_cell(body: str, prelude: str = "", cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env=ENV)
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


OUT["replay"] = run_cell(REPLAY_PY, cwd=KIT)
REPLAY = json.loads((T / "cache93_replay.json").read_text(encoding="utf-8"))
assert [o["id"] for o in REPLAY if o["verdict"] == "FALSE HIT"] == ["pp-25", "pp-31"]
assert f"different pairs served from the cache: 2 of {N_DIFF}" in OUT["replay"]
assert "second try" not in OUT["replay"]
# the error path, in a home of its own: the first request fails once (a blip), and one pair's question always fails
T_ERR = T / "errhome"
T_ERR.mkdir()
STUB.update(blip=1, fail={PAIRS[0]["question"]}, fixed=True)
r = subprocess.run([sys.executable, "-"], input=REPLAY_PY, cwd=str(KIT), capture_output=True, text=True, encoding="utf-8",
                   env={**ENV, "HOME": str(T_ERR), "USERPROFILE": str(T_ERR)})
STUB.update(blip=0, fail=set(), fixed=False)
assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
assert "  1 question(s) answered on a second try (HTTP 500 the first time): a blip, not an outage" in r.stdout, r.stdout[-600:]
assert ("  1 question(s) got no answer after a second try - the cell below reads the API's traceback:\n"
        f"    {PAIRS[0]['tenant']} {PAIRS[0]['question'][:50]!r}: HTTP 500") in r.stdout, r.stdout[-600:]
ERR = json.loads((T_ERR / "cache93_replay.json").read_text(encoding="utf-8"))
assert [o["verdict"] for o in ERR if o["id"] == PAIRS[0]["id"]] == ["error"] and len(ERR) == len(PAIRS), ERR[:2]
srv.shutdown()

# the rows the replay leaves, priced by the kit's own price() at a typical answer; the savings cell and make usage read them
bq = types.ModuleType("google.cloud.bigquery")
bq.Client = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no BigQuery at build time"))
gc = types.ModuleType("google.cloud")
gc.bigquery = bq
saved = {k: sys.modules.get(k) for k in ("google", "google.cloud", "google.cloud.bigquery")}
if importlib.util.find_spec("google") is None:
    sys.modules["google"] = types.ModuleType("google")
sys.modules.update({"google.cloud": gc, "google.cloud.bigquery": bq})
cost = load("services/rag-api/cost.py", "cost93")
for k, v in saved.items():
    sys.modules.pop(k, None) if v is None else sys.modules.__setitem__(k, v)
REV_CAND = "documind-api-00046-wpk"
ROWS = []
for i, o in enumerate(ORIGINALS):
    tin, tout = 1700 + 37 * i % 400, 360 + 11 * i % 90
    ROWS.append({"event": "query", "tenant": GOLDEN[o]["tenant"], "model": "gemini-3.6-flash", "model_backend": "vertex", "brain": "ui",
                 "tokens_in": tin, "tokens_out": tout, "cached_tokens": 0, "cost_usd": cost.price("gemini-3.6-flash", tin, tout, 0)["usd"],
                 "latency_ms": next(LAT), "unanswerable_flag": 0, "retrieve_ms": 240, "rerank_ms": 150, "generate_ms": 1900, "pool": 20,
                 "retrieval_backend": "vector"})
for o in REPLAY:
    if o["backend"] == "cache":
        ROWS.append({"event": "query", "tenant": o["tenant"], "model": "gemini-3.6-flash", "model_backend": "cache", "brain": "ui", "tokens_in": 0,
                     "tokens_out": 0, "cached_tokens": 0, "cost_usd": 0.0, "latency_ms": o["ms"], "unanswerable_flag": 0, "retrieve_ms": o["ms"] - 20,
                     "rerank_ms": 0, "generate_ms": 0, "pool": 0, "retrieval_backend": "vector"})
    else:
        ROWS.append({**ROWS[0], "tenant": o["tenant"], "latency_ms": o["ms"]})
ENTRIES = [{"resource": {"labels": {"revision_name": REV_CAND}}, "jsonPayload": r} for r in ROWS]
(T / ".candidate-revision").write_text(REV_CAND + "\n", encoding="utf-8")
FAKE_GCLOUD = ("import json, sys, types\n"
               "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               f"ENTRIES = json.loads({json.dumps(json.dumps(ENTRIES))})\n"
               "def run(cmd, **kw):\n"
               "    assert cmd[1:3] == ['logging', 'read'] and 'resource.labels.revision_name=\"" + REV_CAND + "\"' in cmd[3], cmd\n"
               "    return R(json.dumps(ENTRIES))\n"
               "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT["save"] = run_cell(SAVE_PY, FAKE_GCLOUD)
n_hits = sum(o["backend"] == "cache" for o in REPLAY)
assert f"{n_hits} from the answer cache" in OUT["save"] and "2 served a wrong answer: pp-25, pp-31" in OUT["save"], OUT["save"]


class _R:
    def __init__(self, out):
        self.stdout, self.stderr, self.returncode = out, "", 0


ur.subprocess = types.SimpleNamespace(run=lambda cmd, **kw: _R(json.dumps([{"jsonPayload": r} for r in ROWS])))
buf, old_argv = io.StringIO(), sys.argv
sys.argv = ["usage_rows.py", "--project", PROJ, "--hours", "1"]
try:
    with contextlib.redirect_stdout(buf):
        assert ur.main() == 0
finally:
    sys.argv = old_argv
full = buf.getvalue().splitlines()
i = next(k for k, line in enumerate(full) if "by model and backend" in line)
j = next((k for k in range(i + 1, len(full)) if not full[k].strip()), len(full))
OUT["usage"] = "\n".join(full[i:j + 1]) + "\n"                                        # sed -n '/by model and backend/,/^$/p'
assert "cache" in OUT["usage"] and "vertex" in OUT["usage"]
dflt = {k: re.search(rf"^{k}\s+\?= (\S+)", mk, re.M).group(1) for k in ("GENERATOR_MODEL", "RAG_MODEL_BASE", "ROUTING", "MODEL_BACKEND", "ARMOR")}
OUT["candidate"] = ("gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\\n"
                    f"  --update-env-vars \"^|^GENERATOR_MODEL={dflt['GENERATOR_MODEL']}|RAG_MODEL_BASE={dflt['RAG_MODEL_BASE']}|ROUTING={dflt['ROUTING']}"
                    f"|MODEL_BACKEND={dflt['MODEL_BACKEND']}|ARMOR={dflt['ARMOR']}|SEMANTIC_CACHE=on|...\"\n"
                    f"...\n>> candidate revision: {REV_CAND} (deploy/.candidate-revision - make promote moves traffic to it by name)\n"
                    f">> candidate: {CAND} (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)\nCAND={CAND}\n")
OUT["clean"] = ("Updating traffic...done.\nDone.\nURL: https://documind-api-...run.app\nTraffic:\n"
                "  100% documind-api-000MM-xxx      (the live revision, as before; no candidate tag)\n")
shutil.rmtree(T, ignore_errors=True)
PRICE_RS = sum(r["cost_usd"] for r in ROWS if r["model_backend"] != "cache") / sum(r["model_backend"] != "cache" for r in ROWS) * 85


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "curve": f"run in the operator shell, in the kit ({len(PAIRS) + len(ORIGINALS)} embeddings, about a minute; the report goes to your home folder)",
    "candidate": "run in the operator shell, in the kit (a revision with SEMANTIC_CACHE=on at the kit's 0.95, and a start time)",
    "replay": "run in the operator shell, in the kit (the 23 golden questions, then the 42 pairs, to the candidate; a few minutes)",
    "trace": "run in the operator shell, only if the replay listed questions with no answer (the API's last three tracebacks)",
    "save": "run in the operator shell, in the kit (the candidate's rows since the start: hits, p95, rupees; reads only)",
    "usage": "run in the operator shell, in the kit (the kit's own table of the last hour, by model and backend)",
    "clean": "run in the operator shell, in the kit (the candidate's tag and recorded name removed)",
}
OUT_LABELS = {
    "curve": "(the kit's own printing over stand-in embeddings that reproduce the page's INVENTED example similarities; your curve is Google's)",
    "candidate": "shape (gcloud's progress lines are left out)",
    "replay": "(against a local stub answering at 0.95 with the example similarities; only hits are printed)",
    "save": "(against a fake gcloud holding the replay's rows, priced by the kit's own price())",
    "usage": "(usage_rows.main()'s own printing over the same rows; your numbers differ)",
    "clean": "shape",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: the threshold explorer
EXAMPLE = [[p["id"], p["same"], SIM[p["id"]], p["question"]] for p in PAIRS]
UI_JS = r"""var root = document.getElementById('thx'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); }, data = %s, src = 'the example (invented similarities)';
  function pct(x){ return Math.round(x * 100) + '%%'; }
  function render(){
    var t = parseFloat($('th-t').value), sims = data.map(function(d){ return [d[1], d[2]]; });
    var rows = curve(sims), rec = recommend(rows), tr = data.filter(function(d){ return d[1]; }), fa = data.filter(function(d){ return !d[1]; });
    var hits = tr.filter(function(d){ return d[2] >= t; }).length, wrong = fa.filter(function(d){ return d[2] >= t; });
    var lo = 0.80, span = 0.20, strip = $('th-strip');
    strip.innerHTML = data.map(function(d, i){ var x = Math.max(0, Math.min(1, (d[2] - lo) / span)) * 100;
      return '<span class="th-dot ' + (d[1] ? 'same' : 'diff') + '" style="left:' + x + '%%;top:' + (d[1] ? 8 + (i %% 3) * 12 : 44 + (i %% 2) * 12) + 'px" title="' + d[0] + ' ' + d[2].toFixed(3) + '"></span>'; }).join('')
      + '<span class="th-line" style="left:' + Math.max(0, Math.min(1, (t - lo) / span)) * 100 + '%%"></span>';
    var n = parseFloat($('th-n').value) || 0, share = (parseFloat($('th-share').value) || 0) / 100, near = (parseFloat($('th-near').value) || 0) / 100, cost = parseFloat($('th-cost').value) || 0;
    var hr = tr.length ? hits / tr.length : 0, fr = fa.length ? wrong.length / fa.length : 0, s = '';
    s += '<li class="skip">data: ' + src + ' - ' + tr.length + ' same-fact, ' + fa.length + ' different</li>';
    s += '<li class="ok">at ' + t.toFixed(3) + ': ' + hits + ' of ' + tr.length + ' same-fact pairs hit (' + pct(hr) + ')</li>';
    s += '<li class="' + (wrong.length ? 'no' : 'ok') + '">' + wrong.length + ' of ' + fa.length + ' different pairs hit (' + pct(fr) + ')' + (wrong.length ? ': ' + wrong.map(function(d){ return d[0] + ' "' + d[3] + '" ' + d[2].toFixed(3); }).join('; ') : '') + '</li>';
    s += '<li class="' + (rec === null ? 'no' : 'ok') + '">the kit\'s rule, the lowest candidate with no false hit: ' + (rec === null ? 'none - every candidate serves a wrong answer here' : rec) + '</li>';
    if (!wrong.length && fa.length) s += '<li class="skip">no false hit on ' + fa.length + ' different pairs still allows a true rate up to about ' + pct(Math.min(1, 3 / fa.length)) + ' (the rule of three, 95%%)</li>';
    s += '<li class="ok">a day of ' + n + ' questions, ' + pct(share) + ' of them rephrasings of an earlier one: about ' + Math.round(n * share * hr) + ' calls avoided, Rs ' + (n * share * hr * cost).toFixed(2) + '</li>';
    s += '<li class="' + (fr ? 'no' : 'ok') + '">and if ' + pct(near) + ' are one word away from an earlier question: about ' + Math.round(n * near * fr) + ' wrong answers served fast</li>';
    $('th-out').innerHTML = s; $('th-tv').textContent = t.toFixed(3);
  }
  $('th-load').addEventListener('click', function(){
    try {
      var j = JSON.parse($('th-paste').value), ps = j.pairs || j;
      var d = ps.filter(function(p){ return typeof p.similarity === 'number'; }).map(function(p){ return [p.id, !!p.same, p.similarity, p.question || '']; });
      if (!d.length) throw new Error('no pairs with a similarity');
      data = d; src = 'your report (' + d.length + ' pairs)'; render();
    } catch (e) { $('th-out').innerHTML = '<li class="no">could not read that as the report: ' + e.message + '</li>'; }
  });
  ['th-t', 'th-n', 'th-share', 'th-near', 'th-cost'].forEach(function(id){ $(id).addEventListener('input', render); });
  render();""" % json.dumps(EXAMPLE)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\n" + squeeze(CURVE_JS) + "\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n")
assert JS.count("<div") == JS.count("</div>") and "<tr" not in JS

STATS = {"N_PAIRS": str(len(PAIRS)), "N_SAME": str(N_SAME), "N_DIFF": str(N_DIFF), "N_ORIG": str(len(ORIGINALS)), "N_EMB": str(len(PAIRS) + len(ORIGINALS)),
         "N_TESTS": str(len(TESTS)), "PRICE_RS": f"{PRICE_RS:.2f}", "RULE3": f"{round(3 / N_DIFF * 100)}"}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {len(PAIRS)} pairs ({N_SAME} same, {N_DIFF} different) against {len(ORIGINALS)} golden questions | curve()/recommend() equal in node on"
      f" {len(TESTS)} sets | the curve cell is the kit's main() over stand-in embeddings | replay, savings and make usage run against stand-ins")
