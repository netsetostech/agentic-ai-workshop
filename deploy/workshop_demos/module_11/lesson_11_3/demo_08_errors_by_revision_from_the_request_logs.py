"""Lesson 11.3: Errors by revision, from the request logs

Do it: the requests, by revision

Run order inside this file:
1. Do it: the requests, by revision (source window 50)

Prerequisites: demo_07_on_your_lane_the_repair_through_the_gate_and_the_proof.
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


def step_01_the_requests_by_revision(session):
    """Run Do it: the requests, by revision at this checkpoint.

    Do it: the requests, by revision

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, after the proof (Cloud Logging reads; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/errors_by_revision.txt]
    """
    import collections, datetime, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    
    P = os.environ["PROJECT"]
    HOURS = float(os.environ.get("HOURS", "3"))
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    logs = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
    since = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=HOURS)
    FILTER = (f'logName="projects/{P}/logs/run.googleapis.com%2Frequests" AND resource.type="cloud_run_revision" '
              f'AND resource.labels.service_name="documind-api" AND timestamp>="{since:%Y-%m-%dT%H:%M:%SZ}"')
    
    
    def entries():
        """documind-api's request log lines in the window, oldest first: every page of Cloud Logging's entries:list.
        
        Example: entries()
        """
        body = {"resourceNames": [f"projects/{P}"], "filter": FILTER, "orderBy": "timestamp asc", "pageSize": 1000}
        while True:
            r = logs.post("https://logging.googleapis.com/v2/entries:list", json=body, timeout=60)
            if r.status_code != 200:
                raise SystemExit(f"entries:list: HTTP {r.status_code} {r.text[:200]}")
            page = r.json()
            yield from page.get("entries", [])
            if not page.get("nextPageToken"):
                return
            body["pageToken"] = page["nextPageToken"]
    
    
    count = collections.defaultdict(collections.Counter)
    failed = collections.defaultdict(collections.Counter)
    span = {}
    for e in entries():
        rev = (e.get("resource", {}).get("labels") or {}).get("revision_name") or "(no revision)"
        req = e.get("httpRequest") or {}
        status = int(req.get("status") or 0)
        count[rev]["2xx" if 200 <= status < 300 else "4xx" if 400 <= status < 500 else "5xx" if status >= 500 else "other"] += 1
        if status >= 500:
            failed[rev][req.get("requestUrl", "").split(".run.app", 1)[-1].split("?", 1)[0] or "?"] += 1
            t = e["timestamp"][:19] + "Z"
            span[rev] = (min(span.get(rev, (t, t))[0], t), max(span.get(rev, (t, t))[1], t))
    print(f"documind-api's requests in the last {HOURS:g} hours, by the revision that answered:")
    for rev in sorted(count):
        c = count[rev]
        line = f"  {rev:26}" + "".join(f"  {k} {c[k]:>4}" for k in ("2xx", "4xx", "5xx"))
        if rev in failed:
            line += f"   5xx {span[rev][0]} to {span[rev][1]}: " + ", ".join(f"{p} {n}" for p, n in failed[rev].most_common())
        print(line)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_50', step_01_the_requests_by_revision),
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
