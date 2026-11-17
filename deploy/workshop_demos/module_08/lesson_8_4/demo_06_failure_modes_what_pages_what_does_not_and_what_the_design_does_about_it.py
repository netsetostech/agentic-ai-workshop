"""Lesson 8.4: Failure modes: what pages, what does not, and what the design does about it

The cell reads every Terraform file, lists the alert policies that watch the document lifecycle with what each one reads and when it exists, and counts the policies that read the main subscription, its oldest unacknowledged age, and cache_stale. The walk's planner is pure Python. The cell hands it three objects nobody indexed: one whose claim was cut off in processing, one zero-byte object, and one PDF the worker queued for the batch lane. Then it asks the claim's lease what the night's rewrite of the first will find. The same list from the Monitoring API: every policy on your lane by name, and whether any of them reads the main subscription or the dead-letter one.

Run order inside this file:
1. Do it: the policies the kit declares, read from its files (source window 39)
2. Do it: the walk on three stuck states (source window 41)
3. Read it on your lane: the policies that exist (source window 43)

Prerequisites: demo_05_architecture_three_designs_the_kit_rejected_and_the_number_that_would_change_eac.
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


def step_01_the_policies_the_kit_declares_read_from_it(session):
    """Run Do it: the policies the kit declares, read from its files at this checkpoint.

    The cell reads every Terraform file, lists the alert policies that watch the document lifecycle with what each one reads and when it exists, and counts the policies that read the main subscription, its oldest unacknowledged age, and cache_stale.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ingest_failed      reads ingest_events
    reconcile_drift    reads reconcile_drift - declared only when reconcile_job is true
    reconcile_failed   reads completed_task_attempt_count on documind-reconcile - declared only when reconcile_job is true
    dlq_depth          reads num_undelivered_messages on ingest-dlq-sub
    ingest_backlog     reads oldest_unacked_message_age on documind-ingest-push
    doc_type_pin_miss  reads doc_type_pin_miss
    policies that read documind-ingest-push: 1; that read oldest_unacked_message_age: 1; that count cache_stale: 0
    the walk: RECONCILE_JOB   ?= false | the batch job: BATCH_JOB       ?= false
    """
    import re, warnings
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    tf = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path("terraform").glob("*.tf"))}
    subs = dict(re.findall(r'resource "google_pubsub_subscription" "(\w+)" \{\s*name\s+= "([\w-]+)"', "".join(tf.values())))
    pols = []
    for f, text in tf.items():
        for m in re.finditer(r'resource "google_monitoring_alert_policy" "(\w+)" \{(.*?)\n\}\n', text, re.S):
            body = re.sub(r"\$\{google_pubsub_subscription\.(\w+)\.name\}", lambda s: subs[s.group(1)], m.group(2))
            gate = re.search(r"count\s+= var\.(\w+) \? 1 : 0", body)
            metric = {t.rsplit("/", 1)[-1] for t in re.findall(r'metric\.type=\\"([^"\\]+)\\"', body)}
            on = set(re.findall(r'(?:subscription_id|job_name)=\\"([^"\\]+)\\"', body))
            pols.append((m.group(1), gate.group(1) if gate else "", metric, on, body))
    for name, gate, metric, on, body in pols:
        if any(w in body for w in ("ingest", "reconcile", "doc_type_pin_miss")):
            print(f"{name:18} reads {', '.join(sorted(metric))}" + (f" on {', '.join(sorted(on))}" if on else "")
                  + (f" - declared only when {gate} is true" if gate else ""))
    sub = subs["ingest_push"]
    print(f"policies that read {sub}: {sum(sub in p[4] for p in pols)}; that read oldest_unacked_message_age: "
          f"{sum('oldest_unacked' in t for t in tf.values())}; that count cache_stale: {sum('cache_stale' in t for t in tf.values())}")
    mk = open("Makefile", encoding="utf-8").read()
    print("the walk:", re.search(r"^RECONCILE_JOB\s+\?= \w+", mk, re.M).group(0), "| the batch job:", re.search(r"^BATCH_JOB\s+\?= \w+", mk, re.M).group(0))

def step_02_the_walk_on_three_stuck_states(session):
    """Run Do it: the walk on three stuck states at this checkpoint.

    The walk's planner is pure Python. The cell hands it three objects nobody indexed: one whose claim was cut off in processing, one zero-byte object, and one PDF the worker queued for the batch lane. Then it asks the claim's lease what the night's rewrite of the first will find.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme/cut_off.md    reingest  (not in the ledger)
    acme/poison.pdf    reingest  (not in the ledger)
    acme/big.pdf       queued    (handed to the batch lane; the batch job indexes it, the claim says queued)
    drift 2 of 3 objects
    acme/cut_off.md's claim at the walk: 23,100 s old, its lease 660 s, so the rewrite's delivery takes the claim back and indexes the bytes
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["services/ingest"]
    from reconcile import decide_bytes, drift_of, plan     # the walk's planner: pure, no cloud client
    from idempotency import lease_of                       # the claim's lease (13 October 2026)
    docs = {"acme_aaa": {"status": "processing", "gcs_uri": "gs://b/acme/cut_off.md"},     # a worker cut off between claim and finish
            "acme_qqq": {"status": "queued", "gcs_uri": "gs://b/acme/big.pdf", "generation": "7"}}
    objects = [{"name": "acme/cut_off.md", "generation": "5", "tenant_id": "acme"},
               {"name": "acme/poison.pdf", "generation": "6", "tenant_id": "acme"},
               {"name": "acme/big.pdf", "generation": "7", "tenant_id": "acme"}]
    sha = {"acme/cut_off.md": "aaa", "acme/poison.pdf": "e3b0c442", "acme/big.pdf": "qqq"}
    summary = {}
    for act in plan(objects, {}, docs):
        if act["action"] == "check_bytes":
            act["action"] = decide_bytes(sha[act["name"]], "acme", None, docs)
        summary[act["action"]] = summary.get(act["action"], 0) + 1
        print(f"{act['name']:18} {act['action']:9} ({act.get('why', '')})")
    print(f"drift {drift_of(summary)} of {len(objects)} objects")
    age = 6 * 3600 + 25 * 60                                # claimed at 17:05 and cut off; the walk runs at 23:30
    verdict = "is nacked: the lease is live" if age < lease_of(docs["acme_aaa"]) else "takes the claim back and indexes the bytes"
    print(f"acme/cut_off.md's claim at the walk: {age:,} s old, its lease {lease_of(docs['acme_aaa']):,} s, so the rewrite's delivery {verdict}")

