#!/usr/bin/env python3
"""Production gotchas (the v5 course's Module 11, lesson 11.7): what a lane does in production that no eval row shows.

    python commands/gotchas.py list                                      make gotchas
    python commands/gotchas.py show ID                                   make gotchas ID=<id>
    python commands/gotchas.py drill [ID]                                make gotcha-drill [ID=<id>]
    python commands/gotchas.py drill ID --live --project <id> --region <region>
                                                                         make gotcha-drill ID=<id> LIVE=1 PROJECT=<id>
    python commands/gotchas.py detect [ID] --project <id> --region <region> [--hours 24]
                                                                         make gotcha-detect [ID=<id>] PROJECT=<id>

The registry is ops/gotchas.json, one entry per gotcha: the symptom production shows, why no eval row catches it, a
drill that reproduces it, a detector that finds it on a lane, the lever that fixes it, the lessons involved, the cost,
and the kit lines it rests on (evidence), each of which must still be in the kit word for word.

drill runs an entry's offline drill: Rs 0, no lane, no credential, no network. Most of them run on a stand-in of
Cloud Run, the JSON gcloud run services describe and gcloud run revisions describe print, changed by the gcloud and
make lines a lane would run. What those lines do is read from the kit (each deploy script's --set-env-vars list, the
Makefile's defaults and its candidate, release-candidate, promote, rollback and deploy-services recipes) and played
with Cloud Run's rules: --update-env-vars merges into the variables already there, --set-env-vars replaces every
literal one, a new revision takes traffic only when a traffic entry follows the latest revision, and --no-traffic
first binds what followed the latest to the revision that was latest. The others run the kit's own code: the chat's
Meter and its timed wrapper (services/chat/limits.py), and the event lists terraform/sql/tenant_daily.sql and
evals/usage_rows.py select. Each drill prints REPRODUCED with the registry's marker
and, where the entry shows its lever, CLEARED with its cleared line. With no ID, every offline drill runs. A drill that
no longer reproduces its gotcha exits 1: the kit changed, and the entry moves to fixed with the test that proves it.

drill --live runs the two drills that have a lane form, pinned-traffic and deploy-drops-hotfix, on documind-chat, with
the very gcloud lines the offline drill printed. Each refuses to start when the chat's traffic does not follow its
latest revision (limits-drill.sh's latest_takes_all) and puts every setting back from a finally block, so a failure
restores it too; deploy-drops-hotfix also refuses unless this checkout is at the commit the chat's image was built from
and the deploy would change nothing but the drill's own variable. Live drills are the author's, on a lane of their own.

detect reads the lane and changes nothing: gcloud run services describe and gcloud run revisions describe, gcloud
logging read, this checkout's deploy/.candidate-revision and deploy/.previous-revision, and, for
environment-without-reviewers, one GET through gh as make ci-vars makes it. With no ID, every detector runs.

Exit codes: 0 done (drill: reproduced, and cleared where the entry shows its lever; detect: nothing found); 1 drill:
the gotcha did not reproduce, detect: found; 2 stopped: a precondition, a tool or a read failed, and the message says
which.
"""
from __future__ import annotations

import argparse
import asyncio
import collections
import contextvars
import copy
import hashlib
import importlib.util
import json
import logging
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
import time
import types
from pathlib import Path
from typing import Callable, NamedTuple

HERE = Path(__file__).resolve().parent
KIT = HERE.parent                                   # the kit: deploy/ here, the repository root in the learner repo
REGISTRY = KIT / "ops" / "gotchas.json"
FOUND, STOPPED = 1, 2
CHAT, API = "documind-chat", "documind-api"
CAP = "CHAT_MAX_MODEL_CALLS"                        # the chat's call cap (services/chat/limits.py): the drills' variable
PROJECT_ID = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]")
PLACEHOLDER = "documind-ai-YOUR-ID"


class Stop(RuntimeError):
    """A precondition, a tool or a read failed. The message says which, and the command exits 2."""


class Changed(RuntimeError):
    """The kit no longer does what a drill rests on, so the drill cannot reproduce its gotcha: exit 1."""


class Refused(RuntimeError):
    """A make target refused, as its recipe does on a lane (the stand-in's make promote and make rollback)."""


def kit_text(rel: str) -> str:
    try:
        return (KIT / rel).read_text(encoding="utf-8")
    except OSError as e:
        raise Stop(f"cannot read the kit's {rel}: {e}") from e


def makefile() -> str:
    return kit_text("Makefile")


def count(n: int, thing: str) -> str:
    return f"{n} {thing}{'' if n == 1 else 's'}"


def cause(text: str) -> str:
    """The line of gcloud's error output that names the cause, else the first line."""
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return next((line for line in lines if line.startswith(("ERROR:", "Error:"))), lines[0] if lines else "no error output")


def _module(path: Path, name: str):
    """A kit file as a module of its own name, imported once (release.py and lane.py; the chat's limits.py)."""
    if name in sys.modules:
        return sys.modules[name]
    if str(KIT) not in sys.path:
        sys.path.insert(0, str(KIT))                # services/chat/limits.py imports shared.prices
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module                      # a dataclass resolves its own module while the class is built
    try:
        spec.loader.exec_module(module)
    except Exception:
        sys.modules.pop(name, None)
        raise
    return module


# ---------------------------------------------------------------- the registry (ops/gotchas.json)

SIGNALS, STATUSES, KINDS = ("loud", "silent"), ("open", "guarded", "fixed"), ("check", "log")
ID = re.compile(r"[a-z][a-z0-9]*(?:-[a-z0-9]+)+")
LESSON = re.compile(r"(?:B|[0-9]{1,2})\.[0-9]{1,2}")
ENTRY_KEYS = {"id", "title", "signal", "signal_by", "status", "fixed_by", "symptom", "why_no_eval", "drill", "detector",
              "lever", "lessons", "cost", "evidence"}
TEXT_KEYS = ("id", "title", "symptom", "why_no_eval", "lever", "cost")
OFFLINE_KEYS, LIVE_KEYS = {"how", "marker", "cleared"}, {"run", "changes", "restores", "cost"}
DETECTOR_KEYS = {"kind", "run", "reads", "finds", "pages", "filter", "count_if", "group_by"}


def _text(value) -> bool:
    return isinstance(value, str) and bool(value.strip())


def load(path: Path = REGISTRY) -> list[dict]:
    """The registry's entries, once they keep the registry's rules; a Stop naming the first problems otherwise."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Stop(f"cannot read the registry {path}: {e}") from e
    bad = problems(data)
    if bad:
        more = f" (and {len(bad) - 6} more)" if len(bad) > 6 else ""
        raise Stop(f"{path.name} breaks its rules: " + "; ".join(bad[:6]) + more)
    return data["gotchas"]


def problems(data) -> list[str]:
    """Every way the registry breaks its schema, or names a drill or a check this file does not run. The page's build
    and commands/tests/test_gotchas.py read the same rules; kit_problems() checks the kit behind each entry."""
    if not isinstance(data, dict) or not _text(data.get("note")) or not isinstance(data.get("gotchas"), list):
        return ["the registry is an object with a note and a list of gotchas"]
    out, seen = [], set()
    for i, g in enumerate(data["gotchas"]):
        if not isinstance(g, dict):
            out.append(f"entry {i} is not an object")
            continue
        gid = g["id"] if _text(g.get("id")) else f"entry {i}"
        found = [f"unknown field {key}" for key in sorted(set(g) - ENTRY_KEYS)]
        found += [f"{key} is missing or empty" for key in TEXT_KEYS if not _text(g.get(key))]
        if _text(g.get("id")):
            if not ID.fullmatch(g["id"]):
                found.append("the id is not lower-case words joined by hyphens")
            if g["id"] in seen:
                found.append("the id is not unique")
            seen.add(g["id"])
        if g.get("signal") not in SIGNALS:
            found.append(f"signal is one of {', '.join(SIGNALS)}")
        if (g.get("signal") == "loud") != _text(g.get("signal_by")):
            found.append("signal_by says what pages or goes red, on a loud gotcha and only there")
        if g.get("status") not in STATUSES:
            found.append(f"status is one of {', '.join(STATUSES)}")
        if (g.get("status") == "fixed") != _text(g.get("fixed_by")):
            found.append("fixed_by names the test that proves the fix, on a fixed gotcha and only there")
        if _text(g.get("cost")) and not g["cost"].startswith("Rs "):
            found.append("cost starts with Rs")
        lessons = g.get("lessons")
        if not (isinstance(lessons, list) and lessons and len(set(map(str, lessons))) == len(lessons)
                and all(isinstance(x, str) and LESSON.fullmatch(x) for x in lessons)):
            found.append("lessons is a list of the workshop's lesson numbers, dotted, each once")
        evidence = g.get("evidence")
        if not (isinstance(evidence, list) and evidence and all(isinstance(p, list) and len(p) == 2
                                                                and all(_text(x) for x in p) for p in evidence)):
            found.append("evidence is a list of [kit file, its exact text] pairs")
        found += _drill_problems(g) + _detector_problems(g)
        out += [f"{gid}: {why}" for why in found]
    return out


def _drill_problems(g: dict) -> list[str]:
    drill, gid = g.get("drill"), g.get("id")
    if not isinstance(drill, dict) or set(drill) != {"offline", "live"}:
        return ["drill has an offline and a live drill, either of them null"]
    offline, live, out = drill["offline"], drill["live"], []
    if offline is None and live is None:
        out.append("a gotcha needs a drill, offline or live")
    if offline is not None:
        if not (isinstance(offline, dict) and set(offline) == OFFLINE_KEYS and _text(offline.get("how"))
                and _text(offline.get("marker")) and (offline.get("cleared") is None or _text(offline["cleared"]))):
            out.append("drill.offline has how, marker and cleared (null when the drill shows no lever)")
        if gid not in DRILLS:
            out.append("drill.offline names a drill commands/gotchas.py does not run")
    elif gid in DRILLS:
        out.append("commands/gotchas.py runs an offline drill the registry does not list")
    if live is not None:
        if not (isinstance(live, dict) and set(live) == LIVE_KEYS and all(_text(live.get(k)) for k in LIVE_KEYS)):
            out.append("drill.live has run, changes, restores and cost")
        elif gid in LIVE_DRILLS and not live["run"].startswith(f"make gotcha-drill ID={gid} LIVE=1 PROJECT="):
            out.append(f"drill.live.run is the make gotcha-drill ID={gid} LIVE=1 line")
    if gid in LIVE_DRILLS and (live is None or offline is None):
        out.append("a drill with a lane form has its offline rehearsal and its live line both")
    return out


def _detector_problems(g: dict) -> list[str]:
    det, gid = g.get("detector"), g.get("id")
    if not isinstance(det, dict) or not set(det) <= DETECTOR_KEYS or det.get("kind") not in KINDS:
        return ["detector has a kind (check or log), run, reads, finds and pages"]
    out = [f"detector.{k} is missing or empty" for k in ("run", "reads", "finds") if not _text(det.get(k))]
    if not (det.get("pages") is None or _text(det.get("pages"))):
        out.append("detector.pages is an alert policy's display name, or null")
    if _text(det.get("run")) and not det["run"].startswith(f"make gotcha-detect ID={gid} PROJECT="):
        out.append(f"detector.run is the make gotcha-detect ID={gid} line")
    if det.get("kind") == "check":
        if gid not in CHECKS:
            out.append("detector.kind is check, and commands/gotchas.py has no check for this id")
        if set(det) & {"filter", "count_if", "group_by"}:
            out.append("a check takes no filter, count_if or group_by")
    else:
        if not _text(det.get("filter")):
            out.append("a log detector names its Cloud Logging filter")
        if "count_if" in det and not _text(det["count_if"]):
            out.append("detector.count_if is a field of the log entry")
        if "group_by" in det and not (isinstance(det["group_by"], list) and det["group_by"]
                                      and all(_text(f) for f in det["group_by"])):
            out.append("detector.group_by is a list of fields of the log entry")
        if gid in CHECKS:
            out.append("commands/gotchas.py has a check for this id, and the registry calls it a log detector")
    return out


def missing_evidence(entry: dict) -> list[str]:
    """The entry's evidence that is no longer in the kit, as 'file: text' lines."""
    out = []
    for rel, text in entry["evidence"]:
        path = KIT / rel
        if not path.is_file() or text not in path.read_text(encoding="utf-8"):
            out.append(f"{rel}: {text}")
    return out


