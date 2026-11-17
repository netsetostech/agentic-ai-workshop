#!/usr/bin/env python3
"""An incident's plan, from rules (workshop lesson 10.11): what make remediate runs, without make.

    python commands/remediate.py --project <id> [--service documind-chat] [--policy '<display name>'] [--since 1h]
                                 [--save FILE]                  read the lane, print the plan
    python commands/remediate.py --offline [FILE]               the same on a recorded lane state (ops/incidents/)
    python commands/remediate.py --runbooks                     every alert policy, its runbook and what remediate may do

It reads, and only reads, at Rs 0: the service's traffic and template (gcloud run services describe), its revisions
(gcloud run revisions list) and its own log lines of the window (one gcloud logging read: the request log's status and
latency, and the structured events the alert policies count), keeping a line's revision, status and event fields and
never a person, a session or any text a person wrote. Locally it reads make promote's deploy/.previous-revision and the
drill's deploy/.fault-hold (make incident-drill). Then rules decide - the first that holds - and no model is called:

    unknown_policy  POLICY= names no policy the kit's Terraform declares        no rule: page a person
    person_only     POLICY= names a policy ops/runbooks.json gives a person     its runbook, and a person decides
    split_traffic   more than one revision serves                               no rule: page a person
    bad_revision    the serving revision was created inside the window, differs from the revision before it, and fails
                    where that one did not                                      roll back, verify, restore
    no_change       it fails, and no recent change explains it                  no rule: page a person
    rolled_back     traffic is pinned to an older revision, and the newest one failed in the window: verify, restore
    pinned_clean    pinned, and the newest revision's template matches the serving one again: finish the restore
    pinned_new      pinned, and a newer revision that differs has not failed: remediate cannot tell a fix from a new
                    fault                                                       no rule: page a person
    no_failure      nothing fails                                               nothing to roll back

A revision fails on a signal when at least MIN_BAD (2) of its lines are bad and they are at least that signal's share of
its lines: a fifth (SHARE) for 5xx answers and for chat turns a limit stopped, and each alert policy's own threshold
for its own lines (ops/runbooks.json); the API's latency policy, when the p95 of at least MIN_P95 (5) requests is over
its 3,000 ms. Starting values, not yet calibrated on any lane's traffic. A revision that carries a tag and no traffic
is a candidate: what its tag URL was asked is a gate's business (lesson 11.2), never an incident's.

It PRINTS the plan: the rollback command, then the verify and the restore, each a line to paste. It runs none of it:
the person does. A policy's runbook is printed from the policy's own documentation block in terraform/*.tf, so it has
one home. --save writes what it read as a fixture for --offline, the lane's project id and number replaced by the
placeholders, and --offline then prints the same plan.

Exit codes: 0 a plan was printed (whatever it says); 2 stopped: an input or a read failed, and the message says which.
"""
from __future__ import annotations

import argparse
import collections
import datetime as dt
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import textwrap
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent                        # the kit: deploy/ here, the repository root in the learner repo
TF_DIR = KIT / "terraform"
CATALOG = KIT / "ops" / "runbooks.json"
DEFAULT_FIXTURE = KIT / "ops" / "incidents" / "held_model.json"
CHECKOUT = KIT                           # where make promote writes .previous-revision and the drill .fault-hold

PLACEHOLDER_PROJECT, PLACEHOLDER_NUMBER = "documind-ai-YOUR-ID", "NUMBER"
PROJECT_ID = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]")
NAME = re.compile(r"[a-z](?:[a-z0-9-]{0,61}[a-z0-9])?")             # a Cloud Run service or revision name
VAR = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
REGION = re.compile(r"[a-z]+-[a-z]+[0-9]+")
SINCE = re.compile(r"([1-9][0-9]{0,3})([mh])")
STOPS = ("model_calls", "turn_budget", "turn_deadline", "recursion_limit")   # services/chat/limits.py's STOPS
KEEP = ("event", "stopped_by", "surface", "arm", "method", "accepted_by", "outcome", "unanswerable_flag")
SECRETISH = re.compile(r"KEY|SECRET|TOKEN|PASSWORD|DSN|CREDENTIAL", re.I)
MIN_BAD, SHARE, MIN_P95 = 2, 0.2, 5      # remediate's own starting values (above)
LIMIT = 2000                             # log lines read; the newest first
MAX_SINCE_H = 168
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
DRILL_FAULTS = ("model", "model_calls")

# The only commands remediate runs. gcloud_json() refuses any other, so the plan it prints can never be run by it.
READS = (("gcloud", "run", "services", "describe"), ("gcloud", "run", "revisions", "list"), ("gcloud", "logging", "read"))
# What no command remediate prints may do: delete, destroy, deploy or build anything, touch a quota or a grant, or
# take a service down. Checked on every printed command's words and flags, never its values (shape_of), before printing.
NEVER = re.compile(r"\bdelete\b|\bdestroy\b|\bdeploy\b|\bbuilds?\b|\bquotas?\b|-iam-policy|\binvoker\b|\bterraform\b|"
                   r"\bexecute\b|--allow-unauthenticated|\bmake (?:up|down|plan|build|deploy-services|down-services|off|purge)\b")


class Stop(RuntimeError):
    """An input or a read failed. The message says which, and the command exits 2."""


# ---------------------------------------------------------------- the policies, from the kit's Terraform

POLICY_HEAD = re.compile(r'^resource "google_monitoring_alert_policy" "(\w+)" \{\n', re.M)


def hcl_string(text: str) -> str:
    """An HCL quoted string's value: \\" \\\\ \\n \\t unescaped, and $${ back to ${."""
    out, i = [], 0
    while i < len(text):
        if text[i] == "\\" and i + 1 < len(text):
            out.append({"n": "\n", "t": "\t", '"': '"', "\\": "\\"}.get(text[i + 1], text[i:i + 2]))
            i += 2
        else:
            out.append(text[i])
            i += 1
    return "".join(out).replace("$${", "${")


