"""Build lesson 0.1 from its three parts, the shared template and verbatim kit excerpts.

Set up the Google Cloud billing account, budget and project. The first lesson of the core course: the learner has a
browser and Cloud Shell, no kit clone and no lane. So the page carries its own setup section (open Cloud Shell; no
setup_section(), which assumes a deployed lane), and every command it shows is gcloud: the billing account, the
project and its link, the APIs of the kit's ENABLE_APIS block, a budget made in the console at the kit's values and
read back. Then the kit's own budget (terraform/budget.tf, which lesson 0.3 applies) read verbatim, and the lane's
standing cost: what bills by the hour while the lane exists, priced per day and per weekend.

What the page computes at build time, from the kit:
  - the budget: amount (Makefile BUDGET_AMOUNT, passed as -var budget_amount), currency rule, thresholds and their
    basis, display name, recipients and the Pub/Sub switch (terraform/budget.tf);
  - the APIs: the list, the calls and the per-request limit (commands/lesson-12.1.sh's ENABLE_APIS block, which
    make apis runs), and the subset smoke/preflight.sh checks;
  - THE STANDING COST (lesson 0.4 states "the daily cost of a lane left up" from the same source): the kit's
    Terraform declarations of everything that runs by the hour with no traffic - vector.tf's deployed index (its
    replicas, and the machine its shard size names), spanner.tf's instance (edition and processing units),
    cloudsql.tf's and gateway.tf's instances (tier and disk), gke.tf's regional cluster and its lab pool (nodes,
    machine and disk) and network.tf's connector (its minimum instances) - each size parsed from the file, times
    the official Mumbai list price below, at the kit's USD_INR (shared/prices.py). The README's "One shape" sentence
    is the kit's own summary of what bills by the hour, quoted on the page.
Live outputs (gcloud on the author's account) come from data/ through pb.recorded(); RUN_LIST.md says how to record
each. The recorded text is redacted here: billing account ids, project ids, project numbers and mailboxes.
"""
import html
import json
import math
import re
import subprocess
import sys
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, window  # noqa: E402

LESSON = "0.1"
title = ("<title>Lesson 0.1 Set up the Google Cloud billing account, budget and project - an alert before the first "
         "resource, and the standing cost written down | Netsetos</title>\n")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.sc-controls{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:10px 16px;margin-bottom:8px;}
