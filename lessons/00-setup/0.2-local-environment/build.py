"""Build lesson 0.2 from its three parts, the shared template and verbatim kit excerpts.

Reproduce the local environment, read the master diagram and prove a first success. This lesson makes the operator
shell every later lesson starts from: the tools, the clone of the public learner repository in ~/deploy_module_rag,
and ~/rag-shell-venv with the kit's operator pins (commands/session-restart.sh installs and checks them). Then the
master diagram of DocuMind's two workflows, built from the kit's own names; the Rs 0 lane (make chat-local: Ollama
gemma3:4b and a Chroma directory) answering the notice-period question with citations; and make dryrun green, red on
one loosened golden row, and green again.

Build-time proof. The three commands make dryrun runs (extract_documind.py --check, validate.py, evals/run_eval.py)
run against a fresh copy of the kit's tracked files, the files a learner's clone holds, with terraform, tflint and
docker off the PATH so their checks skip as they do on a laptop without them. The page's own cell then loosens lk-06
in that copy, git diff shows the edit, the run goes red with its reason, git checkout repairs it, and the run is green
again. The Rs 0 lane's retrieval runs the kit's own code (local_corpus.seed, documind_tools.retrieve on the local
profile) over the chunks make chat-local seeds, with Chroma stood in by a dictionary that answers the same get().
What only a laptop with Ollama can print (the tool versions, the install's last lines, make chat-local, /health, the
model's answer, and make dryrun with Terraform and Docker installed) is read with pb.recorded(); RUN_LIST.md says how.
"""
import ast
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "0.2"
title = ("<title>Lesson 0.2 Reproduce the local environment, read the master diagram and prove a first success"
         " - the kit on your laptop, two workflows, and a gate that goes red | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the master diagram: DOM boxes in two columns that stack on a phone, lit by module */
.md-pick{display:flex;flex-wrap:wrap;gap:6px;margin-bottom:10px;}
.md-b{font:inherit;font-size:var(--small-size);line-height:1.3;padding:6px 10px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(36px,var(--touch));}
.md-b[aria-pressed="true"]{background:var(--teal);border-color:var(--teal);color:#fff;}
.md-sum{font-size:var(--small-size);line-height:1.55;color:var(--navy);margin:0 0 12px;min-height:3.2em;overflow-wrap:anywhere;}
.md-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:14px;}
.md-h{font-family:var(--mono);font-size:var(--kicker-size);font-weight:700;letter-spacing:1px;text-transform:uppercase;color:var(--navy);margin:0 0 6px;}
.md-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 10px;font-size:13px;line-height:1.45;color:var(--slate);transition:opacity .2s;}
.md-box b{display:block;font-family:var(--mono);font-size:12.5px;color:var(--navy);overflow-wrap:anywhere;}
.md-box code{font-size:12px;}
.md-tags{display:block;font-family:var(--mono);font-size:11px;color:var(--teal);margin-top:4px;}
.md-local{display:none;margin-top:4px;color:#92400e;}
.md-box.loc .md-local{display:block;}
.md-box.on{border:2px solid var(--teal);background:var(--teal-light);}
.md-box.off{opacity:.45;}
.md-dn{text-align:center;color:var(--teal);font-weight:700;line-height:1.3;}
.md-band{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px;}
.md-stores{display:grid;gap:6px;}
.md-sec{margin-top:14px;}
@media (prefers-reduced-motion: reduce){.md-box{transition:none;}}
"""


def kit(rel: str) -> str:
    return (KIT / rel).read_text(encoding="utf-8")


def esc(s: str) -> str:
    return html.escape(s, quote=False)


def num(n: int) -> str:
    """A count as the pages write it: 1,628."""
    return f"{n:,}"


# ------------------------------------------------------------------ facts read from the kit, asserted where prose leans on them
MAKEFILE = kit("Makefile")
SERVICES = re.search(r"^SERVICES\s*=\s*(.+)$", MAKEFILE, re.M).group(1).split()
DOWN = re.search(r"^DOWN_SERVICES\s*=\s*(.+)$", MAKEFILE, re.M).group(1).split()
assert DOWN[:len(SERVICES)] == [f"documind-{s}" for s in SERVICES], (SERVICES, DOWN)   # the Cloud Run names, in the same order
NAME = {s: f"documind-{s}" for s in SERVICES}
for s in ("ingest", "api", "admin", "ui", "chat", "mcp", "agent"):
    assert s in SERVICES, s                                               # the diagram draws each of these
CONFIG = kit("services/rag-api/config.py")
BACKENDS = ast.literal_eval(re.search(r"^RETRIEVAL_BACKENDS = (\(.*?\))", CONFIG, re.M).group(1))
GRAPHS = ast.literal_eval(re.search(r"^GRAPH_BACKENDS = (\(.*?\))", CONFIG, re.M).group(1))
MANAGED = ast.literal_eval(re.search(r"^MANAGED_BACKENDS = (\(.*?\))", CONFIG, re.M).group(1))
OWN = tuple(b for b in BACKENDS if b not in MANAGED)
assert OWN == ("vector", "firestore") and MANAGED == ("rag_engine", "vertex_search"), (OWN, MANAGED)
EMBED = re.search(r"^EMBEDDING_MODEL\s*\?=\s*(\S+)", MAKEFILE, re.M).group(1)
GEN = re.search(r"^GENERATOR_MODEL\s*\?=\s*(\S+)", MAKEFILE, re.M).group(1)
EVENTARC = kit("terraform/eventarc.tf")
TOPIC = re.search(r'resource "google_pubsub_topic" "ingest" \{ name = "([^"]+)" \}', EVENTARC).group(1)
DLQ = re.search(r'resource "google_pubsub_topic" "ingest_dlq" \{ name = "([^"]+)" \}', EVENTARC).group(1)
PUSH = re.search(r'resource "google_pubsub_subscription" "ingest_push" \{\s*name\s*=\s*"([^"]+)"', EVENTARC).group(1)
ATTEMPTS = int(re.search(r"max_delivery_attempts = (\d+)", EVENTARC).group(1))
assert 'name                        = "${var.project_id}-uploads"' in kit("terraform/storage.tf")
BUCKET = "documind-ai-YOUR-ID-uploads"                                   # the placeholder project's uploads bucket
INDEX_NAME = re.search(r'display_name = "([^"]+)"', kit("terraform/vector.tf")).group(1)
FRONT = kit("services/frontend/app.py")
UI_PAGES = ast.literal_eval(re.search(r'pages = \[[^\]]*\] if is_admin\(user\) else (\[[^\]]*\])', FRONT).group(1))
assert 'pages.insert(1, "Desk")' in FRONT
UI_PAGES.insert(1, "Desk")                                               # what every roster member sees
assert "RETRIEVAL_GRAPH ?= off" in MAKEFILE                               # the graph is off until it is built and asked for

PROFILE_PY = kit("shared/profile.py")
LOCAL_MODEL = re.search(r'LOCAL_MODEL = os.environ.get\("DOCUMIND_LOCAL_MODEL", "([^"]+)"\)', PROFILE_PY).group(1)
CHROMA_DIR = re.search(r'CHROMA_DIR = os.environ.get\("DOCUMIND_CHROMA_DIR", "([^"]+)"\)', PROFILE_PY).group(1)
CHROMA_COLL = re.search(r'CHROMA_COLLECTION = "([^"]+)"', PROFILE_PY).group(1)
assert "DeterministicFakeEmbedding(size=768)" in PROFILE_PY
# make chat-local: the seed runs from the kit's root, the service from services/chat. CHROMA_DIR is relative, so the two
# lines open two different directories unless DOCUMIND_CHROMA_DIR names one; the page says to set it, and why.
CHAT_LOCAL = block("Makefile", "chat-local:", n=4)
assert CHAT_LOCAL.splitlines()[0] == "chat-local:", CHAT_LOCAL
assert CHAT_LOCAL.splitlines()[1].strip() == "DOCUMIND_PROFILE=local $(PY) -m shared.local_corpus acme", CHAT_LOCAL
assert CHAT_LOCAL.splitlines()[2].strip() == "cd services/chat && DOCUMIND_PROFILE=local PYTHONPATH=../.. \\", CHAT_LOCAL
assert CHROMA_DIR.startswith("./") and "DOCUMIND_CHROMA_DIR" not in MAKEFILE, "the chat-local note on the page is stale"
PORT = re.search(r"--port (\d+)", CHAT_LOCAL).group(1)
TOOLS_PY = kit("shared/documind_tools.py")
assert '"local corpus is empty - run: python -m shared.local_corpus"' in TOOLS_PY        # what an empty store answers
assert "EVIDENCE_FLOOR = 0.5" in TOOLS_PY and 'EVIDENCE_MODE = "set"' in TOOLS_PY        # the gate: half the question's information
assert "CHUNK_CHARS, CHUNK_OVERLAP = 2000, 200" in kit("shared/documind_corpus.py")     # the two cutting rules' window
assert "documind_chroma" not in kit(".gitignore") and "documind_threads" not in kit(".gitignore")       # git status lists both
assert ".DEFAULT_GOAL := dryrun" in MAKEFILE
AGENT_PY = kit("services/chat/agent.py")
assert 'path = os.environ.get("DOCUMIND_THREADS_DB", "./documind_threads.db")' in AGENT_PY
assert 'tenant_id = os.environ.get("LOCAL_TENANT", "acme")' in AGENT_PY
assert 'return {"email": os.environ.get("LOCAL_USER", "dev@documind.local"), "assertion": None}' in AGENT_PY
BRAINS_PY = kit("services/chat/brains.py")
BRAINS = ast.literal_eval(re.search(r"^BRAINS = (\(.*?\))", BRAINS_PY, re.M).group(1))
TOP_K = int(re.search(r'r = documind_tools\.retrieve\(question, tenant_id=context\.get\("tenant_id", ""\), top_k=(\d+),', BRAINS_PY).group(1))
assert "dryrun: check validate eval" in MAKEFILE
assert 'DEFAULT_BRAIN = os.environ.get("DOCUMIND_BRAIN", "langchain")' in BRAINS_PY and "direct" in BRAINS
assert 'if PROFILE == "local":\n        return 0.0' in kit("shared/prices.py")      # the local lane prices every call at 0
CHAT_REQ = kit("services/chat/requirements-local.txt")
assert "Installed ON TOP of requirements.txt, never instead of it, and never in the image:" in CHAT_REQ
CI = kit(".github/workflows/documind-dryrun.yml")
CI_PY = re.search(r'python-version: "([^"]+)"', CI).group(1)
CI_TF = re.search(r'terraform_version: "([^"]+)"', CI).group(1)
TF_MIN = re.search(r'required_version = ">= ([0-9.]+)"', kit("terraform/backend.tf")).group(1)
assert "tuple(map(int, match.groups())) < (1, 9, 0)" in kit("commands/session-restart.sh") and TF_MIN == "1.9.0"
DOCKERFILES = sorted((KIT / "services").glob("*/Dockerfile"))
BASES = [re.search(r"^FROM\s+(\S+)", p.read_text(encoding="utf-8"), re.M).group(1) for p in DOCKERFILES]
N_IMAGES, N_PY312 = len(BASES), sum(b == "python:3.12-slim" for b in BASES)
assert CI_PY == "3.12" and "sys.version_info[:2] != (3, 12)" in kit("commands/session-restart.sh")
assert "gcloud builds submit" in MAKEFILE                                # make up builds its images with Cloud Build

# the operator install: commands/session-restart.sh, the files it installs and the checks it makes, counted its way
RESTART = kit("commands/session-restart.sh")
_dep = RESTART[RESTART.index("<<'RAG_DEPENDENCIES'") + len("<<'RAG_DEPENDENCIES'"):]
_dep = _dep[_dep.index("\n") + 1:_dep.index("\nRAG_DEPENDENCIES\n")]
_vals = {n.targets[0].id: n.value for n in ast.parse(_dep).body
         if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name)}
REQ_FILES = ast.literal_eval(_vals["files"])
PINS = dict(ast.literal_eval(_vals["expected"]))
N_IMPORTS = len(ast.literal_eval(_vals["checks"]))
for _rel in REQ_FILES:
    for _line in kit(_rel).splitlines():
        _line = _line.split("#", 1)[0].strip()
        if _line:
            _m = re.fullmatch(r'([A-Za-z0-9][A-Za-z0-9_.-]*)(?:\[[A-Za-z0-9_,.-]+\])?==([^\s;]+)', _line)
            assert _m, _line
            PINS[re.sub(r'[-_.]+', '-', _m[1]).lower()] = _m[2]
N_PINS = len(PINS)
assert "google-cloud-firestore" in PINS                                    # the shared block's pip line is covered
assert "\"$executable\" -m pip install \"${requirements[@]}\" numpy 'rank-bm25==0.2.2'" in RESTART
PASS_DEPS = f"PASS: {N_PINS} source-pinned packages and {N_IMPORTS} operator imports are available."
assert "rag_save_session() (" in RESTART and "rag_resume() {" in RESTART and "rag_check_python_dependencies || return" in RESTART

# the corpus and the golden set
REAL = json.loads(kit("evals/real_sources.json"))
N_REAL = len(REAL)
N_STATUTE = sum(d["doc_type"] == "statute" for d in REAL)
N_GUIDE = sum(d["doc_type"] == "guidance" for d in REAL)
assert N_STATUTE + N_GUIDE == N_REAL
SCANNED = [d for d in REAL if not d["text_layer"]]
assert [d["slug"] for d in SCANNED] == ["posh_act_2013"]
TENANTS = sorted(p.name for p in (KIT / "evals/corpus").iterdir() if p.is_dir())
assert TENANTS == ["acme", "globex", "zeta"], TENANTS
NOTICE = {t: re.search(r"serves a notice period of (\d+) days", kit(f"evals/corpus/{t}/{h}.md")).group(1)
          for t, h in (("acme", "hr_policy_2026"), ("zeta", "hr_policy_zeta_2026"))}
assert not list((KIT / "evals/corpus/globex").glob("hr_policy*")), "globex has a handbook now"
SYNTHETIC = {"acme": ["hr_policy_2026", "msa_acme_2026", "inv_2026_0412", "annual_report_2026", "townhall_2026_q1"],
             "zeta": ["hr_policy_zeta_2026", "msa_zeta_2026"], "globex": ["msa_globex_2026"]}
_real_slugs = {d["slug"] for d in json.loads(kit("evals/real_sources.json"))}
for _t, _docs in SYNTHETIC.items():                                       # every text document a tenant holds, and no more
    _texts = {p.stem for p in (KIT / "evals/corpus" / _t).glob("*.md")}
    assert _texts == set(_docs) | {s for s in _real_slugs if (KIT / "evals/corpus" / _t / f"{s}.md").is_file()}, (_t, _texts)
SERVICE_DIRS = sorted(p.parent.name for p in (KIT / "services").glob("*/Dockerfile"))
DEPLOYED_DIRS = {"ingest": "ingest", "api": "rag-api", "admin": "admin", "ui": "frontend", "chat": "chat", "mcp": "mcp", "agent": "agent"}
EXTRA_DIRS = [d for d in SERVICE_DIRS if d not in DEPLOYED_DIRS.values()]
assert set(DEPLOYED_DIRS) == set(SERVICES) and EXTRA_DIRS == ["gchat", "gemma-vllm", "litellm", "slm"], EXTRA_DIRS
N_TF = len(list((KIT / "terraform").glob("*.tf")))
INV = kit("evals/corpus/acme/inv_2026_0412.md")
assert "Synthetic document. PAN, GSTIN, mobile and Aadhaar below are invented." in INV
PAN = re.search(r"^PAN: (\S+)$", INV, re.M).group(1)
GSTIN = re.search(r"^GSTIN: (\S+)$", INV, re.M).group(1)
MOBILE = re.search(r"^Contact / \S+: (\+\d+)$", INV, re.M).group(1)
GOLDEN = [json.loads(line) for line in kit("evals/golden.jsonl").split("\n") if line.strip()]
SHAPES = {}
for _r in GOLDEN:
    SHAPES[_r["shape"]] = SHAPES.get(_r["shape"], 0) + 1
LK06 = next(r for r in GOLDEN if r["id"] == "lk-06")
QUESTION = LK06["question"]
assert LK06["must_contain"] == ["60"] and LK06["must_retrieve"][0] == "NP-03" and LK06["answerable"], LK06
assert NOTICE["acme"] == LK06["must_contain"][0] and NOTICE["zeta"] != NOTICE["acme"], NOTICE
VR01 = next(r for r in GOLDEN if r["id"] == "vr-01")
assert VR01["question"] == QUESTION and VR01["must_contain"] == ["60"]   # the version row asks the same question
REQUIRED = json.loads(kit("evals/required.json"))["ids"]

# validate.py: the checks main() runs, in order, and the kit's own list of them
VALIDATE = kit("validate.py")
_main = next(n for n in ast.parse(VALIDATE).body if isinstance(n, ast.FunctionDef) and n.name == "main")
_loop = next(n for n in ast.walk(_main) if isinstance(n, ast.For) and isinstance(n.iter, ast.Tuple))
CHECK_FNS = [e.id for e in _loop.iter.elts]
N_CHECKS = len(CHECK_FNS)
CHECK_NAMES = [f.replace("check_", "") for f in CHECK_FNS]
CHECK_NAMES[CHECK_NAMES.index("pycompile")] = "py_compile"
CHECK_NAMES[CHECK_NAMES.index("pin_consistency")] = "pins"
CHECK_NAMES[CHECK_NAMES.index("shared_deps")] = "shared-deps"
CHECK_NAMES[CHECK_NAMES.index("copy_paths")] = "copy-paths"
_doc = VALIDATE[VALIDATE.index("Checks (each -> PASS / WARN / FAIL / SKIP):"):VALIDATE.index("USAGE")]
N_LISTED = max(int(n) for n in re.findall(r"^\s*(\d+)\. ", _doc, re.M))
assert re.search(r"^\s*3b\. shared-deps", _doc, re.M) and N_LISTED + 1 == len(CHECK_FNS), (N_LISTED, CHECK_FNS)
TOOL_CHECKS = ("terraform", "tflint", "docker")                          # each skips when its tool is not on the PATH
assert all(f'shutil.which("{t}")' in VALIDATE for t in TOOL_CHECKS), "a tool check no longer skips without its tool"


# ------------------------------------------------------------------ a fresh copy of the kit, the files a learner's clone holds
GIT = shutil.which("git")
assert GIT, "git is needed to copy the tracked kit files"
TRACKED = subprocess.run([GIT, "ls-files", "-z", "--", "deploy"], cwd=str(ROOT), capture_output=True, check=True).stdout
TMP = Path(tempfile.mkdtemp(prefix="lesson02-"))
CLONE = TMP / "deploy_module_rag"
for rel in (p for p in TRACKED.decode("utf-8").split("\0") if p):
    src = ROOT / rel
    if not src.is_file():
        continue                                   # deleted in the working tree: not in the next commit either
    dst = CLONE / rel[len("deploy/"):]
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
(TMP / "gitconfig").write_text("", encoding="utf-8")

# no cloud identity, no tool that would reach out: terraform, tflint and docker leave the PATH, so their checks skip
_hidden = ("terraform", "tflint", "docker", "gcloud")
PATH = os.pathsep.join(d for d in os.environ.get("PATH", "").split(os.pathsep)
                       if d and not any(shutil.which(t, path=d) for t in _hidden))
ENV = {k: v for k, v in os.environ.items()
       if not k.startswith(("GOOGLE_", "CLOUDSDK_", "GITHUB_", "DOCUMIND_", "GIT_", "PYTHONPATH", "VIRTUAL_ENV"))}
ENV.update(PATH=PATH, HOME=str(TMP), USERPROFILE=str(TMP), APPDATA=str(TMP), CLOUDSDK_CONFIG=str(TMP / "gcloud"),
           PYTHONIOENCODING="utf-8", PYTHONUTF8="1", PYTHONDONTWRITEBYTECODE="1", PYTHONUNBUFFERED="1",
           GIT_CONFIG_GLOBAL=str(TMP / "gitconfig"), GIT_CONFIG_NOSYSTEM="1")
assert not any(shutil.which(t, path=PATH) for t in _hidden)


def run(args, env=None, stdin=None, ok=(0,)) -> tuple:
    """One command in the copy, as a learner runs it from the kit's root. Returns (exit code, stdout)."""
    r = subprocess.run(args, cwd=str(CLONE), input=stdin, capture_output=True, text=True, encoding="utf-8",
                       env={**ENV, **(env or {})})
    assert r.returncode in ok and not r.stderr.strip(), (args, r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.returncode, r.stdout


def git(*args) -> str:
    return run([GIT, "-c", "core.autocrlf=false", "-c", "core.safecrlf=false", "-c", "color.ui=false", *args])[1]


def dryrun() -> tuple:
    """make dryrun's three recipes (check, validate, eval), run the way the Makefile runs them. Returns the eval exit
    code and what the three printed, in order. validate.py's per-check seconds are your machine's: written as N."""
    _, a = run([sys.executable, "extract_documind.py", "--check"])
    _, b = run([sys.executable, "validate.py"])
    rc, c = run([sys.executable, "evals/run_eval.py"], ok=(0, 1))
    b = re.sub(r"\(\d+s\)$", "(Ns)", b, flags=re.M)
    b = re.sub(r" · \d+s$", " · Ns", b, flags=re.M)
    return rc, (a + b + c).rstrip("\n")


git("-c", "init.defaultBranch=main", "init", "-q")
git("add", "-A")                                 # the index stands in for the commit a fresh clone checks out

# 1. make dryrun, green
RC1, GREEN = dryrun()
assert RC1 == 0, GREEN
VAL_LINES = re.findall(r"^  \[(PASS|WARN|FAIL|SKIP)\] (\S+)", GREEN, re.M)
assert [c for _, c in VAL_LINES[:N_CHECKS]] == CHECK_NAMES, (VAL_LINES, CHECK_NAMES)
VERDICT = dict((c, v) for v, c in VAL_LINES[:N_CHECKS])
for t in TOOL_CHECKS:
    assert VERDICT[t] == "SKIP", (t, VERDICT)
assert VERDICT["extract"] == "SKIP" and VERDICT["copy-paths"] == "WARN", VERDICT
COUNT = {k: sum(1 for v in VERDICT.values() if v == k) for k in ("PASS", "WARN", "FAIL", "SKIP")}
assert f"  {COUNT['PASS']} pass · {COUNT['WARN']} warn · {COUNT['FAIL']} fail · {COUNT['SKIP']} skip · Ns" in GREEN, GREEN
EVAL_HEAD = re.search(r"^  (\d+) golden rows over (\d+) tenants, (\d+) documents$", GREEN, re.M)
assert int(EVAL_HEAD.group(1)) == len(GOLDEN) and int(EVAL_HEAD.group(2)) == len(TENANTS), EVAL_HEAD.group(0)
N_TEXT_DOCS = int(EVAL_HEAD.group(3))
for name in ("falsifiable", "anchors", "coverage"):
    assert f"  [PASS] {name}" in GREEN
assert "The golden set is sound. It can go red, and it still contains the rows that would." in GREEN
N_PASS_GREEN = GREEN.count("[PASS]")
N_EVAL_CHECKS = len(re.findall(r"^  \[(?:PASS|FAIL)\] ", GREEN.split("== eval gate", 1)[1], re.M))
assert N_EVAL_CHECKS == 3 and N_PASS_GREEN == COUNT["PASS"] + N_EVAL_CHECKS
N_PYFILES = int(re.search(r"\[PASS\] py_compile\s+(\d+) python files parse", GREEN).group(1))
WARN_LINE = re.search(r"^  \[WARN\] copy-paths.*$", GREEN, re.M).group(0)
assert "services/slm/build/" in WARN_LINE and "make deploy-slm" in WARN_LINE

# 2. the page's own cell loosens lk-06 in the copy
LOOSEN_PY = '''import json, warnings; warnings.filterwarnings("ignore", category=UserWarning)
path = "evals/golden.jsonl"
lines = open(path, encoding="utf-8").read().split("\\n")
for i, line in enumerate(lines):
    if line.strip() and json.loads(line)["id"] == "lk-06":   # the notice-period row the lane answered
        row = json.loads(line)
        print("lk-06 must_contain before:", row["must_contain"])
        row["must_contain"] = []                              # loosened: any answer at all would now pass
        lines[i] = json.dumps(row, ensure_ascii=False)
        print("lk-06 must_contain after: ", row["must_contain"])
open(path, "w", encoding="utf-8", newline="\\n").write("\\n".join(lines))'''
_, LOOSEN_OUT = run([sys.executable, "-"], stdin=LOOSEN_PY)
assert LOOSEN_OUT == "lk-06 must_contain before: ['60']\nlk-06 must_contain after:  []\n", LOOSEN_OUT

# 3. git diff: one line changed, the row's must_contain emptied
DIFF = git("diff", "--no-ext-diff", "-U0").rstrip("\n")
assert DIFF.startswith("diff --git a/evals/golden.jsonl b/evals/golden.jsonl"), DIFF
_minus = [ln for ln in DIFF.splitlines() if ln.startswith("-{")]
_plus = [ln for ln in DIFF.splitlines() if ln.startswith("+{")]
assert len(_minus) == len(_plus) == 1 and _minus[0][1:].replace('"must_contain": ["60"]', '"must_contain": []') == _plus[0][1:], DIFF

# 4. make dryrun, red: one FAIL with its reason, everything else as before
RC2, RED = dryrun()
assert RC2 == 1, RED
FAIL_REASON = "lk-06: an answerable row with no must_contain accepts any answer at all"
assert f"  [FAIL] falsifiable\n         {FAIL_REASON}\n  [PASS] anchors\n  [PASS] coverage" in RED, RED
assert "  1 problem(s). The golden set cannot judge the model until it judges itself." in RED
assert RED.split("== eval gate")[0] == GREEN.split("== eval gate")[0]     # validate.py did not change its mind
N_PASS_RED, N_FAIL_RED = RED.count("[PASS]"), RED.count("[FAIL]")
assert (N_PASS_RED, N_FAIL_RED) == (N_PASS_GREEN - 1, 1)

# 5. the repair: git puts the committed row back, and the run is green again
git("checkout", "--", "evals/golden.jsonl")
assert git("diff", "--stat") == ""
RC3, AGAIN = dryrun()
assert RC3 == 0 and AGAIN == GREEN
AGAIN_TAIL = "== eval gate" + AGAIN.split("== eval gate", 1)[1]

# 6. the Rs 0 lane's retrieval: the kit's code over what make chat-local seeds, Chroma stood in
LOCAL = {"DOCUMIND_PROFILE": "local"}
STORE_PRELUDE = '''import types
import shared.profile as _profile


class _Store:
    """Chroma's add_texts() and get() over a dict: what make chat-local writes, without the database."""

    def __init__(self):
        self.rows = {}
        self._collection = types.SimpleNamespace(count=lambda: len(self.rows))

    def add_texts(self, texts, metadatas, ids):
        for text, meta, cid in zip(texts, metadatas, ids):
            self.rows[cid] = (text, dict(meta))

    def get(self, ids=None, where=None, include=None):
        conds = [] if not where else (where["$and"] if "$and" in where else [where])

        def ok(meta):
            for cond in conds:
                for key, want in cond.items():
                    if isinstance(want, dict) and "$in" in want:
                        if meta.get(key) not in want["$in"]:
                            return False
                    elif meta.get(key) != want:
                        return False
            return True
        keep = [(cid, t, m) for cid, (t, m) in self.rows.items() if (ids is None or cid in ids) and ok(m)]
        return {"ids": [k[0] for k in keep], "documents": [k[1] for k in keep], "metadatas": [k[2] for k in keep]}


_store = _Store()
_profile.build_store = lambda embeddings=None: _store
'''
# make chat-local's first line: python -m shared.local_corpus acme, run as the Makefile runs it
_, SEED_OUT = run([sys.executable, "-"], env=LOCAL, stdin=STORE_PRELUDE + (
    'import runpy, sys\nsys.argv = ["shared.local_corpus", "acme"]\nrunpy.run_module("shared.local_corpus", run_name="__main__")\n'))
SEED_LINE = SEED_OUT.strip()
_m = re.fullmatch(r"seeded (\d+) chunks for tenant 'acme' into the local store", SEED_LINE)
assert _m, SEED_LINE
N_ACME = int(_m.group(1))

# the three tenants' chunks and documents, as local_corpus would seed each
_, _counts = run([sys.executable, "-"], env=LOCAL, stdin=(
    "import json\nfrom shared import local_corpus as lc\nout = {}\n"
    "for t in ('acme', 'zeta', 'globex'):\n    ch = lc.chunks_for(t)\n"
    "    out[t] = [len(ch), len({c['source_uri'] for c in ch}), sorted({c['doc_type'] for c in ch})]\nprint(json.dumps(out))\n"))
CHUNKS = json.loads(_counts)
assert CHUNKS["acme"][0] == N_ACME
assert CHUNKS["acme"][1] == N_REAL - len(SCANNED) + len(SYNTHETIC["acme"]), CHUNKS   # the real mirrors and the synthetic documents
ALL_CHUNKS = sum(v[0] for v in CHUNKS.values())

# the cell the page shows: read the store make chat-local seeded, then the one retrieve() the direct brain calls
READ_PY = f'''import warnings; warnings.filterwarnings("ignore", category=UserWarning)
from shared.profile import CHROMA_COLLECTION, build_store
from shared import documind_tools as dt
store = build_store()                                  # the directory make chat-local seeded
print(store._collection.count(), "chunks in the collection", CHROMA_COLLECTION)
m = store.get(ids=["acme:hr_policy_2026#NP-03"], include=["metadatas"])["metadatas"][0]
print("NP-03:", m["source_uri"], "| page", m["page"], "|", m["section"])
out = dt.retrieve("{QUESTION}", tenant_id="acme", top_k={TOP_K})
print("answerable", out["answerable"], "| confidence", out["confidence"])
for c in out["citations"]:
    print(f'{{c["score"]:5.3f}}  {{c["chunk_id"]:40}}  page {{c["page"]}}')
print(out["citations"][0]["quote"])'''
_, READ_OUT = run([sys.executable, "-"], env=LOCAL, stdin=STORE_PRELUDE + (
    "from shared import local_corpus as _lc\n_lc.seed(store=_store, tenant_id='acme')      # what make chat-local's first line did\n") + READ_PY)
CITES = re.findall(r"^([01]\.\d{3})  (\S+)\s+page (\d+)$", READ_OUT, re.M)
assert len(CITES) == TOP_K, READ_OUT                                      # the direct brain asks for TOP_K, and gets them
TOP_ID, TOP_SCORE = CITES[0][1], CITES[0][0]
assert READ_OUT.splitlines()[0] == f"{N_ACME} chunks in the collection {CHROMA_COLL}", READ_OUT
assert TOP_ID == "acme:hr_policy_2026#NP-03" and TOP_SCORE == "1.000", CITES
assert "answerable True | confidence high" in READ_OUT
assert "serves a notice period of 60 days" in READ_OUT
NEXT_BEST = CITES[1][0]
N_STATUTE_CITES = sum(1 for _, cid, _ in CITES[1:] if not cid.startswith("acme:hr_policy_2026#"))

# the ranking does not depend on the order Chroma hands the rows back: no tie at the top six
_, _ties = run([sys.executable, "-"], env=LOCAL, stdin=STORE_PRELUDE + f'''import json, re
from shared import local_corpus as lc, documind_tools as dt
lc.seed(store=_store, tenant_id="acme")
got = _store.get(where={{"tenant_id": "acme"}}, include=["documents", "metadatas"])
ranked, idf = dt._lexical_rank("{QUESTION}", list(zip(got["documents"], got["metadatas"])))
keys = [(round(s, 9), len(h), len(t)) for s, h, t, m in ranked[:{TOP_K + 1}]]
top = [[m["chunk_id"], sorted(h), len(re.findall(r"[a-z0-9]+", t.lower())),
        {{w: sorted({{k for k in re.findall(r"[a-z0-9]+", t.lower()) if dt._match(w, k)}}) for w in h}}] for s, h, t, m in ranked[:{TOP_K}]]
print(json.dumps({{"distinct": len(set(keys)) == len(keys), "words": sorted(idf), "top": top,
                  "candidates": len(ranked), "n": len(got["ids"])}}))
''')
TIES = json.loads(_ties)
assert TIES["distinct"], TIES
WORDS = TIES["words"]
TOP5 = TIES["top"]
assert [t[0] for t in TOP5] == [c[1] for c in CITES], (TOP5, CITES)
assert TOP5[0][1] == WORDS, TOP5[0]                                       # NP-03 holds every content word of the question
N_TOP_WORDS = TOP5[0][2]
N_CANDIDATES = TIES["candidates"]                                        # chunks sharing at least one word with the question
assert TIES["n"] == N_ACME
REST_LEN = [t[2] for t in TOP5[1:]]
assert min(REST_LEN) > 5 * N_TOP_WORDS, REST_LEN                          # the runners-up are long statute windows
_statutes = {d["slug"] for d in REAL if d["doc_type"] == "statute"}
assert all(t[0].split(":", 1)[1].split("#", 1)[0] in _statutes for t in TOP5[1:]), TOP5   # the runners-up are all Acts
# "confirmed" reaches three of them only through the five-letter prefix rule of _match(): confiscation, confinement
FRIENDS = sorted({k for t in TOP5[1:] for k in t[3].get("confirmed", []) if not k.startswith("confirm")})
N_FRIEND_CHUNKS = sum(1 for t in TOP5[1:] if t[3].get("confirmed") and not any(k.startswith("confirm") for k in t[3]["confirmed"]))
assert "confiscation" in FRIENDS and "confinement" in FRIENDS and N_FRIEND_CHUNKS == 3, (FRIENDS, N_FRIEND_CHUNKS)
assert "token[:5] == word[:5]" in kit("shared/documind_tools.py")

# the Desk's door lets this question through to the brain, and the local profile prices a model call at zero
_, _door = run([sys.executable, "-"], env=LOCAL, stdin=(
    f'from shared import desk_rules, prices\nq = "{QUESTION}"\nprint(desk_rules.gate(q), desk_rules.mask(q)[1], prices.usd("{LOCAL_MODEL}", 1000, 1000))\n'))
assert _door.strip() == "None [] 0.0", _door

shutil.rmtree(TMP, ignore_errors=True)

# ------------------------------------------------------------------ what only a laptop can print, recorded once from the author's run
REC = {name: pb.recorded(LESSON, name) for name in (
    "tool_checks.txt", "install_check.txt", "chat_local.txt", "chat_health.txt", "chat_answer.txt", "dryrun_tools.txt")}


def recorded(name: str) -> bool:
    return not REC[name].startswith("[awaiting the author's run:")


if recorded("install_check.txt"):
    assert PASS_DEPS in REC["install_check.txt"], "install_check.txt does not match the kit's pins"
if recorded("chat_local.txt"):
    assert SEED_LINE in REC["chat_local.txt"], "chat_local.txt does not seed what the build seeded"
if recorded("chat_health.txt"):
    assert '"profile": "local"' in REC["chat_health.txt"], REC["chat_health.txt"]
if recorded("chat_answer.txt"):
    assert TOP_ID in REC["chat_answer.txt"] and "60" in REC["chat_answer.txt"], REC["chat_answer.txt"]
    assert "cost Rs 0.0" in REC["chat_answer.txt"], REC["chat_answer.txt"]
if recorded("dryrun_tools.txt"):
    assert "The golden set is sound." in REC["dryrun_tools.txt"] and "Tier-A offline dry run" in REC["dryrun_tools.txt"]


# ------------------------------------------------------------------ the shared shell block every later lesson opens with
SHARED = setup_section()
_sm = re.search(r'<div class="cw"><div class="ch-bar"><span>bash &mdash; run in the operator shell, once per session</span>'
                r'<button class="cp" type="button">copy</button></div><pre tabindex="0">(.*?)</pre></div>', SHARED, re.S)
assert _sm, "lesson 1.1's setup block moved"
SHARED_PRE = _sm.group(1)
_plain = html.unescape(re.sub(r"<[^>]+>", "", SHARED_PRE))
for _needle in ('export DEMO_ROOT="${DEMO_ROOT:-$HOME/deploy_module_rag}" KIT_REPO=https://github.com/netsetos/agents_workshop_learner.git',
                'source "$HOME/rag-shell-venv/bin/activate"', "python -m pip install -q google-cloud-firestore",
                'export PROJECT="$(gcloud config get-value project 2>/dev/null)"', "firestore.Client(project=",
                'export API="https://documind-api-$NUMBER.$REGION.run.app"', "documind-outsider-sa@", 'curl -s "$API/health"'):
    assert _needle in _plain, _needle
SHARED_WINDOW = ('<div class="cw"><div class="ch-bar"><span>lesson 1.1&#x27;s setup block, the one every later lesson opens with'
                 ' (read only here)</span><span class="ro">read only</span></div><pre tabindex="0">' + SHARED_PRE + "</pre></div>\n")


# ------------------------------------------------------------------ verbatim kit excerpts
EXCERPTS = {
    "install": ("commands/session-restart.sh - rag_install_python_dependencies(): the install, then the check",
                block("commands/session-restart.sh", "rag_install_python_dependencies() {", end="rag_resume() {")),
    "py312": ("commands/session-restart.sh - the interpreter check: Python 3.12, inside ~/rag-shell-venv",
              block("commands/session-restart.sh", "if sys.version_info[:2] != (3, 12)", n=4)),
    "lk06": ("evals/golden.jsonl - lk-06, the notice-period row", block("evals/golden.jsonl", '"id": "lk-06"', n=1)),
    "chat_local": ("Makefile - the chat-local target", CHAT_LOCAL),
    "profile": ("shared/profile.py - the switch, and the local half of each builder",
                block("shared/profile.py", 'PROFILE = os.environ.get("DOCUMIND_PROFILE", "gcp")', n=4) + "\n\n\n"
                + block("shared/profile.py", "def build_llm():", n=8) + "\n    ...\n\n\n"
                + block("shared/profile.py", "def build_store(embeddings=None):", n=14)),
    "seed": ("shared/local_corpus.py - seed(): the tenant's chunks, as Firestore's notebook seed mints them, into the store",
             block("shared/local_corpus.py", "def chunks_for(", end='if __name__ == "__main__":')),
    "agent_local": ("services/chat/agent.py - chat(): on the local profile the tenant is LOCAL_TENANT",
                    block("services/chat/agent.py", "    # The tenant is LOOKED UP, never received.", n=10)),
    "direct": ("services/chat/brains.py - the direct brain: one retrieve(), then one grounded call to the profile's model",
               block("services/chat/brains.py", "class DirectBrain:", end="_REGISTRY = {")),
    "retrieve_local": ("shared/documind_tools.py - _retrieve_local(): every chunk of the tenant, ranked by BM25, then the gate",
                       block("shared/documind_tools.py", "        got = store.get(where=where, include=[\"documents\", \"metadatas\"])", n=1)
                       + "\n        ...\n"
                       + block("shared/documind_tools.py", "    ranked, idf = _lexical_rank(query, rows)", n=12)),
    "mk_dryrun": ("Makefile - make dryrun is three targets", block("Makefile", "# ---------- Tier A: offline ----------", end="# ---------- Tier B: live (guarded) ----------")),
    "validate_list": ("validate.py - the kit's own list of its checks", block("validate.py", "Checks (each -> PASS / WARN / FAIL / SKIP):", end="USAGE")),
    "eval_offline": ("evals/run_eval.py - offline(): three checks over the golden set, and a sentence for each outcome",
                     block("evals/run_eval.py", "def offline() -> int:", end="# ------------------------------------------------------------- the figure, not the spelling")),
    "falsifiable": ("evals/run_eval.py - check_falsifiable(): the rule lk-06 just broke",
                    block("evals/run_eval.py", "def check_falsifiable(", n=15)),
    "ci": ("documind-dryrun.yml - the last three steps CI runs on every push (.github/workflows/)",
           block(".github/workflows/documind-dryrun.yml", "      - name: Extraction check", n=200)),
}
assert "lk-06" in EXCERPTS["lk06"][1] and '"must_contain": ["60"]' in EXCERPTS["lk06"][1]
assert "2.3 and 4.2" in kit("shared/local_corpus.py")                      # the seed's ids are the notebook seed's
assert 'return f"{self.tenant_id}:{self.sha256}#{i}"' in kit("services/ingest/contracts.py")   # the worker's are not
assert '"chunk_id": f"{tenant}:{doc[\'slug\']}{at}#{loc}"' in kit("shared/documind_corpus.py")
fill = filler(EXCERPTS, window)


# ------------------------------------------------------------------ the page's own windows
def sh(code: str) -> str:
    """A command block, escaped, every # comment (at a line's start or after a blank) in the comment colour."""
    out = []
    for line in code.split("\n"):
        m = re.search(r"(^|\s)(#.*)$", line)
        if m:
            out.append(esc(line[:m.start(2)]) + '<span class="cm">' + esc(m.group(2)) + "</span>")
        else:
            out.append(esc(line))
    return "\n".join(out)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + sh(code) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + esc(text.rstrip("\n")) + "</pre></div>\n")


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


CELL_TOOLS = """for t in git curl python3.12 terraform gcloud docker ollama make; do    # each prints a path, or MISSING
  printf '%-10s %s\\n' "$t" "$(command -v "$t" || echo MISSING)"
done
python3.12 --version; terraform version | head -1; gcloud --version | head -1
docker --version; ollama --version"""

CELL_SETUP = """export DEMO_ROOT="${DEMO_ROOT:-$HOME/deploy_module_rag}" KIT_REPO=https://github.com/netsetos/agents_workshop_learner.git
if [ ! -d "$DEMO_ROOT" ]; then git clone -q "$KIT_REPO" "$DEMO_ROOT"     # the first time: the kit is one clone
else git -C "$DEMO_ROOT" pull -q --ff-only; fi                          # every time after: the latest kit
cd "$DEMO_ROOT" && git log -1 --format='kit %h, %cd' --date=short
[ -d "$HOME/rag-shell-venv" ] || python3.12 -m venv "$HOME/rag-shell-venv"   # the operator venv, made once
source "$HOME/rag-shell-venv/bin/activate" && python --version            # the prompt gains (rag-shell-venv)
source commands/session-restart.sh                                       # the kit's restart helper: it only defines functions
rag_install_python_dependencies                                          # the operator pins, then the check
rag_require_terraform                                                    # Terraform, at the version the kit asks for"""

CELL_LOCALVENV = """cd "${DEMO_ROOT:-$HOME/deploy_module_rag}"                                 # a new terminal: the clone's default place
[ -d "$HOME/rag-local-venv" ] || python3.12 -m venv "$HOME/rag-local-venv"   # the Rs 0 lane's venv, made once
"$HOME/rag-local-venv/bin/python" -m pip install -q -r services/chat/requirements.txt -r services/chat/requirements-local.txt
ollama pull """ + LOCAL_MODEL + """                                                   # the model, once"""

CELL_SERVE = """cd "${DEMO_ROOT:-$HOME/deploy_module_rag}" && source "$HOME/rag-local-venv/bin/activate"
export DOCUMIND_CHROMA_DIR="$PWD/documind_chroma"     # one directory for the seed and the service
make chat-local                                       # seeds acme, then serves until Ctrl+C"""

CELL_HEALTH = f"curl -s localhost:{PORT}/health | python -m json.tool"

ASK_PY = """import json, warnings; warnings.filterwarnings("ignore", category=UserWarning)
r = json.load(open("/tmp/answer02.json", encoding="utf-8"))
print(r["answer"])
for c in r["citations"]:
    print(f'  {c["score"]:5.3f}  {c["chunk_id"]}  page {c["page"]}')
print("brain", r["brain"], "| tool calls", r["tool_calls"], "| model calls", r["limits"]["model_calls"],
      "| cost Rs", r["limits"]["cost_inr"])"""
CELL_ASK = (f"curl -s localhost:{PORT}/v1/chat -H 'content-type: application/json' -o /tmp/answer02.json \\\n"
            f"  -d '{{\"question\": \"{QUESTION}\", \"brain\": \"direct\", \"session_id\": \"lesson-0-2\"}}'\n"
            + heredoc(ASK_PY))

CELL_READ = ('cd "$DEMO_ROOT" && DOCUMIND_PROFILE=local DOCUMIND_CHROMA_DIR="$PWD/documind_chroma" \\\n'
             '  "$HOME/rag-local-venv/bin/python" - <<\'PY\'\n' + READ_PY + "\nPY")

CELL_DRYRUN = """cd "$DEMO_ROOT" && source "$HOME/rag-shell-venv/bin/activate"
make dryrun          # or, without make: python extract_documind.py --check && python validate.py && python evals/run_eval.py"""

CELL_LOOSEN = heredoc(LOOSEN_PY, prefix='cd "$DEMO_ROOT" && ')
CELL_DIFF = 'git -C "$DEMO_ROOT" diff -U0          # what changed in your clone, with no context lines'
CELL_RED = 'cd "$DEMO_ROOT" && make dryrun'
CELL_REPAIR = """git -C "$DEMO_ROOT" checkout -- evals/golden.jsonl     # the committed row comes back
git -C "$DEMO_ROOT" diff --stat                         # prints nothing: the clone is clean again
cd "$DEMO_ROOT" && make dryrun"""

WIN = {
    "CELL_TOOLS": bash_window("run in a terminal on your laptop, after installing the tools", CELL_TOOLS),
    "OUT_TOOLS": out_window("on the author's laptop (your paths and versions are yours; no line may say MISSING except docker, which is optional)", REC["tool_checks.txt"]),
    "CELL_SETUP": bash_window("run in the same terminal: the clone, the venv and the install (the first run takes a few minutes)", CELL_SETUP),
    "OUT_SETUP": out_window("on the author's laptop: the first lines and the last (pip's long progress between them is cut to ...)", REC["install_check.txt"]),
    "CELL_LOCALVENV": bash_window("run once, in a second terminal, which the lane will keep: its own venv and its model", CELL_LOCALVENV),
    "CELL_SERVE": bash_window("run in the second terminal, and leave it running", CELL_SERVE),
    "OUT_SERVE": out_window("in the second terminal, on the author's laptop", REC["chat_local.txt"]),
    "CELL_HEALTH": bash_window("run in the first terminal, while the lane serves", CELL_HEALTH),
    "OUT_HEALTH": out_window("on the author's laptop", REC["chat_health.txt"]),
    "CELL_ASK": bash_window("run in the first terminal: the notice-period question, through the direct brain", CELL_ASK),
    "OUT_ASK": out_window("on the author's laptop (the model's wording is gemma3:4b's and can differ on yours; the citations come from retrieval and do not)", REC["chat_answer.txt"]),
    "CELL_READ": bash_window("run in the first terminal after Ctrl+C has stopped the lane: read the store directly", CELL_READ),
    "OUT_READ": out_window("(the build ran this cell on the kit, with Chroma stood in by a dictionary that answers the same get())", READ_OUT),
    "CELL_DRYRUN": bash_window("run in the first terminal, in the operator venv", CELL_DRYRUN),
    "OUT_GREEN": out_window("(the build ran the three commands on a fresh copy of the kit, with no Terraform, tflint or Docker on the PATH; N is your machine&#x27;s seconds)", GREEN),
    "OUT_TOOLS_DRYRUN": out_window("with Terraform and Docker installed, on the author's laptop (make also prints each command above its output)", REC["dryrun_tools.txt"]),
    "CELL_LOOSEN": bash_window("run in the first terminal: loosen lk-06 in your clone (or delete the 60 by hand in an editor)", CELL_LOOSEN),
    "OUT_LOOSEN": out_window("(run at build time on the copy)", LOOSEN_OUT),
    "CELL_DIFF": bash_window("run in the first terminal", CELL_DIFF),
    "OUT_DIFF": out_window("(git, on the build's copy: the same file, the same hashes as in your clone)", DIFF),
    "CELL_RED": bash_window("run in the first terminal", CELL_RED),
    "OUT_RED": out_window("(the same three commands on the copy with lk-06 loosened: red, and the reason under the FAIL)", RED),
    "CELL_REPAIR": bash_window("run in the first terminal: repair, check, run again", CELL_REPAIR),
    "OUT_REPAIRED": out_window("(the end of the run, on the repaired copy: validate.py&#x27;s lines are as before)", AGAIN_TAIL),
    "SHARED_WINDOW": SHARED_WINDOW,
}

# ------------------------------------------------------------------ tables built from the facts
_by = {t: [d for d in REAL if t in d["tenants"]] for t in TENANTS}
for _t, _docs in SYNTHETIC.items():
    _real_text = [d for d in _by[_t] if d["text_layer"]]
    assert CHUNKS[_t][1] == len(_docs) + len(_real_text), (_t, CHUNKS[_t], _docs)
CORPUS_ROWS = "".join(
    f'<tr><td><code>{t}</code></td><td data-label="Synthetic documents">{len(SYNTHETIC[t])}: '
    + ", ".join(f"<code>{d}</code>" for d in SYNTHETIC[t])
    + f'</td><td data-label="Real documents">{len(_by[t])}</td>'
    f'<td data-label="Chunks on your laptop">{num(CHUNKS[t][0])}</td></tr>\n' for t in ("acme", "zeta", "globex"))
REAL_ROWS = "".join(
    f'<tr><td>{esc(d["title"])}</td><td data-label="Pages">{d["pages"]}</td>'
    f'<td data-label="Held by">{", ".join(d["tenants"])}</td>'
    f'<td data-label="On the laptop">{"a text mirror, chunked" if d["text_layer"] else "scanned, no text layer: only the lane&#x27;s OCR reads it"}</td></tr>\n'
    for d in REAL)
CHECK_ROWS = []
_what = {
    "extract": "the tree still matches the notebooks it was first extracted from; in a kit-only clone there is nothing to compare",
    "py_compile": f"every Python file under services/, smoke/, shared/ and evals/ parses ({num(N_PYFILES)} files)",
    "imports": "no service imports a module it does not have",
    "shared-deps": "a Google Cloud client that a shared/ module opens is pinned by every service that imports it",
    "requirements": "every dependency carries an exact version",
    "pins": "a package two services share has the same version in both",
    "dockerfile": "every service ships a Dockerfile",
    "copy-paths": "every file a Dockerfile copies exists where its build expects it",
    "terraform": "terraform fmt, init without a backend, and validate",
    "tflint": "the Terraform linter",
    "docker": "every Python image builds from its own context, without pushing",
}
assert set(_what) == set(CHECK_NAMES)
for _c in CHECK_NAMES:
    _needs = {"terraform": "Terraform", "tflint": "tflint", "docker": "Docker"}.get(_c, "Python only")
    CHECK_ROWS.append(f'<tr><td><code>{_c}</code></td><td data-label="What it proves">{_what[_c]}</td>'
                      f'<td data-label="Needs">{_needs}</td><td data-label="On the build&#x27;s machine"><code>{VERDICT[_c]}</code></td></tr>\n')

# ------------------------------------------------------------------ the master diagram: the kit's names, lit by module
MODS = {int(k): v for k, v in MANIFEST["modules"].items() if k != "B"}
assert sorted(MODS) == list(range(13)), sorted(MODS)
BOXES = {   # id: (title, what it is, modules that light it, (on the laptop?, what stands in for it, or why not, if anything))
    "upload": ("an upload", f"the UI&#x27;s Documents page, or <code>make ingest-corpus</code> for the whole corpus",
               (1, 3), (False, "the seed reads <code>evals/corpus/</code> directly")),
    "bucket": (f"<code>{BUCKET}</code>", "the uploads bucket: one folder per tenant, <code>acme/</code>, <code>zeta/</code>, <code>globex/</code>",
               (1,), (False, "")),
    "events": (f"Pub/Sub <code>{TOPIC}</code>", f"pushed to the worker by <code>{PUSH}</code>; after {ATTEMPTS} attempts, <code>{DLQ}</code>",
               (1, 8), (False, "")),
    "worker": (f"<code>{NAME['ingest']}</code>", f"the worker: parse, chunk, scan for personal data, embed with <code>{EMBED}</code>",
               (1, 4, 7, 8), (True, "stood in by <code>shared/local_corpus.py</code>: the same two cutting rules, run once by make chat-local")),
    "index": ("Firestore <code>chunks</code> + Vector Search", f"the kit&#x27;s own index, <code>{INDEX_NAME}</code>: the <code>{OWN[0]}</code> and <code>{OWN[1]}</code> backends",
              (1, 2), (True, f"stood in by a Chroma directory, collection <code>{CHROMA_COLL}</code>")),
    "managed": ("RAG Engine + Vertex AI Search", f"two managed mirrors: the <code>{MANAGED[0]}</code> and <code>{MANAGED[1]}</code> backends",
                (7,), (False, "")),
    "graph": ("the graph", f"in {GRAPHS[0].capitalize()} or {GRAPHS[1].capitalize()}; off by default, built in Module 7",
              (7,), (False, "")),
    "ui": (f"<code>{NAME['ui']}</code>", "the Streamlit app behind IAP: " + ", ".join(UI_PAGES),
           (0, 3, 7), (False, "curl asks the question")),
    "api": (f"<code>{NAME['api']}</code>", "who is asking, which tenant, then retrieve and generate; caches and budgets",
            (4, 6, 11), (False, "the chat service reads the store itself")),
    "retriever": ("the retriever", "one backend per tenant; dense or hybrid; reranked; a fallback rung",
                  (2,), (True, "BM25 over the tenant&#x27;s chunks, <code>documind_tools._retrieve_local()</code>")),
    "generator": ("the generator", f"<code>{GEN}</code> on the global endpoint",
                  (3, 9, 12), (True, f"<code>{LOCAL_MODEL}</code> on Ollama")),
    "answer": ("a cited answer", "answer, citations, answerable, confidence: the contract the golden set scores",
               (3, 4), (True, "the same answer and citations, at Rs 0")),
    "chat": (f"<code>{NAME['chat']}</code>", f"{len(BRAINS)} brains over one <code>retrieve()</code>, and conversation memory",
             (5, 6, 10), (True, f"this service, <code>DOCUMIND_PROFILE=local</code>, on 127.0.0.1:{PORT}")),
    "mcp": (f"<code>{NAME['mcp']}</code>", "the MCP server, for agents outside the kit",
            (5,), (False, "make chat-local does not start it")),
    "agent": (f"<code>{NAME['agent']}</code>", "the A2A peer: an agent that reaches the lane only through MCP",
              (10,), (False, "")),
    "admin": (f"<code>{NAME['admin']}</code>", "the admin console, under its own account",
              (4, 11), (False, "")),
    "run": ("deploy, gate, release, switch off", "<code>make plan</code>, <code>make up</code>, the eval gate in CI, <code>make off</code>",
            (0, 4, 11), (True, "<code>make dryrun</code>, the offline half, runs here")),
}
_lit = {m for b in BOXES.values() for m in b[2]}
assert _lit == set(MODS), sorted(set(MODS) - _lit)                        # every module lights at least one box
assert sum(1 for k in ("worker", "ui", "api", "chat", "mcp", "agent", "admin") if k in BOXES) == len(SERVICES)


def box(key: str) -> str:
    t, what, mods, (here, local) = BOXES[key]
    assert local or not here, key                                         # a box on the laptop says what stands in for it
    note = f"On your laptop: {local}" if here else ("Not on your laptop" + (f": {local}" if local else "."))
    return (f'<div class="md-box" data-m="{" ".join(map(str, mods))}" data-here="{int(here)}"><b>{t}</b>{what}'
            f'<span class="md-local">{note}</span>'
            f'<span class="md-tags">{" ".join(f"M{m}" for m in mods)}</span></div>')


DN = '<div class="md-dn" aria-hidden="true">&#8595;</div>'
_buttons = ['<button type="button" class="md-b" data-k="all" aria-pressed="true">Every box</button>',
            '<button type="button" class="md-b" data-k="local" aria-pressed="false">Your laptop today (Rs 0)</button>']
_buttons += [f'<button type="button" class="md-b" data-k="{m}" aria-pressed="false">{m} {esc(MODS[m]["name"].split(" - ")[0])}</button>'
             for m in sorted(MODS)]
MAP = ('<div class="diagram" id="map">\n<div class="dg-title">The master diagram - DocuMind&#x27;s two workflows, and the module that lights each box</div>\n'
       '<div class="md-pick" role="group" aria-label="Light up a module">' + "".join(_buttons) + "</div>\n"
       '<p class="md-sum" id="md-sum" aria-live="polite"></p>\n'
       '<div class="md-cols">\n'
       '<div><div class="md-h">Upload to index</div>' + DN.join(box(k) for k in ("upload", "bucket", "events", "worker"))
       + DN + '<div class="md-stores">' + box("index") + box("managed") + box("graph") + "</div></div>\n"
       '<div><div class="md-h">Question to answer</div>' + DN.join(box(k) for k in ("ui", "api", "retriever", "generator", "answer"))
       + "</div>\n</div>\n"
       '<div class="md-sec"><div class="md-h">Agents around the API</div><div class="md-band">'
       + "".join(box(k) for k in ("chat", "mcp", "agent", "admin")) + "</div></div>\n"
       '<div class="md-sec"><div class="md-h">Around all of it</div><div class="md-band">' + box("run") + "</div></div>\n"
       f'<p class="dg-cap">Every name is read from the kit when this page is built: the {len(SERVICES)} Cloud Run services <code>make up</code> deploys'
       f' (the Makefile&#x27;s <code>SERVICES</code>), the bucket and the topic (<code>terraform/storage.tf</code>, <code>terraform/eventarc.tf</code>),'
       f' and the {len(BACKENDS)} stores the API can answer from (<code>RETRIEVAL_BACKENDS</code> in <code>services/rag-api/config.py</code>).'
       ' M1 on a box means Module 1 lights it; pick a module to see its lessons.</p>\n</div>\n')
MOD_DATA = {str(m): {"name": MODS[m]["name"], "lessons": [[lid, les["name"]] for lid, les in MODS[m]["lessons"].items()]}
            for m in sorted(MODS)}

JS = """<script>
(function(){
  'use strict';
  var root = document.getElementById('map'); if (!root) return;
  var MODS = %s;
  var boxes = root.querySelectorAll('.md-box'), btns = root.querySelectorAll('.md-b'), sum = document.getElementById('md-sum');
  function esc(t){ return String(t).replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;'); }
  function show(key){
    var lit = 0;
    Array.prototype.forEach.call(btns, function(b){ b.setAttribute('aria-pressed', b.getAttribute('data-k') === key ? 'true' : 'false'); });
    Array.prototype.forEach.call(boxes, function(x){
      var on = key === 'all' || (key === 'local' ? x.getAttribute('data-here') === '1'
               : (' ' + x.getAttribute('data-m') + ' ').indexOf(' ' + key + ' ') !== -1);
      x.classList.toggle('on', key !== 'all' && on);
      x.classList.toggle('off', !on);
      x.classList.toggle('loc', key === 'local');
      if (on && key !== 'all') lit++;
    });
    if (key === 'all'){
      sum.innerHTML = 'Two workflows: an upload becomes rows in the stores; a question becomes a cited answer. Pick a module to light the boxes it opens, or your laptop to see what <code>make chat-local</code> runs.';
    } else if (key === 'local'){
      sum.innerHTML = '<b>Your laptop today:</b> ' + lit + ' boxes run, or are stood in for, with no cloud and no cost. The rest wait for the lane lesson 0.3 deploys.';
    } else {
      var m = MODS[key];
      sum.innerHTML = '<b>Module ' + key + ' &middot; ' + esc(m.name) + '</b> lights ' + lit + ' box' + (lit === 1 ? '' : 'es') + '. Its lessons: ' +
        m.lessons.map(function(l){ return esc(l[0] + ' ' + l[1]); }).join('; ') + '.';
    }
  }
  Array.prototype.forEach.call(btns, function(b){ b.addEventListener('click', function(){ show(b.getAttribute('data-k')); }); });
  show('all');
})();
</script>
""" % json.dumps(MOD_DATA, ensure_ascii=False)

# ------------------------------------------------------------------ the numbers the prose names
NEXT_LID = "0.3"
NEXT_NAME = MODS[0]["lessons"][NEXT_LID]["name"]
STATS = {
    "N_SERVICES": str(len(SERVICES)), "N_BACKENDS": str(len(BACKENDS)), "N_TENANTS": str(len(TENANTS)),
    "N_REAL": str(N_REAL), "N_STATUTE": str(N_STATUTE), "N_GUIDE": str(N_GUIDE), "N_TEXT_REAL": str(N_REAL - len(SCANNED)),
    "N_GOLDEN": str(len(GOLDEN)), "N_LOOKUP": str(SHAPES["lookup"]), "N_JOIN": str(SHAPES["join"]),
    "N_REFUSAL": str(SHAPES["refusal"]), "N_ISOLATION": str(SHAPES["isolation"]), "N_VERSION": str(SHAPES["version"]),
    "N_REQUIRED": str(len(REQUIRED)), "N_TEXT_DOCS": str(N_TEXT_DOCS),
    "N_ACME": num(N_ACME), "N_ZETA": num(CHUNKS["zeta"][0]), "N_GLOBEX": num(CHUNKS["globex"][0]), "N_ALL_CHUNKS": num(ALL_CHUNKS),
    "N_ACME_DOCS": str(CHUNKS["acme"][1]),
    "PAN": PAN, "GSTIN": GSTIN, "MOBILE": MOBILE,
    "N_CHECKS": str(N_CHECKS), "N_PASS_VAL": str(COUNT["PASS"]), "N_WARN_VAL": str(COUNT["WARN"]), "N_SKIP_VAL": str(COUNT["SKIP"]),
    "N_PASS_GREEN": str(N_PASS_GREEN), "N_PASS_RED": str(N_PASS_RED), "N_PYFILES": num(N_PYFILES),
    "N_PINS": str(N_PINS), "N_IMPORTS": str(N_IMPORTS), "PASS_DEPS": esc(PASS_DEPS), "N_REQ_FILES": str(len(REQ_FILES)),
    "N_IMAGES": str(N_IMAGES), "N_PY312": str(N_PY312), "TF_MIN": TF_MIN, "CI_TF": CI_TF, "CI_PY": CI_PY,
    "LOCAL_MODEL": LOCAL_MODEL, "CHROMA_DIR": CHROMA_DIR, "CHROMA_COLL": CHROMA_COLL, "PORT": PORT,
    "EMBED": EMBED, "GEN": GEN, "N_BRAINS": str(len(BRAINS)),
    "BRAINS": ", ".join(f"<code>{b}</code>" for b in BRAINS[:-1]) + f" and <code>{BRAINS[-1]}</code>",
    "QUESTION": esc(QUESTION), "TOP_ID": TOP_ID, "TOP_SCORE": TOP_SCORE, "NEXT_BEST": NEXT_BEST,
    "N_STATUTE_CITES": str(N_STATUTE_CITES), "WORDS": ", ".join(f"<code>{w}</code>" for w in WORDS),
    "SEED_LINE": esc(SEED_LINE), "FAIL_REASON": esc(FAIL_REASON), "ATTEMPTS": str(ATTEMPTS),
    "N_TOP_WORDS": str(N_TOP_WORDS), "N_CANDIDATES": num(N_CANDIDATES), "N_FRIEND_CHUNKS": str(N_FRIEND_CHUNKS),
    "TOP_K": str(TOP_K), "N_WORDS": str(len(WORDS)), "N_LISTED": str(N_LISTED), "N_EVAL_CHECKS": str(N_EVAL_CHECKS),
    "N_ACME_SYN": str(len(SYNTHETIC["acme"])),
    "REST_MIN": num(min(REST_LEN)), "REST_MAX": num(max(REST_LEN)),
    "NOTICE_ACME": NOTICE["acme"], "NOTICE_ZETA": NOTICE["zeta"], "N_TF": str(N_TF),
    "N_SERVICE_DIRS": str(len(SERVICE_DIRS)),
    "CORPUS_ROWS": CORPUS_ROWS, "REAL_ROWS": REAL_ROWS, "CHECK_ROWS": "".join(CHECK_ROWS), "MAP": MAP,
    "NEXT": f"Lesson {NEXT_LID} {esc(NEXT_NAME)}",
}


if os.environ.get("CELLS_ONLY"):                  # print what the build computed, and stop before the page
    for k, v in (("GREEN", GREEN), ("LOOSEN", LOOSEN_OUT), ("DIFF", DIFF), ("RED", RED), ("AGAIN_TAIL", AGAIN_TAIL),
                 ("SEED", SEED_LINE), ("READ", READ_OUT), ("CHUNKS", json.dumps(CHUNKS)), ("WORDS", json.dumps(WORDS)),
                 ("TOP5", json.dumps(TOP5)), ("CANDIDATES", str(N_CANDIDATES))):
        print(f"===== {k}\n{v}")
    print({k: v for k, v in STATS.items() if len(v) < 120})
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
assert body.count('<h3 id="setup">') == 1
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {N_CHECKS} checks, {COUNT} | eval green, red on lk-06, green again | acme {N_ACME} chunks, top {TOP_ID} {TOP_SCORE}"
      f" | operator pins {N_PINS}, imports {N_IMPORTS}")
