"""Offline tests of commands/release.py (lesson 11.1): make ci-vars and make keys-check against stub gcloud, gh and
terraform executables. Nothing reaches Google Cloud or GitHub.

Each stub is one Python script behind a wrapper per tool: a /bin/sh script on Linux and macOS, a .cmd file on Windows,
where release.py finds it as it finds the real gcloud.cmd, through PATH and PATHEXT. PATH holds the stub directory and
nothing else, so a tool a test removes is a missing tool, never the real one. The stubs answer from a scenario file the
test writes, and record every call, which the tests read back: what was asked, with which flags, from which directory,
and that nothing but terraform output, gcloud's describe and list calls, and one GET through gh was asked.

Covered: ci-vars' four lines from terraform output and the lane's confirmed inputs, the workflow's variable names, the
production environment's reviewer (present, missing, no environment, a gh that cannot read it, no gh), every refusal
(another region, another project, another lane's state, no state, no outputs, no confirmed inputs, a workflow that reads
other variables, no terraform); keys with none, with keys found and then deleted, an account that could not be read, the project's parent,
no gcloud; the exit codes (0, 1 keys found, 2 stopped); and the make targets, the .PHONY line and mk/README.md.
"""
import copy
import importlib.util
import json
import os
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
RELEASE = KIT / "commands" / "release.py"
spec = importlib.util.spec_from_file_location("release", RELEASE)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

PROJECT, NUMBER, REGION = "documind-course-demo", "123456789012", "asia-south1"
REPO, REPO_ID = "example-learner/agents-workshop-fork", "987654321"
PROVIDER = f"projects/{NUMBER}/locations/global/workloadIdentityPools/documind-github/providers/github-oidc"
CICD = f"sa-documind-cicd@{PROJECT}.iam.gserviceaccount.com"
API_SA, UI_SA = f"documind-api-sa@{PROJECT}.iam.gserviceaccount.com", f"documind-ui-sa@{PROJECT}.iam.gserviceaccount.com"
SECRET = "postgresql://litellm:not-a-real-password@localhost/litellm?host=/cloudsql/x"   # a sensitive output
INPUTS = {"project_id": PROJECT, "region": REGION, "billing_account_id": "ABCDEF-123456-A1B2C3",
          "github_repository": REPO, "github_repository_id": REPO_ID, "deploy_ref": "refs/heads/main"}
ENVIRONMENT = f"repos/{REPO}/environments/production"
REVIEWED = {"name": "production", "protection_rules": [
    {"type": "required_reviewers", "reviewers": [{"type": "User", "reviewer": {"login": "example-learner"}}]},
    {"type": "branch_policy"}]}
WORLD = {
    "terraform": {"outputs": {"wif_provider": PROVIDER, "cicd_service_account": CICD, "gateway_database_url": SECRET,
                              "docai_location": "us"}},
    "gh": {ENVIRONMENT: REVIEWED},
    "project": {"projectId": PROJECT, "projectNumber": NUMBER, "lifecycleState": "ACTIVE"},
    "accounts": [UI_SA, CICD, API_SA],
    "keys": {},
    "unreadable": {},
}


def user_key(email: str, key_id: str, **extra) -> dict:
    return {"name": f"projects/{PROJECT}/serviceAccounts/{email}/keys/{key_id}", "keyType": "USER_MANAGED",
            "keyOrigin": "GOOGLE_PROVIDED", "keyAlgorithm": "KEY_ALG_RSA_2048", "validAfterTime": "2026-10-26T09:14:02Z",
            "validBeforeTime": "9999-12-31T23:59:59Z", **extra}


