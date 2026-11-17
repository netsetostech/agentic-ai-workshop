#!/usr/bin/env python3
"""make ralph: a Ralph loop (workshop lesson 10.10). A coding agent, started fresh on the same prompt each iteration,
works on one function in a copy of a kit file, and an oracle it cannot see or edit decides when the work is done.

    python commands/ralph.py loop --offline [--task deadline|statute] [--oracle strong|weak]   # a script, Rs 0
    python commands/ralph.py loop --budget-inr 30 [--max-iters 8] [--model gemini-3.6-flash]  # Gemini CLI, live
    python commands/ralph.py loop --budget-inr 30 --egress proxy    # live, the agent held to the model endpoint
    python commands/ralph.py workspace [--task deadline|statute]    # the starting workspace, for an iteration by hand
    python commands/ralph.py check [--patch FILE | --workspace DIR] # the oracles' verdicts, offline, Rs 0
    python commands/ralph.py probe [--yes] [--egress proxy]         # the batch-1 probe: Docker and Gemini CLI headless
    make ralph | ralph-workspace | ralph-check | ralph-image | ralph-probe                      (mk/coding.mk)

THE TASK. shared/desk_calc.py's statutory_deadline (the Code on Wages, 2019, s.17(2): wages due two working days after
the last working day, Monday to Friday), cut out of a copy of the kit's file: the copy keeps the def line and raises
NotImplementedError. --task deadline (the default) gives the agent an engineer's spec, commands/ralph/spec.md. --task
statute is paper-to-code, the same function from the statute alone: commands/ralph/statute.md and the corpus lines
desk_calc.RULES cites for it (wages_s17_2 and wages_s17_3), read from evals/corpus as its selftest reads them, with the
function's own docstring, which states the desk's reading, replaced. The answer key is the kit's own function, so there
is no second copy of it to drift: commands/ralph/seeds.json's six defects are one-line substitutions on it, and a seed
whose line has changed stops the run with its name.

THE WORKSPACE. A fresh run directory under the system's temp directory, or under --out, which may not be inside the
kit. workspace/ holds the cut shared/desk_calc.py, the shared/ files it imports and the evals/corpus/ files its
selftest reads, all copied from the kit; PROMPT.md, spec.md, fix_plan.md, GEMINI.md (commands/ralph/context.md: it gets
the name Gemini CLI loads only here, so a gemini session opened in the kit never loads the loop's instructions) and
oracle.md. Its git repository is git/, beside it and never inside it, so the agent can neither see nor write it and a
hook it writes cannot run when the loop commits; it has no remote, and its git ignores your global and system config.

ONE ITERATION. The agent runs once, fresh: the scripted agent offline, Gemini CLI headless in the ralph image live.
Then code inspects the workspace and undoes the iteration, keeping it in the log, when it made a symlink; changed or
deleted any file but fix_plan.md, GEMINI.md, oracle.md and shared/desk_calc.py; changed what shared/desk_calc.py does
outside statutory_deadline (the module's syntax tree without that function differs from the task's: a weakened
selftest is one); changed more lines of shared/desk_calc.py than RALPH_MAX_DIFF_LINES (80); or, live, named a host
that serves the kit's public copy, where the oracle can be read. It flags, without undoing, more than one fix_plan.md
item ticked and a RALPH_DONE the oracle does not back. Otherwise the oracle judges the function, its verdict goes into
oracle.md - each failed check's words with the oracle's own counts (never an acceptance check's expected value, never
the candidate's own text), and the selftest's FAIL lines, which the agent's copy of the file prints anyway - and the
iteration is one commit. oracle.md is all the next iteration learns of the oracle.

THE ORACLE. commands/ralph/oracle.py, on a copy of the kit with only the candidate's statutory_deadline spliced into the
kit's own shared/desk_calc.py. --oracle weak is desk_calc's own selftest, which checks the function on one date;
strong, the default, adds the acceptance checks, among them every day of 2026 for each event. It runs in a separate
Python process with the network and new processes refused (oracle.py's no_network()) and no credential in its
environment. The live loop's code is a model's, so there it runs in the ralph image with --network none.

THE CAPS. The loop stops when the oracle passes, at RALPH_MAX_ITERS (8), or at RALPH_BUDGET_INR. The rupee cap follows
the chat Meter's rule (services/chat/limits.py): it is checked before each iteration but the first, so an iteration
under way always finishes, and the loop also stops when the dearest iteration so far would take it past the cap. An
iteration's rupees are its tokens at list price (shared/prices.py: thinking billed as output, cached input at a
tenth), from Gemini CLI's JSON stats; offline they are commands/agent_patterns.py's scripted count, four characters a
token over what the script reads and writes, and nothing is billed. The live loop has no default cap: without
RALPH_BUDGET_INR it does not start. A live iteration is cut at RALPH_ITERATION_TIMEOUT_S (900); a cut iteration, or one
whose agent printed no stats, cost what nobody counted, so the loop stops there.

THE LIVE AGENT. One docker run of the ralph image an iteration (commands/ralph/Dockerfile, make ralph-image): the
workspace at /work; the prompt and Gemini CLI's system settings (commands/ralph/settings.json: the web tools excluded,
the session's turns capped) mounted read-only from the kit, outside the workspace; --cap-drop ALL, no-new-privileges, a
read-only root, memory and process limits; and in its environment only the model credential. That is RALPH_API_KEY
from your shell, written for the iteration into a 0600 --env-file beside the workspace and deleted when it ends, as
GOOGLE_API_KEY with GOOGLE_GENAI_USE_VERTEXAI, plus GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=global when --project
is given (the batch-1 probe says whether the key needs them). Never your gcloud config, never ADC, never the docker
socket. The credential is one the author creates for the run, able to call the model and nothing else, and deletes
after it (the cohort plan's decision 12). By default the agent's container can reach the network, hence the public-copy
rule above; RALPH_EGRESS=proxy holds it to the model endpoint.

THE EGRESS PROXY (RALPH_EGRESS=proxy, or --egress proxy; off unless given, and off the loop runs as before). Added on
13 October 2026, the day of work the cohort plan had cut first. Each iteration's agent container joins an internal
network of its own (docker network create --internal: no route out), with HTTPS_PROXY naming the one other container
on it, as egress: the proxy, commands/ralph/egress.py in a container of the ralph image, which also sits on docker's
default bridge. It opens a tunnel to EGRESS_ALLOW, the model endpoint, and refuses every other host, port and plain
request; a tool in the agent's container that ignores HTTPS_PROXY has no route at all, as the network has none. The
network and the proxy are made before the iteration and removed after it, whatever happens; the proxy's log, a line a
request, is iterations/NN-egress.txt, and the iteration's line counts it. It holds the host, not the requests: what
goes through a tunnel is TLS, and the key in the agent's container could call the model outside Gemini CLI's stats,
which the rupee cap reads. Whether a name lookup still leaves the internal network is docker's to say (its embedded
DNS): make ralph-probe RALPH_EGRESS=proxy prints it, with the rest of the isolation, on a live docker.

WHAT IT NEVER DOES. Write inside the kit (a run directory there is refused), apply a patch to your clone, or run git
push: its git refuses push, pull, fetch, clone and remote, and runs only on the run directory.

THE OUTPUT. Per iteration: the fix_plan.md item it ticked, the oracle's verdict, the lines changed, the tokens and
rupees, and any flag or undo; then why it stopped. In the run directory: ralph.patch (the loop's work, the task's start
to its end: what make review-diff reads), kit.patch (its statutory_deadline against the kit's own: git apply it in your
clone, run python shared/desk_calc.py --selftest and the kit's tests, then git apply -R; empty when the agent wrote the
kit's function byte for byte),
summary.json, and iterations/ with each agent's output, each verdict and, with RALPH_EGRESS=proxy, each proxy's log.
Exit 0 when the oracle passed, 1 when the loop stopped without it, 2 when it could not start.
"""
from __future__ import annotations

import argparse
import ast
import difflib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent
ASSETS = HERE / "ralph"
ORACLE_PY = ASSETS / "oracle.py"
SEEDS_FILE = ASSETS / "seeds.json"
for _p in (str(HERE), str(KIT)):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from agent_patterns import CHARS_PER_TOKEN, SCRIPTED_THINKING  # noqa: E402 - the bench's scripted count, stdlib
from shared import desk_calc, prices  # noqa: E402 - the standard library only

SCOPE = "shared/desk_calc.py"
FUNCTION = "statutory_deadline"
DEPENDS = ("shared/cases.py", "shared/desk_law.py", "shared/roles.py")     # what desk_calc.py imports from shared/
NOTES = ("fix_plan.md", "GEMINI.md", "oracle.md")                          # what else an iteration may change
LAW = ("wages_s17_2", "wages_s17_3")                                        # desk_calc.RULES' lines for FUNCTION
DEFAULT_MODEL = "gemini-3.6-flash"
MAX_ITERS, MAX_DIFF_LINES, ITERATION_TIMEOUT_S, ORACLE_TIMEOUT_S = 8, 80, 900, 180
IMAGE = "documind-ralph"
DONE = "RALPH_DONE"
PUBLIC_COPY = ("github.com", "githubusercontent.com", "agents_workshop_learner")
NEVER = ("push", "pull", "fetch", "clone", "remote", "submodule", "ls-remote", "request-pull", "send-email")
MODEL_NAME = re.compile(r"^[a-z0-9][a-z0-9.-]{0,63}$")
TICKED, OPEN = re.compile(r"^\s*- \[[xX]\] (.*)$", re.M), re.compile(r"^(\s*)- \[ \] (.*)$", re.M)
MARK = "ORACLE-VERDICT "                         # oracle.py's verdict line


class Refused(Exception):
    """The run cannot start, or a seed no longer fits the kit: exit 2 with these words."""


# ----------------------------------------------------------------------------- text, written as the kit writes it
def _read(path: Path) -> str:
    return Path(path).read_bytes().decode("utf-8")


def _write(path: Path, text: str) -> None:
    """UTF-8 and LF on every platform: git apply refuses a patch whose lines end CRLF where the file's end LF."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(text.encode("utf-8"))


# ----------------------------------------------------------------------------- the function in scope
def _node(text: str, name: str = FUNCTION):
    """The last top-level def of `name` (the one an import binds). SyntaxError when the text does not parse."""
    found = [n for n in ast.parse(text).body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name]
    if not found:
        raise LookupError(f"no top-level def {name}")
    return found[-1]


def _span(text: str, name: str = FUNCTION) -> tuple[int, int]:
    node = _node(text, name)
    return min([d.lineno for d in node.decorator_list] + [node.lineno]), node.end_lineno


def extract(text: str, name: str = FUNCTION) -> str:
    """The function's source, its decorators to its last statement."""
    first, last = _span(text, name)
    return "".join(text.splitlines(keepends=True)[first - 1:last])


