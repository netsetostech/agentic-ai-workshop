"""Build lesson B.1 from its three parts, the shared template, the Basics laptop setup and verbatim kit excerpts.

Run Python the way the kit does: venvs, JSON and HTTP calls. Basics is pre-work on the learner's laptop, before the kit
is cloned (lesson 0.2), so every cell is self-contained: it writes its own small files and starts its own server on
127.0.0.1. Each cell runs here at build time on the Basics interpreter (Python 3.12 with numpy 2.5.3 and google-genai
2.22.0, the versions the setup block pins), its stdout becomes the page's expected window, and asserts pin every claim
the prose makes. Timings differ between machines, so the cells print rounded counts of a fixed wait, never seconds,
and every cell is run twice and must print the same both times.

  step 3  the venv: sys.prefix against sys.base_prefix, site-packages, the two pins and what google-genai brings;
          a throwaway venv made, asked and deleted
  step 4  pathlib and json: four golden rows written as JSONL and read back the kit's way; a broken line caught
  step 5  one HTTP call: an http.server stand-in on 127.0.0.1 answering JSON, called with urllib (200, 200, 401, 404)
  step 6  two calls at once: one after the other, gather over blocking calls, gather over asyncio.to_thread
  step 7  a call the kit would trust: one retry for a 5xx, a timeout, a 200 that is not an answer

The cells run with HTTP_PROXY and HTTPS_PROXY pointing at a port where nothing listens: the cells open URLs through an
opener with no proxy, and this proves it. The kit side, all read at build time: the pins in every requirements.txt
(validate.py's two checks, run on the kit; their rules ported to the explorer and compared with validate.py itself on
every one-pin change), golden.jsonl's writer and reader, rag-api's JSON log line, smoke.py's call() and token,
documind_tools' ID token and timeout, the chat service's asyncio, run_eval's retry and validate_body().

Python facts the prose states, checked 7 October 2026:
  https://docs.python.org/3.12/library/venv.html - sys.prefix != sys.base_prefix is sufficient to tell a venv; pyvenv.cfg
      has home and include-system-site-packages; a venv is disposable, not movable or copyable; bin, or Scripts on
      Windows; activation prepends that directory to PATH; --without-pip skips pip
  https://docs.python.org/3.12/library/http.server.html - not recommended for production; log_message writes to stderr
  https://docs.python.org/3.12/library/urllib.error.html - HTTPError also works as a file-like response: code, and the body
  https://docs.python.org/3.12/library/asyncio-task.html - gather's results come in the order of the awaitables;
      to_thread is for IO-bound functions that would otherwise block the event loop (added in 3.9)
  https://docs.python.org/3.12/library/json.html - ensure_ascii defaults to True; the JSON-to-Python table;
      JSONDecodeError's msg, lineno and colno
  https://jsonlines.org/ - UTF-8, one JSON value per line, '\\n' as the terminator, a blank line is not valid, .jsonl
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

sys.dont_write_bytecode = True                     # validate.py, imported below, leaves no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, window  # noqa: E402

LESSON = "B.1"
title = ("<title>Lesson B.1 Run Python the way the kit does: venvs, JSON and HTTP calls - a venv, a JSONL file and a "
         "call to a server on your laptop | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pe{font-variant-ligatures:none;}   /* the explorer is about the text "==": the code font must not join it into one glyph */
.pe-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:10px 14px;margin-bottom:10px;}
.pe-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pe-l select,.pe-l input[type=text]{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pe-chk{flex-direction:row;align-items:center;gap:8px;min-height:44px;}
.pe-chk input{width:22px;height:22px;flex-shrink:0;}
.pe-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal);margin:6px 0 8px;overflow-wrap:anywhere;}
.pe-chips{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px;}
.pe-chip{font-family:var(--mono);font-size:12px;line-height:1.4;padding:3px 8px;border:1px solid var(--border);border-radius:6px;background:var(--card);color:var(--slate);overflow-wrap:anywhere;}
.pe-chip.sh{border-color:#5eead4;background:var(--teal-light);color:var(--teal-dark);}
.pe-chip.on{border:2px solid var(--teal);font-weight:600;}
.pe-who{font-size:var(--small-size);margin:0 0 8px;overflow-wrap:anywhere;}
.pe-check{font-family:var(--mono);font-size:12.5px;line-height:1.5;margin:4px 0;padding:6px 10px;border-radius:8px;background:#ecfdf5;color:#065f46;overflow-wrap:anywhere;}
.pe-check.warn{background:#fffbeb;color:#92400e;}
.pe-check.fail{background:#fef2f2;color:#991b1b;}
"""

setup = pb.basics_setup_section()


def esc(text: str) -> str:
    return html.escape(text, quote=False)


# ------------------------------------------------------------------ the setup block, as step 3 reads it line by line
SETUP_CODE = html.unescape(re.sub(r'<span class="cm">.*?</span>', "", re.search(r'<pre tabindex="0">(.*?)</pre>', setup, re.S).group(1)))
SETUP_LINES = [line.rstrip() for line in SETUP_CODE.splitlines()]
assert SETUP_LINES == [
    'export BASICS_VENV="$HOME/basics-venv"',
    'PY312="$(command -v python3.12 || command -v python3)"; [ -n "$PY312" ] || PY312="py -3.12"',
    '[ -d "$BASICS_VENV" ] || $PY312 -m venv "$BASICS_VENV"',
    'source "$BASICS_VENV/bin/activate" 2>/dev/null || source "$BASICS_VENV/Scripts/activate"',
    'python -m pip install -q "numpy==2.5.3" "google-genai==2.22.0"',
    'python -c "import sys, numpy, google.genai as g; print(sys.version.split()[0], numpy.__version__, g.__version__)"',
], SETUP_LINES
NUMPY_PIN, GENAI_PIN = re.search(r'"numpy==([\d.]+)" "google-genai==([\d.]+)"', SETUP_LINES[4]).groups()
assert "python:3.12-slim" in setup and "~/basics-venv" in setup

# ------------------------------------------------------------------ the kit's environments: the files, the pins, the images
REQS = sorted(KIT.glob("services/*/requirements.txt"))
SERVICES = [p.parent.name for p in REQS]


def req_lines(path: Path) -> list:
    """A requirements file as validate.py reads it: each line cut at '#', stripped, the empty ones skipped."""
    return [ln.split("#", 1)[0].strip() for ln in path.read_text(encoding="utf-8").splitlines() if ln.split("#", 1)[0].strip()]


PIN_LINES = {s: req_lines(p) for s, p in zip(SERVICES, REQS)}
SHARED_LINES = req_lines(KIT / "shared/requirements.txt")
N_SERVICES = len(REQS)
N_PIN_LINES = sum(len(v) for v in PIN_LINES.values())
assert all("==" in ln for v in PIN_LINES.values() for ln in v) and all("==" in ln for ln in SHARED_LINES)
DOCKER_FROM = {d.name: re.search(r"^FROM (\S+)", (d / "Dockerfile").read_text(encoding="utf-8"), re.M).group(1)
               for d in sorted((KIT / "services").iterdir()) if d.is_dir()}