# One script plays all three tools: argv[1] is the tool, the rest its arguments. Every account also holds a
# Google-managed key, which gcloud lists unless --managed-by=user filters it out.
STUB = r'''
import json, os, sys, time

tool, args = sys.argv[1], sys.argv[2:]
home = os.environ["RELEASE_STUB_HOME"]
with open(os.path.join(home, "calls", "%d-%d.json" % (time.time_ns(), os.getpid())), "w", encoding="utf-8") as log:
    json.dump({"tool": tool, "args": args, "cwd": os.getcwd()}, log)
with open(os.path.join(home, "scenario.json"), encoding="utf-8") as f:
    world = json.load(f)
project = world["project"]["projectId"]


def reply(out=None, code=0, err=""):
    if out is not None:
        sys.stdout.write(out if isinstance(out, str) else json.dumps(out))
    if err:
        sys.stderr.write(err + "\n")
    sys.exit(code)


def flag(name):
    return next((a.split("=", 1)[1] for a in args if a.startswith(name + "=")), None)


if tool == "terraform" and args == ["output", "-json"]:
    tf = world["terraform"]
    if tf.get("error"):
        reply(None, 1, tf["error"])
    reply({name: {"sensitive": name == "gateway_database_url", "type": "string", "value": value}
           for name, value in tf["outputs"].items()})
if tool == "gh" and len(args) == 2 and args[0] == "api":
    if world.get("gh_error"):
        reply(None, 4, world["gh_error"])
    if args[1] in world["gh"]:
        reply(world["gh"][args[1]])
    reply('{"message":"Not Found","documentation_url":"https://docs.github.com/rest","status":"404"}', 1,
          "gh: Not Found (HTTP 404)")
if tool == "gcloud" and args[:2] == ["projects", "describe"] and args[3:] == ["--format=json"]:
    if args[2] == project:
        reply(world["project"])
    reply(None, 1, "ERROR: (gcloud.projects.describe) NOT_FOUND: project " + args[2])
if tool == "gcloud" and args[:3] == ["iam", "service-accounts", "list"] and sorted(args[3:]) == sorted(
        ["--project=" + project, "--format=json"]):
    reply([{"email": e, "displayName": e.split("@")[0], "projectId": project} for e in world["accounts"]])
if (tool == "gcloud" and args[:4] == ["iam", "service-accounts", "keys", "list"] and flag("--format") == "json"
        and flag("--project") == project and flag("--iam-account") in world["accounts"]):
    email, managed = flag("--iam-account"), flag("--managed-by")
    if email in world["unreadable"]:
        reply(None, 1, world["unreadable"][email])
    system = {"name": "projects/%s/serviceAccounts/%s/keys/google-held" % (project, email), "keyType": "SYSTEM_MANAGED",
              "validAfterTime": "2026-10-01T00:00:00Z", "validBeforeTime": "2026-10-17T00:00:00Z"}
    keys = world["keys"].get(email, []) + [system]
    wanted = {"user": ["USER_MANAGED"], "system": ["SYSTEM_MANAGED"]}.get(managed, ["USER_MANAGED", "SYSTEM_MANAGED"])
    reply([k for k in keys if k["keyType"] in wanted])
reply(None, 99, "stub: unexpected call: " + " ".join([tool] + args))
'''


