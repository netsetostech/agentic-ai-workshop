#!/usr/bin/env python3
"""make managed-peer-*: the A2A peer of workshop lesson 10.6 on Vertex AI Agent Engine (workshop lesson 10.9).

    bash commands/managed-peer.sh up       --project <id> [--region R] [--services-region R]     # 10 to 20 minutes
    bash commands/managed-peer.sh ask      --project <id> [--tenant zeta] [--question Q] [--host cloudrun] [--json]
    bash commands/managed-peer.sh trace    --project <id> [--since MINUTES]
    bash commands/managed-peer.sh smoke    --project <id> [--keep]
    bash commands/managed-peer.sh sessions --project <id> [--delete]
    bash commands/managed-peer.sh down     --project <id>
    python commands/managed_peer.py stage   --dir DIR [--project <id>]   # what up deploys, written out: no call, Rs 0
    python commands/managed_peer.py compare [--json]                   # Cloud Run against Agent Engine, from this
                                                                       # machine's records: no call, Rs 0
Any of the first six with --dry-run prints every call it would make and makes none (no credential, Rs 0).

The SAME peer on a second host. up stages services/agent/agent.py and its requirements.txt byte for byte, with
commands/managed_peer_agent.py beside them as the package's __init__.py (the peer's own agent, its model pinned to
location global), and deploys the package with google-adk's own deploy (`adk deploy agent_engine`) into an instance
named documind-managed-peer that runs as documind-agent-sa: the account the Cloud Run peer runs as, on acme's roster
alone (the lesson plan's decision 13: no new account, no Terraform). Its environment is the Cloud Run peer's: MCP_URL
(documind-mcp), AGENT_MODEL, and ADK_MAX_LLM_CALLS=12, the peer's cap. Telemetry is on with message content off,
min_instances 0 and max_instances 1. Agent Engine's service agent is granted GRANT_ROLE on documind-agent-sa first,
and down takes the grant back when up added it. Run again, up does nothing unless --redeploy.

ask sends one question through the instance's query API (streamQuery, async_stream_query) as documind-ui-sa: acme's
is answered through documind-mcp, and TENANT=zeta's is refused by the roster, asked the way make smoke-agent's check
4 asks the Cloud Run peer. HOST=cloudrun asks the Cloud Run peer the same question over A2A, measured the same way.
trace reads what the last ask left: the spans in Cloud Trace (the question's words must be in none of them), the rows
documind-mcp logged (the caller is documind-agent-sa from either host: one identity, two hosts), and the runtime's
own line (its GOOGLE_CLOUD_LOCATION, the versions its image installed). sessions lists the instance's managed
sessions and reads the newest as another user, which ADK's session service refuses - a check in the client, after
the read - beside the API's own read, which names no user. smoke is the lesson's proof: it deploys an instance when
there is none, checks all of the above, asks the Cloud Run peer the same questions, prints the comparison table and
deletes what it deployed unless --keep. down deletes the instance by name and every documind-managed-peer* instance
in the regions, takes the grant back, says what it deleted and reads it back gone; run again, it says there is
nothing to delete.

Every Google call goes through one seam, Seam.call(): printed, then made - or printed only, with --dry-run. The tests
replace the backend (commands/tests/test_managed_peer.py). Each run appends a record to
evals/reports/managed-peer/runs.ndjson (gitignored; no identifier in it): latency to the first event and to the
last, whether it was the first call after a deploy and how long the host had idled, the region, the runtime's account
and the caller, the model's tokens and rupees where the reply carries them, the host's scaling and price. --json
prints the record instead. compare reads the records into the Cloud Run against Agent Engine table.

Torn down by default. Agent Engine's price is not stated here (fact 12) and whether an idle instance bills is fact 4,
so the smoke deletes what it deploys and up says what bills until make managed-peer-down. While the instance exists,
every account holding roles/aiplatform.user on the project may query it unless the instance has an IAM policy of its
own (fact 8), and it answers each of them as documind-agent-sa, on acme's roster: up lists them.

FACTS are what this rests on that no lane had shown when it was written (13 October 2026). Each is a row of the
author's dated probe of Agent Engine (tools/probe_agent_stack.py in the authoring repository, run in batch 0, Mon 19
- Wed 21 Oct 2026; lesson 10.9's page cites its facts table). A refusal that contradicts one stops the command with
that row's name, what the platform said and what to do. Exit 0 done, 1 a check failed, 2 stopped (a precondition, or
a refusal that settles no fact), 3 a fact refused, 4 something could not be deleted.
"""
from __future__ import annotations

import argparse
import asyncio
import datetime as dt
import hashlib
import json
import logging
import re
import shutil
import statistics
import sys
import tempfile
import time
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
for _p in (str(KIT), str(KIT / "smoke")):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from shared import prices  # noqa: E402  (stdlib: the kit's list prices and USD_INR)
import smoke_agent  # noqa: E402  (stdlib: make smoke-agent's question, its expected answer and its A2A request)

PLACEHOLDER = "documind-ai-YOUR-ID"
APP_NAME = "documind_peer"                  # the staged package: a Python identifier, because ADK's loader imports it
DISPLAY_NAME = "documind-managed-peer"      # every instance this creates; down deletes only names starting with it
DESCRIPTION = "DocuMind's A2A peer (services/agent/agent.py, unchanged) on Agent Engine - workshop lesson 10.9"
PEER = KIT / "services" / "agent"
WRAPPER = KIT / "commands" / "managed_peer_agent.py"
DEPLOY_84 = KIT / "commands" / "lesson-8.4.sh"
AGENT_SA = "documind-agent-sa"              # decision 13: the cohort reuses the Cloud Run peer's account (sa.tf)
MEMBER_SA = "documind-ui-sa"                # roles/aiplatform.user on the project; make operators lets you mint as it
OUTSIDER_SA = "documind-outsider-sa"        # no project role at all (sa.tf outsider_roles = [])
PEER_TENANT = "acme"                        # the one roster documind-agent-sa is on (commands/lane.py roster_plan)
SERVICE_AGENT = "service-{number}@gcp-sa-aiplatform-re.iam.gserviceaccount.com"     # Agent Engine's service agent
# The grant that lets the service agent run the runtime as documind-agent-sa. Unverified: it is the role the author's
# probe grants when its deploy is refused (its run note's step 4), until fact 2 says which one the platform asks for;
# a refusal that names a permission says which role carries it (grant_hint()).
GRANT_ROLE = "roles/iam.serviceAccountTokenCreator"
MIN_INSTANCES, MAX_INSTANCES = 0, 1         # facts 3 and 4: no instance kept warm, and one at most
PEER_MAX_LLM_CALLS = 12                     # the peer's cap (the lesson plan's decision 14: on, at 12)
QUESTION = smoke_agent.DEFAULT_QUESTION     # make smoke-agent's question, with its expected answer pattern
OTHER_TENANT = "For tenant {tenant}: {question}"        # make smoke-agent's check 4 asks zeta this way
REFUSAL_WORDS = ("roster", "not on", "refus", "cannot", "not a member", "no access")   # the same check's words
OTHER_USER = "another-user"                 # the user id sessions reads a session as, which ADK must refuse
RESERVED_ENV = frozenset({"GOOGLE_CLOUD_PROJECT", "GOOGLE_CLOUD_QUOTA_PROJECT", "GOOGLE_CLOUD_LOCATION", "PORT",
                          "K_SERVICE", "K_REVISION", "K_CONFIGURATION", "GOOGLE_APPLICATION_CREDENTIALS"})
QUERY_ROLES = ("roles/aiplatform.user", "roles/aiplatform.admin", "roles/editor", "roles/owner")
CLOUD_PLATFORM = "https://www.googleapis.com/auth/cloud-platform"
RECORDS = KIT / "evals" / "reports" / "managed-peer"     # evals/reports/ is gitignored: one lab's state
RECORD_KIND = "managed-peer/1"
INSTANCE_KEYS = ("name", "deployed_at", "asks", "last_ask_at", "last_ask")   # state.json's keys about the instance

FACTS = {
    "1": "Agent Engine instances can be created in the instance's region (us-central1 and asia-south1 probed)",
    "2": "documind-agent-sa is accepted as the runtime's account, with the grant its service agent needs on it",
    "3": "min_instances 0 and max_instances 1 are accepted",
    "4": "whether an idle instance bills, and the first call's latency",
    "5": "the runtime's metadata server mints an ID token for documind-mcp's audience",
    "6": "the runtime's GOOGLE_CLOUD_LOCATION is its region, so Gemini 3.x needs the global pin",
    "7": "the spans the default telemetry writes, with message content off",
    "8": "per-resource IAM on an instance, or any roles/aiplatform.user holder may query it",
    "9": "one user reading another user's managed session",
    "11": "google-cloud-aiplatform[agent_engines] resolves beside google-adk 2.8.0 and the peer's pins",
    "12": "the prices",
}


# ----------------------------------------------------------------------------------------------- errors

class Refused(Exception):
    """An API said no: its HTTP status and its own words."""

    def __init__(self, status: int, body: str = ""):
        self.status, self.body = int(status), str(body or "")
        super().__init__(f"HTTP {status}: {api_message(self.body)}")


class Stop(Exception):
    """A precondition is missing, or a refusal that settles no fact: exit 2 with the reason."""


class FactRefused(Exception):
    """The platform contradicted one of FACTS: exit 3, naming the row."""

    def __init__(self, row: str, said: str, meaning: str, todo: str = ""):
        self.row, self.said, self.meaning, self.todo = row, str(said or ""), meaning, todo
        super().__init__(f"fact {row}: {FACTS[row]}")

    def render(self) -> str:
        lines = [f"STOPPED on fact {self.row} of the author's Agent Engine probe: {FACTS[self.row]}",
                 f"  the platform said: {trim(self.said, 500)}", f"  what it means: {self.meaning}"]
        if self.todo:
            lines.append(f"  what to do: {self.todo}")
        lines.append("  Lesson 10.9's page reads the author's dated capture wherever a fact fails on your lane.")
        return "\n".join(lines)


def trim(text, limit: int = 300) -> str:
    text = " ".join(str(text if text is not None else "").split())
    return text if len(text) <= limit else text[:limit] + " ..."


def api_message(body) -> str:
    """The API's own message out of an error body, or its first line."""
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


# ---------------------------------------------------------------------------------------------- helpers

def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def parse_time(text: str) -> dt.datetime:
    return dt.datetime.strptime(text, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=dt.timezone.utc)


def shift(text: str, seconds: float) -> str:
    return (parse_time(text) + dt.timedelta(seconds=seconds)).strftime("%Y-%m-%dT%H:%M:%SZ")


def idle_since(stamp) -> int | None:
    try:
        return int((dt.datetime.now(dt.timezone.utc) - parse_time(stamp)).total_seconds())
    except (TypeError, ValueError):
        return None


def region_of(name: str) -> str:
    m = re.match(r"projects/[^/]+/locations/([^/]+)/", str(name or ""))
    return m.group(1) if m else ""


def engine_id(name: str) -> str:
    return str(name or "").rstrip("/").rsplit("/", 1)[-1]


def endpoint(region: str) -> str:
    return f"https://{region}-aiplatform.googleapis.com"


def sa_email(account: str, project: str) -> str:
    return account if "@" in account else f"{account}@{project}.iam.gserviceaccount.com"


# Google's own accounts on a project carry its number in their id (NUMBER-compute@developer, NUMBER@cloudservices,
# service-NUMBER@gcp-sa-...); most projects grant them Editor, so may_query() lists them (13 Oct 2026)
GOOGLE_OWNED = re.compile(r"@(?:developer|cloudservices|cloudbuild)\.gserviceaccount\.com$|@gcp-sa-[a-z0-9-]+\.iam\.gserviceaccount\.com$")


