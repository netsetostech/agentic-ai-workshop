"""Build lesson 6.7 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Two properties, forced to fail and watched not to. Durability: a conversation outlives the instance that held it, so a
redeploy - new revision, new instances - must not lose it. Isolation: a conversation is readable only by its own tenant,
person and session, because the server builds the thread id from the verified identity and the request carries no
tenant and no person. Offline, in ~/graph-venv: the kit's own chat app under FastAPI's TestClient, with a model that can
only answer from the history it is sent - the word given, asked for by the same person, a new session, a colleague, a
member of another tenant, a body that names another tenant, a session id with a colon, the outsider and a token that
names nobody - then a restart of that app on the memory checkpointer. Live: a word given to the LangChain and ADK brains,
a redeploy of documind-chat, the word asked for again; you, in the UI, asking for it; and the rows the tables hold.

Build-time proof: the offline cell runs here on the kit's agent.py, brains.py and tools.py; every status and answer is
the app's own. The widget's rule is checked against that run and, with node, against this file's for every choice. The
live cells run against stand-ins: a local chat service that keeps the LangChain thread across a redeploy and ADK's
sessions in memory, a fake gcloud, and a fake Cloud SQL connector.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "6.7"
title = "<title>Lesson 6.7 Verify restart recovery and session isolation - a conversation that outlives a redeploy, and a thread nobody else can read | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,9em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid code{overflow-wrap:anywhere;}
.fs-grid .yes{color:var(--teal-dark);font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
AG, BR, FE = "services/chat/agent.py", "services/chat/brains.py", "services/frontend/chat.py"
EXCERPTS = {
    "request": ("services/chat/agent.py - the request: a question, a conversation, a brain, and nowhere to name a tenant or a person",
                block(AG, "class ChatRequest(BaseModel):", n=11)),
    "thread": ("services/chat/agent.py - the thread id the server builds from the verified identity",
               block(AG, "def thread_config(tenant_id: str, user_id: str, session_id: str) -> dict:", n=9)),
    "turn": ("services/chat/agent.py - each turn: the tenant from the roster, the person from the token, the session from the request",
             block(AG, "    out = brain.answer(", n=5)),
    "lifespan": ("services/chat/agent.py - the checkpointer, opened once per instance",
                 block(AG, "async def lifespan(app: FastAPI):", n=6)),
}
assert 'session_id: str = Field(default="default", pattern=r"^[A-Za-z0-9_-]{1,64}$")' in EXCERPTS["request"][1]
assert "tenant_id and user_id used to be fields here" in EXCERPTS["request"][1]
assert 'raise HTTPException(400, "ids must not contain \':\'")' in EXCERPTS["thread"][1]
assert "config=thread_config(tenant_id, user[\"email\"], req.session_id)," in EXCERPTS["turn"][1]
assert "app.state.checkpointer = build_checkpointer(stack)" in EXCERPTS["lifespan"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
ag_src, br_src, fe_src = ((KIT / p).read_text(encoding="utf-8") for p in (AG, BR, FE))
req_cls = ag_src[ag_src.index("class ChatRequest(BaseModel):"):ag_src.index("def caller(")]
assert "model_config" not in req_cls and "tenant_id:" not in req_cls and "user_id:" not in req_cls      # extra keys ignored; no tenant, no person
saver_src = ag_src[ag_src.index("def build_checkpointer("):ag_src.index("def thread_config(")]
mem = saver_src[saver_src.index('if CHECKPOINT_DSN == "memory":'):saver_src.index("if not CHECKPOINT_DSN:")]
assert "raise" not in mem and "PROFILE" not in mem                                                       # memory is accepted, with a warning
deploy_sh = (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")
assert "--min-instances=0 --max-instances=10" in deploy_sh                                              # it scales to zero: restarts are routine
chat_reqs = (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8")
assert re.search(r"^google-adk==[\d.]+$", chat_reqs, re.M) and "sqlalchemy" not in chat_reqs.lower()    # ADK's sessions: memory
assert "st.session_state.session_id = uuid.uuid4().hex[:12]" in fe_src and 'brain = st.radio("Brain", BRAINS, index=0,' in fe_src
assert 'BRAINS = ("direct", "langchain", "langgraph", "adk")' in fe_src                                   # the radio starts on direct
assert "headers=_headers(CHAT_URL)" in fe_src
assert "IAP_AUDIENCE=/projects/$PROJECT_NUMBER/locations/${REGION:-us-central1}/services/documind-ui" in (KIT / "commands/lesson-12.4.sh").read_text(encoding="utf-8")
reqs = dict(re.findall(r"^([a-z-]+)==([\d.]+)$", chat_reqs, re.M))
PINS = {k: reqs[k] for k in ("langchain", "langchain-core", "requests", "google-auth", "fastapi")}
PINS.update({"cloud-sql-python-connector[pg8000]": "1.22.0", "pg8000": "1.31.5"})

# ------------------------------------------------------------------ the cells
VENV = ("[ -x ~/graph-venv/bin/python ] || python -m venv ~/graph-venv   # lesson 5.4's venv, made here if it is missing\n"
        "~/graph-venv/bin/pip install -q " + " ".join(f'"{k}=={v}"' for k, v in list(PINS.items())[:5]) + " \\\n"
        "  " + " ".join(f'"{k}=={v}"' for k, v in list(PINS.items())[5:]) + "   # the chat image's pins, and 6.6's connector\n"
        "~/graph-venv/bin/python -c 'import fastapi.testclient, google.cloud.sql.connector; print(\"graph-venv ok: fastapi\", fastapi.__version__)'")

ISO_PY = """import logging, os, sys, warnings
warnings.filterwarnings("ignore"); logging.disable(logging.CRITICAL)
os.environ.update(CHECKPOINT_DSN="memory", SELF_URL="https://documind-chat.example")   # the app's own start-up, in memory
sys.path[:0] = [".", "services/chat"]
from fastapi.testclient import TestClient
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from shared import iap
import agent, brains
class Recall(BaseChatModel):                       # a model that can answer only from the history it is sent
    @property
    def _llm_type(self): return "recall"
    def bind_tools(self, tools, **kw): return self
    def _generate(self, messages, stop=None, run_manager=None, **kw):
        asked = [str(m.content) for m in messages if m.type == "human"]
        text = ("Got it: saffron." if "Remember" in asked[-1] else "You asked me to remember saffron."
                if any("saffron" in a for a in asked[:-1]) else "I have no word from you in this conversation.")
        return ChatResult(generations=[ChatGeneration(message=AIMessage(text))])