def kit_problems(entries: list[dict]) -> list[str]:
    """What each entry names in the kit, checked against the kit: its evidence, word for word; the alert policy it
    says pages (a display_name in terraform/*.tf); the event its log filter reads (an "event": "<name>" the services
    or shared/ write)."""
    tf = "\n".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "terraform").glob("*.tf")))
    code = "\n".join(p.read_text(encoding="utf-8", errors="replace") for d in ("services", "shared")
                     for p in sorted((KIT / d).rglob("*.py")))
    out = []
    for g in entries:
        out += [f"{g['id']}: evidence no longer in the kit: {line}" for line in missing_evidence(g)]
        det = g["detector"]
        if det.get("pages") and f'display_name = "{det["pages"]}"' not in tf:
            out.append(f"{g['id']}: no alert policy in terraform/*.tf is called {det['pages']!r}")
        for event in re.findall(r'jsonPayload\.event="([a-z_]+)"', det.get("filter") or ""):
            if f'"event": "{event}"' not in code:
                out.append(f"{g['id']}: nothing in services/ or shared/ writes the event {event!r} its filter reads")
    return out


# ---------------------------------------------------------------- what make deploy-services writes (the deploy scripts)

DEPLOY, MARKER = re.compile(r"^# ---- DEPLOY ----"), re.compile(r"^# ---- [A-Z_]* ----$")
ADDRESS = ("PROJECT", "REGION", "GIT_SHA", "PROJECT_NUMBER")   # where the lane is, which every deploy is given
LANE, KNOB = "\x00", "\x01"     # a value only the lane knows; a value a variable of yours decides
REF = re.compile(r"\$\{?([A-Za-z_][A-Za-z0-9_]*)")


class Change(NamedTuple):
    name: str
    line: str


def deploy_block(text: str) -> str:
    """What make deploy-services hands to sh -ec: sed's range from the DEPLOY marker through the next marker line, then
    every line that starts '# ----' dropped (commands/tests/test_deploy_scripts.py holds the same cut to sed)."""
    kept, inside = [], False
    for line in text.splitlines():
        if inside:
            kept.append(line)
            inside = not MARKER.search(line)
        elif DEPLOY.search(line):
            kept.append(line)
            inside = True
    return "\n".join(line for line in kept if not line.startswith("# ----"))


def shell_commands(block: str) -> list[str]:
    """A block's commands as sh reads them: comment lines dropped, continuation lines joined."""
    code = "\n".join(line for line in block.splitlines() if not line.lstrip().startswith("#"))
    return [line.strip() for line in code.replace("\\\n", " ").splitlines() if line.strip()]


def recipe(mk: str, target: str) -> str:
    """A target's recipe from its rule line to the next blank line, continuation lines joined."""
    m = re.search(r"^" + re.escape(target) + r":[^\n]*\n(.*?)(?:\n\n|\Z)", mk, re.M | re.S)
    if not m:
        raise Changed(f"the Makefile has no {target} target")
    return m.group(1).replace("\\\n", " ")


def make_default(mk: str, name: str) -> str | None:
    """NAME's default in the Makefile (NAME ?= value) when it is a literal; None when there is none or it is computed."""
    m = re.search(r"^" + re.escape(name) + r"[ \t]*\?=[ \t]*(.*)$", mk, re.M)
    return m.group(1).strip() if m and "$" not in m.group(1) else None


def default_scripts(mk: str) -> list[str]:
    m = re.search(r"^SCRIPTS\s*=\s*((?:.*\\\n)*.*)$", mk, re.M)
    if not m:
        raise Changed("the Makefile no longer lists the deploy scripts (SCRIPTS =)")
    return re.findall(r"commands/[\w.-]+\.sh", m.group(1))


def deploy_passes(mk: str) -> dict[str, tuple[str, str | None]]:
    """name -> how make deploy-services sets it for each deploy script: ('make', the Makefile's literal default) for
    NAME=$(NAME); ('recipe', the literal) for a shell variable the recipe sets to a literal (RETRIEVAL_BACKEND=vector,
    and CHAT_EXTRA_ENV empty); ('lane', None) for the lane's address, terraform output and anything computed."""
    body = recipe(mk, "deploy-services")
    start, end = body.find("(DEPLOY block)"), body.find("sh -ec")
    if start < 0 or end < start:
        raise Changed("make deploy-services no longer hands each script's DEPLOY block to sh -ec")
    literals = dict(re.findall(r"(?:^|[;\s])([A-Z][A-Z0-9_]*)=([^;\s$\"'`]*);", body[:start]))
    out = {}
    for name, value in re.findall(r"\b([A-Z][A-Z0-9_]*)=(\"[^\"]*\"|\S*)", body[start:end]):
        value = value.strip('"')
        if name in ADDRESS:
            out[name] = ("lane", None)
        elif value == f"$({name})" and make_default(mk, name) is not None:
            out[name] = ("make", make_default(mk, name))
        elif value == f"$${name}" and name in literals:
            out[name] = ("recipe", literals[name])
        else:
            out[name] = ("lane", None)
    return out


def expand(text: str, env: dict) -> str:
    """sh's parameter expansion, for the forms the deploy scripts use: $X, ${X}, ${X-word}, ${X:-word}, ${X+word} and
    ${X:+word}, the word expanded in turn. A name missing from env is unset; '' is set and empty."""
    out, i, n = [], 0, len(text)
    while i < n:
        c = text[i]
        if c != "$" or i + 1 >= n:
            out.append(c)
            i += 1
            continue
        if text[i + 1] == "{":
            depth, j = 1, i + 2
            while j < n and depth:
                depth += {"{": 1, "}": -1}.get(text[j], 0)
                j += 1
            m = re.fullmatch(r"([A-Za-z_][A-Za-z0-9_]*)(?:(:?[-+])(.*))?", text[i + 2:j - 1], re.S)
            if not m:
                raise Changed(f"a deploy script uses a parameter expansion this reader does not know: {text[i:j]}")
            name, op, word = m.groups()
            value = env.get(name)
            if op is None:
                out.append(value or "")
            elif op == "-":
                out.append(value if value is not None else expand(word, env))
            elif op == ":-":
                out.append(value if value else expand(word, env))
            elif op == "+":
                out.append(expand(word, env) if value is not None else "")
            else:
                out.append(expand(word, env) if value else "")
            i = j
            continue
        m = re.match(r"[A-Za-z_][A-Za-z0-9_]*", text[i + 1:])
        if m:
            out.append(env.get(m.group(0)) or "")
            i += 1 + m.end()
            continue
        out.append(c)
        i += 1
    return "".join(out)


def split_spec(spec: str) -> list[tuple[str, str]]:
    """gcloud's dictionary flag: KEY=VALUE,KEY=VALUE, or ^D^KEY=VALUEDKEY=VALUE with its own delimiter D."""
    delim = ","
    if spec.startswith("^"):
        end = spec.find("^", 1)
        if end < 0:
            raise Changed(f"an environment list with an unclosed delimiter: {spec[:40]}")
        delim, spec = spec[1:end], spec[end + 1:]
    pairs = []
    for item in spec.split(delim):
        if item:
            name, eq, value = item.partition("=")
            if not eq:
                raise Changed(f"an environment entry with no '=': {item[:40]}")
            pairs.append((name, value))
    return pairs


def _knob(value: str) -> str | None:
    m = re.fullmatch(KNOB + r"([A-Za-z_][A-Za-z0-9_]*)" + KNOB, value or "")
    return m.group(1) if m else None


class DeploySpec:
    """One service's deploy as make deploy-services runs it: the script, its gcloud run deploy line and what that
    line's --set-env-vars writes, given what the recipe passes (deploy_passes)."""

    def __init__(self, service: str, script: str, command: str, passes: dict):
        self.service, self.script, self.command, self.passes = service, script, command, passes
        m = re.search(r"--set-env-vars[= ](\"(?:[^\"\\]|\\.)*\"|\S+)", command)
        if not m:
            raise Changed(f"{script} deploys {service} without --set-env-vars")
        self.spec = m.group(1)[1:-1] if m.group(1).startswith('"') else m.group(1)
        image = re.search(r"--image[= ](\S+)", command)
        self.image = image.group(1) if image else ""
        self.names = set(REF.findall(self.spec)) | set(REF.findall(self.image))
        self.hooks = sorted(n for n in self.names if passes.get(n) == ("recipe", ""))

    def _env(self, knobs: bool, overrides: dict | None, lane: dict | None) -> dict:
        env = {}
        for name in self.names:
            how, value = self.passes.get(name, ("env", None))
            if overrides and name in overrides:
                env[name] = overrides[name]
            elif how == "recipe" or (how == "make" and not knobs):
                env[name] = value
            elif how == "make" or (how == "env" and knobs):
                env[name] = KNOB + name + KNOB
            elif how == "lane":
                env[name] = lane.get(name, name) if lane is not None else LANE + name + LANE
        return env

    def writes(self, overrides: dict | None = None, lane: dict | None = None) -> dict[str, str]:
        """What the deploy writes when nobody passes a variable: the Makefile's defaults, the recipe's literals, and
        the lane's values (a LANE marker in each, unless lane gives them)."""
        return dict(split_spec(expand(self.spec, self._env(False, overrides, lane))))

    def could(self, overrides: dict | None = None) -> dict[str, str]:
        """The same with each variable a person may pass made a KNOB: which variable decides each entry."""
        return dict(split_spec(expand(self.spec, self._env(True, overrides, None))))

    def image_for(self, lane: dict) -> str:
        return expand(self.image, self._env(False, None, lane))

    def changes(self, live: dict[str, str], overrides: dict | None = None) -> list[Change]:
        """What the next make deploy-services does to the service's literal variables: drops those its list does not
        name, writes back those it names, and adds back those a variable of yours decides only when you pass it."""
        writes, could, out = self.writes(overrides), self.could(overrides), []
        hooks = [h for h in self.hooks if not (overrides or {}).get(h)]
        for name, value in live.items():
            if name in writes:
                wrote = writes[name]
                if LANE in wrote or wrote == value:
                    continue
                knob = _knob(could.get(name, ""))
                how = f", the default, unless you pass {knob}={value}" if knob else "; no variable of yours changes that"
                out.append(Change(name, f"{name}={value}: written back as {name}={wrote}{how}"))
            elif name in could:
                knob = _knob(could[name]) or "the variable it names"
                out.append(Change(name, f"{name}={value}: dropped unless you pass {knob}={value}"))
            else:
                note = f"; make deploy-services empties {', '.join(hooks)}, the script's hook for more" if hooks else ""
                out.append(Change(name, f"{name}={value}: dropped, not in {self.script}'s --set-env-vars{note}"))
        return out


