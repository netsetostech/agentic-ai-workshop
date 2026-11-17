#!/usr/bin/env python3
"""Probe Vertex AI Agent Engine on the author's own lane before lesson 10.9 claims any fact about it.

PR 10.9-A of plan/cohort-2-lesson-plan-2026-10-07.md. The author runs it in batch 0 (Mon 19 - Wed 21 Oct 2026),
and lesson 10.9 ("Run the peer on Google's managed agent platform") states only what it observed. It lives in
the authoring repo only: tools/publish_learner.py publishes deploy/ and nothing else, so no learner receives it.

    python tools/probe_agent_stack.py --project documind-ai-YOUR-ID              # a dry run: every call printed, none made
    python tools/probe_agent_stack.py --project documind-ai-YOUR-ID --run-note   # the prerequisites and commands only
    python tools/probe_agent_stack.py --project $PROJECT --yes                   # the run, about 20 to 30 minutes
    python tools/probe_agent_stack.py --project $PROJECT --cleanup --yes         # delete what an interrupted run left

Twelve facts, each recorded as observed (the API did it on this run), refused (the API said no, in its own words)
or not tested (with the reason):
   1 instances in us-central1 and asia-south1        7 the spans the default telemetry writes, content off
   2 documind-agent-sa as the runtime's account,     8 per-resource IAM, or any principal with aiplatform.user
     and the grant its service agent needs           9 one user reading another user's managed session
   3 min_instances 0 and max_instances 1            10 Memory Bank in each region
   4 idle billing, and first-call latency           11 google-cloud-aiplatform[agent_engines] beside google-adk
   5 an ID token for documind-mcp's audience           2.8.0 (a pip resolution the author runs)
   6 the runtime's GOOGLE_CLOUD_LOCATION            12 the prices, with the date read (the author)

Nothing is called without --yes. Each step stands alone, so one refusal never stops the rest. Every resource the
run creates is deleted in a finally block, by name, and read back until it is gone; the summary lists anything
left behind with its delete command. The facts table goes to plan/agent-engine-probe-<date>.md with every
identifier replaced (Scrubber), and is written only when tools/leakscan.py finds nothing in it.

The calls follow google-adk 2.8.0 wherever ADK makes them itself - the create, the deploy, the delete, the
sessions and Memory Bank - and each is marked "verified" with its file and line in the installed package.
google-cloud-aiplatform is not in the kit's pins, so every call ADK does not make is written against Google's
documentation and marked "unverified" with the page it follows.
"""
from __future__ import annotations

import argparse
import asyncio
import contextlib
import dataclasses
import datetime as dt
import io
import itertools
import json
import re
import secrets
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from tools.leakscan import PATTERNS as LEAK_PATTERNS, deny_strings, scan_text  # noqa: E402

PLACEHOLDER = "documind-ai-YOUR-ID"
DEFAULT_REGIONS = ("us-central1", "asia-south1")
RUNTIME_REGION = "asia-south1"     # where the course lane runs: the lessons deploy with REGION=asia-south1
PREFIX = "documind-probe-"         # every display name this probe gives; --cleanup deletes only these
APP_NAME = "documind_probe"        # the deployed ADK app: a Python identifier, because ADK's loader imports it
AGENT_SA = "documind-agent-sa"     # decision 13: the cohort reuses the A2A peer's account (terraform/sa.tf)
MEMBER_SA = "documind-ui-sa"       # roles/aiplatform.user at project scope (sa.tf ui_roles); make operators mints it
OUTSIDER_SA = "documind-outsider-sa"   # no project role at all (sa.tf outsider_roles = [])
MODEL = "gemini-3.6-flash"
SESSION_TTL = "900s"
NO_MODEL = "[no-model]"            # a query carrying this gets the facts only: no Gemini call in the runtime
STATUSES = ("observed", "refused", "not tested")
CLOUD_PLATFORM = "https://www.googleapis.com/auth/cloud-platform"
PRICING_URL = "https://cloud.google.com/products/gemini-enterprise-agent-platform/pricing"
ACT_AS = ("iam.serviceAccounts.actAs", "iam.serviceAccounts.getAccessToken", "iam.serviceAccounts.getOpenIdToken")
# The deploy page's list: env_vars may not set these, and the GOOGLE_CLOUD_AGENT_ENGINE prefix is the platform's.
RESERVED_ENV = frozenset({"GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_QUOTA_PROJECT", "GOOGLE_CLOUD_LOCATION", "PORT",
                          "K_SERVICE", "K_REVISION", "K_CONFIGURATION", "GOOGLE_APPLICATION_CREDENTIALS"})

# Google's pages were read on 2026-10-08 (each "last updated 2026-10-07"); every unverified call names its page. During
# 2026 Google renamed Agent Engine to Agent Runtime, on the Gemini Enterprise Agent Platform, and its newer SDK calls
# the namespace client.runtimes. google-adk 2.8.0 still calls vertexai.Client(...).agent_engines, and so does this.
DOC_SETUP = "https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/setup"

# (row, the fact, how this probe settles it)
ROWS = [
    ("1", "Instances can be created in us-central1 and asia-south1",
     "client.agent_engines.create() in each --region, the call `adk deploy agent_engine` itself makes "
     "(google-adk 2.8.0 cli/cli_deploy.py:1430): an empty instance named documind-probe-..., deleted at the end."),
    ("2", "documind-agent-sa is accepted as the runtime's service account, and the grant the service agent needs on it",
     "ADK's own deploy (cli_deploy.to_agent_engine) with service_account in .agent_engine_config.json. The runtime's "
     "metadata server names the account it runs as. The account's IAM policy is read before and after the deploy, "
     "your actAs is checked with testIamPermissions, and a refusal's permission is named with the role that grants it."),
    ("3", "min_instances 0 and max_instances 1 are accepted",
     "Sent in the same deploy's config; the instance is then read back with GET."),
    ("4", "Whether an idle instance bills, and the first-call latency",
     "Idle billing: the instance's min_instances as read back, with the pricing page's own line (the author reads "
     "it). Latency: from the request to the first streamed event and to the last, on the first call after the deploy "
     "(after --idle-wait seconds, when given) and on a second call."),
    ("5", "The runtime's metadata server mints an ID token for documind-mcp's audience",
     "The probe agent asks the metadata server, then google.oauth2.id_token.fetch_id_token (the peer's own call, "
     "deploy/services/agent/agent.py _mcp_headers); it returns the token's claims, never the token, and knocks on "
     "documind-mcp's /health with it (401 is the token, 403 is IAM)."),
    ("6", "The runtime's GOOGLE_CLOUD_LOCATION",
     "The probe agent reports its environment, then asks Gemini one word on that location and on global "
     "(GlobalGemini, google-adk 2.8.0 models/google_llm.py:104-121)."),
    ("7", "The spans the default telemetry writes, with message content off",
     "Deployed with otel_to_cloud, so ADK sets GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY=true and "
     "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false (cli_deploy.py:1273-1282). Cloud Trace is read for the queries' "
     "window, and a marker sent in the message is looked for in every span label."),
    ("8", "Per-resource IAM on an instance, or any principal with aiplatform.user may query it",
     "getIamPolicy on the instance; then one query as documind-ui-sa (roles/aiplatform.user on the project, nothing "
     "on the instance) and one as documind-outsider-sa (no roles), each minted by impersonation."),
    ("9", "One user reading another user's managed session (VertexAiSessionService)",
     "ADK 2.8.0's VertexAiSessionService creates a session for one user (ttl 900 s) and appends an event; a get as "
     "another user follows, then the raw sessions.get that ADK itself makes, which names no user, and a list with no "
     "user."),
    ("10", "Memory Bank is available in the region",
     "ADK 2.8.0's VertexAiMemoryBankService on each region's empty instance: add_memory (memories.create), then "
     "search_memory (memories.retrieve), polled for 60 s."),
    ("11", "google-cloud-aiplatform[agent_engines] resolves beside google-adk 2.8.0",
     "The author's pip resolution (the run note prints the commands); this run's own venv versions and pip check; the "
     "versions ADK's deploy installed in the runtime image."),
    ("12", "The prices, with the date they were read",
     "The author reads the pricing page and fills the AUTHOR lines; the script states no price."),
]
ROW_IDS = [r[0] for r in ROWS]

STEPS = ("preflight", "instances", "sessions", "memory", "runtime", "access", "telemetry", "author")
STEP_TITLES = {
    "preflight": "the SDKs in this venv (row 11)",
    "instances": "an empty instance per region (row 1)",
    "sessions": "one user's session, read as another (row 9)",
    "memory": "Memory Bank per region (row 10)",
    "runtime": "the probe agent on documind-agent-sa, min 0 max 1 (rows 2-6)",
    "access": "who may query the instance (row 8)",
    "telemetry": "the spans in Cloud Trace (row 7)",
    "author": "what the author reads from the pricing page (rows 4, 12)",
}
STEP_ROWS = {"preflight": ("11",), "instances": ("1",), "sessions": ("9",), "memory": ("10",),
             "runtime": ("2", "3", "4", "5", "6"), "access": ("8",), "telemetry": ("7",), "author": ("4", "12")}
NEEDS = {"sessions": ("instances",), "memory": ("instances",), "access": ("runtime",), "telemetry": ("runtime",)}

COST_NOTE = (
    "Cost note. A live run creates, and then deletes: one empty Agent Engine instance per --region, and one runtime "
    "instance in the runtime region with min_instances 0 and max_instances 1, built once from ADK's own Dockerfile. "
    "It sends four queries, about four Gemini Flash calls of a few tokens, one session, and one memory per region, "
    "and reads IAM and Cloud Trace. Expect a few rupees (the plan's estimate for batch 0). No Agent Engine price is "
    "stated here: the 2026 SKUs are re-read by the author (row 12). Nothing is created without --yes; everything "
    "created is deleted in a finally block, and the summary lists anything left behind with its delete command.")


# ------------------------------------------------------------------------------------------------ scrubbing

