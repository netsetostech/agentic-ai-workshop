"""Build lesson 10.10 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Coding agents under an oracle. commands/ralph.py runs a Ralph loop on one function, statutory_deadline, cut out of a
copy of shared/desk_calc.py: an agent started fresh each iteration on commands/ralph/PROMPT.md, code that undoes or
flags what the agent may not do, and an oracle it cannot see (commands/ralph/oracle.py): weak, desk_calc's own
selftest, or strong, the selftest and ten acceptance checks. commands/review_diff.py is an AI code reviewer scored on
commands/ralph/seeds.json's six planted defects. TASK=statute is paper-to-code: the same function from the statute's
lines alone.

Build-time proof, offline and at Rs 0, on the kit's own code: every version's verdict under both oracles (the widget
and make ralph-check); the hand iteration's workspace and its two checks; the Change it (the sweep deleted, the
placeholder passes); the scripted loop under the strong and the weak oracle, on a rupee cap, on the iteration cap and on
paper-to-code; the guards (each misbehaviour the scripted agent can play, and what the loop did with it); the live
loop's refusals and its dry run, with the egress proxy off and on (RALPH_EGRESS=proxy); the linter in the reviewer's
seat; the human step on the weak run's kit.patch, in a scratch git repository holding the kit's files. The live outputs
(the loop on Gemini CLI, the reviewer on Gemini, the reads of the live run, the proxy's isolation on a live docker) are
pb.recorded() from the author's batch-4 runs, which RUN_LIST.md lists with their rupees.
Run directories, stamps, the kit's path, docker's path and the uid are shown as placeholders, so a build on Windows and
one on Linux print the same page.
"""
import html
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from unittest import mock

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

# The build never starts a live loop: no key, no cap and no switch of the author's shell reaches the kit's code here.
for _k in [k for k in os.environ if k.startswith("RALPH_")] + ["DOCUMIND_PROFILE"]:
    os.environ.pop(_k, None)
sys.path[:0] = [str(KIT / "commands"), str(KIT)]
import ralph  # noqa: E402 - commands/ralph.py: the loop, the oracle's runner, the seeds, the scripted agent
import review_diff as rd  # noqa: E402 - commands/review_diff.py: the reviewer and its linter
from shared import desk_calc, prices  # noqa: E402

LESSON = "10.10"
title = ("<title>Lesson 10.10 Coding agents: a Ralph loop, an AI code reviewer and paper-to-code - an agent that forgets "
         "each iteration, an oracle it cannot see, and a reviewer scored on planted defects | Netsetos</title>\n")
