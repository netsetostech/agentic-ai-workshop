"""Build lesson 12.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Improve the agent safely: eval-gated self-improvement. One answer that went wrong on the lane becomes one rule for
rag-api's prompt: gemini-3.1-pro-preview proposes it (make improve ROW=), services/rag-api/prompt_rules.py checks it,
a person accepts it as the next prompt version (make improve REVIEWER=), the printed R(...) row joins the golden set by
lesson 4.1's method, and the version goes out on a no-traffic candidate (make prompt-candidate PROMPT_VERSION=v4) that
lesson 11.2's make gate judges before make promote-gated moves traffic, or the commit is reverted. The chapter's proof:
a production row turned into a candidate prompt change, gated by eval-live, then promoted or rolled back.

Build-time proof (offline, Rs 0), on a temporary copy of the kit: the row cell over a stand-in answer; improve.py's own
main() for --prompt-only, a row whose figure is not in the documents, a "never refuse" rule (refused), a scripted
proposal in place of the model (the kit test's Proposer and token counts) and accept; the hashes of the copy before
and after (only prompt_rules.json and the proposal change); the paste cell, build_golden.py and make eval's offline
gate over the new row; improve.py version for a listed and an unlisted version; with_rules() refusing an unlisted
version, as the rag-api would at import; write() refusing every file of the evaluator; make prompt-version on the kit,
and again with v4 accepted; the validator and byte-identity cells on the kit itself. The Level 0 panel's check is
prompt_rules.problems() ported to JavaScript and compared with the kit's own on every case below, through node.
Live: every output a lane prints is pb.recorded() from the author's run (RUN_LIST.md, batch 4).
"""
import ast
import contextlib
import datetime as dt
import hashlib
import html
import importlib.util
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
os.environ.pop("DOCUMIND_PROFILE", None)           # shared/prices.py prices at list price unless the profile is local
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "12.4"
title = ("<title>Lesson 12.4 Improve the agent safely: eval-gated self-improvement - a production row, a person and "
         "the gate | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
HOME = "/home/you"
LANE_KIT = HOME + "/deploy_module_rag"
REVIEWER = "you@your-company.com"
EX_DAY = dt.date(2026, 10, 13)          # the example's acceptance date: the day kit R6 was written (generator.py's comment)
GEN, CFG = "services/rag-api/generator.py", "services/rag-api/config.py"
PRP, PRJ, REG = "services/rag-api/prompt_rules.py", "services/rag-api/prompt_rules.json", "services/rag-api/prompt_versions.json"
IMP, MK, MAIN, SC = "evals/improve.py", "mk/generation.mk", "services/rag-api/main.py", "services/rag-api/semantic_cache.py"
MT, RE, BG, PRICES_PY = "evals/make_trainset.py", "evals/run_eval.py", "evals/build_golden.py", "shared/prices.py"
PIN, TEST_IMP, DEPLOY_API = "commands/prompt_pin.py", "evals/tests/test_improve.py", "commands/lesson-12.2.sh"
PY = sys.executable

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.rt-presets{display:flex;flex-wrap:wrap;gap:6px;margin:4px 0 10px;}
.rt-presets button{font:inherit;font-size:13px;line-height:1.3;padding:6px 10px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(36px,var(--touch));}
.rt-presets button[aria-pressed="true"]{border-color:var(--teal);background:var(--teal-light);color:var(--teal-dark);font-weight:600;}
.rt-presets button:active{transform:translateY(1px);}
.rt-lab{display:block;font-size:var(--small-size);font-weight:600;color:var(--navy);margin:6px 0 4px;}
.rt textarea{display:block;width:100%;box-sizing:border-box;font-family:var(--mono);font-size:16px;line-height:1.5;padding:8px 10px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);min-height:88px;resize:vertical;}
.rt-opts{display:flex;flex-wrap:wrap;gap:8px 18px;align-items:center;margin:10px 0 6px;font-size:var(--small-size);color:var(--navy);}
.rt-opts label{display:flex;gap:8px;align-items:center;min-height:max(36px,var(--touch));}
.rt-opts select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.rt-opts input[type="checkbox"]{width:20px;height:20px;accent-color:var(--teal);}
.rt-out{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:8px 0;font-size:13px;line-height:1.6;color:var(--slate);overflow-wrap:anywhere;}
.rt-out .mono{font-family:var(--mono);font-size:12px;color:var(--navy);}
.rt-out .pass{color:var(--teal-dark);font-weight:600;}
.rt-out .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()


# ================================================================== the kit, read
def load(path: Path, name: str):
    """A kit module loaded by path, as improve.py and the kit's tests load them (each is standard library only)."""
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def kit(rel: str) -> str:
    return (KIT / rel).read_text(encoding="utf-8")


def literal_of(src: str, name: str) -> str:
    """A module-level string constant, read by AST as make prompt-version reads generator.py's."""
    values = [ast.literal_eval(n.value) for n in ast.parse(src).body if isinstance(n, ast.Assign)
              and any(isinstance(t, ast.Name) and t.id == name for t in n.targets)]
    assert len(values) == 1, (name, len(values))
    return values[0]


pr = load(KIT / PRP, "prompt_rules_124")
improve = load(KIT / IMP, "improve_124")
run_eval = load(KIT / RE, "run_eval_124")
prices = load(KIT / PRICES_PY, "prices_124")

SYSTEM, DATED_RULE = improve.literal(KIT, "SYSTEM"), improve.literal(KIT, "DATED_RULE")
TRAIN_SYSTEM = literal_of(kit(MT), "SYSTEM")
assert pr.with_rules(SYSTEM, "documind-rag", "v3") is SYSTEM and SYSTEM == TRAIN_SYSTEM   # v3 serves the literal itself
DEFAULTS = improve.config_defaults(KIT)
assert DEFAULTS == {"prompt_id": "documind-rag", "prompt_version": "v3"}, DEFAULTS
DOC = pr.load()
assert DOC["versions"] == {"v3": {"rules": []}}, DOC["versions"]
OWN, MAX_WORDS = pr.own_rules(SYSTEM), pr.MAX_WORDS
assert (OWN, MAX_WORDS) == (5, 40)
PHRASES = [p for _, _, group in pr.FORBIDDEN for p in group]
N_PHRASES = len(PHRASES)
assert [n for n, _, _ in pr.FORBIDDEN] == [3, 1, 2, 5, None]           # the prose names rules 1, 2, 3 and 5, and "the rules above"
REG_SHA = json.loads(kit(REG))["versions"]["documind-rag@v3"]
assert REG_SHA == hashlib.sha256((SYSTEM + DATED_RULE).encode("utf-8")).hexdigest()
REBIND = 'globals()["SYSTEM"] = with_rules(SYSTEM, settings.prompt_id, settings.prompt_version)'
assert kit(GEN).rstrip("\n").split("\n")[-1] == REBIND                 # the two lines are generator.py's last
assert "return max(1, len(text) // 4)" in kit("services/rag-api/context_budget.py")   # the kit's estimate_tokens
assert "PROMPT_VERSION" not in kit(DEPLOY_API) and "--set-env-vars=" in kit(DEPLOY_API)  # deploy-services drops it
assert re.search(r"^SYSTEM = \($", kit("services/chat/brains.py"), re.M)  # the chat brains keep a prompt of their own

MODEL, LOCATION = improve.MODEL, improve.LOCATION
assert (MODEL, LOCATION) == ("gemini-3.1-pro-preview", "global")
assert improve.SCHEMA["required"] == ["rule", "why"] and set(improve.SCHEMA["properties"]) == {"rule", "why"}
assert set(improve.RETRY["http_status_codes"]) == {408, 429, 500, 502, 503, 504}   # timeouts, 429s and server errors
RETRY_N = improve.RETRY["attempts"]
EVALUATOR = improve.EVALUATOR
assert EVALUATOR == ("evals/run_eval.py", "evals/required.json", "evals/golden.jsonl", "evals/build_golden.py",
                     "evals/manifest.json", "evals/corpus", "evals/demo")
assert improve.PROPOSAL.startswith("evals/reports/") and "evals/reports/" in kit(".gitignore").split("\n")
assert "__pycache__/" in kit(".gitignore").split("\n")
assert "about Rs 2" in improve.__doc__ and "about\n# Rs 2, printed" in kit(MK)   # the kit's own estimate of a proposal