_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")
_SECRETS = [
    (re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY-----.*?(?:-----END [A-Z ]*PRIVATE KEY-----|$)", re.S), "[REDACTED KEY]"),
    (re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]*"), "[REDACTED TOKEN]"),
    (re.compile(r"\bya29\.[0-9A-Za-z_\-]+"), "[REDACTED TOKEN]"),
    (re.compile(r"AIza[0-9A-Za-z_\-]{35}"), "[REDACTED KEY]"),
    (re.compile(r"(?i)(bearer\s+)[A-Za-z0-9._~+/-]{16,}=*"), r"\1[REDACTED TOKEN]"),
]


def _keep_email(address: str) -> bool:
    """Service accounts stay (their project is the placeholder by now); a person's address becomes "yours"."""
    domain = address.rsplit("@", 1)[-1].lower()
    return domain.endswith("gserviceaccount.com") or domain == "example.com" or domain.endswith(".example.com")


class Scrubber:
    """Every identifier out of a text: the facts table, the console and the evidence all pass through it.

    The project id becomes documind-ai-YOUR-ID and the project number NUMBER (CLAUDE.md's placeholders), instance
    and session ids ENGINE_ID and SESSION_ID, a person's email "yours", a home directory YOU, and a token or key a
    REDACTED marker. Whatever tools/leakscan.py would still refuse is redacted last, and so are your PUBLISH_DENY
    strings. Numbers are learned from resource names as they pass, so a bare project number is caught too. Text is
    scrubbed whole and only then cut, so a cut never leaves half an identifier behind.
    """

    def __init__(self, project: str):
        self.project = project
        self.numbers: set[str] = set()
        self.engines: set[str] = set()
        self.sessions: set[str] = set()
        self.home = str(Path.home())

    def learn(self, text) -> None:
        text = str(text or "")
        self.numbers.update(m.group(1) for m in re.finditer(r"projects/(\d{8,})(?!\d)", text))
        self.engines.update(m.group(1) for m in re.finditer(r"reasoningEngines/(\d{6,})", text))
        self.sessions.update(m.group(1) for m in
                             re.finditer(r"reasoningEngines/[^/\s]+/sessions/([A-Za-z0-9_-]{6,})", text))

    def learn_number(self, number) -> None:
        number = str(number if number is not None else "").strip()
        if number.isdigit() and len(number) >= 8:
            self.numbers.add(number)

    def learn_session(self, session_id) -> None:
        session_id = str(session_id or "")
        if len(session_id) >= 6 and re.fullmatch(r"[A-Za-z0-9_-]+", session_id):
            self.sessions.add(session_id)

    def __call__(self, text) -> str:
        if text is None:
            return ""
        text = str(text)
        self.learn(text)
        for rx, repl in _SECRETS:
            text = rx.sub(repl, text)
        # a home directory names a person
        for home in {self.home, self.home.replace("\\", "/"), self.home.replace("\\", "\\\\")}:
            if len(home) > 3:
                text = text.replace(home, "~")
        text = re.sub(r"(?i)\b([A-Z]:(?:\\\\|\\|/)Users(?:\\\\|\\|/))[^\\/\s\"':]+", r"\1YOU", text)
        text = re.sub(r"(/home/|/Users/)[^/\s\"':]+", r"\1YOU", text)
        # resource ids before numbers, so an instance id is never read as a project number
        text = re.sub(r"reasoningEngines/\d+", "reasoningEngines/ENGINE_ID", text)
        text = re.sub(r"(reasoningEngines/[A-Za-z0-9_]+/sessions/)[A-Za-z0-9_-]+", r"\1SESSION_ID", text)
        text = re.sub(r"(reasoningEngines/[A-Za-z0-9_]+/memories/)[A-Za-z0-9_-]+", r"\1MEMORY_ID", text)
        text = re.sub(r"operations/\d+", "operations/OPERATION_ID", text)
        for engine in sorted(self.engines, key=len, reverse=True):
            text = re.sub(rf"(?<!\d){engine}(?!\d)", "ENGINE_ID", text)
        for session in sorted(self.sessions, key=len, reverse=True):
            text = re.sub(rf"(?<![A-Za-z0-9_-]){re.escape(session)}(?![A-Za-z0-9_-])", "SESSION_ID", text)
        # the project id wherever it stands, glued to other text included (a URL-encoded path is %2F + id), then its number
        if self.project and self.project != PLACEHOLDER:
            text = text.replace(self.project, PLACEHOLDER)
        for number in sorted(self.numbers, key=len, reverse=True):
            text = re.sub(rf"(?<!\d){number}(?!\d)", "NUMBER", text)
        text = re.sub(r"projects/\d{6,}", "projects/NUMBER", text)
        text = re.sub(r"service-\d{6,}@", "service-NUMBER@", text)
        text = re.sub(r"\b\d{6,}-compute@", "NUMBER-compute@", text)
        text = re.sub(r"-\d{6,}(\.[a-z0-9-]+\.run\.app)", r"-NUMBER\1", text)
        text = re.sub(r"(?<![\w.-])\d{12}(?![\w.-])", "NUMBER", text)      # project numbers are twelve digits
        text = _EMAIL.sub(lambda m: m.group(0) if _keep_email(m.group(0)) else "yours", text)
        for what, rx in LEAK_PATTERNS:
            text = rx.sub(f"[REDACTED: {what}]", text)
        for denied in deny_strings():
            text = text.replace(denied, "[REDACTED]")
        return text


# --------------------------------------------------------------------------------------- errors and findings

class Refused(Exception):
    """The API said no: its HTTP status and its own words."""

    def __init__(self, status: int, body: str = ""):
        self.status, self.body = status, str(body or "")
        super().__init__(f"HTTP {status}: {api_message(self.body)}")


class NotTested(Exception):
    """A precondition was missing, so the fact was not tested. The message names it."""


def trim(text, limit: int = 600) -> str:
    text = str(text if text is not None else "").strip()
    return text if len(text) <= limit else text[:limit] + " ... [trimmed]"


def tail(text, limit: int = 600) -> str:
    text = str(text or "").strip()
    return text if len(text) <= limit else "[trimmed] ... " + text[-limit:]


def api_message(body) -> str:
    """The API's own message out of an error body, or its first line. Never cut here: see Scrubber."""
    body = str(body or "").strip()
    try:
        parsed = json.loads(body)
        if isinstance(parsed, list) and parsed:
            parsed = parsed[0]
        error = parsed.get("error", parsed) if isinstance(parsed, dict) else {}
        message = error.get("message") if isinstance(error, dict) else None
        if message:
            status = error.get("status")
            return f"{status}: {message}" if status else str(message)
    except (ValueError, AttributeError):
        pass
    return body.splitlines()[0] if body else ""


_API_MODULES = ("google.api_core", "google.genai", "google.cloud", "vertexai", "requests")


def classify(error: BaseException) -> tuple[str, str, str]:
    """(status, finding, evidence) for an exception: refused when the API or the SDK said no, else not tested.
    Whole texts: the Recorder scrubs them first and cuts them after."""
    if isinstance(error, NotTested):
        return "not tested", str(error), ""
    if isinstance(error, Refused):
        return "refused", f"HTTP {error.status}: {api_message(error.body)}", error.body
    if isinstance(error, ImportError):
        return "not tested", f"not importable in this venv: {error}", ""
    kind, module, text = type(error).__name__, type(error).__module__, str(error)
    if kind == "ValidationError":
        return "refused", "the SDK refused the request before sending it: " + text, text
    if module.startswith(_API_MODULES) or kind in {"ClientError", "ServerError", "APIError", "PermissionDenied",
                                                    "InvalidArgument", "FailedPrecondition", "NotFound", "Forbidden"}:
        return "refused", f"{kind}: {text}", text
    return "not tested", f"the step stopped on {kind}: {text}", text


@dataclasses.dataclass
class Part:
    row: str
    label: str
    status: str
    finding: str
    evidence: str = ""


class Recorder:
    """What each row found, part by part, scrubbed as it is recorded and only then cut to length. In a dry run every
    part is "not tested", because nothing was called."""

    def __init__(self, dry_run: bool, scrub=str):
        self.dry_run, self.scrub = dry_run, scrub
        self.parts: list[Part] = []

    def add(self, row: str, label: str, status: str, finding: str, evidence: str = "", *, keep_end: bool = False,
            limit: int = 600) -> None:
        if row not in ROW_IDS or status not in STATUSES:
            raise ValueError(f"row {row!r} status {status!r}")
        if self.dry_run:
            status, finding, evidence = "not tested", "dry run: nothing was called", ""
        evidence = self.scrub(evidence)
        self.parts.append(Part(row, label, status, trim(self.scrub(finding), 900),
                               tail(evidence, limit) if keep_end else trim(evidence, limit)))

    def for_row(self, row: str) -> list[Part]:
        return [p for p in self.parts if p.row == row]

    def status(self, row: str) -> str:
        """One status when every part agrees; else each status with the parts it covers, e.g.
        "observed (us-central1); refused (asia-south1)"."""
        parts = self.for_row(row)
        if not parts:
            return "not tested"
        groups: dict[str, list[str]] = {}
        for part in parts:
            groups.setdefault(part.status, []).append(part.label or "part")
        if len(groups) == 1:
            return parts[0].status
        return "; ".join(f"{status} ({', '.join(labels)})" for status, labels in groups.items())


@dataclasses.dataclass
class Resource:
    kind: str        # instance, session or memory (a session or memory goes with its instance's forced delete)
    name: str
    region: str
    user: str = ""
    parent: str = ""
    sid: str = ""


def region_of(name: str) -> str:
    m = re.match(r"projects/[^/]+/locations/([^/]+)/", str(name or ""))
    return m.group(1) if m else ""


def engine_id(name: str) -> str:
    return str(name or "").rstrip("/").rsplit("/", 1)[-1]


def endpoint(name: str) -> str:
    return f"https://{region_of(name)}-aiplatform.googleapis.com"


def sdk(project: str, region: str) -> str:
    return f"vertexai.Client(project={project!r}, location={region!r})"


def sa_email(account: str, project: str) -> str:
    return account if "@" in account else f"{account}@{project}.iam.gserviceaccount.com"


def dumps(obj) -> str:
    return json.dumps(obj, sort_keys=True, default=str)


def pick(obj, *keys):
    """The first of keys (camelCase or snake_case) found anywhere in a JSON-like object."""
    wanted = set(keys)
    stack = [obj]
    while stack:
        item = stack.pop(0)
        if isinstance(item, dict):
            for key, value in item.items():
                if key in wanted:
                    return value
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    return None


# ------------------------------------------------------------------------------ the agent the runtime runs

# ADK's deploy stages this as agents/documind_probe/agent.py in ADK's own Dockerfile (python:3.11-slim,
# google-adk[a2a]==2.8.0, `adk api_server --a2a`). The probe only ever reads what it returns.
AGENT_SOURCE = r'''"""documind_probe: the tiny ADK agent tools/probe_agent_stack.py deploys to Agent Engine (authoring repo only).

A message first gets one LlmAgent turn on Gemini at location global, which calls probe_tool once, so the default
telemetry writes its model and tool spans. Then one event of runtime facts (PROBE_FACTS <json>), gathered in Python
with no model, so the facts never depend on what a model decides. A message carrying [no-model] gets the facts only.
It never returns a token: only the claims a token carries.
"""
from __future__ import annotations

import asyncio
import base64
import importlib.metadata
import json
import os
import urllib.error
import urllib.parse
import urllib.request
from functools import cached_property

from google.adk.agents import BaseAgent, LlmAgent
from google.adk.events import Event
from google.adk.models.google_llm import Gemini
from google.genai import Client, types

MODEL = os.environ.get("PROBE_MODEL", "gemini-3.6-flash")
METADATA = os.environ.get("PROBE_METADATA_URL", "http://metadata.google.internal/computeMetadata/v1/")
NO_MODEL = "[no-model]"
ENV_VALUES = ("GOOGLE_CLOUD_LOCATION", "GOOGLE_CLOUD_REGION", "GOOGLE_GENAI_USE_ENTERPRISE", "GOOGLE_GENAI_USE_VERTEXAI",
              "GOOGLE_CLOUD_AGENT_ENGINE_ENABLE_TELEMETRY", "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS",
              "OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT", "PROBE_MODEL", "PROBE_MCP_REGION")
ENV_PREFIXES = ("GOOGLE_", "K_", "OTEL_", "ADK_", "PROBE_", "CLOUD_")


def _trim(error: BaseException) -> str:
    return f"{type(error).__name__}: {error}"[:400]


def _metadata(path: str, timeout: float = 3.0) -> str:
    # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/runtime-contract
    #   (a Cloud Run style metadata server: email, numeric-project-id, identity?audience=)
    request = urllib.request.Request(METADATA + path, headers={"Metadata-Flavor": "Google"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode()


def _claims(token: str) -> dict:
    """What a probe may report about an ID token. Never the token: it is a bearer credential for an hour."""
    payload = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4)))
    return {"aud": claims.get("aud"), "email": claims.get("email"), "iss": claims.get("iss"),
            "lifetime_s": int(claims.get("exp", 0)) - int(claims.get("iat", 0))}


def _version(dist: str):
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return None


def runtime_facts(with_model: bool = True) -> dict:
    facts = {"env": {name: os.environ.get(name) for name in ENV_VALUES},
             "env_names": sorted(name for name in os.environ if name.startswith(ENV_PREFIXES)),
             "versions": {d: _version(d) for d in ("google-adk", "google-cloud-aiplatform", "google-genai", "google-auth")},
             "metadata": {}}
    for key, path in (("service_account", "instance/service-accounts/default/email"),
                      ("project_number", "project/numeric-project-id")):
        try:
            facts["metadata"][key] = _metadata(path)
        except Exception as error:
            facts["metadata"][key + "_error"] = _trim(error)
    number = facts["metadata"].get("project_number")
    audience = os.environ.get("PROBE_MCP_URL") or (
        f"https://documind-mcp-{number}.{os.environ.get('PROBE_MCP_REGION', 'asia-south1')}.run.app" if number else "")
    facts["audience"] = audience
    token = None
    try:            # the metadata server, asked directly
        minted = _metadata("instance/service-accounts/default/identity?audience=" + urllib.parse.quote(audience, safe=""))
        facts["id_token_metadata"] = {"minted": True, **_claims(minted)}
        token = minted
    except Exception as error:
        facts["id_token_metadata"] = {"minted": False, "error": _trim(error)}
    try:            # the peer's own call: deploy/services/agent/agent.py _mcp_headers
        import google.auth.transport.requests
        import google.oauth2.id_token
        minted = google.oauth2.id_token.fetch_id_token(google.auth.transport.requests.Request(), audience)
        facts["id_token_fetch"] = {"minted": True, **_claims(minted)}
        token = minted
    except Exception as error:
        facts["id_token_fetch"] = {"minted": False, "error": _trim(error)}
    if token and audience:      # documind-mcp's door: 401 is the token, 403 is IAM, anything else got past both
        # verified: GET /health is documind-mcp's own route (deploy/services/mcp, @mcp.custom_route("/health"))
        knock = urllib.request.Request(audience.rstrip("/") + "/health", headers={"Authorization": "Bearer " + token})
        try:
            with urllib.request.urlopen(knock, timeout=20) as response:
                facts["mcp_door"] = {"status": response.status}
        except urllib.error.HTTPError as error:
            facts["mcp_door"] = {"status": error.code}
        except Exception as error:
            facts["mcp_door"] = {"error": _trim(error)}
    if with_model:
        facts["gemini"] = {}
        for label, location in (("environment", None), ("global", "global")):
            kwargs = {"enterprise": True}
            if location:
                kwargs["location"] = location
            try:
                reply = Client(**kwargs).models.generate_content(model=MODEL, contents="Reply with the single word ok.")
                facts["gemini"][label] = {"answered": True, "text": (reply.text or "")[:20]}
            except Exception as error:
                facts["gemini"][label] = {"answered": False, "error": _trim(error)}
    return facts


class GlobalGemini(Gemini):
    """Gemini 3.x is served only from location global, and the runtime's location is its region: the subclass
    google-adk 2.8.0 documents for exactly this (google/adk/models/google_llm.py, the Gemini class docstring)."""

    @cached_property
    def api_client(self) -> Client:
        return Client(enterprise=True, location="global")


def probe_tool(marker: str) -> dict:
    """Says whether a marker arrived, so the trace holds one tool call. The marker is the user's message: if message
    content were captured, it would appear in this span's attributes."""
    return {"marker_received": bool(marker)}


class ProbeAgent(BaseAgent):
    """The model turn first, while the session holds only the user's message, so the model reads the marker; then
    the facts, which are Python's and never the model's."""

    def _event(self, ctx, text: str) -> Event:
        return Event(author=self.name, invocation_id=ctx.invocation_id, branch=ctx.branch,
                     content=types.Content(role="model", parts=[types.Part(text=text)]))

    async def _run_async_impl(self, ctx):
        parts = (ctx.user_content.parts or []) if ctx.user_content else []
        with_model = NO_MODEL not in " ".join(part.text or "" for part in parts)
        if with_model:
            try:
                async for event in self.sub_agents[0].run_async(ctx):
                    yield event
            except Exception as error:      # reported, not raised: the facts still go out
                yield self._event(ctx, "PROBE_MODEL_ERROR " + _trim(error))
        facts = await asyncio.to_thread(runtime_facts, with_model)
        yield self._event(ctx, "PROBE_FACTS " + json.dumps(facts, sort_keys=True))


root_agent = ProbeAgent(
    name="documind_probe",
    description="Reports the Agent Engine runtime's identity, location and token minting for tools/probe_agent_stack.py.",
    sub_agents=[LlmAgent(
        name="probe_model",
        model=GlobalGemini(model=MODEL),
        instruction="Call probe_tool exactly once, passing the marker that appears in the user's message "
                    "(a word starting with pm). Then reply with the single word: ok.",
        tools=[probe_tool],
    )],
)
'''


def deploy_inputs(args, project: str) -> tuple[dict, dict]:
    """The deploy's .agent_engine_config.json and .env, as data (the dry run prints them; a live run stages them).

    ADK reads the config file and passes its keys to agent_engines.update(config=...) unread (google-adk 2.8.0
    cli/cli_deploy.py:1154-1159, :1439); the keys themselves follow Google's deploy page.
    """
    # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/deploy-an-agent
    #   (service_account; min_instances in [0, 10], default 1; max_instances in [1, 1000], default 100)
    config = {"service_account": sa_email(args.service_account, project), "min_instances": 0, "max_instances": 1}
    env = {"PROBE_MODEL": args.model, "PROBE_MCP_REGION": args.mcp_region}
    if args.mcp_url:
        env["PROBE_MCP_URL"] = args.mcp_url
    # .env's GOOGLE_CLOUD_LOCATION would become the deploy region AND stay in env_vars (cli_deploy.py:1247-1258),
    # and the platform reserves it; nothing reserved goes in.
    assert not RESERVED_ENV & set(env) and not any(k.startswith("GOOGLE_CLOUD_AGENT_ENGINE") for k in env)
    return config, env


def stage_agent(root: Path, config: dict, env: dict) -> tuple[Path, Path, Path]:
    """The agent folder ADK's deploy copies, and its config and .env beside it rather than inside it, so they are not
    shipped in the source package. ADK checks both paths after changing directory, so they are absolute."""
    folder = root / APP_NAME
    folder.mkdir(parents=True)
    (folder / "__init__.py").write_text("from . import agent\n", encoding="utf-8", newline="\n")
    (folder / "agent.py").write_text(AGENT_SOURCE, encoding="utf-8", newline="\n")
    side = root / "deploy_config"
    side.mkdir()
    config_file, env_file = side / ".agent_engine_config.json", side / ".env"
    config_file.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
    env_file.write_text("".join(f"{k}={v}\n" for k, v in env.items()), encoding="utf-8", newline="\n")
    return folder.resolve(), env_file.resolve(), config_file.resolve()


# ---------------------------------------------------------------------------------- reading what came back

def stream_events(lines) -> list:
    """A streamQuery reply, one JSON event per line or per `data:` line."""
    events = []
    for line in lines:
        text = str(line).strip()
        if text.startswith("data:"):
            text = text[5:].strip()
        if not text or text == "[DONE]":
            continue
        try:
            events.append(json.loads(text))
        except ValueError:
            events.append({"unparsed": text})
    return events


def _texts(obj):
    if isinstance(obj, dict):
        for key, value in obj.items():
            if key == "text" and isinstance(value, str):
                yield value
            else:
                yield from _texts(value)
    elif isinstance(obj, list):
        for value in obj:
            yield from _texts(value)


def probe_facts(events) -> tuple[dict | None, str | None, list[str]]:
    """(the PROBE_FACTS json, the model turn's error, the other texts) out of the agent's events."""
    facts, model_error, texts = None, None, []
    for text in (t for event in events or [] for t in _texts(event)):
        if text.startswith("PROBE_FACTS "):
            try:
                facts = json.loads(text[len("PROBE_FACTS "):])
            except ValueError:
                facts = {"unparsed": text}
        elif text.startswith("PROBE_MODEL_ERROR "):
            model_error = text[len("PROBE_MODEL_ERROR "):]
        else:
            texts.append(text)
    return facts, model_error, texts


def deployment_view(instance: dict) -> dict:
    """The deployment fields of a GET reasoningEngines reply. proto3 JSON leaves out a zero, so minInstances 0 and an
    unset minInstances read alike; the caller says so rather than guessing."""
    view = {}
    for camel, snake in (("serviceAccount", "service_account"), ("minInstances", "min_instances"),
                         ("maxInstances", "max_instances"), ("resourceLimits", "resource_limits"),
                         ("containerConcurrency", "container_concurrency")):
        value = pick(instance, camel, snake)
        if value is not None:
            view[camel] = value
    env = pick(instance, "env", "envVars", "env_vars")
    if isinstance(env, list):
        view["env"] = sorted(str(e.get("name")) for e in env if isinstance(e, dict))
    elif isinstance(env, dict):
        view["env"] = sorted(env)
    return view


def grant_hint(text: str, sa: str) -> str:
    """The permission a refusal names, and the role that carries it, as a command the author can run."""
    perm = re.search(r"iam\.serviceAccounts\.(actAs|getAccessToken|getOpenIdToken|signBlob|signJwt|implicitDelegation)",
                     text or "")
    if not perm:
        return ""
    role = "roles/iam.serviceAccountUser" if perm.group(1) == "actAs" else "roles/iam.serviceAccountTokenCreator"
    who = re.search(r"service-\d+@gcp-sa-[a-z-]+\.iam\.gserviceaccount\.com", text or "")
    member = f"serviceAccount:{who.group(0)}" if who else "PRINCIPAL-NAMED-IN-THE-REFUSAL"
    return (f"the refusal names {perm.group(0)}{' for ' + who.group(0) if who else ''}: grant {role} on {sa}: "
            f"gcloud iam service-accounts add-iam-policy-binding {sa} --member={member} --role={role}")


def bindings(policy) -> set[tuple[str, str]]:
    out = set()
    for binding in (policy or {}).get("bindings", []) if isinstance(policy, dict) else []:
        for member in binding.get("members", []):
            out.add((binding.get("role", ""), member))
    return out


# ---------------------------------------------------------------------------------- the calls, in one place

class Cloud:
    """Every call the probe makes to Google passes through call(): printed first, then made - or, in a dry run,
    printed only. The backend is built on the first live call, so a dry run never builds one."""

    def __init__(self, project: str, *, dry_run: bool, backend_factory, say):
        self.project, self.dry_run, self._factory, self.say = project, dry_run, backend_factory, say
        self._backend = None
        self.calls: list[str] = []

    @property
    def backend(self):
        if self._backend is None:
            self._backend = self._factory(self.project)
        return self._backend

    def call(self, step: str, desc: str, method: str, *args, stub=None):
        self.calls.append(desc)
        self.say(f"[{step}] {'would call' if self.dry_run else 'call'}: {desc}")
        if self.dry_run:
            return stub
        return getattr(self.backend, method)(*args)


class LiveBackend:
    """The real calls. Nothing here is imported until a live run reaches it; the dry run and the tests never build it.

    Needs google-adk 2.8.0 and google-cloud-aiplatform[agent_engines] in the venv (the run note's step 2).
    """

    def __init__(self, project: str):
        self.project = project
        self._sessions: dict = {}

    # credentials and REST -----------------------------------------------------------------------------------
    def _credentials(self, as_sa: str | None = None):
        import google.auth
        from google.auth.transport.requests import Request
        source, _ = google.auth.default(scopes=[CLOUD_PLATFORM])
        if not as_sa:
            return source
        from google.auth import impersonated_credentials
        # the shape the peer's own _mcp_headers mints with (deploy/services/agent/agent.py:84-88)
        creds = impersonated_credentials.Credentials(source_credentials=source, target_principal=as_sa,
                                                     target_scopes=[CLOUD_PLATFORM], lifetime=900)
        try:
            creds.refresh(Request())
        except Exception as error:
            raise NotTested(f"could not mint a token as {as_sa} (make operators grants it): {error}") from error
        return creds

    def _rest(self, method: str, url: str, *, body=None, params=None, credentials=None, stream=False, timeout=120):
        from google.auth.transport.requests import AuthorizedSession
        response = AuthorizedSession(credentials or self._credentials()).request(
            method, url, json=body, params=params, stream=stream, timeout=timeout)
        if response.status_code >= 400:
            raise Refused(response.status_code, response.text)
        return response

    def _client(self, region: str, credentials=None):
        import vertexai
        kwargs = {"project": self.project, "location": region}
        if credentials is not None:
            kwargs["credentials"] = credentials
        # verified: the client google-adk 2.8.0 builds - cli/cli_deploy.py:1319 (project, location) and
        # memory/vertex_ai_memory_bank_service.py:641-645 (credentials)
        return vertexai.Client(**kwargs)

    # row 11 ------------------------------------------------------------------------------------------------
    def versions(self, region: str) -> dict:
        import importlib.metadata as md
        out: dict = {"python": sys.version.split()[0]}
        for dist in ("google-adk", "google-cloud-aiplatform", "google-genai", "google-auth"):
            try:
                out[dist] = md.version(dist)
            except md.PackageNotFoundError:
                out[dist] = None
        try:
            client = self._client(region)
            engines = getattr(client, "agent_engines", None)
            # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/build/runtime/sdk-migration
            #   (which namespaces this aiplatform keeps: the newer SDK moved them to client.runtimes)
            out["namespaces"] = {"agent_engines": engines is not None,
                                 "agent_engines.sessions": engines is not None and hasattr(engines, "sessions"),
                                 "agent_engines.memories": engines is not None and hasattr(engines, "memories"),
                                 "runtimes": hasattr(client, "runtimes")}
        except Exception as error:
            out["namespaces"] = {"error": f"{type(error).__name__}: {error}"}
        check = subprocess.run([sys.executable, "-m", "pip", "check"], capture_output=True, text=True)
        out["pip_check"] = (check.stdout + check.stderr).strip()
        return out

    # instances ---------------------------------------------------------------------------------------------
    def create_instance(self, region: str, display_name: str) -> str:
        # verified: google-adk 2.8.0 cli/cli_deploy.py:1430-1431 - agent_engines.create(), then .api_resource.name
        # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/deploy-an-agent
        #   (config={'display_name': ...}, which ADK does not pass; the probe names its instances for --cleanup)
        engine = self._client(region).agent_engines.create(config={"display_name": display_name})
        return engine.api_resource.name

    def get_instance(self, name: str) -> dict:
        # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/manage-deployed-agents
        #   (GET v1 projects/*/locations/*/reasoningEngines/*)
        return self._rest("GET", f"{endpoint(name)}/v1/{name}").json()

    def list_instances(self, region: str) -> list:
        # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/manage-deployed-agents
        #   (GET v1 projects/*/locations/*/reasoningEngines, paged)
        url = f"https://{region}-aiplatform.googleapis.com/v1/projects/{self.project}/locations/{region}/reasoningEngines"
        out, token = [], None
        for _ in range(20):
            params = {"pageSize": 100, **({"pageToken": token} if token else {})}
            page = self._rest("GET", url, params=params).json()
            out += page.get("reasoningEngines", [])
            token = page.get("nextPageToken")
            if not token:
                break
        return out

    def delete_instance(self, name: str) -> None:
        # verified: google-adk 2.8.0 cli/cli_deploy.py:1445 - agent_engines.delete(name=...)
        # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/manage-deployed-agents
        #   (force=True, which takes the instance's sessions and memories with it)
        self._client(region_of(name)).agent_engines.delete(name=name, force=True)

    def deploy(self, name: str, folder, env_file, config_file, display_name: str) -> str:
        # verified: google-adk 2.8.0's own deploy, as `adk deploy agent_engine --agent_engine_id` calls it
        # (cli/cli_deploy.py:978 to_agent_engine): ADK's Dockerfile, its class methods, then
        # agent_engines.update(name=..., config=...) (:1439). With agent_engine_id given it never deletes (:1444).
        from google.adk.cli import cli_deploy
        log = io.StringIO()
        try:
            with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
                cli_deploy.to_agent_engine(agent_folder=str(folder), project=self.project, region=region_of(name),
                                           agent_engine_id=name, display_name=display_name, otel_to_cloud=True,
                                           env_file=str(env_file), agent_engine_config_file=str(config_file))
        except Exception as error:
            error.probe_log = log.getvalue()
            raise
        return log.getvalue()

    def query(self, name: str, message: str, user_id: str, as_sa: str | None = None) -> dict:
        # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/use-an-adk-agent
        #   (POST v1 {name}:streamQuery?alt=sse with class_method async_stream_query and input user_id, message)
        credentials = self._credentials(as_sa)
        body = {"class_method": "async_stream_query", "input": {"user_id": user_id, "message": message}}
        started = time.monotonic()
        response = self._rest("POST", f"{endpoint(name)}/v1/{name}:streamQuery", body=body, params={"alt": "sse"},
                              credentials=credentials, stream=True, timeout=600)
        first, lines = None, []
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            if first is None:
                first = time.monotonic() - started
            lines.append(line)
        return {"status": response.status_code, "events": stream_events(lines), "first_event_s": first,
                "total_s": time.monotonic() - started}

    # sessions (row 9) ----------------------------------------------------------------------------------------
    def _session_service(self, name: str):
        from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService
        return VertexAiSessionService(project=self.project, location=region_of(name), agent_engine_id=engine_id(name))

    def create_session(self, name: str, user_id: str, ttl: str) -> str:
        # verified: VertexAiSessionService.create_session, ttl passed through as its docstring says
        # (google-adk 2.8.0 sessions/vertex_ai_session_service.py:162-219)
        session = asyncio.run(self._session_service(name).create_session(
            app_name=engine_id(name), user_id=user_id, ttl=ttl))
        self._sessions[session.id] = session
        return session.id

    def append_event(self, name: str, session_id: str, text: str) -> None:
        # verified: VertexAiSessionService.append_event (vertex_ai_session_service.py:392-499)
        from google.adk.events import Event
        from google.genai import types
        event = Event(author="user", invocation_id="probe-" + secrets.token_hex(4),
                      content=types.Content(role="user", parts=[types.Part(text=text)]))
        asyncio.run(self._session_service(name).append_event(self._sessions[session_id], event))

    def get_session(self, name: str, session_id: str, user_id: str) -> dict | None:
        # verified: VertexAiSessionService.get_session (:221-304); a session of another user raises ValueError (:272-275)
        session = asyncio.run(self._session_service(name).get_session(
            app_name=engine_id(name), user_id=user_id, session_id=session_id))
        return None if session is None else {"user_id": session.user_id, "id": session.id, "events": len(session.events)}

    def raw_get_session(self, name: str, session_id: str) -> dict:
        # verified: the read VertexAiSessionService itself makes, which names no user (vertex_ai_session_service.py:252-258)
        async def read():
            async with self._client(region_of(name)).aio as client:
                return await client.agent_engines.sessions.get(
                    name=f"reasoningEngines/{engine_id(name)}/sessions/{session_id}")
        got = asyncio.run(read())
        return got.model_dump(mode="json", exclude_none=True) if hasattr(got, "model_dump") else dict(got)

    def list_sessions(self, name: str) -> list:
        # verified: VertexAiSessionService.list_sessions with no user_id: no filter is sent (:306-333)
        listed = asyncio.run(self._session_service(name).list_sessions(app_name=engine_id(name)))
        return [{"user_id": s.user_id, "id": s.id} for s in listed.sessions]

    def delete_session(self, name: str, session_id: str, user_id: str) -> None:
        # verified: VertexAiSessionService.delete_session (:335-369)
        asyncio.run(self._session_service(name).delete_session(
            app_name=engine_id(name), user_id=user_id, session_id=session_id))

    # Memory Bank (row 10) ------------------------------------------------------------------------------------
    def _memory_service(self, name: str):
        from google.adk.memory.vertex_ai_memory_bank_service import VertexAiMemoryBankService
        return VertexAiMemoryBankService(project=self.project, location=region_of(name), agent_engine_id=engine_id(name))

    def add_memory(self, name: str, user_id: str, fact: str) -> None:
        # verified: add_memory writes through memories.create (memory/vertex_ai_memory_bank_service.py:295-329, :473-506)
        from google.adk.memory.memory_entry import MemoryEntry
        from google.genai import types
        entry = MemoryEntry(content=types.Content(role="user", parts=[types.Part(text=fact)]), author="user")
        asyncio.run(self._memory_service(name).add_memory(app_name=APP_NAME, user_id=user_id, memories=[entry]))

    def search_memory(self, name: str, user_id: str, query: str) -> list:
        # verified: search_memory reads through memories.retrieve (vertex_ai_memory_bank_service.py:542-593)
        found = asyncio.run(self._memory_service(name).search_memory(app_name=APP_NAME, user_id=user_id, query=query))
        return [part.text for memory in found.memories for part in (memory.content.parts or []) if part.text]

    # IAM (rows 2, 8) ------------------------------------------------------------------------------------------
    def sa_policy(self, email: str) -> dict:
        # unverified: https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts/getIamPolicy
        return self._rest("POST", f"https://iam.googleapis.com/v1/projects/{self.project}/serviceAccounts/{email}"
                                  ":getIamPolicy", body={"options": {"requestedPolicyVersion": 3}}).json()

    def sa_permissions(self, email: str, permissions) -> list:
        # unverified: https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts/testIamPermissions
        return self._rest("POST", f"https://iam.googleapis.com/v1/projects/{self.project}/serviceAccounts/{email}"
                                  ":testIamPermissions", body={"permissions": list(permissions)}).json().get("permissions", [])

    def engine_policy(self, name: str) -> dict:
        # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/reference/rest/v1/projects.locations.reasoningEngines
        #   (and the point of the call: whether an instance has an IAM policy of its own at all)
        return self._rest("POST", f"{endpoint(name)}/v1/{name}:getIamPolicy", body={}).json()

    # Cloud Trace (row 7) --------------------------------------------------------------------------------------
    def trace_spans(self, start: str, end: str) -> list:
        # unverified: https://cloud.google.com/trace/docs/reference/v1/rest/v1/projects.traces/list (view COMPLETE)
        url = f"https://cloudtrace.googleapis.com/v1/projects/{self.project}/traces"
        spans, token = [], None
        for _ in range(5):
            params = {"view": "COMPLETE", "startTime": start, "endTime": end, "pageSize": 100,
                      **({"pageToken": token} if token else {})}
            page = self._rest("GET", url, params=params).json()
            for trace in page.get("traces", []):
                for span in trace.get("spans", []):
                    spans.append({"trace": trace.get("traceId", ""), "name": span.get("name", ""),
                                  "labels": span.get("labels", {})})
            token = page.get("nextPageToken")
            if not token:
                break
        return spans



# --------------------------------------------------------------------------------------------- the probe

class Probe:
    def __init__(self, args, cloud: Cloud, say, scrub: Scrubber, *, sleep=time.sleep):
        self.args, self.cloud, self.say, self.scrub, self.sleep = args, cloud, say, scrub, sleep
        self.dry = cloud.dry_run
        self.rec = Recorder(self.dry, scrub)
        self.p = args.project
        self.sa = sa_email(args.service_account, args.project)
        self.member = sa_email(args.member_sa, args.project)
        self.outsider = sa_email(args.outsider_sa, args.project)
        self.stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d-%H%M")
        self.marker = "pm" + secrets.token_hex(4)
        self.created: list[Resource] = []
        self.left: list[tuple[Resource, str]] = []
        self.empty: dict[str, str] = {}
        self.runtime_name: str | None = None
        self.deployed = False
        self.window: list | None = None
        self.versions: dict = {}
        self.image_versions: dict = {}
        self.model_error: str | None = None
        self.sdk_problem: str | None = None
        self.written: Path | None = None
        self.write_refused = False
        self._dry_ids = itertools.count(1)

    # running --------------------------------------------------------------------------------------------------
    def selected(self) -> list[str]:
        if not self.args.only:
            return list(STEPS)
        wanted = set(self.args.only) | {"preflight", "author"}
        for step in list(wanted):
            wanted |= set(NEEDS.get(step, ()))
        return [s for s in STEPS if s in wanted]

    def run(self) -> None:
        for name in self.selected():
            self.step(name)

    def step(self, name: str) -> None:
        self.say(f"\n== {name}: {STEP_TITLES[name]} ==")
        try:
            getattr(self, "step_" + name)()
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as error:          # one refusal never stops the steps after it
            status, finding, evidence = classify(error)
            self.say(f"[{name}] {status}: {self.brief(finding)}")
            for row in STEP_ROWS[name]:
                if not self.rec.for_row(row):
                    self.rec.add(row, "", status, finding, evidence)

    def require_sdk(self) -> None:
        if self.sdk_problem:
            raise NotTested(self.sdk_problem)

    def brief(self, text) -> str:
        """For a console line: scrubbed whole, then cut."""
        return trim(self.scrub(text), 300)

    def poll(self, fn, *, until, seconds: int, every: int):
        waited = 0
        while True:
            result = fn()
            if self.dry or until(result) or waited >= seconds:
                return result
            self.sleep(every)
            waited += every

    def create_instance(self, step: str, region: str, display_name: str) -> str:
        name = self.cloud.call(step, f"{sdk(self.p, region)}.agent_engines.create(config={{'display_name': "
                                     f"{display_name!r}}})", "create_instance", region, display_name,
                               stub=f"projects/NUMBER/locations/{region}/reasoningEngines/DRYRUN{next(self._dry_ids)}")
        self.created.append(Resource("instance", name, region))     # tracked before anything else can fail
        self.scrub.learn(name)
        return name

    def query(self, step: str, name: str, user_id: str, *, as_sa: str | None = None, model: bool = True) -> dict:
        message = (f"Probe {self.marker}: call probe_tool with the marker {self.marker}, then report the runtime facts."
                   if model else f"Probe {self.marker} {NO_MODEL}: the runtime facts only.")
        who = f" as {as_sa} (impersonated)" if as_sa else ""
        desc = (f"POST {endpoint(name)}/v1/{name}:streamQuery?alt=sse {{\"class_method\": \"async_stream_query\", "
                f"\"input\": {{\"user_id\": {json.dumps(user_id)}, \"message\": \"Probe <marker>{'' if model else ' ' + NO_MODEL}"
                f"...\"}}}}{who}")
        for attempt in range(3):
            try:
                return self.cloud.call(step, desc, "query", name, message, user_id, as_sa,
                                       stub={"status": None, "events": [], "first_event_s": None, "total_s": None})
            except Refused as error:        # a revision still rolling out answers 5xx: two retries, 30 s apart
                if error.status < 500 or attempt == 2:
                    raise
                self.say(f"[{step}] HTTP {error.status}; retrying in 30 s")
                self.sleep(30)
        raise AssertionError("unreachable")

    # steps --------------------------------------------------------------------------------------------------
    def step_preflight(self) -> None:
        region = self.args.runtime_region
        v = self.cloud.call("preflight", f"import vertexai and google.adk; read the installed versions; check {sdk(self.p, region)} "
                                         f"has .agent_engines (sessions, memories) and .runtimes; "
                                         f"{Path(sys.executable).name} -m pip check", "versions", region, stub={}) or {}
        if self.dry:            # nothing was read, so nothing is judged: the dry run goes on to print every call
            return
        self.versions = v
        adk, aip, genai = v.get("google-adk"), v.get("google-cloud-aiplatform"), v.get("google-genai")
        ns = v.get("namespaces") or {}
        if not aip:
            self.sdk_problem = "google-cloud-aiplatform is not installed in this venv (the run note's step 2)"
        elif not adk:
            self.sdk_problem = "google-adk is not installed in this venv (the run note's step 2)"
        elif "error" in ns:
            self.sdk_problem = f"vertexai.Client could not be built (is ADC set? the run note's step 1): {ns['error']}"
        elif not ns.get("agent_engines"):
            self.sdk_problem = (f"vertexai.Client in google-cloud-aiplatform {aip} has no agent_engines namespace, which "
                                f"google-adk 2.8.0 deploys and keeps sessions through")
        if aip and adk:
            note = "" if adk == "2.8.0" else f" (not the kit's google-adk 2.8.0: rows 2-10 then describe {adk})"
            self.rec.add("11", "this venv", "observed",
                         f"google-adk {adk}, google-cloud-aiplatform {aip} and google-genai {genai} installed together, "
                         f"Python {v.get('python')}{note}",
                         dumps({k: v.get(k) for k in ("google-adk", "google-cloud-aiplatform", "google-genai", "google-auth")}))
        else:
            self.rec.add("11", "this venv", "not tested", self.sdk_problem or "")
        if ns and "error" not in ns:
            self.rec.add("11", "namespaces", "observed", "vertexai.Client has " + ", ".join(
                f"{name} {'yes' if present else 'no'}" for name, present in ns.items()), dumps(ns))
        else:
            self.rec.add("11", "namespaces", "not tested", f"vertexai.Client not read: {ns.get('error', 'no client')}")
        if v.get("pip_check"):
            broken = "no broken requirements" not in v["pip_check"].lower()
            self.rec.add("11", "pip check", "observed", "BROKEN requirements, see the evidence" if broken
                         else "no broken requirements", v["pip_check"])
        self.rec.add("11", "beside the peer's pins", "not tested",
                     "the author's resolution, beside deploy/services/agent/requirements.txt, which ADK's deploy appends "
                     "google-cloud-aiplatform[adk,agent_engines] to (cli_deploy.py:151-175): see the run note's step 2")

    def step_instances(self) -> None:
        self.require_sdk()
        for region in self.args.regions:
            try:
                name = self.create_instance("instances", region, f"{PREFIX}{self.stamp}-{region}")
            except Exception as error:
                self.rec.add("1", region, *classify(error))
                continue
            self.empty[region] = name
            self.rec.add("1", region, "observed", "an empty instance was created", name)
        for region in DEFAULT_REGIONS:
            if region not in self.args.regions:
                self.rec.add("1", region, "not tested", "not in this run's --region")

    def step_sessions(self) -> None:
        self.require_sdk()
        name = self.empty.get(self.args.runtime_region) or next(iter(self.empty.values()), None)
        if not name:
            raise NotTested("no empty instance to hold a session (row 1)")
        eid, region = engine_id(name), region_of(name)
        svc = f"VertexAiSessionService(project={self.p!r}, location={region!r}, agent_engine_id={eid!r})"
        owner, other = "acme:probe-a", "zeta:probe-b"
        sid = self.cloud.call("sessions", f"{svc}.create_session(app_name={eid!r}, user_id={owner!r}, ttl={SESSION_TTL!r})",
                              "create_session", name, owner, SESSION_TTL, stub="DRYRUN-SESSION")
        self.created.append(Resource("session", f"{name}/sessions/{sid}", region, user=owner, parent=name, sid=str(sid)))
        self.scrub.learn_session(sid)
        self.cloud.call("sessions", f"{svc}.append_event(session, Event(author='user', text='probe event <marker>'))",
                        "append_event", name, sid, f"probe event {self.marker}")
        try:
            got = self.cloud.call("sessions", f"{svc}.get_session(app_name={eid!r}, user_id={other!r}, session_id=SESSION_ID)",
                                  "get_session", name, sid, other)
            self.rec.add("9", "ADK get as another user", "observed",
                         f"VertexAiSessionService returned {owner}'s session to {other}", dumps(got))
        except ValueError as error:
            if "does not belong to user" in str(error):     # google-adk 2.8.0 vertex_ai_session_service.py:272-275
                self.rec.add("9", "ADK get as another user", "refused",
                             f"VertexAiSessionService refused {other}: ADK reads the session, then compares its user_id "
                             f"(a check in the client, not the API)", str(error))
            else:
                self.rec.add("9", "ADK get as another user", *classify(error))
        except Exception as error:
            self.rec.add("9", "ADK get as another user", *classify(error))
        try:
            raw = self.cloud.call("sessions", f"{sdk(self.p, region)}.aio.agent_engines.sessions.get(name='reasoningEngines/"
                                              f"{eid}/sessions/SESSION_ID')  # ADK's own read, naming no user",
                                  "raw_get_session", name, sid, stub={}) or {}
            seen = pick(raw, "userId", "user_id")
            self.rec.add("9", "raw sessions.get", "observed",
                         f"the API returned the session (user_id {seen!r}) to a read that names no user: what stands "
                         f"between one user and another's session is IAM on the instance and ADK's check, not the API",
                         dumps(raw))
            expire = pick(raw, "expireTime", "expire_time")
            self.rec.add("9", "ttl", "observed" if expire else "not tested",
                         f"ttl {SESSION_TTL} set expireTime {expire}" if expire else "the session read back no expireTime",
                         dumps({"expireTime": expire}))
        except Exception as error:
            self.rec.add("9", "raw sessions.get", *classify(error))
        try:
            listed = self.cloud.call("sessions", f"{svc}.list_sessions(app_name={eid!r})  # no user_id",
                                     "list_sessions", name, stub=[]) or []
            self.rec.add("9", "list with no user", "observed",
                         f"list_sessions with no user id returned {len(listed)} session(s), users "
                         f"{sorted({str(s.get('user_id')) for s in listed})}", dumps(listed))
        except Exception as error:
            self.rec.add("9", "list with no user", *classify(error))

    def step_memory(self) -> None:
        self.require_sdk()
        for region in self.args.regions:
            name = self.empty.get(region)
            if not name:
                self.rec.add("10", region, "not tested", "no instance in this region (row 1)")
                continue
            try:
                self.memory_in(region, name)
            except Exception as error:
                self.rec.add("10", region, *classify(error))

    def memory_in(self, region: str, name: str) -> None:
        eid, user, question = engine_id(name), "acme:probe-a", "What is the probe's marker?"
        fact = f"The probe's marker is {self.marker}."
        svc = f"VertexAiMemoryBankService(project={self.p!r}, location={region!r}, agent_engine_id={eid!r})"
        self.cloud.call("memory", f"{svc}.add_memory(app_name={APP_NAME!r}, user_id={user!r}, memories=[MemoryEntry("
                                  f"content=Content(parts=[Part(text=\"The probe's marker is <marker>.\")]))])",
                        "add_memory", name, user, fact)
        self.created.append(Resource("memory", f"{name}/memories/(the probe's)", region, parent=name))
        found = self.poll(lambda: self.cloud.call(
            "memory", f"{svc}.search_memory(app_name={APP_NAME!r}, user_id={user!r}, query={question!r})"
                      f"  # polled every 10 s for 60 s", "search_memory", name, user, question,
            stub=[]), until=bool, seconds=60, every=10) or []
        if found:
            self.rec.add("10", region, "observed", "memories.create took a fact and memories.retrieve returned it",
                         dumps(found))
        else:
            self.rec.add("10", region, "observed", "memories.create took a fact without a refusal; memories.retrieve "
                                                   "returned nothing within 60 s", "")

    def step_runtime(self) -> None:
        self.require_sdk()
        region = self.args.runtime_region
        iam = f"https://iam.googleapis.com/v1/projects/{self.p}/serviceAccounts/{self.sa}"
        before, mine = self.safe("runtime", f"POST {iam}:getIamPolicy", "sa_policy", self.sa), \
            self.safe("runtime", f"POST {iam}:testIamPermissions {{\"permissions\": {json.dumps(list(ACT_AS))}}}",
                      "sa_permissions", self.sa, list(ACT_AS))
        display = f"{PREFIX}{self.stamp}-runtime"
        name = self.create_instance("runtime", region, display)
        self.runtime_name = name
        config, env = deploy_inputs(self.args, self.p)
        self.say(f"[runtime] stage: {APP_NAME}/agent.py ({len(AGENT_SOURCE.splitlines())} lines: tools/probe_agent_stack.py "
                 f"AGENT_SOURCE) and __init__.py; beside them .agent_engine_config.json {json.dumps(config)} and .env "
                 f"{json.dumps(env)}")
        desc = (f"google.adk.cli.cli_deploy.to_agent_engine(agent_folder='<staged>/{APP_NAME}', project={self.p!r}, "
                f"region={region!r}, agent_engine_id={name!r}, display_name={display!r}, otel_to_cloud=True, "
                f"env_file='<staged>/.env', agent_engine_config_file='<staged>/.agent_engine_config.json')"
                f"  # = adk deploy agent_engine --agent_engine_id=... --otel_to_cloud; ADK then calls "
                f"agent_engines.update(name=..., config=...) (cli_deploy.py:1439)")
        staging = None if self.dry else tempfile.mkdtemp(prefix="ae109-")
        try:
            staged = (None, None, None) if self.dry else stage_agent(Path(staging), config, env)
            log = self.cloud.call("runtime", desc, "deploy", name, *staged, display, stub="")
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as error:
            self.deploy_stopped(error, before, mine, config)
            return
        finally:
            if staging:
                shutil.rmtree(staging, ignore_errors=True)
        self.deployed = True
        self.rec.add("2", "deploy", "observed", f"ADK's deploy completed in {region} with service_account {self.sa}",
                     log, keep_end=True)
        self.rec.add("3", "accepted", "observed", "min_instances 0 and max_instances 1 went in the deploy's config and "
                                                  "the update completed without a refusal", json.dumps(config))
        inst = self.safe("runtime", f"GET {endpoint(name)}/v1/{name}", "get_instance", name)
        view = deployment_view(inst or {})
        self.read_back(view, inst)
        after = self.safe("runtime", f"POST {iam}:getIamPolicy  # after the deploy", "sa_policy", self.sa)
        self.grant(before, after, mine, "")
        self.window = [dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=2), None]
        if self.args.idle_wait:
            self.say(f"[runtime] waiting {self.args.idle_wait} s idle before the first call (--idle-wait)")
            if not self.dry:
                self.sleep(self.args.idle_wait)
        try:
            cold = self.query("runtime", name, "probe-operator")
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as error:
            status, finding, evidence = classify(error)
            for row, label in (("2", "runtime identity"), ("4", "first call"), ("5", ""), ("6", "")):
                self.rec.add(row, label, status, f"the first query: {finding}", evidence)
            return
        finally:
            if self.window:
                self.window[1] = dt.datetime.now(dt.timezone.utc)
        try:
            warm = self.query("runtime", name, "probe-operator", model=False)
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as error:
            warm = None
            self.rec.add("4", "second call", *classify(error))
        self.window[1] = dt.datetime.now(dt.timezone.utc)
        self.record_runtime(cold, warm, view)

    def safe(self, step: str, desc: str, method: str, *args):
        """A call whose failure is evidence, not a stop: returns the answer, or {"error": ...}."""
        try:
            return self.cloud.call(step, desc, method, *args, stub={})
        except (KeyboardInterrupt, SystemExit):
            raise
        except Exception as error:
            status, finding, _ = classify(error)
            self.say(f"[{step}] {status}: {self.brief(finding)}")
            return {"error": finding}

    def deploy_stopped(self, error: BaseException, before, mine, config: dict) -> None:
        status, finding, evidence = classify(error)
        whole = f"{evidence or error}\n{getattr(error, 'probe_log', '')}"
        self.rec.add("2", "deploy", status, f"the deploy (service_account {self.sa}, min_instances 0, max_instances 1) "
                                            f"stopped: {finding}", whole, keep_end=True)
        self.grant(before, None, mine, whole)
        if re.search(r"(?i)min_?instances|max_?instances", whole):
            self.rec.add("3", "accepted", "refused", f"the deploy's refusal names the instance bounds: {finding}", whole,
                         keep_end=True)
        else:
            self.rec.add("3", "accepted", "not tested", "the deploy stopped before the bounds were judged (row 2)",
                         json.dumps(config))
        for row in ("4", "5", "6"):
            self.rec.add(row, "", "not tested", "the runtime was not deployed (row 2)")

    def grant(self, before, after, mine, refusal: str) -> None:
        """Row 2's second half: the grant on the account, from a refusal's own words or from the policy's change."""
        if isinstance(mine, list):
            held = [p for p in mine if p in ACT_AS]
            mine_note = f"you hold {', '.join(held) if held else 'none of ' + ', '.join(ACT_AS)} on the account"
        else:
            mine_note = f"your permissions on the account were not read ({(mine or {}).get('error')})"
        if refusal:
            hint = grant_hint(refusal, self.sa)
            if hint:
                self.rec.add("2", "grant", "observed", hint, refusal, keep_end=True)
            else:
                self.rec.add("2", "grant", "not tested", f"the refusal names no iam.serviceAccounts permission; {mine_note}",
                             dumps(before))
            return
        unread = [p.get("error") for p in (before, after) if isinstance(p, dict) and p.get("error")]
        if unread:
            self.rec.add("2", "grant", "not tested", f"the account's policy was not read ({unread[0]}); {mine_note}")
            return
        added = sorted(bindings(after) - bindings(before))
        if added:
            self.rec.add("2", "grant", "observed", "the deploy added to the account's policy: "
                         + "; ".join(f"{r} for {m}" for r, m in added) + f"; {mine_note}", dumps(after))
        else:
            self.rec.add("2", "grant", "observed", f"no binding on {self.sa} was needed or added: the deploy and the "
                                                   f"runtime worked with the account's policy as it was, read before and "
                                                   f"after; {mine_note}", dumps(after))

    def read_back(self, view: dict, inst) -> None:
        if isinstance(inst, dict) and inst.get("error"):
            self.rec.add("3", "read back", "not tested", f"GET refused: {inst['error']}")
            self.rec.add("4", "instance config", "not tested", f"GET refused: {inst['error']}")
            return
        lo, hi = view.get("minInstances"), view.get("maxInstances")
        lo_text = f"minInstances {lo}" if lo is not None else \
            "minInstances absent (proto3 JSON leaves out a zero, so 0 and unset read alike; the docs' default is 1)"
        self.rec.add("3", "read back", "observed", f"{lo_text}; maxInstances {hi if hi is not None else 'absent'}", dumps(view))
        self.rec.add("4", "instance config", "observed",
                     f"{lo_text}: with no instance kept, an idle runtime holds no compute; whether anything else bills "
                     f"while idle is the pricing page's to say (AUTHOR below)", dumps(view))

    def record_runtime(self, cold: dict, warm: dict | None, view: dict) -> None:
        facts, model_error, _ = probe_facts((cold or {}).get("events"))
        self.model_error = model_error
        if not facts or "unparsed" in facts:
            facts = None
            for row, label in (("2", "runtime identity"), ("5", ""), ("6", "")):
                self.rec.add(row, label, "not tested", "the reply carried no readable PROBE_FACTS event",
                             dumps((cold or {}).get("events")))
        meta = (facts or {}).get("metadata") or {}
        self.scrub.learn_number(meta.get("project_number"))
        self.image_versions = (facts or {}).get("versions") or {}
        idle = self.args.idle_wait
        when = f"after {idle} s idle" if idle else "the first call after the deploy, which may have left an instance warm"
        if cold.get("total_s") is not None:
            first = cold.get("first_event_s")
            self.rec.add("4", "first call", "observed",
                         f"first event after {first:.1f} s, reply complete after {cold['total_s']:.1f} s ({when}; it "
                         f"includes one model turn and the facts)" if first is not None else
                         f"reply complete after {cold['total_s']:.1f} s ({when})", dumps({"status": cold.get("status")}))
        if warm and warm.get("total_s") is not None:
            self.rec.add("4", "second call", "observed",
                         f"reply complete after {warm['total_s']:.1f} s (the facts only, no model)", dumps({"status": warm.get("status")}))
        if not facts:
            return
        email = meta.get("service_account")
        if email:
            same = email == self.sa
            self.rec.add("2", "runtime identity", "observed",
                         f"the runtime's metadata server names {email}" + (", the account the deploy asked for" if same
                                                                          else f", NOT the account the deploy asked for ({self.sa})"),
                         dumps(meta))
        else:
            self.rec.add("2", "runtime identity", "refused", "the metadata server named no account: "
                         f"{meta.get('service_account_error')}", dumps(meta))
        for key, label in (("id_token_metadata", "metadata server"), ("id_token_fetch", "fetch_id_token, the peer's call")):
            token = facts.get(key) or {}
            if token.get("minted"):
                self.rec.add("5", label, "observed", f"an ID token for {token.get('aud')} as {token.get('email')}, issuer "
                                                     f"{token.get('iss')}, lifetime {token.get('lifetime_s')} s", dumps(token))
            else:
                self.rec.add("5", label, "refused", f"no token: {token.get('error')}", dumps(token))
        door = facts.get("mcp_door")
        if door is None:
            self.rec.add("5", "documind-mcp's door", "not tested", "no token, or no audience, to knock with")
        elif door.get("status") == 200:
            self.rec.add("5", "documind-mcp's door", "observed",
                         "the token got past Cloud Run's IAM door: documind-mcp's GET /health answered 200", dumps(door))
        elif door.get("status") in (401, 403):
            self.rec.add("5", "documind-mcp's door", "refused",
                         "documind-mcp did not accept the token (401: its audience or issuer)" if door["status"] == 401
                         else "Cloud Run IAM refused the runtime's account (403: no run.invoker on documind-mcp)", dumps(door))
        elif "status" in door:          # a 404 can be a service that is not there at all, so it proves nothing
            self.rec.add("5", "documind-mcp's door", "not tested",
                         f"GET /health answered {door['status']} at {facts.get('audience')}: is documind-mcp deployed in "
                         f"{self.args.mcp_region}? (--mcp-url names another)", dumps(door))
        else:
            self.rec.add("5", "documind-mcp's door", "not tested",
                         f"documind-mcp did not answer at {facts.get('audience')} (is it deployed in "
                         f"{self.args.mcp_region}? --mcp-url names another): {door.get('error')}", dumps(door))
        env = facts.get("env") or {}
        location = env.get("GOOGLE_CLOUD_LOCATION")
        note = ""
        if location and location != "global":
            note = (" - the region, not global: Gemini 3.x needs GlobalGemini (google_llm.py:104-121), and env_vars "
                    "cannot set GOOGLE_CLOUD_LOCATION, which the deploy page reserves")
        self.rec.add("6", "GOOGLE_CLOUD_LOCATION", "observed", f"the runtime's GOOGLE_CLOUD_LOCATION is {location!r}{note}",
                     dumps(env))
        for key, label in (("environment", "Gemini on that location"), ("global", "Gemini on global")):
            answer = (facts.get("gemini") or {}).get(key)
            if answer is None:
                self.rec.add("6", label, "not tested", "the probe agent asked no model")
            elif answer.get("answered"):
                self.rec.add("6", label, "observed", f"{self.args.model} answered {answer.get('text')!r}", dumps(answer))
            else:
                self.rec.add("6", label, "refused", f"{self.args.model}: {answer.get('error')}", dumps(answer))
        names = facts.get("env_names")
        if names:
            self.say(f"[runtime] the runtime's environment names: {', '.join(names)}")

    def step_access(self) -> None:
        if not self.deployed:
            raise NotTested("the runtime was not deployed (row 2)")
        name = self.runtime_name
        try:
            policy = self.cloud.call("access", f"POST {endpoint(name)}/v1/{name}:getIamPolicy {{}}", "engine_policy", name,
                                     stub={}) or {}
            self.rec.add("8", "instance IAM policy", "observed",
                         f"getIamPolicy answered: the instance has an IAM policy of its own "
                         f"({len(policy.get('bindings', []))} binding(s))", dumps(policy))
        except Exception as error:
            status, finding, evidence = classify(error)
            if isinstance(error, Refused) and (error.status == 501 or "method not found" in finding.lower()):
                finding = f"no IAM policy of its own: the API has no getIamPolicy for an instance ({finding})"
            self.rec.add("8", "instance IAM policy", status, f"getIamPolicy on the instance: {finding}", evidence)
        for account, label, holds in ((self.member, f"as {self.args.member_sa}",
                                       "roles/aiplatform.user on the project, nothing on the instance"),
                                      (self.outsider, f"as {self.args.outsider_sa}", "no role on the project")):
            try:
                reply = self.query("access", name, "probe-" + label.split()[-1], as_sa=account, model=False)
                facts, _, _ = probe_facts(reply.get("events"))
                self.rec.add("8", label, "observed",
                             f"{account} ({holds}) queried the instance: HTTP {reply.get('status')}, "
                             f"{'the facts came back' if facts else 'no facts event'}", dumps({"status": reply.get("status")}))
            except Exception as error:
                status, finding, evidence = classify(error)
                self.rec.add("8", label, status, f"{account} ({holds}): {finding}", evidence)

    def step_telemetry(self) -> None:
        if not self.window or not self.window[1]:
            raise NotTested("no query ran, so there is no window to read (rows 2 and 4)")
        start = self.window[0].strftime("%Y-%m-%dT%H:%M:%SZ")
        url = f"https://cloudtrace.googleapis.com/v1/projects/{self.p}/traces"

        def read():
            end = (dt.datetime.now(dt.timezone.utc) + dt.timedelta(minutes=1)).strftime("%Y-%m-%dT%H:%M:%SZ")
            return self.cloud.call("telemetry", f"GET {url}?view=COMPLETE&startTime={start}&endTime=<now+1m>&pageSize=100"
                                                f"  # polled every 20 s for {self.args.trace_wait} s",
                                   "trace_spans", start, end, stub=[]) or []

        spans = self.poll(read, until=lambda s: bool(ours(s)), seconds=self.args.trace_wait, every=20)
        mine = ours(spans)
        if not mine:
            self.rec.add("7", "spans", "not tested",
                         f"no trace naming {APP_NAME} within {self.args.trace_wait} s ({len(spans)} span(s) of other "
                         f"services in the window): is telemetry.googleapis.com enabled (the run note's step 1)? Look "
                         f"in Trace Explorer by hand, or run again with a longer --trace-wait"
                         + (f"; the model turn failed: {self.model_error}" if self.model_error else ""))
            return
        names = sorted({s["name"] for s in mine})
        keys = sorted({k for s in mine for k in (s.get("labels") or {})})
        self.rec.add("7", "spans", "observed", f"{len(mine)} span(s) in {len({s['trace'] for s in mine})} trace(s): "
                                               + ", ".join(names), dumps({"names": names, "label_keys": keys}), limit=1500)
        hits = sorted({f"{s['name']}: {k}" for s in mine for k, v in (s.get("labels") or {}).items()
                       if self.marker in str(v)})
        if hits:
            self.rec.add("7", "message content", "observed",
                         "the message's marker IS in span labels, so content was captured: " + "; ".join(hits), dumps(hits))
        else:
            self.rec.add("7", "message content", "observed",
                         "the message's marker is in no span label: message content stayed out of the trace", "")

    def step_author(self) -> None:
        self.rec.add("4", "pricing page", "not tested",
                     f"AUTHOR: quote the pricing page's line on idle time, with the date read ({PRICING_URL})")
        self.rec.add("12", "prices", "not tested",
                     f"AUTHOR: read {PRICING_URL} and write each price with the date read: Agent Runtime compute (per "
                     f"vCPU-hour) and memory (per GiB-hour), any free tier, the asia-south1 rate if it differs; Sessions "
                     f"and Memory Bank storage and operations; Code Execution. This script states no price.")
        if self.image_versions:
            self.rec.add("11", "the runtime image", "observed",
                         "ADK's deploy installed " + ", ".join(f"{k} {v}" for k, v in sorted(self.image_versions.items())),
                         dumps(self.image_versions))

    # cleanup ------------------------------------------------------------------------------------------------
    def cleanup(self) -> None:
        """Sessions by name, then instances by name, newest first (force: their sessions and memories go with them);
        each instance is read back until it is gone, then this run's display names are swept for any orphan."""
        self.say("\n== cleanup: delete what this run created, by name ==")
        instances = [r for r in self.created if r.kind == "instance"]
        for res in reversed([r for r in self.created if r.kind == "session"]):
            eid, region = engine_id(res.parent), res.region
            try:
                self.cloud.call("cleanup", f"VertexAiSessionService(project={self.p!r}, location={region!r}, "
                                           f"agent_engine_id={eid!r}).delete_session(app_name={eid!r}, user_id={res.user!r}, "
                                           f"session_id=SESSION_ID)", "delete_session", res.parent, res.sid, res.user)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as error:
                self.say(f"[cleanup] the session goes with its instance: {self.brief(classify(error)[1])}")
        deleted = []
        for res in reversed(instances):
            try:
                self.cloud.call("cleanup", f"{sdk(self.p, res.region)}.agent_engines.delete(name={res.name!r}, force=True)",
                                "delete_instance", res.name)
                deleted.append(res)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as error:
                self.left.append((res, "the delete failed: " + classify(error)[1]))
        for res in deleted:
            if not self.gone(res):
                self.left.append((res, "deleted, but still readable after 60 s"))
        self.sweep({r.name for r in instances})

    def gone(self, res: Resource) -> bool:
        def check() -> bool:
            try:
                self.cloud.call("cleanup", f"GET {endpoint(res.name)}/v1/{res.name}  # expect 404", "get_instance",
                                res.name)
                return False
            except Refused as error:
                return error.status == 404
            except Exception:
                return False
        if self.dry:            # printed once, like every other call; nothing exists to be gone
            check()
            return True
        return bool(self.poll(check, until=bool, seconds=60, every=10))

    def sweep(self, tracked: set[str]) -> None:
        """Delete, by name, every instance whose display name is this run's (any probe run's when stamp is empty)."""
        mark = f"{PREFIX}{self.stamp}-" if self.stamp else PREFIX
        for region in dict.fromkeys(list(self.args.regions) + [self.args.runtime_region]):
            url = f"https://{region}-aiplatform.googleapis.com/v1/projects/{self.p}/locations/{region}/reasoningEngines"
            try:
                engines = self.cloud.call("cleanup", f"GET {url}  # any {mark}* not already deleted by name",
                                          "list_instances", region, stub=[]) or []
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as error:
                self.say(f"[cleanup] could not list {region}: {self.brief(classify(error)[1])}")
                continue
            for engine in engines:
                name, display = engine.get("name", ""), str(engine.get("displayName", ""))
                if not display.startswith(mark) or name in tracked:
                    continue
                orphan = Resource("instance", name, region)
                self.scrub.learn(name)
                try:
                    self.cloud.call("cleanup", f"{sdk(self.p, region)}.agent_engines.delete(name={name!r}, force=True)"
                                               f"  # an orphan of this run", "delete_instance", name)
                    if not self.gone(orphan):
                        self.left.append((orphan, "an orphan of this run, deleted but still readable after 60 s"))
                except (KeyboardInterrupt, SystemExit):
                    raise
                except Exception as error:
                    self.left.append((orphan, "an orphan of this run; the delete failed: " + classify(error)[1]))

    # report -------------------------------------------------------------------------------------------------
    def finalize(self) -> None:
        chosen = self.selected()
        for row in ROW_IDS:
            if not self.rec.for_row(row):
                steps = [s for s, rows in STEP_ROWS.items() if row in rows]
                why = "not run: its step was not selected (--only)" if not set(steps) & set(chosen) else "not run"
                self.rec.add(row, "", "not tested", why)

    def report(self, out) -> None:
        self.finalize()
        if self.dry:
            self.say(f"\nDry run: nothing was created and nothing was called; {len(self.cloud.calls)} calls printed above.")
            self.say(f"A live run writes the facts table to {rel(self.args.out)} (rows {ROW_IDS[0]}-{ROW_IDS[-1]}), "
                     f"identifiers replaced; a dry run writes nothing.\n")
            self.say(run_note(self.args))
            return
        text = render_facts(self)
        found = scan_text(text, deny_strings())
        if found:
            self.write_refused = True
            self.say("REFUSED to write the facts table: tools/leakscan.py found " + ", ".join(sorted({w for w, _ in found})))
        else:
            try:
                path = free_path(self.args.out)
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(text, encoding="utf-8", newline="\n")
                self.written = path
            except OSError as error:
                self.write_refused = True
                self.say(f"Could not write the facts table: {self.brief(error)}")
        self.say("\n== summary ==")
        for row, title, _ in ROWS:
            parts = self.rec.for_row(row)
            self.say(f"{row:>3}  {title}: {self.rec.status(row)}")
            for part in parts:
                self.say(f"       {part.label + ': ' if part.label else ''}{trim(part.finding, 220)}")
        if self.written:
            self.say(f"\nFacts table written: {rel(self.written)}. Fill its AUTHOR lines (rows 4 and 12) from "
                     f"{PRICING_URL}, with the date you read it.")
        if self.left:
            print_left_behind(self.left, self.p, out)
        else:
            self.say("\nLeft behind: nothing. Every resource this run created was deleted and read back gone.")

    def exit_code(self) -> int:
        return 3 if self.left else (4 if self.write_refused else 0)


