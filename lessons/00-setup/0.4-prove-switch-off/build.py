"""Build lesson 0.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Prove the lane, break it once, and switch it off. The lane is up from lesson 0.3. make preflight checks, read-only,
everything the lane stands on; make smoke asks the deployed API the golden gratuity question as documind-ui-sa and asks it
again with no token, which must be refused. The failure on purpose: the smoke without DOCUMIND_TENANT asks as smoke.py's
default tenant, tenant-smoke, which no roster lists, so the API answers 403 "not a member of this tenant"; naming acme
repairs it. Then /health, /ready and /version by hand; the progress kept between sessions (the Terraform state in the
state bucket, infrastructure.py's saved inputs, session-restart.sh's rag-resume.env); make off and zero instances,
read from Cloud Monitoring after the idle window; what still bills with zero instances; a restored session; make down,
whose terraform destroy is refused while managed.tf's data stores carry prevent_destroy, and project deletion.

Offline, at build time: smoke.py run with no URL prints its own checklist (exit 2) and lane.py roster --dry-run prints the
roster plan; both are run here, on the kit, with no network. The standing cost is lessons/00-setup/standing_cost.py's, the
one source 0.1 and 0.3 state it from: every size parsed from the kit's Terraform, priced at Google's Mumbai (asia-south1)
list prices read on 7 October 2026, at shared/prices.py's USD_INR. This build adds no price of its own; it reads from the
kit which lane state still bills which line. Live: every output a lane prints is pb.recorded() from the author's run;
RUN_LIST.md says which command records which file.

    python pagekit/build.py 0.4
"""
import html
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, MANIFEST, block, filler, finish, setup_section, window  # noqa: E402

LESSON = "0.4"
title = ("<title>Lesson 0.4 Prove the lane, break it once, and switch it off - a green smoke, one 403 read and repaired, "
         "zero instances, and what still bills | Netsetos</title>\n")