def short(account) -> str:
    """An account as a record names it: a service account by its id, a project number in one of Google's own written
    NUMBER; a person is "a person", ADC is "you"."""
    account = str(account or "")
    if not account:
        return "you"
    if account.endswith(".gserviceaccount.com") or "@" not in account:
        local = account.split("@", 1)[0]
        if GOOGLE_OWNED.search(account):
            local = "-".join("NUMBER" if part.isdigit() else part for part in local.split("-"))
        return local
    return "a person"


def rnd(value):
    return None if value is None else round(float(value), 2)


def pick(obj, *keys):
    """The first of keys (camelCase or snake_case) found anywhere in a JSON-like object."""
    wanted, stack = set(keys), [obj]
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


def cloud_run_settings() -> dict:
    """The Cloud Run peer as commands/lesson-8.4.sh deploys it: its scaling, its account, its model, who may call it."""
    text = DEPLOY_84.read_text(encoding="utf-8")
    block = text.split("# ---- DEPLOY ----", 1)[1].split("# ---- SMOKE ----", 1)[0]

    def flag(name: str) -> str:
        m = re.search(rf"--{name}=(?:\$\{{\w+:-)?([\w.@$-]+)", block)
        return m.group(1) if m else ""
    model = re.search(r"\bAGENT_MODEL=([\w.-]+)", block)
    loop = re.search(r"for sa in ([^;\n]+); do", block)
    if not model:
        raise Stop("commands/lesson-8.4.sh sets no AGENT_MODEL")
    return {"min_instances": int(flag("min-instances") or 0), "max_instances": int(flag("max-instances") or 0),
            "concurrency": int(flag("concurrency") or 0), "timeout_s": int(flag("timeout") or 0),
            "memory": flag("memory"), "cpu": flag("cpu"), "model": model.group(1),
            "account": flag("service-account").split("@", 1)[0], "invokers": loop.group(1).split() if loop else []}


def adk_pin() -> str:
    """The google-adk version the peer's image pins, which the managed runtime's image is built with too."""
    pins = (PEER / "requirements.txt").read_text(encoding="utf-8")
    m = re.search(r"^google-adk(?:\[[^\]]*\])?==([\d.]+)$", pins, re.M)
    if not m:
        raise Stop("services/agent/requirements.txt pins no google-adk")
    return m.group(1)


def bindings(policy) -> set[tuple[str, str]]:
    """(role, member) of every binding without a condition."""
    out = set()
    for binding in (policy or {}).get("bindings", []) if isinstance(policy, dict) else []:
        if binding.get("condition"):
            continue
        for member in binding.get("members", []):
            out.add((binding.get("role", ""), member))
    return out


def with_binding(policy: dict, role: str, member: str) -> dict:
    new = json.loads(json.dumps(policy or {}))
    for binding in new.setdefault("bindings", []):
        if binding.get("role") == role and not binding.get("condition"):
            binding.setdefault("members", []).append(member)
            return new
    new["bindings"].append({"role": role, "members": [member]})
    return new


def without_binding(policy: dict, role: str, member: str) -> dict:
    new, kept = json.loads(json.dumps(policy or {})), []
    for binding in new.get("bindings", []):
        if binding.get("role") == role and not binding.get("condition"):
            binding["members"] = [m for m in binding.get("members", []) if m != member]
            if not binding["members"]:
                continue
        kept.append(binding)
    new["bindings"] = kept
    return new


def grant_hint(text: str, sa: str) -> str:
    """The permission a refusal names, and the make line that grants the role carrying it instead."""
    perm = re.search(r"iam\.serviceAccounts\.(actAs|getAccessToken|getOpenIdToken|signBlob|signJwt|implicitDelegation)",
                     text or "")
    if not perm:
        return ""
    role = "roles/iam.serviceAccountUser" if perm.group(1) == "actAs" else "roles/iam.serviceAccountTokenCreator"
    return (f"the refusal names {perm.group(0)}, which {role} carries: make managed-peer-down, then make "
            f"managed-peer-up MANAGED_PEER_GRANT_ROLE={role} grants that role on {sa} instead")


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


# ------------------------------------------------------------------------------------ what up deploys

def deploy_inputs(project: str, mcp_url: str, model: str) -> tuple[dict, dict]:
    """The deploy's .agent_engine_config.json and .env, as data.

    ADK reads the config file and passes its keys to agent_engines.update(config=...) unread (google-adk 2.8.0
    cli/cli_deploy.py:1154-1159, :1439); the keys follow Google's deploy page (facts 2 and 3). The .env becomes the
    runtime's env_vars (cli_deploy.py:1226-1303): the Cloud Run peer's own variables (commands/lesson-8.4.sh), and the
    cap. Four of them stay behind: GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION, which the platform reserves and
    ADK's Dockerfile sets (the location to the region: GlobalGemini answers that); GOOGLE_GENAI_USE_VERTEXAI, whose
    part ADK's Dockerfile plays with GOOGLE_GENAI_USE_ENTERPRISE=1; and SELF_URL, the agent card's address, because
    no card is served here - the peer is asked through the platform's query API.
    """
    config = {"service_account": sa_email(AGENT_SA, project), "min_instances": MIN_INSTANCES,
              "max_instances": MAX_INSTANCES}
    env = {"MCP_URL": mcp_url, "AGENT_MODEL": model, "ADK_MAX_LLM_CALLS": str(PEER_MAX_LLM_CALLS)}
    # A .env's GOOGLE_CLOUD_LOCATION would become the deploy's region AND stay in env_vars (cli_deploy.py:1247-1258),
    # and the platform reserves it and the GOOGLE_CLOUD_AGENT_ENGINE prefix: nothing reserved goes in.
    assert not RESERVED_ENV & set(env) and not any(k.startswith("GOOGLE_CLOUD_AGENT_ENGINE") for k in env), env
    return config, env


def stage(root: Path, project: str, mcp_url: str, model: str, aiplatform_pin: str = "") -> dict:
    """The folder ADK's deploy copies, with its .env and config beside it rather than inside it, so they are not
    shipped in the source package. ADK checks both paths after changing directory, so they are absolute."""
    folder = root / APP_NAME
    folder.mkdir(parents=True)
    shutil.copyfile(PEER / "agent.py", folder / "agent.py")                       # the peer, byte for byte
    shutil.copyfile(PEER / "requirements.txt", folder / "requirements.txt")       # its image's pins, byte for byte
    shutil.copyfile(WRAPPER, folder / "__init__.py")                              # root_agent, on location global
    for extra in ("chain.py", "pins.py", "tool_pins.json"):     # agent.py's own modules and data when the kit has them
        if (PEER / extra).exists():                             # (PEER_CHAIN, TOOL_PINS: 13 October 2026), so an import
            shutil.copyfile(PEER / extra, folder / extra)       # that works on Cloud Run works on Agent Engine
    if aiplatform_pin:
        # With a google-cloud-aiplatform line present, ADK's deploy appends none of its own (cli_deploy.py:151-175);
        # without one, it appends the line unpinned and the image takes the latest (fact 11).
        with (folder / "requirements.txt").open("a", encoding="utf-8", newline="\n") as f:
            f.write(f"google-cloud-aiplatform[adk,agent_engines]=={aiplatform_pin}\n")
    config, env = deploy_inputs(project, mcp_url, model)
    side = root / "deploy_config"
    side.mkdir()
    config_file, env_file = side / ".agent_engine_config.json", side / ".env"
    config_file.write_text(json.dumps(config, indent=2) + "\n", encoding="utf-8", newline="\n")
    env_file.write_text("".join(f"{k}={v}\n" for k, v in env.items()), encoding="utf-8", newline="\n")
    return {"folder": folder.resolve(), "env_file": env_file.resolve(), "config_file": config_file.resolve(),
            "config": config, "env": env}


def sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


# ---------------------------------------------------------------------------------------- the one seam

class Seam:
    """Every call to Google passes through call(): printed first, then made - or, with --dry-run, printed only. The
    backend is built on the first live call, so a dry run never builds one and never imports a Google library."""

    def __init__(self, project: str, factory, *, dry_run: bool, say):
        self.project, self.factory, self.dry_run, self.say = project, factory, dry_run, say
        self._google = None
        self.calls: list[str] = []

    @property
    def google(self):
        if self._google is None:
            self._google = self.factory(self.project)
        return self._google

    def call(self, desc: str, method: str, *args, stub=None, quiet: bool = False):
        self.calls.append(desc)
        if not quiet:
            self.say(f"  {'would call' if self.dry_run else 'call'}: {desc}")
        if self.dry_run:
            return stub
        return getattr(self.google, method)(*args)