assert sorted(DOCKER_FROM) == SERVICES
assert not any("venv" in (d / "Dockerfile").read_text(encoding="utf-8") for d in (KIT / "services").iterdir() if d.is_dir())   # no image makes one
N_SLIM = sum(1 for base in DOCKER_FROM.values() if base == "python:3.12-slim")
VENDOR = sorted(base.split(":")[0] for base in DOCKER_FROM.values() if base != "python:3.12-slim")
assert VENDOR == ["docker.litellm.ai/berriai/litellm", "ollama/ollama", "vllm/vllm-openai"], VENDOR
N_OTHER_BASE = N_SERVICES - N_SLIM


def pinned(name: str, files: dict) -> dict:
    """{file: version} for every file that pins `name` (extras ignored), the way validate.py keys its pins."""
    out = {}
    for f, lines in files.items():
        for ln in lines:
            m = re.match(r"^([A-Za-z0-9_.\-]+)(\[[^\]]*\])?==(\S+)$", ln)
            if m and m.group(1) == name:
                out[f] = m.group(3)
    return out


GENAI = pinned("google-genai", PIN_LINES)
assert set(GENAI.values()) == {GENAI_PIN}, GENAI           # the setup block's pin is the kit's pin
N_GENAI = len(GENAI)
GAUTH = pinned("google-auth", PIN_LINES)                  # the services that pin it, each image getting exactly that version
assert len(set(GAUTH.values())) == 1 and pinned("google-auth", {"shared": SHARED_LINES})["shared"] in GAUTH.values()
KIT_GAUTH, N_GAUTH_SVC = next(iter(GAUTH.values())), len(GAUTH)
RAG_PINS = len(PIN_LINES["rag-api"])

# validate.py's two pin checks, run on the kit as it is
sys.path.insert(0, str(KIT))
import validate  # noqa: E402

del validate.results[:]
validate.check_requirements()
validate.check_pin_consistency()
CHECKS = [tuple(r) for r in validate.results]
assert [(c, s) for c, s, _ in CHECKS] == [("requirements", "PASS"), ("pins", "PASS")], CHECKS
assert CHECKS[0][2] == f"{N_SERVICES} files, all deps pinned", CHECKS
N_SHARED, N_PIN_FILES = map(int, re.fullmatch(r"(\d+) shared packages agree across (\d+) files", CHECKS[1][2]).groups())
assert N_PIN_FILES == N_SERVICES + 1                       # the services' files and shared/requirements.txt
VALIDATE_OUT = "\n".join(f"[{s}] {c.ljust(12)}  {d}" for c, s, d in CHECKS)   # validate.py's own layout, less the seconds

# ------------------------------------------------------------------ the kit's JSON: the golden set, and the eval gate's call
GOLDEN_TEXT = (KIT / "evals/golden.jsonl").read_text(encoding="utf-8")
GOLDEN = [json.loads(line) for line in GOLDEN_TEXT.splitlines() if line.strip()]
BY_ID = {r["id"]: r for r in GOLDEN}
N_GOLDEN = len(GOLDEN)
assert all(set(r) >= {"id", "shape", "question", "tenant", "must_contain", "must_retrieve", "answerable"} for r in GOLDEN)
assert not any(v is None for r in GOLDEN for v in r.values())        # the table says the golden set has no null
assert not any(isinstance(v, (int, float)) and not isinstance(v, bool) for r in GOLDEN for v in r.values())   # and no number
assert all(isinstance(x, str) for r in GOLDEN for v in r.values() if isinstance(v, list) for x in v)   # a figure is a string, comma and all
JSONL_FILES = sorted(p for p in KIT.rglob("*.jsonl") if "__pycache__" not in p.parts)
N_JSONL = len(JSONL_FILES)
JSONL_LINES = sum(len(p.read_text(encoding="utf-8").splitlines()) for p in JSONL_FILES)
LK = BY_ID["lk-01"]
LK_LINE = GOLDEN_TEXT.splitlines()[0]
assert json.loads(LK_LINE) == LK and LK_LINE == json.dumps(LK, ensure_ascii=False)
SAMPLE_IDS = ["lk-01", "jn-01", "rf-02", "iso-01"]
SAMPLE = [{k: v for k, v in BY_ID[i].items() if k != "note"} for i in SAMPLE_IDS]
assert [r["shape"] for r in SAMPLE] == ["lookup", "join", "refusal", "isolation"]
assert all("note" not in BY_ID[i] for i in SAMPLE_IDS[:3]) and "note" in BY_ID["iso-01"]
assert BY_ID["iso-01"]["question"].replace("per-trip cap on", "per-trip cap on domestic") == LK["question"]
assert BY_ID["iso-01"]["must_not_contain"] == LK["must_contain"]   # zeta must never say acme's figure
RUN_EVAL = (KIT / "evals/run_eval.py").read_text(encoding="utf-8")
assert 'body = json.dumps({"query": question, "tenant_id": tenant, "top_k": 6}).encode()' in RUN_EVAL
assert 'req.add_header("Authorization", f"Bearer {token}")' in RUN_EVAL
EVAL_TIMEOUT = re.search(r'req = urllib\.request\.Request\(f"\{api_url\.rstrip\(\'/\'\)\}/v1/query".*?urlopen\(req, timeout=(\d+)\)', RUN_EVAL, re.S).group(1)
assert 'for key, kind in (("answer", str), ("citations", list), ("answerable", bool)):' in RUN_EVAL
assert 'if body.get("confidence") not in ("high", "medium", "low"):' in RUN_EVAL
assert "time.sleep(2)" in RUN_EVAL and "if status == 200 or 400 <= status < 500:" in RUN_EVAL
assert "12 September 2026 - the gate learned to fail" in RUN_EVAL
LK_BODY = json.dumps({"query": LK["question"], "tenant_id": LK["tenant"], "top_k": 6})
RAG_DF = (KIT / "services/rag-api/Dockerfile").read_text(encoding="utf-8")
assert RAG_DF.startswith("FROM python:3.12-slim\n") and "RUN pip install --no-cache-dir -r requirements.txt" in RAG_DF
RAG_WORKERS = re.search(r'CMD \["gunicorn", "-k", "uvicorn\.workers\.UvicornWorker", "-w", "(\d+)",', RAG_DF).group(1)
assert "import urllib.request as r; r.urlopen('http://localhost:8080/health').read()" in RAG_DF
SMOKE = (KIT / "smoke/smoke.py").read_text(encoding="utf-8")
SMOKE_TIMEOUT = re.search(r"def call\(.*?urllib\.request\.urlopen\(req, timeout=(\d+)\)", SMOKE, re.S).group(1)
assert "Uses only the Python standard library + the `gcloud` CLI" in SMOKE and 'if st in (401, 403):' in SMOKE
TOOLS = (KIT / "shared/documind_tools.py").read_text(encoding="utf-8")
RAG_TIMEOUT = re.search(r'RAG_TIMEOUT_S = float\(os\.environ\.get\("RAG_TIMEOUT_S", "(\d+)"\)\)', TOOLS).group(1)
assert "ONE implementation, consumed by every brain" in TOOLS and "THE single retrieval entry point. Every brain calls this one." in TOOLS
assert TOOLS.count("requests.post(") == 2 and "time.sleep" not in TOOLS and "retr" not in TOOLS.replace("retrieve", "").replace("retrieval", "")   # no retry
MAIN = (KIT / "services/rag-api/main.py").read_text(encoding="utf-8")
assert "# bare JSON -> Cloud Run jsonPayload" in MAIN
SINK = (KIT / "terraform/sink.tf").read_text(encoding="utf-8")
assert 'destination            = "bigquery.googleapis.com/' in SINK and 'jsonPayload.event = "query"' in SINK
assert 'WHERE jsonPayload.event IN ("query", "stream", "media")' in (KIT / "terraform/sql/tenant_daily.sql").read_text(encoding="utf-8")
CHAT_DESK = (KIT / "services/chat/desk.py").read_text(encoding="utf-8")
assert "shadow = asyncio.create_task(_quietly(_shadow(scope, question, tenant)))" in CHAT_DESK
assert "while the tenant's desk_route is shadow" in CHAT_DESK and "(workshop lesson 10.4)" in CHAT_DESK
assert 'hits = (_db().collection_group("members")' in (KIT / "shared/tenancy.py").read_text(encoding="utf-8")
MAKE = (KIT / "Makefile").read_text(encoding="utf-8")
assert "dryrun: check validate eval" in MAKE and "\t$(PY) validate.py" in MAKE and "\t$(PY) smoke/smoke.py" in MAKE