def deploy_specs() -> dict[str, DeploySpec]:
    """service -> its DeploySpec, for every script make deploy-services runs by default, in the Makefile's order."""
    mk = makefile()
    passes, out = deploy_passes(mk), {}
    for script in default_scripts(mk):
        for command in shell_commands(deploy_block(kit_text(script))):
            m = re.match(r"gcloud run deploy (\S+)", command)
            if m:
                out[m.group(1)] = DeploySpec(m.group(1), script, command, passes)
    if CHAT not in out or API not in out:
        raise Changed(f"make deploy-services' scripts no longer deploy {CHAT} and {API}")
    return out


def candidate_names(mk: str) -> list[str]:
    """The switches make candidate sets on its candidate, each from the make variable of its name."""
    m = re.search(r'--update-env-vars "\^\|\^(.*?)\$\(if', recipe(mk, "candidate"))
    names = re.findall(r"([A-Z][A-Z0-9_]*)=\$\(\1\)", m.group(1)) if m else []
    if "GENERATOR_MODEL" not in names:
        raise Changed("make candidate no longer sets GENERATOR_MODEL with --update-env-vars")
    return names


def chat_cap_default() -> int:
    m = re.search(r'os\.environ\.get\("' + CAP + r'", "(\d+)"\)', kit_text("services/chat/limits.py"))
    if not m:
        raise Changed(f"services/chat/limits.py no longer reads {CAP} with a default")
    return int(m.group(1))


# ---------------------------------------------------------------- Cloud Run, as gcloud describes it

def _json(text: str, what: str):
    try:
        return json.loads(text or "null")
    except ValueError:
        raise Stop(f"{what} did not return JSON") from None


def describe(lane, service: str) -> dict:
    data = _json(lane.gcloud("run", "services", "describe", service, *lane.where(), "--format=json"),
                 f"gcloud run services describe {service}")
    if not isinstance(data, dict):
        raise Stop(f"gcloud run services describe {service} did not return a service")
    return data


def revision(lane, name: str) -> dict:
    data = _json(lane.gcloud("run", "revisions", "describe", name, *lane.where(), "--format=json"),
                 f"gcloud run revisions describe {name}")
    if not isinstance(data, dict):
        raise Stop(f"gcloud run revisions describe {name} did not return a revision")
    return data


def template(desc: dict) -> dict:
    """The service's template: what the next revision is made from (image and environment)."""
    c = (((desc.get("spec") or {}).get("template") or {}).get("spec") or {}).get("containers") or [{}]
    return {"image": c[0].get("image", ""), "env": c[0].get("env") or []}


def revision_template(rev: dict) -> dict:
    c = (rev.get("spec") or {}).get("containers") or [{}]
    return {"image": c[0].get("image", ""), "env": c[0].get("env") or []}


def template_image(lane, desc: dict) -> str:
    """The template's image as the revision it made holds it. The template keeps the tag a deploy gave it, and each
    revision the digest Cloud Run resolved that tag to, so a tag never equals a revision's image: on 22 October 2026
    lesson 11.6's undone candidate read as a change no request reaches, tag against digest."""
    latest = latest_created(desc)
    return revision_template(revision(lane, latest))["image"] if latest else template(desc)["image"]


def literal_env(env: list) -> dict[str, str]:
    """name -> value of the literal variables; a secret's reference (valueFrom) is --set-secrets', not ours."""
    return {e["name"]: e.get("value", "") for e in env if isinstance(e, dict) and "name" in e and "valueFrom" not in e}


def traffic(desc: dict) -> list[dict]:
    return [t for t in ((desc.get("status") or {}).get("traffic") or []) if isinstance(t, dict)]


def follows_latest(desc: dict) -> bool:
    """The latest revision takes all the traffic: limits-drill.sh's latest_takes_all, on the same JSON."""
    return any(t.get("latestRevision") and t.get("percent") == 100 for t in traffic(desc))


def serving(desc: dict) -> dict[str, int]:
    out: dict[str, int] = {}
    for t in traffic(desc):
        if t.get("percent") and t.get("revisionName"):
            out[t["revisionName"]] = out.get(t["revisionName"], 0) + int(t["percent"])
    return out


def serving_revision(desc: dict) -> str | None:
    """The one revision that takes 100% of the traffic, or None when it is split."""
    whole = [name for name, pct in serving(desc).items() if pct == 100]
    return whole[0] if whole else None


def tagged(desc: dict, tag: str) -> str | None:
    return next((t.get("revisionName") for t in traffic(desc) if t.get("tag") == tag), None)


def latest_created(desc: dict) -> str | None:
    return (desc.get("status") or {}).get("latestCreatedRevisionName")


def percent_of(desc: dict, name: str) -> int:
    return serving(desc).get(name, 0)


def env_diff(before: dict, after: dict) -> dict[str, tuple]:
    return {n: (before.get(n), after.get(n)) for n in sorted(set(before) | set(after)) if before.get(n) != after.get(n)}


def shown(value) -> str:
    return "unset" if value is None else value


# ---------------------------------------------------------------- the stand-in: Cloud Run with no lane