PROJ, ME = "documind-ai-YOUR-ID", "you@your-company.com"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
/* the four states: buttons, two inputs, one row per thing that runs, bills or stays */
.ls-tabs{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,150px),1fr));gap:8px;margin:0 0 10px;}
.ls-tab{font:inherit;font-size:var(--small-size);line-height:1.35;text-align:left;padding:8px 10px;border:1px solid var(--border);border-radius:10px;background:var(--card);color:var(--navy);cursor:pointer;min-height:max(40px,var(--touch));-webkit-tap-highlight-color:transparent;}
.ls-tab[aria-pressed="true"]{border:2px solid var(--teal);background:var(--teal-light);font-weight:700;}
.ls-tab:active{transform:scale(.98);}
.ls-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,220px),1fr));gap:8px 14px;margin:0 0 6px;}
.ls-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.ls-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.ls-in input[type=range]{width:100%;min-height:44px;accent-color:var(--teal);}
.ls-sum{font-family:var(--mono);font-size:var(--kicker-size);color:var(--teal-dark);margin:6px 0 8px;overflow-wrap:anywhere;}
.ls-row{display:grid;grid-template-columns:minmax(0,1fr) auto;gap:2px 12px;padding:8px 10px;border:1px solid var(--border);border-left-width:4px;border-radius:10px;background:var(--card);margin:0 0 6px;font-size:12.5px;line-height:1.5;color:var(--slate);}
.ls-row b{color:var(--navy);}
.ls-row .rs{font-family:var(--mono);color:var(--navy);text-align:right;white-space:nowrap;}
.ls-row .why{grid-column:1 / -1;overflow-wrap:anywhere;}
.ls-row.bill{border-left-color:#c2410c;}
.ls-row.zero{border-left-color:var(--teal);}
.ls-row.kept{border-left-color:#0891b2;}
"""

# ------------------------------------------------------------------ the shared setup section, with this lesson's pin words
setup = setup_section()
for old, new in (
        ("This lesson is about the kit's own rows, so point acme at them for the duration and put the pin back at the end.",
         "This lesson's smoke checks the kit's own index only when a request ran on it, so point acme at it for the duration "
         "and put the pin back before you switch off, in step 9."),
        ("Leave it until the lesson's last step is done.", "Leave it until step 9, just before <code>make off</code>.")):
    assert setup.count(old) == 1, old
    setup = setup.replace(old, new)
assert "step 3 makes the difference visible." in setup          # this page's step 3 is the browser against the shell

# ------------------------------------------------------------------ verbatim kit excerpts
SMOKE, PRE, SR, INFRA, MAIN, AUTH = ("smoke/smoke.py", "smoke/preflight.sh", "commands/session-restart.sh",
                                     "commands/infrastructure.py", "services/rag-api/main.py", "services/rag-api/auth.py")


def nth_exact(rel: str, start: str, exact: str) -> int:
    """block()'s nth for the line that is exactly `exact` among the lines containing `start`."""
    lines = (KIT / rel).read_text(encoding="utf-8").splitlines()
    hits = [line for line in lines if start in line]
    return hits.index(exact) + 1


EXCERPTS = {
    "mk_preflight": ("Makefile - make preflight: read-only, one shell script",
                     block("Makefile", "# Read-only: is everything `make up` needs in place?", n=4)),
    "preflight_sh": ("smoke/preflight.sh - the whole script", block(PRE, "#!/usr/bin/env sh", n=200)),
    "mk_smoke": ("Makefile - the header's example, and make smoke itself",
                 block("Makefile", "#     make smoke DOCUMIND_API_URL", n=1) + "\n...\n"
                 + block("Makefile", "smoke:", n=2, nth=nth_exact("Makefile", "smoke:", "smoke:"))),
    "smoke_env": ("smoke/smoke.py - what it reads from the environment", block(SMOKE, 'API = os.environ.get("DOCUMIND_API_URL", "").rstrip("/")', n=10)),
    "smoke_first": ("smoke/smoke.py - checks 1 and 2: /health and /ready", block(SMOKE, "    # 1. health", end="    # 3. query - one the corpus ANSWERS.")),
    "smoke_query": ("smoke/smoke.py - check 3: a question the corpus answers, cited", block(SMOKE, "    # 3. query - one the corpus ANSWERS.", end="    # 3a. THE ANN TIER")),
    "smoke_vector": ("smoke/smoke.py - check 3a: the ANN tier, asserted only on vector", block(SMOKE, "    # 3a. THE ANN TIER", end="    # 3b. the same question with NO token")),
    "smoke_door": ("smoke/smoke.py - check 3b: the same question with no token", block(SMOKE, "    # 3b. the same question with NO token", n=7)),
    "smoke_identity": ("smoke/smoke.py - the docstring's identity paragraph", block(SMOKE, "Identity: the ID token IS who you are", n=4)),
    "query_door": ("services/rag-api/main.py - /v1/query asks the roster first", block(MAIN, '@app.post("/v1/query", response_model=RAGResponse)', n=3)),
    "enforce": ("services/rag-api/auth.py - enforce_membership(): the 403 and its words", block(AUTH, "def enforce_membership(")),
    "roster_plan": ("commands/lane.py - roster_plan(): who make roster puts on which roster", block("commands/lane.py", "def roster_plan(", end="def cmd_roster(")),
    "ui_tenant": ("services/frontend/chat.py - the browser's tenant: a reverse lookup of your email", block("services/frontend/chat.py", "def chat_page(user):", n=9)),
    "health_version": ("services/rag-api/main.py - /health and /version", block(MAIN, '@app.get("/health")', end='@app.get("/v1/sources")')),
    "ready": ("services/rag-api/main.py - /ready: the clients built, the index endpoint reached", block(MAIN, '@app.get("/ready")', end="def _guard():")),
    "mk_state": ("Makefile - where the Terraform state lives", block("Makefile", "# Explicit legacy import and teardown targets use this init recipe", n=4)),
    "infra_files": ("commands/infrastructure.py - the two files it keeps beside the Terraform", block(INFRA, 'INPUT_FILE = "runbook-project.auto.tfvars.json"', n=4)),
    "infra_saved": ("commands/infrastructure.py - saved_inputs(): a different project or region is refused", block(INFRA, "    def saved_inputs(self):", n=7)),
    "infra_apply": ("commands/infrastructure.py - apply(): the checked plan is consumed", block(INFRA, "    def apply(self):", n=6)),
    "sr_keys": ("commands/session-restart.sh - _rag_session_keys(): the names it saves", block(SR, "_rag_session_keys() {", n=14)),
    "sr_save": ("commands/session-restart.sh - rag_save_session()", block(SR, "rag_save_session() (", end="rag_restore_api_url() {")),
    "sr_verify": ("commands/session-restart.sh - _rag_verify_base_snapshot(): what a save and a resume require", block(SR, "_rag_verify_base_snapshot() (", end="_rag_graph_exports() {")),
    "git_format": ("commands/git-source.sh - the source session file's format", block("commands/git-source.sh", "  # Save quoted values rather than sourcing data returned by Git.", n=7)),
    "mk_off": ("Makefile - make off: four floors, the GKE workload, then the floors printed", block("Makefile", "# The four switches in one, then the lines that prove it.", n=12)),
    "off_tf": ("terraform/off.tf - the same switches at 23:00 IST, every night", block("terraform/off.tf", "# 23:00 IST, every night", n=7)),
    "alarm_tf": ("terraform/alerts.tf - instance_count, the gauge the zero read uses", block("terraform/alerts.tf", "# Cost control (10 September 2026): a GPU service left warm.", n=5)),
    "mk_floor": ("Makefile - the floor make up deploys with", block("Makefile", "# the UI's floor: 1 on a session day, 0 after", n=2)),
    "vector_tf": ("terraform/vector.tf - the deployed index: one replica, billed while it serves", block("terraform/vector.tf", "# An index and an endpoint are two things", end="# These two outputs are the whole contract")),
    "vector_shard": ("terraform/vector.tf - the machine follows the shard size the API chose", block("terraform/vector.tf", "  # Use the ACTUAL shard size returned by the index", n=9)),
    "spanner_tf": ("terraform/spanner.tf - Enterprise, 100 processing units, by the hour", block("terraform/spanner.tf", "# WHAT THIS COSTS.", n=14)),
    "cloudsql_tf": ("terraform/cloudsql.tf - the kit's own price for a db-f1-micro", block("terraform/cloudsql.tf", "# WHAT THIS COSTS.", n=4)),
    "gke_tf": ("terraform/gke.tf - the cluster is regional, and its one lab node", block("terraform/gke.tf", 'resource "google_container_cluster" "autopilot"', n=3)
               + "\n...\n" + block("terraform/gke.tf", 'resource "google_container_node_pool" "lab"', n=12)),
    "network_tf": ("terraform/network.tf - the VPC connector: never fewer than two instances", block("terraform/network.tf", 'resource "google_vpc_access_connector" "conn"', n=8)),
    "sr_resume": ("commands/session-restart.sh - rag_resume(): the saved names back, then the project's settings", block(SR, "rag_resume() {", n=15)),
    "sr_resume_end": ("commands/session-restart.sh - rag_resume(): the last lines", block(SR, "  printf 'PASS: restored project %s", n=8)),
    "sr_check": ("commands/session-restart.sh - rag_check_resumed_api(): the three GETs", block(SR, "rag_check_resumed_api() {", n=9)),
    "mk_down": ("Makefile - make down: the services first, then terraform destroy, then the list", block("Makefile", "# destroy needs the SAME variables plan/apply need", end="# ---------- Teardown")),
    "mk_down_services": ("Makefile - down-services: what terraform destroy does not own", block("Makefile", "# The eight services the deploy scripts create with gcloud run deploy", end="# SLM_REGION is deliberately")),
    "managed_tf": ("terraform/managed.tf - the guard on the two Vertex AI Search data stores", block("terraform/managed.tf", "  # A parser/identity change or disabling managed_search", n=6)),
    "mk_managed": ("Makefile - the switch that declares them, and the variable destroy passes", block("Makefile", "MANAGED_SEARCH  ?= true", n=1) + "\n...\n" + block("Makefile", "                -var managed_search=$(MANAGED_SEARCH) \\", n=1)),
}
E = {k: v[1] for k, v in EXCERPTS.items()}
assert E["mk_smoke"].endswith("smoke:\n\t$(PY) smoke/smoke.py"), E["mk_smoke"]
assert E["preflight_sh"] == (KIT / PRE).read_text(encoding="utf-8").rstrip("\n") and E["preflight_sh"].endswith("exit $bad")
assert 'TENANT = os.environ.get("DOCUMIND_TENANT", "tenant-smoke")' in E["smoke_env"]
assert E["smoke_query"].rstrip().endswith('bad("query", f"status={st} body={body[:120]}")')
assert 'bad("no token refused", f"status={st} - the service answered an anonymous caller")' in E["smoke_door"]
assert E["enforce"].rstrip().endswith('raise HTTPException(403, "not a member of this tenant")')
assert "enforce_membership(user[\"email\"], req.tenant_id)" in E["query_door"]
assert E["health_version"].rstrip().endswith('"git_sha": os.environ.get("GIT_SHA", "unknown")}') and E["ready"].rstrip().endswith('return {"status": "ready"}')
assert E["mk_state"].rstrip().endswith("TFSTATE_PREFIX     ?= documind/$(PROJECT)")
assert E["sr_save"].rstrip().endswith("printf 'PASS: saved nonsecret restart settings to %s\\n' \"$root/rag-resume.env\"\n)")
assert E["sr_verify"].rstrip().endswith('git -C "$RAG_SOURCE_REPO" cat-file -e "$SOURCE_COMMIT^{commit}"\n)')
assert E["mk_off"].rstrip().endswith('echo "$$s: min-instances $$f"; done')
assert E["mk_down"].rstrip().endswith('echo ">>   gcloud projects delete $(PROJECT)"; exit $$rc')
assert E["mk_down_services"].rstrip().endswith("@rm -f .candidate-revision .previous-revision")
assert E["managed_tf"].rstrip().endswith("  lifecycle {\n    prevent_destroy = true\n  }")
assert E["sr_check"].rstrip().endswith("printf 'PASS: API health, readiness and version requests succeeded.\\n'\n}")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
flat = lambda s: re.sub(r"\s+", " ", s)                             # noqa: E731
flatc = lambda s: flat(re.sub(r"\n\s*#\s*", " ", s))                # noqa: E731
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (SMOKE, PRE, SR, INFRA, MAIN, AUTH, "Makefile",
       "evals/golden.jsonl", "gke/README.md", "gke/vllm-deployment.yaml", "README.md", "commands/lane.py", "commands/lesson-12.4.sh",
       "commands/lesson-7.2.sh", "commands/lesson-8.4.sh", "commands/lesson-12.2.sh", "commands/lesson-12.3.sh",
       "commands/lesson-12.5.sh", "commands/lesson-12.8.sh")}
TF = {p: (KIT / "terraform" / p).read_text(encoding="utf-8") for p in ("vector.tf", "spanner.tf", "cloudsql.tf", "gke.tf",
                                                                       "managed.tf", "firestore.tf", "storage.tf", "off.tf")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
recipe = lambda name: MK[MK.index(f"\n{name}:") + 1:].split("\n\n", 1)[0]      # noqa: E731

# preflight: eleven checks, read-only
P = src[PRE]
TOOLS = re.search(r"for tool in ([\w ]+); do", P).group(1).split()
APIS = re.search(r"for api in (.*?); do", P, re.S).group(1).replace("\\", " ").split()
OK_LINES = [line for line in P.splitlines() if re.search(r'(^|&& |\s)ok "', line)]
N_PREFLIGHT = len(TOOLS) + len(OK_LINES) - 1                         # the tools line runs once per tool
assert TOOLS == ["gcloud", "terraform", "make", "python"] and len(APIS) == 22 and N_PREFLIGHT == 11, (TOOLS, len(APIS), N_PREFLIGHT)
assert "Read-only. Everything `make up` will need, checked before anything is created:" in P and "Creates nothing." in P
assert 'echo "preflight clean - next: make plan, then make up"' in P and "exit $bad" in P
assert "TFSTATE_BUCKET=documind-ai-live-0910-tfstate" in P            # the usage line: the bucket named after the project

# smoke: the default tenant, the golden question, what a 403 prints
S = src[SMOKE]
SMOKE_TENANT = re.search(r'TENANT = os.environ.get\("DOCUMIND_TENANT", "([\w-]+)"\)', S).group(1)
SMOKE_Q = re.search(r'"DOCUMIND_SMOKE_QUESTION",\s*"([^"]+)"\)', S).group(1)
GOLDEN = [json.loads(line) for line in src["evals/golden.jsonl"].splitlines() if line.strip()]
ROW = next(r for r in GOLDEN if r["question"] == SMOKE_Q)
assert (SMOKE_TENANT, ROW["id"], ROW["tenant"], ROW["must_contain"], ROW["must_retrieve"]) == \
    ("tenant-smoke", "lk-16", "acme", ["five years"], ["payment_of_gratuity_act_1972"]), (SMOKE_TENANT, ROW)
assert "This question is golden.jsonl's lk-16" in S and "must be a member of DOCUMIND_TENANT, or check 3 is a 403" in flat(S)
# no roster lists the smoke's default tenant: make roster's plan names the three golden tenants and nothing else
LANE = src["commands/lane.py"]
assert 'GOLDEN_TENANTS = ("acme", "zeta", "globex")' in LANE and SMOKE_TENANT not in LANE
assert not [p for p in pb.kit_runtime_files("*.py") if SMOKE_TENANT in p.read_text(encoding="utf-8", errors="ignore") and p.name != "smoke.py"]
assert "smoke:\n\t$(PY) smoke/smoke.py" in src["Makefile"] and "DOCUMIND_TENANT" not in recipe("smoke")
assert "DOCUMIND_TENANT=$(TENANT)" in recipe("smoke-all")             # smoke-all passes it; plain make smoke does not
assert "make smoke DOCUMIND_API_URL=https://documind-api-NUMBER.us-central1.run.app DOCUMIND_PROJECT=documind-ai-live-0901 DOCUMIND_TENANT=acme" in src["README.md"]

# the UI: your tenant by email; the floor make up deploys with
assert "MIN_INSTANCES ?= 0" in src["Makefile"]
MIN_SCRIPTS = {s: re.search(r"gcloud run deploy (documind-[\w-]+)", src[f"commands/{s}"]).group(1)
               for s in ("lesson-12.4.sh", "lesson-7.2.sh", "lesson-8.4.sh") if "--min-instances=${MIN_INSTANCES:-0}" in src[f"commands/{s}"]}
FIXED_ZERO = [s for s in ("lesson-12.5.sh", "lesson-12.2.sh", "lesson-12.8.sh") if "--min-instances=0 " in src[f"commands/{s}"]]
assert MIN_SCRIPTS == {"lesson-12.4.sh": "documind-ui", "lesson-7.2.sh": "documind-mcp", "lesson-8.4.sh": "documind-agent"}, MIN_SCRIPTS
assert len(FIXED_ZERO) == 3 and "min-instances" not in src["commands/lesson-12.3.sh"]
OFF = recipe("off")
OFF_SERVICES = re.search(r"for s in ([\w -]+); do", OFF).group(1).split()
assert OFF_SERVICES == ["documind-slm", "documind-vllm", "documind-gateway", "documind-ui"], OFF_SERVICES
UNFLOORED = [svc for svc in MIN_SCRIPTS.values() if svc not in OFF_SERVICES]
assert UNFLOORED == ["documind-mcp", "documind-agent"]
UP_SERVICES = re.search(r"^SERVICES   = ([\w ]+)$", src["Makefile"], re.M).group(1).split()
assert UP_SERVICES == ["ingest", "api", "admin", "ui", "chat", "mcp", "agent"]
OFF_PRESENT = [s for s in OFF_SERVICES if s.removeprefix("documind-") in UP_SERVICES]
assert OFF_PRESENT == ["documind-ui"]                                 # of make off's four, make up deploys the UI only
for t in ("slm-off", "vllm-off", "gateway-off", "gke-down"):
    assert f"-$(MAKE) {t} PROJECT=$(PROJECT)" in OFF
assert '"vLLM workload removed; the cluster and any Standard lab node remain (gke.tf) - make down removes them"' in recipe("gke-down")
assert 'schedule    = "0 23 * * *"' in TF["off.tf"] and 'time_zone   = "Asia/Kolkata"' in TF["off.tf"]

# saving progress: the inputs file, the session keys
CRITICAL = re.search(r"CRITICAL = \((.*?)\)", src[INFRA], re.S).group(1)
CRITICAL = re.findall(r'"(\w+)"', CRITICAL)
assert CRITICAL == ["project_id", "region", "billing_account_id", "github_repository", "github_repository_id", "deploy_ref"]
assert "self.selected.unlink(missing_ok=True)" in E["infra_apply"]
KEYS_BODY = src[SR].split("_rag_session_keys() {", 1)[1].split("\n}\n", 1)[0].split("printf '%s\\n'", 1)[1]
KEYS = re.findall(r"\b[A-Z][A-Za-z0-9_]+\b", KEYS_BODY)
assert len(KEYS) == len(set(KEYS)) == 48 and KEYS[:2] == ["PROJECT", "REGION"] and "TFSTATE_BUCKET" in KEYS, (len(KEYS), KEYS[:4])
assert all(k in KEYS for k in ("PROJECT_NUMBER", "OPERATOR_EMAIL", "TFSTATE_BUCKET", "SOURCE_COMMIT", "GIT_SHA"))
assert "_rag_stop 'Missing rag-source-session.env; restore the original source setup.'" in src[SR]
assert "chmod 600 \"$temporary\"" in src[SR] and "nonsecret" in src[SR]
assert '"$snapshot:deploy/terraform/backend.tf"' in (KIT / "commands/git-source.sh").read_text(encoding="utf-8")   # see RUN_LIST: a learner clone has no deploy/
assert 'for endpoint in health ready version; do' in E["sr_check"]

# teardown: what make down removes, what it cannot, and why terraform destroy stops
DOWN = MK[MK.index("\ndown: guard-project"):MK.index("# ---------- Teardown")]
assert "terraform destroy -input=false -auto-approve $(TF_VARS)" in DOWN and "-target" not in DOWN and "state rm" not in DOWN
assert "data store" not in DOWN.lower() and "vertex ai search" not in DOWN.lower()      # the closing list never names the protected stores
assert re.search(r"^MANAGED_SEARCH  \?= true$", src["Makefile"], re.M) and "-var managed_search=$(MANAGED_SEARCH)" in MK
assert "TF_VARS = -var project_id=$(PROJECT) -var region=$(REGION) $(TF_EXTRA_VARS)" in src["Makefile"]
assert 'managed_tenants = var.managed_search ? toset(var.tenants) : toset([])' in TF["managed.tf"]
assert 'default     = ["acme", "zeta"]' in TF["managed.tf"]
assert 'delete_protection_state         = "DELETE_PROTECTION_ENABLED"' in TF["firestore.tf"]
assert TF["storage.tf"].count("force_destroy               = false") == 2
DOWN_LIST = [m.group(1) for m in re.finditer(r'echo ">>   ([^"]+)"', DOWN)]
assert len(DOWN_LIST) == 6 and DOWN_LIST[-1] == "gcloud projects delete $(PROJECT)", DOWN_LIST
assert "protected managed search stores (`prevent_destroy = true`)" in src["README.md"]
DOWN_SVCS = re.search(r"^DOWN_SERVICES     = ([\w -]+)$", src["Makefile"], re.M).group(1).split()
assert len(DOWN_SVCS) == 8 and DOWN_SVCS[-1] == "documind-gchat"

# ------------------------------------------------------------------ the standing cost: what bills by the hour with no traffic
# One source for the three Module 0 pages that state it (0.1's per day and per weekend, 0.3's hourly items, this page's
# daily cost of a lane left up), so they cannot disagree: lessons/00-setup/standing_cost.py parses every size from the
# kit's Terraform and prices it at Google's Mumbai (asia-south1) list prices, read on 7 October 2026, at the kit's USD_INR
# (its docstring says how). This page adds no price of its own: it states the module's per-item figures and totals, and
# which lane state still bills which line.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import standing_cost as sc  # noqa: E402

USD_INR, PRICE_DATE = sc.USD_INR, "7 October 2026"
SC_SRC = Path(sc.__file__).read_text(encoding="utf-8")
assert f"Mumbai (asia-south1), read on {PRICE_DATE}" in SC_SRC and sc.LANE_REGION == "asia-south1"
PAGES = {
    "vertex": "https://cloud.google.com/vertex-ai/pricing",                      # Vector Search, serving, per node hour
    "spanner": "https://cloud.google.com/spanner/pricing",                       # regional compute, per node hour, all three replicas
    "sql": "https://cloud.google.com/sql/pricing",                               # db-f1-micro, per hour; SSD, per GiB hour
    "gke": "https://cloud.google.com/kubernetes-engine/pricing",                 # $0.10 per cluster hour; the free-tier credit: zonal and Autopilot only
    "compute": "https://cloud.google.com/products/compute/pricing/general-purpose",   # E2, on demand
    "disk": "https://cloud.google.com/compute/disks-image-pricing",              # Standard provisioned space
    "vpc": "https://cloud.google.com/vpc/pricing",                               # connector instances bill as Compute Engine VMs
    "connector": "https://docs.cloud.google.com/vpc/docs/configure-serverless-vpc-access",   # a connector's default machine type: e2-micro
    "idle": "https://docs.cloud.google.com/run/docs/about-instance-autoscaling",  # idle instances kept up to 15 minutes
    "shutdown": "https://docs.cloud.google.com/resource-manager/docs/delete-restore-projects",   # shutting down stops billing; 30 days to restore
}
# step 10 links the pages the module cites for its prices
assert all(PAGES[k] in SC_SRC for k in ("vertex", "spanner", "sql", "gke", "compute", "disk", "vpc", "connector"))

# the six lines the prose names, in the order step 10 reads their declarations, and the sizes the prose and the excerpt
# labels put in words: one replica, Enterprise at 100 processing units, two instances, one lab node, never fewer than two
LINES = [k for k, *_ in sc.ITEMS]
assert LINES == ["index", "spanner", "sql", "gkefee", "gkenode", "conn"], LINES
assert (sc.VS_REPLICAS, sc.SP_EDITION, sc.SP_PU, len(sc.SQL), sc.GKE_NODES, sc.CONN_MIN) == (1, "ENTERPRISE", 100, 2, 1, 2)
assert "including an existing index whose API-selected size was MEDIUM" in flatc(TF["vector.tf"])
assert "A deployed index bills while serving" in flatc(TF["vector.tf"]) and "it bills by the hour while it exists" in flatc(TF["spanner.tf"])
# Cloud SQL's comment gives the kit's rough monthly price; step 10 says so, and the table prices the tier from the list
assert re.search(r"db-f1-micro, zonal, 10 GB, no backups: roughly \$\d+-\d+ \(Rs [\d,]+-[\d,]+\) a month", flatc(TF["cloudsql.tf"]))
# the page notes that two of the excerpts promise make down removes them, and that the destroy never starts (step 12)
assert "Either way, `make down` removes it." in flatc(TF["spanner.tf"]) and "`make down` destroys it" in flatc(TF["cloudsql.tf"])

# Which lane state still bills which line, read from the kit. make off floors four services and runs gke-down, which
# deletes the vLLM manifest's Deployment and Service from the cluster (kubectl delete -f) and nothing else: the cluster
# and its lab pool (a fixed node_count, no autoscaling) stay, so the fee and the node bill on, as gke-down's message and
# the README say. make down runs down-services and managed-stores-down, then terraform destroy, which managed.tf's
# prevent_destroy refuses whole while MANAGED_SEARCH is true, its default (asserted under teardown above): all six bill
# on. Only deleting the project stops them.
GKE_DOWN = recipe("gke-down")
assert "kubectl delete -f - --ignore-not-found" in GKE_DOWN and "gke/vllm-deployment.yaml" in GKE_DOWN
assert not re.search(r"clusters (delete|resize)|node-pools|terraform", OFF + GKE_DOWN)
assert re.findall(r"^kind: (\w+)$", src["gke/vllm-deployment.yaml"], re.M) == ["Deployment", "Service"]
assert "autoscaling" not in TF["gke.tf"].split('resource "google_container_node_pool" "lab"', 1)[1].split("\n}\n", 1)[0]
assert "deleting the cluster stops the $0.10/hr fee as well" in src["gke/README.md"]
assert "The regional control-plane fee and the Standard CPU node continue while provisioned." in src["README.md"]
BUDGET = int(re.search(r"^BUDGET_AMOUNT      \?= (\d+)$", src["Makefile"], re.M).group(1))
assert BUDGET == 5000 and "# In the billing account's currency (an Indian account is INR)." in src["Makefile"]


def usd(x: float) -> str:
    """A list price as the pricing page prints it: plain decimals, no exponent."""
    return "$" + ("%.10f" % x).rstrip("0").rstrip(".")


def rs_day(key: str, shard: str) -> int:
    """One line's rupees a day, the module's figure, rounded as the panel's Math.round rounds."""
    return sc.r0(sc.item_usd(key, shard) * sc.DAY_H * USD_INR)


def size(key: str, shard: str) -> str:
    """A line's size as the table and the panel print it: the index names the machine its shard size gives it."""
    return f"{sc.VS_REPLICAS} replica of {sc.SHARDS[shard]}" if key == "index" else next(s for k, _l, _w, s, _u in sc.ITEMS if k == key)


WORDS = {2: "two", 3: "three", 4: "four", 6: "six", 7: "seven", 8: "eight"}


def inr(x: float) -> str:
    """Whole rupees, grouped the Indian way: 66,145 and 1,00,000."""
    s = str(int(round(x)))
    head, tail = s[:-3], s[-3:]
    groups = []
    while len(head) > 2:
        groups.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + groups + [tail])


# the table in step 10: the module's lines for the MEDIUM index vector.tf's comment records, each with its Mumbai unit price
PRICE = sc.PRICES
UNIT = {"index": f"{usd(PRICE['vs:' + sc.SHARDS['medium']])} a node hour (Vector Search, {sc.SHARDS['medium']})",
        "spanner": f"{usd(PRICE['spanner:' + sc.SP_EDITION])} a node hour (1,000 units, all three replicas); {sc.SP_PU} units are {sc.SP_PU / 1000:g} of a node",
        "sql": f"{usd(PRICE['sql:' + sc.SQL_TIER])} an hour each, plus {usd(PRICE['sql:ssd_gib'])} a GiB hour of SSD",
        "gkefee": f"${PRICE['gke:cluster']:.2f} a cluster hour (no free-tier credit for a regional cluster)",
        "gkenode": f"{usd(PRICE['ce:' + sc.GKE_MACHINE])} an hour, plus {usd(PRICE['pd:standard_gib'])} a GiB hour for the disk",
        "conn": f"{usd(PRICE['ce:e2-micro'])} an hour each (e2-micro, the connector's default)"}
assert set(UNIT) == set(LINES) and not re.search(r"\de-\d", "".join(UNIT.values()))
assert all(float(usd(p)[1:]) == p for p in PRICE.values())            # every list price prints as the module holds it
rows = []
for key, label, where, _s, _u in sc.ITEMS:
    rows.append(f'<tr><td>{html.escape(label)}</td><td data-label="Declared"><code>{html.escape(where)}</code>: {html.escape(size(key, "medium"))}</td>'
                f'<td data-label="Unit price">{html.escape(UNIT[key])}</td><td data-label="Rs a day">Rs {inr(rs_day(key, "medium"))}</td></tr>')
rows.append(f'<tr><td>Total</td><td data-label="Declared">six lines, none of them a Cloud Run instance</td>'
            f'<td data-label="Unit price">Mumbai list prices of {PRICE_DATE}, Rs {USD_INR} to the dollar</td>'
            f'<td data-label="Rs a day"><strong>Rs {inr(sc.PER_DAY["medium"])}</strong></td></tr>')
COST_TABLE = ('<div class="tw"><div class="tw-scroll" tabindex="0"><table class="comp-table">\n'
              '<thead><tr><th>Line</th><th>Declared</th><th>Unit price</th><th>Rs a day</th></tr></thead>\n<tbody>\n'
              + "\n".join(rows) + '\n</tbody></table></div><span class="scroll-hint">&#8596; SWIPE</span></div>')

# ------------------------------------------------------------------ the four states, for the panel in step 1
def hourly(cls: str, why: str, **why_for: str) -> dict:
    """What one state does to each of the six lines: 'bill' or 'zero', and why (one line may have its own reason)."""
    return {k: [cls, why_for.get(k, why)] for k in LINES}


STATES = {
    "up": {"label": "Up", "cloud_run": ("bill", "Seven services, each scaled to zero when idle (every floor is 0 as make up deploys them). "
                                                "They bill per request while they serve; a floor you raise bills all day."),
           "hourly": hourly("bill", "bills"), "corpora": ("kept", "kept: the RAG Engine corpora for acme and zeta, billed by size"),
           "data": ("kept", "kept: Firestore, the buckets, the two data stores, the BigQuery views, billed by size")},
    "off": {"label": "Off", "cloud_run": ("zero", "make off forces the floor to 0 on documind-ui and on Module 9's three; with every floor at 0, "
                                                  "each service falls to zero instances within 15 minutes of its last request, and bills nothing."),
            "hourly": hourly("bill", "still bills: make off does not touch it",
                             gkefee="still bills: make off's gke-down removes the vLLM workload, not the cluster",
                             gkenode="still bills: make off's gke-down removes the vLLM workload, not the node"),
            "corpora": ("kept", "kept, billed by size"), "data": ("kept", "kept, billed by size")},
    "down": {"label": "Down", "cloud_run": ("zero", "deleted by down-services, with the candidate tag and the context caches."),
             "hourly": hourly("bill", "still bills: terraform destroy is refused while the two data stores carry prevent_destroy"),
             "corpora": ("zero", "deleted by managed-stores-down"),
             "data": ("kept", "kept: Firestore's delete protection, buckets that hold objects, the protected data stores, the views")},
    "gone": {"label": "Deleted", "cloud_run": ("zero", "gone with the project."),
             "hourly": hourly("zero", "stops: shutting a project down stops all its billing"),
             "corpora": ("zero", "gone with the project"),
             "data": ("zero", "deleted at the end of the 30 days in which the project can still be restored")},
}
SHARD_OF = {"MEDIUM": "medium", "SMALL": "small"}                     # the panel's select values (part a), the module's shards
PANEL = {"states": STATES, "inr": USD_INR, "dayH": sc.DAY_H, "date": PRICE_DATE,
         "lines": {opt: [{"key": k, "what": label, "unit": size(k, shard), "usd": sc.item_usd(k, shard)} for k, label, *_ in sc.ITEMS]
                   for opt, shard in SHARD_OF.items()}}
PART_A = pb.part(LESSON, "a")
assert all(f'<option value="{opt}"' + (" selected" if shard == "medium" else "") + f'>{opt}: {sc.SHARDS[shard]}' in PART_A
           for opt, shard in SHARD_OF.items())
WEEK_DAYS = 5                                                          # the gap between two weekend sessions: the panel opens on it
assert f'id="ls-days" min="1" max="30" step="1" value="{WEEK_DAYS}"' in PART_A


def panel_rs(state: str, shard: str, days: int = 1) -> int:
    """The rupees the panel prints for a state: its script's sum, line by line in the same order, rounded as Math.round."""
    day = 0
    for line in PANEL["lines"][next(o for o, s in SHARD_OF.items() if s == shard)]:
        if STATES[state]["hourly"][line["key"]][0] == "bill":
            day += line["usd"] * PANEL["dayH"] * PANEL["inr"]
    return sc.r0(day * days)


# every state's figure is 0.1's: up, after make off and after a refused make down, all six lines bill on; deleted, none
for shard in sc.SHARDS:
    assert [panel_rs(st, shard) for st in STATES] == [sc.PER_DAY[shard]] * 3 + [0], shard
WEEK_MEDIUM = sc.r0(sc.HOURLY["medium"] * sc.DAY_H * WEEK_DAYS * USD_INR)
assert panel_rs("off", "medium", WEEK_DAYS) == WEEK_MEDIUM            # step 10's five days are what the panel opens on
JS = """<script>
(function(){
  'use strict';
  var D = %s;
  var root = document.getElementById('ls'); if (!root) return;
  var tabs = root.querySelectorAll('.ls-tab'), shard = document.getElementById('ls-shard'), days = document.getElementById('ls-days'),
      daysV = document.getElementById('ls-days-v'), sum = document.getElementById('ls-sum'), out = document.getElementById('ls-rows'), state = 'up';
  function rs(x){ return 'Rs ' + Math.round(x).toLocaleString('en-IN'); }
  function row(cls, name, why, money){
    var d = document.createElement('div'); d.className = 'ls-row ' + cls;
    var b = document.createElement('b'); b.textContent = name; d.appendChild(b);
    var r = document.createElement('span'); r.className = 'rs'; r.textContent = money; d.appendChild(r);
    var w = document.createElement('span'); w.className = 'why'; w.textContent = why; d.appendChild(w);
    out.appendChild(d);
  }
  function render(){
    var s = D.states[state], ls = D.lines[shard.value], n = parseInt(days.value, 10), day = 0;
    daysV.textContent = n + (n === 1 ? ' day' : ' days');
    out.textContent = '';
    row(s.cloud_run[0], 'Cloud Run services', s.cloud_run[1], s.cloud_run[0] === 'zero' ? 'Rs 0' : 'per use');
    ls.forEach(function(l){
      var h = s.hourly[l.key], bills = h[0] === 'bill', perDay = l.usd * D.dayH * D.inr;
      if (bills){ day += perDay; }
      row(bills ? 'bill' : 'zero', l.what, l.unit + ': ' + h[1], bills ? rs(perDay) + ' a day' : 'Rs 0');
    });
    row(s.corpora[0], 'RAG Engine corpora', s.corpora[1], s.corpora[0] === 'zero' ? 'Rs 0' : 'by size');
    row(s.data[0], 'Firestore, buckets, data stores, views', s.data[1], s.data[0] === 'zero' ? 'Rs 0' : 'by size');
    sum.textContent = s.label + ': ' + (day ? rs(day) + ' a day by the hour alone, ' + rs(day * n) + ' for ' + n + (n === 1 ? ' day' : ' days')
      : 'nothing bills by the hour') + ' (Mumbai list prices of ' + D.date + ', Rs ' + D.inr + ' to the dollar)';
  }
  Array.prototype.forEach.call(tabs, function(t){ t.addEventListener('click', function(){
    state = t.getAttribute('data-s');
    Array.prototype.forEach.call(tabs, function(u){ u.setAttribute('aria-pressed', u === t ? 'true' : 'false'); });
    render(); }); });
  shard.addEventListener('change', render); days.addEventListener('input', render); days.addEventListener('change', render);
  render();
})();
</script>
""" % json.dumps(PANEL)
assert "</" not in JS.split("<script>", 1)[1].rsplit("</script>", 1)[0]

# ------------------------------------------------------------------ the offline runs: the kit's own output, no network
QUIET = {"PATH": str(Path(sys.executable).parent), "SYSTEMROOT": os.environ.get("SYSTEMROOT", ""), "PYTHONIOENCODING": "utf-8",
         "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUTF8": "1"}        # no gcloud on PATH, no DOCUMIND_* in the environment


def offline(args: list) -> tuple:
    r = subprocess.run([sys.executable] + args, cwd=str(KIT), capture_output=True, text=True, encoding="utf-8", env=QUIET)
    assert not r.stderr.strip(), r.stderr[-800:]
    return r.returncode, r.stdout.rstrip("\n")


rc, SMOKE_NO_URL = offline(["smoke/smoke.py"])
assert rc == 2 and SMOKE_NO_URL.startswith("DOCUMIND_API_URL is not set") and "3b. the same question with no token -> 401/403" in SMOKE_NO_URL
SMOKE_NO_URL += f"\nexit {rc}"
rc, ROSTER_PLAN = offline(["commands/lane.py", "--project", PROJ, "roster", "--tenant", "acme", "--members", ME, "--dry-run"])
assert rc == 0 and ROSTER_PLAN.startswith(f"would put {ME} on acme\n") and ROSTER_PLAN.endswith("would set globex: data_region=in")
# the roster lowercases every email, the placeholder's YOUR-ID with it; a real project id is lowercase already, so the
# page shows the placeholder as the course writes it
assert ROSTER_PLAN.count(PROJ.lower()) == 10
ROSTER_PLAN = ROSTER_PLAN.replace(PROJ.lower(), PROJ)
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
assert [line.rsplit(" ", 1)[1] for line in ROSTER_PLAN.splitlines() if f" {UI_SA} " in line] == ["acme", "zeta", "globex"]
assert SMOKE_TENANT not in ROSTER_PLAN

# ------------------------------------------------------------------ the cells: what you run, and what the lane prints
ZERO_PY = r'''import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P = os.environ["PROJECT"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
q = urllib.parse.urlencode({"filter": 'metric.type="run.googleapis.com/container/instance_count" AND resource.type="cloud_run_revision"',
                            "interval.startTime": iso(now - dt.timedelta(minutes=30)), "interval.endTime": iso(now),
                            "aggregation.alignmentPeriod": "60s", "aggregation.perSeriesAligner": "ALIGN_MAX",
                            "aggregation.crossSeriesReducer": "REDUCE_SUM", "aggregation.groupByFields": "resource.label.service_name"})
req = urllib.request.Request(f"https://monitoring.googleapis.com/v3/projects/{P}/timeSeries?{q}", headers={"Authorization": f"Bearer {tok}"})
last = {}
for s in json.load(urllib.request.urlopen(req, timeout=60)).get("timeSeries", []):
    up = [p["interval"]["endTime"] for p in s.get("points", []) if int(p["value"].get("int64Value", 0)) > 0]
    last[s["resource"]["labels"]["service_name"]] = max(up) if up else None
names = sorted(set(last) | {"documind-" + s for s in ("ingest", "api", "admin", "ui", "chat", "mcp", "agent")})
print(f"instances per Cloud Run service, {iso(now - dt.timedelta(minutes=30))[11:16]} to {iso(now)[11:16]} UTC, one point a minute (Cloud Monitoring):")
for n in names:
    t = last.get(n)
    print(f"  {n:17} " + (f"last instance at {t[11:16]} UTC" if t else "no instance in the window"))
fresh = iso(now - dt.timedelta(minutes=3))      # a sample becomes visible up to 120 s after it is taken
still = [n for n in names if last.get(n) and last[n] >= fresh]
print("services with an instance in the last 3 minutes: " + (", ".join(still) if still else "none - zero instances"))'''
for s in UP_SERVICES:
    assert f'"{s}"' in ZERO_PY

CELLS = {
    "ui": 'echo "https://documind-ui-$NUMBER.$REGION.run.app"     # open it in the browser signed in to Google as yourself',
    "preflight": ('export TFSTATE_BUCKET="${TFSTATE_BUCKET:-$PROJECT-tfstate}"   # lesson 0.3\'s state bucket: preflight.sh\'s own usage line names it <project>-tfstate\n'
                  'make preflight PROJECT="$PROJECT" TFSTATE_BUCKET="$TFSTATE_BUCKET" REGION="$REGION"'),
    "nourl": 'env -u DOCUMIND_API_URL python smoke/smoke.py; echo "exit $?"     # no URL: it refuses, and says what it checks',
    "green": 'make smoke DOCUMIND_API_URL="$API" DOCUMIND_PROJECT="$PROJECT" DOCUMIND_TENANT="$TENANT"',
    "broken": ('# on purpose: no DOCUMIND_TENANT, which the Makefile\'s header example leaves out too\n'
               'env -u DOCUMIND_TENANT make smoke DOCUMIND_API_URL="$API" DOCUMIND_PROJECT="$PROJECT"; echo "exit status: $?"'),
    "plan": 'python commands/lane.py --project "$PROJECT" roster --tenant acme --members "$ME" --dry-run     # prints the plan, writes nothing',
    "roster": 'for t in tenant-smoke acme; do echo "== $t"; GOOGLE_CLOUD_PROJECT="$PROJECT" python -m shared.tenancy list "$t"; done',
    "rest": ('for p in health ready version; do echo "GET /$p"; curl -s -w \'\\nHTTP %{http_code}\\n\' "$API/$p" -H "Authorization: Bearer $(tok "$API")"; done\n'
             'curl -s -o /dev/null -w \'GET /health with no token: HTTP %{http_code}\\n\' "$API/health"'),
    "state": ('gcloud storage ls -l "gs://$TFSTATE_BUCKET/**/default.tfstate"      # the state make up wrote\n'
              'python -c \'import json; print(sorted(json.load(open("terraform/runbook-project.auto.tfvars.json"))))\'   # the inputs\' names, not their values'),
    "first": ('# once per machine, and only if rag_save_session stops with "Missing rag-source-session.env": the git helper rag_resume\n'
              '# sources, and the source snapshot the helper checks, in the format commands/git-source.sh writes, for your clone\n'
              '[ -s ~/rag-git-source.sh ] || cp commands/git-source.sh ~/rag-git-source.sh\n'
              '[ -s ~/rag-source-session.env ] || ( umask 077; C=$(git -C "$DEMO_ROOT" rev-parse HEAD)\n'
              '  printf \'export %s=%q\\n\' SOURCE_BRANCH main SOURCE_COMMIT "$C" GIT_SHA "$C" RAG_SOURCE_REPO "$DEMO_ROOT" \\\n'
              '    DEMO_ROOT "$DEMO_ROOT" RAG_SOURCE_BACKUP "$(mktemp -d ~/rag-source-backup.XXXXXXXX)" > ~/rag-source-session.env )'),
    "save": ('source commands/session-restart.sh                     # defines the helper\'s functions; runs nothing\n'
             'export PROJECT_NUMBER="$NUMBER" OPERATOR_EMAIL="$ME"   # two names it saves that the setup block calls NUMBER and ME\n'
             'rag_save_session\n'
             'sed \'s/=.*//\' ~/rag-resume.env; stat -c \'%a %n\' ~/rag-resume.env   # the names saved, never the values; the file\'s mode'),
    "off": 'make off PROJECT="$PROJECT" REGION="$REGION"',
    "zero": "sleep 900     # Cloud Run keeps an idle instance up to 15 minutes after its last request\npython - <<'PY'\n" + ZERO_PY + "\nPY",
    "standing": ('gcloud ai index-endpoints list --region="$REGION" --project="$PROJECT" \\\n'
                 '  --format="table(displayName,deployedIndexes[0].dedicatedResources.machineSpec.machineType,deployedIndexes[0].dedicatedResources.minReplicaCount)"\n'
                 'gcloud ai indexes list --region="$REGION" --project="$PROJECT" --format="table(displayName,metadata.config.shardSize)"\n'
                 'gcloud spanner instances list --project="$PROJECT" --format="table(name.basename(),config.basename(),edition,processingUnits)"\n'
                 'gcloud sql instances list --project="$PROJECT" --format="table(name,settings.tier,region,state)"\n'
                 'gcloud container clusters list --project="$PROJECT" --format="table(name,location,autopilot.enabled,currentNodeCount)"\n'
                 'gcloud container node-pools list --cluster=documind-autopilot --region="$REGION" --project="$PROJECT" \\\n'
                 '  --format="table(name,config.machineType,config.diskType,config.diskSizeGb,locations.list())"\n'
                 'gcloud compute networks vpc-access connectors describe documind-vpc --region="$REGION" --project="$PROJECT" \\\n'
                 '  --format="table(name.basename(),machineType,minInstances,maxInstances)"'),
    "resume": ('cd ~/deploy_module_rag && source commands/session-restart.sh && rag_resume\n'
               'echo "PROJECT=$PROJECT REGION=$REGION API_URL=$API_URL"'),
    "down": 'make down PROJECT="$PROJECT" REGION="$REGION"',
}
CELL_LABELS = {
    "ui": "run in the operator shell (prints your UI's address)",
    "preflight": "run in the operator shell, in the kit (read-only; creates nothing; under a minute)",
    "nourl": "run in the operator shell, in the kit (no network: smoke.py stops before its first call)",
    "green": "run in the operator shell, in the kit (one question answered, one refused; about a minute)",
    "broken": "run in the operator shell, in the kit (the same smoke without a tenant: one check fails, on purpose)",
    "plan": "run in the operator shell, in the kit (no network: the dry run prints and returns)",
    "roster": "run in the operator shell, in the kit (two Firestore reads; writes nothing)",
    "rest": "run in the operator shell (four GETs; tok is the setup block's function)",
    "state": "run in the operator shell, in the kit (reads one object's listing and one local file)",
    "first": "run in the operator shell, in the kit, once per machine and only if the save below stops on it",
    "save": "run in the operator shell, in the kit, at the end of every session",
    "off": "run in the operator shell, in the kit, after the setup section's pin-back window",
    "zero": "run in the operator shell after make off, with no request to the lane in between (reads Cloud Monitoring; changes nothing)",
    "standing": "run in the operator shell (read-only: seven listings of what bills by the hour)",
    "resume": "run in a new shell at the start of your next session",
    "down": "run in the operator shell, in the kit, when you are finished with the lane - not now: Module 1 starts on this lane",
}
RECORDED = {k: pb.recorded(LESSON, f"{k}.txt") for k in
            ("preflight", "smoke_green", "smoke_broken", "roster_read", "rest_reads", "state_inputs", "save_session",
             "off", "zero_instances", "standing_resources", "resume", "down")}
OUTS = {
    "nourl": ("(smoke.py run here on the kit at build time, with no network)", SMOKE_NO_URL),
    "plan": ("(lane.py's dry run, run here on the kit at build time; documind-ai-YOUR-ID and the email stand for yours)", ROSTER_PLAN),
    "ui": ("(the format: NUMBER is your project number)", f"https://documind-ui-NUMBER.asia-south1.run.app"),
}
LANE_LABEL = "(the author's lane: your ids, times and counts are yours)"
for name, key in (("preflight", "preflight"), ("green", "smoke_green"), ("broken", "smoke_broken"), ("roster", "roster_read"),
                  ("rest", "rest_reads"), ("state", "state_inputs"), ("save", "save_session"), ("off", "off"),
                  ("zero", "zero_instances"), ("standing", "standing_resources"), ("resume", "resume"), ("down", "down")):
    OUTS[name] = (LANE_LABEL, RECORDED[key])


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + html.escape(label) + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + html.escape(label) + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(*v) for k, v in OUTS.items()})

