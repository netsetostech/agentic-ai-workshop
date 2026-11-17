"""Build lesson 11.7 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Reproduce the agent failures production shows and no eval row does. The kit keeps them in one registry,
ops/gotchas.json: each gotcha with its symptom, why no eval row catches it, a drill that reproduces it (offline on a
stand-in of Cloud Run or on the kit's own code, at Rs 0; on a lane for some), a detector that finds it on a lane and only
reads, the lever that fixes it, the lessons involved, the cost, and the kit lines it rests on (its evidence, word for
word). commands/gotchas.py runs the registry: make gotchas, make gotcha-drill [LIVE=1] and make gotcha-detect.

Computed here, offline, from the kit:
  - the board (Level 0): the registry itself, embedded when the page is built, after gotchas.problems() and
    gotchas.kit_problems() find nothing and every lesson it names is in the manifest;
  - make gotchas and make gotchas ID=deploy-drops-hotfix, every offline drill (make gotcha-drill), and the drills of
    pinned-traffic, deploy-drops-hotfix and ungated-api-release: commands/gotchas.py run as the make targets run it,
    with no gcloud on PATH and no Google credential;
  - the two Rs 0 drills again, on a stand-in, the way commands/tests/test_gotchas.py runs them: the gcloud lines, the cap
    /health reports at each step, the lever clearing the detector, the chat put back, and put back after a failure in
    the middle; and their live path on a stand-in that takes the lane's branch (the preconditions asked, no fork deploy);
  - the deploy reader's cell (what make deploy-services writes, per service), and the Change-it (an entry whose detector
    does not exist, refused) on a throwaway copy of the registry in a throwaway git repository.
Recorded from the author's lane with pb.recorded() (RUN_LIST.md says how): the REST read of documind-chat and
documind-api, the two live drills, make smoke-chat and make gotcha-detect. The REST cell also runs here, against the
kit's own stand-in of Cloud Run, so its code is tested before a lane runs it.

    python pagekit/build.py 11.7
"""
import html
import importlib.util
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
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, module_key, setup_section, window  # noqa: E402

