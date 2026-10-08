"""Build lesson 4.7 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The page tests the checks lesson 4.6 traced: a request refused at the door, a 401 and a 403 from the API side by
side, the isolation rows as the outsider and as a member, and the data-residency policy with a pin it must
overrule. The two request cells are run here against a local stub server that answers the way the API does (the
page says so), so their printing is the cells' own. The access matrix is computed from the kit's invoker list and
make roster's plan; the residency panel ports choose_for()'s pin rule and retrieval_backend_for(), and the build
runs the kit's own two functions on every combination the panel offers, and node must agree with each.
"""
import ast
import html
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "4.7"
title = "<title>Lesson 4.7 Test valid access, denied access and cross-tenant requests - the door, a 401 and a 403 side by side, the isolation rows, and a residency policy that overrules a pin | Netsetos</title>\n"
PROJ, ME = "documind-ai-YOUR-ID", "you@example.com"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.am-grid{display:grid;grid-template-columns:minmax(0,1.6fr) repeat(3,minmax(0,1fr));gap:4px;margin:0 0 8px;}
.am-grid span{font-family:var(--mono);font-size:11.5px;min-width:0;overflow-wrap:anywhere;padding:4px 6px;}
.am-grid .hd{color:var(--slate);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;}
.am-grid button{font-family:var(--mono);font-size:12px;min-height:44px;border-radius:8px;border:1px solid var(--border);background:var(--card);cursor:pointer;color:var(--navy);}
.am-grid button.ok{background:#ecfdf5;border-color:#a7f3d0;color:#065f46;}.am-grid button.no{background:#fef2f2;border-color:#fca5a5;color:#991b1b;}.am-grid button.door{background:#f1f5f9;border-color:#cbd5e1;color:#475569;}
.am-grid button.sel{outline:2px solid var(--navy);outline-offset:1px;}
.am-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.am-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.rp-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.rp-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.rp-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.rp-out{font-family:var(--mono);font-size:12.5px;white-space:pre-wrap;color:var(--navy);margin:6px 0 0;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
RE_, RAPI, MAIN, TEN, RET = "evals/run_eval.py", "services/rag-api/auth.py", "services/rag-api/main.py", "shared/tenancy.py", "services/rag-api/retriever.py"
EXCERPTS = {
    "smoke_3b": ("smoke/smoke.py - check 3b: the same question with no token must be refused",
                 block("smoke/smoke.py", "    # 3b. the same question with NO token", n=7)),
    "api_codes": ("services/rag-api/auth.py - who is a 401, whether is a 403",
                  block(RAPI, "    except iap.IapError as e:", n=5) + "\n\n\n" + block(RAPI, "def enforce_membership(")),
    "outsider": ("terraform/sa.tf - the outsider: an account IAM admits and no roster lists",
                 block("terraform/sa.tf", "# The eval gate's OUTSIDER", n=11)),
    "restricts": ("services/rag-api/retriever.py - the tenant filter, on the vector query and on the Firestore rung",
                  block(RET, '    restricts = [Namespace(name="tenant_id", allow_tokens=[tenant_id])]', n=6) + "\n...\n"
                  + block(RET, '    query = _fs().collection(settings.chunks_collection).where("tenant_id", "==", tenant_id)', n=1)),
    "isolation": ("evals/run_eval.py - check_isolation(): every isolation row, asked by the outsider, must be a 403",
                  block(RE_, '    rows = [r for r in golden if r["shape"] == "isolation"]', n=10)),
    "policy": ("shared/tenancy.py - policy_of() and permits(): absent is in, and in keeps text in India",
               block(TEN, "def policy_of(doc: dict | None) -> str:", n=5) + "\n\n\n" + block(TEN, "def permits(policy: str, region: str | None) -> bool:", n=6)),
    "pin": ("services/rag-api/main.py - choose_for(): a tenant's pin, unless the deployment cannot serve it",
            block(MAIN, '    pin = ts.get("retrieval_backend")', n=9)),
    "fallback": ("services/rag-api/main.py - retrieval_backend_for(): the policy overrules the pin, per request",
                 block(MAIN, "def retrieval_backend_for(tenant_id: str, backend: str) -> tuple[str, int]:")),
    "chat4": ("smoke/smoke_chat.py - check 4: the chat service refuses the outsider the same way",
              block("smoke/smoke_chat.py", "    4. POST /v1/chat as the outsider", n=3)),
}
assert EXCERPTS["smoke_3b"][1].rstrip().endswith('the service answered an anonymous caller")')
assert EXCERPTS["api_codes"][1].rstrip().endswith('raise HTTPException(403, "not a member of this tenant")')
assert EXCERPTS["outsider"][1].rstrip().endswith('no roster does)"\n}'), EXCERPTS["outsider"][1][-80:]
assert EXCERPTS["isolation"][1].rstrip().endswith("return (got / len(rows) if rows else 0.0), bad"), EXCERPTS["isolation"][1][-80:]
assert EXCERPTS["policy"][1].rstrip().endswith("return str(region or \"\").strip().lower().startswith(INDIA_REGION_PREFIXES)")
assert EXCERPTS["pin"][1].rstrip().endswith("return backend, model, retrieval"), EXCERPTS["pin"][1][-90:]
assert EXCERPTS["fallback"][1].rstrip().endswith("return backend, 0")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts
sys.path[:0] = [str(KIT), str(KIT / "evals"), str(KIT / "services" / "rag-api")]
import run_eval as rv  # noqa: E402
from shared.tenancy import policy_of  # noqa: E402

golden = rv.load_golden()
ISO = [r for r in golden if r["shape"] == "isolation"]
deploy = (KIT / "commands" / "lesson-12.2.sh").read_text(encoding="utf-8")
INVOKERS = re.search(r"for who in ([a-z\- ]+); do\n  gcloud run services add-iam-policy-binding documind-api", deploy).group(1).split()
r = subprocess.run([sys.executable, "commands/lane.py", "--project", PROJ, "roster", "--tenant", "acme", "--members", ME, "--dry-run"],
                   cwd=str(KIT), capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 0, r.stderr[-400:]
ROSTER, POLICIES = {}, dict(re.findall(r"^would set (\S+): data_region=(\S+)$", r.stdout, re.M))
for e, t in re.findall(r"^would put (\S+) on (\S+)$", r.stdout, re.M):
    ROSTER.setdefault(t, []).append(e.replace(PROJ.lower(), PROJ))
TENANTS = ["acme", "zeta", "globex"]
cfg = (KIT / "services" / "rag-api" / "config.py").read_text(encoding="utf-8")
RB = ast.literal_eval(re.search(r"^RETRIEVAL_BACKENDS = (\(.*?\))", cfg, re.M).group(1))
MB = ast.literal_eval(re.search(r"^MANAGED_BACKENDS = (\(.*?\))", cfg, re.M).group(1))

# ------------------------------------------------------------------ the kit's pin and policy rules, over every combination
main_src = (KIT / MAIN).read_text(encoding="utf-8")
tree = ast.parse(main_src)
fsrc = {n.name: ast.get_source_segment(main_src, n) for n in tree.body if isinstance(n, ast.FunctionDef) and n.name in ("choose_for", "retrieval_backend_for")}


class Settings:
    model_backend = "vertex"


RES_CASES, RES_KIT = [], []
for dep, mode, pin, policy in itertools.product(["vector", "firestore"], ["dense", "hybrid"], [None, "vector", "firestore", "rag_engine", "vertex_search", "bogus"], ["in", "any", None]):
    warnings = []
    s = Settings()
    s.retrieval_backend, s.retrieval_mode = dep, mode
    doc = {k: v for k, v in (("retrieval_backend", pin), ("data_region", policy)) if v}
    ns = {"settings": s, "tenant_settings": lambda t, d=doc: d, "choose_model_for": lambda q: "m", "RETRIEVAL_BACKENDS": RB, "MANAGED_BACKENDS": MB,
          "policy_of": policy_of, "json": json, "log": type("L", (), {"warning": staticmethod(lambda m: warnings.append(m))})}
    for f in fsrc.values():
        exec(f, ns)
    req = type("Req", (), {"tenant_id": "globex", "query": "q"})()
    _, _, chosen = ns["choose_for"](req)
    served, fb = ns["retrieval_backend_for"]("globex", chosen)
    RES_CASES.append([dep, mode, pin or "", policy or ""])
    RES_KIT.append({"served": served, "fallback": fb, "ignored": bool(warnings)})
assert {"served": "vector", "fallback": 1, "ignored": False} in RES_KIT and any(k["ignored"] for k in RES_KIT)

# ------------------------------------------------------------------ the access matrix, from the invoker list and the roster plan
IDS = [["you, signed in to the UI", "person", ME], ["a colleague on no roster, signed in", "person", "colleague@example.com"],
       ["documind-ui-sa", "sa", "documind-ui-sa"], ["documind-chat-sa", "sa", "documind-chat-sa"], ["documind-mcp-sa", "sa", "documind-mcp-sa"],
       ["documind-agent-sa", "sa", "documind-agent-sa"], ["documind-outsider-sa", "sa", "documind-outsider-sa"]]
mail = lambda i: i[2] if i[1] == "person" else f"{i[2]}@{PROJ}.iam.gserviceaccount.com"  # noqa: E731
MATRIX = []
for ident in IDS:
    row = []
    for t in TENANTS:
        door = "documind-ui-sa" if ident[1] == "person" else ident[2]            # a person arrives with the UI's token for the door
        if door not in INVOKERS:
            row.append("door")
        else:
            row.append("200" if mail(ident) in ROSTER.get(t, []) else "403")
    MATRIX.append(row)
assert MATRIX[0] == ["200", "403", "403"] and MATRIX[5] == ["door"] * 3 and MATRIX[6] == ["403"] * 3 and MATRIX[2] == ["200"] * 3

# ------------------------------------------------------------------ the request cells, run against a local stub of the API
PY_LADDER = """import json, os, urllib.error, urllib.request
body = json.dumps({"query": "What is the notice period for a confirmed E3?", "tenant_id": "acme", "top_k": 6}).encode()
for label, token in [("no token", None), ("a token without its email", os.environ["BARE"]),
                     ("the outsider's token", os.environ["OUTSIDER"]), ("documind-ui-sa's token", os.environ["TOKEN"])]:
    req = urllib.request.Request(os.environ["API"] + "/v1/query", data=body, method="POST", headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            status, text = r.status, r.read().decode()
    except urllib.error.HTTPError as e:
        status, text = e.code, e.read().decode(errors="replace")
    shown = text[:66] if text.startswith("{") else "(Cloud Run's own page: the request never reached the API)"
    print(f"  {label:26} {status}  {shown}")"""

PY_ISO = """import os, sys; sys.path.insert(0, "evals")
from run_eval import ask, check_isolation, contains, load_golden
api, token = os.environ["API"], os.environ["TOKEN"]
iso = [r for r in load_golden() if r["shape"] == "isolation"]
rate, bad = check_isolation(api, iso, token, os.environ["OUTSIDER"])
print(f"the outsider, on {len(iso)} isolation rows: 403 on {rate:.0%}", *bad, sep="\\n  ")
for r in iso:
    status, body, _ = ask(api, r["question"], r["tenant"], "eval@documind.in", token)
    leaked = [w for w in r["must_not_contain"] if contains(body.get("answer", ""), w)]
    print(f"  {r['id']:6} as {r['tenant']:6} HTTP {status}  answerable {str(body.get('answerable')):5}  "
          + (f"LEAKED {', '.join(leaked)}" if leaked else f"no {r['must_not_contain'][0]!r}"))"""

ANS = {"What is the notice period for a confirmed E3?": "A confirmed employee at grade E3 or above serves a notice period of 60 days [1]."}


class Stub(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def reply(self, code, obj=None, raw=None):
        data = raw.encode() if raw is not None else json.dumps(obj, separators=(",", ":")).encode()
        self.send_response(code)
        self.send_header("Content-Type", "text/html" if raw is not None else "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_POST(self):
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        auth = self.headers.get("Authorization", "")
        if not auth:
            return self.reply(403, raw="<html><head><title>403 Forbidden</title></head><body>Your client does not have permission</body></html>")
        tok = auth[7:]
        if tok == "BARE":
            return self.reply(401, {"detail": "the bearer token carries no verified email"})
        if tok == "OUTSIDER":
            return self.reply(403, {"detail": "not a member of this tenant"})
        row = next((g for g in golden if g["question"] == req["query"] and g["tenant"] == req["tenant_id"]), None)
        answerable = bool(row and row["answerable"]) or req["query"] in ANS
        answer = ANS.get(req["query"]) or (f"{' and '.join(row['must_contain'])} [1]." if answerable else "The documents for this tenant do not say.")
        cites = [{"chunk_id": f"{req['tenant_id']}:x#0", "source_uri": f"gs://x/{req['tenant_id']}/d.md", "quote": "q"}] if answerable else []
        self.reply(200, {"answer": answer, "citations": cites, "answerable": answerable, "confidence": "high" if answerable else "low"})


srv = ThreadingHTTPServer(("127.0.0.1", 0), Stub)
threading.Thread(target=srv.serve_forever, daemon=True).start()
T = Path(tempfile.mkdtemp(prefix="lesson82-"))
(T / "evals").mkdir()
for n in ("run_eval.py", "golden.jsonl", "required.json", "manifest.json"):
    shutil.copy2(KIT / "evals" / n, T / "evals" / n)
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1",
       "API": f"http://127.0.0.1:{srv.server_address[1]}", "TOKEN": "TOKEN", "BARE": "BARE", "OUTSIDER": "OUTSIDER"}


def run_cell(body: str) -> str:
    r = subprocess.run([sys.executable, "-"], input=body, cwd=str(T), capture_output=True, text=True, encoding="utf-8", env=ENV)
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


OUT = {"ladder": run_cell(PY_LADDER), "iso": run_cell(PY_ISO)}
srv.shutdown()
shutil.rmtree(T, ignore_errors=True)
assert "401  {\"detail\":\"the bearer token carries no verified email\"}" in OUT["ladder"] and "403 on 100%" in OUT["iso"], (OUT["ladder"], OUT["iso"])


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


BARE = 'BARE="$(gcloud auth print-identity-token --audiences="$API" --impersonate-service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com")"'
LOG = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" AND jsonPayload.tenant="globex"')
PY_GLOBEX = """import os, sys; sys.path.insert(0, "evals")
from run_eval import ask
status, body, _ = ask(os.environ["API"], "Who is a Data Fiduciary under the DPDP Act?", "globex", "eval@documind.in", os.environ["TOKEN"])
print(f"globex asked: HTTP {status}, answerable {body.get('answerable')}")"""
CELLS = {
    "ladder": heredoc(PY_LADDER, prefix=f'TOKEN="$(tok "$API")" OUTSIDER="$(otok)" {BARE} \\\n  '),
    "iso": heredoc(PY_ISO, prefix='TOKEN="$(tok "$API")" OUTSIDER="$(otok)" '),
    "smoke": 'DOCUMIND_API_URL="$API" DOCUMIND_PROJECT="$PROJECT" DOCUMIND_TENANT=acme make smoke | grep -E "no token|pass ·"',
    "policy": "for t in acme zeta globex; do make tenant-policy TENANT=$t; done",
    "pin": ("make tenant-backend TENANT=globex RETRIEVAL_BACKEND=rag_engine\n"
            "sleep 65                        # the API reads tenant_settings once a minute\n"
            + heredoc(PY_GLOBEX, prefix='TOKEN="$(tok "$API")" ') + "\nsleep 20\n"
            f"gcloud logging read '{LOG}' \\\n  --project \"$PROJECT\" --freshness=10m --limit 1 --format='value(jsonPayload.retrieval_backend,jsonPayload.policy_fallback)'\n"
            "make tenant-backend TENANT=globex RETRIEVAL_BACKEND=default"),
}
assert "lk-28" in {g["id"] for g in golden if g["question"] == "Who is a Data Fiduciary under the DPDP Act?" and g["tenant"] == "globex"}
OUT["smoke"] = "  [PASS] no token refused  status=403\n  N pass · 0 fail\n"
OUT["policy"] = "".join(f"{t}: data_region={POLICIES[t]}\n" for t in TENANTS)
OUT["pin"] = ("globex: retrieval_backend=rag_engine\nglobex asked: HTTP 200, answerable True\nvector\t1\nglobex: retrieval_backend=default\n")
tb = (KIT / "shared" / "tenancy.py").read_text(encoding="utf-8")
assert 'print(f"{args.tenant}: data_region={policy_for(args.tenant)}")' in tb and 'print(f"{args.tenant}: retrieval_backend={set_backend(args.tenant, args.backend)}")' in tb
assert 'print(f"  {len(passed)} pass · {len(failed)} fail\\n")' in (KIT / "smoke" / "smoke.py").read_text(encoding="utf-8")


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "ladder": "run in the operator shell, in the kit (four requests to /v1/query; one is answered)",
    "iso": f"run in the operator shell, in the kit ({len(ISO)} outsider requests, then {len(ISO)} member questions)",
    "smoke": "run in the operator shell, in the kit (the kit's smoke test, two of its lines)",
    "policy": "run in the operator shell, in the kit (each tenant's data_region; reads only)",
    "pin": "run in the operator shell, in the kit (a pin set, one question, its usage row, the pin cleared)",
}
OUT_LABELS = {
    "ladder": "(this cell against a local stub that answers as the API does; the door's code is 401 or 403, and your answer's words differ)",
    "iso": "(this cell against the same stub; your answers' words differ, and every line should still say no marker)",
    "smoke": "shape (the door's code is 401 or 403; N is the number of checks your lane runs)",
    "policy": "(the values make roster writes; a tenant it never wrote prints in, because absent means in)",
    "pin": "shape (the backend is your deployment's own: vector or firestore)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: the access matrix and the residency panel
W = {"ids": IDS, "tenants": TENANTS, "matrix": MATRIX, "invokers": INVOKERS, "roster": ROSTER, "rb": list(RB), "mb": list(MB), "project": PROJ}
RES_JS = r"""function serve(W, dep, mode, pin, policy){                      /* choose_for()'s pin rule, then retrieval_backend_for() */
    var r = dep, ignored = false, fb = 0;
    if (pin && pin !== dep) { if (W.rb.indexOf(pin) >= 0 && !(W.mb.indexOf(pin) >= 0 && mode === 'hybrid')) r = pin; else ignored = true; }
    if (W.mb.indexOf(r) >= 0 && policy !== 'any') { r = W.mb.indexOf(dep) < 0 ? dep : 'firestore'; fb = 1; }
    return {served: r, fallback: fb, ignored: ignored}; }"""
test_js = ("'use strict';\n" + RES_JS + "\nvar W = " + json.dumps(W) + ";\nvar C = " + json.dumps(RES_CASES) + ";\n"
           "console.log(JSON.stringify(C.map(function(c){ return serve(W, c[0], c[1], c[2], c[3]); })));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson82-js-")) / "res.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-600:]
for c, k, j in zip(RES_CASES, RES_KIT, json.loads(node.stdout)):
    assert k == j, (c, k, j)

UI_JS = r"""var root = document.getElementById('access'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var grid = $('am-grid'), why = $('am-why'), sel = null;
  var WHERE = {vector: 'the kit\'s Vector Search index, in your lane\'s region', firestore: 'the kit\'s Firestore rows, in your lane\'s region',
               rag_engine: 'RAG Engine, in us-central1', vertex_search: 'Vertex AI Search, in global'};
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function label(o){ return o === 'door' ? 'door' : o === '200' ? '200' : '403'; }
  function explain(i, t){
    var id = W.ids[i], o = W.matrix[i][t], tenant = W.tenants[t], person = id[1] === 'person', acct = person ? 'documind-ui-sa' : id[2];
    var mail = person ? id[2] : id[2] + '@' + W.project + '.iam.gserviceaccount.com';
    if (o === 'door') return '<b class="h">' + esc(id[0]) + ' asks ' + tenant + ': refused at the door</b><code>' + acct + '</code> holds no <code>roles/run.invoker</code> on documind-api, so Cloud Run answers 403 before the API runs. This account reaches the lane through the MCP server, which asks as itself.';
    var head = '<b class="h">' + esc(id[0]) + ' asks ' + tenant + ': HTTP ' + o + '</b>';
    var how = person ? 'The UI\'s own token passes the door, and the verifier takes the person from the forwarded assertion: <code>' + esc(mail) + '</code>. ' : '<code>' + acct + '</code> passes the door, and the verifier takes the account from its own token. ';
    return head + how + (o === '200' ? 'The roster <code>tenants/' + tenant + '/members</code> lists it, so the question is answered, and the usage row says so.'
      : 'The roster <code>tenants/' + tenant + '/members</code> does not list it: authenticated, not authorised, <code>not a member of this tenant</code>.');
  }
  function renderGrid(){
    grid.innerHTML = '<span class="hd">asks</span>' + W.tenants.map(function(t){ return '<span class="hd">' + t + '</span>'; }).join('')
      + W.ids.map(function(id, i){ return '<span>' + esc(id[0]) + '</span>' + W.tenants.map(function(t, j){ var o = W.matrix[i][j];
          return '<button type="button" data-c="' + i + ',' + j + '" class="' + (o === '200' ? 'ok' : o === 'door' ? 'door' : 'no') + (sel === i + ',' + j ? ' sel' : '') + '">' + label(o) + '</button>'; }).join(''); }).join('');
    why.innerHTML = sel ? explain(+sel.split(',')[0], +sel.split(',')[1]) : '<b class="h">Pick a cell</b>Each cell is one identity asking one tenant. Tap it for the path through the door, the verifier and the roster.';
  }
  grid.addEventListener('click', function(e){ var b = e.target.closest('button'); if (!b) return; sel = b.getAttribute('data-c'); renderGrid(); });
  var rin = ['rp-policy', 'rp-pin', 'rp-dep', 'rp-mode'], rout = $('rp-out');
  function renderRes(){
    var policy = $('rp-policy').value, pin = $('rp-pin').value, dep = $('rp-dep').value, mode = $('rp-mode').value;
    var s = serve(W, dep, mode, pin, policy);
    rout.textContent = (s.ignored ? 'the pin is ignored with a retrieval_pin_ignored line: ' + (W.rb.indexOf(pin) < 0 ? 'not a backend the API knows' : 'a managed store cannot fuse hybrid') + '\n' : '')
      + 'served from   ' + s.served + '\nsearched in   ' + WHERE[s.served] + '\npolicy_fallback ' + s.fallback + (s.fallback ? '   (the pin named a store outside India and the policy is in)' : '');
  }
  rin.forEach(function(id){ $(id).addEventListener('change', renderRes); });
  renderGrid(); renderRes();"""

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar W = " + json.dumps(W, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n"
      + squeeze(RES_JS) + "\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert JS.count("<div") == JS.count("</div>") and "<tr" not in JS

STATS = {"N_ISO": str(len(ISO)), "N_INVOKERS": str(len(INVOKERS)), "N_RES": str(len(RES_CASES)), "P_ACME": POLICIES["acme"], "P_ZETA": POLICIES["zeta"], "P_GLOBEX": POLICIES["globex"]}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: invokers {len(INVOKERS)} | policies {POLICIES} | {len(RES_CASES)} residency cases equal to choose_for + retrieval_backend_for in node"
      f" | ladder and isolation cells run against a local stub")
