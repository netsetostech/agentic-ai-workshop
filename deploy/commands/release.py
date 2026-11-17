#!/usr/bin/env python3
"""The release's operator commands (the v5 course's Module 11): what mk/release.mk runs, without make.

    python commands/release.py ci-vars --project <id> --region <region>         make ci-vars         (lesson 11.1)
    python commands/release.py keys --project <id>                              make keys-check      (lesson 11.1)
    python commands/release.py gate --project <id> --region <region>            make gate            (lesson 11.2)
    python commands/release.py gate-check --project <id> --region <region>      make promote-gated   (lesson 11.2)
    python commands/release.py smoke-deployed --project <id> --region <region>  make smoke-deployed  (lesson 11.3)
    python commands/release.py incident --project <id> --region <region>        make incident        (lesson 11.3)

ci-vars and keys only read: terraform output, the lane's confirmed inputs, gcloud's describe and list calls and, when gh
is installed, one GET of the repository's production environment. Neither writes to Google Cloud, to GitHub or to
this checkout, so neither has a switch. Every tool is found on PATH the way a shell finds it (gcloud is gcloud.cmd on
Windows), and gcloud never prompts: its one prompt here would offer to enable an API, which is a write.

ci-vars prints the `gh variable set` lines for the repository variables .github/workflows/documind-cd.yml reads, once
it has checked that the workflow reads exactly these four: GCP_PROJECT and GCP_REGION from the lane's confirmed inputs
(terraform/runbook-project.auto.tfvars.json, which infrastructure.py confirmed and saved when make plan ran),
WIF_PROVIDER and CICD_SERVICE_ACCOUNT from `terraform output -json` (wif.tf). A PROJECT or REGION the lane was not
planned with is refused: the Makefile's REGION defaults to us-central1, and a workflow told the wrong region builds its
image into a repository that does not exist. The lines name the repository wif.tf's condition trusts, and the dispatch
line names the one branch it trusts; any other repository or branch is refused at the workflow's auth step. GitHub
creates an environment the first time a job names it, with no protection rule, so a repository with no production
environment, or one with no required reviewer, would let promote move traffic with nobody approving: with gh
installed, ci-vars reads the environment and warns.

keys lists every service account in the project with its user-managed keys, and says where the project sits: under an
organization, org_policy.tf's enforce_no_sa_keys can forbid making keys; a personal account's project has no
organization, nothing can forbid them, and this check is the control.

gate judges the exact revision deploy/.candidate-revision names and records what it judged. Before any row is asked, the
candidate tag must route to that revision (promote's own rule), the revision's image digest and GIT_SHA are read (gcloud
run revisions describe), the tag its image was deployed by must be GIT_SHA (F43; read from the service's spec.template,
which keeps the tag while the revision is the last it made), and the tag URL's GET /version must answer as that GIT_SHA
(the CD workflow's check), as documind-ui-sa with a token for the service's canonical URL (F42). Then evals/run_eval.py
asks every golden row of the tag URL, as make eval-live does, into evals/reports/gate-<revision>.json, and the gate
record, by default evals/reports/gate.json (gitignored), names the revision, its image as deployed, its digest and
GIT_SHA, the report's sha256, the verdict and scores, the time, and the sha256 of each file the verdict was judged by. A
red gate writes its record too. A gate refused before its rows start leaves the earlier record as it was; one that stops
once they have started writes none, and the earlier record is gone with it, deleted as the rows start. It writes nothing
to Google Cloud, so the target is its own switch: a lane that never runs it behaves as before.
GATE_PROMPT=1 (off by default: it can refuse a release) also holds the candidate's prompt to lesson 3.6's registry where
the rows would start: the label GET /version answers under, against generator.py, config.py, prompt_versions.json and
prompt_rules.json as the commit its GIT_SHA names holds them (git show, in this checkout). A prompt that is not a
registered version at that commit (prompt_reasons() says why) stops the gate before any row is asked, and leaves no
record.

gate-check decides whether make promote may move traffic: only to the revision a green record names, while
deploy/.candidate-revision still names it and the candidate tag is not on another, with the record's digest and
GIT_SHA, a report that still hashes to the record's sha256 and says what the record says, and a record that is not
stale. Stale: finished more than 24 hours ago (the lane's documents, rosters and the model's answers may have moved
since), or judged by other rules - evals/run_eval.py, golden.jsonl, required.json or manifest.json differ from this
checkout's. make promote-gated runs it, then make promote, unchanged.

smoke-deployed runs the smokes of the services this lane has deployed. make smoke-all runs eight, the gateway's and
the SLM's among them, so on a lane without Module 9's services it is red whatever the API does. This reads which Cloud
Run services exist (gcloud run services list in REGION, and in SLM_REGION for documind-slm) and runs each of
smoke-all's smokes whose services all exist, through make, with the exports smoke-all's loop gives them and its output
filtered as that loop filters it. A smoke's own exit status decides, and a skipped smoke is named with the service it
lacks. Before the smokes it reads the traffic table and GET /version on the service's URL as documind-ui-sa; after
them it appends one line to evals/reports/smoke-deployed.jsonl (gitignored): the time, the revision serving
documind-api and what /version said, and each smoke's exit status. The smokes are make targets, as smoke-all's are, so
it needs make (--make, or make on PATH). It writes nothing to Google Cloud.

incident prints a release incident from the lane and this checkout's records: documind-api's revisions made in the
last --hours (24), with their image and GENERATOR_MODEL; the gate record and each revision's gate report; every
smoke-deployed run, with what served and what /version said; then the traffic table, .candidate-revision,
.previous-revision and the service's spec.template as they are now. Last, whether the lane is in the gated state: the
revision serving is one a gate judged green, spec.template is what serves, and .candidate-revision names no revision
the gate judged red. spec.template keeps the tag a deploy gave its image and a revision the digest that tag named, so
the template's image is compared as the revision it made (status.latestCreatedRevisionName) holds it, as
commands/gotchas.py reads it. make rollback moves traffic and leaves spec.template as the last update made it, and make
candidate and make release-candidate start from the template (env vars merge across revisions, F43): after a forced
promote of a bad candidate and a rollback, the next candidate would carry the bad setting until a candidate made from
what serves puts it back. incident names that candidate's make line. It only reads.

Exit codes: 0 done (ci-vars may still warn); 1 keys found a user-managed key, the gate judged the candidate red (its
record says so), gate-check refused the record, a smoke failed (smoke-deployed), or the lane is not in the gated state
(incident); 2 stopped: a tool, an input or a read failed, and the message says which.
"""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime
import hashlib
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
KIT = HERE.parent                                   # the kit: deploy/ here, the repository root in the learner repo
WORKFLOW = KIT / ".github" / "workflows" / "documind-cd.yml"

# infrastructure.py owns the lane's confirmed inputs (the file, its reader, validate_trust): make plan wrote them, and
# ci-vars reads the same record rather than a second copy of the rules.
_spec = importlib.util.spec_from_file_location("infrastructure", HERE / "infrastructure.py")
infra = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(infra)

# The repository variables documind-cd.yml reads, in the order ci-vars prints them.
CI_VARS = ("GCP_PROJECT", "GCP_REGION", "WIF_PROVIDER", "CICD_SERVICE_ACCOUNT")
# wif.tf's pool and provider ids, and sa.tf's pipeline account, as terraform output prints them.
WIF_PROVIDER = re.compile(r"projects/[0-9]+/locations/global/workloadIdentityPools/documind-github/providers/github-oidc")
CICD_ACCOUNT = re.compile(r"sa-documind-cicd@([a-z][a-z0-9-]{4,28}[a-z0-9])\.iam\.gserviceaccount\.com")
PROJECT_ID = re.compile(r"[a-z][a-z0-9-]{4,28}[a-z0-9]")
KEYS_FOUND, STOPPED = 1, 2
INSTALL = {"terraform": "install Terraform 1.9.0 or newer (lesson 0.2)",
           "gcloud": "install the Google Cloud CLI, or run this in Cloud Shell", "gh": "install the GitHub CLI"}
REVIEWERS = ("Settings > Environments > production > Required reviewers (on a private repository, required reviewers "
             "need a paid GitHub plan)")


class Stop(RuntimeError):
    """A precondition failed. The message says which, and the command exits 2."""


def count(n: int, thing: str) -> str:
    return f"{n} {thing}{'' if n == 1 else 's'}"


def cause(text: str) -> str:
    """The line of a tool's error output that names the cause: gcloud's ERROR line, terraform's Error line (out of its
    box), else the first line."""
    lines = [line.strip(" \t\u2502\u2577\u2575") for line in (text or "").splitlines()]
    lines = [line for line in lines if line]
    return next((line for line in lines if line.startswith(("ERROR:", "Error:", "error:"))),
                lines[0] if lines else "no error output")