# ------------------------------------------------------------------ verbatim excerpts
DF, CHAT_REQ, VAL = "services/rag-api/Dockerfile", "services/chat/requirements.txt", "validate.py"
EXCERPTS = {
    "dockerfile_head": ("services/rag-api/Dockerfile - the image: one Python, one requirements.txt",
                        block(DF, "FROM python:3.12-slim", end="COPY --chown=app:app shared/ ./shared/")),
    "chat_reqs": ("services/chat/requirements.txt - the first lines, and the note above them",
                  block(CHAT_REQ, "# DocuMind chat service", n=7)),
    "validate_checks": ("validate.py - check_requirements() and check_pin_consistency(), two of the dry run's checks",
                        block(VAL, "# ---- 4. requirements pinned", end="# ---- 5. dockerfile presence")),
    "golden_writer": ("evals/build_golden.py - how the kit writes golden.jsonl",
                      block("evals/build_golden.py", 'p = os.path.join(HERE, "golden.jsonl")', n=4)),
    "golden_reader": ("evals/run_eval.py - load_golden(), how the eval gate reads it",
                      block("evals/run_eval.py", "def load_golden() -> list[dict]:", n=3)),
    "json_log": ("services/rag-api/main.py - the log is JSON: the logging setup, and the usage row every answer writes",
                 block("services/rag-api/main.py", 'logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)', n=1)
                 + "\n# ...\n" + block("services/rag-api/main.py", "    row = usage_row(req, user, ans.tokens_in", n=5)),
    "smoke_doc": ("smoke/smoke.py - from its docstring",
                  block("smoke/smoke.py", "Run this AFTER `make up` against a real deployment", n=3)),
    "smoke_call": ("smoke/smoke.py - call(), every request the smoke test makes",
                   block("smoke/smoke.py", "def call(method, path, token, body=None, headers=None):")),
    "smoke_token": ("smoke/smoke.py - identity_token(): where the real token comes from",
                    block("smoke/smoke.py", "def identity_token() -> str | None:")),
    "dockerfile_tail": ("services/rag-api/Dockerfile - the last three lines: the container's health check, and the server it runs",
                        block(DF, "HEALTHCHECK --interval=20s", n=3)),
    "mcp_async": ("smoke/smoke_mcp.py - call(), an async client, and a plain script running it",
                  block("smoke/smoke_mcp.py", "async def call(token: str | None, name: str, args: dict):", n=9)
                  + "\n# ...\n" + block("smoke/smoke_mcp.py", 'names = set(asyncio.run(call(member, "__list__", {})))', n=1)),
    "tenant_for": ("shared/tenancy.py - tenant_for(): one Firestore query",
                   block("shared/tenancy.py", "def tenant_for(email: str) -> str | None:", end="# ---- the write side")),
    "chat_thread": ("services/chat/desk.py - the chat door asks for the caller and the tenant in a thread",
                    block("services/chat/desk.py", '                user = await asyncio.to_thread(_hooks["caller"], Request(scope))', n=2)),
    "chat_pass": ("services/chat/desk.py - a second task beside the turn, awaited before the request ends",
                  block("services/chat/desk.py", "async def _quietly(aw) -> None:", n=5) + "\n# ...\n"
                  + block("services/chat/desk.py", "    async def _pass(self, scope, receive, send, body: bytes, question: str, tenant: str | None):", n=8)),
    "eval_ask": ("evals/run_eval.py - ask(): one retry, and only for a 5xx or no answer",
                 block("evals/run_eval.py", "def ask(api_url: str, question: str, tenant: str, email: str, token: str | None, retries: int = 1):")),
    "validate_body": ("evals/run_eval.py - validate_body(): a 200 is checked before it counts",
                      block("evals/run_eval.py", "def validate_body(body) -> str | None:")),
    "tools_retrieve": ("shared/documind_tools.py - retrieve()'s call: a fresh ID token, a timeout, a failure returned as data",
                       block("shared/documind_tools.py", '    headers = {"Authorization": f"Bearer {_id_token(RAG_API_URL)}"}', end="    answer = resp.json()")),
    "tools_token": ("shared/documind_tools.py - _id_token(): why the token is minted on every call",
                    block("shared/documind_tools.py", "def _id_token(audience: str) -> str:", n=6)),
}
EX = {k: v[1] for k, v in EXCERPTS.items()}
assert EX["dockerfile_head"].startswith("FROM python:3.12-slim") and EX["dockerfile_head"].endswith("RUN pip install --no-cache-dir -r requirements.txt")
assert "pip install succeeded, the image" in EX["chat_reqs"] and EX["chat_reqs"].endswith("gunicorn==26.2.0")
assert EX["validate_checks"].count("def check_") == 2 and "one service on google-genai\n    2.20 and one on 2.22" in EX["validate_checks"]
assert 'SERVICES.rglob("requirements.txt")' in EX["validate_checks"] and 'read_text(encoding="utf-8").splitlines()' in EX["validate_checks"]
assert 'newline="\\n"' in EX["golden_writer"] and "ensure_ascii=False" in EX["golden_writer"]
assert EX["golden_reader"].rstrip().endswith("return [json.loads(line) for line in f if line.strip()]")
assert EX["json_log"].rstrip().endswith("log.info(json.dumps(row))")
assert EX["smoke_call"].rstrip().endswith("return None, str(e)") and "except urllib.error.HTTPError as e:" in EX["smoke_call"]
assert '"--include-email"' in EX["smoke_token"] and "--audiences={API}" in EX["smoke_token"]
assert EX["dockerfile_tail"].splitlines()[0].startswith("HEALTHCHECK") and EX["dockerfile_tail"].splitlines()[2].startswith("CMD [\"gunicorn\"")
assert EX["mcp_async"].count("await ") == 2 and "async with Client(" in EX["mcp_async"] and "asyncio.run(" in EX["mcp_async"]
assert EX["tenant_for"].rstrip().endswith("return None") and ".limit(1).get())" in EX["tenant_for"]
assert EX["chat_thread"].count("await asyncio.to_thread(") == 2
assert "asyncio.create_task(" in EX["chat_pass"] and EX["chat_pass"].rstrip().endswith("await shadow")
assert "retried\n    ONCE after two seconds" in EX["eval_ask"] and EX["eval_ask"].rstrip().endswith("return status, body, ms")
assert "one retry separates a blip from an outage, more would hide one." in EX["eval_ask"]    # quoted in step 7
assert EX["validate_body"].rstrip().endswith("return None") and "A 200 whose body is {} used to count as a refusal" in EX["validate_body"]
assert "timeout=RAG_TIMEOUT_S)" in EX["tools_retrieve"] and 'return {"error": "document retrieval is unavailable",' in EX["tools_retrieve"]
assert "Minted per call. These last an hour" in EX["tools_token"]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the cells, as the page shows them and as the build runs them
T = Path(tempfile.mkdtemp(prefix="lessonB1-"))
HOME = T / "home"
HOME.mkdir()
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(HOME), "USERPROFILE": str(HOME),
       "PATH": str(Path(sys.executable).parent) + os.pathsep + os.environ.get("PATH", ""),   # as activate leaves it
       "HTTP_PROXY": "http://127.0.0.1:9", "HTTPS_PROXY": "http://127.0.0.1:9",               # nothing listens there
       "http_proxy": "http://127.0.0.1:9", "https_proxy": "http://127.0.0.1:9"}
