"""Build lesson 11.5 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Reconcile usage events, reports and alerts. Every answer writes one usage row (main.py usage_row, media.py's _usage,
the chat service's turn row), and four readers count those rows: Cloud Logging keeps them all; the log sink copies
some into BigQuery, where tenant_daily groups them by Indian day; make usage (evals/usage_rows.py) reads the log for
the last N hours; two log-based metrics count them for an alert. Offline: the four readers as the kit writes them
down, and what each one leaves out. Live: four questions, their rows in make usage; the view reconciled with make
usage's own grouping over the same Indian day, group by group, to the paisa; the lane's alert policies and what each
reads - nothing reads the dead-letter queue; the policy this lesson adds to alerts.tf, planned and applied through the
kit's reviewed path; a drill message in the dead-letter queue, the gauge the policy reads above zero, the incident,
and the drill message acknowledged.

Kit change in this lesson's pull request: google_monitoring_alert_policy.dlq_depth in terraform/alerts.tf (quota.tf
listed a dlq_depth alert that no resource declared, under a subscription name that does not exist).

Build-time proof: the offline cell runs on the kit. The rows are the kit's own: its rag-api served on localhost behind a
Cloud Run stand-in, answering over a stand-in lane (acme's and zeta's handbooks cut by the kit's chunker, Firestore,
the index, the Ranking API and a reader for Gemini stood in). make usage is the kit's usage_rows.py and the reconcile
cell imports its group(); Cloud Logging, BigQuery (tenant_daily's arithmetic over the rows the sink's filter exports,
both parsed from the kit and asserted), Pub/Sub and Cloud Monitoring are stood in, and the clock is frozen at 11:22 IST.
The panel's eight rows are the kit's own row builders (usage_row, media._usage) and the chat turn's line, and each
reader's verdict comes from the filters parsed out of sink.tf, tenant_daily.sql, usage_rows.py and alerts.tf.
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

LESSON = "11.5"
title = "<title>Lesson 11.5 Reconcile usage events, reports and alerts - one row, four readers, and the queue nobody watched | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
UI_SA = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
PORT = 8132
ASKS = [("acme", "lk-01"), ("acme", "lk-06"), ("acme", "rf-01"), ("zeta", "iso-01")]

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.rw-list{display:grid;grid-template-columns:1fr;gap:2px;margin:4px 0 8px;}
.rw-list label{display:flex;align-items:center;gap:10px;min-height:44px;font-size:13px;color:var(--navy);cursor:pointer;}
.rw-list input{width:20px;height:20px;flex:0 0 auto;accent-color:var(--teal);}
.rd-grid{display:grid;grid-template-columns:minmax(0,1fr) auto auto;gap:4px 12px;font-size:12.5px;align-items:baseline;}
.rd-grid b{color:var(--navy);font-weight:600;}
.rd-grid .num{font-family:var(--mono);text-align:right;white-space:nowrap;}
.rd-why{margin:8px 0 0;font-size:12.5px;color:var(--slate);}
.rd-why .pass{color:var(--teal-dark);font-weight:600;}
.rd-why .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
SINK, VIEW, TOOL, ALERTS = "terraform/sink.tf", "terraform/sql/tenant_daily.sql", "evals/usage_rows.py", "terraform/alerts.tf"
EXCERPTS = {
    "sink": ("terraform/sink.tf - the sink: which services' rows, and which events, BigQuery ever sees",
             block(SINK, 'resource "google_logging_project_sink" "api_to_bq" {', n=13)),
    "view": ("terraform/sql/tenant_daily.sql - the view: the events it reads from the sink's table, and its GROUP BY",
             block(VIEW, 'WHERE jsonPayload.event IN ("query", "stream", "media")', n=3)),
    "tool": ("evals/usage_rows.py - make usage: one service, three events, the last N hours",
             block(TOOL, "def read_rows(project: str, hours: int", n=5)),
    "dlq": ("terraform/alerts.tf - the dead-letter policy this lesson adds",
            block(ALERTS, 'resource "google_monitoring_alert_policy" "dlq_depth" {', n=18)),
}
assert '(jsonPayload.event = "query" OR jsonPayload.event = "stream" OR jsonPayload.event = "chat" OR\n' in EXCERPTS["sink"][1]
assert EXCERPTS["sink"][1].rstrip().endswith("bigquery_options { use_partitioned_tables = true }")
assert "GROUP BY day, tenant, surface" in EXCERPTS["view"][1]
assert 'OR jsonPayload.event="media") AND timestamp>="{since}"' in EXCERPTS["tool"][1]
assert "num_undelivered_messages" in EXCERPTS["dlq"][1] and "local.alert_channel_ids" in EXCERPTS["dlq"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts: the four readers' filters, parsed
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (SINK, VIEW, TOOL, ALERTS, "terraform/quota.tf", "terraform/eventarc.tf",
                                                           "services/admin/admin_dashboard.py", "services/chat/agent.py",
                                                           "services/rag-api/media.py", "services/rag-api/main.py", "Makefile")}


def tf_block(text: str, head: str) -> str:
    """One terraform resource block, from its header line to the closing brace at column 0."""
    i = text.index(head)
    return text[i:text.index("\n}\n", i) + 2]


SINK_FILTER = src[SINK].split("filter", 1)[1].split("EOT", 2)[1]
SINK_SERVICES = list(dict.fromkeys(re.findall(r'resource\.labels\.service_name = "([\w-]+)"', SINK_FILTER)))
SINK_EVENTS = re.findall(r'jsonPayload\.event = "(\w+)"', SINK_FILTER)
VIEW_EVENTS = re.findall(r'"(\w+)"', src[VIEW].split("WHERE jsonPayload.event IN (", 1)[1].split(")", 1)[0])
VIEW_KEYS = [k.strip() for k in src[VIEW].rsplit("GROUP BY", 1)[1].rstrip().rstrip(";").split(",")][1:]
DESK_EVENTS = ["desk", "passages", "desk_shadow", "desk_gate"]               # the DocuMind Desk's rows (lessons 5.6, 10.4)
# the two the sink copies on a condition: no sensitive row beside its turn's chat row, which names the person
SINK_CONDITIONS = re.findall(r'\(jsonPayload\.event = "(\w+)" AND ([^)]+)\)', SINK_FILTER)
assert SINK_CONDITIONS == [("desk_shadow", 'NOT jsonPayload.case_type = "sensitive"'),
                           ("desk_gate", 'resource.labels.service_name = "documind-chat"')], SINK_CONDITIONS
assert SINK_SERVICES == ["documind-api", "documind-chat"] and SINK_EVENTS == ["query", "stream", "chat"] + DESK_EVENTS, (SINK_SERVICES, SINK_EVENTS)
assert VIEW_EVENTS == ["query", "stream", "media"], VIEW_EVENTS
assert VIEW_KEYS == ["tenant", "surface", "model_backend", "prompt_version", "retrieval_mode", "retrieval_backend", "modality"], VIEW_KEYS
assert 'DATE(timestamp, "Asia/Kolkata") AS day' in src[VIEW] and "FROM `documind_observability.run_googleapis_com_stdout`" in src[VIEW]
for expr in ("COUNT(*) AS queries", "COUNTIF(jsonPayload.answerable = false) AS unanswerable",
             "SUM(CAST(jsonPayload.tokens_in  AS INT64)) AS tokens_in", "SUM(CAST(jsonPayload.tokens_out AS INT64)) AS tokens_out",
             "ROUND(SUM(CAST(jsonPayload.cost_usd AS FLOAT64)), 4) AS cost_usd", "ROUND(SUM(CAST(jsonPayload.cost_usd AS FLOAT64)) * 85, 2) AS cost_inr"):
    assert expr in src[VIEW], expr                  # the arithmetic the stand-in BigQuery implements, and nothing else
TOOL_EVENTS = re.findall(r'jsonPayload\.event="(\w+)"', src[TOOL].split("def read_rows", 1)[1].split("def p95", 1)[0])
assert TOOL_EVENTS == ["query", "stream", "media"] and 'service: str = "documind-api", limit: int = 2000' in src[TOOL]
assert "USD_INR = 85" in src[TOOL] and 'ap.add_argument("--hours", type=int, default=24)' in src[TOOL]
assert "limit" not in src[TOOL].split("def main", 1)[1].split("rows = read_rows", 1)[1].split("return 0", 1)[0]   # a full read is not flagged
METRICS = {}
for name in re.findall(r'resource "google_logging_metric" "(\w+)"', src[ALERTS]):
    b = tf_block(src[ALERTS], f'resource "google_logging_metric" "{name}"')
    METRICS[re.search(r'name\s+= "([^"]+)"', b).group(1)] = b.split("filter", 1)[1].split("EOT", 2)[1]
Q_FILTER = METRICS["documind/queries"]
METRIC_SERVICE = re.search(r'service_name="([\w-]+)"', Q_FILTER).group(1)
METRIC_EVENTS = re.findall(r'jsonPayload\.event="(\w+)"', Q_FILTER)
assert METRIC_SERVICE == "documind-api" and METRIC_EVENTS == ["query", "stream"]
POLICIES = []                                       # the lane's policies, as alerts.tf declares them (reconcile_job off)
for name in re.findall(r'resource "google_monitoring_alert_policy" "(\w+)"', src[ALERTS]):
    b = tf_block(src[ALERTS], f'resource "google_monitoring_alert_policy" "{name}"')
    if "count        = var.reconcile_job ? 1 : 0" in b:
        continue
    disp = re.search(r'display_name = "([^"]+)"', b).group(1)
    flt = re.search(r'\n      filter\s+= "(.*)"\n', b).group(1).replace('\\"', '"')
    flt = flt.replace("${google_pubsub_subscription.ingest_dlq_sub.name}", "ingest-dlq-sub")
    for svc in (["documind-slm", "documind-vllm"] if "for_each" in b else [None]):
        d, f = (disp.replace("${each.key}", svc), flt.replace("${each.key}", svc)) if svc else (disp, flt)
        th = re.search(r"threshold_value\s+= ([\d.]+)", b).group(1)
        POLICIES.append({"name": f"projects/{PROJ}/alertPolicies/{len(POLICIES) + 1}", "displayName": d, "enabled": True, "resource": name,
                         "conditions": [{"conditionThreshold": {"filter": f, "comparison": "COMPARISON_GT",
                                                                **({"thresholdValue": float(th)} if float(th) else {}),
                                                                "duration": re.search(r'duration\s+= "(\w+)"', b).group(1)}}]})
assert [p["resource"] for p in POLICIES] == ["api_latency", "unanswerable_rate", "gpu_left_warm", "gpu_left_warm", "ingest_failed", "dlq_depth"], POLICIES
LANE_POLICIES = [p for p in POLICIES if p["resource"] != "dlq_depth"]     # a lane made up before this kit version
assert not any("ingest-dlq-sub" in p["conditions"][0]["conditionThreshold"]["filter"] for p in LANE_POLICIES)
assert 'resource "google_pubsub_subscription" "ingest_dlq_sub" {\n  name  = "ingest-dlq-sub"' in src["terraform/eventarc.tf"]
assert "max_delivery_attempts = 12" in src["terraform/eventarc.tf"]
INTENTS = re.findall(r"^    (\w+) = \"", src["terraform/quota.tf"].split("documind_alerts = {", 1)[1].split("\n  }", 1)[0], re.M)
DECLARED = [k for k in INTENTS if f'"google_monitoring_alert_policy" "{k}"' in src[ALERTS]]
assert INTENTS == ["unanswerable_rate", "dlq_depth", "guardrail_blocks", "cache_hit_low", "burn_rate"] and DECLARED == ["unanswerable_rate", "dlq_depth"]
ADMIN = src["services/admin/admin_dashboard.py"]
assert '("Cost", "12.6 - INR per tenant per day, from tenant_daily"),' in ADMIN and "cost_inr" not in ADMIN
assert "col3.metric(\"p95 latency\", f\"{df['p95_ms'].median():.0f} ms\")" in ADMIN
assert re.search(r'logger\.info\(json\.dumps\(\{"event": "chat", "surface": "chat", "brain": name,', src["services/chat/agent.py"])
CHAT_SRC = src["services/chat/agent.py"].split('{"event": "chat"', 1)[1].split("}))", 1)[0]
assert '"cost_usd": used["cost_usd"]' in CHAT_SRC and '"model_calls": used["model_calls"]' in CHAT_SRC   # the turn's own model calls, priced
CHAT_KEYS = re.findall(r'"(\w+)": ', '{"event": "chat"' + CHAT_SRC)                                     # the row's fields, in its order
assert '"event": "media", "surface": "media"' in src["services/rag-api/media.py"] and "IMAGE_USD = 0.039" in src["services/rag-api/media.py"]
assert 'default_table_expiration_ms = 7776000000 # 90 days for raw logs' in src[SINK] and "partition_expiration" not in src[SINK]
assert "bq --project_id=$(PROJECT) query --use_legacy_sql=false < terraform/sql/tenant_daily.sql" in src["Makefile"]
GOLDEN = {r["id"]: r for r in (json.loads(line) for line in (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip())}
QUESTIONS = [(t, GOLDEN[i]["question"]) for t, i in ASKS]
assert all(GOLDEN[i]["tenant"] == t for t, i in ASKS) and not GOLDEN["rf-01"]["answerable"]

# ------------------------------------------------------------------ the cells
READERS_PY = """import re
def between(text, start, end):
    return text.split(start, 1)[1].split(end, 1)[0]