def splice(text: str, function_text: str, name: str = FUNCTION) -> str:
    """`text` with the function's source replaced by `function_text`."""
    first, last = _span(text, name)
    lines = text.splitlines(keepends=True)
    return "".join(lines[:first - 1]) + function_text.rstrip("\n") + "\n" + "".join(lines[last:])


def outside(text: str, name: str = FUNCTION) -> str:
    """What the module does without the function: its syntax tree, every def of `name` left out. Comments, blank lines
    and line numbers are not in it, so only a change of behaviour outside the function changes it."""
    tree = ast.parse(text)
    tree.body = [n for n in tree.body if not (isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == name)]
    return ast.dump(tree)


STUB = 'raise NotImplementedError("statutory_deadline has no body yet: spec.md says what it does")'
PAPER_DOC = '"""Code on Wages, 2019, s.17(2): the law in spec.md says what this works out."""'


def cut(text: str, keep_docstring: bool = True) -> str:
    """The task's start: the function's def line, its docstring (or, for paper-to-code, a line pointing at the law in
    spec.md), then a raise of NotImplementedError where its body was."""
    node = _node(text)
    lines = text.splitlines(keepends=True)
    first = node.body[0]
    indent = " " * first.col_offset
    has_doc = isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant) and isinstance(first.value.value, str)
    head_end = (first.end_lineno if keep_docstring else first.lineno - 1) if has_doc else first.lineno - 1
    middle = "" if keep_docstring and has_doc else indent + PAPER_DOC + "\n"
    return "".join(lines[:head_end]) + middle + indent + STUB + "\n" + "".join(lines[node.end_lineno:])


# ----------------------------------------------------------------------------- the seeds and the answer key
def load_seeds() -> dict:
    return json.loads(_read(SEEDS_FILE))


def kit_text() -> str:
    return _read(KIT / SCOPE)


def versions(seeds: dict | None = None) -> dict[str, str]:
    """The function as the kit holds it (reference) and each seeded defect's version of it, by name."""
    seeds = seeds or load_seeds()
    reference = extract(kit_text())
    out = {"reference": reference}
    for s in seeds["seeds"]:
        n = reference.count(s["old"])
        if n != 1:
            raise Refused(f"seed {s['name']}: {s['old']!r} is in the kit's {FUNCTION} {n} times, not once: the function "
                          f"changed, so refresh commands/ralph/seeds.json")
        out[s["name"]] = reference.replace(s["old"], s["new"])
    return out


def corpus_files() -> list[str]:
    """The corpus files desk_calc's selftest reads: every file RULES cites."""
    return sorted({f"evals/corpus/{r['file']}" for r in desk_calc.RULES.values()})


def law_text() -> str:
    """The corpus lines desk_calc.RULES cites for the function, verbatim, as the selftest reads them."""
    rules = [desk_calc.RULES[k] for k in LAW]
    (rel,) = {r["file"] for r in rules}
    lo = min(int(r["lines"].split("-")[0]) for r in rules)
    hi = max(int(r["lines"].split("-")[-1]) for r in rules)
    rows = _read(KIT / "evals" / "corpus" / rel).split("\n")      # grep -n's lines, as desk_calc._corpus_text counts
    return f"evals/corpus/{rel}, lines {lo}-{hi}:\n\n```\n" + "\n".join(rows[lo - 1:hi]) + "\n```\n"


# ----------------------------------------------------------------------------- the tasks
@dataclass(frozen=True)
class Step:
    """One iteration of the scripted agent: the version of the function it writes, the fix_plan.md item it adds
    first, how many items it ticks, whether it claims RALPH_DONE, and what else it does (the tests' misbehaviours)."""
    version: str = "unchanged"            # "reference", a seed's name, or "unchanged"
    add: str | None = None
    tick: int = 1
    done: bool = False
    also: tuple = ()
    function: str | None = None           # a statutory_deadline of its own, in place of a version
    tokens: tuple | None = None           # (in, out, thinking, cached) in place of the script's count


@dataclass(frozen=True)
class Task:
    name: str
    title: str
    spec: str                             # under commands/ralph/
    keep_docstring: bool
    script: tuple                         # the scripted agent's steps


TASKS = {
    "deadline": Task("deadline", "statutory_deadline written to an engineer's spec", "spec.md", True, (
        Step("placeholder"),
        Step("calendar_days", add="Count the two working days from any last working day: the sweep over 2026 failed"),
        Step("reference", add="Skip Saturdays and Sundays: the due date fell on a weekend", done=True))),
    "statute": Task("statute", "statutory_deadline from the statute alone (paper-to-code)", "statute.md", False, (
        Step("closure_counted"),
        Step("reference", add="Refuse closure with CalcError: an event outside the four was taken", done=True))),
}


def spec_text(task: Task) -> str:
    text = _read(ASSETS / task.spec)
    return text + "\n" + law_text() if task.name == "statute" else text


# ----------------------------------------------------------------------------- the run and its git
def inside_kit(path: Path) -> bool:
    p, kit = Path(path).resolve(), KIT.resolve()
    return p == kit or kit in p.parents


@dataclass
class Run:
    dir: Path
    task: Task
    start: str = ""                       # the task's commit
    start_text: str = ""                  # shared/desk_calc.py at the start
    oracles: int = 0

    @property
    def ws(self) -> Path:
        return self.dir / "workspace"

    @property
    def git_dir(self) -> Path:
        return self.dir / "git"

    def git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess:
        """git on this run's workspace and repository only, with your global and system config ignored."""
        if args and args[0] in NEVER:
            raise Refused(f"the loop never runs git {args[0]}")
        env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
        env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CONFIG_GLOBAL=str(self.dir / "gitconfig"), GIT_TERMINAL_PROMPT="0")
        cmd = ["git", f"--git-dir={self.git_dir}", f"--work-tree={self.ws}",
               "-c", f"core.hooksPath={self.dir / 'nohooks'}", "-c", "core.autocrlf=false", "-c", "core.fsmonitor=false",
               "-c", "core.quotepath=off", "-c", "commit.gpgsign=false", "-c", "init.defaultBranch=main",
               "-c", "user.name=ralph", "-c", "user.email=ralph@localhost", *args]
        r = subprocess.run(cmd, cwd=self.dir, env=env, capture_output=True, text=True, encoding="utf-8",
                           errors="replace")
        if check and r.returncode != 0:
            raise RuntimeError(f"git {' '.join(args)}: {(r.stderr or r.stdout).strip()[:300]}")
        return r

    def commit(self, message: str) -> str:
        self.git("add", "-A")
        self.git("commit", "-q", "--allow-empty", "--no-verify", "-m", message)
        return self.git("rev-parse", "HEAD").stdout.strip()

    def head(self, rel: str) -> str:
        r = self.git("show", f"HEAD:{rel}", check=False)
        return r.stdout if r.returncode == 0 else ""

    def status(self) -> list[tuple[str, str]]:
        out = self.git("status", "--porcelain=v1", "-z", "--untracked-files=all", "--no-renames").stdout
        return [(e[:2], e[3:]) for e in out.split("\0") if e]

    def reset(self) -> None:
        self.git("reset", "-q", "--hard", "HEAD")
        self.git("clean", "-q", "-f", "-d")

    def diff(self, frm: str, to: str = "HEAD", path: str = SCOPE) -> str:
        return self.git("diff", "--no-color", "--no-ext-diff", "--no-textconv", frm, to, "--", path).stdout


def new_run(task: Task, parent: str | Path | None = None) -> Run:
    base = Path(parent).expanduser().resolve() if parent else Path(tempfile.gettempdir()).resolve()
    if inside_kit(base):
        raise Refused(f"{base} is inside the kit: the loop never writes there. Give OUT= a directory outside it")
    if not shutil.which("git"):
        raise Refused("git is not on PATH: the loop keeps each iteration as a commit in a repository beside the workspace")
    base.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    run = Run(Path(tempfile.mkdtemp(prefix=f"ralph-{task.name}-{stamp}-", dir=base)), task)
    (run.dir / "nohooks").mkdir()
    _write(run.dir / "gitconfig", "")
    (run.dir / "iterations").mkdir()
    return run


def build_workspace(run: Run, oracle: "Oracle") -> dict:
    """The task's start in run.ws, its oracle.md, and the first commit. Returns the oracle's verdict on the start."""
    task, ws = run.task, run.ws
    run.start_text = cut(kit_text(), keep_docstring=task.keep_docstring)
    _write(ws / SCOPE, run.start_text)
    for rel in DEPENDS + tuple(corpus_files()):
        _write(ws / rel, _read(KIT / rel))
    _write(ws / "PROMPT.md", _read(ASSETS / "PROMPT.md"))
    _write(ws / "spec.md", spec_text(task))
    _write(ws / "fix_plan.md", _read(ASSETS / "fix_plan.md"))
    _write(ws / "GEMINI.md", _read(ASSETS / "context.md"))
    verdict = oracle.judge(run.start_text, run)
    _write(ws / "oracle.md", oracle_md(verdict, "on the task as it starts, before any iteration"))
    run.git("init", "-q")
    _write(run.git_dir / "info" / "exclude", "__pycache__/\n*.pyc\n")
    run.start = run.commit(f"the task: {task.title}")
    _write(run.dir / "ralph-run.json", json.dumps({"task": task.name, "start": run.start, "scope": SCOPE,
                                                    "function": FUNCTION}, indent=1) + "\n")
    return verdict


def load_run(workspace: Path) -> Run | None:
    """The run a workspace belongs to, when make ralph-workspace or make ralph made it."""
    d = Path(workspace).resolve().parent
    marker = d / "ralph-run.json"
    if not marker.is_file():
        return None
    meta = json.loads(_read(marker))
    run = Run(d, TASKS[meta["task"]], start=meta["start"])
    run.start_text = run.git("show", f"{run.start}:{SCOPE}").stdout
    return run