def step_03_on_your_lane_the_policies_that_exist(session):
    """Run Read it on your lane: the policies that exist at this checkpoint.

    The same list from the Monitoring API: every policy on your lane by name, and whether any of them reads the main subscription or the dead-letter one.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one GET on the Monitoring API; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 11 alert policies on the lane
      A registered document arrived at a version nobody reviewed
      API p95 latency > 3s
      Desk case queue: a case due within 24 hours and unacknowledged, or breached
      Desk gate check: a door could not read which tenants are on
      Desk: a delegation was refused
      Ingest dead-letter queue holds messages
      Ingest failed
      Ingest subscription backlog: oldest message over 30 minutes
      Unanswerable rate > 20% for a tenant
      documind-slm left warm: instances > 0 for 2 hours
      documind-vllm left warm: instances > 0 for 2 hours
    reads documind-ingest-push: True | reads the dead-letter subscription: True

    13 alert policies on the lane
      A registered document arrived at a versi
    """
    import json, os, re, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P = os.environ["PROJECT"]
    tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    req = urllib.request.Request(f"https://monitoring.googleapis.com/v3/projects/{P}/alertPolicies?pageSize=200", headers={"Authorization": "Bearer " + tok})
    policies = json.load(urllib.request.urlopen(req, timeout=60)).get("alertPolicies", [])
    print(f"{len(policies)} alert policies on the lane")
    for p in sorted(policies, key=lambda p: p["displayName"]):
        print(" ", p["displayName"])
    filters = " ".join(c.get("conditionThreshold", {}).get("filter", "") for p in policies for c in p.get("conditions", []))
    print("reads documind-ingest-push:", "documind-ingest-push" in filters, "| reads the dead-letter subscription:", "ingest-dlq-sub" in filters)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_39', step_01_the_policies_the_kit_declares_read_from_it),
        ('source_41', step_02_the_walk_on_three_stuck_states),
        ('source_43', step_03_on_your_lane_the_policies_that_exist),
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