class Stubbed(unittest.TestCase):
    """A temporary home with the stubs on PATH, a scenario, and the lane's terraform/ with its confirmed inputs."""

    def setUp(self):
        self.home = Path(tempfile.mkdtemp(prefix="release_test_"))
        self.addCleanup(shutil.rmtree, self.home, True)
        self.bin, self.tf = self.home / "bin", self.home / "terraform"
        for d in (self.bin, self.tf, self.home / "calls"):
            d.mkdir()
        (self.home / "stub.py").write_text(STUB, encoding="utf-8")
        for tool in ("gcloud", "gh", "terraform"):
            self.install(tool)
        self.world = copy.deepcopy(WORLD)
        self.save_inputs(INPUTS)

    def install(self, tool: str) -> None:
        stub = self.home / "stub.py"
        if os.name == "nt":                                                 # text mode writes CRLF here
            (self.bin / f"{tool}.cmd").write_text(f'@echo off\n"{sys.executable}" "{stub}" {tool} %*\nexit /b %errorlevel%\n',
                                                  encoding="utf-8")
        else:
            path = self.bin / tool
            path.write_text(f"#!/bin/sh\nexec {shlex.quote(sys.executable)} {shlex.quote(str(stub))} {tool} \"$@\"\n",
                            encoding="utf-8")
            path.chmod(0o755)

    def uninstall(self, tool: str) -> None:
        for path in self.bin.glob(tool + "*"):
            path.unlink()

    def save_inputs(self, inputs: dict) -> None:
        (self.tf / release.infra.INPUT_FILE).write_text(json.dumps(inputs), encoding="utf-8")

    def release(self, *args: str) -> subprocess.CompletedProcess:
        (self.home / "scenario.json").write_text(json.dumps(self.world), encoding="utf-8")
        env = {"PATH": str(self.bin), "RELEASE_STUB_HOME": str(self.home), "PYTHONIOENCODING": "utf-8",
               "HOME": str(self.home), "USERPROFILE": str(self.home), "APPDATA": str(self.home),
               "CLOUDSDK_CONFIG": str(self.home / "gcloud")}
        for key in ("SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR", "TEMP", "TMP"):    # what Windows itself needs
            if key in os.environ:
                env[key] = os.environ[key]
        return subprocess.run([sys.executable, str(RELEASE), *args], cwd=str(self.home), env=env, capture_output=True,
                              text=True, encoding="utf-8", errors="replace", timeout=180)

    def ci_vars(self, *extra: str) -> subprocess.CompletedProcess:
        return self.release("ci-vars", "--project", PROJECT, "--region", REGION, "--terraform-dir", str(self.tf), *extra)

    def keys(self) -> subprocess.CompletedProcess:
        return self.release("keys", "--project", PROJECT)

    def calls(self) -> list:
        return [json.loads(p.read_text(encoding="utf-8")) for p in sorted((self.home / "calls").glob("*.json"))]

    def assert_read_only(self) -> None:
        """terraform output -json, gcloud describe and list, and a two-word gh api call (a GET): nothing else."""
        for call in self.calls():
            tool, args = call["tool"], call["args"]
            words = [a for a in args if not a.startswith("-")]
            if tool == "terraform":
                self.assertEqual(args, ["output", "-json"])
            elif tool == "gh":
                self.assertEqual((len(args), args[0]), (2, "api"), args)
            else:
                self.assertTrue(words[:2] == ["projects", "describe"] or words[-1] == "list", args)

    def gh_lines(self, out: str) -> list:
        return [line for line in out.splitlines() if line.startswith("gh variable set ")]