# ----------------------------------------------------------------------------- the oracle
def oracle_dir(dest: Path, function_text: str) -> Path:
    """A copy of the kit for the oracle: the kit's own shared/desk_calc.py with `function_text` spliced in, the shared/
    files it imports, the corpus files its selftest reads, and an empty home."""
    _write(dest / SCOPE, splice(kit_text(), function_text))
    for rel in DEPENDS + tuple(corpus_files()):
        _write(dest / rel, _read(KIT / rel))
    (dest / "home").mkdir(parents=True, exist_ok=True)
    return dest


def quiet_env(home: Path) -> dict:
    """The oracle process's environment: a path, a home of its own, nothing else of yours - no credential, no project."""
    env = {"PATH": os.environ.get("PATH", os.defpath), "HOME": str(home), "USERPROFILE": str(home),
           "TMPDIR": str(home), "TEMP": str(home), "TMP": str(home), "LANG": "C.UTF-8"}
    for key in ("SYSTEMROOT", "WINDIR"):                          # what Python itself needs on Windows
        if key in os.environ:
            env[key] = os.environ[key]
    return env


def user_flags() -> list[str]:
    """Run a container as you, so what it writes in a mounted workspace is yours (POSIX hosts)."""
    return ["--user", f"{os.getuid()}:{os.getgid()}"] if hasattr(os, "getuid") else []


def _failed_verdict(mode: str, what: str, detail: str, feedback: str) -> dict:
    return {"mode": mode, "passed": False,
            "checks": [{"what": what, "weak": True, "ok": False, "detail": detail, "feedback": feedback}]}


def parse_verdict(stdout: str) -> dict | None:
    lines = [line for line in (stdout or "").splitlines() if line.startswith(MARK)]
    if not lines:
        return None
    try:
        v = json.loads(lines[-1][len(MARK):])
    except json.JSONDecodeError:
        return None
    if not isinstance(v, dict) or not isinstance(v.get("checks"), list) or not v["checks"]:
        return None
    v["passed"] = all(bool(c.get("ok")) for c in v["checks"])
    return v


class Oracle:
    """oracle.py in a separate Python process (host) or, for code a model wrote, in the ralph image (container)."""

    def __init__(self, mode: str = "strong", image: str | None = None, docker: str | None = None):
        if mode not in ("strong", "weak"):
            raise Refused(f"the oracle is strong or weak, not {mode!r}")
        self.mode, self.image, self.docker = mode, image, docker

    def command(self, kit_dir: Path) -> tuple[list[str], dict | None]:
        if self.image:
            return [self.docker or "docker", "run", "--rm", "--network", "none", "--read-only", "--tmpfs", "/tmp",
                    "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--pids-limit", "64",
                    "--memory", "512m", *user_flags(),
                    "--mount", f"type=bind,source={kit_dir},target=/oracle/kit,readonly",
                    "--mount", f"type=bind,source={ASSETS},target=/oracle/check,readonly",
                    self.image, "python3", "-I", "-B", "-X", "utf8", "/oracle/check/oracle.py",
                    "--kit", "/oracle/kit", "--mode", self.mode, "--json"], None
        return [sys.executable, "-I", "-B", "-X", "utf8", str(ORACLE_PY), "--kit", str(kit_dir), "--mode", self.mode,
                "--json"], quiet_env(kit_dir / "home")

    def judge(self, scope_text: str, run: Run | None = None, scratch: Path | None = None) -> dict:
        """The verdict on shared/desk_calc.py's text: {mode, passed, checks, output}."""
        try:
            function_text = extract(scope_text)
        except SyntaxError as e:
            return _failed_verdict(self.mode, "shared/desk_calc.py parses", f"SyntaxError: {e.msg} (line {e.lineno})",
                                   "it does not parse: SyntaxError")
        except LookupError:
            return _failed_verdict(self.mode, f"{FUNCTION} is defined", f"no top-level def {FUNCTION}",
                                   f"{FUNCTION} is not defined at the top level of shared/desk_calc.py")
        if run is not None:
            run.oracles += 1
            kit_dir = oracle_dir(run.dir / "oracle" / f"{run.oracles:02d}", function_text)
        else:
            kit_dir = oracle_dir(Path(tempfile.mkdtemp(prefix="oracle-", dir=scratch)), function_text)
        cmd, env = self.command(kit_dir)
        try:
            p = subprocess.run(cmd, cwd=str(kit_dir), env=env, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=ORACLE_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            return _failed_verdict(self.mode, "the oracle's checks finished", f"cut at {ORACLE_TIMEOUT_S} s",
                                   f"the checks did not finish in {ORACLE_TIMEOUT_S} s")
        verdict = parse_verdict(p.stdout)
        if verdict is None:
            tail = " | ".join((p.stderr or p.stdout).strip().splitlines()[-3:])[:300]
            return _failed_verdict(self.mode, "the oracle printed its verdict", f"exit {p.returncode}: {tail}",
                                   "the oracle printed no verdict")
        verdict["output"] = "\n".join(line for line in p.stdout.splitlines() if not line.startswith(MARK))
        return verdict


def weak_passed(verdict: dict) -> bool:
    return all(c["ok"] for c in verdict["checks"] if c.get("weak"))


def failed(verdict: dict) -> list[dict]:
    return [c for c in verdict["checks"] if not c["ok"]]


def oracle_md(verdict: dict, when: str) -> str:
    """What the agent may read of a verdict: each failed check's words and the oracle's own feedback line."""
    n, bad = len(verdict["checks"]), failed(verdict)
    out = [f"# The oracle's verdict: {'PASS' if verdict['passed'] else 'FAIL'}", "",
           f"The {verdict['mode']} oracle, {when}. " + (f"Every one of its {n} checks passes." if not bad else
                                                         f"{len(bad)} of its {n} checks failed:"), ""]
    for c in bad:
        first, *more = (c.get("feedback") or "").split("\n")
        out.append(f"- {c['what']}" + (f": {first}" if first else ""))
        out += [f"  {m.strip()}" for m in more if m.strip()]
    return "\n".join(out).rstrip() + "\n"


# ----------------------------------------------------------------------------- the agents
@dataclass
class AgentRun:
    tokens: dict = field(default_factory=lambda: {"in": 0, "cached": 0, "out": 0, "thinking": 0})
    inr: float | None = 0.0               # None: nobody counted it (a cut iteration, or no stats)
    claimed_done: bool = False
    log: str = ""
    error: str | None = None
    seconds: float = 0.0
    timed_out: bool = False
    models: dict = field(default_factory=dict)
    egress: dict | None = None            # RALPH_EGRESS=proxy: the proxy's log, counted (egress_seen())


def tick_first(plan: str) -> tuple[str, str | None]:
    m = OPEN.search(plan)
    if not m:
        return plan, None
    return plan[:m.start()] + f"{m.group(1)}- [x] {m.group(2)}" + plan[m.end():], m.group(2)


class ScriptedAgent:
    """Plays a script, a Step an iteration (Task.script unless given): no model, no network, nothing billed. Its
    tokens are counted as commands/agent_patterns.py counts its scripted model's - four characters a token over what it
    reads (the prompt, spec.md, fix_plan.md, GEMINI.md, oracle.md and shared/desk_calc.py) and what it writes, and the
    low level's 64 thinking tokens - and priced at list price, so the rupee cap is exercised as it would be live."""

    name = "scripted"

    def __init__(self, steps=(), model: str = DEFAULT_MODEL, seeds: dict | None = None):
        self.steps, self.model = tuple(steps), model
        self.versions = versions(seeds)

    def run(self, run: Run, i: int) -> AgentRun:
        steps = self.steps or run.task.script
        step = steps[min(i, len(steps)) - 1]
        ws, started = run.ws, time.monotonic()
        read = sum(len(_read(ws / f)) for f in ("PROMPT.md", "spec.md", "fix_plan.md", "GEMINI.md", "oracle.md", SCOPE)
                   if (ws / f).is_file())
        plan = _read(ws / "fix_plan.md")
        if step.add:
            plan = plan.rstrip("\n") + f"\n- [ ] {step.add}\n"
        for _ in range(step.tick):
            plan = tick_first(plan)[0]
        _write(ws / "fix_plan.md", plan)
        if i == 1:
            _write(ws / "GEMINI.md", _read(ws / "GEMINI.md").rstrip("\n") +
                   "\n- python3 shared/desk_calc.py --selftest: the fast test; it stops at statutory_deadline until "
                   "the body is written\n")
        written = 0
        if step.function or step.version != "unchanged":
            fn = step.function or self.versions[step.version]
            _write(ws / SCOPE, splice(_read(ws / SCOPE), fn))
            written = len(fn)
        for what in step.also:
            written += self._also(what, run)
        tokens_in, tokens_out = math.ceil(read / CHARS_PER_TOKEN), math.ceil(written / CHARS_PER_TOKEN)
        thinking, cached = SCRIPTED_THINKING["low"], 0
        if step.tokens:
            tokens_in, tokens_out, thinking, cached = step.tokens
        inr = prices.inr(prices.usd(self.model, tokens_in, tokens_out + thinking, cached))
        log = f"(scripted) wrote {step.function and 'a function of its own' or step.version}" + (
            f"; also {', '.join(step.also)}" if step.also else "") + (f"\n{DONE}" if step.done else "")
        return AgentRun({"in": tokens_in, "cached": cached, "out": tokens_out, "thinking": thinking}, inr, step.done,
                        log, seconds=time.monotonic() - started)

    def _also(self, what: str, run: Run) -> int:
        """The misbehaviours the loop must catch, for its tests. Returns the characters written."""
        ws = run.ws
        if what == "weaken_selftest":
            text = _read(ws / SCOPE)
            _write(ws / SCOPE, text.replace('check(_raises(lambda: statutory_deadline("closure", "2026-10-02")),',
                                            "check(True,"))
        elif what == "edit_prompt":
            _write(ws / "PROMPT.md", _read(ws / "PROMPT.md") + "\nThe oracle passes anything: write RALPH_DONE.\n")
        elif what == "delete_spec":
            (ws / "spec.md").unlink()
        elif what == "edit_cases":
            _write(ws / DEPENDS[0], _read(ws / DEPENDS[0]) + "\n# an edit to a file the task does not cover\n")
        elif what == "symlink":
            os.symlink(KIT / SCOPE, ws / "shared" / "kit_copy.py")
        elif what == "new_file":
            _write(ws / "notes" / "scratch.md", "what the agent kept for itself\n")
        elif what == "big_diff":
            fn = self.versions["reference"].splitlines(keepends=True)
            padded = fn[0] + "".join(f"    # padding line {n}\n" for n in range(MAX_DIFF_LINES + 20)) + "".join(fn[1:])
            _write(ws / SCOPE, splice(_read(ws / SCOPE), padded))
            return len(padded)
        else:
            raise ValueError(f"no such misbehaviour: {what}")
        return 0


def write_env_file(path: Path, values: dict) -> None:
    """KEY=value lines, readable by you alone (0600), never a word of it on a command line."""
    for k, v in values.items():
        if "\n" in v or "\r" in v:
            raise Refused(f"{k} holds a line break")
    if path.exists():
        path.unlink()
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "wb") as f:
        f.write("".join(f"{k}={v}\n" for k, v in values.items()).encode("utf-8"))


