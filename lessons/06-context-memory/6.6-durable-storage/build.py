"""Build lesson 6.6 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Durable conversation storage: what holds a conversation, and what is inside. The pieces: terraform/cloudsql.tf's
instance, database, user and DSN secret; the service's mount; migrate.py's one-off setup() job; agent.py's pool. What a
turn writes: a checkpoint row per step and, for the messages channel, the whole list again at every new version. The
ADK brain asks for a database store too, and cannot open one: the image installs google-adk without its db extra, so
brains.py falls back to memory. Offline in ~/graph-venv: two turns of the kit's LangChain brain against the checkpointer
interface PostgresSaver shares, their checkpoints and message versions counted, and the ADK brain's fallback. Live: the
configuration the lane runs (instance, backups, network, secret, the setup job's image against the service's, the ADK
fallback in the log); the tables, their rows and one row per thread, through the Cloud SQL Python Connector; and the
latest thread, step by step.

Build-time proof: the offline cell runs here on the kit's brains.py, with google-adk 2.8.0 and no SQLAlchemy, as the
chat image has them. The live cells run against stand-ins: a fake gcloud, and a fake database connection that answers
the page's SQL from threads the kit's own brains wrote at build time, counted the way the tables count them.
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "6.6"
title = "<title>Lesson 6.6 Configure and inspect durable conversation storage - the tables, one row per thread, and what every turn adds | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin-bottom:4px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,13em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid .big{font-family:var(--mono);color:var(--teal-dark);font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
TF, MIG, AG, BR = "terraform/cloudsql.tf", "services/chat/migrate.py", "services/chat/agent.py", "services/chat/brains.py"
EXCERPTS = {
    "instance": ("terraform/cloudsql.tf - the instance: the cheapest Cloud SQL there is, reached only through the connector",
                 block(TF, 'resource "google_sql_database_instance" "checkpoint" {', n=20)),
    "migrate": ("services/chat/migrate.py - the tables are made once, by a job, never at start-up",
                block(MIG, "`PostgresSaver.setup()` is idempotent", n=6) + "\n...\n" + block(MIG, 'dsn = os.environ.get("CHECKPOINT_DSN", "")', n=7)),
    "pool": ("services/chat/agent.py - one pool per instance, opened at start-up, and no setup()",
             block(AG, "    from langgraph.checkpoint.postgres import PostgresSaver", n=10)),
    "sessions": ("services/chat/brains.py - the ADK brain asks for a database store, and falls back to memory",
                 block(BR, "    def _sessions():", n=11)),
}
assert 'ipv4_enabled = true # reached only through the connector; no authorized_networks, on purpose' in EXCERPTS["instance"][1]
assert "saver.setup()" in EXCERPTS["migrate"][1] and "ACCESS EXCLUSIVE" in EXCERPTS["migrate"][1]
assert "min_size=1, max_size=4" in EXCERPTS["pool"][1] and "setup() deliberately absent" in EXCERPTS["pool"][1]
assert 'logger.warning("ADK DatabaseSessionService unavailable (%s); using memory", exc)' in EXCERPTS["sessions"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
tf_src, ag_src, br_src = ((KIT / p).read_text(encoding="utf-8") for p in (TF, AG, BR))
for fact in ('database_version    = "POSTGRES_16"', 'tier              = "db-f1-micro"', 'availability_type = "ZONAL"', "disk_size         = 10",
             "enabled = false # checkpoints, not customer documents", "deletion_protection = false", 'name     = "documind"', 'name     = "chat"',
             'secret_id = "documind-checkpoint-dsn"', 'role      = "roles/secretmanager.secretAccessor"', 'role    = "roles/cloudsql.client"',
             "roughly $8-10 (Rs 700-850) a month"):
    assert fact in tf_src, fact
assert "authorized_networks {" not in tf_src
deploy_sh = (KIT / "commands/lesson-12.8.sh").read_text(encoding="utf-8")
assert re.search(r"gcloud run jobs create documind-checkpoint-setup \\\n(.*\n)*?.*--command=python --args=migrate.py \|\| echo \"job exists - continuing\"", deploy_sh)
assert "gcloud run jobs execute documind-checkpoint-setup" in deploy_sh
assert not re.search(r"jobs (update|deploy) documind-checkpoint-setup", deploy_sh)                      # the job keeps its first image
reqs_txt = (KIT / "services/chat/requirements.txt").read_text(encoding="utf-8")
assert re.search(r"^google-adk==2\.8\.0$", reqs_txt, re.M) and "sqlalchemy" not in reqs_txt.lower()         # no db extra, no SQLAlchemy
assert "DatabaseSessionService on the same Cloud SQL when CHECKPOINT_DSN is set" in br_src                  # what brains.py's docstring says
assert "12.1" and "sqladmin.googleapis.com" in (KIT / "commands/lesson-12.1.sh").read_text(encoding="utf-8")
assert 'if not dsn or dsn == "memory":' in (KIT / MIG).read_text(encoding="utf-8")
reqs = dict(re.findall(r"^([a-z-]+)==([\d.]+)$", reqs_txt, re.M))
assert reqs["langgraph-checkpoint-postgres"] == "3.1.2"
MIGRATIONS = 10                                    # langgraph-checkpoint-postgres 3.1.2's MIGRATIONS list, read 23 September 2026
PINS = {k: reqs[k] for k in ("langchain", "langchain-core", "requests", "google-auth", "google-adk")}
PINS.update({"cloud-sql-python-connector[pg8000]": "1.22.0", "pg8000": "1.31.5"})

# ------------------------------------------------------------------ the cells
VENV = ("[ -x ~/graph-venv/bin/python ] || python -m venv ~/graph-venv   # lesson 5.4's venv, made here if it is missing\n"
        "~/graph-venv/bin/pip install -q " + " ".join(f'"{k}=={v}"' for k, v in list(PINS.items())[:5]) + " \\\n"
        "  " + " ".join(f'"{k}=={v}"' for k, v in list(PINS.items())[5:]) + "   # the chat image's pins, and the Cloud SQL connector\n"
        "~/graph-venv/bin/python -c 'import google.cloud.sql.connector as c, pg8000; print(\"graph-venv ok: connector\", c.__version__)'")

STORE_PY = """import logging, os, sys, warnings
warnings.filterwarnings("ignore")
logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s", stream=sys.stdout)
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
import shared.documind_tools as dt
import brains
QUOTE = ("Gratuity shall be payable to an employee on the termination of his employment after he has rendered "
         "continuous service for not less than five years, on his superannuation, or on his retirement or resignation.")