class LiveGoogle:
    """The real calls. Nothing here is imported until a live run reaches it: the dry run and the tests never build it.

    Needs google-adk at the peer's pin and google-cloud-aiplatform[adk,agent_engines] (commands/managed-peer.sh makes
    that venv), and Application Default Credentials as you. Where ADK makes a call itself - the create, its own deploy,
    the delete, the session service - it is made the way google-adk 2.8.0 makes it; the rest follow Google's pages.
    """

    def __init__(self, project: str):
        self.project = project

    # credentials and REST ------------------------------------------------------------------------------------
    def _credentials(self, as_sa: str | None = None):
        import google.auth
        from google.auth.transport.requests import Request
        source, _ = google.auth.default(scopes=[CLOUD_PLATFORM])
        if not as_sa:
            return source
        from google.auth import impersonated_credentials
        # the shape the peer's own _mcp_headers mints with (services/agent/agent.py)
        creds = impersonated_credentials.Credentials(source_credentials=source, target_principal=as_sa,
                                                     target_scopes=[CLOUD_PLATFORM], lifetime=900)
        try:
            creds.refresh(Request())
        except Exception as error:
            raise Stop(f"could not mint a token as {as_sa} (make operators grants that to the lane's operators): "
                       f"{trim(error, 200)}") from error
        return creds

    def _rest(self, method: str, url: str, *, body=None, params=None, credentials=None, stream=False, timeout=120):
        from google.auth.transport.requests import AuthorizedSession
        response = AuthorizedSession(credentials or self._credentials()).request(
            method, url, json=body, params=params, stream=stream, timeout=timeout)
        if response.status_code >= 400:
            raise Refused(response.status_code, response.text)
        return response

    def _client(self, region: str):
        import vertexai
        # the client google-adk 2.8.0 builds (cli/cli_deploy.py:1319: project, location)
        return vertexai.Client(project=self.project, location=region)

    # the project ---------------------------------------------------------------------------------------------
    def project_number(self) -> str:
        # https://cloud.google.com/resource-manager/reference/rest/v1/projects/get
        got = self._rest("GET", f"https://cloudresourcemanager.googleapis.com/v1/projects/{self.project}").json()
        return str(got.get("projectNumber", ""))

    def project_policy(self) -> dict:
        # https://cloud.google.com/resource-manager/reference/rest/v1/projects/getIamPolicy
        url = f"https://cloudresourcemanager.googleapis.com/v1/projects/{self.project}:getIamPolicy"
        return self._rest("POST", url, body={"options": {"requestedPolicyVersion": 3}}).json()

    # instances -----------------------------------------------------------------------------------------------
    def create_instance(self, region: str, display_name: str) -> str:
        # google-adk 2.8.0 cli/cli_deploy.py:1430-1431: agent_engines.create(), then .api_resource.name. The display
        # name follows Google's deploy page; ADK passes none, and down finds this command's instances by it.
        engine = self._client(region).agent_engines.create(config={"display_name": display_name})
        return engine.api_resource.name

    def get_instance(self, name: str) -> dict:
        # GET v1 projects/*/locations/*/reasoningEngines/* (Google's manage-deployed-agents page)
        return self._rest("GET", f"{endpoint(region_of(name))}/v1/{name}").json()

    def list_instances(self, region: str) -> list:
        url = f"{endpoint(region)}/v1/projects/{self.project}/locations/{region}/reasoningEngines"
        out, token = [], None
        for _ in range(20):
            page = self._rest("GET", url, params={"pageSize": 100, **({"pageToken": token} if token else {})}).json()
            out += page.get("reasoningEngines", [])
            token = page.get("nextPageToken")
            if not token:
                break
        return out

    def delete_instance(self, name: str) -> None:
        # google-adk 2.8.0 cli/cli_deploy.py:1445: agent_engines.delete(name=...); force=True takes the instance's
        # sessions with it (Google's manage-deployed-agents page)
        try:
            self._client(region_of(name)).agent_engines.delete(name=name, force=True)
        except Exception as error:
            if getattr(error, "code", None) == 404 or "NOT_FOUND" in str(error):
                raise Refused(404, str(error)) from error
            raise

    def deploy(self, name: str, folder, env_file, config_file, display_name: str, adk_version: str) -> None:
        # google-adk's own deploy, as `adk deploy agent_engine --agent_engine_id` calls it (cli/cli_deploy.py:978,
        # cli/cli_tools_click.py:2789-2815): ADK's Dockerfile and class methods, then agent_engines.update(name=...,
        # config=...) (:1439). With the id given, a failed update never deletes the instance (:1444): down does, by
        # name. The two flags passed False are deprecated and unused in 2.8.0, where True only prints a warning; the
        # client's progress logger is raised to INFO as the CLI raises it, so the build's progress prints as it goes.
        from google.adk.cli import cli_deploy
        progress = logging.getLogger("vertexai_genai.agentengines")
        if not progress.handlers:
            progress.addHandler(logging.StreamHandler(sys.stdout))
        progress.setLevel(logging.INFO)
        cli_deploy.to_agent_engine(agent_folder=str(folder), project=self.project, region=region_of(name),
                                   agent_engine_id=name, display_name=display_name, description=DESCRIPTION,
                                   otel_to_cloud=True, env_file=str(env_file),
                                   agent_engine_config_file=str(config_file), adk_version=adk_version,
                                   absolutize_imports=False, skip_agent_import_validation=False)

    # the questions -------------------------------------------------------------------------------------------
    def query(self, name: str, message: str, user_id: str, as_sa: str | None) -> dict:
        # POST v1 {name}:streamQuery?alt=sse with class_method async_stream_query (Google's use-an-adk-agent page; the
        # method is one of ADK's, cli_deploy.py's _AGENT_ENGINE_CLASS_METHODS)
        credentials = self._credentials(as_sa)
        body = {"class_method": "async_stream_query", "input": {"user_id": user_id, "message": message}}
        started = time.monotonic()
        response = self._rest("POST", f"{endpoint(region_of(name))}/v1/{name}:streamQuery", body=body,
                              params={"alt": "sse"}, credentials=credentials, stream=True, timeout=600)
        first, lines = None, []
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            if first is None:
                first = time.monotonic() - started
            lines.append(line)
        return {"status": response.status_code, "events": stream_events(lines), "first_event_s": first,
                "total_s": time.monotonic() - started}

    def a2a_send(self, url: str, message: str, as_sa: str | None) -> dict:
        """The Cloud Run peer, asked as make smoke-agent asks it (smoke/smoke_agent.py send()), with an ID token for its
        URL minted as as_sa: one of the two accounts commands/lesson-8.4.sh lets invoke it."""
        import google.auth.transport.requests
        from google.auth import impersonated_credentials
        if not as_sa:
            raise Stop("the Cloud Run peer admits documind-ui-sa and documind-chat-sa alone (commands/lesson-8.4.sh): "
                       "ask it as one of them, not as yourself")
        idc = impersonated_credentials.IDTokenCredentials(self._credentials(as_sa), target_audience=url,
                                                          include_email=True)
        idc.refresh(google.auth.transport.requests.Request())
        token = idc.token
        smoke_agent.AGENT_URL = url.rstrip("/")
        started = time.monotonic()
        status, reply, text = smoke_agent.send(token, message)
        return {"status": status, "reply": reply, "text": text, "first_event_s": None,
                "total_s": time.monotonic() - started}

    # IAM ----------------------------------------------------------------------------------------------------
    def sa_policy(self, email: str) -> dict:
        # https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts/getIamPolicy
        return self._rest("POST", f"https://iam.googleapis.com/v1/projects/{self.project}/serviceAccounts/{email}"
                                  ":getIamPolicy", body={"options": {"requestedPolicyVersion": 3}}).json()

    def set_sa_policy(self, email: str, policy: dict) -> dict:
        # https://cloud.google.com/iam/docs/reference/rest/v1/projects.serviceAccounts/setIamPolicy (its etag kept)
        return self._rest("POST", f"https://iam.googleapis.com/v1/projects/{self.project}/serviceAccounts/{email}"
                                  ":setIamPolicy", body={"policy": policy}).json()

    # sessions -----------------------------------------------------------------------------------------------
    def _sessions(self, name: str):
        from google.adk.sessions.vertex_ai_session_service import VertexAiSessionService
        return VertexAiSessionService(project=self.project, location=region_of(name), agent_engine_id=engine_id(name))

    def list_sessions(self, name: str) -> list:
        # VertexAiSessionService.list_sessions with no user id sends no filter (google-adk 2.8.0
        # sessions/vertex_ai_session_service.py:306-333)
        listed = asyncio.run(self._sessions(name).list_sessions(app_name=engine_id(name)))
        return [{"user_id": s.user_id, "id": s.id, "updated": s.last_update_time} for s in listed.sessions]

    def session_as(self, name: str, session_id: str, user_id: str) -> dict | None:
        # VertexAiSessionService.get_session reads the session, then compares its user id and raises ValueError for
        # another user's (vertex_ai_session_service.py:221-304): the check is in this client, not in the API
        got = asyncio.run(self._sessions(name).get_session(app_name=engine_id(name), user_id=user_id,
                                                           session_id=session_id))
        if got is None:
            return None
        return {"user_id": got.user_id, "id": got.id,
                "events": [event_line(e.model_dump(mode="json", exclude_none=True)) for e in got.events]}

    def raw_session(self, name: str, session_id: str) -> dict:
        # the read VertexAiSessionService itself makes, which names no user (vertex_ai_session_service.py:252-258)
        async def read():
            async with self._client(region_of(name)).aio as client:
                return await client.agent_engines.sessions.get(
                    name=f"reasoningEngines/{engine_id(name)}/sessions/{session_id}")
        got = asyncio.run(read())
        return got.model_dump(mode="json", exclude_none=True) if hasattr(got, "model_dump") else dict(got)

    def delete_session(self, name: str, session_id: str, user_id: str) -> None:
        # VertexAiSessionService.delete_session, which checks the owner first (vertex_ai_session_service.py:335-369)
        asyncio.run(self._sessions(name).delete_session(app_name=engine_id(name), user_id=user_id,
                                                        session_id=session_id))

    # what the asks left ---------------------------------------------------------------------------------------
    def trace_spans(self, start: str, end: str) -> list:
        # https://cloud.google.com/trace/docs/reference/v1/rest/v1/projects.traces/list (view COMPLETE)
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

    def log_entries(self, log_filter: str, limit: int) -> list:
        # https://cloud.google.com/logging/docs/reference/v2/rest/v2/entries/list
        body = {"resourceNames": [f"projects/{self.project}"], "filter": log_filter, "orderBy": "timestamp desc",
                "pageSize": limit}
        return self._rest("POST", "https://logging.googleapis.com/v2/entries:list", body=body).json().get("entries", [])


# ------------------------------------------------------------------------------- reading what came back

def stream_events(lines) -> list:
    """A streamQuery reply: one JSON event per line, or per `data:` line; server-sent-event fields are skipped."""
    events = []
    for line in lines:
        text = str(line).strip()
        if text.startswith("data:"):
            text = text[5:].strip()
        elif text.startswith((":", "event:", "id:", "retry:")):
            continue
        if not text or text == "[DONE]":
            continue
        try:
            events.append(json.loads(text))
        except ValueError:
            events.append({"unparsed": text})
    return events


def _part(part: dict, *names):
    for name in names:
        if isinstance(part.get(name), dict):
            return part[name]
    return None


def _usage(total: dict, meta: dict) -> None:
    total["calls"] += 1
    total["in"] += int(meta.get("prompt_token_count") or meta.get("promptTokenCount") or 0)
    total["out"] += int(meta.get("candidates_token_count") or meta.get("candidatesTokenCount") or 0)
    total["thinking"] += int(meta.get("thoughts_token_count") or meta.get("thoughtsTokenCount") or 0)
    total["cached"] += int(meta.get("cached_content_token_count") or meta.get("cachedContentTokenCount") or 0)


def event_line(event: dict) -> str:
    """One managed-session event as sessions prints it: who wrote it, then its calls, results and text."""
    content = event.get("content") or {}
    bits = []
    for part in content.get("parts") or []:
        call = _part(part, "function_call", "functionCall")
        result = _part(part, "function_response", "functionResponse")
        if call:
            bits.append(f"function_call {call.get('name')}({json.dumps(call.get('args') or {}, ensure_ascii=False)})")
        elif result:
            bits.append(f"function_response {result.get('name')}: "
                        f"{trim(json.dumps(result.get('response'), ensure_ascii=False), 90)}")
        elif isinstance(part.get("text"), str):
            bits.append(f"text {trim(part['text'], 120)!r}")
    return f"{event.get('author') or content.get('role') or '?'}: {'; '.join(bits) or '(no content)'}"


def read_turn(events) -> dict:
    """One async_stream_query reply: the answer, the tool calls and their results, errors and the model's usage."""
    answer, calls, results, errors = "", [], [], []
    usage = {"calls": 0, "in": 0, "out": 0, "thinking": 0, "cached": 0}
    for event in events or []:
        if not isinstance(event, dict):
            continue
        if "unparsed" in event:
            errors.append(str(event["unparsed"]))
            continue
        if event.get("error") or (event.get("code") and event.get("message")):
            errors.append(api_message(json.dumps(event)))
        for key in ("error_message", "errorMessage"):
            if event.get(key):
                errors.append(f"{event.get('error_code') or event.get('errorCode') or ''} {event[key]}".strip())
        meta = event.get("usage_metadata") or event.get("usageMetadata")
        if isinstance(meta, dict) and not event.get("partial"):
            _usage(usage, meta)
        content = event.get("content") or {}
        texts = []
        for part in content.get("parts") or []:
            call = _part(part, "function_call", "functionCall")
            result = _part(part, "function_response", "functionResponse")
            if call:
                calls.append({"name": call.get("name"), "args": call.get("args") or {}})
            elif result:
                results.append({"name": result.get("name"), "response": result.get("response")})
            elif isinstance(part.get("text"), str) and not part.get("thought") \
                    and content.get("role", "model") == "model":
                texts.append(part["text"])
        if texts and not event.get("partial"):
            answer = "".join(texts)
    return {"answer": answer, "tool_calls": calls, "tool_results": results, "errors": errors, "usage": usage}


