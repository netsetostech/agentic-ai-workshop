"""Build lesson 11.6 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Exercise model routing, budgets and shutdown controls. Three clocks, three controls. Per answer: with ROUTING on, a
flash-lite classifier labels each question and breakers.choose_model() picks the model from the class and the month's
spend - the Firestore counter every answer adds to (budget.py), or SPEND_PCT, the replay - strict from 80 percent: Pro
is never chosen. Per month: the billing budget emails the billing admins at 50, 80 and 100 percent of the project's
whole bill and at a 120 percent forecast, and acts on nothing. Per hour: the off switch floors the GPU services, the
gateway and the UI to zero instances (documind-off at 23:00 IST, make off by hand), under a GPU quota capped at one card
(make gpu-cap). Offline: the three controls as the kit writes them down, and choose_model() run over the classes and
the spends. Live: the month so far (the counter, the service's settings, the billing budget, the GPU quota); three
questions to a candidate revision with ROUTING on, then the same three with SPEND_PCT=85 - the tier changes; the
candidate undone; a session-day floor on the UI, make off, the nightly job's schedule, the instance count at zero;
make gpu-cap.

Build-time proof: the offline cell runs on the kit (breakers.py is imported and run). The candidate cells ran against the
kit's own rag-api on localhost, ROUTING=on then SPEND_PCT=85, so the model each answer names is the kit's
choose_model_for() - router.classify() and breakers.choose_model() over budget.spend_pct() - with the classifier and
the reader stood in for Gemini, and record() the kit's own, incrementing the stand-in counter. The month cell reads a
stand-in Firestore and a fake gcloud; make gpu-quota and make gpu-cap are the kit's gpu_quota.py against a stand-in of
the Service Usage API; the instance count reads a stand-in of the Monitoring API. make off's printing, the undo's and
the scheduler's are the shape gcloud prints. The panel's choice is breakers.choose_model(), ported, and a Node check
compares the port with the kit on every class, spend and ROUTING setting.
"""
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "11.6"
title = "<title>Lesson 11.6 Exercise model routing, budgets and shutdown controls - the tier at 85 percent, and the lane off at night | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
PORT = 8133
QUESTIONS = ["What is the notice period for a confirmed E3?",
             "Explain what happens when a trip costs more than the per-trip travel cap.",
             "Work out, step by step, the total reimbursed for three domestic trips costing Rs 38,000, Rs 45,000 and Rs 22,000."]

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;}
.pc-in input[type=range]{width:100%;min-height:44px;accent-color:var(--teal);}
.pc-in .chk{flex-direction:row;align-items:center;gap:10px;min-height:44px;}
.pc-in .chk input{width:20px;height:20px;accent-color:var(--teal);}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.fs-grid{display:grid;grid-template-columns:minmax(0,10em) minmax(0,1fr);gap:4px 10px;font-size:12.5px;}
.fs-grid b{color:var(--navy);font-weight:600;}
.fs-grid .pass{color:var(--teal-dark);font-weight:600;}
.fs-grid .stop{color:#9a3412;font-weight:600;}
.fs-grid .skip{color:var(--slate-light);}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
BRK, BUD, MAIN, OFF = "services/rag-api/breakers.py", "services/rag-api/budget.py", "services/rag-api/main.py", "terraform/off.tf"
EXCERPTS = {
    "choose": ("services/rag-api/breakers.py - choose_model(): the class and the month's spend pick the model",
               block(BRK, "def choose_model(question_class: str, spend_pct: float) -> str:")),
    "spend": ("services/rag-api/budget.py - the counter every answer adds to, and the replay that overrides it",
              block(BUD, "def record(db: firestore.Client, usd: float) -> None:", n=16)),
    "wired": ("services/rag-api/main.py - choose_model_for(): the classifier, the breaker, and the fall-back",
              block(MAIN, "    if settings.routing != \"on\":", n=8)),
    "night": ("terraform/off.tf - the nightly job's loop: four services, floored where a floor is above zero",
              block(OFF, "    for pair in documind-slm:$SLM_REGION", n=6)),
}
assert 'return ("gemini-3.6-flash" if question_class == "COMPLEX"' in EXCERPTS["choose"][1]
assert EXCERPTS["choose"][1].rstrip().endswith('"gemini-3.1-flash-lite")')                  # the whole function, its last line included
assert 'firestore.Increment(usd)' in EXCERPTS["spend"][1] and "if override:" in EXCERPTS["spend"][1]
assert "return choose_model(tier, spend_pct(_fs(), settings.budget_usd, settings.spend_pct_override))" in EXCERPTS["wired"][1]
assert "--min-instances 0 --quiet" in EXCERPTS["night"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (BRK, BUD, MAIN, OFF, "services/rag-api/router.py", "services/rag-api/config.py",
                                                           "services/rag-api/generator.py", "services/rag-api/cost.py", "terraform/budget.tf",
                                                           "commands/lesson-12.2.sh", "commands/lesson-12.4.sh", "commands/lesson-7.2.sh",
                                                           "commands/lesson-8.4.sh", "Makefile")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
sys.path.insert(0, str(KIT / "services" / "rag-api"))
import breakers  # noqa: E402 - pure: the kit's own table, run here and ported to the panel
assert (breakers.BUDGET_STRICT_PCT, breakers.BUDGET_FLOOR_PCT) == (80, 100)
FLOOR_USERS = [p for p in (KIT / "services").rglob("*.py") if "BUDGET_FLOOR_PCT" in p.read_text(encoding="utf-8") and p.name != "breakers.py"]
assert not FLOOR_USERS and "BUDGET_FLOOR_PCT" not in MK                      # the 100 percent action: a constant, read by nothing
assert "ROUTING=${ROUTING-off}" in src["commands/lesson-12.2.sh"] and "BUDGET_USD=${BUDGET_USD-100}" in src["commands/lesson-12.2.sh"]
assert "${SPEND_PCT:+|SPEND_PCT=$SPEND_PCT}" in src["commands/lesson-12.2.sh"]
CAND_RECIPE = MK[MK.index("candidate: guard-project"):MK.index("# Eval CANDIDATES from the feed")]
assert "ROUTING=$(ROUTING)" in CAND_RECIPE and "SPEND_PCT" not in CAND_RECIPE and "BUDGET_USD" not in CAND_RECIPE   # make candidate cannot replay
assert "from router import classify" in src[MAIN] and "ROUTING_TABLE" not in src[MAIN] and "route(" not in src[MAIN]
assert '"COMPLEX": {"model": "gemini-3.1-pro-preview", "thinking_budget": 8192, "max_output_tokens": 16384}' not in src["services/rag-api/router.py"]
assert re.search(r'Complexity\.COMPLEX: \{"model": "gemini-3\.1-pro-preview", "thinking_budget": 8192, "max_output_tokens": 16384\}', src["services/rag-api/router.py"])
assert 'thinking_config=types.ThinkingConfig(thinking_level="LOW")' in src["services/rag-api/generator.py"] and "max_answer_tokens: int = 2048" in src["services/rag-api/config.py"]
assert 'CLASSIFIER_MODEL = "gemini-3.1-flash-lite"' in src["services/rag-api/router.py"]
QUERY_FN = src[MAIN][src[MAIN].index("def query("):src[MAIN].index("def _record(")]
USAGE_ROW = src[MAIN].split("def usage_row(", 1)[1].split("@app.get", 1)[0]
assert "classify" not in QUERY_FN and "classif" not in USAGE_ROW          # the classifier's call is on no row: only the answer's tokens are
assert '"model": model,' in USAGE_ROW and "complexity" not in USAGE_ROW.lower() and '"tier"' not in USAGE_ROW   # the model, never the class
assert 'db.collection("budget").document(dt.datetime.now(dt.timezone.utc).strftime("%Y-%m"))' in src[BUD]
assert "routing: str = Field(\"off\", alias=\"ROUTING\")" in src["services/rag-api/config.py"] and 'budget_usd: float = Field(100.0, alias="BUDGET_USD")' in src["services/rag-api/config.py"]
BTF = src["terraform/budget.tf"]
THRESHOLDS = re.findall(r"threshold_percent = ([\d.]+)", BTF)
assert THRESHOLDS == ["0.5", "0.8", "1.0", "1.2"] and 'spend_basis       = "FORECASTED_SPEND"' in BTF and "BUDGET_AMOUNT      ?= 5000" in MK
assert "budget_pubsub" in BTF and "default     = false" in BTF.split('variable "budget_pubsub"', 1)[1]
SUBSCRIBERS = [p for pat in ("*.tf", "*.py", "*.sh", "*.mk", "*.yaml", "Makefile") for p in pb.kit_runtime_files(pat)
               if p.name != "budget.tf" and ("documind-budget-alerts" in p.read_text(encoding="utf-8", errors="ignore")
                                            or "budget_alerts" in p.read_text(encoding="utf-8", errors="ignore"))]
assert not SUBSCRIBERS, SUBSCRIBERS                                           # the topic, when declared, has no reader
OFF_TF = src[OFF]
OFF_SERVICES = re.findall(r"(documind-[\w-]+):\$", OFF_TF.split("for pair in", 1)[1].split("; do", 1)[0])
assert OFF_SERVICES == ["documind-slm", "documind-vllm", "documind-gateway", "documind-ui"], OFF_SERVICES
assert 'schedule    = "0 23 * * *"' in OFF_TF and 'time_zone   = "Asia/Kolkata"' in OFF_TF and 'name        = "documind-off-nightly"' in OFF_TF
MIN_SCRIPTS = {s: re.search(r"gcloud run deploy (documind-[\w-]+)", src[f"commands/{s}"]).group(1) for s in ("lesson-12.4.sh", "lesson-7.2.sh", "lesson-8.4.sh")
               if "--min-instances=${MIN_INSTANCES:-0}" in src[f"commands/{s}"]}
assert MIN_SCRIPTS == {"lesson-12.4.sh": "documind-ui", "lesson-7.2.sh": "documind-mcp", "lesson-8.4.sh": "documind-agent"}, MIN_SCRIPTS
UNFLOORED = [svc for svc in MIN_SCRIPTS.values() if svc not in OFF_SERVICES]
assert UNFLOORED == ["documind-mcp", "documind-agent"]
assert "CAP ?= 1" in MK and "SLM_REGION ?= us-central1" in MK and "off-now: guard-project\n\tgcloud run jobs execute documind-off" in MK
assert '  echo "$$s: min-instances $$f"; done' in MK
import ast  # noqa: E402 - cost.py imports BigQuery at the top; its FALLBACK table is a literal, read without importing it
FALLBACK = ast.literal_eval(next(n.value for n in ast.parse(src["services/rag-api/cost.py"]).body
                                 if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK"))
MODELS = ["gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.1-pro-preview"]
RATES = {m: FALLBACK[m] for m in MODELS}
assert RATES == {"gemini-3.1-flash-lite": (0.25, 1.50), "gemini-3.6-flash": (1.50, 7.50), "gemini-3.1-pro-preview": (2.00, 12.00)}

# ------------------------------------------------------------------ the cells
MAP_PY = """import pathlib, re, sys
sys.path.insert(0, "services/rag-api")
import breakers                                                     # the kit's own table, run below
router, deploy, mk = (open(p, encoding="utf-8").read() for p in ("services/rag-api/router.py", "commands/lesson-12.2.sh", "Makefile"))
budget_tf, off_tf = (open(f"terraform/{f}", encoding="utf-8").read() for f in ("budget.tf", "off.tf"))
classes = re.findall(r"^    (SIMPLE|MEDIUM|COMPLEX) = ", router, re.M)
print("per answer: ROUTING=" + re.search(r"ROUTING=\\$\\{ROUTING-(\\w+)\\}", deploy).group(1) + " on the lane (lesson-12.2.sh). With it on, "
      + re.search(r'CLASSIFIER_MODEL = "([^"]+)"', router).group(1) + " labels each question " + ", ".join(classes)
      + ", and breakers.choose_model() picks the model:")
print((f"  {'spend':8}" + "".join(f"{c:24}" for c in classes)).rstrip())
for pct in (0, 79.9, 80, 85, 100, 120):
    print((f"  {str(pct) + '%':8}" + "".join(f"{breakers.choose_model(c, pct):24}" for c in classes)).rstrip())
cap = re.search(r"BUDGET_USD=\\$\\{BUDGET_USD-(\\d+)\\}", deploy).group(1)
print(f"  the spend: Firestore budget/<month, UTC>, USD added by every answer, over BUDGET_USD ({cap} on the lane); SPEND_PCT replaces it")
readers = [p.as_posix() for p in pathlib.Path("services").rglob("*.py") if "BUDGET_FLOOR_PCT" in p.read_text(encoding="utf-8") and p.name != "breakers.py"]
print(f"  BUDGET_FLOOR_PCT = {breakers.BUDGET_FLOOR_PCT} (the comment's min-instances 0): read by " + (", ".join(readers) or "nothing"))
rules = [float(t) for t in re.findall(r"threshold_percent = ([\\d.]+)", budget_tf)]
print("per month: " + re.search(r'display_name    = "([^"]+)"', budget_tf).group(1) + ", BUDGET_AMOUNT " + re.search(r"BUDGET_AMOUNT\\s+\\?= (\\d+)", mk).group(1)
      + " in the billing account's currency; it emails at " + ", ".join(f"{r:.0%}" for r in rules[:-1]) + f" and at a {rules[-1]:.0%} forecast")
loop = off_tf.split("for pair in", 1)[1].split("; do", 1)[0]
print("per hour: documind-off runs " + re.search(r'schedule    = "([^"]+)"', off_tf).group(1) + " " + re.search(r'time_zone   = "([^"]+)"', off_tf).group(1)
      + " and floors " + ", ".join(re.findall(r"(documind-[\\w-]+):", loop)) + " to min-instances 0; make off does the same by hand")
print("  make gpu-cap: the GPU quota in " + re.search(r"SLM_REGION \\?= ([\\w-]+)", mk).group(1) + " capped at " + re.search(r"CAP \\?= (\\d+)", mk).group(1)
      + "; alerts.tf's gpu_left_warm pages when one stays up two hours")"""

MONTH_PY = """import datetime as dt, json, os, subprocess
from google.cloud import firestore
P, R = os.environ["PROJECT"], os.environ["REGION"]
def gcloud(*a):
    return subprocess.run(["gcloud", *a], capture_output=True, text=True)
svc = json.loads(gcloud("run", "services", "describe", "documind-api", "--region", R, "--project", P, "--format", "json").stdout)
env = {e["name"]: e.get("value") for e in svc["spec"]["template"]["spec"]["containers"][0].get("env", [])}
month = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m")
snap = firestore.Client(project=P).collection("budget").document(month).get()
usd = float((snap.to_dict() or {}).get("usd", 0.0)) if snap.exists else 0.0
cap = float(env.get("BUDGET_USD") or 100)
pct = float(env["SPEND_PCT"]) if env.get("SPEND_PCT") else 100 * usd / cap
print(f"documind-api: ROUTING={env.get('ROUTING', 'off')}, BUDGET_USD={cap:g}, SPEND_PCT={env.get('SPEND_PCT') or 'unset'}")
print(f"the counter, budget/{month}: USD {usd:.4f} of {cap:g} = {pct:.2f}% - the breaker would read '{'strict' if pct >= 80 else 'normal'}'")
account = gcloud("billing", "projects", "describe", P, "--format=value(billingAccountName)").stdout.strip().rsplit("/", 1)[-1]
b = gcloud("billing", "budgets", "list", f"--billing-account={account}", "--format=json")
if b.returncode != 0:
    print("the billing budget: not readable as you (the Budgets API needs billing.budgets.list on the billing account)")
for budget in json.loads(b.stdout or "[]") if b.returncode == 0 else []:
    if budget.get("displayName") == "DocuMind monthly budget":
        amount = budget["amount"]["specifiedAmount"]
        rules = ", ".join(f"{float(t['thresholdPercent']):.0%}" + (" forecast" if t.get("spendBasis") == "FORECASTED_SPEND" else "")
                          for t in budget.get("thresholdRules", []))
        print(f"the billing budget: {amount.get('units')} {amount.get('currencyCode')} a month on the whole project; emails at {rules}")"""

ASK_PY = """import json, os, subprocess, urllib.request
P, API, URL = os.environ["PROJECT"], os.environ["API"], os.environ["URL"]
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
for q in %r:
    body = json.dumps({"query": q, "tenant_id": "acme"}).encode()
    req = urllib.request.Request(URL + "/v1/query", data=body, headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    a = json.load(urllib.request.urlopen(req, timeout=180))
    print(f"  {a['model']:24} {q}")
    print(f"  {'':24} {a['answer'][:132] + ('...' if len(a['answer']) > 132 else '')}")""" % QUESTIONS

COUNT_PY = """import datetime as dt, json, os, subprocess, urllib.parse, urllib.request
P = os.environ["PROJECT"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
end = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
stamp = lambda t: t.isoformat().replace("+00:00", "Z")
query = {"filter": 'metric.type="run.googleapis.com/container/instance_count" AND resource.labels.service_name="documind-ui"',
         "interval.startTime": stamp(end - dt.timedelta(minutes=30)), "interval.endTime": stamp(end)}
url = f"https://monitoring.googleapis.com/v3/projects/{P}/timeSeries?" + urllib.parse.urlencode(query)
series = json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": "Bearer " + tok}), timeout=60))
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
count = {}
for s in series.get("timeSeries", []):                          # one series per state: active, idle
    for p in s["points"]:
        t = dt.datetime.fromisoformat(p["interval"]["endTime"].replace("Z", "+00:00")).astimezone(IST)
        count[t] = count.get(t, 0) + int(p["value"]["int64Value"])
points = sorted(count.items())
print("documind-ui, container instances (active and idle), a sample a minute, last 30 minutes:")
for i in range(0, len(points), 10):
    print("  " + "  ".join(f"{t:%H:%M} {n}" for t, n in points[i:i + 10]))
zero = next((t for i, (t, n) in enumerate(points) if all(m == 0 for _, m in points[i:])), None)
print(f"zero instances since {zero:%H:%M} IST" if zero and points[-1][1] == 0
      else "not zero yet: an idle instance can stay up to 15 minutes after its last request; run this again")"""


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


ASK_FN = ("ask133() {   # ask133 URL: three acme questions (a lookup, an explanation, a worked sum) as documind-ui-sa - the model that answered each\n"
          + heredoc(ASK_PY, 'URL="$1" ') + "\n}")
CELLS = {
    "map": heredoc(MAP_PY),
    "month": heredoc(MONTH_PY) + '\nmake gpu-quota PROJECT="$PROJECT"',
    "cand": ('gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\\n'
             "  --update-env-vars ROUTING=on --quiet\n"
             'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"\n' + ASK_FN + '\nask133 "$CAND"'),
    "replay": ('gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\\n'
               "  --update-env-vars SPEND_PCT=85 --quiet     # the replay: the breaker reads 85, the counter is not touched\n"
               'ask133 "$CAND"'),
    "undo": ('gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag candidate \\\n'
             "  --update-env-vars ROUTING=off --remove-env-vars SPEND_PCT --quiet     # env vars merge: take them back off the template\n"
             'gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet\n'
             'gcloud run services describe documind-api --region "$REGION" --project "$PROJECT" --format=\'value(status.traffic[].percent,status.traffic[].revisionName)\''),
    "off": ('gcloud run services update documind-ui --region "$REGION" --project "$PROJECT" --min-instances 1 --quiet   # a session day\'s floor\n'
            'make off PROJECT="$PROJECT"\n'
            'gcloud scheduler jobs describe documind-off-nightly --location "$REGION" --project "$PROJECT" \\\n'
            "  --format='value(schedule,timeZone,state,lastAttemptTime)'"),
    "count": "sleep 900     # Cloud Run keeps an idle instance up to 15 minutes\n" + heredoc(COUNT_PY),
    "cap": 'make gpu-cap PROJECT="$PROJECT"',
}

T = Path(tempfile.mkdtemp(prefix="lesson133-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ,
       "REGION": "asia-south1", "GOOGLE_CLOUD_PROJECT": PROJ, "USERPROFILE": str(T), "HOME": str(T)}
for k in [k for k in ENV if k.startswith(("RETRIEVAL_", "TOP_K", "RERANK_", "SEMANTIC_", "VECTOR_", "GENERATOR_", "ARMOR", "ROUTING", "SPEND_", "BUDGET_"))]:
    ENV.pop(k)


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout


# ---- step 3: the controls as the kit writes them down
OUT = {"map": run_cell(MAP_PY, cwd=KIT)}
M3 = OUT["map"]
assert "  85%     gemini-3.1-flash-lite   gemini-3.1-flash-lite   gemini-3.6-flash\n" in M3, M3
assert "  0%      gemini-3.1-flash-lite   gemini-3.6-flash        gemini-3.1-pro-preview\n" in M3, M3
assert "BUDGET_FLOOR_PCT = 100 (the comment's min-instances 0): read by nothing" in M3 and "emails at 50%, 80%, 100% and at a 120% forecast" in M3, M3
assert "floors documind-slm, documind-vllm, documind-gateway, documind-ui to min-instances 0" in M3, M3

# ---- the stand-in lane, a module every process below imports as lane133
LANE_LIB = r'''"""The stand-in lane for lesson 11.6's build. The kit's rag-api runs on top of it with ROUTING on: its query() calls
router.classify() and breakers.choose_model() with budget.spend_pct() reading the month's counter, then generates with
the model the breaker chose. Below the kit's code: Firestore in JSON files (acme's handbook, cut by the kit's chunker,
and the budget counter, which the kit's own record() increments), the index, the Ranking API, and Gemini - a
classifier that labels by the question's words, and a reader that answers from the packed clause. For the cells:
gcloud, the Cloud Monitoring API and the Service Usage API, answered from the lane's state."""
import collections
import datetime as dt
import io
import json
import math
import os
import re
import subprocess
import sys
import types
import urllib.parse
import urllib.request
from types import SimpleNamespace

KIT = os.environ["LANE133_KIT"]
with open(os.environ["LANE133_CORPUS"], encoding="utf-8") as _f:
    CORPUS = json.load(_f)
STATE_PATH = os.environ["LANE133_STATE"]
LAST = {"q": ""}                                   # the question embed_query was last given


def state() -> dict:
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


# ---- similarity: the stand-in for text-embedding-005 and for the Ranking API - word overlap, TF-IDF weighted
STOP = set("a an the of for to in on at by is are be what which who how when does do i my can during with and or from as per this that it its".split())


def _toks(text: str, pairs: bool) -> list:
    w = [x for x in re.findall(r"[a-z0-9]+", text.lower()) if x not in STOP]
    return w + ([a + "_" + b for a, b in zip(w, w[1:])] if pairs else [])


_TEXTS = sorted({r["text"] for r in CORPUS["rows"].values()})
_DF = collections.Counter(t for text in _TEXTS for t in set(_toks(text, True)))
_VEC: dict = {}


def _vec(text: str, pairs: bool) -> dict:
    key = (text, pairs)
    if key not in _VEC:
        c = collections.Counter(_toks(text, pairs))
        v = {t: (1 + math.log(n)) * (math.log((len(_TEXTS) + 1) / (_DF.get(t, 0) + 1)) + 1) for t, n in c.items()}
        s = math.sqrt(sum(x * x for x in v.values())) or 1.0
        _VEC[key] = {t: x / s for t, x in v.items()}
    return _VEC[key]


def sim(a: str, b: str, pairs: bool = False) -> float:
    va, vb = _vec(a, pairs), _vec(b, pairs)
    return round(sum(x * vb.get(t, 0.0) for t, x in va.items()), 6)


# ---- Firestore: the chunk rows (every one current), the tenant's pin, and the month's budget counter
MEM: dict = collections.defaultdict(dict)


def rows(coll: str) -> dict:
    base = {k: dict(v) for k, v in (CORPUS["rows"].items() if coll == "chunks" else state().get(coll, {}).items())}
    for k, v in MEM[coll].items():
        base[k] = dict(v)
    return base


class Snap:
    def __init__(self, id_, data, ref=None):
        self.id, self._d, self.exists, self.reference = id_, data, data is not None, ref

    def to_dict(self):
        return None if self._d is None else dict(self._d)


class Doc:
    def __init__(self, coll: str, id_: str):
        self.coll, self.id = coll, id_

    def get(self):
        return Snap(self.id, rows(self.coll).get(self.id), self)

    def set(self, data, merge=False):
        """A write, with firestore.Increment applied the way Firestore applies it: added to what is there."""
        from google.cloud.firestore_v1.transforms import Increment
        old = (rows(self.coll).get(self.id) or {}) if merge else {}
        new = dict(old)
        for k, v in data.items():
            new[k] = (old.get(k) or 0) + v.value if isinstance(v, Increment) else v
        MEM[self.coll][self.id] = new


def _holds(id_: str, d: dict, field: str, op: str, value) -> bool:
    x = id_ if field == "__name__" else d.get(field)
    if op == "==":
        return x == value
    if op == "in":
        return x in value
    raise NotImplementedError(op)


class Query:
    def __init__(self, coll: str, preds=(), lim=None):
        self.coll, self.preds, self.lim = coll, tuple(preds), lim

    def where(self, field=None, op=None, value=None, *, filter=None):
        if filter is not None:
            field, op, value = filter.field_path, filter.op_string, filter.value
        return Query(self.coll, self.preds + ((field, op, value),), self.lim)

    def limit(self, n):
        return Query(self.coll, self.preds, n)

    def document(self, id_):
        return Doc(self.coll, id_)

    def matched(self) -> list:
        return [(i, d) for i, d in rows(self.coll).items() if all(_holds(i, d, *p) for p in self.preds)]

    def stream(self):
        return [Snap(i, d, Doc(self.coll, i)) for i, d in self.matched()[:self.lim]]

    get = stream

    def find_nearest(self, vector_field, query_vector, distance_measure=None, limit=10, distance_result_field=None, **kw):
        return Nearest(self, limit, distance_result_field)


class Nearest:
    def __init__(self, q: Query, limit: int, field):
        self.q, self.limit, self.field = q, limit, field

    def get(self):
        scored = sorted(((sim(LAST["q"], d.get("text") or ""), i, d) for i, d in self.q.matched()), key=lambda x: (-x[0], x[1]))
        out = []
        for s, i, d in scored[:self.limit]:
            if self.field:
                d[self.field] = round(1.0 - s, 6)
            out.append(Snap(i, d, Doc(self.q.coll, i)))
        return out


class DBClass:
    def collection(self, name):
        return Query(name)


DB = DBClass()


# ---- the index, the Ranking API and Gemini
class Index:
    def find_neighbors(self, deployed_index_id, queries, num_neighbors, filter=None):
        allow = {ns.name: set(ns.allow_tokens) for ns in (filter or [])}
        keep = lambda d: all({"tenant_id": d["tenant_id"], "doc_type": d["doc_type"], "kind": d["kind"],  # noqa: E731
                              "current": "true"}.get(k) in toks for k, toks in allow.items())
        found = sorted(((sim(LAST["q"], d["text"]), i) for i, d in CORPUS["rows"].items() if keep(d)), key=lambda x: (-x[0], x[1]))
        return [[SimpleNamespace(id=i, distance=s) for s, i in found[:num_neighbors]]] if found else []


class Ranker:
    def ranking_config_path(self, project, location, ranking_config):
        return f"projects/{project}/locations/{location}/rankingConfigs/{ranking_config}"

    def rank(self, request, timeout=None):
        order = sorted(((sim(request.query, r.content, pairs=True), int(r.id)) for r in request.records), key=lambda x: (-x[0], x[1]))
        return SimpleNamespace(records=[SimpleNamespace(id=str(i), score=round(s, 4)) for s, i in order[:request.top_n]])


def classify_words(query: str) -> str:
    """The classifier, stood in: router.py's criteria read off the question's words - a worked, multi-step question is
    COMPLEX, a comparison or an explanation MEDIUM, a lookup SIMPLE."""
    q = query.lower()
    return "COMPLEX" if "step by step" in q or "work out" in q else "MEDIUM" if "compare" in q or "explain" in q else "SIMPLE"


def inr(n: int) -> str:
    """Rupees the Indian way: the last three digits, then pairs - 1,00,000."""
    s = str(n)
    head, tail = s[:-3], s[-3:]
    pairs = []
    while len(head) > 2:
        pairs.insert(0, head[-2:])
        head = head[:-2]
    return ",".join(([head] if head else []) + pairs + [tail])


def _reply(prompt: str):
    """Gemini, stood in by a reader: the answer from the packed clause that states it, cited, or a refusal."""
    question = prompt.rsplit("\n\nQuestion:", 1)[1].strip()
    ctx = prompt.split("\nContext:\n", 1)[1].rsplit("\n\nQuestion:", 1)[0]
    parts = re.split(r"(?m)^\[Source (\d+)\] ?(.*)$", ctx)
    draft = {"answer": "The context does not say.", "citations": [], "confidence": "low", "answerable": False}
    for k in range(1, len(parts) - 2, 3):
        n, body = int(parts[k]), parts[k + 2]
        q = question.lower()
        if "notice" in q:
            m = re.search(r"serves a notice period of (\d+) days", body)
            if m:
                draft = {"answer": f"A confirmed employee at grade E3 or above serves a notice period of {m.group(1)} days [{n}].",
                         "citations": [{"source": n, "quote": f"serves a notice period of {m.group(1)} days"}], "confidence": "high", "answerable": True}
                break
        elif "travel" in q or "trip" in q:
            m = re.search(r"capped at Rs ([\d,]+) per trip", body)
            if m:
                cap = int(m.group(1).replace(",", ""))
                costs = [int(x.replace(",", "")) for x in re.findall(r"Rs ([\d,]+)", question)]
                if costs:
                    paid = [min(c, cap) for c in costs]
                    over = sum(c - cap for c in costs if c > cap)
                    answer = (f"Each trip is reimbursed up to the cap of Rs {inr(cap)} [{n}]: " + " + ".join(f"Rs {inr(x)}" for x in paid)
                              + f" = Rs {inr(sum(paid))}; the Rs {inr(over)} above the cap needs the function head's written approval.")
                else:
                    answer = (f"Travel is capped at Rs {inr(cap)} per trip [{n}]; a trip above the cap needs the function head's "
                              f"written approval before travel [{n}].")
                draft = {"answer": answer, "citations": [{"source": n, "quote": f"capped at Rs {m.group(1)} per trip"}],
                         "confidence": "high", "answerable": True}
                break
    usage = SimpleNamespace(prompt_token_count=len(prompt) // 4, candidates_token_count=len(draft["answer"]) // 4 + 24,
                            thoughts_token_count=0, cached_content_token_count=0)
    return SimpleNamespace(parsed=draft, text=json.dumps(draft), usage_metadata=usage,
                           candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))], prompt_feedback=None)


CALLS: list = []                                   # every model call this process made, in order: (model, what for)


class Models:
    def generate_content(self, model, contents, config=None):
        text = contents[0] if isinstance(contents, list) else contents
        if isinstance(text, str) and text.startswith("Classify this query's complexity level."):
            label = classify_words(text.rsplit("Query:", 1)[1])
            CALLS.append((model, "classify"))
            return SimpleNamespace(text=label, parsed=None)
        CALLS.append((model, "answer"))
        return _reply(text)


class GenaiClient:
    def __init__(self, *a, **kw):
        self.models, self.caches = Models(), None
        self._api_client = SimpleNamespace(location=kw.get("location"))


def _mod(name: str, **attrs):
    m = types.ModuleType(name)
    m.__dict__.update(attrs)
    sys.modules[name] = m
    return m


def stubs() -> None:
    """The modules rag-api imports that this machine does not have; nothing below reaches them."""
    if "google.cloud.discoveryengine_v1" in sys.modules:
        return
    from opentelemetry.sdk.trace.export import SpanExporter, SpanExportResult

    class CloudTraceSpanExporter(SpanExporter):
        def __init__(self, **kw):
            pass

        def export(self, spans):
            return SpanExportResult.SUCCESS

        def shutdown(self):
            pass

    class FastAPIInstrumentor:
        @staticmethod
        def instrument_app(app, **kw):
            return None

    class GoogleGenAiSdkInstrumentor:
        def instrument(self, **kw):
            return None

    class Namespace:
        def __init__(self, name, allow_tokens=None, deny_tokens=None):
            self.name, self.allow_tokens, self.deny_tokens = name, list(allow_tokens or []), list(deny_tokens or [])

    class Rec:
        def __init__(self, **kw):
            self.__dict__.update(kw)

    class Anything:
        def __init__(self, *a, **kw):
            pass

        def __getattr__(self, name):
            return lambda *a, **kw: None

    _mod("opentelemetry.exporter.cloud_trace", CloudTraceSpanExporter=CloudTraceSpanExporter)
    _mod("opentelemetry.instrumentation.fastapi", FastAPIInstrumentor=FastAPIInstrumentor)
    _mod("opentelemetry.instrumentation.google_genai", GoogleGenAiSdkInstrumentor=GoogleGenAiSdkInstrumentor)
    _mod("google.cloud.aiplatform", MatchingEngineIndexEndpoint=Anything, MatchingEngineIndex=Anything, init=lambda **kw: None)
    _mod("google.cloud.aiplatform.matching_engine")
    _mod("google.cloud.aiplatform.matching_engine.matching_engine_index_endpoint", Namespace=Namespace)
    _mod("google.cloud.discoveryengine_v1", RankServiceClient=Anything, RankingRecord=Rec, RankRequest=Rec)
    for name in ("bigquery", "storage", "spanner", "logging"):
        _mod(f"google.cloud.{name}", Client=Anything)
    import google.genai
    google.genai.Client = GenaiClient
    import google.cloud.firestore
    google.cloud.firestore.Client = lambda *a, **kw: DB


def rag():
    """rag-api's modules, imported from the kit and wired to the stand-ins above. record() is the kit's own."""
    stubs()
    sys.path[:0] = [KIT, os.path.join(KIT, "services", "rag-api")]
    import main
    import retriever
    import generator
    import cache_manager
    main._fs = retriever._fs = lambda: DB
    retriever._index_endpoint = lambda: Index()
    retriever._ranker = lambda: Ranker()

    def embed(q):
        LAST["q"] = q
        return [0.001] * 768
    main.embed_query = retriever.embed_query = embed
    main.enforce_membership = lambda email, tenant_id: None     # the roster is lesson 8's; every ask here is a member's

    def caches():
        m = object.__new__(cache_manager.TenantCacheManager)
        m.db, m.global_client, m.regional_client = DB, GenaiClient(), GenaiClient()
        return m
    generator._caches = caches
    return main


def serve(port: int, who: dict) -> None:
    """The kit's app on localhost, behind a stand-in of Cloud Run's IAM check; /calls reports the model calls made."""
    main = rag()
    import shared.iap as iap

    def identity(headers, bearer_audience=None):
        tok = headers.get("authorization", "").removeprefix("Bearer ")
        if tok not in who:
            raise iap.IapError("the bearer token carries no verified email")
        return {"email": who[tok], "via": "iam", "aud": bearer_audience}
    iap.identity = identity

    @main.app.get("/_standin/calls")
    def calls():
        return {"calls": CALLS, "budget": MEM["budget"]}

    class FrontDoor:
        def __init__(self, app):
            self.app = app

        async def __call__(self, scope, receive, send):
            if scope["type"] == "http" and not dict(scope["headers"]).get(b"authorization"):
                await send({"type": "http.response.start", "status": 403, "headers": [(b"content-type", b"text/html")]})
                await send({"type": "http.response.body", "body": b"<html><title>403 Forbidden</title></html>"})
                return
            await self.app(scope, receive, send)
    import uvicorn
    uvicorn.run(FrontDoor(main.app), host="127.0.0.1", port=port, log_level="warning")


# ---- gcloud, the Monitoring API and Service Usage, for the cells
def _monitoring(url: str) -> dict:
    st, path = state(), urllib.parse.urlparse(url)
    q = urllib.parse.parse_qs(path.query)
    assert path.path.endswith("/timeSeries") and "run.googleapis.com/container/instance_count" in q["filter"][0], (path, q)
    svc = re.search(r'service_name="([\w-]+)"', q["filter"][0]).group(1)
    return {"timeSeries": [{"resource": {"type": "cloud_run_revision", "labels": {"service_name": svc}}, "metric": {"labels": {"state": s}},
                            "metricKind": "GAUGE", "valueType": "INT64",
                            "points": [{"interval": {"startTime": t, "endTime": t}, "value": {"int64Value": str(n[s])}}
                                       for t, n in reversed(st["instances"][svc])]} for s in ("active", "idle")]}


def _gcloud(cmd: list) -> str:
    st = state()
    if cmd[:3] == ["gcloud", "auth", "print-identity-token"]:
        return "MEMBER\n"
    if cmd[:3] == ["gcloud", "auth", "print-access-token"]:
        return "ACCESS\n"
    if cmd[:4] == ["gcloud", "run", "services", "describe"]:
        env = [{"name": k, "value": v} for k, v in st["service_env"].items()]
        return json.dumps({"spec": {"template": {"spec": {"containers": [{"env": env}]}}}})
    if cmd[:4] == ["gcloud", "billing", "projects", "describe"]:
        return st["billing_account"] + "\n"
    if cmd[:4] == ["gcloud", "billing", "budgets", "list"]:
        return json.dumps(st["budgets"])
    raise SystemExit(f"the stand-in gcloud has no answer for {cmd[:4]}")


def fake_cli() -> None:
    """gcloud and the Monitoring API answer from the lane's state; the rest of subprocess and urllib stays."""
    real_run, real_open = subprocess.run, urllib.request.urlopen

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] == "gcloud":
            return subprocess.CompletedProcess(list(cmd), 0, _gcloud(list(cmd)), "")
        return real_run(cmd, *a, **kw)

    def urlopen(req, *a, **kw):
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        if url.startswith("https://monitoring.googleapis.com/"):
            return io.BytesIO(json.dumps(_monitoring(url)).encode())
        return real_open(req, *a, **kw)
    subprocess.run, urllib.request.urlopen = run, urlopen


class _Resp:
    def __init__(self, body, code=200):
        self._b, self.status_code, self.text = body, code, json.dumps(body)

    def json(self):
        return self._b

    def raise_for_status(self):
        assert self.status_code == 200, self.status_code


class QuotaSession:
    """Service Usage v1beta1 and Resource Manager, stood in for services/slm/gpu_quota.py: the project's GPU quota metrics
    from the lane's state, an override POSTed onto the region's bucket, and an operation that is already done."""
    def get(self, url, params=None, timeout=None):
        st = state()
        if "cloudresourcemanager" in url:
            return _Resp({"projectNumber": "314159265358"})
        if url.endswith("/consumerQuotaMetrics"):
            return _Resp({"metrics": st["quota_metrics"]})
        raise SystemExit(f"the stand-in Service Usage API has no GET for {url}")

    def post(self, url, params=None, json=None, timeout=None):
        st = state()
        for m in st["quota_metrics"]:
            for lim in m["consumerQuotaLimits"]:
                if url.startswith(f"https://serviceusage.googleapis.com/v1beta1/{lim['name']}/consumerOverrides"):
                    for b in lim["quotaBuckets"]:
                        if (b.get("dimensions") or {}) == (json.get("dimensions") or {}):
                            b["consumerOverride"] = {"name": lim["name"] + "/consumerOverrides/Cg1vdmVycmlkZQ", "overrideValue": json["overrideValue"]}
                            b["effectiveLimit"] = json["overrideValue"]
        with open(STATE_PATH, "w", encoding="utf-8") as f:
            import json as _j
            _j.dump(st, f)
        return _Resp({"name": "operations/quota-override-1", "done": True})


def quota_session() -> None:
    import google.auth
    import google.auth.transport.requests as gtr
    google.auth.default = lambda scopes=None: (None, "documind-ai-YOUR-ID")
    gtr.AuthorizedSession = lambda creds: QuotaSession()
'''

# ---- the stand-in lane: acme's handbook, as the kit's chunker cuts it, with the worker's chunk ids
sys.path.insert(0, str(KIT))
from hashlib import sha256  # noqa: E402
from shared.documind_corpus import chunk_document  # noqa: E402
ROWS = {}
data = (KIT / "evals/corpus/acme/hr_policy_2026.md").read_bytes()
SHA, URI = sha256(data).hexdigest(), f"gs://{PROJ}-uploads/acme/hr_policy_2026.md"
for i, c in enumerate(chunk_document({"text": data.decode("utf-8"), "source_uri": URI, "doc_type": "unknown", "slug": "hr_policy_2026"}, "acme")):
    ROWS[f"acme:{SHA}#{i}"] = {"tenant_id": "acme", "text": c["text"], "source_uri": URI, "page_start": None, "doc_type": "unknown", "kind": "text",
                               "doc_key": f"acme_{SHA}", "chunk_hash": c["chunk_hash"], "locator": c["locator"], "current": True,
                               **({"section": c["section"]} if c.get("section") else {})}
(T / "corpus133.json").write_text(json.dumps({"rows": ROWS}), encoding="utf-8")
(T / "lane133.py").write_text(LANE_LIB, encoding="utf-8")
STATE = T / "state133.json"
LIVE_ENV = {"ROUTING": "off", "BUDGET_USD": "100", "RETRIEVAL_BACKEND": "firestore", "GENERATOR_MODEL": "gemini-3.6-flash", "GIT_SHA": "COMMIT"}
L4 = {"metric": "run.googleapis.com/nvidia_l4_gpu_allocation_no_zonal_redundancy", "displayName": "Total NVIDIA L4 GPU allocation without zonal redundancy",
      "consumerQuotaLimits": [{"name": "projects/314159265358/services/run.googleapis.com/consumerQuotaMetrics/run.googleapis.com%2Fnvidia_l4_gpu_allocation_no_zonal_redundancy/limits/%2Fproject%2Fregion",
                               "unit": "1/{project}/{region}",
                               "quotaBuckets": [{"effectiveLimit": "3", "defaultLimit": "3"},
                                                {"effectiveLimit": "3", "defaultLimit": "3", "dimensions": {"region": "us-central1"}}]}]}
STATE.write_text(json.dumps({
    "tenant_settings": {"acme": {"retrieval_backend": "vector"}},
    "budget": {"2026-09": {"usd": 7.8412}},                                  # the month so far, on the stand-in lane
    "service_env": LIVE_ENV, "billing_account": "billingAccounts/0X0X0X-0X0X0X-0X0X0X",
    "budgets": [{"displayName": "DocuMind monthly budget", "amount": {"specifiedAmount": {"currencyCode": "INR", "units": "5000"}},
                 "thresholdRules": [{"thresholdPercent": 0.5, "spendBasis": "CURRENT_SPEND"}, {"thresholdPercent": 0.8, "spendBasis": "CURRENT_SPEND"},
                                    {"thresholdPercent": 1.0, "spendBasis": "CURRENT_SPEND"}, {"thresholdPercent": 1.2, "spendBasis": "FORECASTED_SPEND"}]}],
    "quota_metrics": [L4],
    "instances": {"documind-ui": [(f"2026-09-24T{6 + (m + 22) // 60:02d}:{(m + 22) % 60:02d}:00Z",
                                   {"active": 0, "idle": 1 if m < 17 else 0}) for m in range(30)]},
}), encoding="utf-8")
LANE_ENV = {"LANE133_KIT": str(KIT), "LANE133_CORPUS": str(T / "corpus133.json"), "LANE133_STATE": str(STATE), "PYTHONPATH": str(T)}
FREEZE = ("import datetime as _d\n"
          "_NOW = _d.datetime.fromisoformat('2026-09-24T06:52:00+00:00')\n"
          "class _Frozen(_d.datetime):\n"
          "    @classmethod\n"
          "    def now(cls, tz=None):\n"
          "        return _NOW.astimezone(tz) if tz else _NOW.replace(tzinfo=None)\n"
          "_d.datetime = _Frozen\n")
PRELUDE = FREEZE + "import lane133\nlane133.stubs()\nlane133.fake_cli()\n"
QUOTA = FREEZE + "import lane133\nlane133.quota_session()\n"

# ---- step 4: the month so far, and the GPU quota
GPU_PY = ("import runpy, sys\nsys.argv = ['gpu_quota.py', '--project', %r, '--region', 'us-central1'%s]\n"
          "try:\n    runpy.run_path('services/slm/gpu_quota.py', run_name='__main__')\nexcept SystemExit as e:\n    assert not e.code, e.code\n")
OUT["month"] = (run_cell(MONTH_PY, PRELUDE, env=LANE_ENV)
                + "python services/slm/gpu_quota.py --project documind-ai-YOUR-ID --region us-central1\n"
                + run_cell(GPU_PY % (PROJ, ""), QUOTA, cwd=KIT, env=LANE_ENV))
M4 = OUT["month"]
assert "documind-api: ROUTING=off, BUDGET_USD=100, SPEND_PCT=unset\n" in M4 and "USD 7.8412 of 100 = 7.84% - the breaker would read 'normal'" in M4, M4
assert "the billing budget: 5000 INR a month on the whole project; emails at 50%, 80%, 100%, 120% forecast" in M4, M4
assert "1/{project}/{region}         us-central1  effective 3 (default 3)" in M4, M4

# ---- step 5: the kit's app on localhost as the candidate - ROUTING on, then SPEND_PCT=85
with socket.socket() as s:
    assert s.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} is taken on this machine"
URL = f"http://127.0.0.1:{PORT}"
SERVE = f"import lane133; lane133.serve({PORT}, {{'MEMBER': {UI_SA!r}}})"


def candidate(extra: dict) -> tuple[str, dict]:
    log = T / f"api133-{len(extra)}.log"
    with open(log, "w", encoding="utf-8") as logf:
        srv = subprocess.Popen([sys.executable, "-c", SERVE], cwd=str(T), env={**ENV, **LANE_ENV, **LIVE_ENV, **extra}, stdout=logf, stderr=subprocess.STDOUT)
    try:
        for _ in range(150):
            try:
                urllib.request.urlopen(urllib.request.Request(URL + "/health", headers={"Authorization": "Bearer MEMBER"}), timeout=1).read()
                break
            except Exception:                      # noqa: BLE001 - not up yet
                time.sleep(0.2)
        else:
            raise SystemExit("the API did not start: " + log.read_text(encoding="utf-8")[-1500:])
        out = run_cell(ASK_PY, PRELUDE, env={**LANE_ENV, "API": "https://documind-api-NUMBER.asia-south1.run.app", "URL": URL})
        calls = json.load(urllib.request.urlopen(urllib.request.Request(URL + "/_standin/calls", headers={"Authorization": "Bearer MEMBER"}), timeout=5))
    finally:
        srv.terminate()
        srv.wait(timeout=20)
    rows = [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines() if line.startswith('{"event": "query"')]
    return out, {"calls": calls, "rows": rows}


OUT["cand"], NORMAL = candidate({"ROUTING": "on"})
OUT["replay"], STRICT = candidate({"ROUTING": "on", "SPEND_PCT": "85"})
MODELS_NORMAL = [r["model"] for r in NORMAL["rows"]]
MODELS_STRICT = [r["model"] for r in STRICT["rows"]]
assert MODELS_NORMAL == ["gemini-3.1-flash-lite", "gemini-3.6-flash", "gemini-3.1-pro-preview"], MODELS_NORMAL
assert MODELS_STRICT == ["gemini-3.1-flash-lite", "gemini-3.1-flash-lite", "gemini-3.6-flash"], MODELS_STRICT
for side in (NORMAL, STRICT):
    assert [c[1] for c in side["calls"]["calls"]] == ["classify", "answer"] * 3 and all(c[0] == "gemini-3.1-flash-lite" for c in side["calls"]["calls"][::2])
# record() is the kit's own: the counter grew by exactly the three rows' costs, on top of the month so far
GREW = NORMAL["calls"]["budget"]
MONTH_KEY = next(iter(GREW))                                                  # the server's own clock picks the month's document
BASE = json.loads(STATE.read_text(encoding="utf-8"))["budget"].get(MONTH_KEY, {}).get("usd", 0.0)
assert len(GREW) == 1 and abs(GREW[MONTH_KEY]["usd"] - (BASE + sum(r["cost_usd"] for r in NORMAL["rows"]))) < 1e-9, GREW
assert all(line in OUT["cand"] for line in (f"  {m:24} " for m in MODELS_NORMAL)) and "Rs 1,00,000" in OUT["cand"], OUT["cand"]
PRO_ROW = next(r for r in NORMAL["rows"] if r["model"] == "gemini-3.1-pro-preview")
FLASH_ROW = next(r for r in STRICT["rows"] if r["model"] == "gemini-3.6-flash")
assert PRO_ROW["cost_usd"] > FLASH_ROW["cost_usd"]                          # the same worked question, cheaper at 85 percent

# ---- step 6: the switch, the schedule, the count, the cap
OUT["undo"] = "100\tdocumind-api-00031-kez\n"
OUT["off"] = ("gcloud run services update documind-slm --region us-central1 --project documind-ai-YOUR-ID --min-instances 0 --quiet\n"
              "ERROR: (gcloud.run.services.update) Service [documind-slm] could not be found.\n"
              "make[1]: [Makefile:659: slm-off] Error 1 (ignored)\n...\n"
              "gcloud run services update documind-ui --region asia-south1 --project documind-ai-YOUR-ID --min-instances 0 --quiet\n"
              "Deploying...\n...\nDone.\n...\n"
              "documind-slm: min-instances absent\ndocumind-vllm: min-instances absent\n"
              "documind-gateway: min-instances absent\ndocumind-ui: min-instances 0\n"
              "0 23 * * *\tAsia/Kolkata\tENABLED\t2026-09-23T17:30:03.184Z\n")
assert "slm-off: guard-project\n\tgcloud run services update documind-slm --region $(SLM_REGION) --project $(PROJECT) --min-instances 0 --quiet" in MK
OUT["count"] = run_cell(COUNT_PY, PRELUDE, env=LANE_ENV)
C6 = OUT["count"]
assert "zero instances since 12:09 IST" in C6 and "  11:52 1  11:53 1" in C6 and "12:08 1  12:09 0" in C6, C6
OUT["cap"] = "python services/slm/gpu_quota.py --project documind-ai-YOUR-ID --region us-central1 --cap 1\n" + run_cell(GPU_PY % (PROJ, ", '--cap', '1'"), QUOTA, cwd=KIT, env=LANE_ENV)
assert "-> capped at 1" in OUT["cap"] and "effective 1 (default 3, override 1)" in OUT["cap"] and "1 override(s) written. Read back:" in OUT["cap"], OUT["cap"]
shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "map": "run in the operator shell, in the kit (the controls as the kit writes them down; no network)",
    "month": "run in the operator shell, in the kit (reads only)",
    "cand": "run in the operator shell, in the kit (a candidate revision, no traffic, ROUTING on; three questions)",
    "replay": "run in the operator shell, in the kit (the same candidate at 85 percent; the same three questions)",
    "undo": "run in the operator shell, in the kit (the variables off the template, the tag dropped)",
    "off": "run in the operator shell, in the kit (a floor, then the switch, then the nightly job's entry)",
    "count": "run in the operator shell, in the kit (after 15 minutes; reads only)",
    "cap": "run in the operator shell, in the kit (lowers one quota; make gpu-cap-off takes it back)",
}
OUT_LABELS = {
    "map": "(this cell run on the kit's own breakers.py, router.py, lesson-12.2.sh, budget.tf, off.tf and Makefile)",
    "month": "(a stand-in Firestore and gcloud, then the kit's gpu_quota.py against a stand-in Service Usage API; your figures are your lane's)",
    "cand": "(the kit's rag-api on a stand-in lane, the classifier and Gemini stood in; gcloud's deploy lines left out)",
    "replay": "(the same stand-ins, SPEND_PCT=85)",
    "undo": "shape (your revision's name)",
    "off": "shape (make and gcloud print more; a service you never deployed says absent)",
    "count": "(a stand-in of the Monitoring API; your times differ)",
    "cap": "(the kit's gpu_quota.py against a stand-in Service Usage API; your quota's names and limits are your project's)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: the router at any spend
TYPICAL = (2000, 300)                               # a prompt of 2,000 tokens and an answer of 300, priced at cost.py's rates
PRICES = {m: (TYPICAL[0] * i + TYPICAL[1] * o) / 1_000_000 for m, (i, o) in RATES.items()}
UI_JS = r"""var root = document.getElementById('rt'); if (!root) return;
  var RATES = %s, PRICES = %s, GENERATOR = 'gemini-3.6-flash', STRICT = %d, $ = function(id){ return document.getElementById(id); };
  function choose(cls, pct){ if (pct >= STRICT) { return cls === 'COMPLEX' ? 'gemini-3.6-flash' : 'gemini-3.1-flash-lite'; }
    return {'COMPLEX': 'gemini-3.1-pro-preview', 'MEDIUM': 'gemini-3.6-flash', 'MODERATE': 'gemini-3.6-flash'}[cls] || 'gemini-3.1-flash-lite'; }
  function pick(on, cls, pct){ return on ? choose(cls, pct) : GENERATOR; }
  window.__rt = pick;
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } e.textContent = text; return e; }
  function render(){ var on = $('rt-on').checked, cls = $('rt-cls').value, pct = Number($('rt-pct').value), out = $('rt-out');
    $('rt-pv').textContent = pct + '%%'; var m = pick(on, cls, pct), r = RATES[m], rs = PRICES[m] * 85; out.textContent = '';
    var rows = [['Routing', !on ? 'off: every question goes to GENERATOR_MODEL, whatever the spend' : pct >= STRICT ? 'strict, from ' + STRICT + '%%: Pro is never chosen' : 'normal', !on ? 'skip' : pct >= STRICT ? 'stop' : 'pass'],
      ['The model', m, 'pass'], ['Its rate', 'USD ' + r[0].toFixed(2) + ' in / ' + r[1].toFixed(2) + ' out, per million tokens', ''],
      ['A typical answer', 'Rs ' + rs.toFixed(3) + ' for 2,000 tokens in and 300 out, plus the classifier call, which no row prices', ''],
      ['At 100%%', pct >= 100 ? 'the comment in breakers.py says min-instances 0; no code does it' : 'not reached', pct >= 100 ? 'stop' : 'skip'],
      ['The billing budget', 'a different number: the whole project\'s bill in the account\'s currency; emails at 50, 80 and 100%%, and a 120%% forecast', 'skip']];
    rows.forEach(function(x){ out.appendChild(el('b', '', x[0])); out.appendChild(el('span', x[2], x[1])); }); }
  ['rt-on', 'rt-cls', 'rt-pct'].forEach(function(id){ $(id).addEventListener('input', render); $(id).addEventListener('change', render); });
  $('rt-cls').value = 'COMPLEX'; $('rt-pct').value = 85; render();""" % (json.dumps(RATES), json.dumps(PRICES), breakers.BUDGET_STRICT_PCT)

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

# the port against the kit: every class, every half percent from 0 to 120, ROUTING on and off
GRID = [(on, c, p / 2) for on in (True, False) for c in ("SIMPLE", "MEDIUM", "COMPLEX", "MODERATE", "OTHER") for p in range(0, 241)]
EXPECT = [breakers.choose_model(c, p) if on else "gemini-3.6-flash" for on, c, p in GRID]
NODE = ("var window = {}, document = {getElementById: function(){ return null; }};\n"
        "var src = " + json.dumps(UI_JS.replace("var root = document.getElementById('rt'); if (!root) return;", "")) + ";\n"
        "var f = new Function('window', 'document', src.split('function el(')[0]); f(window, document);\n"
        "var grid = " + json.dumps(GRID) + ";\nprocess.stdout.write(JSON.stringify(grid.map(function(g){ return window.__rt(g[0], g[1], g[2]); })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
assert json.loads(node.stdout) == EXPECT, "the panel's port disagrees with breakers.choose_model()"

STATS = {"N_GRID": str(len(GRID)), "COST_PRO": f"{PRO_ROW['cost_usd'] * 85:.2f}", "COST_FLASH": f"{FLASH_ROW['cost_usd'] * 85:.2f}",
         "UNFLOORED": ", ".join(UNFLOORED)}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: the controls from breakers.py, router.py, budget.tf and off.tf; the tier from the kit's rag-api at the counter and at 85%"
      f" | panel port checked against breakers.choose_model() on {len(GRID)} points")