class StandIn:
    """Cloud Run and this checkout with no lane: each service a list of revisions, a traffic spec and a template, shown
    as gcloud describes them, and changed only by the gcloud lines a lane would run (gcloud() below interprets them)
    and by make's targets played from the kit's own recipes. Every line run is kept in .calls."""

    offline = True
    SUFFIX = ("kav", "mup", "zeq", "rix", "lod", "fen", "tob", "wyc", "gan", "hes", "pid", "sov", "nar", "bex")

    def __init__(self, project: str = PLACEHOLDER, region: str = "us-central1"):
        self.project, self.region = project, region
        self.services: dict[str, dict] = {}
        self.files: dict[str, str] = {}      # this checkout's deploy/.candidate-revision and deploy/.previous-revision
        self.calls: list[str] = []
        self.fail_on: str | None = None      # a test's failure, once: the first gcloud or make line holding this text
        self.log_rows: dict[str, list] = {}  # a test's log rows, keyed by a text the filter holds

    def where(self) -> tuple[str, str]:
        return f"--region={self.region}", f"--project={self.project}"

    def _fail(self, line: str) -> None:
        if self.fail_on and self.fail_on in line:
            self.fail_on = None
            raise Stop(f"{line[:60]} failed (exit 1): ERROR: (stand-in) a failure the test asked for")

    # ---- gcloud, the lines the drills and detectors run
    def gcloud(self, *args: str) -> str:
        line = "gcloud " + " ".join(args)
        self.calls.append(line)
        self._fail(line)
        pos, flags = [], {}
        for a in args:
            if a.startswith("--"):
                key, eq, value = a[2:].partition("=")
                flags[key] = value if eq else True
            else:
                pos.append(a)
        if pos[:2] == ["logging", "read"]:
            return json.dumps(next((rows for key, rows in self.log_rows.items() if key in pos[2]), []))
        if pos[:1] != ["run"] or flags.get("region") != self.region or flags.get("project") != self.project:
            raise Stop(f"the stand-in answers gcloud run lines for {self.project} in {self.region}: {line}")
        what, name = pos[1:3], pos[3] if len(pos) > 3 else ""
        if what == ["services", "describe"]:
            return json.dumps(self.describe_json(name))
        if what == ["revisions", "describe"]:
            return json.dumps(self.revision_json(name))
        if what == ["services", "update"]:
            self._update(name, flags)
            return ""
        if what == ["services", "update-traffic"]:
            self._traffic(name, flags)
            return ""
        raise Stop(f"the stand-in does not answer: {line}")

    def _service(self, name: str) -> dict:
        if name not in self.services:
            raise Stop(f"gcloud run services describe {name} failed (exit 1): ERROR: (gcloud.run.services.describe) "
                       f"Cannot find service [{name}]")
        return self.services[name]

    def describe_json(self, name: str) -> dict:
        s = self._service(name)
        latest = s["order"][-1]
        made = s["revisions"][latest]
        resolved = []
        for t in s["traffic"]:
            if t.get("latestRevision"):
                resolved.append({"latestRevision": True, "percent": t["percent"], "revisionName": latest})
            elif t.get("tag"):
                resolved.append({"revisionName": t["revisionName"], "tag": t["tag"],
                                 "url": f"https://{t['tag']}---{name}-NUMBER.{self.region}.run.app"})
            else:
                resolved.append({"revisionName": t["revisionName"], "percent": t["percent"]})
        return {"apiVersion": "serving.knative.dev/v1", "kind": "Service",
                "metadata": {"name": name, "namespace": "NUMBER", "generation": len(s["order"]),
                             "labels": {"cloud.googleapis.com/location": self.region}},
                "spec": {"template": {"spec": {"containers": [{"image": made["image"],
                                                               "env": copy.deepcopy(made["env"])}]}},
                         "traffic": copy.deepcopy(s["traffic"])},
                "status": {"observedGeneration": len(s["order"]), "conditions": [{"type": "Ready", "status": "True"}],
                           "latestCreatedRevisionName": latest, "latestReadyRevisionName": latest,
                           "url": f"https://{name}-NUMBER.{self.region}.run.app", "traffic": resolved}}

    def revision_json(self, name: str) -> dict:
        service = next((s for s, st in self.services.items() if name in st["revisions"]), None)
        if service is None:
            raise Stop(f"gcloud run revisions describe {name} failed (exit 1): ERROR: (gcloud.run.revisions.describe) "
                       f"Revision [{name}] could not be found.")
        made = self.services[service]["revisions"][name]
        # A revision holds the digest its image's tag named when it was made, as Cloud Run writes it; the template keeps
        # the tag. The stand-in's digest is the reference's own sha256.
        digest = made["image"].rpartition(":")[0] + "@sha256:" + hashlib.sha256(made["image"].encode()).hexdigest()
        return {"apiVersion": "serving.knative.dev/v1", "kind": "Revision",
                "metadata": {"name": name, "labels": {"serving.knative.dev/service": service}},
                "spec": {"containers": [{"image": digest, "env": copy.deepcopy(made["env"])}]},
                "status": {"imageDigest": digest, "conditions": [{"type": "Ready", "status": "True"}]}}

    def _revision(self, name: str, image: str, env: list, no_traffic: bool = False, tag: str | None = None) -> str:
        s = self.services.setdefault(name, {"revisions": {}, "order": [], "n": 0,
                                            "traffic": [{"latestRevision": True, "percent": 100}]})
        before = s["order"][-1] if s["order"] else None
        s["n"] += 1
        rev = f"{name}-{s['n']:05d}-{self.SUFFIX[s['n'] % len(self.SUFFIX)]}"
        s["revisions"][rev] = {"image": image, "env": env}
        s["order"].append(rev)
        if no_traffic and before:       # gcloud: what followed the latest is bound to the revision that was latest
            for t in s["traffic"]:
                if t.pop("latestRevision", None):
                    t["revisionName"] = before
        if tag:                         # a tag names one revision: it moves to the new one
            s["traffic"] = [t for t in s["traffic"] if t.get("tag") != tag] + [{"revisionName": rev, "tag": tag}]
        return rev

    def _update(self, name: str, flags: dict) -> None:
        s = self._service(name)
        made = s["revisions"][s["order"][-1]]
        env = {e["name"]: dict(e) for e in made["env"]}
        for key, value in split_spec(flags.get("update-env-vars") or ""):       # --update-env-vars merges
            env[key] = {"name": key, "value": value}
        for key in [k for k in str(flags.get("remove-env-vars") or "").split(",") if k]:
            env.pop(key, None)
        self._revision(name, flags.get("image") or made["image"], list(env.values()),
                       no_traffic=bool(flags.get("no-traffic")), tag=flags.get("tag") or None)

    def _traffic(self, name: str, flags: dict) -> None:
        s = self._service(name)
        tags = [t for t in s["traffic"] if t.get("tag")]
        if flags.get("to-latest"):
            s["traffic"] = [{"latestRevision": True, "percent": 100}] + tags
        if flags.get("to-revisions"):
            rev, _, pct = str(flags["to-revisions"]).partition("=")
            if rev not in s["revisions"] or pct != "100":
                raise Stop(f"the stand-in moves 100% of the traffic to one revision of {name}: {flags['to-revisions']}")
            s["traffic"] = [{"revisionName": rev, "percent": 100}] + tags
        if flags.get("remove-tags"):
            drop = str(flags["remove-tags"]).split(",")
            s["traffic"] = [t for t in s["traffic"] if t.get("tag") not in drop]

    # ---- what a lane gives the drills besides gcloud
    def limits(self, service: str) -> dict:
        """/health's limits, as the revision that answers publishes them: its CHAT_MAX_MODEL_CALLS, or the default."""
        desc = self.describe_json(service)
        answering = serving_revision(desc)
        if answering is None:
            raise Stop(f"{service}'s traffic is split: /health would answer from more than one revision")
        env = literal_env(self.services[service]["revisions"][answering]["env"])
        return {"max_model_calls": int(env.get(CAP, chat_cap_default()))}

    def lane_values(self, git_sha: str) -> dict:
        """The values the lane gives a deploy (its address, terraform output), as placeholders."""
        return {"PROJECT": self.project, "REGION": self.region, "GIT_SHA": git_sha, "PROJECT_NUMBER": "NUMBER",
                "DOCAI_LOCATION": "us", "BATCH_JOB_NAME": "", "RETENTION_DAYS": "30",
                "EMBEDDING_MODEL": "text-embedding-005", "EMBEDDING_VERSION": "1",
                "BQ_CHUNK_TABLE": f"{self.project}.rag_data.chunk_source",
                "CHAT_URL": f"https://documind-chat-NUMBER.{self.region}.run.app"}

    def deploy_services(self, scripts: list[str], git_sha: str, extra: dict | None = None) -> None:
        """make deploy-services SCRIPTS=... GIT_SHA=...: each script's gcloud run deploy with its --set-env-vars list
        as the recipe passes it (extra: a recipe variable a fork sets, CHAT_EXTRA_ENV), then, when lesson-12.2.sh ran,
        the recipe's own move of documind-api's traffic to the revision it made, by name (F44)."""
        mk = makefile()
        self.calls.append(f"make deploy-services SCRIPTS={' '.join(scripts)} GIT_SHA={git_sha}"
                          + "".join(f" ({k}={v!r} in this fork's recipe)" for k, v in (extra or {}).items()))
        self._fail(self.calls[-1])
        specs = {spec.script: spec for spec in deploy_specs().values()}
        lane = self.lane_values(git_sha)
        for script in scripts:
            spec = specs.get(script)
            if spec is None:
                raise Stop(f"the stand-in deploys the scripts make deploy-services runs by default, not {script}")
            pairs = spec.writes(extra, lane)
            image = spec.image_for(lane)
            old = self.services.get(spec.service)
            secrets = ([e for e in old["revisions"][old["order"][-1]]["env"] if "valueFrom" in e] if old
                       else [{"name": n, "valueFrom": {"secretKeyRef": {"name": s, "key": "latest"}}}
                             for n, s in re.findall(r"--set-secrets=([A-Z_]+)=([\w-]+):latest", spec.command)])
            self.calls.append(f"gcloud run deploy {spec.service} --image={image} --set-env-vars=<{spec.script}'s list, "
                              f"{count(len(pairs), 'variable')}>")
            self._revision(spec.service, image, [{"name": k, "value": v} for k, v in pairs.items()] + secrets)
        moves = '@if echo "$(SCRIPTS)" | grep -q lesson-12.2.sh; then' in mk      # the recipe's step after the API
        if moves and any(s.endswith("lesson-12.2.sh") for s in scripts):
            made = latest_created(describe(self, API))
            self.gcloud("run", "services", "update-traffic", API, *self.where(), f"--to-revisions={made}=100", "--quiet")

    def _record(self, files: dict) -> None:
        """make record-candidate: the revision the update just made, by name, into deploy/.candidate-revision."""
        files[".candidate-revision"] = latest_created(describe(self, API))

    def make_candidate(self, files: dict | None = None, **given: str) -> None:
        """make candidate NAME=value ...: the API's switches on a no-traffic revision tagged candidate, each at the
        Makefile's default unless given; GENERATOR_LOCATION removed unless given (F43)."""
        mk = makefile()
        pairs = [f"{n}={given.get(n, make_default(mk, n) or '')}" for n in candidate_names(mk)]
        if given.get("GENERATOR_LOCATION"):
            pairs.append(f"GENERATOR_LOCATION={given['GENERATOR_LOCATION']}")
        self.calls.append("make candidate " + " ".join(f"{k}={v}" for k, v in given.items()))
        self.gcloud("run", "services", "update", API, *self.where(), "--no-traffic", "--tag=candidate",
                    "--update-env-vars=^|^" + "|".join(pairs),
                    *([] if given.get("GENERATOR_LOCATION") else ["--remove-env-vars=GENERATOR_LOCATION"]), "--quiet")
        self._record(self.files if files is None else files)

    def make_release_candidate(self, git_sha: str, files: dict | None = None) -> None:
        """make release-candidate GIT_SHA=...: the image flipped on a no-traffic revision tagged candidate, with GIT_SHA."""
        self.calls.append(f"make release-candidate GIT_SHA={git_sha}")
        self.gcloud("run", "services", "update", API, *self.where(),
                    f"--image={self.region}-docker.pkg.dev/{self.project}/documind/api:{git_sha}", "--no-traffic",
                    "--tag=candidate", f"--update-env-vars=GIT_SHA={git_sha}", "--quiet")
        self._record(self.files if files is None else files)

    def make_promote(self, files: dict | None = None) -> None:
        """make promote: traffic to deploy/.candidate-revision by name, the revision serving before into
        deploy/.previous-revision; refused when the candidate tag has moved on."""
        files = self.files if files is None else files
        self.calls.append("make promote")
        cand = files.get(".candidate-revision")
        if not cand:
            raise Refused("ERROR: deploy/.candidate-revision is missing")
        desc = describe(self, API)
        before, on_tag = serving_revision(desc), tagged(desc, "candidate")
        if on_tag and on_tag != cand:
            raise Refused(f"ERROR: the candidate tag is on {on_tag} but deploy/.candidate-revision names {cand}")
        if before == cand:
            return
        if before:
            files[".previous-revision"] = before
        self.gcloud("run", "services", "update-traffic", API, *self.where(), f"--to-revisions={cand}=100", "--quiet")

    def make_rollback(self, files: dict | None = None) -> None:
        """make rollback: traffic back to deploy/.previous-revision by name; the recipe's own refusal without it."""
        files = self.files if files is None else files
        self.calls.append("make rollback")
        prev = files.get(".previous-revision")
        if not prev:
            m = re.search(r"ERROR: (deploy/\.previous-revision is missing[^.]*\.)", recipe(makefile(), "rollback"))
            if not m:
                raise Changed("make rollback no longer refuses without deploy/.previous-revision")
            raise Refused("ERROR: " + m.group(1))
        self.gcloud("run", "services", "update-traffic", API, *self.where(), f"--to-revisions={prev}=100", "--quiet")

    def recorded(self, name: str) -> str | None:
        return self.files.get(name)

    def require_checkout(self, tag: str) -> None:
        """A lane's routine deploy rebuilds the image from the checkout; the stand-in's checkout is that commit."""

    def require_admin(self) -> None:
        """make deploy-services' make operators needs ADMIN_EMAILS on a lane; the stand-in grants nothing."""

    def logs(self, flt: str, hours: int, limit: int = 1000) -> list:
        return _json(self.gcloud("logging", "read", flt, f"--project={self.project}", f"--freshness={hours}h",
                                 f"--limit={limit}", "--format=json"), "gcloud logging read") or []


# ---------------------------------------------------------------- the lane

class Live:
    """A lane: gcloud and make as subprocesses found on PATH the way a shell finds them (gcloud is gcloud.cmd on
    Windows), never a prompt; /health read as make limits reads it (commands/lane.py, as documind-ui-sa)."""

    offline = False

    def __init__(self, project: str, region: str, admin_emails: str = ""):
        if not PROJECT_ID.fullmatch(project or ""):
            raise Stop("pass --project with the lane's project id (PROJECT=<id> with make)")
        if not region:
            raise Stop("pass --region with the lane's region (REGION=<region> with make)")
        self.project, self.region, self.admin_emails = project, region, admin_emails

    def where(self) -> tuple[str, str]:
        return f"--region={self.region}", f"--project={self.project}"

    def gcloud(self, *args: str) -> str:
        exe = shutil.which("gcloud")
        if not exe:
            raise Stop("gcloud is not on PATH: install the Google Cloud CLI, or run this in Cloud Shell")
        try:
            r = subprocess.run([exe, *args], env=dict(os.environ, CLOUDSDK_CORE_DISABLE_PROMPTS="1"),
                               stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
                               errors="replace", timeout=900)
        except (OSError, subprocess.TimeoutExpired) as e:
            raise Stop(f"gcloud {' '.join(args[:3])} could not run: {e}") from e
        if r.returncode:
            raise Stop(f"gcloud {' '.join(args[:3])} failed (exit {r.returncode}): {cause(r.stderr)}")
        return r.stdout

    def limits(self, service: str) -> dict:
        lane = _module(HERE / "lane.py", "_gotchas_lane")
        url, body = lane._health(service, self.project, self.region)
        if not isinstance(body, dict) or not isinstance(body.get("limits"), dict):
            why = body if isinstance(body, str) else "an image from before lesson 5.5"
            raise Stop(f"{url}/health gave no limits: {why}")
        return body["limits"]

    def deploy_services(self, scripts: list[str], git_sha: str, extra: dict | None = None) -> None:
        if extra:
            raise Stop("a deploy that carries more settings is a change to your fork; the offline drill shows it")
        exe = shutil.which("make")
        if not exe:
            raise Stop("make is not on PATH: the routine deploy is make deploy-services")
        argv = [exe, "deploy-services", "SCRIPTS=" + " ".join(scripts), f"PROJECT={self.project}",
                f"REGION={self.region}", f"GIT_SHA={git_sha}", f"ADMIN_EMAILS={self.admin_emails}"]
        r = subprocess.run(argv, cwd=str(KIT), env=dict(os.environ, CLOUDSDK_CORE_DISABLE_PROMPTS="1"),
                           stdin=subprocess.DEVNULL)
        if r.returncode:
            raise Stop(f"make deploy-services failed (exit {r.returncode}); its own output is above")

    def recorded(self, name: str) -> str | None:
        path = KIT / name
        return (path.read_text(encoding="utf-8").strip() or None) if path.is_file() else None

    def require_checkout(self, tag: str) -> None:
        exe = shutil.which("git")
        head = ""
        if exe:
            r = subprocess.run([exe, "rev-parse", "HEAD"], cwd=str(KIT), capture_output=True, text=True)
            head = r.stdout.strip() if r.returncode == 0 else ""
        if not tag or not head.startswith(tag):
            raise Stop(f"{CHAT} runs the chat image tagged {tag or '(none)'}, and this checkout is at "
                       f"{head[:12] or 'no commit git can read'}: the routine deploy rebuilds the image from this "
                       f"checkout, so it would change the code too. Check out {tag or 'that commit'} (or redeploy "
                       "the chat from here first), then run the drill again")

    def require_admin(self) -> None:
        if not self.admin_emails or self.admin_emails == make_default(makefile(), "ADMIN_EMAILS"):
            raise Stop("pass ADMIN_EMAILS=<you> (with make, or --admin-emails), as lesson 5.1's deploy does: make "
                       "deploy-services ends with make operators, which grants token minting with it")

    def logs(self, flt: str, hours: int, limit: int = 1000) -> list:
        rows = _json(self.gcloud("logging", "read", flt, f"--project={self.project}", f"--freshness={hours}h",
                                 f"--limit={limit}", "--format=json"), "gcloud logging read")
        return rows if isinstance(rows, list) else []