def read_a2a(reply: dict) -> dict:
    """The Cloud Run peer's message/send reply in read_turn's shape: smoke_agent's text, the tool calls and results
    its history carries as data parts (ADK's A2A converter marks them adk_type), and the model's usage where the
    converter put it in a message's metadata (adk_usage_metadata, counted once per adk_event_id)."""
    raw = reply.get("reply")
    calls, results, errors, seen = [], [], [], {}
    usage = {"calls": 0, "in": 0, "out": 0, "thinking": 0, "cached": 0}
    stack = [raw]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            meta = item.get("metadata") if isinstance(item.get("metadata"), dict) else {}
            data = item.get("data") if isinstance(item.get("data"), dict) else None
            if item.get("kind") == "data" and data is not None:
                if meta.get("adk_type") == "function_call":
                    calls.append({"name": data.get("name"), "args": data.get("args") or {}})
                elif meta.get("adk_type") == "function_response":
                    results.append({"name": data.get("name"), "response": data.get("response")})
            used = meta.get("adk_usage_metadata")
            if isinstance(used, dict):
                seen[str(meta.get("adk_event_id") or json.dumps(used, sort_keys=True))] = used
            stack.extend(item.values())
        elif isinstance(item, list):
            stack.extend(item)
    for meta in seen.values():
        _usage(usage, meta)
    if isinstance(raw, dict) and raw.get("error"):
        errors.append(api_message(json.dumps(raw)))
    elif not isinstance(raw, dict):
        errors.append(trim(raw, 300))
    return {"answer": reply.get("text") or "", "tool_calls": list(reversed(calls)),
            "tool_results": list(reversed(results)), "errors": errors, "usage": usage}


def refused_by_roster(turn: dict) -> bool:
    """documind-mcp's own refusal in a tool's result (`... is not on tenant 'zeta''s roster`); from a reply that shows
    no tool results, the refusal relayed in the answer, as make smoke-agent's check 4 reads it."""
    said = json.dumps([r.get("response") for r in turn["tool_results"]], ensure_ascii=False).lower()
    if "roster" in said:
        return True
    return not turn["tool_results"] and any(w in turn["answer"].lower() for w in REFUSAL_WORDS)


def answered(turn: dict, question: str) -> bool | None:
    """Whether the answer holds make smoke-agent's expected value; None for a question that has no expectation."""
    try:
        expected = smoke_agent.expected_answer_pattern(question)
    except ValueError:
        return None
    return bool(expected.search(re.sub(r"[*_`]", "", turn["answer"])))


def model_inr(usage: dict, model: str) -> float | None:
    """The peer's own model calls at list price (shared/prices.py); thinking tokens bill as output."""
    if not usage.get("calls"):
        return None
    return round(prices.inr(prices.usd(model, usage["in"], usage["out"] + usage["thinking"], usage["cached"])), 4)


def turn_fact(turn: dict) -> FactRefused | None:
    """A failed managed turn whose own words contradict a fact: no ID token in the runtime (5), a token documind-mcp
    would not take (5), documind-mcp's door refusing the runtime's account (2), the model looked up in the region
    (6)."""
    results = [json.dumps(r.get("response"), ensure_ascii=False) for r in turn["tool_results"]]
    said = " ".join(turn["errors"] + results + [turn["answer"]])
    if re.search(r"(?i)metadata server|fetch_id_token|DefaultCredentialsError|Failed to retrieve http://metadata",
                 said):
        return FactRefused("5", said, "the runtime minted no ID token for documind-mcp, so the peer cannot reach the "
                           "lane from this host: agent.py's _mcp_headers asks the metadata server, as on Cloud Run")
    if "not authenticated" in said:
        return FactRefused("5", said, "a token was minted, but documind-mcp did not take it (its audience or issuer)")
    if re.search(r"403|PERMISSION_DENIED", said) and re.search(r"(?i)aiplatform\.sessions|/sessions\b", said):
        return FactRefused("2", said, "the runtime's account may not keep the instance's managed sessions, which each "
                           "question opens: documind-agent-sa holds roles/aiplatform.user (terraform/sa.tf)")
    if re.search(r"403|Forbidden|PERMISSION_DENIED", said) and re.search(r"(?i)\bmcp\b|run\.app", said):
        return FactRefused("2", said, "Cloud Run refused the runtime's account at documind-mcp's door: it is not "
                           "running as documind-agent-sa, which commands/lesson-7.2.sh lets invoke documind-mcp")
    if re.search(r"(?i)publisher model|publishers/google/models", said) and "NOT_FOUND" in said.upper():
        return FactRefused("6", said, "the model was looked up in the instance's region, not on global: the "
                           "GlobalGemini pin did not take (commands/managed_peer_agent.py)")
    return None


def deploy_fact(text: str, region: str, sa: str) -> FactRefused | None:
    """A refused deploy whose own words contradict a fact; None for one that settles none."""
    hint = grant_hint(text, sa)
    if hint or (re.search(r"(?i)service ?account", text) and re.search(r"PERMISSION_DENIED|403|denied", text)):
        return FactRefused("2", text, f"the platform may not run the runtime as {sa}",
                           hint or "the refusal names no iam.serviceAccounts permission: read it beside the author's "
                                   "capture of fact 2")
    if re.search(r"(?i)min_?instances|max_?instances", text):
        return FactRefused("3", text, "the platform refused the instance bounds (min_instances 0, max_instances 1)",
                           "the author's dated capture says which bounds the platform takes")
    if re.search(r"(?i)(location|region)\b[^.]{0,80}\b(not supported|unsupported|not available|is not enabled)", text) \
            or re.search(rf"(?i)not supported in {re.escape(region)}", text):
        return FactRefused("1", text, f"Agent Engine refused the region {region}",
                           "make managed-peer-down, then make managed-peer-up MANAGED_PEER_REGION=us-central1")
    if re.search(r"(?i)ResolutionImpossible|No matching distribution|Could not find a version|pip install|"
                 r"dependency conflict|requirements\.txt|\bbuild(ing)? (failed|error)|failed to build", text):
        return FactRefused("11", text, "the runtime's image did not build: google-cloud-aiplatform beside the peer's "
                           "pins is fact 11",
                           "AIPLATFORM_PIN=<the version fact 11 recorded> pins it in the venv and the image")
    return None


# ------------------------------------------------------------------------------------------- the runs