PEOPLE = {"alice": ("alice@acme.example", "acme"), "bob": ("bob@acme.example", "acme"),
          "carol": ("carol@zeta.example", "zeta"), "outsider": ("outsider@example.com", None)}
def identity(headers, bearer_audience=None):       # stands in for the token check: the bearer names the person
    who = headers.get("authorization", "").removeprefix("Bearer ")
    if who not in PEOPLE:
        raise iap.IapError("the bearer token carries no verified email")
    return {"email": PEOPLE[who][0], "via": "iam", "aud": bearer_audience}
iap.identity, brains.build_llm = identity, Recall
agent.tenant_for = lambda email: next((t for e, t in PEOPLE.values() if e == email), None)   # stands in for the roster
def ask(c, who, question, session="lesson113", **extra):
    r = c.post("/v1/chat", headers={"Authorization": f"Bearer {who}"},
               json={"question": question, "session_id": session, "brain": "langchain", **extra})
    said = r.json().get("answer") or r.json().get("detail")
    return f"{r.status_code}  {said[0]['msg'] if isinstance(said, list) else said}"
WORD, ASK = "Remember this word for me: saffron.", "Which word did I ask you to remember?"
with TestClient(agent.app) as c:                   # one instance of the kit's chat service
    print(f"  alice gives the word, lesson113        {ask(c, 'alice', WORD)}")
    print(f"  alice asks for it                      {ask(c, 'alice', ASK)}")
    print(f"  alice, a new session                   {ask(c, 'alice', ASK, session='lesson113-b')}")
    print(f"  bob, her tenant, same session name     {ask(c, 'bob', ASK)}")
    print(f"  carol, another tenant, the same name   {ask(c, 'carol', ASK)}")
    print(f"  alice, the body naming zeta            {ask(c, 'alice', ASK, tenant_id='zeta')}")
    print(f"  alice, a session id with a colon       {ask(c, 'alice', ASK, session='lesson113:x')}")
    print(f"  the outsider                           {ask(c, 'outsider', ASK)}")
    print(f"  a token that names nobody              {ask(c, 'nobody', ASK)}")
    print("  the threads the checkpointer holds:")
    for t in sorted({t.config["configurable"]["thread_id"] for t in agent.app.state.checkpointer.list(None)}):
        print("    " + t)