class CiVarsTests(Stubbed):
    def test_the_four_lines_from_terraform_output_and_the_confirmed_inputs(self):
        r = self.ci_vars()
        self.assertEqual((r.returncode, r.stderr), (0, ""), r.stdout + r.stderr)
        want = {"GCP_PROJECT": PROJECT, "GCP_REGION": REGION, "WIF_PROVIDER": PROVIDER, "CICD_SERVICE_ACCOUNT": CICD}
        lines = self.gh_lines(r.stdout)
        self.assertEqual([shlex.split(line) for line in lines],
                         [["gh", "variable", "set", name, "--repo", REPO, "--body", want[name]] for name in release.CI_VARS])
        self.assertEqual(list(want), list(release.CI_VARS))
        self.assertIn(f"# The trust (wif.tf): {REPO}, id {REPO_ID}, ref refs/heads/main.", r.stdout)
        self.assertIn(f"#   gh workflow run documind-cd.yml --repo {REPO} --ref main -f path=candidate\n", r.stdout)
        self.assertIn("# production: 1 required reviewer, so promote waits for a person", r.stdout)
        self.assertNotIn(SECRET, r.stdout + r.stderr)                     # terraform output -json carries it; never echoed
        self.assertTrue(all(line.startswith(("gh variable set ", "# ")) for line in r.stdout.splitlines()), r.stdout)
        calls = self.calls()
        tf = [c for c in calls if c["tool"] == "terraform"]
        self.assertEqual(len(tf), 1)
        self.assertTrue(os.path.samefile(tf[0]["cwd"], self.tf))          # run in the lane's terraform/
        self.assertEqual([c["args"] for c in calls if c["tool"] == "gh"], [["api", ENVIRONMENT]])
        self.assertFalse([c for c in calls if c["tool"] == "gcloud"])    # ci-vars needs no gcloud
        self.assert_read_only()

    def test_no_region_takes_the_one_the_lane_was_planned_in(self):
        r = self.release("ci-vars", "--project", PROJECT, "--terraform-dir", str(self.tf))
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertIn(f"gh variable set GCP_REGION --repo {REPO} --body {REGION}", r.stdout)

    def test_a_missing_reviewer_is_a_warning(self):
        self.world["gh"][ENVIRONMENT] = {"name": "production", "protection_rules": [{"type": "wait_timer", "wait_timer": 5}]}
        r = self.ci_vars()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.gh_lines(r.stdout)), 4)
        self.assertTrue(r.stderr.startswith(f"WARNING: {REPO}'s production environment has no required reviewer, so "
                                            "promote would move traffic with nobody approving."), r.stderr)
        self.assertNotIn("# production:", r.stdout)
        self.assert_read_only()

    def test_no_production_environment_is_a_warning(self):
        del self.world["gh"][ENVIRONMENT]                                  # gh api answers 404
        r = self.ci_vars()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.gh_lines(r.stdout)), 4)
        self.assertIn(f"WARNING: {REPO} has no production environment, or gh's account cannot see the repository. "
                      "GitHub creates the environment the first time a job names it, with no required reviewer", r.stderr)
        self.assertIn("Settings > Environments > production > Required reviewers", r.stderr)

    def test_a_gh_that_cannot_read_it_is_a_warning(self):
        self.world["gh_error"] = "To get started with GitHub CLI, please run:  gh auth login"     # gh not signed in
        r = self.ci_vars()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(len(self.gh_lines(r.stdout)), 4)
        self.assertTrue(r.stderr.startswith(f"WARNING: could not read {REPO}'s production environment (To get started "
                                            "with GitHub CLI, please run:  gh auth login): check by hand"), r.stderr)

    def test_without_gh_the_lines_print_and_say_what_was_not_read(self):
        self.uninstall("gh")
        r = self.ci_vars()
        self.assertEqual((r.returncode, r.stderr), (0, ""), r.stderr)
        self.assertEqual(len(self.gh_lines(r.stdout)), 4)
        self.assertIn("# gh is not installed here, so the production environment was not read", r.stdout)
        self.assertFalse([c for c in self.calls() if c["tool"] == "gh"])

    def test_a_region_the_lane_was_not_planned_in_is_refused(self):
        r = self.release("ci-vars", "--project", PROJECT, "--region", "us-central1", "--terraform-dir", str(self.tf))
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn(f"STOP: REGION is us-central1, but lane {PROJECT} was planned in {REGION}", r.stderr)
        self.assertIn(f"make ci-vars PROJECT={PROJECT} REGION={REGION}", r.stderr)
        self.assertEqual(self.calls(), [])                                 # refused before any tool ran

    def test_another_project_or_another_lanes_state_is_refused(self):
        r = self.release("ci-vars", "--project", "documind-other-lane", "--region", REGION, "--terraform-dir", str(self.tf))
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn(f"STOP: PROJECT is documind-other-lane, but {self.tf.resolve()} is lane {PROJECT}'s", r.stderr)
        self.world["terraform"]["outputs"]["cicd_service_account"] = "sa-documind-cicd@documind-other-lane.iam.gserviceaccount.com"
        r = self.ci_vars()
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("this checkout's backend points at another lane's state", r.stderr)
        self.world["terraform"]["outputs"]["cicd_service_account"] = "someone-else@documind-course-demo.iam.gserviceaccount.com"
        self.assertIn("is not sa.tf's sa-documind-cicd", self.ci_vars().stderr)
        self.world["terraform"]["outputs"]["cicd_service_account"] = CICD
        self.world["terraform"]["outputs"]["wif_provider"] = PROVIDER.replace("documind-github", "another-pool")
        self.assertIn("is not wif.tf's provider", self.ci_vars().stderr)

    def test_no_state_no_outputs_no_inputs_no_terraform(self):
        self.world["terraform"] = {"error": "\u2577\n\u2502 Error: Backend initialization required, please run "
                                            "\"terraform init\"\n\u2502 \n\u2502 Reason: Initial configuration of the "
                                            "requested backend \"gcs\"\n\u2575"}
        r = self.ci_vars()
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("(exit 1): Error: Backend initialization required, please run \"terraform init\". A checkout that "
                      "was never connected to the lane's state: make tf-backend PROJECT=<id> first", r.stderr)
        self.world["terraform"] = {"outputs": {}}                          # applied without the pipeline, or empty state
        r = self.ci_vars()
        self.assertEqual(r.returncode, 2)
        self.assertIn("STOP: terraform output has no wif_provider or no cicd_service_account", r.stderr)
        self.uninstall("terraform")
        r = self.ci_vars()
        self.assertEqual(r.returncode, 2)
        self.assertIn("STOP: terraform is not on PATH: install Terraform 1.9.0 or newer", r.stderr)
        (self.tf / release.infra.INPUT_FILE).unlink()
        r = self.ci_vars()
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn(f"STOP: no {release.infra.INPUT_FILE} in {self.tf.resolve()}", r.stderr)
        self.assertIn("python commands/infrastructure.py prepare --project PROJECT --region REGION", r.stderr)
        self.save_inputs({**INPUTS, "github_repository_id": "not-a-number"})   # infrastructure.validate_trust's rule
        self.assertIn("STOP: Set the CI repository's immutable numeric GitHub ID.", self.ci_vars().stderr)

    def test_the_workflow_reads_exactly_the_four(self):
        self.assertEqual(release.workflow_vars(), sorted(release.CI_VARS))
        text = release.WORKFLOW.read_text(encoding="utf-8")
        for name in release.CI_VARS:
            self.assertIn("${{ vars.%s }}" % name, text)
        extra = self.home / "extra.yml"
        extra.write_text(text + "      ZONE: ${{ vars.GCP_ZONE }}\n# vars.IN_A_COMMENT is not read\n", encoding="utf-8")
        self.assertEqual(release.workflow_vars(extra), sorted([*release.CI_VARS, "GCP_ZONE"]))
        r = self.ci_vars("--workflow", str(extra))
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("STOP: extra.yml reads CICD_SERVICE_ACCOUNT, GCP_PROJECT, GCP_REGION, GCP_ZONE, WIF_PROVIDER, and "
                      "ci-vars sets GCP_PROJECT, GCP_REGION, WIF_PROVIDER, CICD_SERVICE_ACCOUNT", r.stderr)
        fewer = self.home / "fewer.yml"
        fewer.write_text(text.replace("vars.WIF_PROVIDER", "secrets.WIF_PROVIDER"), encoding="utf-8")
        self.assertEqual(self.ci_vars("--workflow", str(fewer)).returncode, 2)
        self.assertEqual(self.calls(), [])