def ours(spans) -> list:
    """The spans of every trace that names the probe agent, its model turn or its tool."""
    traces = {s.get("trace") for s in spans or [] if any(k in s.get("name", "") for k in (APP_NAME, "probe_model", "probe_tool"))}
    return [s for s in spans or [] if s.get("trace") in traces]


def rel(path: Path) -> str:
    try:
        return Path(path).resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def free_path(path: Path) -> Path:
    path = Path(path)
    if not path.exists():
        return path
    for n in itertools.count(2):
        candidate = path.with_name(f"{path.stem}-{n}{path.suffix}")
        if not candidate.exists():
            return candidate


def _cell(text: str, limit: int = 240) -> str:
    return trim(str(text).replace("|", "/").replace("\n", " "), limit)


def delete_commands(res: Resource, project: str) -> list[str]:
    region = res.region or region_of(res.name)
    return [f"python -c \"import vertexai; vertexai.Client(project='{project}', location='{region}').agent_engines"
            f".delete(name='{res.name}', force=True)\"",
            # unverified: https://docs.cloud.google.com/gemini-enterprise-agent-platform/scale/runtime/manage-deployed-agents
            #   (REST DELETE; the force=true query parameter mirrors the SDK's force=True)
            f"curl -X DELETE -H \"Authorization: Bearer $(gcloud auth print-access-token)\" "
            f"\"https://{region}-aiplatform.googleapis.com/v1/{res.name}?force=true\"",
            f"python tools/probe_agent_stack.py --project {project} --region {region} --cleanup --yes"]