for k in ("PYTHONPATH", "PYTHONHOME", "NO_PROXY", "no_proxy"):
    ENV.pop(k, None)


def run_cell(body: str) -> str:
    """The cell's body, piped to the Basics interpreter as `python -` is in the heredoc. Run twice: the same output both times."""
    outs = []
    for _ in range(2):
        r = subprocess.run([sys.executable, "-"], input=body, cwd=str(T), capture_output=True, text=True, encoding="utf-8",
                           env=ENV, timeout=180)
        assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-3000:])
        outs.append(r.stdout)
    assert outs[0] == outs[1], outs
    return outs[0]


def heredoc(body: str) -> str:
    return f"python - <<'PY'\n{body}\nPY"


def py_literal(v) -> str:
    if isinstance(v, bool) or v is None:
        return repr(v)
    if isinstance(v, list):
        return "[" + ", ".join(py_literal(x) for x in v) + "]"
    return json.dumps(v)                                   # a str or a number: JSON's spelling is Python's too


def row_literal(row: dict) -> str:
    keys = list(row)
    cut = keys.index("question") + 1
    part = lambda ks: ", ".join(f"{json.dumps(k)}: {py_literal(row[k])}" for k in ks)  # noqa: E731
    return "    {" + part(keys[:cut]) + ",\n     " + part(keys[cut:]) + "},"


ROWS_SRC = "\n".join(row_literal(r) for r in SAMPLE)
assert ast.literal_eval("[" + ROWS_SRC + "]") == SAMPLE

VENV_PY = r'''import re, shutil, sys, sysconfig, warnings
from importlib import metadata
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)

venv, base = Path(sys.prefix), Path(sys.base_prefix)     # the venv's folder, and the Python it was made from
print(f"python {sys.version_info.major}.{sys.version_info.minor}, running from a venv: {venv != base}")
print("`python` on PATH is the venv's:", Path(shutil.which("python")).parent.parent == venv)
site = Path(sysconfig.get_paths()["purelib"])            # where pip puts libraries for this Python
print("site-packages is inside the venv:", site.is_relative_to(venv))
for name in ("numpy", "google-genai"):
    home = Path(metadata.distribution(name).locate_file("")).resolve()
    print(f"{name} {metadata.version(name)}, installed in that site-packages: {home == site.resolve()}")
needs = sorted({re.match(r"[\w.-]+", r).group() for r in metadata.requires("google-genai") if "extra ==" not in r})
print(f"google-genai brought {len(needs)} more:", ", ".join(needs))
rule = next(r for r in metadata.requires("google-genai") if r.startswith("google-auth"))
print(f"its rule for google-auth is {rule}; pip chose {metadata.version('google-auth')}")'''

VENV2_PY = r'''import importlib.util, os, shutil, subprocess, sys, tempfile, warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)

root = Path(tempfile.mkdtemp()) / "throwaway-venv"
subprocess.run([sys.executable, "-m", "venv", "--without-pip", str(root)], check=True)   # a venv with nothing in it
cfg = dict(line.split(" = ", 1) for line in (root / "pyvenv.cfg").read_text(encoding="utf-8").splitlines() if " = " in line)
print(f"made {root.name}: pyvenv.cfg says include-system-site-packages = {cfg['include-system-site-packages']}")
exe = root / ("Scripts/python.exe" if os.name == "nt" else "bin/python")                 # Windows, else macOS and Linux
probe = ("import sys, importlib.util, importlib.metadata as m; print(sys.prefix != sys.base_prefix, "
         "importlib.util.find_spec('numpy') is not None, len(list(m.distributions())), sys.base_prefix)")
in_venv, has_numpy, n_packages, its_base = subprocess.run(
    [str(exe), "-c", probe], capture_output=True, text=True, check=True).stdout.split(maxsplit=3)
print(f"its python: running from a venv {in_venv}, numpy importable {has_numpy}, packages installed {n_packages}")
print("made from the same base Python as this venv:", Path(its_base.strip()) == Path(sys.base_prefix))
shutil.rmtree(root.parent)                                # deleting the folder is uninstalling the venv
print(f"deleted: {root.name} exists {root.exists()}; numpy still imports here: {importlib.util.find_spec('numpy') is not None}")'''