sink = between(open("terraform/sink.tf", encoding="utf-8").read(), "filter", "EOT\\n  unique")
view = open("terraform/sql/tenant_daily.sql", encoding="utf-8").read()
tool = open("evals/usage_rows.py", encoding="utf-8").read()
alerts = open("terraform/alerts.tf", encoding="utf-8").read()
desk_view = open("terraform/sql/desk_daily.sql", encoding="utf-8").read()
desk_alerts = open("terraform/desk_alerts.tf", encoding="utf-8").read()
queries = between(alerts, 'name    = "documind/queries"', "EOT\\n  metric")
readers = [
    ("the sink, into BigQuery", list(dict.fromkeys(re.findall(r'service_name = "([\\w-]+)"', sink))), re.findall(r'event = "(\\w+)"', sink),
     "every row, as it is written"),
    ("tenant_daily, the view", ["what the sink copied"], re.findall(r'"(\\w+)"', between(view, "WHERE jsonPayload.event IN (", ")")),
     "one row per India day and " + str(len(between(view, "GROUP BY day,", ";").split(","))) + " dimensions"),
    ("make usage", [re.search(r'"--service", default="([\\w-]+)"', tool).group(1)], re.findall(r'event="(\\w+)"', between(tool, "def read_rows", "def p95")),
     "the last N hours (default " + re.search(r'"--hours", type=int, default=(\\d+)', tool).group(1) + "), at most "
     + re.search(r"limit: int = (\\d+)", tool).group(1) + " rows"),
    ("documind/queries, for alerts", re.findall(r'service_name="([\\w-]+)"', queries), re.findall(r'event="(\\w+)"', queries), "counted as written"),
]
print(f"{'reader':30} {'services':28} window")
for name, services, events, when in readers:
    print(f"{name:30} {', '.join(services):28} {when}")
    print(f"{'':30} events: {', '.join(events)}")
    for ev, cond in re.findall(r'\\(jsonPayload\\.event = "(\\w+)" AND ([^)]+)\\)', sink) if name.startswith("the sink") else ():
        print(f"{'':30} {ev} only where {cond}")
inr = re.search(r"\\* (\\d+), 2\\) AS cost_inr", view).group(1)
usd_inr = re.search(r"USD_INR = (\\d+)", tool).group(1)
print(f"rupees: tenant_daily's cost_inr is cost_usd x {inr}; make usage's USD_INR is {usd_inr}")
events = {name: set(e) for name, _, e, _ in readers}
for ev in sorted(set().union(*events.values())):
    print(f"  {ev:11} read by: " + ", ".join(n for n, _, e, _ in readers if ev in e))
print("the Desk's own view, desk_daily (make desk-views), reads: " + ", ".join(re.findall(r'jsonPayload\\.event = "(\\w+)"', desk_view)))
policies = re.findall(r'resource "google_monitoring_alert_policy" "(\\w+)"', alerts)
print(f"alert policies in terraform/alerts.tf: {len(policies)} - " + ", ".join(policies))
desk_policies = re.findall(r'resource "google_monitoring_alert_policy" "(\\w+)" \\{\\n(?:  count += var\\.(\\w+) \\? 1 : 0\\n)?', desk_alerts)
switches = list(dict.fromkeys(s for _, s in desk_policies if s))
mark = {s: "*" * (i + 1) for i, s in enumerate(switches)}
print(f"alert policies in terraform/desk_alerts.tf: {len(desk_policies)} - " + ", ".join(n + mark.get(s, "") for n, s in desk_policies)
      + " (" + ", ".join(f"{mark[s]} only on a lane planned with {s.upper()}=true" for s in switches) + ")")