with TestClient(agent.app) as c:                   # a restart: the lifespan builds a new checkpointer
    print(f"  after a restart, alice asks again      {ask(c, 'alice', ASK)}")"""

REDEPLOY_PY = """import json, os, subprocess, time, urllib.request
def text(answer):   # a chat service built before 24 September 2026 can send Gemini's content blocks instead of a string
    return answer if isinstance(answer, str) else "".join(p if isinstance(p, str) else p.get("text", "") for p in answer
                                                          if isinstance(p, str) or p.get("type") == "text")
P, R, CHAT = os.environ["PROJECT"], os.environ["REGION"], os.environ["CHAT"]
def gc(*a):
    return subprocess.run(["gcloud", *a, "--project", P, "--region", R, "--quiet"], capture_output=True, text=True, check=True).stdout.strip()
def serving():
    return gc("run", "services", "describe", "documind-chat", "--format", "value(status.latestReadyRevisionName)")
def ask(brain, session, question):
    req = urllib.request.Request(CHAT + "/v1/chat", method="POST",
                                 data=json.dumps({"question": question, "session_id": session, "brain": brain}).encode(),
                                 headers={"Authorization": "Bearer " + os.environ["CHAT_TOKEN"], "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        return " ".join(text(json.loads(r.read())["answer"]).split())
state = {"session": f"lesson113-{os.getpid()}", "before": serving()}
print(f"serving {state['before']}")
for brain in ("langchain", "adk"):
    said = ask(brain, f"{state['session']}-{brain}", "Remember this word for me: saffron. Just confirm you have it.")
    print(f"  {brain:9} {state['session']}-{brain:9}  {said[:44]!r}")
state["redeployed_at"] = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
gc("run", "services", "update", "documind-chat", "--update-env-vars", f"LESSON113_RESTART={int(time.time())}")   # a new revision
gc("run", "services", "update-traffic", "documind-chat", "--to-latest")
state["after"] = serving()
print(f"serving {state['after']}, redeployed at {state['redeployed_at']}Z")
for brain in ("langchain", "adk"):
    said = ask(brain, f"{state['session']}-{brain}", "Which word did I ask you to remember?")
    print(f"  {brain:9} {state['session']}-{brain:9}  saffron {'yes' if 'saffron' in said.lower() else 'no '}  {said[:34]!r}")
json.dump(state, open(os.path.expanduser("~/lesson113.json"), "w"))"""

UI_CELL = 'echo "open https://documind-ui-$NUMBER.$REGION.run.app and sign in as $ME"'

CONNECT = """import json, os, subprocess
from urllib.parse import unquote, urlparse
from google.cloud.sql.connector import Connector
gc = lambda *a: subprocess.run(["gcloud", *a, "--project", os.environ["PROJECT"]], capture_output=True, text=True, check=True).stdout.strip()
dsn = urlparse(gc("secrets", "versions", "access", "latest", "--secret", "documind-checkpoint-dsn"))   # the password stays in memory
instance = gc("sql", "instances", "describe", "documind-checkpoint", "--format", "value(connectionName)")
state = json.load(open(os.path.expanduser("~/lesson113.json")))
with Connector() as connector:
    db = connector.connect(instance, "pg8000", user=dsn.username, password=unquote(dsn.password), db=dsn.path.lstrip("/"))
    cur = db.cursor()
    def q(sql, *args):
        cur.execute(sql, args)                  # a tuple, empty or not: pg8000 takes len() of it, and None has none
        return cur.fetchall()
"""

ROWS_PY = CONNECT + """    for brain in ("langchain", "adk"):
        session = f"{state['session']}-{brain}"
        ts = [t for (t,) in q("SELECT checkpoint->>'ts' FROM checkpoints WHERE thread_id LIKE %s ORDER BY checkpoint_id", "%:" + session)]
        before = sum(t[:19] < state["redeployed_at"] for t in ts)
        print(f"  {session}: " + (f"{len(ts)} checkpoints, {before} before the redeploy and {len(ts) - before} after" if ts
                                  else "no rows - the ADK brain keeps none"))
    for person in (os.environ["ME"], "documind-ui-sa@"):
        rows = q("SELECT thread_id, count(*) FROM checkpoints WHERE thread_id LIKE %s GROUP BY thread_id ORDER BY max(checkpoint->>'ts') DESC",
                 f"%:{person}%")
        print(f"  threads of {person.split('@')[0]}: {len(rows)}" + (f"; the latest is session {rows[0][0].split(':', 2)[2]}, {rows[0][1]} checkpoints" if rows else ""))
    db.close()"""


def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "venv": VENV,
    "iso": heredoc(ISO_PY, python="~/graph-venv/bin/python"),
    "redeploy": 'export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"\n' + heredoc(REDEPLOY_PY, 'CHAT_TOKEN="$(tok "$CHAT")" '),
    "ui": UI_CELL,
    "rows": heredoc(ROWS_PY, python="~/graph-venv/bin/python"),
}

T = Path(tempfile.mkdtemp(prefix="lesson113-"))
HOME = T / "home"
HOME.mkdir()
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "REGION": "asia-south1",
       "ME": "you@example.com", "HOME": str(HOME), "USERPROFILE": str(HOME), "CHECKPOINT_DSN": ""}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.stdout[-800:], r.stderr[-1500:])
    return r.stdout


def reply(h, code: int, body) -> None:
    data = json.dumps(body, separators=(",", ":")).encode()
    h.send_response(code)
    h.send_header("Content-Type", "application/json")
    h.send_header("Content-Length", str(len(data)))
    h.end_headers()
    h.wfile.write(data)


# ---- step 3: the kit's own app under TestClient
OUT = {"iso": run_cell(ISO_PY, cwd=KIT)}
F = OUT["iso"]
got = dict(re.findall(r"^  (\S.*?)\s+(\d{3}  .*)$", F, re.M))
EXPECT = {"alice gives the word, lesson113": "200  Got it: saffron.", "alice asks for it": "200  You asked me to remember saffron.",
          "alice, a new session": "200  I have no word from you in this conversation.",
          "bob, her tenant, same session name": "200  I have no word from you in this conversation.",
          "carol, another tenant, the same name": "200  I have no word from you in this conversation.",
          "alice, the body naming zeta": "200  You asked me to remember saffron.",
          "the outsider": "403  not a member of any tenant", "a token that names nobody": "401  the bearer token carries no verified email",
          "after a restart, alice asks again": "200  I have no word from you in this conversation."}
for k, v in EXPECT.items():
    assert got.get(k) == v, (k, got.get(k), F)
assert got["alice, a session id with a colon"].startswith("422  String should match pattern"), F
assert "    acme:alice@acme.example:lesson113\n    acme:alice@acme.example:lesson113-b\n    acme:bob@acme.example:lesson113\n    zeta:carol@zeta.example:lesson113\n" in F, F
COLON = got["alice, a session id with a colon"][5:]
OUT["venv"] = f"graph-venv ok: fastapi {PINS['fastapi']}\n"

# ---- step 4: a stand-in chat service that keeps the LangChain thread across a redeploy and ADK's sessions in memory,
# and a fake gcloud whose update makes a new revision (and so empties the instances' memory)
STORE = {"graph": {}, "adk": {}, "revision": 7}


class Chat(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_POST(self):
        if self.path == "/__redeploy__":           # the fake gcloud's update: new instances, empty memory
            STORE["adk"].clear()
            STORE["revision"] += 1
            return reply(self, 200, {})
        req = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
        mem = STORE["graph" if req["brain"] in ("langchain", "langgraph") else "adk"].setdefault(req["session_id"], [])
        if "Remember" in req["question"]:
            answer = "Got it: saffron. I'll keep it for this conversation."
        elif any("saffron" in m for m in mem):
            answer = 'You asked me to remember "saffron".'
        else:
            answer = "I don't have a word from you in this conversation."
        mem.append(req["question"])
        reply(self, 200, {"answer": answer, "tool_calls": [], "refusals": [], "brain": req["brain"], "session_id": req["session_id"], "latency_ms": 3900})


chat = ThreadingHTTPServer(("127.0.0.1", 0), Chat)
threading.Thread(target=chat.serve_forever, daemon=True).start()
CHAT_URL = f"http://127.0.0.1:{chat.server_address[1]}"
SUFFIX = {7: "x4q", 8: "m2k"}
FAKE_GCLOUD = ("import json, sys, types, urllib.request\n"
               "class _Out:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               f"URL, SUFFIX = {CHAT_URL!r}, {json.dumps({str(k): v for k, v in SUFFIX.items()})}\n"
               "REV = [7]\n"
               "def run(cmd, **kw):\n"
               "    if cmd[1:4] == ['run', 'services', 'update']:\n"
               "        urllib.request.urlopen(urllib.request.Request(URL + '/__redeploy__', data=b'{}', method='POST')); REV[0] += 1\n"
               "    if cmd[1:4] == ['run', 'services', 'describe']:\n"
               "        return _Out(f'documind-chat-{REV[0]:05d}-{SUFFIX[str(REV[0])]}\\n')\n"
               "    return _Out('')\n"
               "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n"
               "import os; os.getpid = lambda: 4242\n")
OUT["redeploy"] = run_cell(REDEPLOY_PY, FAKE_GCLOUD, env={"CHAT": CHAT_URL, "CHAT_TOKEN": "TOKEN"})
chat.shutdown()
R4 = OUT["redeploy"]
assert "serving documind-chat-00007-x4q" in R4 and "serving documind-chat-00008-m2k, redeployed at" in R4, R4
assert re.search(r"langchain lesson113-4242-langchain  saffron yes", R4) and re.search(r"adk\s+lesson113-4242-adk\s+saffron no", R4), R4
STATE = json.loads((HOME / "lesson113.json").read_text(encoding="utf-8"))
assert STATE["session"] == "lesson113-4242" and STATE["before"] != STATE["after"], STATE
# the redeploy time on the page is the build's clock; fix it so the page does not change with every build
R4 = re.sub(r"redeployed at \d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ", "redeployed at 2026-09-23T11:20:41Z", R4)
OUT["redeploy"] = R4
STATE["redeployed_at"] = "2026-09-23T11:20:41"
OUT["ui"] = "open https://documind-ui-NUMBER.asia-south1.run.app and sign in as you@example.com\n"

# ---- step 6: a fake connector over rows shaped like the lane's after steps 4 and 5
(HOME / "lesson113.json").write_text(json.dumps(STATE), encoding="utf-8")
CK_LC = ["2026-09-23T11:19:58.1", "2026-09-23T11:19:58.9", "2026-09-23T11:20:02.4",
         "2026-09-23T11:21:37.2", "2026-09-23T11:21:37.8", "2026-09-23T11:21:41.0"]
FAKE_DB = ("import json, sys, types\n"
           f"CK = {CK_LC!r}\n"
           f"MINE = [['acme:you@example.com:3f9c2a1d0b7e', 3]]\n"
           f"UI = [['acme:{UI}:lesson113-4242-langchain', 6], ['acme:{UI}:lesson111-4242-b', 8]]\n"
           "class Cur:\n"
           "    def execute(self, sql, args=()):\n"
           "        len(args)                                   # as pg8000 1.31.5 does: None has no len(), and the cell must not send it\n"
           "        if sql.startswith(\"SELECT checkpoint->>'ts'\"): self.rows = [[t + '+00:00'] for t in CK] if args[0].endswith('-langchain') else []\n"
           "        elif sql.startswith('SELECT thread_id, count(*)'): self.rows = MINE if 'you@example.com' in args[0] else UI\n"
           "        else: raise AssertionError(sql)\n"
           "    def fetchall(self): return self.rows\n"
           "class Conn:\n    def cursor(self): return Cur()\n    def close(self): pass\n"
           "class Connector:\n"
           "    def __enter__(self): return self\n    def __exit__(self, *a): return False\n"
           "    def connect(self, instance, driver, **kw): return Conn()\n"
           "con = types.ModuleType('google.cloud.sql.connector'); con.Connector = Connector\n"
           "sys.modules['google.cloud.sql'] = types.ModuleType('google.cloud.sql'); sys.modules['google.cloud.sql.connector'] = con\n"
           "class _Out:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
           f"def run(cmd, **kw): return _Out('postgresql://chat:PASSWORD@/documind?host=/cloudsql/x' if cmd[1] == 'secrets' else '{PROJ}:asia-south1:documind-checkpoint')\n"
           "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT["rows"] = run_cell(ROWS_PY, FAKE_DB)
R6 = OUT["rows"]
assert "lesson113-4242-langchain: 6 checkpoints, 3 before the redeploy and 3 after" in R6 and "lesson113-4242-adk: no rows" in R6, R6
assert "threads of you: 1; the latest is session 3f9c2a1d0b7e" in R6 and "threads of documind-ui-sa: 2" in R6, R6
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "venv": "run in the operator shell, in the kit (lesson 5.4's venv, with the web layer and 6.6's connector)",
    "iso": "run in the operator shell, in the kit (the kit's chat app on your machine; no model, no network)",
    "redeploy": "run in the operator shell, in the kit (a word, a redeploy, the word again)",
    "ui": "run in the operator shell (the address of your UI)",
    "rows": "run in the operator shell, in the kit (the rows behind steps 4 and 5)",
}
OUT_LABELS = {
    "venv": "",
    "iso": "(this cell run on the kit's own agent.py and brains.py; every status and answer is the app's own)",
    "redeploy": "(against a local stand-in and a fake gcloud; the revision names, the time and the answers are invented)",
    "ui": "",
    "rows": "(from a fake connector over rows shaped like the lane's; your sessions and counts will differ)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: who can read the thread, and what survives
REQ = {
    "alice": {"label": "alice again, same session", "email": "alice@acme.example", "tenant": "acme", "session": "lesson113"},
    "alice-new": {"label": "alice, a new session", "email": "alice@acme.example", "tenant": "acme", "session": "lesson113-b"},
    "bob": {"label": "bob, her tenant, the same session name", "email": "bob@acme.example", "tenant": "acme", "session": "lesson113"},
    "carol": {"label": "carol, another tenant, the same name", "email": "carol@zeta.example", "tenant": "zeta", "session": "lesson113"},
    "alice-zeta": {"label": "alice, the body naming tenant zeta", "email": "alice@acme.example", "tenant": "acme", "session": "lesson113",
                   "note": "the tenant_id field is ignored; the roster decides"},
    "colon": {"label": "alice, session id lesson113:x", "status": 422, "detail": COLON},
    "outsider": {"label": "an account on no roster", "status": 403, "detail": "not a member of any tenant"},
    "nobody": {"label": "a token that names nobody", "status": 401, "detail": "the bearer token carries no verified email"},
}
STORES = {"postgres": "the lane: PostgresSaver on Cloud SQL", "memory": "CHECKPOINT_DSN=memory"}
BETWEEN = {"nothing": "nothing: the same instance answers", "restart": "the instance restarts", "redeploy": "a redeploy: a new revision"}
BRAINS = {"graph": "LangChain or LangGraph", "adk": "ADK", "direct": "direct"}
FIRST = "acme:alice@acme.example:lesson113"


def rule(req: str, store: str, between: str, brain: str) -> dict:
    """What the second turn finds, by the kit's rules: the door, the thread id, and the store behind the brain."""
    r = REQ[req]
    if "status" in r:
        return {"status": str(r["status"]), "thread": "none: refused before any brain", "finds": "nothing", "why": r["detail"]}
    thread = f"{r['tenant']}:{r['email']}:{r['session']}"
    if brain == "direct":
        return {"status": "200", "thread": thread, "finds": "nothing", "why": "the direct brain keeps no history"}
    kept = between == "nothing" or (store == "postgres" and brain == "graph")
    same = thread == FIRST
    why = ("another thread: " + ("another session" if r["email"] == "alice@acme.example" else "another person" if r["tenant"] == "acme" else "another tenant")
           if not same else "the thread is gone: " + ("ADK keeps its sessions in memory on this image" if brain == "adk" else "the checkpointer was in memory")
           if not kept else "the same thread, still held" + (" (" + r["note"] + ")" if r.get("note") else ""))
    return {"status": "200", "thread": thread, "finds": "the word" if same and kept else "nothing", "why": why}


# the rule against the offline run: the memory checkpointer, the LangChain brain, the same instance and after a restart
ran = {"alice": "alice asks for it", "alice-new": "alice, a new session", "bob": "bob, her tenant, same session name",
       "carol": "carol, another tenant, the same name", "alice-zeta": "alice, the body naming zeta", "colon": "alice, a session id with a colon",
       "outsider": "the outsider", "nobody": "a token that names nobody"}
for key, line in ran.items():
    o = rule(key, "memory", "nothing", "graph")
    assert got[line].startswith(o["status"]) and (("saffron" in got[line]) == (o["finds"] == "the word")), (key, o, got[line])
assert rule("alice", "memory", "restart", "graph")["finds"] == "nothing" and "no word" in got["after a restart, alice asks again"]
assert rule("alice", "postgres", "redeploy", "graph")["finds"] == "the word" and rule("alice", "postgres", "redeploy", "adk")["finds"] == "nothing"

UI_JS = r"""var root = document.getElementById('ri'); if (!root) return;
  var REQ = %s, OPT = {req: REQ, store: %s, between: %s, brain: %s}, FIRST = %s, $ = function(id){ return document.getElementById(id); };
  function rule(req, store, between, brain){ var r = REQ[req];
    if (r.status) { return {status: String(r.status), thread: 'none: refused before any brain', finds: 'nothing', why: r.detail}; }
    var thread = r.tenant + ':' + r.email + ':' + r.session;
    if (brain === 'direct') { return {status: '200', thread: thread, finds: 'nothing', why: 'the direct brain keeps no history'}; }
    var kept = between === 'nothing' || (store === 'postgres' && brain === 'graph'), same = thread === FIRST;
    var why = !same ? 'another thread: ' + (r.email === 'alice@acme.example' ? 'another session' : r.tenant === 'acme' ? 'another person' : 'another tenant')
      : !kept ? 'the thread is gone: ' + (brain === 'adk' ? 'ADK keeps its sessions in memory on this image' : 'the checkpointer was in memory')
      : 'the same thread, still held' + (r.note ? ' (' + r.note + ')' : '');
    return {status: '200', thread: thread, finds: same && kept ? 'the word' : 'nothing', why: why}; }
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
  function render(){ var o = rule($('ri-req').value, $('ri-store').value, $('ri-between').value, $('ri-brain').value), out = $('ri-out');
    out.textContent = '';
    [['Status', o.status], ['Thread', o.thread], ['Turn 2 finds', o.finds], ['Why', o.why]].forEach(function(r){
      out.appendChild(el('b', '', r[0])); out.appendChild(el('span', r[0] === 'Turn 2 finds' && o.finds === 'the word' ? 'yes' : '', r[1])); }); }
  Object.keys(OPT).forEach(function(k){ var s = $('ri-' + k);
    Object.keys(OPT[k]).forEach(function(v){ var o = el('option', '', k === 'req' ? OPT[k][v].label : OPT[k][v]); o.value = v; s.appendChild(o); });
    s.addEventListener('change', render); });
  $('ri-between').value = 'redeploy'; render();""" % (json.dumps(REQ), json.dumps(STORES), json.dumps(BETWEEN), json.dumps(BRAINS), json.dumps(FIRST))

# the page's rule against this file's, for every choice
JS_RULE = re.search(r"(function rule\(req, store, between, brain\)\{.*?return \{status: '200', thread: thread, finds: same && kept \? 'the word' : 'nothing', why: why\}; \})", UI_JS, re.S).group(1)
cases = [(a, b, c, d) for a in REQ for b in STORES for c in BETWEEN for d in BRAINS]
node = subprocess.run(["node", "-e", f"var REQ = {json.dumps(REQ)}, FIRST = {json.dumps(FIRST)};\n{JS_RULE}\n"
                       f"console.log(JSON.stringify({json.dumps(cases)}.map(function(c){{ return rule(c[0], c[1], c[2], c[3]); }})));"],
                      capture_output=True, text=True, check=True)
for c, js in zip(cases, json.loads(node.stdout)):
    assert js == rule(*c), (c, js, rule(*c))

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"N_CASES": str(len(cases)), "COLON": html.escape(COLON, quote=False)}

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
print(f"kit: the chat app's statuses and answers under TestClient, its own | the widget's rule checked against the run and, with node,"
      f" against this file's for {len(cases)} choices | live cells against stand-ins")
