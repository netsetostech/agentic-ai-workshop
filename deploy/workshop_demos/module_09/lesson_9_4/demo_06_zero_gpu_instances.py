"""Lesson 9.4: Zero GPU instances

Do it

Run order inside this file:
1. Do it (source window 20)

Prerequisites: demo_05_everything_off.
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


def step_01_zero_gpu_instances(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, at least 10 minutes after make off (reads Cloud Monitoring; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: instance_count per service, 09:40 to 10:25 UTC, one point a minute (Cloud Monitoring):
      documind-slm      last instance at 10:13 UTC    a GPU service
      documind-vllm     no instance in the window     a GPU service
      documind-gateway  last instance at 10:09 UTC
      documind-ui       no instance in the window
    GPU services with an instance in the last 3 minutes: none - zero GPU instances
    """
    manual_checkpoint('The next read is Cloud Monitoring at least ten minutes after make off. Stop and rerun this demo later if you like; completed comparison/shutdown steps are retained. After done, it waits only for whatever is left of the ten minutes.')
    from workshop_helpers.steps import wait_after
    wait_after(session, "source_17", 600)   # the page: at least ten minutes after make off
    import json, os, subprocess, time, urllib.parse, urllib.request
    from datetime import datetime, timedelta, timezone
    P = os.environ["PROJECT"]
    tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    now = datetime.fromtimestamp(time.time(), timezone.utc).replace(second=0, microsecond=0)
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
    q = urllib.parse.urlencode({"filter": 'metric.type="run.googleapis.com/container/instance_count" AND resource.type="cloud_run_revision"',
                                "interval.startTime": iso(now - timedelta(minutes=45)), "interval.endTime": iso(now),
                                "aggregation.alignmentPeriod": "60s", "aggregation.perSeriesAligner": "ALIGN_MAX",
                                "aggregation.crossSeriesReducer": "REDUCE_SUM", "aggregation.groupByFields": "resource.label.service_name"})
    req = urllib.request.Request(f"https://monitoring.googleapis.com/v3/projects/{P}/timeSeries?{q}", headers={"Authorization": f"Bearer {tok}"})
    last = {}
    for s in json.load(urllib.request.urlopen(req, timeout=60)).get("timeSeries", []):
        up = [p["interval"]["endTime"] for p in s.get("points", []) if int(p["value"].get("int64Value", 0)) > 0]
        last[s["resource"]["labels"]["service_name"]] = max(up) if up else None
    GPU = ("documind-slm", "documind-vllm")
    print(f"instance_count per service, {iso(now - timedelta(minutes=45))[11:16]} to {iso(now)[11:16]} UTC, one point a minute (Cloud Monitoring):")
    for name in GPU + ("documind-gateway", "documind-ui"):
        t = last.get(name)
        what = f"last instance at {t[11:16]} UTC" if t else "no instance in the window"
        print(f"  {name:17} " + (f"{what:28}  a GPU service" if name in GPU else what))
    fresh = iso(now - timedelta(minutes=3))           # a sample shows up to 120 s after it is taken
    still = [n for n in GPU if last.get(n) and last[n] >= fresh]
    print("GPU services with an instance in the last 3 minutes: " + (", ".join(still) if still else "none - zero GPU instances"))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_zero_gpu_instances),
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
