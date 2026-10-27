"""Lesson 3.6: The rows name the prompt; the candidate taken down, and v4 spent

Do it: the rows, by revision, event and version Removing the tag ends the candidate's URL. Deleting .candidate-revision means a stray make promote stops with an error instead of moving traffic to v4. Then main again, whose four files say v3, and the check on them. The branch stays.

Run order inside this file:
1. Do it: the rows, by revision, event and version (source window 55)
2. Do it: take the candidate down (source window 57)

Prerequisites: demo_07_ship_it_v4_on_a_branch_checked_built_and_answering_on_a_candidate.
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


def step_01_the_rows_by_revision_event_and_version(session):
    """Run Do it: the rows, by revision, event and version at this checkpoint.

    Do it: the rows, by revision, event and version

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one Cloud Logging read and one describe; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rows_v4.txt]
    """
    import collections, datetime as dt, json, os, subprocess, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P, REGION = os.environ["PROJECT"], os.environ["REGION"]
    
    
    def gcloud_json(*args):
        """Run one gcloud command for the project and return its JSON output, parsed.
        
        Example: gcloud_json('logging', 'read', f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.prompt_version:* AND timestamp>="{since}"', '--limit', '2000')
        """
        out = subprocess.run(["gcloud", *args, "--project", P, "--format=json"], capture_output=True, text=True, check=True).stdout
        return json.loads(out or "[]")
    
    
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=6)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = gcloud_json("logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
                       f'AND jsonPayload.prompt_version:* AND timestamp>="{since}"', "--limit", "2000")
    serving = {t["revisionName"] for t in gcloud_json("run", "services", "describe", "documind-api", "--region", REGION)["status"]["traffic"]
               if t.get("percent")}
    n, out = collections.Counter(), collections.Counter()
    for e in rows:
        p = e["jsonPayload"]
        key = (e["resource"]["labels"]["revision_name"], p.get("event"), p.get("prompt_version"))
        n[key] += 1
        out[key] += int(p.get("tokens_out") or 0)
    print(f"{len(rows)} usage rows from documind-api in the last 6 h, by revision, event and prompt_version")
    print(f"  {'revision':30} {'traffic':8} {'event':9} {'prompt':7} {'rows':>5} {'tokens_out':>10}")
    for rev, event, version in sorted(n):
        key = (rev, event, version)
        print(f"  {rev:30} {'serving' if rev in serving else 'none':8} {event:9} {version:7} {n[key]:5} {out[key]:10}")
    v4 = sorted({rev for rev, _, version in n if version == "v4"})
    print(f"rows that say v4 come from: {', '.join(v4) or 'no revision'}; serving traffic among them: {', '.join(sorted(set(v4) & serving)) or 'none'}")

# Original CLI workflow for step_02_take_the_candidate_down.
COMMANDS_02 = """gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
rm -f .candidate-revision      # make promote moves traffic to the revision this file names
curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"
git switch main
make prompt-version; echo "exit $?"
git branch --list prompt-v4

"""

def step_02_take_the_candidate_down(session):
    """Run Do it: take the candidate down at this checkpoint.

    Removing the tag ends the candidate's URL. Deleting .candidate-revision means a stray make promote stops with an error instead of moving traffic to v4. Then main again, whose four files say v3, and the check on them. The branch stays.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the tag and its record removed, main checked out; the branch kept).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    the candidate URL now: HTTP 404
    Switched to branch 'main'
    Your branch is up to date with 'origin/main'.
    python commands/prompt_pin.py
    prompt:   documind-rag@v3 (services/rag-api/config.py: prompt_id@prompt_version, as /version reports it)
    text:     SYSTEM + DATED_RULE, 604 characters, as generate() joins them (services/rag-api/generator.py)
    sha256:   543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
    registry: documind-rag@v3 has this sha256 (services/rag-api/prompt_versions.json): the text is the one its version names
    exit 0
      prompt-v4
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_55', step_01_the_rows_by_revision_event_and_version),
        ('source_57', step_02_take_the_candidate_down),
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