def policies(tf_dir: Path = TF_DIR) -> list[dict]:
    """Every google_monitoring_alert_policy in tf_dir/*.tf, a for_each expanded per key: its display name, its address,
    the variable its count is behind (or None) and its documentation's content (or None)."""
    out = []
    for path in sorted(tf_dir.glob("*.tf")):
        text = path.read_text(encoding="utf-8")
        for m in POLICY_HEAD.finditer(text):
            block = text[m.start():text.index("\n}\n", m.start()) + 2]
            name = m.group(1)
            display = re.search(r'^  display_name\s*=\s*"((?:[^"\\]|\\.)*)"$', block, re.M)
            if not display:
                raise Stop(f"terraform/{path.name}: policy {name} has no display_name")
            gate = re.search(r"^  count\s*=\s*var\.(\w+) \? 1 : 0$", block, re.M)
            each = re.search(r"^  for_each\s*=\s*toset\(\[([^\]]*)\]\)$", block, re.M)
            doc = re.search(r'\n  documentation \{\n    content\s*=\s*"((?:[^"\\]|\\.)*)"\n', block)
            for key in (re.findall(r'"([^"]+)"', each.group(1)) if each else [None]):
                def own(s: str) -> str:
                    return s.replace("${each.key}", key) if key else s
                out.append({"policy": own(hcl_string(display.group(1))),
                            "resource": f"terraform/{path.name} google_monitoring_alert_policy.{name}"
                                        + (f'["{key}"]' if key else ""),
                            "gate": gate.group(1) if gate else None,
                            "runbook": own(hcl_string(doc.group(1))) if doc else None})
    return out


def load_catalog(path: Path = CATALOG) -> dict:
    try:
        catalog = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Stop(f"cannot read the runbook catalog {path}: {e}") from e
    if not isinstance(catalog, dict) or not isinstance(catalog.get("policies"), list):
        raise Stop(f"{path} holds no policies list")
    return catalog


def runbooks(tf_dir: Path = TF_DIR, catalog: dict | None = None) -> list[dict]:
    """The catalog's rows joined to the policies Terraform declares, in Terraform's order. A policy with no row, or a
    row with no policy, stops: a runbook catalog that has drifted from the policies is no catalog."""
    catalog = catalog if catalog is not None else load_catalog()
    declared = policies(tf_dir)
    rows = {row.get("policy"): row for row in catalog["policies"] if isinstance(row, dict)}
    missing = [p["policy"] for p in declared if p["policy"] not in rows]
    extra = sorted(set(rows) - {p["policy"] for p in declared}, key=str)
    if missing or extra:
        raise Stop("ops/runbooks.json and terraform/*.tf disagree: "
                   + "; ".join(filter(None, [missing and "no row for " + ", ".join(missing),
                                             extra and "a row for no policy: " + ", ".join(map(str, extra))])))
    return [{**rows[p["policy"]], **p} for p in declared]


# ---------------------------------------------------------------- reading a lane: three reads, nothing else

def cause(text: str) -> str:
    lines = [line.strip() for line in (text or "").splitlines() if line.strip()]
    return next((line for line in lines if line.startswith(("ERROR:", "Error:"))), lines[0] if lines else "no error output")


def run(argv: list[str]) -> subprocess.CompletedProcess:
    """One gcloud read, its output captured, never a prompt: gcloud is found on PATH as a shell finds it."""
    exe = shutil.which(argv[0])
    if not exe:
        raise Stop(f"{argv[0]} is not on PATH: install the Google Cloud CLI, or run this in Cloud Shell")
    try:
        return subprocess.run([exe, *argv[1:]], env=dict(os.environ, CLOUDSDK_CORE_DISABLE_PROMPTS="1"),
                              stdin=subprocess.DEVNULL, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Stop(f"{' '.join(argv[:4])} could not run: {e}") from e


def gcloud_json(argv: list[str]):
    """A read as JSON. Anything but the three reads is refused before it runs."""
    if tuple(argv[:4]) not in READS and tuple(argv[:3]) not in READS:
        raise Stop(f"remediate only reads, and {' '.join(argv[:4])} is not one of its reads")
    r = run(argv)
    what = " ".join(argv[:3] if argv[1] == "logging" else argv[:4])
    if r.returncode:
        raise Stop(f"{what} failed (exit {r.returncode}): {cause(r.stderr)}")
    try:
        return json.loads(r.stdout or "null")
    except ValueError:
        raise Stop(f"{what} did not return JSON") from None


def utc(text: str) -> dt.datetime | None:
    """An RFC 3339 time as gcloud prints it (nanoseconds and Z included), in UTC; None when it is not one."""
    m = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(\.\d+)?(Z|[+-]\d\d:\d\d)", str(text or "").strip())
    if not m:
        return None
    frac = (m.group(2) or ".0")[:7].ljust(7, "0")
    zone = "+00:00" if m.group(3) == "Z" else m.group(3)
    return dt.datetime.fromisoformat(m.group(1) + frac + zone).astimezone(dt.timezone.utc)


def stamp(when: dt.datetime) -> str:
    return when.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc)


def since_delta(text: str) -> dt.timedelta:
    m = SINCE.fullmatch(str(text or "").strip())
    if not m:
        raise Stop(f"SINCE is minutes or hours, as 45m or 2h, not {text!r}")
    delta = dt.timedelta(minutes=int(m.group(1))) if m.group(2) == "m" else dt.timedelta(hours=int(m.group(1)))
    if delta > dt.timedelta(hours=MAX_SINCE_H):
        raise Stop(f"SINCE is at most {MAX_SINCE_H}h")
    return delta


def traffic_of(service: dict) -> list[dict]:
    rows = ((service or {}).get("status") or {}).get("traffic") or []
    return [{"revision": str(t.get("revisionName") or ""), "percent": int(t.get("percent") or 0),
             "latest": bool(t.get("latestRevision")), "tag": t.get("tag") or None} for t in rows if isinstance(t, dict)]


def revision_of(rev: dict) -> dict:
    """A revision as the rules compare it: when it was made, whether it is Ready, its image and digest, its environment
    (a secret as secret:NAME:VERSION) and a few settings."""
    meta, spec, status = rev.get("metadata") or {}, rev.get("spec") or {}, rev.get("status") or {}
    container = (spec.get("containers") or [{}])[0] or {}
    env = {}
    for e in container.get("env") or []:
        if isinstance(e, dict) and e.get("name"):
            ref = ((e.get("valueFrom") or {}).get("secretKeyRef") or {}) if "valueFrom" in e else None
            env[e["name"]] = f"secret:{ref.get('name', '?')}:{ref.get('key', '?')}" if ref is not None else str(e.get("value", ""))
    notes = meta.get("annotations") or {}
    limits = (container.get("resources") or {}).get("limits") or {}
    settings = {"concurrency": spec.get("containerConcurrency"), "timeout": spec.get("timeoutSeconds"),
                "service account": spec.get("serviceAccountName"), "cpu": limits.get("cpu"), "memory": limits.get("memory"),
                "min instances": notes.get("autoscaling.knative.dev/minScale"),
                "max instances": notes.get("autoscaling.knative.dev/maxScale")}
    ready = any(isinstance(c, dict) and c.get("type") == "Ready" and c.get("status") == "True"
                for c in status.get("conditions") or [])
    return {"name": str(meta.get("name") or ""), "created": str(meta.get("creationTimestamp") or ""), "ready": ready,
            "image": str(container.get("image") or ""), "digest": str(status.get("imageDigest") or ""), "env": env,
            "settings": {k: str(v) for k, v in settings.items() if v not in (None, "")}}