def print_left_behind(left, project: str, out) -> None:
    """The one block printed without the scrubber: a delete command needs the real name. Not for pasting."""
    lines = ["", "== LEFT BEHIND: NOT SCRUBBED - real resource names for your terminal; do not paste this block =="]
    for res, why in left:
        lines += [f"{res.kind} {res.name} ({why})", *("    " + c for c in delete_commands(res, project))]
    safe_print("\n".join(lines), out)


def render_facts(probe: Probe) -> str:
    """The dated facts table, every identifier replaced. The plan's facts-table shape: what, status, evidence."""
    args, v = probe.args, probe.versions
    commit = _git_commit()
    at = f", at the authoring repo's {commit}" if commit else ""
    lines = [
        f"# Agent Engine probe: the facts lesson 10.9 rests on ({args.date})", "",
        f"*Written by `tools/probe_agent_stack.py` on {args.date}{at}, "
        f"on the author's lane, for PR 10.9-A of `plan/cohort-2-lesson-plan-2026-10-07.md` (batch 0). Every identifier "
        f"is replaced: the project id is `{PLACEHOLDER}`, the project number `NUMBER`, instance and session ids "
        f"`ENGINE_ID` and `SESSION_ID`, a person's email \"yours\". A part is **observed** when the API did it on this "
        f"run, **refused** when the API said no (its own words are the evidence, trimmed), and **not tested** when it "
        f"was not run (the reason is given). Lines marked AUTHOR are filled by hand from the pricing page.*", "",
        f"- Regions: {', '.join(args.regions)}; the runtime in {args.runtime_region}; model {args.model}.",
        f"- The runtime's account: `{sa_email(args.service_account, args.project)}`.",
        f"- This venv: google-adk {v.get('google-adk')}, google-cloud-aiplatform {v.get('google-cloud-aiplatform')}, "
        f"google-genai {v.get('google-genai')}, Python {v.get('python')}.", "",
        "| # | Fact | Status | Finding |", "|---|---|---|---|"]
    for row, title, _ in ROWS:
        parts = probe.rec.for_row(row)
        finding = " / ".join(f"{p.label + ': ' if p.label else ''}{p.finding}" for p in parts)
        lines.append(f"| {row} | {title} | {_cell(probe.rec.status(row), 300)} | {_cell(finding, 700)} |")
    lines += ["", "## Evidence", ""]
    for row, title, how in ROWS:
        lines += [f"### {row}. {title}", "", f"How: {how}", ""]
        for part in probe.rec.for_row(row):
            lines.append(f"- {part.label + ': ' if part.label else ''}**{part.status}**. {part.finding}")
            if part.evidence:
                body = part.evidence.replace("```", "'''")
                lines += ["", "  ```", *("  " + line for line in body.splitlines()), "  ```"]
        lines.append("")
    lines += ["## Left behind", ""]
    if probe.left:
        for res, why in probe.left:
            lines += [f"- {res.kind} `{res.name}`: {why}. Delete:", "", "  ```",
                      *("  " + c for c in delete_commands(res, args.project)), "  ```", ""]
    else:
        lines.append("Nothing: every resource this run created was deleted and read back gone.")
    lines += ["", "## Not probed here", "",
              "The cohort's scope (plan section 10) leaves these to after 6 December: G-decision 7's rows for N4 (the "
              "Code Execution sandbox's isolation), N5 (a computer-use sandbox) and S9 (Agent Registry, Agent Gateway, "
              "Security Command Center's agent detection), and uplift I1's Gemini calling-mode and laptop rows. Each is "
              "probed, and dated, before a page cites it.",
              "", "## For the author", "",
              f"- Row 4: quote the pricing page's line on idle time, with the date read: {PRICING_URL}.",
              "- Row 12: each price with the date read, from the same page. Then commit this file on a branch; 10.9's "
              "page cites it, and a fact that is not observed here ships as \"documented, not run\".", ""]
    return probe.scrub("\n".join(lines))


