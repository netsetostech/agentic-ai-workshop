"""Build lesson 6.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Two caches that cache different things. The explicit Gemini context cache (cache_manager.py, make cache) holds a
PREFIX of the model's input on Google's side: the model still runs for every question, and the cached tokens are
billed at a tenth. The semantic answer cache (semantic_cache.py, SEMANTIC_CACHE=on) holds the ANSWER in Firestore: a
hit skips retrieval, the reranker and the model, and the row says model_backend=cache at cost 0. The panel's three
boxes are the kit's own rules, executed here: generate_config_kwargs() with get() and stale_against() on all 16
combinations, lookup() on a fake Firestore for all 128, and price() on a grid - node must agree with each. The lane
cells run against stand-ins: the asks against a local stub of the API, make cache's printing is cache_admin.main()'s
own over a fake manager, the rows cell against a fake gcloud, the holdings cell against a fake Firestore.
"""
import ast
import datetime as dt
import html
import importlib.util
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import textwrap
import threading
import types
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "6.2"
title = "<title>Lesson 6.2 Compare context caching and answer caching - a cached prefix the model still reads, and a stored answer the model never sees | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
CAND = "https://candidate---documind-api-NUMBER.asia-south1.run.app"
Q91 = "How many days a month can I work remotely?"
Q_LOWER = "how many days a month can i work remotely"
Q_PARA = "How many days per month am I allowed to work from home?"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select,.pc-in input{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.pc-steps{margin:6px 0 0;padding-left:20px;}
.pc-steps li{margin:3px 0;}
.pc-steps li.no{color:#991b1b;}.pc-steps li.ok{color:#065f46;}.pc-steps li.skip{color:#94a3b8;}
.pc-out{font-family:var(--mono);font-size:13px;font-weight:700;padding:5px 10px;border-radius:8px;display:inline-block;margin-top:6px;}
.pc-out.ok{background:#d1fae5;color:#065f46;}.pc-out.no{background:#fee2e2;color:#991b1b;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
CM, CA, GEN, COST = "services/rag-api/cache_manager.py", "services/rag-api/cache_admin.py", "services/rag-api/generator.py", "services/rag-api/cost.py"
SC, MAIN = "services/rag-api/semantic_cache.py", "services/rag-api/main.py"
EXCERPTS = {
    "pack": ("services/rag-api/cache_admin.py - pack_for(): the tenant's synthetic documents, joined, and the corpus manifest's hash",
             block(CA, "def pack_for(tenant: str")),
    "create": ("services/rag-api/cache_manager.py - create(): one cache on global, a regional fallback, and the record in tenant_caches",
               block(CM, "    def create(self, tenant_id: str, system_instruction: str, pack: str", end="    def get(self")),
    "attach": ("services/rag-api/cache_manager.py - generate_config_kwargs(): attached only when alive, the model's, and not stale",
               block(CM, "    def get(self, tenant_id: str, min_remaining_s: int = 120)", n=8) + "\n...\n"
               + block(CM, "    def generate_config_kwargs(self, tenant_id: str, model: str | None = None) -> dict:")),
    "call": ("services/rag-api/generator.py - the prompt is the same with or without a cache; the cache is one more keyword",
             block(GEN, r'    prompt = f"{SYSTEM}{_dated_rule(packed)}\n\nContext:', n=1) + "\n...\n"
             + block(GEN, "def _call(prompt: str, packed: list[dict], tenant_id: str | None, max_tokens: int, model: str | None = None):", end="def _exhausted_tier(")),
    "price": ("services/rag-api/cost.py - price(): the cached tokens at a tenth of the input rate",
              block(COST, "def price(model: str, tokens_in: int, tokens_out: int,")),
    "alive": ("services/rag-api/semantic_cache.py - _alive(): the same corpus, the same scope, not expired",
              block(SC, "def _alive(d: dict, fingerprint: str | None, scope: str, now: datetime) -> bool:", end="def lookup(")),
    "lookup": ("services/rag-api/semantic_cache.py - lookup(): the exact rung, then the five nearest at 0.95",
               block(SC, "    now = _now()", end="def store(")),
    "hit": ("services/rag-api/main.py - _semantic_hit(): a stored answer comes back as backend cache, cost 0",
            block(MAIN, "def _semantic_hit(req, qvec, fingerprint):", end="def _semantic_store(")),
    "store": ("services/rag-api/main.py - _semantic_store(): only an answer the caller is getting, answerable and cited",
              block(MAIN, "def _semantic_store(req, qvec, ans, fingerprint) -> None:", end="def check_filters(")),
}
assert EXCERPTS["pack"][1].rstrip().endswith('return "\\n\\n".join(parts), version'), EXCERPTS["pack"][1][-60:]
assert EXCERPTS["create"][1].rstrip().endswith("return rec") and 'self.global_client.caches.create(model=MODEL, config=cfg), "global"' in EXCERPTS["create"][1]
assert EXCERPTS["attach"][1].rstrip().endswith('return {"cached_content": rec["cache_name"]}')
assert "**_cache_kwargs(tenant_id, model)," in EXCERPTS["call"][1] and "contents=_contents(prompt, packed)," in EXCERPTS["call"][1]
assert "cached_tokens * usd_in * 0.10" in EXCERPTS["price"][1]
assert EXCERPTS["lookup"][1].rstrip().endswith("return None") and 'd["rung"] = "near"' in EXCERPTS["lookup"][1]
assert 'backend="cache"' in EXCERPTS["hit"][1] and "not (ans.answerable and ans.citations)" in EXCERPTS["store"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
cm_src, sc_src, main_src, gen_src = ((KIT / p).read_text(encoding="utf-8") for p in (CM, SC, MAIN, GEN))
assert "MIN_CACHE_TOKENS = 4_096" in cm_src and 'DEFAULT_TTL_S = int(os.environ.get("CACHE_TTL_S", "3600"))' in cm_src
assert 'THRESHOLD = float(os.environ.get("SEMANTIC_CACHE_THRESHOLD", "0.95"))' in sc_src and 'TTL_HOURS = int(os.environ.get("SEMANTIC_CACHE_TTL_H", "24"))' in sc_src
assert "CANDIDATES = 5" in sc_src
assert gen_src.count(r'prompt = f"{SYSTEM}{_dated_rule(packed)}\n\nContext:\n{context}\n\nQuestion: {query}"') == 2    # generate and generate_stream, cache or not
assert gen_src.count("**_cache_kwargs(tenant_id, model),") == 2
assert 'if settings.semantic_cache != "on":\n        return None' in main_src
assert "qvec = embed_query(req.query)                     # once: the answer cache and the retrieval share it" in main_src
assert "guard, reason = screen_response(ans.answer, guard)" in main_src and "if not (hit or reason):\n        _semantic_store(" in main_src
assert '"model_backend": backend or settings.model_backend,' in main_src
mk = (KIT / "Makefile").read_text(encoding="utf-8")
assert re.search(r"^SEMANTIC_CACHE\s+\?= off$", mk, re.M) and "SEMANTIC_CACHE=$(SEMANTIC_CACHE)|" in mk
assert "$(PY) cache_admin.py $${CACHE_OP:-create} --project $(PROJECT) --tenant $(TENANT)" in mk
tf = "\n".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "terraform").glob("*.tf")))
SCHEDULED = sorted(re.findall(r'resource "google_cloud_scheduler_job" "(\w+)"', tf))
assert SCHEDULED == ["cases_overdue", "ingest_batch", "off", "reconcile"], SCHEDULED                 # none refreshes a cache
assert "Cloud\nScheduler job (12.6) calls `refresh()`" in cm_src                                                      # what the docstring promises
assert 'collection = "answer_cache"\n  field      = "expire_at"' in tf and "dimension = 768" in tf
assert (KIT / "evals" / "demo" / "hr_policy_2026_v2.md").is_file()                   # 4.2's new version, which the pack never sees
readme = (KIT / "evals" / "README.md").read_text(encoding="utf-8")
assert "| acme | `hr_policy_2026` | policy | synthetic | — | 40,096 |" in readme


def load(rel: str, name: str, fakes: dict | None = None):
    """A kit module, executed with stand-ins for the cloud clients it imports."""
    if fakes and importlib.util.find_spec("google") is None:
        fakes = {"google": types.ModuleType("google"), **fakes}
    saved = {k: sys.modules.get(k) for k in (fakes or {})}
    sys.modules.update(fakes or {})
    try:
        spec = importlib.util.spec_from_file_location(name, KIT / rel)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        return mod
    finally:
        for k, v in saved.items():
            if v is None:
                sys.modules.pop(k, None)
            else:
                sys.modules[k] = v


ca = load(CA, "ca91")
PACK, CORPUS_V = ca.pack_for("acme")
PACK_DOCS = [line[4:] for line in PACK.splitlines() if line.startswith("### ")]
assert PACK_DOCS == ["annual_report_2026.md", "hr_policy_2026.md", "inv_2026_0412.md", "msa_acme_2026.md", "townhall_2026_q1.md"], PACK_DOCS
SYSTEM = re.search(r'^SYSTEM = """(.*?)"""', gen_src, re.S | re.M).group(1)
est = lambda text: max(1, len(text) // 4)  # noqa: E731 - context_budget.estimate_tokens, asserted below
assert "def estimate_tokens(text: str) -> int:\n    return max(1, len(text) // 4)" in (KIT / "services/rag-api/context_budget.py").read_text(encoding="utf-8")
PACK_TOKENS = est(PACK)
K = est(SYSTEM) + PACK_TOKENS                      # the cache holds SYSTEM as its system instruction, and the pack

# ------------------------------------------------------------------ box 1: is the context cache attached? (the kit's get, stale_against, generate_config_kwargs)
cls = next(n for n in ast.parse(cm_src).body if isinstance(n, ast.ClassDef) and n.name == "TenantCacheManager")
meth = {n.name: textwrap.dedent(ast.get_source_segment(cm_src, n)) for n in cls.body if isinstance(n, ast.FunctionDef)}
CTX_CASES, CTX_KIT = [], []
for rec_ok, time_ok, model_ok, corpus_ok in itertools.product([True, False], repeat=4):
    logs = []
    ns = {"dt": dt, "json": json, "log": types.SimpleNamespace(info=logs.append)}
    for m in ("get", "stale_against", "generate_config_kwargs"):
        exec(meth[m], ns)
    left = dt.timedelta(minutes=45 if time_ok else 1)
    rec = {"cache_name": "projects/NUMBER/locations/global/cachedContents/CACHE_ID", "model": "gemini-3.6-flash",
           "corpus_fingerprint": "fp-1", "expire_time": dt.datetime.now(dt.timezone.utc) + left}
    snap = types.SimpleNamespace(exists=rec_ok, to_dict=lambda r=rec: dict(r))
    mgr = types.SimpleNamespace(_doc=lambda t, s=snap: types.SimpleNamespace(get=lambda: s),
                                ledger_fingerprint=lambda t, c=corpus_ok: "fp-1" if c else "fp-2")
    for m in ("get", "stale_against", "generate_config_kwargs"):
        setattr(mgr, m, types.MethodType(ns[m], mgr))
    out = mgr.generate_config_kwargs("acme", "gemini-3.6-flash" if model_ok else "projects/NUMBER/locations/us/endpoints/TUNED")
    CTX_CASES.append([rec_ok, time_ok, model_ok, corpus_ok])
    CTX_KIT.append({"attached": out == {"cached_content": rec["cache_name"]}, "stale": any('"event": "cache_stale"' in x for x in logs)})
assert sum(k["attached"] for k in CTX_KIT) == 1 and sum(k["stale"] for k in CTX_KIT) == 1

# ------------------------------------------------------------------ box 2: does the answer cache answer? (the kit's lookup on a fake Firestore)
fs = types.ModuleType("google.cloud.firestore")
fs.Client, fs.SERVER_TIMESTAMP = object, object()
bvq = types.ModuleType("google.cloud.firestore_v1.base_vector_query")
bvq.DistanceMeasure = types.SimpleNamespace(COSINE="COSINE")
vmod = types.ModuleType("google.cloud.firestore_v1.vector")
vmod.Vector = list
gc = types.ModuleType("google.cloud")
gc.firestore = fs
sc = load(SC, "sc91", {"google.cloud": gc, "google.cloud.firestore": fs, "google.cloud.firestore_v1": types.ModuleType("google.cloud.firestore_v1"),
                       "google.cloud.firestore_v1.base_vector_query": bvq, "google.cloud.firestore_v1.vector": vmod})
assert sc.qhash(Q91) == sc.qhash(Q_LOWER) != sc.qhash(Q_PARA)


class FakeQuery:
    def __init__(self, rows):
        self.rows, self.eq = rows, []

    def where(self, field, op, value):
        assert op == "=="
        self.eq.append((field, value))
        return self

    def limit(self, n):
        return self

    def find_nearest(self, field, vec, distance_measure, limit, distance_result_field):
        return self

    def get(self):
        return [types.SimpleNamespace(to_dict=lambda r=r: dict(r)) for r in self.rows if all(r.get(f) == v for f, v in self.eq)]


WORDS = {"same": (Q91, 0.0), "case": (Q_LOWER, 0.004), "p97": (Q_PARA, 0.03), "p90": ("How much remote work am I allowed?", 0.10)}
ANS_CASES, ANS_KIT = [], []
for on, first_ok, words, corpus_ok, scope_ok, young in itertools.product([True, False], [True, False], list(WORDS), [True, False], [True, False], [True, False]):
    text, dist = WORDS[words]
    now = dt.datetime.now(dt.timezone.utc)
    stored = on and first_ok                          # _semantic_store: SEMANTIC_CACHE on, and an answerable, cited answer
    entry = {"tenant_id": "acme", "qhash": sc.qhash(Q91), "fingerprint": "fp-1", "scope": sc.scope_of(None, 6, "v3"),
             "expire_at": now + dt.timedelta(hours=23 if young else -1), "d": dist, "answer": {"answer": "..."}}
    db = types.SimpleNamespace(collection=lambda name, rows=([entry] if stored else []): FakeQuery(rows))
    got = None
    if on:                                            # _semantic_hit returns None before any lookup when the switch is off
        got = sc.lookup(db, "acme", [0.0], "fp-1" if corpus_ok else "fp-2",
                        scope=sc.scope_of(None, 6 if scope_ok else 8, "v3"), question=text)
    ANS_CASES.append([on, first_ok, words, corpus_ok, scope_ok, young])
    ANS_KIT.append(got["rung"] if got else "")
assert {"exact", "near", ""} == set(ANS_KIT)

# ------------------------------------------------------------------ box 3: what one question costs (the kit's price, bigquery refused so FALLBACK answers)
bq = types.ModuleType("google.cloud.bigquery")
bq.Client = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no BigQuery at build time"))
gc2 = types.ModuleType("google.cloud")
gc2.bigquery = bq
cost = load(COST, "cost91", {"google.cloud": gc2, "google.cloud.bigquery": bq})
FALLBACK = {m: cost.FALLBACK[m] for m in ("gemini-3.6-flash", "gemini-3.1-flash-lite", "gemini-3.1-pro-preview")}
assert FALLBACK["gemini-3.6-flash"] == (1.50, 7.50) and cost.USD_INR == 85
PRICE_CASES = [[m, tin, tout, cached] for m in FALLBACK for tin in (0, 1800, 1800 + K) for tout in (0, 400) for cached in (0, K)]
PRICE_KIT = [[cost.price(*c)["usd"], cost.price(*c)["inr"]] for c in PRICE_CASES]

# ------------------------------------------------------------------ the cells
ASK_PY = """import json, os, urllib.error, urllib.request
body = json.dumps({"query": os.environ["Q"], "tenant_id": "acme", "top_k": 6}).encode()
req = urllib.request.Request(os.environ["URL"] + "/v1/query", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
try:
    a = json.load(urllib.request.urlopen(req, timeout=120))
    print(f"  backend {a['backend']:6} cache_hit {a['cache_hit']:8} tokens_in {a['tokens_in']:>6}  cached_tokens {a['cached_tokens']:>6}  {a['latency_ms']:>5} ms  | {a['answer'][:44]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}  {e.read().decode(errors='replace')[:90]}")"""

ASKFN = ("ask91() {   # one /v1/query to $1 about acme, as documind-ui-sa; prints the answer's cache fields\n"
         "TOKEN=\"$(tok \"$API\")\" URL=\"$1\" Q=\"$2\" python - <<'PY'\n" + ASK_PY + "\nPY\n}\n"
         f'export SINCE91="$(date -u +%FT%TZ)" Q91="{Q91}"\n'
         'ask91 "$API" "$Q91"')

ROWS_PY = """import json, os, subprocess
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" '
     f'AND jsonPayload.tenant="acme" AND timestamp>="{os.environ["SINCE91"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                      "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j, rev = e["jsonPayload"], e["resource"]["labels"]["revision_name"]
    print(f"  {rev[-9:]}  {j['model_backend']:6}  in {j['tokens_in']:>6}  cached {j['cached_tokens']:>6}  Rs {j['cost_usd'] * 85:.4f}  {j['latency_ms']:>5} ms")"""

HOLD_PY = """import os, sys
from google.cloud import firestore
from google.cloud.firestore_v1.base_query import FieldFilter
sys.path.insert(0, "services/rag-api")
from semantic_cache import qhash
db = firestore.Client(project=os.environ["PROJECT"])
c = db.collection("tenant_caches").document("acme").get().to_dict() or {}
print("context cache  (Firestore holds a pointer; the pack itself is on Google's side)")
for k in ("cache_name", "location", "model", "tokens", "expire_time", "corpus_fingerprint"):
    print(f"    {k}: {c.get(k)}")
rows = [d.to_dict() for d in db.collection("answer_cache").where(filter=FieldFilter("tenant_id", "==", "acme")).stream()]
mine = [r for r in rows if r.get("qhash") == qhash(os.environ["Q91"])]
print(f"answer cache  ({len(rows)} acme entries; {len(mine)} for this question's words)")
for r in mine[:1]:
    print(f"    question: {r['question']}\\n    qhash: {r['qhash']}  scope: {r['scope']}  fingerprint: {r['fingerprint'][:12]}")
    print(f"    model: {r['model']}  expire_at: {r['expire_at']}  embedding: {len(r['embedding'])} numbers")
    print(f"    answer: {r['answer']['answer'][:60]}  citations: {len(r['answer']['citations'])}")"""


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


CELLS = {
    "askfn": ASKFN,
    "cache": 'make cache PROJECT="$PROJECT" TENANT=acme',
    "ask2": 'ask91 "$API" "$Q91"',
    "rows": heredoc(ROWS_PY),
    "candidate": ('make candidate PROJECT="$PROJECT" SEMANTIC_CACHE=on\n'
                  'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"'),
    "asks": ('ask91 "$CAND" "$Q91"                                   # 1: a miss - retrieved, generated, stored\n'
             'ask91 "$CAND" "$Q91"                                   # 2: the same words - the exact rung\n'
             f'ask91 "$CAND" "{Q_LOWER}"      # 3: other case, no "?" - the same qhash\n'
             f'ask91 "$CAND" "{Q_PARA}"   # 4: a paraphrase - the near rung, if it is 0.95 close'),
    "rows2": heredoc(ROWS_PY),
    "hold": heredoc(HOLD_PY),
    "clean": ('gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate\n'
              'rm -f .candidate-revision      # make promote would otherwise flip traffic to the recorded revision\n'
              'make cache PROJECT="$PROJECT" TENANT=acme CACHE_OP=delete'),
}

# the asks, against a local stub that answers the way the API does
P, O, P2, O2 = 1812, 412, 1794, 398
ENVELOPE = {"answer": "Employees may work remotely up to eight days per month with manager consent [1].",
            "citations": [{"n": 1, "chunk_id": "acme:SHA#14"}], "confidence": "high", "answerable": True,
            "model": "gemini-3.6-flash", "backend": "vertex", "cost_usd": None, "tokens_out": O, "stages": {}}
PLAN = {"/live0": [dict(tokens_in=P, cached_tokens=0, latency_ms=2410, cache_hit="none")],
        "/live1": [dict(tokens_in=P + K, cached_tokens=K, latency_ms=2650, cache_hit="none")],
        "/cand": [dict(tokens_in=P + K, cached_tokens=K, latency_ms=2590, cache_hit="none"),
                  dict(tokens_in=0, tokens_out=0, cached_tokens=0, latency_ms=182, cache_hit="semantic", backend="cache", cost_usd=0.0),
                  dict(tokens_in=0, tokens_out=0, cached_tokens=0, latency_ms=176, cache_hit="semantic", backend="cache", cost_usd=0.0),
                  dict(tokens_in=P2 + K, tokens_out=O2, cached_tokens=K, latency_ms=2720, cache_hit="none")]}
SEEN = {k: 0 for k in PLAN}


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        base = self.path.rsplit("/v1/query", 1)[0]
        step = PLAN[base][SEEN[base]]
        SEEN[base] += 1
        data = json.dumps({**ENVELOPE, **step}, separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


srv = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASE = f"http://127.0.0.1:{srv.server_address[1]}"
T = Path(tempfile.mkdtemp(prefix="lesson91-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ,
       "TOKEN": "TOKEN", "SINCE91": "YYYY-MM-DDTHH:MM:SSZ", "Q91": Q91}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


ask = lambda base, q: run_cell(ASK_PY, env={"URL": BASE + base, "Q": q})  # noqa: E731
OUT = {"askfn": ask("/live0", Q91), "ask2": ask("/live1", Q91),
       "asks": "".join(ask("/cand", q) for q in (Q91, Q91, Q_LOWER, Q_PARA))}
srv.shutdown()
assert OUT["askfn"].count("cached_tokens      0") == 1 and OUT["asks"].count("backend cache") == 2, OUT["asks"]

# make cache: cache_admin.main()'s own printing, over a fake manager and the generator's real SYSTEM
REC = {"tenant_id": "acme", "cache_name": "projects/NUMBER/locations/global/cachedContents/CACHE_ID", "location": "global",
       "model": "gemini-3.6-flash", "tokens": K, "expire_time": "YYYY-MM-DD HH:MM:SS.ssssss+00:00",
       "version": CORPUS_V, "corpus_fingerprint": "FINGERPRINT"}


class FakeMgr:
    def __init__(self, project):
        pass

    def ledger_fingerprint(self, tenant):
        return "FINGERPRINT"

    def create(self, tenant, system, pack, ttl_s, version, fingerprint):
        assert system == SYSTEM and pack == PACK and ttl_s == 3600
        return {**REC, "version": version}

    def get(self, tenant, min_remaining_s=0):
        return dict(REC)

    def delete(self, tenant):
        pass


def admin(*argv) -> str:
    import contextlib
    import io
    mods = {"cache_manager": types.SimpleNamespace(TenantCacheManager=FakeMgr), "generator": types.SimpleNamespace(SYSTEM=SYSTEM)}
    saved = {k: sys.modules.get(k) for k in mods}
    sys.modules.update(mods)
    old_argv, buf = sys.argv, io.StringIO()
    sys.argv = ["cache_admin.py", *argv, "--project", PROJ, "--tenant", "acme"]
    try:
        with contextlib.redirect_stdout(buf):
            assert ca.main() == 0
    finally:
        sys.argv = old_argv
        for k, v in saved.items():
            sys.modules.pop(k, None) if v is None else sys.modules.__setitem__(k, v)
    return buf.getvalue()


dflt = {k: re.search(rf"^{k}\s+\?= (\S+)", mk, re.M).group(1) for k in ("GENERATOR_MODEL", "RAG_MODEL_BASE", "ROUTING", "MODEL_BACKEND", "ARMOR", "PY")}
assert dflt["GENERATOR_MODEL"] == "gemini-3.6-flash"
MAKE_LINE = ("cd services/rag-api && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=gemini-3.6-flash \\\n"
             f"  {dflt['PY']} cache_admin.py ${{CACHE_OP:-create}} --project documind-ai-YOUR-ID --tenant acme\n")   # make echoes before the shell expands
OUT["cache"] = MAKE_LINE + admin("create")
assert f"tokens {K}" in OUT["cache"] and "location global" in OUT["cache"]

# the rows: every usage row since SINCE91, priced by the kit's own price()
REV_LIVE, REV_CAND = "documind-api-00041-kqz", "documind-api-00044-rtv"
row = lambda rev, backend, tin, tout, cached, ms: {"resource": {"labels": {"revision_name": rev}}, "jsonPayload": {  # noqa: E731
    "event": "query", "tenant": "acme", "model_backend": backend, "tokens_in": tin, "tokens_out": tout, "cached_tokens": cached,
    "cost_usd": 0.0 if backend == "cache" else round(cost.price("gemini-3.6-flash", tin, tout, cached)["usd"], 6), "latency_ms": ms}}
ROWS1 = [row(REV_LIVE, "vertex", P, O, 0, 2410), row(REV_LIVE, "vertex", P + K, O, K, 2650)]
ROWS2 = ROWS1 + [row(REV_CAND, "vertex", P + K, O, K, 2590), row(REV_CAND, "cache", 0, 0, 0, 182), row(REV_CAND, "cache", 0, 0, 0, 176),
                 row(REV_CAND, "vertex", P2 + K, O2, K, 2720)]


def fake_gcloud(entries) -> str:
    return ("import json, sys, types\n"
            "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
            f"ENTRIES = json.loads({json.dumps(json.dumps(entries))})\n"
            "def run(cmd, **kw):\n"
            "    assert cmd[1:3] == ['logging', 'read'] and '--order' in cmd, cmd\n"
            "    return R(json.dumps(ENTRIES))\n"
            "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")


OUT["rows"] = run_cell(ROWS_PY, fake_gcloud(ROWS1))
OUT["rows2"] = run_cell(ROWS_PY, fake_gcloud(ROWS2))
extra = cost.price("gemini-3.6-flash", P + K, O, K)["inr"] - cost.price("gemini-3.6-flash", P, O, 0)["inr"]
assert abs(extra - K * 1.50 * 0.10 / 1e6 * 85) < 1e-3, extra                  # the cache adds a tenth of the pack's price, and nothing else changes
assert OUT["rows2"].count("cache   in      0  cached      0  Rs 0.0000") == 2, OUT["rows2"]

# the holdings: the record and the entry, from a fake Firestore; qhash is the kit's own, imported the way the cell does
ENTRY = {"tenant_id": "acme", "question": Q91, "qhash": sc.qhash(Q91), "scope": sc.scope_of(None, 6, "v3"), "fingerprint": "FINGERPRINT_ABCDEF",
         "model": "gemini-3.6-flash", "expire_at": "YYYY-MM-DD HH:MM:SS+00:00", "embedding": [0.0] * 768,
         "answer": {"answer": ENVELOPE["answer"], "citations": ENVELOPE["citations"], "confidence": "high", "answerable": True}}
FAKE_FS = ("import json, sys, types\n"
           f"CACHE, ENTRIES = json.loads({json.dumps(json.dumps(REC))}), json.loads({json.dumps(json.dumps([ENTRY, {**ENTRY, 'question': Q_PARA, 'qhash': 'other'}]))})\n"
           "class Snap:\n    def __init__(self, d): self.d = d\n    def to_dict(self): return dict(self.d) if self.d is not None else None\n"
           "class Doc:\n    def __init__(self, d): self.d = d\n    def get(self): return Snap(self.d)\n"
           "class Coll:\n    def __init__(self, name): self.name = name\n"
           "    def document(self, i): return Doc(CACHE if (self.name, i) == ('tenant_caches', 'acme') else None)\n"
           "    def where(self, filter=None): assert filter == ('tenant_id', '==', 'acme'); return self\n"
           "    def stream(self): return [Snap(e) for e in ENTRIES]\n"
           "class Client:\n    def __init__(self, project=None): pass\n    def collection(self, n): return Coll(n)\n"
           "fs = types.ModuleType('google.cloud.firestore'); fs.Client = Client; fs.SERVER_TIMESTAMP = object()\n"
           "bq = types.ModuleType('google.cloud.firestore_v1.base_query'); bq.FieldFilter = lambda *a: a\n"
           "bvq = types.ModuleType('google.cloud.firestore_v1.base_vector_query'); bvq.DistanceMeasure = types.SimpleNamespace(COSINE='COSINE')\n"
           "vec = types.ModuleType('google.cloud.firestore_v1.vector'); vec.Vector = list\n"
           "gc = types.ModuleType('google.cloud'); gc.firestore = fs\n"
           "sys.modules.setdefault('google', types.ModuleType('google'))\n"
           "sys.modules.update({'google.cloud': gc, 'google.cloud.firestore': fs, 'google.cloud.firestore_v1': types.ModuleType('google.cloud.firestore_v1'),\n"
           "                    'google.cloud.firestore_v1.base_query': bq, 'google.cloud.firestore_v1.base_vector_query': bvq, 'google.cloud.firestore_v1.vector': vec})\n")
OUT["hold"] = run_cell(HOLD_PY, FAKE_FS, cwd=KIT)                           # the cell imports the kit's semantic_cache from services/rag-api
assert "1 for this question's words" in OUT["hold"] and "embedding: 768 numbers" in OUT["hold"], OUT["hold"]
shutil.rmtree(T, ignore_errors=True)

OUT["candidate"] = ("gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\\n"
                    f"  --update-env-vars \"^|^GENERATOR_MODEL={dflt['GENERATOR_MODEL']}|RAG_MODEL_BASE={dflt['RAG_MODEL_BASE']}|ROUTING={dflt['ROUTING']}"
                    f"|MODEL_BACKEND={dflt['MODEL_BACKEND']}|ARMOR={dflt['ARMOR']}|SEMANTIC_CACHE=on|...\"\n"
                    f"...\n>> candidate revision: {REV_CAND} (deploy/.candidate-revision - make promote moves traffic to it by name)\n"
                    f">> candidate: {CAND} (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)\nCAND={CAND}\n")
assert "record-candidate PROJECT=$(PROJECT)" in mk and 'echo ">> candidate: https://candidate---documind-api-$$NUMBER.$(REGION).run.app' in mk
OUT["clean"] = ("Updating traffic...done.\nDone.\nURL: https://documind-api-...run.app\nTraffic:\n"
                f"  100% {REV_LIVE}      (the live revision, as before; no candidate tag)\n"
                + MAKE_LINE + admin("delete"))
assert OUT["clean"].rstrip().endswith("deleted acme's cache")


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "askfn": "run in the operator shell, in the kit (a small ask function, a start time for the rows, and one question to the live API)",
    "cache": "run in the operator shell, in the kit (acme's context cache: its pack, on Gemini, for an hour)",
    "ask2": "run in the operator shell, in the kit (the same question again, to the live API)",
    "rows": "run in the operator shell, in the kit (every acme usage row since the first ask; reads only)",
    "candidate": "run in the operator shell, in the kit (a revision with SEMANTIC_CACHE=on and no traffic)",
    "asks": "run in the operator shell, in the kit (four asks to the candidate)",
    "rows2": "run in the operator shell, in the kit (the same rows cell, now with the candidate's)",
    "hold": "run in the operator shell, in the kit (what each cache is holding; reads only)",
    "clean": "run in the operator shell, in the kit (the candidate's tag and recorded name removed, the context cache deleted)",
}
OUT_LABELS = {
    "askfn": "(this cell against a local stub that answers the way the API does; your tokens and times differ)",
    "cache": "shape (make cache's own printing; Google counts your tokens, this block uses the kit's estimate)",
    "ask2": "(this cell against a local stub; cached_tokens is the cache's count)",
    "rows": "(this cell against a fake gcloud, priced by the kit's own price(); your numbers differ)",
    "candidate": "shape (gcloud's progress lines are left out)",
    "asks": "(this cell against a local stub; the fourth line is a hit or a miss, and 9.3 measures which)",
    "rows2": "(this cell against a fake gcloud, priced by the kit's own price(); your numbers differ)",
    "hold": "(this cell against a fake Firestore; your names, dates and fingerprints differ)",
    "clean": "shape (gcloud's own lines vary by version)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: two caches, one question
CTX_JS = r"""function ctx(rec, time, model, corpus){                          /* get(), stale_against(), generate_config_kwargs() */
    if (!rec || !time) return {attached: false, stale: false, why: rec ? 'under two minutes left: get() treats it as gone' : 'no record in tenant_caches'};
    if (!model) return {attached: false, stale: false, why: 'another model: a cache belongs to one model'};
    if (!corpus) return {attached: false, stale: true, why: 'the corpus moved: the log says cache_stale'};
    return {attached: true, stale: false, why: ''}; }"""
ANS_JS = r"""function ans(on, first, words, corpus, scope, young){              /* _semantic_hit(), _semantic_store(), lookup(), _alive() */
    if (!on) return {rung: '', why: 'SEMANTIC_CACHE is off: no lookup at all'};
    if (!first) return {rung: '', why: 'nothing was stored: only an answerable, cited answer is'};
    var alive = corpus && scope && young;
    var why = !corpus ? 'answered under another corpus fingerprint' : !scope ? 'answered for other filters, top_k or prompt' : 'expired: older than 24 hours';
    if (words === 'same' || words === 'case') return alive ? {rung: 'exact', why: ''} : {rung: '', why: why};
    if (words === 'p90') return {rung: '', why: 'the nearest earlier question is below 0.95'};
    return alive ? {rung: 'near', why: ''} : {rung: '', why: why}; }"""
PRICE_JS = r"""var FB = %s;
  function price(model, tin, tout, cached){                         /* cost.py price(), the FALLBACK table */
    var r = FB[model], billable = Math.max(tin - cached, 0);
    var usd = (billable * r[0] + cached * r[0] * 0.10 + tout * r[1]) / 1e6;
    return {usd: Math.round(usd * 1e6) / 1e6, inr: Math.round(usd * 85 * 1e4) / 1e4}; }""" % json.dumps(FALLBACK)
test_js = ("'use strict';\n" + CTX_JS + "\n" + ANS_JS + "\n" + PRICE_JS.replace("\n  ", "\n") + "\n"
           f"var C1 = {json.dumps(CTX_CASES)}, C2 = {json.dumps(ANS_CASES)}, C3 = {json.dumps(PRICE_CASES)};\n"
           "console.log(JSON.stringify([C1.map(function(c){ var r = ctx(c[0], c[1], c[2], c[3]); return {attached: r.attached, stale: r.stale}; }),"
           " C2.map(function(c){ return ans(c[0], c[1], c[2], c[3], c[4], c[5]).rung; }),"
           " C3.map(function(c){ var r = price(c[0], c[1], c[2], c[3]); return [r.usd, r.inr]; })]));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson91-js-")) / "caches.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-600:]
J1, J2, J3 = json.loads(node.stdout)
for c, k, j in zip(CTX_CASES, CTX_KIT, J1):
    assert k == j, (c, k, j)
for c, k, j in zip(ANS_CASES, ANS_KIT, J2):
    assert k == j, (c, k, j)
for c, k, j in zip(PRICE_CASES, PRICE_KIT, J3):
    assert abs(k[0] - j[0]) < 1.01e-6 and abs(k[1] - j[1]) < 1.01e-4, (c, k, j)

UI_JS = r"""var root = document.getElementById('caches'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var on = function(id){ return $(id).value === 'y'; };
  function li(cls, t){ return '<li class="' + cls + '">' + t + '</li>'; }
  function rs(x){ return 'Rs ' + x.toFixed(x < 1 ? 4 : 2); }
  function renderC(){
    var r = ctx(on('cx-rec'), on('cx-time'), on('cx-model'), on('cx-corpus'));
    var s = li(r.attached ? 'ok' : 'no', r.attached ? 'cached_content is set on the call: the pack is read from the cache, and the model still runs' : 'not attached: ' + r.why);
    s += li(r.attached ? 'ok' : 'skip', r.attached ? 'the row: tokens_in grows by the cache\'s count, cached_tokens equals it, billed at a tenth' : 'the row: cached_tokens 0, the answer priced as plain RAG');
    $('cx-out').innerHTML = '<ol class="pc-steps">' + s + '</ol><span class="pc-out ' + (r.attached ? 'ok' : 'no') + '">' + (r.attached ? 'attached' : 'uncached') + '</span>';
  }
  function renderA(){
    var r = ans(on('an-on'), on('an-first'), $('an-words').value, on('an-corpus'), on('an-scope'), on('an-young')), s = '';
    if (r.rung) {
      s += li('ok', (r.rung === 'exact' ? 'the exact rung: the same words by qhash, two equality filters' : 'the near rung: one of the five nearest earlier questions, at 0.95 or closer') + ', the same corpus and scope, not expired');
      s += li('ok', 'the stored answer comes back with its original citations: no retrieval, no reranker, no model');
      s += li('ok', 'the row: model_backend cache, tokens 0, cost 0');
    } else {
      s += li('no', 'a miss: ' + r.why);
      s += li('skip', 'retrieval, the reranker and the model run, priced as usual' + (on('an-on') ? '; the answer is stored if it is answerable and cited' : ''));
    }
    $('an-out').innerHTML = '<ol class="pc-steps">' + s + '</ol><span class="pc-out ' + (r.rung ? 'ok' : 'no') + '">' + (r.rung ? 'hit: ' + r.rung : 'miss') + '</span>';
  }
  function num(id, lo){ var v = parseFloat($(id).value); return isFinite(v) && v >= lo ? v : lo; }
  function renderP(){
    var m = $('pr-model').value, p = num('pr-p', 0), o = num('pr-o', 0), k = num('pr-k', 0), n = num('pr-n', 0), h = Math.min(num('pr-h', 0), 100) / 100;
    var plain = price(m, p, o, 0).inr, withc = price(m, p + k, o, k).inr, raw = price(m, p + k, o, 0).inr, rate = parseFloat($('pr-s').value);
    var store = isFinite(rate) && rate > 0 ? k * rate / 1e6 * 85 : null, s = '';
    s += li('ok', 'plain RAG: ' + rs(plain) + ' a question');
    s += li('no', 'with the context cache attached, as the kit does: ' + rs(withc) + ', ' + (plain > 0 ? (withc / plain).toFixed(2) + ' times plain RAG' : 'against plain RAG at Rs 0'));
    s += li('ok', 'the same question with the pack sent uncached: ' + rs(raw) + '; the cache saves ' + rs(raw - withc) + ' of that');
    s += li('ok', 'an answer-cache hit: Rs 0 on the row');
    s += li(store === null ? 'skip' : 'ok', 'the cache\'s storage: ' + (store === null ? 'enter the rate from your model\'s price page' : rs(store) + ' an hour'));
    s += li('ok', 'an hour of ' + n + ' questions: plain ' + rs(n * plain) + ' | context cache ' + rs(n * withc + (store || 0)) + (store === null ? ' + storage' : '') + ' | answer cache alone, ' + Math.round(h * 100) + '% hits ' + rs(n * (1 - h) * plain));
    $('pr-out').innerHTML = '<ol class="pc-steps">' + s + '</ol>';
  }
  ['cx-rec', 'cx-time', 'cx-model', 'cx-corpus'].forEach(function(id){ $(id).addEventListener('change', renderC); });
  ['an-on', 'an-first', 'an-words', 'an-corpus', 'an-scope', 'an-young'].forEach(function(id){ $(id).addEventListener('change', renderA); });
  ['pr-model', 'pr-p', 'pr-o', 'pr-k', 'pr-n', 'pr-h', 'pr-s'].forEach(function(id){ $(id).addEventListener('input', renderP); $(id).addEventListener('change', renderP); });
  renderC(); renderA(); renderP();"""

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\n" + squeeze(CTX_JS) + "\n" + squeeze(ANS_JS) + "\n" + squeeze(PRICE_JS) + "\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert JS.count("<div") == JS.count("</div>") and "<tr" not in JS

per_q = lambda tin, tout, cached: cost.price("gemini-3.6-flash", tin, tout, cached)["inr"]  # noqa: E731
STATS = {"PACK_TOKENS": f"{PACK_TOKENS:,}", "K": str(K), "K_FMT": f"{K:,}", "PACK_CHARS": f"{len(PACK):,}", "N_DOCS": str(len(PACK_DOCS)),
         "N_CTX": str(len(CTX_CASES)), "N_ANS": str(len(ANS_CASES)), "N_PRICE": str(len(PRICE_CASES)),
         "EXTRA_RS": f"{K * 1.50 * 0.10 / 1e6 * 85:.2f}", "RAW_RS": f"{K * 1.50 / 1e6 * 85:.2f}",
         "PLAIN_RS": f"{per_q(P, O, 0):.2f}", "CTX_RS": f"{per_q(P + K, O, K):.2f}", "P": str(P), "O": str(O), "Q91": Q91,
         "N_SCHED": {3: "three", 4: "four", 5: "five"}[len(SCHEDULED)]}

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
print(f"kit: pack {len(PACK):,} chars ~{PACK_TOKENS:,} tokens ({len(PACK_DOCS)} documents) | context box {len(CTX_CASES)} cases, answer box {len(ANS_CASES)},"
      f" price grid {len(PRICE_CASES)} - each equal to the kit's own functions in node | asks, make cache, rows and holdings run against stand-ins")