def milliseconds(latency) -> int | None:
    m = re.fullmatch(r"([0-9]+(?:\.[0-9]+)?)s", str(latency or ""))
    return round(float(m.group(1)) * 1000) if m else None


def line_of(entry: dict) -> dict | None:
    """One log entry reduced to what the rules count: its revision, and either a request's status, latency and whether
    it came through a tag URL, or an event's fields. Who asked is reduced to whether a service account did."""
    if not isinstance(entry, dict):
        return None
    rev = str(((entry.get("resource") or {}).get("labels") or {}).get("revision_name") or "")
    if not rev:
        return None
    http = entry.get("httpRequest")
    if isinstance(http, dict) and http.get("status") is not None:
        host = str(http.get("requestUrl") or "").split("://", 1)[-1].split("/", 1)[0]
        try:
            status = int(http.get("status"))
        except (TypeError, ValueError):
            return None
        return {"revision": rev, "status": status, "via": "tag" if "---" in host else "service",
                "ms": milliseconds(http.get("latency"))}
    payload = entry.get("jsonPayload")
    if isinstance(payload, dict) and isinstance(payload.get("event"), str):
        out = {"revision": rev}
        for key in KEEP:
            value = payload.get(key)
            if key in payload and (value is None or isinstance(value, (bool, int, float))):
                out[key] = value
            elif isinstance(value, str):
                out[key] = value[:64]
        if "user" in payload:
            out["sa"] = str(payload.get("user") or "").endswith(".iam.gserviceaccount.com")
        return out
    return None


def log_filter(project: str, service: str, since: dt.datetime, events: list[str]) -> str:
    kinds = [f'logName="projects/{project}/logs/run.googleapis.com%2Frequests"'] + [f'jsonPayload.event="{e}"' for e in events]
    return (f'resource.type="cloud_run_revision" AND resource.labels.service_name="{service}" '
            f'AND timestamp>="{stamp(since)}" AND ({" OR ".join(kinds)})')


def events_for(service: str, rows: list[dict]) -> list[str]:
    """The structured events remediate reads on service: the chat row on documind-chat, and every event an alert
    policy watching the service counts."""
    found = ["chat"] if service == "documind-chat" else []
    for row in rows:
        ev = row.get("evidence") or {}
        if service in row.get("watches", []) and ev.get("kind") == "events":
            for match in ev.get("match", []):
                if match.get("event") not in found:
                    found.append(match["event"])
    return found


def local_files(checkout: Path | None = None) -> dict:
    """make promote's record of the revision it moved traffic off, and the drill's record of the fault it holds."""
    checkout = checkout or CHECKOUT
    previous, hold = None, None
    try:
        previous = (checkout / ".previous-revision").read_text(encoding="utf-8").strip() or None
    except OSError:
        pass
    try:
        held = json.loads((checkout / ".fault-hold").read_text(encoding="utf-8"))
        if isinstance(held, dict):
            hold = {k: held.get(k) for k in ("service", "fault", "var", "revision", "previous")}
    except (OSError, ValueError):
        pass
    return {"previous_revision": previous, "hold": hold}


def read_state(project: str, region: str, service: str, policy: str | None, rows: list[dict], since: str = "1h",
               until: dt.datetime | None = None, checkout: Path | None = None) -> dict:
    """The lane's state for the rules, in the shape a fixture holds. A policy the catalog gives a person, or one the
    kit does not declare, needs nothing read: the rules decide on its name."""
    until = until or now()
    start = until - since_delta(since)
    state = {"about": f"read from the lane by make remediate on {stamp(until)}", "recorded": stamp(until),
             "project": project, "region": region, "service": service, "policy": policy,
             "since": stamp(start), "until": stamp(until), "traffic": [], "revisions": [], "lines": [],
             "lines_capped": False, "reads": 0, **local_files(checkout)}
    row = next((r for r in rows if r["policy"] == policy), None) if policy else None
    if policy and (row is None or row.get("action") == "person"):
        return state
    where = [f"--region={region}", f"--project={project}", "--format=json"]
    svc = gcloud_json(["gcloud", "run", "services", "describe", service, *where])
    revs = gcloud_json(["gcloud", "run", "revisions", "list", f"--service={service}", *where])
    entries = gcloud_json(["gcloud", "logging", "read", log_filter(project, service, start, events_for(service, rows)),
                           f"--project={project}", "--format=json", f"--limit={LIMIT}"])
    if not isinstance(svc, dict) or not isinstance(revs, list) or not isinstance(entries, list):
        raise Stop(f"gcloud did not return {service}'s service, revisions and log lines in the shape remediate reads")
    lines = [line for line in map(line_of, entries) if line]
    revisions = [revision_of(r) for r in revs if isinstance(r, dict)]
    # The project number, for --save to replace: Cloud Run's namespace, else the deterministic URLs the services'
    # environments carry (SELF_URL, RAG_API_URL: documind-x-NUMBER.REGION.run.app).
    number = str((svc.get("metadata") or {}).get("namespace") or "")
    if not number.isdigit():
        found = re.search(r"-(\d{9,})\.[a-z0-9-]+\.run\.app", json.dumps(revisions))
        number = found.group(1) if found else ""
    state.update(traffic=traffic_of(svc), revisions=revisions, lines=lines, lines_capped=len(entries) >= LIMIT, reads=3,
                 number=number)
    return state


# ---------------------------------------------------------------- a recorded state: --offline reads it, --save writes it

def load_state(path: Path) -> dict:
    if not path.is_file() and not path.is_absolute() and (KIT / path).is_file():
        path = KIT / path
    try:
        state = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as e:
        raise Stop(f"cannot read the fixture {path}: {e}") from e
    if not isinstance(state, dict):
        raise Stop(f"{path} is not a recorded lane state")
    for key, default in (("traffic", []), ("revisions", []), ("lines", []), ("policy", None), ("lines_capped", False),
                         ("previous_revision", None), ("hold", None), ("region", "us-central1")):
        state.setdefault(key, default)
    for key in ("project", "service", "since", "until"):
        if not state.get(key):
            raise Stop(f"{path} names no {key}")
    if not utc(state["since"]) or not utc(state["until"]):
        raise Stop(f"{path}: since and until are RFC 3339 times")
    state["fixture"] = str(path)
    return state