def _git_commit() -> str:
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=str(ROOT), capture_output=True, text=True,
                             timeout=10)
        return out.stdout.strip() if out.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        return ""


# ------------------------------------------------------------------------------------------- --cleanup mode

def cleanup_mode(args, cloud: Cloud, say, scrub: Scrubber, out, sleep=time.sleep) -> int:
    """Every documind-probe-* instance in the regions, deleted by name and read back gone. Nothing else is touched."""
    say("\n== cleanup: every " + PREFIX + "* instance in " + ", ".join(dict.fromkeys(args.regions + [args.runtime_region])) + " ==")
    probe = Probe(args, cloud, say, scrub, sleep=sleep)
    probe.stamp = ""                            # match any run's display names
    probe.sweep(set())
    if cloud.dry_run:
        say("\nDry run: nothing was listed or deleted.")
        return 0
    if probe.left:
        print_left_behind(probe.left, args.project, out)
        return 3
    say("\nLeft behind: nothing named " + PREFIX + "* in those regions.")
    return 0


# ---------------------------------------------------------------------------------------------- run note

def run_note(args) -> str:
    regions = " ".join(f"--region {r}" for r in args.regions)
    default_regions = list(args.regions) == list(DEFAULT_REGIONS)
    return f"""RUN NOTE - the Agent Engine probe, batch 0 (Mon 19 - Wed 21 Oct 2026), before lesson 10.9 claims anything

Where: Cloud Shell on your lane (Linux; gcloud and your ADC are ready), or a laptop with Python 3.12, from the root of
this authoring repo. Not the chat venv: google-cloud-aiplatform is not in the kit's pins, and the probe installs
nothing itself. Expect 20 to 30 minutes, most of it ADK's build of the runtime image.

1. Prerequisites, once
   export PROJECT=documind-ai-YOUR-ID                 # your lane
   gcloud services enable aiplatform.googleapis.com cloudbuild.googleapis.com cloudtrace.googleapis.com \\
     telemetry.googleapis.com logging.googleapis.com monitoring.googleapis.com storage.googleapis.com \\
     cloudresourcemanager.googleapis.com iam.googleapis.com iamcredentials.googleapis.com --project=$PROJECT
   #   (the setup page's list, plus Cloud Build for the image and IAM Credentials for row 8's impersonation;
   #    make up enables most of them already - telemetry.googleapis.com is the likeliest to be missing)
   # Your roles: Owner on the lane covers roles/aiplatform.user and actAs on {AGENT_SA} (the probe checks your
   # actAs with testIamPermissions). Row 8 mints tokens as {MEMBER_SA} and {OUTSIDER_SA}: make up's own
   # make operators granted that to its ADMIN_EMAILS; otherwise, with your address in place of the placeholder:
   (cd deploy && make operators PROJECT=$PROJECT ADMIN_EMAILS=you@example.com)
   # {AGENT_SA} exists, with roles/aiplatform.user, once make up has applied terraform/sa.tf:
   gcloud iam service-accounts describe {AGENT_SA}@$PROJECT.iam.gserviceaccount.com --format='value(email)'
   # A laptop only (Cloud Shell has these): ADC as you, billed to the lane
   gcloud auth application-default login
   gcloud auth application-default set-quota-project $PROJECT
   # documind-mcp deployed in {args.mcp_region} (make up does it) gives row 5 its door; without it row 5 still
   # reports the token, and the door reads "not tested"

2. The venv - row 11 is this step: does google-cloud-aiplatform[agent_engines] resolve beside google-adk 2.8.0?
   python3 -m venv ~/probe-venv          # a Windows laptop: py -3.12 -m venv %USERPROFILE%\\probe-venv
   ~/probe-venv/bin/pip install --quiet --upgrade pip              # --dry-run --report need pip 22.2 or later
   ~/probe-venv/bin/pip install --dry-run --ignore-installed --quiet --report /tmp/ae-resolve.json \\
     "google-adk[a2a]==2.8.0" "google-cloud-aiplatform[agent_engines]" && echo "row 11: resolves"
   ~/probe-venv/bin/pip install "google-adk[a2a]==2.8.0" "google-cloud-aiplatform[adk,agent_engines]"
   ~/probe-venv/bin/pip check
   # ...and beside the peer's own pins, which ADK's deploy appends google-cloud-aiplatform[adk,agent_engines] to:
   ~/probe-venv/bin/pip install --dry-run --ignore-installed --quiet --report /tmp/ae-resolve-peer.json \\
     -r deploy/services/agent/requirements.txt "google-cloud-aiplatform[adk,agent_engines]" && echo "peer: resolves"
   # The docs ask for google-cloud-aiplatform >= 1.112.0 ({DOC_SETUP}); the probe records the version pip chose.

3. The run
   ~/probe-venv/bin/python tools/probe_agent_stack.py --project $PROJECT{'' if default_regions else ' ' + regions}            # the dry run: read every call
   ~/probe-venv/bin/python tools/probe_agent_stack.py --project $PROJECT{'' if default_regions else ' ' + regions} --yes      # the run
   #   add --idle-wait 900 for a true cold start after 15 idle minutes (the run takes 15 minutes longer)
   # If the summary lists anything left behind (exit code 3), or the run was interrupted:
   ~/probe-venv/bin/python tools/probe_agent_stack.py --project $PROJECT --cleanup --yes

4. If row 2 is refused because the service agent may not act as {AGENT_SA}, the summary names the permission and
   the role. Grant it, then run the runtime rows again (they write the next free facts file):
   gcloud iam service-accounts add-iam-policy-binding {AGENT_SA}@$PROJECT.iam.gserviceaccount.com \\
     --member=serviceAccount:service-NUMBER@gcp-sa-aiplatform-re.iam.gserviceaccount.com \\
     --role=roles/iam.serviceAccountTokenCreator --project=$PROJECT       # the role and member the refusal names
   ~/probe-venv/bin/python tools/probe_agent_stack.py --project $PROJECT --yes --only runtime,access,telemetry

5. After the run
   - Fill the AUTHOR lines of plan/agent-engine-probe-<the run's date>.md (rows 4 and 12) from
     {PRICING_URL}, with the date you read it.
   - The probe has already held the file to tools/leakscan.py; it refuses to write a file that fails.
   - Commit it on a branch. Lesson 10.9 cites it; a fact not observed there ships as "documented, not run".
"""