class Ctx:
    def __init__(self, args, seam: Seam, say, *, sleep, records: Path):
        self.args, self.seam, self.say, self.sleep, self.records = args, seam, say, sleep, records
        self.p = args.project
        self._number = args.project_number or ""
        self.known: str | None = None       # the instance once found or made in this run, so it is looked up once

    # the lane ------------------------------------------------------------------------------------------------
    def number(self) -> str:
        if not self._number:
            got = self.seam.call(f"GET https://cloudresourcemanager.googleapis.com/v1/projects/{self.p}  # its number",
                                 "project_number", stub="NUMBER")
            if not got:
                raise Stop("the project's number could not be read")
            self._number = str(got)
        return self._number

    def mcp_url(self) -> str:
        return f"https://documind-mcp-{self.number()}.{self.args.services_region}.run.app"

    def cloud_run_url(self) -> str:
        return f"https://documind-agent-{self.number()}.{self.args.services_region}.run.app"

    def service_agent(self) -> str:
        return "serviceAccount:" + SERVICE_AGENT.format(number=self.number())

    def asker(self, account: str | None = None) -> str | None:
        account = self.args.as_account if account is None else account
        return None if account in ("me", "") else sa_email(account, self.p)

    # local state ---------------------------------------------------------------------------------------------
    @property
    def state_file(self) -> Path:
        return self.records / "state.json"

    def state(self) -> dict:
        try:
            got = json.loads(self.state_file.read_text(encoding="utf-8"))
            return got if isinstance(got, dict) else {}
        except (OSError, ValueError):
            return {}

    def save(self, state: dict) -> None:
        if self.seam.dry_run:
            return
        self.records.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(state, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")

    def forget(self) -> None:
        if not self.seam.dry_run and self.state_file.exists():
            self.state_file.unlink()

    def keep(self, record: dict) -> dict:
        if not self.seam.dry_run:
            self.records.mkdir(parents=True, exist_ok=True)
            with (self.records / "runs.ndjson").open("a", encoding="utf-8", newline="\n") as f:
                f.write(json.dumps(record, sort_keys=True) + "\n")
        return record

    def history(self) -> list:
        try:
            lines = (self.records / "runs.ndjson").read_text(encoding="utf-8").splitlines()
        except OSError:
            return []
        out = []
        for line in lines:
            try:
                rec = json.loads(line)
            except ValueError:
                continue
            if isinstance(rec, dict) and rec.get("kind") == RECORD_KIND:
                out.append(rec)
        return out

    # the instance --------------------------------------------------------------------------------------------
    def exists(self, name: str) -> bool:
        try:
            self.seam.call(f"GET {endpoint(region_of(name))}/v1/{name}", "get_instance", name, stub={})
            return True
        except Refused as error:
            if error.status == 404:
                return False
            raise

    def ours(self, region: str) -> list:
        url = f"{endpoint(region)}/v1/projects/{self.p}/locations/{region}/reasoningEngines"
        engines = self.seam.call(f"GET {url}  # any {DISPLAY_NAME}*", "list_instances", region, stub=[]) or []
        return [e.get("name", "") for e in engines if str(e.get("displayName", "")).startswith(DISPLAY_NAME)]

    def instance(self) -> str | None:
        """This command's instance: the state's while it exists, else one found by its display name."""
        if self.known:
            return self.known
        state = self.state()
        if state.get("name"):
            if state.get("region") != self.args.region:
                raise Stop(f"the managed peer is in {state.get('region')} ({state['name']}): run with "
                           f"MANAGED_PEER_REGION={state.get('region')}, or make managed-peer-down first")
            if self.exists(state["name"]):
                self.known = state["name"]
                return self.known
            state = {k: v for k, v in state.items() if k not in INSTANCE_KEYS}    # gone: a recorded grant stays
            self.save(state)
        found = self.ours(self.args.region)
        if found:
            self.save({**state, "name": found[0], "region": self.args.region})
            self.known = found[0]
        return self.known

    def require(self) -> str:
        name = self.instance()
        if name:
            return name
        if self.seam.dry_run:
            self.known = f"projects/NUMBER/locations/{self.args.region}/reasoningEngines/ENGINE_ID"
            return self.known
        raise Stop(f"no managed peer in {self.args.region}: make managed-peer-up first")


def show(ctx: Ctx, record: dict, lines: list[str]) -> None:
    """The run's record kept, and printed: as JSON with --json, else as lines."""
    ctx.keep(record)
    if ctx.args.json:
        ctx.say(json.dumps(record, sort_keys=True))
    else:
        for line in lines:
            ctx.say(line)


# ------------------------------------------------------------------------------------------------ up

def cmd_up(ctx: Ctx) -> int:
    up(ctx)
    return 0


def up(ctx: Ctx) -> str:
    a, seam = ctx.args, ctx.seam
    sa = sa_email(AGENT_SA, ctx.p)
    model = cloud_run_settings()["model"]
    ctx.say(f"== up: the A2A peer on Agent Engine in {a.region}, as {sa} ==")
    name = ctx.instance()
    state = ctx.state()
    if name and state.get("deployed_at") and not getattr(a, "redeploy", False):
        ctx.say(f"  deployed already, at {state['deployed_at']}: {name} (--redeploy deploys the peer into it again)")
        return name
    if name:
        ctx.say(f"  the instance exists: {name} - deploying the peer into it")
    else:
        name = seam.call(f"vertexai.Client(project={ctx.p!r}, location={a.region!r}).agent_engines.create("
                         f"config={{'display_name': {DISPLAY_NAME!r}}})", "create_instance", a.region, DISPLAY_NAME,
                         stub=f"projects/NUMBER/locations/{a.region}/reasoningEngines/ENGINE_ID")
        state.update(name=name, region=a.region, created_at=utc_now())
        ctx.save(state)                     # recorded before anything else can fail, so down finds it
        ctx.known = name
        if not seam.dry_run:
            ctx.say(f"  created {name}")
    # the grant first: the runtime is built and run as documind-agent-sa
    member, role = ctx.service_agent(), a.grant_role
    policy = seam.call(f"POST https://iam.googleapis.com/v1/projects/{ctx.p}/serviceAccounts/{sa}:getIamPolicy",
                       "sa_policy", sa, stub={}) or {}
    if (role, member) in bindings(policy):
        ctx.say(f"  grant: {member} already holds {role} on {sa}"
                + ("" if state.get("grant") else " (not added here, so down leaves it)"))
    else:
        seam.call(f"POST https://iam.googleapis.com/v1/projects/{ctx.p}/serviceAccounts/{sa}:setIamPolicy  # adds "
                  f"{role} for {member}", "set_sa_policy", sa, with_binding(policy, role, member), stub={})
        state["grant"] = {"role": role, "member": member, "on": sa}
        ctx.save(state)
        ctx.say(f"  grant: {role} on {sa} for Agent Engine's service agent (down takes it back)")
    staging = Path(tempfile.mkdtemp(prefix="managed-peer-"))
    started = time.monotonic()
    try:
        staged = stage(staging, ctx.p, ctx.mcp_url(), model, a.aiplatform_pin)
        ctx.say(f"  stage: {APP_NAME}/agent.py and requirements.txt (services/agent/, byte for byte) and "
                f"{APP_NAME}/__init__.py (commands/managed_peer_agent.py); beside them .agent_engine_config.json "
                f"{json.dumps(staged['config'])} and .env {json.dumps(staged['env'])}")
        try:
            seam.call(f"google.adk.cli.cli_deploy.to_agent_engine(agent_folder='<staged>/{APP_NAME}', project="
                      f"{ctx.p!r}, region={a.region!r}, agent_engine_id={name!r}, display_name={DISPLAY_NAME!r}, "
                      f"otel_to_cloud=True, env_file='<staged>/.env', agent_engine_config_file='<staged>/"
                      f".agent_engine_config.json', adk_version={adk_pin()!r})  # = adk deploy agent_engine, which "
                      f"ends in agent_engines.update(name=..., config=...)", "deploy", name, staged["folder"],
                      staged["env_file"], staged["config_file"], DISPLAY_NAME, adk_pin())
        except (KeyboardInterrupt, SystemExit, Stop, FactRefused):
            raise
        except Exception as error:
            ctx.say(f"  the instance is kept, undeployed: make managed-peer-down deletes it ({name})")
            fact = deploy_fact(str(error), a.region, sa)
            if fact:
                raise fact from error
            raise Stop(f"the deploy stopped: {trim(error, 500)}") from error
    finally:
        shutil.rmtree(staging, ignore_errors=True)
    deploy_s = time.monotonic() - started
    try:
        inst = seam.call(f"GET {endpoint(a.region)}/v1/{name}  # what the platform kept", "get_instance", name,
                         stub={}) or {}
    except Refused as error:
        ctx.say(f"  read back refused: {error}")
        inst = {}
    view = deployment_view(inst)
    if view.get("serviceAccount") and view["serviceAccount"] != sa:
        raise FactRefused("2", json.dumps(view), f"the platform kept {view['serviceAccount']} as the runtime's "
                          f"account, not {sa}", "make managed-peer-down, and read the author's capture of fact 2")
    low = view.get("minInstances")
    low = low if low is not None else "absent (proto3 JSON leaves out a zero: 0 and unset read alike)"
    may = may_query(ctx)
    state = {k: v for k, v in ctx.state().items() if k not in ("last_ask", "last_ask_at")}   # idle from the deploy
    state.update(name=name, region=a.region, asks=0)
    if not seam.dry_run:
        state["deployed_at"] = utc_now()
    ctx.save(state)
    record = {"kind": RECORD_KIND, "command": "up", "host": "agent_engine", "at": utc_now(), "region": a.region,
              "deploy_s": None if seam.dry_run else round(deploy_s, 1),
              "settings": {"min_instances": MIN_INSTANCES, "max_instances": MAX_INSTANCES,
                           "max_llm_calls": PEER_MAX_LLM_CALLS, "model": model, "adk": adk_pin(),
                           "aiplatform": a.aiplatform_pin or "unpinned (fact 11)"},
              "read_back": {k: view[k] for k in ("minInstances", "maxInstances") if k in view},
              "identity": {"runtime": short(view.get("serviceAccount") or sa), "may_query": may}}
    show(ctx, record, [
        "  dry run: nothing deployed, nothing read back" if seam.dry_run else
        f"  deployed in {deploy_s:.0f} s: {name}\n  read back: serviceAccount "
        f"{view.get('serviceAccount', 'absent')}; minInstances {low}; maxInstances "
        f"{view.get('maxInstances', 'absent')}; env {', '.join(view.get('env', [])) or 'absent'}",
        "",
        "STANDING COST: this instance exists until make managed-peer-down. Agent Engine's price is not stated here "
        "(fact 12, the author's dated read of the pricing page); min_instances 0 is asked for (fact 3), and whether "
        "an idle instance bills is fact 4. Torn down by default: make managed-peer-down when you are done.",
        f"WHO MAY CALL IT: every account holding roles/aiplatform.user (or owner, or editor) on the project, unless "
        f"the instance has an IAM policy of its own (fact 8) - {', '.join(may) or 'the policy was not read'} - and it "
        f"answers each of them as {AGENT_SA}, on {PEER_TENANT}'s roster. The Cloud Run peer admits "
        f"{', '.join(cloud_run_settings()['invokers'])} (commands/lesson-8.4.sh)."])
    return name


def may_query(ctx: Ctx) -> list[str]:
    """The project's holders of a role that carries aiplatform.reasoningEngines.query: service accounts by id, people
    counted. Empty when the policy cannot be read."""
    try:
        policy = ctx.seam.call(f"POST https://cloudresourcemanager.googleapis.com/v1/projects/{ctx.p}:getIamPolicy  "
                               f"# who holds {', '.join(QUERY_ROLES)}", "project_policy", stub={}) or {}
    except Refused as error:
        ctx.say(f"  the project's IAM policy was not read: {error}")
        return []
    accounts, people = set(), set()
    for role, member in bindings(policy):
        if role in QUERY_ROLES:
            kind, _, who = member.partition(":")
            if kind == "serviceAccount":
                accounts.add(short(who))
            else:
                people.add(member)
    return sorted(accounts) + ([f"{len(people)} person(s) or group(s)"] if people else [])


# ----------------------------------------------------------------------------------------------- ask

def question_for(tenant: str, question: str) -> str:
    return question if tenant == PEER_TENANT else OTHER_TENANT.format(tenant=tenant, question=question)


def ask(ctx: Ctx, *, host: str, tenant: str, question: str, account: str | None, label: str = "") -> dict:
    """One question to one host: its record, its turn and the text sent. Raises Refused when the host refused the
    asker, Stop when no token could be minted as it."""
    a, seam = ctx.args, ctx.seam
    text = question_for(tenant, question)
    asker = ctx.asker(account)
    who = short(asker) if asker else "you"
    run = cloud_run_settings()
    if host == "cloud_run":
        url = ctx.cloud_run_url()
        part = json.dumps({"kind": "text", "text": text})
        reply = seam.call(f"POST {url}/ message/send {{\"parts\": [{part}]}}  # make smoke-agent's request, with an "
                          f"ID token minted as {who}", "a2a_send", url, text, asker,
                          stub={"status": None, "reply": {}, "text": "", "first_event_s": None, "total_s": None}) or {}
        if reply.get("status") not in (None, 200):
            body = reply.get("reply")
            raise Refused(reply["status"], body if isinstance(body, str) else json.dumps(body))
        turn = read_a2a(reply)
        region = a.services_region
        before = [r for r in ctx.history() if r.get("host") == "cloud_run" and r.get("command") == "ask"]
        cold = {"first_after_deploy": None, "idle_s": idle_since(before[-1]["at"]) if before else None}
        door = f"roles/run.invoker on documind-agent: {', '.join(run['invokers'])} (commands/lesson-8.4.sh)"
        hosting = {k: run[k] for k in ("min_instances", "max_instances", "concurrency", "timeout_s", "memory", "cpu")}
        hosting["price"] = "Cloud Run's, billed by request time like the lane's other services"
        runtime = run["account"]
    else:
        name = ctx.require()
        state = ctx.state()
        user = who if asker else "operator"
        reply = seam.call(f"POST {endpoint(region_of(name))}/v1/{name}:streamQuery?alt=sse {{\"class_method\": "
                          f"\"async_stream_query\", \"input\": {{\"user_id\": {json.dumps(user)}, \"message\": "
                          f"{json.dumps(text)}}}}}  # as {who}", "query", name, text, user, asker,
                          stub={"status": None, "events": [], "first_event_s": None, "total_s": None}) or {}
        turn = read_turn(reply.get("events"))
        region = region_of(name) or a.region
        since = state.get("last_ask_at") or state.get("deployed_at")
        cold = {"first_after_deploy": (state.get("asks", 0) == 0) if state.get("deployed_at") else None,
                "idle_s": idle_since(since) if since else None}
        door = ("aiplatform.reasoningEngines.query: any roles/aiplatform.user holder, unless the instance has an "
                "IAM policy (fact 8)")
        hosting = {"min_instances": MIN_INSTANCES, "max_instances": MAX_INSTANCES, "concurrency": None,
                   "price": "not stated here: fact 12, the author's dated read of the pricing page"}
        runtime = AGENT_SA
        if not seam.dry_run:
            ended = utc_now()
            ctx.save({**state, "asks": state.get("asks", 0) + 1, "last_ask_at": ended,
                      "last_ask": {"start": shift(ended, -(reply.get("total_s") or 0) - 1), "end": ended,
                                   "question": text}})
    ok = answered(turn, question) if tenant == PEER_TENANT else None
    record = {"kind": RECORD_KIND, "command": "ask", "host": host, "at": utc_now(), "region": region,
              "label": label or None,
              "question": (PEER_TENANT if tenant == PEER_TENANT else tenant) if question == QUESTION else "custom",
              "answered": ok, "refused_by_roster": refused_by_roster(turn) if tenant != PEER_TENANT else False,
              "latency_s": {"first_event": rnd(reply.get("first_event_s")), "total": rnd(reply.get("total_s"))},
              "cold": cold, "tool_calls": [c.get("name") for c in turn["tool_calls"]],
              "model": {"name": run["model"], **turn["usage"], "inr": model_inr(turn["usage"], run["model"])},
              "identity": {"runtime": runtime, "caller": who, "door": door}, "hosting": hosting,
              "errors": [trim(e, 200) for e in turn["errors"]][:3]}
    return {"record": record, "turn": turn, "text": text}


def turn_lines(got: dict) -> list[str]:
    rec, turn = got["record"], got["turn"]
    lat, model, cold = rec["latency_s"], rec["model"], rec["cold"]
    lines = [f"  question: {got['text']}"]
    for i, call in enumerate(turn["tool_calls"]):
        lines.append(f"  tool call: {call['name']}({json.dumps(call['args'], ensure_ascii=False)})")
        if i < len(turn["tool_results"]):
            result = json.dumps(turn["tool_results"][i].get("response"), ensure_ascii=False)
            lines.append(f"    result: {trim(result, 200)}")
    for error in turn["errors"]:
        lines.append(f"  error: {trim(error, 300)}")
    lines.append(f"  answer: {trim(turn['answer'], 600) or '(none)'}")
    if rec["question"] == PEER_TENANT:
        verdict = {True: "the expected answer", False: "NOT the expected answer",
                   None: "no expectation"}[rec["answered"]]
    elif rec["question"] == "custom":
        verdict = "refused by the roster" if rec["refused_by_roster"] else "no refusal seen"
    else:
        verdict = "refused by the roster" if rec["refused_by_roster"] else "NOT refused by the roster"
    timing = (f"first event after {lat['first_event']} s, " if lat["first_event"] is not None else "") + \
        (f"done in {lat['total']} s" if lat["total"] is not None else "not timed")
    cost = (f"{model['calls']} model call(s), {model['in']} in / {model['out']} out / {model['thinking']} thinking "
            f"tokens, Rs {model['inr']}" if model["calls"] else "the reply carries no model usage")
    lines.append(f"  {rec['host']} in {rec['region']}: {verdict}; {timing}; {cost}")
    lines.append(f"  first call after the deploy: {cold['first_after_deploy']}; idle before it: {cold['idle_s']} s")
    return lines


def cmd_ask(ctx: Ctx) -> int:
    a = ctx.args
    host = "cloud_run" if a.host == "cloudrun" else "agent_engine"
    title = "Cloud Run" if host == "cloud_run" else "managed"
    ctx.say(f"== ask: the {title} peer, as tenant {a.tenant}'s question ==")
    question = a.question or QUESTION
    try:
        got = ask(ctx, host=host, tenant=a.tenant, question=question, account=None)
    except Refused as error:
        if error.status == 403 and host == "agent_engine":
            raise FactRefused("8", error.body, f"{short(ctx.asker())} may not query the instance",
                              "the author's capture of fact 8 says which principals an instance admits") from error
        raise Stop(f"the {title} peer refused the question: {error}") from error
    except OSError as error:
        raise Stop(f"the {title} peer did not answer: {error}") from error
    rec = got["record"]
    if ctx.seam.dry_run:
        show(ctx, rec, [f"  question: {got['text']}", "  dry run: nothing was asked"])
        return 0
    if host == "agent_engine" and a.tenant == PEER_TENANT and rec["answered"] is False:
        fact = turn_fact(got["turn"])
        if fact:
            ctx.keep(rec)
            for line in turn_lines(got):
                ctx.say(line)
            raise fact
    show(ctx, rec, turn_lines(got))
    if a.tenant == PEER_TENANT:
        return 1 if rec["answered"] is False else 0
    return 0 if rec["refused_by_roster"] or question != QUESTION else 1


# ---------------------------------------------------------------------------------------------- trace

MCP_ROWS = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-mcp" AND '
            'jsonPayload.event="mcp_call"')