# the golden set and the gate's rules (lessons 4.1 to 4.3 teach them)
GOLDEN = run_eval.load_golden()
N_ROWS = len(GOLDEN)
UNANS = [r for r in GOLDEN if not r["answerable"]]
N_UNANS, N_REF = len(UNANS), sum(r["shape"] == "refusal" for r in GOLDEN)
N_ISO_UNANS = sum(r["shape"] == "isolation" for r in UNANS)
assert N_UNANS == N_REF + N_ISO_UNANS      # the prose: the rows the documents cannot answer are the refusal and isolation rows
REQUIRED = run_eval.load_required()
N_REQ = len(REQUIRED)
TH = run_eval.THRESHOLDS
N_TH, REFUSAL = len(TH), TH["refusal_rate"]
N_RED = next(k for k in range(1, N_UNANS + 1) if (N_UNANS - k) / N_UNANS < REFUSAL)   # how many answered turn it red
N_RED_REF = next(k for k in range(1, N_REF + 1) if (N_REF - k) / N_REF < REFUSAL)    # over the refusal rows alone
assert N_RED_REF == 1
assert (N_ROWS, N_UNANS, N_REF, N_REQ, N_TH, REFUSAL, N_RED) == (65, 18, 8, 15, 9, 0.90, 2), \
    (N_ROWS, N_UNANS, N_REF, N_REQ, N_TH, REFUSAL, N_RED)
LK04 = next(r for r in GOLDEN if r["id"] == "lk-04")
assert LK04["must_contain"] == ["15"] and LK04["must_retrieve"] == ["PB-02", "hr_policy_2026"], LK04

# the rupees: shared/prices.py, at lesson 11.2's typical answer
GEN_MODEL = re.search(r"^GENERATOR_MODEL \?= (\S+)$", kit("Makefile"), re.M).group(1)
assert GEN_MODEL == "gemini-3.6-flash" and re.search(r"^PY\s+\?= python$", kit("Makefile"), re.M)
RATE_IN, RATE_OUT = prices.PRICES[GEN_MODEL]
TYPICAL = (2000, 300)                  # the course's typical answer (lessons 4.3, 11.1 and 11.2): 2,000 tokens in, 300 out
RS_ANSWER = (TYPICAL[0] * RATE_IN + TYPICAL[1] * RATE_OUT) / 1_000_000 * prices.USD_INR
N_GATE = N_ROWS + 1                    # every golden row, the one you paste among them
RS_GATE_X = RS_ANSWER * N_GATE
N_LANE = 2 + 2 + 1                     # step 3 (the UI and the cell), step 8 (live and candidate), step 9 (once more)
RS_PROPOSE = 2                         # the kit's own "about Rs 2" (improve.py's docstring, mk/generation.mk)
RS_PASS = RS_ANSWER * N_LANE + RS_PROPOSE + RS_GATE_X
RS_WITH_OPTIONAL = RS_PASS + RS_GATE_X  # the optional step: your own rule (Rs 0), another candidate and another gate
assert (prices.USD_INR, RATE_IN, RATE_OUT) == (85, 1.50, 7.50)

# the kit test's scripted proposer: its fixed "never refuse" rule and the usage google-genai reports for it
TEST_SRC = kit(TEST_IMP)
NEVER = re.search(r'^NEVER = "(.+)"$', TEST_SRC, re.M).group(1)
U_IN, U_CAND, U_THINK = (int(v) for v in re.search(
    r"USAGE = SimpleNamespace\(prompt_token_count=(\d+), candidates_token_count=(\d+), thoughts_token_count=(\d+)\)",
    TEST_SRC).groups())
RS_PROPOSE_TEST = prices.inr(prices.usd(MODEL, U_IN, U_CAND + U_THINK))   # the thinking is billed as output

# the recipes this page's commands expand
MKSRC = kit(MK)
MK_LINES = MKSRC.split("\n")
IMPROVE_RECIPE = ('\t$(PY) evals/improve.py $(if $(REVIEWER),accept --reviewer "$(REVIEWER)",propose --row "$(ROW)" '
                  '--project "$(PROJECT)") $(IMPROVE_ARGS)')
IMPROVE_LINE = MK_LINES.index(IMPROVE_RECIPE) + 1           # make names it in the error line when the recipe fails
assert MK_LINES[IMPROVE_LINE - 2] == "improve:"
PC_RECIPE = ["prompt-candidate: guard-project",
             '\t@$(PY) evals/improve.py version "$(PROMPT_VERSION)"',
             "\tgcloud run services update documind-api --region $(REGION) --project $(PROJECT) --image "
             "$(IMAGE_REPO)/api:$(GIT_SHA) --no-traffic --tag candidate --update-env-vars "
             "GIT_SHA=$(GIT_SHA),PROMPT_VERSION=$(PROMPT_VERSION) --quiet",
             "\t@$(MAKE) --no-print-directory record-candidate PROJECT=$(PROJECT) REGION=$(REGION)"]
i = MK_LINES.index(PC_RECIPE[0])
assert MK_LINES[i:i + 4] == PC_RECIPE, MK_LINES[i:i + 4]
assert "prompt-version:\n\t$(PY) commands/prompt_pin.py\n" in MKSRC and "eval:\n\t$(PY) evals/run_eval.py\n" in kit("Makefile")


def echo_improve(row: str = "", reviewer: str = "", args: str = "") -> str:
    """make improve's recipe line as make echoes it, PROJECT taken from the setup section's environment."""
    step = f'accept --reviewer "{reviewer}"' if reviewer else f'propose --row "{row}" --project "{PROJ}"'
    return f"python evals/improve.py {step} {args}"


MAKE_FAIL = f"make: *** [{MK}:{IMPROVE_LINE}: improve] Error 1"

# ================================================================== the page's example (a stand-in, not a lane's answer)
EX_Q = "I am still on probation. If I resign now, how long is my notice?"
EX_ANSWER = "A confirmed employee at grade E3 or above serves a notice period of 60 days."
EX_WRONG = "It gave the notice of a confirmed employee; the question is about probation."
EX_CONTAIN, EX_RETRIEVE = ["15"], ["PB-02", "hr_policy_2026"]
EX_RULE = ("When the context gives different figures for different conditions, give the figure whose condition matches "
           "the question, and name that condition.")
EX_WHY = "The answer gave the figure stated for one condition when the question was about another."
PAST = ("When the context only partly covers the question, give the closest answer it supports rather than saying it "
        "is not covered.")
BAD_FIGURE = "17 days"
HR = " ".join(kit("evals/corpus/acme/hr_policy_2026.md").split())
assert "During probation the notice period is 15 days" in HR                     # PB-02
assert EX_ANSWER[:-1] in HR                                                       # NP-03, word for word
for rule in (EX_RULE, PAST):
    assert pr.problems(rule) == [], (rule, pr.problems(rule))
assert pr.problems(NEVER) == ['"never refuse" undoes SYSTEM\'s rule 3 (say so, answerable=false, when the context does not hold the answer)']

# ================================================================== the flow, offline, on a copy of the kit
TMP = tempfile.TemporaryDirectory(prefix="b124_")
T = Path(TMP.name).resolve()
K2, H2 = T / "deploy", T / "home"
H2.mkdir()
for rel in ("evals", "services/rag-api", "shared"):
    shutil.copytree(KIT / rel, K2 / rel, ignore=shutil.ignore_patterns("__pycache__", "reports", "tests", "node_modules"))
(K2 / "commands").mkdir()
shutil.copyfile(KIT / PIN, K2 / PIN)
for name in (".gitignore", "Makefile"):
    shutil.copyfile(KIT / name, K2 / name)


def lane(text: str) -> str:
    """The copy's paths as a learner's: the kit is ~/deploy_module_rag, the temporary home is /home/you."""
    for base, to in ((K2, LANE_KIT), (H2, HOME)):
        text = re.sub(re.escape(str(base)) + r"((?:[\\/][^\s'\"]*)?)", lambda m: to + m.group(1).replace("\\", "/"), text)
    return text


