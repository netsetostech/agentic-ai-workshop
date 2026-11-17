"""Build lesson 10.9 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

The managed peer. Kit 10.9-B deploys lesson 10.6's A2A peer, unchanged, to Vertex AI Agent Engine:
commands/managed_peer.py stages services/agent/agent.py and its requirements.txt byte for byte, with
commands/managed_peer_agent.py as the package's __init__.py (root_agent is the peer's own agent, its model GlobalGemini
on location global), and deploys the package with google-adk 2.8.0's own deploy, running as documind-agent-sa. Every
Google call goes through Seam.call(); --dry-run prints each and makes none. The peer is asked through the platform's
query API, not A2A, so its door is the project's IAM: every holder of roles/aiplatform.user may ask (fact 8).

Build-time (Rs 0, no credential, no network): the kit's facts the page states, read from its files and from the pinned
google-adk in this interpreter (the chat venv); stage; the dry runs of up and of ask on both hosts; the staged package
imported by ADK's own loader in a venv holding the peer image's pins (the one lesson 10.6's build keeps); and compare
over records the kit's own ask() wrote against a stand-in Google whose replies carry no timings and no token counts.
Recorded from the author's runs (pb.recorded): the probe's facts table (batch 0), then up, the three asks, trace,
sessions, the smoke, compare and two downs (batch 3).
"""
import html
import io
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
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "10.9"
title = ("<title>Lesson 10.9 Run the peer on Google's managed agent platform - lesson 10.6's peer, unchanged, on "
         "Vertex AI Agent Engine | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
SA = lambda name: f"documind-{name}-sa@{PROJ}.iam.gserviceaccount.com"  # noqa: E731

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.mp-two{display:grid;grid-template-columns:repeat(auto-fit,minmax(240px,1fr));gap:4px 14px;}
.hops{list-style:none;margin:0;padding:0;counter-reset:hop;}
.hops li{position:relative;padding:6px 8px 6px 34px;border-left:2px solid var(--border);margin-left:10px;font-size:12.5px;overflow-wrap:anywhere;}
.hops li::before{counter-increment:hop;content:counter(hop);position:absolute;left:-12px;top:6px;width:22px;height:22px;border-radius:50%;background:var(--teal);color:#fff;font-family:var(--mono);font-size:11px;display:flex;align-items:center;justify-content:center;}
.hops li.stop::before{background:#c2410c;}
.hops li.skip{color:#64748b;}
.hops li.skip::before{background:#94a3b8;}
.hops b{color:var(--navy);}
.src{display:block;margin-top:3px;font-family:var(--mono);font-size:11.5px;line-height:1.4;color:#64748b;overflow-wrap:anywhere;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
MP_PY, WRAP, MK = "commands/managed_peer.py", "commands/managed_peer_agent.py", "mk/managed.mk"
EXCERPTS = {
    "inputs": ("commands/managed_peer.py - deploy_inputs(): the deploy's config and .env, as data",
               block(MP_PY, "def deploy_inputs(project: str", end="def stage(")),
    "stage": ("commands/managed_peer.py - stage(): the folder ADK's deploy copies, and the two files beside it",
              block(MP_PY, "def stage(root: Path", end="def sha256(")),
    "gglobal": ("commands/managed_peer_agent.py - GlobalGemini: the model's client, always on location global",
                block(WRAP, "class GlobalGemini(Gemini):", n=6)),
    "root": ("commands/managed_peer_agent.py - root_agent: the peer's own agent, and the one line it logs",
             block(WRAP, "root_agent = peer.agent", n=8)),
    "seam": ("commands/managed_peer.py - Seam: every Google call printed, then made, or printed only",
             block(MP_PY, "class Seam:", end="class LiveGoogle:")),
    "query": ("commands/managed_peer.py - LiveGoogle.query(): one question through the instance's query API",
              block(MP_PY, "    def query(self, name: str, message: str, user_id: str", n=17)),
    "facts": ("commands/managed_peer.py - FACTS: the rows of the author's probe the code rests on",
              block(MP_PY, "FACTS = {", n=13)),
    "render": ("commands/managed_peer.py - FactRefused.render(): what exit 3 prints",
               block(MP_PY, "    def render(self) -> str:", n=7)),
    "mk_up": ("mk/managed.mk - managed-peer-up", block(MK, "# The peer deployed to Agent Engine:", n=10)),
    "mk_ask": ("mk/managed.mk - managed-peer-ask", block(MK, "# One question through the instance's query API", n=7)),
    "may": ("commands/managed_peer.py - may_query(): who may query the instance, read from the project's policy",
            block(MP_PY, "def may_query(ctx: Ctx)", end="# ------")),
    "rows": ("commands/managed_peer.py - the two log filters trace reads",
             block(MP_PY, "MCP_ROWS = (", n=5)),
    "sess": ("commands/managed_peer.py - LiveGoogle.session_as() and raw_session(): ADK's check, and the API's read",
             block(MP_PY, "    def session_as(self, name: str", n=18)),
    "mk_smoke": ("mk/managed.mk - managed-peer-smoke", block(MK, "# The lesson's proof:", n=7)),
    "mk_down": ("mk/managed.mk - managed-peer-down", block(MK, "# Torn down:", n=5)),
}
assert 'env = {"MCP_URL": mcp_url, "AGENT_MODEL": model, "ADK_MAX_LLM_CALLS": str(PEER_MAX_LLM_CALLS)}' in EXCERPTS["inputs"][1]
assert 'shutil.copyfile(WRAPPER, folder / "__init__.py")' in EXCERPTS["stage"][1]
assert 'return Client(enterprise=True, location="global")' in EXCERPTS["gglobal"][1]
assert "root_agent.model = GlobalGemini(model=peer.MODEL)" in EXCERPTS["root"][1]
assert "if self.dry_run:\n            return stub" in EXCERPTS["seam"][1]
assert '"class_method": "async_stream_query"' in EXCERPTS["query"][1] and ":streamQuery" in EXCERPTS["query"][1]
assert EXCERPTS["facts"][1].rstrip().endswith("}") and EXCERPTS["render"][1].rstrip().endswith('return "\\n".join(lines)')
assert EXCERPTS["mk_up"][1].splitlines()[-1].startswith("\t@$(MANAGED_PEER) up")
assert EXCERPTS["mk_smoke"][1].splitlines()[-1].startswith("\t@$(MANAGED_PEER) smoke")
assert EXCERPTS["mk_down"][1].splitlines()[-1].startswith("\t@$(MANAGED_PEER) down")
assert EXCERPTS["mk_ask"][1].splitlines()[-1].startswith("\t@$(MANAGED_PEER) ask")
assert "raise ValueError for\n" in EXCERPTS["sess"][1] or "raises ValueError" in EXCERPTS["sess"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
sys.path[:0] = [str(KIT), str(KIT / "commands")]
import managed_peer as mp  # noqa: E402  (the standard library at import)
from lane import roster_plan  # noqa: E402

read = lambda rel: (KIT / rel).read_text(encoding="utf-8")  # noqa: E731
mk, dep84, satf, ag_src, wrap_src = read(MK), read("commands/lesson-8.4.sh"), read("terraform/sa.tf"), \
    read("services/agent/agent.py"), read(WRAP)
RUN = mp.cloud_run_settings()                        # the Cloud Run peer, as lesson-8.4.sh deploys it (the kit's parser)
assert RUN == {"min_instances": 0, "max_instances": 5, "concurrency": 20, "timeout_s": 300, "memory": "1Gi", "cpu": "1",
               "model": "gemini-3.6-flash", "account": "documind-agent-sa",
               "invokers": ["documind-ui-sa", "documind-chat-sa"]}, RUN
MCP_PH = "https://documind-mcp-NUMBER.asia-south1.run.app"
CONFIG, ENVS = mp.deploy_inputs(PROJ, MCP_PH, RUN["model"])
assert CONFIG == {"service_account": SA("agent"), "min_instances": 0, "max_instances": 1}, CONFIG
assert ENVS == {"MCP_URL": MCP_PH, "AGENT_MODEL": "gemini-3.6-flash", "ADK_MAX_LLM_CALLS": "12"}, ENVS
assert mp.AGENT_SA == RUN["account"] and mp.MEMBER_SA == "documind-ui-sa" and mp.PEER_TENANT == "acme"
assert mp.QUESTION == "After how many years of continuous service does gratuity become payable?"
assert mp.DISPLAY_NAME == "documind-managed-peer" and mp.APP_NAME == "documind_peer" and mp.OTHER_USER == "another-user"
assert sorted(mp.FACTS) == sorted(["1", "2", "3", "4", "5", "6", "7", "8", "9", "11", "12"])
assert "batch 0, Mon 19\n- Wed 21 Oct 2026" in mp.__doc__ and "13 October 2026" in mp.__doc__
assert "0 done, 1 a check failed, 2 stopped (a precondition, or\na refusal that settles no fact), 3 a fact refused, 4 something could not be deleted." in mp.__doc__
ROSTERS = sorted(t for t, e in roster_plan(PROJ, "acme", [])[0] if e == SA("agent"))
assert ROSTERS == ["acme"], ROSTERS
# who holds which project role (terraform/sa.tf): every <name>_roles list is bound at project scope
ACCOUNT = {"ui": "documind-ui-sa", "api": "documind-api-sa", "ingest": "documind-ingest-sa", "chat": "documind-chat-sa",
           "mcp": "documind-mcp-sa", "agent": "documind-agent-sa", "outsider": "documind-outsider-sa",
           "admin": "documind-admin-sa", "cicd": "sa-documind-cicd"}
ROLES = {}
for name, body in re.findall(r"\n  (\w+)_roles = \[(\]|[\s\S]*?\n  \])", satf):     # outsider_roles = [] is one line
    ROLES[name] = re.findall(r'"roles/([\w.]+)"', re.sub(r"#[^\n]*", "", body))
    assert f"for_each = toset(local.{name}_roles)" in satf, name
assert set(ROLES) == set(ACCOUNT), sorted(ROLES)
QUERY = [r.split("/", 1)[1] for r in mp.QUERY_ROLES]
assert QUERY == ["aiplatform.user", "aiplatform.admin", "editor", "owner"], QUERY
MAY = [k for k in ACCOUNT if set(ROLES[k]) & set(QUERY)]
assert MAY == ["ui", "api", "ingest", "chat", "agent"] and ROLES["outsider"] == [], (MAY, ROLES["outsider"])
assert not any(set(ROLES[k]) & {"run.invoker", "run.admin", "editor", "owner"} for k in ACCOUNT)
assert "run.developer" in ROLES["admin"] and "run.developer" in ROLES["cicd"]   # the two the panel leaves out
# the Cloud Run peer: capped at 12 since lesson 10.7's kit (lesson-8.4.sh sets ADK_MAX_LLM_CALLS; agent.py keeps the
# figure when nothing sets it, and /health reports it); no telemetry. Both hosts' caps are one figure.
deploy84 = dep84.split("# ---- DEPLOY ----", 1)[1].split("# ---- SMOKE ----", 1)[0]
PEER_CAP = re.search(r"ADK_MAX_LLM_CALLS=(\d+)", deploy84).group(1)
assert 'os.environ.setdefault("ADK_MAX_LLM_CALLS", "12")' in ag_src and '"max_llm_calls": MAX_LLM_CALLS' in ag_src
assert PEER_CAP == ENVS["ADK_MAX_LLM_CALLS"] == "12", (PEER_CAP, ENVS["ADK_MAX_LLM_CALLS"])
assert not re.search(r"(?i)otel|telemetry|opentelemetry", deploy84 + ag_src)
assert "GOOGLE_CLOUD_LOCATION=global" in deploy84 and "SELF_URL=" in deploy84 and "SELF_URL" not in "".join(ENVS)
assert "services/agent/Dockerfile" in deploy84
# the wrapper's line, and the Makefile's flags the page's commands rely on
assert '"event": "managed_peer_up"' in wrap_src and '"model_location": "global"' in wrap_src
# the three settings the author's probe decides (facts 1, 2, 11): the page's dry run and prose follow mk/managed.mk
MK_REGION = re.search(r"^MANAGED_PEER_REGION \?= (\S+)$", mk, re.M).group(1)
MK_GRANT = re.search(r"^MANAGED_PEER_GRANT_ROLE \?= (roles/\S+)$", mk, re.M).group(1)
PEER_REGION = "asia-south1" if MK_REGION == "$(REGION)" else MK_REGION      # the course's lane runs in asia-south1
REGION_TEXT = "your <code>REGION</code> by default" if MK_REGION == "$(REGION)" else f"<code>{html.escape(MK_REGION)}</code> by default"
assert re.search(r"^AIPLATFORM_PIN \?=$", mk, re.M), "step 9's gap and step 5's prose say aiplatform is unpinned"
for needle in ("MANAGED_PEER = $(if $(DRY_RUN),$(PY) commands/managed_peer.py,",
               "--project $(or $(PROJECT),documind-ai-YOUR-ID) --region $(MANAGED_PEER_REGION)",
               "--services-region $(REGION) --grant-role $(MANAGED_PEER_GRANT_ROLE)", "$(if $(DRY_RUN),--dry-run,)",
               "--tenant $(TENANT) $(if $(Q),--question \"$(Q)\",) $(if $(HOST),--host $(HOST),)",
               "$(if $(SINCE),--since $(SINCE),)", "$(if $(KEEP),--keep,)", "$(if $(ASKER),--as $(ASKER),)"):
    assert needle in mk, needle
TARGETS = re.findall(r"^(managed-peer-[a-z]+):", mk, re.M)
assert TARGETS == ["managed-peer-up", "managed-peer-ask", "managed-peer-trace", "managed-peer-smoke",
                   "managed-peer-sessions", "managed-peer-down"], TARGETS
assert any(" ".join(TARGETS) in line for line in read("Makefile").splitlines())   # on the .PHONY line (later kits append after)
assert re.search(r"^up:", read("Makefile"), re.M) and re.search(r"^operators:", read("Makefile"), re.M)
assert "commands/lesson-7.2.sh commands/lesson-8.4.sh" in read("Makefile") and \
    "SERVICES   = ingest api admin ui chat mcp agent" in read("Makefile")       # make up deploys the Cloud Run peer
PEER_PINS = dict(re.findall(r"^([a-z0-9\-\[\],]+)==([\d.]+)$", read("services/agent/requirements.txt"), re.M))
assert PEER_PINS["google-adk[a2a,mcp]"] == "2.8.0" == mp.adk_pin() and PEER_PINS["a2a-sdk[http-server]"] == "1.1.2"
# the author's probe (authoring repository only): the dates and the platform's new name it records
probe_src = (ROOT / "tools" / "probe_agent_stack.py").read_text(encoding="utf-8")
assert "batch 0 (Mon 19 - Wed 21 Oct 2026)" in probe_src
assert "During\n# 2026 Google renamed Agent Engine to Agent Runtime, on the Gemini Enterprise Agent Platform" in probe_src
assert "Google's pages were read on 2026-10-08" in probe_src
# rag-api's answer budget (config.py), priced as lesson 2.5 prices it: the most one answer inside retrieve costs
cfg = read("services/rag-api/config.py")
CTX_TOK = int(re.search(r"max_context_tokens: int = (\d+)", cfg).group(1))
ANS_TOK = int(re.search(r"max_answer_tokens: int = (\d+)", cfg).group(1))
from shared import prices  # noqa: E402
FLASH_IN, FLASH_OUT = prices.PRICES[RUN["model"]]
ANSWER_INR = round(prices.inr(prices.usd(RUN["model"], CTX_TOK, ANS_TOK)), 2)
assert (CTX_TOK, ANS_TOK, ANSWER_INR, prices.USD_INR) == (8000, 2048, 2.33, 85), (CTX_TOK, ANS_TOK, ANSWER_INR)
N_ANSWERS = 6                                   # rag-api answers in the batch: step 6's acme asks on both hosts (2), the smoke's four
RUN_CAP, SMOKE_CAP = round(N_ANSWERS * ANSWER_INR, 2), round(4 * ANSWER_INR, 2)

# ------------------------------------------------------------------ the pinned google-adk (this interpreter: the chat venv)
import importlib.metadata  # noqa: E402
import importlib.util  # noqa: E402
assert importlib.metadata.version("google-adk") == "2.8.0", "build 10.9 with the chat venv (google-adk 2.8.0)"
ADK = Path(importlib.util.find_spec("google.adk").submodule_search_locations[0])
cli = (ADK / "cli/cli_deploy.py").read_text(encoding="utf-8")
for needle in ("FROM python:3.11-slim", "ENV GOOGLE_GENAI_USE_ENTERPRISE=1", "ENV GOOGLE_CLOUD_LOCATION={gcp_region}",
               'RUN pip install "google-adk[a2a]=={adk_version}"',
               "env_vars['ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS'] = 'false'",
               "env_vars['GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY'] = 'true'",
               "    'google-cloud-aiplatform[adk,agent_engines]'", "click.echo('Deploying to Agent Platform...')",
               "agent_config['image_spec'] = {}  # Use the Dockerfile", "def to_gke("):
    assert needle in cli, needle
assert "_validate_agent_import(\n" not in cli.split("def _validate_agent_import(", 1)[1]   # defined, never called
from google.adk.agents import run_config as adk_run_config  # noqa: E402
ADK_DEFAULT_CALLS = adk_run_config._DEFAULT_MAX_LLM_CALLS
assert ADK_DEFAULT_CALLS == 500 and "os.getenv('ADK_MAX_LLM_CALLS')" in Path(adk_run_config.__file__).read_text(encoding="utf-8")
assert "run_config=RunConfig(custom_metadata=custom_metadata)" in (ADK / "a2a/converters/request_converter.py").read_text(encoding="utf-8")
assert "session_service = InMemorySessionService()" in (ADK / "a2a/utils/agent_to_a2a.py").read_text(encoding="utf-8")
assert "class GlobalGemini(Gemini):" in (ADK / "models/google_llm.py").read_text(encoding="utf-8")

# ------------------------------------------------------------------ the cells
STAGE_CMD = ('rm -rf /tmp/mp109 && python commands/managed_peer.py stage --dir /tmp/mp109 \\\n'
             '  --project "$PROJECT" --project-number "$NUMBER" --services-region "$REGION"   # no call, Rs 0')
PINS_PY = r'''import json, logging, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
logging.basicConfig(level=logging.WARNING, format="%(message)s", stream=sys.stdout)
logging.getLogger("documind.managed_peer").setLevel(logging.INFO)   # the wrapper's one line, as the runtime logs it
env = dict(line.split("=", 1) for line in open("/tmp/mp109/deploy_config/.env").read().splitlines())
os.environ.update(env, GOOGLE_CLOUD_LOCATION=os.environ["REGION"],  # ADK's Dockerfile sets the region here
                  ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS="false",      # ADK's deploy sets this with telemetry on
                  ADK_DISABLE_LOAD_DOTENV="1")                       # the image ships no .env
from google.adk.agents.run_config import RunConfig
from google.adk.cli.utils.agent_loader import AgentLoader
root = AgentLoader(agents_dir="/tmp/mp109").load_agent("documind_peer")   # as adk api_server loads it
peer = sys.modules["documind_peer.agent"]
print("root_agent is agent.py's own agent:", root is peer.agent, "| name:", root.name)
print("its model:", type(root.model).__name__, root.model.model, "| its tools:", [type(t).__name__ for t in root.tools])
print("model calls a turn, at most:", RunConfig().max_llm_calls)'''
PINS_VENV = ('[ -x ~/peer-pins-venv/bin/python ] || { python3 -m venv ~/peer-pins-venv && '
             '~/peer-pins-venv/bin/pip install -q -r services/agent/requirements.txt; }   # the peer image\'s pins, once\n')
LANE_FLAGS = 'PROJECT="$PROJECT" REGION="$REGION"'
CELLS = {
    "stage": STAGE_CMD,
    "pins": PINS_VENV + "~/peer-pins-venv/bin/python - <<'PY'\n" + PINS_PY + "\nPY",
    "dry": f"make managed-peer-up DRY_RUN=1 {LANE_FLAGS}   # every call printed, none made: no credential, Rs 0",
    "dryask": (f"make managed-peer-ask DRY_RUN=1 {LANE_FLAGS}                 # the managed peer\n"
               f"make managed-peer-ask DRY_RUN=1 {LANE_FLAGS} HOST=cloudrun    # the Cloud Run peer"),
    "up": f"make managed-peer-up {LANE_FLAGS}   # 10 to 20 minutes, most of it the image's build",
    "ask": f"make managed-peer-ask {LANE_FLAGS}",
    "zeta": f"make managed-peer-ask {LANE_FLAGS} TENANT=zeta",
    "cloudrun": f"make managed-peer-ask {LANE_FLAGS} HOST=cloudrun",
    "trace": f"make managed-peer-trace {LANE_FLAGS} SINCE=15   # the last 15 minutes: both hosts' asks",
    "sessions": f"make managed-peer-sessions {LANE_FLAGS}",
    "smoke": f"make managed-peer-smoke {LANE_FLAGS}   # eight checks, then the Cloud Run peer and the table",
    "compare": "python commands/managed_peer.py compare   # this machine's records: no call, Rs 0",
    "down": f"make managed-peer-down {LANE_FLAGS}\nmake managed-peer-down {LANE_FLAGS}   # again: nothing left to delete",
}

T = Path(tempfile.mkdtemp(prefix="lesson109-"))
ENV = {k: v for k, v in os.environ.items()
       if k not in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT", "GCLOUD_PROJECT")}
for k in ("APPDATA", "CLOUDSDK_CONFIG", "USERPROFILE", "HOME"):       # no credential is reachable from a cell run here
    (T / k.lower()).mkdir()
    ENV[k] = str(T / k.lower())
ENV.update(PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", REGION="asia-south1")


def kit(*argv) -> str:
    """commands/managed_peer.py from deploy/, as make runs it: its stdout; it must exit 0 and write nothing to stderr."""
    r = subprocess.run([sys.executable, "commands/managed_peer.py", *argv], cwd=KIT, env=ENV, capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode == 0 and not r.stderr.strip(), (argv, r.stdout[-800:], r.stderr[-1500:])
    return r.stdout


OUT = {}
# ---- step 3: stage, then the staged package imported as the runtime imports it
STAGE = T / "mp109"
OUT["stage"] = kit("stage", "--dir", str(STAGE)).replace(str(STAGE), "/tmp/mp109")
S3 = OUT["stage"]
assert S3.startswith("== stage: what make managed-peer-up deploys, written to /tmp/mp109 ==\n"), S3
# agent.py's own modules and data ride along when the kit has them (lesson 10.7's chain, lesson 10.8's pins): stage()
# copies each byte for byte, so the count and the list follow the kit
STAGED_EXTRAS = [f for f in ("chain.py", "pins.py", "tool_pins.json") if (KIT / "services/agent" / f).exists()]
N_STAGED = 3 + len(STAGED_EXTRAS)
N_STAGED_WORD = {3: "three", 4: "four", 5: "five", 6: "six"}[N_STAGED]
assert S3.count("byte for byte") == N_STAGED and json.dumps(CONFIG) in S3 and json.dumps(ENVS) in S3, S3
assert "the image: google-adk[a2a]==2.8.0 (the peer's pin); the deploy appends google-cloud-aiplatform[adk,agent_engines], unpinned (fact 11)" in S3
assert sorted(p.relative_to(STAGE).as_posix() for p in STAGE.rglob("*") if p.is_file()) == sorted([
    "deploy_config/.agent_engine_config.json", "deploy_config/.env", "documind_peer/__init__.py",
    "documind_peer/agent.py", "documind_peer/requirements.txt"] + [f"documind_peer/{f}" for f in STAGED_EXTRAS])

VENV = Path(tempfile.gettempdir()) / "agents_workshop" / "venv-a2a"     # lesson 10.6's build makes and keeps it
VPY = VENV / ("Scripts/python.exe" if os.name == "nt" else "bin/python")
if not VPY.exists():
    print(f"making {VENV} with services/agent/requirements.txt (once)")
    subprocess.run([sys.executable, "-m", "venv", str(VENV)], check=True)
    subprocess.run([str(VPY), "-m", "pip", "install", "-q", "-r", str(KIT / "services/agent/requirements.txt")], check=True)
r = subprocess.run([str(VPY), "-"], input=PINS_PY.replace("/tmp/mp109", STAGE.as_posix()), cwd=str(T), env=ENV,
                   capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 0 and not r.stderr.strip(), (r.stdout[-800:], r.stderr[-2000:])
OUT["pins"] = r.stdout
LINE = json.loads(OUT["pins"].splitlines()[0])
assert (LINE["event"], LINE["agent"], LINE["model"], LINE["model_location"], LINE["GOOGLE_CLOUD_LOCATION"],
        LINE["ADK_MAX_LLM_CALLS"], LINE["ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"]) == (
    "managed_peer_up", "documind_peer", "gemini-3.6-flash", "global", "asia-south1", "12", "false"), LINE
assert LINE["versions"]["google-adk"] == "2.8.0" and LINE["versions"]["a2a-sdk"] == "1.1.2", LINE
assert OUT["pins"].splitlines()[1:] == ["root_agent is agent.py's own agent: True | name: documind_peer",
                                        "its model: GlobalGemini gemini-3.6-flash | its tools: ['McpToolset']",
                                        "model calls a turn, at most: 12"], OUT["pins"]

# ---- step 4: the dry runs, as make runs them with DRY_RUN=1 (the state and records folder is a fresh temporary one)
FLAGS = ["--project", PROJ, "--region", PEER_REGION, "--services-region", "asia-south1", "--grant-role", MK_GRANT,
         "--dry-run", "--records", str(T / "records")]
OUT["dry"] = kit("up", *FLAGS)
D4 = OUT["dry"]
assert D4.rstrip().endswith("Dry run: nothing was created or changed; 8 call(s) printed above."), D4
N_DRY_CALLS = D4.count("  would call: ")
assert N_DRY_CALLS == 8 and "  call: " not in D4 and str(T) not in D4, D4
assert "WHO MAY CALL IT: every account holding roles/aiplatform.user (or owner, or editor) on the project" in D4
OUT["dryask"] = kit("ask", *FLAGS, "--tenant", "acme") + kit("ask", *FLAGS, "--tenant", "acme", "--host", "cloudrun")
A4 = OUT["dryask"]
assert ':streamQuery?alt=sse {"class_method": "async_stream_query", "input": {"user_id": "documind-ui-sa", "message": ' in A4
assert '.run.app/ message/send {"parts": [{"kind": "text", "text": ' in A4 and A4.count("2 call(s) printed above.") == 2
assert not (T / "records").exists(), "a dry run wrote the state or a record"

# ---- compare over a sample: the kit's own ask() against a stand-in Google, twice for each host
ANSWER = "Gratuity is payable after not less than five years of continuous service [1]."
TURN = [{"author": "documind_peer", "content": {"role": "model", "parts": [
            {"function_call": {"name": "retrieve", "args": {"query": mp.QUESTION}}}]}},
        {"author": "documind_peer", "content": {"role": "user", "parts": [{"function_response": {
            "name": "retrieve", "response": {"isError": False, "content": [{"type": "text", "text": ANSWER}]}}}]}},
        {"author": "documind_peer", "content": {"role": "model", "parts": [{"text": ANSWER}]}}]
TASK = {"jsonrpc": "2.0", "id": "1", "result": {"kind": "task", "status": {"state": "completed"},
        "artifacts": [{"parts": [{"kind": "text", "text": ANSWER}]}],
        "history": [{"role": "agent", "kind": "message", "parts": [{"kind": "data", "metadata": {"adk_type": "function_call"},
                                                                     "data": {"name": "retrieve", "args": {"query": mp.QUESTION}}}]}]}}


class StandIn:
    """Google, stood in for compare's sample: one instance that exists, and replies that carry no timings and no tokens."""

    def __init__(self, project):
        self.project = project

    def project_number(self):
        """The project's number, as a placeholder."""
        return "NUMBER"

    def get_instance(self, name):
        """The instance exists."""
        return {}

    def query(self, name, message, user_id, as_sa):
        """The managed peer's turn: retrieve, its result, the answer; untimed."""
        return {"status": 200, "events": TURN, "first_event_s": None, "total_s": None}

    def a2a_send(self, url, message, as_sa):
        """The Cloud Run peer's task; untimed."""
        return {"status": 200, "reply": TASK, "text": ANSWER, "first_event_s": None, "total_s": None}


SAMPLE = T / "sample"
SAMPLE.mkdir()
ENGINE = "projects/NUMBER/locations/asia-south1/reasoningEngines/ENGINE_ID"
(SAMPLE / "state.json").write_text(json.dumps({"name": ENGINE, "region": "asia-south1", "asks": 0,
                                               "deployed_at": "2026-11-16T00:00:00Z"}), encoding="utf-8")
SAMPLE_PROJECT = "stand-in-lane-109"        # live commands refuse the placeholder; no record or line names a project
for host in ([], ["--host", "cloudrun"]):
    for _ in range(2):
        buf = io.StringIO()
        code = mp.main(["ask", "--project", SAMPLE_PROJECT, "--region", "asia-south1", "--services-region", "asia-south1",
                        "--records", str(SAMPLE), *host], google_factory=StandIn, out=buf, sleep=lambda s: None)
        assert code == 0, buf.getvalue()
buf = io.StringIO()
assert mp.main(["compare", "--records", str(SAMPLE)], out=buf) == 0
OUT["sample"] = buf.getvalue()
C4 = OUT["sample"]
assert SAMPLE_PROJECT not in C4 and SAMPLE_PROJECT not in (SAMPLE / "runs.ndjson").read_text(encoding="utf-8")
assert re.search(r"asks of acme's question, answered\s+\| Cloud Run: 2\s+\| Agent Engine: 2", C4), C4
assert re.search(r"warm calls, median s\s+\| Cloud Run: -\s+\| Agent Engine: -", C4), C4
assert re.search(r"runs as\s+\| Cloud Run: documind-agent-sa\s+\| Agent Engine: documind-agent-sa", C4), C4
assert "roles/run.invoker on documind-agent: documind-ui-sa, documind-chat-sa (commands/lesson-8.4.sh)" in C4
assert "aiplatform.reasoningEngines.query: any roles/aiplatform.user holder, unless the instance has an IAM policy (fact 8)" in C4
SAMPLE_RECORD = json.loads((SAMPLE / "runs.ndjson").read_text(encoding="utf-8").splitlines()[0])
assert set(SAMPLE_RECORD) == {"kind", "command", "host", "at", "region", "label", "question", "answered",
                              "refused_by_roster", "latency_s", "cold", "tool_calls", "model", "identity", "hosting",
                              "errors"}, sorted(SAMPLE_RECORD)
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ the author's runs
LANE = "(the author's lane, batch 3: your times, tokens, rupees and ids are yours)"
RECORDED = {
    "up": ("(the author's lane, batch 3: your deploy's minutes and ids are yours)", "up.txt"),
    "ask": (LANE, "ask_acme.txt"), "zeta": (LANE, "ask_zeta.txt"), "cloudrun": (LANE, "ask_cloudrun.txt"),
    "trace": ("(the author's lane, batch 3: your span counts and times are yours)", "trace.txt"),
    "sessions": ("(the author's lane, batch 3: your session ids are yours)", "sessions.txt"),
    "smoke": (LANE, "smoke.txt"), "compare": ("(the author's records, batch 3: your table is your own runs)", "compare.txt"),
    "down": ("(the author's lane, batch 3: both runs)", None),
}
for k, (label, name) in RECORDED.items():
    if name:
        OUT[k] = (label, pb.recorded(LESSON, name))
OUT["down"] = (RECORDED["down"][0], pb.recorded(LESSON, "down.txt") + "\n\n" + pb.recorded(LESSON, "down_again.txt"))
PROBE = pb.recorded(LESSON, "probe_facts.md")
STATUS, PROBE_DATE = {}, ""
if not PROBE.startswith("[awaiting"):
    m = re.search(r"\((\d{4}-\d{2}-\d{2})\)", PROBE)
    PROBE_DATE = m.group(1) if m else ""
    STATUS = {row: " ".join(status.split())[:40] for row, status in
              re.findall(r"^\|\s*(\d+)\s*\|[^|\n]*\|\s*([^|\n]+?)\s*\|", PROBE, re.M)}
    assert set(mp.FACTS) <= set(STATUS), f"data/probe_facts.md lacks rows {sorted(set(mp.FACTS) - set(STATUS))}"


def fact(n: str) -> str:
    """A probe fact as a cell names it: its row and its status in the author's table, or that the table is awaited."""
    if n not in STATUS:
        return f"fact {n}: awaiting the author's probe"
    return f"fact {n}: {STATUS[n]}" + (f", {PROBE_DATE}" if PROBE_DATE else "")


def facts(*ns: str) -> str:
    """Several probe facts in one cell: named together while the table is awaited, one by one once it is in."""
    if not any(n in STATUS for n in ns):
        return f"facts {', '.join(ns[:-1])} and {ns[-1]}: awaiting the author's probe"
    return "; ".join(fact(n) for n in ns)


WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five", 6: "six", 7: "seven", 8: "eight", 9: "nine"}


# ------------------------------------------------------------------ the windows
def bash_window(label: str, code: str) -> str:
    """A command window: the label says where to run it, and it carries a copy button."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str, kind: str = "expected") -> str:
    """An output window: read only."""
    return ('<div class="cw"><div class="ch-bar"><span>' + kind + " " + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "stage": "run in the operator shell, in the kit (what up deploys, written out; no call)",
    "pins": "run in the operator shell, in the kit (the staged package, imported as the runtime imports it; no Google call)",
    "dry": "run in the operator shell, in the kit (up, every call printed and none made)",
    "dryask": "run in the operator shell, in the kit (one question, as each host is asked; nothing sent)",
    "up": "run in the operator shell, in the kit (the managed peer deployed: it bills until step 10)",
    "ask": "run in the operator shell, in the kit (acme's question, through the query API)",
    "zeta": "run in the operator shell, in the kit (the same question, naming zeta)",
    "cloudrun": "run in the operator shell, in the kit (the same question to the Cloud Run peer, over A2A)",
    "trace": "run in the operator shell, in the kit (what the asks left: spans, rows, the runtime's line)",
    "sessions": "run in the operator shell, in the kit (the managed sessions, and who may read one)",
    "smoke": "run in the operator shell, in the kit (the lesson's proof)",
    "compare": "run in the operator shell, in the kit (Cloud Run against Agent Engine, from your records)",
    "down": "run in the operator shell, in the kit (torn down, then checked)",
}
BUILT = {
    "stage": "(the kit's stage, run when this page was built)",
    "pins": ("(run when this page was built, in a venv made the same way; the runtime's own line also names the "
             "google-cloud-aiplatform its image took)"),
    "dry": "(the kit's dry run, run when this page was built: your project id where this shows the placeholder)",
    "dryask": "(the kit's dry runs, run when this page was built)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
for k, v in OUT.items():
    if k == "sample":
        WIN["OUT_SAMPLE"] = out_window("of compare over four stand-in asks (the kit's own ask(), twice for each host, run "
                                       "when this page was built against a stand-in Google whose replies carry no timings "
                                       "and no token counts: every - is a cell your runs fill)", v, kind="output")
    elif isinstance(v, tuple):
        WIN[f"OUT_{k.upper()}"] = out_window(*v)
    else:
        WIN[f"OUT_{k.upper()}"] = out_window(BUILT[k], v)
WIN["OUT_PROBE"] = out_window("of the author's probe, batch 0 (the facts table it writes to plan/, every identifier "
                              "replaced)", PROBE, kind="log")

# ------------------------------------------------------------------ Level 0: who may ask the peer, and the two hosts side by side
C = lambda text: "<code>" + html.escape(text) + "</code>"  # noqa: E731
INV = RUN["invokers"]
ROLE_TEXT = ", ".join(C(r) for r in QUERY[:-1]) + " or " + C(QUERY[-1])
CALLERS, ORDER = {}, ["ui", "chat", "api", "ingest", "agent", "mcp", "outsider"]
for k in ORDER:
    acct = ACCOUNT[k]
    held = ROLES[k]
    cr_ok = acct in INV
    ae_ok = bool(set(held) & set(QUERY))
    if ae_ok:
        ae_why = (f"admits {acct}, which holds roles/aiplatform.user on the project (terraform/sa.tf): that role carries "
                  f"aiplatform.reasoningEngines.query, unless the instance carries an IAM policy of its own ({fact('8')}).")
    elif held:
        ae_why = (f"refuses {acct}: its project roles ({', '.join('roles/' + x for x in held)}) carry no "
                  f"aiplatform.reasoningEngines.query (terraform/sa.tf).")
    else:
        ae_why = f"refuses {acct}: it holds no project role at all (terraform/sa.tf)."
    CALLERS[k] = {
        "label": acct,
        "cr": {"ok": cr_ok, "why": (f"admits {acct}, which commands/lesson-8.4.sh binds as roles/run.invoker on documind-agent."
                                     if cr_ok else
                                     f"refuses {acct} with 403: it is not one of the {WORDS[len(INV)]} invokers commands/lesson-8.4.sh binds.")},
        "ae": {"ok": ae_ok, "why": ae_why},
    }
assert [k for k in ORDER if CALLERS[k]["cr"]["ok"]] == ["ui", "chat"]
assert [k for k in ORDER if CALLERS[k]["ae"]["ok"]] == ["ui", "chat", "api", "ingest", "agent"]
AFTER = {
    "Cloud Run": [["The peer:", f"runs the turn as {RUN['account']}, and mints an ID token for documind-mcp from Cloud Run's metadata server."],
                  ["documind-mcp:", f"finds {RUN['account']} on {', '.join(ROSTERS)}'s roster alone: the answer is acme's, and a question naming zeta is refused."],
                  ["Who asked:", "nothing past the door records it (lesson 10.6's trace)."]],
    "Agent Engine": [["The platform:", f"runs the turn as {RUN['account']} ({fact('2')}) and keeps a session under the user id the caller wrote ({fact('9')})."],
                     ["documind-mcp:", f"takes the runtime's ID token ({fact('5')}) and finds the same account on the same roster: the same answer, and zeta refused."],
                     ["Who asked:", "the session's user id is the caller's own word; documind-mcp still sees only documind-agent-sa."]],
}
PANEL = {"callers": CALLERS, "order": ORDER, "after": AFTER}

ROWS = [
    ("How another agent asks it", "A2A: the card, then " + C("message/send") + " at the peer's URL", "services/agent/agent.py: to_a2a",
     "the query API: " + C("streamQuery") + " with " + C("async_stream_query") + "; no card", "commands/managed_peer.py: LiveGoogle.query"),
    ("The caller's token", "an ID token minted for the peer's URL", "smoke/smoke_agent.py",
     "an access token for Google's API", "commands/managed_peer.py: LiveGoogle._credentials"),
    ("Who may call it", f"{WORDS[len(INV)]} accounts: " + ", ".join(C(a) for a in INV), "commands/lesson-8.4.sh",
     f"every holder of {ROLE_TEXT} on the project: {WORDS[len(MAY)]} of the lane's accounts, and anyone else with those roles",
     "terraform/sa.tf; managed_peer.py: QUERY_ROLES; " + fact("8")),
    ("Runs as", C(RUN["account"]), "commands/lesson-8.4.sh",
     C(CONFIG["service_account"].split("@")[0]), ".agent_engine_config.json; " + fact("2")),
    ("What it reaches", f"documind-mcp alone, on {', '.join(ROSTERS)}'s roster", "commands/lane.py: roster_plan",
     "the same, with the runtime's ID token", fact("5")),
    ("Where Gemini is called", "location global", "commands/lesson-8.4.sh: GOOGLE_CLOUD_LOCATION=global",
     "location global, through GlobalGemini; the image sets the region", "managed_peer_agent.py; ADK's Dockerfile; " + fact("6")),
    ("Model calls a turn, at most", f"{PEER_CAP}, the peer's own cap", "commands/lesson-8.4.sh: ADK_MAX_LLM_CALLS; "
     "agent.py's setdefault (lesson 10.7)", ENVS["ADK_MAX_LLM_CALLS"], ".env: ADK_MAX_LLM_CALLS"),
    ("Instances", f"{RUN['min_instances']} to {RUN['max_instances']}, {RUN['concurrency']} requests each, a {RUN['timeout_s']} s "
                  f"timeout, {RUN['cpu']} CPU, {RUN['memory']}", "commands/lesson-8.4.sh",
     f"{CONFIG['min_instances']} to {CONFIG['max_instances']}", ".agent_engine_config.json; " + facts("3", "4")),
    ("Sessions", "in memory, inside each instance", "google-adk 2.8.0: to_a2a",
     "kept by the platform, per user id", "VertexAiSessionService; " + fact("9")),
    ("Spans in Cloud Trace", "none turned on by the kit", "commands/lesson-8.4.sh",
     "on, with message content off", "ADK's deploy: otel_to_cloud; " + fact("7")),
    ("The image", "services/agent/Dockerfile", "commands/lesson-8.4.sh",
     "ADK's Dockerfile on python:3.11-slim, then the same requirements.txt", "google-adk 2.8.0: cli_deploy; " + fact("11")),
    ("Price", "Cloud Run's, by request time", "commands/managed_peer.py: ask()", "not stated by the kit", fact("12")),
    ("Lifetime", "with the lane: " + C("make up") + " deploys it", "Makefile",
     C("make managed-peer-up") + " until " + C("make managed-peer-down"), "mk/managed.mk"),
]


def cell(value: str, source: str) -> str:
    """One table cell's content: the value, then the file or probe fact it comes from."""
    return value + '<span class="src">' + html.escape(source) + "</span>"


TABLE = "".join(f'<tr><td><strong>{a}</strong></td><td data-label="Cloud Run">{cell(cv, cs)}</td>'
                f'<td data-label="Agent Engine">{cell(av, asrc)}</td></tr>\n' for a, cv, cs, av, asrc in ROWS)

UI_JS = r"""var root = document.getElementById('mp'); if (!root) return;
  var P = %s, $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
  function hop(cls, head, text){ var li = el('li', cls, ''); li.appendChild(el('b', '', head + ' ')); li.appendChild(document.createTextNode(text)); return li; }
  function side(id, host, door){ var ol = $(id); ol.textContent = '';
    ol.appendChild(hop(door.ok ? '' : 'stop', host + ':', door.why));
    if (!door.ok) { ol.appendChild(hop('skip', 'The peer:', 'never sees the question.')); return; }
    P.after[host].forEach(function(s){ ol.appendChild(hop('', s[0], s[1])); }); }
  function render(){ var c = P.callers[$('mp-who').value]; side('mp-cr', 'Cloud Run', c.cr); side('mp-ae', 'Agent Engine', c.ae); }
  P.order.forEach(function(k){ var o = el('option', '', P.callers[k].label); o.value = k; $('mp-who').appendChild(o); });
  $('mp-who').addEventListener('change', render); render();""" % json.dumps(PANEL)
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

STATS = {
    "TABLE": TABLE, "N_INV": WORDS[len(INV)], "N_MAY": WORDS[len(MAY)], "ROLE_TEXT": ROLE_TEXT,
    "MAY_LIST": ", ".join(C(ACCOUNT[k]) for k in MAY), "ADK_CALLS": str(ADK_DEFAULT_CALLS), "PEER_CAP": PEER_CAP, "N_STAGED_WORD": N_STAGED_WORD, "N_STAGED_WORD_CAP": N_STAGED_WORD.capitalize(),
    "STAGED_EXTRAS": ("" if not STAGED_EXTRAS else " and ".join([", ".join(f"<code>{f}</code>" for f in STAGED_EXTRAS[:-1]),
                                                                  f"<code>{STAGED_EXTRAS[-1]}</code>"]) if len(STAGED_EXTRAS) > 1
                      else f"<code>{STAGED_EXTRAS[0]}</code>") + (" are agent.py's own modules and data (lessons 10.7 and 10.8), "
                                                                  if len(STAGED_EXTRAS) > 1 else
                                                                  " is agent.py's own (lessons 10.7 and 10.8), " if STAGED_EXTRAS else ""),
    "CAP": ENVS["ADK_MAX_LLM_CALLS"], "ANSWER_INR": f"{ANSWER_INR:.2f}", "CTX_TOK": f"{CTX_TOK:,}", "ANS_TOK": f"{ANS_TOK:,}",
    "FLASH_IN": f"{FLASH_IN:.2f}", "FLASH_OUT": f"{FLASH_OUT:.2f}", "USD_INR": str(prices.USD_INR),
    "N_ANSWERS": str(N_ANSWERS), "RUN_CAP": f"{RUN_CAP:.2f}", "FACT8": fact("8"), "FACT9": fact("9"),
    "N_DRY_CALLS": str(N_DRY_CALLS), "N_FACTS": str(len(mp.FACTS)), "SMOKE_CAP": f"{SMOKE_CAP:.2f}",
    "GRANT_ROLE": MK_GRANT, "REGION_TEXT": REGION_TEXT,
    "SERVICE_AGENT": mp.SERVICE_AGENT.format(number="NUMBER"),
    "FACT_ROWS": ", ".join(sorted(mp.FACTS, key=int)[:-1]) + " and " + sorted(mp.FACTS, key=int)[-1],
}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v if isinstance(v, str) else v[1]}")
    sys.exit(0)


def subst(text: str) -> str:
    """The part's %%NAME%% tokens, filled from the windows and the numbers computed above."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print("kit: stage, the dry runs and the staged package's import run here; compare over four stand-in asks"
      f" | the doors: Cloud Run {len(INV)} invokers, Agent Engine {len(MAY)} of the lane's accounts (fact 8)")