RUNTIME_ROWS = ('resource.type="aiplatform.googleapis.com/ReasoningEngine" AND '
                'resource.labels.reasoning_engine_id="{id}" AND '
                '(jsonPayload.event="managed_peer_up" OR textPayload:"managed_peer_up")')


def ours(spans) -> list:
    """The spans of every trace that holds the peer's own agent span (ADK names it invoke_agent documind_peer)."""
    traces = {s.get("trace") for s in spans or [] if "documind_peer" in s.get("name", "")}
    return [s for s in spans or [] if s.get("trace") in traces]


def content_in(spans, question: str) -> list[str]:
    """The span labels that carry the question's own words: message content in the trace."""
    probe = " ".join(question.lower().split())[:40]
    if len(probe) < 12:
        return []
    return sorted({f"{s['name']}: {k}" for s in spans for k, v in (s.get("labels") or {}).items()
                   if probe in " ".join(str(v).lower().split())})


def read_trace(ctx: Ctx, start: str, end: str, wait: int) -> list:
    """Our spans in the window, polled every 20 s for up to wait seconds: Cloud Trace takes a while to show them."""
    url = f"https://cloudtrace.googleapis.com/v1/projects/{ctx.p}/traces"
    waited = 0
    while True:
        spans = ctx.seam.call(f"GET {url}?view=COMPLETE&startTime={start}&endTime={end}  # polled every 20 s for up "
                              f"to {wait} s", "trace_spans", start, end, stub=[], quiet=waited > 0) or []
        found = ours(spans)
        if found or ctx.seam.dry_run or waited >= wait:
            return found
        ctx.sleep(20)
        waited += 20


def read_callers(ctx: Ctx, start: str, end: str, wait: int) -> list:
    """documind-mcp's mcp_call rows in the window (a refused call writes none: the roster refuses before the row)."""
    flt = f'{MCP_ROWS} AND timestamp>="{start}" AND timestamp<="{end}"'
    waited = 0
    while True:
        rows = ctx.seam.call(f"POST https://logging.googleapis.com/v2/entries:list {{\"filter\": {json.dumps(flt)}}}"
                             f"  # documind-mcp's rows", "log_entries", flt, 50, stub=[], quiet=waited > 0) or []
        if rows or ctx.seam.dry_run or waited >= wait:
            return [r.get("jsonPayload") or {} for r in rows]
        ctx.sleep(15)
        waited += 15


def runtime_line(ctx: Ctx, name: str) -> dict:
    """The line commands/managed_peer_agent.py logs at import, from the runtime's own log."""
    flt = RUNTIME_ROWS.format(id=engine_id(name))
    rows = ctx.seam.call(f"POST https://logging.googleapis.com/v2/entries:list {{\"filter\": {json.dumps(flt)}}}"
                         f"  # the runtime's own line", "log_entries", flt, 5, stub=[]) or []
    for row in rows:
        payload = row.get("jsonPayload")
        if isinstance(payload, dict) and payload.get("event") == "managed_peer_up":
            return payload
        text = str(row.get("textPayload") or "")
        if "managed_peer_up" in text and "{" in text:
            try:
                return json.loads(text[text.index("{"):])
            except ValueError:
                continue
    return {}


def cmd_trace(ctx: Ctx) -> int:
    a = ctx.args
    ctx.say("== trace: what the managed peer's last ask left behind ==")
    state = ctx.state()
    last = state.get("last_ask") or {}
    tight = bool(last.get("start")) and not a.since
    if tight:
        start, end, question = shift(last["start"], -120), shift(last["end"], 300), last.get("question", "")
        rows_from, rows_to = shift(last["start"], -10), shift(last["end"], 10)
    else:
        now = utc_now()
        start, end, question = shift(now, -60 * (a.since or 30)), shift(now, 60), ""
        rows_from, rows_to = start, end
    spans = read_trace(ctx, start, end, a.wait)
    names = []
    for span in spans:
        if not names or names[-1] != span["name"]:
            names.append(span["name"])
    lines = [f"  window {start} .. {end} " + ("(the last ask's)" if tight else f"(the last {a.since or 30} minutes)")]
    if spans:
        keys = sorted({k for s in spans for k in (s.get("labels") or {})})
        lines.append(f"  {len(spans)} span(s) in {len({s['trace'] for s in spans})} trace(s): {', '.join(names)}")
        lines.append(f"  label keys: {', '.join(keys)}")
    else:
        lines.append(f"  no trace naming documind_peer in Cloud Trace after {a.wait} s: spans can take minutes to "
                     f"show; run make managed-peer-trace again (fact 7)")
    hits = content_in(spans, question) if question else []
    callers = read_callers(ctx, rows_from, rows_to, min(a.wait, 30))
    seen = sorted({short(c.get("caller")) for c in callers if c.get("caller")})
    for row in callers[:10]:
        lines.append(f"  documind-mcp row: tool {row.get('tool')}, tenant {row.get('tenant')}, "
                     f"caller {row.get('caller')}")
    if not callers:
        lines.append("  no documind-mcp row in the window (a refused call writes none: the roster refuses first)")
    runtime = runtime_line(ctx, state["name"]) if state.get("name") else {}
    if runtime:
        lines.append(f"  the runtime's own line: GOOGLE_CLOUD_LOCATION={runtime.get('GOOGLE_CLOUD_LOCATION')}, "
                     f"model {runtime.get('model')} on {runtime.get('model_location')}, ADK_MAX_LLM_CALLS="
                     f"{runtime.get('ADK_MAX_LLM_CALLS')}, versions "
                     f"{json.dumps(runtime.get('versions'), sort_keys=True)}")
    elif state.get("name"):
        lines.append("  the runtime's own line was not found (its log's resource type is unverified until a lane run)")
    record = {"kind": RECORD_KIND, "command": "trace", "host": "agent_engine", "at": utc_now(), "region": a.region,
              "spans": len(spans), "span_names": names, "content_in_spans": bool(hits), "mcp_callers": seen,
              "runtime": {k: runtime.get(k) for k in ("GOOGLE_CLOUD_LOCATION", "model_location",
                                                       "ADK_MAX_LLM_CALLS", "versions")} if runtime else None}
    if hits:
        ctx.keep(record)
        raise FactRefused("7", "; ".join(hits), "the question's own words are in the spans: message content was "
                          "captured", "the deploy asks for telemetry, which sets ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS="
                          "false: read the runtime's env in make managed-peer-up's read back")
    strangers = [c for c in seen if c != AGENT_SA]
    if strangers and tight:
        ctx.keep(record)
        raise FactRefused("2", ", ".join(strangers), f"during the last ask documind-mcp was called as "
                          f"{', '.join(strangers)}, not only as {AGENT_SA}",
                          "if something else called documind-mcp at that moment, ask again and trace again")
    checked = "none of the question" if spans and question else "not checked"
    lines.append(f"  message content in the spans: {checked}; documind-mcp's callers: "
                 f"{', '.join(seen) or 'none in the window'}")
    show(ctx, record, lines)
    return 0


# ------------------------------------------------------------------------------------------- sessions

def cmd_sessions(ctx: Ctx) -> int:
    ctx.say("== sessions: the managed peer's sessions, and who may read one ==")
    found = sessions(ctx, ctx.require())
    show(ctx, found["record"], found["lines"])
    return 0


def sessions(ctx: Ctx, name: str, owner: str | None = None) -> dict:
    seam, eid, region = ctx.seam, engine_id(name), region_of(name) or ctx.args.region
    svc = f"VertexAiSessionService(project={ctx.p!r}, location={region!r}, agent_engine_id={eid!r})"
    listed = seam.call(f"{svc}.list_sessions(app_name={eid!r})  # every user's", "list_sessions", name, stub=[]) or []
    users: dict[str, int] = {}
    for s in listed:
        users[s["user_id"]] = users.get(s["user_id"], 0) + 1
    lines = [f"  {len(listed)} session(s) on the instance: " + (", ".join(f"{u} {n}" for u, n in sorted(users.items()))
                                                                 or "none yet (each ask writes one)")]
    record = {"kind": RECORD_KIND, "command": "sessions", "host": "agent_engine", "at": utc_now(), "region": region,
              "sessions": len(listed), "users": sorted(users), "other_user_refused": None, "raw_read_names_user": None}
    mine = [s for s in listed if not owner or s["user_id"] == owner]
    if mine:
        newest = max(mine, key=lambda s: s.get("updated") or 0)
        sid, user = newest["id"], newest["user_id"]
        got = seam.call(f"{svc}.get_session(app_name={eid!r}, user_id={user!r}, session_id={sid!r})", "session_as",
                        name, sid, user, stub={"events": []}) or {}
        lines.append(f"  {user}'s newest session, {sid}, event by event:")
        lines += [f"    {line}" for line in (got.get("events") or [])[:12]]
        try:
            other = seam.call(f"{svc}.get_session(app_name={eid!r}, user_id={OTHER_USER!r}, session_id={sid!r})  # as "
                              f"another user", "session_as", name, sid, OTHER_USER, stub=None)
            if not seam.dry_run:
                record["other_user_refused"] = False
                lines.append(f"  as {OTHER_USER}: ADK's session service RETURNED it "
                             f"({'not found' if other is None else trim(json.dumps(other), 120)})")
        except ValueError as error:
            record["other_user_refused"] = True
            lines.append(f"  as {OTHER_USER}: refused by ADK's session service - {error} - a check in this client, "
                         f"made after the read (fact 9)")
        try:
            raw = seam.call(f"vertexai.Client(project={ctx.p!r}, location={region!r}).aio.agent_engines.sessions.get("
                            f"name='reasoningEngines/{eid}/sessions/{sid}')  # ADK's own read, naming no user",
                            "raw_session", name, sid, stub={}) or {}
            if not seam.dry_run:
                seen = pick(raw, "user_id", "userId")
                record["raw_read_names_user"] = bool(seen)
                lines.append(f"  the API's own read, which names no user, returned it (user_id {seen!r}): what keeps "
                             f"one user from another's session is IAM on the instance and ADK's check, not the API")
        except Refused as error:
            lines.append(f"  the API's own read was refused: {error}")
    if getattr(ctx.args, "delete", False):
        for s in listed:
            seam.call(f"{svc}.delete_session(app_name={eid!r}, user_id={s['user_id']!r}, session_id={s['id']!r})",
                      "delete_session", name, s["id"], s["user_id"])
        lines.append(f"  deleted {len(listed)} session(s)")
    return {"record": record, "lines": lines}