JSONL_PY = r'''import json, warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)

ROWS = [   # four rows of the kit's evals/golden.jsonl: a lookup, a join, a refusal and an isolation row (iso-01 without its note)
__ROWS__
]
folder = Path.home() / "basics-b1"                         # / joins the parts, on every operating system
folder.mkdir(exist_ok=True)
path = folder / "golden_sample.jsonl"
with path.open("w", encoding="utf-8", newline="\n") as f:  # newline="\n": the same bytes on Windows
    for row in ROWS:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")   # one object, one line: the kit's writer
print(f"wrote ~/{folder.name}/{path.name}: {path.stat().st_size} bytes, {len(ROWS)} lines")

with path.open(encoding="utf-8") as f:
    back = [json.loads(line) for line in f if line.strip()]   # the kit's reader, line for line
print("read back:", len(back), "rows, equal to what was written:", back == ROWS)
first = path.read_text(encoding="utf-8").splitlines()[0]
print("line 1 on disk:", first)
row = back[0]
print(f"{row['id']}: answerable {row['answerable']!r} is a {type(row['answerable']).__name__}, "
      f"must_contain {row['must_contain']!r} is a {type(row['must_contain']).__name__}")
by_id = {r["id"]: r for r in back}
iso, lk = by_id["iso-01"], by_id["lk-01"]
print(f"iso-01 asks {iso['tenant']} what lk-01 asks {lk['tenant']}: it must contain {iso['must_contain']}, never {iso['must_not_contain']}")
print("answerable:", sum(r["answerable"] for r in back), "of", len(back), "| shapes:", ", ".join(r["shape"] for r in back))
broken = first.replace('"lookup", ', '"lookup" ', 1)        # the same line with one comma lost
try:
    json.loads(broken)
except json.JSONDecodeError as e:
    print(f"the line with one comma lost: {e.msg} (line {e.lineno}, column {e.colno})")'''
JSONL_PY = JSONL_PY.replace("__ROWS__", ROWS_SRC)

HTTP_PY = r'''import json, threading, urllib.error, urllib.request, warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
warnings.filterwarnings("ignore", category=UserWarning)

seen = []                                                  # the server's own log: what arrived, and its answer

class Api(BaseHTTPRequestHandler):                         # a stand-in API: three routes, JSON in and out
    def reply(self, status, body):
        seen.append(f"{self.command} {self.path} {status}")
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/health":
            return self.reply(200, {"status": "ok"})
        self.reply(404, {"detail": f"no route GET {self.path}"})

    def do_POST(self):
        raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))   # read the body first, always
        if self.path != "/v1/query":
            return self.reply(404, {"detail": f"no route POST {self.path}"})
        if not self.headers.get("Authorization", "").startswith("Bearer "):
            return self.reply(401, {"detail": "no bearer token"})
        self.reply(200, {"received": json.loads(raw), "content_type": self.headers["Content-Type"]})

    def log_message(self, *args):                          # quiet: by default every request is logged to stderr
        pass

server = ThreadingHTTPServer(("127.0.0.1", 0), Api)        # 127.0.0.1: this laptop only; port 0: any free port
threading.Thread(target=server.serve_forever, daemon=True).start()
API = f"http://127.0.0.1:{server.server_address[1]}"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # no proxy, even if your shell names one

def call(method, path, token=None, body=None):             # the shape of the kit's smoke/smoke.py call()
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(API + path, data=data, method=method)
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    if body is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with opener.open(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:                    # a 4xx or 5xx: an exception that carries the status and the body
        return e.code, json.loads(e.read())

question = __BODY__
for method, path, token, body in (("GET", "/health", None, None),
                                  ("POST", "/v1/query", "stand-in-token", question),
                                  ("POST", "/v1/query", None, question),
                                  ("GET", "/v1/missing", None, None)):
    status, answer = call(method, path, token, body)
    print(f"{method:4} {path:11} {'token' if token else '     '} -> {status} {json.dumps(answer)}")
server.shutdown()
server.server_close()
print("the server's log:", " | ".join(seen))'''
HTTP_PY = HTTP_PY.replace("__BODY__", LK_BODY)

ASYNC_PY = r'''import asyncio, json, threading, time, urllib.request, warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
warnings.filterwarnings("ignore", category=UserWarning)

WAIT = 0.5                                                 # every answer takes half a second: a stand-in for a slow model
busy, overlap, lock = 0, [], threading.Lock()

class Slow(BaseHTTPRequestHandler):
    def do_GET(self):
        global busy
        with lock:
            busy += 1
            overlap.append(busy > 1)                       # was another request already being served?
        time.sleep(WAIT)
        with lock:
            busy -= 1
        data = json.dumps({"name": self.path.strip("/")}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(("127.0.0.1", 0), Slow)       # a thread per request: it can serve two at once
threading.Thread(target=server.serve_forever, daemon=True).start()
API = f"http://127.0.0.1:{server.server_address[1]}"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def fetch(name):                                           # an ordinary call: it blocks until the answer is in
    with opener.open(f"{API}/{name}", timeout=10) as r:
        return json.loads(r.read())["name"]

async def fetch_in_async_def(name):                        # async def, but the call inside still blocks the loop
    return fetch(name)

async def gather_blocking():
    return await asyncio.gather(fetch_in_async_def("a"), fetch_in_async_def("b"))

async def gather_threads():                                # each call in a thread of its own; the loop awaits both
    return await asyncio.gather(asyncio.to_thread(fetch, "a"), asyncio.to_thread(fetch, "b"))

def timed(label, run):
    overlap.clear()
    t0 = time.perf_counter()
    names = run()
    waits = round((time.perf_counter() - t0) / WAIT)       # how many waits it took, rounded: not seconds
    print(f"{label:30} {names}  about {waits} wait{'s' if waits != 1 else ''}, both in flight at once: {any(overlap)}")

timed("one after the other", lambda: [fetch("a"), fetch("b")])
timed("gather over blocking calls", lambda: asyncio.run(gather_blocking()))
timed("gather over asyncio.to_thread", lambda: asyncio.run(gather_threads()))
server.shutdown()
server.server_close()'''

