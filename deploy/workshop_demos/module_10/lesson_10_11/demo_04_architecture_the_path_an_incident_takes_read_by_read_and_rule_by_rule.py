"""Lesson 10.11: Architecture: the path an incident takes, read by read and rule by rule

The loop runs make remediate OFFLINE=1 on each of the kit's seven recordings and prints, for each, the rule that decided, how many commands the plan printed, and its last line. The cell loads remediate.py, prints the only commands it may run, the events it reads on each service, the exact filter of its one logging read for the drill's window, and holds five commands against the denylist. RUNBOOKS=1 lists every policy the kit declares with its runbook and what remediate may do. Its first line, and the two signals no policy watches: One GET on the Monitoring API lists every alert policy on your lane by its display name, and the cell holds each against ops/runbooks.json. On a lane deployed with the defaults, expect eleven: three that remediate may roll back for and eight that are a person's, with the other six behind their switches. A no row line would be a policy that pages with no runbook remediate knows.

Run order inside this file:
1. Do it: every recording, offline (source window 36)
2. Do it: the reads, and the denylist (source window 38)
3. Do it: the catalog (source window 40)
4. Read it on your lane: the policies your lane holds (source window 42)

Prerequisites: demo_03_on_your_lane_hold_a_fault_read_the_plan_run_it_by_hand.
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


# Original CLI workflow for step_01_every_recording_offline.
COMMANDS_01 = """for f in held_model held_model_calls rolled_back restored old_revision person_only unknown_policy; do
  make remediate OFFLINE=1 FIXTURE=ops/incidents/$f.json > /tmp/plan_$f.txt
  printf '%-17s %-15s %s printed, %s\\n' "$f" "$(sed -n 's/^Diagnosis - rule \\([a-z_]*\\).*/\\1/p' /tmp/plan_$f.txt)" \\
    "$(grep -c '^       [^ ]' /tmp/plan_$f.txt)" "$(tail -n 1 /tmp/plan_$f.txt | cut -d. -f1)"
done

"""

def step_01_every_recording_offline(session):
    """Run Do it: every recording, offline at this checkpoint.

    The loop runs make remediate OFFLINE=1 on each of the kit's seven recordings and prints, for each, the rule that decided, how many commands the plan printed, and its last line.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: held_model        bad_revision    4 printed, 0 model calls
    held_model_calls  bad_revision    4 printed, 0 model calls
    rolled_back       rolled_back     3 printed, 0 model calls
    restored          no_failure      0 printed, 0 model calls
    old_revision      no_change       0 printed, 0 model calls
    person_only       person_only     0 printed, 0 model calls
    unknown_policy    unknown_policy  0 printed, 0 model calls
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_the_reads_and_the_denylist(session):
    """Run Do it: the reads, and the denylist at this checkpoint.

    The cell loads remediate.py, prints the only commands it may run, the events it reads on each service, the exact filter of its one logging read for the drill's window, and holds five commands against the denylist.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the only commands it runs: gcloud run services describe; gcloud run revisions list; gcloud logging read
    documind-chat: the request log, and the events chat, desk, desk_shadow, desk_delegation_refused, desk_gate_check, desk_check_tenants_unread
    documind-api: the request log, and the events query, stream, desk_gate_check, desk_check_tenants_unread
    resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND timestamp>="2026-10-12T09:00:00Z" AND (logName="projects/documind-ai-YOUR-ID/logs/run.googleapis.com%2Frequests" OR jsonPayload.event="chat" OR jsonPayload.event="desk" OR jsonPayload.event="desk_shadow" OR jsonPayload.event="desk_delegation_refused" OR jsonPayloa
    """
    import importlib.util, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    spec = importlib.util.spec_from_file_location("remediate", "commands/remediate.py")
    rm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rm)
    rows = rm.runbooks(rm.TF_DIR, rm.load_catalog())
    print("the only commands it runs:", "; ".join(" ".join(r) for r in rm.READS))
    for service in ("documind-chat", "documind-api"):
        print(f"{service}: the request log, and the events {', '.join(rm.events_for(service, rows))}")
    since = rm.utc("2026-10-12T09:00:00Z")                      # held_model.json's window opens here
    print(rm.log_filter("documind-ai-YOUR-ID", "documind-chat", since, rm.events_for("documind-chat", rows)))
    print(f"the newest {rm.LIMIT} lines of a window of {rm.build_parser().get_default('since')} (SINCE=, {rm.MAX_SINCE_H}h at most)")
    for c in ("gcloud run services update-traffic documind-chat --to-revisions documind-chat-00041-kpw=100",
              "gcloud run services delete documind-chat --quiet",
              "gcloud run deploy documind-chat --image chat:fix",
              "gcloud run services add-iam-policy-binding documind-chat --member=allUsers",
              "make down PROJECT=documind-ai-YOUR-ID"):
        hit = rm.NEVER.search(c)                                  # the denylist every printed command passes first
        print(f"{'refused: ' + repr(hit.group(0)) if hit else 'may be printed':22} {c}")

