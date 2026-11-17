"""Build lesson 11.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Build and deploy using keyless identity. The lane trusts one GitHub repository on one branch (terraform/wif.tf, named
at lesson 0.3's step 3). A run of .github/workflows/documind-cd.yml asks GitHub for a signed OIDC token; Google's token
service checks the provider's three-clause condition (repository_id, repository, ref); the binding on sa-documind-cicd,
keyed on the repository's immutable id, lets the federated identity become that account for about an hour, enough to
build the API's image and put it on a candidate revision that takes no traffic. make ci-vars (commands/release.py)
prints the workflow's four repository variables from the lane; make keys-check counts every account's user-managed keys.

Computed here, offline, from the kit:
  - the panel in step 1: wif.tf's attribute mapping, condition and binding, parsed from the file. The condition,
    rendered with stand-in values, is accepted by infrastructure.parse_trust(), the plan guard's own parser, and the
    panel's evaluator, run by node over every preset and all three trust shapes, must agree with a Python evaluation of
    the condition's and the binding's text;
  - sa.tf's cicd_roles and cicd_actas, wif.tf's token grants, documind-cd.yml's permissions, jobs, auth steps and
    variables, the 41 APIs of commands/lesson-12.1.sh (sts.googleapis.com among them), build-access.sh's two grants to
    sa-documind-cicd, the workflow's staged and polled build, the Makefile's build line and
    REGION default, cloudbuild.yaml's logging option, run-service.yaml's literal PROJECT_NUMBER;
  - release.py ci-vars and keys, run against stand-in terraform, gh and gcloud executables on a PATH that holds nothing
    else, as the kit's own commands/tests/test_release.py runs them: the missing-environment warning, the region
    refusal, and a key planted on sa-documind-cicd. Their identifiers are printed as the course's placeholders;
  - the lines make build and make release-candidate print, from the Makefile's own echo statements; the live gate's
    rupees from shared/prices.py and evals/golden.jsonl.
Recorded from the author's lane and fork with pb.recorded(): the first keyless dispatch (batch 1's probe) and the page's
runs in batch 3. RUN_LIST.md says which command records which file, and build.py holds its rupees to the kit's.

    python pagekit/build.py 11.1
"""
import html
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[2]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section  # noqa: E402

LESSON = "11.1"
title = ("<title>Lesson 11.1 Build and deploy using keyless identity - a GitHub run proves which repository and branch "
         "it is, and gets an hour as the pipeline's account | Netsetos</title>\n")
PROJ = "documind-ai-YOUR-ID"
REPO = "YOUR-GITHUB-USER/YOUR-REPO"                 # lesson 0.3's placeholder for the repository the lane trusts
UPSTREAM = "netsetos/agents_workshop_learner"


def kit(rel: str) -> str:
    """One kit file's text."""
    return (KIT / rel).read_text(encoding="utf-8")


def load(rel: str, name: str):
    """A kit module, imported from its file (both are standard library only)."""
    spec = importlib.util.spec_from_file_location(name, KIT / rel)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


