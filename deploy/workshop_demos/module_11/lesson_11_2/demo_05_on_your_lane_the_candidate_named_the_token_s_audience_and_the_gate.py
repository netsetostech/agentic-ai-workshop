"""Lesson 11.2: On your lane: the candidate named, the token's audience, and the gate

make record-candidate is the line make release-candidate ends with, run on its own. The cell then prints the traffic table and whether the file and the tag name one revision. The cell mints two tokens as documind-ui-sa, one for the canonical URL and one for the tag URL, and calls the tag URL twice with each: /version, which checks no token itself, and /v1/sources for acme, which goes through verify_iap and acme's roster but calls no model. About ten minutes: every golden row as the member, then the isolation rows again as the outsider. run_eval.py's own lines stream between the gate's two blocks; lesson 4.3 reads them.

Run order inside this file:
1. Do it: name the candidate (source window 27)
2. Do it: the tag URL and the audience (source window 29)
3. Do it: the gate (source window 31)

Prerequisites: demo_04_make_gate_and_make_promote_gated_line_by_line.
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


# Original CLI workflow for step_01_name_the_candidate.
COMMANDS_01 = """make record-candidate PROJECT="$PROJECT" REGION="$REGION"
python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, R = os.environ["PROJECT"], os.environ["REGION"]
svc = json.loads(subprocess.run(["gcloud", "run", "services", "describe", "documind-api", f"--project={P}", f"--region={R}",
                                 "--format=json"], capture_output=True, text=True, check=True).stdout)
traffic = svc["status"]["traffic"]
for t in traffic:
    print(f"  {t.get('percent', 0):>3}%  {t.get('revisionName')}  tag {t.get('tag', '-')}")
named = open(".candidate-revision", encoding="utf-8").read().strip()
tagged = next((t.get("revisionName") for t in traffic if t.get("tag") == "candidate"), None)
print(f".candidate-revision names {named}; the candidate tag is on {tagged or 'no revision'}: "
      + ("the same revision" if named == tagged else "NOT the same, and make gate will refuse"))
PY

"""

def step_01_name_the_candidate(session):
    """Run Do it: name the candidate at this checkpoint.

    make record-candidate is the line make release-candidate ends with, run on its own. The cell then prints the traffic table and whether the file and the tag name one revision.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one describe; writes .candidate-revision).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/record_candidate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_the_tag_url_and_the_audience(session):
    """Run Do it: the tag URL and the audience at this checkpoint.

    The cell mints two tokens as documind-ui-sa, one for the canonical URL and one for the tag URL, and calls the tag URL twice with each: /version, which checks no token itself, and /v1/sources for acme, which goes through verify_iap and acme's roster but calls no model.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two tokens, four GETs, no model call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/audience.txt]
    """
    import json, os, re, subprocess, urllib.error, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P, N, R = os.environ["PROJECT"], os.environ["NUMBER"], os.environ["REGION"]
    CANONICAL = f"https://documind-api-{N}.{R}.run.app"           # SELF_URL: the audience the API checks
    TAG = f"https://candidate---documind-api-{N}.{R}.run.app"     # the URL make gate calls
    
    
    def token(audience):
        """An ID token for this audience as documind-ui-sa, minted as tok() and make gate mint theirs.
        
        Example: token(audience)
        """
        return subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={audience}",
                               f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com"],
                              capture_output=True, text=True, check=True).stdout.strip()
    
    
    def get(path, tok):
        """GET one path of the tag URL with this token: (the HTTP status, the body as text).
        
        Example: get(path, tok)
        """
        req = urllib.request.Request(TAG + path, headers={"Authorization": f"Bearer {tok}"})
        try:
            with urllib.request.urlopen(req, timeout=90) as resp:
                return resp.status, resp.read().decode("utf-8", "replace")
        except urllib.error.HTTPError as e:
            return e.code, e.read().decode("utf-8", "replace")
    
    
    for name, audience in (("the canonical URL", CANONICAL), ("the tag URL", TAG)):
        tok = token(audience)
        print(f"a token for {name}, {audience}")
        for path in ("/version", "/v1/sources?tenant_id=acme"):
            status, body = get(path, tok)
            try:
                doc = json.loads(body)
            except ValueError:
                doc = None
            if status == 200 and path == "/version":
                said = f"git_sha {doc['git_sha']}, {doc['generator_model']}, {doc['prompt']}"
            elif status == 200:
                said = f"{len(doc['sources'])} sources of {doc['tenant_id']}"
            else:
                said = (doc.get("detail") if isinstance(doc, dict) else None) or " ".join(re.sub(r"<[^>]+>", " ", body).split())[:100]
            print(f"  GET {path:27} HTTP {status}  {said}")

# Original CLI workflow for step_03_the_gate.
COMMANDS_03 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make gate PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_03_the_gate(session):
    """Run Do it: the gate at this checkpoint.

    About ten minutes: every golden row as the member, then the isolation rows again as the outsider. run_eval.py's own lines stream between the gate's two blocks; lesson 4.3 reads them.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every golden row, about ten minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/gate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_name_the_candidate),
        ('source_29', step_02_the_tag_url_and_the_audience),
        ('source_31', step_03_the_gate),
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
