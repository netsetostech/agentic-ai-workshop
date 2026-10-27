"""Lesson 4.3: Live traffic: the usage rows, and the gate's rows among them

The cell reads the last day's query and stream rows with the label make usage drops, the revision, and marks the revision that serves traffic now. Then it counts the rows by caller, and checks the eval identity's rows on a revision with no traffic against golden.jsonl. Do it: the same rows, as make usage groups them

Run order inside this file:
1. Do it: the rows, split by revision and by caller (source window 30)
2. Do it: the same rows, as make usage groups them (source window 32)

Prerequisites: demo_04_the_candidate_gate_a_revision_with_no_traffic_judged_before_any_user_meets_it.
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


def step_01_the_rows_split_by_revision_and_by_caller(session):
    """Run Do it: the rows, split by revision and by caller at this checkpoint.

    The cell reads the last day's query and stream rows with the label make usage drops, the revision, and marks the revision that serves traffic now. Then it counts the rows by caller, and checks the eval identity's rows on a revision with no traffic against golden.jsonl.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one Cloud Logging read and one describe; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rows_by_revision.txt]
    """
    import collections, datetime as dt, json, os, subprocess, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P, REGION = os.environ["PROJECT"], os.environ["REGION"]
    EVAL = f"documind-ui-sa@{P}.iam.gserviceaccount.com"     # make eval-live, make judge, make smoke and tok() ask as this
    
    
    def gcloud_json(*args):
        """Run one gcloud command for the project and return its JSON output, parsed.
        
        Example: gcloud_json() in the owning lesson/helper context
        """
        out = subprocess.run(["gcloud", *args, "--project", P, "--format=json"], capture_output=True, text=True, check=True).stdout
        return json.loads(out or "[]")
    
    
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=24)).strftime("%Y-%m-%dT%H:%M:%SZ")
    rows = gcloud_json("logging", "read", 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
                       f'AND (jsonPayload.event="query" OR jsonPayload.event="stream") AND timestamp>="{since}"', "--limit", "2000")
    traffic = gcloud_json("run", "services", "describe", "documind-api", "--region", REGION)["status"]["traffic"]
    serving = {t["revisionName"] for t in traffic if t.get("percent")}
    by_rev, by_who, asked = (collections.defaultdict(collections.Counter) for _ in range(3))
    others = set()
    for e in rows:
        p, rev = e["jsonPayload"], e["resource"]["labels"]["revision_name"]
        mine = p.get("user") == EVAL
        if not mine:
            others.add(p.get("user"))
        for c in (by_rev[rev], by_who[mine]):
            c["rows"] += 1
            c[p["event"]] += 1
            c["eval"] += mine
            c["unans"] += int(p.get("unanswerable_flag") or 0)
        if mine and rev not in serving:
            asked[rev][p["tenant"]] += 1
    print(f"{len(rows)} usage rows from documind-api in the last 24 h (events query and stream)")
    cols = f"{'rows':>5} {'query':>6} {'stream':>7} {'unans':>6}"
    print(f"\n  {'revision':30} {'traffic':8} {cols} {'eval id':>8}")
    for rev, c in sorted(by_rev.items()):
        print(f"  {rev:30} {'serving' if rev in serving else 'none':8} {c['rows']:5} {c['query']:6} {c['stream']:7} {c['unans']:6} {c['eval']:8}")
    print(f"\n  {'identity':39} {cols}")
    for mine, label in ((True, "documind-ui-sa: gates, judge, smoke, tok"), (False, f"everyone else: {len(others)} identities")):
        c = by_who[mine]
        print(f"  {label:39} {c['rows']:5} {c['query']:6} {c['stream']:7} {c['unans']:6}")
    gold = collections.Counter(json.loads(l)["tenant"] for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip())
    print("\n  golden.jsonl: " + ", ".join(f"{t} {n}" for t, n in sorted(gold.items())))
    for rev, t in sorted(asked.items()):
        print(f"  {rev}, no traffic, the eval identity: " + ", ".join(f"{k} {n}" for k, n in sorted(t.items())))

# Original CLI workflow for step_02_the_same_rows_as_make_usage_groups_them.
COMMANDS_02 = """make usage PROJECT="$PROJECT" HOURS=24

"""

def step_02_the_same_rows_as_make_usage_groups_them(session):
    """Run Do it: the same rows, as make usage groups them at this checkpoint.

    Do it: the same rows, as make usage groups them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same rows, as make usage groups them).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/usage_rows.py --project documind-ai-YOUR-ID --hours ${HOURS:-24}
    NN answers from documind-api in the last 24 h; USD_INR=85

    by tenant
    tenant                 answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ------------------------------------------------------------------------------------
    ...

    by model and backend (what answered, through which door)
    model                 model_backend          answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ----------------------------------------------------------------------------------------------------------
    ...

    by brain (8.7's question, from the row)
    brain                  answers    tok_in  tok_out       USD   
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_30', step_01_the_rows_split_by_revision_and_by_caller),
        ('source_32', step_02_the_same_rows_as_make_usage_groups_them),
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