# tools/leakscan.py's patterns for a lane's identifiers, which the kit cannot import: a real project id, and a project
# number in a resource path or in a Cloud Run URL.
LEAKS = (re.compile(r"\bdocumind-ai-(?!YOUR-ID\b|live-)[a-z0-9][a-z0-9-]*"), re.compile(r"\bprojects/\d{6,}/"),
         re.compile(r"-\d{9,}\.[a-z0-9-]+\.run\.app"))


def save_state(state: dict, path: Path) -> None:
    """The state as a fixture, the lane's project id and number replaced by the placeholders the pages use; refused
    if anything that still looks like a lane's identifier is left."""
    keep = {k: v for k, v in state.items() if k not in ("reads", "number", "fixture")}
    keep["about"] = f"read from a lane by make remediate on {state['recorded']}, the project id and number replaced"
    text = json.dumps(keep, indent=1, sort_keys=False) + "\n"
    # Whole tokens only: a project id is also the start of names like <id>-audit, never the middle of a revision's.
    text = re.sub(rf"(?<![a-z0-9]){re.escape(state['project'])}(?![a-z0-9])", PLACEHOLDER_PROJECT, text)
    number = state.get("number") or ""
    if re.fullmatch(r"\d{6,}", number):
        text = re.sub(rf"(?<!\d){number}(?!\d)", PLACEHOLDER_NUMBER, text)
    left = [p.pattern for p in LEAKS if p.search(text)]
    if left:
        raise Stop(f"not saved: the state still holds what looks like a lane's identifier ({'; '.join(left)})")
    try:
        # SAVE= names evals/reports/, which is gitignored: a fresh clone has no such folder (13 October 2026).
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
    except OSError as e:
        raise Stop(f"cannot write {path}: {e}") from e


# ---------------------------------------------------------------- the rules

def signals(service: str, rows: list[dict], catalog: dict) -> list[dict]:
    """What a revision can fail on: the silent signals no policy counts, then each policy watching the service whose
    lines remediate reads. rollback: whether a failure on it can choose the rollback (else it is only reported)."""
    silent = {s["signal"]: s for s in catalog.get("silent", [])}
    out = [{"id": "5xx", "label": silent.get("5xx", {}).get("label", "5xx answers"), "kind": "status", "rollback": True,
            "silent": silent.get("5xx", {}).get("why", "")}]
    if service == "documind-chat":
        out.append({"id": "stopped", "label": silent.get("stopped", {}).get("label", "chat turns stopped by a limit"),
                    "kind": "stopped", "rollback": True, "silent": silent.get("stopped", {}).get("why", "")})
    for row in rows:
        ev = row.get("evidence") or {}
        if service in row.get("watches", []) and ev.get("kind") in ("events", "latency"):
            out.append({"id": row["policy"], "label": row["policy"], "kind": ev["kind"], "evidence": ev,
                        "rollback": row.get("action") == "rollback", "silent": "", "row": row})
    return out


def matches(line: dict, evidence: dict) -> bool:
    if evidence.get("people_only") and line.get("sa"):
        return False
    return any(all(line.get(k) == v for k, v in m.items()) for m in evidence.get("match", []))


def p95(values: list[int]) -> int:
    s = sorted(values)
    return s[max(0, int(round(0.95 * len(s))) - 1)] if s else 0


def tally(state: dict, sigs: list[dict]) -> dict:
    """Per revision: requests and their 5xx and latencies (through the service URL, and through a tag URL apart),
    chat turns and their stops, and each event signal's bad and total lines."""
    t = collections.defaultdict(lambda: {"requests": 0, "errors": 0, "ms": [], "tag_requests": 0, "tag_errors": 0,
                                         "turns": 0, "stopped": collections.Counter(), "events": {}, "lines": 0})
    event_sigs = [s for s in sigs if s["kind"] == "events"]
    for line in state.get("lines", []):
        if not isinstance(line, dict) or not isinstance(line.get("revision"), str):
            continue
        r = t[line["revision"]]
        r["lines"] += 1
        if "status" in line:
            status = line.get("status") if isinstance(line.get("status"), int) else 0
            if line.get("via") == "tag":
                r["tag_requests"] += 1
                r["tag_errors"] += status >= 500
            else:
                r["requests"] += 1
                r["errors"] += status >= 500
                if isinstance(line.get("ms"), int):
                    r["ms"].append(line["ms"])
            continue
        if line.get("event") == "chat":
            r["turns"] += 1
            if line.get("stopped_by"):
                r["stopped"][line["stopped_by"] if line["stopped_by"] in STOPS else "another limit"] += 1
        for s in event_sigs:
            ev = s["evidence"]
            if matches(line, ev):
                bad, total = r["events"].get(s["id"], (0, 0))
                is_bad = all(line.get(k) == v for k, v in (ev.get("bad") or {}).items())
                r["events"][s["id"]] = (bad + is_bad, total + 1)
    return t


def failing(r: dict, sigs: list[dict]) -> list[dict]:
    """The rollback signals a revision's tally fails on."""
    out = []
    for s in sigs:
        if not s["rollback"]:
            continue
        if s["kind"] == "status":
            bad, total, share = r["errors"], r["requests"], SHARE
        elif s["kind"] == "stopped":
            bad, total, share = sum(r["stopped"].values()), r["turns"], SHARE
        elif s["kind"] == "latency":
            if len(r["ms"]) >= MIN_P95 and p95(r["ms"]) > s["evidence"]["p95_ms"]:
                out.append(s)
            continue
        else:
            (bad, total), share = r["events"].get(s["id"], (0, 0)), float(s["evidence"].get("share", SHARE))
        if bad >= MIN_BAD and total and bad / total >= share:
            out.append(s)
    return out


def present(r: dict, sigs: list[dict]) -> list[tuple[dict, int]]:
    """The person-only signals with lines on a revision, and how many."""
    return [(s, r["events"][s["id"]][0]) for s in sigs if not s["rollback"] and s["kind"] == "events"
            and r["events"].get(s["id"], (0, 0))[0]]


