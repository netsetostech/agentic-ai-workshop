"""Lesson 11.5: The alert the dead-letter queue never had

Do it: what pages you today Do it: plan and apply A drill proves the alert end to end without waiting an hour for a poison upload. The cell publishes one message straight to the dead-letter topic, labelled drill=13.2. After five minutes it reads the gauge the policy reads, a sample a minute, and the policy itself. The drill message must not stay in the queue, and a real message must not be thrown away with it. The cell pulls without acknowledging, acknowledges only the messages labelled drill=13.2, and leaves anything else for make dlq.

Run order inside this file:
1. Do it: what pages you today (source window 15)
2. Do it: plan and apply (source window 18)
3. Do it: the drill (source window 20)
4. Do it: drain the drill message (source window 22)

Prerequisites: demo_05_reconcile_the_view_with_make_usage.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


def step_01_what_pages_you_today(session):
    """Run Do it: what pages you today at this checkpoint.

    Do it: what pages you today

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: log-based metrics on the lane: documind/ingest_embedded, documind/ingest_events, documind/ingest_reused, documind/queries, documind/reconcile_drift, documind/unanswerable
    alert policies on the lane: 5, and what each one reads
      API p95 latency > 3s                                 request_latencies on documind-api
      Ingest failed                                        ingest_events on any service
      Unanswerable rate > 20% for a tenant                 unanswerable on any service
      documind-slm left warm: instances > 0 for 2 hours    instance_count on documind-slm
      documind-vllm left warm: instances > 0 for 2 hours   instance_count on documind-vllm
    reads the dead-letter queue (ingest-dlq-sub):
    """
    import json, os, re, subprocess, urllib.request
    P = os.environ["PROJECT"]
    def gcloud(*a):
        """Run this cell's gcloud command with its project/region context and decode the requested output.
        
        Example: gcloud('logging', 'metrics', 'list', '--project', P, '--format=json')
        """
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
            metric = re.search(r'metric\.type="([^"]+)"', f)
            on = re.search(r'(?:service_name|subscription_id)="([^"]+)"', f)
            print(f"  {p['displayName'][:52]:52} {metric.group(1).rsplit('/', 1)[-1] if metric else '?'} on {on.group(1) if on else 'any service'}")
            if "ingest-dlq-sub" in f:
                dlq.append(p["displayName"])
    print("reads the dead-letter queue (ingest-dlq-sub): " + (", ".join(dlq) or "NOTHING - an upload the worker refused twelve times pages nobody"))

# Original CLI workflow for step_02_plan_and_apply.
COMMANDS_02 = """make plan PROJECT="$PROJECT" REGION="$REGION" ADMIN_EMAILS="$ME"   # the flags you gave make up; the plan refuses to delete
python commands/infrastructure.py apply --project "$PROJECT" --region "$REGION" --terraform-dir terraform   # make up's first line, alone

"""

def step_02_plan_and_apply(session):
    """Run Do it: plan and apply at this checkpoint.

    Do it: plan and apply

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the checkout where make up ran (Terraform's state).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: PASS: saved confirmed inputs to .../terraform/runbook-project.auto.tfvars.json
    CI trust: OWNER/REPO (ID NUMBER) / refs/heads/main
    ...
    Terraform will perform the following actions:

      # google_monitoring_alert_policy.dlq_depth will be created
      + resource "google_monitoring_alert_policy" "dlq_depth" {
          + combiner              = "OR"
          + display_name          = "Ingest dead-letter queue holds messages"
          + notification_channels = [
              + "projects/documind-ai-YOUR-ID/notificationChannels/NUMBER",
            ]
          ...
        }

    Plan: 1 to add, 0 to change, 0 to destroy.
    PASS: no deletes/replacements or existing CI trust changes. Reviewed plan: .../terraform/rag-20260924T060011Z-3
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_drill.
COMMANDS_03 = """gcloud pubsub topics publish documind-ingest-dlq --project "$PROJECT" --message="drill 13.2: not an upload" --attribute=drill=13.2
sleep 300     # a sample a minute, shown up to two minutes late, and the policy wants a minute above zero
python - <<'PY'
import datetime as dt, json, os, subprocess, urllib.parse, urllib.request
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
      else "not above zero yet: Pub/Sub's sample can take two minutes to appear; run this again")
PY

"""

def step_03_the_drill(session):
    """Run Do it: the drill at this checkpoint.

    A drill proves the alert end to end without waiting an hour for a poison upload. The cell publishes one message straight to the dead-letter topic, labelled drill=13.2. After five minutes it reads the gauge the policy reads, a sample a minute, and the policy itself.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one drill message into the dead-letter queue, then the gauge).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: messageIds:
    - '17405836920431227'
    ingest-dlq-sub, undelivered messages - the gauge the policy reads, a sample a minute:
      11:30 0  11:31 0  11:32 0  11:33 1  11:34 1  11:35 1  11:36 1  11:37 1
    policy: Ingest dead-letter queue holds messages - above 0 for 60s, 1 notification channel(s)
    above zero since 11:33 IST: the condition holds - Monitoring > Alerting shows the incident
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def step_04_drain_the_drill_message(session):
    """Run Do it: drain the drill message at this checkpoint.

    The drill message must not stay in the queue, and a real message must not be thrown away with it. The cell pulls without acknowledging, acknowledges only the messages labelled drill=13.2, and leaves anything else for make dlq.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acknowledges the drill message only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: pulled 1; acknowledged 1 drill message(s); 0 other(s) left for make dlq
    """
    import json, os, subprocess
    P = os.environ["PROJECT"]
    def gcloud(*a):
        """Run this cell's gcloud command with its project/region context and decode the requested output.
        
        Example: gcloud('pubsub', 'subscriptions', 'ack', 'ingest-dlq-sub', '--project', P, '--ack-ids=' + ','.join(drill))
        """
        return subprocess.run(["gcloud", *a], capture_output=True, text=True, check=True).stdout
    pulled = json.loads(gcloud("pubsub", "subscriptions", "pull", "ingest-dlq-sub", "--project", P, "--limit", "10", "--format=json") or "[]")
    drill = [m["ackId"] for m in pulled if (m["message"].get("attributes") or {}).get("drill") == "13.2"]
    if drill:
        gcloud("pubsub", "subscriptions", "ack", "ingest-dlq-sub", "--project", P, "--ack-ids=" + ",".join(drill))
    print(f"pulled {len(pulled)}; acknowledged {len(drill)} drill message(s); {len(pulled) - len(drill)} other(s) left for make dlq")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_what_pages_you_today),
        ('source_18', step_02_plan_and_apply),
        ('source_20', step_03_the_drill),
        ('source_22', step_04_drain_the_drill_message),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