LESSON = "11.7"
title = ("<title>Lesson 11.7 Reproduce the agent failures production shows and no eval row does - a registry of "
         "gotchas, each with a drill, a detector and a lever, and two drills at Rs 0 that put the lane back | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the board: three filters, one row per gotcha, the open gotcha's card under its row */
.gb-filters{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,190px),1fr));gap:8px 12px;margin:0 0 8px;}
.gb-filters label{display:flex;flex-direction:column;gap:4px;font-size:var(--small-size);color:var(--navy);min-width:0;}
.gb-filters select{font:inherit;font-size:16px;min-height:44px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);max-width:100%;}
.gb-count{font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--slate);margin:0 0 6px;}
.gb-row{width:100%;font:inherit;text-align:left;color:var(--navy);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:7px 10px;margin:0 0 5px;cursor:pointer;min-height:44px;display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 10px;align-items:center;-webkit-tap-highlight-color:transparent;}
.gb-row[aria-expanded="true"]{border:2px solid var(--teal);background:var(--teal-light);}
.gb-row[hidden]{display:none;}
.gb-name{display:flex;flex-direction:column;min-width:0;}
.gb-id{font-family:var(--mono);font-size:11.5px;color:var(--teal-dark);overflow-wrap:anywhere;}
.gb-t{font-size:13.5px;line-height:1.4;overflow-wrap:anywhere;}
.gb-tags{display:flex;flex-wrap:wrap;gap:4px;justify-content:flex-end;}
.gb-tag{font-family:var(--mono);font-size:10.5px;border-radius:5px;padding:2px 6px;background:#f1f5f9;color:#475569;white-space:nowrap;}
.gb-tag.loud{background:#fef3c7;color:#92400e;}
.gb-tag.silent{background:#e0f2fe;color:#075985;}
.gb-card{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--teal);border-radius:10px;padding:8px 12px;margin:0 0 8px;font-size:var(--small-size);line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.gb-card b{display:block;font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--navy);margin:8px 0 2px;}
.gb-card p{margin:0 0 4px;font-size:var(--small-size);}
.gb-card .gb-mono{font-family:var(--mono);font-size:12px;color:var(--navy);}
@media (hover:hover) and (pointer:fine){.gb-row:hover{border-color:var(--teal);}}
@media (max-width: 640px){.gb-row{grid-template-columns:minmax(0,1fr);}.gb-tags{justify-content:flex-start;}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson's drills change documind-chat alone, and the one answer that reads acme's rows is make smoke-chat's, "
         "which checks that each brain cites something, not which store it came from. Pin acme or not, as you prefer; if "
         "you set the pin, put it back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head: make smoke-chat and the drills' /health reads call as documind-ui-sa, and every "
         "gcloud line runs as you.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ------------------------------------------------------------------ the kit's registry, and the command that runs it
spec = importlib.util.spec_from_file_location("_gotchas117", KIT / "commands" / "gotchas.py")
G = importlib.util.module_from_spec(spec)
spec.loader.exec_module(G)
REG_TEXT = (KIT / "ops" / "gotchas.json").read_text(encoding="utf-8")
REG = json.loads(REG_TEXT)
ENTRIES = {g["id"]: g for g in REG["gotchas"]}
assert G.problems(REG) == [], G.problems(REG)                  # the schema, and every drill and check it names exists
assert G.kit_problems(REG["gotchas"]) == [], G.kit_problems(REG["gotchas"])   # evidence word for word, policies, events
assert [g["id"] for g in G.load()] == list(ENTRIES)
LESSON_IDS = {lid for m in MANIFEST["modules"].values() for lid in m["lessons"]}
assert all(lid in LESSON_IDS for g in REG["gotchas"] for lid in g["lessons"])      # the learner repo has no manifest to check
CHAT, API, CAP = G.CHAT, G.API, G.CAP
DEFAULT_CAP = G.chat_cap_default()
assert DEFAULT_CAP == 12 and CAP == "CHAT_MAX_MODEL_CALLS"

N = len(REG["gotchas"])
LOUD = [g for g in REG["gotchas"] if g["signal"] == "loud"]
SILENT = [g for g in REG["gotchas"] if g["signal"] == "silent"]
STATUS = {s: [g["id"] for g in REG["gotchas"] if g["status"] == s] for s in G.STATUSES}
OFFLINE = [g["id"] for g in REG["gotchas"] if g["drill"]["offline"]]
LIVE = [g["id"] for g in REG["gotchas"] if g["drill"]["live"]]
KIT_LIVE = list(G.LIVE_DRILLS)
OTHER_LIVE = [gid for gid in LIVE if gid not in G.LIVE_DRILLS]
CHECK_IDS = [g["id"] for g in REG["gotchas"] if g["detector"]["kind"] == "check"]
LOG_IDS = [g["id"] for g in REG["gotchas"] if g["detector"]["kind"] == "log"]
PAGED = [g for g in REG["gotchas"] if g["detector"]["pages"]]
N_EVIDENCE = sum(len(g["evidence"]) for g in REG["gotchas"])
EV_FILES = sorted({rel for g in REG["gotchas"] for rel, _ in g["evidence"]})
assert (N, len(LOUD), len(SILENT)) == (13, 2, 11), (N, len(LOUD), len(SILENT))
assert STATUS == {"open": [g for g in ENTRIES if g != "tag-audience-401"], "guarded": ["tag-audience-401"], "fixed": []}
assert (len(OFFLINE), len(LIVE), KIT_LIVE) == (9, 7, ["pinned-traffic", "deploy-drops-hotfix"])
assert set(OTHER_LIVE) == {"tag-audience-401", "looping-model-stopped", "vector-search-fallback", "poison-upload",
                           "environment-without-reviewers"}
assert [g["id"] for g in PAGED] == ["poison-upload"] and PAGED[0]["detector"]["pages"] == "Ingest dead-letter queue holds messages"
assert {g["id"] for g in LOUD} == {"poison-upload", "tag-audience-401"}
assert all(ENTRIES[gid]["drill"]["live"]["run"].startswith(f"make gotcha-drill ID={gid} LIVE=1 PROJECT=") for gid in KIT_LIVE)
assert all(ENTRIES[gid]["cost"].startswith("Rs 0") for gid in KIT_LIVE)

# ------------------------------------------------------------------ verbatim kit excerpts
GO, MK, OPS = "commands/gotchas.py", "Makefile", "mk/operations.mk"
REG_LINES = REG_TEXT.splitlines()
E_START = next(i for i, line in enumerate(REG_LINES) if '"id": "deploy-drops-hotfix"' in line)
E_END = next(i for i in range(E_START, len(REG_LINES)) if REG_LINES[i] == "    },")
EXCERPTS = {
    "targets": ("mk/operations.mk - the three targets: the registry, the drills, the detectors",
                block(OPS, "# The registry, one line a gotcha; ID=<id> prints every field of one.",
                      end="# ---- An incident's plan from rules")),      # lesson 10.11's section follows in the same file
    "entry": ("ops/gotchas.json - one entry, deploy-drops-hotfix, every field (the braces around it left out)",
              block("ops/gotchas.json", '"id": "deploy-drops-hotfix"', n=E_END - E_START)),
    "flip": ("Makefile - make deploy-services: after the API's deploy, its traffic moves to the new revision by name (F44)",
             block(MK, "# After the API's DEPLOY block, traffic goes to the revision that block just created", n=4)
             + "\n...\n" + block(MK, '@if echo "$(SCRIPTS)" | grep -q lesson-12.2.sh; then', n=4)),
    "extra_env": ("Makefile - make deploy-services: CHAT_EXTRA_ENV, emptied for every deploy",
                  block(MK, 'CHAT_SQL_FLAGS="--add-cloudsql-instances=', n=3)
                  + "\n...\n" + block(MK, 'CHAT_SQL_FLAGS="$$CHAT_SQL_FLAGS" CHAT_EXTRA_ENV="$$CHAT_EXTRA_ENV" \\', n=1)),
    "chat_deploy": ("commands/lesson-12.8.sh - the chat's deploy: its whole environment, with --set-env-vars",
                    block("commands/lesson-12.8.sh", "# 2. The service. The Makefile fills two variables",
                          end="# 2b. Who may call it")),
    "cap": ("services/chat/limits.py and agent.py - the cap, read once when a revision starts, and what /health publishes",
            block("services/chat/limits.py", 'MAX_MODEL_CALLS = int(os.environ.get("CHAT_MAX_MODEL_CALLS", "12"))', n=1)
            + "\n...\n" + block("services/chat/limits.py", "def published() -> dict:", end="def recursion_limit")
            + "\n...\n" + block("services/chat/agent.py", '@app.get("/health")', n=5)),
    "latest": ("commands/limits-drill.sh - latest_takes_all(): a change that must serve needs the latest revision to take the traffic",
               block("commands/limits-drill.sh", "latest_takes_all() {", n=7)),
    "follows": ("commands/gotchas.py - follows_latest(): the same check, on the same JSON",
                block(GO, "def follows_latest(desc: dict) -> bool:", n=3)),
    "drill_pinned": ("commands/gotchas.py - drill_pinned(): the drill, offline on the stand-in and live on your lane",
                     block(GO, "def drill_pinned(lane, entry: dict, say: Callable) -> tuple[bool, bool | None]:")),
    "restore": ("commands/gotchas.py - restore(): what the finally block runs, and what it says when it cannot",
                block(GO, "def restore(lane, say: Callable, before: str | None) -> None:")),
    "deploy_pre": ("commands/gotchas.py - drill_deploy_drop(): the four refusals before anything changes",
                   block(GO, "def drill_deploy_drop(lane, entry: dict, say: Callable) -> tuple[bool, bool | None]:",
                         end='    say(f"{CHAT}: image tag {tag}, nothing the next deploy would change;')),
    "up": ("Makefile - make up deploys every service, and SCRIPTS' default holds the API's script",
           block(MK, "SCRIPTS    = commands/lesson-12.5.sh commands/lesson-12.2.sh commands/lesson-12.3.sh", n=3)
           + "\n...\n" + block(MK, "up: guard-project", n=3)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["targets"].startswith("# The registry") and E["targets"].rstrip().endswith("$(if $(HOURS),--hours $(HOURS),)")
assert E["entry"].startswith('      "id": "deploy-drops-hotfix",') and E["entry"].rstrip().endswith("]")
assert json.loads("{" + E["entry"] + "}")["id"] == "deploy-drops-hotfix"          # the whole entry, and only it
assert "--no-traffic pins the service to a named revision" in E["flip"] and "--to-revisions $$REV=100" in E["flip"]
assert "CHAT_EXTRA_ENV=; \\" in E["extra_env"] and 'CHAT_EXTRA_ENV="$$CHAT_EXTRA_ENV"' in E["extra_env"]
assert E["chat_deploy"].rstrip().endswith('${CHAT_EXTRA_ENV-}"') and "gcloud run deploy documind-chat" in E["chat_deploy"]
assert "CHAT_EXTRA_ENV  extra environment for the service, empty on the lane." in E["chat_deploy"]
assert '"limits": limits.published()}' in E["cap"] and '"max_model_calls": MAX_MODEL_CALLS' in E["cap"]
assert E["latest"].count("latest_takes_all") == 2 and "--to-latest" in E["latest"]
assert 'return any(t.get("latestRevision") and t.get("percent") == 100 for t in traffic(desc))' in E["follows"]
assert E["drill_pinned"].rstrip().endswith("return reproduced, cleared") and "    finally:\n        restore(lane, say, before)" in E["drill_pinned"]
assert E["restore"].rstrip().endswith("raise") and "RESTORE FAILED" in E["restore"]
assert "lane.require_checkout(tag)" in E["deploy_pre"] and "lane.require_admin()" in E["deploy_pre"] and "pending = spec.changes(" in E["deploy_pre"]
assert E["deploy_pre"].count("raise Stop(") == 2 and "def require_checkout(self, tag: str) -> None:" in (KIT / GO).read_text(encoding="utf-8")
LIVE_SRC = (KIT / GO).read_text(encoding="utf-8").split("class Live:", 1)[1].split("# ----------------", 1)[0]
assert LIVE_SRC.count("raise Stop(") >= 2 and "Check out {tag or 'that commit'} (or redeploy " in LIVE_SRC     # the other two refusals
assert "$(MAKE) drift secrets build-access build deploy-services" in E["up"] and "commands/lesson-12.2.sh" in E["up"]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
MAKEFILE = G.makefile()
SPECS, PASSES = G.deploy_specs(), G.deploy_passes(MAKEFILE)
SCRIPTS = G.default_scripts(MAKEFILE)
assert len(SPECS) == len(SCRIPTS) == 7 and "commands/lesson-12.2.sh" in SCRIPTS                 # every deploy: --set-env-vars
assert SPECS[CHAT].script == "commands/lesson-12.8.sh" and SPECS[CHAT].hooks == ["CHAT_EXTRA_ENV"] and CAP not in SPECS[CHAT].writes()
assert PASSES["CHAT_EXTRA_ENV"] == ("recipe", "") and PASSES["ADMIN_EMAILS"] == ("make", "admin@documind.example.com")
assert "ADMIN_EMAILS" in SPECS["documind-admin"].writes() and "ADMIN_EMAILS" in SPECS["documind-ui"].writes()
CHAT_WRITES = sorted(SPECS[CHAT].writes())
CAND_SWITCHES = G.candidate_names(MAKEFILE)
TF_WATCHERS = G.tf_blocks("google_monitoring_alert_policy", "google_logging_metric")
N_POLICIES = len(G.tf_blocks("google_monitoring_alert_policy"))
N_METRICS = len(G.tf_blocks("google_logging_metric"))
assert N_POLICIES + N_METRICS == len(TF_WATCHERS)
PRICES = {}
exec(compile((KIT / "shared" / "prices.py").read_text(encoding="utf-8"), "prices.py", "exec"), PRICES)
FLASH_IN, FLASH_OUT = PRICES["PRICES"][PRICES["DEFAULT_MODEL"]]
assert PRICES["USD_INR"] == 85 and (FLASH_IN, FLASH_OUT) == (1.50, 7.50)
LIM = (KIT / "services/chat/limits.py").read_text(encoding="utf-8")
TURN_INR = float(re.search(r'TURN_BUDGET_INR = float\(os\.environ\.get\("CHAT_TURN_BUDGET_INR", "([\d.]+)"\)\)', LIM).group(1))
CFG = (KIT / "services/rag-api/config.py").read_text(encoding="utf-8")
CTX, ANS = (int(re.search(rf"{k}: int = (\d+)", CFG).group(1)) for k in ("max_context_tokens", "max_answer_tokens"))
RS_ANSWER_MAX = (CTX * FLASH_IN + ANS * FLASH_OUT) / 1_000_000 * PRICES["USD_INR"]
assert (TURN_INR, CTX, ANS) == (5.0, 8000, 2048) and f"{RS_ANSWER_MAX:.2f}" == "2.33"
CD = (KIT / ".github/workflows/documind-cd.yml").read_text(encoding="utf-8")
DRY = (KIT / ".github/workflows/documind-dryrun.yml").read_text(encoding="utf-8")
assert "run: python -m unittest discover -s commands/tests -v" in DRY                 # test_gotchas.py runs in CI
assert "environment: production" in CD and 'make promote PROJECT="$PROJECT" REGION="$REGION"' in CD
TESTS = (KIT / "commands/tests/test_gotchas.py").read_text(encoding="utf-8")
N_TESTS = len(re.findall(r"^    def test_", TESTS, re.M))
assert "def test_a_detector_that_does_not_exist_is_refused(self):" in TESTS and "def test_the_schema(self):" in TESTS
N_BOTH = sum(1 for g in REG["gotchas"] if g["drill"]["offline"] and g["drill"]["live"])
N_DROP_EV = len(ENTRIES["deploy-drops-hotfix"]["evidence"])
HOURS = int(re.search(r'default=int\(os\.environ\.get\("HOURS"\) or (\d+)\)', (KIT / GO).read_text(encoding="utf-8")).group(1))
SMOKE = (KIT / "smoke/smoke_chat.py").read_text(encoding="utf-8")
BRAINS = re.findall(r'"(\w+)"', re.search(r"^BRAINS = \(([^)]*)\)", SMOKE, re.M).group(1))
SMOKE_RECIPE = G.recipe(MAKEFILE, "smoke-chat")
assert BRAINS == ["direct", "langchain", "langgraph", "adk"] and "DOCUMIND_OUTSIDER_SA=" in SMOKE_RECIPE
N_SMOKE = 1 + len(BRAINS) + 1                                     # health, one question per brain, the outsider refused
EVENTARC = (KIT / "terraform/eventarc.tf").read_text(encoding="utf-8")
N_DELIVERIES = int(re.search(r"max_delivery_attempts = (\d+)", EVENTARC).group(1))
assert N_DELIVERIES == 12 and "twelve deliveries over about an hour" in ENTRIES["poison-upload"]["symptom"]
assert not [name for _, name, body in TF_WATCHERS if "vector_search_fallback" in body]   # no policy or metric reads it
# the gaps box: the kit's own account of what has not run on a lane, the plan's hazard and its later gotchas
UNOWNED = (KIT / "UNOWNED.md").read_text(encoding="utf-8")
if "| `commands/gotchas.py` | **11.7**" in UNOWNED:            # the row this page's pull request adopts, while it is there
    assert ("Not yet run against a lane: the live drills, the detectors' reads, and the request-log fields the "
            "tag-audience-401 filter names.") in UNOWNED
PLAN = (ROOT / "plan/cohort-2-lesson-plan-2026-10-07.md").read_text(encoding="utf-8")
assert "### 3.3 Hazards a learner can trigger, named on the pages and fixed after 6 December" in PLAN
assert "- **`make deploy-services` and `make up`** release the API without the gate. 11.2 and 11.7 say so." in PLAN
GAP = (ROOT / "plan/agents-coverage-gap-plan-2026-10-07.md").read_text(encoding="utf-8")
for later in ("ADK sessions live in each gunicorn worker's memory", "A new message on a paused thread drops its interrupt",
              "Cloud Run may rewrite an incoming trace id", "A2A tasks and contextId sessions live in one instance's memory",
              "Breakers and rate windows are per worker and per instance", "A resumed node reruns from its first line"):
    assert later in GAP, later
assert "creates the environment the first time a job names it, with no required reviewer" in (
    KIT / "commands/release.py").read_text(encoding="utf-8")                                 # release.py's claim, unverified
assert 'gc("run", "services", "update-traffic", "documind-chat", "--to-latest")' in (
    ROOT / "lessons/06-context-memory/6.7-restart-isolation/build.py").read_text(encoding="utf-8")   # 6.7 leaves it following

# ------------------------------------------------------------------ the command line, as make's targets run it
T = Path(tempfile.mkdtemp(prefix="lesson117-"))
TOOLS = ("gcloud", "gcloud.cmd", "gcloud.ps1", "bq", "bq.cmd", "gsutil", "gsutil.cmd", "terraform", "terraform.exe")


def iso_env(extra: dict | None = None) -> dict:
    """No Google credential, no gcloud, bq, gsutil or terraform on PATH, a throwaway home: nothing here reaches a lane."""
    env = {k: v for k, v in os.environ.items() if not k.startswith(("GOOGLE_", "CLOUDSDK_"))
           and k not in ("PROJECT", "REGION", "ADMIN_EMAILS", "HOURS", "ID", "LIVE")}
    keep = [p for p in env.get("PATH", "").split(os.pathsep) if p and not any((Path(p) / t).exists() for t in TOOLS)]
    env.update(PATH=os.pathsep.join(keep), HOME=str(T), USERPROFILE=str(T), APPDATA=str(T), CLOUDSDK_CONFIG=str(T / "gcloud"),
               PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1")
    env.update(extra or {})
    return env


def cli(*args: str, cwd: Path = KIT, want: int = 0) -> str:
    """python commands/gotchas.py ARGS, the line each make target runs; stdout then stderr, as a terminal shows them."""
    r = subprocess.run([sys.executable, "commands/gotchas.py", *args], cwd=str(cwd), env=iso_env(), capture_output=True,
                       text=True, encoding="utf-8")
    assert r.returncode == want, (args, r.returncode, r.stdout[-1500:], r.stderr[-1500:])
    return r.stdout + r.stderr


def run_cell(body: str, prelude: str = "", cwd: Path = KIT, env: dict | None = None) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", env=iso_env(env))
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout


OUT = {}
OUT["list"] = cli("list")
OUT["show"] = cli("show", "deploy-drops-hotfix")
OUT["pinned"] = cli("drill", "pinned-traffic")
OUT["drop"] = cli("drill", "deploy-drops-hotfix")
OUT["ungated"] = cli("drill", "ungated-api-release")
ALL = cli("drill")
L = OUT["list"].splitlines()
assert L[0].startswith(f"{N} gotchas in ops/gotchas.json (workshop lesson 11.7).") and [x.split()[0] for x in L[2:]] == list(ENTRIES)
assert OUT["show"].startswith("deploy-drops-hotfix: A routine make deploy-services drops a setting made by hand\n")
assert "  kit        Makefile: CHAT_EXTRA_ENV=; \\\n" in OUT["show"]

# every offline drill: its marker, its lever's line where it has one, and the summary; the board's own counts agree
for gid in OFFLINE:
    off = ENTRIES[gid]["drill"]["offline"]
    assert f"== {gid}, offline (a stand-in, Rs 0): {ENTRIES[gid]['title']}\n" in ALL, gid
    assert "REPRODUCED: " + off["marker"] in ALL, gid
    assert not off["cleared"] or "CLEARED: " + off["cleared"] in ALL, gid
assert "NOT " not in ALL and ALL.rstrip().endswith(f"{len(OFFLINE)} of {len(OFFLINE)} offline drills reproduced their gotcha")
N_CLEARED = sum(1 for gid in OFFLINE if ENTRIES[gid]["drill"]["offline"]["cleared"])
GREP = re.compile(r"^(==|REPRODUCED|CLEARED|NOT|[0-9]+ of)")
OUT["all"] = "\n".join(line for line in ALL.splitlines() if GREP.match(line)) + "\n"
assert OUT["all"].count("REPRODUCED: ") == len(OFFLINE) and OUT["all"].count("CLEARED: ") == N_CLEARED
# each drill's own output is the same with ID= as in the full run: one function, one stand-in each
for key, gid in (("pinned", "pinned-traffic"), ("drop", "deploy-drops-hotfix"), ("ungated", "ungated-api-release")):
    assert OUT[key].rstrip("\n") in ALL, key

# the facts the page reads off the drills
P_ = OUT["pinned"]
FIRST = re.search(r"documind-chat: (documind-chat-\d{5}-\w+) takes 100% of the traffic, following the latest revision; "
                  r"/health: max_model_calls (\d+)", P_)
assert FIRST and FIRST.group(2) == str(DEFAULT_CAP), P_
SECOND = re.search(r"(documind-chat-\d{5}-\w+): made with CHAT_MAX_MODEL_CALLS=3, takes 0% of the traffic; /health: max_model_calls (\d+)", P_)
assert SECOND and SECOND.group(2) == str(DEFAULT_CAP), P_
assert f"{SECOND.group(1)} takes 100% of the traffic; /health: max_model_calls 3\n" in P_
assert P_.rstrip().endswith(f"restored: {CAP} unset, traffic on the latest revision; /health: max_model_calls {DEFAULT_CAP}")
D_ = OUT["drop"]
assert "/health: max_model_calls 8: the hand-set value answers" in D_ and f"{CAP} gone; /health: max_model_calls {DEFAULT_CAP}" in D_
assert "CHAT_EXTRA_ENV='|CHAT_MAX_MODEL_CALLS=8'" in D_ and "/health: max_model_calls 8; the detector, with that deploy: nothing to drop" in D_
assert D_.rstrip().endswith(f"restored: {CAP} unset, traffic on the latest revision; /health: max_model_calls {DEFAULT_CAP}")
U_ = OUT["ungated"]
assert f"(SCRIPTS: {len(SCRIPTS)} scripts, lesson-12.2.sh among them)" in U_ and "no gate judged it" in U_
LOOP = re.search(r"(\d+) calls allowed, the next refused: stopped_by=model_calls, Rs ([\d.]+) spent", ALL)
WATCH = re.search(r"terraform/\*\.tf: (\d+) alert policies and log metrics; none of them reads stopped_by or the chat rows", ALL)
CUT = re.search(r"a search that takes (\d+) s, cut at its (\d+) s budget", ALL)
SPEND = re.search(r"tenant_daily \(terraform/sql/tenant_daily\.sql\) counts the events ([a-z, ]+): Rs ([\d.]+) of this turn", ALL)
AGENT = re.search(r"the agent's own model calls: Rs ([\d.]+), on the chat row alone", ALL)
SINK = re.search(r"terraform's log sink (\w+) copies event chat", ALL)
assert LOOP and LOOP.group(1) == str(DEFAULT_CAP) and WATCH and int(WATCH.group(1)) == len(TF_WATCHERS), (LOOP, WATCH)
assert CUT and SPEND and SPEND.group(1) == "query, stream, media" and AGENT and SINK, (CUT, SPEND, AGENT, SINK)
assert "may_commit() said False" in ALL and "make rollback: ERROR: deploy/.previous-revision is missing" in ALL
assert "QUERY_REWRITE: unset -> on   rode in? no make target sets it on a candidate" in ALL
assert "the next candidate documind-api-00003-rix: GENERATOR_MODEL=gemini-3.6-flsh" in ALL

# ------------------------------------------------------------------ the two Rs 0 drills, the way the kit's tests run them
def drill_on(gid: str, lane) -> tuple[int, list[str]]:
    out: list[str] = []
    return G.run_drill(ENTRIES[gid], out.append, lane), out


def chat_lane(cls=G.StandIn):
    lane = cls()
    G.initial(lane, "pinned-traffic")
    return lane


def chat_env(lane) -> dict:
    return G.literal_env(G.template(G.describe(lane, CHAT))["env"])


lane = chat_lane()
first = G.serving_revision(G.describe(lane, CHAT))
code, out = drill_on("pinned-traffic", lane)
WHERE = f"--region=us-central1 --project={PROJ}"
assert code == 0 and [c for c in lane.calls if c.startswith(("gcloud run services update ", "gcloud run services update-traffic "))] == [
    f"gcloud run services update-traffic {CHAT} --to-revisions={first}=100 {WHERE} --quiet",
    f"gcloud run services update {CHAT} --update-env-vars={CAP}=3 {WHERE} --quiet",
    f"gcloud run services update-traffic {CHAT} --to-latest {WHERE} --quiet",
    f"gcloud run services update {CHAT} --remove-env-vars={CAP} {WHERE} --quiet"], lane.calls
assert G.follows_latest(G.describe(lane, CHAT)) and CAP not in chat_env(lane) and not G.pinned_findings(CHAT, G.describe(lane, CHAT), lane)
lane = chat_lane()
code, out = drill_on("deploy-drops-hotfix", lane)
deploys = [c.split(" (")[0] for c in lane.calls if c.startswith("make deploy-services")]
assert code == 0 and deploys == [f"make deploy-services SCRIPTS=commands/lesson-12.8.sh GIT_SHA=c0ffee1"] * 4, deploys  # first, routine, fork, back
assert CAP not in chat_env(lane) and lane.limits(CHAT)["max_model_calls"] == DEFAULT_CAP and SPECS[CHAT].changes(chat_env(lane)) == []
for gid, fail_on in (("pinned-traffic", "--to-latest"), ("deploy-drops-hotfix", "make deploy-services SCRIPTS=commands/lesson-12.8.sh")):
    lane = chat_lane()
    lane.fail_on = fail_on                                       # a line in the middle fails, once: the finally block restores
    try:
        drill_on(gid, lane)
        raise AssertionError(f"{gid}: the failure did not stop the drill")
    except G.Stop:
        pass
    assert G.follows_latest(G.describe(lane, CHAT)) and CAP not in chat_env(lane), gid


class LaneBranch(G.StandIn):
    """The live drills' path on a stand-in: offline is False, so a drill takes its lane branch (the preconditions asked,
    no fork deploy), while every gcloud line still lands on the stand-in."""
    offline = False

    def __init__(self):
        super().__init__()
        self.asked: list[str] = []

    def require_checkout(self, tag: str) -> None:
        self.asked.append(f"checkout {tag}")

    def require_admin(self) -> None:
        self.asked.append("admin")


lane = chat_lane(LaneBranch)
code, out = drill_on("deploy-drops-hotfix", lane)
assert code == 0 and lane.asked == ["checkout c0ffee1", "admin"] and sum(c.startswith("make deploy-services") for c in lane.calls) == 2
assert ("the lever, carrying the value in the deploy, is a change to your fork: the offline drill shows it "
        "(make gotcha-drill ID=deploy-drops-hotfix)") in out and not any(line.startswith("CLEARED: ") for line in out)
assert any(line.startswith("restored: ") for line in out)
lane = chat_lane(LaneBranch)
code, out = drill_on("pinned-traffic", lane)
assert code == 0 and any(line.startswith("CLEARED: ") for line in out) and lane.asked == []
# the refusals before anything changes: a pinned chat, and a chat with a setting the deploy would drop (6.7's LESSON113_RESTART)
lane = chat_lane()
lane.gcloud("run", "services", "update-traffic", CHAT, f"--to-revisions={first}=100", *lane.where())
before = len(lane.calls)
for fn in (G.drill_pinned, G.drill_deploy_drop):
    try:
        fn(lane, ENTRIES["pinned-traffic" if fn is G.drill_pinned else "deploy-drops-hotfix"], lambda line: None)
        raise AssertionError("no refusal")
    except G.Stop as e:
        assert "follow" in str(e) or "pinned" in str(e), e
assert not [c for c in lane.calls[before:] if " describe " not in c]
lane = chat_lane()
lane.gcloud("run", "services", "update", CHAT, "--update-env-vars=LESSON113_RESTART=1", *lane.where())
try:
    G.drill_deploy_drop(lane, ENTRIES["deploy-drops-hotfix"], lambda line: None)
    raise AssertionError("no refusal")
except G.Stop as e:
    REFUSE_613 = str(e)
assert "LESSON113_RESTART=1: dropped, not in commands/lesson-12.8.sh's --set-env-vars" in REFUSE_613 and "--remove-env-vars=LESSON113_RESTART" in REFUSE_613

# ------------------------------------------------------------------ the cells
def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


READER_PY = r'''import importlib.util, warnings
warnings.filterwarnings("ignore", category=UserWarning)
spec = importlib.util.spec_from_file_location("gotchas", "commands/gotchas.py")
g = importlib.util.module_from_spec(spec)
spec.loader.exec_module(g)                          # the kit's own reader of the deploy scripts: no lane, no network
mk = g.makefile()
specs, passes = g.deploy_specs(), g.deploy_passes(mk)
print(f"make deploy-services runs {len(g.default_scripts(mk))} deploy scripts, and each sets its service's whole environment:")
for name, s in specs.items():
    print(f"  {name:16} {s.script:26} --set-env-vars, {len(s.writes())} variables")
chat = specs["documind-chat"]
print("documind-chat's list: " + ", ".join(sorted(chat.writes())))
print("CHAT_MAX_MODEL_CALLS in it:", "CHAT_MAX_MODEL_CALLS" in chat.writes())
print(f"the script's hook for more: {', '.join(chat.hooks)}, which make deploy-services sets to {passes['CHAT_EXTRA_ENV'][1]!r}")
made = sorted(f"{n}={v}" for n, (how, v) in passes.items() if how == "make" and v)
print("the switches it passes, each back to the Makefile's default unless you pass it: " + ", ".join(made))'''
OUT["reader"] = run_cell(READER_PY)
R_ = OUT["reader"]
assert R_.startswith(f"make deploy-services runs {len(SCRIPTS)} deploy scripts") and "CHAT_MAX_MODEL_CALLS in it: False" in R_
assert "documind-chat's list: " + ", ".join(CHAT_WRITES) in R_ and "which make deploy-services sets to ''" in R_
assert "ADMIN_EMAILS=admin@documind.example.com" in R_ and "ARMOR=off" in R_ and "GENERATOR_MODEL=gemini-3.6-flash" in R_
assert all(f"  {svc:16} {s.script:26} --set-env-vars, {len(s.writes())} variables" in R_ for svc, s in SPECS.items())

REST_PY = r'''import json, os, subprocess, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()


def get(kind, name):
    """One object from Cloud Run's Admin API v1, services or revisions: the JSON gcloud's describe prints."""
    url = f"https://{R}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{P}/{kind}/{name}"
    req = urllib.request.Request(url, headers={"Authorization": "Bearer " + TOKEN})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def env(spec):
    """A revision spec's literal variables, by name; a secret's reference is not one."""
    return {e["name"]: e.get("value", "") for e in spec["containers"][0].get("env", []) if "valueFrom" not in e}


for name in ("documind-chat", "documind-api"):
    svc = get("services", name)
    traffic, made = svc["status"].get("traffic", []), env(svc["spec"]["template"]["spec"])
    print(f"{name}: newest revision {svc['status']['latestCreatedRevisionName']}")
    for t in traffic:
        how = "follows the latest revision" if t.get("latestRevision") else "held by name"
        print(f"  {t.get('percent', 0):>3}%  {t['revisionName']}  {how}" + (f", tag {t['tag']}" if t.get("tag") else ""))
    serving = next((t["revisionName"] for t in traffic if t.get("percent") == 100), None)
    if serving:
        answers = env(get("revisions", serving)["spec"])
        moved = [f"{k} {answers.get(k, 'unset')} -> {made.get(k, 'unset')}" for k in sorted(set(made) | set(answers))
                 if made.get(k) != answers.get(k)]
        print(f"  the template against {serving}: " + ("; ".join(moved) or "the same variables"))
    if name == "documind-chat":
        print(f"  CHAT_MAX_MODEL_CALLS on the template: {made.get('CHAT_MAX_MODEL_CALLS', 'unset (limits.py: CAP_DEFAULT_VALUE)')}")'''.replace(
    "CAP_DEFAULT_VALUE", str(DEFAULT_CAP))

STAND_IN = r'''import io, json, subprocess, urllib.request
WORLD = json.loads(%r)
class _Done:
    def __init__(self, out): self.stdout, self.stderr, self.returncode = out, "", 0
def _run(cmd, **kw):
    assert list(cmd) == ["gcloud", "auth", "print-access-token"], cmd
    return _Done("stand-in-token\n")
subprocess.run = _run
class _Resp(io.BytesIO):
    def __enter__(self): return self
    def __exit__(self, *a): return False
BASE = "https://asia-south1-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/%s/"
def _open(req, timeout=None):
    assert req.get_header("Authorization") == "Bearer stand-in-token" and req.full_url.startswith(BASE), req.full_url
    kind, name = req.full_url[len(BASE):].split("/")
    return _Resp(json.dumps(WORLD[kind][name]).encode())
urllib.request.urlopen = _open
'''


def world(lane) -> str:
    """The stand-in's services and revisions as the Admin API returns them (the same JSON gcloud describe prints)."""
    return json.dumps({"services": {s: lane.describe_json(s) for s in lane.services},
                       "revisions": {r: lane.revision_json(r) for st in lane.services.values() for r in st["order"]}})


REST_ENV = {"PROJECT": PROJ, "REGION": "asia-south1"}
fresh = G.StandIn(PROJ, "asia-south1")
fresh.deploy_services(SCRIPTS, "c0ffee1")                          # every service as make deploy-services leaves it
rest_fresh = run_cell(REST_PY, STAND_IN % (world(fresh), PROJ), env=REST_ENV)
chat0 = G.serving_revision(G.describe(fresh, CHAT))
api0 = G.serving_revision(G.describe(fresh, API))
assert rest_fresh == (f"documind-chat: newest revision {chat0}\n  100%  {chat0}  follows the latest revision\n"
                      f"  the template against {chat0}: the same variables\n"
                      f"  CHAT_MAX_MODEL_CALLS on the template: unset (limits.py: {DEFAULT_CAP})\n"
                      f"documind-api: newest revision {api0}\n  100%  {api0}  held by name\n"
                      f"  the template against {api0}: the same variables\n"), rest_fresh
busy = G.StandIn(PROJ, "asia-south1")                               # a candidate waiting, and the chat pinned with a change
busy.deploy_services(SCRIPTS, "c0ffee1")
busy.make_release_candidate("b2c3d4e")
busy.gcloud("run", "services", "update-traffic", CHAT, f"--to-revisions={chat0}=100", *busy.where())
busy.gcloud("run", "services", "update", CHAT, f"--update-env-vars={CAP}=3", *busy.where())
rest_busy = run_cell(REST_PY, STAND_IN % (world(busy), PROJ), env=REST_ENV)
assert f"  100%  {chat0}  held by name\n" in rest_busy and f"the template against {chat0}: {CAP} unset -> 3" in rest_busy, rest_busy
assert "    0%  documind-api-00002-zeq  held by name, tag candidate" in rest_busy and "GIT_SHA c0ffee1 -> b2c3d4e" in rest_busy, rest_busy

# the Change-it: an entry nobody wrote a drill or a check for, on a throwaway copy of the registry in its own git repo
CHANGE_PY = r'''import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
path = "ops/gotchas.json"
with open(path, encoding="utf-8") as f:
    reg = json.load(f)
made = json.loads(json.dumps(next(g for g in reg["gotchas"] if g["id"] == "pinned-traffic")))     # a copy of one entry
made["id"], made["title"] = "made-up-gotcha", "A gotcha nobody wrote a drill or a check for"
made["detector"]["run"] = "make gotcha-detect ID=made-up-gotcha PROJECT=documind-ai-YOUR-ID REGION=<region>"
made["drill"]["live"]["run"] = "make gotcha-drill ID=made-up-gotcha LIVE=1 PROJECT=documind-ai-YOUR-ID"
reg["gotchas"].append(made)
with open(path, "w", encoding="utf-8", newline="\n") as f:
    json.dump(reg, f, indent=2)
    f.write("\n")
print(f"{path}: {len(reg['gotchas'])} entries, the last one {made['id']}")'''
REPO = T / "kit"
(REPO / "commands").mkdir(parents=True)
(REPO / "ops").mkdir()
shutil.copy2(KIT / "commands" / "gotchas.py", REPO / "commands" / "gotchas.py")
(REPO / "ops" / "gotchas.json").write_bytes((KIT / "ops" / "gotchas.json").read_bytes())


def git(*args: str) -> str:
    r = subprocess.run(["git", "-c", "user.name=lesson117", "-c", "user.email=lesson117@example.com", *args], cwd=str(REPO),
                       env=iso_env(), capture_output=True, text=True, encoding="utf-8")
    assert r.returncode == 0, (args, r.stderr)
    return r.stdout


git("init", "-q")
git("add", "-A")
git("commit", "-q", "-m", "the kit's registry")
changed = run_cell(CHANGE_PY, cwd=REPO)
refused = cli("list", cwd=REPO, want=2)
git("checkout", "--", "ops/gotchas.json")
again = cli("list", cwd=REPO)
OUT["change"] = changed + refused + "exit 2\n" + again.splitlines()[0] + "\n"
assert changed == f"ops/gotchas.json: {N + 1} entries, the last one made-up-gotcha\n", changed
assert refused == ("STOP: gotchas.json breaks its rules: made-up-gotcha: drill.offline names a drill commands/gotchas.py "
                   "does not run; made-up-gotcha: detector.kind is check, and commands/gotchas.py has no check for this id\n"), refused
assert again == OUT["list"] and not git("status", "--porcelain").strip()
shutil.rmtree(T, ignore_errors=True)

CELLS = {
    "list": "make gotchas",
    "show": "make gotchas ID=deploy-drops-hotfix",
    "reader": heredoc(READER_PY),
    "pinned": "make gotcha-drill ID=pinned-traffic",
    "drop": "make gotcha-drill ID=deploy-drops-hotfix",
    "all": "make gotcha-drill | grep -E '^(==|REPRODUCED|CLEARED|NOT|[0-9]+ of)'   # every offline drill, its verdict lines",
    "rest": heredoc(REST_PY),
    "pinned_live": 'make gotcha-drill ID=pinned-traffic LIVE=1 PROJECT="$PROJECT" REGION="$REGION"',
    "drop_live": 'make gotcha-drill ID=deploy-drops-hotfix LIVE=1 PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"',
    "smoke": 'make smoke-chat PROJECT="$PROJECT" REGION="$REGION"',
    "detect": 'make gotcha-detect PROJECT="$PROJECT" REGION="$REGION"',
    "ungated": "make gotcha-drill ID=ungated-api-release",
    "change": (heredoc(CHANGE_PY) + '\npython commands/gotchas.py list; echo "exit $?"   # the command make gotchas runs'
               + "\ngit checkout -- ops/gotchas.json && python commands/gotchas.py list | head -1"),
}
CELL_LABELS = {
    "list": "run in the operator shell, in the kit (reads one file; no lane, no cost)",
    "show": "run in the operator shell, in the kit (one entry, every field)",
    "reader": "run in the operator shell, in the kit (the kit's own reader of the deploy scripts; no lane, no cost)",
    "pinned": "run in the operator shell, in the kit (a stand-in of Cloud Run; no lane, Rs 0)",
    "drop": "run in the operator shell, in the kit (a stand-in of Cloud Run; no lane, Rs 0)",
    "all": "run in the operator shell, in the kit (every offline drill; no lane, Rs 0, a few seconds)",
    "rest": "run in the operator shell, in the kit (reads only: two services and their serving revisions)",
    "pinned_live": "run in the operator shell, in the kit (documind-chat for a few minutes; Rs 0)",
    "drop_live": "run in the operator shell, in the kit (documind-chat: a routine deploy of the chat alone, about four minutes; Rs 0 in model calls)",
    "smoke": f"run in the operator shell, in the kit ({len(BRAINS)} questions, one per brain, and the outsider refused; about Rs 5)",
    "detect": "run in the operator shell, in the kit (reads only)",
    "ungated": "run in the operator shell, in the kit (a stand-in of Cloud Run; no lane, Rs 0)",
    "change": "run in the operator shell, in the kit (edits ops/gotchas.json, then puts it back; no lane, no cost)",
}
STANDIN = "(this drill run on the kit's stand-in of Cloud Run when the page was built: its project, region and revision names are the stand-in's)"
LANE = "(the author's lane, recorded: your revision names, image tag and times are yours)"
OUT_LABELS = {
    "list": "(this command run on the kit when the page was built)",
    "show": "(this command run on the kit when the page was built)",
    "reader": "(this cell run on the kit when the page was built)",
    "pinned": STANDIN, "drop": STANDIN, "ungated": STANDIN,
    "all": "(every offline drill run on the kit when the page was built, filtered as the cell filters it)",
    "change": "(this cell run on a copy of the kit's registry when the page was built)",
}
REC = {"rest": "rest_traffic.txt", "pinned_live": "drill_pinned.txt", "drop_live": "drill_deploy_drop.txt",
       "smoke": "smoke_chat.txt", "detect": "detect_all.txt"}
for key, name in REC.items():
    OUT[key] = pb.recorded(LESSON, name)
    OUT_LABELS[key] = LANE
assert set(CELLS) == set(OUT) == set(CELL_LABELS) == set(OUT_LABELS), (set(CELLS) ^ set(OUT))


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the board: the registry, generated from the file
BOARD = [{"id": g["id"], "title": g["title"], "signal": g["signal"], "signal_by": g.get("signal_by", ""), "status": g["status"],
          "symptom": g["symptom"], "why": g["why_no_eval"], "offline": g["drill"]["offline"], "live": g["drill"]["live"],
          "det": {k: g["detector"].get(k) for k in ("kind", "run", "reads", "finds", "pages", "filter")},
          "lever": g["lever"], "lessons": g["lessons"], "cost": g["cost"], "evidence": g["evidence"]} for g in REG["gotchas"]]
LESSONS = sorted({lid for g in REG["gotchas"] for lid in g["lessons"]}, key=lambda x: tuple(int(p) for p in x.split(".")))


def lesson_name(lid: str) -> str:
    return MANIFEST["modules"][module_key(lid)]["lessons"][lid]["name"]


LESSON_OPTIONS = "".join(f'<option value="{lid}">Lesson {lid}: {html.escape(lesson_name(lid))}</option>' for lid in LESSONS)
UI_JS = r"""var root = document.getElementById('gb'); if (!root) return;
  var $ = function(id){ return document.getElementById(id); };
  var list = $('gb-list'), count = $('gb-count'), fs = $('gb-sig'), fd = $('gb-drill'), fl = $('gb-les'), rows = [], open = -1;
  var card = document.createElement('div'); card.className = 'gb-card'; card.id = 'gb-card'; card.setAttribute('aria-live', 'polite');
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) e.className = cls; if (text != null) e.textContent = text; return e; }
  function sec(title, lines){ card.appendChild(el('b', '', title)); lines.forEach(function(x){ if (x) card.appendChild(el('p', x[1] || '', x[0])); }); }
  function show(i){
    var g = R[i]; open = i; card.textContent = '';
    rows.forEach(function(r, j){ r.setAttribute('aria-expanded', j === i ? 'true' : 'false'); });
    rows[i].parentNode.insertBefore(card, rows[i].nextSibling);
    sec(g.signal === 'loud' ? 'Loud: ' + g.signal_by : 'Silent: nothing pages or goes red on its own', [['Status ' + g.status + '. Lessons ' + g.lessons.join(', ') + '. Cost: ' + g.cost + '.']]);
    sec('Symptom', [[g.symptom]]);
    sec('Why no eval row catches it', [[g.why]]);
    var d = [];
    if (g.offline) { d.push(['Offline, on a stand-in or the kit\'s own code: make gotcha-drill ID=' + g.id, 'gb-mono']); d.push([g.offline.how]);
      d.push(['It prints REPRODUCED: ' + g.offline.marker + (g.offline.cleared ? '; and, with the lever, CLEARED: ' + g.offline.cleared : '') + '.']); }
    if (g.live) { d.push(['On a lane: ' + g.live.run, 'gb-mono']); d.push(['Changes: ' + g.live.changes + '. Restores: ' + g.live.restores + '. Cost: ' + g.live.cost + '.']); }
    sec('Drill', d);
    var t = g.det, dd = [[t.run, 'gb-mono'], ['Reads ' + t.reads + '; finds ' + t.finds + '.']];
    if (t.pages) dd.push(['Pages: the alert policy "' + t.pages + '".']);
    if (t.filter) dd.push(['Filter: ' + t.filter, 'gb-mono']);
    sec('Detector (' + (t.kind === 'log' ? 'a log read' : 'a check') + ')', dd);
    sec('Lever', [[g.lever]]);
    sec('The kit lines it rests on, word for word', g.evidence.map(function(e){ return [e[0] + ': ' + e[1], 'gb-mono']; })); }
  function apply(){
    var s = fs.value, d = fd.value, l = fl.value, n = 0, first = -1;
    R.forEach(function(g, i){
      var ok = (s === 'all' || g.signal === s) && (d === 'all' || (d === 'offline' ? !!g.offline : !!g.live)) && (l === 'all' || g.lessons.indexOf(l) >= 0);
      rows[i].hidden = !ok; if (ok) { n++; if (first < 0) first = i; } });
    count.textContent = n + ' of ' + R.length + ' gotchas';
    if (first < 0) { if (card.parentNode) card.parentNode.removeChild(card); open = -1; rows.forEach(function(r){ r.setAttribute('aria-expanded', 'false'); }); }
    else if (open < 0 || rows[open].hidden) show(first); }
  R.forEach(function(g, i){
    var b = el('button', 'gb-row'); b.type = 'button'; b.setAttribute('aria-expanded', 'false'); b.setAttribute('aria-controls', 'gb-card');
    var name = el('span', 'gb-name'); name.appendChild(el('span', 'gb-id', g.id)); name.appendChild(el('span', 'gb-t', g.title)); b.appendChild(name);
    var tags = el('span', 'gb-tags'); tags.appendChild(el('span', 'gb-tag ' + g.signal, g.signal));
    if (g.offline) tags.appendChild(el('span', 'gb-tag', 'offline'));
    if (g.live) tags.appendChild(el('span', 'gb-tag', 'live'));
    tags.appendChild(el('span', 'gb-tag', g.status)); b.appendChild(tags);
    b.addEventListener('click', function(){ show(i); }); list.appendChild(b); rows.push(b); });
  [fs, fd, fl].forEach(function(x){ x.addEventListener('change', apply); });
  apply();"""
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\nvar R = " + json.dumps(BOARD, ensure_ascii=True, separators=(",", ":")).replace("</", "<\\/")
      + ";\n" + squeeze(UI_JS) + "\n})();\n</script>\n")
assert "<div" not in JS and "<tr" not in JS and "—" not in JS and "–" not in JS

# the board's filter, checked in Node against the registry: every signal, drill and lesson choice shows the entries it should
NODE = ("var R = " + json.dumps(BOARD) + ";\nvar picks = [];\n"
        "['all','loud','silent'].forEach(function(s){ ['all','offline','live'].forEach(function(d){ ['all'].concat(" + json.dumps(LESSONS)
        + ").forEach(function(l){\n  picks.push(R.filter(function(g){ return (s === 'all' || g.signal === s) && (d === 'all' || (d === 'offline' ? !!g.offline : !!g.live))"
        " && (l === 'all' || g.lessons.indexOf(l) >= 0); }).map(function(g){ return g.id; })); }); }); });\n"
        "process.stdout.write(JSON.stringify(picks));\n")
assert "(s === 'all' || g.signal === s) && (d === 'all' || (d === 'offline' ? !!g.offline : !!g.live)) && (l === 'all' || g.lessons.indexOf(l) >= 0)" in UI_JS
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
WANT = [[g["id"] for g in REG["gotchas"] if (s == "all" or g["signal"] == s)
         and (d == "all" or bool(g["drill"][d])) and (lid == "all" or lid in g["lessons"])]
        for s in ("all", "loud", "silent") for d in ("all", "offline", "live") for lid in ["all"] + LESSONS]
assert json.loads(node.stdout) == WANT, "the board's filter disagrees with the registry"


# ------------------------------------------------------------------ the tables the parts carry
def td(label: str, text: str) -> str:
    return f'<td data-label="{label}">{text}</td>'


def code(text: str) -> str:
    return "<code>" + html.escape(text) + "</code>"


SORT_ROWS = []
for g in sorted(REG["gotchas"], key=lambda g: (g["signal"] != "loud", not g["detector"]["pages"])):
    det = g["detector"]
    tells = (f'the alert policy &ldquo;{html.escape(det["pages"])}&rdquo;' if det["pages"]
             else html.escape(g["signal_by"]) if g["signal"] == "loud" else "nothing")
    watch = (code(f"make gotcha-detect ID={g['id']}") + (", a log read, finds " if det["kind"] == "log" else ", a check, finds ")
             + html.escape(det["finds"]))
    SORT_ROWS.append(f"<tr><td>{code(g['id'])}</td>{td('What pages or goes red', tells)}{td('What you watch instead', watch)}</tr>")
SORT_ROWS = "\n".join(SORT_ROWS)

STATS = {
    "N_GOTCHAS": str(N), "N_LOUD": str(len(LOUD)), "N_SILENT": str(len(SILENT)), "N_OPEN": str(len(STATUS["open"])),
    "N_GUARDED": str(len(STATUS["guarded"])), "N_OFFLINE": str(len(OFFLINE)), "N_LIVE": str(len(LIVE)),
    "N_OTHER_LIVE": str(len(OTHER_LIVE)), "N_CHECKS": str(len(CHECK_IDS)), "N_LOGS": str(len(LOG_IDS)),
    "N_CLEARED": str(N_CLEARED), "N_EVIDENCE": str(N_EVIDENCE), "N_EV_FILES": str(len(EV_FILES)), "N_LESSONS": str(len(LESSONS)),
    "N_SCRIPTS": str(len(SCRIPTS)), "N_CHAT_VARS": str(len(CHAT_WRITES)), "N_CAND": str(len(CAND_SWITCHES)),
    "N_POLICIES": str(N_POLICIES), "N_METRICS": str(N_METRICS), "N_WATCHERS": str(len(TF_WATCHERS)), "N_TESTS": str(N_TESTS),
    "CAP_DEFAULT": str(DEFAULT_CAP), "FIRST_REV": FIRST.group(1), "SECOND_REV": SECOND.group(1),
    "LOOP_RS": LOOP.group(2), "CUT_S": CUT.group(1), "CUT_BUDGET": CUT.group(2), "SPEND_RS": SPEND.group(2),
    "AGENT_RS": AGENT.group(1), "SINK": SINK.group(1), "TURN_INR": f"{TURN_INR:g}", "RS_ANSWER_MAX": f"{RS_ANSWER_MAX:.2f}",
    "N_BOTH": str(N_BOTH), "N_DROP_EV": str(N_DROP_EV), "HOURS": str(HOURS), "N_BRAINS": str(len(BRAINS)),
    "N_SMOKE": str(N_SMOKE), "N_DELIVERIES": str(N_DELIVERIES),
    "LESSON_OPTIONS": LESSON_OPTIONS, "SORT_ROWS": SORT_ROWS,
}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print({k: v for k, v in STATS.items() if k not in ("LESSON_OPTIONS", "SORT_ROWS")})
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {N} gotchas ({len(LOUD)} loud, {len(SILENT)} silent), {N_EVIDENCE} evidence lines in {len(EV_FILES)} files | "
      f"{len(OFFLINE)} offline drills reproduced, {N_CLEARED} cleared | the two Rs 0 drills checked on the stand-in as the kit's tests "
      f"check them, and on the lane branch | the REST cell and the Change-it run offline | board filter checked in Node "
      f"on {len(WANT)} choices")