print("the one that reads the dead-letter queue: " + ", ".join(p for p in policies
      if "ingest_dlq_sub" in between(alerts, f'"google_monitoring_alert_policy" "{p}"', "\\n}\\n")))"""

ASK_PY = """import json, os, subprocess, urllib.request
P, API = os.environ["PROJECT"], os.environ["API"]
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                     capture_output=True, text=True, check=True).stdout.strip()
ASKS = %s
for tenant, question in ASKS:
    body = json.dumps({"query": question, "tenant_id": tenant}).encode()
    req = urllib.request.Request(API + "/v1/query", data=body, headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    a = json.load(urllib.request.urlopen(req, timeout=120))
    print(f"  {tenant:5} {'answered' if a['answerable'] else 'refused':8} {a['tokens_in']:>5} in {a['tokens_out']:>3} out  "
          f"cost_usd {a['cost_usd']}  {question}")""" % repr(QUESTIONS)

RECON_PY = """import datetime as dt, json, os, subprocess, sys
sys.path.insert(0, "evals")
from usage_rows import USD_INR, group                       # make usage's own GROUP BY, and its rate
P = os.environ["PROJECT"]
KEYS = ("tenant", "surface", "model_backend", "prompt_version", "retrieval_mode", "retrieval_backend", "modality")   # the view's, less the day
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
midnight = dt.datetime.now(IST).replace(hour=0, minute=0, second=0, microsecond=0)
since = midnight.astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
flt = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND '
       f'(jsonPayload.event="query" OR jsonPayload.event="stream" OR jsonPayload.event="media") AND timestamp>="{since}"')
log = subprocess.run(["gcloud", "logging", "read", flt, "--project", P, "--limit", "5000", "--format=json"],
                     capture_output=True, text=True, check=True).stdout
rows = [e["jsonPayload"] for e in json.loads(log or "[]")]
tool = {tuple(str(g[k]) for k in KEYS): g for g in group(rows, KEYS)}
sql = "SELECT * EXCEPT(day) FROM `documind_observability.tenant_daily` WHERE day = CURRENT_DATE('Asia/Kolkata')"
out = subprocess.run(["bq", "--project_id", P, "query", "--use_legacy_sql=false", "--format=json", "--max_rows=1000", sql],
                     capture_output=True, text=True, check=True).stdout
view = {tuple(str(r[k]) for k in KEYS): r for r in json.loads(out or "[]")}
print(f"today since 00:00 IST: {len(rows)} usage rows in Cloud Logging, {len(view)} tenant_daily rows")
print(f"  {'group (the view GROUP BY)':42} {'answers':>9} {'refused':>7} {'tokens in':>11} {'Rs':>11}")
agree, totals = True, {}
for k in sorted(set(tool) | set(view)):
    t, v = tool.get(k), view.get(k)
    tv = (t["answers"], round(t["unanswerable_rate"] * t["answers"]), t["tokens_in"], t["tokens_out"], t["inr"]) if t else None
    vv = (int(v["queries"]), int(v["unanswerable"]), int(v["tokens_in"]), int(v["tokens_out"]), float(v["cost_inr"])) if v else None
    same = tv is not None and vv is not None and tv[:4] == vv[:4] and abs(tv[4] - vv[4]) < 0.005
    agree &= same
    for side, x in (("view", vv), ("tool", tv)):
        totals.setdefault(k[0], {"view": 0.0, "tool": 0.0})[side] += x[4] if x else 0.0
    cell = lambda a, b: f"{a}/{b}"
    print(f"  {' '.join(k)[:42]:42} {cell(vv and vv[0], tv and tv[0]):>9} {cell(vv and vv[1], tv and tv[1]):>7} "
          f"{cell(vv and vv[2], tv and tv[2]):>11} {cell(vv and vv[4], tv and tv[4]):>11}  {'equal' if same else 'DIFFERENT'}")
print("  (each pair is tenant_daily/make usage's grouping; p95 is left out: the view's APPROX_QUANTILES is not the tool's nearest rank)")
for tenant, s in sorted(totals.items()):
    print(f"{tenant}: tenant_daily Rs {s['view']:.2f}, make usage's grouping Rs {s['tool']:.2f} - " + ("equal" if abs(s['view'] - s['tool']) < 0.005 else "DIFFERENT"))
media = [r for r in rows if r.get("event") == "media"]
print(f"media rows today: {len(media)}" + (f" (Rs {sum(r['cost_usd'] for r in media) * USD_INR:.2f}) - make usage counts them, the sink never copies them" if media else ""))
print("RECONCILED: every group equal in answers, refusals, tokens and rupees" if agree else "NOT RECONCILED: read the DIFFERENT rows")"""

ALERTS_PY = """import json, os, re, subprocess, urllib.request
P = os.environ["PROJECT"]
def gcloud(*a):
    return subprocess.run(["gcloud", *a], capture_output=True, text=True, check=True).stdout
tok = gcloud("auth", "print-access-token").strip()
req = urllib.request.Request(f"https://monitoring.googleapis.com/v3/projects/{P}/alertPolicies", headers={"Authorization": "Bearer " + tok})
policies = json.load(urllib.request.urlopen(req, timeout=60)).get("alertPolicies", [])
metrics = json.loads(gcloud("logging", "metrics", "list", "--project", P, "--format=json"))
print("log-based metrics on the lane: " + ", ".join(sorted(m["name"] for m in metrics)))
print(f"alert policies on the lane: {len(policies)}, and what each one reads")
dlq = []
for p in sorted(policies, key=lambda p: p["displayName"]):
    for c in p.get("conditions", []):
        f = (c.get("conditionThreshold") or {}).get("filter", "")
        metric = re.search(r'metric\\.type="([^"]+)"', f)
        on = re.search(r'(?:service_name|subscription_id)="([^"]+)"', f)
        print(f"  {p['displayName'][:52]:52} {metric.group(1).rsplit('/', 1)[-1] if metric else '?'} on {on.group(1) if on else 'any service'}")
        if "ingest-dlq-sub" in f:
            dlq.append(p["displayName"])