# ---------------------------------------------------------------- the drills

def run(lane, say: Callable, *args: str) -> str:
    """One gcloud line on the lane, printed first as it runs."""
    say("$ gcloud " + " ".join(shlex.quote(a) for a in args))
    return lane.gcloud(*args)


def restore(lane, say: Callable, before: str | None) -> None:
    """documind-chat's CHAT_MAX_MODEL_CALLS as it was, and its traffic on the latest revision. A failure here says
    which lines finish the job by hand."""
    try:
        if literal_env(template(describe(lane, CHAT))["env"]).get(CAP) != before:
            change = f"--remove-env-vars={CAP}" if before is None else f"--update-env-vars={CAP}={before}"
            run(lane, say, "run", "services", "update", CHAT, change, *lane.where(), "--quiet")
        if not follows_latest(describe(lane, CHAT)):
            run(lane, say, "run", "services", "update-traffic", CHAT, "--to-latest", *lane.where(), "--quiet")
        say(f"restored: {CAP} {'unset' if before is None else '= ' + before}, traffic on the latest revision; "
            f"/health: max_model_calls {lane.limits(CHAT)['max_model_calls']}")
    except Stop as e:
        say(f"RESTORE FAILED: {e}")
        say(f"  by hand: gcloud run services update {CHAT} "
            + (f"--remove-env-vars={CAP}" if before is None else f"--update-env-vars={CAP}={before}")
            + f" --region={lane.region} --project={lane.project}; then gcloud run services update-traffic {CHAT} "
            f"--to-latest --region={lane.region} --project={lane.project}")
        raise


def pinned_findings(service: str, desc: dict, lane) -> list[str]:
    """pinned-traffic's detector on one service: its describe output, and the serving revision's own settings when a
    newer revision takes no traffic (an undo, such as lessons 2.4's and 2.5's, leaves one that changes nothing)."""
    out = []
    now, latest = serving(desc), latest_created(desc)
    tags = {t.get("revisionName") for t in traffic(desc) if t.get("tag")}
    if service != API and not follows_latest(desc):
        held = ", ".join(f"{name} {pct}%" for name, pct in now.items()) or "nothing"
        out.append(f"{service}: its traffic is held on {held}, not on the latest revision: every later update and "
                   "deploy lands at 0%")
    if latest and latest not in now and latest not in tags:
        answering, made = serving_revision(desc), template(desc)
        same = False
        if answering:
            answers = revision_template(revision(lane, answering))
            same = (answers["image"] == template_image(lane, desc)
                    and literal_env(answers["env"]) == literal_env(made["env"]))
        if not same:
            out.append(f"{service}: its newest revision {latest} takes 0% of the traffic and carries no tag: a change "
                       "no request reaches")
    return out


def drill_pinned(lane, entry: dict, say: Callable) -> tuple[bool, bool | None]:
    desc = describe(lane, CHAT)
    if not follows_latest(desc):
        raise Stop(f"{CHAT}'s traffic is already pinned away from its latest revision, so the drill would change what "
                   f"answers. gcloud run services update-traffic {CHAT} --to-latest --region={lane.region} "
                   f"--project={lane.project}, then run it again")
    before, first = literal_env(template(desc)["env"]).get(CAP), serving_revision(desc)
    cap = lane.limits(CHAT)["max_model_calls"]
    say(f"{CHAT}: {first} takes 100% of the traffic, following the latest revision; /health: max_model_calls {cap}")
    reproduced, cleared = False, False
    try:
        say("the traffic held on that revision by name, as a rollback by traffic leaves it:")
        run(lane, say, "run", "services", "update-traffic", CHAT, f"--to-revisions={first}=100", *lane.where(), "--quiet")
        say("a setting changed by hand:")
        run(lane, say, "run", "services", "update", CHAT, f"--update-env-vars={CAP}=3", *lane.where(), "--quiet")
        desc = describe(lane, CHAT)
        made, now = latest_created(desc), lane.limits(CHAT)["max_model_calls"]
        say(f"{made}: made with {CAP}=3, takes {percent_of(desc, made)}% of the traffic; /health: max_model_calls {now}")
        found = pinned_findings(CHAT, desc, lane)
        for line in found:
            say("detector: " + line)
        reproduced = bool(found) and made != first and now == cap and literal_env(template(desc)["env"]).get(CAP) == "3"
        if reproduced:
            say("REPRODUCED: " + entry["drill"]["offline"]["marker"])
        say("the lever:")
        run(lane, say, "run", "services", "update-traffic", CHAT, "--to-latest", *lane.where(), "--quiet")
        desc = describe(lane, CHAT)
        now = lane.limits(CHAT)["max_model_calls"]
        say(f"{latest_created(desc)} takes {percent_of(desc, latest_created(desc))}% of the traffic; /health: "
            f"max_model_calls {now}")
        cleared = follows_latest(desc) and now == 3 and not pinned_findings(CHAT, desc, lane)
        if cleared:
            say("CLEARED: " + entry["drill"]["offline"]["cleared"])
    finally:
        restore(lane, say, before)
    return reproduced, cleared


def drill_deploy_drop(lane, entry: dict, say: Callable) -> tuple[bool, bool | None]:
    spec = deploy_specs()[CHAT]
    desc = describe(lane, CHAT)
    if not follows_latest(desc):
        raise Stop(f"{CHAT}'s traffic does not follow its latest revision, so neither the setting nor the deploy would "
                   f"serve. gcloud run services update-traffic {CHAT} --to-latest --region={lane.region} "
                   f"--project={lane.project}, then run it again")
    pending = spec.changes(literal_env(template(desc)["env"]))
    if pending:
        names = ",".join(c.name for c in pending)
        raise Stop("the routine deploy would change more than the drill's own variable: "
                   + "; ".join(c.line for c in pending) + ". Carry those into the deploy, or take them off first so "
                   f"that the drill leaves the lane as it was: gcloud run services update {CHAT} "
                   f"--remove-env-vars={names} --region={lane.region} --project={lane.project}")
    tag = template(desc)["image"].rpartition(":")[2]
    lane.require_checkout(tag)
    lane.require_admin()
    cap = lane.limits(CHAT)["max_model_calls"]
    say(f"{CHAT}: image tag {tag}, nothing the next deploy would change; /health: max_model_calls {cap}")
    reproduced, cleared = False, None
    try:
        say("a setting changed by hand:")
        run(lane, say, "run", "services", "update", CHAT, f"--update-env-vars={CAP}=8", *lane.where(), "--quiet")
        say(f"/health: max_model_calls {lane.limits(CHAT)['max_model_calls']}: the hand-set value answers")
        found = spec.changes(literal_env(template(describe(lane, CHAT))["env"]))
        for c in found:
            say("detector, before the deploy: " + c.line)
        say(f"the routine deploy:\n$ make deploy-services SCRIPTS={spec.script} PROJECT={lane.project} "
            f"REGION={lane.region} GIT_SHA={tag}")
        lane.deploy_services([spec.script], tag)
        desc = describe(lane, CHAT)
        after = lane.limits(CHAT)["max_model_calls"]
        gone = CAP not in literal_env(template(desc)["env"])
        say(f"{latest_created(desc)}: {CAP} {'gone' if gone else 'still set'}; /health: max_model_calls {after}")
        reproduced = any(c.name == CAP for c in found) and gone and after == cap
        if reproduced:
            say("REPRODUCED: " + entry["drill"]["offline"]["marker"])
        if lane.offline:
            say(f"the lever: carry the value in the deploy. {spec.script} reads CHAT_EXTRA_ENV for more variables, and "
                "make deploy-services empties it (the Makefile's CHAT_EXTRA_ENV=;), so a fork that keeps the setting "
                f"sets it there: CHAT_EXTRA_ENV='|{CAP}=8'")
            fork = {"CHAT_EXTRA_ENV": f"|{CAP}=8"}
            lane.deploy_services([spec.script], tag, extra=fork)
            desc = describe(lane, CHAT)
            kept, left = lane.limits(CHAT)["max_model_calls"], spec.changes(literal_env(template(desc)["env"]), fork)
            say(f"{latest_created(desc)}: /health: max_model_calls {kept}; the detector, with that deploy: "
                + ("; ".join(c.line for c in left) or "nothing to drop"))
            cleared = kept == 8 and not left
            if cleared:
                say("CLEARED: " + entry["drill"]["offline"]["cleared"])
            lane.deploy_services([spec.script], tag)            # back as the kit deploys it
        else:
            say("the lever, carrying the value in the deploy, is a change to your fork: the offline drill shows it "
                "(make gotcha-drill ID=deploy-drops-hotfix)")
    finally:
        restore(lane, say, None)
    return reproduced, cleared


def _gated_api(lane: StandIn, say: Callable) -> str:
    """The API as a lane in the release flow has it: deployed, then a candidate released through make promote."""
    lane.deploy_services(["commands/lesson-12.2.sh"], "a1b2c3d")
    lane.make_release_candidate("b2c3d4e")
    lane.make_promote()
    gated = lane.recorded(".candidate-revision")
    say(f"{API} after make release-candidate GIT_SHA=b2c3d4e, the gate and make promote: {gated} serves 100%, "
        "recorded in deploy/.candidate-revision")
    return gated


def ungated_findings(lane) -> tuple[bool | None, list[str]]:
    """ungated-api-release's detector."""
    now = serving_revision(describe(lane, API))
    if now is None:
        raise Stop(f"{API}'s traffic is split: no one revision serves")
    cand, prev = lane.recorded(".candidate-revision"), lane.recorded(".previous-revision")
    if now == cand:
        return False, [f"{API} serves {now}, the candidate this checkout recorded (make candidate or make "
                       "release-candidate), which the gate judged if you ran make eval-live on it"]
    if now == prev:
        return False, [f"{API} serves {now}, the revision make rollback returns to (deploy/.previous-revision)"]
    if not cand and not prev:
        return None, [f"{API} serves {now}; this checkout recorded no candidate and no rollback, so it cannot tell how "
                      "that revision reached the traffic (a CI release records them on its runner: read its log)"]
    return True, [f"{API} serves {now}, which this checkout neither recorded as a candidate ({cand or 'none'}) nor "
                  f"rolled back to ({prev or 'none'}): make deploy-services, make up or a hand update-traffic put it "
                  "live, and no gate judged it"]