def diff(new: dict, old: dict) -> list[dict]:
    """What changed from old to new: environment variables, the image (by digest when both have one), settings."""
    out = []
    for name in sorted(set(new["env"]) | set(old["env"])):
        if new["env"].get(name) != old["env"].get(name):
            out.append({"kind": "env", "name": name, "old": old["env"].get(name), "new": new["env"].get(name)})
    if (new["digest"] != old["digest"]) if (new["digest"] and old["digest"]) else (new["image"] != old["image"]):
        out.append({"kind": "image", "name": "image", "old": old["digest"] or old["image"],
                    "new": new["digest"] or new["image"]})
    for name in sorted(set(new["settings"]) | set(old["settings"])):
        if new["settings"].get(name) != old["settings"].get(name):
            out.append({"kind": "setting", "name": name, "old": old["settings"].get(name), "new": new["settings"].get(name)})
    return out


def diagnose(state: dict, rows: list[dict], catalog: dict) -> dict:
    """The rule that decides, and what it read. Never a model: the first rule that holds, in the module's order."""
    policy, service = state.get("policy"), state["service"]
    row = next((r for r in rows if r["policy"] == policy), None) if policy else None
    if policy and row is None:
        return {"rule": "unknown_policy", "page": True}
    if row is not None and row.get("action") == "person":
        return {"rule": "person_only", "row": row}
    sigs = signals(service, rows, catalog)
    revs = {r["name"]: r for r in state.get("revisions", []) if isinstance(r, dict) and r.get("name")}
    share, tags = collections.Counter(), collections.defaultdict(list)
    for x in state.get("traffic", []):
        share[x["revision"]] += x.get("percent", 0)
        if x.get("tag"):
            tags[x["revision"]].append(x["tag"])
    candidates = {name for name in tags if not share[name]}
    # The revisions that count, newest first: Ready, with a creation time, and not a candidate.
    newest = sorted((r for r in revs.values() if r["name"] not in candidates and r.get("ready", True) and utc(r["created"])),
                    key=lambda r: utc(r["created"]), reverse=True)
    t = tally(state, sigs)
    base = {"row": row, "signals": sigs, "tally": t, "candidates": sorted(candidates), "share": dict(share)}
    serving = [name for name, p in share.items() if p > 0]
    if len(serving) != 1 or serving[0] not in revs:
        return {**base, "rule": "split_traffic" if len(serving) > 1 else "no_change", "page": True,
                "why": ("traffic is split across " + ", ".join(sorted(serving)) if len(serving) > 1 else
                        "no revision remediate read takes the traffic")}
    s = revs[serving[0]]
    base["serving"] = s
    fails_s = failing(t[s["name"]], sigs)
    latest = newest[0] if newest else s
    base["latest"] = latest
    if latest["name"] == s["name"]:
        if not fails_s:
            return {**base, "rule": "no_failure"}
        created = utc(s["created"])
        before = [r for r in newest if created and utc(r["created"]) < created]
        prev = before[0] if before else None
        recorded = state.get("previous_revision")
        if service == "documind-api" and recorded and recorded in revs and recorded != s["name"]:
            prev = revs[recorded]                 # make promote's record beats creation order: a red candidate is newer
        base.update(fails=fails_s, previous=prev)
        if prev is None:
            return {**base, "rule": "no_change", "page": True, "why": f"{s['name']} fails and no revision before it is Ready"}
        if not created or created < utc(state["since"]):
            return {**base, "rule": "no_change", "page": True,
                    "why": f"{s['name']} fails, and it was created before the window: no change inside it explains the "
                           "failure (a longer SINCE= reads further back)"}
        change = diff(s, prev)
        base["change"] = change
        if not change:
            return {**base, "rule": "no_change", "page": True,
                    "why": f"{s['name']} fails, and its template is the same as {prev['name']}'s"}
        if failing(t[prev["name"]], sigs):
            return {**base, "rule": "no_change", "page": True,
                    "why": f"{prev['name']}, the revision before, fails too: the cause is not the change between them"}
        return {**base, "rule": "bad_revision"}
    change = diff(latest, s)
    base.update(change=change, fails=failing(t[latest["name"]], sigs),
                newer_candidates=sorted(c for c in candidates if c in revs and utc(revs[c]["created"])
                                        and utc(revs[c]["created"]) > utc(latest["created"])))
    if fails_s:
        return {**base, "rule": "no_change", "page": True,
                "why": f"{s['name']} takes the traffic by name and fails itself: the rollback did not help, or the "
                       "cause is not a revision"}
    if base["fails"] and change:
        return {**base, "rule": "rolled_back"}
    if not change:
        return {**base, "rule": "pinned_clean"}
    return {**base, "rule": "pinned_new", "page": True,
            "why": f"traffic is pinned to {s['name']}, and the newest revision, {latest['name']}, differs from it and has "
                   "not failed in the window: remediate cannot tell a fix from a new fault"}


# ---------------------------------------------------------------- the plan, printed

def wrap(text: str, indent: int = 2, hang: int = 0) -> list[str]:
    return textwrap.wrap(text, width=118, initial_indent=" " * indent, subsequent_indent=" " * (indent + hang),
                         break_on_hyphens=False, break_long_words=False)


def n_of(n: int, thing: str) -> str:
    return f"{n} {thing}{'' if n == 1 else 's'}"


def sentence(text: str) -> str:
    return text if text.endswith((".", ":", "?")) else text + "."


def when(text: str) -> str:
    t = utc(text)
    return f"{t:%Y-%m-%d %H:%M} UTC ({t.astimezone(IST):%H:%M} IST)" if t else "an unreadable time"


def shown(name: str, value: str | None) -> str:
    if value is None:
        return "unset"
    if value.startswith("secret:"):
        return value
    if SECRETISH.search(name):
        return "(a value, hidden: the name looks like a secret's)"
    return json.dumps(value if len(value) <= 72 else value[:69] + "...")


def change_lines(change: list[dict]) -> list[str]:
    return [f"{c['name']}: {shown(c['name'], c['old'])} -> {shown(c['name'], c['new'])}"
            if c["kind"] == "env" else f"{c['name']}: {c['old'] or 'none'} -> {c['new'] or 'none'}" for c in change]


def env_flag(flag: str, values: dict) -> str:
    joined = [f"{k}={v}" for k, v in values.items()]
    if not any("," in v for v in values.values()):
        return f"{flag}=" + ",".join(joined)
    sep = next((c for c in "@;:#~^|" if not any(c in v for v in joined)), None)
    if sep is None:
        raise Stop(f"the values of {', '.join(values)} use every delimiter gcloud accepts: set them back by hand")
    return f"{flag}=^{sep}^" + sep.join(joined)


