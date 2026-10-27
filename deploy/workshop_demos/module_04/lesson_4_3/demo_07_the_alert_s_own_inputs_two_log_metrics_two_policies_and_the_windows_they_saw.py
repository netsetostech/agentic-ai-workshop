"""Lesson 4.3: The alert's own inputs: two log metrics, two policies, and the windows they saw

The cell reads each metric's filter from Cloud Logging, both policies from Cloud Monitoring, and each metric's counts per tenant over the last six hours, aligned the way the policy aligns them. Then it divides, window by window.

Run order inside this file:
1. Do it: the metrics, the policies, and the windows (source window 42)

Prerequisites: demo_06_the_stream_s_row_answerable_unless_the_pool_was_empty.
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


def step_01_the_metrics_the_policies_and_the_windows(session):
    """Run Do it: the metrics, the policies, and the windows at this checkpoint.

    The cell reads each metric's filter from Cloud Logging, both policies from Cloud Monitoring, and each metric's counts per tenant over the last six hours, aligned the way the policy aligns them. Then it divides, window by window.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (two Cloud Logging reads and three Cloud Monitoring reads; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/alert_series.txt]
    """
    import datetime as dt, json, os, subprocess, urllib.parse, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P = os.environ["PROJECT"]
    TOKEN = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    
    
    def api_json(url):
        """GET one Google API URL with the operator's token and return the parsed JSON.
        
        Example: api_json(f"https://logging.googleapis.com/v2/projects/{P}/metrics/{urllib.parse.quote(name, safe='')}")
        """
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {TOKEN}"})
        return json.load(urllib.request.urlopen(req, timeout=60))
    
    
    for name in ("documind/unanswerable", "documind/queries"):
        m = api_json(f"https://logging.googleapis.com/v2/projects/{P}/metrics/{urllib.parse.quote(name, safe='')}")
        print(f"{name}: {' '.join(m['filter'].split())}")
    for p in api_json(f"https://monitoring.googleapis.com/v3/projects/{P}/alertPolicies?pageSize=200").get("alertPolicies", []):
        if p["displayName"] in ("Unanswerable rate > 20% for a tenant", "API p95 latency > 3s"):
            c = p["conditions"][0]["conditionThreshold"]
            print(f"policy {p['displayName']!r}: above {c['thresholdValue']} for {c['duration']}, "
                  f"enabled {p.get('enabled', True)}, notification channels {len(p.get('notificationChannels', []))}")
    now = dt.datetime.now(dt.timezone.utc).replace(second=0, microsecond=0)
    iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    
    def windows(metric):
        """One log metric's count per tenant in five-minute windows over the last six hours, aligned as the policy aligns it.
        
        Example: windows('documind/unanswerable')
        """
        q = urllib.parse.urlencode({
            "filter": f'metric.type="logging.googleapis.com/user/{metric}" AND resource.type="cloud_run_revision"',
            "interval.startTime": iso(now - dt.timedelta(hours=6)), "interval.endTime": iso(now),
            "aggregation.alignmentPeriod": "300s", "aggregation.perSeriesAligner": "ALIGN_DELTA",
            "aggregation.crossSeriesReducer": "REDUCE_SUM", "aggregation.groupByFields": "metric.label.tenant"})
        out = {}
        for s in api_json(f"https://monitoring.googleapis.com/v3/projects/{P}/timeSeries?{q}").get("timeSeries", []):
            for pt in s.get("points", []):
                out[(pt["interval"]["endTime"][11:16], s["metric"]["labels"].get("tenant", "?"))] = int(pt["value"].get("int64Value", 0))
        return out
    
    
    num, den = windows("documind/unanswerable"), windows("documind/queries")
    print("\nfive-minute windows with questions, the last six hours (UTC), per tenant:")
    for key in sorted(den):
        if den[key]:
            share = num.get(key, 0) / den[key]
            print(f"  {key[0]}  {key[1]:7} {num.get(key, 0):3} of {den[key]:3} unanswerable = {share:.2f}" + ("  above 0.20" if share > 0.20 else ""))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_42', step_01_the_metrics_the_policies_and_the_windows),
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