def run(argv: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    """One read-only call of terraform, gcloud or gh, with its output captured and never a prompt."""
    exe = shutil.which(argv[0])
    if not exe:
        raise Stop(f"{argv[0]} is not on PATH: {INSTALL.get(argv[0], 'install it')}")
    env = dict(os.environ, CLOUDSDK_CORE_DISABLE_PROMPTS="1", GH_PROMPT_DISABLED="1", GH_NO_UPDATE_NOTIFIER="1")
    try:
        return subprocess.run([exe, *argv[1:]], cwd=cwd, env=env, stdin=subprocess.DEVNULL, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=300)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise Stop(f"{argv[0]} {argv[1]} could not run: {e}") from e


def read_json(argv: list[str]):
    """A gcloud read as JSON, or a Stop naming the call and the line of gcloud's error that names the cause."""
    r = run(argv)
    what = " ".join(argv[:4]) if argv[1] in ("iam", "run") else " ".join(argv[:3])
    if r.returncode:
        raise Stop(f"{what} failed (exit {r.returncode}): {cause(r.stderr)}")
    try:
        return json.loads(r.stdout or "null")
    except ValueError:
        raise Stop(f"{what} did not return JSON") from None


# ---------------------------------------------------------------- ci-vars (lesson 11.1)

def workflow_vars(path: Path = WORKFLOW) -> list[str]:
    """Every repository variable the workflow reads: each vars.NAME inside a ${{ }} expression, sorted."""
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as e:
        raise Stop(f"cannot read the workflow {path}: {e}") from e
    return sorted({name for expr in re.findall(r"\$\{\{(.*?)\}\}", text)
                   for name in re.findall(r"\bvars\.([A-Za-z_][A-Za-z0-9_]*)", expr)})


def check_workflow(path: Path) -> None:
    found = workflow_vars(path)
    if found != sorted(CI_VARS):
        raise Stop(f"{path.name} reads {', '.join(found) or 'no repository variable'}, and ci-vars sets "
                   f"{', '.join(CI_VARS)}: change CI_VARS in commands/release.py with the workflow, and say where each "
                   "value comes from")


def lane_inputs(tf_dir: Path) -> dict:
    """The lane's confirmed inputs: its project and region, and the CI trust its WIF condition holds."""
    path = tf_dir / infra.INPUT_FILE
    if not path.is_file():
        raise Stop(f"no {infra.INPUT_FILE} in {tf_dir}. It is the lane's confirmed inputs, saved by make plan: run this "
                   "in the checkout that planned the lane, or first run python commands/infrastructure.py prepare "
                   "--project PROJECT --region REGION here, which reads the CI trust from the lane's state")
    saved = infra.read_json(path)
    trust = infra.validate_trust({key: str(saved.get(key, "")) for key in infra.TRUST})
    project, region = str(saved.get("project_id", "")), str(saved.get("region", ""))
    if not PROJECT_ID.fullmatch(project) or not region:
        raise Stop(f"{path} names no project or no region: run python commands/infrastructure.py prepare again")
    return {**trust, "project_id": project, "region": region}


def terraform_outputs(tf_dir: Path) -> dict:
    """name -> value of every output. -json prints sensitive outputs in clear (gateway_database_url), so its text is
    parsed here and never echoed, not even in an error."""
    r = run(["terraform", "output", "-json"], cwd=tf_dir)
    if r.returncode:
        raise Stop(f"terraform output failed in {tf_dir} (exit {r.returncode}): {cause(r.stderr)}. A checkout that "
                   "was never connected to the lane's state: make tf-backend PROJECT=<id> first")
    try:
        data = json.loads(r.stdout or "{}")
    except ValueError:
        raise Stop(f"terraform output -json in {tf_dir} did not return JSON") from None
    if not isinstance(data, dict):
        raise Stop(f"terraform output -json in {tf_dir} did not return an object")
    return {name: out.get("value") for name, out in data.items() if isinstance(out, dict)}


def ci_values(project: str, region: str, tf_dir: Path) -> tuple[dict, dict]:
    """(the four values by variable name, the lane's confirmed inputs), every source checked against the others."""
    lane = lane_inputs(tf_dir)
    if project and project != lane["project_id"]:
        raise Stop(f"PROJECT is {project}, but {tf_dir} is lane {lane['project_id']}'s ({infra.INPUT_FILE}): "
                   "run this in that lane's checkout, or with its project")
    if region and region != lane["region"]:
        raise Stop(f"REGION is {region}, but lane {lane['project_id']} was planned in {lane['region']} "
                   f"({infra.INPUT_FILE}), where its image repository and services are: make ci-vars "
                   f"PROJECT={lane['project_id']} REGION={lane['region']}")
    outputs = terraform_outputs(tf_dir)
    provider, account = outputs.get("wif_provider"), outputs.get("cicd_service_account")
    if not provider or not account:
        raise Stop("terraform output has no wif_provider or no cicd_service_account: the state this checkout reads "
                   "holds no CI pipeline. make up applies wif.tf and sa.tf; make tf-backend connects a checkout to "
                   "the lane's state")
    if not isinstance(provider, str) or not WIF_PROVIDER.fullmatch(provider):
        raise Stop(f"wif_provider is not wif.tf's provider (pool documind-github, provider github-oidc): {provider}")
    match = CICD_ACCOUNT.fullmatch(account) if isinstance(account, str) else None
    if not match:
        raise Stop(f"cicd_service_account is not sa.tf's sa-documind-cicd: {account}")
    if match[1] != lane["project_id"]:
        raise Stop(f"terraform output is project {match[1]}'s, but {infra.INPUT_FILE} is lane {lane['project_id']}'s: "
                   "this checkout's backend points at another lane's state")
    return {"GCP_PROJECT": lane["project_id"], "GCP_REGION": lane["region"], "WIF_PROVIDER": provider,
            "CICD_SERVICE_ACCOUNT": account}, lane


def production_environment(repo: str) -> tuple[str, str]:
    """('ok' | 'warn' | 'unread' | 'note', the line to print) for the repository's production environment, which
    promote names: one GET through gh, when gh is installed. 'unread': gh ran and did not return the environment."""
    if not shutil.which("gh"):
        return "note", ("gh is not installed here, so the production environment was not read: check it has a "
                        "required reviewer, " + REVIEWERS)
    r = run(["gh", "api", f"repos/{repo}/environments/production"])
    if r.returncode:
        if "HTTP 404" in r.stderr or '"Not Found"' in r.stdout:
            return "warn", (f"{repo} has no production environment, or gh's account cannot see the repository. GitHub "
                            "creates the environment the first time a job names it, with no required reviewer, and "
                            "promote would then move traffic with nobody approving. Create it with a reviewer before "
                            "the first dispatch: " + REVIEWERS)
        return "unread", (f"could not read {repo}'s production environment ({cause(r.stderr)}): check by hand that it "
                          "has a required reviewer, " + REVIEWERS)
    try:
        rules = json.loads(r.stdout or "{}").get("protection_rules") or []
    except (ValueError, AttributeError):
        return "unread", f"gh did not return {repo}'s production environment as JSON: check it by hand, " + REVIEWERS
    reviewers = sum(len(rule.get("reviewers") or []) for rule in rules
                    if isinstance(rule, dict) and rule.get("type") == "required_reviewers")
    if not reviewers:
        return "warn", (f"{repo}'s production environment has no required reviewer, so promote would move traffic "
                        "with nobody approving. Add one: " + REVIEWERS)
    return "ok", f"production: {count(reviewers, 'required reviewer')}, so promote waits for a person"


def cmd_ci_vars(a) -> int:
    workflow = Path(a.workflow).expanduser().resolve()
    tf_dir = Path(a.terraform_dir).expanduser().resolve()
    check_workflow(workflow)
    values, lane = ci_values(a.project, a.region, tf_dir)
    repo, ref = lane["github_repository"], lane["deploy_ref"]
    q = shlex.quote
    print(f"# {workflow.name} reads {len(CI_VARS)} repository variables. Set them on {repo}, the repository wif.tf "
          "trusts:")
    for name in CI_VARS:
        print(f"gh variable set {name} --repo {q(repo)} --body {q(values[name])}")
    print(f"# The trust (wif.tf): {repo}, id {lane['github_repository_id']}, ref {ref}. A run from any other ref is "
          "refused at the auth step.")
    print("# Dispatch from that branch, on the candidate path - path=clouddeploy would replace documind-api's settings "
          "with run-service.yaml's:")
    print(f"#   gh workflow run {workflow.name} --repo {q(repo)} --ref {q(ref.removeprefix('refs/heads/'))} "
          "-f path=candidate")
    level, line = production_environment(repo)
    if level in ("warn", "unread"):
        sys.stdout.flush()
        print(f"WARNING: {line}", file=sys.stderr)
    else:
        print(f"# {line}")
    return 0


# ---------------------------------------------------------------- keys (lesson 11.1)

def parent_line(project: str, parent) -> str:
    if not isinstance(parent, dict) or not parent.get("type"):
        return (f"{project} has no parent: it is in no organization, so org_policy.tf's enforce_no_sa_keys cannot be "
                "applied and nothing stops a key being made; this check is the control")
    kind, ident = parent["type"], parent.get("id", "?")
    where = "" if kind == "organization" else ", inside an organization"
    return (f"{project} is in {kind} {ident}{where}: org_policy.tf's enforce_no_sa_keys can forbid making keys here, "
            "and an organization created on or after 3 May 2024 forbids it by default")


def user_keys(project: str, email: str) -> tuple[list | None, str]:
    """(the account's user-managed keys, '') or (None, why they could not be listed)."""
    try:
        r = run(["gcloud", "iam", "service-accounts", "keys", "list", f"--iam-account={email}", f"--project={project}",
                 "--managed-by=user", "--format=json"])
    except Stop as e:
        return None, str(e)
    if r.returncode:
        return None, cause(r.stderr)
    try:
        keys = json.loads(r.stdout or "[]")
    except ValueError:
        return None, "gcloud did not return JSON"
    return ([k for k in keys if isinstance(k, dict)], "") if isinstance(keys, list) else (None, "not a list")


def key_line(key: dict) -> str:
    expires = str(key.get("validBeforeTime") or "")
    when = "never expires" if not expires or expires.startswith("9999-") else f"expires {expires}"
    return (f"       key {str(key.get('name', '?')).rsplit('/', 1)[-1]}  created {key.get('validAfterTime', '?')}  "
            f"{when}" + ("  (disabled, not deleted)" if key.get("disabled") else ""))


def cmd_keys(a) -> int:
    project = a.project
    if not PROJECT_ID.fullmatch(project or ""):
        raise Stop("pass --project with the lane's project id (or PROJECT in the environment)")
    info = read_json(["gcloud", "projects", "describe", project, "--format=json"])
    if not isinstance(info, dict) or info.get("projectId") != project:
        raise Stop(f"gcloud projects describe did not return project {project}")
    print(parent_line(project, info.get("parent")))
    accounts = read_json(["gcloud", "iam", "service-accounts", "list", f"--project={project}", "--format=json"])
    if not isinstance(accounts, list):
        raise Stop("gcloud iam service-accounts list did not return a list")
    emails = sorted({acct["email"] for acct in accounts if isinstance(acct, dict) and acct.get("email")})
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        listed = list(pool.map(lambda email: user_keys(project, email), emails))
    print(f"{count(len(emails), 'service account')}, and the user-managed keys of each:")
    found, holders, unread = 0, 0, []
    for email, (keys, why) in zip(emails, listed):
        if keys is None:
            unread.append(email)
            print(f"  ?  {email}  could not list its keys: {why}")
            continue
        print(f"  {len(keys)}  {email}")
        for key in keys:
            print(key_line(key))
        found, holders = found + len(keys), holders + bool(keys)
    if found:
        print(f"{count(found, 'user-managed key')} on {count(holders, 'account')}"
              + (f" ({count(len(unread), 'more account')} not read)" if unread else "")
              + ". A key is a credential that does not expire and works wherever it is copied: delete each one "
              "nothing uses")
        print(f"  gcloud iam service-accounts keys delete KEY_ID --iam-account=ACCOUNT --project={project}")
        return KEYS_FOUND
    if unread:
        raise Stop(f"the keys of {count(len(unread), 'account')} could not be listed, so this is no proof of zero "
                   f"keys: {', '.join(unread)}")
    print(f"no user-managed keys: no key file can sign in as any account of {project}")
    return 0


# ---------------------------------------------------------------- gate and gate-check (lesson 11.2)

SERVICE = "documind-api"
# The gate's two identities, the ones make eval-live mints: a roster member asks every row; the outsider, who is on no
# roster, asks the isolation rows and must be refused.
MEMBER_SA, OUTSIDER_SA = "documind-ui-sa", "documind-outsider-sa"
GATE_FORMAT = "documind-gate/1"
# What a verdict was judged by: the evaluator (its thresholds and how a row is judged), the rows, the rows that must
# each pass, and the documents a citation may name. A record judged by other copies of these than the checkout's is
# stale.
RULES = ("evals/run_eval.py", "evals/golden.jsonl", "evals/required.json", "evals/manifest.json")
# A verdict is about the lane as it was when the rows were asked: its documents, rosters and the model's answers move.
MAX_AGE_HOURS = 24.0
SKEW = datetime.timedelta(minutes=5)       # a record stamped later than now by more than this came from another clock
# A revision of documind-api by name, as record-candidate writes it and the CD workflow's promote job accepts it.
REVISION = re.compile(r"documind-api-[a-z0-9](?:[a-z0-9-]{0,48}[a-z0-9])?")
# status.imageDigest: the image Cloud Run resolved when it made the revision, by content, never by tag.
DIGEST = re.compile(r"[a-z0-9.-]+(?:/[A-Za-z0-9._-]+)+@sha256:[0-9a-f]{64}")
REGION_NAME = re.compile(r"[a-z]+-[a-z]+[0-9]+")
RECORD_FIELDS = ("project", "region", "service", "revision", "image", "digest", "git_sha", "report", "report_sha256",
                 "eval_exit", "verdict", "rules", "finished")
REFUSED = 1


def now() -> datetime.datetime:
    """The clock a record is stamped and judged by: a function, so the tests can move it."""
    return datetime.datetime.now(datetime.timezone.utc)


def stamp(t: datetime.datetime) -> str:
    return t.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def read_stamp(text) -> datetime.datetime | None:
    try:
        return datetime.datetime.strptime(str(text), "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=datetime.timezone.utc)
    except ValueError:
        return None


def sha256_of(path: Path) -> str:
    digest = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(1 << 16), b""):
            digest.update(block)
    return digest.hexdigest()


def rules_now() -> dict:
    """{path: sha256} of the files a verdict is judged by, as this checkout holds them."""
    try:
        return {rel: sha256_of(KIT / rel) for rel in RULES}
    except OSError as e:
        raise Stop(f"cannot read the gate's rules: {e}") from e


def shown(path: Path) -> str:
    """A path as a record keeps it and a message shows it: inside the kit, relative to it; elsewhere, absolute."""
    try:
        return path.resolve().relative_to(KIT.resolve()).as_posix()
    except ValueError:
        return str(path.resolve())


def located(text: str) -> Path:
    path = Path(text)
    return path if path.is_absolute() else KIT / path


def lane_of(a) -> tuple[str, str]:
    if not PROJECT_ID.fullmatch(a.project or ""):
        raise Stop("pass --project with the lane's project id (or PROJECT in the environment)")
    if not REGION_NAME.fullmatch(a.region or ""):
        raise Stop("pass --region with the region documind-api runs in (or REGION in the environment)")
    return a.project, a.region


def gate_paths(a) -> tuple[Path, Path]:
    """(the gate record, the candidate file): by default the kit's evals/reports/gate.json and .candidate-revision, the
    files make's recipes name from the kit's directory."""
    record = Path(a.gate_file).expanduser() if a.gate_file else KIT / "evals" / "reports" / "gate.json"
    candidate = Path(a.candidate_file).expanduser() if a.candidate_file else KIT / ".candidate-revision"
    return record.resolve(), candidate.resolve()


def recorded_candidate(path: Path) -> str:
    """The revision the candidate file names: the one make release-candidate or make candidate recorded, and the one
    make promote moves traffic to."""
    try:
        name = path.read_text(encoding="utf-8").strip()
    except FileNotFoundError:
        raise Stop(f"{shown(path)} is missing: make release-candidate (or make candidate) records the revision it "
                   "makes, and make promote moves traffic to that revision by name") from None
    except OSError as e:
        raise Stop(f"cannot read {path}: {e}") from e
    if not REVISION.fullmatch(name):
        raise Stop(f"{shown(path)} does not name a {SERVICE} revision: {name[:80]!r}")
    return name


def describe_api(project: str, region: str):
    """documind-api as gcloud run services describe returns it: the traffic table and spec.template."""
    return read_json(["gcloud", "run", "services", "describe", SERVICE, f"--region={region}", f"--project={project}",
                      "--format=json"])


def service_traffic(project: str, region: str) -> tuple[str, str]:
    """(the revision serving the most traffic, the revision the candidate tag names), '' for none: documind-api's
    status.traffic, read the way make promote reads it."""
    return traffic_of(describe_api(project, region))


def traffic_of(data) -> tuple[str, str]:
    """service_traffic's two names, from a describe already read."""
    traffic = (data.get("status") or {}).get("traffic") if isinstance(data, dict) else None
    if not isinstance(traffic, list):
        raise Stop(f"gcloud run services describe {SERVICE} returned no status.traffic")
    rows = [t for t in traffic if isinstance(t, dict)]
    serving = max((t for t in rows if t.get("percent")), key=lambda t: t["percent"], default={})
    tagged = next((t for t in rows if t.get("tag") == "candidate"), {})
    return str(serving.get("revisionName") or ""), str(tagged.get("revisionName") or "")


def revision_facts(project: str, region: str, name: str) -> dict:
    """What a revision is: its service, the digest Cloud Run resolved its image to when it made the revision
    (status.imageDigest; a revision never changes), its GIT_SHA, and whether it is Ready. The revision's own spec names
    its image by that digest too, never by the tag the deploy gave: deployed_image() reads the tag."""
    data = read_json(["gcloud", "run", "revisions", "describe", name, f"--region={region}", f"--project={project}",
                      "--format=json"])
    if not isinstance(data, dict):
        raise Stop(f"gcloud run revisions describe {name} did not return a revision")
    meta, spec, status = (data.get(key) if isinstance(data.get(key), dict) else {}
                          for key in ("metadata", "spec", "status"))
    containers = [c for c in spec.get("containers") or [] if isinstance(c, dict)]
    env = {e.get("name"): e.get("value") for c in containers for e in c.get("env") or [] if isinstance(e, dict)}
    return {"service": (meta.get("labels") or {}).get("serving.knative.dev/service"),
            "digest": status.get("imageDigest"),
            "git_sha": env.get("GIT_SHA"),
            "ready": any(isinstance(c, dict) and c.get("type") == "Ready" and c.get("status") == "True"
                         for c in status.get("conditions") or [])}


def deployed_image(service, name: str) -> str:
    """The image reference revision `name` was deployed by (.../documind/api:abc1234), from a describe of the service
    already read; '' when it cannot be read. Cloud Run writes the digest the tag named on every revision, and only the
    service's spec.template keeps the tag (22 October 2026), so the reference is the template's while the revision is
    the one the template made, status.latestCreatedRevisionName, and unknown once a later update has made another."""
    status = service.get("status") if isinstance(service, dict) else None
    if not isinstance(status, dict) or status.get("latestCreatedRevisionName") != name:
        return ""
    return container_of(((service.get("spec") or {}).get("template") or {}).get("spec"))[0]


def image_tag(image) -> str:
    """The tag of an image reference, '' for one named by digest alone: .../documind/api:abc1234 -> abc1234."""
    last = str(image or "").rsplit("/", 1)[-1].split("@", 1)[0]
    return last.split(":", 1)[1] if ":" in last else ""


def unjudgeable(facts: dict) -> list[str]:
    """Why a revision cannot be bound to a verdict, or []: its revision_facts(), with its deployed_image() as image."""
    why = []
    if facts["service"] != SERVICE:
        why.append(f"it belongs to {facts['service'] or 'no service'}, not {SERVICE}")
    if not facts["ready"]:
        why.append("it is not Ready (status.conditions)")
    if not DIGEST.fullmatch(str(facts["digest"] or "")):
        why.append("Cloud Run reports no image digest for it (status.imageDigest)")
    sha, tag = facts["git_sha"], image_tag(facts["image"])
    if not sha:
        why.append("it carries no GIT_SHA, so GET /version cannot say which build answers: make release-candidate "
                   "GIT_SHA=<tag> sets it")
    elif not facts["image"]:
        why.append(f"{SERVICE}'s spec.template has made a later revision (status.latestCreatedRevisionName), so the "
                   "tag its image was deployed by cannot be read: a revision holds only the digest, and an image-only "
                   "update (F43) cannot be ruled out. make release-candidate again")
    elif tag and tag != sha:
        why.append(f"it runs {str(facts['image']).rsplit('/', 1)[-1]} but its GIT_SHA says {sha}: env vars merge "
                   "across revisions, so an image-only update keeps the old GIT_SHA (F43). make release-candidate "
                   f"GIT_SHA={tag} sets both")
    return why


def project_number(project: str) -> str:
    info = read_json(["gcloud", "projects", "describe", project, "--format=json"])
    number = str(info.get("projectNumber") or "") if isinstance(info, dict) else ""
    if not number.isdigit():
        raise Stop(f"gcloud projects describe {project} returned no project number")
    return number


def identity_token(project: str, account: str, audience: str) -> str:
    """An ID token for audience as one of the lane's accounts, minted by impersonation as make eval-live mints it: the
    operator needs the token-creator role on the account, which make operators grants. Never printed."""
    email = f"{account}@{project}.iam.gserviceaccount.com"
    r = run(["gcloud", "auth", "print-identity-token", "--include-email", f"--impersonate-service-account={email}",
             f"--audiences={audience}"])
    token = (r.stdout or "").strip()
    if r.returncode or not token or any(ch.isspace() for ch in token):
        raise Stop(f"could not mint a token as {email} (exit {r.returncode}): {cause(r.stderr)}. make operators "
                   f"PROJECT={project} grants the operator the token-creator role on it")
    return token


def get_version(url: str, token: str) -> dict:
    """GET /version on url with the token: what the revision behind that URL says it is (main.py's version()). Two
    attempts: a revision with no traffic has scaled to zero, and its first request waits for an instance."""
    request = urllib.request.Request(url.rstrip("/") + "/version", headers={"Authorization": f"Bearer {token}"})
    last = ""
    for _ in range(2):
        try:
            with urllib.request.urlopen(request, timeout=60) as response:
                body = json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            if e.code == 401:
                raise Stop(f"GET {url}/version answered HTTP 401: the token was refused. Its audience must be the "
                           f"service's canonical URL, https://{SERVICE}-NUMBER.REGION.run.app, whichever of its URLs "
                           "is called (F42); a DOCUMIND_ID_TOKEN in the environment is used as it is") from None
            if e.code == 403:
                raise Stop(f"GET {url}/version answered HTTP 403: the token's account may not invoke {SERVICE} "
                           "(roles/run.invoker)") from None
            last = f"HTTP {e.code}"
            continue
        except (urllib.error.URLError, OSError, ValueError) as e:
            last = str(getattr(e, "reason", e))
            continue
        if not isinstance(body, dict):
            raise Stop(f"GET {url}/version did not return a JSON object")
        return body
    raise Stop(f"GET {url}/version failed twice: {last}")


def live_gate(url: str, report: Path, member: str, outsider: str) -> int:
    """evals/run_eval.py's live half against url, as make eval-live runs it: every golden row asked as the member, the
    isolation rows as the outsider too, every verdict into report. Its output streams to this terminal; its exit code
    comes back (0 every threshold met, 1 blocked, 2 a leak, or a refusal to start). With GATE_PROMPT=1 the candidate's
    prompt is held to lesson 3.6's registry first (prompt_gate()), and one that is not a registered version stops here,
    before any row is asked."""
    if os.environ.get("GATE_PROMPT") == "1":
        prompt_gate(url, member)
    env = dict(os.environ, DOCUMIND_ID_TOKEN=member, DOCUMIND_OUTSIDER_TOKEN=outsider)
    sys.stdout.flush()
    try:
        return subprocess.run([sys.executable, str(KIT / "evals" / "run_eval.py"), "--api-url", url, "--report",
                               str(report)], cwd=KIT, env=env, stdin=subprocess.DEVNULL).returncode
    except OSError as e:
        raise Stop(f"evals/run_eval.py could not run: {e}") from e


# The candidate's prompt, held to lesson 3.6's registry (13 October 2026). Off unless GATE_PROMPT=1 is in the
# environment (make gate ... GATE_PROMPT=1 exports it to the recipe), because it can refuse a release. It runs where
# the rows would start, so the earlier record is already gone when it refuses, as for a gate stopped mid-rows.
PROMPT_RULES = "services/rag-api/prompt_rules.json"      # lesson 12.4's versions: rules appended to SYSTEM


def _prompt_pin():
    """commands/prompt_pin.py, loaded by path when GATE_PROMPT=1 asks for it: make prompt-version's own readers of
    SYSTEM + DATED_RULE, config.py's label and the registry."""
    spec = importlib.util.spec_from_file_location("prompt_pin_gate", HERE / "prompt_pin.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(kit: Path, *args: str) -> subprocess.CompletedProcess:
    """One read-only git command in the kit's directory, its output captured."""
    try:
        return subprocess.run(["git", "--no-pager", *args], cwd=kit, capture_output=True, text=True, encoding="utf-8",
                              errors="replace", stdin=subprocess.DEVNULL, timeout=60)
    except (OSError, subprocess.SubprocessError) as e:
        raise Stop(f"git could not run in {kit}: {e}") from e


def prompt_reasons(sha: str, served: str, kit: Path | None = None) -> list[str]:
    """Why the prompt a candidate answers under is not a registered version, read from the commit its GIT_SHA names
    (git show, in this checkout): [] when it is. `served` is GET /version's "prompt", prompt_id@version. That commit's
    files decide what the label serves, as prompt_rules.py decides it at import: a version prompt_rules.json lists with
    rules of its own (lesson 12.4) serves SYSTEM and those rules, so SYSTEM + DATED_RULE must be the text config.py's
    label is registered to, make prompt-version's verdict at that commit; any other version serves SYSTEM +
    DATED_RULE as they stand, so its own label must be registered to their sha256. The image is the commit's only as
    far as make build's upload was: commit a prompt before you build it."""
    pp, kit = _prompt_pin(), KIT if kit is None else kit
    if not served:
        return ["GET /version names no prompt"]
    if not re.fullmatch(r"[0-9a-f]{7,40}", sha):
        return [f"GIT_SHA {sha!r} names no commit"]
    if _git(kit, "rev-parse", "--verify", "--quiet", f"{sha}^{{commit}}").returncode:
        return [f"this checkout holds no commit {sha}: fetch it, or gate from the clone that built the image"]
    texts = {}
    for rel in (pp.GENERATOR, pp.CONFIG, pp.REGISTRY, PROMPT_RULES):
        shown_file = _git(kit, "show", f"{sha}:./{rel}")
        texts[rel] = shown_file.stdout if shown_file.returncode == 0 else None
    missing = [rel for rel in (pp.GENERATOR, pp.CONFIG, pp.REGISTRY) if texts[rel] is None]
    if missing:
        return [f"commit {sha} has no {', '.join(missing)}"]
    try:
        text, label = pp.prompt_text(texts[pp.GENERATOR]), pp.label(texts[pp.CONFIG])
        versions = pp.registry(texts[pp.REGISTRY])
        rules = json.loads(texts[PROMPT_RULES]).get("versions") if texts[PROMPT_RULES] is not None else {}
    except pp.Unreadable as e:
        return [f"at {sha}, {e}"]
    except (ValueError, AttributeError):
        return [f"at {sha}, {PROMPT_RULES} is not a rules file prompt_rules.py reads"]
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    prompt_id = label.split("@", 1)[0]
    version = served.split("@", 1)[1] if served.startswith(f"{prompt_id}@") else ""
    entry = rules.get(version) if isinstance(rules, dict) else None
    added = entry.get("rules") if isinstance(entry, dict) else None
    if added:
        why = []
        if served in versions:
            why.append(f"{served} is a rules version in {PROMPT_RULES} and registered in {pp.REGISTRY} as well: "
                       "one label, two texts")
        if versions.get(label) != digest:
            why.append(f"{served} serves SYSTEM and {count(len(added), 'rule')} of {PROMPT_RULES}, and SYSTEM + "
                       f"DATED_RULE (sha256 {digest[:12]}...) is not the text {label} is registered to: make "
                       "prompt-version at that commit says why")
        return why
    if served not in versions:
        return [f"{served} is not registered in {pp.REGISTRY}, and SYSTEM + DATED_RULE hash to {digest[:12]}...: "
                "register the label, or answer under the one that text is registered to"]
    if versions[served] != digest:
        return [f"{served} is registered to sha256 {versions[served][:12]}..., and SYSTEM + DATED_RULE hash to "
                f"{digest[:12]}...: the text changed and the version did not"]
    return []


def prompt_gate(url: str, member: str, kit: Path | None = None) -> None:
    """GATE_PROMPT=1's check, where the rows would start: the prompt the tag URL answers under (GET /version, as the
    member) held to the registry of the commit its GIT_SHA names (prompt_reasons()). Stops the gate when it is not a
    registered version; prints the label it passed otherwise."""
    answers = get_version(url, member)
    sha, served = str(answers.get("git_sha") or ""), str(answers.get("prompt") or "")
    why = prompt_reasons(sha, served, kit)
    if why:
        raise Stop(f"GATE_PROMPT=1: the candidate answers as {served or 'no prompt'} at GIT_SHA {sha or '?'}, which is "
                   f"not a registered prompt version: {'; '.join(why)}. No row was asked and there is no gate record "
                   "(lesson 3.6: a changed prompt is a new version, registered in services/rag-api/prompt_versions.json)")
    print(f">> prompt: {served} at GIT_SHA {sha} is a registered version (GATE_PROMPT=1, "
          "services/rag-api/prompt_versions.json at that commit)")


def report_blocked(report) -> list[str]:
    """What blocked a run, read from the report evals/run_eval.py --report wrote, by the rules its live() exits 0 by: no
    threshold missed, no leak, no version row citing a retired figure, no required row failed; and over every row,
    since a gate is never scoped with --source. [] is green."""
    if not isinstance(report, dict) or not all(key in report for key in ("rows", "scores", "thresholds", "failed")):
        return ["not a report evals/run_eval.py --report writes"]

    def pct(v):
        return f"{v:.0%}" if isinstance(v, (int, float)) else "?"
    scores, thresholds = report.get("scores") or {}, report.get("thresholds") or {}
    blocked = [f"scoped to {report['source']}: a gate asks every row"] if report.get("source") is not None else []
    blocked += [f"{k}: {pct(scores.get(k))} < {pct(thresholds.get(k))}" for k in report.get("failed") or []]
    if report.get("leaks"):
        blocked.append(f"leaks: {count(len(report['leaks']), 'must_not_contain hit')}")
    if report.get("stale"):
        blocked.append("stale: a version row cited a retired figure")
    if report.get("required_failed"):
        blocked.append(f"required: {count(len(report['required_failed']), 'mandatory row')} did not pass")
    return blocked


def write_record(path: Path, record: dict) -> None:
    """The record, whole or not at all: written beside itself, then renamed over the old one."""
    path.parent.mkdir(parents=True, exist_ok=True)
    part = path.with_name(path.name + ".part")
    with open(part, "w", encoding="utf-8", newline="\n") as f:
        json.dump(record, f, indent=1)
        f.write("\n")
    os.replace(part, path)


def cmd_gate(a) -> int:
    project, region = lane_of(a)
    gate_file, candidate_file = gate_paths(a)
    revision = recorded_candidate(candidate_file)
    service = describe_api(project, region)
    _, tagged = traffic_of(service)
    if tagged != revision:
        raise Stop(f"the candidate tag is on {tagged or 'no revision'}, but {shown(candidate_file)} names {revision}: "
                   "the tag URL would answer from a revision make promote would not move traffic to. make "
                   "release-candidate (or make candidate) again, so the two name one revision")
    facts = dict(revision_facts(project, region, revision), image=deployed_image(service, revision))
    why = unjudgeable(facts)
    if why:
        raise Stop(f"{revision} cannot be gated: {'; '.join(why)}")
    number = project_number(project)
    audience = f"https://{SERVICE}-{number}.{region}.run.app"      # the token's audience, whichever URL is called (F42)
    url = f"https://candidate---{SERVICE}-{number}.{region}.run.app"
    member = os.environ.get("DOCUMIND_ID_TOKEN") or identity_token(project, MEMBER_SA, audience)
    answers = get_version(url, member)
    if answers.get("git_sha") != facts["git_sha"]:
        raise Stop(f"{url} answers as git_sha {answers.get('git_sha')!r}, but {revision} carries GIT_SHA "
                   f"{facts['git_sha']}: the tag URL is not serving the revision this gate would record")
    outsider = os.environ.get("DOCUMIND_OUTSIDER_TOKEN") or identity_token(project, OUTSIDER_SA, audience)
    rules = rules_now()
    report = gate_file.parent / f"gate-{revision}.json"
    print(f">> gate: {revision}, the revision {shown(candidate_file)} names and the candidate tag routes to")
    print(f"   image   {facts['image']}")
    print(f"   digest  {facts['digest']}")
    print(f"   GET /version on {url}: git_sha {facts['git_sha']}, {answers.get('generator_model', '?')}, "
          f"{answers.get('prompt', '?')}")
    print(f">> every golden row, asked of that URL by evals/run_eval.py; the report: {shown(report)}")
    for old in (gate_file, report):        # from here, an earlier verdict must not stand for this gate's
        try:
            old.unlink()
        except FileNotFoundError:
            pass
        except OSError as e:
            raise Stop(f"cannot remove {old}: {e}") from e
    started = now()
    try:
        rc = live_gate(url, report, member, outsider)
    except KeyboardInterrupt:
        raise Stop("interrupted while the rows were asked: no gate record") from None
    finished = now()
    if not report.is_file():
        raise Stop(f"evals/run_eval.py wrote no report (exit {rc}): there is no verdict, and no gate record")
    _, after = service_traffic(project, region)
    if after != revision:
        raise Stop(f"the candidate tag moved to {after or 'no revision'} while the rows were asked, so the answers may "
                   "have come from more than one revision: no gate record. make gate again")
    body = report.read_bytes()
    try:
        data = json.loads(body.decode("utf-8"))
    except ValueError:
        data = None
    blocked = report_blocked(data) or ([f"evals/run_eval.py exited {rc}"] if rc else [])
    verdict = "fail" if blocked else "pass"                   # green: exit 0, and nothing in the report blocked it
    data, report_sha256 = data if isinstance(data, dict) else {}, hashlib.sha256(body).hexdigest()
    write_record(gate_file, {
        "format": GATE_FORMAT, "project": project, "region": region, "service": SERVICE, "revision": revision,
        "image": facts["image"], "digest": facts["digest"], "git_sha": facts["git_sha"], "url": url,
        "answers_as": answers, "report": shown(report), "report_sha256": report_sha256,
        "eval_exit": rc, "verdict": verdict, "blocked": blocked, "rows": data.get("rows"),
        "scores": data.get("scores"), "thresholds": data.get("thresholds"), "rules": rules,
        "started": stamp(started), "finished": stamp(finished)})
    print(f">> gate record: {shown(gate_file)}")
    if verdict == "pass":
        print(f"   {revision}  PASS  {data.get('rows')} rows, eval exit 0, report sha256 {report_sha256}")
        print(f"   make promote-gated moves traffic to it while the record holds: for {MAX_AGE_HOURS:g} hours, under "
              "these rules, while it is the recorded candidate")
        return 0
    print(f"   {revision}  FAIL  {'; '.join(blocked)}")
    print("   make promote-gated refuses it (make promote reads no record)")
    return REFUSED


def load_record(path: Path) -> tuple[dict | None, str]:
    """(the gate record, '') or (None, why it is not one)."""
    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return None, f"there is no gate record at {shown(path)}: make gate judges the candidate and writes it"
    except OSError as e:
        raise Stop(f"cannot read {path}: {e}") from e
    try:
        record = json.loads(text)
    except ValueError:
        return None, f"{shown(path)} is not JSON"
    if not isinstance(record, dict) or record.get("format") != GATE_FORMAT:
        return None, f"{shown(path)} is not a gate record ({GATE_FORMAT}, which make gate writes)"
    missing = [key for key in RECORD_FIELDS if key not in record]
    if missing:
        return None, f"{shown(path)} has no {', '.join(missing)}"
    if not REVISION.fullmatch(str(record["revision"])):
        return None, f"{shown(path)} names no {SERVICE} revision"
    return record, ""


def offline_reasons(record: dict, project: str, region: str, candidate_file: Path, max_hours: float) -> list[str]:
    """Why the record does not let make promote move traffic, from the files alone: [] when it does."""
    reasons, rev = [], record["revision"]
    if (record["project"], record["region"], record["service"]) != (project, region, SERVICE):
        reasons.append(f"another lane: the record is of {record['service']} in {record['project']}, "
                       f"{record['region']}; this is {SERVICE} in {project}, {region}")
    try:
        candidate = recorded_candidate(candidate_file)
    except Stop as e:
        reasons.append(str(e))
    else:
        if candidate != rev:
            reasons.append(f"another revision: the record names {rev}, and make promote would move traffic to "
                           f"{candidate} ({shown(candidate_file)}). The gate judged {rev}; make gate judges "
                           f"{candidate}")
    if record["verdict"] != "pass" or record["eval_exit"] != 0:
        what = "; ".join(str(b) for b in record.get("blocked") or []) or f"eval exit {record['eval_exit']}"
        reasons.append(f"red: the gate judged {rev} red ({what})")
    report = located(str(record["report"]))
    try:
        body = report.read_bytes()
    except OSError:
        reasons.append(f"the report {record['report']} is missing, so the record cannot be checked against it")
    else:
        if hashlib.sha256(body).hexdigest() != record["report_sha256"]:
            reasons.append(f"the report {record['report']} changed after the gate: its sha256 is not the record's")
        else:
            try:
                blocked = report_blocked(json.loads(body.decode("utf-8")))
            except ValueError:
                blocked = ["not JSON"]
            if record["verdict"] == "pass" and blocked:
                reasons.append(f"the record says pass, and its report does not: {'; '.join(blocked)}")
    finished = read_stamp(record["finished"])
    if finished is None:
        reasons.append(f"the record's time, {record['finished']!r}, is not a UTC time make gate writes")
    else:
        age = now() - finished
        if age < -SKEW:
            reasons.append(f"the record's time, {record['finished']}, is in the future: it was not written by make "
                           "gate on this clock")
        elif age > datetime.timedelta(hours=max_hours):
            reasons.append(f"stale: the gate finished {age.total_seconds() / 3600:.1f} hours ago "
                           f"({record['finished']}), and a verdict holds for {max_hours:g}: the lane's documents, "
                           "rosters and the model's answers may have moved since. make gate again")
    rules, current = record["rules"] if isinstance(record["rules"], dict) else {}, rules_now()
    changed = [rel for rel in RULES if rules.get(rel) != current[rel]]
    if changed:
        reasons.append(f"stale: {', '.join(changed)} changed since the gate, which judged by other rules than this "
                       "checkout's. make gate again")
    return reasons


def live_reasons(record: dict, project: str, region: str) -> list[str]:
    """Why the lane, as it is now, does not match the record: [] when it does."""
    reasons, rev = [], record["revision"]
    _, tagged = service_traffic(project, region)
    if tagged and tagged != rev:
        reasons.append(f"the candidate tag is on {tagged}, not on {rev}: a newer candidate superseded the one the gate "
                       "judged (make promote refuses this too)")
    facts = revision_facts(project, region, rev)
    if (facts["digest"], facts["git_sha"]) != (record["digest"], record["git_sha"]):
        reasons.append(f"{rev} is not what the gate judged: Cloud Run says {facts['digest']} with GIT_SHA "
                       f"{facts['git_sha']}, the record {record['digest']} with GIT_SHA {record['git_sha']}")
    if not facts["ready"]:
        reasons.append(f"{rev} is not Ready")
    return reasons


def cmd_gate_check(a) -> int:
    project, region = lane_of(a)
    if not a.max_age_hours > 0:
        raise Stop("--max-age-hours must be more than 0")
    gate_file, candidate_file = gate_paths(a)
    record, problem = load_record(gate_file)
    reasons = [problem] if problem else offline_reasons(record, project, region, candidate_file, a.max_age_hours)
    if not reasons:                         # the files agree: now the lane
        reasons = live_reasons(record, project, region)
    if reasons:
        sys.stdout.flush()
        print(f"REFUSED: the gate record {shown(gate_file)} does not let make promote move traffic:", file=sys.stderr)
        for reason in reasons:
            print(f"  - {reason}", file=sys.stderr)
        return REFUSED
    age = (now() - read_stamp(record["finished"])).total_seconds() / 3600
    print(f"gate record {shown(gate_file)}: {record['revision']} passed at {record['finished']}, {age:.1f} hours ago")
    print(f"  digest  {record['digest']}  GIT_SHA {record['git_sha']}")
    print(f"  report  {record['report']}  sha256 {record['report_sha256']}")
    print(f"  {shown(candidate_file)} names it and the candidate tag is not on another revision; judged by this "
          "checkout's " + ", ".join(RULES))
    return 0


# ---------------------------------------------------------------- smoke-deployed and incident (lesson 11.3)

# smoke-all's smokes, in its order, each with the Cloud Run services its make target calls: the URLs its recipe sets.
# smoke-all's loop also hands every smoke the API's URL, and smoke.py (make smoke) reads that alone.
SMOKES = (("smoke", ("documind-api",)), ("smoke-mcp", ("documind-mcp",)), ("smoke-chat", ("documind-chat",)),
          ("smoke-agent", ("documind-agent",)), ("smoke-media", ("documind-api", "documind-mcp")),
          ("smoke-reindex", ("documind-api",)), ("smoke-gateway", ("documind-gateway",)),
          ("smoke-slm", ("documind-slm", "documind-gateway")))
IN_SLM_REGION = ("documind-slm",)        # make deploy-slm runs it in SLM_REGION; every other service runs in REGION
SLM_REGION_DEFAULT = "us-central1"       # the Makefile's SLM_REGION: Cloud Run's L4 in asia-south1 is invitation-only
SMOKE_LINE = re.compile(r"PASS|FAIL|pass|fail|not set")      # the lines smoke-all's grep keeps
SMOKE_FORMAT = "documind-smoke/1"
RED = 1                                  # a smoke failed, or the lane is not in the gated state


def makefile_text() -> str:
    try:
        return (KIT / "Makefile").read_text(encoding="utf-8")
    except OSError as e:
        raise Stop(f"cannot read the kit's Makefile: {e}") from e


def recipe_of(text: str, target: str) -> str:
    """A target's recipe in the Makefile, its tab-indented lines as one text ('' when there is no such rule)."""
    rule = re.search(rf"^{re.escape(target)}:[^\n]*\n((?:\t[^\n]*\n)+)", text, re.M)
    return rule.group(1) if rule else ""


def smoke_all_targets(text: str) -> list[str]:
    """The smokes make smoke-all runs, in its order: its recipe's for loop."""
    loop = re.search(r"\bfor t in ([a-z0-9 -]+); do\b", recipe_of(text, "smoke-all"))
    if not loop:
        raise Stop("the kit's Makefile has no smoke-all loop (for t in ...; do) to read its smokes from")
    return loop.group(1).split()


def candidate_settings(text: str) -> dict:
    """{env var: the Makefile's default, or None where it has none} for each setting make candidate passes as an env
    var of the same name (its recipe): a candidate that should carry what serves names those that differ from the
    default. PROJECT and REGION, which the recipe's record-candidate line passes the same way, name the lane and are
    no setting of the revision (13 October 2026)."""
    names = dict.fromkeys(name for name in re.findall(r"\b([A-Z][A-Z0-9_]*)=\$\(\1\)", recipe_of(text, "candidate"))
                          if name not in ("PROJECT", "REGION"))
    found = {}
    for name in names:
        default = re.search(rf"^{name}[ \t]*\?=[ \t]*(.*?)[ \t]*$", text, re.M)
        found[name] = default.group(1) if default else None
    return found


def deployed_services(project: str, region: str, slm_region: str) -> set:
    """The Cloud Run services this lane has deployed: every one in REGION, and documind-slm in SLM_REGION."""
    found = set()
    for where in dict.fromkeys((region, slm_region)):
        data = read_json(["gcloud", "run", "services", "list", f"--region={where}", f"--project={project}",
                          "--format=json"])
        if not isinstance(data, list):
            raise Stop(f"gcloud run services list in {where} did not return a list")
        for service in data:
            meta = service.get("metadata") if isinstance(service, dict) else None
            name = str(meta.get("name") or "") if isinstance(meta, dict) else ""
            if name and where == (slm_region if name in IN_SLM_REGION else region):
                found.add(name)
    return found


def choose_smokes(deployed: set) -> tuple[list, dict]:
    """(smoke-all's smokes whose services are all deployed, in its order; {each other smoke: the services it lacks})."""
    chosen, skipped = [], {}
    for target, needs in SMOKES:
        missing = [name for name in needs if name not in deployed]
        if missing:
            skipped[target] = missing
        else:
            chosen.append(target)
    return chosen, skipped


def run_smoke(make: str, target: str, variables: list[str], env: dict) -> int:
    """make <target>, as smoke-all's loop runs it: its output streamed through that loop's filter, its own exit status
    returned."""
    sys.stdout.flush()
    try:
        child = subprocess.Popen([make, "--no-print-directory", target, *variables], cwd=KIT, env=env,
                                 stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True,
                                 encoding="utf-8", errors="replace")
    except OSError as e:
        raise Stop(f"make {target} could not run: {e}") from e
    with child.stdout:
        for line in child.stdout:
            if SMOKE_LINE.search(line):
                print(line.rstrip("\n"), flush=True)
    return child.wait()


def smoke_log(a) -> Path:
    """The smoke-deployed runs' log: by default the kit's evals/reports/smoke-deployed.jsonl."""
    return (Path(a.log).expanduser() if a.log else KIT / "evals" / "reports" / "smoke-deployed.jsonl").resolve()


def answered(version) -> str:
    """What a GET /version said, in one line."""
    if not isinstance(version, dict) or "error" in version:
        return f"no answer ({version.get('error') if isinstance(version, dict) else version})"
    return f"git_sha {version.get('git_sha', '?')}, {version.get('generator_model', '?')}, {version.get('prompt', '?')}"


def cmd_smoke_deployed(a) -> int:
    project, region = lane_of(a)
    slm_region = a.slm_region or SLM_REGION_DEFAULT
    if not REGION_NAME.fullmatch(slm_region):
        raise Stop("pass --slm-region with the region documind-slm runs in (SLM_REGION)")
    if not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", a.tenant or ""):
        raise Stop("pass --tenant with the tenant the smokes ask as (TENANT)")
    known, found = [target for target, _ in SMOKES], smoke_all_targets(makefile_text())
    if found != known:
        raise Stop(f"make smoke-all runs {' '.join(found)}, and smoke-deployed knows {' '.join(known)}: change SMOKES "
                   "in commands/release.py with smoke-all, naming the services each smoke's target calls")
    make = shutil.which(a.make)
    if not make:
        raise Stop(f"{a.make} is not on PATH: the smokes are make targets, as smoke-all's are (--make names another)")
    deployed = deployed_services(project, region, slm_region)
    if SERVICE not in deployed:
        raise Stop(f"{SERVICE} is not deployed in {region} ({project}), so there is no lane to smoke there: REGION is "
                   "the region the lane runs in, and the Makefile's default is us-central1")
    chosen, skipped = choose_smokes(deployed)
    url = f"https://{SERVICE}-{project_number(project)}.{region}.run.app"
    serving, tagged = service_traffic(project, region)
    try:
        version = get_version(url, os.environ.get("DOCUMIND_ID_TOKEN") or identity_token(project, MEMBER_SA, url))
    except Stop as e:                    # the smokes still run: what /version could not say is recorded with them
        version = {"error": str(e)}
    log = smoke_log(a)
    print(f">> smoke-deployed: {SERVICE} in {project}, {region}, serving {serving or 'no revision'}")
    print(f"   GET /version: {answered(version)}")
    print(f"   deployed: {', '.join(sorted(deployed))}")
    lacks = [f"{target} ({', '.join(f'{s} in {slm_region}' if s in IN_SLM_REGION else s for s in missing)})"
             for target, missing in skipped.items()]
    print(f">> {len(chosen)} of smoke-all's {len(SMOKES)} smokes" + (f"; skipped, a service not deployed: "
                                                                       f"{'; '.join(lacks)}" if lacks else ""))
    env = dict(os.environ, DOCUMIND_PROJECT=project, DOCUMIND_API_URL=url, DOCUMIND_TENANT=a.tenant,
               DOCUMIND_IMPERSONATE_SA=f"{MEMBER_SA}@{project}.iam.gserviceaccount.com")
    variables = [f"PROJECT={project}", f"REGION={region}", f"SLM_REGION={slm_region}", f"TENANT={a.tenant}"]
    ran, started = {}, now()
    try:
        for target in chosen:
            print(f"== {target}", flush=True)
            ran[target] = run_smoke(make, target, variables, env)
            if ran[target]:
                print(f"== {target}: FAILED (exit {ran[target]})", flush=True)
    except KeyboardInterrupt:
        raise Stop("interrupted during the smokes: nothing recorded") from None
    finished = now()
    try:
        after, _ = service_traffic(project, region)
    except Stop as e:
        after = ""
        print(f">> the traffic table could not be read again after the smokes: {e}")
    failed = [target for target, code in ran.items() if code]
    record = {"format": SMOKE_FORMAT, "project": project, "region": region, "slm_region": slm_region,
              "tenant": a.tenant, "serving": serving, "candidate": tagged, "version": version,
              "deployed": sorted(deployed), "ran": ran, "skipped": skipped, "verdict": "fail" if failed else "pass",
              "started": stamp(started), "finished": stamp(finished)}
    if after and after != serving:
        record["serving_after"] = after
        print(f">> the traffic moved during the smokes, from {serving} to {after}: the results may come from both")
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8", newline="\n") as f:
        f.write(json.dumps(record) + "\n")
    tally = f"{len(ran) - len(failed)} passed, {len(skipped)} skipped. Recorded in {shown(log)}"
    if failed:
        print(f">> FAIL: {', '.join(failed)} failed; {tally}")
        return RED
    print(f">> PASS: {tally}")
    return 0


def lane_time(text) -> datetime.datetime | None:
    """A Cloud Run timestamp (RFC 3339: seconds, a fraction or none, Z or an offset) in UTC, or None."""
    m = re.fullmatch(r"(\d{4}-\d\d-\d\dT\d\d:\d\d:\d\d)(?:\.(\d+))?(Z|[+-]\d\d:\d\d)", str(text or "").strip())
    if not m:
        return None
    zone = datetime.timezone.utc if m[3] == "Z" else datetime.timezone(
        (1 if m[3][0] == "+" else -1) * datetime.timedelta(hours=int(m[3][1:3]), minutes=int(m[3][4:6])))
    t = datetime.datetime.strptime(m[1], "%Y-%m-%dT%H:%M:%S").replace(tzinfo=zone)
    return (t + datetime.timedelta(microseconds=int((m[2] or "0")[:6].ljust(6, "0")))).astimezone(datetime.timezone.utc)


def container_of(spec) -> tuple[str, dict]:
    """(image, env) of the first container of a revision's spec, or of the service's spec.template.spec: env as name ->
    value, a secret as the reference it names."""
    containers = [c for c in (spec.get("containers") if isinstance(spec, dict) else None) or [] if isinstance(c, dict)]
    first = containers[0] if containers else {}
    env = {}
    for e in first.get("env") or []:
        if isinstance(e, dict) and e.get("name"):
            ref = e["valueFrom"].get("secretKeyRef") if isinstance(e.get("valueFrom"), dict) else None
            env[e["name"]] = f"<secret {ref.get('name')}:{ref.get('key')}>" if isinstance(ref, dict) else str(
                e.get("value", ""))
    return str(first.get("image") or ""), env


def image_shown(image) -> str:
    """An image as incident prints it: the last part of its path, a digest cut to 12 hex digits as docker shows one
    (.../documind/api@sha256:a471b9b8a0c3... -> api@sha256:a471b9b8a0c3), a tag as it is (api:66f47aa)."""
    last = str(image or "").rsplit("/", 1)[-1]
    name, at, digest = last.partition("@sha256:")
    return f"{name}@sha256:{digest[:12]}" if at else last


def api_revisions(project: str, region: str) -> dict:
    """documind-api's revisions by name: when each was made, its image (the digest Cloud Run resolved the deploy's tag
    to: a revision never holds the tag) and its env."""
    data = read_json(["gcloud", "run", "revisions", "list", f"--service={SERVICE}", f"--region={region}",
                      f"--project={project}", "--format=json"])
    if not isinstance(data, list):
        raise Stop("gcloud run revisions list did not return a list")
    revisions = {}
    for item in data:
        meta = item.get("metadata") if isinstance(item, dict) else None
        if isinstance(meta, dict) and REVISION.fullmatch(str(meta.get("name") or "")):
            image, env = container_of(item.get("spec"))
            revisions[meta["name"]] = {"name": meta["name"], "created": lane_time(meta.get("creationTimestamp")),
                                       "image": image, "env": env}
    return revisions


def judged(name: str, record: dict | None, gate_file: Path) -> tuple | None:
    """How a gate judged a revision, by this checkout's records: ('pass' or 'fail', the file that says so, what blocked
    it). The gate record when it names the revision, else the revision's own report beside it; None when neither does.
    As the files say: make promote-gated's gate-check is what binds a verdict to the lane."""
    if record and record.get("revision") == name:
        if record.get("verdict") == "pass" and record.get("eval_exit") == 0:
            return "pass", shown(gate_file), []
        return "fail", shown(gate_file), [str(b) for b in record.get("blocked") or []] or [
            f"eval exit {record.get('eval_exit')}"]
    report = gate_file.parent / f"gate-{name}.json"
    try:
        data = json.loads(report.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None
    except (OSError, ValueError):
        data = None
    blocked = report_blocked(data)
    return ("fail" if blocked else "pass"), shown(report), blocked


def judged_line(verdict) -> str:
    if verdict is None:
        return "no gate in this checkout judged it"
    return f"gate: {verdict[0]}" + (f" ({'; '.join(verdict[2])})" if verdict[2] else "") + f", {verdict[1]}"


def smoke_runs(path: Path, project: str, region: str) -> tuple[list, int]:
    """This lane's smoke-deployed runs, in the order they were logged, and how many lines of the log were not one."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except FileNotFoundError:
        return [], 0
    except OSError as e:
        raise Stop(f"cannot read {path}: {e}") from e
    runs, other = [], 0
    for line in filter(str.strip, lines):
        try:
            entry = json.loads(line)
        except ValueError:
            entry = None
        if (isinstance(entry, dict) and entry.get("format") == SMOKE_FORMAT and read_stamp(entry.get("finished"))
                and (entry.get("project"), entry.get("region")) == (project, region)):
            runs.append(entry)
        else:
            other += 1
    return runs, other


def smoked_line(entry: dict) -> str:
    ran = entry.get("ran") if isinstance(entry.get("ran"), dict) else {}
    failed = [target for target, code in ran.items() if code]
    line = (f"smoke     {'FAIL' if failed else 'PASS'}  serving {entry.get('serving') or 'no revision'}  /version "
            f"{answered(entry.get('version'))}  " + (f"failed: {', '.join(failed)}; " if failed else "")
            + f"{len(ran) - len(failed)} passed, {len(entry.get('skipped') or {})} skipped")
    if entry.get("serving_after"):
        line += f"; the traffic moved to {entry['serving_after']} during the run"
    return line


def drift(template: tuple, serving: tuple) -> list:
    """(setting, the template's value, the serving revision's value) for each that differs: the image, then each env
    var; None for one that is not set."""
    (t_image, t_env), (s_image, s_env) = template, serving
    found = [("image", t_image, s_image)] if t_image != s_image else []
    return found + [(k, t_env.get(k), s_env.get(k)) for k in sorted(set(t_env) | set(s_env))
                    if t_env.get(k) != s_env.get(k)]


def repair_steps(diffs: list, serving_env: dict, settings: dict, project: str, region: str) -> list[str]:
    """The lines that make a candidate from what serves, then the gate and the gated promote. make release-candidate
    puts the image and GIT_SHA back; make candidate the settings it passes, each one that differs from the Makefile's
    default named (it passes every one, so one left out would go back to the default), and records the candidate; any
    other setting is put back on the template by hand first, with no traffic."""
    drifted = {name for name, _, _ in diffs}
    steps = [f"make release-candidate GIT_SHA={serving_env.get('GIT_SHA') or '<the serving tag>'}"] if (
        drifted & {"image", "GIT_SHA"}) else []
    by_hand = [f"--update-env-vars {shlex.quote(f'{name}={value}')}" if value is not None
               else f"--remove-env-vars {name}" for name, _, value in diffs if name not in ("image", "GIT_SHA")
               and not (name in settings and (value is not None or settings[name] == ""))]
    if by_hand:
        steps.append(f"gcloud run services update {SERVICE} --region {region} --project {project} --no-traffic "
                     + " ".join(by_hand))
    if not drifted or drifted - {"image", "GIT_SHA"}:
        steps.append("make candidate" + "".join(
            f" {name}={shlex.quote(serving_env[name])}" for name, default in settings.items() if name in serving_env
            and (name in drifted or (default is not None and serving_env[name] != default))))
    return steps + ["make gate", "make promote-gated"]


def cmd_incident(a) -> int:
    project, region = lane_of(a)
    if not a.hours > 0:
        raise Stop("--hours must be more than 0")
    gate_file, candidate_file = gate_paths(a)
    log, since = smoke_log(a), now() - datetime.timedelta(hours=a.hours)
    settings = candidate_settings(makefile_text())
    service = describe_api(project, region)
    serving, tagged = traffic_of(service)
    template = container_of(((service.get("spec") or {}).get("template") or {}).get("spec"))
    revisions = api_revisions(project, region)
    # The template keeps the tag a deploy gave it, and each revision the digest Cloud Run resolved that tag to, so a tag
    # never equals what serves (22 October 2026): the template's image is compared as the revision it made holds it.
    made = revisions.get(str((service.get("status") or {}).get("latestCreatedRevisionName") or ""))
    held = (made["image"] if made else template[0], template[1])
    if not serving:
        raise Stop(f"no revision serves {SERVICE}: its traffic table sends no percent anywhere")
    if serving not in revisions:
        raise Stop(f"gcloud run revisions list has no {serving}, which the traffic table says serves {SERVICE}")
    record, problem = load_record(gate_file)
    runs, other = smoke_runs(log, project, region)
    files = {}
    for label, path in ((".candidate-revision", candidate_file), (".previous-revision", KIT / ".previous-revision")):
        try:
            files[label] = path.read_text(encoding="utf-8").strip()
        except FileNotFoundError:
            files[label] = ""
        except OSError as e:
            raise Stop(f"cannot read {path}: {e}") from e

    events = []                          # (time, order, sequence, line)
    for rev in revisions.values():
        if rev["created"] and rev["created"] >= since:
            events.append((rev["created"], 0, 0, f"revision  {rev['name']}  made: {image_shown(rev['image'])}, "
                           f"GENERATOR_MODEL={rev['env'].get('GENERATOR_MODEL', '(unset)')}  "
                           f"{judged_line(judged(rev['name'], record, gate_file))}"))
    finished = read_stamp(record["finished"]) if record else None
    if finished and finished >= since:
        verdict = judged(record["revision"], record, gate_file)
        events.append((finished, 1, 0, f"gate      {record['revision']}  {verdict[0].upper()}"
                       + (f"  {'; '.join(verdict[2])}" if verdict[2] else "") + f"  ({shown(gate_file)})"))
    before = None
    for i, entry in enumerate(runs):
        at = read_stamp(entry["finished"])
        if at >= since:
            was = before and (before.get("serving_after") or before.get("serving"))
            if was and was != entry.get("serving"):
                events.append((at, 2, 2 * i, f"traffic   {was} -> {entry.get('serving')}: seen between the smoke runs "
                                              f"of {before['finished']} and {entry['finished']}"))
            events.append((at, 2, 2 * i + 1, smoked_line(entry)))
        before = entry
    print(f">> {SERVICE} in {project}, {region}: the last {a.hours:g} hours, from the lane and this checkout's records")
    for at, _, _, line in sorted(events, key=lambda e: e[:3]):
        print(f"   {stamp(at)}  {line}")
    if not events:
        print("   no revision made, gate finished or make smoke-deployed run in that time")
    if other:
        print(f"   ({count(other, 'line')} of {shown(log)} not this lane's smoke-deployed runs)")
    if problem and record is None and not problem.startswith("there is no gate record"):
        print(f"   ({problem})")

    serving_verdict = judged(serving, record, gate_file)
    print(">> now")
    print(f"   serving              {serving}  {judged_line(serving_verdict)}")
    print(f"   the candidate tag    {tagged or 'on no revision'}"
          + (f"  {judged_line(judged(tagged, record, gate_file))}" if tagged else ""))
    for label, name in files.items():
        print(f"   {label:<20} {name or 'none in this checkout'}")
    print(f"   spec.template        {template[0].rsplit('/', 1)[-1] or '(no image)'}, "
          f"GENERATOR_MODEL={template[1].get('GENERATOR_MODEL', '(unset)')}")

    reasons, steps = [], []
    serving_env = revisions[serving]["env"]
    if serving_verdict is None:
        reasons.append(f"{serving} serves, and no gate record or gate report in this checkout judged it: make up and "
                       "make deploy-services release the API with no gate")
    elif serving_verdict[0] == "fail":
        reasons.append(f"{serving} serves, and the gate judged it red ({serving_verdict[1]}: "
                       f"{'; '.join(serving_verdict[2])})")
        previous = files[".previous-revision"]
        back = (f"make rollback, which moves traffic back to {previous} (.previous-revision)"
                if previous and previous != serving else f"gcloud run services update-traffic {SERVICE} --region "
                f"{region} --project {project} --to-revisions <a revision the gate judged green>=100")
        steps = [back, "make incident again"]
    diffs = drift(held, (revisions[serving]["image"], serving_env))
    if diffs:
        in_template = image_shown(template[0]) + (f" ({image_shown(held[0])})" if held[0] != template[0] else "")
        reasons.append("spec.template is not what serves: " + "; ".join(
            f"image {in_template} in the template, {image_shown(new)} on {serving}" if name == "image" else
            f"{name} {old if old is not None else '(unset)'} in the template, {new if new is not None else '(unset)'} "
            f"on {serving}" for name, old, new in diffs) + ". make rollback moves traffic and leaves the template as "
            "the last update made it, and make candidate and make release-candidate start from the template (env vars "
            "merge across revisions, F43): the next candidate would carry it")
    candidate = files[".candidate-revision"]
    candidate_verdict = judged(candidate, record, gate_file) if candidate and candidate != serving else None
    if candidate_verdict and candidate_verdict[0] == "fail":
        reasons.append(f".candidate-revision names {candidate}, which the gate judged red ({candidate_verdict[1]}): "
                       "make promote reads no record, and would move traffic to it again")
    if not reasons:
        print(f">> the gated state: {serving} serves, judged green ({serving_verdict[1]}); spec.template is what "
              "serves; no red candidate is recorded")
        return 0
    print(">> not the gated state:")
    for reason in reasons:
        print(f"   - {reason}")
    if not steps:
        steps = repair_steps(diffs, serving_env, settings, project, region)
        flight = revisions.get(candidate)
        if (diffs and flight and candidate != serving and not (candidate_verdict and candidate_verdict[0] == "fail")
                and not drift(held, (flight["image"], flight["env"]))):
            print(f"   If {candidate}, the recorded candidate and what spec.template holds, is the change you mean to "
                  "release: " + ("make promote-gated" if candidate_verdict else "make gate, then make promote-gated")
                  + ". Otherwise put the template back to what serves:")
    print("   Repair: " + "; then ".join(steps))
    return RED


# ---------------------------------------------------------------- the command line

def build_parser() -> argparse.ArgumentParser:
    lines = __doc__.splitlines()
    ap = argparse.ArgumentParser(prog="release.py", description=lines[0], epilog="\n".join(lines[2:]),
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    lane = argparse.ArgumentParser(add_help=False)
    lane.add_argument("--project", default=os.environ.get("PROJECT") or "", help="the lane's project id (PROJECT)")
    sub = ap.add_subparsers(dest="cmd", required=True)
    c = sub.add_parser("ci-vars", parents=[lane], help="the gh variable set lines documind-cd.yml needs (make ci-vars)")
    c.add_argument("--region", default=os.environ.get("REGION") or "",
                   help="the lane's region (REGION); empty takes the one the lane was planned in")
    c.add_argument("--terraform-dir", default=str(KIT / "terraform"), help="the lane's terraform/ (default: the kit's)")
    c.add_argument("--workflow", default=str(WORKFLOW), help="the CD workflow (default: the kit's documind-cd.yml)")
    c.set_defaults(fn=cmd_ci_vars)
    k = sub.add_parser("keys", parents=[lane], help="every service account's user-managed keys (make keys-check)")
    k.set_defaults(fn=cmd_keys)
    gated = argparse.ArgumentParser(add_help=False)
    gated.add_argument("--region", default=os.environ.get("REGION") or "",
                       help="the region documind-api runs in (REGION)")
    gated.add_argument("--gate-file", default="", help="the gate record (default: the kit's evals/reports/gate.json)")
    gated.add_argument("--candidate-file", default="",
                       help="the revision make promote moves traffic to (default: the kit's .candidate-revision)")
    g = sub.add_parser("gate", parents=[lane, gated],
                       help="the live gate on the recorded candidate, and its record (make gate)")
    g.set_defaults(fn=cmd_gate)
    gc = sub.add_parser("gate-check", parents=[lane, gated],
                        help="whether the gate record lets make promote move traffic (make promote-gated)")
    gc.add_argument("--max-age-hours", type=float, default=MAX_AGE_HOURS,
                    help=f"how long a verdict holds (default {MAX_AGE_HOURS:g})")
    gc.set_defaults(fn=cmd_gate_check)
    log = argparse.ArgumentParser(add_help=False)
    log.add_argument("--log", default="", help="the smoke-deployed runs' log (default: the kit's "
                                               "evals/reports/smoke-deployed.jsonl)")
    s = sub.add_parser("smoke-deployed", parents=[lane, log],
                       help="the smokes of the services this lane has deployed (make smoke-deployed)")
    s.add_argument("--region", default=os.environ.get("REGION") or "", help="the region the lane runs in (REGION)")
    s.add_argument("--slm-region", default=os.environ.get("SLM_REGION") or "",
                   help=f"the region documind-slm runs in (SLM_REGION; default {SLM_REGION_DEFAULT}, the Makefile's)")
    s.add_argument("--tenant", default=os.environ.get("TENANT") or "acme", help="the tenant the smokes ask as (TENANT)")
    s.add_argument("--make", default="make", help="the make that runs the smokes (default: make on PATH)")
    s.set_defaults(fn=cmd_smoke_deployed)
    i = sub.add_parser("incident", parents=[lane, gated, log],
                       help="the incident's timeline, and whether the lane is in the gated state (make incident)")
    i.add_argument("--hours", type=float, default=24.0, help="how far back the timeline goes (default 24)")
    i.set_defaults(fn=cmd_incident)
    return ap


def main(argv: list[str] | None = None) -> int:
    a = build_parser().parse_args(argv)
    try:
        return int(a.fn(a) or 0)
    except (Stop, infra.Stop) as e:
        sys.stdout.flush()
        print(f"STOP: {e}", file=sys.stderr)
        return STOPPED


if __name__ == "__main__":
    sys.exit(main())