infra = load("commands/infrastructure.py", "infrastructure_l111")
release = load("commands/release.py", "release_l111")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the trust panel: a token's claims through the provider's condition and the account's binding */
.wi-trust{font-size:var(--small-size);background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;overflow-wrap:anywhere;}
.wi-pre{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 10px;}
.wi-pre button{font:inherit;font-size:13px;line-height:1.3;text-align:left;padding:6px 11px;border:1px solid var(--border);border-radius:16px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(36px,var(--touch));-webkit-tap-highlight-color:transparent;}
.wi-pre button[aria-pressed="true"]{border:2px solid var(--teal);background:var(--teal-light);color:var(--teal-dark);font-weight:700;}
.wi-pre button:active{transform:scale(.98);}
.wi-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,200px),1fr));gap:8px 12px;margin:0 0 10px;}
.wi-in label{font-family:var(--mono);font-size:12.5px;color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.wi-in .wide{grid-column:1 / -1;}
.wi-in input,.wi-in select{font-family:var(--mono);font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);color:var(--navy);min-height:44px;width:100%;max-width:100%;}
.wi-in select{font-family:var(--font);}
.wi-v{border-radius:10px;padding:10px 12px;margin:0 0 8px;font-size:var(--small-size);line-height:1.55;font-weight:600;overflow-wrap:anywhere;}
.wi-v.ok{background:#d1fae5;border:1px solid #6ee7b7;color:#065f46;}
.wi-v.no{background:#f1f5f9;border:1px solid #cbd5e1;color:#334155;}
.wi-v.half{background:#fef3c7;border:1px solid #fcd34d;color:#92400e;}
.wi-v.bad{background:#fee2e2;border:1px solid #fca5a5;color:#991b1b;}
.wi-card{background:var(--card);border:1px solid var(--border);border-left:4px solid var(--slate-light);border-radius:10px;padding:8px 12px;margin:0 0 6px;font-size:12.5px;line-height:1.5;color:var(--slate);min-width:0;}
.wi-card .h{display:block;font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:.8px;text-transform:uppercase;color:var(--navy);margin:0 0 4px;}
.wi-card.wi-pass{border-left-color:var(--teal);}
.wi-card.wi-stop{border-left-color:#dc2626;background:#fef2f2;}
.wi-card.wi-skip{opacity:.6;}
.wi-row{display:grid;grid-template-columns:18px minmax(0,1fr);gap:0 6px;margin:2px 0;font-family:var(--mono);font-size:12px;}
.wi-row .wi-t{min-width:0;overflow-wrap:anywhere;}
.wi-row.ok .wi-m{color:var(--teal-dark);font-weight:700;}
.wi-row.no .wi-m,.wi-row.no .wi-t{color:#b91c1c;font-weight:700;}
@media (hover:hover) and (pointer:fine){.wi-pre button:hover{border-color:var(--teal);}}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's reasons
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson's dispatch runs the live gate on the candidate it makes, and the gate asks acme's golden rows; run it "
         "as lesson 4.3 ran its gate, with acme on the kit's own index, and put the pin back at the end."),
        ("Keep the two apart in your head; step 3 makes the difference visible.",
         "Keep the two apart in your head. This lesson adds a third, <code>sa-documind-cicd</code>, which a GitHub run "
         "becomes for about an hour without any key.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)

# ================================================================== the kit, read
WIF_TF, SA_TF, CD_YML, REL, INFRA_PY = ("terraform/wif.tf", "terraform/sa.tf", ".github/workflows/documind-cd.yml",
                                        "commands/release.py", "commands/infrastructure.py")
WIF, SA, CD, MK = kit(WIF_TF), kit(SA_TF), kit(CD_YML), kit("Makefile")

# wif.tf: the pool, the provider, its mapping and condition, the binding, the trusted ref, the eval tokens
POOL_ID = re.search(r'workload_identity_pool_id\s+= "([^"]+)"', WIF).group(1)
PROVIDER_ID = re.search(r'workload_identity_pool_provider_id\s+= "([^"]+)"', WIF).group(1)
ISSUER = re.search(r'oidc \{ issuer_uri = "([^"]+)" \}', WIF).group(1)
MAPPING = re.findall(r'^\s+"((?:google|attribute)\.[a-z_]+)"\s+= "(assertion\.[a-z_]+)"$', WIF, re.M)
assert MAPPING == [("google.subject", "assertion.sub"), ("attribute.repository", "assertion.repository"),
                   ("attribute.repository_id", "assertion.repository_id"), ("attribute.ref", "assertion.ref")], MAPPING
COND_BLOCK = re.search(r'attribute_condition = join\(" && ", \[\n(.*?)\n  \]\)', WIF, re.S).group(1)
CLAUSE_LINES = re.findall(r'"(assertion\.\w+ == \'\$\{var\.\w+\}\')",', COND_BLOCK)
CLAUSES = [re.fullmatch(r"assertion\.(\w+) == '\$\{var\.(\w+)\}'", c).groups() for c in CLAUSE_LINES]
assert CLAUSES == [("repository_id", "github_repository_id"), ("repository", "github_repository"), ("ref", "deploy_ref")]
MEMBER = re.search(r'member = format\(\n\s+"(principalSet://iam\.googleapis\.com/%s/attribute\.(\w+)/%s)",\n'
                   r'\s+google_iam_workload_identity_pool\.github\.name,\n\s+var\.(\w+),', WIF)
MEMBER_FMT, BIND_ATTR, BIND_VAR = MEMBER.groups()
assert (BIND_ATTR, BIND_VAR) == ("repository_id", "github_repository_id")
BIND_ROLE = re.search(r'resource "google_service_account_iam_member" "cicd_wif" \{\n.*?\n  role\s+= "([^"]+)"', WIF, re.S).group(1)
assert BIND_ROLE == "roles/iam.workloadIdentityUser"
DEPLOY_REF = re.search(r'variable "deploy_ref" \{\n  type    = string\n  default = "([^"]+)"', WIF).group(1)
assert DEPLOY_REF == "refs/heads/main"
EVAL_FOR = re.search(r'resource "google_service_account_iam_member" "cicd_eval_tokens" \{\n  for_each\s+= \{ (.*?) \}\n'
                     r'  service_account_id = each.value\n  role\s+= "roles/iam.serviceAccountTokenCreator"', WIF).group(1)
EVAL_KEYS = [k for k, v in re.findall(r"(\w+) = google_service_account\.(\w+)\.name", EVAL_FOR) if k == v]
assert EVAL_KEYS == ["ui", "outsider"], EVAL_KEYS

# the condition, rendered as Terraform's join renders it, is the one the plan guard's own parser accepts
DIGITS = {"github_repository_id": "200000000022"}            # parse_trust() needs digits; the page never shows these
cond_with = lambda values: " && ".join(re.sub(r"\$\{var\.(\w+)\}", lambda m: values[m.group(1)], c)  # noqa: E731
                                       for c in CLAUSE_LINES)
TRUST_VARS = {"github_repository": REPO, "github_repository_id": "REPO_ID", "deploy_ref": DEPLOY_REF}
assert infra.parse_trust(cond_with({**TRUST_VARS, **DIGITS})) == {**TRUST_VARS, **DIGITS}
assert tuple(infra.TRUST) == ("github_repository", "github_repository_id", "deploy_ref")

# sa.tf: the pipeline's account, its five project roles, the accounts it may act as
ACCOUNT_IDS = dict(re.findall(r'resource "google_service_account" "(\w+)" \{\n  account_id\s+= "([^"]+)"', SA))
CICD_ROLES = re.findall(r'^\s+"(roles/[^"]+)",', re.search(r"  cicd_roles = \[\n(.*?)\n  \]", SA, re.S).group(1), re.M)
assert CICD_ROLES == ["roles/cloudbuild.builds.editor", "roles/artifactregistry.writer", "roles/clouddeploy.releaser",
                      "roles/clouddeploy.jobRunner", "roles/run.developer"], CICD_ROLES
ACTAS = re.findall(r"^\s+(\w+)\s+= google_service_account\.(\w+)\.name$",
                   re.search(r"  cicd_actas = \{\n(.*?)\n  \}", SA, re.S).group(1), re.M)
assert [k for k, _ in ACTAS] == ["api", "ui", "ingest", "admin", "chat", "mcp", "agent", "cicd"] and all(k == v for k, v in ACTAS)
ACTAS_IDS = [ACCOUNT_IDS[k] for k, _ in ACTAS]
TOKEN_IDS = [ACCOUNT_IDS[k] for k in EVAL_KEYS]
assert ACCOUNT_IDS["cicd"] == "sa-documind-cicd" and TOKEN_IDS == ["documind-ui-sa", "documind-outsider-sa"]
# what the build asks beyond sa.tf, and where the kit meets it: STS among the APIs, the source bucket and actAs on the build's
# account from make build-access (no project-wide storage role), and no log read, because the workflow polls the build
assert not [r for r in CICD_ROLES if r.startswith("roles/storage.")]
assert not [r for r in CICD_ROLES if r in ("roles/logging.viewer", "roles/logging.privateLogViewer", "roles/viewer",
                                            "roles/editor", "roles/owner")]
ENABLE = re.search(r"^# ---- ENABLE_APIS ----$(.*?)^# ---- APPLY ----$", kit("commands/lesson-12.1.sh"), re.M | re.S).group(1)
APIS = re.findall(r"([a-z0-9]+)\.googleapis\.com", ENABLE)
assert len(APIS) == len(set(APIS)) == 41 and "sts" in APIS and "iamcredentials" in APIS, len(APIS)
BA = kit("commands/build-access.sh")
assert "--role=roles/storage.legacyBucketWriter" in BA and "--role=roles/iam.serviceAccountUser" in BA and "roles/editor roles/owner" in BA
assert "gcloud builds submit --async --format='value(id)'" in CD and '--gcs-source-staging-dir="gs://${PROJECT}_cloudbuild/source"' in CD
assert "gcloud builds describe \"$BUILD\" --format='value(status)'" in CD

# documind-cd.yml: one permission, four variables, the jobs and which of them sign in, the person, the two paths
assert "  id-token: write          # REQUIRED for OIDC; without it auth fails with no token" in CD
assert "Identity Federation exchanges it for a Google credential that expires in about an hour." in CD
assert "# A workflow_dispatch run from any other branch therefore fails at the auth step." in CD
JOB_TEXT = dict(re.findall(r"^  ([a-z-]+):\n(.*?)(?=^  [a-z-]+:\n|\Z)", CD.split("\njobs:\n", 1)[1], re.M | re.S))
assert list(JOB_TEXT) == ["eval-gate", "release-candidate", "promote", "release-clouddeploy"], list(JOB_TEXT)
SIGNS_IN = [j for j, t in JOB_TEXT.items() if "uses: google-github-actions/auth@" in t]
assert SIGNS_IN == ["release-candidate", "promote", "release-clouddeploy"] and "auth@" not in JOB_TEXT["eval-gate"]
assert set(re.findall(r"uses: google-github-actions/auth@(v\d+)", CD)) == {"v3"}
assert "environment: production" in JOB_TEXT["promote"] and "needs: release-candidate" in JOB_TEXT["promote"]
assert "make build PROJECT=\"$PROJECT\" REGION=\"$REGION\" SERVICES=api GIT_SHA=\"$TAG\"" in JOB_TEXT["release-candidate"]
assert "make release-candidate PROJECT=\"$PROJECT\" REGION=\"$REGION\" GIT_SHA=\"$TAG\"" in JOB_TEXT["release-candidate"]
assert re.search(r"options: \[candidate, clouddeploy\]\n\s+default: candidate", CD)
CI_VARS = list(release.CI_VARS)
assert release.workflow_vars() == sorted(CI_VARS) and len(CI_VARS) == 4
assert "id-token" not in kit(".github/workflows/documind-dryrun.yml")      # the dry run asks GitHub for no token at all

# what path=clouddeploy would roll out over documind-api, and the Makefile's REGION default ci-vars guards against
RS_ENV = re.findall(r"^\s+- name: ([A-Z_]+)\n(?:\s+#.*\n)*\s+value: (.+)$", kit("run-service.yaml"), re.M)
assert [n for n, _ in RS_ENV] == ["AUTH_MODE", "SELF_URL", "IAP_AUDIENCE"], RS_ENV
assert all("PROJECT_NUMBER" in v and "us-central1" in v for n, v in RS_ENV if n != "AUTH_MODE")
REGION_DEFAULT = re.search(r"^REGION\s+\?= (\S+)$", MK, re.M).group(1)
assert REGION_DEFAULT == "us-central1"

# the build line, the build's logging, and the lines make prints on the local operator path
recipe = lambda name: MK[MK.index(f"\n{name}:") + 1:].split("\n\n", 1)[0]  # noqa: E731
assert ("gcloud builds submit . --project=$(PROJECT) --quiet --config=cloudbuild.yaml \\\n"
        "\t      --substitutions=_IMAGE=$(IMAGE_REPO)/$$svc:$(GIT_SHA),_DOCKERFILE=services/$$dir/Dockerfile;") in recipe("build")
assert re.search(r"^options:\n  logging: CLOUD_LOGGING_ONLY$", kit("cloudbuild.yaml"), re.M)
ECHO_BUILD = re.search(r'echo ">> building \$\(IMAGE_REPO\)/\$\$svc:\$\(GIT_SHA\) from services/\$\$dir"', recipe("build"))
ECHO_REV = re.search(r'echo ">> candidate revision: \$\$REV (\(deploy/\.candidate-revision - [^"]+\))"', recipe("record-candidate")).group(1)
ECHO_CAND = re.search(r'echo ">> candidate: https://candidate---documind-api-\$\$NUMBER\.\$\(REGION\)\.run\.app  (\([^"]+\))"',
                      recipe("release-candidate")).group(1)
RC_LINE = recipe("release-candidate").splitlines()[1].strip()
assert ECHO_BUILD and RC_LINE == ("gcloud run services update documind-api --region $(REGION) --project $(PROJECT) --image "
                                  "$(IMAGE_REPO)/api:$(GIT_SHA) --no-traffic --tag candidate --update-env-vars "
                                  "GIT_SHA=$(GIT_SHA) --quiet"), RC_LINE
assert "--min-instances=0" in kit("commands/lesson-12.2.sh")              # an idle candidate costs nothing

# the live gate's rupees: the golden rows at the course's typical answer, priced by the kit's own table
PRICES = {}
exec(compile(kit("shared/prices.py"), "prices.py", "exec"), PRICES)
GENERATOR = re.search(r"^GENERATOR_MODEL \?= (\S+)$", MK, re.M).group(1)
RATE_IN, RATE_OUT = PRICES["PRICES"][GENERATOR]
TYPICAL = (2000, 300)              # the course's typical answer (lessons 4.3, 4.4 and 11.6): 2,000 tokens in, 300 out
RS_ANSWER = (TYPICAL[0] * RATE_IN + TYPICAL[1] * RATE_OUT) / 1_000_000 * PRICES["USD_INR"]
GOLDEN = [json.loads(line) for line in kit("evals/golden.jsonl").splitlines() if line.strip()]
N_ISO = sum(r.get("shape") == "isolation" for r in GOLDEN)
RS_GATE = round(RS_ANSWER * len(GOLDEN))
assert (GENERATOR, PRICES["USD_INR"], RATE_IN, RATE_OUT) == ("gemini-3.6-flash", 85, 1.50, 7.50)
RUN_LIST = (HERE / "RUN_LIST.md").read_text(encoding="utf-8")
for fact in (f"about Rs {RS_GATE}", f"Rs {RS_ANSWER:.2f}", f"{len(GOLDEN)} golden rows", f"about Rs {2 * RS_GATE} in all"):
    assert fact in RUN_LIST, f"RUN_LIST.md no longer says {fact!r}: the kit's rows or prices moved"

# ================================================================== release.py, run against stand-ins
SP_PROJECT = "documind-ai-your-id"   # release.py's project-id rule is lower case; the page prints documind-ai-YOUR-ID
SP_NUMBER, SP_REPO_ID = "100000000011", "200000000022"   # stand-in digits: replaced by NUMBER and REPO_ID below
SP_SECRET = "postgresql://litellm:stand-in@localhost/litellm"
STUB = r'''
import json, os, sys
tool, args = sys.argv[1], sys.argv[2:]
home = os.environ["L111_STUB_HOME"]
with open(os.path.join(home, "calls.jsonl"), "a", encoding="utf-8") as log:
    log.write(json.dumps({"tool": tool, "args": args}) + "\n")
with open(os.path.join(home, "scenario.json"), encoding="utf-8") as f:
    world = json.load(f)


def reply(out=None, code=0, err=""):
    if out is not None:
        sys.stdout.write(out if isinstance(out, str) else json.dumps(out))
    if err:
        sys.stderr.write(err + "\n")
    sys.exit(code)


def flag(name):
    return next((a.split("=", 1)[1] for a in args if a.startswith(name + "=")), None)


if tool == "terraform" and args == ["output", "-json"]:
    reply({k: {"sensitive": k == "gateway_database_url", "type": "string", "value": v} for k, v in world["outputs"].items()})
if tool == "gh" and len(args) == 2 and args[0] == "api":
    if args[1] in world["gh"]:
        reply(world["gh"][args[1]])
    reply('{"message":"Not Found","documentation_url":"https://docs.github.com/rest","status":"404"}', 1, "gh: Not Found (HTTP 404)")
if tool == "gcloud" and args[:2] == ["projects", "describe"]:
    if args[2] == world["project"]["projectId"]:
        reply(world["project"])
    reply(None, 1, "ERROR: (gcloud.projects.describe) NOT_FOUND: project " + args[2])
if tool == "gcloud" and args[:3] == ["iam", "service-accounts", "list"]:
    reply([{"email": e} for e in world["accounts"]])
if tool == "gcloud" and args[:4] == ["iam", "service-accounts", "keys", "list"] and flag("--managed-by") == "user":
    reply(world["keys"].get(flag("--iam-account"), []))
reply(None, 99, "stub: unexpected call: " + " ".join([tool] + args))
'''
ENV_PATH = f"repos/{REPO}/environments/production"
WORLD = {
    "inputs": {"project_id": SP_PROJECT, "region": "asia-south1", "billing_account_id": "STAND-IN",
               "github_repository": REPO, "github_repository_id": SP_REPO_ID, "deploy_ref": DEPLOY_REF},
    "outputs": {"wif_provider": f"projects/{SP_NUMBER}/locations/global/workloadIdentityPools/{POOL_ID}/providers/{PROVIDER_ID}",
                "cicd_service_account": f"sa-documind-cicd@{SP_PROJECT}.iam.gserviceaccount.com",
                "gateway_database_url": SP_SECRET},
    "gh": {},
    "project": {"projectId": SP_PROJECT, "projectNumber": SP_NUMBER, "lifecycleState": "ACTIVE"},
    "accounts": sorted(f"{a}@{SP_PROJECT}.iam.gserviceaccount.com" for a in ACCOUNT_IDS.values()),
    "keys": {},
}


def run_release(world: dict, *args: str) -> tuple:
    """release.py with the stand-ins first and alone on PATH: (exit code, stdout, stderr, the tools' calls)."""
    tmp = Path(tempfile.mkdtemp(prefix="l111_"))
    try:
        bin_dir, tf_dir = tmp / "bin", tmp / "terraform"
        bin_dir.mkdir()
        tf_dir.mkdir()
        stub = tmp / "stub.py"
        stub.write_text(STUB, encoding="utf-8")
        for tool in ("gcloud", "gh", "terraform"):
            if os.name == "nt":
                (bin_dir / f"{tool}.cmd").write_text(f'@echo off\n"{sys.executable}" "{stub}" {tool} %*\nexit /b %errorlevel%\n',
                                                     encoding="utf-8")
            else:
                (bin_dir / tool).write_text(f'#!/bin/sh\nexec "{sys.executable}" "{stub}" {tool} "$@"\n', encoding="utf-8")
                (bin_dir / tool).chmod(0o755)
        (tf_dir / release.infra.INPUT_FILE).write_text(json.dumps(world["inputs"]), encoding="utf-8")
        (tmp / "scenario.json").write_text(json.dumps(world), encoding="utf-8")
        env = {"PATH": str(bin_dir), "L111_STUB_HOME": str(tmp), "PYTHONIOENCODING": "utf-8", "PYTHONDONTWRITEBYTECODE": "1",
               "HOME": str(tmp), "USERPROFILE": str(tmp), "APPDATA": str(tmp), "CLOUDSDK_CONFIG": str(tmp / "gcloud")}
        for key in ("SYSTEMROOT", "COMSPEC", "PATHEXT", "WINDIR", "TEMP", "TMP"):
            if key in os.environ:
                env[key] = os.environ[key]
        argv = [a.replace("@TF@", str(tf_dir)) for a in args]
        r = subprocess.run([sys.executable, str(KIT / REL), *argv], cwd=str(tmp), env=env, capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=180)
        log = tmp / "calls.jsonl"
        calls = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()] if log.exists() else []
        return r.returncode, r.stdout, r.stderr, calls
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def placeholders(text: str) -> str:
    """The stand-in's identifiers as the course's placeholders; no stand-in digit reaches the page."""
    out = text.replace(SP_PROJECT, PROJ).replace(SP_NUMBER, "NUMBER").replace(SP_REPO_ID, "REPO_ID")
    assert not re.search(r"\d{6,}", out) and SP_SECRET not in out, out
    return out


def ci_vars_run(world: dict, region: str = "asia-south1") -> tuple:
    """make ci-vars's own command line against the stand-in lane: (exit code, what the terminal shows)."""
    rc, out, err, calls = run_release(world, "ci-vars", "--project", SP_PROJECT, "--region", region, "--terraform-dir", "@TF@")
    assert all(c["tool"] in ("terraform", "gh") for c in calls), calls                 # ci-vars needs no gcloud
    assert all(c["args"] == ["output", "-json"] or c["args"][0] == "api" for c in calls), calls   # reads only
    return rc, placeholders(out + err)


# 1. the first make ci-vars: the four lines, the trust, the dispatch line, and a warning (no production environment yet)
rc, CIVARS_WARN = ci_vars_run(WORLD)
assert rc == 0 and CIVARS_WARN.count("\ngh variable set ") + CIVARS_WARN.startswith("gh variable set ") == 4, CIVARS_WARN
assert f"WARNING: {REPO} has no production environment" in CIVARS_WARN and "--ref main -f path=candidate" in CIVARS_WARN
GH_LINES = [line for line in CIVARS_WARN.splitlines() if line.startswith("gh variable set ")]
assert [line.split()[3] for line in GH_LINES] == CI_VARS
assert f"gh variable set WIF_PROVIDER --repo {REPO} --body projects/NUMBER/locations/global/workloadIdentityPools/" in CIVARS_WARN
# 2. after the environment exists, with you as its reviewer: the line that replaces the warning
reviewed = json.loads(json.dumps(WORLD))
reviewed["gh"][ENV_PATH] = {"name": "production", "protection_rules": [
    {"type": "required_reviewers", "reviewers": [{"type": "User", "reviewer": {"login": "YOUR-GITHUB-USER"}}]}]}
rc, CIVARS_OK = ci_vars_run(reviewed)
REVIEWER_LINE = "# production: 1 required reviewer, so promote waits for a person"
assert rc == 0 and CIVARS_OK.rstrip().endswith(REVIEWER_LINE) and "WARNING" not in CIVARS_OK, CIVARS_OK
assert CIVARS_OK.splitlines()[:-1] == CIVARS_WARN.splitlines()[:-1]
# 3. the Makefile's own REGION default, refused before any tool runs
rc, CIVARS_REGION = ci_vars_run(WORLD, region=REGION_DEFAULT)
assert rc == 2 and CIVARS_REGION.startswith(f"STOP: REGION is {REGION_DEFAULT}, but lane {PROJ} was planned in asia-south1"), CIVARS_REGION
# 4. make keys-check against a stand-in project of sa.tf's accounts, one of which holds the key this lesson replaces
planted = json.loads(json.dumps(WORLD))
CICD_SP = f"sa-documind-cicd@{SP_PROJECT}.iam.gserviceaccount.com"
planted["keys"][CICD_SP] = [{"name": f"projects/{SP_PROJECT}/serviceAccounts/{CICD_SP}/keys/KEY_ID", "keyType": "USER_MANAGED",
                             "validAfterTime": "WHEN", "validBeforeTime": "9999-12-31T23:59:59Z"}]
rc, out, err, calls = run_release(planted, "keys", "--project", SP_PROJECT)
KEYS_PLANTED = placeholders(out + err)
assert rc == release.KEYS_FOUND == 1 and "1 user-managed key on 1 account." in KEYS_PLANTED, KEYS_PLANTED
assert f"  1  sa-documind-cicd@{PROJ}.iam.gserviceaccount.com\n       key KEY_ID  created WHEN  never expires" in KEYS_PLANTED
assert KEYS_PLANTED.startswith(f"{PROJ} has no parent: it is in no organization")
N_SA_SP = len(WORLD["accounts"])
assert f"{N_SA_SP} service accounts, and the user-managed keys of each:" in KEYS_PLANTED
assert all(c["tool"] == "gcloud" for c in calls)
rc, out, err, _ = run_release(WORLD, "keys", "--project", SP_PROJECT)
assert rc == 0 and placeholders(out).endswith(f"no user-managed keys: no key file can sign in as any account of {PROJ}\n")
NO_KEYS_LINE = f"no user-managed keys: no key file can sign in as any account of {PROJ}"

# ================================================================== the panel: the condition and the binding, evaluated
TRUST = {"repository": REPO, "repository_id": "REPO_ID", "ref": DEPLOY_REF}
POOL = f"projects/NUMBER/locations/global/workloadIdentityPools/{POOL_ID}"
NAME_CLAUSE = next(c for c in CLAUSE_LINES if c.startswith("assertion.repository =="))
NAME_ONLY = NAME_CLAUSE.replace("${var.github_repository}", REPO)      # the clause the condition kept before its repair
COND_TEXT = {"kit": cond_with(TRUST_VARS), "half": NAME_ONLY, "old": NAME_ONLY}
assert NAME_ONLY in COND_TEXT["kit"].split(" && ")
MEMBER_TEXT = {"kit": MEMBER_FMT % (POOL, "REPO_ID"), "half": MEMBER_FMT % (POOL, "REPO_ID"),
               "old": MEMBER_FMT.replace("attribute.repository_id/", "attribute.repository/") % (POOL, REPO)}
POLICIES = {"kit": {"clauses": [f for f, _ in CLAUSES], "bind": BIND_ATTR},
            "half": {"clauses": ["repository"], "bind": BIND_ATTR},
            "old": {"clauses": ["repository"], "bind": "repository"}}
POLICY_LABEL = {"kit": "wif.tf: three clauses, bound by id",
                "half": "the name only, bound by id",
                "old": "the name only, bound by name (old)"}
BASE = {"repository": REPO, "repository_id": "REPO_ID", "ref": DEPLOY_REF, "job": "release-candidate"}
PRESETS = [("main", "Your fork, main", {}),
           ("promote", "The same run's promote job", {"job": "promote"}),
           ("branch", "A branch of your fork", {"ref": "refs/heads/try-a-branch"}),
           ("tag", "A tag of your fork", {"ref": "refs/tags/v1.0"}),
           ("renamed", "Your fork, renamed", {"repository": "YOUR-GITHUB-USER/documind-release"}),
           ("claimed", "Your old name, claimed by someone else", {"repository_id": "ANOTHER_ID"}),
           ("upstream", "The upstream repository", {"repository": UPSTREAM, "repository_id": "ITS_ID"})]
PRESET_TOKENS = {k: {**BASE, **v} for k, _, v in PRESETS}
ENV_NAME = re.search(r"environment: (\w+)", JOB_TEXT["promote"]).group(1)


def py_claims(t: dict) -> dict:
    """The claims the panel shows: three as the token carries them, and GitHub's subject for the job."""
    return {"repository": t["repository"], "repository_id": t["repository_id"], "ref": t["ref"],
            "sub": f"repo:{t['repository']}:" + (f"environment:{ENV_NAME}" if t["job"] == "promote" else f"ref:{t['ref']}")}


def py_eval(t: dict, key: str) -> dict:
    """The condition's text and the binding's member, evaluated as the provider and IAM compare: string equality."""
    c = py_claims(t)
    rows = []
    for clause in COND_TEXT[key].split("&&"):
        m = re.fullmatch(r"\s*assertion\.(\w+)\s*==\s*'([^']*)'\s*", clause)
        rows.append({"field": m.group(1), "want": m.group(2), "got": c[m.group(1)], "ok": c[m.group(1)] == m.group(2)})
    cond = all(r["ok"] for r in rows)
    m = re.fullmatch(r"principalSet://iam\.googleapis\.com/(.+?)/attribute\.(\w+)/(.+)", MEMBER_TEXT[key])
    assert m.group(1) == POOL
    source = dict(MAPPING)[f"attribute.{m.group(2)}"].split(".", 1)[1]
    bind = c[source] == m.group(3)
    return {"claims": c, "rows": rows, "cond": cond, "bind": bind,
            "verdict": ("credential" if bind else "unbound") if cond else "refused"}


VERDICTS = {key: {p: py_eval(t, key)["verdict"] for p, t in PRESET_TOKENS.items()} for key in POLICIES}
assert VERDICTS["kit"] == {"main": "credential", "promote": "credential", "branch": "refused", "tag": "refused",
                           "renamed": "refused", "claimed": "refused", "upstream": "refused"}, VERDICTS["kit"]
assert VERDICTS["half"] == {**VERDICTS["kit"], "branch": "credential", "tag": "credential", "claimed": "unbound"}
assert VERDICTS["old"] == {**VERDICTS["half"], "claimed": "credential"}
N_PASS_KIT = sum(v == "credential" for v in VERDICTS["kit"].values())

SAY = {
    "refused": "Refused at the auth step: Google's token service finds the condition false ({f}), and the job stops "
               "before any gcloud command runs. Nothing in your project is touched.",
    "unbound": "Refused at the first gcloud call: the token service issues a federated token, but the binding on "
               "sa-documind-cicd admits another repository id, so the account's own token is never minted.",
    "danger": "A credential, for a run you never meant to trust: this token differs from your trust in {f}, and it "
              "still becomes sa-documind-cicd for about an hour.",
    "credential": "A credential: this run becomes sa-documind-cicd for about an hour, and builds and deploys as it.",
    "c1": "GitHub signs a token for this job",
    "c2": "The provider's condition, checked by Google's token service at the auth step",
    "c3": "The binding on sa-documind-cicd, checked when the run first asks for the account's token",
    "c4": "About an hour as sa-documind-cicd",
    "sts_ok": "true: a federated token for principal://iam.googleapis.com/",
    "sts_no": "false: the exchange is refused",
    "holds": f"holds {BIND_ROLE}",
    "not_reached": "not reached",
    "iam_ok": "the token may become the account",
    "iam_no": "the account's token is refused",
    "roles": "project roles: ",
    "actas": "may act as: ",
    "tokens": "may mint tokens as: ",
    "none": "no credential, so nothing it could do",
}
WI_DATA = {"issuer": ISSUER, "env": ENV_NAME, "trust": TRUST, "pool": POOL, "policies": POLICIES,
           "presets": PRESET_TOKENS, "roles": CICD_ROLES, "actas": ACTAS_IDS, "tokens": TOKEN_IDS, "say": SAY}

WI_JS = r"""var D = __DATA__;
function claims(t){
  return {repository: t.repository, repository_id: t.repository_id, ref: t.ref,
          sub: 'repo:' + t.repository + ':' + (t.job === 'promote' ? 'environment:' + D.env : 'ref:' + t.ref)};
}
function evaluate(t, key){
  var c = claims(t), P = D.policies[key];
  var rows = P.clauses.map(function(f){ return {field: f, want: D.trust[f], got: c[f], ok: c[f] === D.trust[f]}; });
  var cond = rows.every(function(x){ return x.ok; }), bind = c[P.bind] === D.trust[P.bind];
  return {claims: c, rows: rows, cond: cond, bind: bind, verdict: cond ? (bind ? 'credential' : 'unbound') : 'refused'};
}
window.__wi = {evaluate: evaluate};
var root = document.getElementById('wi'); if (!root) { return; }
var inp = {repository: document.getElementById('wi-repo'), repository_id: document.getElementById('wi-id'),
           ref: document.getElementById('wi-ref'), job: document.getElementById('wi-job')};
var pol = document.getElementById('wi-pol'), out = document.getElementById('wi-out');
var btns = Array.prototype.slice.call(root.querySelectorAll('.wi-pre button'));
function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
function card(n, title, state){ var c = el('section', 'wi-card wi-' + state); c.appendChild(el('b', 'h', n + '  ' + title)); out.appendChild(c); return c; }
function row(parent, mark, text, cls){ var p = el('p', 'wi-row' + (cls ? ' ' + cls : '')); p.appendChild(el('span', 'wi-m', mark)); p.appendChild(el('span', 'wi-t', text)); parent.appendChild(p); }
function render(){
  var t = {repository: inp.repository.value, repository_id: inp.repository_id.value, ref: inp.ref.value, job: inp.job.value};
  var key = pol.value, P = D.policies[key], r = evaluate(t, key), c = r.claims;
  var off = ['repository_id', 'repository', 'ref'].filter(function(k){ return c[k] !== D.trust[k]; });
  out.textContent = '';
  var v = el('p', 'wi-v');
  if (r.verdict === 'refused') { v.className += ' no'; v.textContent = D.say.refused.replace('{f}', r.rows.filter(function(x){ return !x.ok; }).map(function(x){ return x.field; }).join(', ')); }
  else if (r.verdict === 'unbound') { v.className += ' half'; v.textContent = D.say.unbound; }
  else if (off.length) { v.className += ' bad'; v.textContent = D.say.danger.replace('{f}', off.join(', ')); }
  else { v.className += ' ok'; v.textContent = D.say.credential; }
  out.appendChild(v);
  var c1 = card('1', D.say.c1, 'pass');
  ['repository', 'repository_id', 'ref', 'sub'].forEach(function(k){ row(c1, '\u00b7', k + '  ' + c[k]); });
  var c2 = card('2', D.say.c2, r.cond ? 'pass' : 'stop');
  r.rows.forEach(function(x){ row(c2, x.ok ? '\u2713' : '\u2717', 'assertion.' + x.field + " == '" + x.want + "'" + (x.ok ? '' : '  (this token: ' + x.got + ')'), x.ok ? 'ok' : 'no'); });
  row(c2, '\u2192', r.cond ? D.say.sts_ok + D.pool + '/subject/' + c.sub : D.say.sts_no);
  var c3 = card('3', D.say.c3, !r.cond ? 'skip' : (r.bind ? 'pass' : 'stop'));
  row(c3, '\u00b7', 'principalSet://iam.googleapis.com/' + D.pool + '/attribute.' + P.bind + '/' + D.trust[P.bind] + ' ' + D.say.holds);
  if (!r.cond) { row(c3, '\u00b7', D.say.not_reached); }
  else {
    row(c3, r.bind ? '\u2713' : '\u2717', 'attribute.' + P.bind + ' of this token: ' + c[P.bind], r.bind ? 'ok' : 'no');
    row(c3, '\u2192', r.bind ? D.say.iam_ok : D.say.iam_no);
  }
  var c4 = card('4', D.say.c4, r.verdict === 'credential' ? (off.length ? 'stop' : 'pass') : 'skip');
  if (r.verdict === 'credential') {
    row(c4, '\u00b7', D.say.roles + D.roles.join(', '));
    row(c4, '\u00b7', D.say.actas + D.actas.join(', '));
    row(c4, '\u00b7', D.say.tokens + D.tokens.join(', '));
  } else { row(c4, '\u00b7', D.say.none); }
}
function preset(b){
  var p = D.presets[b.getAttribute('data-p')];
  Object.keys(inp).forEach(function(k){ inp[k].value = p[k]; });
  btns.forEach(function(x){ x.setAttribute('aria-pressed', x === b ? 'true' : 'false'); });
  render();
}
btns.forEach(function(b){ b.addEventListener('click', function(){ preset(b); }); });
['repository', 'repository_id', 'ref'].forEach(function(k){ inp[k].addEventListener('input', function(){
  btns.forEach(function(x){ x.setAttribute('aria-pressed', 'false'); }); render(); }); });
inp.job.addEventListener('change', function(){ btns.forEach(function(x){ x.setAttribute('aria-pressed', 'false'); }); render(); });
pol.addEventListener('change', render);
preset(btns[0]);"""
WI_JS = WI_JS.replace("__DATA__", json.dumps(WI_DATA, ensure_ascii=False, separators=(",", ":")))
JS = "<script>\n(function(){\n'use strict';\n" + WI_JS.replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS and "<tr" not in JS and "\u2014" not in JS and "\u2013" not in JS

# node runs the panel's evaluator on every preset under every trust, and on hand edits; it must be the Python's
EDITS = [{**BASE, "repository": REPO.lower()}, {**BASE, "repository": REPO + " "}, {**BASE, "repository_id": ""},
         {**BASE, "ref": "refs/heads/Main"}, {**BASE, "ref": "main"}, {**BASE, "job": "promote", "ref": "refs/heads/x"}]
CASES = [(t, key) for key in POLICIES for t in list(PRESET_TOKENS.values()) + EDITS]
NODE = ("var window = {}, document = {getElementById: function(){ return null; }};\n"
        "(new Function('window', 'document', " + json.dumps(WI_JS) + "))(window, document);\n"
        "var C = " + json.dumps(CASES) + ";\n"
        "process.stdout.write(JSON.stringify(C.map(function(c){ return window.__wi.evaluate(c[0], c[1]); })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
for (t, key), got in zip(CASES, json.loads(node.stdout)):
    assert got == py_eval(t, key), (t, key, got, py_eval(t, key))
assert all(py_eval(t, "kit")["verdict"] == "refused" for t in EDITS[:5])     # exact comparison: case, space, empty

WI_BUTTONS = "".join(f'<button type="button" data-p="{k}" aria-pressed="{"true" if i == 0 else "false"}">{html.escape(label)}</button>'
                     for i, (k, label, _) in enumerate(PRESETS))
WI_POLICIES = "".join(f'<option value="{k}"' + (" selected" if k == "kit" else "") + f">{html.escape(v)}</option>"
                      for k, v in POLICY_LABEL.items())
WI_JOBS = (f'<option value="release-candidate" selected>release-candidate</option>'
           f'<option value="promote">promote (environment: {ENV_NAME})</option>')

# ================================================================== verbatim kit excerpts
EXCERPTS = {
    "wif_provider": ("terraform/wif.tf - the pool, and the provider: the claims it copies and the three it checks",
                     block(WIF_TF, "# The point is the ABSENCE of a key.", end="# Only this repository may impersonate the deploy identity")),
    "wif_binding": ("terraform/wif.tf - who may become the pipeline's account: one repository, by id; and the two outputs",
                    block(WIF_TF, "# Only this repository may impersonate the deploy identity", end="# Which ref may deploy.")),
    "wif_ref": ("terraform/wif.tf - the trusted ref, and the two accounts whose tokens the pipeline may mint",
                block(WIF_TF, "# Which ref may deploy.")),
    "sa_cicd": ("terraform/sa.tf - the pipeline's account, with an honest account of its shape",
                block(SA_TF, "# The identity GitHub Actions impersonates through Workload Identity Federation.",
                      end="# actAs, scoped to named accounts - NOT project-wide.")),
    "sa_roles": ("terraform/sa.tf - cicd_roles: five roles, and the two its comments refuse",
                 block(SA_TF, "  cicd_roles = [", end="  # The identities this pipeline may act as")),
    "cd_keyless": (".github/workflows/documind-cd.yml - the keyless argument, and the one permission it needs",
                   block(CD_YML, "# Keyless: no service-account JSON anywhere.", end="name: documind-cd") + "\n...\n"
                   + block(CD_YML, "permissions:", n=3)),
    "cd_steps": (".github/workflows/documind-cd.yml - release-candidate: sign in, build, a candidate with no traffic",
                 block(CD_YML, "      - id: auth", end="      # Before the gate spends ten minutes:")),
    "infra_refuse": ("commands/infrastructure.py - an applied trust: a plan that changes it, or inputs that differ, are refused",
                     block(INFRA_PY, '        before, after = change.get("before"), change.get("after")', n=8) + "\n...\n"
                     + block(INFRA_PY, "        explicit = {key: getattr(self.args, key, None) for key in TRUST}", n=5)),
    "rel_values": ("commands/release.py - ci_values(): four values, every source checked against the others",
                   block(REL, "def ci_values(project: str, region: str, tf_dir: Path) -> tuple[dict, dict]:")),
    "rel_env": ("commands/release.py - production_environment(): a required reviewer, or a warning",
                block(REL, "def production_environment(repo: str) -> tuple[str, str]:")),
    "mk_release": ("mk/release.mk - the two targets, both of them reads",
                   block("mk/release.mk", "# The four repository variables .github/workflows/documind-cd.yml reads",
                         end="# ---------- The gate on the exact candidate revision, lesson 11.2 ----------")),
    "rel_keys": ("commands/release.py - cmd_keys(): every account, its user-managed keys, exit 1 on any",
                 block(REL, "def cmd_keys(a) -> int:", end="# ----------------------------------------------------------------")),   # to the next section
    "mk_build": ("the kit's Makefile - build: the gcloud builds submit the workflow's build step runs",
                 block("Makefile", "gcloud builds submit . --project=$(PROJECT) --quiet --config=cloudbuild.yaml", n=2)),
    "cb_logging": ("cloudbuild.yaml - where the build writes its log", block("cloudbuild.yaml", "options:", n=2)),
    "rs_env": ("run-service.yaml - what path=clouddeploy would roll out over documind-api's settings",
               block("run-service.yaml", "          env:", end="          resources:")),
}
fill = filler(EXCERPTS)

# ================================================================== the cells, and what each prints
# Each cell is written between its own lines and stripped of them, so a cell may end on a quote; triple single quotes
# because the Python cells carry docstrings.
CELLS = {
    "trust": r'''
read -r GH_REPO TRUST_ID TRUST_REF < <(python -c 'import json; t = json.load(open("terraform/runbook-project.auto.tfvars.json")); print(t["github_repository"], t["github_repository_id"], t["deploy_ref"])')
export GH_REPO; echo "your lane trusts $GH_REPO, id $TRUST_ID, on $TRUST_REF"
gh repo view "$GH_REPO" --json nameWithOwner,visibility,isFork,parent \
  --jq '"GitHub: \(.nameWithOwner), \(.visibility), " + (if .isFork then "a fork of \(.parent.owner.login)/\(.parent.name)" else "not a fork" end)'
gh api "repos/$GH_REPO" --jq '"its GitHub id: \(.id)"'
gh workflow list --repo "$GH_REPO" --all --json name,state --jq '.[] | "workflow \(.name): \(.state)"'
''',
    "civars": r'''
make ci-vars PROJECT="$PROJECT" REGION="$REGION"
''',
    "configure": r'''
printf '{"reviewers":[{"type":"User","id":%s}]}' "$(gh api user --jq .id)" \
  | gh api -X PUT "repos/$GH_REPO/environments/production" --input - --jq '"environment \(.name): " + ([.protection_rules[].type] | join(", "))'
make ci-vars PROJECT="$PROJECT" REGION="$REGION" | tee "$HOME/ci-vars.txt"
grep '^gh variable set ' "$HOME/ci-vars.txt" | bash
gh variable list --repo "$GH_REPO"
echo "repository secrets: $(gh secret list --repo "$GH_REPO" | wc -l)"
''',
    "region": r'''
make ci-vars PROJECT="$PROJECT" REGION=us-central1     # what a shell left on the Makefile's default would send
''',
    "dispatch": r'''
gh workflow run documind-cd.yml --repo "$GH_REPO" --ref main -f path=candidate && sleep 20
export RUN="$(gh run list --repo "$GH_REPO" --workflow documind-cd.yml --branch main --limit 1 --json databaseId --jq '.[0].databaseId')"
echo "run $RUN: https://github.com/$GH_REPO/actions/runs/$RUN"
until [ "$(gh run view "$RUN" --repo "$GH_REPO" --json jobs --jq '[.jobs[] | select(.name == "release-candidate") | .status] | first')" = completed ]; do sleep 30; done
gh run view "$RUN" --repo "$GH_REPO"
''',
    "reject": r'''
ENV_ID="$(gh api "repos/$GH_REPO/environments/production" --jq .id)"
printf '{"environment_ids":[%s],"state":"rejected","comment":"lesson 11.2 judges this candidate first"}' "$ENV_ID" \
  | gh api -X POST "repos/$GH_REPO/actions/runs/$RUN/pending_deployments" --input - --silent && echo "promote: rejected"
''',
    "left": r'''
python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]


def gc(*args):
    """One gcloud read of the lane, as JSON."""
    out = subprocess.run(["gcloud", *args, f"--project={P}", f"--region={R}", "--format=json"],
                         capture_output=True, text=True, check=True).stdout
    return json.loads(out)


svc = gc("run", "services", "describe", "documind-api")
print("documind-api, last changed by", svc["metadata"].get("annotations", {}).get("serving.knative.dev/lastModifier", "(not recorded)"))
for t in svc["status"].get("traffic", []):
    print(f'  {t.get("percent", 0):>3}%  {t.get("revisionName")}  tag {t.get("tag", "-")}')
cand = next((t["revisionName"] for t in svc["status"].get("traffic", []) if t.get("tag") == "candidate"), None)
if cand:
    rev = gc("run", "revisions", "describe", cand)
    box = rev["spec"]["containers"][0]
    env = {e["name"]: e.get("value") for e in box.get("env", [])}
    print("candidate", cand, "made by", rev["metadata"].get("annotations", {}).get("serving.knative.dev/creator", "(not recorded)"))
    print("  image  ", box["image"])
    print("  GIT_SHA", env.get("GIT_SHA"))
PY
echo "the run built: $(gh run view "$RUN" --repo "$GH_REPO" --json headSha --jq .headSha)"
gh run view "$RUN" --repo "$GH_REPO" --json status,conclusion,jobs --jq '"run: \(.status), \(.conclusion)", (.jobs[] | "  \(.name): \(.conclusion)")'
''',
    "branch": r'''
gh api -X POST "repos/$GH_REPO/git/refs" -f ref=refs/heads/try-a-branch \
  -f sha="$(gh api "repos/$GH_REPO/commits/main" --jq .sha)" --jq '"branch \(.ref) at \(.object.sha[0:7])"'
gh workflow run documind-cd.yml --repo "$GH_REPO" --ref try-a-branch -f path=candidate && sleep 20
BR="$(gh run list --repo "$GH_REPO" --workflow documind-cd.yml --branch try-a-branch --limit 1 --json databaseId --jq '.[0].databaseId')"
gh run watch "$BR" --repo "$GH_REPO" --exit-status > /dev/null; echo "gh run watch $BR: exit $?"
gh run view "$BR" --repo "$GH_REPO"
gh run view "$BR" --repo "$GH_REPO" --log-failed | grep -iE "error|attribute condition" | head -n 5
gh api -X DELETE "repos/$GH_REPO/git/refs/heads/try-a-branch" && echo "branch try-a-branch deleted"
''',
    "iam": r'''
python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import google.auth
from google.auth.transport.requests import AuthorizedSession

P = os.environ["PROJECT"]
creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
iam = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
IAM, CICD = "https://iam.googleapis.com/v1", f"sa-documind-cicd@{P}.iam.gserviceaccount.com"


def call(method, path, **kw):
    """One IAM REST call, as JSON; a failure says which call and why."""
    r = iam.request(method, f"{IAM}/{path}", timeout=30, **kw)
    if r.status_code != 200:
        raise SystemExit(f"{method} {path}: HTTP {r.status_code} {r.text[:200]}")
    return r.json()


prov = call("GET", f"projects/{P}/locations/global/workloadIdentityPools/documind-github/providers/github-oidc")
print("provider", prov["name"].split("/workloadIdentityPools/")[1], "|", prov.get("state"), "| issuer", prov["oidc"]["issuerUri"])
for clause in prov["attributeCondition"].split("&&"):
    print("  condition ", clause.strip())
for attr, expr in sorted(prov["attributeMapping"].items()):
    print("  mapping   ", attr, "=", expr)
for b in call("POST", f"projects/{P}/serviceAccounts/{CICD}:getIamPolicy", json={}).get("bindings", []):
    for m in b["members"]:
        print("sa-documind-cicd:", b["role"], "<-", m.split("/workloadIdentityPools/")[-1] if m.startswith("principalSet:") else m)
keys = call("GET", f"projects/{P}/serviceAccounts/{CICD}/keys", params={"keyTypes": "USER_MANAGED"})
print("user-managed keys on sa-documind-cicd:", len(keys.get("keys", [])))
PY
''',
    "audit": r'''
python - <<'PY'
import datetime as dt, os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import google.auth
from google.auth.transport.requests import AuthorizedSession

P = os.environ["PROJECT"]
creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
logs = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
FILTER = (f'logName="projects/{P}/logs/cloudaudit.googleapis.com%2Factivity" AND timestamp>="{since}" '
          f'AND protoPayload.authenticationInfo.principalEmail="sa-documind-cicd@{P}.iam.gserviceaccount.com"')
r = logs.post("https://logging.googleapis.com/v2/entries:list", timeout=60,
              json={"resourceNames": [f"projects/{P}"], "filter": FILTER, "orderBy": "timestamp asc", "pageSize": 50})
r.raise_for_status()
entries = r.json().get("entries", [])
print(len(entries), "Admin Activity entries by sa-documind-cicd in the last 24 hours")
for e in entries:
    pp = e["protoPayload"]
    behind = [d.get("principalSubject") for d in pp.get("authenticationInfo", {}).get("serviceAccountDelegationInfo", [])
              if d.get("principalSubject")]
    print(e["timestamp"][:19], pp.get("methodName"))
    print("   on behalf of", behind[0] if behind else "(no delegation recorded)")
PY
''',
    "keys": r'''
make keys-check PROJECT="$PROJECT"; echo "exit $?"
''',
    "local": r'''
export GIT_SHA="$(git rev-parse HEAD)"     # the kit commit your checkout holds
make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api GIT_SHA="$GIT_SHA"
make release-candidate PROJECT="$PROJECT" REGION="$REGION" GIT_SHA="$GIT_SHA"
''',
}
CELLS = {k: v.strip("\n") for k, v in CELLS.items()}
CELL_LABELS = {
    "trust": "run in the operator shell, in the kit (reads one local file, then GitHub; writes nothing)",
    "civars": "run in the operator shell, in the kit (terraform output and one GitHub read; writes nothing)",
    "configure": "run in the operator shell, in the kit (writes to your fork: one environment, four variables)",
    "region": "run in the operator shell, in the kit, if you want to see the refusal (nothing runs)",
    "dispatch": "run in the operator shell (starts one run on your fork, then waits about fifteen minutes)",
    "reject": "run in the operator shell, or press Reject on the run's page (a person's no)",
    "left": "run in the operator shell, in the kit (two Cloud Run reads and two GitHub reads; writes nothing)",
    "branch": "run in the operator shell (a branch, a run that fails on purpose, the branch deleted)",
    "iam": "run in the operator shell (three IAM REST reads; writes nothing)",
    "audit": "run in the operator shell (one Cloud Logging read; writes nothing)",
    "keys": "run in the operator shell, in the kit (gcloud describe and list calls; writes nothing)",
    "local": "run in the operator shell, in the kit, only if you could not dispatch (a build, and a candidate as you)",
}
assert set(CELL_LABELS) == set(CELLS)
for name, cell in CELLS.items():                            # every function a cell defines carries a one-line docstring
    for m in re.finditer(r"^def (\w+)\(.*\):\n( +)(.*)$", cell, re.M):
        assert m.group(3).startswith('"""') and m.group(3).endswith('"""'), (name, m.group(1))
    if "<<'PY'" in cell:
        assert 'warnings.filterwarnings("ignore", category=UserWarning)' in cell and cell.count("\nPY") >= 1, name
for name in ("trust", "civars", "configure", "dispatch", "reject", "branch", "keys"):     # the run list's exact commands
    assert f"```bash\n{CELLS[name]}\n```" in RUN_LIST, f"RUN_LIST.md's copy of the {name} cell differs from the page's"
assert "--ref main -f path=candidate" in CELLS["dispatch"] and "--ref main -f path=candidate" in CIVARS_WARN
assert "make ci-vars PROJECT=" in CELLS["configure"] and all(f"gh variable set {v} " in CIVARS_WARN for v in CI_VARS)

# the local operator path: the lines make itself prints, read from the Makefile (Cloud Build's and gcloud's own are yours)
IMAGE = f"asia-south1-docker.pkg.dev/{PROJ}/documind/api:COMMIT"
LOCAL_SHAPE = (f">> building {IMAGE} from services/rag-api\n...\n"
               f"gcloud run services update documind-api --region asia-south1 --project {PROJ} --image {IMAGE} "
               "--no-traffic --tag candidate --update-env-vars GIT_SHA=COMMIT --quiet\n...\n"
               f">> candidate revision: documind-api-000NN-yyy {ECHO_REV}\n"
               f">> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app  {ECHO_CAND}")

RECORDED = {k: pb.recorded(LESSON, f"{k}.txt") for k in
            ("probe_dispatch", "fork_check", "gh_setup", "run_main", "candidate", "run_branch", "iam_rest", "audit", "keys")}
LANE_LABEL = "(the author's lane and fork: your names, ids, shas and times are yours)"
OUTS = {
    "trust": (LANE_LABEL, RECORDED["fork_check"]),
    "civars": ("(release.py run when this page was built, against a stand-in lane with no production environment yet; "
               "your project, number and repository id are yours)", CIVARS_WARN),
    "configure": (LANE_LABEL, RECORDED["gh_setup"]),
    "region": ("(release.py run when this page was built, against the same stand-in: refused before any tool runs)",
               CIVARS_REGION),
    "dispatch": (LANE_LABEL, RECORDED["run_main"]),
    "left": (LANE_LABEL, RECORDED["candidate"]),
    "branch": (LANE_LABEL, RECORDED["run_branch"]),
    "iam": (LANE_LABEL, RECORDED["iam_rest"]),
    "audit": (LANE_LABEL, RECORDED["audit"]),
    "keys": (LANE_LABEL, RECORDED["keys"]),
    "planted": (f"(release.py keys, run when this page was built, against a stand-in project holding sa.tf's {N_SA_SP} "
                "accounts, with one key planted on sa-documind-cicd; never make one to try this)", KEYS_PLANTED),
    "local": ("shape (make's own lines, from the Makefile; Cloud Build's log and gcloud's progress in between are yours)",
              LOCAL_SHAPE),
    "probe": ("(the author's first keyless dispatch, batch 1's probe: what it stopped at, if it stopped)",
              RECORDED["probe_dispatch"]),
}


def bash_window(label: str, code: str) -> str:
    """A command window: the label says where to run it, the copy button copies it."""
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    """What a cell prints: read only."""
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})


# ================================================================== the tables the prose carries
WORDS = {2: "two", 3: "three", 4: "four", 5: "five", 7: "seven", 8: "eight", 9: "nine"}
def tw(head: list, rows: list) -> str:
    """A table that turns into cards on a phone: every cell after the first carries its column's name."""
    out = ['<div class="tw"><div class="tw-scroll" tabindex="0"><table class="comp-table">\n<thead><tr>'
           + "".join(f"<th>{h}</th>" for h in head) + "</tr></thead>\n<tbody>\n"]
    for r in rows:
        out.append("<tr><td>" + r[0] + "</td>" + "".join(f'<td data-label="{html.escape(h)}">{c}</td>' for h, c in zip(head[1:], r[1:]))
                   + "</tr>\n")
    out.append('</tbody></table></div><span class="scroll-hint">&#8596; SWIPE</span></div>\n')
    return "".join(out)


code = lambda s: f"<code>{html.escape(s)}</code>"  # noqa: E731
CALLS_TABLE = tw(["The run's step", "What Google is asked", "What the kit gives sa-documind-cicd", "Status"], [
    ["auth", "Google's token service (STS) exchanges GitHub's token, checking the provider's condition",
     f"the condition in {code('wif.tf')}; {code('sts.googleapis.com')}, among the {len(APIS)} APIs {code('make apis')} enables",
     "granted; proved by the first dispatch"],
    ["Build the API image: the build", "Cloud Build: create a build", code(CICD_ROLES[0]), "granted"],
    ["Build the API image: the upload", f"the source, uploaded to the project's {code('gs://PROJECT_cloudbuild')} bucket, which the step names",
     f"{code('roles/storage.legacyBucketWriter')} on that one bucket, from {code('make build-access')}; no project-wide storage role",
     "granted; proved by the first dispatch"],
    ["Build the API image: the build's account", f"Cloud Build runs the build as the project's default compute account, and asks the submitter to act as it",
     f"actAs on that account, from {code('make build-access')}, refused when the account holds Editor or Owner",
     "granted; proved by the first dispatch"],
    ["Build the API image: the result", f"the build's status, polled until it ends ({code('--async')}; its log stays in Cloud Logging, {code('cloudbuild.yaml')})",
     f"{code(CICD_ROLES[0])}; no role that reads logs is needed", "granted"],
    ["A candidate revision, no traffic", f"Cloud Run: a new revision of {code('documind-api')}, which runs as {code('documind-api-sa')}",
     f"{code(CICD_ROLES[4])}, and actAs on {code('documind-api-sa')} ({code('cicd_actas')})", "granted"],
    ["The candidate answers as the tag; the live gate", f"tokens minted as {code(TOKEN_IDS[0])} and {code(TOKEN_IDS[1])}, through "
     f"{code('iamcredentials.googleapis.com')} (among the {len(APIS)})", f"Token Creator on exactly those two ({code('cicd_eval_tokens')})",
     "granted"],
    ["promote (not run in this lesson)", "Cloud Run: traffic to the candidate, by name", f"{code(CICD_ROLES[4])}, actAs on "
     f"{code('documind-api-sa')}", "granted"],
])
COST_TABLE = tw(["Run", "What it costs", "On your lane"], [
    ["The workflow's jobs", "GitHub's runners, on a public repository", "free"],
    [f"{code('make ci-vars')}, {code('make keys-check')}, the reads of steps 3 and 8", "reads, no model call", "Rs 0"],
    ["The main dispatch: the build", "one Cloud Build of the API image, at Cloud Build's own rate per build-minute",
     f"not in {code('shared/prices.py')}; the plan calls it a few rupees"],
    ["The main dispatch: the live gate", f"at most {len(GOLDEN)} answers, and {N_ISO} requests refused at the roster before any "
     "model call", f"about Rs {RS_GATE} at the course's typical answer of 2,000 tokens in and 300 out (Rs {RS_ANSWER:.2f} each); "
     f"lesson 11.2 reads its log, then pays for a gate of its own: CI keeps no gate record"],
    ["The candidate revision", "no traffic, and the API's floor is zero instances", "Rs 0 while nobody calls it"],
    ["The branch dispatch", "refused at the auth step, before any build or call", "Rs 0"],
    ["The local operator path", "the same build and revision as the dispatch, without the gate", "one Cloud Build"],
])

# ================================================================== numbers for the prose
NEXT = MANIFEST["modules"]["11"]["lessons"]["11.2"]["name"]
STATS = {
    "N_CLAUSES": str(len(CLAUSES)), "N_CLAUSES_W": WORDS[len(CLAUSES)], "N_CLAUSES_CAP": WORDS[len(CLAUSES)].capitalize(),
    "N_ROLES": str(len(CICD_ROLES)), "N_ROLES_W": WORDS[len(CICD_ROLES)], "N_ROLES_CAP": WORDS[len(CICD_ROLES)].capitalize(),
    "N_ACTAS": str(len(ACTAS_IDS)), "N_ACTAS_W": WORDS[len(ACTAS_IDS)],
    "N_TOKENS_W": WORDS[len(TOKEN_IDS)], "N_VARS": str(len(CI_VARS)), "N_VARS_W": WORDS[len(CI_VARS)],
    "N_APIS": str(len(APIS)), "N_PRESETS_W": WORDS[len(PRESETS)], "N_PASS_KIT_W": WORDS[N_PASS_KIT],
    "N_GOLDEN": str(len(GOLDEN)), "N_ISO": str(N_ISO), "RS_GATE": str(RS_GATE), "RS_ANSWER": f"{RS_ANSWER:.2f}",
    "N_SA_SP": str(N_SA_SP), "POOL_ID": POOL_ID, "PROVIDER_ID": PROVIDER_ID, "ISSUER": ISSUER, "BIND_ROLE": BIND_ROLE,
    "TRUST_REPO": REPO, "TRUST_REF": DEPLOY_REF, "ENV_NAME": ENV_NAME, "REGION_DEFAULT": REGION_DEFAULT,
    "CI_VARS": ", ".join(f"<code>{v}</code>" for v in CI_VARS),
    "ROLES": ", ".join(f"<code>{r}</code>" for r in CICD_ROLES),
    "ACTAS": ", ".join(f"<code>{a}</code>" for a in ACTAS_IDS),
    "REVIEWER_LINE": html.escape(REVIEWER_LINE), "NO_KEYS_LINE": html.escape(NO_KEYS_LINE),
    "RS_ENV": ", ".join(f"<code>{n}</code>" for n, _ in RS_ENV),
    "WI_BUTTONS": WI_BUTTONS, "WI_POLICIES": WI_POLICIES, "WI_JOBS": WI_JOBS,
    "CALLS_TABLE": CALLS_TABLE, "COST_TABLE": COST_TABLE, "NEXT_TITLE": html.escape(NEXT),
}


def subst(text: str) -> str:
    """Every %%NAME%% in a part: a window, a table or a number computed above."""
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: wif.tf's {len(CLAUSES)} clauses and its binding by {BIND_ATTR} (parse_trust accepts the rendered condition) | "
      f"sa-documind-cicd: {len(CICD_ROLES)} roles, actAs on {len(ACTAS_IDS)}, tokens for {len(TOKEN_IDS)} | {len(APIS)} APIs with sts, build-access's two grants | "
      f"release.py ci-vars and keys run against stand-ins (warning, region refusal, a planted key) | the panel agrees with "
      f"Python on {len(CASES)} cases (node) | the live gate: about Rs {RS_GATE}")