# --------------------------------------------------------------------------------------------------- main

def safe_print(text: str, out) -> None:
    encoding = getattr(out, "encoding", None) or "utf-8"
    print(str(text).encode(encoding, "replace").decode(encoding, "replace"), file=out, flush=True)


def parse_args(argv=None):
    p = argparse.ArgumentParser(prog="probe_agent_stack.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--project", required=True, help="the lane's project id; there is no default")
    p.add_argument("--region", action="append", dest="regions", metavar="REGION",
                   help="an empty instance here (rows 1, 10); repeatable; default us-central1 and asia-south1")
    p.add_argument("--runtime-region", default=RUNTIME_REGION, help="where the probe agent runs (rows 2-9); default %(default)s")
    mode = p.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="print every call and make none (the default)")
    mode.add_argument("--yes", action="store_true", help="make the calls: create, deploy, query and delete on --project")
    p.add_argument("--cleanup", action="store_true", help=f"delete every {PREFIX}* instance in the regions (needs --yes)")
    p.add_argument("--run-note", action="store_true", help="print the prerequisites and the commands, then stop")
    p.add_argument("--only", help=f"comma-separated steps, prerequisites added: {', '.join(STEPS)}")
    p.add_argument("--service-account", default=AGENT_SA, help="the runtime's account; default %(default)s")
    p.add_argument("--member-sa", default=MEMBER_SA, help="row 8's principal with roles/aiplatform.user; default %(default)s")
    p.add_argument("--outsider-sa", default=OUTSIDER_SA, help="row 8's principal with no role; default %(default)s")
    p.add_argument("--model", default=MODEL, help="the probe agent's model; default %(default)s")
    p.add_argument("--mcp-region", default=RUNTIME_REGION, help="documind-mcp's region, for row 5's audience")
    p.add_argument("--mcp-url", default="", help="documind-mcp's URL, if not https://documind-mcp-NUMBER.REGION.run.app")
    p.add_argument("--idle-wait", type=int, default=0, metavar="SECONDS", help="idle time before the first call (row 4)")
    p.add_argument("--trace-wait", type=int, default=180, metavar="SECONDS", help="how long to wait for spans (row 7)")
    p.add_argument("--date", default=dt.date.today().isoformat(), help="the facts table's date; default today")
    p.add_argument("--out", help="the facts table; default plan/agent-engine-probe-<date>.md")
    a = p.parse_args(argv)
    a.regions = list(dict.fromkeys(a.regions or DEFAULT_REGIONS))
    for region in a.regions + [a.runtime_region, a.mcp_region]:
        if not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", region):
            p.error(f"not a region: {region!r}")
    if a.project != PLACEHOLDER and not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", a.project):
        p.error(f"not a project id: {a.project!r}")
    if a.yes and a.project == PLACEHOLDER:
        p.error(f"--yes needs your lane's project id, not the placeholder {PLACEHOLDER}")
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", a.date):
        p.error(f"--date takes YYYY-MM-DD, not {a.date!r}")
    if a.only:
        a.only = [s.strip() for s in a.only.split(",") if s.strip()]
        unknown = [s for s in a.only if s not in STEPS]
        if unknown:
            p.error(f"unknown steps {unknown}; choose from {', '.join(STEPS)}")
    a.out = Path(a.out) if a.out else ROOT / "plan" / f"agent-engine-probe-{a.date}.md"
    return a


