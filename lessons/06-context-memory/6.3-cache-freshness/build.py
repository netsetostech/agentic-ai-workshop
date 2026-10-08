"""Build lesson 6.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

What must match for each cache to be used, and what moves it. The answer cache matches on the tenant, the corpus
fingerprint, the scope (filters, top_k, prompt version) and 24 hours; the context cache on the model, two minutes of
life left and the fingerprint it was packed from. The lane walk: both caches and a candidate with SEMANTIC_CACHE=on,
the E3 question twice, the scope changed twice, revision 2 of the handbook reindexed (both caches go stale), make
cache again (attached again), version 1 back (the fingerprint returns, and so does the old answer). The widget is a
timeline of events; the build replays random event sequences through the kit's own store(), lookup(), get(),
stale_against() and generate_config_kwargs(), and node's port must agree at every ask. The lane cells run against
stand-ins: the asks against a local stub of the API, make cache's printing is cache_admin.main()'s own over a fake
manager, the state and scope cells against a fake Firestore, the log cells against a fake gcloud.
"""
import ast
import contextlib
import datetime as dt
import hashlib
import html
import importlib.util
import io
import itertools
import json
import os
import random
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

LESSON = "6.3"
title = "<title>Lesson 6.3 Test cache scope, configuration changes and freshness - what must match for a hit, what a reindex does to both caches, and what comes back with the old corpus | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
CAND = "https://candidate---documind-api-NUMBER.asia-south1.run.app"
Q92 = "What is the notice period for a confirmed E3?"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.fr-btns{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0;}
.fr-btns button{font:inherit;font-size:13px;min-height:44px;padding:6px 10px;border-radius:8px;border:1px solid var(--border);background:var(--card);cursor:pointer;color:var(--navy);}
.fr-state{font-family:var(--mono);font-size:12px;color:var(--navy);background:#f1f5f9;border-radius:8px;padding:6px 8px;margin:4px 0;}
.pc-steps{margin:6px 0 0;padding-left:20px;}
.pc-steps li{margin:3px 0;}
.pc-steps li.no{color:#991b1b;}.pc-steps li.ok{color:#065f46;}.pc-steps li.skip{color:#94a3b8;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
IDEM, SC, CM, MAIN, GEN = "services/ingest/idempotency.py", "services/rag-api/semantic_cache.py", "services/rag-api/cache_manager.py", "services/rag-api/main.py", "services/rag-api/generator.py"
V1, V2 = "evals/corpus/acme/hr_policy_2026.md", "evals/demo/hr_policy_2026_v2.md"
EXCERPTS = {
    "fp": ("services/ingest/idempotency.py - the fingerprint: a hash of the tenant's current doc_keys, re-computed on every change",
           block(IDEM, "def corpus_fingerprint(db: firestore.Client, tenant_id: str) -> tuple[str, int]:") + "\n\n\n"
           + block(IDEM, "def refresh_fingerprint(db: firestore.Client, tenant_id: str, event: str) -> str:")),
    "scope": ("services/rag-api/semantic_cache.py - scope_of() and _alive(): what else must match, and the clock",
              block(SC, "def scope_of(filters: dict | None, top_k: int, prompt_version: str) -> str:", end="def lookup(")),
    "stale": ("services/rag-api/cache_manager.py - stale_against(): the record's fingerprint against the ledger's",
              block(CM, "    def stale_against(self, rec: dict, tenant_id: str) -> str | None:", end="    def refresh(")),
    "fpread": ("services/rag-api/main.py - _fingerprint(): the answer cache reads the ledger on every request",
               block(MAIN, "def _fingerprint(tenant_id: str) -> str:", end="def _semantic_hit(")),
    "v2": ("evals/demo/hr_policy_2026_v2.md - revision 2: a dated line, and one clause changed",
           block(V2, "# ACME Employee Handbook 2026 (revision 2)", n=3) + "\n...\n" + block(V2, "A confirmed employee at grade E3 or above serves a notice period of 90 days", n=1)),
    "dated": ("services/rag-api/generator.py - the dated rule: added when a packed chunk carries a date",
              block(GEN, "DATED_RULE = (", n=2) + "\n\n\n" + block(GEN, "def _dated_rule(packed: list[dict]) -> str:", n=2)),
}
assert EXCERPTS["fp"][1].rstrip().endswith("return fp") and "on every reindex, retirement and reactivation, and on nothing else" in EXCERPTS["fp"][1]
assert '"filters": filters or {}, "top_k": top_k, "prompt": prompt_version' in EXCERPTS["scope"][1] and "return exp is None or exp > now" in EXCERPTS["scope"][1].splitlines()[-1]
assert EXCERPTS["stale"][1].rstrip().endswith("return now if now and now != have else None")
assert EXCERPTS["fpread"][1].rstrip().endswith('return ((snap.to_dict() or {}).get("fingerprint") or "") if snap.exists else ""')
assert "Effective from: 2026-10-01" in EXCERPTS["v2"][1] and "notice period of 90 days" in EXCERPTS["v2"][1]
assert "follow the one with the latest" in EXCERPTS["dated"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
idem_src, sc_src, cm_src, main_src = ((KIT / p).read_text(encoding="utf-8") for p in (IDEM, SC, CM, MAIN))
v1, v2 = (KIT / V1).read_text(encoding="utf-8"), (KIT / V2).read_text(encoding="utf-8")
assert "serves a notice period of 60 days" in v1 and "Effective from" not in v1
assert [l for l in v2.splitlines() if l not in v1.splitlines()] == ["# ACME Employee Handbook 2026 (revision 2)",
       "Effective from: 2026-10-01. Revision 2 changes NP-03: the notice period for a confirmed E3 becomes 90 days.",
       "A confirmed employee at grade E3 or above serves a notice period of 90 days. Notice runs"]      # the only change: one clause and a date
V1_KEY, V2_KEY = (hashlib.sha256((KIT / p).read_bytes()).hexdigest() for p in (V1, V2))
worker = (KIT / "services/ingest/main.py").read_text(encoding="utf-8")
for ev in ("ingest_ok", "ingest_reactivated", "ingest_already_current"):
    assert f'refresh_fingerprint(_db, doc.tenant_id, "{ev}")' in worker
assert 'RETENTION_DAYS = int(os.environ.get("RETENTION_DAYS", "30"))' in worker
reindex_sh = (KIT / "commands/reindex.sh").read_text(encoding="utf-8")
assert '(jsonPayload.event=\\"ingest_ok\\" OR jsonPayload.event=\\"ingest_reactivated\\")' in reindex_sh
assert 'FILTER_KEYS = ("doc_type", "kind")' in (KIT / "services/rag-api/schemas.py").read_text(encoding="utf-8")
assert "def get(self, tenant_id: str, min_remaining_s: int = 120) -> dict | None:" in cm_src
assert 'log.info(json.dumps({"event": "cache_stale", "tenant": tenant_id, "cache_fingerprint": rec.get("corpus_fingerprint"),' in cm_src
assert "fingerprint = _fingerprint(req.tenant_id) if settings.semantic_cache == \"on\" else \"\"" in main_src
mk = (KIT / "Makefile").read_text(encoding="utf-8")
assert "reindex: guard-project" in (KIT / "mk/lifecycle.mk").read_text(encoding="utf-8")
assert not any("cache_stale" in p.read_text(encoding="utf-8") for p in (KIT / "terraform").glob("*.tf"))      # no metric, no alert
assert worker.index("gone = swap_versions(") < worker.index('fingerprint = refresh_fingerprint(_db, doc.tenant_id, "ingest_ok")')  # after the swap
assert "Every revision" not in sc_src and "model" not in re.search(r"def scope_of\(.*?\n\n\n", sc_src, re.S).group(0).split('"""')[-1]  # the scope has no model


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
            sys.modules.pop(k, None) if v is None else sys.modules.__setitem__(k, v)


fs = types.ModuleType("google.cloud.firestore")
fs.Client, fs.SERVER_TIMESTAMP = object, object()
bvq = types.ModuleType("google.cloud.firestore_v1.base_vector_query")
bvq.DistanceMeasure = types.SimpleNamespace(COSINE="COSINE")
vmod = types.ModuleType("google.cloud.firestore_v1.vector")
vmod.Vector = list
gc = types.ModuleType("google.cloud")
gc.firestore = fs
sc = load(SC, "sc92", {"google.cloud": gc, "google.cloud.firestore": fs, "google.cloud.firestore_v1": types.ModuleType("google.cloud.firestore_v1"),
                       "google.cloud.firestore_v1.base_vector_query": bvq, "google.cloud.firestore_v1.vector": vmod})
ca = load("services/rag-api/cache_admin.py", "ca92")
bq = types.ModuleType("google.cloud.bigquery")
bq.Client = lambda *a, **k: (_ for _ in ()).throw(RuntimeError("no BigQuery at build time"))
gc2 = types.ModuleType("google.cloud")
gc2.bigquery = bq
cost = load("services/rag-api/cost.py", "cost92", {"google.cloud": gc2, "google.cloud.bigquery": bq})
PACK, CORPUS_V = ca.pack_for("acme")
SYSTEM = re.search(r'^SYSTEM = """(.*?)"""', (KIT / GEN).read_text(encoding="utf-8"), re.S | re.M).group(1)
K = max(1, len(SYSTEM) // 4) + max(1, len(PACK) // 4)          # the kit's four-characters-a-token estimate, as in 9.1
SCOPES = {f"{k}|{f}|{p}": sc.scope_of({"kind": "text"} if f == "text" else None, k, p) for k in (6, 8) for f in ("none", "text") for p in ("v3", "v4")}
assert len(set(SCOPES.values())) == 8

# ------------------------------------------------------------------ the widget's rules, replayed through the kit on random event sequences
cls = next(n for n in ast.parse(cm_src).body if isinstance(n, ast.ClassDef) and n.name == "TenantCacheManager")
meth = {n.name: textwrap.dedent(ast.get_source_segment(cm_src, n)) for n in cls.body if isinstance(n, ast.FunctionDef)}
FP = {"v1": "F1", "v2": "F2"}
MODELS = {"flash": "gemini-3.6-flash", "lite": "gemini-3.1-flash-lite"}
BASE = dt.datetime(2026, 9, 23, 9, 0, tzinfo=dt.timezone.utc)


class FakeQuery:
    def __init__(self, rows):
        self.rows, self.eq = rows, []

    def where(self, field, op, value):
        self.eq.append((field, value))
        return self

    def limit(self, n):
        return self

    def find_nearest(self, field, vec, distance_measure, limit, distance_result_field):
        return self

    def get(self):
        return [types.SimpleNamespace(to_dict=lambda r=r: {**r, "d": 0.0}) for r in self.rows if all(r.get(f) == v for f, v in self.eq)]


def kit_replay(events: list) -> list:
    """The kit's own functions over one event sequence: store() and lookup() on a fake Firestore whose clock is the
    sequence's, and get() / stale_against() / generate_config_kwargs() on a record whose expiry is set against real now."""
    rows, out = [], []
    st = {"t": 0, "corpus": "v1", "k": 6, "f": "none", "p": "v3", "m": "flash", "sem": True, "cache": {"fp": "F1", "model": "flash", "exp": 60}}
    db = types.SimpleNamespace(collection=lambda name: types.SimpleNamespace(add=lambda d: rows.append(d), **{
        "where": lambda f, op, v: FakeQuery(rows).where(f, op, v)}))
    for ev in events:
        e = ev["e"]
        if e == "ask":
            sc._now = lambda t=st["t"]: BASE + dt.timedelta(minutes=t)
            fp, scope = FP[st["corpus"]], sc.scope_of({"kind": "text"} if st["f"] == "text" else None, st["k"], st["p"])
            hit = sc.lookup(db, "acme", [0.0], fp, scope=scope, question=Q92) if st["sem"] else None
            stored = False
            if st["sem"] and not hit:
                sc.store(db, "acme", Q92, [0.0], {"answer": "..."}, fp, model=MODELS[st["m"]], scope=scope)
                stored = True
            ctx = "skipped"
            if not hit:
                logs = []
                ns = {"dt": dt, "json": json, "log": types.SimpleNamespace(info=logs.append)}
                for m in ("get", "stale_against", "generate_config_kwargs"):
                    exec(meth[m], ns)
                c = st["cache"]
                rec = None if c is None else {"cache_name": "CACHE", "model": MODELS[c["model"]], "corpus_fingerprint": c["fp"],
                                              "expire_time": dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=c["exp"] - st["t"])}
                snap = types.SimpleNamespace(exists=rec is not None, to_dict=lambda r=rec: dict(r))
                mgr = types.SimpleNamespace(_doc=lambda t, s=snap: types.SimpleNamespace(get=lambda: s),
                                            ledger_fingerprint=lambda t, f=fp: f)
                for m in ("get", "stale_against", "generate_config_kwargs"):
                    setattr(mgr, m, types.MethodType(ns[m], mgr))
                kw = mgr.generate_config_kwargs("acme", MODELS[st["m"]])
                live = mgr.get("acme")
                ctx = ("attached" if kw else "stale" if any('"cache_stale"' in x for x in logs)
                       else "model" if live and live["model"] != MODELS[st["m"]] else "none")
            out.append([("hit" if hit else "off" if not st["sem"] else "miss"), stored, ctx])
        elif e == "reindex":
            st["corpus"] = "v2"
        elif e == "restore":
            st["corpus"] = "v1"
        elif e == "cache":
            st["cache"] = {"fp": FP[st["corpus"]], "model": "flash", "exp": st["t"] + 60}
        elif e == "delete":
            st["cache"] = None
        elif e == "wait":
            st["t"] += ev["m"]
        elif e == "set":
            st[ev["key"]] = ev["value"]
    return out


rnd = random.Random(92)
CHOICES = ([{"e": "ask"}] * 5 + [{"e": "reindex"}, {"e": "restore"}, {"e": "cache"}, {"e": "delete"}, {"e": "wait", "m": 30}, {"e": "wait", "m": 59},
           {"e": "wait", "m": 1500}] + [{"e": "set", "key": "k", "value": v} for v in (6, 8)] + [{"e": "set", "key": "f", "value": v} for v in ("none", "text")]
           + [{"e": "set", "key": "p", "value": v} for v in ("v3", "v4")] + [{"e": "set", "key": "m", "value": v} for v in ("flash", "lite")]
           + [{"e": "set", "key": "sem", "value": v} for v in (True, False)])
SEQS = []
while len(SEQS) < 300:
    seq = [rnd.choice(CHOICES) for _ in range(14)]
    res = kit_replay(seq)
    if sum(r[1] for r in res) <= 5:                  # the kit reads five stored answers per rung; more and the order decides
        SEQS.append((seq, res))
assert any(r[0] == "hit" for _, rs in SEQS for r in rs) and any(r[2] == "stale" for _, rs in SEQS for r in rs) and any(r[2] == "model" for _, rs in SEQS for r in rs)

# ------------------------------------------------------------------ the cells
ASK_PY = """import json, os, urllib.error, urllib.request
body = json.dumps({"query": os.environ["Q"], "tenant_id": "acme", "top_k": int(os.environ["K"]), "filters": json.loads(os.environ["F"])}).encode()
req = urllib.request.Request(os.environ["URL"] + "/v1/query", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
try:
    a = json.load(urllib.request.urlopen(req, timeout=120))
    print(f"  {a['backend']:6} {a['cache_hit']:8} in {a['tokens_in']:>6} cached {a['cached_tokens']:>6} {a['latency_ms']:>5} ms | {a['answer'][:50]}")
except urllib.error.HTTPError as e:
    print(f"  HTTP {e.code}  {e.read().decode(errors='replace')[:90]}")"""

STATE_PY = """import os
from google.cloud import firestore
db = firestore.Client(project=os.environ["PROJECT"])
l, c = (db.document(p).get().to_dict() or {} for p in ("ledger/acme", "tenant_caches/acme"))
state = "none" if not c else "current" if c.get("corpus_fingerprint") == l.get("fingerprint") else "STALE"
print(f"  ledger {l.get('fingerprint')} ({l.get('versions')} versions, last {l.get('last_event')}) | context cache packed from {c.get('corpus_fingerprint')}: {state}")"""

FNS = ("ask92() {   # one /v1/query about acme to $1, as documind-ui-sa; $2 = top_k (6), $3 = filters as JSON (none)\n"
       "TOKEN=\"$(tok \"$API\")\" URL=\"$1\" K=\"${2:-6}\" F=\"${3:-null}\" Q=\"$Q92\" python - <<'PY'\n" + ASK_PY + "\nPY\n}\n"
       "state92() {   # the ledger's fingerprint beside the one the context cache was packed from\n"
       "python - <<'PY'\n" + STATE_PY + "\nPY\n}\n"
       f'export SINCE92="$(date -u +%FT%TZ)" Q92="{Q92}"\n'
       "state92\n"
       'ask92 "$API"            # the live revision: the context cache, no answer cache\n'
       'ask92 "$CAND"           # the candidate: a miss, stored\n'
       'ask92 "$CAND"           # the same words: the exact rung')

SCOPE_PY = """import sys
sys.path.insert(0, "services/rag-api")
from semantic_cache import scope_of
for label, f, k, p in [("as asked", None, 6, "v3"), ("top_k 8", None, 8, "v3"), ("kind: text", {"kind": "text"}, 6, "v3"), ("prompt v4", None, 6, "v4")]:
    print(f"  scope {label:10} {scope_of(f, k, p)}")"""

STALE_PY = """import json, os, subprocess
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="cache_stale" '
     f'AND timestamp>="{os.environ["SINCE92"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "5",
                      "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j = e["jsonPayload"]
    print(f"  cache_stale {j['tenant']}: packed from {j['cache_fingerprint']}, ledger now {j['ledger_fingerprint']}")"""

ROWS_PY = """import json, os, subprocess
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" '
     f'AND jsonPayload.tenant="acme" AND timestamp>="{os.environ["SINCE92"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                      "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j, rev = e["jsonPayload"], e["resource"]["labels"]["revision_name"]
    print(f"  {rev[-9:]}  {j['model_backend']:6}  in {j['tokens_in']:>6}  cached {j['cached_tokens']:>6}  Rs {j['cost_usd'] * 85:.4f}  {j['latency_ms']:>5} ms")"""


def heredoc(body: str) -> str:
    return f"python - <<'PY'\n{body}\nPY"


CELLS = {
    "both": ('make cache PROJECT="$PROJECT" TENANT=acme\n'
             'make candidate PROJECT="$PROJECT" SEMANTIC_CACHE=on\n'
             'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"'),
    "fns": FNS,
    "scope": ('ask92 "$CAND" 8                     # top_k 8: another scope\n'
              "ask92 \"$CAND\" 6 '{\"kind\": \"text\"}'   # a filter: another scope\n" + heredoc(SCOPE_PY)),
    "reindex": 'make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/demo/hr_policy_2026_v2.md NAME=hr_policy_2026.md',
    "after": ('state92\nask92 "$API"            # the live revision\nask92 "$CAND"           # the candidate\n' + heredoc(STALE_PY)),
    "recache": 'make cache PROJECT="$PROJECT" TENANT=acme\nstate92\nask92 "$API"',
    "restore": 'make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/corpus/acme/hr_policy_2026.md',
    "back": 'state92\nask92 "$CAND"',
    "rows": heredoc(ROWS_PY),
    "clean": ('gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate\n'
              'rm -f .candidate-revision      # make promote would otherwise flip traffic to the recorded revision\n'
              'make cache PROJECT="$PROJECT" TENANT=acme CACHE_OP=delete'),
}

# the asks, against a local stub that answers the way the API does
A60 = "A confirmed employee at grade E3 or above serves a notice period of 60 days [1]."
A90 = "From 1 October 2026 the notice period for a confirmed E3 is 90 days, under revision 2 [1]."
P, O = 1850, 405
ENV0 = {"citations": [{"n": 1, "chunk_id": "acme:SHA#7"}], "confidence": "high", "answerable": True, "model": "gemini-3.6-flash",
        "backend": "vertex", "cost_usd": None, "tokens_out": O, "stages": {}, "cache_hit": "none"}
HIT = dict(backend="cache", cache_hit="semantic", tokens_in=0, tokens_out=0, cached_tokens=0, cost_usd=0.0)
PLAN = {"/live-a": [dict(tokens_in=P + K, cached_tokens=K, latency_ms=2480, answer=A60)],
        "/cand-a": [dict(tokens_in=P + K, cached_tokens=K, latency_ms=2530, answer=A60), dict(HIT, latency_ms=170, answer=A60)],
        "/cand-s": [dict(tokens_in=P + 240 + K, cached_tokens=K, latency_ms=2610, answer=A60), dict(tokens_in=P + K, cached_tokens=K, latency_ms=2440, answer=A60)],
        "/live-b": [dict(tokens_in=P + 30, cached_tokens=0, latency_ms=2390, answer=A90)],
        "/cand-b": [dict(tokens_in=P + 30, cached_tokens=0, latency_ms=2455, answer=A90)],
        "/live-c": [dict(tokens_in=P + 30 + K, cached_tokens=K, latency_ms=2575, answer=A90)],
        "/cand-d": [dict(HIT, latency_ms=165, answer=A60)]}
SEEN = {k: 0 for k in PLAN}


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        assert req["query"] == Q92 and req["tenant_id"] == "acme"
        base = self.path.rsplit("/v1/query", 1)[0]
        step = PLAN[base][SEEN[base]]
        SEEN[base] += 1
        data = json.dumps({**ENV0, **step}, separators=(",", ":")).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


srv = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=srv.serve_forever, daemon=True).start()
BASEURL = f"http://127.0.0.1:{srv.server_address[1]}"
T = Path(tempfile.mkdtemp(prefix="lesson92-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ,
       "TOKEN": "TOKEN", "SINCE92": "YYYY-MM-DDTHH:MM:SSZ", "Q": Q92}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


ask = lambda base, k=6, f="null": run_cell(ASK_PY, env={"URL": BASEURL + base, "K": str(k), "F": f})  # noqa: E731

F1, F2 = (hashlib.sha256(x).hexdigest()[:16] for x in (b"acme corpus, handbook version 1", b"acme corpus, handbook revision 2"))


def fake_fs(ledger_fp: str, last: str, cache_fp: str | None) -> str:
    docs = {"ledger/acme": {"fingerprint": ledger_fp, "versions": 17, "last_event": last},
            "tenant_caches/acme": None if cache_fp is None else {"corpus_fingerprint": cache_fp}}
    return ("import json, sys, types\n"
            f"DOCS = json.loads({json.dumps(json.dumps(docs))})\n"
            "class Snap:\n    def __init__(self, d): self.d = d\n    def to_dict(self): return None if self.d is None else dict(self.d)\n"
            "class Ref:\n    def __init__(self, p): self.p = p\n    def get(self): return Snap(DOCS.get(self.p))\n"
            "class Client:\n    def __init__(self, project=None): pass\n    def document(self, p): return Ref(p)\n"
            "fs = types.ModuleType('google.cloud.firestore'); fs.Client = Client\n"
            "gc = types.ModuleType('google.cloud'); gc.firestore = fs\n"
            "sys.modules.setdefault('google', types.ModuleType('google'))\n"
            "sys.modules.update({'google.cloud': gc, 'google.cloud.firestore': fs})\n")


state = lambda *a: run_cell(STATE_PY, fake_fs(*a))  # noqa: E731
OUT = {"fns": state(F1, "ingest_ok", F1) + ask("/live-a") + ask("/cand-a") + ask("/cand-a"),
       "scope": ask("/cand-s", 8) + ask("/cand-s", 6, '{"kind": "text"}'),
       "after": state(F2, "ingest_reactivated", F1) + ask("/live-b") + ask("/cand-b"),
       "back": state(F1, "ingest_reactivated", F2) + ask("/cand-d")}
recache_asks = ask("/live-c")
srv.shutdown()
assert "current" in OUT["fns"] and "STALE" in OUT["after"] and "STALE" in OUT["back"] and OUT["back"].count("cache  ") == 1, OUT

# the scope cell: the kit's own scope_of, imported the way the cell does (from services/rag-api, the Firestore modules stood in)
FAKE_SC = ("import sys, types\n"
           "fs = types.ModuleType('google.cloud.firestore'); fs.Client = object; fs.SERVER_TIMESTAMP = object()\n"
           "bvq = types.ModuleType('google.cloud.firestore_v1.base_vector_query'); bvq.DistanceMeasure = types.SimpleNamespace(COSINE='COSINE')\n"
           "vec = types.ModuleType('google.cloud.firestore_v1.vector'); vec.Vector = list\n"
           "gc = types.ModuleType('google.cloud'); gc.firestore = fs\n"
           "sys.modules.setdefault('google', types.ModuleType('google'))\n"
           "sys.modules.update({'google.cloud': gc, 'google.cloud.firestore': fs, 'google.cloud.firestore_v1': types.ModuleType('google.cloud.firestore_v1'),\n"
           "                    'google.cloud.firestore_v1.base_vector_query': bvq, 'google.cloud.firestore_v1.vector': vec})\n")
OUT["scope"] += run_cell(SCOPE_PY, FAKE_SC, cwd=KIT)
assert OUT["scope"].count("scope ") == 4 and SCOPES["6|none|v3"] in OUT["scope"]


def fake_gcloud(entries) -> str:
    return ("import json, sys, types\n"
            "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
            f"ENTRIES = json.loads({json.dumps(json.dumps(entries))})\n"
            "def run(cmd, **kw):\n"
            "    assert cmd[1:3] == ['logging', 'read'] and '--order' in cmd, cmd\n"
            "    return R(json.dumps(ENTRIES))\n"
            "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")


STALE_ACTION = "answering uncached; make cache TENANT= rebuilds the pack"
assert f'"action": "{STALE_ACTION}"' in cm_src
stale_entries = [{"jsonPayload": {"event": "cache_stale", "tenant": "acme", "cache_fingerprint": F1, "ledger_fingerprint": F2, "action": STALE_ACTION}}] * 2
OUT["after"] += run_cell(STALE_PY, fake_gcloud(stale_entries))
assert OUT["after"].count("cache_stale acme") == 2

REV_LIVE, REV_CAND = "documind-api-00041-kqz", "documind-api-00045-tqm"
row = lambda rev, backend, tin, tout, cached, ms: {"resource": {"labels": {"revision_name": rev}}, "jsonPayload": {  # noqa: E731
    "event": "query", "tenant": "acme", "model_backend": backend, "tokens_in": tin, "tokens_out": tout, "cached_tokens": cached,
    "cost_usd": 0.0 if backend == "cache" else round(cost.price("gemini-3.6-flash", tin, tout, cached)["usd"], 6), "latency_ms": ms}}
ROWS = [row(REV_LIVE, "vertex", P + K, O, K, 2480), row(REV_CAND, "vertex", P + K, O, K, 2530), row(REV_CAND, "cache", 0, 0, 0, 170),
        row(REV_CAND, "vertex", P + 240 + K, O, K, 2610), row(REV_CAND, "vertex", P + K, O, K, 2440),
        row(REV_LIVE, "vertex", P + 30, O, 0, 2390), row(REV_CAND, "vertex", P + 30, O, 0, 2455),
        row(REV_LIVE, "vertex", P + 30 + K, O, K, 2575), row(REV_CAND, "cache", 0, 0, 0, 165)]
OUT["rows"] = run_cell(ROWS_PY, fake_gcloud(ROWS))
assert OUT["rows"].count("cache   in      0") == 2 and OUT["rows"].count("cached      0") == 4

# make cache: cache_admin.main()'s own printing, over a fake manager, once per fingerprint
REC = {"tenant_id": "acme", "cache_name": "projects/NUMBER/locations/global/cachedContents/CACHE_ID", "location": "global",
       "model": "gemini-3.6-flash", "tokens": K, "expire_time": "YYYY-MM-DD HH:MM:SS.ssssss+00:00", "version": CORPUS_V}


def admin(op: str, fingerprint: str) -> str:
    class FakeMgr:
        def __init__(self, project):
            pass

        def ledger_fingerprint(self, tenant):
            return fingerprint

        def create(self, tenant, system, pack, ttl_s, version, fingerprint):
            assert system == SYSTEM and pack == PACK and ttl_s == 3600
            return {**REC, "version": version, "corpus_fingerprint": fingerprint}

        def get(self, tenant, min_remaining_s=0):
            return dict(REC)

        def delete(self, tenant):
            pass

    mods = {"cache_manager": types.SimpleNamespace(TenantCacheManager=FakeMgr), "generator": types.SimpleNamespace(SYSTEM=SYSTEM)}
    saved = {k: sys.modules.get(k) for k in mods}
    sys.modules.update(mods)
    old_argv, buf = sys.argv, io.StringIO()
    sys.argv = ["cache_admin.py", op, "--project", PROJ, "--tenant", "acme"]
    try:
        with contextlib.redirect_stdout(buf):
            assert ca.main() == 0
    finally:
        sys.argv = old_argv
        for k, v in saved.items():
            sys.modules.pop(k, None) if v is None else sys.modules.__setitem__(k, v)
    return buf.getvalue()


PY_DEFAULT = re.search(r"^PY\s+\?= (\S+)", mk, re.M).group(1)
MAKE_LINE = ("cd services/rag-api && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=gemini-3.6-flash \\\n"
             f"  {PY_DEFAULT} cache_admin.py ${{CACHE_OP:-create}} --project documind-ai-YOUR-ID --tenant acme\n")
dflt = {k: re.search(rf"^{k}\s+\?= (\S+)", mk, re.M).group(1) for k in ("GENERATOR_MODEL", "RAG_MODEL_BASE", "ROUTING", "MODEL_BACKEND", "ARMOR")}
CAND_OUT = ("gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\\n"
            f"  --update-env-vars \"^|^GENERATOR_MODEL={dflt['GENERATOR_MODEL']}|RAG_MODEL_BASE={dflt['RAG_MODEL_BASE']}|ROUTING={dflt['ROUTING']}"
            f"|MODEL_BACKEND={dflt['MODEL_BACKEND']}|ARMOR={dflt['ARMOR']}|SEMANTIC_CACHE=on|...\"\n"
            f"...\n>> candidate revision: {REV_CAND} (deploy/.candidate-revision - make promote moves traffic to it by name)\n"
            f">> candidate: {CAND} (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)\nCAND={CAND}\n")
OUT["both"] = MAKE_LINE + admin("create", F1) + CAND_OUT
OUT["recache"] = MAKE_LINE + admin("create", F2) + state(F2, "ingest_reactivated", F2) + recache_asks
assert f"ledger fingerprint {F2}" in OUT["recache"] and ": current" in OUT["recache"]
GATE = f">> the gate, scoped to this document, on a candidate: make eval-live PROJECT={PROJ} SOURCE=hr_policy_2026.md API=<candidate url>\n"
assert 'echo ">> the gate, scoped to this document, on a candidate: make eval-live PROJECT=$PROJECT SOURCE=$OBJ API=<candidate url>"' in reindex_sh
REINDEX_HEAD = (f">> gs://{PROJ}-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)\n"
                ">> event doc_key chunks reused embedded retired effective_from\n")
OUT["reindex"] = REINDEX_HEAD + f">> ingest_reactivated\tacme_{V2_KEY[:16]}...\t283\t283\t0\t283\n" + GATE
OUT["restore"] = REINDEX_HEAD + f">> ingest_reactivated\tacme_{V1_KEY[:16]}...\t283\t283\t0\t283\n" + GATE
OUT["clean"] = ("Updating traffic...done.\nDone.\nURL: https://documind-api-...run.app\nTraffic:\n"
                f"  100% {REV_LIVE}      (the live revision, as before; no candidate tag)\n" + MAKE_LINE + admin("delete", F1))
assert OUT["clean"].rstrip().endswith("deleted acme's cache")
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "both": "run in the operator shell, in the kit (acme's context cache, and a candidate with the answer cache on)",
    "fns": "run in the operator shell, in the kit (two small functions, a start time, the state, and three asks)",
    "scope": "run in the operator shell, in the kit (the same question under two other scopes, and four scope hashes)",
    "reindex": "run in the operator shell, in the kit (revision 2 of the handbook, as a release)",
    "after": "run in the operator shell, in the kit (the state, both asks again, and the API's cache_stale lines)",
    "recache": "run in the operator shell, in the kit (the pack again, under the new fingerprint)",
    "restore": "run in the operator shell, in the kit (version 1's bytes again: the undo)",
    "back": "run in the operator shell, in the kit (the state, and the candidate's ask)",
    "rows": "run in the operator shell, in the kit (every acme usage row since the start; reads only)",
    "clean": "run in the operator shell, in the kit (the candidate's tag and recorded name removed, the context cache deleted)",
}
OUT_LABELS = {
    "both": "shape (make cache's own printing and the candidate's lines; your names, counts and fingerprint differ)",
    "fns": "(these cells against a fake Firestore and a local stub of the API; your fingerprints and tokens differ)",
    "scope": "(the asks against a local stub; the four hashes are the kit's own scope_of())",
    "reindex": "shape (or ingest_ok with a few chunks embedded, when revision 2's rows have aged out of the 30-day window)",
    "after": "(against a fake Firestore, a local stub and a fake gcloud; your fingerprints differ)",
    "recache": "(make cache's own printing, then the stand-ins; the answer's words are the model's)",
    "restore": "shape (the same counts as lesson 1.6's undo)",
    "back": "(against a fake Firestore and a local stub)",
    "rows": "(this cell against a fake gcloud, priced by the kit's own price(); your numbers differ)",
    "clean": "shape (gcloud's own lines vary by version)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: freshness over time
SIM_JS = r"""var SC = %s;
  function fresh(){ return {t: 0, corpus: 'v1', k: 6, f: 'none', p: 'v3', m: 'flash', sem: true, rows: [], cache: {fp: 'F1', model: 'flash', exp: 60}}; }
  function step(st, ev){                                            /* the kit's lookup(), store(), get(), stale_against(), generate_config_kwargs() */
    var e = ev.e, fp = st.corpus === 'v1' ? 'F1' : 'F2';
    if (e === 'reindex') { st.corpus = 'v2'; return null; }
    if (e === 'restore') { st.corpus = 'v1'; return null; }
    if (e === 'cache') { st.cache = {fp: fp, model: 'flash', exp: st.t + 60}; return null; }
    if (e === 'delete') { st.cache = null; return null; }
    if (e === 'wait') { st.t += ev.m; return null; }
    if (e === 'set') { st[ev.key] = ev.value; return null; }
    var scope = SC[st.k + '|' + st.f + '|' + st.p], hit = false, stored = false, why = '', ctx = 'skipped';
    if (st.sem) {
      hit = st.rows.some(function(r){ return r.fp === fp && r.scope === scope && r.exp > st.t; });
      if (!hit) {
        why = !st.rows.length ? 'nothing stored yet' : st.rows.some(function(r){ return r.fp === fp && r.scope === scope; }) ? 'the stored answer has expired'
          : st.rows.some(function(r){ return r.scope === scope; }) ? 'answered under another corpus fingerprint' : st.rows.some(function(r){ return r.fp === fp; }) ? 'answered for another scope' : 'another corpus and another scope';
        st.rows.push({fp: fp, scope: scope, exp: st.t + 1440}); stored = true;
      }
    }
    if (!hit) {
      var c = st.cache;
      ctx = !c || c.exp - st.t <= 2 ? 'none' : c.model !== st.m ? 'model' : c.fp !== fp ? 'stale' : 'attached';
    }
    return {answer: hit ? 'hit' : st.sem ? 'miss' : 'off', stored: stored, ctx: ctx, why: why}; }""" % json.dumps(SCOPES)
test_js = ("'use strict';\n" + SIM_JS.replace("\n  ", "\n") + "\n"
           f"var SEQS = {json.dumps([s for s, _ in SEQS])};\n"
           "console.log(JSON.stringify(SEQS.map(function(seq){ var st = fresh(), out = [];"
           " seq.forEach(function(ev){ var r = step(st, ev); if (r) out.push([r.answer, r.stored, r.ctx]); }); return out; })));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson92-js-")) / "fresh.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-600:]
for (seq, kit), js in zip(SEQS, json.loads(node.stdout)):
    assert kit == js, (seq, kit, js)
N_ASKS = sum(len(r) for _, r in SEQS)

UI_JS = r"""var root = document.getElementById('fresh'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); }, st = fresh(), log = [];
  var MODEL = {flash: 'gemini-3.6-flash', lite: 'gemini-3.1-flash-lite'};
  function clock(t){ var d = Math.floor(t / 1440), h = Math.floor(t %% 1440 / 60), m = t %% 60; return '+' + (d ? d + 'd ' : '') + h + 'h ' + (m < 10 ? '0' : '') + m + 'm'; }
  function sync(){ st.k = +$('fr-k').value; st.f = $('fr-f').value; st.p = $('fr-p').value; st.m = $('fr-m').value; st.sem = $('fr-s').value === 'on'; }
  function render(){
    var fp = st.corpus === 'v1' ? 'F1' : 'F2', c = st.cache, left = c ? c.exp - st.t : 0;
    $('fr-state').textContent = clock(st.t) + ' | corpus ' + (st.corpus === 'v1' ? 'version 1, 60 days' : 'revision 2, 90 days') + ', fingerprint ' + fp + ' | scope ' + SC[st.k + '|' + st.f + '|' + st.p]
      + ' | stored answers ' + st.rows.length + ' | context cache ' + (!c ? 'none' : left <= 0 ? 'expired' : 'packed from ' + c.fp + ', ' + left + ' min left');
    $('fr-log').innerHTML = log.slice(-10).map(function(x){ return '<li class="' + x[0] + '">' + x[1] + '</li>'; }).join('')
      + (st.rows.length > 5 ? '<li class="no">more than five stored answers for these words: the kit reads five per rung, so which ones Firestore returns now decides a hit</li>' : '');
  }
  var LABEL = {reindex: 'make reindex: revision 2 is current, the fingerprint moves', restore: 'make reindex: version 1 again, the old fingerprint returns',
               cache: 'make cache: packed under the current fingerprint, an hour to live', 'delete': 'the context cache deleted'};
  root.querySelectorAll('[data-ev]').forEach(function(b){ b.addEventListener('click', function(){
    var k = b.getAttribute('data-ev'); sync();
    if (k === 'reset') { st = fresh(); sync(); log = [['skip', 'start: a context cache packed under F1, no stored answers']]; render(); return; }
    var ev = k === 'w30' ? {e: 'wait', m: 30} : k === 'w1d' ? {e: 'wait', m: 1440} : {e: k};
    var r = step(st, ev);
    if (!r) { log.push(['skip', clock(st.t) + ' ' + (LABEL[k] || (ev.m === 30 ? '30 minutes pass' : 'a day passes'))]); render(); return; }
    var a = r.answer === 'hit' ? 'answer cache: HIT, the stored answer at cost 0, no model call' : r.answer === 'off' ? 'answer cache: off' : 'answer cache: miss (' + r.why + '), stored';
    var cx = r.ctx === 'skipped' ? '' : ' | context cache: ' + ({attached: 'attached, cached_tokens on the row', stale: 'not attached, cache_stale in the log',
      model: 'not attached, ' + MODEL[st.m] + ' is not the cache\'s model', none: 'none alive'})[r.ctx];
    log.push([r.answer === 'hit' || r.ctx === 'attached' ? 'ok' : 'no', clock(st.t) + ' ask (' + MODEL[st.m] + '): ' + a + cx]); render(); }); });
  sync(); log = [['skip', 'start: a context cache packed under F1, no stored answers']]; render();"""

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\n" + squeeze(SIM_JS) + "\n" + squeeze(UI_JS.replace("%%", "%")) + "\n})();\n</script>\n")
assert JS.count("<div") == JS.count("</div>") and "<tr" not in JS

STATS = {"N_SEQS": str(len(SEQS)), "N_ASKS": str(N_ASKS), "Q92": Q92, "F1": F1, "F2": F2, "K_FMT": f"{K:,}"}

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
print(f"kit: {len(SEQS)} random event sequences, {N_ASKS} asks, each equal to the kit's store()/lookup()/get()/stale_against()/generate_config_kwargs() in node"
      f" | 8 scope hashes from scope_of() | asks, make cache, state, scope and log cells run against stand-ins")