def drill_ungated(lane: StandIn, entry: dict, say: Callable) -> tuple[bool, bool | None]:
    scripts = default_scripts(makefile())
    gated = _gated_api(lane, say)
    say(f"a routine deploy from a newer checkout:\n$ make deploy-services GIT_SHA=c3d4e5f   (SCRIPTS: "
        f"{count(len(scripts), 'script')}, lesson-12.2.sh among them)")
    lane.deploy_services(scripts, "c3d4e5f")
    now = serving_revision(describe(lane, API))
    found, lines = ungated_findings(lane)
    say(f"{API}: {now} serves 100%, GIT_SHA c3d4e5f")
    for line in lines:
        say("detector: " + line)
    reproduced = bool(found) and now != gated
    if reproduced:
        say("REPRODUCED: " + entry["drill"]["offline"]["marker"])
    say("the lever, from the same gated state: the other services' scripts only")
    other = StandIn(lane.project, lane.region)
    gated = _gated_api(other, say)
    rest = [s for s in scripts if not s.endswith("lesson-12.2.sh")]
    say(f"$ make deploy-services SCRIPTS=\"{' '.join(rest)}\" GIT_SHA=c3d4e5f")
    other.deploy_services(rest, "c3d4e5f")
    found, lines = ungated_findings(other)
    for line in lines:
        say("detector: " + line)
    cleared = found is False and serving_revision(describe(other, API)) == gated
    if cleared:
        say("CLEARED: " + entry["drill"]["offline"]["cleared"])
    lane.calls += other.calls
    return reproduced, cleared


def rides_findings(lane) -> tuple[bool | None, list[str]]:
    """switch-rides-into-candidate's detector."""
    desc = describe(lane, API)
    cand, now = tagged(desc, "candidate"), serving_revision(desc)
    if not cand:
        return False, [f"{API} has no candidate tag: no candidate waits for the gate"]
    if now is None:
        raise Stop(f"{API}'s traffic is split: no one revision serves")
    if cand == now:
        return False, [f"the candidate tag is on {now}, the serving revision: nothing to compare"]
    diff = env_diff(literal_env(revision_template(revision(lane, now))["env"]),
                    literal_env(revision_template(revision(lane, cand))["env"]))
    own = {"GIT_SHA", "GENERATOR_LOCATION", "RETRIEVAL_BACKEND", "RAG_LOCATION", *candidate_names(makefile())}
    lines = [f"the candidate {cand} against the serving {now}:"]
    lines += [f"  {n}: {shown(a)} -> {shown(b)}" + ("" if n in own else "   rode in? no make target sets it on a candidate")
              for n, (a, b) in diff.items()] or ["  the same variables"]
    return any(n not in own for n in diff), lines


def drill_rides(lane: StandIn, entry: dict, say: Callable) -> tuple[bool, bool | None]:
    lane.deploy_services(["commands/lesson-12.2.sh"], "a1b2c3d")
    now = serving_revision(describe(lane, API))
    say(f"{API}: {now} serves, as make deploy-services left it")
    say("lesson 2.5's candidate, judged, and left as it was (no undo):")
    run(lane, say, "run", "services", "update", API, *lane.where(), "--no-traffic", "--tag=candidate",
        "--update-env-vars=QUERY_REWRITE=on", "--quiet")
    say("$ make release-candidate GIT_SHA=b2c3d4e")
    lane.make_release_candidate("b2c3d4e")
    cand = lane.recorded(".candidate-revision")
    found, lines = rides_findings(lane)
    for line in lines:
        say("detector: " + line)
    on = literal_env(revision_template(revision(lane, cand))["env"]).get("QUERY_REWRITE")
    reproduced = bool(found) and on == "on"
    if reproduced:
        say("REPRODUCED: " + entry["drill"]["offline"]["marker"])
    say("the lever, lesson 2.5's undo, then the release again:")
    run(lane, say, "run", "services", "update", API, *lane.where(), "--no-traffic", "--tag=candidate",
        "--remove-env-vars=QUERY_REWRITE", "--quiet")
    say("$ make release-candidate GIT_SHA=b2c3d4e")
    lane.make_release_candidate("b2c3d4e")
    cand = lane.recorded(".candidate-revision")
    found, lines = rides_findings(lane)
    for line in lines:
        say("detector: " + line)
    diff = env_diff(literal_env(revision_template(revision(lane, now))["env"]),
                    literal_env(revision_template(revision(lane, cand))["env"]))
    cleared = found is False and set(diff) == {"GIT_SHA"}
    if cleared:
        say("CLEARED: " + entry["drill"]["offline"]["cleared"])
    return reproduced, cleared


def template_findings(lane) -> tuple[bool | None, list[str]]:
    """rollback-keeps-template's detector."""
    desc = describe(lane, API)
    now, latest, on_tag = serving_revision(desc), latest_created(desc), tagged(desc, "candidate")
    if now is None:
        raise Stop(f"{API}'s traffic is split: no one revision serves")
    answering = revision_template(revision(lane, now))
    diff = env_diff(literal_env(answering["env"]), literal_env(template(desc)["env"]))
    if template_image(lane, desc) != answering["image"]:
        diff["(image)"] = (answering["image"], template(desc)["image"])
    if not diff:
        return False, [f"{API}'s template is what its serving revision {now} was made from"]
    lines = [f"{API}'s template ({latest}) differs from the serving revision {now}:"]
    lines += [f"  {n}: {shown(a)} on {now}, {shown(b)} on the template" for n, (a, b) in diff.items()]
    cand, prev = lane.recorded(".candidate-revision"), lane.recorded(".previous-revision")
    if latest == on_tag:
        if cand == latest and prev == now:
            lines.append(f"make rollback returned the traffic to {now}; the template still holds {latest}'s settings, "
                         "and the next update or make release-candidate starts from them")
            return True, lines
        if not cand and not prev:
            lines.append(f"{latest} carries the candidate tag; this checkout cannot tell whether it waits for the gate "
                         "or was rolled back by a CI run")
            return None, lines
        lines.append(f"{latest} is the candidate waiting for the gate: its settings are on the template until make "
                     "promote or a repair")
        return False, lines
    lines.append(f"{latest} takes no traffic and carries no tag: an update nobody moved the traffic to, and the next "
                 "update starts from it")
    return True, lines


def drill_template(lane: StandIn, entry: dict, say: Callable) -> tuple[bool, bool | None]:
    lane.deploy_services(["commands/lesson-12.2.sh"], "a1b2c3d")
    model = literal_env(template(describe(lane, API))["env"]).get("GENERATOR_MODEL")
    say(f"{API}: {serving_revision(describe(lane, API))} serves on GENERATOR_MODEL={model}")
    say("lesson 11.3's controlled failure:\n$ make candidate GENERATOR_MODEL=gemini-3.6-flsh\n$ make promote\n"
        "$ make rollback")
    lane.make_candidate(GENERATOR_MODEL="gemini-3.6-flsh")
    lane.make_promote()
    lane.make_rollback()
    found, lines = template_findings(lane)
    for line in lines:
        say("detector: " + line)
    say("$ make release-candidate GIT_SHA=b2c3d4e")
    lane.make_release_candidate("b2c3d4e")
    got = literal_env(revision_template(revision(lane, lane.recorded(".candidate-revision")))["env"]).get("GENERATOR_MODEL")
    say(f"the next candidate {lane.recorded('.candidate-revision')}: GENERATOR_MODEL={got}")
    reproduced = bool(found) and got == "gemini-3.6-flsh"
    if reproduced:
        say("REPRODUCED: " + entry["drill"]["offline"]["marker"])
    say(f"the lever, lesson 11.3's repair before the release:\n$ make candidate GENERATOR_MODEL={model}\n"
        "$ make release-candidate GIT_SHA=b2c3d4e")
    lane.make_candidate(GENERATOR_MODEL=model)
    lane.make_release_candidate("b2c3d4e")
    got = literal_env(revision_template(revision(lane, lane.recorded(".candidate-revision")))["env"]).get("GENERATOR_MODEL")
    say(f"the next candidate {lane.recorded('.candidate-revision')}: GENERATOR_MODEL={got}")
    cleared = got == model
    if cleared:
        say("CLEARED: " + entry["drill"]["offline"]["cleared"])
    return reproduced, cleared


def previous_findings(lane) -> tuple[bool | None, list[str]]:
    """ci-promote-loses-previous's detector."""
    now = serving_revision(describe(lane, API))
    prev, cand = lane.recorded(".previous-revision"), lane.recorded(".candidate-revision")
    if not prev:
        return True, [f"this checkout has no deploy/.previous-revision: make rollback refuses here. {API} serves "
                      f"{now}; the revision before it is in the promote job's log ('serving before the flip: ...')"]
    if prev == now:
        return False, [f"deploy/.previous-revision names {prev}, which serves: nothing to return to"]
    try:
        revision(lane, prev)
    except Stop:
        return True, [f"deploy/.previous-revision names {prev}, which {API} no longer has"]
    if cand != now:
        return True, [f"{API} serves {now}, which this checkout did not promote (its last candidate was "
                      f"{cand or 'none'}): make rollback here would return to {prev}, from an older release"]
    return False, [f"make rollback would return {API} from {now} to {prev}, the revision this checkout's promote "
                   "moved the traffic off"]


def drill_previous(lane: StandIn, entry: dict, say: Callable) -> tuple[bool, bool | None]:
    lane.deploy_services(["commands/lesson-12.2.sh"], "a1b2c3d")
    before = serving_revision(describe(lane, API))
    runner: dict[str, str] = {}
    say(f"{API}: {before} serves. documind-cd.yml's jobs, each on a runner of their own:\n"
        "$ make release-candidate GIT_SHA=b2c3d4e   (the release-candidate job)\n$ make promote   (the promote job)")
    lane.make_release_candidate("b2c3d4e", files=runner)
    lane.make_promote(files=runner)
    say(f"the promote job's log: serving before the flip: {runner.get('.previous-revision')}; the runner is gone")
    found, lines = previous_findings(lane)
    for line in lines:
        say("detector: " + line)
    say("$ make rollback   (in this checkout)")
    refused = ""
    try:
        lane.make_rollback()
    except Refused as e:
        refused = str(e)
        say(f"make rollback: {refused}")
    reproduced = bool(found) and refused.startswith("ERROR: deploy/.previous-revision is missing")
    if reproduced:
        say("REPRODUCED: " + entry["drill"]["offline"]["marker"])
    say(f"the lever: the name from the log, into this checkout\n$ printf '%s\\n' {before} > deploy/.previous-revision\n"
        "$ make rollback")
    lane.files[".previous-revision"] = before
    lane.make_rollback()
    cleared = serving_revision(describe(lane, API)) == before
    say(f"{API}: {serving_revision(describe(lane, API))} serves")
    if cleared:
        say("CLEARED: " + entry["drill"]["offline"]["cleared"])
    return reproduced, cleared


def chat_limits():
    """services/chat/limits.py, the chat service's own Meter (the standard library and shared/prices.py at import)."""
    return _module(KIT / "services" / "chat" / "limits.py", "_gotchas_chat_limits")