dt.retrieve = lambda query, **kw: {"answerable": True, "confidence": "high", "citations": [   # five passages, no network
    {"chunk_id": f"acme:payment_of_gratuity_act_1972#{4 + i}", "quote": QUOTE, "score": 0.9} for i in range(5)]}
class Script(FakeMessagesListChatModel):           # a model that says what it is told
    def bind_tools(self, tools, **kw): return self
saver = InMemorySaver()                            # PostgresSaver's interface: a row per checkpoint, a blob per new version
thread = {"configurable": {"thread_id": "acme:you@example.com:lesson112"}}
def turn(question, tool):                          # one turn of the kit's LangChain brain, with or without retrieve
    said = [AIMessage("", tool_calls=[{"name": "retrieve", "args": {"query": question}, "id": "c1"}])] if tool else []
    brains.LangChainBrain(saver, llm=Script(responses=said + [AIMessage("Five years of continuous service [1].")])).answer(
        question, config=thread, context={"tenant_id": "acme", "brain": "langchain"})
def kept():                                        # the thread's checkpoints, and each version of messages they stored
    cps, versions = list(saver.list(thread))[::-1], {}
    for c in cps:
        v = c.checkpoint["channel_versions"].get("messages")
        if v and v not in versions:
            msgs = c.checkpoint["channel_values"]["messages"]
            versions[v] = (len(msgs), len(saver.serde.dumps_typed(msgs)[1]))
    return cps, versions
done = (0, 0)
for question, tool in (("Remember this word for me: tamarind.", False), ("After how many years is gratuity payable?", True)):
    turn(question, tool)
    cps, versions = kept()
    print(f"a turn {'with retrieve' if tool else 'with no tool':14} +{len(cps) - done[0]} checkpoints, +{len(versions) - done[1]} versions of messages")
    done = (len(cps), len(versions))