.sc-l{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.sc-l select{font:inherit;font-size:16px;padding:8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.sc-l input[type=range]{width:100%;min-height:44px;accent-color:var(--teal);}
.sc-presets{display:flex;flex-wrap:wrap;gap:6px;margin:0 0 8px;}
.sc-p{font:inherit;font-size:var(--small-size);padding:6px 12px;border:1px solid var(--border);border-radius:20px;background:var(--card);color:var(--navy);cursor:pointer;min-height:44px;}
.sc-p[aria-pressed=true]{background:var(--teal);border-color:var(--teal);color:#fff;}
.sc-p:active{transform:scale(.97);}
.sc-sum{font-family:var(--mono);font-size:var(--small-size);color:var(--teal-dark);margin:6px 0 8px;overflow-wrap:anywhere;}
.sc-row{display:grid;grid-template-columns:minmax(0,12em) minmax(0,1fr) 6em;align-items:center;gap:8px;font-size:12.5px;color:var(--navy);margin:4px 0;}
.sc-track{height:16px;background:#e2e8f0;border-radius:5px;overflow:hidden;}
.sc-fill{height:100%;background:linear-gradient(90deg,#0d9488,#0891b2);}
.sc-rs{font-family:var(--mono);text-align:right;}
.sc-note{font-size:var(--small-size);color:var(--slate);margin:8px 0 0;}
@media (max-width: 640px){.sc-row{grid-template-columns:minmax(0,1fr) 6em;}.sc-track{grid-column:1 / -1;}}
"""

# ================================================================== the kit's facts
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (
    "Makefile", "terraform/budget.tf", "terraform/vector.tf", "terraform/spanner.tf", "terraform/cloudsql.tf",
    "terraform/gateway.tf", "terraform/gke.tf", "terraform/network.tf", "commands/lesson-12.1.sh", "commands/infrastructure.py", "smoke/preflight.sh", "shared/prices.py",
    "gke/README.md", "README.md")}
MK = src["Makefile"]
BTF = src["terraform/budget.tf"]


def one(pattern: str, text: str, flags: int = 0) -> str:
    """The one match of a pattern's first group: a kit fact the page states, or the build stops."""
    found = re.findall(pattern, text, flags)
    assert len(found) == 1, (pattern, found)
    return found[0]


def r0(x: float) -> int:
    """Half up, as the widget's Math.round rounds, so the page and the meter print the same rupees."""
    return int(math.floor(x + 0.5))


def word(n: int) -> str:
    """A small count as the prose writes it: 2 -> 'two'."""
    return "zero one two three four five six seven eight nine ten eleven twelve".split()[n]


def inr(n: int) -> str:
    """Rupees the Indian way: the last three digits, then pairs - 1,00,000."""
    s = str(n)
    head, tail = s[:-3], s[-3:]
    pairs = []
    while len(head) > 2:
        pairs.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + pairs + [tail])


# ---- the budget the kit declares (terraform/budget.tf) and the amount make passes it (Makefile)
USD_INR = int(one(r"^USD_INR = (\d+)\b", src["shared/prices.py"], re.M))
BUDGET_AMOUNT = int(one(r"^BUDGET_AMOUNT\s+\?= (\d+)$", MK, re.M))
assert "-var budget_amount=$(BUDGET_AMOUNT)" in MK
assert "# In the billing account's currency (an Indian account is INR)." in MK
BUDGET_NAME = one(r'display_name\s+= "([^"]+)"', BTF)
VAR_DEFAULT = int(one(r'variable "budget_amount" \{.*?default\s+= "(\d+)"', BTF, re.S))
RULES = []
for body in re.findall(r"threshold_rules \{(.*?)\}", BTF, re.S):
    raw = one(r"threshold_percent = ([\d.]+)", body)
    basis = "FORECASTED_SPEND" if 'spend_basis       = "FORECASTED_SPEND"' in body else "CURRENT_SPEND"
    RULES.append((float(raw), basis, raw))
ACTUAL = [int(round(p * 100)) for p, b, _ in RULES if b == "CURRENT_SPEND"]
FORECAST = [int(round(p * 100)) for p, b, _ in RULES if b == "FORECASTED_SPEND"]
ACTUAL_RAW = [raw for _, b, raw in RULES if b == "CURRENT_SPEND"]
FORECAST_RAW = [raw for _, b, raw in RULES if b == "FORECASTED_SPEND"]
assert len(RULES) == 4 and len(FORECAST) == 1 and ACTUAL == sorted(ACTUAL), RULES
assert "credit_types_treatment" not in BTF          # so the Budgets API's default applies: every credit subtracted
assert 'projects = ["projects/${data.google_project.current.number}"]' in BTF
assert "currency_code = var.budget_currency != \"\" ? var.budget_currency : null" in BTF
assert "disable_default_iam_recipients   = false" in BTF and "for_each = (length(var.alert_channels) > 0 || var.budget_pubsub) ? [1] : []" in BTF
assert one(r'variable "budget_pubsub" \{.*?default\s+= (\w+)', BTF, re.S) == "false"
assert 'member = "serviceAccount:billing-budget-alert@system.gserviceaccount.com"' in BTF


def pct_list(xs):
    return ", ".join(str(x) for x in xs[:-1]) + " and " + str(xs[-1])


ACTUAL_TXT = pct_list(ACTUAL)                      # "50, 80 and 100"
FORECAST_PCT = FORECAST[0]

# ---- the APIs: the ENABLE_APIS block make apis runs (commands/lesson-12.1.sh)
S121 = src["commands/lesson-12.1.sh"]
ENABLE = S121[S121.index("# ---- ENABLE_APIS ----"):S121.index("# ---- APPLY ----")]
assert "sed -n '/^# ---- ENABLE_APIS ----/,/^# ---- APPLY ----/p' commands/lesson-12.1.sh" in MK
ENABLE_CMDS = "\n".join(line for line in ENABLE.splitlines() if line.strip() and not line.lstrip().startswith("#")).strip()
APIS = re.findall(r"^\s+([a-z0-9]+\.googleapis\.com)", ENABLE, re.M)
CALLS = [re.findall(r"([a-z0-9]+\.googleapis\.com)", chunk) for chunk in ENABLE.split("gcloud services enable")[1:]]
N_APIS, N_CALLS = len(APIS), len(CALLS)
PER_REQUEST = int(one(r"takes at most (\d+) services per request", ENABLE))
assert len(set(APIS)) == N_APIS and all(len(c) <= PER_REQUEST for c in CALLS) and ENABLE_CMDS.startswith("gcloud config set project $PROJECT")
PRE = src["smoke/preflight.sh"]
PRE_APIS = [a + ".googleapis.com" for a in one(r"for api in (.*?); do", PRE, re.S).replace("\\", " ").split()]
assert set(PRE_APIS) <= set(APIS), set(PRE_APIS) - set(APIS)
assert {"billingbudgets.googleapis.com", "cloudbilling.googleapis.com"} <= set(APIS)

# what each API is, by Google's product name; a kit API with no line here stops the build until the page names it
API_FAMILY = {
    "Serving and building": {"run": "Cloud Run", "cloudbuild": "Cloud Build", "artifactregistry": "Artifact Registry",
                             "cloudfunctions": "Cloud Run functions (Cloud Functions)", "container": "Google Kubernetes Engine",
                             "compute": "Compute Engine", "vpcaccess": "Serverless VPC Access", "clouddeploy": "Cloud Deploy",
                             "workflows": "Workflows", "cloudscheduler": "Cloud Scheduler", "eventarc": "Eventarc"},
    "Data": {"firestore": "Firestore", "storage": "Cloud Storage", "bigquery": "BigQuery", "spanner": "Spanner",
             "sqladmin": "Cloud SQL Admin", "pubsub": "Pub/Sub", "dataplex": "Dataplex"},
    "AI and documents": {"aiplatform": "Vertex AI (Gemini, embeddings, the Vector Search index)",
                         "vectorsearch": "Vector Search (the serverless store behind RAG Engine)",
                         "discoveryengine": "Vertex AI Search", "documentai": "Document AI", "vision": "Cloud Vision",
                         "language": "Cloud Natural Language", "translate": "Cloud Translation", "speech": "Speech-to-Text",
                         "texttospeech": "Text-to-Speech", "dlp": "Sensitive Data Protection (DLP)", "modelarmor": "Model Armor"},
    "Identity and security": {"iap": "Identity-Aware Proxy", "iamcredentials": "IAM Service Account Credentials",
                              "secretmanager": "Secret Manager", "orgpolicy": "Organization Policy"},
    "Operations": {"logging": "Cloud Logging", "monitoring": "Cloud Monitoring", "cloudtrace": "Cloud Trace"},
    "Billing and the project itself": {"billingbudgets": "Cloud Billing Budget", "cloudbilling": "Cloud Billing",
                                       "cloudresourcemanager": "Resource Manager", "serviceusage": "Service Usage"},
}
NAMED = {f"{k}.googleapis.com": (fam, name) for fam, d in API_FAMILY.items() for k, name in d.items()}
assert set(NAMED) == set(APIS), (set(APIS) - set(NAMED), set(NAMED) - set(APIS))

# ---- the project the kit expects (commands/infrastructure.py) and what make plan checks about it
INF = src["commands/infrastructure.py"]
lo, hi = map(int, one(r're\.fullmatch\(r"\[a-z\]\[a-z0-9-\]\{(\d+),(\d+)\}\[a-z0-9\]", args\.project', INF))
ID_MIN, ID_MAX = lo + 2, hi + 2
assert 'raise Stop("The project has no valid linked billing account; link billing before planning.")' in INF
assert 'billing.get("billingEnabled") is not True' in INF
assert "CLOUDSDK_BILLING_QUOTA_PROJECT=args.project" in INF     # the kit names a quota project for its gcloud calls; step 6's read-back does too
assert 'miss "billing (gcloud billing projects link $PROJECT --billing-account=...)"' in PRE
assert 'miss "project $PROJECT (gcloud projects create $PROJECT --set-as-default)"' in PRE

# ---- trial terms, verified 7 October 2026 (not kit numbers: Google's own pages)
# https://docs.cloud.google.com/free/docs/free-cloud-features (last updated 2026-10-05): "$300 in Welcome credit to
# spend over 90 days"; "You will not be billed for any Google Cloud usage during your Free Trial."; at the end "All
# resources you created during the trial are stopped", "a 30-day grace period", then "permanently deleted"; upgrading
# keeps "any unused credit until it expires 90 days from the Free Trial signup"; no GPUs on VMs, no Marketplace, no
# quota increase, no Windows Server images, no VMware Engine; the credit "can't pay for Gemini API in AI Studio costs"
# nor "a generative AI partner model that is offered as a managed API". Payment: "a credit card or other payment
# method"; "The authorization request is a temporary hold, it isn't an actual charge."; "Depending on your country,
# you might also need to verify your bank account."
TRIAL_USD, TRIAL_DAYS, GRACE_DAYS = 300, 90, 30
TRIAL_INR = TRIAL_USD * USD_INR
# India: https://docs.cloud.google.com/billing/docs/how-to/payment-methods ("Due to Reserve Bank of India (RBI)
# regulations, your bank might decline automatic card charges >15,000 INR for recurring payments") and
# https://docs.cloud.google.com/billing/docs/how-to/resolve-issues (the same rule with "over Rs 5,000", "Make manual
# payments for your usage. You can also make manual payments to proactively add credit to your account."); the two
# pages differ on the figure, so the page names neither. UPI: https://docs.cloud.google.com/billing/docs/resources/upi-payment-india
# ("qualified organization in India"; "a prepayment, typically 500 to 1000 INR").
UPI_PREPAY = "500 to 1,000"
# Budgets: https://docs.cloud.google.com/billing/docs/how-to/budgets (2026-10-05): "Setting an alerts-only budget
# doesn't automatically cap Google Cloud or Google Maps Platform usage or spending."; default recipients
# roles/billing.admin and roles/billing.user; "Promotional credits are things like ... Google Cloud Free Trial";
# all savings selected by default; "it may take several hours before receiving the first email"; console defaults
# "50%, 90%, and 100% of the budget amount, calculated against Actual spend". API:
# https://docs.cloud.google.com/billing/docs/reference/budget/rest/v1/billingAccounts.budgets - creditTypesTreatment
# "If not set, default behavior is INCLUDE_ALL_CREDITS" ("All types of credit are subtracted from the gross cost");
# currencyCode "must match the currency of the billing account"; default recipients "Billing Account Administrator
# and Billing Account User". Spend caps: https://docs.cloud.google.com/billing/docs/how-to/budgets-spend-caps -
# eligible: Gemini API, Gemini Enterprise Agent Platform, Cloud Run, Cloud Run functions; single project, monthly;
# "the enforcement of spend caps isn't instant and any cost overages are billed as normal".
CONSOLE_DEFAULTS = [50, 90, 100]
SPEND_CAP_SERVICES = "the Gemini API, Gemini Enterprise Agent Platform, Cloud Run and Cloud Run functions"
# Cloud Shell: https://docs.cloud.google.com/shell/docs/how-cloud-shell-works (2026-09-30): "5 GB of free persistent
# disk storage mounted as your $HOME directory"; "after an hour of inactivity, your session terminates"; $HOME deleted
# after 120 days without access; the gcloud CLI pre-installed.

# ================================================================== the standing cost
# The standing cost is shared with 0.3 and 0.4, so the three pages state one figure: lessons/00-setup/standing_cost.py
# parses the sizes from the Terraform and prices them at Mumbai's list prices (its docstring says how).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from standing_cost import (CONN_MIN, DAY_H, GKE_DISK_GB, GKE_DISK_TYPE, GKE_MACHINE, GKE_NODES, HOURLY, INDEX_USD,  # noqa: E402
                           ITEMS, LANE_REGION, MONTH_H, PER_DAY, PER_MONTH, PER_WEEKEND, PRICES, REST_USD, SHARD_MACHINE,
                           SHARDS, SP_CONFIG, SP_EDITION, SP_PU, SQL, SQL_GB, SQL_TIER, VS_REPLICAS, WEEKEND_H, item_usd)
import standing_cost  # noqa: E402
assert standing_cost.USD_INR == USD_INR
# the Cloud Run services make up deploys, and their floors: no minimum instance unless a session day sets the UI's
SERVICES = one(r"^SERVICES\s+= (.+)$", MK, re.M).split()
DEPLOY_SCRIPTS = re.findall(r"commands/[\w.-]+\.sh", one(r"^SCRIPTS\s+= ((?:.*\\\n)*.*)$", MK, re.M))
assert len(DEPLOY_SCRIPTS) == len(SERVICES) and "MIN_INSTANCES ?= 0" in MK, (SERVICES, DEPLOY_SCRIPTS)
for script in DEPLOY_SCRIPTS:
    floors = re.findall(r"--min-instances[= ](\S+)", (KIT / script).read_text(encoding="utf-8"))
    assert all(f in ("0", "${MIN_INSTANCES:-0}") for f in floors), (script, floors)
README = src["README.md"]
SHAPE_SENTENCE = " ".join(one(r"(It bills while it exists - the Vector Search\s+endpoint, two Cloud SQL instances and the cluster by "
                              r"the hour - which is what `make off` \(the night\s+switch\), `make down` and the throwaway project are for\.)",
                              README).split())

HOURS_TO = {k: {p: r0(BUDGET_AMOUNT * p / 100 / (HOURLY[k] * USD_INR)) for p in ACTUAL} for k in SHARDS}
TRIAL_DAYS_COVERED = {k: math.floor(TRIAL_INR / (HOURLY[k] * DAY_H * USD_INR) * 10) / 10 for k in SHARDS}
assert all(PER_MONTH[k] > TRIAL_INR for k in SHARDS)          # the page says a month of standing cost outruns the credit


# what the prose says in words: a tenth of a node, one replica, one lab node, and the largest item for each shard
assert SP_PU == 100 and VS_REPLICAS == 1 and GKE_NODES == 1
LARGEST = {s: max(ITEMS, key=lambda it: item_usd(it[0], s))[0] for s in SHARDS}
assert LARGEST == {"small": "spanner", "medium": "index"}, LARGEST
# make off: the Cloud Run services it floors (the target's own loop over them) and the GKE workload it removes
OFF_FLOORED = one(r"@for s in ((?:documind-[\w-]+ ?)+); do", MK).split()
assert OFF_FLOORED == ["documind-slm", "documind-vllm", "documind-gateway", "documind-ui"], OFF_FLOORED
assert "-$(MAKE) gke-down PROJECT=$(PROJECT)" in MK


# the standing-cost table, step 8
rows = []
for key, label, where, size, _ in ITEMS:
    size_txt = (f"{VS_REPLICAS} replica: {SHARDS['small']} (small shard) or {SHARDS['medium']} (medium)" if key == "index" else size)
    usd = (f"{INDEX_USD['small']:.4f} or {INDEX_USD['medium']:.4f}" if key == "index" else f"{item_usd(key, 'small'):.4f}")
    day = (f"{inr(r0(INDEX_USD['small'] * DAY_H * USD_INR))} or {inr(r0(INDEX_USD['medium'] * DAY_H * USD_INR))}" if key == "index"
           else inr(r0(item_usd(key, "small") * DAY_H * USD_INR)))
    rows.append(f'<tr><td>{label}</td><td data-label="Declared in"><code>{where}</code></td><td data-label="Size">{html.escape(size_txt)}</td>'
                f'<td data-label="USD an hour">{usd}</td><td data-label="Rs a day">{day}</td></tr>')
for shard in SHARDS:
    rows.append(f'<tr><td><strong>The lane, {shard} shard</strong></td><td data-label="Declared in">all {word(len(ITEMS))}</td>'
                f'<td data-label="Size">everything above</td><td data-label="USD an hour"><strong>{HOURLY[shard]:.4f}</strong></td>'
                f'<td data-label="Rs a day"><strong>{inr(PER_DAY[shard])}</strong> (a weekend: {inr(PER_WEEKEND[shard])})</td></tr>')
STANDING_TABLE = "\n".join(rows)

# the APIs table, step 5: the kit's order inside each family
api_rows = []
for fam in API_FAMILY:
    names = [a for a in APIS if NAMED[a][0] == fam]
    api_rows.append(f'<tr><td>{fam}</td><td data-label="APIs">{len(names)}</td><td data-label="Which">'
                    + "; ".join(f"<code>{a.split('.')[0]}</code> {html.escape(NAMED[a][1])}" for a in names) + "</td></tr>")
API_TABLE = "\n".join(api_rows)

# ================================================================== verbatim kit excerpts
EXCERPTS = {
    "mk_apis": ("Makefile - the apis target: the ENABLE_APIS block of commands/lesson-12.1.sh, run as it is",
                block("Makefile", "# The APIs a fresh project needs", n=4)),
    "infra_project": ("commands/infrastructure.py - the project id make plan accepts",
                      block("commands/infrastructure.py", 'if not re.fullmatch(r"[a-z][a-z0-9-]{4,28}[a-z0-9]", args.project or ""):', n=2)),
    "infra_discover": ("commands/infrastructure.py - discover(): what make plan reads about your project first",
                       block("commands/infrastructure.py", "    def discover(self, state, saved):", n=12)),
    "infra_billing": ("commands/infrastructure.py - billing_id(): no linked account, no plan",
                      block("commands/infrastructure.py", "def billing_id(value):", end="def validate_trust(value):")),
    "preflight": ("smoke/preflight.sh - make preflight's project and billing checks, and the command it names for a MISS",
                  block("smoke/preflight.sh", 'if gcloud projects describe "$PROJECT"', n=7)),
    "budget_locals": ("terraform/budget.tf - which billing account the budget goes on",
                      block("terraform/budget.tf", "# The existing project data source", end='resource "google_billing_budget" "documind" {')),
    "budget_tf": ("terraform/budget.tf - the budget the kit declares",
                  block("terraform/budget.tf", 'resource "google_billing_budget" "documind" {', end='resource "google_pubsub_topic" "budget_alerts" {')),
    "budget_vars": ("terraform/budget.tf - its inputs",
                    block("terraform/budget.tf", 'variable "alert_channels" {')),
    "mk_budget": ("Makefile - the amount make plan passes it",
                  block("Makefile", "# In the billing account's currency (an Indian account is INR).", n=2) + "\n...\n"
                  + block("Makefile", "TF_EXTRA_VARS = -var audit_lock=$(AUDIT_LOCK)", n=4)),
    "vector": ("terraform/vector.tf - the deployed index: one replica, on the machine its shard size names",
               block("terraform/vector.tf", "locals {", end="# These two outputs are the whole contract")),
    "spanner": ("terraform/spanner.tf - the graph instance, and what the kit says it costs",
                block("terraform/spanner.tf", "# WHAT THIS COSTS.", end='resource "google_spanner_database" "graph" {')),
    "cloudsql": ("terraform/cloudsql.tf - the chat checkpointer's instance (gateway.tf declares documind-gateway the same way)",
                 block("terraform/cloudsql.tf", 'resource "google_sql_database_instance" "checkpoint" {', end='resource "google_sql_database" "checkpoint" {')),
    "gke": ("terraform/gke.tf - a regional cluster and its one-node lab pool",
            block("terraform/gke.tf", 'resource "google_container_cluster" "autopilot" {', n=4) + "\n...\n"
            + block("terraform/gke.tf", 'resource "google_container_node_pool" "lab" {', n=12)),
    "connector": ("terraform/network.tf - the connector Cloud Run reaches the VPC through",
                  block("terraform/network.tf", 'resource "google_vpc_access_connector" "conn" {', n=8)),
    "mk_gke_down": ("Makefile - what make off leaves standing",
                    block("Makefile", "gke-down: guard-project", n=4)),
    "mk_down": ("Makefile - the last lines make down prints",
                block("Makefile", 'echo ">> Delete the throwaway project to stop all billing:"', n=2)),
}
assert "min_replica_count = 1" in EXCERPTS["vector"][1] and "SHARD_SIZE_MEDIUM = \"e2-standard-16\"" in EXCERPTS["vector"][1]
assert "processing_units = 100" in EXCERPTS["spanner"][1] and 'tier              = "db-f1-micro"' in EXCERPTS["cloudsql"][1]
assert "it bills by the hour while it exists" in EXCERPTS["spanner"][1] and "price this on the" in EXCERPTS["spanner"][1]
assert "node_count     = 1" in EXCERPTS["gke"][1] and "min_instances = 2" in EXCERPTS["connector"][1]
assert "threshold_percent = 1.2" in EXCERPTS["budget_tf"][1] and "BUDGET_AMOUNT      ?= 5000" in EXCERPTS["mk_budget"][1]
assert "make down removes them" in EXCERPTS["mk_gke_down"][1] and "gcloud projects delete" in EXCERPTS["mk_down"][1]
fill = filler(EXCERPTS, window)


# ================================================================== the cells, and what they print
def bash_hl(code: str) -> str:
    """A shell block escaped, with each comment coloured: a # outside quotes, at a line's start or after a blank.
    (pagebuild.hl() reads Python, and would colour the 'as' inside --set-as-default as a keyword.)"""
    out = []
    for line in code.split("\n"):
        quote, cut = None, None
        for i, ch in enumerate(line):
            if quote:
                quote = None if ch == quote else quote
            elif ch in "'\"":
                quote = ch
            elif ch == "#" and (i == 0 or line[i - 1] in " \t"):
                cut = i
                break
        out.append(html.escape(line, quote=False) if cut is None else
                   html.escape(line[:cut], quote=False) + '<span class="cm">' + html.escape(line[cut:], quote=False) + "</span>")
    return "\n".join(out)


def bash(label: str, code: str) -> str:
    """A window to paste into the shell: the label, a copy button, the code."""
    return ('<div class="cw"><div class="ch-bar"><span>' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + bash_hl(code) + "</pre></div>\n")


def expected(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text, quote=False) + "</pre></div>\n")


def redact(text: str) -> str:
    """What the author's run printed, with the author's identifiers replaced by the page's placeholders."""
    text = re.sub(r"\b[0-9A-Za-z]{6}-[0-9A-Za-z]{6}-[0-9A-Za-z]{6}\b", "XXXXXX-XXXXXX-XXXXXX", text)   # budget.tf's own pattern
    text = re.sub(r"\bdocumind-ai-[a-z0-9-]*[a-z0-9]\b", "documind-ai-YOUR-ID", text)
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)+", "you@example.com", text)
    return re.sub(r"\b\d{10,}\b", "NUMBER", text)


def rec(name: str) -> str:
    return redact(pb.recorded(LESSON, name))


ID_RULE = f"{ID_MIN} to {ID_MAX} characters"
CELL = {
    "setup": ("gcloud --version | head -n 1\n"
              "gcloud config get-value account\n"
              "gcloud config get-value project"),
    "accounts": "gcloud billing accounts list",
    "project": ("export BILLING=XXXXXX-XXXXXX-XXXXXX     # yours: the ACCOUNT_ID of the OPEN account in the list above\n"
                f"export PROJECT=documind-ai-YOUR-ID      # yours: {ID_RULE}, lower case, digits and hyphens, a letter first\n"
                'gcloud projects create "$PROJECT" --name="DocuMind lane" --set-as-default\n'
                'gcloud billing projects link "$PROJECT" --billing-account="$BILLING"'),
    "apis": ENABLE_CMDS,
    "apis_check": ("enabled=\"$(gcloud services list --enabled --project \"$PROJECT\" --format='value(config.name)')\"\n"
                   "missing=0\n"
                   "for api in " + " \\\n           ".join(" ".join(APIS[i:i + 5]) for i in range(0, N_APIS, 5)) + "; do\n"
                   "  grep -qxF \"$api\" <<< \"$enabled\" || { echo \"MISSING $api\"; missing=$((missing + 1)); }\n"
                   "done\n"
                   f"echo \"the kit's {N_APIS}: $(({N_APIS} - missing)) enabled, $missing missing\"\n"
                   "echo \"enabled on the project in all: $(grep -c . <<< \"$enabled\")\""),
    "budget": ('gcloud billing budgets list --billing-account="$BILLING" --billing-project="$PROJECT" \\\n'
               "  --filter='displayName=\"Billing account guard\"' \\\n"
               "  --format='yaml(displayName,amount,thresholdRules,budgetFilter.calendarPeriod,budgetFilter.creditTypesTreatment,budgetFilter.creditTypes)'"),
    "verify": ('gcloud billing projects describe "$PROJECT"\n'
               "gcloud config get-value project"),
}
for name, code in CELL.items():
    assert "\t" not in code, name

# the arithmetic cell, step 8: run here, so the output it shows is the output it prints
PY_ITEMS = [(label, round(item_usd(key, "small"), 6)) for key, label, *_ in ITEMS if key != "index"]
STANDING_PY = (
    "import warnings\n"
    "warnings.filterwarnings(\"ignore\", category=UserWarning)\n"
    "# USD an hour, Mumbai list prices; sizes from the kit's Terraform (see the table above)\n"
    f"INDEX = {{\"small\": {INDEX_USD['small']:.7f}, \"medium\": {INDEX_USD['medium']:.7f}}}   # one replica, e2-standard-2 or e2-standard-16\n"
    "REST = {\n" + "".join(f"    {label!r}: {usd},\n" for label, usd in PY_ITEMS) + "}\n"
    f"USD_INR, BUDGET = {USD_INR}, {BUDGET_AMOUNT}   # the kit's rate (shared/prices.py) and BUDGET_AMOUNT (Makefile)\n"
    "for shard, index in INDEX.items():\n"
    "    hourly = index + sum(REST.values())\n"
    "    rs = lambda hours: round(hourly * hours * USD_INR)\n"
    f"    print(f\"{{shard:6}} shard: USD {{hourly:.4f}} an hour = Rs {{rs({DAY_H}):,}} a day, Rs {{rs({WEEKEND_H}):,}} a weekend, Rs {{rs({MONTH_H}):,}} a month\")\n"
    f"    print(f\"              the budget's {ACTUAL[0]}% (Rs {{BUDGET * {ACTUAL[0]} // 100:,}}) after {{BUDGET * {ACTUAL[0]} / 100 / (hourly * USD_INR):.0f}} hours of this alone\")"
)
PY_CELL = "python - <<'PY'\n" + STANDING_PY + "\nPY"
r = subprocess.run([sys.executable, "-c", STANDING_PY], capture_output=True, text=True, encoding="utf-8")
assert r.returncode == 0 and not r.stderr.strip(), r.stderr
PY_OUT = r.stdout.rstrip("\n")
assert f"Rs {PER_DAY['small']:,} a day" in PY_OUT and f"Rs {PER_DAY['medium']:,} a day" in PY_OUT, (PY_OUT, PER_DAY)
assert f"Rs {PER_WEEKEND['small']:,} a weekend" in PY_OUT and f"after {HOURS_TO['small'][ACTUAL[0]]} hours" in PY_OUT, PY_OUT

WINDOWS = {
    "SETUP_CELL": bash("bash &mdash; run in Cloud Shell, once per session (or in a terminal where gcloud is signed in)", CELL["setup"]),
    "SETUP_OUT": expected("expected (recorded in Cloud Shell; your version and account)", rec("setup_check.txt")),
    "ACCOUNTS_CELL": bash("bash &mdash; run in Cloud Shell (read-only)", CELL["accounts"]),
    "ACCOUNTS_OUT": expected("expected (recorded; your account id and name)", rec("billing_accounts.txt")),
    "PROJECT_CELL": bash("bash &mdash; run in Cloud Shell, once (put your own account id and project id in the first two lines)", CELL["project"]),
    "PROJECT_OUT": expected("expected (recorded; your ids and operation numbers)", rec("project_link.txt")),
    "APIS_CELL": bash(f"bash &mdash; run in Cloud Shell, once (the kit's ENABLE_APIS block: {N_APIS} APIs in {N_CALLS} calls)", CELL["apis"]),
    "APIS_OUT": expected("expected (recorded; your operation ids)", rec("apis_enable.txt")),
    "APIS_CHECK_CELL": bash("bash &mdash; run in Cloud Shell (read-only)", CELL["apis_check"]),
    "APIS_CHECK_OUT": expected("expected (recorded; the last line is your project's own total)", rec("apis_check.txt")),
    "BUDGET_CELL": bash("bash &mdash; run in Cloud Shell after the console steps (read-only)", CELL["budget"]),
    "BUDGET_OUT": expected("expected (recorded on the author's account)", rec("budgets_list.txt")),
    "PY_CELL": bash("bash &mdash; run in Cloud Shell (a Python cell, arithmetic only: no network, no credentials, Rs 0)", PY_CELL),
    "PY_OUT": expected("expected", PY_OUT),
    "VERIFY_CELL": bash("bash &mdash; run in Cloud Shell (read-only)", CELL["verify"]),
    "VERIFY_OUT": expected("expected (recorded; your ids)", rec("verify.txt")),
}

# ================================================================== the numbers the parts state
TOK = {
    "N_APIS": str(N_APIS), "N_CALLS": str(N_CALLS), "PER_REQUEST": str(PER_REQUEST), "N_PRE_APIS": str(len(PRE_APIS)),
    "BUDGET_AMOUNT": str(BUDGET_AMOUNT), "BUDGET_AMOUNT_INR": inr(BUDGET_AMOUNT), "BUDGET_NAME": BUDGET_NAME,
    "VAR_DEFAULT": str(VAR_DEFAULT), "ACTUAL_TXT": ACTUAL_TXT, "FORECAST_PCT": str(FORECAST_PCT),
    "ACTUAL_FIRST": str(ACTUAL[0]), "ACTUAL_SECOND": str(ACTUAL[1]), "ACTUAL_LAST": str(ACTUAL[-1]),
    "HALF_INR": inr(BUDGET_AMOUNT * ACTUAL[0] // 100),
    "CONSOLE_DEFAULTS": pct_list(CONSOLE_DEFAULTS), "CONSOLE_DROP": str(next(p for p in CONSOLE_DEFAULTS if p not in ACTUAL)),
    "TRIAL_USD": str(TRIAL_USD), "TRIAL_DAYS": str(TRIAL_DAYS), "GRACE_DAYS": str(GRACE_DAYS), "TRIAL_INR": inr(TRIAL_INR),
    "USD_INR": str(USD_INR), "UPI_PREPAY": UPI_PREPAY, "SPEND_CAP_SERVICES": SPEND_CAP_SERVICES,
    "ID_RULE": ID_RULE,
    "DAY_SMALL": inr(PER_DAY["small"]), "DAY_MEDIUM": inr(PER_DAY["medium"]),
    "WEEKEND_SMALL": inr(PER_WEEKEND["small"]), "WEEKEND_MEDIUM": inr(PER_WEEKEND["medium"]),
    "MONTH_SMALL": inr(PER_MONTH["small"]), "MONTH_MEDIUM": inr(PER_MONTH["medium"]),
    "H50_SMALL": str(HOURS_TO["small"][ACTUAL[0]]), "H50_MEDIUM": str(HOURS_TO["medium"][ACTUAL[0]]),
    "H100_SMALL": str(HOURS_TO["small"][ACTUAL[-1]]), "H100_MEDIUM": str(HOURS_TO["medium"][ACTUAL[-1]]),
    "TRIAL_DAYS_SMALL": f"{TRIAL_DAYS_COVERED['small']:.1f}", "TRIAL_DAYS_MEDIUM": f"{TRIAL_DAYS_COVERED['medium']:.1f}",
    "SMALL_MACHINE": SHARDS["small"], "MEDIUM_MACHINE": SHARDS["medium"],
    "INDEX_DAY_SMALL": inr(r0(INDEX_USD["small"] * DAY_H * USD_INR)), "INDEX_DAY_MEDIUM": inr(r0(INDEX_USD["medium"] * DAY_H * USD_INR)),
    "SPANNER_DAY": inr(r0(item_usd("spanner", "small") * DAY_H * USD_INR)), "SP_PU": str(SP_PU),
    "SQL_COUNT": word(len(SQL)), "SQL_COUNT_CAP": word(len(SQL)).capitalize(), "N_CALLS_WORD": word(N_CALLS),
    "N_ITEMS": word(len(ITEMS)), "N_ITEMS_CAP": word(len(ITEMS)).capitalize(),
    "N_RULES": word(len(RULES)), "N_RULES_CAP": word(len(RULES)).capitalize(), "OFF_N": word(len(OFF_FLOORED)),
    "SQL_TIER": SQL_TIER, "SQL_GB": str(SQL_GB), "GKE_MACHINE": GKE_MACHINE,
    "GKE_DISK_GB": str(GKE_DISK_GB), "GKE_FEE": f"{PRICES['gke:cluster']:.2f}", "CONN_MIN": str(CONN_MIN),
    "N_SERVICES": word(len(SERVICES)),
    "ACTUAL_FRAC": ", ".join(ACTUAL_RAW[:-1]) + " and " + ACTUAL_RAW[-1], "FORECAST_FRAC": FORECAST_RAW[0],
    "SHAPE_SENTENCE": html.escape(SHAPE_SENTENCE),
    "STANDING_TABLE": STANDING_TABLE, "API_TABLE": API_TABLE,
    **WINDOWS,
}


def tokens(text: str) -> str:
    def rep(m):
        return TOK[m.group(1)]
    return re.sub(r"%%(\w+)%%", rep, text)


# ================================================================== the standing-cost meter
METER = {
    "items": [{"label": label, "usd": ({s: round(INDEX_USD[s], 7) for s in SHARDS} if k == "index" else round(item_usd(k, "small"), 7))}
              for k, label, *_ in ITEMS],
    "machines": SHARDS, "usdInr": USD_INR, "budget": BUDGET_AMOUNT, "actual": ACTUAL, "trialInr": TRIAL_INR,
    "dayH": DAY_H, "weekendH": WEEKEND_H,
}
JS = """<script>
(function(){
  'use strict';
  var M = __METER__;
  var meter = document.getElementById('meter');
  if (!meter) return;
  var hours = document.getElementById('sc-h'), hv = document.getElementById('sc-h-v'), shard = document.getElementById('sc-shard'),
      sum = document.getElementById('sc-sum'), out = document.getElementById('sc-out'), note = document.getElementById('sc-note'),
      presets = meter.querySelectorAll('.sc-p');
  function rs(n){ return 'Rs ' + Math.round(n).toLocaleString('en-IN'); }
  function usd(item){ return typeof item.usd === 'number' ? item.usd : item.usd[shard.value]; }
  function span(h){ return h + (h === 1 ? ' hour' : ' hours') + (h % 24 === 0 ? ' (' + (h / 24) + (h === 24 ? ' day' : ' days') + ')' : ''); }
  function render(){
    var h = parseInt(hours.value, 10), hourly = 0, top = 0;
    M.items.forEach(function(i){ hourly += usd(i); top = Math.max(top, usd(i)); });
    hv.textContent = span(h);
    Array.prototype.forEach.call(presets, function(b){ b.setAttribute('aria-pressed', String(parseInt(b.getAttribute('data-h'), 10) === h)); });
    out.innerHTML = M.items.map(function(i){
      var u = usd(i);
      return '<div class="sc-row"><span>' + i.label + '</span><div class="sc-track"><div class="sc-fill" style="width:' + Math.round(u / top * 100) + '%"></div></div><span class="sc-rs">' + rs(u * h * M.usdInr) + '</span></div>';
    }).join('');
    var perDay = hourly * M.dayH * M.usdInr;
    sum.textContent = rs(hourly * h * M.usdInr) + ' for ' + span(h) + '  |  ' + rs(perDay) + ' a day, ' + rs(hourly * M.weekendH * M.usdInr) + ' a weekend  |  USD ' + hourly.toFixed(4) + ' an hour, ' + M.machines[shard.value] + ' index';
    var first = M.actual[0], last = M.actual[M.actual.length - 1];
    note.textContent = 'With nothing else running, the kit\\'s budget of ' + M.budget.toLocaleString('en-IN') + ' a month would cross ' + first + '% after ' +
      Math.round(M.budget * first / 100 / (hourly * M.usdInr)) + ' hours of this and ' + last + '% after ' + Math.round(M.budget * last / 100 / (hourly * M.usdInr)) +
      ' hours. The trial\\'s credit (' + rs(M.trialInr) + ' at Rs ' + M.usdInr + ' to the dollar) would cover ' + (Math.floor(M.trialInr / perDay * 10) / 10).toFixed(1) + ' days of it.';
  }
  hours.addEventListener('input', render);
  shard.addEventListener('change', render);
  Array.prototype.forEach.call(presets, function(b){ b.addEventListener('click', function(){ hours.value = b.getAttribute('data-h'); render(); }); });
  render();
})();
</script>
""".replace("__METER__", json.dumps(METER))

body = "".join([
    tokens(fill(pb.part(LESSON, "a"))),
    tokens(fill(pb.part(LESSON, "b"))),
    tokens(fill(pb.part(LESSON, "c"))),
])
finish(LESSON, title, EXTRA_CSS, body, JS)