# ----------------------------------------------------------------------------------------------- down

def cmd_down(ctx: Ctx) -> int:
    return 4 if down(ctx) else 0


def down(ctx: Ctx, also: tuple = ()) -> list:
    """Delete this command's instances by name and take the grant back, each step on its own. Returns what is left."""
    seam, state = ctx.seam, ctx.state()
    regions = list(dict.fromkeys(r for r in (state.get("region"), ctx.args.region) if r))
    ctx.say(f"== down: every {DISPLAY_NAME}* instance in {', '.join(regions)}, and the grant ==")
    targets = [state["name"]] if state.get("name") else []
    targets += [n for n in also if n]
    for region in regions:
        try:
            targets += ctx.ours(region)
        except Refused as error:
            ctx.say(f"  could not list {region}: {error}")
    deleted, gone, left = [], [], []
    for name in dict.fromkeys(targets):
        try:
            seam.call(f"vertexai.Client(project={ctx.p!r}, location={region_of(name)!r}).agent_engines.delete(name="
                      f"{name!r}, force=True)  # its sessions go with it", "delete_instance", name)
        except Refused as error:
            (gone.append(name) if error.status == 404 else left.append((name, f"the delete was refused: {error}")))
            continue
        if seam.dry_run or read_back_gone(ctx, name):
            deleted.append(name)
        else:
            left.append((name, "deleted, but still readable after 60 s"))
    grant = state.get("grant")
    grant_line = ("  grant: dry run, no grant recorded (a dry run records nothing); nothing to take back"
                  if seam.dry_run else "  grant: none recorded as added by make managed-peer-up; nothing to take back")
    if grant:
        try:
            policy = seam.call(f"POST https://iam.googleapis.com/v1/projects/{ctx.p}/serviceAccounts/{grant['on']}"
                               ":getIamPolicy", "sa_policy", grant["on"], stub={}) or {}
            if (grant["role"], grant["member"]) in bindings(policy) or seam.dry_run:
                seam.call(f"POST https://iam.googleapis.com/v1/projects/{ctx.p}/serviceAccounts/{grant['on']}"
                          f":setIamPolicy  # removes {grant['role']} for {grant['member']}", "set_sa_policy",
                          grant["on"], without_binding(policy, grant["role"], grant["member"]), stub={})
                grant_line = (f"  grant {'would be ' if seam.dry_run else ''}taken back: {grant['role']} on "
                              f"{grant['on']} for {grant['member']} (up added it)")
            else:
                grant_line = f"  grant: {grant['role']} for {grant['member']} was already gone"
            state.pop("grant")
        except Refused as error:
            left.append((grant["on"], f"the grant could not be taken back: {error}"))
            grant_line = f"  grant NOT taken back: {error}"
    done = "would be deleted (dry run)" if seam.dry_run else "deleted, and read back gone"
    lines = [f"  {done}: {n}" for n in deleted] + [f"  already gone: {n}" for n in gone]
    if not deleted and not gone:
        lines.append(f"  nothing to delete: no {DISPLAY_NAME}* instance in {', '.join(regions)}")
    lines.append(grant_line)
    ctx.known = None
    for name, why in left:
        lines.append(f"  LEFT: {name} - {why}")
        if name.startswith("projects/"):
            lines.append(f"    python -c \"import vertexai; vertexai.Client(project='{ctx.p}', location='"
                         f"{region_of(name)}').agent_engines.delete(name='{name}', force=True)\"")
    stuck = [n for n, _ in left if n.startswith("projects/")]
    if left:
        kept = {k: v for k, v in state.items() if k not in INSTANCE_KEYS}
        ctx.save({**kept, **({"name": stuck[0], "region": region_of(stuck[0])} if stuck else {})})
    else:
        ctx.forget()
    record = {"kind": RECORD_KIND, "command": "down", "host": "agent_engine", "at": utc_now(),
              "region": ctx.args.region, "deleted": len(deleted), "already_gone": len(gone), "left": len(left),
              "grant_taken_back": bool(grant) and not any(n == grant["on"] for n, _ in left)}
    show(ctx, record, lines)
    return left


def read_back_gone(ctx: Ctx, name: str) -> bool:
    """GET until 404, every 10 s for a minute."""
    for attempt in range(7):
        try:
            ctx.seam.call(f"GET {endpoint(region_of(name))}/v1/{name}  # expect 404", "get_instance", name,
                          quiet=attempt > 0)
        except Refused as error:
            if error.status == 404:
                return True
        if attempt < 6:
            ctx.sleep(10)
    return False


# ---------------------------------------------------------------------------------------------- smoke

class Checks:
    def __init__(self, say):
        self.say, self.passed, self.failed, self.skipped = say, [], [], []

    def ok(self, name, detail=""):
        self.passed.append(name)
        self.say(f"  [PASS] {name}  {detail}".rstrip())

    def bad(self, name, detail=""):
        self.failed.append(name)
        self.say(f"  [FAIL] {name}  {detail}".rstrip())

    def skip(self, name, detail=""):
        self.skipped.append(name)
        self.say(f"  [SKIP] {name}  {detail}".rstrip())


def cmd_smoke(ctx: Ctx) -> int:
    a, seam = ctx.args, ctx.seam
    ctx.say(f"== smoke: the managed peer in {a.region} (workshop lesson 10.9) ==")
    checks, records, created, name = Checks(ctx.say), [], False, None
    member = sa_email(MEMBER_SA, ctx.p)
    wait = 0 if seam.dry_run else a.wait
    try:
        name = ctx.instance()
        if not name:
            ctx.say("  no managed peer yet: this smoke deploys one, and deletes it at the end unless --keep")
            created = True
            name = up(ctx)
        # 1-3: the managed peer's questions, as documind-ui-sa (roles/aiplatform.user, nothing on the instance)
        began = utc_now()
        for label, tenant, check in (("first", PEER_TENANT, "acme answered through documind-mcp"),
                                     ("again", PEER_TENANT, "acme answered again, warm"),
                                     ("zeta", "zeta", "zeta refused by the roster")):
            try:
                got = ask(ctx, host="agent_engine", tenant=tenant, question=QUESTION, account=member, label=label)
            except (Refused, Stop) as error:
                checks.bad(check, f"{error}")
                continue
            records.append(ctx.keep(got["record"]))
            rec, turn = got["record"], got["turn"]
            if seam.dry_run:
                checks.ok(check, "(dry run)")
            elif tenant == PEER_TENANT:
                fact = None if rec["answered"] else turn_fact(turn)
                (checks.ok if rec["answered"] and "retrieve" in rec["tool_calls"] else checks.bad)(
                    check, f"{rec['latency_s']['total']} s, {rec['model']['calls']} model call(s)"
                           + (f"  - STOPPED on {fact}: {trim(fact.meaning, 160)}" if fact
                              else f"  {trim(turn['answer'], 90)!r}"))
            else:
                (checks.ok if rec["refused_by_roster"] else checks.bad)(check, f"{trim(turn['answer'], 110)!r}")
        ended = utc_now()
        # 4: the outsider, with a token: it holds no project role, so the platform refuses it
        try:
            ask(ctx, host="agent_engine", tenant=PEER_TENANT, question=QUESTION, account=sa_email(OUTSIDER_SA, ctx.p),
                label="outsider")
            (checks.ok if seam.dry_run else checks.bad)("the outsider refused by the platform",
                                                        "(dry run)" if seam.dry_run else
                                                        "the instance ANSWERED documind-outsider-sa (fact 8)")
        except Refused as error:
            (checks.ok if error.status == 403 else checks.bad)("the outsider refused by the platform", f"{error}")
        except Stop as error:
            checks.skip("the outsider refused by the platform", f"(no token as {OUTSIDER_SA}: {trim(error, 120)})")
        # 5: whom documind-mcp saw during the managed asks: the runtime's account
        callers = sorted({short(c.get("caller")) for c in read_callers(ctx, shift(began, -10), shift(ended, 10), wait)
                          if c.get("caller")})
        if seam.dry_run:
            checks.ok("documind-mcp saw documind-agent-sa", "(dry run)")
        elif not callers:
            checks.skip("documind-mcp saw documind-agent-sa", "(no row in Cloud Logging yet: make managed-peer-trace)")
        elif callers == [AGENT_SA]:
            checks.ok("documind-mcp saw documind-agent-sa", "(one identity, whichever host asks)")
        else:
            checks.bad("documind-mcp saw documind-agent-sa", f"callers {callers} (fact 2)")
        # 6: the trace, and no question in it
        spans = read_trace(ctx, shift(began, -120), shift(utc_now(), 60), wait)
        asked = [question_for(t, QUESTION) for t in (PEER_TENANT, "zeta")]
        hits = sorted({h for q in asked for h in content_in(spans, q)})
        if seam.dry_run:
            checks.ok("spans written, message content off", "(dry run)")
        elif hits:
            checks.bad("spans written, message content off", f"the question is in {hits[:3]} (fact 7)")
        elif spans:
            checks.ok("spans written, message content off", f"({len(spans)} span(s))")
        else:
            checks.skip("spans written, message content off", f"(none in Cloud Trace after {wait} s: make "
                                                              f"managed-peer-trace later)")
        # 7: the sessions the asks wrote, and another user refused by ADK's check
        rec = sessions(ctx, name, owner=short(member))["record"]
        if seam.dry_run:
            checks.ok("sessions kept, another user refused", "(dry run)")
        elif not rec["sessions"]:
            checks.bad("sessions kept, another user refused", "no session on the instance (fact 9)")
        elif rec["other_user_refused"]:
            checks.ok("sessions kept, another user refused", f"({rec['sessions']} session(s); ADK's check, in the "
                                                             f"client: fact 9)")
        else:
            checks.bad("sessions kept, another user refused", "ADK's session service returned another user's (fact 9)")
        # 8: the runtime's own line (commands/managed_peer_agent.py): its location, the model on global, the cap,
        #    content off - the deploy's settings as the running image read them
        check = "the runtime's settings: the model on global, the cap of 12, content off"
        runtime = runtime_line(ctx, name)
        settings = tuple(runtime.get(k) for k in ("model_location", "ADK_MAX_LLM_CALLS",
                                                  "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"))
        if seam.dry_run:
            checks.ok(check, "(dry run)")
        elif not runtime:
            checks.skip(check, "(its line is not in Cloud Logging: the runtime log's resource type is unverified)")
        elif settings == ("global", str(PEER_MAX_LLM_CALLS), "false"):
            checks.ok(check, f"(GOOGLE_CLOUD_LOCATION={runtime.get('GOOGLE_CLOUD_LOCATION')}: fact 6)")
        else:
            checks.bad(check, f"read {settings} (facts 6 and 7)")
        # the Cloud Run peer: the same questions, measured the same way, for the table
        ctx.say("  -- the Cloud Run peer, asked the same way, for the comparison --")
        for label, tenant in (("first", PEER_TENANT), ("again", PEER_TENANT), ("zeta", "zeta")):
            try:
                got = ask(ctx, host="cloud_run", tenant=tenant, question=QUESTION, account=member, label=label)
            except (Refused, Stop, OSError) as error:
                ctx.say(f"  [SKIP] the Cloud Run peer  ({trim(error, 140)}: is documind-agent deployed? make "
                        f"smoke-agent)")
                break
            records.append(ctx.keep(got["record"]))
            rec = got["record"]
            ctx.say(f"  cloud run, {label}: (dry run)" if seam.dry_run else
                    f"  cloud run, {label}: {rec['latency_s']['total']} s, answered {rec['answered']}, refused by "
                    f"the roster {rec['refused_by_roster']}")
    finally:
        if created and not a.keep:
            ctx.say("  -- deleting what this smoke deployed --")
            down(ctx, also=(name,))
        elif created:
            ctx.say("  kept (--keep): it bills until make managed-peer-down")
    ctx.say("")
    both = {r.get("host") for r in records} >= {"cloud_run", "agent_engine"}
    for line in table(records if both else ctx.history() or records):
        ctx.say(line)
    ctx.say(f"\n  {len(checks.passed)} passed, {len(checks.failed)} failed, {len(checks.skipped)} skipped")
    return 1 if checks.failed else 0