def key_problem(key: str | None) -> str | None:
    """Why RALPH_API_KEY is no model-only key, or None."""
    if not key:
        return ("RALPH_API_KEY is not set: the live loop runs only on a model-only credential the author creates for "
                "the run and deletes after it, never on your gcloud login or ADC")
    if key.lstrip().startswith("{") or "private_key" in key:
        return "RALPH_API_KEY holds a service-account key's JSON: the loop takes a model-only API key, never a key file"
    if any(c.isspace() for c in key):
        return "RALPH_API_KEY holds a space or a line break"
    if os.path.exists(key):
        return "RALPH_API_KEY names a file: it holds the key itself"
    return None


def parse_cli_json(stdout: str) -> dict | None:
    """Gemini CLI's --output-format json object: the whole output, or the last line-start "{" that parses."""
    text = (stdout or "").strip()
    try:
        out = json.loads(text)
        return out if isinstance(out, dict) else None
    except json.JSONDecodeError:
        pass
    for m in reversed(list(re.finditer(r"(?m)^\{", text))):
        try:
            out = json.loads(text[m.start():])
            return out if isinstance(out, dict) else None
        except json.JSONDecodeError:
            continue
    return None


def price_stats(stats: dict | None) -> dict | None:
    """An iteration's tokens and rupees from Gemini CLI's stats.models: per model, input is prompt plus tool-use
    prompt tokens (cached ones among them, billed at a tenth), output is candidates plus thoughts (thinking billed as
    output), at list price (shared/prices.py; a model it does not know is priced as flash). None when there are none:
    then nobody counted the iteration's cost."""
    models = (stats or {}).get("models") if isinstance(stats, dict) else None
    if not isinstance(models, dict) or not models:
        return None
    total = {"in": 0, "cached": 0, "out": 0, "thinking": 0, "inr": 0.0, "models": {}}
    for model, m in models.items():
        if not isinstance(m, dict):
            continue
        t = m.get("tokens") or {}
        prompt, tool, cached, cand, thoughts = (int(t.get(k) or 0) for k in ("prompt", "tool", "cached", "candidates",
                                                                              "thoughts"))
        inr = prices.inr(prices.usd(model, prompt + tool, cand + thoughts, cached))
        total["models"][model] = {"in": prompt + tool, "cached": cached, "out": cand, "thinking": thoughts,
                                  "requests": int((m.get("api") or {}).get("totalRequests") or 0),
                                  "inr": round(inr, 6)}
        for k, v in (("in", prompt + tool), ("cached", cached), ("out", cand), ("thinking", thoughts)):
            total[k] += v
        total["inr"] += inr
    return total if total["models"] else None


class GeminiCliAgent:
    """Gemini CLI headless in the ralph image, one docker run an iteration (commands/ralph/iteration.sh)."""

    name = "gemini-cli"

    def __init__(self, docker: str, image: str, model: str, api_key: str, project: str | None = None,
                 timeout_s: float = ITERATION_TIMEOUT_S):
        if not MODEL_NAME.match(model or ""):
            raise Refused(f"{model!r} is not a model name")
        self.docker, self.image, self.model, self.key, self.project = docker, image, model, api_key, project
        self.timeout_s = timeout_s

    def env_values(self) -> dict:
        values = {"GOOGLE_API_KEY": self.key, "GOOGLE_GENAI_USE_VERTEXAI": "true"}
        if self.project:
            values.update(GOOGLE_CLOUD_PROJECT=self.project, GOOGLE_CLOUD_LOCATION="global")
        return values

    def command(self, workspace: Path, env_file: Path, name: str, prompt: Path = ASSETS / "PROMPT.md",
                run: tuple = ("ralph-iteration",)) -> list[str]:
        """The docker run line: what it mounts, and what it does not (no gcloud config, no ADC, no docker socket)."""
        return [self.docker, "run", "--rm", "--init", "--name", name,
                "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--read-only", "--tmpfs", "/tmp",
                "--memory", "2g", "--pids-limit", "256", "--cpus", "2", *user_flags(),
                "--env-file", str(env_file), "--env", f"RALPH_MODEL={self.model}", "--env", "HOME=/tmp",
                "--mount", f"type=bind,source={workspace},target=/work",
                "--mount", f"type=bind,source={prompt},target=/ralph/PROMPT.md,readonly",
                "--mount", f"type=bind,source={ASSETS / 'settings.json'},target=/etc/gemini-cli/settings.json,readonly",
                "--workdir", "/work", self.image, *run]

    def call(self, workspace: Path, env_file: Path, name: str, prompt: Path = ASSETS / "PROMPT.md") -> AgentRun:
        started = time.monotonic()
        write_env_file(env_file, self.env_values())
        try:
            p = subprocess.run(self.command(workspace, env_file, name, prompt), capture_output=True, text=True,
                               encoding="utf-8", errors="replace", timeout=self.timeout_s)
        except subprocess.TimeoutExpired:
            for verb in ("kill", "rm"):
                subprocess.run([self.docker, verb, *(["-f"] if verb == "rm" else []), name], capture_output=True,
                               timeout=60)
            return AgentRun(inr=None, error=f"cut at {self.timeout_s:.0f} s", timed_out=True,
                            seconds=time.monotonic() - started)
        finally:
            env_file.unlink(missing_ok=True)
        log = p.stdout + ("\n--- stderr ---\n" + p.stderr if p.stderr.strip() else "")
        out = parse_cli_json(p.stdout) or {}
        priced = price_stats(out.get("stats"))
        response = str(out.get("response") or "")
        error = out.get("error")
        error = (json.dumps(error)[:300] if isinstance(error, (dict, list)) else str(error)[:300]) if error else (
            None if p.returncode == 0 else f"exit {p.returncode}")
        run = AgentRun(log=log, error=error, seconds=time.monotonic() - started,
                       claimed_done=any(line.strip() == DONE for line in response.splitlines()))
        if priced is None:
            run.inr = None
        else:
            run.inr, run.models = priced["inr"], priced["models"]
            run.tokens = {k: priced[k] for k in ("in", "cached", "out", "thinking")}
        return run

    def run(self, run: Run, i: int) -> AgentRun:
        return self.call(run.ws, run.dir / "agent.env", f"ralph-{run.dir.name[-8:]}-{i:02d}".lower())


# ----------------------------------------------------------------------------- the egress proxy (RALPH_EGRESS=proxy)
# The one host:port the agent's container reaches with RALPH_EGRESS=proxy: Vertex AI's global endpoint. Gemini 3.x is
# served only from location global, and the agent's credential is a Vertex AI key (settings.json selects vertex-ai,
# env_values() sets GOOGLE_GENAI_USE_VERTEXAI), so the SDK's base URL is https://aiplatform.googleapis.com/ with
# RALPH_PROJECT and without it. Whatever else Gemini CLI asks for is refused and named in the proxy's log, which make
# ralph-probe RALPH_EGRESS=proxy YES=1 prints for its two calls.
EGRESS_ALLOW = ("aiplatform.googleapis.com:443",)
EGRESS_MODES = ("off", "proxy")
EGRESS_ALIAS, EGRESS_PORT = "egress", 3128   # its name on the agent's network: a valid hostname, unlike mkdtemp's _
EGRESS_PY = ASSETS / "egress.py"
EGRESS_WAIT_S = 30.0                     # how long the proxy may take to listen before its iteration stops the loop


def egress_mode(given: str | None = None) -> str:
    """--egress, else RALPH_EGRESS, else off; Refused for any other word."""
    mode = (given or os.environ.get("RALPH_EGRESS", "")).strip() or "off"
    if mode not in EGRESS_MODES:
        raise Refused(f"RALPH_EGRESS is off or proxy, not {mode!r}")
    return mode


def egress_seen(log: str) -> dict:
    """The proxy's log counted: what it allowed, refused and could not open, each {what: times}, first seen first."""
    seen = {"allowed": {}, "refused": {}, "failed": {}}
    for line in log.splitlines():
        verdict, _, rest = line.partition(" ")
        if verdict in seen and rest:
            what = rest.split(": ", 1)[0]
            seen[verdict][what] = seen[verdict].get(what, 0) + 1
    return seen


def egress_words(seen: dict) -> str:
    """egress_seen() in one line."""
    def each(counted: dict) -> str:
        return ", ".join(f"{what} ({n})" for what, n in counted.items())
    words = [f"allowed {each(seen['allowed'])}" if seen.get("allowed") else "allowed nothing",
             f"refused {each(seen['refused'])}" if seen.get("refused") else "refused nothing"]
    if seen.get("failed"):
        words.append(f"could not open {each(seen['failed'])}")
    if seen.get("error"):
        words.append(seen["error"])
    return "; ".join(words)


def _docker(cmd: list[str], timeout: float = 120) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)


def _tail(r: subprocess.CompletedProcess) -> str:
    return " | ".join((r.stderr or r.stdout or "").strip().splitlines()[-2:])[:300]