def env_for(**extra) -> dict:
    """A subprocess's environment: no Google credentials, no bytecode, the temporary home, the cell's variables."""
    env = {k: v for k, v in os.environ.items()
           if k not in ("GOOGLE_APPLICATION_CREDENTIALS", "GOOGLE_CLOUD_PROJECT", "CLOUDSDK_CORE_PROJECT")}
    env.update(PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", HOME=str(H2), USERPROFILE=str(H2), **extra)
    return env


def run(argv: list, cwd: Path, stdin: str | None = None, ok=(0,), **extra) -> str:
    """One offline command: what it printed, stdout then stderr, with the copy's paths made a learner's."""
    r = subprocess.run(argv, cwd=cwd, input=stdin, capture_output=True, text=True, encoding="utf-8", env=env_for(**extra))
    assert r.returncode in ok, (argv, r.returncode, r.stdout[-1500:], r.stderr[-1500:])
    return lane(r.stdout + r.stderr).rstrip("\n")


def hashes(root: Path) -> dict:
    """Every file of the copy by its sha256, bytecode caches aside (the kit test's own comparison)."""
    return {p.relative_to(root).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(root.rglob("*")) if p.is_file() and "__pycache__" not in p.parts}


def imp(*argv, client=None) -> tuple:
    """improve.py's own main() on the copy: (exit code, stdout, stderr)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = improve.main(["--kit", str(K2)] + [str(a) for a in argv], client=client)
    return code, lane(out.getvalue()).rstrip("\n"), lane(err.getvalue()).rstrip("\n")


class Proposer:
    """The kit test's scripted gemini-3.1-pro-preview: the request kept, a fixed reply, the usage google-genai reports."""
    USAGE = SimpleNamespace(prompt_token_count=U_IN, candidates_token_count=U_CAND, thoughts_token_count=U_THINK)

    def __init__(self, reply: dict):
        self.reply, self.requests, self.models = reply, [], self

    def generate_content(self, model, contents, config):
        self.requests.append({"model": model, "contents": contents, "config": config})
        return SimpleNamespace(text=json.dumps(self.reply), parsed=None, usage_metadata=self.USAGE)


def heredoc(code: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{code}\nPY"


CELLS, OUT = {}, {}

# ---- step 3: the row, written by the page's cell over a stand-in answer
ROW_PY = r'''import json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
home = os.path.expanduser("~")
answer = json.load(open(os.path.join(home, "answer124.json"), encoding="utf-8"))
version = json.load(open(os.path.join(home, "version124.json"), encoding="utf-8"))
row = {"tenant": os.environ["TENANT"], "question": os.environ["Q"], "answer": answer["answer"],
       "citations": answer.get("citations", []), "prompt_version": version["prompt"].split("@")[1],
       "wrong": os.environ.get("WRONG", ""),
       "expected": {"shape": os.environ["SHAPE"], "must_contain": json.loads(os.environ.get("CONTAIN") or "[]"),
                    "must_retrieve": json.loads(os.environ.get("RETRIEVE") or "[]")}}
path = os.path.join(home, "row124.json")
with open(path, "w", encoding="utf-8") as f:
    json.dump(row, f, indent=2, ensure_ascii=False)
print(path)
print(json.dumps(row, indent=2, ensure_ascii=False))'''
ROW_ENV = (f'export WRONG="{EX_WRONG}"   # yours, in your own words\n'
           f"export SHAPE=lookup CONTAIN='{json.dumps(EX_CONTAIN)}' RETRIEVE='{json.dumps(EX_RETRIEVE)}'   "
           "# what a right answer holds (lesson 4.1)\n")
CELLS["row"] = heredoc(ROW_PY, ROW_ENV)
(H2 / "answer124.json").write_text(json.dumps({"answer": EX_ANSWER, "citations": [], "confidence": "medium",
                                               "answerable": True}), encoding="utf-8")
(H2 / "version124.json").write_text(json.dumps({"prompt": f"{DEFAULTS['prompt_id']}@{DEFAULTS['prompt_version']}"}),
                                    encoding="utf-8")
OUT["row"] = run([PY, "-"], T, ROW_PY, TENANT="acme", Q=EX_Q, WRONG=EX_WRONG, SHAPE="lookup",
                 CONTAIN=json.dumps(EX_CONTAIN), RETRIEVE=json.dumps(EX_RETRIEVE))
ROW_FILE = H2 / "row124.json"
EX_ROW = json.loads(ROW_FILE.read_text(encoding="utf-8"))
assert OUT["row"].startswith(HOME + "/row124.json\n") and EX_ROW["expected"]["must_retrieve"] == EX_RETRIEVE
assert improve.corpus_problems(KIT, "acme", improve.check_row(EX_ROW)) == []

# ---- step 5: what the proposer is sent, a row that could never pass, "never refuse", a scripted proposal
ROW_ARG = HOME + "/row124.json"
code, PROMPT_TEXT, err = imp("propose", "--row", ROW_FILE, "--prompt-only")
assert code == 0 and not err
CELLS["prompt"] = 'make improve ROW="$HOME/row124.json" IMPROVE_ARGS=--prompt-only'
OUT["prompt"] = echo_improve(ROW_ARG, args="--prompt-only") + "\n" + PROMPT_TEXT
for needle in (SYSTEM.rstrip(), DATED_RULE.strip(), EX_Q, EX_ANSWER, EX_WRONG, "citations: none recorded",
               f'contains "15" and cites PB-02, hr_policy_2026', f"at most {MAX_WORDS} words", "never refuse; do not refuse"):
    assert needle in PROMPT_TEXT, needle

bad_row = dict(EX_ROW, expected={"shape": "lookup", "must_contain": [BAD_FIGURE], "must_retrieve": EX_RETRIEVE})
(H2 / "bad124.json").write_text(json.dumps(bad_row), encoding="utf-8")
code, out, err = imp("propose", "--row", H2 / "bad124.json", "--prompt-only")
assert code == 1 and not out and err.startswith("improve: refused: ") and BAD_FIGURE in err
OUT["bad"] = echo_improve(ROW_ARG, args="--prompt-only") + "\n" + err + "\n" + MAKE_FAIL

BEFORE = hashes(K2)
code, out, err = imp("propose", "--row", ROW_FILE, "--rule", NEVER)
assert code == 1 and not err and "Nothing was written." in out and hashes(K2) == BEFORE
CELLS["never"] = (f"make improve ROW=\"$HOME/row124.json\" IMPROVE_ARGS=\"--rule '{NEVER}'\"; echo \"exit $?\"")
OUT["never"] = echo_improve(ROW_ARG, args=f"--rule '{NEVER}'") + "\n" + out + "\n" + MAKE_FAIL + "\nexit 2"

model = Proposer({"rule": EX_RULE, "why": EX_WHY})
code, SCRIPTED, err = imp("propose", "--row", ROW_FILE, "--project", PROJ, client=model)
assert code == 0 and not err, (SCRIPTED, err)
req, = model.requests
assert req["model"] == MODEL and req["config"] == improve.config() and req["contents"] == PROMPT_TEXT  # what --prompt-only printed
assert f"Rs {RS_PROPOSE_TEST:.2f} at list price" in SCRIPTED and f"rule:      {OWN + 1}. {EX_RULE}" in SCRIPTED
OUT["scripted"] = SCRIPTED
CELLS["propose"] = 'make improve ROW="$HOME/row124.json" PROJECT="$PROJECT"'

# ---- step 6: accept, what changed, the paste, the golden set built and checked, the guard
out, err = io.StringIO(), io.StringIO()
with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
    code = improve.accept(K2, REVIEWER, today=EX_DAY)
ACCEPT = lane(out.getvalue()).rstrip("\n")
assert code == 0 and not err.getvalue(), err.getvalue()
CHANGED = sorted(f for f, h in hashes(K2).items() if BEFORE.get(f) != h)
assert CHANGED == sorted([PRJ, improve.PROPOSAL]), CHANGED
R_LINE = next(line for line in ACCEPT.split("\n") if line.startswith('    R("'))
NEXT_ID = R_LINE.split('"')[1]
assert NEXT_ID == improve.next_id(improve.golden_ids(KIT), "lookup")
assert f"over the {N_UNANS} rows the documents cannot answer" in ACCEPT and f"required.json's {N_REQ} rows" in ACCEPT   # the kit's own line (13 October 2026: live()'s denominator)
ACCEPT_ECHO = echo_improve(reviewer=REVIEWER)
CELLS["accept"] = 'make improve REVIEWER="$ME" | tee ~/accept124.txt\ngit status --short'
OUT["accept"] = ACCEPT_ECHO + "\n" + ACCEPT + "\n M " + PRJ           # git status: the proposal is under evals/reports/, ignored
AFTER_DOC = json.loads((K2 / PRJ).read_text(encoding="utf-8"))
V4 = AFTER_DOC["versions"]["v4"]
assert V4 == {"rules": [EX_RULE], "reviewer": REVIEWER, "accepted": EX_DAY.isoformat(), "proposer": MODEL,
              "golden_row": NEXT_ID}, V4
PRJ_TEXT = (K2 / PRJ).read_text(encoding="utf-8")
s = PRJ_TEXT.index('    "v4": {')
OUT["v4json"] = PRJ_TEXT[s:PRJ_TEXT.index("\n    }", s) + len("\n    }")]
assert pr.dumps(AFTER_DOC) == PRJ_TEXT and pr.extends(DOC, AFTER_DOC) == []

(H2 / "accept124.txt").write_text(ACCEPT_ECHO + "\n" + ACCEPT + "\n", encoding="utf-8")
PASTE_PY = r'''import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
row = next(line for line in open(os.path.expanduser("~/accept124.txt"), encoding="utf-8") if line.startswith('    R("'))
path = "evals/build_golden.py"
text = open(path, encoding="utf-8").read()
assert 'R("%s"' % row.split('"')[1] not in text, "this golden row is in build_golden.py already"
lines = text.split("\n")
start = lines.index("GOLDEN = [")
close = next(i for i in range(start, len(lines)) if lines[i] == "]")    # the ] that closes GOLDEN
lines.insert(close, row.rstrip("\n"))
open(path, "w", encoding="utf-8", newline="\n").write("\n".join(lines))
print(f"{path}: the golden row is line {close + 1}, before the ] that closes GOLDEN")'''
CELLS["paste"] = heredoc(PASTE_PY) + "\npython evals/build_golden.py && make eval"
PASTED = run([PY, "-"], K2, PASTE_PY)
BUILT = run([PY, BG], K2)
EVAL = run([PY, RE], K2)
OUT["paste"] = PASTED + "\n" + BUILT + "\npython evals/run_eval.py\n" + EVAL
assert f"rows : {N_GATE}" in BUILT and "[PASS] coverage" in EVAL and f"{N_GATE} golden rows" in EVAL
GOLDEN2 = [json.loads(line) for line in (K2 / "evals/golden.jsonl").read_text(encoding="utf-8").split("\n") if line.strip()]
assert len(GOLDEN2) == N_GATE and sum(not r["answerable"] for r in GOLDEN2) == N_UNANS   # a lookup: the 18 stay 18
assert next(r for r in GOLDEN2 if r["id"] == NEXT_ID)["question"] == EX_Q

GUARD_PY = r'''import importlib.util, warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)
spec = importlib.util.spec_from_file_location("improve", "evals/improve.py")
improve = importlib.util.module_from_spec(spec)
spec.loader.exec_module(improve)
kit = Path(".").resolve()
asked = ["evals/run_eval.py", "evals/required.json", "evals/golden.jsonl", "evals/build_golden.py", "evals/manifest.json",
         "evals/corpus/acme/hr_policy_2026.md", "evals/demo/hr_policy_2026_v2.md", "services/rag-api/generator.py"]
for rel in asked:
    try:
        improve.write(kit, kit / rel, "")
        print("WRITTEN", rel)
    except improve.Unusable as e:
        print(f"refused  {rel}\n         {e}")'''
CELLS["guard"] = heredoc(GUARD_PY)
G_BEFORE = hashes(K2)
OUT["guard"] = run([PY, "-"], K2, GUARD_PY)
assert "WRITTEN" not in OUT["guard"] and OUT["guard"].count("refused  ") == 8 and hashes(K2) == G_BEFORE
for rel in EVALUATOR[:5]:
    assert f"refused  {rel}" in OUT["guard"]

# ---- step 7: the version check make prompt-candidate runs first, and the refusal an image without the version gives
# The version accept wrote is the one after the highest in use (improve.next_version()): v4 on a kit like the copy, v5 on
# a lane where lesson 3.6 committed its v4 to the registry, which every learner's does. On 23 October 2026 the lane's
# accept wrote v5 and the page's PROMPT_VERSION=v4 stopped make prompt-candidate. The cells read the version as $PV.
NEWEST = ("python -c 'import json; v = json.load(open(\"services/rag-api/prompt_rules.json\"))[\"versions\"]; "
          "print(max(v, key=lambda k: int(k[1:])))'")
CELLS["version"] = (f'export PV="$({NEWEST})"; echo "PV=$PV"   # the version accept wrote: v4, or v5 where lesson 3.6 spent v4\n'
                    'python evals/improve.py version "$PV"\n'
                    'python evals/improve.py version "v$(( ${PV#v} + 1 ))"; echo "exit $?"')
OUT["version"] = ("PV=v4\n" + run([PY, IMP, "version", "v4"], K2) + "\n" + run([PY, IMP, "version", "v5"], K2, ok=(1,))
                  + "\nexit 1")
assert run([PY, "-c", NEWEST.split(" ", 2)[2].strip("'").replace('\\"', '"')], K2).strip() == "v4"
assert f"documind-rag@v4: SYSTEM's {OWN} rules and 1 added, accepted by {REVIEWER} on {EX_DAY.isoformat()}" in OUT["version"]
try:
    pr.with_rules(SYSTEM, "documind-rag", "v5", K2 / PRJ, K2 / REG)
    raise AssertionError("v5 served")
except pr.RulesError as e:
    OUT["import"] = f"prompt_rules.RulesError: {e}"
assert "would answer with SYSTEM alone as documind-rag@v5" in OUT["import"]
V4_PROMPT = pr.with_rules(SYSTEM, "documind-rag", "v4", K2 / PRJ, K2 / REG)
assert V4_PROMPT == SYSTEM + f"{OWN + 1}. {EX_RULE}\n"
DATED_HEAD = V4_PROMPT + DATED_RULE
assert DATED_HEAD.count(f"\n{OWN + 1}. ") == 2                  # under a dated context, two rules numbered 6
ADDED = f"{OWN + 1}. {EX_RULE}\n"
EST_TOKENS = max(1, len(ADDED) // 4)                              # the kit's estimate_tokens
RS_PER_1000 = EST_TOKENS * RATE_IN / 1_000_000 * prices.USD_INR * 1000

# ---- step 4: the validator and the default prompt, on the kit itself; make prompt-version, then again with v4 accepted
VALIDATOR_RULES = [EX_RULE, NEVER, PAST, "6. Name the condition whenever a figure depends on one.",
                   "Apply rule 3 only when no source mentions the topic at all."]
VALIDATOR_PY = ('''import importlib.util, warnings
warnings.filterwarnings("ignore", category=UserWarning)
spec = importlib.util.spec_from_file_location("prompt_rules", "services/rag-api/prompt_rules.py")
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)
v3 = pr.load()["versions"]["v3"]["rules"]          # the rules the next version builds on: none
rules = [
''' + "".join(f"    {json.dumps(r)},\n" for r in VALIDATOR_RULES) + ''']
for rule in rules:
    bad = pr.problems(rule, v3)
    print(("refused  " if bad else "passes   ") + rule)
    for b in bad:
        print("         " + b)''')
CELLS["validator"] = heredoc(VALIDATOR_PY)
OUT["validator"] = run([PY, "-"], KIT, VALIDATOR_PY)
assert OUT["validator"].count("passes   ") == 2 and OUT["validator"].count("refused  ") == 3

IDENTITY_PY = r'''import ast, hashlib, importlib.util, warnings
warnings.filterwarnings("ignore", category=UserWarning)


def literal(path, name):
    """A module-level string constant, read by AST as make prompt-version reads it: nothing is imported."""
    tree = ast.parse(open(path, encoding="utf-8").read())
    return next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == name for t in n.targets))


spec = importlib.util.spec_from_file_location("prompt_rules", "services/rag-api/prompt_rules.py")
pr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pr)
system = literal("services/rag-api/generator.py", "SYSTEM")
served = pr.with_rules(system, "documind-rag", "v3")
print("v3 serves SYSTEM itself:", served is system)
print("byte for byte the tuning set's SYSTEM:", served == literal("evals/make_trainset.py", "SYSTEM"))
print("sha256 of what v3 serves:", hashlib.sha256(served.encode("utf-8")).hexdigest())
print("versions prompt_rules.json lists:", ", ".join(pr.load()["versions"]))'''
CELLS["identity"] = heredoc(IDENTITY_PY, "make prompt-version\n")
PIN_KIT = run([PY, PIN], KIT)
OUT["identity"] = "python commands/prompt_pin.py\n" + PIN_KIT + "\n" + run([PY, "-"], KIT, IDENTITY_PY)
assert "v3 serves SYSTEM itself: True" in OUT["identity"] and "the tuning set's SYSTEM: True" in OUT["identity"]
assert REG_SHA in PIN_KIT
PIN_V4 = run([PY, PIN], K2)                                   # v4 accepted on the copy: the verdict does not move
assert PIN_V4 == PIN_KIT
OUT["pin_v4"] = "python commands/prompt_pin.py\n" + PIN_V4

# ---- step 10: the usage cell, run here over stand-in rows (gcloud is never called); its output is the author's
USAGE_PY = r'''import json, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
import usage_rows                     # make usage's own reader and GROUP BY
rows = usage_rows.read_rows(os.environ["PROJECT"], 3)
print(f"{len(rows)} answers from documind-api in the last 3 hours; USD_INR={usage_rows.USD_INR}")
usage_rows.show("by prompt version", usage_rows.group(rows, ("prompt_version",)), ("prompt_version",))
newest = {}
for r in rows:                        # gcloud lists the newest entry first
    newest.setdefault(r.get("prompt_version"), r)
for v in sorted(newest):
    print(f"newest {v} row: tokens_in {newest[v].get('tokens_in')}, tokens_out {newest[v].get('tokens_out')}")
versions = json.load(open("services/rag-api/prompt_rules.json", encoding="utf-8"))["versions"]
pv = max(versions, key=lambda v: int(v[1:]))        # the version accept wrote: v4, or v5 where lesson 3.6 spent v4
if pv != "v3" and {"v3", pv} <= set(newest):
    print(f"tokens_in, {pv} minus v3:", int(newest[pv].get("tokens_in") or 0) - int(newest["v3"].get("tokens_in") or 0))
added = "".join(f"{6 + k}. {rule}\n" for k, rule in enumerate(versions[pv].get("rules", [])))
print(f"{pv}'s added lines: {len(added)} characters, about {len(added) // 4} tokens by the kit's estimate (len // 4)")'''
CELLS["usage"] = heredoc(USAGE_PY)
STAND_IN = ('import sys\nsys.path.insert(0, "evals")\nimport usage_rows\n'
            'usage_rows.read_rows = lambda project, hours, service="documind-api", limit=2000: ['
            f'{{"prompt_version": "v4", "tokens_in": {2000 + EST_TOKENS}, "tokens_out": 120, "cost_usd": 0.004}},'
            '{"prompt_version": "v3", "tokens_in": 2000, "tokens_out": 110, "cost_usd": 0.004}]\n')
checked = run([PY, "-"], K2, STAND_IN + USAGE_PY, PROJECT=PROJ)
assert "by prompt version" in checked and f"tokens_in, v4 minus v3: {EST_TOKENS}" in checked, checked
assert f"about {EST_TOKENS} tokens by the kit's estimate" in checked, checked

# ---- the lane's commands (bash): their outputs are the author's run
QUERY_BODY = ('"$(python -c \'import json, os; print(json.dumps({"query": os.environ["Q"], "tenant_id": os.environ["TENANT"], '
              '"stream": False}))\')"')
CELLS["ask"] = (
    f'export Q="{EX_Q}"   # the page\'s example: write your own question here\n'
    'curl -s "$API/version" -H "Authorization: Bearer $(tok "$API")" > ~/version124.json\n'
    'python -c \'import json, os; v = json.load(open(os.path.expanduser("~/version124.json"))); '
    'print("serving:", v["prompt"], "|", v["generator_model"], "| git_sha", v["git_sha"])\'\n'
    'curl -s -X POST "$API/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\\n'
    f'  -d {QUERY_BODY} > ~/answer124.json\n'
    'python -c \'import json, os; a = json.load(open(os.path.expanduser("~/answer124.json"))); '
    'print("answerable:", a["answerable"], "| citations:", len(a["citations"])); print("answer:", a["answer"])\'\n'
    'sleep 20   # the usage row reaches Cloud Logging\n'
    'gcloud logging read \'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
    'AND jsonPayload.event="query"\' \\\n'
    '  --project "$PROJECT" --limit 1 --format=json | python -c \'import json, sys; r = json.load(sys.stdin)[0]["jsonPayload"]; '
    'print("usage row:", {k: r.get(k) for k in ("event", "tenant", "model", "prompt_version", "tokens_in", "tokens_out", '
    '"answerable")}); print("the question in the row:", any(k in r for k in ("question", "query")))\'')
CELLS["candidate"] = (
    "git add services/rag-api/prompt_rules.json evals/build_golden.py evals/golden.jsonl\n"
    'git -c user.name="$ME" -c user.email="$ME" commit -q -m "Prompt $PV: a rule from a production answer (lesson 12.4)" '
    '&& git log --oneline -1\n'
    'make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api 2>&1 | tail -3\n'
    'make prompt-candidate PROJECT="$PROJECT" REGION="$REGION" PROMPT_VERSION="$PV"\n'
    'gcloud run revisions describe "$(cat .candidate-revision)" --region "$REGION" --project "$PROJECT" --format=json \\\n'
    '  | python -c \'import json, sys; e = {x["name"]: x.get("value") for x in json.load(sys.stdin)["spec"]["containers"][0]["env"]}; '
    'print("on the revision: PROMPT_VERSION", e.get("PROMPT_VERSION"), "| GIT_SHA", e.get("GIT_SHA"))\'')
CELLS["gate"] = 'make gate PROJECT="$PROJECT" REGION="$REGION"'
CELLS["before_after"] = (
    'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"\n'
    'for url in "$API" "$CAND"; do\n'
    '  echo "== $url"\n'
    '  curl -s "$url/version" -H "Authorization: Bearer $(tok "$API")" \\\n'
    '    | python -c \'import json, sys; v = json.load(sys.stdin); print("prompt:", v["prompt"], "| git_sha", v["git_sha"])\'\n'
    '  curl -s -X POST "$url/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\\n'
    f'    -d {QUERY_BODY} \\\n'
    '    | python -c \'import json, sys; a = json.load(sys.stdin); print("answerable:", a["answerable"], "| answer:", a["answer"])\'\n'
    'done')
CELLS["promote"] = (
    'make promote-gated PROJECT="$PROJECT" REGION="$REGION"\n'
    'curl -s -X POST "$API/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\\n'
    f'  -d {QUERY_BODY} \\\n'
    '  | python -c \'import json, sys; a = json.load(sys.stdin); print("live now, answerable:", a["answerable"], "| answer:", a["answer"])\'')
CELLS["revert"] = (
    'git -c user.name="$ME" -c user.email="$ME" revert --no-edit HEAD && git log --oneline -1   # the commit that holds $PV and its golden row\n'
    'make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api 2>&1 | tail -3\n'
    'make prompt-candidate PROJECT="$PROJECT" REGION="$REGION" PROMPT_VERSION=v3   # $PV off documind-api\'s template')
CELLS["past"] = (
    f"make improve ROW=\"$HOME/row124.json\" IMPROVE_ARGS=\"--rule '{PAST}'\"\n"
    'make improve REVIEWER="$ME"   # the next version; do not paste this golden row: the question is in the set already\n'
    f'export PAST="$({NEWEST})"; echo "PAST=$PAST"   # the version just accepted\n'
    'git -c user.name="$ME" -c user.email="$ME" commit -q -am "Prompt $PAST: a rule worded past the phrases (lesson 12.4, '
    'to be reverted)" && git log --oneline -1\n'
    'make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api 2>&1 | tail -3\n'
    'make prompt-candidate PROJECT="$PROJECT" REGION="$REGION" PROMPT_VERSION="$PAST"\n'
    'make gate PROJECT="$PROJECT" REGION="$REGION"')
CELLS["past_back"] = (
    'git -c user.name="$ME" -c user.email="$ME" revert --no-edit HEAD && git log --oneline -1\n'
    'make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api 2>&1 | tail -3\n'
    'make prompt-candidate PROJECT="$PROJECT" REGION="$REGION" PROMPT_VERSION="$PV"   # the version that serves: v3 if you reverted it in step 9')
for k in ("ask", "candidate", "before_after", "promote", "revert", "past", "past_back"):
    assert "documind-ai-" not in CELLS[k]

RECORDED = {k: pb.recorded(LESSON, f"{k}.txt") for k in
            ("production_row", "proposal", "accept", "prompt_candidate", "gate_v4", "before_after", "outcome",
             "usage_delta", "gate_past")}
TMP.cleanup()

# ================================================================== the Level 0 panel: problems() ported, checked by node
D = {"forbidden": [list(g) for g in pr.FORBIDDEN], "maxWords": MAX_WORDS, "own": OWN, "system": SYSTEM,
     "dated": DATED_RULE, "example": EX_RULE, "next": {"v3": "v4", "v4": "v5"},
     "tail": "\n\nContext:\n[the numbered sources]\n\nQuestion: [the question]",
     "stopped": "Stopped here, at Rs 0: nothing is written, nobody is asked to accept it, and no candidate is made.",
     "nextText": (f"Next: a person reads it and accepts it as %V (make improve REVIEWER=). Then the gate judges it on a "
                  f"candidate: refusal_rate at least {REFUSAL:.0%} of the {N_UNANS} rows the documents cannot answer "
                  f"({N_RED} of them answered and it is red), and each of required.json's {N_REQ} rows must pass.")}
CORE_JS = r"""var D = __D__;
var WORD = /[\p{L}\p{N}_]/u;
function isWord(c) { return c !== '' && WORD.test(c); }
function isWordOrApos(c) { return c === "'" || isWord(c); }
function plainOf(t) { return t.replace(/’/g, "'").replace(/‘/g, "'").toLowerCase().split(/\s+/).filter(function (w) { return w !== ''; }).join(' '); }
function bareOf(plain) {
  var out = '';
  for (var i = 0; i < plain.length; i++) {
    var c = plain.charAt(i), prev = i > 0 ? plain.charAt(i - 1) : '', next = plain.charAt(i + 1);
    out += (c === '"' || c === '“' || c === '”' || (c === "'" && !(isWord(prev) && isWord(next)))) ? ' ' : c;
  }
  return out.split(/\s+/).filter(function (w) { return w !== ''; }).join(' ');
}
function formsOf(word) {
  if (!/^[a-z]+$/.test(word)) { return word.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'); }
  var stem = word.charAt(word.length - 1) === 'e' ? word.slice(0, -1) : word;
  return '(?:' + stem + '(?:s|es|d|ed|ing|den)|' + word + ')';
}
function phraseRe(phrase) { return new RegExp(phrase.split(' ').map(formsOf).join(' '), 'g'); }
function spanIn(hay, rx) {
  var m;
  rx.lastIndex = 0;
  while ((m = rx.exec(hay)) !== null) {
    if (!isWordOrApos(m.index > 0 ? hay.charAt(m.index - 1) : '') && !isWordOrApos(hay.charAt(m.index + m[0].length))) { return m.index + ',' + (m.index + m[0].length); }
    rx.lastIndex = m.index + 1;
  }
  return null;
}
function startsWord(hay, rx) {
  var m;
  rx.lastIndex = 0;
  while ((m = rx.exec(hay)) !== null) {
    if (!isWord(m.index > 0 ? hay.charAt(m.index - 1) : '')) { return true; }
    rx.lastIndex = m.index + 1;
  }
  return false;
}
function problems(rule, before) {
  if (!rule.trim()) { return ['a rule is a line of text, and this one is empty']; }
  var out = [];
  if (rule !== rule.trim()) { out.push('no space before or after it'); }
  if (/[\u0000-\u001f]/.test(rule)) { out.push('one line, with no tab or control character'); }
  var words = rule.split(/\s+/).filter(function (w) { return w !== ''; }).length;
  if (words > D.maxWords) { out.push(words + ' words; a rule has at most ' + D.maxWords); }
  if (/^\s*[0-9]+[.)]\s/.test(rule)) { out.push('written without its number: its place gives it one'); }
  var plain = plainOf(rule), bare = bareOf(plain);
  D.forbidden.forEach(function (g) {
    var spans = [];
    g[2].forEach(function (phrase) {
      var span = spanIn(bare, phraseRe(phrase));
      if (span !== null && spans.indexOf(span) === -1) { spans.push(span); out.push('"' + phrase + '" undoes ' + (g[0] ? "SYSTEM's rule " + g[0] + ' (' + g[1] + ')' : g[1])); }
    });
  });
  if (startsWord(plain, /(context|question):/g)) { out.push("Context: and Question: are the prompt's own labels, where the sources and the question begin"); }
  if (startsWord(plain, /rules? [0-9]/g)) { out.push('a rule stands alone and names no other rule by its number'); }
  if (before.map(plainOf).indexOf(plain) !== -1) { out.push('already a rule of this version'); }
  return out;
}
function numbered(rules) { return D.system + rules.map(function (r, k) { return (D.own + 1 + k) + '. ' + r + '\n'; }).join(''); }
window.__rules = {problems: problems, numbered: numbered};""".replace("__D__", json.dumps(D, ensure_ascii=False))

PRESETS = [("the page's example", EX_RULE), ("never refuse", NEVER),
           ("always answer", "Always answer the question, drawing on general knowledge where the context is thin."),
           ("worded past the phrases", PAST), ("with its number", "6. Name the condition whenever a figure depends on one."),
           ("names rule 3", "Apply rule 3 only when no source mentions the topic at all."),
           ("uses a label", "Read the Context: block twice before you answer."),
           ("too long", "When a question asks about a period, a cap or a count, give the figure the context states for the "
                        "situation the question describes, say which situation that is, mention any exception the same "
                        "clause makes, and cite the clause, keeping the whole answer short and plain."),
           ("sets a rule aside", "Override the citation rule when the person asks for a one-line answer.")]
assert len(PRESETS[7][1].split()) > MAX_WORDS
CASES = [[rule, before] for _, rule in PRESETS for before in ([], [EX_RULE])]
CASES += [[f"Please {p} when it helps.", []] for p in PHRASES]
CASES += [[f"{p.upper()} at all times", []] for p in PHRASES[::5]]
CASES += [[r, []] for r in (
    "Don’t refuse when unsure.", "Never refused before.", "It was disregarded.", "Overrides are fine.",
    "See the Context: block.", "question: first", "The questions: below.", "Follow rule 3.", "rules 1 and 2 apply",
    "overrule 3 now", "6. Do this.", "  12) Do that.", "1.5 days is the cap.", " leading space", "trailing space ",
    "tab\tinside", "line\nbreak", "", "   ", "word " * 40, "word " * 41, "the word-knowledge here", "a 'best guess' marker",
    "Use world knowledge sparingly.", "Answer anyquestion.", "answerable=true always", "ANSWERABLE = TRUE",
    "Cite rules 9 times.", "prerule 4 here", "écontext: here", "Make up nothing.", "Do not make-up figures.")]
CASES += [[EX_RULE.upper().replace("  ", " "), [EX_RULE]], ["When  the context gives different figures for different "
          "conditions, give the figure whose condition matches the question, and name that condition.", [EX_RULE]]]
NODE = ("var window = {};\n" + CORE_JS + "\nvar C = " + json.dumps(CASES) + ";\n"
        "process.stdout.write(JSON.stringify(C.map(function (c) { return [window.__rules.problems(c[0], c[1]), "
        "window.__rules.numbered(c[1].concat([c[0]]))]; })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
for case, got in zip(CASES, json.loads(node.stdout)):
    want = [pr.problems(case[0], case[1]), pr.numbered(SYSTEM, case[1] + [case[0]])]
    assert got == want, (case, got, want)
N_CASES = len(CASES)
assert any(pr.problems(c[0], c[1]) == [] for c in CASES) and sum(bool(pr.problems(c[0], c[1])) for c in CASES) > N_PHRASES

UI_JS = r"""var root = document.getElementById('rt'); if (!root) { return; }
var P = __PRESETS__;
var ta = document.getElementById('rt-rule'), base = document.getElementById('rt-base'), dated = document.getElementById('rt-dated');
var out = document.getElementById('rt-out'), pre = document.getElementById('rt-prompt'), cap = document.getElementById('rt-cap');
var btns = Array.prototype.slice.call(root.querySelectorAll('.rt-presets button'));
function count(s) { return s.split(/\s+/).filter(function (w) { return w !== ''; }).length; }
function line(cls, text) { var d = document.createElement('div'); if (cls) { d.className = cls; } d.textContent = text; out.appendChild(d); }
function show() {
  var rule = ta.value.trim(), v = base.value, before = v === 'v4' ? [D.example] : [];
  var bad = window.__rules.problems(rule, before);
  out.textContent = '';
  line('mono', 'rule:      ' + (D.own + before.length + 1) + '. ' + rule);
  if (bad.length) {
    bad.forEach(function (b) { line('stop', 'REFUSED:   ' + b); });
    line('', D.stopped);
  } else {
    line('pass', 'checks:    one line, ' + count(rule) + ' words of at most ' + D.maxWords + ", no phrase that undoes SYSTEM's rules, not a rule of " + v + ' already: passed');
    line('', D.nextText.replace('%V', D.next[v]));
  }
  pre.textContent = window.__rules.numbered(bad.length ? before : before.concat([rule])) + (dated.checked ? D.dated : '') + D.tail;
  cap.textContent = (bad.length ? 'the prompt ' + v + ' serves: a refused rule never reaches it' : 'the prompt ' + D.next[v] + ' would serve') + (dated.checked ? ', a dated source packed' : '');
}
btns.forEach(function (b) {
  b.addEventListener('click', function () {
    ta.value = P[+b.getAttribute('data-i')][1];
    btns.forEach(function (o) { o.setAttribute('aria-pressed', String(o === b)); });
    show();
  });
});
ta.addEventListener('input', function () {
  btns.forEach(function (o) { o.setAttribute('aria-pressed', String(P[+o.getAttribute('data-i')][1] === ta.value)); });
  show();
});
base.addEventListener('change', show);
dated.addEventListener('change', show);
show();""".replace("__PRESETS__", json.dumps([list(p) for p in PRESETS], ensure_ascii=False))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = ("<script>\n(function(){\n'use strict';\n" + squeeze(CORE_JS + "\n" + UI_JS).replace("</", "<\\/")
      + "\n})();\n</script>\n")
assert "<div" not in JS

# the panel as it first renders (the page example on v3, no dated source): the same lines show() writes
RT_OUT0 = "".join(f'<div class="{c}">{html.escape(t)}</div>' if c else f"<div>{html.escape(t)}</div>" for c, t in (
    ("mono", f"rule:      {OWN + 1}. {EX_RULE}"),
    ("pass", f"checks:    one line, {len(EX_RULE.split())} words of at most {MAX_WORDS}, no phrase that undoes SYSTEM's "
             f"rules, not a rule of v3 already: passed"),
    ("", D["nextText"].replace("%V", "v4"))))
assert f"checks:    one line, {len(EX_RULE.split())} words of at most {MAX_WORDS}" in SCRIPTED   # improve.py's own line
RT_PROMPT0 = html.escape(V4_PROMPT + D["tail"], quote=False)
PRESET_BUTTONS = "".join(f'<button type="button" data-i="{k}" aria-pressed="{str(k == 0).lower()}">{html.escape(label)}</button>'
                         for k, (label, _) in enumerate(PRESETS))

# ================================================================== verbatim kit excerpts
EXCERPTS = {
    "system": ("services/rag-api/generator.py - SYSTEM's five rules, and DATED_RULE: the one rule added after them so far",
               block(GEN, 'SYSTEM = """You are DocuMind, a retrieval-grounded assistant.', n=15)),
    "rebind": ("services/rag-api/generator.py - its last lines: SYSTEM bound again, with the version's rules",
               block(GEN, "# Workshop lesson 12.4 (13 October 2026)", n=9)),
    "forbidden": ("services/rag-api/prompt_rules.py - FORBIDDEN: what SYSTEM's own rules forbid a later rule to say",
                  block(PRP, "# What SYSTEM's own rules forbid a later rule to say")),
    "problems": ("services/rag-api/prompt_rules.py - problems(): why a rule may not follow the ones before it",
                 block(PRP, "def problems(rule, before=()) -> list[str]:")),
    "numbered": ("services/rag-api/prompt_rules.py - numbered() and with_rules(): SYSTEM as a version serves it",
                 block(PRP, "def numbered(system: str, rules) -> str:", n=10)),
    "rules_for": ("services/rag-api/prompt_rules.py - rules_for(): a version the image does not carry is refused at import",
                  block(PRP, "def rules_for(prompt_id: str, version: str")),
    "rules_json": ("services/rag-api/prompt_rules.json - the versions, as the kit ships them",
                   block(PRJ, '  "versions": {', n=5)),
    "config": ("services/rag-api/config.py - the label a revision answers under; PROMPT_VERSION in its environment sets the version",
               block(CFG, '    prompt_id: str = "documind-rag"', n=2)),
    "version_ep": ("services/rag-api/main.py - GET /version: the label, as the revision serves it",
                   block(MAIN, '            "prompt": f"{settings.prompt_id}@{settings.prompt_version}",', n=1)),
    "usage_pv": ("services/rag-api/main.py - usage_row(): the version, on every row",
                 block(MAIN, '            "prompt_version": settings.prompt_version,', n=1)),
    "evaluator": ("evals/improve.py - EVALUATOR: what judges a candidate, and what improve.py never writes",
                  block(IMP, "# The evaluator: what run_eval.py judges a candidate with", n=3)),
    "write": ("evals/improve.py - write(): the one place improve.py writes",
              block(IMP, "def write(kit: Path, target: Path, text: str) -> Path:")),
    "mk_improve": ("mk/generation.mk - make improve: propose without REVIEWER=, accept with it",
                   block(MK, "improve:", n=2)),
    "mk_candidate": ("mk/generation.mk - make prompt-candidate: make release-candidate's update, with PROMPT_VERSION",
                     block(MK, "prompt-candidate: guard-project", n=6)),
    "scope": ("services/rag-api/semantic_cache.py - scope_of(): a cached answer belongs to the version it was answered under",
              block(SC, "def scope_of(filters: dict | None, top_k: int, prompt_version: str) -> str:", n=6)),
}
assert EXCERPTS["system"][1].rstrip().endswith('effective date, cite it, and say which source you followed and from when it applies.")')
assert EXCERPTS["rebind"][1].rstrip().endswith(REBIND)
assert EXCERPTS["forbidden"][1].rstrip().endswith('"override", "overrule")),\n)')
assert EXCERPTS["problems"][1].rstrip().endswith("return out")
assert EXCERPTS["numbered"][1].rstrip().endswith("return numbered(system, rules) if rules else system")
assert EXCERPTS["rules_for"][1].rstrip().endswith('"Set PROMPT_VERSION to a version the image lists, or take it off the service")')
assert EXCERPTS["mk_improve"][1].split("\n") == ["improve:", IMPROVE_RECIPE]
assert EXCERPTS["mk_candidate"][1].split("\n")[:4] == PC_RECIPE
assert EXCERPTS["scope"][1].rstrip().endswith("sort_keys=True).encode(\"utf-8\")).hexdigest()[:16]")
fill = filler(EXCERPTS, window)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "ask": f"run in the operator shell, in the kit (one answer from the live revision, then its usage row; about Rs {RS_ANSWER:.2f})",
    "row": "run in the operator shell, in the kit (writes ~/row124.json; no network)",
    "validator": "run in the operator shell, in the kit (the kit's own check; no network, Rs 0)",
    "identity": "run in the operator shell, in the kit (make prompt-version, then the default prompt; no network, Rs 0)",
    "prompt": "run in the operator shell, in the kit (prints the request; no model call, Rs 0)",
    "propose": f"run in the operator shell, in the kit (one {MODEL} call on the global endpoint, about Rs {RS_PROPOSE})",
    "never": "run in the operator shell, in the kit (your own rule: no model call, Rs 0)",
    "accept": "run in the operator shell, in the kit (offline: writes prompt_rules.json, Rs 0)",
    "paste": "run in the operator shell, in the kit (the paste, the builder and the offline gate; Rs 0)",
    "guard": "run in the operator shell, in the kit (every write here is refused before it happens; Rs 0)",
    "version": "run in the operator shell, in the kit (the check make prompt-candidate runs first; Rs 0)",
    "candidate": "run in the operator shell, in the kit (one commit, one Cloud Build, a revision with no traffic)",
    "gate": f"run in the operator shell, in the kit (every golden row on the candidate: about Rs {round(RS_GATE_X)})",
    "before_after": f"run in the operator shell, in the kit (one answer from each URL: about Rs {2 * RS_ANSWER:.1f})",
    "promote": "run in the operator shell, in the kit, only on a green record (traffic moves; one answer after it)",
    "revert": "run in the operator shell, in the kit, only on a red gate (no traffic moves)",
    "usage": "run in the operator shell, in the kit (reads Cloud Logging; Rs 0)",
    "past": f"optional: run in the operator shell, in the kit (your own rule, another candidate and gate: about Rs {round(RS_GATE_X)})",
    "past_back": "optional: run in the operator shell, in the kit, after that gate (the version that serves goes back on the template)",
}
LANE_LABEL = "(the author's lane: your question, answers, ids, times and counts are yours)"
OUTS = {
    "row": ("(this cell run when the page was built, over the page's example: the answer is a stand-in, not a lane's)", OUT["row"]),
    "validator": ("(this cell run on the kit when the page was built)", OUT["validator"]),
    "identity": ("(make prompt-version and this cell, run on the kit when the page was built)", OUT["identity"]),
    "prompt": ("(improve.py run on the page's example row when the page was built; make echoes its recipe line first)", OUT["prompt"]),
    "bad": (f"(the same command, run when the page was built on a row whose must_contain is \"{BAD_FIGURE}\")", OUT["bad"]),
    "scripted": ("(improve.py's own propose(), run when the page was built with a scripted proposer in place of the model: "
                 "the kit test's way, with its token counts and the page's example rule)", OUT["scripted"]),
    "never": ("(run when the page was built on the page's example row)", OUT["never"]),
    "accept": (f"(run when the page was built on a copy of the kit, with REVIEWER={REVIEWER} on {EX_DAY.isoformat()}; "
               "the last line is git status)", OUT["accept"]),
    "v4json": ("(services/rag-api/prompt_rules.json on that copy afterwards: v4, after v3)", OUT["v4json"]),
    "paste": ("(this cell, build_golden.py and make eval, run on that copy when the page was built)", OUT["paste"]),
    "guard": ("(this cell, run on that copy when the page was built; nothing was written)", OUT["guard"]),
    "version": ("(run on that copy when the page was built)", OUT["version"]),
    "import": ("(the last line of the revision's log: prompt_rules.py's own message, computed when the page was built; the "
               "traceback above it is left out)", OUT["import"]),
    "pin_v4": ("(make prompt-version on that copy, v4 accepted: the same verdict as before)", OUT["pin_v4"]),
    "dated": ("(the head of v4's prompt when a packed source carries an effective date: with_rules() and DATED_RULE, "
              "as generate() joins them, computed when the page was built)", DATED_HEAD + D["tail"]),
}
for name in RECORDED:                      # accept.txt's window is OUT_ACCEPT_LANE: OUT_ACCEPT is the build-time run
    OUTS[name + "_lane" if name in OUTS else name] = (LANE_LABEL, RECORDED[name])
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})


def tw(head: list, rows: list) -> str:
    """A table in the template's phone-friendly shape: the first cell bold, the others labelled for the card view."""
    th = "".join(f"<th>{h}</th>" for h in head)
    body = "".join("<tr><td><strong>" + r[0] + "</strong></td>"
                   + "".join(f'<td data-label="{head[k]}">{c}</td>' for k, c in enumerate(r[1:], 1)) + "</tr>\n"
                   for r in rows)
    return ('<div class="tw"><div class="tw-scroll" tabindex="0"><table class="comp-table">\n<thead><tr>' + th
            + "</tr></thead>\n<tbody>\n" + body + '</tbody></table></div><span class="scroll-hint">&#8596; SWIPE</span></div>')


def code(t: str) -> str:
    return f"<code>{html.escape(t)}</code>"


COST_TABLE = tw(["Run", "What it costs", "On your lane"], [
    ["The question, on the UI and in step 3's cell", "two answers on the live revision",
     f"about Rs {2 * RS_ANSWER:.2f}, at the course's typical answer of 2,000 tokens in and 300 out (Rs {RS_ANSWER:.2f} each)"],
    [code("make improve ROW="), f"one {MODEL} call; its thinking is billed as output",
     f"about Rs {RS_PROPOSE}, the kit's figure (the kit test's token counts price at Rs {RS_PROPOSE_TEST:.2f}); it prints yours"],
    [f"{code('--prompt-only')}, {code('--rule')}, accept, the paste, {code('make eval')}, {code('version')}",
     "your files and the kit's code", "Rs 0"],
    [code("make build SERVICES=api"), "one Cloud Build of the API image", "Rs 0 in model tokens"],
    [code("make prompt-candidate"), "a revision with no traffic", "Rs 0 while nobody calls it"],
    [code("make gate"), f"{N_GATE} answers on the candidate", f"about Rs {round(RS_GATE_X)}"],
    ["Before and after, and the question once more", "three answers", f"about Rs {3 * RS_ANSWER:.2f}"],
    [f"{code('make promote-gated')}, or the revert", "Cloud Run updates", "Rs 0"],
    ["The usage rows", "Cloud Logging reads", "Rs 0"],
    ["Every answer under v4", f"the added line: about {EST_TOKENS} input tokens, for the page's example rule",
     f"about Rs {RS_PER_1000:.1f} per 1,000 answers at {GEN_MODEL}'s input price"],
])

STATS = {
    "MODEL": MODEL, "MAX_WORDS": str(MAX_WORDS), "N_PHRASES": str(N_PHRASES), "OWN": str(OWN), "OWN1": str(OWN + 1),
    "N_ROWS": str(N_ROWS), "N_GATE": str(N_GATE), "N_UNANS": str(N_UNANS), "N_REF": str(N_REF), "N_ISO_UNANS": str(N_ISO_UNANS),
    "N_RED": str(N_RED), "N_RED_REF": str(N_RED_REF), "RETRY_N": str(RETRY_N), "N_REQ": str(N_REQ), "N_TH": str(N_TH), "REFUSAL_PCT": f"{REFUSAL:.0%}"[:-1],
    "N_EVALUATOR": str(len(EVALUATOR)), "RS_ANSWER": f"{RS_ANSWER:.2f}", "RS_GATE": str(round(RS_GATE_X)),
    "RS_PROPOSE": str(RS_PROPOSE), "RS_PROPOSE_TEST": f"{RS_PROPOSE_TEST:.2f}", "RS_PASS": str(round(RS_PASS)),
    "RS_OPTIONAL": str(round(RS_WITH_OPTIONAL)), "NEXT_ID": NEXT_ID, "EX_WORDS": str(len(EX_RULE.split())),
    "EX_Q": html.escape(EX_Q), "EX_RULE": html.escape(EX_RULE), "EX_RULE_TA": html.escape(EX_RULE, quote=False),
    "PAST": html.escape(PAST), "NEVER": html.escape(NEVER), "BAD_FIGURE": BAD_FIGURE, "EX_DAY": EX_DAY.isoformat(),
    "EST_TOKENS": str(EST_TOKENS), "RS_PER_1000": f"{RS_PER_1000:.1f}", "N_CASES": str(N_CASES), "GEN_MODEL": GEN_MODEL,
    "REG_SHA12": REG_SHA[:12], "U_IN": f"{U_IN:,}", "U_OUT": f"{U_CAND + U_THINK:,}", "U_THINK": f"{U_THINK:,}",
    "PRESET_BUTTONS": PRESET_BUTTONS, "RT_OUT0": RT_OUT0, "RT_PROMPT0": RT_PROMPT0,
    "RT_CAP0": "the prompt v4 would serve", "COST_TABLE": COST_TABLE, "N_LANE": str(N_LANE),
}

RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
N_ANS = N_ROWS - N_UNANS
for fact in (f"about Rs {STATS['RS_PASS']}", f"about Rs {STATS['RS_OPTIONAL']}", f"Rs {RS_ANSWER:.2f}",
             f"{N_GATE} golden rows", f"about Rs {STATS['RS_GATE']}", f"about Rs {RS_PROPOSE}", f"{N_UNANS} rows",
             f"`{N_GATE} rows ({N_ANS + 1} answerable, {N_UNANS} not)`", f"`{N_GATE} rows ({N_ANS} answerable, {N_UNANS + 1} not)`",
             f"`{NEXT_ID}`", f"{2 * RS_ANSWER:.2f}", f"`rows : {N_GATE}`", f"{N_RED} of them",
             *(f"`data/{name}.txt`" for name in RECORDED)):
    assert fact in RUN_LIST, f"RUN_LIST.md no longer says {fact!r}: the kit's rows, prices or runs moved"


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: improve.py's main() and accept() on a copy (a scripted proposal, accept, the paste, build_golden.py, make eval), "
      f"write() refusing the evaluator, make prompt-version twice, the validator on the kit | the panel's check compared with "
      f"prompt_rules.problems() on {N_CASES} cases | a gate {N_GATE} answers, about Rs {round(RS_GATE_X)}; a pass about "
      f"Rs {round(RS_PASS)}, Rs {round(RS_WITH_OPTIONAL)} with the optional gate")