def main(argv=None, *, backend_factory=LiveBackend, out=None, sleep=time.sleep) -> int:
    out = out or sys.stdout
    args = parse_args(argv)
    scrub = Scrubber(args.project)

    def say(text: str = "") -> None:
        safe_print(scrub(text), out)

    if args.run_note:
        say(run_note(args))
        return 0
    dry = not args.yes
    say(f"Agent Engine probe for lesson 10.9 (PR 10.9-A) - {'DRY RUN: every call printed, none made' if dry else 'LIVE'}")
    say(f"project {args.project} | regions {', '.join(args.regions)} | runtime {args.runtime_region} | {args.date}\n")
    say(COST_NOTE)
    cloud = Cloud(args.project, dry_run=dry, backend_factory=backend_factory, say=say)
    if args.cleanup:
        return cleanup_mode(args, cloud, say, scrub, out, sleep=sleep)
    probe = Probe(args, cloud, say, scrub, sleep=sleep)
    interrupted = False
    try:
        probe.run()
    except KeyboardInterrupt:
        interrupted = True
        say("\nInterrupted: deleting what this run created before stopping (a second Ctrl-C skips that; "
            "--cleanup --yes then finds what is left).")
    finally:
        probe.cleanup()
        probe.report(out)
    return 130 if interrupted else probe.exit_code()


if __name__ == "__main__":
    sys.exit(main())