print("reads the dead-letter queue (ingest-dlq-sub): " + (", ".join(dlq) or "NOTHING - an upload the worker refused twelve times pages nobody"))"""

GAUGE_PY = """import datetime as dt, json, os, subprocess, urllib.parse, urllib.request
P = os.environ["PROJECT"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
def monitoring(path, **query):
    url = f"https://monitoring.googleapis.com/v3/projects/{P}/{path}" + ("?" + urllib.parse.urlencode(query) if query else "")
    return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": "Bearer " + tok}), timeout=60))
end = dt.datetime.now(dt.timezone.utc).replace(microsecond=0)
stamp = lambda t: t.isoformat().replace("+00:00", "Z")
series = monitoring("timeSeries", filter='metric.type="pubsub.googleapis.com/subscription/num_undelivered_messages" '
                                          'AND resource.labels.subscription_id="ingest-dlq-sub"',
                    **{"interval.startTime": stamp(end - dt.timedelta(minutes=10)), "interval.endTime": stamp(end)})
IST = dt.timezone(dt.timedelta(hours=5, minutes=30))
points = sorted((dt.datetime.fromisoformat(p["interval"]["endTime"].replace("Z", "+00:00")).astimezone(IST), int(p["value"]["int64Value"]))
                for s in series.get("timeSeries", []) for p in s["points"])
print("ingest-dlq-sub, undelivered messages - the gauge the policy reads, a sample a minute:")
print("  " + "  ".join(f"{t:%H:%M} {n}" for t, n in points))
for p in monitoring("alertPolicies").get("alertPolicies", []):
    th = p["conditions"][0].get("conditionThreshold", {})
    if "ingest-dlq-sub" in th.get("filter", ""):
        print(f"policy: {p['displayName']} - above {th.get('thresholdValue', 0)} for {th['duration']}, "
              f"{len(p.get('notificationChannels', []))} notification channel(s)")
above = [t for t, n in points if n > 0]
print(f"above zero since {above[0]:%H:%M} IST: the condition holds - Monitoring > Alerting shows the incident" if above
      else "not above zero yet: Pub/Sub's sample can take two minutes to appear; run this again")"""

DRAIN_PY = """import json, os, subprocess
P = os.environ["PROJECT"]
def gcloud(*a):
    return subprocess.run(["gcloud", *a], capture_output=True, text=True, check=True).stdout
pulled = json.loads(gcloud("pubsub", "subscriptions", "pull", "ingest-dlq-sub", "--project", P, "--limit", "10", "--format=json") or "[]")
drill = [m["ackId"] for m in pulled if (m["message"].get("attributes") or {}).get("drill") == "13.2"]
if drill:
    gcloud("pubsub", "subscriptions", "ack", "ingest-dlq-sub", "--project", P, "--ack-ids=" + ",".join(drill))
print(f"pulled {len(pulled)}; acknowledged {len(drill)} drill message(s); {len(pulled) - len(drill)} other(s) left for make dlq")"""


def heredoc(body: str, prefix: str = "") -> str:
    return f"{prefix}python - <<'PY'\n{body}\nPY"


CELLS = {
    "readers": heredoc(READERS_PY),
    "ask": heredoc(ASK_PY) + "\nsleep 20      # Cloud Logging needs a moment to show the rows\nmake usage PROJECT=\"$PROJECT\" HOURS=1",
    "recon": heredoc(RECON_PY),
    "alerts": heredoc(ALERTS_PY),
    "plan": ('make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"   # the flags you gave make up; the plan refuses to delete\n'
             'python commands/infrastructure.py apply --project "$PROJECT" --region "$REGION" --terraform-dir terraform   # make up\'s first line, alone'),
    "drill": ('gcloud pubsub topics publish documind-ingest-dlq --project "$PROJECT" --message="drill 13.2: not an upload" --attribute=drill=13.2\n'
              "sleep 300     # a sample a minute, shown up to two minutes late, and the policy wants a minute above zero\n" + heredoc(GAUGE_PY)),
    "drain": heredoc(DRAIN_PY),
}

T = Path(tempfile.mkdtemp(prefix="lesson132-"))
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ,
       "REGION": "asia-south1", "GOOGLE_CLOUD_PROJECT": PROJ, "USERPROFILE": str(T), "HOME": str(T)}
for k in [k for k in ENV if k.startswith(("RETRIEVAL_", "TOP_K", "RERANK_", "SEMANTIC_", "VECTOR_", "GENERATOR_", "ARMOR", "ROUTING"))]:
    ENV.pop(k)


def run_cell(body: str, prelude: str = "", env: dict | None = None, cwd: Path = T) -> str:
    r = subprocess.run([sys.executable, "-"], input=prelude + body, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-2500:])
    return r.stdout


# ---- step 3: the readers as the kit writes them down
OUT = {"readers": run_cell(READERS_PY, cwd=KIT)}
R3 = OUT["readers"]
assert ("the sink, into BigQuery        documind-api, documind-chat  every row, as it is written\n"
        "                               events: query, stream, chat, desk, passages, desk_shadow, desk_gate\n"
        "                               desk_shadow only where NOT jsonPayload.case_type = \"sensitive\"\n"
        "                               desk_gate only where resource.labels.service_name = \"documind-chat\"\n") in R3, R3
assert "  media       read by: tenant_daily, the view, make usage\n" in R3 and "  chat        read by: the sink, into BigQuery\n" in R3, R3
assert all(f"  {ev:11} read by: the sink, into BigQuery\n" in R3 for ev in DESK_EVENTS), R3
assert "the Desk's own view, desk_daily (make desk-views), reads: desk\n" in R3, R3
DESK_ALERTS_TF = (KIT / "terraform/desk_alerts.tf").read_text(encoding="utf-8")
DESK_POLICIES = re.findall(r'resource "google_monitoring_alert_policy" "(\w+)"', DESK_ALERTS_TF)
ROUTER_POLICIES = re.findall(r'resource "google_monitoring_alert_policy" "(\w+)" \{\n  count        = var\.desk_router_alerts \? 1 : 0\n', DESK_ALERTS_TF)
GATE_POLICIES = re.findall(r'resource "google_monitoring_alert_policy" "(\w+)" \{\n  count        = var\.desk_gate_alerts \? 1 : 0\n', DESK_ALERTS_TF)
assert DESK_POLICIES == ["desk_fallback_share", "desk_l2_share", "desk_clarify_oos_trend", "case_overdue", "doc_type_pin_miss",
                         "desk_delegation_refused", "desk_gate_error_share", "desk_check_tenants_unread"], DESK_POLICIES
assert ROUTER_POLICIES == DESK_POLICIES[:3] and GATE_POLICIES == ["desk_gate_error_share"], (ROUTER_POLICIES, GATE_POLICIES)
assert len(re.findall(r"^  count +=", DESK_ALERTS_TF, re.M)) == len(ROUTER_POLICIES) + len(GATE_POLICIES)   # no other switch
assert ("alert policies in terraform/desk_alerts.tf: 8 - desk_fallback_share*, desk_l2_share*, desk_clarify_oos_trend*, case_overdue, "
        "doc_type_pin_miss, desk_delegation_refused, desk_gate_error_share**, desk_check_tenants_unread "
        "(* only on a lane planned with DESK_ROUTER_ALERTS=true, ** only on a lane planned with DESK_GATE_ALERTS=true)\n") in R3, R3
assert "one row per India day and 7 dimensions" in R3 and "at most 2000 rows" in R3, R3
assert R3.rstrip().endswith("the one that reads the dead-letter queue: dlq_depth"), R3

# ---- the stand-in lane, a module every process below imports as lane132
LANE_LIB = r'''"""The stand-in lane for lesson 11.5's build. rag-api's usage rows are the kit's own: its query() runs on top of a
Firestore held in JSON files (acme's and zeta's handbooks, cut by the kit's chunker), with the index, the Ranking API
and Gemini stood in. What reads those rows afterwards is stood in too, from the lane's state: Cloud Logging (a store of
timestamped entries, filtered the way the cells filter it), BigQuery (tenant_daily's arithmetic over the rows the sink
exports, with the sink's and the view's filters as the build parsed them from the kit), Pub/Sub, Cloud Monitoring and
gcloud itself."""
import base64
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
import uuid
from decimal import ROUND_HALF_UP, Decimal
from types import SimpleNamespace

KIT = os.environ["LANE132_KIT"]
with open(os.environ["LANE132_CORPUS"], encoding="utf-8") as _f:
    CORPUS = json.load(_f)
STATE_PATH = os.environ["LANE132_STATE"]
LAST = {"q": ""}                                   # the question embed_query was last given


def state() -> dict:
    with open(STATE_PATH, encoding="utf-8") as f:
        return json.load(f)


def save(st: dict) -> None:
    with open(STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f)


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


# ---- Firestore: the chunk rows (every one current) and the few documents query() reads
MEM: dict = collections.defaultdict(dict)


def rows(coll: str) -> dict:
    base = {k: dict(v) for k, v in (CORPUS["rows"].items() if coll == "chunks" else state().get(coll, {}).items())}
    for k, v in MEM[coll].items():
        base[k] = dict(v)
    for d in base.values():
        for k in ("indexed_at", "expire_at", "created_at"):
            if isinstance(d.get(k), str):
                d[k] = dt.datetime.fromisoformat(d[k])
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
        MEM[self.coll][self.id] = {**(MEM[self.coll].get(self.id, {}) if merge else {}), **data}


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
    """find_nearest, exact: every row the predicates keep, ordered by the stand-in similarity to the question."""
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


# Gemini, stood in by a reader: a question it knows is answered from the packed clause that states it, cited; any other
# question is refused, as the prompt's rule 3 asks when the context does not hold the answer.
RULES = [(("notice period", "E3"), r"serves a notice period of (\d+) days",
          "A confirmed employee at grade E3 or above serves a notice period of {0} days [{n}].", "serves a notice period of {0} days"),
         (("travel", "cap"), r"capped at Rs ([\d,]+) per trip",
          "Domestic travel is reimbursed against original receipts, capped at Rs {0} per trip [{n}].", "capped at Rs {0} per trip")]


def _reply(prompt: str):
    question = prompt.rsplit("\n\nQuestion:", 1)[1].strip()
    ctx = prompt.split("\nContext:\n", 1)[1].rsplit("\n\nQuestion:", 1)[0]
    parts = re.split(r"(?m)^\[Source (\d+)\] ?(.*)$", ctx)
    draft = {"answer": "The context does not say; it holds nothing on this question.", "citations": [],
             "confidence": "low", "answerable": False}
    for words, pattern, answer, quote in RULES:
        if all(w.lower() in question.lower() for w in words):
            for k in range(1, len(parts) - 2, 3):
                m = re.search(pattern, parts[k + 2])
                if m:
                    n = int(parts[k])
                    draft = {"answer": answer.format(m.group(1), n=n), "citations": [{"source": n, "quote": quote.format(m.group(1))}],
                             "confidence": "high", "answerable": True}
                    break
            break
    usage = SimpleNamespace(prompt_token_count=len(prompt) // 4, candidates_token_count=len(draft["answer"]) // 4 + 24,
                            thoughts_token_count=0, cached_content_token_count=0)
    return SimpleNamespace(parsed=draft, text=json.dumps(draft), usage_metadata=usage,
                           candidates=[SimpleNamespace(finish_reason=SimpleNamespace(name="STOP"))], prompt_feedback=None)


class Models:
    def generate_content(self, model, contents, config=None):
        return _reply(contents[0] if isinstance(contents, list) else contents)


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
    """rag-api's modules, imported from the kit and wired to the stand-ins above."""
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
    main.record = lambda db, usd: None                         # the month's budget counter is 11.6's

    def caches():
        m = object.__new__(cache_manager.TenantCacheManager)
        m.db, m.global_client, m.regional_client = DB, GenaiClient(), GenaiClient()
        return m
    generator._caches = caches
    return main


def serve(port: int, who: dict) -> None:
    """The kit's app on localhost, behind a stand-in of Cloud Run's IAM check."""
    main = rag()
    import shared.iap as iap

    def identity(headers, bearer_audience=None):
        tok = headers.get("authorization", "").removeprefix("Bearer ")
        if tok not in who:
            raise iap.IapError("the bearer token carries no verified email")
        return {"email": who[tok], "via": "iam", "aud": bearer_audience}
    iap.identity = identity

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


# ---- what reads the rows: Cloud Logging, the sink and tenant_daily, Pub/Sub, Monitoring
def entries() -> list:
    with open(os.environ["LANE132_LOGSTORE"], encoding="utf-8") as f:
        return json.load(f)


def _read_log(flt: str, limit: int) -> list:
    """gcloud logging read, for the filters the cells and the kit write: one service, a set of events, a start time."""
    svc = re.search(r'resource\.labels\.service_name="([\w-]+)"', flt)
    events = set(re.findall(r'jsonPayload\.event="(\w+)"', flt))
    since = re.search(r'timestamp>="([^"]+)"', flt)
    out = [e for e in entries() if (not svc or e["resource"]["labels"]["service_name"] == svc.group(1))
           and (not events or e["jsonPayload"].get("event") in events) and (not since or e["timestamp"] >= since.group(1))]
    return sorted(out, key=lambda e: e["timestamp"], reverse=True)[:limit]      # newest first, as gcloud reads


IST = dt.timezone(dt.timedelta(hours=5, minutes=30))


def _round(x: float, n: int) -> float:                  # BigQuery's ROUND: halves away from zero
    return float(Decimal(repr(x)).quantize(Decimal(1).scaleb(-n), rounding=ROUND_HALF_UP))


def tenant_daily() -> list:
    """The view, over the sink's table: the rows the sink exports, the view's WHERE, its GROUP BY and its sums."""
    v = state()["view"]
    table = [e for e in entries() if e["resource"]["labels"]["service_name"] in v["sink_services"]
             and e["jsonPayload"].get("event") in v["sink_events"]]
    groups: dict = collections.OrderedDict()
    for e in sorted(table, key=lambda e: e["timestamp"]):
        j = e["jsonPayload"]
        if j.get("event") not in v["view_events"]:
            continue
        day = dt.datetime.fromisoformat(e["timestamp"].replace("Z", "+00:00")).astimezone(IST).date().isoformat()
        key = (day,) + tuple(j.get(k) for k in v["keys"])
        g = groups.setdefault(key, {"queries": 0, "unanswerable": 0, "tokens_in": 0, "tokens_out": 0, "usd": 0.0})
        g["queries"] += 1
        g["unanswerable"] += j.get("answerable") is False
        g["tokens_in"] += int(j.get("tokens_in") or 0)
        g["tokens_out"] += int(j.get("tokens_out") or 0)
        g["usd"] += float(j.get("cost_usd") or 0.0)
    out = []
    for key, g in groups.items():
        out.append({"day": key[0], **dict(zip(v["keys"], key[1:])), "queries": g["queries"], "unanswerable": g["unanswerable"],
                    "tokens_in": g["tokens_in"], "tokens_out": g["tokens_out"], "cost_usd": _round(g["usd"], 4),
                    "cost_inr": _round(g["usd"] * v["rate"], 2)})
    return out


def _bq(cmd: list) -> str:
    sql = cmd[-1]
    rows = tenant_daily()
    today = re.search(r"CURRENT_DATE\('Asia/Kolkata'\)", sql)
    if today:
        rows = [r for r in rows if r["day"] == state()["today"]]
    if "EXCEPT(day)" in sql:
        rows = [{k: v for k, v in r.items() if k != "day"} for r in rows]
    return json.dumps([{k: (None if v is None else str(v)) for k, v in r.items()} for r in rows])   # bq prints every value as a string


def _monitoring(url: str) -> dict:
    st, path = state(), urllib.parse.urlparse(url)
    if path.path.endswith("/alertPolicies"):
        return {"alertPolicies": st["policies"]}
    if path.path.endswith("/timeSeries"):
        q = urllib.parse.parse_qs(path.query)
        assert "ingest-dlq-sub" in q["filter"][0] and "num_undelivered_messages" in q["filter"][0], q
        return {"timeSeries": [{"resource": {"type": "pubsub_subscription", "labels": {"subscription_id": "ingest-dlq-sub"}},
                                "metricKind": "GAUGE", "valueType": "INT64",
                                "points": [{"interval": {"startTime": t, "endTime": t}, "value": {"int64Value": str(n)}}
                                           for t, n in reversed(st["dlq_gauge"])]}]}
    raise SystemExit(f"the stand-in Monitoring API has no answer for {path.path}")


def _gcloud(cmd: list) -> str:
    st = state()
    if cmd[:3] == ["gcloud", "auth", "print-identity-token"]:
        return "MEMBER\n"
    if cmd[:3] == ["gcloud", "auth", "print-access-token"]:
        return "ACCESS\n"
    if cmd[:3] == ["gcloud", "logging", "read"]:
        limit = int(cmd[cmd.index("--limit") + 1]) if "--limit" in cmd else 1000
        return json.dumps(_read_log(cmd[3], limit))
    if cmd[:4] == ["gcloud", "logging", "metrics", "list"]:
        return json.dumps(st["metrics"])
    if cmd[:4] == ["gcloud", "pubsub", "topics", "publish"]:
        attrs = dict(a.split("=", 1) for c in cmd if c.startswith("--attribute=") for a in c.split("=", 1)[1].split(","))
        data = next(c.split("=", 1)[1] for c in cmd if c.startswith("--message="))
        mid = st["next_message_id"]
        st["dlq"].append({"ackId": f"ACK-{mid}", "message": {"attributes": attrs, "data": base64.b64encode(data.encode()).decode(),
                                                               "messageId": mid, "publishTime": st["publish_time"]}})
        st["next_message_id"] = str(int(mid) + 1)
        save(st)
        return f"messageIds:\n- '{mid}'\n"
    if cmd[:4] == ["gcloud", "pubsub", "subscriptions", "pull"]:
        return json.dumps(st["dlq"])
    if cmd[:4] == ["gcloud", "pubsub", "subscriptions", "ack"]:
        ids = set(next(c.split("=", 1)[1] for c in cmd if c.startswith("--ack-ids=")).split(","))
        st["dlq"] = [m for m in st["dlq"] if m["ackId"] not in ids]
        save(st)
        return ""
    raise SystemExit(f"the stand-in gcloud has no answer for {cmd[:4]}")


def fake_cli() -> None:
    """gcloud, bq and the Monitoring API answer from the lane's state; the rest of subprocess and urllib stays."""
    real_run, real_open = subprocess.run, urllib.request.urlopen

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and cmd and cmd[0] in ("gcloud", "bq"):
            out = _bq(list(cmd)) if cmd[0] == "bq" else _gcloud(list(cmd))
            return subprocess.CompletedProcess(list(cmd), 0, out, "")
        return real_run(cmd, *a, **kw)

    def urlopen(req, *a, **kw):
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        if url.startswith("https://monitoring.googleapis.com/"):
            return io.BytesIO(json.dumps(_monitoring(url)).encode())
        return real_open(req, *a, **kw)
    subprocess.run, urllib.request.urlopen = run, urlopen
'''

# ---- the stand-in lane: acme's and zeta's handbooks, as the kit's chunker cuts them, with the worker's chunk ids
sys.path.insert(0, str(KIT))
from hashlib import sha256  # noqa: E402
from shared.documind_corpus import chunk_document  # noqa: E402
ROWS = {}
for tenant, rel in (("acme", "evals/corpus/acme/hr_policy_2026.md"), ("zeta", "evals/corpus/zeta/hr_policy_zeta_2026.md")):
    data = (KIT / rel).read_bytes()
    sha, uri = sha256(data).hexdigest(), f"gs://{PROJ}-uploads/{tenant}/{Path(rel).name}"
    for i, c in enumerate(chunk_document({"text": data.decode("utf-8"), "source_uri": uri, "doc_type": "unknown", "slug": Path(rel).stem}, tenant)):
        ROWS[f"{tenant}:{sha}#{i}"] = {"tenant_id": tenant, "text": c["text"], "source_uri": uri, "page_start": None, "doc_type": "unknown",
                                       "kind": "text", "doc_key": f"{tenant}_{sha}", "chunk_hash": c["chunk_hash"], "locator": c["locator"],
                                       "current": True, "indexed_at": "2026-09-10T09:14:02+00:00", **({"section": c["section"]} if c.get("section") else {})}
(T / "corpus132.json").write_text(json.dumps({"rows": ROWS}), encoding="utf-8")
(T / "lane132.py").write_text(LANE_LIB, encoding="utf-8")
STATE, LOGSTORE = T / "state132.json", T / "logstore132.json"
SERVICE_ENV = {"GOOGLE_CLOUD_PROJECT": PROJ, "RETRIEVAL_BACKEND": "firestore", "VECTOR_INDEX_ENDPOINT": "projects/NUMBER/locations/asia-south1/indexEndpoints/9876543210987654321",
               "VECTOR_DEPLOYED_INDEX_ID": "documind_chunks_v1", "GENERATOR_MODEL": "gemini-3.6-flash", "RETRIEVAL_CURRENT_ONLY": "off",
               "SEMANTIC_CACHE": "off", "GIT_SHA": "COMMIT", "SELF_URL": "https://documind-api-NUMBER.asia-south1.run.app"}
LANE_ENV = {"LANE132_KIT": str(KIT), "LANE132_CORPUS": str(T / "corpus132.json"), "LANE132_STATE": str(STATE),
            "LANE132_LOGSTORE": str(LOGSTORE), "PYTHONPATH": str(T)}
TODAY, NOW = "2026-09-24", "2026-09-24T05:52:00+00:00"                       # 11:22 IST, the frozen clock
STATE_0 = {"tenant_settings": {"acme": {"retrieval_backend": "vector"}}, "today": TODAY,
           "view": {"sink_services": SINK_SERVICES, "sink_events": SINK_EVENTS, "view_events": VIEW_EVENTS, "keys": VIEW_KEYS, "rate": 85},
           "metrics": [{"name": n, "filter": f.strip()} for n, f in METRICS.items()], "policies": LANE_POLICIES,
           "dlq": [], "next_message_id": "17405836920431227", "publish_time": "2026-09-24T06:02:41.518Z", "dlq_gauge": []}
STATE.write_text(json.dumps(STATE_0), encoding="utf-8")
FREEZE = ("import datetime as _d\n"
          f"_NOW = _d.datetime.fromisoformat({NOW!r})\n"
          "class _Frozen(_d.datetime):\n"
          "    @classmethod\n"
          "    def now(cls, tz=None):\n"
          "        return _NOW.astimezone(tz) if tz else _NOW.replace(tzinfo=None)\n"
          "_d.datetime = _Frozen\n")
PRELUDE = FREEZE + "import lane132\nlane132.stubs()\nlane132.fake_cli()\n"

# ---- steps 4 and 5: the kit's app on localhost, four questions, their rows timed into a Cloud Logging stand-in
with socket.socket() as s:
    assert s.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} is taken on this machine"
LOG = T / "api132.log"
URL = f"http://127.0.0.1:{PORT}"
with open(LOG, "w", encoding="utf-8") as logf:
    srv = subprocess.Popen([sys.executable, "-c", f"import lane132; lane132.serve({PORT}, {{'MEMBER': {UI_SA!r}}})"],
                           cwd=str(T), env={**ENV, **LANE_ENV, **SERVICE_ENV}, stdout=logf, stderr=subprocess.STDOUT)
CELL_ENV = {**LANE_ENV, "API": URL}
try:
    for _ in range(150):
        try:
            urllib.request.urlopen(urllib.request.Request(URL + "/health", headers={"Authorization": "Bearer MEMBER"}), timeout=1).read()
            break
        except Exception:                          # noqa: BLE001 - not up yet
            time.sleep(0.2)
    else:
        raise SystemExit("the API did not start: " + LOG.read_text(encoding="utf-8")[-1500:])
    LOGSTORE.write_text("[]", encoding="utf-8")
    before = len(LOG.read_text(encoding="utf-8"))
    OUT["ask"] = run_cell(ASK_PY, PRELUDE, env=CELL_ENV)
    time.sleep(0.5)
    ROWS_TODAY = [json.loads(line) for line in LOG.read_text(encoding="utf-8")[before:].splitlines() if line.startswith('{"event": "query"')]
    # The stand-in answers in milliseconds and its clocks move from build to build: the rows keep every field the kit wrote,
    # with the four clocks set to a lane's typical values (the Firestore rung's retrieval slower than the index's), so the
    # page is the same on every build and its p95 columns read like a lane's.
    for r, (ret, rer, gen) in zip(ROWS_TODAY, [(236, 142, 1874), (221, 138, 1790), (248, 151, 1602), (412, 147, 1851)]):
        r.update(retrieve_ms=ret, rerank_ms=rer, generate_ms=gen, latency_ms=ret + rer + gen + 96)
    # the widget's eight rows: the kit's own builders, in a process of their own
    WIDGET_PY = f"""import json
import lane132
main = lane132.rag()
import media
from schemas import QueryRequest
real = json.loads({json.dumps(ROWS_TODAY)!r})
user = {{"email": {UI_SA!r}}}
z, a = real[3], real[0]
stages = {{k: z[k] for k in ("retrieve_ms", "rerank_ms", "generate_ms", "pool", "graph_chunks", "managed_chunks", "policy_fallback")}}
stream = main.usage_row(QueryRequest(query="x", tenant_id="zeta"), user, z["tokens_in"], z["tokens_out"], 0, z["latency_ms"], True, "medium",
                        "stream", model=z["model"], backend="vertex", stages=stages, retrieval_backend=z["retrieval_backend"])
chain = main.usage_row(QueryRequest(query="x", tenant_id="acme", brain="langchain"), user, a["tokens_in"], a["tokens_out"], 0, a["latency_ms"], True,
                       "high", "query", model=a["model"], backend="vertex", stages=stages, retrieval_backend="vector")
image = media._usage("acme", user["email"], media.IMAGE_USD, False, 5210)
print(json.dumps({{"stream": stream, "chain": chain, "image": image}}))
"""
    BUILT = json.loads(run_cell(WIDGET_PY, env={**LANE_ENV, **SERVICE_ENV}).strip().splitlines()[-1])
finally:
    srv.terminate()
    srv.wait(timeout=20)

assert len(ROWS_TODAY) == 4 and [r["tenant"] for r in ROWS_TODAY] == ["acme", "acme", "acme", "zeta"], ROWS_TODAY
assert [r["answerable"] for r in ROWS_TODAY] == [True, True, False, True] and all(r["cost_usd"] > 0 for r in ROWS_TODAY)
assert [r["retrieval_backend"] for r in ROWS_TODAY] == ["vector", "vector", "vector", "firestore"]
A4 = OUT["ask"]
assert A4.count("cost_usd None") == 4 and "  acme  refused " in A4, A4                 # the answer carries tokens, never its price
sys.path.insert(0, str(KIT / "services/chat"))
import limits  # noqa: E402
METER = limits.Meter(model="gemini-3.6-flash")      # the turn's own two model calls, invented counts, priced as the chat service prices them
for i, (t_in, t_out) in enumerate(((1180, 28), (2410, 61))):
    assert METER.allow_model_call()
    METER.charge_model(t_in, t_out)
    if i == 0:
        METER.charge_rag({"cost_usd": BUILT["chain"]["cost_usd"]})
CHAT_ROW = {"event": "chat", "surface": "chat", "brain": "langchain", "tenant": "acme", "user": UI_SA, "session_id": "s-7f3a",
            "latency_ms": 6120, "tool_calls": ["retrieve"], "refusals": [], **METER.row()}
assert list(CHAT_ROW) == [k for k in CHAT_KEYS if k != "tenant_id"] and CHAT_ROW["cost_usd"] > 0, (list(CHAT_ROW), CHAT_KEYS)


def entry(ts: str, service: str, payload: dict) -> dict:
    return {"timestamp": ts, "resource": {"type": "cloud_run_revision", "labels": {"service_name": service}}, "jsonPayload": payload}


YESTERDAY = [entry("2026-09-23T05:11:07Z", "documind-api", ROWS_TODAY[1]), entry("2026-09-23T17:10:44Z", "documind-api", ROWS_TODAY[0])]
TODAYS = [entry(f"2026-09-24T05:4{i}:{12 + 9 * i}Z", "documind-api", r) for i, r in enumerate(ROWS_TODAY)]
TODAYS.append(entry("2026-09-24T04:35:31Z", "documind-chat", CHAT_ROW))       # a chat turn at 10:05 IST: exported, read by neither report
LOGSTORE.write_text(json.dumps(YESTERDAY + TODAYS), encoding="utf-8")
USAGE_PY = ("import runpy, sys\nsys.argv = ['usage_rows.py', '--project', %r, '--hours', '1']\n"
            "try:\n    runpy.run_path('evals/usage_rows.py', run_name='__main__')\nexcept SystemExit as e:\n    assert not e.code, e.code\n") % PROJ
OUT["ask"] += f"python evals/usage_rows.py --project {PROJ} --hours ${{HOURS:-24}}\n" + run_cell(USAGE_PY, PRELUDE, cwd=KIT, env=CELL_ENV)
OUT["recon"] = run_cell(RECON_PY, PRELUDE, cwd=KIT, env=CELL_ENV)
U4, R5 = OUT["ask"], OUT["recon"]
assert "4 answers from documind-api in the last 1 h; USD_INR=85" in U4, U4
assert "today since 00:00 IST: 4 usage rows in Cloud Logging, 2 tenant_daily rows" in R5, R5
assert R5.rstrip().endswith("RECONCILED: every group equal in answers, refusals, tokens and rupees") and R5.count("equal") >= 4, R5
TOTAL_INR = {t: round(sum(r["cost_usd"] for r in ROWS_TODAY if r["tenant"] == t) * 85, 2) for t in ("acme", "zeta")}
for t, inr in TOTAL_INR.items():
    assert f"{t}: tenant_daily Rs {inr:.2f}, make usage's grouping Rs {inr:.2f} - equal" in R5, (t, inr, R5)

# ---- step 6: the alerting on the lane, the plan, the drill and the drain - Pub/Sub and Monitoring stood in
OUT["alerts"] = run_cell(ALERTS_PY, PRELUDE, env=CELL_ENV)
A6 = OUT["alerts"]
assert "alert policies on the lane: 5, and what each one reads" in A6 and A6.rstrip().endswith("pages nobody"), A6
st = json.loads(STATE.read_text(encoding="utf-8"))
st["policies"] = [{**p, "notificationChannels": [f"projects/{PROJ}/notificationChannels/NUMBER"]} if p["resource"] == "dlq_depth" else p for p in POLICIES]
st["dlq_gauge"] = [(f"2026-09-24T06:{m:02d}:00Z", 0 if m < 3 else 1) for m in range(0, 8)]   # published at 11:32:41 IST
STATE.write_text(json.dumps(st), encoding="utf-8")
DRILL_PY = ("import subprocess\nprint(subprocess.run(['gcloud', 'pubsub', 'topics', 'publish', 'documind-ingest-dlq', '--project', %r, "
            "'--message=drill 13.2: not an upload', '--attribute=drill=13.2'], capture_output=True, text=True, check=True).stdout, end='')\n") % PROJ
FREEZE_DRILL = PRELUDE.replace(NOW, "2026-09-24T06:08:00+00:00")                # five minutes after the publish
OUT["drill"] = run_cell(DRILL_PY, FREEZE_DRILL, env=CELL_ENV) + run_cell(GAUGE_PY, FREEZE_DRILL, env=CELL_ENV)
OUT["drain"] = run_cell(DRAIN_PY, FREEZE_DRILL, env=CELL_ENV)
D6 = OUT["drill"]
assert D6.startswith("messageIds:\n- '17405836920431227'\n") and "11:33 1" in D6 and "above zero since 11:33 IST: the condition holds" in D6, D6
assert "policy: Ingest dead-letter queue holds messages - above 0 for 60s, 1 notification channel(s)" in D6, D6
assert OUT["drain"] == "pulled 1; acknowledged 1 drill message(s); 0 other(s) left for make dlq\n", OUT["drain"]
assert json.loads(STATE.read_text(encoding="utf-8"))["dlq"] == []

# the plan and the apply are terraform's and infrastructure.py's own printing on a lane with state: their shape
OUT["plan"] = ("PASS: saved confirmed inputs to .../terraform/runbook-project.auto.tfvars.json\n"
               "CI trust: OWNER/REPO (ID NUMBER) / refs/heads/main\n...\n"
               "Terraform will perform the following actions:\n\n"
               "  # google_monitoring_alert_policy.dlq_depth will be created\n"
               '  + resource "google_monitoring_alert_policy" "dlq_depth" {\n'
               '      + combiner              = "OR"\n'
               '      + display_name          = "Ingest dead-letter queue holds messages"\n'
               "      + notification_channels = [\n"
               f'          + "projects/{PROJ}/notificationChannels/NUMBER",\n'
               "        ]\n      ...\n    }\n\n"
               "Plan: 1 to add, 0 to change, 0 to destroy.\n"
               "PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: .../terraform/rag-20260924T060011Z-3f2a9c1d7e.tfplan\n"
               "Review the displayed changes, then run this command with 'apply' instead of 'plan'.\n"
               "PASS: selected plan, confirmed inputs, backend/workspace and state agree: .../terraform/rag-20260924T060011Z-3f2a9c1d7e.tfplan\n"
               "PASS: selected plan, confirmed inputs, backend/workspace and state agree: .../terraform/rag-20260924T060011Z-3f2a9c1d7e.tfplan\n"
               "google_monitoring_alert_policy.dlq_depth: Creating...\n"
               f"google_monitoring_alert_policy.dlq_depth: Creation complete after 1s [id=projects/{PROJ}/alertPolicies/NUMBER]\n\n"
               "Apply complete! Resources: 1 added, 0 changed, 0 destroyed.\n")
INFRA = (KIT / "commands/infrastructure.py").read_text(encoding="utf-8")
for line in ('print(f"PASS: saved confirmed inputs to {self.inputs}")', 'print(f"PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: {path}")',
             'print("Review the displayed changes, then run this command with \'apply\' instead of \'plan\'.")',
             'print(f"PASS: selected plan, confirmed inputs, backend/workspace and state agree: {path}")', 'path = self.check()\n        self.check()'):
    assert line in INFRA, line
assert 'filename = "rag-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:10] + ".tfplan"' in INFRA
assert "plan: guard-project\n\t$(INFRA) plan $(INFRA_FLAGS) $(INFRA_VARS)" in src["Makefile"]
assert "up: guard-project\n\t$(INFRA) apply $(INFRA_FLAGS) $(INFRA_PLAN)\n" in src["Makefile"]

# ---- the panel: eight rows and the four readers' verdicts, from the filters parsed above
H = {"api": "documind-api", "chat": "documind-chat"}
PANEL_ROWS = [
    ("q1", "An answer on /v1/query (acme), 11:10 IST today", "api", ROWS_TODAY[0], 0, 0.17),
    ("q2", "A refused question (acme), 11:12 IST today", "api", ROWS_TODAY[2], 0, 0.15),
    ("st", "A streamed answer from the UI (zeta), 09:40 IST today", "api", BUILT["stream"], 0, 1.7),
    ("lc", "A retrieval for the chat service's LangChain brain (acme), 10:05 IST", "api", BUILT["chain"], 0, 1.3),
    ("ch", "The chat service's own row for that turn, 10:05 IST", "chat", CHAT_ROW, 0, 1.3),
    ("im", "A Media Studio image (acme), 10:30 IST today", "api", BUILT["image"], 0, 0.9),
    ("y1", "An answer at 22:40 IST yesterday (acme)", "api", ROWS_TODAY[0], -1, 12.7),
    ("y2", "An answer 26 hours ago (zeta)", "api", ROWS_TODAY[3], -1, 26.0),
]
READERS = ["Cloud Logging", "the sink's table in BigQuery", "tenant_daily, today", "make usage HOURS=24", "documind/queries, today"]


def verdicts(service: str, row: dict, day: int, age_h: float) -> list:
    ev, svc = row["event"], H[service]
    sink = svc in SINK_SERVICES and ev in SINK_EVENTS
    missing = f"the sink's filter has no {'event ' + ev if svc in SINK_SERVICES else svc}"
    out = [(True, "keeps every row for 30 days"),
           (sink, "copied: its service and event are in the sink's filter" if sink else "not copied: " + missing)]
    out.append((sink and ev in VIEW_EVENTS and day == 0,
                "never in BigQuery, since " + missing if not sink else f"its WHERE has no {ev}" if ev not in VIEW_EVENTS
                else "yesterday's row, not today's" if day else "today, counted"))
    usage_ok = svc == "documind-api" and ev in TOOL_EVENTS
    out.append((usage_ok and age_h <= 24, f"reads {', '.join(TOOL_EVENTS)} from documind-api only" if not usage_ok
                else "older than 24 hours" if age_h > 24 else "inside the last 24 hours" + (" (across midnight)" if day else "")))
    metric_ok = svc == METRIC_SERVICE and ev in METRIC_EVENTS
    out.append((metric_ok and day == 0, f"counts {', '.join(METRIC_EVENTS)} only" if not metric_ok
                else "counted on the day it was written" if day else "counted"))
    return out


PANEL = []
for key, label, service, row, day, age in PANEL_ROWS:
    PANEL.append({"key": key, "label": label, "inr": float(row.get("cost_usd") or 0.0) * 85,
                  "event": row["event"], "service": H[service], "v": [[ok, why] for ok, why in verdicts(service, row, day, age)]})
V = {p["key"]: [ok for ok, _ in p["v"]] for p in PANEL}
assert V["im"] == [True, False, False, True, False] and V["ch"] == [True, True, False, False, False], V
assert V["y1"] == [True, True, False, True, False] and V["y2"] == [True, True, False, False, False], V
assert V["q1"] == V["q2"] == V["st"] == V["lc"] == [True, True, True, True, True], V
IMAGE_INR = next(p["inr"] for p in PANEL if p["key"] == "im")
assert IMAGE_INR == 0.039 * 85

shutil.rmtree(T, ignore_errors=True)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "readers": "run in the operator shell, in the kit (the readers as the kit writes them down; no network)",
    "ask": "run in the operator shell, in the kit (four questions, then make usage)",
    "recon": "run in the operator shell, in the kit (reads only: Cloud Logging and one small BigQuery query)",
    "alerts": "run in the operator shell, in the kit (reads only)",
    "plan": "run in the operator shell, in the checkout where make up ran (Terraform's state)",
    "drill": "run in the operator shell, in the kit (one drill message into the dead-letter queue, then the gauge)",
    "drain": "run in the operator shell, in the kit (acknowledges the drill message only)",
}
OUT_LABELS = {
    "readers": "(this cell run on the kit's own sink.tf, tenant_daily.sql, usage_rows.py and alerts.tf)",
    "ask": "(the kit's rag-api on a stand-in lane, then the kit's usage_rows.py over its rows; your tokens and rupees differ)",
    "recon": "(the kit's group() over the same rows; Cloud Logging and BigQuery stood in, the view's arithmetic asserted against its SQL)",
    "alerts": "(a lane made up before this kit version, from a stand-in of the Monitoring API; RECONCILE_JOB=true adds two policies)",
    "plan": "shape (terraform prints the whole resource; your paths, ids and CI repository are your lane's)",
    "drill": "(Pub/Sub and Monitoring stood in; your times differ)",
    "drain": "(Pub/Sub stood in)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})

# ------------------------------------------------------------------ the widget: which reader counts which row
UI_JS = r"""var root = document.getElementById('rc'); if (!root) return;
  var ROWS = %s, READERS = %s, $ = function(id){ return document.getElementById(id); };
  function el(tag, cls, text){ var e = document.createElement(tag); if (cls) { e.className = cls; } if (text !== undefined) { e.textContent = text; } return e; }
  function rs(x){ return 'Rs ' + (Math.round(x * 100 + 1e-7) / 100).toFixed(2); }
  function render(){ var on = ROWS.filter(function(r){ return $('rc-' + r.key).checked; }), grid = $('rc-grid'), why = $('rc-why');
    grid.textContent = ''; why.textContent = '';
    grid.appendChild(el('b', '', 'Reader')); grid.appendChild(el('b', 'num', 'rows')); grid.appendChild(el('b', 'num', 'rupees'));
    READERS.forEach(function(name, i){ var n = 0, inr = 0;
      on.forEach(function(r){ if (r.v[i][0]) { n += 1; inr += r.inr; } });
      grid.appendChild(el('span', '', name)); grid.appendChild(el('span', 'num', String(n)));
      grid.appendChild(el('span', 'num', i === 4 ? 'a count' : rs(inr))); });
    var only = function(a, b){ return on.filter(function(r){ return r.v[a][0] && !r.v[b][0]; }); };
    var diff = only(3, 2).concat(only(2, 3));
    var head = el('p', diff.length ? 'stop' : 'pass', diff.length ? 'tenant_daily and make usage disagree, by these rows:' : 'tenant_daily and make usage agree on these rows.');
    why.appendChild(head);
    diff.forEach(function(r){ var p = el('p', '', ''); p.appendChild(el('b', '', r.label + ': '));
      p.appendChild(document.createTextNode('tenant_daily - ' + r.v[2][1] + '; make usage - ' + r.v[3][1] + '.')); why.appendChild(p); }); }
  ROWS.forEach(function(r){ var l = el('label', ''), c = el('input', ''); c.type = 'checkbox'; c.id = 'rc-' + r.key; c.checked = true;
    c.addEventListener('change', render); l.appendChild(c); l.appendChild(document.createTextNode(r.label + (r.inr ? ' (' + rs(r.inr) + ')' : ' (no cost on the row)')));
    $('rc-rows').appendChild(l); });
  render();""" % (json.dumps(PANEL), json.dumps(READERS))

squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS

N_TF_POLICIES = len(re.findall(r'resource "google_monitoring_alert_policy"', src[ALERTS]))
assert N_TF_POLICIES == 7 and src[ALERTS].count('alert_policy" "dlq_depth"') == 1        # the setup box's grep prints 1
STATS = {"N_TF_POLICIES": str(N_TF_POLICIES), "N_LANE_POLICIES": str(len(LANE_POLICIES)), "N_METRICS": str(len(METRICS)),
         "IMAGE_INR": f"{int(IMAGE_INR * 100 + 0.5 + 1e-7) / 100:.2f}", "N_INTENTS": str(len(INTENTS)), "N_ROWS": str(len(PANEL))}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    for p in PANEL:
        print(f"----- {p['key']}: {p['inr']} | {[ok for ok, _ in p['v']]}")
    print(STATS)
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: the readers from sink.tf, tenant_daily.sql, usage_rows.py and alerts.tf; the rows from the kit's rag-api on a stand-in lane,"
      f" reconciled with usage_rows.group() | {len(PANEL)} panel rows | the dead-letter policy added to alerts.tf")
