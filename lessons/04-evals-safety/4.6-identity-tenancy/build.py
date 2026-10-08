"""Build lesson 4.6 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The page traces one request through three gates: Cloud Run's IAM (who may knock), shared/iap.py (who is asking)
and shared/tenancy.py (which tenant they may read), and ends on the usage row that names the verified caller.
What a build can run, it runs: make roster's dry run, and the list of services that call the shared verifier. The
cells that need the lane (the API's settings and invoker policy, the token claims, the rosters) are run against a
fake gcloud, fake tokens and a fake Firestore, so their code is tested even though their inputs are the lane's.
The identity tracer ports the verifier's decisions and the roster check to JavaScript; the build drives the kit's
own iap.identity() over every combination the tracer offers, with google-auth's signature check faked and its real
exception classes raised, and node must reproduce every verdict and message.
"""
import base64
import html
import itertools
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "4.6"
title = "<title>Lesson 4.6 Trace authenticated identity into tenant membership - the door, the verifier with two legs, the roster, and the usage row that names who asked | Netsetos</title>\n"
PROJ, ME = "documind-ai-YOUR-ID", "you@example.com"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.it-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px 12px;margin:0 0 10px;}
.it-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.it-in select,.it-in input{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.it-stage{background:var(--card);border:1px solid var(--border);border-left-width:4px;border-radius:10px;padding:8px 12px;margin:0 0 8px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.it-stage b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:2px;}
.it-stage.ok{border-left-color:#10b981;}.it-stage.no{border-left-color:#ef4444;background:#fef2f2;}.it-stage.off{border-left-color:#cbd5e1;color:#94a3b8;}
.it-stage code{overflow-wrap:anywhere;}
.it-final{font-family:var(--mono);font-size:13px;font-weight:700;padding:6px 10px;border-radius:8px;display:inline-block;}
.it-final.ok{background:#d1fae5;color:#065f46;}.it-final.no{background:#fee2e2;color:#991b1b;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
IAP, TEN = "shared/iap.py", "shared/tenancy.py"
RAPI, FE, CHAT, MAIN = "services/rag-api/auth.py", "services/frontend/auth.py", "services/frontend/chat.py", "services/rag-api/main.py"
EXCERPTS = {
    "invokers": ("commands/lesson-12.2.sh - who may knock on documind-api: run.invoker for four accounts, on this service only",
                 block("commands/lesson-12.2.sh", "# Who may KNOCK", n=10)),
    "identity": ("shared/iap.py - identity(): the assertion first, the bearer token second, never a header",
                 block(IAP, "def identity(headers, *, bearer_audience: str | None = None) -> dict:")),
    "verify": ("shared/iap.py - verify(): IAP's own keys, every accepted audience, IAP's issuer, an email",
               block(IAP, "def verify(assertion: str | None) -> dict:", end="def email_from(")),
    "bearer": ("shared/iap.py - bearer_email(): the caller's own ID token, verified for SELF_URL",
               block(IAP, "def bearer_email(headers, audience: str) -> str:", end="def identity(")),
    "roster_read": ("shared/tenancy.py - is_member() and tenant_for(): the point lookup and the reverse lookup",
                    block(TEN, "def is_member(email: str, tenant_id: str) -> bool:", end="# ---- the write side")),
    "roster_write": ("shared/tenancy.py - the write side: the operator's, never a service's",
                     block(TEN, "# Nothing above WRITES the roster;", end="def list_members(")),
    "roster_plan": ("commands/lane.py - roster_plan(): the memberships make roster writes",
                    block("commands/lane.py", "    sa = lambda name:", n=5)),
    "api_auth": ("services/rag-api/auth.py - verify_iap() and enforce_membership(): 401 for who, 403 for whether",
                 block(RAPI, "def verify_iap(request: Request) -> dict:") + "\n\n\n" + block(RAPI, "def enforce_membership(")),
    "ui_forward": ("services/frontend/chat.py - _headers(): two credentials on every call to the API",
                   block(CHAT, "def _headers(audience: str = RAG_API_URL) -> dict:", n=17)),
    "ui_admin": ("services/frontend/auth.py - the UI's own copy: its admin list, parsed the old way",
                 block(FE, 'ADMIN_EMAILS = set(os.getenv("ADMIN_EMAILS", "").split(","))', n=2) + "\n...\n" + block(FE, "def is_admin(user):", n=4)),
    "usage_row": ("services/rag-api/main.py - usage_row(): the tenant and the verified caller on every answer",
                  block(MAIN, '    return {"event": surface, "tenant": req.tenant_id, "user": user["email"],', n=1)),
}
assert EXCERPTS["invokers"][1].rstrip().endswith("done")
assert EXCERPTS["identity"][1].rstrip().endswith('refusing")')
assert EXCERPTS["verify"][1].rstrip().endswith("""raise IapError(f"invalid assertion: {type(last).__name__ if last else 'no audience matched'}")""")
assert EXCERPTS["bearer"][1].rstrip().endswith("return email")
assert EXCERPTS["roster_read"][1].rstrip().endswith("return None"), EXCERPTS["roster_read"][1][-60:]
assert EXCERPTS["roster_plan"][1].rstrip().endswith('plan.append(("acme", sa("agent")))'), EXCERPTS["roster_plan"][1][-60:]
assert EXCERPTS["api_auth"][1].rstrip().endswith('raise HTTPException(403, "not a member of this tenant")')
assert EXCERPTS["ui_forward"][1].rstrip().endswith("return h")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts
sys.path[:0] = [str(KIT), str(KIT / "commands")]
os.environ["IAP_AUDIENCE"] = "/projects/NUMBER/locations/asia-south1/services/documind-ui,/projects/NUMBER/locations/asia-south1/services/documind-chat"
from shared import iap  # noqa: E402

deploy = (KIT / "commands" / "lesson-12.2.sh").read_text(encoding="utf-8")
INVOKERS = re.search(r"for who in ([a-z\- ]+); do\n  gcloud run services add-iam-policy-binding documind-api", deploy).group(1).split()
assert INVOKERS == ["documind-ui-sa", "documind-chat-sa", "documind-mcp-sa", "documind-outsider-sa"], INVOKERS
assert "|IAP_AUDIENCE=/projects/$PROJECT_NUMBER/locations/${REGION:-us-central1}/services/documind-ui,/projects/$PROJECT_NUMBER/locations/${REGION:-us-central1}/services/documind-chat|" in deploy
assert "|SELF_URL=https://documind-api-$PROJECT_NUMBER.${REGION:-us-central1}.run.app|" in deploy
mk_roster = (KIT / "mk" / "ingestion.mk").read_text(encoding="utf-8")
assert "commands/lane.py --project $(PROJECT) roster --tenant" in mk_roster     # the global flag before the subcommand (fixed 23 September 2026)
r = subprocess.run([sys.executable, "commands/lane.py", "--project", PROJ, "roster", "--tenant", "acme", "--members", ME, "--dry-run"],
                   cwd=str(KIT), capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 0, r.stderr[-600:]
PLAN_OUT = r.stdout.replace(PROJ.lower(), PROJ)          # the tool lowercases every email; the page keeps the placeholder's spelling
ROSTER = {}
for e, t in re.findall(r"^would put (\S+) on (\S+)$", PLAN_OUT, re.M):
    ROSTER.setdefault(t, []).append(e)
ACCOUNTS = ["documind-ui-sa", "documind-chat-sa", "documind-mcp-sa", "documind-agent-sa", "documind-outsider-sa"]
sa_mail = lambda n: f"{n}@{PROJ}.iam.gserviceaccount.com"  # noqa: E731
assert sa_mail("documind-agent-sa") in ROSTER["acme"] and sa_mail("documind-agent-sa") not in ROSTER["zeta"] and not any(sa_mail("documind-outsider-sa") in v for v in ROSTER.values())
who_calls = sorted(str(p.relative_to(KIT)).replace("\\", "/") for d in ("services", "smoke") for p in (KIT / d).rglob("*.py")
                   if "iap.identity(" in p.read_text(encoding="utf-8", errors="replace"))
WHO_OUT = "\n".join(who_calls) + "\n"
assert who_calls == ["services/chat/agent.py", "services/mcp/server.py", "services/rag-api/auth.py"], who_calls

# ------------------------------------------------------------------ the kit's verifier over every combination the tracer offers
from google.auth import exceptions as gexc  # noqa: E402
from google.oauth2 import id_token  # noqa: E402

AUDS = iap.accepted_audiences()
SELF_URL = "https://documind-api-NUMBER.asia-south1.run.app"


def fake_verify_token(token, request, audience=None, certs_url=None):
    kind, aud_kind, email = token.split("|")
    if kind == "forged":
        raise gexc.MalformedError("Could not verify token signature.")
    if (aud_kind == "ui" and audience != AUDS[0]) or aud_kind == "other":
        raise gexc.InvalidValue(f"Token has wrong audience {aud_kind}, expected one of {audience}")
    return {"iss": iap.IAP_ISSUER, "email": email, "sub": "s", "aud": audience}


def fake_verify_oauth2(token, request, audience=None):
    kind, email = token.split("|")
    if kind == "tag":
        raise gexc.InvalidValue(f"Token has wrong audience candidate---..., expected one of {audience}")
    if kind == "noemail":
        return {"iss": "https://accounts.google.com", "aud": audience, "sub": "1"}
    return {"iss": "https://accounts.google.com", "aud": audience, "email": email, "email_verified": True}


id_token.verify_token, id_token.verify_oauth2_token = fake_verify_token, fake_verify_oauth2
PEOPLE = {"you": ME, "colleague": "colleague@example.com"}
CASES, KIT_OUT = [], []
for bearer, acct, assertion, person, tenant in itertools.product(["self", "tag", "noemail"], ACCOUNTS, ["none", "ui", "other", "forged"],
                                                                 list(PEOPLE), ["acme", "zeta", "globex"]):
    headers = {"authorization": f"Bearer {bearer}|{sa_mail(acct)}"}
    if assertion != "none":
        headers[iap.ASSERTION_HEADER] = f"{'forged' if assertion == 'forged' else 'ok'}|{assertion}|{PEOPLE[person]}"
    try:
        who = iap.identity(headers, bearer_audience=SELF_URL)
        member = who["email"] in [m.lower() for m in ROSTER.get(tenant, [])]
        KIT_OUT.append({"ok": True, "email": who["email"].lower(), "via": who["via"], "member": member})
    except iap.IapError as e:
        KIT_OUT.append({"ok": False, "msg": str(e)})
    CASES.append([bearer, acct, assertion, person, tenant])
assert any(k["ok"] and not k["member"] for k in KIT_OUT) and any(not k["ok"] for k in KIT_OUT)

# ------------------------------------------------------------------ the cells, tested against fakes
PY_SETTINGS = """import json, os, subprocess
def gcloud(*a):
    cmd = ["gcloud", *a, "--region", os.environ["REGION"], "--project", os.environ["PROJECT"], "--format=json"]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
env = {e["name"]: e.get("value", "") for e in gcloud("run", "services", "describe", "documind-api")["spec"]["template"]["spec"]["containers"][0].get("env", [])}
for k in ("IAP_AUDIENCE", "SELF_URL"):
    print(f"{k:13}", "\\n              ".join(env.get(k, "(unset)").split(",")))
for b in gcloud("run", "services", "get-iam-policy", "documind-api").get("bindings", []):
    if b["role"] == "roles/run.invoker":
        print("run.invoker  ", "\\n              ".join(sorted(b["members"])))"""

PY_CLAIMS = """import base64, json, os, time
for name in ("TOKEN", "BARE"):
    part = os.environ[name].split(".")[1]
    c = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))      # read, not verified: the API verifies
    print(f"{name}: aud {c.get('aud')}")
    print(f"       email {c.get('email', '(none)')}, email_verified {c.get('email_verified', '(none)')}, "
          f"iss {c.get('iss')}, {int((c['exp'] - time.time()) / 60)} minutes left")"""

PY_ROSTERS = """import os
from google.cloud import firestore
db = firestore.Client(project=os.environ["PROJECT"])
for t in ("acme", "zeta", "globex"):
    members = sorted(d.id for d in db.collection("tenants").document(t).collection("members").stream())
    print(f"{t:7} {len(members)} member(s)")
    for m in members:
        print("   ", m)"""

PY_ASK = """import os, sys; sys.path.insert(0, "evals")
from run_eval import ask
q = "What is the notice period for a confirmed E3?"
for header in ("eval@documind.in", "ceo@acme.example"):
    status, body, ms = ask(os.environ["API"], q, "acme", header, os.environ["TOKEN"])
    print(f"x-user-email {header:18} HTTP {status}, answerable {body.get('answerable')}")"""


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


LOG = 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" AND jsonPayload.tenant="acme"'
CELLS = {
    "settings": heredoc(PY_SETTINGS),
    "claims": heredoc(PY_CLAIMS, prefix='TOKEN="$(tok "$API")" BARE="$(gcloud auth print-identity-token --audiences="$API" \\\n'
                                        '  --impersonate-service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com")" '),
    "rosters": heredoc(PY_ROSTERS),
    "plan": 'python commands/lane.py --project "$PROJECT" roster --tenant acme --members "$ME" --dry-run',
    "who": 'grep -rl "iap.identity(" --include=*.py services smoke | sort',
    "ask": heredoc(PY_ASK, prefix='TOKEN="$(tok "$API")" ') + "\nsleep 20\n"
           f"gcloud logging read '{LOG}' \\\n  --project \"$PROJECT\" --freshness=10m --limit 2 --format='value(timestamp,jsonPayload.user,jsonPayload.tenant)'",
    "users": ("gcloud logging read 'resource.type=\"cloud_run_revision\" AND resource.labels.service_name=\"documind-api\" AND "
              "(jsonPayload.event=\"query\" OR jsonPayload.event=\"stream\")' \\\n"
              "  --project \"$PROJECT\" --freshness=1d --limit 1000 --format='value(jsonPayload.user)' | sort | uniq -c | sort -rn"),
}

T = Path(tempfile.mkdtemp(prefix="lesson81-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "REGION": "asia-south1", "PROJECT": PROJ}


def run_cell(body: str, prelude: str = "", env: dict | None = None) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(T), capture_output=True, text=True, encoding="utf-8", env=env or ENV)
    assert r.returncode == 0 and not r.stderr.strip(), r.stderr[-800:]
    return r.stdout


API_ENV = [{"name": "SELF_URL", "value": SELF_URL}, {"name": "IAP_AUDIENCE", "value": os.environ["IAP_AUDIENCE"]}]
FAKE_GCLOUD = ("import json, sys, types\n"
               "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               f"ENV, MEMBERS = {json.dumps(API_ENV)}, {json.dumps(sorted('serviceAccount:' + sa_mail(n) for n in INVOKERS))}\n"
               "def run(cmd, **kw):\n"
               "    if cmd[1:4] == ['run', 'services', 'describe']:\n"
               "        return R(json.dumps({'spec': {'template': {'spec': {'containers': [{'env': ENV}]}}}}))\n"
               "    if cmd[1:4] == ['run', 'services', 'get-iam-policy']:\n"
               "        return R(json.dumps({'bindings': [{'role': 'roles/run.invoker', 'members': MEMBERS}]}))\n"
               "    raise SystemExit('unexpected: ' + ' '.join(cmd))\n"
               "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT = {"settings": run_cell(PY_SETTINGS, FAKE_GCLOUD)}
assert "run.invoker   serviceAccount:documind-chat-sa@" in OUT["settings"] and OUT["settings"].count("serviceAccount:") == 4


def jwt(claims: dict) -> str:
    enc = lambda d: base64.urlsafe_b64encode(json.dumps(d).encode()).decode().rstrip("=")  # noqa: E731
    return f"{enc({'alg': 'RS256'})}.{enc(claims)}.signature"


import time  # noqa: E402

now = int(time.time())
tok_env = {**ENV, "TOKEN": jwt({"aud": SELF_URL, "email": sa_mail("documind-ui-sa"), "email_verified": True, "iss": "https://accounts.google.com", "exp": now + 3570}),
           "BARE": jwt({"aud": SELF_URL, "iss": "https://accounts.google.com", "exp": now + 3570})}
OUT["claims"] = run_cell(PY_CLAIMS, env=tok_env)
assert "email (none), email_verified (none)" in OUT["claims"] and "59 minutes left" in OUT["claims"], OUT["claims"]
FAKE_FS = ("import sys, types\n"
           f"ROSTER = {json.dumps(ROSTER)}\n"
           "class Doc:\n    def __init__(self, i): self.id = i\n"
           "class Coll:\n    def __init__(self, path): self.path = path\n"
           "    def document(self, d): return Ref(self.path + [d])\n"
           "    def stream(self): return [Doc(m) for m in ROSTER.get(self.path[1], [])]\n"
           "class Ref:\n    def __init__(self, path): self.path = path\n"
           "    def collection(self, c): return Coll(self.path + [c])\n"
           "class Client:\n    def __init__(self, project=None): pass\n"
           "    def collection(self, c): return Coll([c])\n"
           "fs = types.ModuleType('google.cloud.firestore'); fs.Client = Client\n"
           "gc = types.ModuleType('google.cloud'); gc.firestore = fs\n"
           "sys.modules['google.cloud'] = gc; sys.modules['google.cloud.firestore'] = fs\n")
OUT["rosters"] = run_cell(PY_ROSTERS, FAKE_FS)
assert OUT["rosters"].startswith("acme    5 member(s)"), OUT["rosters"]
shutil.rmtree(T, ignore_errors=True)
OUT["plan"] = PLAN_OUT
OUT["who"] = WHO_OUT
OUT["ask"] = ("x-user-email eval@documind.in   HTTP 200, answerable True\n"
              "x-user-email ceo@acme.example   HTTP 200, answerable True\n"
              f"YYYY-MM-DDTHH:MM:SS.ssssssZ\t{sa_mail('documind-ui-sa')}\tacme\n"
              f"YYYY-MM-DDTHH:MM:SS.ssssssZ\t{sa_mail('documind-ui-sa')}\tacme\n")
OUT["users"] = f"     NN {sa_mail('documind-ui-sa')}\n      N {ME}\n"


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "settings": "run in the operator shell, in the kit (the API's two audiences and who may invoke it; reads only)",
    "claims": "run in the operator shell, in the kit (two tokens for the API, one with the email and one without; decoded, not sent)",
    "rosters": "run in the operator shell, in the kit (the three rosters in Firestore; reads only)",
    "plan": "run in the operator shell, in the kit (make roster's plan; --dry-run writes nothing)",
    "who": "run in the operator shell, in the kit (which services call the shared verifier)",
    "ask": "run in the operator shell, in the kit (two questions, one with a forged x-user-email; then their usage rows)",
    "users": "run in the operator shell, in the kit (every caller the API recorded in the last day)",
}
OUT_LABELS = {
    "settings": "(this cell against a fake gcloud answering with lesson-12.2.sh's settings; your NUMBER and project id differ)",
    "claims": "(this cell over two fake tokens shaped like gcloud's; your project id and minutes differ)",
    "rosters": "(this cell against a fake Firestore holding make roster's plan; your roster may carry more people)",
    "plan": "(captured when this page was built, with PROJECT=documind-ai-YOUR-ID and ME=you@example.com)",
    "who": "(captured when this page was built)",
    "ask": "shape (the timestamps are your lane's; what matters is who the rows name)",
    "users": "shape (the counts are your lane's; your email appears once you have asked in the UI)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the identity tracer: the door, the verifier, the roster, the row
TRACE = {"invokers": INVOKERS, "roster": ROSTER, "people": PEOPLE, "project": PROJ, "accounts": ACCOUNTS}
TRACE_JS = r"""function verifier(T, c){                                             /* shared/iap.identity(), the API's settings */
    var bearer = c[0], acct = c[1], assertion = c[2], person = c[3], mail = acct + '@' + T.project + '.iam.gserviceaccount.com';
    if (assertion !== 'none') {
      if (assertion === 'forged') return {ok: false, msg: 'invalid assertion: MalformedError'};
      if (assertion === 'other') return {ok: false, msg: 'invalid assertion: InvalidValue'};
      return {ok: true, email: T.people[person], via: 'iap'};
    }
    if (bearer === 'tag') return {ok: false, msg: 'invalid bearer token: InvalidValue'};
    if (bearer === 'noemail') return {ok: false, msg: 'the bearer token carries no verified email'};
    return {ok: true, email: mail, via: 'iam'}; }
  function member(T, email, tenant){ return (T.roster[tenant] || []).map(function(m){ return m.toLowerCase(); }).indexOf(email.toLowerCase()) >= 0; }"""

test_js = ("'use strict';\n" + TRACE_JS + "\nvar T = " + json.dumps(TRACE) + ";\nvar C = " + json.dumps(CASES) + ";\n"
           "console.log(JSON.stringify(C.map(function(c){ var v = verifier(T, c); return v.ok ? {ok: true, email: v.email, via: v.via, member: member(T, v.email, c[4])} : v; })));\n")
tjs = Path(tempfile.mkdtemp(prefix="lesson81-js-")) / "trace.js"
tjs.write_text(test_js, encoding="utf-8")
node = subprocess.run(["node", str(tjs)], capture_output=True, text=True, encoding="utf-8")
shutil.rmtree(tjs.parent, ignore_errors=True)
assert node.returncode == 0, node.stderr[-600:]
for c, k, j in zip(CASES, KIT_OUT, json.loads(node.stdout)):
    if j.get("email"):
        j["email"] = j["email"].lower()
    assert k == j, (c, k, j)

UI_JS = r"""var root = document.getElementById('tracer'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var ids = ['it-bearer', 'it-acct', 'it-assert', 'it-person', 'it-hdr', 'it-tenant'], out = $('it-out');
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function stage(cls, head, body){ return '<p class="it-stage ' + cls + '"><b class="h">' + head + '</b>' + body + '</p>'; }
  function render(){
    var bearer = $('it-bearer').value, acct = $('it-acct').value, assertion = $('it-assert').value, person = $('it-person').value, hdr = $('it-hdr').value, tenant = $('it-tenant').value;
    var html = '', final;
    if (bearer === 'none') {
      html += stage('no', '1 &middot; the door: Cloud Run IAM', 'No <code>Authorization: Bearer</code> token. Cloud Run refuses before any kit code runs: 401 or 403, which the kit\'s smoke test accepts either way.');
      final = 'refused at the door';
    } else if (T.invokers.indexOf(acct) < 0) {
      html += stage('no', '1 &middot; the door: Cloud Run IAM', '<code>' + acct + '</code> holds no <code>roles/run.invoker</code> on documind-api. Cloud Run refuses: HTTP 403.');
      final = 'HTTP 403 from Cloud Run';
    } else {
      html += stage('ok', '1 &middot; the door: Cloud Run IAM', '<code>' + acct + '</code> is one of the four accounts with <code>roles/run.invoker</code> on this service. The request reaches the API.');
      var v = verifier(T, [bearer, acct, assertion, person]);
      if (!v.ok) {
        html += stage('no', '2 &middot; who is asking: shared/iap.identity()', (assertion !== 'none' ? 'An assertion is present, so it is the only leg tried. ' : 'No assertion, so the bearer leg: the token must be for SELF_URL and carry a verified email. ')
          + 'Refused: <code>' + esc(v.msg) + '</code>');
        final = 'HTTP 401: ' + v.msg;
      } else {
        html += stage('ok', '2 &middot; who is asking: shared/iap.identity()', 'Verified <code>' + esc(v.email) + '</code>, via <code>' + v.via + '</code>' + (v.via === 'iap' ? ': the person the surface forwarded, not the surface\'s own account.' : ': the caller\'s own account, since no person was forwarded.')
          + (hdr ? ' The <code>x-user-email: ' + esc(hdr) + '</code> header is never read.' : ''));
        if (member(T, v.email, tenant)) {
          html += stage('ok', '3 &middot; which tenant: enforce_membership()', '<code>tenants/' + tenant + '/members/' + esc(v.email) + '</code> exists. One document read.');
          html += stage('ok', '4 &middot; the usage row', '<code>"tenant": "' + tenant + '", "user": "' + esc(v.email) + '"</code>');
          final = 'HTTP 200, answered for ' + v.email;
        } else {
          html += stage('no', '3 &middot; which tenant: enforce_membership()', 'No <code>tenants/' + tenant + '/members/' + esc(v.email) + '</code>. Authenticated, not authorised: <code>not a member of this tenant</code>');
          html += stage('off', '4 &middot; the usage row', 'none: the request stopped before retrieval');
          final = 'HTTP 403: not a member of this tenant';
        }
      }
    }
    out.innerHTML = html + '<span class="it-final ' + (final.indexOf('HTTP 200') === 0 ? 'ok' : 'no') + '">' + esc(final) + '</span>';
  }
  ids.forEach(function(id){ $(id).addEventListener('input', render); $(id).addEventListener('change', render); });
  render();"""

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar T = " + json.dumps(TRACE, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/") + ";\n"
      + squeeze(TRACE_JS) + "\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert JS.count("<div") == JS.count("</div>") and "<tr" not in JS

STATS = {"N_CASES": str(len(CASES)), "N_INVOKERS": str(len(INVOKERS)), "N_ACME": str(len(ROSTER["acme"])), "N_ZETA": str(len(ROSTER["zeta"])),
         "N_GLOBEX": str(len(ROSTER["globex"]))}

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
print(f"kit: invokers {INVOKERS} | roster acme {len(ROSTER['acme'])}, zeta {len(ROSTER['zeta'])}, globex {len(ROSTER['globex'])}"
      f" | {len(CASES)} tracer cases equal to shared/iap.identity() in node | callers of the verifier: {len(who_calls)}")