def restore_commands(state: dict, change: list[dict]) -> tuple[list[str], list[str]]:
    """The template put back as the good revision had it, then the traffic sent to the latest revision. Returns the
    commands, and what must be set back by hand first."""
    service, where = state["service"], f"--region {state['region']} --project {state['project']}"
    updates, secrets, removes, image, by_hand = {}, {}, [], None, []
    for c in change:
        if c["kind"] == "image":
            image = c["old"]
        elif c["kind"] != "env" or not VAR.fullmatch(c["name"]):
            by_hand.append(f"{c['name']}: {c['old'] or 'none'} on the good revision, {c['new'] or 'none'} now")
        elif c["old"] is None:
            removes.append(c["name"])
        elif c["old"].startswith("secret:"):
            secrets[c["name"]] = c["old"][len("secret:"):]
        elif SECRETISH.search(c["name"]):
            by_hand.append(f"{c['name']}: its value on the good revision is not printed (the name looks like a secret's)")
        else:
            updates[c["name"]] = c["old"]
    flags = ([env_flag("--update-env-vars", updates)] if updates else []) \
        + ([env_flag("--update-secrets", secrets)] if secrets else []) \
        + (["--remove-env-vars=" + ",".join(removes)] if removes else []) + ([f"--image={image}"] if image else [])
    commands = [f"gcloud run services update {service} {where} {' '.join(shlex.quote(f) for f in flags)} --quiet"] if flags else []
    return commands + [f"gcloud run services update-traffic {service} {where} --to-latest"], by_hand


def verify_command(state: dict, catalog: dict) -> str | None:
    service = (catalog.get("services") or {}).get(state["service"]) or {}
    return service.get("verify", "").format(project=state["project"], region=state["region"]) or None


def rollback_command(state: dict, d: dict, catalog: dict) -> tuple[str, str]:
    """(the rollback, a note). A service the kit rolls back with a make target (documind-api: make rollback, which
    moves traffic to the revision deploy/.previous-revision names) gets the target when that record names the revision
    before; every other case gets the by-name form make rollback itself prints when it has no record."""
    prev, service = d["previous"]["name"], state["service"]
    make = ((catalog.get("services") or {}).get(service) or {}).get("rollback")
    recorded = state.get("previous_revision")
    if make and recorded == prev:
        return (make.format(project=state["project"], region=state["region"]),
                f"deploy/.previous-revision, which make promote wrote, names {prev}")
    note = ""
    if make and recorded:
        note = f"make rollback would move traffic to {recorded}, the revision deploy/.previous-revision names: by name instead"
    elif make:
        note = "make rollback reads deploy/.previous-revision, which make promote writes, and this checkout has none: by name"
    return (f"gcloud run services update-traffic {service} --region {state['region']} --project {state['project']} "
            f"--to-revisions {prev}=100", note)


def policy_runbook(row: dict) -> list[str]:
    head = f"  The policy's runbook ({row['resource']}, as its incidents carry it):"
    return [head] + (wrap(row["runbook"], 4) if row.get("runbook") else ["    none: the policy declares no documentation"])


def counted(r: dict, service: str) -> str:
    parts = []
    if r["requests"]:
        parts.append(f"{n_of(r['requests'], 'request')}, {r['errors']} answered 5xx ({100 * r['errors'] // r['requests']}%)")
    if service == "documind-chat" and r["turns"]:
        stops = ", ".join(f"{k} {v}" for k, v in sorted(r["stopped"].items()))
        parts.append(f"{n_of(r['turns'], 'chat turn')}, {sum(r['stopped'].values())} stopped by a limit"
                     + (f" ({stops})" if stops else ""))
    if r["tag_requests"]:
        parts.append(f"{r['tag_requests']} through a tag URL, {r['tag_errors']} 5xx")
    for name, (bad, total) in sorted(r["events"].items()):
        parts.append(f"{bad} of {total} of {name!r}'s lines")
    return "; ".join(parts) if parts else "nothing in the window"


def shape_of(command: str) -> str:
    """A printed command less its values: what it calls (gcloud run services update, make rollback) and each flag's or
    variable's name - --update-env-vars for --update-env-vars=ROLLOUT=canary-deploy, --region for --region us-central1.
    The denylist reads this shape (13 October 2026): a value a lane chose is data, and a word inside it names no action
    - on one lane an environment value ending in -deploy refused the whole plan, the rollback included."""
    words, value_next = [], False
    for token in shlex.split(command):
        if token.startswith("-"):
            words.append(token.split("=", 1)[0])
            value_next = "=" not in token                     # a bare --flag: its value may follow as the next token
        elif value_next:
            value_next = False                                # that value, dropped
        else:
            words.append(token.split("=", 1)[0])              # a word, or NAME=value with the value dropped
    return " ".join(words)


def check_printable(commands: list[str]) -> None:
    for c in commands:
        hit = NEVER.search(shape_of(c))
        if hit:
            raise Stop(f"refused to print a command that {hit.group(0)!r} names: {c}")


def lane_lines(state: dict, d: dict) -> list[str]:
    """What the lane shows: the traffic, the revisions that matter and what each answered, the change, the signals."""
    t, sigs, service = d["tally"], d["signals"], state["service"]
    s, latest, prev = d.get("serving"), d.get("latest"), d.get("previous")
    out = ["What the lane shows"]
    for x in state.get("traffic", []):
        if x.get("percent") or x.get("tag"):
            out.append(f"  traffic     {x['percent']:>3}% {x['revision']}"
                       + (" (following the latest revision)" if x.get("latest") else " (by name)" if x.get("percent") else "")
                       + (f", tag {x['tag']}" if x.get("tag") else ""))
    revs = {r["name"]: r for r in state.get("revisions", []) if isinstance(r, dict) and r.get("name")}
    listed, roles = [], {}
    for r, role in ((s, "serving"), (prev, "the revision before it"), (latest, "the newest revision, no traffic")):
        if r and r["name"] not in roles:
            listed.append(r)
            roles[r["name"]] = role
    for name in sorted(t, key=lambda n: revs.get(n, {}).get("created", ""), reverse=True):
        if name in revs and name not in roles and name not in d.get("candidates", []) and t[name]["lines"]:
            listed.append(revs[name])
            roles[name] = "no traffic"
    for r in listed:
        inside = utc(r["created"]) and utc(r["created"]) >= utc(state["since"])
        out.append(f"  revision    {r['name']}  created {when(r['created'])}{', inside the window' if inside else ''}"
                   f"  [{roles[r['name']]}]")
    for name in d.get("candidates", []):
        out.append(f"  candidate   {name}: a tag and no traffic; what its tag URL was asked is a gate's business, not an "
                   "incident's")
    for line in change_lines(d.get("change") or []):
        out.append(f"  the change  {line}")
    for r in listed:
        out.append(f"  answers     {r['name']}: {counted(t[r['name']], service)}")
    for sig in d.get("fails") or []:
        out.append(f"  signal      {sig['label']}, silent: {sig['silent']}" if sig["silent"] else
                   f"  signal      {sig['label']}: the alert policy of that name counts these lines")
    for sig, n in (present(t[s["name"]], sigs) if s else []):
        out.append(f"  also        {sig['label']}: {n_of(n, 'line')} in the window, a person's to act on: "
                   f"{sig['row']['person']}")
    if state.get("lines_capped"):
        out.append(f"  (the newest {LIMIT} lines of the window were read: the counts are theirs)")
    return out