print("the messages channel, every version kept:")
for i, (n, size) in enumerate(versions.values(), 1):
    print(f"   version {i}  {n} message{'s' if n > 1 else ' '}  {size:>6,} bytes")
sizes = [size for _, size in versions.values()]
print(f"   {sum(sizes):,} bytes kept, for a conversation whose latest version is {sizes[-1]:,} bytes")
print("the ADK brain, given the lane's DSN, with google-adk and no SQLAlchemy - as the chat image has them:")
os.environ["CHECKPOINT_DSN"] = "postgresql://chat:PASSWORD@/documind?host=/cloudsql/PROJECT:REGION:documind-checkpoint"
print(f"   it keeps its sessions in {type(brains.AdkBrain._sessions()).__name__}")"""

CONF_PY = """import json, os, subprocess
def gc(*args):
    r = subprocess.run(["gcloud", *args, "--project", os.environ["PROJECT"], "--format", "json"], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 and r.stdout.strip() else None
i = gc("sql", "instances", "describe", "documind-checkpoint")
s, ip = i["settings"], i["settings"].get("ipConfiguration", {})
print(f"  instance      {i['name']}: {i['databaseVersion']}, {s['tier']}, {s['availabilityType'].lower()}, {s['dataDiskSizeGb']} GB")
print(f"  backups       {'on' if s.get('backupConfiguration', {}).get('enabled') else 'off'}")
print(f"  network       public IP {'on' if ip.get('ipv4Enabled') else 'off'}, {len(ip.get('authorizedNetworks', []))} authorized networks")
print(f"  databases     {', '.join(d['name'] for d in gc('sql', 'databases', 'list', '--instance', i['name']))}")
print(f"  users         {', '.join(u['name'] for u in gc('sql', 'users', 'list', '--instance', i['name']))}")
v = gc("secrets", "versions", "list", "documind-checkpoint-dsn") or []
print(f"  the DSN       secret documind-checkpoint-dsn, {len(v)} version(s), the latest {v[0]['state'].lower() if v else 'missing'}")
tag = lambda image: image.rsplit(":", 1)[-1][:12]
job = gc("run", "jobs", "describe", "documind-checkpoint-setup", "--region", os.environ["REGION"])
svc = gc("run", "services", "describe", "documind-chat", "--region", os.environ["REGION"])
if job and svc:
    ran = (gc("run", "jobs", "executions", "list", "--job", "documind-checkpoint-setup", "--region", os.environ["REGION"], "--limit", "1") or [{}])[0]
    ji, si = job["spec"]["template"]["spec"]["template"]["spec"]["containers"][0]["image"], svc["spec"]["template"]["spec"]["containers"][0]["image"]
    print(f"  setup job     last run {ran.get('metadata', {}).get('creationTimestamp', 'never')[:16]}, succeeded {ran.get('status', {}).get('succeededCount', 0)}")
    print(f"  images        job chat:{tag(ji)}, service chat:{tag(si)} - {'the same' if ji == si else 'DIFFERENT'}")
else:
    print(f"  setup job     not found beside documind-chat in {os.environ['REGION']}")
adk = subprocess.run(["gcloud", "logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" '
                      'AND textPayload:"DatabaseSessionService unavailable"', "--project", os.environ["PROJECT"], "--freshness", "30d",
                      "--limit", "1", "--format", "value(textPayload)"], capture_output=True, text=True).stdout.strip()
print("  ADK sessions  " + ("in memory: " + adk[:62] if adk else "no fallback warning in 30 days of the log"))"""

CONNECT = """import os, subprocess
from urllib.parse import unquote, urlparse
from google.cloud.sql.connector import Connector
gc = lambda *a: subprocess.run(["gcloud", *a, "--project", os.environ["PROJECT"]], capture_output=True, text=True, check=True).stdout.strip()
dsn = urlparse(gc("secrets", "versions", "access", "latest", "--secret", "documind-checkpoint-dsn"))   # the password stays in memory
instance = gc("sql", "instances", "describe", "documind-checkpoint", "--format", "value(connectionName)")
with Connector() as connector:
    db = connector.connect(instance, "pg8000", user=dsn.username, password=unquote(dsn.password), db=dsn.path.lstrip("/"))
    cur = db.cursor()
    def q(sql, *args):
        cur.execute(sql, args)                  # a tuple, empty or not: pg8000 takes len() of it, and None has none
        return cur.fetchall()
"""

TABLES_PY = CONNECT + """    tables = [t for (t,) in q("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public' ORDER BY table_name")]
    print(f"{instance}, database {dsn.path.lstrip('/')}, as {dsn.username}: {len(tables)} tables")
    for t in tables:
        print(f"  {t:22} {q(f'SELECT count(*) FROM {t}')[0][0]:>6,} rows")
    print(f"setup() has applied migrations 0 to {q('SELECT max(v) FROM checkpoint_migrations')[0][0]}")
    print("one row per thread, the latest first:")
    for thread, n, step, ts in q("SELECT thread_id, count(*), max((metadata->>'step')::int), max(checkpoint->>'ts') "
                                 "FROM checkpoints GROUP BY thread_id ORDER BY 4 DESC LIMIT 12"):
        tenant, person, session = thread.split(":", 2)
        print(f"  {tenant:5} {person.split('@')[0][:15]:15} {session[:18]:18} {n:>3} checkpoints  step {step:>2}  {ts[:16]}")
    if "sessions" not in tables:
        print("no ADK tables: the ADK brain's sessions are not in this database")
    db.close()"""

THREAD_PY = CONNECT + """    (thread,) = q("SELECT thread_id FROM checkpoints GROUP BY thread_id ORDER BY max(checkpoint->>'ts') DESC LIMIT 1")[0]
    size = dict(q("SELECT version, length(blob) FROM checkpoint_blobs WHERE thread_id = %s AND channel = 'messages'", thread))
    print(f"the latest thread, session {thread.split(':', 2)[2]}: its checkpoints in order")
    seen = []
    for step, source, version in q("SELECT (metadata->>'step')::int, metadata->>'source', checkpoint->'channel_versions'->>'messages' "
                                   "FROM checkpoints WHERE thread_id = %s ORDER BY checkpoint_id", thread):
        new = version is not None and version not in seen
        seen += [version] if new else []
        print(f"  step {step:>2}  {source:5}  " + (f"messages, version {len(seen)}: {size[version]:>6,} bytes" if new else "messages unchanged"))
    print(f"every version kept: {sum(size.values()):,} bytes; the latest alone: {size[max(size)]:,} bytes")
    db.close()"""


def heredoc(body: str, prefix: str = "", python: str = "python") -> str:
    return f"{prefix}{python} - <<'PY'\n{body}\nPY"


CELLS = {
    "venv": VENV,
    "store": heredoc(STORE_PY, python="~/graph-venv/bin/python"),
    "conf": heredoc(CONF_PY),
    "tables": heredoc(TABLES_PY, python="~/graph-venv/bin/python"),
    "thread": heredoc(THREAD_PY, python="~/graph-venv/bin/python"),
}

T = Path(tempfile.mkdtemp(prefix="lesson112-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ,
       "REGION": "asia-south1", "CHECKPOINT_DSN": ""}


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.stdout[-800:], r.stderr[-1500:])
    return r.stdout


# ---- step 3: the offline cell, verbatim, on the kit (google-adk 2.8.0 and no SQLAlchemy here, as in the chat image)
OUT = {"store": run_cell(STORE_PY, cwd=KIT)}
F = OUT["store"]
assert "a turn with no tool   +3 checkpoints, +2 versions of messages" in F and "a turn with retrieve  +5 checkpoints, +4 versions of messages" in F, F
VSIZE = [int(x.replace(",", "")) for x in re.findall(r"^   version \d  \d messages?\s+([\d,]+) bytes$", F, re.M)]
assert len(VSIZE) == 6 and VSIZE == sorted(VSIZE), F
assert re.search(r"WARNING documind\.chat\.brains: ADK DatabaseSessionService unavailable \(The 'sqlalchemy' package is required.*\); using memory", F), F
assert F.rstrip().endswith("it keeps its sessions in InMemorySessionService"), F
ADK_WARN = re.search(r"WARNING documind\.chat\.brains: (ADK DatabaseSessionService unavailable .*; using memory)", F).group(1)
OUT["venv"] = f"graph-venv ok: connector {PINS['cloud-sql-python-connector[pg8000]']}\n"
# the widget's sizes: what each message adds to the list (turn 2's question, tool call, tool result and answer)
INC = {"H": VSIZE[2] - VSIZE[1], "C": VSIZE[3] - VSIZE[2], "T": VSIZE[4] - VSIZE[3], "A": VSIZE[5] - VSIZE[4]}
assert INC["T"] == max(INC.values()) and min(INC.values()) > 0, INC

# ---- step 4: the configuration, from a fake gcloud answering as the lane does
FAKE = {
    ("sql", "instances", "describe"): {"name": "documind-checkpoint", "databaseVersion": "POSTGRES_16", "connectionName": f"{PROJ}:asia-south1:documind-checkpoint",
                                       "settings": {"tier": "db-f1-micro", "edition": "ENTERPRISE", "availabilityType": "ZONAL", "dataDiskSizeGb": "10",
                                                    "backupConfiguration": {"enabled": False}, "ipConfiguration": {"ipv4Enabled": True}}},
    ("sql", "databases", "list"): [{"name": "postgres"}, {"name": "documind"}],
    ("sql", "users", "list"): [{"name": "chat"}, {"name": "postgres"}],
    ("secrets", "versions", "list"): [{"name": f"projects/NUMBER/secrets/documind-checkpoint-dsn/versions/1", "state": "ENABLED"}],
    ("run", "jobs", "describe"): {"spec": {"template": {"spec": {"template": {"spec": {"containers": [{"image": f"us-central1-docker.pkg.dev/{PROJ}/documind/chat:3f9c2a1d0b7e"}]}}}}}},
    ("run", "services", "describe"): {"spec": {"template": {"spec": {"containers": [{"image": f"asia-south1-docker.pkg.dev/{PROJ}/documind/chat:8e41d7c2f5a9"}]}}}},
    ("run", "jobs", "executions"): [{"metadata": {"name": "documind-checkpoint-setup-x7k2p", "creationTimestamp": "2026-09-12T10:41:07Z"}, "status": {"succeededCount": 1}}],
}
FAKE_GCLOUD = ("import json, sys, types\n"
               "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
               f"FAKE = {{tuple(k.split('|')): v for k, v in json.loads({json.dumps(json.dumps({'|'.join(k): v for k, v in FAKE.items()}))}).items()}}\n"
               f"WARN = {ADK_WARN!r}\n"
               "def run(cmd, **kw):\n"
               "    if cmd[1:3] == ['logging', 'read']: return R(WARN + '\\n')\n"
               "    return R(json.dumps(FAKE[tuple(cmd[1:4])]))\n"
               "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT["conf"] = run_cell(CONF_PY, FAKE_GCLOUD)
assert "backups       off" in OUT["conf"] and "public IP on, 0 authorized networks" in OUT["conf"] and "DIFFERENT" in OUT["conf"], OUT["conf"]
assert "ADK sessions  in memory: ADK DatabaseSessionService unavailable" in OUT["conf"], OUT["conf"]

# ---- steps 5 and 6: a stand-in lane - the threads your lane would hold, written by the kit's own brains at build time -
# and a fake connector whose cursor answers the page's SQL from them, counted the way the tables count them
LANE = f"""import json, sys, warnings
warnings.filterwarnings("ignore")
sys.path[:0] = [".", "services/chat"]
from langchain_core.language_models.fake_chat_models import FakeMessagesListChatModel
from langchain_core.messages import AIMessage
from langgraph.checkpoint.memory import InMemorySaver
import shared.documind_tools as dt
import brains
dt.retrieve = lambda query, **kw: {{"answerable": True, "confidence": "high", "citations": [
    {{"chunk_id": f"acme:payment_of_gratuity_act_1972#{{4 + i}}", "quote": "Gratuity shall be payable to an employee on the termination of his employment after he has rendered continuous service for not less than five years.", "score": 0.9}} for i in range(5)]}}
class Script(FakeMessagesListChatModel):
    def bind_tools(self, tools, **kw): return self
saver = InMemorySaver()
THREADS = [("lesson103", [("langchain", True)]), ("smoke-langchain", [("langchain", True)]), ("smoke-langgraph", [("langgraph", True)]),
           ("lesson111-4242", [("langchain", False), ("langgraph", False)]), ("lesson111-4242-b", [("langchain", False), ("langchain", True)])]
TS = {{"lesson103": "2026-09-23T08:41", "smoke-langchain": "2026-09-23T09:15", "smoke-langgraph": "2026-09-23T09:16",
       "lesson111-4242": "2026-09-23T10:02", "lesson111-4242-b": "2026-09-23T10:03"}}
out = {{"threads": [], "blobs": 0, "writes": 0, "latest": None}}
for session, turns in THREADS:
    cfg = {{"configurable": {{"thread_id": "acme:{UI}:" + session}}}}
    for brain, tool in turns:
        said = [AIMessage("", tool_calls=[{{"name": "retrieve", "args": {{"query": "gratuity"}}, "id": "c1"}}])] if tool else []
        cls = brains.LangChainBrain if brain == "langchain" else brains.LangGraphBrain
        cls(saver, llm=Script(responses=said + [AIMessage("Five years [1].")])).answer("q", config=cfg, context={{"tenant_id": "acme", "brain": brain}})
    cps = list(saver.list(cfg))[::-1]
    seen, rows, sizes = set(), [], {{}}
    for c in cps:
        vals, vers = c.checkpoint["channel_values"], c.checkpoint["channel_versions"]
        for ch, v in vers.items():                 # a blob per new version of a value that is not a scalar, as PostgresSaver writes them
            if (ch, v) not in seen and ch in vals and not isinstance(vals[ch], (str, int, float, bool, type(None))):
                seen.add((ch, v)); out["blobs"] += 1
                if ch == "messages":
                    sizes[v] = len(saver.serde.dumps_typed(vals[ch])[1])
        out["writes"] += len(c.pending_writes or [])
        rows.append([c.metadata["step"], c.metadata["source"], vers.get("messages")])
    out["threads"].append([cfg["configurable"]["thread_id"], len(cps), max(r[0] for r in rows), TS[session] + ":07.123456+00:00"])
    out["latest"] = {{"thread": cfg["configurable"]["thread_id"], "rows": rows, "sizes": sizes}}
out["checkpoints"] = sum(t[1] for t in out["threads"])
print(json.dumps(out))
"""
LANE_DATA = json.loads(run_cell(LANE, cwd=KIT))
LANE_DATA["threads"].sort(key=lambda t: t[3], reverse=True)
COUNTS = {"checkpoint_blobs": LANE_DATA["blobs"], "checkpoint_migrations": MIGRATIONS, "checkpoint_writes": LANE_DATA["writes"], "checkpoints": LANE_DATA["checkpoints"]}
FAKE_DB = ("import json, sys, types\n"
           f"D = json.loads({json.dumps(json.dumps({'counts': COUNTS, 'threads': LANE_DATA['threads'], 'latest': LANE_DATA['latest'], 'mig': MIGRATIONS - 1}))})\n"
           "class Cur:\n"
           "    def execute(self, sql, args=()):\n"
           "        len(args)                                   # as pg8000 1.31.5 does: None has no len(), and the cell must not send it\n"
           "        if 'information_schema.tables' in sql: self.rows = [[t] for t in sorted(D['counts'])]\n"
           "        elif sql.startswith('SELECT count(*) FROM '): self.rows = [[D['counts'][sql.split()[-1]]]]\n"
           "        elif 'max(v)' in sql: self.rows = [[D['mig']]]\n"
           "        elif sql.startswith('SELECT thread_id, count(*)'): self.rows = D['threads']\n"
           "        elif sql.startswith('SELECT thread_id FROM checkpoints'): self.rows = [[D['latest']['thread']]]\n"
           "        elif 'checkpoint_blobs WHERE' in sql: self.rows = list(D['latest']['sizes'].items())\n"
           "        elif \"metadata->>'source'\" in sql: self.rows = D['latest']['rows']\n"
           "        else: raise AssertionError(sql)\n"
           "    def fetchall(self): return self.rows\n"
           "class Conn:\n    def cursor(self): return Cur()\n    def close(self): pass\n"
           "class Connector:\n"
           "    def __enter__(self): return self\n    def __exit__(self, *a): return False\n"
           "    def connect(self, instance, driver, **kw):\n"
           "        assert driver == 'pg8000' and kw == {'user': 'chat', 'password': 'PASSWORD', 'db': 'documind'}, kw\n"
           "        return Conn()\n"
           "sql = types.ModuleType('google.cloud.sql'); con = types.ModuleType('google.cloud.sql.connector'); con.Connector = Connector\n"
           "sys.modules['google.cloud.sql'] = sql; sys.modules['google.cloud.sql.connector'] = con\n"
           "class R:\n    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, '', 0\n"
           f"def run(cmd, **kw): return R('postgresql://chat:PASSWORD@/documind?host=/cloudsql/{PROJ}:asia-south1:documind-checkpoint' if cmd[1] == 'secrets' else '{PROJ}:asia-south1:documind-checkpoint')\n"
           "fake = types.ModuleType('subprocess'); fake.run = run; sys.modules['subprocess'] = fake\n")
OUT["tables"] = run_cell(TABLES_PY, FAKE_DB)
OUT["thread"] = run_cell(THREAD_PY, FAKE_DB)
TB, TH = OUT["tables"], OUT["thread"]
assert f"setup() has applied migrations 0 to {MIGRATIONS - 1}" in TB and "no ADK tables" in TB and "PASSWORD" not in TB + TH, TB
per_thread = re.findall(r"^  acme  documind-ui-sa\s+(\S+)\s+(\d+) checkpoints  step\s+(\d+)", TB, re.M)
assert [p[0] for p in per_thread] == ["lesson111-4242-b", "lesson111-4242", "smoke-langgraph", "smoke-langchain", "lesson103"], per_thread
assert dict((p[0], int(p[1])) for p in per_thread) == {"lesson111-4242-b": 8, "lesson111-4242": 6, "smoke-langgraph": 5, "smoke-langchain": 5, "lesson103": 5}, per_thread
assert "the latest thread, session lesson111-4242-b" in TH and TH.count("messages, version") == 6 and "messages, version 6:" in TH, TH
assert TH.count("messages unchanged") == 2, TH
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "venv": "run in the operator shell, in the kit (lesson 5.4's venv, with the Cloud SQL connector added)",
    "store": "run in the operator shell, in the kit (two turns, their checkpoints and versions counted; no model, no network)",
    "conf": "run in the operator shell, in the kit (what holds the conversations on your lane)",
    "tables": "run in the operator shell, in the kit (the tables, their rows, and one row per thread)",
    "thread": "run in the operator shell, in the kit (the latest thread, step by step)",
}
OUT_LABELS = {
    "venv": "",
    "store": "(this cell run on the kit's own brains.py, with google-adk 2.8.0 and no SQLAlchemy; the sizes are the installed LangChain's)",
    "conf": "(from a fake gcloud; the image tags and the time are invented)",
    "tables": "(from a stand-in database: threads the kit's brains wrote at build time, as your lane's lessons did, counted the way the tables count them; the times are invented)",
    "thread": "(from the same stand-in; your latest thread, sizes and versions will differ)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})


# ------------------------------------------------------------------ the widget: what keeping every version costs
def model(turns: int, tools: int, per_day: int, days: int) -> dict:
    """The widget's arithmetic: each message adds its size to the list, and each new version stores the whole list."""
    pattern = [INC["H"]] + [INC["C"], INC["T"]] * tools + [INC["A"]]
    cum = total = 0
    for _ in range(turns):
        for s in pattern:
            cum += s
            total += cum
    return {"ck": turns * (3 + 2 * tools), "ver": turns * (2 + 2 * tools), "all": total, "latest": cum, "gb": per_day * days * total / 1e9}


OPTS = {"turns": [1, 5, 10, 20, 40], "tools": [0, 1, 2], "day": [50, 200, 1000], "days": [30, 90, 365]}
UI_JS = r"""var root = document.getElementById('ds'); if (!root) return;
  var INC = %s, O = %s, $ = function(id){ return document.getElementById(id); };
  function model(turns, tools, perDay, days){ var pattern = [INC.H], i, t, cum = 0, total = 0;
    for (i = 0; i < tools; i++) { pattern.push(INC.C, INC.T); } pattern.push(INC.A);
    for (t = 0; t < turns; t++) { for (i = 0; i < pattern.length; i++) { cum += pattern[i]; total += cum; } }
    return {ck: turns * (3 + 2 * tools), ver: turns * (2 + 2 * tools), all: total, latest: cum, gb: perDay * days * total / 1e9}; }
  function n(x){ return Math.round(x).toLocaleString('en-IN'); }
  function kb(x){ return x < 1e3 ? n(x) + ' bytes' : x < 1e6 ? n(x / 1e3) + ' KB' : (x / 1e6).toFixed(1) + ' MB'; }
  function gb(x){ return x < 1 ? n(x * 1000) + ' MB' : x < 100 ? x.toFixed(1) + ' GB' : n(x) + ' GB'; }
  function disk(x, days){ if (x < 10) { return x * 10 < 1 ? 'under 1 per cent' : Math.round(x * 10) + ' per cent'; }
    var d = Math.ceil(10 / (x / days)); return d <= 1 ? 'full within a day' : 'full in ' + n(d) + ' days'; }
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
  function render(){ var v = {}; ['turns', 'tools', 'day', 'days'].forEach(function(k){ v[k] = +$('ds-' + k).value; });
    var m = model(v.turns, v.tools, v.day, v.days), out = $('ds-out');
    var rows = [['Checkpoint rows, one conversation', n(m.ck)], ['Versions of messages kept', n(m.ver)],
      ['Every version, one conversation', kb(m.all)], ['The latest version alone', kb(m.latest)],
      ['Keeping every version costs', (m.all / m.latest).toFixed(1) + ' times the latest'],
      ['Messages kept after ' + v.days + ' days', gb(m.gb)], ['Against the 10 GB disk', disk(m.gb, v.days)]];
    out.textContent = '';
    rows.forEach(function(r, i){ out.appendChild(el('b', '', r[0])); out.appendChild(el('span', i === 4 || i === 6 ? 'big' : '', r[1])); }); }
  ['turns', 'tools', 'day', 'days'].forEach(function(k){ var s = $('ds-' + k);
    O[k].forEach(function(x){ var o = el('option', '', k === 'days' ? x + ' days' : n(x)); o.value = x; s.appendChild(o); });
    s.value = {turns: 10, tools: 1, day: 200, days: 90}[k]; s.addEventListener('change', render); });
  render();""" % (json.dumps(INC), json.dumps(OPTS))

# the page's JS arithmetic against this file's, for every choice the selects offer
JS_MODEL = re.search(r"(function model\(turns, tools, perDay, days\)\{.*?\n\s*return \{.*?\}; \})", UI_JS, re.S).group(1)
cases = [(t, k, d, n) for t in OPTS["turns"] for k in OPTS["tools"] for d in OPTS["day"] for n in OPTS["days"]]
node = subprocess.run(["node", "-e", f"var INC = {json.dumps(INC)};\n{JS_MODEL}\nconsole.log(JSON.stringify({json.dumps(cases)}.map(function(c){{ return model(c[0], c[1], c[2], c[3]); }})));"],
                      capture_output=True, text=True, check=True)
for c, got in zip(cases, json.loads(node.stdout)):
    want = model(*c)
    assert all(abs(got[k] - want[k]) < 1e-9 for k in want), (c, got, want)
ONE = model(2, 1, 1, 1)                            # the offline cell's second turn is the pattern's own
assert ONE["ck"] == 10 and ONE["ver"] == 8

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {"MIG_LAST": str(MIGRATIONS - 1), "N_MIG": str(MIGRATIONS), "V_ALL": f"{sum(VSIZE):,}", "V_LAST": f"{VSIZE[-1]:,}",
         "ADK_WARN": html.escape(ADK_WARN, quote=False), "N_CASES": str(len(cases)),
         **{f"INC_{k}": f"{v:,}" for k, v in INC.items()}}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(STATS, INC)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: two turns' checkpoints and versions and the ADK fallback, on the kit's brains.py, their own printing | the widget's"
      f" arithmetic checked against this file's for {len(cases)} choices | live cells against stand-ins")