PROD_PY = r'''import json, threading, time, urllib.error, urllib.request, warnings
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
warnings.filterwarnings("ignore", category=UserWarning)

hits, release = {}, threading.Event()

class Unreliable(BaseHTTPRequestHandler):                  # three ways a real service lets a caller down
    def send_json(self, status, body):
        data = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        hits[self.path] = hits.get(self.path, 0) + 1
        if self.path == "/flaky":                          # a blip: a 503 the first time, an answer the second
            if hits["/flaky"] == 1:
                return self.send_json(503, {"detail": "overloaded, try again"})
            return self.send_json(200, {"answer": "", "citations": [], "answerable": False, "confidence": "low"})
        if self.path == "/hang":                           # takes the request and never answers
            release.wait(10)
            return
        self.send_json(200, {})                            # /empty: a 200 with nothing in it

    def log_message(self, *args):
        pass

server = ThreadingHTTPServer(("127.0.0.1", 0), Unreliable)
threading.Thread(target=server.serve_forever, daemon=True).start()
API = f"http://127.0.0.1:{server.server_address[1]}"
opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))

def get(path, timeout):
    try:
        with opener.open(API + path, timeout=timeout) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())
    except Exception as e:                                 # a timeout or a refused connection: no status at all
        return 0, {"error": type(e).__name__}

def ask(path, timeout=0.5, retries=1):                     # the kit's rule: retry a 5xx or no answer once, after a pause
    status, body = get(path, timeout)
    for _ in range(retries):
        if status == 200 or 400 <= status < 500:
            break
        time.sleep(0.2)                                    # run_eval.py pauses two seconds; a fifth of a second here
        status, body = get(path, timeout)
    return status, body

def well_formed(body):                                     # the kit's shape check, cut down to its four fields
    return (isinstance(body.get("answer"), str) and isinstance(body.get("citations"), list)
            and isinstance(body.get("answerable"), bool) and body.get("confidence") in ("high", "medium", "low"))

for path in ("/flaky", "/hang", "/empty"):
    status, body = ask(path)
    n = hits[path]
    print(f"{path:6} -> {status} {json.dumps(body)} | asked {n} time{'s' if n > 1 else ''} | an answer: {status == 200 and well_formed(body)}")
release.set()
server.shutdown()
server.server_close()'''

CELLS = {"venv": VENV_PY, "venv2": VENV2_PY, "jsonl": JSONL_PY, "http": HTTP_PY, "async": ASYNC_PY, "prod": PROD_PY}
assert sum(c.count("ThreadingHTTPServer((\"127.0.0.1\", 0)") for c in CELLS.values()) == 3     # three servers, all on 127.0.0.1
assert all('warnings.filterwarnings("ignore", category=UserWarning)' in c for c in CELLS.values())
assert all("urlopen" not in c for c in CELLS.values())    # every call goes through the opener with no proxy
OUT = {k: run_cell(v) for k, v in CELLS.items()}
shutil.rmtree(T, ignore_errors=True)

# ---- what each cell printed, pinned to what the prose says
V = OUT["venv"].splitlines()
assert V[:5] == ["python 3.12, running from a venv: True", "`python` on PATH is the venv's: True",
                 "site-packages is inside the venv: True",
                 f"numpy {NUMPY_PIN}, installed in that site-packages: True",
                 f"google-genai {GENAI_PIN}, installed in that site-packages: True"], V
m = re.fullmatch(r"google-genai brought (\d+) more: (.+)", V[5])
GENAI_NEEDS, NEEDS = int(m.group(1)), m.group(2).split(", ")
assert GENAI_NEEDS == len(NEEDS) and "google-auth" in NEEDS and "httpx" in NEEDS and "requests" in NEEDS, V
m = re.fullmatch(r"its rule for google-auth is google-auth\[requests\]<([\d.]+),>=([\d.]+); pip chose ([\d.]+)", V[6])
GAUTH_MAX, GAUTH_MIN, GAUTH_CHOSE = m.groups()
assert len(V) == 7, V
# what google-genai's metadata asks for, read here on the same interpreter the cell ran on: a range for each, never ==
from importlib import metadata as _md  # noqa: E402
assert _md.version("google-genai") == GENAI_PIN
REQUIRES = [r for r in _md.requires("google-genai") if "extra ==" not in r]
assert len(REQUIRES) == GENAI_NEEDS and not any("==" in r for r in REQUIRES), REQUIRES
OPEN = [r for r in REQUIRES if not re.search(r"[<>=~!]", r)]
assert OPEN == ["sniffio"], OPEN                           # the one the prose names as accepting any version
OPEN_ENDED = OPEN[0]
V2 = OUT["venv2"].splitlines()
assert V2 == ["made throwaway-venv: pyvenv.cfg says include-system-site-packages = false",
              "its python: running from a venv True, numpy importable False, packages installed 0",
              "made from the same base Python as this venv: True",
              "deleted: throwaway-venv exists False; numpy still imports here: True"], V2