def tf_blocks(*kinds: str) -> list[tuple[str, str, str]]:
    """(file, resource name, body) of every terraform resource of these kinds, read as terraform fmt writes them."""
    out = []
    for path in sorted((KIT / "terraform").glob("*.tf")):
        text = path.read_text(encoding="utf-8")
        for m in re.finditer(r'^resource "(\w+)" "(\w+)" \{\n', text, re.M):
            if m.group(1) in kinds:
                end = re.search(r"^\}", text[m.end():], re.M)
                out.append((path.name, m.group(2), text[m.end():m.end() + (end.start() if end else len(text))]))
    return out


def drill_loop(lane, entry: dict, say: Callable) -> tuple[bool, bool | None]:
    limits = chat_limits()
    meter = limits.Meter(model=limits.prices.DEFAULT_MODEL)
    say(f"services/chat/limits.py's Meter at the defaults: {meter.max_model_calls} model calls, Rs {meter.budget_inr:g}, "
        f"{meter.deadline_s:g} s; a model that asks for one more search on every call (1,500 tokens in, 60 out)")
    asked = 0
    while asked < 100 and meter.allow_model_call():
        asked += 1
        meter.charge_model(1500, 60)
    say(f"{meter.model_calls} calls allowed, the next refused: stopped_by={meter.stopped_by}, "
        f"Rs {meter.spent_inr():.2f} spent")
    say(f"the turn's answer, with HTTP 200: {limits.STOP_ANSWER}")
    say("the chat row: " + json.dumps({k: meter.row()[k] for k in ("model_calls", "stopped_by", "cost_usd")}))
    watchers = tf_blocks("google_monitoring_alert_policy", "google_logging_metric")
    readers = [f"{f}: {name}" for f, name, body in watchers
               if re.search(r'stopped_by|event\s*=\s*\\?"chat\\?"', body)]
    say(f"terraform/*.tf: {len(watchers)} alert policies and log metrics; "
        + (f"reading stopped_by or the chat rows: {', '.join(readers)}" if readers else
           "none of them reads stopped_by or the chat rows"))
    reproduced = meter.stopped_by in limits.STOPS and bool(watchers) and not readers
    if reproduced:
        say("REPRODUCED: " + entry["drill"]["offline"]["marker"])
    return reproduced, None


class _Lines(logging.Handler):
    """The log lines one logger writes while a drill runs, kept to be printed with the drill."""

    def __init__(self):
        super().__init__()
        self.lines: list[str] = []

    def emit(self, record):
        self.lines.append(record.getMessage())


def drill_abandoned(lane, entry: dict, say: Callable) -> tuple[bool, bool | None]:
    """The chat's own timed wrapper (timed_async, the ADK brain's) on one search that takes four seconds, cut at a
    one-second budget. One call and wide margins: commands/tests/test_chat_limits.py's three queued calls, cut at 0.2 s,
    can race on a loaded machine (they did on 12 October 2026: a queued call started before its cut), and this drill
    needs the running call alone."""
    limits = chat_limits()
    ran, wrote = [], []

    def search(n: int) -> dict:
        started = time.monotonic()
        ran.append(n)
        time.sleep(4.0)
        wrote.append((limits.may_commit(), time.monotonic() - started))      # may it write into the turn now?
        return {"citations": [n]}

    # services/chat/tools.py's two names limits.py reads, as the kit's test gives them: the real module imports LangChain
    stand_in = types.SimpleNamespace(TIMEOUTS={"retrieve": 1},
                                     REQUEST=contextvars.ContextVar("documind_request", default={}))
    saved, log, lines = sys.modules.get("tools"), logging.getLogger(limits.logger.name), _Lines()
    sys.modules["tools"] = stand_in
    log.addHandler(lines)
    propagate, level = log.propagate, log.level
    log.propagate = False
    log.setLevel(logging.INFO)          # _log_time writes INFO when the cut lands on the budget, WARNING when past it
    try:
        began = time.monotonic()
        out = asyncio.run(limits.timed_async("retrieve", search, n=0))
        moved_on = time.monotonic() - began
        deadline = time.monotonic() + 20
        while not wrote and time.monotonic() < deadline:
            time.sleep(0.05)
    finally:
        log.removeHandler(lines)
        log.propagate = propagate
        log.setLevel(level)
        if saved is None:
            sys.modules.pop("tools", None)
        else:
            sys.modules["tools"] = saved
    say(f"a search that takes 4 s, cut at its 1 s budget: the turn moved on after {moved_on:.1f} s, and the model read "
        + json.dumps(out))
    for line in lines.lines:
        say("the chat's log: " + line)
    if wrote:
        say(f"the search ran on to its end, {wrote[0][1]:.1f} s, then asked whether it may write into the turn: "
            f"may_commit() said {wrote[0][0]}")
    say("on a lane that search is rag-api's: it answers after the turn has moved on and bills the answer on its own "
        "row, while the chat row names the call in tool_timeouts and leaves its cost out")
    reproduced = (bool(out.get("timed_out")) and ran == [0] and bool(wrote) and wrote[0][0] is False
                  and wrote[0][1] > moved_on)
    if reproduced:
        say("REPRODUCED: " + entry["drill"]["offline"]["marker"])
    return reproduced, None


def usage_events() -> list[str]:
    events = re.findall(r'jsonPayload\.event="([a-z_]+)"', kit_text("evals/usage_rows.py"))
    if not events:
        raise Changed("evals/usage_rows.py no longer selects rows by event")
    return list(dict.fromkeys(events))


def daily_events() -> list[str]:
    m = re.search(r"jsonPayload\.event IN \(([^)]*)\)", kit_text("terraform/sql/tenant_daily.sql"))
    if not m:
        raise Changed("terraform/sql/tenant_daily.sql no longer selects rows by event")
    return re.findall(r'"([a-z_]+)"', m.group(1))


def drill_spend(lane, entry: dict, say: Callable) -> tuple[bool, bool | None]:
    limits = chat_limits()
    prices, model = limits.prices, limits.prices.DEFAULT_MODEL
    meter = limits.Meter(model=model)
    for _ in range(3):
        meter.allow_model_call()
        meter.charge_model(4000, 300)
    rag = prices.usd(model, 6000, 250)
    meter.charge_rag({"model": model, "cost_usd": rag})
    row = meter.row()
    rows = [{"event": "chat", "brain": "langchain", **{k: row[k] for k in ("model_calls", "cost_usd", "rag_cost_usd")}},
            {"event": "query", "brain": "langchain", "cost_usd": round(rag, 6)}]
    say("one stand-in turn on the langchain brain, three model calls and one search, as the two services log it:")
    for row in rows:
        say("  " + json.dumps(row))
    daily, usage = daily_events(), usage_events()
    writes = re.compile(r"^from budget import .*\brecord\b", re.M)       # rag-api's own import of the counter's writer
    writers = sorted(p.relative_to(KIT).as_posix() for p in (KIT / "services").rglob("*.py")
                     if writes.search(p.read_text(encoding="utf-8", errors="replace")))
    say(f"tenant_daily (terraform/sql/tenant_daily.sql) counts the events {', '.join(daily)}: "
        f"Rs {prices.inr(sum(r['cost_usd'] for r in rows if r['event'] in daily)):.2f} of this turn")
    say(f"make usage (evals/usage_rows.py) counts the events {', '.join(usage)}: "
        f"Rs {prices.inr(sum(r['cost_usd'] for r in rows if r['event'] in usage)):.2f}")
    say(f"the breaker's month counter (services/rag-api/budget.py) is added to by {', '.join(writers) or 'nothing'}")
    sinks = [name for _, name, body in tf_blocks("google_logging_project_sink") if 'jsonPayload.event = "chat"' in body]
    if sinks:
        say(f"the chat rows do reach BigQuery: terraform's log sink {', '.join(sinks)} copies event chat into the table "
            "tenant_daily reads, which leaves them out")
    say(f"the agent's own model calls: Rs {prices.inr(rows[0]['cost_usd']):.2f}, on the chat row alone")
    reproduced = ("chat" not in daily and "chat" not in usage and bool(writers)
                  and not any(w.startswith("services/chat/") for w in writers))
    if reproduced:
        say("REPRODUCED: " + entry["drill"]["offline"]["marker"])
    return reproduced, None


# the offline drills, by id: each takes a stand-in lane (or none it needs), the entry and a printer, and returns
# (reproduced, cleared); the two in LIVE_DRILLS run unchanged on a lane
DRILLS = {"pinned-traffic": drill_pinned, "deploy-drops-hotfix": drill_deploy_drop, "ungated-api-release": drill_ungated,
          "switch-rides-into-candidate": drill_rides, "rollback-keeps-template": drill_template,
          "looping-model-stopped": drill_loop, "abandoned-call-bills": drill_abandoned,
          "agent-spend-outside-the-month": drill_spend, "ci-promote-loses-previous": drill_previous}
LIVE_DRILLS = {"pinned-traffic": drill_pinned, "deploy-drops-hotfix": drill_deploy_drop}


def initial(lane: StandIn, gid: str) -> None:
    """The stand-in a drill starts from: documind-chat as make deploy-services leaves it, for the chat's drills."""
    if gid in ("pinned-traffic", "deploy-drops-hotfix"):
        lane.deploy_services([deploy_specs()[CHAT].script], "c0ffee1")


def run_drill(entry: dict, say: Callable, lane=None) -> int:
    """One drill, offline on a fresh stand-in unless a lane is given: 0 reproduced (and cleared, offline, where the
    entry shows its lever), 1 not, with the reason."""
    gid, offline = entry["id"], entry["drill"]["offline"]
    missing = missing_evidence(entry)
    if missing:
        say(f"NOT REPRODUCED: the kit no longer says what {gid} rests on: " + "; ".join(missing)
            + ". If the gotcha is fixed, set its status to fixed and fixed_by to the test that proves it")
        return 1
    if lane is None:
        lane = StandIn()
        initial(lane, gid)
    try:
        reproduced, cleared = (LIVE_DRILLS if not lane.offline else DRILLS)[gid](lane, entry, say)
    except (Changed, Refused) as e:
        say(f"NOT REPRODUCED: {e}")
        return 1
    if not reproduced:
        say(f"NOT REPRODUCED: {gid}'s drill no longer shows its gotcha. If the kit fixed it, set its status to fixed "
            "and fixed_by to the test that proves it")
        return 1
    if lane.offline and offline and offline["cleared"] and not cleared:
        say(f"NOT CLEARED: the lever the entry names did not clear {gid} on the stand-in")
        return 1
    return 0


# ---------------------------------------------------------------- the detectors

def dig(row, path: str):
    for part in path.split("."):
        row = row.get(part) if isinstance(row, dict) else None
    return row


def _usd(value) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def each_service(lane) -> tuple[dict[str, dict], list[str]]:
    """Every service make deploy-services deploys, described: (service -> describe output, lines for those that could
    not be read). Not one read is a Stop: no proof of anything."""
    read, unread = {}, []
    for service in deploy_specs():
        try:
            read[service] = describe(lane, service)
        except Stop as e:
            unread.append(f"{service}: not read: {e}")
    if not read:
        raise Stop(unread[0].split(": not read: ", 1)[1] if unread else "no service to read")
    return read, unread


