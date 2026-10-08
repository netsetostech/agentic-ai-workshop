"""Build lesson 11.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Debug a wrong answer through the complete pipeline. Every answer carries a trail: the answer cache's verdict, the store
that served and whether a fallback rung answered (stages: retrieval_backend, vector_chunks, policy_fallback), the pool
the reranker saw, whether the Ranking API ordered it, and the version each citation came from (the chunk id carries the
bytes' SHA-256). Beside it sit the log's fallback events and the ledger's versions (make sources, GET /v1/sources). The
runbook reads the marks in the order the answer was made and names the first one that is off. Offline: the trail as the
kit writes it down. Live: a right answer and its trail; the handbook's revision 2 re-issued (make reindex, the kit's own
shape-A demo), the same question answered 90 days; the trace - six links, the version the first one off - with make
sources and the two read-only probes (the vector index attached; the Firestore probe refusing the ledger's version);
then version 1 back.

Build-time proof: the offline cell runs on the kit. The live cells ran against the kit's own rag-api - query(),
/version and /v1/sources, served on localhost behind a Cloud Run stand-in - over a stand-in lane that holds the
handbook's two versions as the kit's chunker cuts them (283 chunks each, the worker's chunk ids), with Firestore, the
index, the Ranking API, Gemini (a reader that answers from the packed clause) and gcloud stood in. make sources is the
kit's reconcile.py --report, and the probes are the kit's two commands, run on the same lane. The panel's seven answers
are the kit's query() under seven breaks, and their verdicts are the trace cell's own read_trail().
"""
import ast
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from datetime import datetime, timedelta
from hashlib import sha256
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "11.4"
title = "<title>Lesson 11.4 Debug a wrong answer through the complete pipeline - the trail an answer leaves, and the cause it names | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
PORT = 8131
Q = "What is the notice period for a confirmed E3?"
V1, V2 = "evals/corpus/acme/hr_policy_2026.md", "evals/demo/hr_policy_2026_v2.md"
NAME, URI = "acme/hr_policy_2026.md", f"gs://{PROJ}-uploads/acme/hr_policy_2026.md"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,10em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid .pass{color:var(--teal-dark);font-weight:600;}
.fs-grid .stop{color:#9a3412;font-weight:600;}
.fs-grid .skip{color:var(--slate-light);}
.fs-grid code{font-size:11.5px;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
MAIN, RET, PROBE = "services/rag-api/main.py", "services/rag-api/retriever.py", "commands/check-firestore-fallback.py"
EXCERPTS = {
    "marks": ("services/rag-api/main.py - query(): the pool, and each rung's share of it, onto the answer",
              block(MAIN, '    stages["pool"] = len(chunks)', n=4)),
    "rung": ("services/rag-api/retriever.py - the index's rung: the error logged, then the Firestore rung asked",
             block(RET, "    except Exception as e:", nth=3, n=8)),
    "current": ("services/rag-api/retriever.py - prefer_current(): a retired version never reaches the reranker",
                block(RET, "def prefer_current(chunks: list[dict]) -> list[dict]:", n=6)),
    "probe": ("commands/check-firestore-fallback.py - the probe holds the ledger to the handbook in your checkout",
              block(PROBE, '    require(source.get("status") == "indexed"', n=4)),
}
assert 'stages["vector_chunks"] = sum(1 for c in chunks if c.get("found_by") == "vector")' in EXCERPTS["marks"][1]
assert '"vector_search_fallback"' in EXCERPTS["rung"][1] and "return prefer_current(_firestore_fallback(" in EXCERPTS["rung"][1]
assert 'c.get("current") is not False' in EXCERPTS["current"][1]
assert "HR source ledger does not match the selected local HR file" in EXCERPTS["probe"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (MAIN, RET, "services/rag-api/config.py", "services/rag-api/generator.py",
                                                           "services/ingest/main.py", "commands/lesson-12.2.sh", "commands/reindex.sh")}
VERSION_FN = src[MAIN][src[MAIN].index("def version():"):src[MAIN].index('@app.get("/v1/sources")')]
assert "top_k" not in VERSION_FN.lower()                                                    # /version does not say how deep the pool is
assert 'top_k_retrieve: int = Field(20, alias="TOP_K_RETRIEVE")' in src["services/rag-api/config.py"]
assert "TOP_K_RETRIEVE" not in src["commands/lesson-12.2.sh"] and "RETRIEVAL_CURRENT_ONLY=${RETRIEVAL_CURRENT_ONLY-off}" in src["commands/lesson-12.2.sh"]
assert "RETRIEVAL_BACKEND=${RETRIEVAL_BACKEND:-firestore}" in src["commands/lesson-12.2.sh"]
assert "doc.sha256, back, effective_from_of(msg.name, None)," in src["services/ingest/main.py"]       # a reactivation forgets the date
assert "effective_from" in src["services/rag-api/generator.py"] and "today" not in src[RET] and "datetime.now" not in src[RET]
assert 'echo ">> the gate, scoped to this document, on a candidate: make eval-live PROJECT=$PROJECT SOURCE=$OBJ API=<candidate url>"' in src["commands/reindex.sh"]
mk = (KIT / "Makefile").read_text(encoding="utf-8") + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert "$(PY) services/ingest/reconcile.py --project $(PROJECT) --report $(if $(TENANT_ONLY),--tenant $(TENANT_ONLY),)" in mk
assert not re.search(r"^(trace|debug|why)[\w-]*:", mk, re.M)                                # no target reads the trail in order
GOLDEN = [json.loads(line) for line in (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
LK06, VR01 = (next(r for r in GOLDEN if r["id"] == i) for i in ("lk-06", "vr-01"))
assert LK06["question"] == VR01["question"] == Q and LK06["must_contain"] == ["60"] and VR01["must_not_contain"] == ["90 days"]
B1, B2 = (KIT / V1).read_bytes(), (KIT / V2).read_bytes()
SHA1, SHA2 = sha256(B1).hexdigest(), sha256(B2).hexdigest()
assert b"Effective from: 2026-10-01." in B2 and b"notice period of 90 days" in B2 and b"notice period of 60 days" in B1

# ------------------------------------------------------------------ the cells
MAP_PY = """import ast, re
root = "services/rag-api/"
main, ret = (open(root + f, encoding="utf-8").read() for f in ("main.py", "retriever.py"))
tree = ast.parse(open(root + "schemas.py", encoding="utf-8").read())
env = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "RAGResponse")
print("the envelope on every answer, beyond the contract (schemas.py, RAGResponse):")
print("  " + ", ".join(n.target.id for n in env.body if isinstance(n, ast.AnnAssign)))
q = main[main.index("def query("):main.index("def _record(")]
keys = set(re.findall(r'stages\\["(\\w+)"\\]', q)) | {n + "_ms" for n in re.findall(r'stage\\(stages, "(\\w+)"\\)', q)}
print("stages, as query() fills them (main.py):")
print("  " + ", ".join(sorted(keys)))
print("found_by, the rung that put a chunk in the pool (retriever.py):")
print("  " + ", ".join(sorted(set(re.findall(r'found_by"\\]? ?[:=] ?"(\\w+)"', ret)))))
v = main[main.index("def version():"):main.index('@app.get("/v1/sources")')]
print("GET /version, what is serving (main.py):")
print("  " + ", ".join(re.findall(r'"(\\w+)":', v)))
print("the events a degraded answer leaves in documind-api's log:")
for f in ("main.py", "retriever.py", "generator.py", "cache_manager.py"):
    for i, line in enumerate(open(root + f, encoding="utf-8"), 1):
        for ev in re.findall(r'"event": "(\\w+(?:fallback|stale|ignored|exhausted|truncated))"', line):
            print(f"  {ev:24} {f}:{i}")"""

ASK_PY = """import json, os, subprocess, urllib.request
label, P, API = os.environ["LABEL"], os.environ["PROJECT"], os.environ["API"]
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
body = json.dumps({"query": "What is the notice period for a confirmed E3?", "tenant_id": "acme"}).encode()
req = urllib.request.Request(API + "/v1/query", data=body, headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
ans = json.load(urllib.request.urlopen(req, timeout=120))
json.dump(ans, open(os.path.expanduser(f"~/ask131-{label}.json"), "w"), indent=1)
s = ans["stages"]
print(ans["answer"])
for n, c in enumerate(ans["citations"], 1):
    version, chunk = c["chunk_id"].split(":", 1)[1].split("#")
    print(f"  [{n}] {c['source_uri'].rsplit('/', 1)[-1]}  version {version[:12]}  chunk {chunk}  {c['quote']!r}")
print(f"  cache_hit {ans['cache_hit']} | backend {ans['backend']} | answerable {ans['answerable']}")
print(f"  store {s.get('retrieval_backend')} | vector_chunks {s.get('vector_chunks')} | pool {s.get('pool')} | "
      f"rerank_fallback {s.get('rerank_fallback', 0)} | policy_fallback {s.get('policy_fallback')}")
print(f"  kept in ~/ask131-{label}.json")"""

TRACE_RULES = """DECIDED = 20      # the pool's depth: config.py's TOP_K_RETRIEVE default, the number evals/ablate.py decided
RUNG_EVENTS = ("vector_search_fallback", "rag_engine_fallback", "vertex_search_fallback", "retrieval_pin_ignored")
CAUSE = {"the answer cache": "the answer cache", "the store and its rungs": "a fallback rung", "the pool": "a pool too small",
         "the reranker": "a fallback rung", "the version": "a version", "the model": "the model"}

def read_trail(ans, top_k, events, v):
    \"\"\"The marks, in the order the answer was made: (link, True clean / False off / None not reached, what it says).\"\"\"
    s, hit, none = ans["stages"], ans["cache_hit"] != "none", ans["backend"] == "none"
    pool, backend, fell = s.get("pool", 0), s.get("retrieval_backend"), [e for e in events if e in RUNG_EVENTS]
    marks = [("the answer cache", not hit, "served from the answer cache: an earlier answer, retrieval never ran" if hit
              else "cache_hit none: retrieval ran")]
    if hit:
        marks += [(link, None, "not reached: retrieval never ran") for link in ("the store and its rungs", "the pool", "the reranker")]
    else:
        own = s.get("vector_chunks", 0) if backend == "vector" else pool
        marks.append(("the store and its rungs", not fell and not s.get("policy_fallback") and own == pool,
                      f"{backend}: {own} of the pool's {pool} from its own index; "
                      + (f"fell back: {', '.join(fell)}" if fell else "no fallback event")
                      + ("; the tenant's data_region sent it to the kit's index" if s.get("policy_fallback") else "")))
        why = (f" (TOP_K_RETRIEVE={top_k} on the revision)" if top_k < DECIDED else
               " (nothing retrieved: a filter, or no such document)" if not pool else " (retired rows or a filter took the rest)")
        marks.append(("the pool", pool >= DECIDED, f"{pool} of the {DECIDED} the ablation decided" + ("" if pool >= DECIDED else why)))
        marks.append(("the reranker", None if not pool else not s.get("rerank_fallback"),
                      "not reached: nothing to order" if not pool else
                      "the Ranking API did not answer: the pool stood in by retrieval score" if s.get("rerank_fallback")
                      else "the Ranking API ordered the pool"))
    if not v:
        marks.append(("the version", None, "no citation to trace"))
    elif v["cited"] != v["ledger"]:
        marks.append(("the version", False, f"cites {v['cited'][:12]}, a version the ledger has retired; its current is {v['ledger'][:12]}"))
    elif not v["bucket_agrees"]:
        marks.append(("the version", False, "the bucket holds a newer object than the ledger: the last upload never landed"))
    elif v["golden"] and v["ledger"] != v["golden"]:
        marks.append(("the version", False, f"{v['source']}: the ledger's current since {v['since'][:16]} is {v['ledger'][:12]}, "
                      f"not the golden set's {v['golden'][:12]}" + (f"; it declares effective_from {v['effective']}" if v["effective"] else "")))
    else:
        marks.append(("the version", True, f"cites {v['cited'][:12]}, the ledger's current and the golden set's"))
    if none or hit:
        marks.append(("the model", None, "not called: " + ("the empty-pool refusal" if none else "a stored answer")))
    elif not ans["answerable"]:
        marks.append(("the model", False, f"refused with {pool} chunks in the pool: read what was packed, then make judge"))
    else:
        n = len(ans["citations"])
        marks.append(("the model", True, f"answered from {n} citation{'s' if n != 1 else ''}; groundedness is make judge's"))
    return marks

def cause(marks):
    off = [(n, link) for n, (link, ok, _) in enumerate(marks, 1) if ok is False]
    if not off:
        return "CAUSE: no link is off - the answer is what the lane holds; if it is still wrong, the golden set or the question is"
    n, link = off[0]
    return f"CAUSE: {CAUSE[link]} (link {n}) - every link before it is clean"
"""

TRACE_IO = """import hashlib, json, os, subprocess, urllib.request
from google.cloud import firestore
P, R, API, SINCE = os.environ["PROJECT"], os.environ["REGION"], os.environ["API"], os.environ["SINCE131"]
def gcloud(*a):
    return subprocess.run(["gcloud", *a], capture_output=True, text=True, check=True).stdout
tok = gcloud("auth", "print-identity-token", "--include-email", f"--audiences={API}",
             f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com").strip()
def api(path):
    return json.load(urllib.request.urlopen(urllib.request.Request(API + path, headers={"Authorization": "Bearer " + tok}), timeout=60))
ans = json.load(open(os.path.expanduser("~/ask131-after.json")))           # the answer that was reported
ver = api("/version")
print(f"serving: {ver['git_sha']}, {ver['generator_model']} via {ver['model_backend']}, prompt {ver['prompt']}, "
      f"{ver['embedding']}, current-only {ver['retrieval_current_only']}, answer cache {ver['semantic_cache']}")
svc = json.loads(gcloud("run", "services", "describe", "documind-api", "--region", R, "--project", P, "--format", "json"))
env = {e["name"]: e.get("value") for e in svc["spec"]["template"]["spec"]["containers"][0].get("env", [])}
top_k = int(env.get("TOP_K_RETRIEVE") or 20)                                # config.py's default when the revision sets none
ors = " OR ".join('jsonPayload.event="%s"' % e for e in RUNG_EVENTS + ("rerank_fallback", "cache_stale"))
flt = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
       f'AND timestamp>="{SINCE}" AND ({ors})')
events = [e["jsonPayload"]["event"] for e in json.loads(gcloud("logging", "read", flt, "--project", P, "--format", "json") or "[]")]
print(f"events since the break: {', '.join(events) or 'none'}")
v = None
if ans["citations"]:
    c = ans["citations"][0]
    name = c["source_uri"].split("/", 3)[3]                                   # acme/hr_policy_2026.md
    row = firestore.Client(project=P).collection("chunks").document(c["chunk_id"]).get().to_dict() or {}
    led = next(s for s in api("/v1/sources?tenant_id=" + name.split("/")[0])["sources"] if s["name"] == name)
    gen = gcloud("storage", "objects", "describe", c["source_uri"], "--format=value(generation)").strip()
    frozen = "evals/corpus/" + name                                           # the bytes the golden set was written against
    v = {"source": name, "cited": c["chunk_id"].split(":", 1)[1].split("#")[0], "ledger": led["doc_key"].split("_", 1)[1],
         "golden": hashlib.sha256(open(frozen, "rb").read()).hexdigest() if os.path.exists(frozen) else None,
         "since": led["indexed_at"] or "", "effective": row.get("effective_from"), "bucket_agrees": gen == led["generation"]}
print("the trail of ~/ask131-after.json, in the order the answer was made:")
marks = read_trail(ans, top_k, events, v)
for n, (link, ok, said) in enumerate(marks, 1):
    print(f"  {n} {link:24} {'clean' if ok else '-' if ok is None else 'OFF':5}  {said}")
print(cause(marks))"""
TRACE_PY = TRACE_IO.split("\nans = ", 1)[0] + "\n" + TRACE_RULES + "ans = " + TRACE_IO.split("\nans = ", 1)[1]


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


ASK_FN = ("ask131() {   # ask131 LABEL: acme's E3 notice-period question as documind-ui-sa - the answer and its trail, kept in ~/ask131-LABEL.json\n"
          + heredoc(ASK_PY, 'LABEL="$1" ') + "\n}")
CELLS = {
    "map": heredoc(MAP_PY),
    "ask": ASK_FN + "\nask131 before",
    "break": ('export SINCE131="$(date -u +%FT%TZ)"     # the trace reads the log from here\n'
              'make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/demo/hr_policy_2026_v2.md NAME=hr_policy_2026.md\n'
              "ask131 after"),
    "trace": heredoc(TRACE_PY),
    "probes": ('make sources PROJECT="$PROJECT" TENANT_ONLY=acme | grep -E "^source|hr_policy_2026"\n'
               'python commands/verify-vector-index.py --deploy-root "$DEMO_ROOT" --project "$PROJECT" --region "$REGION"\n'
               'GOOGLE_CLOUD_PROJECT="$PROJECT" python commands/check-firestore-fallback.py'),
    "restore": ('make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/corpus/acme/hr_policy_2026.md\n'
                "ask131 restored\n"
                'GOOGLE_CLOUD_PROJECT="$PROJECT" python commands/check-firestore-fallback.py | tail -1'),
}

T = Path(tempfile.mkdtemp(prefix="lesson131-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ,
       "REGION": "asia-south1", "GOOGLE_CLOUD_PROJECT": PROJ, "USERPROFILE": str(T), "HOME": str(T)}
for k in [k for k in ENV if k.startswith(("RETRIEVAL_", "TOP_K", "RERANK_", "SEMANTIC_", "VECTOR_", "GENERATOR_", "ARMOR", "ROUTING"))]:
    ENV.pop(k)


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T, ok_codes=(0,)) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode in ok_codes and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout


# ---- step 3: the trail as the kit writes it down
OUT = {"map": run_cell(MAP_PY, cwd=KIT)}
M3 = OUT["map"]
assert "  model, backend, cost_usd, tokens_in, tokens_out, cached_tokens, latency_ms, stages, cache_hit\n" in M3, M3
for k in ("pool", "vector_chunks", "rerank_fallback", "policy_fallback", "retrieval_backend", "retrieve_ms"):
    assert re.search(rf"\b{k}\b", M3.split("found_by")[0]), (k, M3)
assert "  firestore, graph, rag_engine, vector, vertex_search\n" in M3, M3
for ev in ("vector_search_fallback", "rerank_fallback", "cache_stale", "routing_fallback", "rag_engine_fallback", "retrieval_pin_ignored"):
    assert re.search(rf"^  {ev}\s+\w+\.py:\d+$", M3, re.M), (ev, M3)
STAGE_KEYS = M3.split("(main.py):\n  ", 1)[1].split("\n", 1)[0].split(", ")
RUNGS = M3.split("(retriever.py):\n  ", 1)[1].split("\n", 1)[0].split(", ")
EVENT_LINES = re.findall(r"^  (\w+)\s+\w+\.py:\d+$", M3, re.M)
assert len(STAGE_KEYS) == 10 and len(RUNGS) == 5 and len(EVENT_LINES) == 11 and len(set(EVENT_LINES)) == 9,(STAGE_KEYS, RUNGS, EVENT_LINES)
USAGE_ROW = src[MAIN][src[MAIN].index("def usage_row("):src[MAIN].index('@app.get("/health")')]
assert "vector_chunks" not in USAGE_ROW and all(f'"{k}"' in USAGE_ROW for k in ("pool", "rerank_fallback", "policy_fallback", "graph_chunks", "managed_chunks"))
assert 'RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))' in src["services/ingest/main.py"]
assert "Where sources disagree, follow the one with the latest" in src["services/rag-api/generator.py"]

# ---- the stand-in lane, a module every process below imports as lane131
LANE_LIB = r'''"""The stand-in lane for lesson 11.4's build. What rag-api, the two probes and the ledger report read is held in two
JSON files: the handbook's chunk rows, both versions, cut by the kit's own chunker, and the lane's state (which version
is current, the ledger rows, the tenant's pin). The kit's code runs unchanged on top of it. Only what sits below that
code is stood in: the SDK modules this machine does not have, Firestore, the index, the Ranking API, Gemini and gcloud."""
import collections
import datetime as dt
import json
import math
import os
import random
import re
import subprocess
import sys
import types
import uuid
from types import SimpleNamespace

KIT = os.environ["LANE131_KIT"]
with open(os.environ["LANE131_CORPUS"], encoding="utf-8") as _f:
    CORPUS = json.load(_f)
STATE_PATH = os.environ["LANE131_STATE"]
LAST = {"q": ""}                                   # the question embed_query was last given
TS = ("indexed_at", "reactivated_at", "superseded_at", "expire_at", "created_at", "updated_at")


def state() -> dict:
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---- similarity: the stand-in for text-embedding-005 and for the Ranking API - word overlap, TF-IDF weighted
STOP = set("a an the of for to in on at by is are be what which who how when does do i my can during with and or from as per this that it its".split())


def _toks(text: str, pairs: bool) -> list:
    w = [x for x in re.findall(r"[a-z0-9]+", text.lower()) if x not in STOP]
    return w + ([a + "_" + b for a, b in zip(w, w[1:])] if pairs else [])


_TEXTS = sorted({r["text"] for r in CORPUS["rows"].values()})
_DF = collections.Counter(t for text in _TEXTS for t in set(_toks(text, True)))
_VEC: dict = {}


def _vec(text: str, pairs: bool) -> dict:
    key = (text, pairs)
    if key not in _VEC:
        c = collections.Counter(_toks(text, pairs))
        v = {t: (1 + math.log(n)) * (math.log((len(_TEXTS) + 1) / (_DF.get(t, 0) + 1)) + 1) for t, n in c.items()}
        s = math.sqrt(sum(x * x for x in v.values())) or 1.0
        _VEC[key] = {t: x / s for t, x in v.items()}
    return _VEC[key]


def sim(a: str, b: str, pairs: bool = False) -> float:
    va, vb = _vec(a, pairs), _vec(b, pairs)
    return round(sum(x * vb.get(t, 0.0) for t, x in va.items()), 6)


_BY_EMB: dict = {}


def embedding(row_id: str) -> list:
    """A chunk row's stored vector: 768 floats, the same every time for the same row."""
    r = random.Random(row_id)
    e = [round(r.uniform(-0.1, 0.1), 6) or 1e-6 for _ in range(768)]
    _BY_EMB[(e[0], e[1])] = CORPUS["rows"][row_id]["text"]
    return e


# ---- Firestore, held in the two files (and, for what this process writes, in memory)
MEM: dict = collections.defaultdict(dict)


def _typed(d: dict) -> dict:
    for k in TS:
        if isinstance(d.get(k), str):
            d[k] = dt.datetime.fromisoformat(d[k])
    return d


def chunk_rows() -> dict:
    st, out = state(), {}
    for cid, row in CORPUS["rows"].items():
        d = dict(row)
        sha = d["doc_key"].split("_", 1)[1]
        d["current"] = sha == st["current"]
        d.update(st["versions"][sha])
        out[cid] = d
    return out


def rows(coll: str) -> dict:
    base = chunk_rows() if coll == "chunks" else {k: dict(v) for k, v in state().get(coll, {}).items()}
    for k, v in MEM[coll].items():
        base[k] = dict(v)
    return {k: _typed(v) for k, v in base.items()}


class Snap:
    def __init__(self, id_, data, ref=None):
        self.id, self._d, self.exists, self.reference = id_, data, data is not None, ref

    def to_dict(self):
        return None if self._d is None else dict(self._d)


class Doc:
    def __init__(self, coll: str, id_: str):
        self.coll, self.id = coll, id_

    def get(self):
        return Snap(self.id, rows(self.coll).get(self.id), self)

    def set(self, data, merge=False):
        MEM[self.coll][self.id] = {**(MEM[self.coll].get(self.id, {}) if merge else {}), **data}

    def delete(self):
        MEM[self.coll].pop(self.id, None)


def _holds(id_: str, d: dict, field: str, op: str, value) -> bool:
    x = id_ if field == "__name__" else d.get(field)
    if op == "==":
        return x == value
    if op == "in":
        return x in value
    raise NotImplementedError(op)


class Query:
    def __init__(self, coll: str, preds=(), lim=None):
        self.coll, self.preds, self.lim = coll, tuple(preds), lim

    def where(self, field=None, op=None, value=None, *, filter=None):
        if filter is not None:
            field, op, value = filter.field_path, filter.op_string, filter.value
        return Query(self.coll, self.preds + ((field, op, value),), self.lim)

    def limit(self, n):
        return Query(self.coll, self.preds, n)

    def select(self, fields):
        return self

    def document(self, id_):
        return Doc(self.coll, id_)

    def add(self, data):
        id_ = uuid.uuid4().hex
        MEM[self.coll][id_] = dict(data)
        return None, Doc(self.coll, id_)

    def matched(self) -> list:
        return [(i, d) for i, d in rows(self.coll).items() if all(_holds(i, d, *p) for p in self.preds)]

    def stream(self):
        out = []
        for i, d in self.matched()[:self.lim]:
            if self.coll == "chunks":
                d["embedding"] = embedding(i)
            out.append(Snap(i, d, Doc(self.coll, i)))
        return out

    get = stream

    def find_nearest(self, vector_field, query_vector, distance_measure=None, limit=10, distance_result_field=None, **kw):
        return Nearest(self, list(query_vector), limit, distance_result_field)


class Nearest:
    """find_nearest, exact: every row the predicates keep, ordered by the stand-in similarity to the query's text."""
    def __init__(self, q: Query, vec: list, limit: int, field):
        self.q, self.vec, self.limit, self.field = q, vec, limit, field

    def get(self):
        text = _BY_EMB.get((self.vec[0], self.vec[1])) or LAST["q"]
        key = "question" if self.q.coll == "answer_cache" else "text"
        # a tie is broken by the text first: two rows with the same text carry the same vector (the carry-over copies it),
        # so a retired version's twin sits beside its current row, as it does in an exact nearest-neighbour search
        scored = sorted(((sim(text, d.get(key) or ""), i, d) for i, d in self.q.matched()), key=lambda x: (-x[0], x[2].get(key) or "", x[1]))
        out = []
        for s, i, d in scored[:self.limit]:
            if self.field:
                d[self.field] = round(1.0 - s, 6)
            if self.q.coll == "chunks":
                d["embedding"] = embedding(i)
            out.append(Snap(i, d, Doc(self.q.coll, i)))
        return out


class DBClass:
    def collection(self, name):
        return Query(name)

    def batch(self):
        raise NotImplementedError("the stand-in lane writes nothing in batches")


DB = DBClass()


# ---- the index, the Ranking API and Gemini
class Neighbor:
    def __init__(self, id_, distance):
        self.id, self.distance = id_, distance


class Index:
    """find_neighbors over the CURRENT rows only: the worker takes a retired version's datapoints out of the index."""
    def find_neighbors(self, deployed_index_id, queries, num_neighbors, filter=None):
        from google.api_core.exceptions import NotFound
        if deployed_index_id != state()["deployed_index"]:
            raise NotFound(f"Deployed index {deployed_index_id} was not found on the index endpoint")
        allow = {ns.name: set(ns.allow_tokens) for ns in (filter or [])}
        def keep(d):
            vals = {"tenant_id": d["tenant_id"], "doc_type": d["doc_type"], "kind": d["kind"], "current": "true"}
            return all(vals.get(k) in toks for k, toks in allow.items())
        found = sorted(((sim(LAST["q"], d["text"]), i) for i, d in chunk_rows().items() if d["current"] and keep(d)),
                       key=lambda x: (-x[0], x[1]))[:num_neighbors]
        return [[Neighbor(i, s) for s, i in found]] if found else []


class Ranker:
    def ranking_config_path(self, project, location, ranking_config):
        return f"projects/{project}/locations/{location}/rankingConfigs/{ranking_config}"

    def rank(self, request, timeout=None):
        from google.api_core.exceptions import DeadlineExceeded
        if timeout is not None and timeout < 0.05:
            raise DeadlineExceeded(f"Deadline of {timeout}s exceeded while calling rank")
        order = sorted(((sim(request.query, r.content, pairs=True), int(r.id)) for r in request.records),
                       key=lambda x: (-x[0], x[1]))[:request.top_n]
        return SimpleNamespace(records=[SimpleNamespace(id=str(i), score=round(s, 4)) for s, i in order])


MONTHS = "January February March April May June July August September October November December".split()


def _reply(prompt: str):
    """Gemini, stood in by a reader: the E3 notice period from the packed clause that states it, cited, or a refusal."""
    ctx = prompt.split("\nContext:\n", 1)[1].rsplit("\n\nQuestion:", 1)[0]
    parts = re.split(r"(?m)^\[Source (\d+)\] ?(.*)$", ctx)
    draft = {"answer": "The context does not state the notice period for a confirmed E3.", "citations": [],
             "confidence": "low", "answerable": False}
    for k in range(1, len(parts) - 2, 3):
        n, header, body = int(parts[k]), parts[k + 1], parts[k + 2]
        m = re.search(r"serves a notice period of (\d+) days", body)
        if m and "E3" in body:
            eff = re.search(r"effective from (\d{4})-(\d{2})-(\d{2})", header)
            lead = f"From {int(eff.group(3))} {MONTHS[int(eff.group(2)) - 1]} {eff.group(1)}, a" if eff else "A"
            draft = {"answer": f"{lead} confirmed employee at grade E3 or above serves a notice period of {m.group(1)} days [{n}].",
                     "citations": [{"source": n, "quote": f"serves a notice period of {m.group(1)} days"}],
                     "confidence": "high", "answerable": True}
            break
    usage = SimpleNamespace(prompt_token_count=len(prompt) // 4, candidates_token_count=len(draft["answer"]) // 4 + 24,
                            thoughts_token_count=0, cached_content_token_count=0)
    return SimpleNamespace(parsed=draft, text=json.dumps(draft), usage_metadata=usage,
                           candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))], prompt_feedback=None)


class Models:
    def generate_content(self, model, contents, config=None):
        return _reply(contents[0] if isinstance(contents, list) else contents)


class GenaiClient:
    def __init__(self, *a, **kw):
        self.models, self.caches = Models(), None
        self._api_client = SimpleNamespace(location=kw.get("location"))


def _mod(name: str, **attrs):
    m = types.ModuleType(name)
    m.__dict__.update(attrs)
    sys.modules[name] = m
    return m


def stubs() -> None:
    """The modules rag-api imports that this machine does not have; nothing below reaches them."""
    if "google.cloud.discoveryengine_v1" in sys.modules:
        return
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

    class CloudTraceSpanExporter(SpanExporter):
        def __init__(self, **kw):
            pass

        def export(self, spans):
            return SpanExportResult.SUCCESS

        def shutdown(self):
            pass

    class FastAPIInstrumentor:
        @staticmethod
        def instrument_app(app, **kw):
            return None

    class GoogleGenAiSdkInstrumentor:
        def instrument(self, **kw):
            return None

    class Namespace:
        def __init__(self, name, allow_tokens=None, deny_tokens=None):
            self.name, self.allow_tokens, self.deny_tokens = name, list(allow_tokens or []), list(deny_tokens or [])

    class Rec:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class Anything:
        def __init__(self, *a, **kw):
            pass

        def __getattr__(self, name):
            return lambda *a, **kw: None

    _mod("opentelemetry.exporter.cloud_trace", CloudTraceSpanExporter=CloudTraceSpanExporter)
    _mod("opentelemetry.instrumentation.fastapi", FastAPIInstrumentor=FastAPIInstrumentor)
    _mod("opentelemetry.instrumentation.google_genai", GoogleGenAiSdkInstrumentor=GoogleGenAiSdkInstrumentor)
    _mod("google.cloud.aiplatform", MatchingEngineIndexEndpoint=Anything, MatchingEngineIndex=Anything, init=lambda **kw: None)
    _mod("google.cloud.aiplatform.matching_engine")
    _mod("google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint", Namespace=Namespace)
    _mod("google.cloud.discoveryengine_v1", RankServiceClient=Anything, RankingRecord=Rec, RankRequest=Rec)
    for name in ("bigquery", "storage", "spanner", "logging"):
        _mod(f"google.cloud.{name}", Client=Anything)
    import google.genai
    google.genai.Client = GenaiClient
    import google.cloud.firestore
    google.cloud.firestore.Client = lambda *a, **kw: DB


def rag():
    """rag-api's modules, imported from the kit and wired to the stand-ins above."""
    stubs()
    sys.path[:0] = [KIT, os.path.join(KIT, "services", "rag-api")]
    import main
    import retriever
    import generator
    import cache_manager
    main._fs = retriever._fs = lambda: DB
    retriever._index_endpoint = lambda: Index()
    retriever._ranker = lambda: Ranker()

    def embed(q):
        LAST["q"] = q
        return [0.001] * 768
    main.embed_query = retriever.embed_query = embed
    main.enforce_membership = lambda email, tenant_id: None     # the roster is lesson 8's; every ask here is a member's
    main.record = lambda db, usd: None                         # the month's budget counter is 11.6's

    def caches():
        m = object.__new__(cache_manager.TenantCacheManager)
        m.db, m.global_client, m.regional_client = DB, GenaiClient(), GenaiClient()
        return m
    generator._caches = caches
    return main


def serve(port: int, who: dict) -> None:
    """The kit's app on localhost, behind a stand-in of Cloud Run's IAM check."""
    main = rag()
    import shared.iap as iap

    def identity(headers, bearer_audience=None):
        tok = headers.get("authorization", "").removeprefix("Bearer ")
        if tok not in who:
            raise iap.IapError("the bearer token carries no verified email")
        return {"email": who[tok], "via": "iam", "aud": bearer_audience}
    iap.identity = identity

    class FrontDoor:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http" and not dict(scope["headers"]).get(b"authorization"):
                await send({"type": "http.response.start", "status": 403, "headers": [(b"content-type", b"text/html")]})
                await send({"type": "http.response.body", "body": b"<html><title>403 Forbidden</title></html>"})
                return
            await self.app(scope, receive, send)
    import uvicorn
    uvicorn.run(FrontDoor(main.app), host="127.0.0.1", port=port, log_level="warning")


# ---- gcloud and terraform, for the cells
NUMBER = "314159265358"


def _gcloud(cmd: list) -> str:
    st = state()
    if cmd[:3] == ["gcloud", "auth", "print-identity-token"]:
        return "MEMBER\n"
    if cmd[:4] == ["gcloud", "run", "services", "describe"]:
        env = [{"name": k, "value": v} for k, v in st["service_env"].items()]
        return json.dumps({"spec": {"template": {"spec": {"containers": [{"env": env}]}}}})
    if cmd[:3] == ["gcloud", "logging", "read"]:
        with open(os.environ["LANE131_LOG"], encoding="utf-8") as f:
            lines = f.read()[int(os.environ["LANE131_LOG_FROM"]):].splitlines()
        wanted = set(re.findall(r'"(\w+)"', cmd[3].split("jsonPayload.event=", 1)[1]))
        out = []
        for line in lines:
            if line.startswith("{"):
                j = json.loads(line)
                if j.get("event") in wanted:
                    out.append({"jsonPayload": j})
        return json.dumps(out)
    if cmd[:4] == ["gcloud", "storage", "objects", "describe"]:
        return st["generation"] + "\n"
    if cmd[:3] == ["gcloud", "projects", "describe"]:
        return json.dumps({"projectId": cmd[3], "projectNumber": NUMBER, "lifecycleState": "ACTIVE"})
    if cmd[0] == "terraform":
        return st["terraform"][cmd[-1]]
    if cmd[:3] == ["gcloud", "ai", "indexes"]:
        return json.dumps(st["index"])
    if cmd[:3] == ["gcloud", "ai", "index-endpoints"]:
        return json.dumps(st["endpoint"])
    raise SystemExit(f"the stand-in gcloud has no answer for {cmd[:4]}")


def fake_cli() -> None:
    """gcloud and terraform answer from the lane's state; the rest of subprocess stays."""
    real = subprocess.run

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] in ("gcloud", "terraform"):
            return subprocess.CompletedProcess(list(cmd), 0, _gcloud(list(cmd)), "")
        return real(cmd, *a, **kw)
    subprocess.run = run
'''

# ---- the stand-in lane: the handbook's two versions, as the kit's chunker cuts them, with the worker's chunk ids
sys.path.insert(0, str(KIT))
from shared import doc_types  # noqa: E402
from shared.documind_corpus import chunk_document  # noqa: E402
# the labels lesson 10.4's relabel leaves on the handbook: the pin's rows carry its class, any other version stays unknown
ENTRY = doc_types.registry_from_manifest()[NAME]
assert ENTRY["sha256"] == SHA1 and ENTRY["doc_type"] == "policy", ENTRY        # the manifest's bytes are version 1: the pin
LABEL = {SHA1: ENTRY["doc_type"], SHA2: doc_types.UNKNOWN}                     # revision 2 is a pin miss
# the filter case: a doc_type rag-api accepts (check_filters takes any non-empty string) that no row holds on any tenant.
# Every registry class is held, each one on acme, so no class can be it: the first value the MCP server's list offers
# that is not a class, a manifest type or a media type the worker writes
MANIFEST = json.loads(doc_types.MANIFEST.read_text(encoding="utf-8"))
MEDIA = set(ast.literal_eval(re.search(r"^MEDIA_TYPES = (\{.*?\})$", src["services/ingest/main.py"], re.M | re.S).group(1)).values())
HELD = {m["doc_type"] for m in MANIFEST} | MEDIA | {doc_types.UNKNOWN}
assert set(doc_types.CLASSES) <= {m["doc_type"] for m in MANIFEST if m["tenant_id"] == "acme"}, doc_types.CLASSES
OFFERED = ast.literal_eval(re.search(r"^DOC_TYPES = (\(.*\))$", (KIT / "services/mcp/server.py").read_text(encoding="utf-8"), re.M).group(1))
FILTER_TYPE = next(t for t in OFFERED if t not in HELD)
assert FILTER_TYPE == "form" and FILTER_TYPE not in doc_types.CLASSES, FILTER_TYPE
ROWS = {}
T_FIRST = {SHA1: "2026-09-10T09:14:02+00:00", SHA2: "2026-09-21T10:05:44+00:00"}
for sha, data in ((SHA1, B1), (SHA2, B2)):
    cut = chunk_document({"text": data.decode("utf-8"), "source_uri": URI, "doc_type": LABEL[sha], "slug": "hr_policy_2026"}, "acme")
    eff = "2026-10-01" if sha == SHA2 else None
    for i, c in enumerate(cut):
        row = {"tenant_id": "acme", "text": c["text"], "source_uri": URI, "page_start": None, "doc_type": LABEL[sha], "kind": "text",
               "doc_key": f"acme_{sha}", "chunk_hash": c["chunk_hash"], "locator": c["locator"], "embedding_model": "text-embedding-005",
               "embedding_version": "1", "embedding_task_type": "RETRIEVAL_DOCUMENT", "indexed_at": T_FIRST[sha]}
        if c.get("section"):
            row["section"] = c["section"]
        if eff:
            row["effective_from"] = eff
        ROWS[f"acme:{sha}#{i}"] = row
N1 = sum(1 for r in ROWS.values() if r["doc_key"] == f"acme_{SHA1}")
assert N1 == 283 and len(ROWS) == 566, (N1, len(ROWS))
NP03 = {sha: next(i for i, r in ROWS.items() if r["doc_key"] == f"acme_{sha}" and r["locator"] == "NP-03") for sha in (SHA1, SHA2)}
assert NP03[SHA1] == f"acme:{SHA1}#1" and NP03[SHA2] == f"acme:{SHA2}#1" and "60 days" in ROWS[NP03[SHA1]]["text"] and "90 days" in ROWS[NP03[SHA2]]["text"]
HASH1 = {r["chunk_hash"] for r in ROWS.values() if r["doc_key"] == f"acme_{SHA1}"}
assert sum(1 for r in ROWS.values() if r["doc_key"] == f"acme_{SHA2}" and r["chunk_hash"] in HASH1) == 281   # a fresh ingest: 281 reused, 2 embedded
(T / "corpus131.json").write_text(json.dumps({"rows": ROWS}), encoding="utf-8")
(T / "lane131.py").write_text(LANE_LIB, encoding="utf-8")

T_EARLIER, T_BREAK, T_RESTORE = "2026-09-21T10:21:09+00:00", "2026-09-23T10:41:07+00:00", "2026-09-23T10:52:31+00:00"
GEN = {"earlier": "1758450069811342", "break": "1758624067215604", "restore": "1758624751090381"}
IDX = "projects/{p}/locations/asia-south1/indexes/1234567890123456789"
EP = "projects/{p}/locations/asia-south1/indexEndpoints/9876543210987654321"
SERVICE_ENV = {"GOOGLE_CLOUD_PROJECT": PROJ, "RETRIEVAL_BACKEND": "firestore", "VECTOR_INDEX_ENDPOINT": EP.format(p="NUMBER"),
               "VECTOR_DEPLOYED_INDEX_ID": "documind_chunks_v1", "GENERATOR_MODEL": "gemini-3.6-flash", "RETRIEVAL_CURRENT_ONLY": "off",
               "SEMANTIC_CACHE": "off", "GIT_SHA": "COMMIT", "SELF_URL": "https://documind-api-NUMBER.asia-south1.run.app"}


def fingerprint(doc_keys) -> str:                  # idempotency.corpus_fingerprint over the tenant's current doc_keys
    return sha256("\n".join(sorted(doc_keys)).encode("utf-8")).hexdigest()[:16]


def lane(current: str, since: str, gen: str) -> dict:
    old = SHA2 if current == SHA1 else SHA1
    retired_at = T_EARLIER if current == SHA1 and since == T_EARLIER else since
    expire = (datetime.fromisoformat(retired_at) + timedelta(days=30)).isoformat()
    versions = {current: {"indexed_at": T_FIRST[current], "reactivated_at": since},
                old: {"indexed_at": T_FIRST[old], "superseded_by": f"acme_{current}", "superseded_at": retired_at, "expire_at": expire}}
    return {"current": current, "versions": versions, "generation": gen, "deployed_index": "documind_chunks_v1",
            "service_env": SERVICE_ENV,
            "sources": {"acme~hr_policy_2026.md": {"tenant_id": "acme", "name": NAME, "gcs_uri": URI, "doc_key": f"acme_{current}",
                                                    "generation": gen, "sha256": current, "chunks": 283, "effective_from": None,
                                                    "status": "indexed", "reused": 283, "embedded": 0, "retired": 283, "indexed_at": since,
                                                    "embedding_model": "text-embedding-005", "embedding_version": "1"}},
            "ledger": {"acme": {"tenant_id": "acme", "fingerprint": fingerprint([f"acme_{current}"]), "versions": 1,
                                "last_event": "ingest_reactivated"}},
            "tenant_settings": {"acme": {"retrieval_backend": "vector"}},
            "terraform": {"vector_index_name": IDX.format(p=PROJ), "vector_index_endpoint": EP.format(p=PROJ),
                          "vector_deployed_index_id": "documind_chunks_v1"},
            "index": {"name": IDX.format(p="314159265358"), "indexUpdateMethod": "STREAM_UPDATE", "metadata": {"config": {"dimensions": 768}},
                      "indexStats": {"vectorsCount": "1745"}},
            "endpoint": {"name": EP.format(p="314159265358"), "deployedIndexes": [{"id": "documind_chunks_v1", "index": IDX.format(p="314159265358"),
                                                                                "indexSyncTime": "2026-09-23T10:42:18.000Z"}]}}


BEFORE, AFTER, RESTORED = lane(SHA1, T_EARLIER, GEN["earlier"]), lane(SHA2, T_BREAK, GEN["break"]), lane(SHA1, T_RESTORE, GEN["restore"])
STATE = T / "state131.json"
LANE_ENV = {"LANE131_KIT": str(KIT), "LANE131_CORPUS": str(T / "corpus131.json"), "LANE131_STATE": str(STATE), "PYTHONPATH": str(T)}


def put(st: dict) -> None:
    STATE.write_text(json.dumps(st), encoding="utf-8")


# ---- the panel: the kit's query() under seven breaks, one process each (the settings are read at import)
CASE_PY = f"""import json, os
import lane131
main = lane131.rag()
from schemas import QueryRequest
filters = json.loads(os.environ.get("CASE_FILTERS") or "null")
print("BEGIN")
for _ in range(int(os.environ.get("CASE_TIMES", "1"))):
    ans = main.query(QueryRequest(query={Q!r}, tenant_id="acme", filters=filters), user={{"email": {UI_SA!r}}})
print("RESULT " + ans.model_dump_json())
"""
CASES = {
    "none": ("Nothing broken", BEFORE, {}, None, 1),
    "version": ("The handbook re-issued: revision 2 is current", AFTER, {}, None, 1),
    "index": ("The index unreachable: a wrong VECTOR_DEPLOYED_INDEX_ID", BEFORE, {"VECTOR_DEPLOYED_INDEX_ID": "documind_missing"}, None, 1),
    "ranker": ("The Ranking API timing out: RERANK_TIMEOUT_S=0.001", BEFORE, {"RERANK_TIMEOUT_S": "0.001"}, None, 1),
    "pool": ("A shallow pool: TOP_K_RETRIEVE=2", BEFORE, {"TOP_K_RETRIEVE": "2"}, None, 1),
    "filter": (f"A filter nothing matches: doc_type {FILTER_TYPE}", BEFORE, {}, {"doc_type": FILTER_TYPE}, 1),
    "cache": ("The answer cache on, the question asked twice", BEFORE, {"SEMANTIC_CACHE": "on"}, None, 2),
}
rules: dict = {}
exec(TRACE_RULES, rules)                            # the trace cell's own read_trail() and cause()
PANEL = {}
for key, (label, st, extra, filters, times) in CASES.items():
    put(st)
    out = run_cell(CASE_PY, env={**LANE_ENV, **SERVICE_ENV, **extra, "CASE_FILTERS": json.dumps(filters), "CASE_TIMES": str(times)})
    logs, result = out.split("BEGIN\n", 1)[1].rsplit("RESULT ", 1)
    ans = json.loads(result)
    lines = [json.loads(line) for line in logs.splitlines() if line.startswith("{")]
    events = [j["event"] for j in lines if j.get("event") != "query"]
    top_k = int({**SERVICE_ENV, **extra}.get("TOP_K_RETRIEVE", 20))
    v = None
    if ans["citations"]:
        cid = ans["citations"][0]["chunk_id"]
        cur = st["current"]
        v = {"source": NAME, "cited": cid.split(":", 1)[1].split("#")[0], "ledger": cur, "golden": SHA1, "since": st["sources"]["acme~hr_policy_2026.md"]["indexed_at"],
             "effective": ROWS[cid].get("effective_from"), "bucket_agrees": True}
    marks = rules["read_trail"](ans, top_k, events, v)
    right = ans["answerable"] and "60" in ans["answer"] and "90 days" not in ans["answer"]
    PANEL[key] = {"label": label, "answer": ans["answer"], "right": right, "cache_hit": ans["cache_hit"], "backend": ans["backend"],
                  "stages": {k: ans["stages"].get(k) for k in ("retrieval_backend", "vector_chunks", "pool", "rerank_fallback", "policy_fallback")},
                  "version": (v["cited"][:12] + (" (revision 2)" if v["cited"] == SHA2 else " (version 1)")) if v else "none",
                  "events": [f"{j['event']}: {j.get('error', '')}".rstrip(": ") for j in lines if j.get("event") != "query"],
                  "marks": [[link, ok, said] for link, ok, said in marks], "cause": rules["cause"](marks)}
P_ = PANEL
assert P_["none"]["right"] and P_["none"]["cause"].startswith("CAUSE: no link is off") and P_["none"]["stages"]["pool"] == 20
assert not P_["version"]["right"] and "90 days" in P_["version"]["answer"] and P_["version"]["cause"] == "CAUSE: a version (link 5) - every link before it is clean"
assert P_["index"]["right"] and P_["index"]["stages"]["vector_chunks"] == 0 and P_["index"]["cause"].startswith("CAUSE: a fallback rung (link 2)")
POOL_ON_RUNG = P_["index"]["stages"]["pool"]
assert 0 < POOL_ON_RUNG < 20, POOL_ON_RUNG                                    # the retired rows took the Firestore rung's slots
assert P_["index"]["events"][0].startswith("vector_search_fallback: 404 Deployed index documind_missing")
assert P_["ranker"]["right"] and P_["ranker"]["events"] == ["rerank_fallback: DeadlineExceeded"] and P_["ranker"]["cause"].startswith("CAUSE: a fallback rung (link 4)")
assert P_["pool"]["right"] and P_["pool"]["stages"]["pool"] == 2 and P_["pool"]["cause"].startswith("CAUSE: a pool too small (link 3)")
assert not P_["filter"]["right"] and P_["filter"]["backend"] == "none" and P_["filter"]["cause"].startswith("CAUSE: a pool too small (link 3)")
assert P_["cache"]["right"] and P_["cache"]["cache_hit"] == "semantic" and P_["cache"]["cause"].startswith("CAUSE: the answer cache (link 1)")
N_RIGHT = sum(p["right"] for p in PANEL.values())
put(BEFORE)                                         # the old case, doc_type policy, finds version 1 since the relabel
OLD = json.loads(run_cell(CASE_PY, env={**LANE_ENV, **SERVICE_ENV, "CASE_FILTERS": json.dumps({"doc_type": LABEL[SHA1]})}).rsplit("RESULT ", 1)[1])
assert OLD["answerable"] and OLD["stages"]["pool"] > 0 and OLD["backend"] != "none", OLD["stages"]
assert N_RIGHT == 5 and all(any(m[1] is False for m in p["marks"]) for k, p in PANEL.items() if k != "none")   # every break moves a mark

# ---- steps 4 to 6: the kit's app on localhost, the cells against it
with socket.socket() as s:
    assert s.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} is taken on this machine"
LOG = T / "api131.log"
URL = f"http://127.0.0.1:{PORT}"
put(BEFORE)
with open(LOG, "w", encoding="utf-8") as logf:
    srv = subprocess.Popen([sys.executable, "-c", f"import lane131; lane131.serve({PORT}, {{'MEMBER': {UI_SA!r}}})"],
                           cwd=str(T), env={**ENV, **LANE_ENV, **SERVICE_ENV}, stdout=logf, stderr=subprocess.STDOUT)
PRELUDE = "import lane131\nlane131.stubs()\nlane131.fake_cli()\n"
CELL_ENV = {**LANE_ENV, "API": URL, "LANE131_LOG": str(LOG)}
try:
    for _ in range(150):
        try:
            urllib.request.urlopen(urllib.request.Request(URL + "/health", headers={"Authorization": "Bearer MEMBER"}), timeout=1).read()
            break
        except Exception:                          # noqa: BLE001 - not up yet
            time.sleep(0.2)
    else:
        raise SystemExit("the API did not start: " + LOG.read_text(encoding="utf-8")[-1500:])
    OUT["ask"] = run_cell(ASK_PY, PRELUDE, env={**CELL_ENV, "LABEL": "before"})
    put(AFTER)
    since_at = len(LOG.read_text(encoding="utf-8"))
    OUT["after"] = run_cell(ASK_PY, PRELUDE, env={**CELL_ENV, "LABEL": "after"})
    OUT["trace"] = run_cell(TRACE_PY, PRELUDE, cwd=KIT, env={**CELL_ENV, "SINCE131": "2026-09-23T10:40:58Z", "LANE131_LOG_FROM": str(since_at)})
    # make sources: the kit's reconcile.py --report, filtered the way the cell's grep filters it
    SOURCES_PY = ("import runpy, sys\nsys.path.insert(0, 'services/ingest')\n"
                  f"sys.argv = ['reconcile.py', '--project', {PROJ!r}, '--report', '--tenant', 'acme']\n"
                  "runpy.run_path('services/ingest/reconcile.py', run_name='__main__')\n")
    rep = run_cell(SOURCES_PY, PRELUDE, cwd=KIT, env=CELL_ENV)
    kept = [line for line in rep.splitlines() if re.search(r"^source|hr_policy_2026", line)]
    VV_PY = ("import runpy, sys\n"
             f"sys.argv = ['verify-vector-index.py', '--deploy-root', {str(T / 'kit131')!r}, '--project', {PROJ!r}, '--region', 'asia-south1']\n"
             "try:\n    runpy.run_path('commands/verify-vector-index.py', run_name='__main__')\nexcept SystemExit as e:\n    assert not e.code, e.code\n")
    (T / "kit131" / "terraform").mkdir(parents=True)
    vv = run_cell(VV_PY, PRELUDE, cwd=KIT, env=CELL_ENV).replace("314159265358", "NUMBER")
    FB_PY = ("import runpy, sys\nsys.argv = ['check-firestore-fallback.py']\n"
             f"runpy.run_path({str(KIT / PROBE)!r}, run_name='__main__')\n")
    r = subprocess.run([sys.executable, "-"], input=PRELUDE + FB_PY, cwd=str(T), capture_output=True, text=True, encoding="utf-8", env={**ENV, **CELL_ENV})
    stop = "STOP: HR source ledger does not match the selected local HR file; review the source version."
    assert r.returncode == 1 and r.stderr.strip() == stop, (r.stdout, r.stderr[-1500:])
    OUT["probes"] = "\n".join(kept) + "\n" + vv + r.stdout + stop + "\n"
    put(RESTORED)
    OUT["restored"] = run_cell(ASK_PY, PRELUDE, env={**CELL_ENV, "LABEL": "restored"})
    fb = run_cell(FB_PY, PRELUDE, env=CELL_ENV)
    OUT["restore_fb"] = fb.strip().splitlines()[-1].replace("\\", "/") + "\n"      # this machine's path separator, not the lane's
finally:
    srv.terminate()
    srv.wait(timeout=20)

A4, A5, T6, P6 = OUT["ask"], OUT["after"], OUT["trace"], OUT["probes"]
assert A4.startswith("A confirmed employee at grade E3 or above serves a notice period of 60 days [1].\n"), A4
assert f"  [1] hr_policy_2026.md  version {SHA1[:12]}  chunk 1  'serves a notice period of 60 days'\n" in A4, A4
assert "  store vector | vector_chunks 20 | pool 20 | rerank_fallback 0 | policy_fallback 0\n" in A4, A4
assert A5.startswith("From 1 October 2026, a confirmed employee at grade E3 or above serves a notice period of 90 days [1].\n"), A5
assert f"version {SHA2[:12]}  chunk 1" in A5 and "  store vector | vector_chunks 20 | pool 20 | rerank_fallback 0 | policy_fallback 0\n" in A5, A5
assert "serving: COMMIT, gemini-3.6-flash via vertex, prompt documind-rag@v3, text-embedding-005@1, current-only off, answer cache off\n" in T6, T6
assert "events since the break: none\n" in T6 and T6.rstrip().endswith("CAUSE: a version (link 5) - every link before it is clean"), T6
assert re.search(r"^  5 the version\s+OFF\s+acme/hr_policy_2026\.md: the ledger's current since 2026-09-23T10:41 is " + SHA2[:12]
                 + ", not the golden set's " + SHA1[:12] + "; it declares effective_from 2026-10-01$", T6, re.M), T6
assert sum(1 for line in T6.splitlines() if re.match(r"^  \d the .* clean ", line)) == 5, T6
assert re.search(r"^acme/hr_policy_2026\.md\s+indexed\s+" + GEN["break"] + r"\s+283\s+283\s+0\s+283 -\s+text-embedding-005@1\s+2026-09-23T10:41:07$", P6, re.M), P6
assert "PASS: the expected index is attached to the expected endpoint." in P6 and "Deployment: documind_chunks_v1" in P6, P6
assert P6.rstrip().endswith("STOP: HR source ledger does not match the selected local HR file; review the source version."), P6
assert f'"source_doc_key": "acme_{SHA2}"' in P6, P6
assert OUT["restored"].startswith("A confirmed employee at grade E3 or above serves a notice period of 60 days [1].\n"), OUT["restored"]
assert OUT["restore_fb"] == "PASS: both Firestore filter modes verified. Evidence: operator-evidence/firestore-combined-filters.json\n", OUT["restore_fb"]

# the two reindexes are the worker's, not stood in here: their lines are the shape reindex.sh prints (lesson 6.3's counts)
HEAD = f">> gs://{PROJ}-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)\n>> event doc_key chunks reused embedded retired effective_from\n"
GATE = f">> the gate, scoped to this document, on a candidate: make eval-live PROJECT={PROJ} SOURCE=hr_policy_2026.md API=<candidate url>\n"
OUT["break"] = HEAD + f">> ingest_reactivated\tacme_{SHA2[:16]}...\t283\t283\t0\t283\n" + GATE + A5
OUT["restore"] = HEAD + f">> ingest_reactivated\tacme_{SHA1[:16]}...\t283\t283\t0\t283\n" + GATE + OUT["restored"] + OUT["restore_fb"]
OUT.pop("after"), OUT.pop("restored"), OUT.pop("restore_fb")
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "map": "run in the operator shell, in the kit (the trail as the kit writes it down; no network)",
    "ask": "run in the operator shell, in the kit (the question, the answer and its trail)",
    "break": "run in the operator shell, in the kit (revision 2 re-issued, then the same question)",
    "trace": "run in the operator shell, in the kit (the trace: reads only)",
    "probes": "run in the operator shell, in $DEMO_ROOT (the versions view and the two probes; reads only)",
    "restore": "run in the operator shell, in the kit (version 1 back, the question again, the probe again)",
}
OUT_LABELS = {
    "map": "(this cell run on the kit's own main.py, retriever.py, schemas.py, generator.py and cache_manager.py)",
    "ask": "(the kit's rag-api on a stand-in lane; your version hash is the one in your ledger)",
    "break": "(the reindex lines are the shape reindex.sh prints for a lane that re-issued revision 2 inside 30 days; the answer is the kit's rag-api on the stand-in lane)",
    "trace": "(the kit's rag-api, a fake gcloud and a fake Firestore; your times and hashes are your lane's)",
    "probes": "(make sources and both probes are the kit's own, on the stand-in lane; your ids, counts and times differ)",
    "restore": "(the reindex lines are the shape reindex.sh prints; the rest is the kit's rag-api and probe on the stand-in lane)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: break one thing, read the trail
UI_JS = r"""var root = document.getElementById('tr'); if (!root) return;
  var D = %s, ORDER = %s, $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
  function row(out, name, text, cls){ out.appendChild(el('b', '', name)); out.appendChild(el('span', cls || '', text)); }
  function render(){ var d = D[$('tr-break').value], s = d.stages, out = $('tr-out'); out.textContent = '';
    row(out, 'The answer', d.answer, d.right ? 'pass' : 'stop');
    row(out, 'Against lk-06', d.right ? 'right: 60 days, as the golden set says' : 'WRONG: the golden set says 60 days', d.right ? 'pass' : 'stop');
    row(out, 'The trail', 'cache_hit ' + d.cache_hit + ' | backend ' + d.backend + ' | store ' + s.retrieval_backend + ' | vector_chunks ' + s.vector_chunks +
        ' | pool ' + s.pool + ' | rerank_fallback ' + (s.rerank_fallback || 0) + ' | policy_fallback ' + s.policy_fallback + ' | cited ' + d.version);
    row(out, 'The log', d.events.length ? d.events.join('; ') : 'no fallback event', d.events.length ? 'stop' : 'skip');
    d.marks.forEach(function(m, i){ row(out, (i + 1) + ' ' + m[0], (m[1] === true ? 'clean: ' : m[1] === false ? 'OFF: ' : 'not reached: ') +
        m[2].replace(/^not reached: /, ''), m[1] === true ? 'pass' : m[1] === false ? 'stop' : 'skip'); });
    row(out, 'The trace says', d.cause.replace(/^CAUSE: /, ''), /no link is off/.test(d.cause) ? 'pass' : 'stop'); }
  ORDER.forEach(function(k){ var o = el('option', '', D[k].label); o.value = k; $('tr-break').appendChild(o); });
  $('tr-break').addEventListener('change', render);
  $('tr-break').value = 'version'; render();""" % (json.dumps(PANEL), json.dumps(list(CASES)))

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

WORDS = {6: "six", 7: "seven", 8: "eight", 9: "nine"}
STATS = {"FILTER_TYPE": FILTER_TYPE, "N_CLASSES": WORDS[len(doc_types.CLASSES)], "N_CASES": str(len(CASES)), "N_RIGHT": str(N_RIGHT), "POOL_ON_RUNG": str(POOL_ON_RUNG), "SHA1": SHA1[:12], "SHA2": SHA2[:12],
         "N_STAGE_KEYS": str(len(STAGE_KEYS)), "N_RUNGS": str(len(RUNGS)), "N_EVENTS": str(len(set(EVENT_LINES))), "N_EVENT_LINES": str(len(EVENT_LINES))}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    for k, p in PANEL.items():
        print(f"----- {k}: {p['answer']} | {p['stages']} | {p['events']} | {p['cause']}")
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: the map from main.py/retriever.py, the trail from the kit's rag-api on a stand-in lane (283 chunks a version),"
      f" make sources and both probes the kit's own | {len(CASES)} panel breaks, {N_RIGHT} still right, the Firestore rung's pool {POOL_ON_RUNG}")