class KeysTests(Stubbed):
    def test_no_user_managed_keys(self):
        r = self.keys()
        self.assertEqual((r.returncode, r.stderr), (0, ""), r.stderr)
        self.assertEqual(r.stdout.splitlines(), [
            f"{PROJECT} has no parent: it is in no organization, so org_policy.tf's enforce_no_sa_keys cannot be applied "
            "and nothing stops a key being made; this check is the control",
            "3 service accounts, and the user-managed keys of each:",
            f"  0  {API_SA}", f"  0  {UI_SA}", f"  0  {CICD}",
            f"no user-managed keys: no key file can sign in as any account of {PROJECT}"])
        listed = [c["args"] for c in self.calls() if c["args"][:4] == ["iam", "service-accounts", "keys", "list"]]
        self.assertEqual(sorted(a[4] for a in listed), sorted(f"--iam-account={e}" for e in WORLD["accounts"]))
        for args in listed:                                                # Google's own keys are not counted
            self.assertEqual(args[5:], [f"--project={PROJECT}", "--managed-by=user", "--format=json"])
        self.assert_read_only()

    def test_keys_found_then_none_after_the_delete(self):
        self.world["keys"][API_SA] = [user_key(API_SA, "0a1b2c3d4e5f"),
                                      user_key(API_SA, "9f8e7d6c5b4a", disabled=True, validBeforeTime="2027-01-01T00:00:00Z")]
        r = self.keys()
        self.assertEqual((r.returncode, r.stderr), (1, ""), r.stderr)
        self.assertIn(f"  2  {API_SA}\n"
                      "       key 0a1b2c3d4e5f  created 2026-10-26T09:14:02Z  never expires\n"
                      "       key 9f8e7d6c5b4a  created 2026-10-26T09:14:02Z  expires 2027-01-01T00:00:00Z  "
                      f"(disabled, not deleted)\n  0  {UI_SA}\n", r.stdout)
        self.assertIn("2 user-managed keys on 1 account. A key is a credential that does not expire", r.stdout)
        self.assertTrue(r.stdout.endswith("  gcloud iam service-accounts keys delete KEY_ID --iam-account=ACCOUNT "
                                          f"--project={PROJECT}\n"), r.stdout)
        self.world["keys"] = {}                                            # the person deleted them
        r = self.keys()
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertTrue(r.stdout.endswith(f"no user-managed keys: no key file can sign in as any account of {PROJECT}\n"))
        self.assert_read_only()

    def test_an_account_that_could_not_be_read_is_no_proof(self):
        self.world["unreadable"][UI_SA] = ("ERROR: (gcloud.iam.service-accounts.keys.list) PERMISSION_DENIED: Permission "
                                           "'iam.serviceAccountKeys.list' denied on resource (or it may not exist).\n"
                                           "- '@type': type.googleapis.com/google.rpc.ErrorInfo\n"
                                           "  reason: IAM_PERMISSION_DENIED")
        r = self.keys()
        self.assertEqual(r.returncode, 2)
        self.assertIn(f"  ?  {UI_SA}  could not list its keys: ERROR: (gcloud.iam.service-accounts.keys.list) "
                      "PERMISSION_DENIED: Permission 'iam.serviceAccountKeys.list' denied", r.stdout)
        self.assertIn(f"STOP: the keys of 1 account could not be listed, so this is no proof of zero keys: {UI_SA}",
                      r.stderr)
        self.world["keys"][API_SA] = [user_key(API_SA, "0a1b2c3d4e5f")]   # a key found still decides
        r = self.keys()
        self.assertEqual(r.returncode, 1)
        self.assertIn("1 user-managed key on 1 account (1 more account not read).", r.stdout)

    def test_the_projects_parent(self):
        self.world["project"]["parent"] = {"type": "organization", "id": "246813579"}
        first = self.keys().stdout.splitlines()[0]
        self.assertEqual(first, f"{PROJECT} is in organization 246813579: org_policy.tf's enforce_no_sa_keys can forbid "
                                "making keys here, and an organization created on or after 3 May 2024 forbids it by default")
        self.world["project"]["parent"] = {"type": "folder", "id": "135792468"}
        self.assertTrue(self.keys().stdout.startswith(f"{PROJECT} is in folder 135792468, inside an organization: "))

    def test_refusals(self):
        self.world["project"]["projectId"] = "documind-other-lane"         # describe answers for another project only
        r = self.keys()
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn(f"STOP: gcloud projects describe failed (exit 1): ERROR: (gcloud.projects.describe) NOT_FOUND: "
                      f"project {PROJECT}", r.stderr)
        self.uninstall("gcloud")
        r = self.keys()
        self.assertEqual((r.returncode, r.stdout), (2, ""))
        self.assertIn("STOP: gcloud is not on PATH", r.stderr)
        r = self.release("keys")                                           # no --project, no PROJECT
        self.assertEqual(r.returncode, 2)
        self.assertIn("STOP: pass --project", r.stderr)


