"""Lesson 11.6: Off at night, and the ceiling under it

Do it: the floor, then the switch A floor of zero lets the service scale to zero, but an idle instance can stay up for up to fifteen minutes after its last request. The cell waits, then reads the UI's instance count from Cloud Monitoring for the last half hour, a sample a minute. make gpu-cap writes a consumer quota override on the L4 quotas in us-central1, capping them at one card. --max-instances belongs to one service. The quota belongs to the project, so a second GPU service, a GPU candidate or a typo cannot allocate a second card. Lowering a quota needs no approval; raising it again does.

Run order inside this file:
1. Do it: the floor, then the switch (source window 20)
2. Do it: the instances, after fifteen minutes (source window 22)
3. Do it: the ceiling (source window 24)

Prerequisites: demo_05_the_tier_at_85_percent.
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


# Original CLI workflow for step_01_the_floor_then_the_switch.
COMMANDS_01 = """gcloud run services update documind-ui --region "$REGION" --project "$PROJECT" --min-instances 1 --quiet   # a session day's floor
make off PROJECT="$PROJECT"
gcloud scheduler jobs describe documind-off-nightly --location "$REGION" --project "$PROJECT" \\
  --format='value(schedule,timeZone,state,lastAttemptTime)'

"""

def step_01_the_floor_then_the_switch(session):
    """Run Do it: the floor, then the switch at this checkpoint.

    Do it: the floor, then the switch

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a floor, then the switch, then the nightly job's entry).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gcloud run services update documind-slm --region us-central1 --project documind-ai-YOUR-ID --min-instances 0 --quiet
    ERROR: (gcloud.run.services.update) Service [documind-slm] could not be found.
    make[1]: [Makefile:659: slm-off] Error 1 (ignored)
    ...
    gcloud run services update documind-ui --region asia-south1 --project documind-ai-YOUR-ID --min-instances 0 --quiet
    Deploying...
    ...
    Done.
    ...
    documind-slm: min-instances absent
    documind-vllm: min-instances absent
    documind-gateway: min-instances absent
    documind-ui: min-instances 0
    0 23 * * *	Asia/Kolkata	ENABLED	2026-09-23T17:30:03.184Z
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_instances_after_fifteen_minutes.
COMMANDS_02 = """python - <<'PY'
import datetime as dt, json, os, subprocess, urllib.parse, urllib.request
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
      else "not zero yet: an idle instance can stay up to 15 minutes after its last request; run this again")
PY

"""

def step_02_the_instances_after_fifteen_minutes(session):
    """Run Do it: the instances, after fifteen minutes at this checkpoint.

    A floor of zero lets the service scale to zero, but an idle instance can stay up for up to fifteen minutes after its last request. The cell waits, then reads the UI's instance count from Cloud Monitoring for the last half hour, a sample a minute.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (after 15 minutes; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-ui, container instances (active and idle), a sample a minute, last 30 minutes:
      11:52 1  11:53 1  11:54 1  11:55 1  11:56 1  11:57 1  11:58 1  11:59 1  12:00 1  12:01 1
      12:02 1  12:03 1  12:04 1  12:05 1  12:06 1  12:07 1  12:08 1  12:09 0  12:10 0  12:11 0
      12:12 0  12:13 0  12:14 0  12:15 0  12:16 0  12:17 0  12:18 0  12:19 0  12:20 0  12:21 0
    zero instances since 12:09 IST
    """
    manual_checkpoint('The next read is Cloud Monitoring fifteen minutes after make off. Stop and rerun this demo later if you like; completed shutdown steps will not run again. After done, it waits only for whatever is left of the fifteen minutes.')
    from workshop_helpers.steps import wait_after
    wait_after(session, "source_20", 900)   # the page's sleep 900, less the time since make off completed
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_ceiling.
COMMANDS_03 = """make gpu-cap PROJECT="$PROJECT"

"""

def step_03_the_ceiling(session):
    """Run Do it: the ceiling at this checkpoint.

    make gpu-cap writes a consumer quota override on the L4 quotas in us-central1, capping them at one card. --max-instances belongs to one service. The quota belongs to the project, so a second GPU service, a GPU candidate or a typo cannot allocate a second card. Lowering a quota needs no approval; raising it again does.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (lowers one quota; make gpu-cap-off takes it back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python services/slm/gpu_quota.py --project documind-ai-YOUR-ID --region us-central1 --cap 1

    Total NVIDIA L4 GPU allocation without zonal redundancy
      run.googleapis.com/nvidia_l4_gpu_allocation_no_zonal_redundancy
      1/{project}/{region}         us-central1  effective 3 (default 3)
                                   -> capped at 1

    1 override(s) written. Read back:
      Total NVIDIA L4 GPU allocation without zonal red 1/{project}/{region}       effective 1 (default 3, override 1)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_the_floor_then_the_switch),
        ('source_22', step_02_the_instances_after_fifteen_minutes),
        ('source_24', step_03_the_ceiling),
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