J = OUT["jsonl"].splitlines()
m = re.fullmatch(r"wrote ~/basics-b1/golden_sample\.jsonl: (\d+) bytes, 4 lines", J[0])
JSONL_BYTES = int(m.group(1))
assert JSONL_BYTES == len("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in SAMPLE).encode("utf-8"))
assert J[1] == "read back: 4 rows, equal to what was written: True"
assert J[2] == "line 1 on disk: " + LK_LINE                 # line 1 is the kit's own line 1, byte for byte
assert J[3] == "lk-01: answerable True is a bool, must_contain ['40,000'] is a list", J[3]
assert J[4] == "iso-01 asks zeta what lk-01 asks acme: it must contain ['25,000'], never ['40,000']", J[4]
assert J[5] == "answerable: 3 of 4 | shapes: lookup, join, refusal, isolation", J[5]
m = re.fullmatch(r"the line with one comma lost: Expecting ',' delimiter \(line 1, column (\d+)\)", J[6])
JSON_COL = int(m.group(1))
assert LK_LINE.index('"lookup", ') + len('"lookup"') + 2 == JSON_COL      # the column of the word after the lost comma
assert len(J) == 7, J
H = OUT["http"].splitlines()
assert H == ['GET  /health           -> 200 {"status": "ok"}',
             f'POST /v1/query   token -> 200 {{"received": {LK_BODY}, "content_type": "application/json"}}',
             'POST /v1/query         -> 401 {"detail": "no bearer token"}',
             'GET  /v1/missing       -> 404 {"detail": "no route GET /v1/missing"}',
             "the server's log: GET /health 200 | POST /v1/query 200 | POST /v1/query 401 | GET /v1/missing 404"], H
A = OUT["async"].splitlines()
assert A == ["one after the other            ['a', 'b']  about 2 waits, both in flight at once: False",
             "gather over blocking calls     ['a', 'b']  about 2 waits, both in flight at once: False",
             "gather over asyncio.to_thread  ['a', 'b']  about 1 wait, both in flight at once: True"], A
P = OUT["prod"].splitlines()
assert P == ['/flaky -> 200 {"answer": "", "citations": [], "answerable": false, "confidence": "low"} | asked 2 times | an answer: True',
             '/hang  -> 0 {"error": "TimeoutError"} | asked 2 times | an answer: False',
             '/empty -> 200 {} | asked 1 time | an answer: False'], P
assert "WAIT = 0.5" in ASYNC_PY and "def ask(path, timeout=0.5, retries=1):" in PROD_PY and "time.sleep(0.2)" in PROD_PY

# ------------------------------------------------------------------ step 1's explorer: validate.py's two checks, ported, and compared
FILES = [{"f": f"services/{s}/requirements.txt", "s": s, "svc": True, "l": PIN_LINES[s]} for s in SERVICES] + \
        [{"f": "shared/requirements.txt", "s": "shared", "svc": False, "l": SHARED_LINES}]

CORE_JS = r"""var RX = /^([A-Za-z0-9_.\-]+)(\[[\w,]+\])?==([\w.]+)\s*$/;   /* validate.py's pattern, unchanged */
function requirementsCheck(files){                       /* check_requirements(): the service files only */
  var n = 0, unpinned = [];
  files.forEach(function(f){
    if (!f.svc) { return; }
    n++;
    f.l.forEach(function(ln){ if (ln.indexOf('==') === -1) { unpinned.push(f.s + ': ' + ln); } });
  });
  if (!n) { return ['WARN', 'no requirements.txt found']; }
  if (unpinned.length) { return ['WARN', unpinned.length + ' unpinned: ' + unpinned.slice(0, 6).join(', ')]; }
  return ['PASS', n + ' files, all deps pinned'];
}
function pinsCheck(files){                               /* check_pin_consistency(): the services' files and shared/ */
  var pins = {}, order = [];
  files.forEach(function(f){
    f.l.forEach(function(ln){
      var m = RX.exec(ln);
      if (!m) { return; }
      if (!Object.prototype.hasOwnProperty.call(pins, m[1])) { pins[m[1]] = {}; order.push(m[1]); }
      pins[m[1]][f.s] = m[3];
    });
  });
  var shared = order.filter(function(p){ return Object.keys(pins[p]).length > 1; });
  var bad = shared.filter(function(p){
    var seen = {};
    Object.keys(pins[p]).forEach(function(s){ seen[pins[p][s]] = true; });
    return Object.keys(seen).length > 1;
  });
  if (!shared.length) { return ['WARN', 'no package is shared by two services']; }
  if (bad.length) {
    return ['FAIL', bad.length + ' package(s) pinned differently: ' + bad.slice(0, 4).map(function(p){
      return p + ' (' + Object.keys(pins[p]).sort().map(function(s){ return s + '=' + pins[p][s]; }).join(', ') + ')';
    }).join('; ')];
  }
  return ['PASS', shared.length + ' shared packages agree across ' + files.length + ' files'];
}
function withLine(files, fi, li, line){
  return files.map(function(f, i){
    return i !== fi ? f : {f: f.f, s: f.s, svc: f.svc, l: f.l.map(function(x, j){ return j === li ? line : x; })};
  });
}"""

UI_JS = r"""var $ = function(id){ return document.getElementById(id); };
var fileSel = $('pe-file'), pkgSel = $('pe-pkg'), ver = $('pe-ver'), drop = $('pe-drop');
if (!fileSel || !pkgSel || !ver || !drop) { return; }
function key(line){ var m = /^[A-Za-z0-9_.\-]+/.exec(line); return m ? m[0] : line; }
function head(line){ var i = line.indexOf('=='); return i === -1 ? line : line.slice(0, i); }
function version(line){ var i = line.indexOf('=='); return i === -1 ? '' : line.slice(i + 2); }
function count(files, k){ return files.filter(function(f){ return f.l.some(function(ln){ return key(ln) === k; }); }).length; }
FILES.forEach(function(f, i){ var o = document.createElement('option'); o.value = String(i); o.textContent = f.f + ' (' + f.l.length + ' pins)'; fileSel.appendChild(o); });
function fillPkgs(keep){
  var f = FILES[+fileSel.value], names = f.l.map(key), j = names.indexOf(keep);
  pkgSel.textContent = '';
  names.forEach(function(n, k){ var o = document.createElement('option'); o.value = String(k); o.textContent = n; pkgSel.appendChild(o); });
  pkgSel.value = String(j === -1 ? 0 : j);
  ver.value = version(f.l[+pkgSel.value]);
  drop.checked = false;
}
function show(el, name, r){
  el.className = 'pe-check' + (r[0] === 'PASS' ? '' : r[0] === 'WARN' ? ' warn' : ' fail');
  el.textContent = 'validate.py, ' + name + ': [' + r[0] + '] ' + r[1];
}
function render(){
  var fi = +fileSel.value, li = +pkgSel.value, old = FILES[fi].l[li];
  var line = drop.checked ? head(old) : head(old) + '==' + ver.value.trim();
  var files = withLine(FILES, fi, li, line), f = files[fi], k = key(line);
  var shared = f.l.filter(function(ln){ return count(files, key(ln)) > 1; }).length;
  $('pe-sum').textContent = f.f + ': ' + f.l.length + ' libraries, ' + shared + ' of them in another file too';
  var chips = $('pe-chips');
  chips.textContent = '';
  f.l.forEach(function(ln, j){
    var c = count(files, key(ln)), s = document.createElement('span');
    s.className = 'pe-chip' + (c > 1 ? ' sh' : '') + (j === li ? ' on' : '');
    s.textContent = ln + (c > 1 ? ' ' + String.fromCharCode(183) + ' ' + c : '');   /* a middle dot, then the count */
    chips.appendChild(s);
  });
  var who = [];
  files.forEach(function(g){ g.l.forEach(function(ln){ if (key(ln) === k) { who.push(g.s + (ln.indexOf('==') === -1 ? ' unpinned' : ' ' + version(ln))); } }); });
  $('pe-who').textContent = k + ' is in ' + who.length + ' file' + (who.length === 1 ? '' : 's') + ': ' + who.join(', ');
  show($('pe-req'), 'requirements', requirementsCheck(files));
  show($('pe-pins'), 'pins', pinsCheck(files));
}
var current = 'google-genai';                            /* the library stays chosen when the file changes, if it is there */
fileSel.addEventListener('change', function(){ fillPkgs(current); current = key(FILES[+fileSel.value].l[+pkgSel.value]); render(); });
pkgSel.addEventListener('change', function(){
  var ln = FILES[+fileSel.value].l[+pkgSel.value];
  current = key(ln); ver.value = version(ln); drop.checked = false; render();
});
ver.addEventListener('input', render);
drop.addEventListener('change', render);
fileSel.value = String(__START__);
fillPkgs(current);
render();"""
START = SERVICES.index("rag-api")
UI_JS = UI_JS.replace("__START__", str(START))
assert "google-genai" in [re.match(r"[A-Za-z0-9_.\-]+", ln).group() for ln in PIN_LINES["rag-api"]]


def py_checks(files: list) -> list:
    """validate.py's own two checks over a copy of the kit's requirements files with one line changed."""
    root = Path(tempfile.mkdtemp(prefix="lessonB1-pins-"))
    for f in files:
        p = root / (f"services/{f['s']}" if f["svc"] else "shared") / "requirements.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("\n".join(f["l"]) + "\n", encoding="utf-8")
    saved = validate.SERVICES
    validate.SERVICES = root / "services"
    try:
        del validate.results[:]
        validate.check_requirements()
        validate.check_pin_consistency()
        return [[s, d] for _, s, d in validate.results]
    finally:
        validate.SERVICES = saved
        shutil.rmtree(root, ignore_errors=True)


CASES = [[-1, -1, ""]]                                       # the kit as it is, then every pin given a new version or none
for i, f in enumerate(FILES):
    for j, ln in enumerate(f["l"]):
        CASES += [[i, j, ln.split("==", 1)[0] + "==0.0.0"], [i, j, ln.split("==", 1)[0]]]
PY_SIDE = []
for i, j, line in CASES:
    files = FILES if i < 0 else [g if k != i else {**g, "l": [line if n == j else x for n, x in enumerate(g["l"])]} for k, g in enumerate(FILES)]
    PY_SIDE.append(py_checks(files))
assert PY_SIDE[0] == [[s, d] for _, s, d in CHECKS]           # the copy reads the same as the kit itself
NODE = (CORE_JS + "\nvar FILES = " + json.dumps(FILES) + ", CASES = " + json.dumps(CASES) + ";\n"
        "process.stdout.write(JSON.stringify(CASES.map(function(c){ var fs = c[0] < 0 ? FILES : withLine(FILES, c[0], c[1], c[2]);"
        " return [requirementsCheck(fs), pinsCheck(fs)]; })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
JS_SIDE = json.loads(node.stdout)
assert len(JS_SIDE) == len(PY_SIDE)
for case, a_, b_ in zip(CASES, JS_SIDE, PY_SIDE):
    assert a_ == b_, (case, a_, b_)
assert any(r[1][0] == "FAIL" for r in PY_SIDE) and any(r[0][0] == "WARN" for r in PY_SIDE)
N_CASES = len(CASES) - 1
JS = ("<script>\n(function(){\n'use strict';\nvar FILES = " + json.dumps(FILES) + ";\n" + CORE_JS + "\n" + UI_JS + "\n})();\n</script>\n")
assert "</" not in JS[len("<script>"):-len("</script>\n")] and "<div" not in JS


# ------------------------------------------------------------------ the windows and the numbers the parts name
def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + esc(code) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + esc(text.rstrip("\n")) + "</pre></div>\n")


CELL_LABELS = {
    "venv": "run on your laptop, in the shell where the setup block activated ~/basics-venv",
    "venv2": "run on your laptop: a second venv in a temporary folder, deleted at the end",
    "jsonl": "run on your laptop: writes ~/basics-b1/golden_sample.jsonl",
    "http": "run on your laptop: a server on 127.0.0.1, stopped at the end; nothing leaves the machine",
    "async": "run on your laptop: the same kind of server, slowed down on purpose",
    "prod": "run on your laptop: a server that misbehaves on purpose",
}
OUT_LABELS = {
    "venv": "expected (your Python's minor version, and the google-auth pip chose for you, may differ)",
    "venv2": "expected",
    "jsonl": "expected",
    "http": "expected",
    "async": "expected (the waits are counted and rounded, not timed in seconds, so a slower laptop should print the same)",
    "prod": "expected",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], heredoc(v)) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