# --------------------------------------------------------------------------------------------- compare

def table(records: list) -> list[str]:
    """Cloud Run against Agent Engine, from the records: the first call (after a deploy, or a smoke's first), the warm
    calls' median, the peer's own model rupees, and what each host's records say about its account and its door."""
    asks = [r for r in records if r.get("command") == "ask" and r.get("question") == PEER_TENANT and r.get("answered")]
    rows = {}
    for host in ("cloud_run", "agent_engine"):
        mine = [r for r in asks if r.get("host") == host]
        if not mine:
            rows[host] = None
            continue
        total = lambda r: (r.get("latency_s") or {}).get("total")  # noqa: E731
        first = [r for r in mine if (r.get("cold") or {}).get("first_after_deploy") or r.get("label") == "first"]
        warm = [total(r) for r in mine if r not in first and total(r) is not None]
        inr = [r["model"]["inr"] for r in mine if (r.get("model") or {}).get("inr") is not None]
        last = mine[-1]
        idle = (first[-1].get("cold") or {}).get("idle_s") if first else None
        rows[host] = {"asks": len(mine), "region": last.get("region"),
                      "first": (f"{total(first[-1])}" + (f" (idle {idle} s before)" if idle is not None else "")
                                if first and total(first[-1]) is not None else None),
                      "warm": round(statistics.median(warm), 2) if warm else None,
                      "slowest": max((total(r) for r in mine if total(r) is not None), default=None),
                      "inr": round(statistics.median(inr), 4) if inr else None,
                      "runtime": (last.get("identity") or {}).get("runtime"),
                      "door": (last.get("identity") or {}).get("door"), "hosting": last.get("hosting") or {}}
    lines = ["Cloud Run against Agent Engine, from this machine's records (evals/reports/managed-peer/runs.ndjson):"]
    for title, key in (("asks of acme's question, answered", "asks"), ("region", "region"),
                       ("first call (after a deploy, or a smoke's first), s", "first"),
                       ("warm calls, median s", "warm"), ("slowest call, s", "slowest"),
                       ("the peer's own model calls, median Rs", "inr"), ("runs as", "runtime"),
                       ("who may call it", "door")):
        cells = ["no record yet" if rows[h] is None else ("-" if rows[h][key] is None else str(rows[h][key]))
                 for h in ("cloud_run", "agent_engine")]
        lines.append(f"  {title:50} | Cloud Run: {cells[0]:28} | Agent Engine: {cells[1]}")
    for host, title in (("cloud_run", "Cloud Run"), ("agent_engine", "Agent Engine")):
        if rows[host]:
            lines.append(f"  {title} hosting: {json.dumps(rows[host]['hosting'], sort_keys=True)}")
    lines.append("  rag-api's own answer inside retrieve is billed on the lane whichever host asks, so it is in "
                 "neither column.")
    return lines


def cmd_compare(ctx: Ctx) -> int:
    records = ctx.history()
    if ctx.args.json:
        ctx.say(json.dumps({"records": len(records), "table": table(records)}, sort_keys=True))
    else:
        for line in table(records):
            ctx.say(line)
    return 0


# ----------------------------------------------------------------------------------------------- stage

def cmd_stage(ctx: Ctx) -> int:
    root = Path(ctx.args.dir)
    if root.exists() and any(root.iterdir()):
        raise Stop(f"{root} is not empty: stage writes into a new or empty folder")
    mcp_url = f"https://documind-mcp-{ctx.args.project_number or 'NUMBER'}.{ctx.args.services_region}.run.app"
    staged = stage(root, ctx.p, mcp_url, cloud_run_settings()["model"], ctx.args.aiplatform_pin)
    ctx.say(f"== stage: what make managed-peer-up deploys, written to {root} ==")
    sources = {"agent.py": PEER / "agent.py", "requirements.txt": PEER / "requirements.txt", "__init__.py": WRAPPER}
    sources.update({extra: PEER / extra for extra in ("chain.py", "pins.py", "tool_pins.json")
                    if (PEER / extra).exists()})                     # what stage() copied along, byte for byte
    for name in sorted(sources):
        same = sha256(staged["folder"] / name) == sha256(sources[name])
        ctx.say(f"  {APP_NAME}/{name:17} {'byte for byte' if same else 'differs from'} "
                f"{sources[name].relative_to(KIT).as_posix()}")
    ctx.say(f"  deploy_config/.agent_engine_config.json  {json.dumps(staged['config'])}")
    ctx.say(f"  deploy_config/.env                       {json.dumps(staged['env'])}")
    appended = "nothing more" if ctx.args.aiplatform_pin else \
        "google-cloud-aiplatform[adk,agent_engines], unpinned (fact 11)"
    ctx.say(f"  the image: google-adk[a2a]=={adk_pin()} (the peer's pin); the deploy appends {appended}")
    return 0


# ------------------------------------------------------------------------------------------------ main

COMMANDS = {"up": cmd_up, "ask": cmd_ask, "trace": cmd_trace, "smoke": cmd_smoke, "sessions": cmd_sessions,
            "down": cmd_down, "compare": cmd_compare, "stage": cmd_stage}
LIVE = ("up", "ask", "trace", "smoke", "sessions", "down")


def parse_args(argv=None):
    common = argparse.ArgumentParser(add_help=False)
    common.add_argument("--project", default=PLACEHOLDER, help="the lane's project id")
    common.add_argument("--project-number", default="", help="its number; read from the project when not given")
    common.add_argument("--region", default="asia-south1", help="where the managed peer runs (MANAGED_PEER_REGION)")
    common.add_argument("--services-region", default="asia-south1",
                        help="where the lane's Cloud Run services run (REGION)")
    common.add_argument("--dry-run", action="store_true", help="print every call and make none")
    common.add_argument("--json", action="store_true", help="the run's record as one JSON object")
    common.add_argument("--records", default=str(RECORDS), help="where state.json and runs.ndjson are kept")
    common.add_argument("--aiplatform-pin", default="",
                        help="google-cloud-aiplatform's version for the image (AIPLATFORM_PIN)")
    common.add_argument("--grant-role", default=GRANT_ROLE,
                        help="the role Agent Engine's service agent gets on documind-agent-sa")
    common.add_argument("--as", dest="as_account", default=MEMBER_SA,
                        help="who asks: a service account, or me (your ADC)")
    common.add_argument("--wait", type=int, default=120, metavar="SECONDS",
                        help="how long to wait for spans and log rows")
    p = argparse.ArgumentParser(prog="managed_peer.py", description=__doc__.split("\n\n")[0],
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="command", required=True)
    for name in COMMANDS:
        s = sub.add_parser(name, parents=[common])
        if name == "up":
            s.add_argument("--redeploy", action="store_true", help="deploy into an instance that is deployed already")
        if name == "ask":
            s.add_argument("--tenant", default=PEER_TENANT, help="acme is the peer's roster; another is refused")
            s.add_argument("--question", default="", help="unset: make smoke-agent's gratuity question")
            s.add_argument("--host", choices=("managed", "cloudrun"), default="managed")
        if name == "trace":
            s.add_argument("--since", type=int, default=0, metavar="MINUTES", help="unset: the last ask's window")
        if name == "smoke":
            s.add_argument("--keep", action="store_true", help="keep an instance the smoke deployed")
        if name == "sessions":
            s.add_argument("--delete", action="store_true", help="delete the sessions listed")
        if name == "stage":
            s.add_argument("--dir", required=True, help="a new or empty folder")
    a = p.parse_args(argv)
    for region in (a.region, a.services_region):
        if not re.fullmatch(r"[a-z][a-z0-9-]{1,40}", region):
            p.error(f"not a region: {region!r}")
    if a.project != PLACEHOLDER and not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", a.project):
        p.error(f"not a project id: {a.project!r}")
    if a.command in LIVE and not a.dry_run and a.project == PLACEHOLDER:
        p.error(f"{a.command} needs your lane's project id (--project), not the placeholder {PLACEHOLDER}")
    if a.project_number and not a.project_number.isdigit():
        p.error("--project-number takes digits")
    if a.aiplatform_pin and not re.fullmatch(r"\d+(\.\d+){1,3}", a.aiplatform_pin):
        p.error(f"not a version: {a.aiplatform_pin!r}")
    if not a.grant_role.startswith("roles/"):
        p.error(f"not a role: {a.grant_role!r}")
    return a


def main(argv=None, *, google_factory=LiveGoogle, out=None, sleep=time.sleep) -> int:
    out = out or sys.stdout
    args = parse_args(argv)

    def say(text: str = "") -> None:
        encoding = getattr(out, "encoding", None) or "utf-8"
        print(str(text).encode(encoding, "replace").decode(encoding, "replace"), file=out, flush=True)

    seam = Seam(args.project, google_factory, dry_run=args.dry_run, say=say)
    ctx = Ctx(args, seam, say, sleep=sleep, records=Path(args.records))
    if args.dry_run:
        say(f"DRY RUN: every call printed, none made ({args.command}, project {args.project})")
    try:
        code = COMMANDS[args.command](ctx)
    except FactRefused as fact:
        say(fact.render())
        return 3
    except (Stop, Refused) as stop:
        say(f"STOPPED: {stop}")
        return 2
    except ImportError as error:
        say(f"STOPPED: {error} - run it through commands/managed-peer.sh (make managed-peer-*), which makes "
            f"~/managed-peer-venv with google-adk and google-cloud-aiplatform")
        return 2
    except Exception as error:
        if type(error).__name__ != "DefaultCredentialsError":
            raise
        say(f"STOPPED: no Application Default Credentials ({trim(error, 160)}): gcloud auth application-default login")
        return 2
    if args.dry_run:
        say(f"Dry run: nothing was created or changed; {len(seam.calls)} call(s) printed above.")
    return code


if __name__ == "__main__":
    sys.exit(main())