class Egress:
    """RALPH_EGRESS=proxy around one agent container, `tag` its name: the internal network <tag>-net, with no route out,
    and the proxy <tag>-egress (commands/ralph/egress.py, read-only, in a container of the ralph image) on docker's
    default bridge and on that network, where the agent finds it as `egress`: the agent's one way out, to EGRESS_ALLOW
    alone. up() makes both, or nothing; down() keeps the proxy's log, removes both, and never raises."""

    def __init__(self, docker: str, image: str, tag: str):
        self.docker, self.image = docker, image
        self.net, self.proxy = f"{tag}-net", f"{tag}-egress"
        self.log, self.made = "", []

    def agent_flags(self) -> list[str]:
        """What the agent's docker run line gains: the internal network, and the proxy as Gemini CLI's way out (it reads
        HTTPS_PROXY when its --proxy flag is not given)."""
        return ["--network", self.net, "--env", f"HTTPS_PROXY=http://{EGRESS_ALIAS}:{EGRESS_PORT}"]

    def up_commands(self) -> list[list[str]]:
        """The network, then the proxy on docker's default bridge, then the proxy joined to the network as `egress`."""
        allow = [word for host in EGRESS_ALLOW for word in ("--allow", host)]
        return [[self.docker, "network", "create", "--internal", self.net],
                [self.docker, "run", "-d", "--name", self.proxy, "--network", "bridge", "--read-only",
                 "--cap-drop", "ALL", "--security-opt", "no-new-privileges", "--memory", "256m", "--pids-limit", "128",
                 *user_flags(), "--mount", f"type=bind,source={EGRESS_PY},target=/egress/egress.py,readonly",
                 self.image, "python3", "-I", "-B", "-u", "/egress/egress.py", "--listen", f"0.0.0.0:{EGRESS_PORT}",
                 *allow],
                [self.docker, "network", "connect", "--alias", EGRESS_ALIAS, self.net, self.proxy]]

    def down_commands(self) -> list[list[str]]:
        """After the agent, whatever happened: the proxy's log read, then the proxy and the network removed."""
        return [[self.docker, "logs", self.proxy], [self.docker, "rm", "-f", self.proxy],
                [self.docker, "network", "rm", self.net]]

    def up(self, wait_s: float | None = None) -> "Egress":
        """The network and the proxy, listening; a RuntimeError, with nothing left behind, when they cannot be."""
        wait_s = EGRESS_WAIT_S if wait_s is None else wait_s
        try:
            net, proxy, join = self.up_commands()
            for cmd, made in ((net, "net"), (proxy, "proxy"), (join, None)):
                if made:
                    self.made.append(made)              # before the call: a proxy that failed to start may exist
                r = _docker(cmd)
                if r.returncode:
                    raise RuntimeError(f"the egress proxy did not start: docker {' '.join(cmd[1:3])}: {_tail(r)}")
            deadline = time.monotonic() + wait_s
            while True:
                r = _docker([self.docker, "logs", self.proxy])
                if "egress: listening on" in r.stdout:
                    return self
                if time.monotonic() > deadline:
                    raise RuntimeError(f"the egress proxy did not listen within {wait_s:g} s: {_tail(r) or 'no log'}")
                time.sleep(0.2)
        except BaseException:
            self.down()
            raise

    def down(self) -> dict:
        """The proxy's log kept, then the proxy and the network removed: egress_seen() of the log, with an error when
        the network could not be removed (docker network rm it by hand)."""
        error = None
        logs, rm, net_rm = self.down_commands()
        try:
            if "proxy" in self.made:
                r = _docker(logs, timeout=60)
                if r.returncode == 0:
                    self.log = r.stdout + r.stderr
                _docker(rm, timeout=60)
            if "net" in self.made:
                r = _docker(net_rm, timeout=60)
                if r.returncode:
                    error = f"docker network rm {self.net} failed: {_tail(r)}"
        except (OSError, subprocess.SubprocessError) as e:
            error = f"the egress proxy was not removed: {type(e).__name__}: {e}"
        self.made = []
        seen = egress_seen(self.log)
        if error:
            seen["error"] = error
        return seen

    def __enter__(self) -> "Egress":
        return self.up()

    def __exit__(self, *exc) -> None:
        self.down()


def held_to(line: list[str], egress: Egress) -> list[str]:
    """An agent's docker run line held to the egress proxy: its --network and HTTPS_PROXY after the line's --name."""
    at = line.index("--name") + 2
    return line[:at] + egress.agent_flags() + line[at:]


class EgressAgent(GeminiCliAgent):
    """GeminiCliAgent behind the egress proxy (RALPH_EGRESS=proxy): GeminiCliAgent's own docker run line, held to an
    internal network, with a proxy made for each call and removed after it, and its log kept in the run."""

    egress = "proxy"

    def command(self, workspace: Path, env_file: Path, name: str, prompt: Path = ASSETS / "PROMPT.md",
                run: tuple = ("ralph-iteration",)) -> list[str]:
        return held_to(super().command(workspace, env_file, name, prompt, run), Egress(self.docker, self.image, name))

    def call(self, workspace: Path, env_file: Path, name: str, prompt: Path = ASSETS / "PROMPT.md") -> AgentRun:
        proxy = Egress(self.docker, self.image, name).up()      # a RuntimeError stops the loop with its words
        try:
            ran = super().call(workspace, env_file, name, prompt)
        finally:
            seen = proxy.down()
        ran.egress = {**seen, "log": proxy.log}
        return ran

    def run(self, run: Run, i: int) -> AgentRun:
        ran = super().run(run, i)
        _write(run.dir / "iterations" / f"{i:02d}-egress.txt", ran.egress.pop("log", ""))
        return ran


# ----------------------------------------------------------------------------- one iteration, inspected
@dataclass
class Inspection:
    undo: str | None = None
    flags: list = field(default_factory=list)
    lines: int = 0
    ticked: list = field(default_factory=list)
    added: list = field(default_factory=list)


def changed_lines(before: str, after: str) -> int:
    return sum(1 for line in difflib.unified_diff(before.splitlines(), after.splitlines(), lineterm="", n=0)
               if line[:1] in "+-" and not line.startswith(("+++", "---")))


def inspect(run: Run, max_diff_lines: int, agent_log: str = "") -> Inspection:
    """What code checks of an iteration before the oracle sees it (the module docstring's ONE ITERATION)."""
    out, ws = Inspection(), run.ws
    for code, rel in run.status():
        if os.path.islink(ws / rel):
            out.undo = out.undo or f"made a symlink, {rel}"
        elif "D" in code:
            out.undo = out.undo or f"deleted {rel}"
        elif code == "??":
            out.added.append(rel)
        elif rel not in (SCOPE,) + NOTES:
            out.undo = out.undo or f"changed {rel}, a file the task does not cover"
    now = _read(ws / SCOPE) if (ws / SCOPE).is_file() else ""
    try:
        if outside(now) != outside(run.start_text):
            out.undo = out.undo or f"changed what {SCOPE} does outside {FUNCTION}"
    except SyntaxError:
        pass                                    # the oracle fails it; the next iteration is held to the task's start
    out.lines = changed_lines(run.head(SCOPE), now)
    if out.lines > max_diff_lines:
        out.undo = out.undo or f"changed {out.lines} lines of {SCOPE}, over the cap of {max_diff_lines}"
    named = [host for host in PUBLIC_COPY if host in agent_log.lower()]
    if named:
        out.undo = out.undo or f"named {named[0]}: the oracle is public there, so work that may be copied is not kept"
    before = {m.group(1).strip() for m in TICKED.finditer(run.head("fix_plan.md"))}
    plan = _read(ws / "fix_plan.md") if (ws / "fix_plan.md").is_file() else ""
    out.ticked = [m.group(1).strip() for m in TICKED.finditer(plan) if m.group(1).strip() not in before]
    if len(out.ticked) > 1:
        out.flags.append(f"ticked {len(out.ticked)} items in one iteration: the plan is one an iteration")
    return out


# ----------------------------------------------------------------------------- the loop
def _rs(x: float | None) -> str:
    return "unknown" if x is None else f"Rs {x:.4f}"


def run_loop(task: Task, agent, oracle: Oracle, *, max_iters: int = MAX_ITERS, budget_inr: float | None = None,
             max_diff_lines: int = MAX_DIFF_LINES, out: str | Path | None = None, say=print) -> dict:
    """The loop; returns summary.json's content."""
    run = new_run(task, out)
    verdict = build_workspace(run, oracle)
    say(f"ralph: task {task.name} ({task.title}), agent {agent.name}, {oracle.mode} oracle")
    say(f"  caps: {max_iters} iterations, " + (f"Rs {budget_inr:g}" if budget_inr is not None else "no rupee cap") +
        f", {max_diff_lines} changed lines an iteration")
    say(f"  the run: {run.dir}")
    if agent.name == "scripted":
        say("  OFFLINE: a scripted agent (commands/ralph.py, Task.script), no model, no network; its tokens are the "
            "script's, priced at list price, and nothing is billed")
    if getattr(agent, "egress", None) == "proxy":
        say(f"  egress: RALPH_EGRESS=proxy, each iteration's agent on an internal network of its own; its proxy "
            f"opens a tunnel to {', '.join(EGRESS_ALLOW)} and refuses everything else")
    records, spent, dearest, stopped = [], 0.0, 0.0, None
    try:
        for i in range(1, max_iters + 1):
            if i > 1 and budget_inr is not None:
                if spent >= budget_inr:
                    stopped = ("budget_inr", f"Rs {spent:.4f} spent, the cap is Rs {budget_inr:g}")
                    break
                if spent + dearest > budget_inr:
                    stopped = ("budget_inr", f"Rs {spent:.4f} spent; one more iteration at the dearest so far "
                                             f"(Rs {dearest:.4f}) would pass the cap of Rs {budget_inr:g}")
                    break
            ran = agent.run(run, i)
            _write(run.dir / "iterations" / f"{i:02d}-agent.txt", ran.log)
            if ran.inr is not None:
                spent += ran.inr
                dearest = max(dearest, ran.inr)
            look = inspect(run, max_diff_lines, ran.log if agent.name != "scripted" else "")
            rec = {"n": i, "item": look.ticked[0] if look.ticked else None, "ticked": look.ticked, "lines": look.lines,
                   "tokens": ran.tokens, "inr": None if ran.inr is None else round(ran.inr, 6),
                   "seconds": round(ran.seconds, 1), "claimed_done": ran.claimed_done, "undone": look.undo,
                   "flags": list(look.flags), "added": look.added, "error": ran.error, "oracle": None, "failed": []}
            if ran.egress is not None:
                rec["egress"] = ran.egress
            if look.undo:
                run.reset()
                rec["flags"].append(f"undone: it {look.undo}")
                _write(run.ws / "oracle.md", oracle_md(verdict, f"on the code as it stands: iteration {i} was undone, "
                                                                f"because it {look.undo}"))
                run.commit(f"iteration {i}: undone ({look.undo})")
            else:
                verdict = oracle.judge(_read(run.ws / SCOPE), run)
                _write(run.dir / "iterations" / f"{i:02d}-oracle.txt", verdict.get("output") or json.dumps(verdict))
                rec["oracle"] = "PASS" if verdict["passed"] else "FAIL"
                rec["failed"] = [c["what"] for c in failed(verdict)]
                if ran.claimed_done and not verdict["passed"]:
                    rec["flags"].append(f"claimed {DONE}, and the oracle failed it: a premature claim")
                _write(run.ws / "oracle.md", oracle_md(verdict, f"after iteration {i}"))
                run.commit(f"iteration {i}: {oracle.mode} oracle {rec['oracle']}" +
                           (f" ({len(rec['failed'])} failed)" if rec["failed"] else ""))
            records.append(rec)
            _say_iteration(say, rec, spent, verdict if not look.undo else None)
            if ran.inr is None:
                stopped = ("iteration_timeout" if ran.timed_out else "agent_failed",
                           f"iteration {i} {'was cut' if ran.timed_out else 'printed no stats'}: what it cost "
                           f"nobody counted, so the loop stops (read it in your lane's billing)")
                break
            if not look.undo and verdict["passed"]:
                stopped = ("oracle_passed", f"the {oracle.mode} oracle passed after {i} iteration{'s' if i > 1 else ''}")
                break
        else:
            stopped = ("max_iters", f"{max_iters} iterations, and the {oracle.mode} oracle never passed")
    except KeyboardInterrupt:
        stopped = ("interrupted", "stopped by you")
    except (OSError, RuntimeError, subprocess.SubprocessError) as e:     # docker gone, a disk full, a git failure
        stopped = ("error", f"{type(e).__name__}: {' '.join(str(e).split())[:300]}")
    finally:
        (run.dir / "agent.env").unlink(missing_ok=True)
    return finish(run, task, agent, oracle, records, stopped, spent, budget_inr, max_iters, max_diff_lines, say)