WIN["OUT_VALIDATE"] = out_window("output of those two checks, run on the kit when this page was built", VALIDATE_OUT)
WAITS_APART, WAITS_TOGETHER = (re.search(r"about (\d+) wait", line).group(1) for line in (A[0], A[2]))
STATS = {
    "N_SERVICES": N_SERVICES, "N_PIN_LINES": N_PIN_LINES, "N_SLIM": N_SLIM, "N_OTHER_BASE": N_OTHER_BASE,
    "N_SHARED": N_SHARED, "N_PIN_FILES": N_PIN_FILES, "N_CASES": N_CASES, "N_GOLDEN": N_GOLDEN,
    "N_JSONL": N_JSONL, "JSONL_LINES": f"{JSONL_LINES:,}", "N_GENAI": N_GENAI, "GENAI_PIN": GENAI_PIN, "NUMPY_PIN": NUMPY_PIN,
    "KIT_GAUTH": KIT_GAUTH, "N_GAUTH_SVC": N_GAUTH_SVC, "RAG_PINS": RAG_PINS, "RAG_WORKERS": RAG_WORKERS,
    "EVAL_TIMEOUT": EVAL_TIMEOUT, "SMOKE_TIMEOUT": SMOKE_TIMEOUT, "RAG_TIMEOUT": RAG_TIMEOUT,
    "GENAI_NEEDS": GENAI_NEEDS, "OPEN_ENDED": OPEN_ENDED, "GAUTH_MIN": GAUTH_MIN, "GAUTH_MAX": GAUTH_MAX, "GAUTH_CHOSE": GAUTH_CHOSE,
    "JSONL_BYTES": JSONL_BYTES, "JSON_COL": JSON_COL, "WAITS_APART": WAITS_APART, "WAITS_TOGETHER": WAITS_TOGETHER,
    "LK_LINE": esc(LK_LINE), "LK_BODY": esc(LK_BODY),
    **{f"SETUP_{n}": esc(line) for n, line in enumerate(SETUP_LINES, 1)},
}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(VALIDATE_OUT)
    print({k: v for k, v in STATS.items() if not k.startswith(("LK_", "SETUP_"))})
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **{k: str(v) for k, v in STATS.items()}}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


# ---- the counts the prose spells out in words, held to what they count
PART = {k: pb.part(LESSON, k) for k in "abc"}


def rows_after(text: str, marker: str) -> int:
    seg = text[text.index(marker):]
    return seg[seg.index("<tbody>"):seg.index("</tbody>")].count("<tr>")


assert "Ten terms" in PART["a"] and rows_after(PART["a"], 'id="s2"') == 10
assert "is six lines" in PART["b"] and rows_after(PART["b"], "What the setup block did") == len(SETUP_LINES) == 6
assert "The first five lines are the venv doing its job. The last two" in PART["b"] and len(V) == 7
assert "Ten checks" in PART["c"] and rows_after(PART["c"], 'id="s8"') == 10
assert "four rows" in PART["c"] and len(SAMPLE) == 4 and "the three servers" in PART["c"]
assert "The first two runs took the same time" in PART["c"] and A[0].split("]", 1)[1] == A[1].split("]", 1)[1]

body = "".join([subst(fill(PART["a"])), setup, subst(fill(PART["b"])), subst(fill(PART["c"]))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"cells: {len(CELLS)} run twice each on {sys.version.split()[0]}, all output pinned | kit: {N_SERVICES} requirements files, "
      f"{N_PIN_LINES} pins, validate.py's checks ported and compared on {N_CASES} one-pin changes | {len(EXCERPTS)} excerpts")