def render(state: dict, d: dict, rows: list[dict], catalog: dict) -> list[str]:
    """The printout: the header, what the lane shows, the rule that decided, and the plan, each command a line."""
    rule, service, project = d["rule"], state["service"], state["project"]
    out: list[str] = []
    if rule in ("unknown_policy", "person_only"):
        out.append(f'remediate: the policy "{state["policy"][:120]}" on {project}')
    else:
        minutes = int((utc(state["until"]) - utc(state["since"])).total_seconds() // 60)
        out.append(f"remediate: {service} on {project} ({state['region']}), the {minutes} minutes to {when(state['until'])}")
    out.append("rules only: no model is called, and nothing on the lane is changed.")
    if state.get("fixture"):
        out.append(f"read from a recorded state: {Path(state['fixture']).name} ({state.get('about', '')[:150]})")
    out.append("")
    if rule == "unknown_policy":
        out += ["Diagnosis - rule unknown_policy", "  no rule: page a person."]
        out += wrap(f'"{state["policy"][:120]}" is not one of the {len(rows)} alert policies the kit\'s Terraform declares, '
                    "so remediate has no runbook for it and proposes nothing. make remediate RUNBOOKS=1 lists them.")
        return out + ["", "0 model calls. Nothing on the lane was read or changed."]
    if rule == "person_only":
        row = d["row"]
        gate = f" (declared only on a lane planned with {row['gate']}=true)" if row.get("gate") else ""
        out.append(f"Diagnosis - rule person_only{gate}")
        out += wrap(f"a person decides: {row['person']}. remediate proposes no action for this policy.")
        out += [""] + policy_runbook(row)
        return out + ["", "The plan: page a person, with the runbook above.", "",
                      "0 model calls. Nothing on the lane was read or changed."]
    t = d["tally"]
    s, latest, prev = d.get("serving"), d.get("latest"), d.get("previous")
    out += lane_lines(state, d) + ["", f"Diagnosis - rule {rule}"]
    steps: list[tuple[str, list[str], list[str]]] = []
    verify = verify_command(state, catalog)
    labels = ", ".join(f["label"] for f in d.get("fails") or [])
    if rule == "bad_revision":
        names = [c["name"] for c in d["change"]]
        changed = (f"only {names[0]} changed" if len(names) == 1 else
                   ", ".join(names[:-1]) + f" and {names[-1]} changed")
        before = (f"did not ({counted(t[prev['name']], service)})" if t[prev["name"]]["lines"] else
                  "answered nothing in the window, so it shows no failure")
        out += wrap(f"{s['name']} was created inside the window and fails ({labels}); {prev['name']}, the revision "
                    f"before it, {before}. Between the two, {changed}.")
        command, note = rollback_command(state, d, catalog)
        steps.append((f"Roll back: all traffic to {prev['name']}, which never went away ({s['name']} stays, at 0%).",
                      [command], [note] if note else []))
    elif rule == "rolled_back":
        out += wrap(f"traffic is on {s['name']} by name, and {latest['name']}, the newest revision, failed in the window "
                    f"({labels}): the rollback is in place.")
        steps.append((f"Roll back: done. {s['name']} takes the traffic by name.", [], []))
    elif rule == "pinned_clean":
        out += wrap(f"traffic is on {s['name']} by name, and the newest revision, {latest['name']}, has its template: the "
                    "change is undone, and the traffic waits to follow the latest revision again.")
    elif rule == "no_failure":
        out += wrap(f"{s['name']} answers without failing in the window: nothing to roll back.")
        if not t[s["name"]]["lines"]:
            out += wrap(f"It answered nothing in the window: {verify or 'its own smoke'} asks it. A line reaches Cloud "
                        "Logging a few seconds after it is written, so the last few seconds' turns may not be read yet.")
        if d.get("row"):
            out += wrap("The policy's own lines on it are under the policy's threshold in the window: its incident may "
                        "have closed, or a longer SINCE= reads further back.")
        hold = state.get("hold") or {}
        if hold.get("service") == service:
            out += wrap(f"deploy/.fault-hold still records a drill's {hold.get('var')}: make incident-drill RESTORE=1 "
                        f"PROJECT={project} puts it back and clears the record.")
    else:
        out.append("  no rule: page a person.")
        out += wrap(sentence(d.get("why", "")))
    if d.get("row"):
        out += [""] + policy_runbook(d["row"])
    if rule in ("bad_revision", "rolled_back", "pinned_clean"):
        seen = t[s["name"]] if rule != "bad_revision" else None
        heard = ([f"So far in the window, {s['name']}: {counted(seen, service)}"] if seen and seen["lines"] else [])
        steps.append(("Verify: " + ("every brain answers." if service == "documind-chat" else "the service's smoke passes."),
                      [verify] if verify else [],
                      heard + ([] if verify else [f"The kit names no smoke for {service}: read its own /health and logs"])))
        if service == "documind-api":
            steps.append(("Restore: documind-api is released through a candidate (lesson 11.3). Undo the change on a "
                          "candidate, judge it (make eval-live API=<its URL>), then make promote; until then the traffic "
                          f"stays on {prev['name'] if rule == 'bad_revision' else s['name']} by name.", [], []))
        elif rule == "pinned_clean":
            newer = d.get("newer_candidates") or []
            where = f"--region {state['region']} --project {project}"
            # --to-latest follows the newest Ready revision, a tagged candidate included: by name when one is newer.
            steps.append(("Restore: send the traffic to the latest revision.",
                          [f"gcloud run services update-traffic {service} {where} "
                           + (f"--to-revisions {latest['name']}=100" if newer else "--to-latest")],
                          [f"By name: {', '.join(newer)}, a tagged candidate, is newer, and --to-latest would send the "
                           "traffic to it"] if newer else []))
        else:
            bad, good = (latest, s) if rule == "rolled_back" else (s, prev)
            commands, by_hand = restore_commands(state, diff(bad, good))
            notes = [f"Set back by hand first: {b}" for b in by_hand]
            hold = state.get("hold") or {}
            if hold.get("service") == service and hold.get("fault") in DRILL_FAULTS:
                notes.append(f"This checkout holds the drill's fault (deploy/.fault-hold): make incident-drill RESTORE=1 "
                             f"PROJECT={project} runs both")
            steps.append(("Restore. The rollback moved traffic only: the template still carries the change, and a service "
                          "whose traffic is pinned to a revision by name leaves every later revision at 0%. Undo the change, "
                          f"then send the traffic to the latest revision, in that order (the other order sends it back to "
                          f"{bad['name']}).", commands, notes))
        again = verify or "the service's own smoke"
        steps.append((f"Verify again: {again}, then make remediate PROJECT={project} SERVICE={service}: it reads no "
                      "failure.", [], []))
    check_printable([c for _, commands, _ in steps for c in commands])
    if steps:
        out += ["", "The plan. remediate runs none of it: you do, in this order."]
        for i, (text, commands, notes) in enumerate(steps, 1):
            out += wrap(f"{i}. {text}", 2, 3)
            out += [f"       {c}" for c in commands]
            for note in notes:
                out += wrap(sentence(note), 5)
    elif d.get("page"):
        out += ["", "The plan: page a person, with what remediate read above."]
    reads = state.get("reads")
    return out + ["", "0 model calls. " + (f"remediate ran {reads} reads and changed nothing on the lane." if reads
                                           else "Nothing on the lane was changed.")]


def render_runbooks(rows: list[dict], catalog: dict) -> list[str]:
    files = collections.Counter(r["resource"].split()[0] for r in rows)
    gated = sum(1 for r in rows if r.get("gate"))
    out = [f"{len(rows)} alert policies the kit declares ({', '.join(f'{f}: {n}' for f, n in files.items())}); "
           f"{gated} behind a switch. remediate may propose a rollback for "
           f"{sum(1 for r in rows if r['action'] == 'rollback')}; the rest are a person's.", ""]
    for r in rows:
        ev = r.get("evidence") or {}
        reads = ("p95 latency over %d ms (the request log)" % ev["p95_ms"] if ev.get("kind") == "latency" else
                 "its lines: " + ", ".join(m["event"] for m in ev.get("match", [])) if ev.get("kind") == "events" else
                 "not read: " + ev.get("reads", "-"))
        out.append(f"{r['policy']}")
        out.append(f"  {r['resource']}" + (f", only with {r['gate']}=true" if r.get("gate") else "")
                   + (f"; watches {', '.join(r['watches'])}" if r.get("watches") else ""))
        out.append("  remediate: " + ("a rollback, when a revision created inside the window fails where the one before "
                                       "did not" if r["action"] == "rollback" else f"a person decides: {r['person']}"))
        out.append(f"  evidence: {reads}")
        out += wrap("runbook: " + (r.get("runbook") or "none: the policy declares no documentation"), 2)
        out.append("")
    out.append("Silent: what remediate reads that no policy watches")
    for s in catalog.get("silent", []):
        out += wrap(f"{s['label']}: {s['what']}. {s['why']}.", 2)
    return out


# ---------------------------------------------------------------- the command line

def build_parser() -> argparse.ArgumentParser:
    lines = __doc__.splitlines()
    ap = argparse.ArgumentParser(prog="remediate.py", description=lines[0], epilog="\n".join(lines[2:]),
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--project", default=os.environ.get("PROJECT") or "", help="the lane's project id (PROJECT)")
    ap.add_argument("--region", default=os.environ.get("REGION") or "us-central1", help="the services' region (REGION)")
    ap.add_argument("--service", default="", help="the Cloud Run service (default: the policy's, else documind-chat)")
    ap.add_argument("--policy", default="", help="the display name of the alert policy that paged (POLICY)")
    ap.add_argument("--since", default="1h", help="the window: minutes or hours before now, as 45m or 2h (default 1h)")
    ap.add_argument("--save", default="", help="write what was read as a fixture for --offline")
    ap.add_argument("--offline", nargs="?", const=str(DEFAULT_FIXTURE), default=None, metavar="FIXTURE",
                    help="a recorded lane state instead of the lane (default ops/incidents/held_model.json)")
    ap.add_argument("--runbooks", action="store_true", help="list every alert policy and its runbook, and stop")
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    try:
        catalog = load_catalog()
        rows = runbooks(TF_DIR, catalog)
        if a.runbooks:
            print("\n".join(render_runbooks(rows, catalog)))
            return 0
        row = next((r for r in rows if r["policy"] == a.policy), None) if a.policy else None
        if a.offline is not None:
            state = load_state(Path(a.offline))
            if a.policy:
                state["policy"] = a.policy
            service = state["service"]
        else:
            if not PROJECT_ID.fullmatch(a.project or ""):
                raise Stop("pass --project with the lane's project id (PROJECT), or --offline for a recorded state")
            if not REGION.fullmatch(a.region):
                raise Stop(f"REGION is a region name, as us-central1, not {a.region!r}")
            service = a.service or ((row or {}).get("watches") or ["documind-chat"])[0]
            if not NAME.fullmatch(service):
                raise Stop(f"SERVICE is a Cloud Run service name, not {service!r}")
        if row and row.get("action") == "rollback" and service not in row["watches"]:
            raise Stop(f"{a.policy!r} watches {', '.join(row['watches'])}, not {service}")
        if a.offline is None:
            state = read_state(a.project, a.region, service, a.policy or None, rows, a.since)
        # The plan is rendered, and every command in it checked, before anything is saved: a state whose plan stops
        # is not written as a fixture (13 October 2026: it was saved first, and only an identifier leak stopped a save).
        plan = render(state, diagnose(state, rows, catalog), rows, catalog)
        if a.save and a.offline is None:
            save_state(state, Path(a.save))
        print("\n".join(plan))
        if a.save and a.offline is None:
            print(f"saved: {a.save} (make remediate OFFLINE=1 FIXTURE={a.save} prints this plan again)")
        return 0
    except Stop as e:
        sys.stdout.flush()
        print(f"STOP: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
