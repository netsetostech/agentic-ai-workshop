"""Lesson 11.2: The record read back against Cloud Run, and gate-check alone

Do it: the record against the lane Do it: gate-check, and nothing after it

Run order inside this file:
1. Do it: the record against the lane (source window 33)
2. Do it: gate-check, and nothing after it (source window 35)

Prerequisites: demo_05_on_your_lane_the_candidate_named_the_token_s_audience_and_the_gate.
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


def step_01_the_record_against_the_lane(session):
    """Run Do it: the record against the lane at this checkpoint.

    Do it: the record against the lane

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two Cloud Run Admin API reads and your files; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/record_vs_lane.txt]
    """
    import hashlib, json, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    
    P, R = os.environ["PROJECT"], os.environ["REGION"]
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    run = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
    V1 = f"https://{R}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{P}"
    
    
    def read(path):
        """One read of the Cloud Run Admin API's v1 resources, as JSON; a failure says which read and why.
        
        Example: read(f"revisions/{rec['revision']}")
        """
        r = run.get(f"{V1}/{path}", timeout=30)
        if r.status_code != 200:
            raise SystemExit(f"GET {path}: HTTP {r.status_code} {r.text[:200]}")
        return r.json()
    
    
    def sha256(path):
        """A file's sha256, as make gate and gate-check compute it.
        
        Example: sha256(rec['report'])
        """
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    
    
    def short(value):
        """A digest or a sha256, cut to what an eye compares: the image's name and twelve hex digits.
        
        Example: short(recorded)
        """
        text = str(value)
        if "@sha256:" in text:
            return text.rsplit("/", 1)[-1][:23] + "..."
        return text[:12] + "..." if len(text) == 64 else text
    
    
    rec = json.load(open("evals/reports/gate.json", encoding="utf-8"))
    rev = read(f"revisions/{rec['revision']}")
    svc = read("services/documind-api")
    env = {e["name"]: e.get("value") for e in rev["spec"]["containers"][0].get("env", [])}
    ready = next((c["status"] for c in rev["status"].get("conditions", []) if c["type"] == "Ready"), "unknown")
    tagged = next((t.get("revisionName") for t in svc["status"]["traffic"] if t.get("tag") == "candidate"), "no revision")
    print(f"{rec['revision']}: {rec['verdict']}, eval exit {rec['eval_exit']}, {rec['rows']} rows, finished {rec['finished']}")
    rows = [("named by .candidate-revision", rec["revision"], open(".candidate-revision", encoding="utf-8").read().strip()),
            ("the candidate tag routes to", rec["revision"], tagged),
            ("image digest", rec["digest"], rev["status"].get("imageDigest")),
            ("GIT_SHA", rec["git_sha"], env.get("GIT_SHA")),
            ("Ready, as the gate required", "True", ready),
            ("report sha256", rec["report_sha256"], sha256(rec["report"]))]
    rows += [(f"{name} sha256", digest, sha256(name)) for name, digest in rec["rules"].items()]
    for what, recorded, now in rows:
        same = recorded == now
        print(f"  {'same' if same else 'DIFFERS':8}{what:31}{short(recorded)}" + ("" if same else f"  now {short(now)}"))

# Original CLI workflow for step_02_gate_check_and_nothing_after_it.
COMMANDS_02 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
python commands/release.py gate-check --project "$PROJECT" --region "$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_02_gate_check_and_nothing_after_it(session):
    """Run Do it: gate-check, and nothing after it at this checkpoint.

    Do it: gate-check, and nothing after it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the check alone: nothing moves).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/gate_check.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_33', step_01_the_record_against_the_lane),
        ('source_35', step_02_gate_check_and_nothing_after_it),
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