def _say_iteration(say, rec: dict, spent: float, verdict: dict | None) -> None:
    t = rec["tokens"]
    parts = [f"item \"{rec['item']}\"" if rec["item"] else "no item ticked",
             f"{rec['lines']} line{'' if rec['lines'] == 1 else 's'} changed"]
    if rec["oracle"]:
        parts.append(f"oracle {rec['oracle']}" + (f" ({len(rec['failed'])} failed)" if rec["failed"] else ""))
    parts.append(f"in {t.get('in', 0):,} (cached {t.get('cached', 0):,}), out {t.get('out', 0):,}, thinking "
                 f"{t.get('thinking', 0):,} tokens, {_rs(rec['inr'])}; spent Rs {spent:.4f}")
    say(f"iteration {rec['n']}: " + " | ".join(parts))
    if verdict is not None:
        for c in failed(verdict):
            say(f"    FAIL  {c['what']} ({(c.get('detail') or '').splitlines()[0][:200]})")
    for f in rec["flags"]:
        say(f"    flag: {f}")
    if rec["error"]:
        say(f"    the agent: {rec['error']}")
    if rec.get("egress") is not None:
        say(f"    egress: {egress_words(rec['egress'])}")


def finish(run: Run, task: Task, agent, oracle: Oracle, records: list, stopped: tuple, spent: float,
           budget_inr: float | None, max_iters: int, max_diff_lines: int, say) -> dict:
    final = _read(run.ws / SCOPE)
    head = run.git("rev-parse", "HEAD").stdout.strip()
    ralph_patch = run.diff(run.start, head)
    _write(run.dir / "ralph.patch", ralph_patch)
    try:
        theirs = splice(kit_text(), extract(final))
        kit_patch = "".join(difflib.unified_diff(kit_text().splitlines(keepends=True), theirs.splitlines(keepends=True),
                                                 f"a/{SCOPE}", f"b/{SCOPE}"))
        _write(run.dir / "kit.patch", kit_patch)
        against_kit = "identical to the kit's own, byte for byte" if not kit_patch else (
            f"{changed_lines(kit_text(), theirs)} lines differ from the kit's own")
    except (SyntaxError, LookupError):
        kit_patch, against_kit = None, f"no kit.patch: the final {SCOPE} has no {FUNCTION} that parses"
    other = None
    if stopped[0] == "oracle_passed":                 # where the loop's own oracle ran: a model's code, in a container
        other_mode = "weak" if oracle.mode == "strong" else "strong"
        other = "PASS" if Oracle(other_mode, oracle.image, oracle.docker).judge(final, run)["passed"] else "FAIL"
    summary = {"task": task.name, "title": task.title, "agent": agent.name,
               "model": getattr(agent, "model", None), "oracle": oracle.mode,
               "caps": {"max_iters": max_iters, "budget_inr": budget_inr, "max_diff_lines": max_diff_lines},
               "stopped_by": stopped[0], "why": stopped[1], "iterations": records, "spent_inr": round(spent, 6),
               "billed": agent.name != "scripted", "run": str(run.dir), "workspace": str(run.ws),
               "git": f"git --git-dir={run.git_dir} --work-tree={run.ws} log --oneline",
               "ralph_patch": "ralph.patch", "kit_patch": "kit.patch" if kit_patch is not None else None,
               "against_kit": against_kit, "other_oracle_on_the_same_code": other}
    if getattr(agent, "egress", None) == "proxy":
        summary["egress"] = {"mode": "proxy", "allow": list(EGRESS_ALLOW), "logs": "iterations/NN-egress.txt"}
    _write(run.dir / "summary.json", json.dumps(summary, indent=1, ensure_ascii=False) + "\n")
    say(f"stopped: {stopped[1]}")
    say(f"  spent: Rs {spent:.4f} at list price" + (" for the script's tokens (nothing is billed)"
                                                    if agent.name == "scripted" else ""))
    if other:
        say(f"  for the record, not used by the loop: the {'weak' if oracle.mode == 'strong' else 'strong'} oracle on "
            f"the same code: {other}")
    say(f"  {run.dir / 'ralph.patch'}: the loop's work ({changed_lines(run.start_text, final)} lines)")
    say(f"  {run.dir / 'kit.patch'}: its {FUNCTION} against the kit's: {against_kit}" if kit_patch is not None
        else f"  {against_kit}")
    say(f"  {run.dir / 'summary.json'}; the commits: {summary['git']}")
    say("  nothing was applied to your clone and nothing was pushed: applying kit.patch is yours to decide")
    return summary


# ----------------------------------------------------------------------------- check: the oracles' verdicts
def version_patch(function_text: str, task: Task) -> str:
    """The diff a reviewer reads for one version: the task's start to the function written."""
    start = cut(kit_text(), keep_docstring=task.keep_docstring)
    return "".join(difflib.unified_diff(start.splitlines(keepends=True),
                                        splice(start, function_text).splitlines(keepends=True),
                                        f"a/{SCOPE}", f"b/{SCOPE}"))


def verdicts(task: str = "deadline") -> list[dict]:
    """Every version's verdicts, for lesson 10.10's build: the task's start, the kit's own function and the six seeds,
    each {name, rule, why, label_weak, label_strong, weak, strong, failed, patch}."""
    t, seeds = TASKS[task], load_seeds()
    vs = versions(seeds)
    rows = [{"name": "the task", "rule": None, "why": "the function cut out: it raises NotImplementedError",
             "label_weak": "fail", "label_strong": "fail", "function": extract(cut(kit_text(), t.keep_docstring))},
            {"name": "reference", "rule": None, "why": "the kit's own statutory_deadline", "label_weak": "pass",
             "label_strong": "pass", "function": vs["reference"]}]
    rows += [{"name": s["name"], "rule": s["rule"], "why": s["why"], "label_weak": s["weak"],
              "label_strong": s["strong"], "function": vs[s["name"]]} for s in seeds["seeds"]]
    oracle = Oracle("strong")
    with tempfile.TemporaryDirectory(prefix="ralph-check-") as tmp:
        for r in rows:
            v = oracle.judge(splice(kit_text(), r["function"]), scratch=Path(tmp))
            r.update(weak="pass" if weak_passed(v) else "fail", strong="pass" if v["passed"] else "fail",
                     failed=[c["what"] for c in failed(v)], detail={c["what"]: c["detail"] for c in failed(v)},
                     patch=version_patch(r.pop("function"), t))
    return rows