class PureTests(unittest.TestCase):
    def test_the_line_that_names_the_cause(self):
        self.assertEqual(release.cause("WARNING: noise\nERROR: (gcloud.x) PERMISSION_DENIED: no\n  reason: X"),
                         "ERROR: (gcloud.x) PERMISSION_DENIED: no")
        self.assertEqual(release.cause("\u2577\n\u2502 Error: Backend initialization required\n\u2575"),
                         "Error: Backend initialization required")
        self.assertEqual(release.cause("gh: Not Found (HTTP 404)\n"), "gh: Not Found (HTTP 404)")
        self.assertEqual(release.cause(""), "no error output")


class WiringTests(unittest.TestCase):
    def read(self, *parts: str) -> str:
        return KIT.joinpath(*parts).read_text(encoding="utf-8")

    def test_the_make_targets(self):
        mk, release_mk, readme = self.read("Makefile"), self.read("mk", "release.mk"), self.read("mk", "README.md")
        self.assertEqual(len(mk.splitlines()), 888)                       # workshop lesson 9.3 counts it
        phony = mk[mk.index(".PHONY:"):mk.index("# ---------- the module files")].replace("\\", " ").split()
        for target, sub in (("ci-vars", "ci-vars"), ("keys-check", "keys")):
            self.assertIn(target, phony)
            self.assertIn(f"`{target}`", readme)
            self.assertIn(f"\n{target}: guard-project\n\t@$(PY) commands/release.py {sub} --project $(PROJECT)", release_mk)
        self.assertIn("ci-vars --project $(PROJECT) --region $(REGION) --terraform-dir $(TF_DIR)\n", release_mk)
        row = next(line for line in readme.splitlines() if line.startswith("| `release.mk` | "))
        self.assertIn("`ci-vars`, `keys-check`", row.split(" | ")[1])      # later lessons' targets follow in the row

    def test_the_names_release_py_expects_are_the_kits(self):
        wif, sa = self.read("terraform", "wif.tf"), self.read("terraform", "sa.tf")
        self.assertRegex(wif, r'\n  workload_identity_pool_id\s+= "documind-github"\n')
        self.assertRegex(wif, r'\n  workload_identity_pool_provider_id\s+= "github-oidc"\n')
        self.assertIn('output "wif_provider"', wif)
        self.assertIn('output "cicd_service_account" { value = google_service_account.cicd.email }', wif)
        self.assertRegex(sa, r'resource "google_service_account" "cicd" \{\n  account_id\s+= "sa-documind-cicd"\n')
        cd = self.read(".github", "workflows", "documind-cd.yml")
        self.assertIn("id-token: write", cd)                              # no OIDC token, no keyless sign-in
        self.assertIn("workload_identity_provider: ${{ vars.WIF_PROVIDER }}", cd)    # the provider's full name
        self.assertIn("service_account: ${{ vars.CICD_SERVICE_ACCOUNT }}", cd)       # the account's email
        self.assertIn("environment: production", cd)                      # the environment ci-vars reads
        self.assertIn("options: [candidate, clouddeploy]", cd)              # the dispatch line's -f path=candidate
        self.assertEqual(release.infra.INPUT_FILE, "runbook-project.auto.tfvars.json")
        self.assertIn("terraform/*.tfvars.json", self.read(".gitignore"))   # the confirmed inputs are never committed


if __name__ == "__main__":
    unittest.main()
