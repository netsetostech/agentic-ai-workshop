"""Lesson 0.4: make off, and zero instances

Four switches and a check. Each switch is a make target of its own, and each line starts with -, which tells make to carry on when the line fails. That matters on your lane. make up deploys seven services, and of the four make off floors, only documind-ui is among them: the small model, the vLLM engine and the gateway arrive in Module 9. Their switches fail on a service that does not exist, make notes each error as ignored, and the loop prints absent for them. gke-down removes the vLLM workload from the GKE cluster, which has none yet, and leaves the cluster and its node standing, as its own message says. The loop at the end reads each floor back from the service's template. The same four floors are lowered every night at 23:00 IST by the documind-off job, so a floor you forget costs an evening; make off-now runs that job by hand. Now run the target: One thing make off does not cover is worth knowing before you ever raise a floor: MIN_INSTANCES reaches three deploy scripts, the UI's, the MCP server's and the A2A peer's, and make off floors only the UI. Deploy with MIN_INSTANCES=1 for a session day, and the read below will show documind-mcp and documind-agent still holding an instance after make off. The cell waits out the idle window, then reads instance_count for every Cloud Run service in the project, one point a minute over the last half hour:

Run order inside this file:
1. make off, and zero instances (source window 52)
2. make off, and zero instances (source window 56)

Prerequisites: demo_08_save_the_session_the_state_the_inputs_the_keys.
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


# Original CLI workflow for step_01_make_off_and_zero_instances.
COMMANDS_01 = """make off PROJECT="$PROJECT" REGION="$REGION"

"""

def step_01_make_off_and_zero_instances(session):
    """Run make off, and zero instances at this checkpoint.

    Four switches and a check. Each switch is a make target of its own, and each line starts with -, which tells make to carry on when the line fails. That matters on your lane. make up deploys seven services, and of the four make off floors, only documind-ui is among them: the small model, the vLLM engine and the gateway arrive in Module 9. Their switches fail on a service that does not exist, make notes each error as ignored, and the loop prints absent for them. gke-down removes the vLLM workload from the GKE cluster, which has none yet, and leaves the cluster and its node standing, as its own message says. The loop at the end reads each floor back from the service's template. The same four floors are lowered every night at 23:00 IST by the documind-off job, so a floor you forget costs an evening; make off-now runs that job by hand. Now run the target:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, after the setup section's pin-back window.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/off.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_make_off_and_zero_instances.
COMMANDS_02 = """sleep 900     # Cloud Run keeps an idle instance up to 15 minutes after its last request
python - <<'PY'
import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
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
print("services with an instance in the last 3 minutes: " + (", ".join(still) if still else "none - zero instances"))
PY

"""

def step_02_make_off_and_zero_instances(session):
    """Run make off, and zero instances at this checkpoint.

    One thing make off does not cover is worth knowing before you ever raise a floor: MIN_INSTANCES reaches three deploy scripts, the UI's, the MCP server's and the A2A peer's, and make off floors only the UI. Deploy with MIN_INSTANCES=1 for a session day, and the read below will show documind-mcp and documind-agent still holding an instance after make off. The cell waits out the idle window, then reads instance_count for every Cloud Run service in the project, one point a minute over the last half hour:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell after make off, with no request to the lane in between (reads Cloud Monitoring; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/zero_instances.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_52', step_01_make_off_and_zero_instances),
        ('source_56', step_02_make_off_and_zero_instances),
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