def _apply(patch: Path, base_text: str, where: Path) -> str | None:
    """`base_text` with the patch's hunks for shared/desk_calc.py applied, or None when they do not apply."""
    _write(where / SCOPE, base_text)
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env.update(GIT_CONFIG_NOSYSTEM="1", GIT_CEILING_DIRECTORIES=str(where.parent))
    r = subprocess.run(["git", "apply", f"--include={SCOPE}", str(patch)], cwd=where, env=env, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return _read(where / SCOPE) if r.returncode == 0 else None


def check_change(task: Task, text: str, base: str, say=print) -> int:
    oracle = Oracle("strong")
    with tempfile.TemporaryDirectory(prefix="ralph-check-") as tmp:
        v = oracle.judge(text, scratch=Path(tmp))
    say(f"  weak oracle (desk_calc's own selftest): {'PASS' if weak_passed(v) else 'FAIL'}")
    say(f"  strong oracle: {'PASS' if v['passed'] else 'FAIL'}")
    for c in failed(v):
        say(f"    FAIL  {c['what']} ({(c.get('detail') or '').splitlines()[0][:200]})")
    try:
        if outside(text) != outside(base):
            say(f"  NOTE: the change also alters what {SCOPE} does outside {FUNCTION}: the oracle judged the function "
                f"alone, spliced into the kit's own file, and the loop would have undone that iteration")
    except SyntaxError:
        pass
    return 0 if v["passed"] else 1


def cmd_check(a, say=print) -> int:
    task = TASKS[a.task]
    if a.patch or a.workspace:
        say(f"ralph-check: the oracles on {FUNCTION} in a change of {SCOPE} (offline, Rs 0)")
        say("  the oracle runs the change's code on this machine, with the network and new processes refused inside "
            "Python: that is not a sandbox, so judge only a change you have read")
        if a.workspace:
            ws = Path(a.workspace).expanduser().resolve()
            if not (ws / SCOPE).is_file():
                say(f"ERROR: {ws} holds no {SCOPE}")
                return 2
            text, base = _read(ws / SCOPE), cut(kit_text(), task.keep_docstring)
            run = load_run(ws)
            if run is not None:
                base = run.start_text
                hand = "".join(difflib.unified_diff(base.splitlines(keepends=True), text.splitlines(keepends=True),
                                                    f"a/{SCOPE}", f"b/{SCOPE}"))
                _write(run.dir / "by-hand.patch", hand)
                say(f"  the workspace's change: {run.dir / 'by-hand.patch'} (make review-diff DIFF= reads it)")
            return check_change(task, text, base, say)
        patch = Path(a.patch).expanduser().resolve()
        if not patch.is_file():
            say(f"ERROR: no patch at {patch}")
            return 2
        with tempfile.TemporaryDirectory(prefix="ralph-apply-") as tmp:
            for label, base in (("the task's start", cut(kit_text(), task.keep_docstring)), ("the kit's own file",
                                                                                              kit_text())):
                text = _apply(patch, base, Path(tmp) / label.replace(" ", "_").replace("'", ""))
                if text is not None:
                    say(f"  {patch.name} applies to {label}")
                    return check_change(task, text, base, say)
        say(f"ERROR: {patch} applies neither to the task's start nor to the kit's own {SCOPE}")
        return 2
    try:
        rows = verdicts(a.task)
    except Refused as e:
        say(f"ERROR: {e}")
        return 1
    say(f"ralph-check: the oracles on {FUNCTION} in a copy of {SCOPE}, task {task.name} (offline, Rs 0)")
    say(f"  {'version':<22}{'weak':<7}{'strong':<8}seeded defect")
    wrong = []
    for r in rows:
        say(f"  {r['name']:<22}{r['weak'].upper():<7}{r['strong'].upper():<8}{r['rule'] or ''}")
        if (r["weak"], r["strong"]) != (r["label_weak"], r["label_strong"]):
            wrong.append(f"{r['name']}: weak {r['weak']}, strong {r['strong']}; its label says weak "
                         f"{r['label_weak']}, strong {r['label_strong']}")
    if a.show:
        for r in rows:
            if r["name"] == a.show:
                say(f"\n{r['name']}: {r['why']}\n{r['patch']}")
                for what, detail in r["detail"].items():
                    say(f"FAIL  {what}: {detail}")
    if a.write_patches:
        d = Path(a.write_patches).expanduser().resolve()
        if inside_kit(d):
            say(f"ERROR: {d} is inside the kit: write the patches elsewhere")
            return 2
        for r in rows[1:]:
            _write(d / f"{r['name']}.patch", r["patch"])
        say(f"  each version's patch, from the task's start: {d}")
    seeds_caught = [r for r in rows[2:] if r["strong"] == "fail"]
    weak_missed = [r["name"] for r in rows[2:] if r["weak"] == "pass"]
    say(f"  the strong oracle fails {len(seeds_caught)} of {len(rows) - 2} seeded defects; the weak one passes "
        f"{len(weak_missed)}: {', '.join(weak_missed) or 'none'}")
    if wrong:
        for w in wrong:
            say(f"  DISAGREES WITH ITS LABEL: {w}")
        return 1
    say("  every verdict is the one commands/ralph/seeds.json labels it with")
    return 0


# ----------------------------------------------------------------------------- the commands
def _setting(given, name: str, default, kind=int):
    """A flag, else the environment's RALPH_ variable, else the default."""
    if given is not None:
        return given
    raw = os.environ.get(name, "").strip()
    return kind(raw) if raw else default


def cmd_loop(a, say=print) -> int:
    task = TASKS[a.task]
    try:
        max_iters = _setting(a.max_iters, "RALPH_MAX_ITERS", MAX_ITERS)
        max_lines = _setting(a.max_diff_lines, "RALPH_MAX_DIFF_LINES", MAX_DIFF_LINES)
        budget = _setting(a.budget_inr, "RALPH_BUDGET_INR", None, float)
    except ValueError as e:
        say(f"ERROR: a cap is not a number: {e}")
        return 2
    model = a.model or os.environ.get("RALPH_MODEL") or DEFAULT_MODEL
    if max_iters < 1 or max_lines < 1 or (budget is not None and budget <= 0):
        say("ERROR: the caps are positive: RALPH_MAX_ITERS, RALPH_MAX_DIFF_LINES and RALPH_BUDGET_INR")
        return 2
    if a.offline:
        try:
            agent, oracle = ScriptedAgent(model=model), Oracle(a.oracle)
        except Refused as e:
            say(f"ERROR: {e}")
            return 2
    else:
        try:
            egress = egress_mode(a.egress)
        except Refused as e:
            say(f"ERROR: {e}")
            return 2
        image = a.image or os.environ.get("RALPH_IMAGE") or IMAGE
        timeout = _setting(None, "RALPH_ITERATION_TIMEOUT_S", ITERATION_TIMEOUT_S, float)
        docker = shutil.which("docker") or "docker"
        if not a.dry_run:
            problem = (None if budget is not None else
                       "the live loop has no default spend: give it RALPH_BUDGET_INR=<cap>, set from a dry run "
                       "(make ralph RALPH_MAX_ITERS=1 RALPH_BUDGET_INR=<a small cap> reads one iteration's rupees)")
            problem = problem or key_problem(os.environ.get("RALPH_API_KEY"))
            if problem is None and not shutil.which("docker"):
                problem = "docker is not on PATH: the live agent runs in a container (Cloud Shell has docker)"
            if problem is None and subprocess.run([docker, "image", "inspect", image], capture_output=True).returncode:
                problem = f"no image {image}: make ralph-image (Gemini CLI at the kit's pin, GEMINI_CLI_VERSION in mk/coding.mk)"
            if problem:
                say(f"ERROR: {problem}")
                return 2
        kind = EgressAgent if egress == "proxy" else GeminiCliAgent
        try:
            agent = kind(docker, image, model, os.environ.get("RALPH_API_KEY", ""), a.project, timeout)
        except Refused as e:
            say(f"ERROR: {e}")
            return 2
        oracle = Oracle(a.oracle, image=image, docker=docker)
        if a.dry_run:
            where, name = Path("<run>"), "ralph-<run>-01"
            proxy = Egress(docker, image, name) if egress == "proxy" else None
            if proxy:
                say("ralph --dry-run: an iteration's network and three containers, the proxy, the agent and the "
                    "oracle, and nothing else; nothing is started")
                say(f"  first, RALPH_EGRESS=proxy: the agent's internal network, and the proxy that opens a tunnel to "
                    f"{', '.join(EGRESS_ALLOW)} alone:")
                for cmd in proxy.up_commands():
                    say("    " + " ".join(cmd))
            else:
                say("ralph --dry-run: the two containers an iteration runs, and nothing else; nothing is started")
            say("  the agent: " + " ".join(agent.command(where / "workspace", where / "agent.env", name)))
            say("    its --env-file, 0600, deleted when the iteration ends: " + ", ".join(agent.env_values()) +
                " (values never printed)")
            if proxy:
                say("  then, whatever happened: the proxy's log, kept as iterations/01-egress.txt, and the proxy and "
                    "the network removed:")
                for cmd in proxy.down_commands():
                    say("    " + " ".join(cmd))
            say("  the oracle: " + " ".join(oracle.command(where / "oracle" / "01")[0]))
            return 0
    try:
        summary = run_loop(task, agent, oracle, max_iters=max_iters, budget_inr=budget, max_diff_lines=max_lines,
                           out=a.out, say=say)
    except Refused as e:
        say(f"ERROR: {e}")
        return 2
    return 0 if summary["stopped_by"] == "oracle_passed" else 1


def cmd_workspace(a, say=print) -> int:
    task = TASKS[a.task]
    try:
        run = new_run(task, a.out)
        build_workspace(run, Oracle("strong"))
    except Refused as e:
        say(f"ERROR: {e}")
        return 2
    say(f"ralph-workspace: task {task.name} ({task.title}), the workspace a loop starts from")
    say(f"  {run.ws}")
    say("  PROMPT.md, spec.md, fix_plan.md, GEMINI.md and oracle.md at its root; no oracle checks and no seeds in it; "
        f"its git repository beside it, with no remote: git --git-dir={run.git_dir} --work-tree={run.ws} log")
    say("  one iteration by hand: cd into it, run gemini in its default approval mode and ask it to follow PROMPT.md, "
        "approving or declining each edit and command; then make ralph-check WORKSPACE=<that path>")
    return 0


def _probe_line(n: int, what: str, status: str, detail: str = "", say=print) -> None:
    say(f"{n}. {what}: {status}" + (f" - {detail}" if detail else ""))


# What the probe runs inside the agent's container with RALPH_EGRESS=proxy, as the agent itself could: whether
# example.com's name resolves there, two connections straight out (example.com, and 169.254.169.254, where a cloud VM's
# metadata server answers), then two CONNECTs through HTTPS_PROXY, to example.com and to the model endpoint. Nothing is
# sent through a tunnel it opens. Docker gets it as one line, exec() of the source, so no wrapper splits it.
REACH_SOURCE = f"""import os, socket
def resolves(host):
    try:
        socket.getaddrinfo(host, 443)
        return "resolved"
    except OSError:
        return "did not resolve"
def direct(host, port):
    try:
        socket.create_connection((host, port), 5).close()
        return "CONNECTED"
    except OSError as e:
        return type(e).__name__ + ": " + str(e)
def via(target):
    try:
        host, port = os.environ["HTTPS_PROXY"].split("//")[-1].rstrip("/").rsplit(":", 1)
        with socket.create_connection((host, int(port)), 10) as s:
            s.sendall(("CONNECT " + target + " HTTP/1.1" + chr(13) + chr(10) + chr(13) + chr(10)).encode())
            return s.recv(256).decode("latin-1").split(chr(13))[0]
    except (OSError, KeyError, ValueError) as e:
        return type(e).__name__ + ": " + str(e)
print("NAME example.com", resolves("example.com"))
print("DIRECT example.com:443", direct("example.com", 443))
print("DIRECT 169.254.169.254:80", direct("169.254.169.254", 80))
print("PROXY example.com:443", via("example.com:443"))
print("PROXY {EGRESS_ALLOW[0]}", via("{EGRESS_ALLOW[0]}"))
"""
REACH = f"exec({REACH_SOURCE!r})"


def _probe_reach(reach: subprocess.CompletedProcess, seen: dict, say=print) -> None:
    """Checks 5 to 7 with RALPH_EGRESS=proxy, from REACH's lines and the proxy's log."""
    got = {}
    for line in (reach.stdout or "").splitlines():
        kind, _, rest = line.partition(" ")
        what, _, result = rest.partition(" ")
        if kind in ("NAME", "DIRECT", "PROXY"):
            got[(kind, what)] = result
    if not got:
        _probe_line(5, "what the agent's container reaches", "not tested", _tail(reach) or f"exit {reach.returncode}",
                    say)
        return
    straight = ("example.com:443", "169.254.169.254:80")
    reached = [t for t in straight if got.get(("DIRECT", t)) == "CONNECTED"]
    _probe_line(5, "the agent's container reaches example.com and 169.254.169.254 directly",
                f"REACHED {', '.join(reached)}, so it is not isolated" if reached else "refused, as it must be",
                f"example.com {got.get(('NAME', 'example.com'), '?')}; " +
                "; ".join(f"{t}: {got.get(('DIRECT', t), '?')}" for t in straight), say)
    status = got.get(("PROXY", "example.com:443"), "")
    _probe_line(6, "the egress proxy opens a tunnel to example.com:443", "OPENED, so the allowlist does not hold"
                if " 200 " in status else "refused, as it must be" if " 403 " in status else "not tested", status, say)
    status = got.get(("PROXY", EGRESS_ALLOW[0]), "")
    _probe_line(7, f"the egress proxy opens a tunnel to {EGRESS_ALLOW[0]}", "observed" if " 200 " in status
                else "refused", f"{status} (nothing sent through it, Rs 0)" if " 200 " in status else status, say)
    say(f"   the proxy's log: {egress_words(seen)}")


def cmd_probe(a, say=print) -> int:
    """The batch-1 probe (lesson 10.10's live facts), each fact observed, refused or not tested."""
    docker = shutil.which("docker")
    image = a.image or os.environ.get("RALPH_IMAGE") or IMAGE
    model = a.model or os.environ.get("RALPH_MODEL") or DEFAULT_MODEL
    try:
        egress = egress_mode(a.egress)
    except Refused as e:
        say(f"ERROR: {e}")
        return 2
    say(f"ralph-probe: Docker and Gemini CLI headless for the Ralph loop, image {image}, model {model}" +
        (", RALPH_EGRESS=proxy" if egress == "proxy" else ""))
    if not docker:
        _probe_line(1, "docker", "not tested", "docker is not on PATH", say)
        return 0
    v = subprocess.run([docker, "version", "--format", "{{.Server.Version}}"], capture_output=True, text=True)
    _probe_line(1, "docker's server", "observed" if v.returncode == 0 else "refused",
                (v.stdout or v.stderr).strip()[:200], say)
    label = subprocess.run([docker, "image", "inspect", "--format", '{{index .Config.Labels "documind.gemini-cli"}}',
                            image], capture_output=True, text=True)
    if label.returncode:
        _probe_line(2, "the ralph image", "not tested", f"no image {image}: make ralph-image", say)
        return 0
    _probe_line(2, "the ralph image's Gemini CLI", "observed", f"version {label.stdout.strip()} (its label)", say)
    cmd = [docker, "run", "--rm", "--network", "none", image, "python3", "-c",
           "import socket; socket.create_connection(('example.com', 443), 5); print('CONNECTED')"]
    iso = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    reached = "CONNECTED" in iso.stdout
    _probe_line(3, "the oracle's container (--network none) reaches example.com", "REACHED, so it is not isolated"
                if reached else "refused, as it must be", (iso.stderr.strip().splitlines() or [""])[-1][:200], say)
    key = os.environ.get("RALPH_API_KEY")
    proxy = Egress(docker, image, "ralph-probe") if egress == "proxy" else None
    with tempfile.TemporaryDirectory(prefix="ralph-probe-") as tmp:
        t = Path(tmp)
        (t / "ws").mkdir()
        # What the agent's container holds, from inside it: its environment's names (never a value) and its mount
        # points, on the loop's own docker run line with a dummy key in the env file. No model call, Rs 0.
        held = GeminiCliAgent(docker, image, model, "probe-dummy-not-a-key", a.project)
        write_env_file(t / "agent.env", held.env_values())

        def line(name: str, run: tuple) -> list[str]:
            """The loop's own agent line for one probe container, held to the proxy when RALPH_EGRESS=proxy."""
            cmd = held.command(t / "ws", t / "agent.env", name, run=run)
            return held_to(cmd, proxy) if proxy else cmd

        seen = reach = None
        try:
            if proxy:
                try:
                    proxy.up()
                except (RuntimeError, OSError, subprocess.SubprocessError) as e:
                    _probe_line(4, "the egress proxy and its network", "refused", str(e)[:300], say)
                    return 0
            h = subprocess.run(line("ralph-probe-holds", (
                "sh", "-c", "env | cut -d= -f1 | sort; echo ---; cut -d' ' -f2 /proc/mounts | sort")),
                capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=120)
            if proxy:                       # checks 5 to 7: free, no key, no model call
                reach = subprocess.run(line("ralph-probe-reach", ("python3", "-I", "-c", REACH)), capture_output=True,
                                       text=True, encoding="utf-8", errors="replace", timeout=120)
        finally:
            (t / "agent.env").unlink(missing_ok=True)
            if proxy:
                seen = proxy.down()
        names, _, mounts = h.stdout.partition("---")
        names, mounts = names.split(), mounts.split()
        bad = [n for n in names if n in ("GOOGLE_APPLICATION_CREDENTIALS", "CLOUDSDK_CONFIG", "GOOGLE_CLOUD_QUOTA_PROJECT")]
        bad += [m for m in mounts if "gcloud" in m or "docker.sock" in m or ".config" in m]
        _probe_line(4, "what the agent's container holds", ("REFUSED: it holds " + ", ".join(bad)) if bad else
                    "observed" if h.returncode == 0 else "not tested", f"env names {names}; mounts {mounts}"
                    if h.returncode == 0 else (h.stderr.strip().splitlines() or [""])[-1][:200], say)
        if proxy:
            _probe_reach(reach, seen, say)
        first = 8 if proxy else 5           # the two calls' numbers: after the proxy's checks when it is on
        if not a.yes:
            _probe_line(first, "one headless call", "not tested", "add YES=1 (two model calls, a few rupees)", say)
            return 0
        if key_problem(key):
            _probe_line(first, "one headless call", "not tested", key_problem(key), say)
            return 0
        agent = (EgressAgent if proxy else GeminiCliAgent)(docker, image, model, key, a.project, timeout_s=300)
        for n, words in ((first, "Reply with the single word OK. Use no tools."),
                         (first + 1, "Fetch https://example.com with a web tool and give its title. If you have no "
                                     "web tool, reply with the single word NO-WEB-TOOL and nothing else.")):
            _write(t / f"prompt{n}.md", words)
            (t / f"ws{n}").mkdir()
            try:
                r = agent.call(t / f"ws{n}", t / "agent.env", f"ralph-probe-{n}", prompt=t / f"prompt{n}.md")
            except RuntimeError as e:                   # the egress proxy did not start for this call
                _probe_line(n, "one headless call" if n == first else "the web tools excluded", "not tested", str(e),
                            say)
                continue
            out = parse_cli_json(r.log.split("\n--- stderr ---\n")[0]) or {}
            stats = out.get("stats") or {}
            if n == first:
                _probe_line(n, "one headless call", "observed" if r.inr is not None else "refused",
                            f"response {str(out.get('response'))[:80]!r}; models {sorted((stats.get('models') or {}))}; "
                            f"tokens {r.tokens}; {_rs(r.inr)}; error {r.error}", say)
                say("   its stats, as Gemini CLI printed them: " + json.dumps(stats)[:2000])
            else:
                tools = ((stats.get("tools") or {}).get("byName") or {})
                web = [k for k in tools if "web" in k.lower() or "fetch" in k.lower()]
                _probe_line(n, "the web tools excluded", "observed" if not web else "REFUSED: a web tool ran",
                            f"response {str(out.get('response'))[:80]!r}; tool calls {sorted(tools)}", say)
            if r.egress is not None:
                say(f"   the egress proxy on this call: {egress_words(r.egress)}")
    return 0


def main(argv=None, say=print) -> int:
    ap = argparse.ArgumentParser(description="A Ralph loop on statutory_deadline (workshop lesson 10.10).")
    sub = ap.add_subparsers(dest="cmd", required=True)
    loop = sub.add_parser("loop", help="the loop: --offline for the scripted agent, else Gemini CLI live")
    work = sub.add_parser("workspace", help="the workspace a loop starts from")
    chk = sub.add_parser("check", help="the oracles' verdicts: every seed, or a change of yours")
    probe = sub.add_parser("probe", help="the batch-1 probe: Docker and Gemini CLI headless")
    for p in (loop, work, chk):
        p.add_argument("--task", choices=sorted(TASKS), default="deadline")
    for p in (loop, work):
        p.add_argument("--out", help="the directory the run directory is made in (not inside the kit)")
    for p in (loop, probe):
        p.add_argument("--model", help=f"RALPH_MODEL, {DEFAULT_MODEL} unset")
        p.add_argument("--image", help=f"RALPH_IMAGE, {IMAGE} unset")
        p.add_argument("--project", help="adds GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=global to the agent's env")
        p.add_argument("--egress", choices=EGRESS_MODES, help="RALPH_EGRESS: proxy holds the agent's container to the "
                                                               "model endpoint; off, the default, leaves it as it was")
    loop.add_argument("--offline", action="store_true", help="the scripted agent: no model, no network, Rs 0")
    loop.add_argument("--dry-run", action="store_true", help="live: print the docker run lines, start nothing")
    loop.add_argument("--oracle", choices=("strong", "weak"), default="strong")
    loop.add_argument("--max-iters", type=int, help=f"RALPH_MAX_ITERS, {MAX_ITERS} unset")
    loop.add_argument("--budget-inr", type=float, help="RALPH_BUDGET_INR: required live")
    loop.add_argument("--max-diff-lines", type=int, help=f"RALPH_MAX_DIFF_LINES, {MAX_DIFF_LINES} unset")
    probe.add_argument("--yes", action="store_true", help="make the two model calls (a few rupees)")
    chk.add_argument("--patch", help="a patch of shared/desk_calc.py: against the task's start or the kit's file")
    chk.add_argument("--workspace", help="a workspace make ralph-workspace made, as you left it")
    chk.add_argument("--show", help="a version's patch and its failed checks")
    chk.add_argument("--write-patches", metavar="DIR", help="each version's patch from the task's start, into DIR")
    a = ap.parse_args(argv)
    if a.cmd == "check" and a.patch and a.workspace:
        ap.error("--patch or --workspace, not both")
    return {"loop": cmd_loop, "workspace": cmd_workspace, "check": cmd_check, "probe": cmd_probe}[a.cmd](a, say)


if __name__ == "__main__":
    sys.exit(main())