def detect_pinned(lane, entry: dict, hours: int) -> tuple[bool | None, list[str]]:
    read, lines = each_service(lane)
    found = False
    for service, desc in read.items():
        problems = pinned_findings(service, desc, lane)
        found = found or bool(problems)
        held = ", ".join(f"{n} {p}%" for n, p in serving(desc).items())
        lines += problems or [f"{service}: {'follows its latest revision' if follows_latest(desc) else 'held by name'}"
                              f" ({held})"]
    return (True if found else None if len(read) < len(deploy_specs()) else False), lines


def detect_drops(lane, entry: dict, hours: int) -> tuple[bool | None, list[str]]:
    read, lines = each_service(lane)
    found, specs = False, deploy_specs()
    for service, desc in read.items():
        spec = specs[service]
        changes = spec.changes(literal_env(template(desc)["env"]))
        found = found or bool(changes)
        lines.append(f"{service} ({spec.script}): " + (f"{count(len(changes), 'variable')} the next make "
                                                        "deploy-services would change" if changes else
                                                        "nothing the next make deploy-services would change"))
        lines += ["  " + c.line for c in changes]
    return (True if found else None if len(read) < len(specs) else False), lines


def detect_spend(lane, entry: dict, hours: int) -> tuple[bool | None, list[str]]:
    prices = chat_limits().prices
    chat = lane.logs(f'resource.type="cloud_run_revision" AND resource.labels.service_name="{CHAT}" AND '
                     'jsonPayload.event="chat"', hours)
    api = lane.logs(f'resource.type="cloud_run_revision" AND resource.labels.service_name="{API}" AND ('
                    + " OR ".join(f'jsonPayload.event="{e}"' for e in usage_events()) + ")", hours)
    agent, rag = (sum(_usd(dig(r, "jsonPayload.cost_usd")) for r in rows) for rows in (chat, api))
    lines = [f"{count(len(chat), 'chat turn')} in the last {hours} h: Rs {prices.inr(agent):.2f} on the agents' own "
             "model calls, in no report of the month",
             f"rag-api's {count(len(api), 'row')}: Rs {prices.inr(rag):.2f}, what tenant_daily, make usage and the "
             "breaker's counter count"]
    if agent and (agent + rag):
        lines.append(f"the month's reports see {100 * rag / (agent + rag):.0f}% of what these {hours} hours cost")
    return agent > 0, lines


def detect_environment(lane, entry: dict, hours: int) -> tuple[bool | None, list[str]]:
    release = _module(HERE / "release.py", "_gotchas_release")
    try:                                         # release.py's Stop, and infrastructure.py's own, are its messages
        inputs = release.lane_inputs(KIT / "terraform")
        level, line = release.production_environment(inputs["github_repository"])
    except Exception as e:
        raise Stop(f"make ci-vars' read of the production environment: {e}") from e
    if level == "unread":                        # gh answered, and not with the environment: a read that failed
        raise Stop(line)
    return (None if level == "note" else level == "warn"), [line]


def detect_log(lane, entry: dict, hours: int) -> tuple[bool | None, list[str]]:
    det, limit = entry["detector"], 1000
    rows = lane.logs(det["filter"], hours, limit)
    if det.get("count_if"):
        rows = [r for r in rows if dig(r, det["count_if"])]
    many = "at least " if len(rows) >= limit else ""
    lines = [f"{many}{len(rows)} {'entry' if len(rows) == 1 else 'entries'} in the last {hours} h: {det['finds']}"]
    if rows and det.get("group_by"):
        groups = collections.Counter(tuple(str(dig(r, f)) for f in det["group_by"]) for r in rows)
        for key, n in groups.most_common(10):
            lines.append(f"  {n:5}  " + "  ".join(f"{f.rsplit('.', 1)[-1]}={v}" for f, v in zip(det["group_by"], key)))
    if det.get("pages"):
        lines.append(f"pages: the alert policy {det['pages']!r} (terraform)")
    return bool(rows), lines


CHECKS = {"pinned-traffic": detect_pinned, "deploy-drops-hotfix": detect_drops,
          "ungated-api-release": lambda lane, entry, hours: ungated_findings(lane),
          "switch-rides-into-candidate": lambda lane, entry, hours: rides_findings(lane),
          "rollback-keeps-template": lambda lane, entry, hours: template_findings(lane),
          "agent-spend-outside-the-month": detect_spend,
          "ci-promote-loses-previous": lambda lane, entry, hours: previous_findings(lane),
          "environment-without-reviewers": detect_environment}


def run_detector(entry: dict, lane, hours: int, say: Callable) -> int:
    """One detector on the lane: 0 nothing found (or nothing this checkout can tell), 1 found, 2 a read failed."""
    try:
        found, lines = (CHECKS[entry["id"]] if entry["detector"]["kind"] == "check" else detect_log)(lane, entry, hours)
    except (Stop, Changed) as e:
        say(f"STOPPED: {e}")
        return STOPPED
    for line in lines:
        say(line)
    say("FOUND: " + entry["title"] if found else "nothing found" if found is False else "nothing this checkout can tell")
    return FOUND if found else 0


# ---------------------------------------------------------------- the command line

def say(line: str = "") -> None:
    print(line, flush=True)


def _entry(entries: list[dict], gid: str) -> dict:
    found = next((g for g in entries if g["id"] == gid), None)
    if found is None:
        raise Stop(f"no gotcha {gid!r} in ops/gotchas.json: make gotchas lists them")
    return found


def _wrap(label: str, text: str) -> None:
    say(textwrap.fill(text, width=118, initial_indent=f"  {label:<10} ", subsequent_indent=" " * 13,
                      break_on_hyphens=False, break_long_words=False))


def cmd_list(a) -> int:
    entries = load()
    say(f"{count(len(entries), 'gotcha')} in ops/gotchas.json (workshop lesson 11.7). make gotchas ID=<id> shows one; "
        "make gotcha-drill runs every offline drill, Rs 0")
    say(f"{'id':31} {'signal':7} {'drill':14} {'status':8} {'lessons':18} title")
    for g in entries:
        drills = ", ".join(k for k in ("offline", "live") if g["drill"][k])
        say(f"{g['id']:31} {g['signal']:7} {drills:14} {g['status']:8} {' '.join(g['lessons']):18} {g['title']}")
    return 0


def cmd_show(a) -> int:
    g = _entry(load(), a.id)
    say(f"{g['id']}: {g['title']}")
    _wrap("signal", g["signal"] + (f": {g['signal_by']}" if g.get("signal_by") else ""))
    _wrap("status", g["status"] + (f": {g['fixed_by']}" if g.get("fixed_by") else ""))
    _wrap("symptom", g["symptom"])
    _wrap("no eval", g["why_no_eval"])
    off, live = g["drill"]["offline"], g["drill"]["live"]
    if off:
        _wrap("drill", f"offline, Rs 0 (make gotcha-drill ID={g['id']}): {off['how']} It prints REPRODUCED: "
                       f"{off['marker']}" + (f"; and CLEARED: {off['cleared']}" if off["cleared"] else ""))
    if live:
        _wrap("on a lane", f"{live['run']}. Changes: {live['changes']}. Restores: {live['restores']}. Cost: {live['cost']}")
    det = g["detector"]
    _wrap("detector", f"{det['run']}. Reads {det['reads']}; finds {det['finds']}"
                      + (f". Pages: the alert policy {det['pages']!r}" if det.get("pages") else "")
                      + (f". Filter: {det['filter']}" if det.get("filter") else ""))
    _wrap("lever", g["lever"])
    _wrap("lessons", ", ".join(g["lessons"]))
    _wrap("cost", g["cost"])
    for rel, text in g["evidence"]:
        _wrap("kit", f"{rel}: {text}")
    return 0


def cmd_drill(a) -> int:
    entries = load()
    if a.live:
        if not a.id:
            raise Stop("one live drill at a time: name it, make gotcha-drill ID=<id> LIVE=1")
        g = _entry(entries, a.id)
        if a.id not in LIVE_DRILLS:
            raise Stop(f"{a.id} has no live drill here: "
                       + (f"on a lane it is {g['drill']['live']['run']}" if g["drill"]["live"] else "it is offline only"))
        lane = Live(a.project, a.region, a.admin_emails)
        say(f"== {a.id}, live on {a.project} ({a.region}): {g['title']}")
        return run_drill(g, say, lane)
    chosen = [_entry(entries, a.id)] if a.id else [g for g in entries if g["drill"]["offline"]]
    failed = []
    for g in chosen:
        if not g["drill"]["offline"]:
            raise Stop(f"{g['id']} has no offline drill: on a lane it is {g['drill']['live']['run']}")
        say(f"== {g['id']}, offline (a stand-in, Rs 0): {g['title']}")
        if run_drill(g, say):
            failed.append(g["id"])
        say()
    if len(chosen) > 1:
        say(f"{len(chosen) - len(failed)} of {count(len(chosen), 'offline drill')} reproduced their gotcha"
            + (f"; not: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


def cmd_detect(a) -> int:
    entries = load()
    chosen = [_entry(entries, a.id)] if a.id else entries
    lane = Live(a.project, a.region)
    codes = []
    for g in chosen:
        say(f"== {g['id']}: {g['detector']['finds']}")
        codes.append(run_detector(g, lane, a.hours, say))
        say()
    if len(chosen) > 1:
        say(f"{count(len(chosen), 'detector')}: {codes.count(FOUND)} found, {codes.count(STOPPED)} could not read")
    return FOUND if FOUND in codes else STOPPED if STOPPED in codes else 0


def build_parser() -> argparse.ArgumentParser:
    lines = __doc__.splitlines()
    ap = argparse.ArgumentParser(prog="gotchas.py", description=lines[0], epilog="\n".join(lines[2:]),
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    lane = argparse.ArgumentParser(add_help=False)
    lane.add_argument("--project", default=os.environ.get("PROJECT") or "", help="the lane's project id (PROJECT)")
    lane.add_argument("--region", default=os.environ.get("REGION") or "us-central1", help="the lane's region (REGION)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list", help="the registry, one line a gotcha (make gotchas)").set_defaults(fn=cmd_list)
    s = sub.add_parser("show", help="one gotcha, every field (make gotchas ID=<id>)")
    s.add_argument("id")
    s.set_defaults(fn=cmd_show)
    d = sub.add_parser("drill", parents=[lane], help="an offline drill, or every one (make gotcha-drill)")
    d.add_argument("id", nargs="?")
    d.add_argument("--live", action="store_true", help="on the lane: pinned-traffic and deploy-drops-hotfix only")
    d.add_argument("--admin-emails", default=os.environ.get("ADMIN_EMAILS") or "",
                   help="ADMIN_EMAILS for deploy-drops-hotfix's make deploy-services")
    d.set_defaults(fn=cmd_drill)
    t = sub.add_parser("detect", parents=[lane], help="read the lane for a gotcha, or every one (make gotcha-detect)")
    t.add_argument("id", nargs="?")
    t.add_argument("--hours", type=int, default=int(os.environ.get("HOURS") or 24), help="the log window (HOURS)")
    t.set_defaults(fn=cmd_detect)
    return ap


def main(argv: list[str] | None = None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(errors="replace")
    a = build_parser().parse_args(argv)
    try:
        return int(a.fn(a) or 0)
    except Stop as e:
        sys.stdout.flush()
        print(f"STOP: {e}", file=sys.stderr)
        return STOPPED


if __name__ == "__main__":
    sys.exit(main())