HOME_KIT = "/home/you/deploy_module_rag"            # where the setup section clones the kit
SCOPE, FUNCTION = ralph.SCOPE, ralph.FUNCTION

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:1fr;gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;width:100%;}
@media (min-width:640px){.pc-in.two{grid-template-columns:3fr 2fr;}}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:8px 0 4px;}
.pc-box p{margin:4px 0;}
.rv-chg{font-family:var(--mono);font-size:12px;white-space:pre-wrap;overflow-wrap:anywhere;padding:2px 8px;border-radius:6px;margin:2px 0;}
.rv-chg.del{background:#fee2e2;color:#7f1d1d;}
.rv-chg.add{background:#dcfce7;color:#14532d;}
.rv-verdict{font-family:var(--mono);font-size:13px;padding:4px 10px;border-radius:8px;display:inline-block;margin:4px 0;}
.rv-verdict.pass{background:#ccfbf1;color:#134e4a;}
.rv-verdict.fail{background:#fee2e2;color:#7f1d1d;}
.rv-list{margin:6px 0;padding-left:18px;font-size:12.5px;}
.rv-list li{margin:3px 0;overflow-wrap:anywhere;}
.rv-list li.hit{color:#134e4a;}
.rv-list li.miss{color:#7c2d12;}
.rv-note{font-size:12.5px;color:var(--slate);}
.hops{list-style:none;margin:0;padding:0;counter-reset:hop;}
.hops li{position:relative;padding:6px 8px 6px 34px;border-left:2px solid var(--border);margin-left:10px;font-size:13px;overflow-wrap:anywhere;}
.hops li::before{counter-increment:hop;content:counter(hop);position:absolute;left:-12px;top:6px;width:22px;height:22px;border-radius:50%;background:var(--teal);color:#fff;font-family:var(--mono);font-size:11px;display:flex;align-items:center;justify-content:center;}
.hops li.stop::before{background:#c2410c;}
.hops b{color:var(--navy);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
RP, OP, RD, DC = "commands/ralph.py", "commands/ralph/oracle.py", "commands/review_diff.py", "shared/desk_calc.py"
EXCERPTS = {
    "prompt": ("commands/ralph/PROMPT.md - the prompt every iteration starts from, fresh",
               block("commands/ralph/PROMPT.md", "You are one iteration of a Ralph loop.", n=16)),
    "selftest_case": ("shared/desk_calc.py - the selftest's one statutory_deadline case: the weak oracle",
                      block(DC, '    sd = statutory_deadline("resignation", "2026-10-02")', n=5)),
    "checks": ("commands/ralph/oracle.py - the strong oracle: the selftest, then ten acceptance checks, in order",
               block(OP, "    def checks(self):", end="def judge(")),
    "sweep": ("commands/ralph/oracle.py - the sweep: every day of 2026 for each event, against the oracle's own count",
              block(OP, "    def sweep(self):", end="    def never_a_weekend(self):")),
    "due": ("commands/ralph/oracle.py - due(): the oracle's count, written apart from the code it judges",
            block(OP, "def due(day: date) -> date:", n=8)),
    "fail": ("commands/ralph/oracle.py - a failed check: a detail for people, a feedback line for the agent",
             block(OP, "class Fail(Exception):", n=7)),
    "oracle_md": ("commands/ralph.py - oracle.md: all the next iteration learns of the oracle",
                  block(RP, "def oracle_md(verdict: dict, when: str) -> str:", end="# ------")),
    "no_network": ("commands/ralph/oracle.py - no_network(): installed before the candidate is imported",
                   block(OP, "def no_network() -> None:", end="# ------")),
    "script": ("commands/ralph.py - the scripted agent's two scripts: what OFFLINE=1 plays",
               block(RP, "TASKS = {", n=9)),
    "caps": ("commands/ralph.py - run_loop(): the caps, checked before each iteration but the first",
             block(RP, "        for i in range(1, max_iters + 1):", n=10)),
    "inspect": ("commands/ralph.py - inspect(): what code checks before the oracle sees an iteration",
                block(RP, 'def inspect(run: Run, max_diff_lines: int, agent_log: str = "") -> Inspection:', end="# ------")),
    "never": ("commands/ralph.py - the hosts that serve the kit's public copy, and the git verbs the loop never runs",
              block(RP, "PUBLIC_COPY = (", n=2)),
    "git": ("commands/ralph.py - Run.git(): the run's repository only, your git config ignored",
            block(RP, "    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:", n=10)),
    "statute": ("commands/ralph/statute.md - paper-to-code's spec, to which the loop appends the law",
                block("commands/ralph/statute.md", "# The task: statutory_deadline, from the statute alone", n=21)),
    "law_text": ("commands/ralph.py - law_text(): the corpus lines desk_calc.RULES cites, as the selftest reads them",
                 block(RP, "def law_text() -> str:", end="# ------")),
    "rules": ("shared/desk_calc.py - RULES: the statute's words each calculator's rule quotes",
              block(DC, '    "wages_s17_2": {', n=7)),
    "selftest_rules": ("shared/desk_calc.py - the selftest's first check: every quote is in the corpus lines it cites",
                       block(DC, "    for key, r in RULES.items():", n=3)),
    "rubric": ("commands/review_diff.py - the rubric and the schema: an answer outside them cannot be given",
               block(RD, "RUBRIC = {", end="CONTEXT = {")),
    "review_prompt": ("commands/review_diff.py - the request: the diff, the spec and the definitions, each fenced as data",
                      block(RD, 'PROMPT = """You review a change', end="# ------")),
    "score": ("commands/review_diff.py - score(): found, near the seeded line, and false alarms",
              block(RD, "def score(diffs: list[dict], runs: dict) -> dict:", end="def render(")),
    "lint": ("commands/review_diff.py - the linter that stands in offline: five patterns and a missing note",
             block(RD, "LINT = (", end="def lint(")),
    "agent_line": ("commands/ralph.py - the agent's docker run line: what it mounts, and what it does not",
                   block(RP, "    def env_values(self) -> dict:", end="    def call(self,")),
    "env_file": ("commands/ralph.py - the key's one file: 0600, created fresh, never on a command line",
                 block(RP, "def write_env_file(path: Path, values: dict) -> None:", end="def key_problem(")),
    "call": ("commands/ralph.py - one iteration's call: the env file written, then deleted whatever happens",
             block(RP, "        write_env_file(env_file, self.env_values())", n=12)),
    "key_problem": ("commands/ralph.py - key_problem(): what the loop refuses as RALPH_API_KEY",
                    block(RP, "def key_problem(key: str | None) -> str | None:", end="def parse_cli_json(")),
    "oracle_box": ("commands/ralph.py - the live oracle's docker run line: no network at all, everything read-only",
                   block(RP, "    def command(self, kit_dir: Path) -> tuple[list[str], dict | None]:", n=11)),
    "iteration": ("commands/ralph/iteration.sh - one iteration inside the image: Gemini CLI headless",
                  block("commands/ralph/iteration.sh", "set -eu", n=3)),
    "settings": ("commands/ralph/settings.json - Gemini CLI's system settings, mounted read-only",
                 block("commands/ralph/settings.json", "{", n=8)),
    "dockerfile": ("commands/ralph/Dockerfile - the image: Gemini CLI at the pinned version, no gcloud, a user of its own",
                   block("commands/ralph/Dockerfile", "# No default: an unpinned build", n=10)),
}
assert "self.sweep" in EXCERPTS["checks"][1] and EXCERPTS["checks"][1].count('", True, self.selftest)') == 1
assert "with os.fdopen(fd, \"wb\") as f:" in EXCERPTS["env_file"][1] and "0o600" in EXCERPTS["env_file"][1]
assert "env_file.unlink(missing_ok=True)" in EXCERPTS["call"][1] and "finally:" in EXCERPTS["call"][1]
assert '"--network", "none"' in EXCERPTS["oracle_box"][1] and "readonly" in EXCERPTS["oracle_box"][1]
assert "--yolo" in EXCERPTS["iteration"][1] and '"web_fetch", "google_web_search"' in EXCERPTS["settings"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ where the page's outputs are made
T = Path(tempfile.mkdtemp(prefix="L")).resolve()
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1"}
MK = (KIT / "mk" / "coding.mk").read_text(encoding="utf-8").splitlines()


def recipe_line(target: str, nth: int = 1) -> int:
    """The line of mk/coding.mk holding the nth recipe line of `target`: what make names when that line fails."""
    i = MK.index(next(line for line in MK if line.startswith(f"{target}:")))
    lines = [k for k in range(i + 1, len(MK)) if MK[k].startswith("\t")]
    return lines[nth - 1] + 1


RECIPE = {"ralph": recipe_line("ralph"), "ralph-check": recipe_line("ralph-check"),
          "ralph-workspace": recipe_line("ralph-workspace"), "review-diff": recipe_line("review-diff", 2),
          "review-eval": recipe_line("review-eval")}
assert all(MK[n - 1].startswith("\t@$(PY) commands/") for n in RECIPE.values()), RECIPE
PATHS = re.compile(r"(?:/tmp|" + re.escape(HOME_KIT) + r"|<run>)[^\s'\",)]*")
# Each run's parent: a one-letter directory here (a run directory nests deep, and Windows refuses paths over 260
# characters), shown as the OUT= the page's command gives.
OUTS = {"h": "/tmp/ralph-hand", "s": "/tmp/ralph-strong", "w": "/tmp/ralph-weak", "c": "/tmp/ralph-cap",
        "i": "/tmp/ralph-iters", "p": "/tmp/ralph-statute", "g": "/tmp/ralph-guards"}


def shown(text: str) -> str:
    """A kit output as the learner's shell prints it: each run's parent as the page's OUT=, the kit as the setup
    section's clone, each run's stamp and random suffix as placeholders, and a Windows build's separators as /."""
    for key, fake in OUTS.items():
        text = re.sub(re.escape(str(T / key)) + r"(?![\w.-])", lambda m: fake, text)
    for real, fake in ((str(T), "/tmp"), (str(KIT), HOME_KIT)):
        text = text.replace(real, fake)
    text = PATHS.sub(lambda m: m.group(0).replace("\\", "/"), text)
    text = re.sub(r"ralph-(deadline|statute)-\d{8}-\d{6}-[a-z0-9_]{8}", r"ralph-\1-YYYYMMDD-HHMMSS-XXXXXXXX", text)
    assert "\\" not in text and str(T) not in text, text[:400]
    return text


def run_main(main, argv: list, target: str | None = None) -> tuple[int, str]:
    """A kit command's main() in this process, as `make <target>` runs it (its recipe lines start with @, so make
    echoes nothing): the lines it prints, then make's own line when it exits non-zero."""
    lines = []
    code = main(argv, lines.append)
    text = "\n".join(lines)
    if code and target:
        text += f"\nmake: *** [mk/coding.mk:{RECIPE[target]}: {target}] Error {code}"
    return code, shown(text)


def ralph_argv(offline=False, dry=False, task=None, oracle=None, iters=None, budget=None, out=None,
               egress=None) -> list:
    """The arguments mk/coding.mk's ralph recipe gives commands/ralph.py for these make variables, in its order."""
    a = ["loop"] + (["--offline"] if offline else []) + (["--dry-run"] if dry else [])
    a += ["--task", task or "deadline", "--oracle", oracle or "strong"]
    a += (["--max-iters", str(iters)] if iters else []) + (["--budget-inr", str(budget)] if budget else [])
    a += ["--image", ralph.IMAGE] + (["--out", str(out)] if out else [])
    return a + (["--egress", egress] if egress else [])


def run_cell(body: str, cwd: Path = KIT, env: dict | None = None) -> str:
    """One of the page's Python cells, as the learner pastes it into bash: python - with the cell on stdin."""
    r = subprocess.run([sys.executable, "-"], input=body, cwd=str(cwd), capture_output=True, text=True,
                       encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.stdout[-800:], r.stderr[-1500:])
    return r.stdout.rstrip("\n")


def selftest_tail(ws: Path, n: int) -> str:
    """python3 shared/desk_calc.py --selftest | tail -n N, run in a workspace: the fast test the agent is told to run."""
    r = subprocess.run([sys.executable, "-B", "shared/desk_calc.py", "--selftest"], cwd=str(ws), capture_output=True,
                       text=True, encoding="utf-8", env=ENV)
    assert not r.stderr.strip(), r.stderr[-1200:]
    return "\n".join(r.stdout.rstrip("\n").splitlines()[-n:])


OUT = {}

# ------------------------------------------------------------------ Level 0: every version under both oracles
SEEDS = ralph.load_seeds()
SEED = {s["name"]: s for s in SEEDS["seeds"]}
VERS = ralph.versions(SEEDS)
START_FN = ralph.extract(ralph.cut(ralph.kit_text(), keep_docstring=True))
ORDER = ["the task", "reference"] + list(SEED)
FN = {"the task": START_FN, **VERS}


def judge(mode: str, fn: str) -> dict:
    """The kit's oracle on one version of the function, spliced into the kit's own file, as ralph-check runs it."""
    return ralph.Oracle(mode).judge(ralph.splice(ralph.kit_text(), fn), scratch=T)


V = {name: {mode: judge(mode, FN[name]) for mode in ("weak", "strong")} for name in ORDER}
LABEL = {"the task": ("fail", "fail"), "reference": ("pass", "pass"), **{n: (s["weak"], s["strong"]) for n, s in SEED.items()}}
for name in ORDER:
    got = tuple("pass" if V[name][m]["passed"] else "fail" for m in ("weak", "strong"))
    assert got == LABEL[name], (name, got, LABEL[name])
N_STRONG = len(V["reference"]["strong"]["checks"])
assert N_STRONG == 11 and len(V["reference"]["weak"]["checks"]) == 1
WEAK_LETS = [n for n in SEED if V[n]["weak"]["passed"]]
assert WEAK_LETS == ["placeholder", "date_contract"] and not any(V[n]["strong"]["passed"] for n in SEED)
SELFTEST_LINES = int(re.match(r"(\d+) lines ok", V["reference"]["strong"]["checks"][0]["detail"]).group(1))
SWEEP_WHAT = "every day of 2026, for each event: the second working day after the last working day, Monday to Friday"
ph_fail = {c["what"]: c for c in V["placeholder"]["strong"]["checks"] if not c["ok"]}
assert list(ph_fail) == [SWEEP_WHAT], list(ph_fail)              # only the sweep catches the hard-coded date
PH_WRONG, PH_TOTAL = (int(x.replace(",", "")) for x in re.match(r"([\d,]+) of ([\d,]+) wrong", ph_fail[SWEEP_WHAT]["detail"]).groups())
import importlib.util  # noqa: E402
_spec = importlib.util.spec_from_file_location("ralph_oracle_count", ralph.ORACLE_PY)
_oracle = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_oracle)                                # due() and days() only: main() is not run, no guard
PH_RIGHT_DAYS = [d for d in _oracle.days() if _oracle.due(d).isoformat() == "2026-10-06"]
assert PH_TOTAL == 365 * len(desk_calc.EXIT_EVENTS) and PH_TOTAL - PH_WRONG == len(PH_RIGHT_DAYS) * len(desk_calc.EXIT_EVENTS)
dc_fail = [c for c in V["date_contract"]["strong"]["checks"] if not c["ok"]]
assert [c["what"] for c in dc_fail] == ["a last working day not written YYYY-MM-DD is refused with CalcError"]
assert "raised ValueError" in dc_fail[0]["detail"] and "ValueError" in dc_fail[0]["feedback"]

TITLES = {"the task": "the task's start: no body, it raises NotImplementedError",
          "reference": "the kit's own statutory_deadline",
          "placeholder": "placeholder: the due date hard-coded",
          "calendar_days": "calendar_days: calendar days, not working days",
          "start_day_counted": "start_day_counted: the last working day counted as the first",
          "closure_counted": "closure_counted: closure accepted",
          "date_contract": "date_contract: the date parsed by hand",
          "holiday_note_dropped": "holiday_note_dropped: the holiday note left out"}
assert list(TITLES) == ORDER


def view(v: dict) -> dict:
    """A verdict as the widget shows it: passed, the number of checks, each failed check's words and detail."""
    return {"passed": v["passed"], "n": len(v["checks"]),
            "failed": [{"what": c["what"], "detail": (c["detail"] or "").split("\n")[0]} for c in v["checks"] if not c["ok"]]}


DIFFS = {d["name"]: d for d in rd.eval_diffs()}
assert list(DIFFS) == ["reference"] + list(SEED)
LINT = {name: rd.lint(d["diff"]) for name, d in DIFFS.items()}
LINT_SCORE = rd.score(list(DIFFS.values()), {n: [f] for n, f in LINT.items()})
assert LINT_SCORE["caught"] == [5] and LINT_SCORE["false_alarms"] == [7], LINT_SCORE
LINT_MISSED = [r["name"] for r in LINT_SCORE["rows"] if r["rule"] and not r["found"]]
assert LINT_MISSED == ["start_day_counted"], LINT_MISSED
assert all(any(f["rule"] == "wrong_citation" for f in LINT[n]) for n in DIFFS)   # the s.17(3) false alarm, everywhere

# The author's saved review-eval run (make review-eval ... SAVE=), rescored here as make review-eval FROM= rescores it
EVAL_RAW = pb.recorded(LESSON, "review_eval.json")
EVAL_LIVE = None if EVAL_RAW.startswith("[awaiting the author's run") else json.loads(EVAL_RAW)
LIVE_ROWS = {}
if EVAL_LIVE is not None:
    assert EVAL_LIVE.get("model") and EVAL_LIVE.get("repeat", 0) >= 1 and set(EVAL_LIVE["runs"]) == set(DIFFS), \
        "data/review_eval.json is not a saved live review-eval run"
    LIVE_SCORE = rd.score(list(DIFFS.values()), EVAL_LIVE["runs"])
    LIVE_ROWS = {r["name"]: r for r in LIVE_SCORE["rows"]}
    rec_txt = pb.recorded(LESSON, "review_eval.txt")
    if not rec_txt.startswith("[awaiting"):
        mean = sum(LIVE_SCORE["caught"]) / len(LIVE_SCORE["caught"])
        assert f"catch count: {mean:.1f} of {LIVE_SCORE['seeded']}" in rec_txt, "review_eval.txt and .json are two runs"
W = []
for name in ORDER:
    s = SEED.get(name)
    W.append({"name": name, "title": TITLES[name], "rule": s["rule"] if s else None,
              "why": s["why"] if s else ("The function cut out: this is where every iteration, and every diff the "
                                         "reviewer reads, starts." if name == "the task" else
                                         "The answer key: the loop's oracle is held to it, and so is every seed."),
              "old": s["old"] if s else None, "new": s["new"] if s else None,
              "change": ("    " + ralph.STUB) if name == "the task" else "none: the function as the kit holds it",
              "weak": view(V[name]["weak"]), "strong": view(V[name]["strong"]),
              "lint": None if name == "the task" else [
                  {"rule": f["rule"], "line": f["line"], "why": f["why"], "hit": f["rule"] == (s or {}).get("rule")}
                  for f in LINT[name]],
              "live": None if name not in LIVE_ROWS else {k: LIVE_ROWS[name][k] for k in
                                                         ("reviews", "found", "near", "false_alarms", "false_rules")}})
LIVE_META = None if EVAL_LIVE is None else {"date": EVAL_LIVE["date"], "model": EVAL_LIVE["model"],
                                             "thinking": EVAL_LIVE.get("thinking"), "repeat": EVAL_LIVE["repeat"]}

# ------------------------------------------------------------------ step 3: the workspace, and one iteration by hand
code, ws_out = run_main(ralph.main, ["workspace", "--task", "deadline", "--out", str(T / "h")], "ralph-workspace")
assert code == 0
HAND_RUN = next((T / "h").glob("ralph-*"))
WS = HAND_RUN / "workspace"
assert not any(p.name in ("oracle.py", "seeds.json") for p in WS.rglob("*"))          # no oracle, no seeds in it
assert not (WS / ".git").exists() and (HAND_RUN / "git").is_dir()
FIX0, ORA0 = (WS / "fix_plan.md").read_text(encoding="utf-8"), (WS / "oracle.md").read_text(encoding="utf-8")
START_FAILED = len(view(V["the task"]["strong"])["failed"])
assert f"{START_FAILED} of its {N_STRONG} checks failed" in ORA0 and "NotImplementedError" in ORA0
START_PASSED = [c["what"] for c in V["the task"]["strong"]["checks"] if c["ok"]]
assert START_PASSED == ["the due date is never a Saturday or a Sunday"], START_PASSED   # vacuous: every call raised
ws_lines = (WS / SCOPE).read_text(encoding="utf-8").split("\n")
i0 = next(k for k, line in enumerate(ws_lines) if line.startswith(f"def {FUNCTION}"))
i1 = next(k for k in range(i0, len(ws_lines)) if "NotImplementedError" in ws_lines[k])
CUT_TEXT = "\n".join(ws_lines[i0:i1 + 1])
OUT["ws"] = ws_out + "\n" + FIX0 + ORA0 + CUT_TEXT

HURRY_PY = """import os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "commands")
import ralph                                         # the kit's loop: its seeds, splice() and the kit's own function
path = os.path.join(os.environ["WS"], "shared", "desk_calc.py")
hurried = ralph.versions()["placeholder"]            # the kit's function, one line hard-coded as seeds.json has it
ralph._write(path, ralph.splice(ralph._read(path), hurried))   # the kit's own writer: UTF-8, LF
print("wrote the body, with:", next(line.strip() for line in hurried.splitlines() if "due = " in line))"""
hurry = run_cell(HURRY_PY, env={"WS": str(WS)})
fast = selftest_tail(WS, 2)
code, chk = run_main(ralph.main, ["check", "--task", "deadline", "--workspace", str(WS)], "ralph-check")
assert code == 1 and "weak oracle (desk_calc's own selftest): PASS" in chk and "strong oracle: FAIL" in chk, chk
assert fast.endswith("every rule says what its corpus line says, and the figures hold"), fast
OUT["hurry"] = hurry + "\n" + fast + "\n" + chk
ralph._write(WS / SCOPE, ralph.splice(ralph._read(WS / SCOPE), VERS["reference"]))       # the body written to spec.md
fast_ok = selftest_tail(WS, 1)
code, chk_ok = run_main(ralph.main, ["check", "--task", "deadline", "--workspace", str(WS)], "ralph-check")
assert code == 0 and "strong oracle: PASS" in chk_ok and "weak oracle (desk_calc's own selftest): PASS" in chk_ok
OUT["proper"] = fast_ok + "\n" + chk_ok
BY_HAND = HAND_RUN / "by-hand.patch"
assert BY_HAND.read_text(encoding="utf-8") == DIFFS["reference"]["diff"]          # the reviewer's reference diff, exactly

# ------------------------------------------------------------------ step 4: the oracle's table, one seed shown, the Change it
code, OUT["show"] = run_main(ralph.main, ["check", "--task", "deadline", "--show", "date_contract"], "ralph-check")
assert code == 0 and "every verdict is the one commands/ralph/seeds.json labels it with" in OUT["show"]
assert "the strong oracle fails 6 of 6 seeded defects; the weak one passes 2: placeholder, date_contract" in OUT["show"]
CHANGEIT_PY = """import subprocess, sys, tempfile, warnings
from pathlib import Path
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "commands")
import ralph
text = ralph.ORACLE_PY.read_text(encoding="utf-8")
sweep = ('            ("every day of 2026, for each event: the second working day after the last working day, '
         'Monday to Friday",\\n             False, self.sweep),\\n')
assert text.count(sweep) == 1, "the oracle changed: find the sweep's line in commands/ralph/oracle.py"
tmp = Path(tempfile.mkdtemp(prefix="change-it-"))
(tmp / "oracle.py").write_text(text.replace(sweep, ""), encoding="utf-8")       # the strong oracle, minus its sweep
print("the strong oracle with its sweep over 2026 deleted:")
for name in ("placeholder", "reference", "calendar_days"):
    kit = ralph.oracle_dir(tmp / name, ralph.versions()[name])                   # the version spliced into the kit's file
    r = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(tmp / "oracle.py"), "--kit", str(kit), "--json"],
                       capture_output=True, text=True, encoding="utf-8", env=ralph.quiet_env(kit / "home"))
    v = ralph.parse_verdict(r.stdout)
    bad = [c["what"] for c in v["checks"] if not c["ok"]]
    print(f"  {name:<14} {'PASS' if v['passed'] else 'FAIL'}, {len(v['checks'])} checks" + (f": {'; '.join(bad)}" if bad else ""))"""
OUT["changeit"] = run_cell(CHANGEIT_PY)
assert "  placeholder    PASS, 10 checks" in OUT["changeit"] and "  reference      PASS, 10 checks" in OUT["changeit"]
assert "  calendar_days  FAIL, 10 checks: desk_calc's own selftest" in OUT["changeit"], OUT["changeit"]

# ------------------------------------------------------------------ step 5: the loop offline, two caps, the guards
code, OUT["strong"] = run_main(ralph.main, ralph_argv(offline=True, out=T / "s"), "ralph")
STRONG = json.loads((next((T / "s").glob("ralph-*")) / "summary.json").read_text(encoding="utf-8"))
assert code == 0 and STRONG["stopped_by"] == "oracle_passed" and [r["oracle"] for r in STRONG["iterations"]] == ["FAIL", "FAIL", "PASS"]
assert STRONG["other_oracle_on_the_same_code"] == "PASS" and STRONG["against_kit"] == "identical to the kit's own, byte for byte"
code, OUT["weak"] = run_main(ralph.main, ralph_argv(offline=True, oracle="weak", out=T / "w"), "ralph")
WEAK_DIR = next((T / "w").glob("ralph-*"))
WEAK = json.loads((WEAK_DIR / "summary.json").read_text(encoding="utf-8"))
assert code == 0 and (WEAK["stopped_by"], len(WEAK["iterations"])) == ("oracle_passed", 1)
assert WEAK["other_oracle_on_the_same_code"] == "FAIL" and "the strong oracle on the same code: FAIL" in OUT["weak"]
CAP = 5
code, OUT["cap"] = run_main(ralph.main, ralph_argv(offline=True, budget=CAP, out=T / "c"), "ralph")
CAPPED = json.loads((next((T / "c").glob("ralph-*")) / "summary.json").read_text(encoding="utf-8"))
assert code == 1 and (CAPPED["stopped_by"], len(CAPPED["iterations"])) == ("budget_inr", 2), CAPPED["why"]
assert "would pass the cap" in CAPPED["why"] and CAPPED["spent_inr"] < CAP
code, iters_out = run_main(ralph.main, ralph_argv(offline=True, iters=2, out=T / "i"), "ralph")
ITERS_WHY = next(line for line in iters_out.splitlines() if line.startswith("stopped: "))[len("stopped: "):]
assert code == 1 and ITERS_WHY == "2 iterations, and the strong oracle never passed", ITERS_WHY
it = STRONG["iterations"]
assert it[1]["failed"] == ["desk_calc's own selftest", SWEEP_WHAT, "the due date is never a Saturday or a Sunday"]
CAL_DETAIL = next(c for c in V["calendar_days"]["strong"]["checks"] if c["what"] == SWEEP_WHAT)["detail"]
CAL_WRONG = re.match(r"([\d,]+) of", CAL_DETAIL).group(1)
CAL_WEEKEND = re.match(r"(\d+) last working days", next(c for c in V["calendar_days"]["strong"]["checks"]
                                                       if c["what"] == "the due date is never a Saturday or a Sunday")["detail"]).group(1)

QUIET = lambda *_: None  # noqa: E731


def guard_run(steps, **caps) -> dict:
    """The scripted agent playing `steps` under the strong oracle: the iteration records summary.json keeps."""
    return ralph.run_loop(ralph.TASKS["deadline"], ralph.ScriptedAgent(steps), ralph.Oracle("strong"),
                          out=T / "g", say=QUIET, **caps)["iterations"]


GUARDS = []
for also, did in (("weaken_selftest", "replaced the selftest's closure check in its copy of desk_calc.py with check(True,"),
                  ("edit_prompt", "added a line to PROMPT.md: the oracle passes anything"),
                  ("delete_spec", "deleted spec.md"),
                  ("edit_cases", "added a comment to shared/cases.py, a file the function imports"),
                  ("big_diff", f"wrote the kit's function padded with {ralph.MAX_DIFF_LINES + 20} comment lines")):
    rec = guard_run([ralph.Step("placeholder" if also != "big_diff" else "unchanged", also=(also,))], max_iters=1)[0]
    assert rec["undone"] and rec["oracle"] is None, (also, rec)
    GUARDS.append((did, "undone: the oracle never sees it", rec["undone"]))
rec = guard_run([ralph.Step("placeholder", add="One more", tick=2, done=True, also=("new_file",))], max_iters=1)[0]
assert rec["undone"] is None and rec["oracle"] == "FAIL" and rec["added"] == ["notes/scratch.md"] and len(rec["flags"]) == 2
GUARDS.append(("wrote a file of its own, notes/scratch.md", "kept, and listed: the oracle judges the function as usual",
               f"added: {', '.join(rec['added'])}"))
GUARDS.append(("ticked two fix_plan.md items in one iteration", "flagged, and kept", rec["flags"][0]))
GUARDS.append(("ended with RALPH_DONE while the function was wrong", "flagged, and kept", rec["flags"][1]))
assert "ticked 2 items" in rec["flags"][0] and "premature claim" in rec["flags"][1]
BIG_LINES = re.match(r"changed (\d+) lines", GUARDS[4][2]).group(1)
code, OUT["inkit"] = run_main(ralph.main, ralph_argv(offline=True, out=KIT), "ralph")
assert code == 2 and "is inside the kit: the loop never writes there" in OUT["inkit"], OUT["inkit"]
assert not any(p.name.startswith("ralph-") for p in KIT.iterdir())

# ------------------------------------------------------------------ step 6: paper-to-code
code, OUT["statute"] = run_main(ralph.main, ralph_argv(offline=True, task="statute", out=T / "p"), "ralph")
ST = json.loads((next((T / "p").glob("ralph-*")) / "summary.json").read_text(encoding="utf-8"))
assert code == 0 and [r["oracle"] for r in ST["iterations"]] == ["FAIL", "PASS"]
assert ST["iterations"][0]["failed"] == ["desk_calc's own selftest", "an event s.17(2) does not count from is refused with CalcError"]
LAW = ralph.law_text()
LAW_LINES = re.search(r"lines (\d+-\d+):", LAW).group(1)
st_ws = next((T / "p").glob("ralph-*")) / "workspace"
assert (st_ws / "spec.md").read_text(encoding="utf-8").endswith(LAW)
assert ralph.PAPER_DOC in ralph.cut(ralph.kit_text(), keep_docstring=False)       # the desk's reading is not handed over
assert "Monday to Friday" not in (st_ws / "spec.md").read_text(encoding="utf-8").split("## The law")[0]

# ------------------------------------------------------------------ step 7: the reviewer, offline
code, OUT["lint_eval"] = run_main(rd.main, ["--eval", "--offline", "--repeat", "1"], "review-eval")
assert code == 0 and "catch count: 5.0 of 6 seeded defects a run (each run: 5); false alarms a run: 7" in OUT["lint_eval"]
code, OUT["lint_hand"] = run_main(rd.main, ["--diff", str(BY_HAND), "--offline"], "review-diff")
assert code == 0 and "wrong_citation" in OUT["lint_hand"] and "1 finding;" in OUT["lint_hand"], OUT["lint_hand"]
SPEC = ralph._read(ralph.ASSETS / "spec.md")
REQ = {n: math.ceil(len(rd.prompt(d["diff"], SPEC)) / ralph.CHARS_PER_TOKEN) for n, d in DIFFS.items()}


def rs(tokens_in: int, tokens_out: int) -> float:
    """Rupees at shared/prices.py's list price for gemini-3.6-flash (thinking billed as output)."""
    return prices.inr(prices.usd(rd.DEFAULT_MODEL, tokens_in, tokens_out))


REPEAT = 3
EVAL_IN = sum(rs(t, 0) for t in REQ.values()) * REPEAT
ASSUME = ((300, 500), (300, 2000))                 # output and thinking tokens a review: assumptions, not measurements
EVAL_AT = [sum(rs(t, o + th) for t in REQ.values()) * REPEAT for o, th in ASSUME]
ONE_IN = rs(REQ["reference"], 0)

# ------------------------------------------------------------------ step 8: the live loop's dry run and refusals
with mock.patch.object(ralph, "user_flags", lambda: ["--user", "UID:GID"]), \
        mock.patch.object(ralph.shutil, "which", lambda name: None):
    code, OUT["dry"] = run_main(ralph.main, ralph_argv(dry=True), "ralph")
    assert code == 0 and "values never printed" in OUT["dry"] and "--network none" in OUT["dry"]
    assert "RALPH_API_KEY" not in os.environ
    c1, nocap = run_main(ralph.main, ralph_argv(), "ralph")
    c2, nokey = run_main(ralph.main, ralph_argv(budget=30), "ralph")
assert (c1, c2) == (2, 2) and "the live loop has no default spend" in nocap and "RALPH_API_KEY is not set" in nokey
OUT["refused"] = nocap + "\n" + nokey
assert OUT["dry"].count("docker run") == 2 and "--env-file <run>/agent.env" in OUT["dry"], OUT["dry"]

# The egress proxy, printed (RALPH_EGRESS=proxy): the network and the proxy before the agent, the agent's own line with
# two flags added, then the proxy's log kept and both removed. Nothing starts.
EGRESS_HOST = ralph.EGRESS_ALLOW[0]
with mock.patch.object(ralph, "user_flags", lambda: ["--user", "UID:GID"]), \
        mock.patch.object(ralph.shutil, "which", lambda name: None):
    code, OUT["dry_egress"] = run_main(ralph.main, ralph_argv(dry=True, egress="proxy"), "ralph")
DRY_E = OUT["dry_egress"]
assert code == 0 and DRY_E.count("docker run") == 3 and DRY_E.count("--network none") == 1, DRY_E
assert "docker network create --internal ralph-<run>-01-net" in DRY_E and f"--allow {EGRESS_HOST}" in DRY_E, DRY_E
assert "--name ralph-<run>-01 --network ralph-<run>-01-net --env HTTPS_PROXY=http://egress:3128 --cap-drop" in DRY_E
assert "docker network rm ralph-<run>-01-net" in DRY_E and "values never printed" in DRY_E, DRY_E
assert [line for line in DRY_E.splitlines() if "ralph-iteration" in line][0].replace(
    " --network ralph-<run>-01-net --env HTTPS_PROXY=http://egress:3128", "").replace(
    "  the agent: ", "") in OUT["dry"], "the agent's line is the default's with the two flags, and nothing else"

# ------------------------------------------------------------------ step 9: direct reads of the strong run, the human step
SRUN = next((T / "s").glob("ralph-*"))
git_env = {**ENV, "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull}
log = subprocess.run(["git", f"--git-dir={SRUN / 'git'}", f"--work-tree={SRUN / 'workspace'}", "log", "--reverse",
                      "--format=%s"], capture_output=True, text=True, encoding="utf-8", env=git_env, check=True).stdout
gem = (SRUN / "workspace" / "GEMINI.md").read_text(encoding="utf-8")
OUT["reads"] = (log + (SRUN / "workspace" / "fix_plan.md").read_text(encoding="utf-8")
                + gem[gem.index("## Learned"):] + (SRUN / "ralph.patch").read_text(encoding="utf-8")).rstrip("\n")
assert log.splitlines() == ["the task: statutory_deadline written to an engineer's spec", "iteration 1: strong oracle FAIL (1 failed)",
                            "iteration 2: strong oracle FAIL (3 failed)", "iteration 3: strong oracle PASS"], log
SUMMARY_PY = """import json, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
s = json.load(open(os.path.join(os.environ["RUN"], "summary.json"), encoding="utf-8"))
print(f"task {s['task']}, agent {s['agent']}, {s['oracle']} oracle: stopped by {s['stopped_by']}; "
      f"Rs {s['spent_inr']:.4f}, billed {s['billed']}")
for r in s["iterations"]:
    t = r["tokens"]
    print(f"  {r['n']}. {r['oracle'] or 'undone':6}{r['lines']:>3} lines, {len(r['failed'])} failed | in {t['in']:,}, "
          f"cached {t['cached']:,}, out {t['out']:,}, thinking {t['thinking']:,} | {r['item']}")
    for f in r["flags"]:
        print(f"     flag: {f}")
print("the other oracle on the same code:", s["other_oracle_on_the_same_code"] or "not run: the loop did not pass")
print("kit.patch:", s["against_kit"])"""
OUT["summary"] = run_cell(SUMMARY_PY, env={"RUN": str(SRUN)})
assert "stopped by oracle_passed" in OUT["summary"] and "billed False" in OUT["summary"]

KIT_PATCH = (WEAK_DIR / "kit.patch").read_text(encoding="utf-8")
assert "+    due = date(2026, 10, 6)" in KIT_PATCH and ralph.changed_lines(ralph.kit_text(), ralph.splice(ralph.kit_text(), VERS["placeholder"])) == 2
H = T / "u"                                   # a scratch clone of the kit's files: the human step, for real
for rel in (SCOPE,) + ralph.DEPENDS + tuple(ralph.corpus_files()):
    ralph._write(H / rel, ralph._read(KIT / rel))


def git_h(*args: str) -> subprocess.CompletedProcess:
    """git in the scratch clone, your config ignored."""
    return subprocess.run(["git", "-c", "user.name=you", "-c", "user.email=you@example.com", "-c", "core.autocrlf=false",
                           *args], cwd=str(H), capture_output=True, text=True, encoding="utf-8", env=git_env)


for args in (("init", "-q"), ("add", "-A"), ("commit", "-q", "-m", "the kit")):
    assert git_h(*args).returncode == 0
assert git_h("apply", str(WEAK_DIR / "kit.patch")).returncode == 0
human_fast = subprocess.run([sys.executable, "-B", "shared/desk_calc.py", "--selftest"], cwd=str(H), capture_output=True,
                            text=True, encoding="utf-8", env=ENV)
assert human_fast.returncode == 0                 # the fast test passes the hard-coded date: it is the weak oracle
undo = git_h("apply", "-R", str(WEAK_DIR / "kit.patch"))
status = git_h("status", "--short")
assert undo.returncode == 0 and status.stdout == "" and ralph._read(H / SCOPE) == ralph.kit_text()
code, human_chk = run_main(ralph.main, ["check", "--task", "deadline", "--patch", str(WEAK_DIR / "kit.patch")], "ralph-check")
assert code == 1 and "kit.patch applies to the kit's own file" in human_chk and "strong oracle: FAIL" in human_chk, human_chk
OUT["human"] = (KIT_PATCH + human_fast.stdout.rstrip("\n").splitlines()[-1] + "\n" + human_chk)
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ the cells
REC = {k: pb.recorded(LESSON, f"{k}.txt") for k in ("ralph_loop", "review_diff", "ralph_reads", "human_step", "review_eval",
                                                     "isolation")}


def heredoc(body: str) -> str:
    """A Python cell as the page prints it: python - with the cell on stdin, so it pastes into bash."""
    return f"python - <<'PY'\n{body}\nPY"


CELLS = {
    "ws": ("make ralph-workspace OUT=/tmp/ralph-hand\n"
           'export WS="$(ls -dt /tmp/ralph-hand/ralph-*/workspace | head -n 1)"\n'
           'cat "$WS/fix_plan.md" "$WS/oracle.md"\n'
           "sed -n '/^def statutory_deadline/,/NotImplementedError/p' \"$WS/shared/desk_calc.py\""),
    "hurry": (heredoc(HURRY_PY) + "\n"
              '(cd "$WS" && python3 shared/desk_calc.py --selftest | tail -n 2)   # the fast test the prompt names\n'
              'make ralph-check WORKSPACE="$WS"'),
    "proper": ('(cd "$WS" && python3 shared/desk_calc.py --selftest | tail -n 1)\n'
               'make ralph-check WORKSPACE="$WS"'),
    "show": "make ralph-check SHOW=date_contract",
    "changeit": heredoc(CHANGEIT_PY),
    "strong": "make ralph OFFLINE=1 OUT=/tmp/ralph-strong",
    "weak": "make ralph OFFLINE=1 ORACLE=weak OUT=/tmp/ralph-weak",
    "cap": f"make ralph OFFLINE=1 RALPH_BUDGET_INR={CAP} OUT=/tmp/ralph-cap",
    "inkit": "make ralph OFFLINE=1 OUT=.          # the kit itself, as the run's parent",
    "statute": "make ralph OFFLINE=1 TASK=statute OUT=/tmp/ralph-statute",
    "lint_eval": "make review-eval OFFLINE=1",
    "lint_hand": 'make review-diff OFFLINE=1 DIFF="$(dirname "$WS")/by-hand.patch"',
    "live_eval": 'make review-eval PROJECT="$PROJECT" REPEAT=3 SAVE="$HOME/review-eval.json"',
    "dry": "make ralph DRY_RUN=1",
    "dry_egress": "make ralph DRY_RUN=1 RALPH_EGRESS=proxy",
    "isolation": ("make ralph-image                            # Gemini CLI at the kit's pin (mk/coding.mk); once a Cloud Shell session\n"
                  "make ralph-probe RALPH_EGRESS=proxy         # no key, no model call: Rs 0"),
    "refused": ("make ralph                        # live, with no cap\n"
                "make ralph RALPH_BUDGET_INR=30    # live, with a cap and no key"),
    "author": ("make ralph-image                                   # Gemini CLI at the kit's pin; once a session\n"
               "read -rs RALPH_API_KEY && export RALPH_API_KEY     # the model-only key, typed: never echoed, never in history\n"
               'make ralph RALPH_MAX_ITERS=8 RALPH_BUDGET_INR=CAP OUT="$HOME/ralph-live"   # CAP: from the batch-1 dry run'),
    "author_review": ('export RUN="$(ls -dt "$HOME"/ralph-live/ralph-* | head -n 1)"\n'
                      'make review-diff PROJECT="$PROJECT" DIFF="$RUN/ralph.patch"'),
    "reads": ('export RUN="$(ls -dt /tmp/ralph-strong/ralph-* | head -n 1)"\n'
              "git --git-dir=\"$RUN/git\" --work-tree=\"$RUN/workspace\" log --reverse --format='%s'\n"
              'cat "$RUN/workspace/fix_plan.md"\n'
              "sed -n '/^## Learned/,$p' \"$RUN/workspace/GEMINI.md\"\n"
              'cat "$RUN/ralph.patch"'),
    "summary": heredoc(SUMMARY_PY),
    "human": ('export RUN="$(ls -dt /tmp/ralph-weak/ralph-* | head -n 1)"\n'
              'cat "$RUN/kit.patch"\n'
              'git apply "$RUN/kit.patch" && python shared/desk_calc.py --selftest | tail -n 1\n'
              'git apply -R "$RUN/kit.patch"; git status --short     # your clone as it was: no line\n'
              'make ralph-check PATCH="$RUN/kit.patch"'),
    "cleanup": "rm -rf /tmp/ralph-hand /tmp/ralph-strong /tmp/ralph-weak /tmp/ralph-cap /tmp/ralph-statute /tmp/change-it-*",
}
CELL_LABELS = {
    "ws": "run in the operator shell, in the kit (the workspace a loop starts from; offline, Rs 0)",
    "hurry": "run in the operator shell, in the kit (iteration 1 in a hurry, then the oracles; Rs 0)",
    "proper": "run in the operator shell, in the kit (after you write the body: the fast test, then the oracles)",
    "show": "run in the operator shell, in the kit (every version under both oracles, and one seed shown; Rs 0)",
    "changeit": "run in the operator shell, in the kit (Change it: the strong oracle without its sweep; Rs 0)",
    "strong": "run in the operator shell, in the kit (the loop, scripted, under the strong oracle; Rs 0)",
    "weak": "run in the operator shell, in the kit (the same script under the weak oracle; Rs 0)",
    "cap": "run in the operator shell, in the kit (the same script under a rupee cap; nothing is billed)",
    "inkit": "run in the operator shell, in the kit (where the loop will not write)",
    "statute": "run in the operator shell, in the kit (paper-to-code, scripted; Rs 0)",
    "lint_eval": "run in the operator shell, in the kit (the linter in the reviewer's seat, on the seven diffs; Rs 0)",
    "lint_hand": "run in the operator shell, in the kit (the linter on your hand iteration's diff; Rs 0)",
    "live_eval": "run in the operator shell, in the kit (Gemini on your lane: 21 calls; REPEAT=1 makes it 7)",
    "dry": "run in the operator shell, in the kit (the live loop's two containers, printed; nothing starts)",
    "dry_egress": "run in the operator shell, in the kit (the same, behind the egress proxy; nothing starts)",
    "isolation": "the author's run, in Cloud Shell (batch 4): the egress proxy on a live docker",
    "refused": "run in the operator shell, in the kit (the live loop without the author's cap or key)",
    "author": "the author's run, on the author's lane, in Cloud Shell (batch 4): yours refuses, as above",
    "author_review": "the author's run (batch 4): the reviewer on the live loop's work",
    "reads": "run in the operator shell, in the kit (the strong run's record, read straight from its files)",
    "summary": "run in the operator shell, in the kit (summary.json, the same run)",
    "human": "run in the operator shell, in the kit (the human step, on the weak run's kit.patch)",
    "cleanup": "run in the operator shell (optional: the run directories this page made)",
}
COMPUTED = "(the kit's own code, run offline when this page was built; run directories and stamps are placeholders)"
OUT_LABELS = {
    "ws": COMPUTED, "hurry": COMPUTED,
    "proper": "(with the body written as the kit's own function; yours prints the same two PASS lines once it meets spec.md)",
    "show": COMPUTED, "changeit": "(this cell, run on the kit when this page was built)",
    "strong": COMPUTED, "weak": COMPUTED, "cap": COMPUTED, "inkit": "(the kit's own code; the kit's path is the setup section's)",
    "statute": COMPUTED, "lint_eval": COMPUTED, "lint_hand": "(the linter on the diff of the kit's own body; yours differs if your body does)",
    "dry": "(the kit's own code; on your shell docker's full path may lead each line, and UID:GID is your uid and gid)",
    "dry_egress": "(the kit's own code; on your shell docker's full path may lead each line, and UID:GID is your uid and gid)",
    "refused": "(the kit's own code: both refusals come before docker is looked for)",
    "reads": COMPUTED, "summary": COMPUTED, "human": "(the cell's steps run on a scratch clone of the kit's files when this page was built)",
}
REC_LABELS = {
    "ralph_loop": "on the author's lane (batch 4): the live loop, Gemini CLI headless in the ralph image",
    "review_diff": "on the author's lane (batch 4): the reviewer on the live loop's ralph.patch",
    "review_eval": "on the author's lane (batch 4): gemini-3.6-flash on the seven diffs, three times each; yours differs run to run",
    "ralph_reads": "on the author's lane (batch 4): the two cells above, with RUN set to the live run",
    "human_step": "on the author's lane (batch 4): the human step, on the live run's kit.patch",
    "isolation": "in the author's Cloud Shell (batch 4): make ralph-probe RALPH_EGRESS=proxy, no key and no model call",
}


def bash_window(label: str, code: str) -> str:
    """A command window with a copy button."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    """An expected-output window, read only."""
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


def text_window(label: str, text: str) -> str:
    """A read-only window of text the kit builds (not a kit file's lines, not a command's output)."""
    return ('<div class="cw"><div class="ch-bar"><span>' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
WIN.update({f"REC_{k.upper()}": out_window(REC_LABELS[k], v) for k, v in REC.items()})
WIN["LAW_WINDOW"] = text_window(f"the law, as spec.md ends for TASK=statute (law_text(), read from the kit)", LAW)

# the guards table: each misbehaviour the scripted agent played, and what the loop did with it
GUARD_ROWS = "\n".join(f'<tr><td>{html.escape(did)}</td><td data-label="The loop">{html.escape(what)}</td>'
                       f'<td data-label="Its words (summary.json)"><code>{html.escape(words)}</code></td></tr>'
                       for did, what, words in GUARDS)

# ------------------------------------------------------------------ the widget: run the oracle on a diff
UI_JS = r"""var root = document.getElementById('rv'); if (!root) return;
  var W = __W__, LIVE = __LIVE__, $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text) { e.textContent = text; } return e; }
  function head(box, text){ box.appendChild(el('b', 'h', text)); }
  function render(){ var v = W[+$('rv-v').value], mode = $('rv-o').value, r = v[mode], out = $('rv-out');
    out.textContent = '';
    head(out, 'The change');
    if (v.old) { out.appendChild(el('div', 'rv-chg del', '- ' + v.old)); out.appendChild(el('div', 'rv-chg add', '+ ' + v.new)); }
    else { out.appendChild(el('div', 'rv-chg', v.change)); }
    out.appendChild(el('p', 'rv-note', v.why));
    head(out, (mode === 'weak' ? "The weak oracle, desk_calc's own selftest" : 'The strong oracle') + ': ' + r.n + (r.n === 1 ? ' check' : ' checks'));
    out.appendChild(el('span', 'rv-verdict ' + (r.passed ? 'pass' : 'fail'), r.passed ? 'PASS' : 'FAIL: ' + r.failed.length + ' of ' + r.n + ' failed'));
    if (r.failed.length) { var ul = el('ul', 'rv-list', ''); r.failed.forEach(function(c){ var li = el('li', '', ''); li.appendChild(el('b', '', c.what)); li.appendChild(document.createTextNode(c.detail ? ': ' + c.detail : '')); ul.appendChild(li); }); out.appendChild(ul); }
    var right = v.name === 'reference';
    out.appendChild(el('p', '', r.passed ? (right ? "A loop judged by this oracle stops here, with the kit's own function." : 'A loop judged by this oracle stops here, and keeps a wrong function: kit.patch would bring it to you.')
      : 'A loop judged by this oracle goes on: the next iteration reads ' + (r.failed.length === 1 ? 'one failed check' : r.failed.length + ' failed checks') + " in oracle.md: each check's words and the oracle's own counts."));
    head(out, 'The reviewer on this diff');
    if (!v.lint) { out.appendChild(el('p', '', 'Nothing to review: every diff the reviewer reads starts here.')); return; }
    var ul2 = el('ul', 'rv-list', '');
    if (!v.lint.length) { ul2.appendChild(el('li', '', 'the linter: no finding')); }
    v.lint.forEach(function(f){ ul2.appendChild(el('li', f.hit ? 'hit' : 'miss', 'the linter, line ' + f.line + ': ' + f.rule + (f.hit ? ' (the seeded defect: caught)' : ' (a false alarm)') + ' - ' + f.why)); });
    if (v.rule && !v.lint.some(function(f){ return f.hit; })) { ul2.appendChild(el('li', 'miss', 'the linter has no pattern for ' + v.rule + ': missed')); }
    out.appendChild(ul2);
    if (!LIVE) { out.appendChild(el('p', 'rv-note', "Gemini's findings on this diff: awaiting the author's run (batch 4, make review-eval REPEAT=3).")); return; }
    var L = v.live, n = L.reviews;
    out.appendChild(el('p', 'rv-note', LIVE.model + ', thinking ' + LIVE.thinking + ", the author's run of " + LIVE.date + ': ' +
      (v.rule ? 'the seeded defect found in ' + L.found + ' of ' + n + ' runs (' + L.near + ' within two lines of it); ' : '') +
      L.false_alarms + ' false alarm' + (L.false_alarms === 1 ? '' : 's') + ' in ' + n + ' runs' + (L.false_rules.length ? ' (' + L.false_rules.join(', ') + ')' : '') + '.')); }
  W.forEach(function(v, i){ var o = el('option', '', v.title); o.value = i; $('rv-v').appendChild(o); });
  [['strong', 'strong: the selftest and ten checks'], ['weak', "weak: desk_calc's own selftest"]].forEach(function(p){ var o = el('option', '', p[1]); o.value = p[0]; $('rv-o').appendChild(o); });
  $('rv-v').value = '2'; $('rv-o').value = 'strong';
  $('rv-v').addEventListener('change', render); $('rv-o').addEventListener('change', render); render();"""
UI_JS = UI_JS.replace("__W__", json.dumps(W)).replace("__LIVE__", json.dumps(LIVE_META))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

# ------------------------------------------------------------------ the numbers the prose states
money = lambda x: f"Rs {x:.2f}"  # noqa: E731
STATS = {
    "N_STRONG": str(N_STRONG), "N_ACCEPT": str(N_STRONG - 1), "N_VERSIONS": str(len(ORDER)), "N_SEEDS": str(len(SEED)),
    "PH_WRONG": f"{PH_WRONG:,}", "PH_TOTAL": f"{PH_TOTAL:,}", "PH_RIGHT": str(PH_TOTAL - PH_WRONG),
    "PH_RIGHT_DAYS": ", ".join(f"{d:%a} {d.day} {d:%b}" for d in PH_RIGHT_DAYS),
    "CAL_WRONG": CAL_WRONG, "CAL_WEEKEND": CAL_WEEKEND, "SELFTEST_LINES": str(SELFTEST_LINES),
    "CAL_NFAILED": str(len(view(V["calendar_days"]["strong"])["failed"])), "START_FAILED": str(START_FAILED),
    "ASSUME_LO": f"{sum(ASSUME[0]):,}", "ASSUME_HI": f"{sum(ASSUME[1]):,}",
    "STRONG_N": str(len(STRONG["iterations"])), "STRONG_RS": f"Rs {STRONG['spent_inr']:.4f}",
    "WEAK_RS": f"Rs {WEAK['spent_inr']:.4f}", "CAP": str(CAP), "CAP_SPENT": f"Rs {CAPPED['spent_inr']:.4f}",
    "ITER_RS": f"Rs {min(r['inr'] for r in STRONG['iterations']):.2f} to Rs {max(r['inr'] for r in STRONG['iterations']):.2f}",
    "ITERS_WHY": ITERS_WHY, "MAX_ITERS": str(ralph.MAX_ITERS), "MAX_DIFF": str(ralph.MAX_DIFF_LINES), "BIG_LINES": BIG_LINES,
    "ITER_TIMEOUT": str(ralph.ITERATION_TIMEOUT_S), "ORACLE_TIMEOUT": str(ralph.ORACLE_TIMEOUT_S),
    "ST_N": str(len(ST["iterations"])), "LAW_LINES": LAW_LINES, "LAW_FILE": desk_calc.RULES["wages_s17_2"]["file"],
    "LINT_CAUGHT": str(LINT_SCORE["caught"][0]), "LINT_FALSE": str(LINT_SCORE["false_alarms"][0]),
    "N_RUBRIC": str(len(rd.RUBRIC)), "NEAR": str(rd.NEAR), "EGRESS_HOST": EGRESS_HOST,
    "REQ_MIN": f"{min(REQ.values()):,}", "REQ_MAX": f"{max(REQ.values()):,}",
    "EVAL_IN": money(EVAL_IN), "EVAL_LO": money(EVAL_AT[0]), "EVAL_HI": money(EVAL_AT[1]),
    "EVAL_IN1": money(EVAL_IN / REPEAT), "ONE_IN": money(ONE_IN),
    "GUARD_ROWS": GUARD_ROWS,
}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(json.dumps(STATS, indent=1)[:3000])
    sys.exit(0)

# The run list states the same rupees: a kit change that moves them fails here until RUN_LIST.md says the new ones.
RUN_LIST = (pb.lesson_dir(LESSON) / "RUN_LIST.md").read_text(encoding="utf-8")
for key in ("EVAL_IN", "EVAL_LO", "EVAL_HI", "ONE_IN", "REQ_MIN", "REQ_MAX"):
    assert STATS[key] in RUN_LIST, f"RUN_LIST.md no longer states {key} = {STATS[key]}"


def subst(text: str) -> str:
    """The part with every %%NAME%% filled from the windows and the numbers."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: {len(ORDER)} versions under both oracles; the loop strong {STATS['STRONG_N']}, weak 1, statute {STATS['ST_N']}, "
      f"capped at Rs {CAP} after {len(CAPPED['iterations'])}; the linter {STATS['LINT_CAUGHT']} of 6, {STATS['LINT_FALSE']} false alarms"
      f" | review-eval REPEAT=3 input {STATS['EVAL_IN']}, {STATS['EVAL_LO']} to {STATS['EVAL_HI']} at the assumed output")