NEXT = MANIFEST["modules"]["01"]
STATS = {
    "N_PREFLIGHT": str(N_PREFLIGHT), "N_APIS": str(len(APIS)), "N_TOOLS": str(len(TOOLS)), "SMOKE_TENANT": SMOKE_TENANT,
    "SMOKE_Q": html.escape(SMOKE_Q), "GOLDEN_ID": ROW["id"], "MUST": html.escape(ROW["must_contain"][0]),
    "MUST_DOC": ROW["must_retrieve"][0], "N_KEYS": str(len(KEYS)), "N_CRITICAL": str(len(CRITICAL)),
    "N_CRITICAL_W": WORDS[len(CRITICAL)], "CRITICAL": ", ".join(f"<code>{k}</code>" for k in CRITICAL),
    "UNFLOORED": " and ".join(f"<code>{s}</code>" for s in UNFLOORED), "N_SQL_W": WORDS[len(sc.SQL)], "CONN_MIN_W": WORDS[sc.CONN_MIN],
    "DAY_MEDIUM": inr(sc.PER_DAY["medium"]), "DAY_SMALL": inr(sc.PER_DAY["small"]),
    "WEEK_MEDIUM": inr(WEEK_MEDIUM), "MONTH_MEDIUM": inr(sc.PER_MONTH["medium"]),
    "MONTH_H": str(sc.MONTH_H), "YEAR_H": f"{sc.MONTH_H * 12:,}", "GKE_FEE": f"{PRICE['gke:cluster']:.2f}",
    "VEC_DAY": inr(rs_day("index", "medium")), "VEC_SHARE": str(round(100 * sc.INDEX_USD["medium"] / sc.HOURLY["medium"])),
    "BUDGET": f"{BUDGET:,}", "BUDGET_DAYS": f"{BUDGET / (sc.HOURLY['medium'] * sc.DAY_H * USD_INR):.1f}", "USD_INR": str(USD_INR),
    "PRICE_DATE": PRICE_DATE, "COST_TABLE": COST_TABLE, "SP_PU": str(sc.SP_PU),
    "NEXT_MODULE": html.escape(NEXT["name"].split(" - ")[0]), "NEXT_TITLE": html.escape(NEXT["lessons"]["1.1"]["name"]),
    **{f"URL_{k.upper()}": v for k, v in PAGES.items()},
}
# "the biggest line by far": with the MEDIUM index vector.tf's comment records, the index outweighs the other five together
assert max(LINES, key=lambda k: sc.item_usd(k, "medium")) == "index" and int(STATS["VEC_SHARE"]) > 50, STATS["VEC_SHARE"]


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(PART_A)), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: smoke.py with no URL (exit 2) and lane.py roster --dry-run, run offline | the standing cost (standing_cost.py, Mumbai "
      f"list prices of {PRICE_DATE}) Rs {inr(sc.PER_DAY['medium'])} a day with a MEDIUM index, Rs {inr(sc.PER_DAY['small'])} with "
      f"SMALL: up, off and after a refused make down alike")