# Original CLI workflow for step_03_the_catalog.
COMMANDS_03 = """make remediate RUNBOOKS=1 | sed -n '1p;/^Silent/,$p'

"""

def step_03_the_catalog(session):
    """Run Do it: the catalog at this checkpoint.

    RUNBOOKS=1 lists every policy the kit declares with its runbook and what remediate may do. Its first line, and the two signals no policy watches:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 17 alert policies the kit declares (terraform/alerts.tf: 9, terraform/desk_alerts.tf: 8); 6 behind a switch. remediate may propose a rollback for 5; the rest are a person's.
    Silent: what remediate reads that no policy watches
      5xx answers: requests a service answered with a 5xx status, from Cloud Run's request log. no alert policy the kit
      declares counts a service's 5xx answers.
      chat turns stopped by a limit: documind-chat turns ended by one of their limits (limits.stopped_by on the chat row,
      workshop lesson 5.5). every chat row carries stopped_by and no policy counts it yet: an agent alert policy is
      designed for after 6 December.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def step_04_on_your_lane_the_policies_your_lane_holds(session):
    """Run Read it on your lane: the policies your lane holds at this checkpoint.

    One GET on the Monitoring API lists every alert policy on your lane by its display name, and the cell holds each against ops/runbooks.json. On a lane deployed with the defaults, expect eleven: three that remediate may roll back for and eight that are a person's, with the other six behind their switches. A no row line would be a policy that pages with no runbook remediate knows.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one GET on the Monitoring API; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/lane_policies.txt]
    """
    import importlib.util, json, os, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    spec = importlib.util.spec_from_file_location("remediate", "commands/remediate.py")
    rm = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rm)
    rows = {r["policy"]: r for r in rm.runbooks(rm.TF_DIR, rm.load_catalog())}
    P = os.environ["PROJECT"]
    tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    req = urllib.request.Request(f"https://monitoring.googleapis.com/v3/projects/{P}/alertPolicies?pageSize=200",
                                 headers={"Authorization": "Bearer " + tok})
    names = sorted(p["displayName"] for p in json.load(urllib.request.urlopen(req, timeout=60)).get("alertPolicies", []))
    print(f"{len(names)} alert policies on the lane")
    for n in names:
        r = rows.get(n)
        print(f"  {(r['action'] if r else 'no row'):8} {n}")
    off = sorted({rows[n]["gate"] for n in set(rows) - set(names) if rows[n]["gate"]})
    print(f"declared by the kit and not on this lane: {len(set(rows) - set(names))}" + (f", behind {', '.join(off)}" if off else ""))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_36', step_01_every_recording_offline),
        ('source_38', step_02_the_reads_and_the_denylist),
        ('source_40', step_03_the_catalog),
        ('source_42', step_04_on_your_lane_the_policies_your_lane_holds),
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
