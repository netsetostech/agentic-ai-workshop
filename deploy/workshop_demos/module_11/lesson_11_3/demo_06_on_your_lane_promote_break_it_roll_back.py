"""Lesson 11.3: On your lane: promote, break it, roll back

gate-check reads lesson 11.2's record, the files first and then the lane; when every check passes, make promote moves the traffic and prints what /version now says. make candidate makes a revision from the template, with every setting it passes at the Makefile's default except the one you name. It takes no traffic, gets the candidate tag and goes into .candidate-revision. The same gate as lesson 11.2's, on the revision the file now names: about ten minutes of rows, and every row that reaches the model fails. run_eval.py's lines stream between the gate's two blocks. The verdict is recorded, red, and make reports release.py's exit 1 on its last line, Error 1, before exiting 2 itself. First make promote-gated, which the red record stops at its first recipe line, line 46 of mk/release.mk, so its make promote never starts. Then plain make promote, which reads no record and moves all the traffic to the mistyped revision. Go straight on to the next cell. make smoke-deployed names the smokes it skips and runs the rest; make incident reads what the smokes logged, with the gate record and the lane. time is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes. Do it: the smokes and the incident, after the rollback The cell reads documind-api and its revisions from the Cloud Run Admin API's v1 resources, the same JSON gcloud run services describe --format=json prints, without release.py: each recent revision's traffic, tag, image and model, then the template's, and whether the template is what serves. Each revision's image is a digest and the template's a tag, so the cell compares the template through the revision it made last, as make incident does. Run it now, before the repair, while they differ.

Run order inside this file:
1. Do it: promote lesson 11.2's candidate (source window 26)
2. Do it: the mistyped model, as a candidate (source window 28)
3. Do it: the gate on it (source window 30)
4. Do it: refused, then forced (source window 32)
5. Do it: the smokes, and the incident (source window 34)
6. Do it: the rollback, timed (source window 36)
7. Do it: the smokes and the incident, after the rollback (source window 39)
8. Read it: the template, from Cloud Run's API (source window 41)

Prerequisites: demo_05_make_smoke_deployed_and_make_incident_line_by_line.
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


# Original CLI workflow for step_01_promote_lesson_11_2_s_candidate.
COMMANDS_01 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make promote-gated PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_01_promote_lesson_11_2_s_candidate(session):
    """Run Do it: promote lesson 11.2's candidate at this checkpoint.

    gate-check reads lesson 11.2's record, the files first and then the lane; when every check passes, make promote moves the traffic and prints what /version now says.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (gate-check, then one traffic move).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/promote_gated.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_mistyped_model_as_a_candidate.
COMMANDS_02 = """make candidate PROJECT="$PROJECT" REGION="$REGION" GENERATOR_MODEL=gemini-3.6-flsh

"""

def step_02_the_mistyped_model_as_a_candidate(session):
    """Run Do it: the mistyped model, as a candidate at this checkpoint.

    make candidate makes a revision from the template, with every setting it passes at the Makefile's default except the one you name. It takes no traffic, gets the candidate tag and goes into .candidate-revision.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a revision with no traffic and a mistyped model).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/candidate_typo.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_gate_on_it.
COMMANDS_03 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make gate PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_03_the_gate_on_it(session):
    """Run Do it: the gate on it at this checkpoint.

    The same gate as lesson 11.2's, on the revision the file now names: about ten minutes of rows, and every row that reaches the model fails. run_eval.py's lines stream between the gate's two blocks. The verdict is recorded, red, and make reports release.py's exit 1 on its last line, Error 1, before exiting 2 itself.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every golden row, about ten minutes; no model call succeeds).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/gate_typo.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_refused_then_forced.
COMMANDS_04 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make promote-gated PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
make promote PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_04_refused_then_forced(session):
    """Run Do it: refused, then forced at this checkpoint.

    First make promote-gated, which the red record stops at its first recipe line, line 46 of mk/release.mk, so its make promote never starts. Then plain make promote, which reads no record and moves all the traffic to the mistyped revision. Go straight on to the next cell.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the refusal, then the forced traffic move: your API answers 500 until the rollback).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/promote_refused_forced.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_the_smokes_and_the_incident.
COMMANDS_05 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make smoke-deployed PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
make incident PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_05_the_smokes_and_the_incident(session):
    """Run Do it: the smokes, and the incident at this checkpoint.

    make smoke-deployed names the smokes it skips and runs the rest; make incident reads what the smokes logged, with the gate record and the lane.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, straight after (the smokes, then the incident read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_incident_red.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_the_rollback_timed.
COMMANDS_06 = """time make rollback PROJECT="$PROJECT" REGION="$REGION"

"""

def step_06_the_rollback_timed(session):
    """Run Do it: the rollback, timed at this checkpoint.

    time is the shell's own: when the command ends, it prints how long it took. The manifest's proof for this lesson asks for under two minutes.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, straight after (one traffic move, timed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rollback_timed.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

# Original CLI workflow for step_07_the_smokes_and_the_incident_after_the_roll.
COMMANDS_07 = """set +e +o pipefail   # as the page runs it: the cell prints its own exit status, which a failure must reach
make smoke-deployed PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
make incident PROJECT="$PROJECT" REGION="$REGION"; echo "exit $?"
true   # the status it printed is the cell's answer: compare it with the page's prose


"""

def step_07_the_smokes_and_the_incident_after_the_roll(session):
    """Run Do it: the smokes and the incident, after the rollback at this checkpoint.

    Do it: the smokes and the incident, after the rollback

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, after the rollback (the smokes, then the incident read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_incident_after.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_07)

def step_08_the_template_from_cloud_run_s_api(session):
    """Run Read it: the template, from Cloud Run's API at this checkpoint.

    The cell reads documind-api and its revisions from the Cloud Run Admin API's v1 resources, the same JSON gcloud run services describe --format=json prints, without release.py: each recent revision's traffic, tag, image and model, then the template's, and whether the template is what serves. Each revision's image is a digest and the template's a tag, so the cell compares the template through the revision it made last, as make incident does. Run it now, before the repair, while they differ.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, before the repair (two Cloud Run Admin API reads; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/template_read.txt]
    """
    import os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import google.auth
    from google.auth.transport.requests import AuthorizedSession
    
    P, R = os.environ["PROJECT"], os.environ["REGION"]
    creds, _ = google.auth.default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
    run = AuthorizedSession(creds.with_quota_project(P) if hasattr(creds, "with_quota_project") else creds)
    V1 = f"https://{R}-run.googleapis.com/apis/serving.knative.dev/v1/namespaces/{P}"
    
    
    def read(path, **params):
        """One read of the Cloud Run Admin API's v1 resources, as JSON; a failure says which read and why.
        
        Example: read('services/documind-api')
        """
        r = run.get(f"{V1}/{path}", params=params or None, timeout=30)
        if r.status_code != 200:
            raise SystemExit(f"GET {path}: HTTP {r.status_code} {r.text[:200]}")
        return r.json()
    
    
    def settings(spec):
        """(the image, GENERATOR_MODEL) of a spec: a revision holds a digest, spec.template the tag it was made from.
        
        Example: settings(svc['spec']['template']['spec'])
        """
        c = (spec.get("containers") or [{}])[0]
        env = {e.get("name"): e.get("value") for e in c.get("env") or []}
        return c.get("image", "").rsplit("/", 1)[-1], env.get("GENERATOR_MODEL")
    
    
    def short(image):
        """An image cut to what an eye compares: a digest to 12 hex digits, as docker shows one; a tag as it is.
        
        Example: short(template[0])
        """
        name, at, digest = image.partition("@sha256:")
        return f"{name}@sha256:{digest[:12]}" if at else image
    
    
    svc = read("services/documind-api")
    traffic = svc["status"]["traffic"]
    revs = sorted(read("revisions", labelSelector="serving.knative.dev/service=documind-api")["items"],
                  key=lambda r: r["metadata"]["creationTimestamp"])
    spec = {r["metadata"]["name"]: r["spec"] for r in revs}
    serving = max((t for t in traffic if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
    for rev in revs[-4:]:
        name = rev["metadata"]["name"]
        pct = sum(t.get("percent", 0) for t in traffic if t.get("revisionName") == name)
        tag = ",".join(t["tag"] for t in traffic if t.get("revisionName") == name and t.get("tag")) or "-"
        image, model = settings(rev["spec"])
        print(f"{name:26} {pct:>3}%  tag {tag:9}  {short(image):23}  GENERATOR_MODEL={model}")
    template = settings(svc["spec"]["template"]["spec"])
    print(f"{'spec.template':26} {'':4}  {'':13}  {short(template[0]):23}  GENERATOR_MODEL={template[1]}")
    now = settings(spec[serving])
    made = settings(spec[svc["status"]["latestCreatedRevisionName"]])[0]      # the digest the template's tag named
    if (made, template[1]) == now:
        print(f"the template is what serves: {serving}")
    else:
        print(f"the template is NOT what serves: {serving} runs GENERATOR_MODEL={now[1]}.")
        print("The next revision any update makes starts from the template, not from what serves.")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_promote_lesson_11_2_s_candidate),
        ('source_28', step_02_the_mistyped_model_as_a_candidate),
        ('source_30', step_03_the_gate_on_it),
        ('source_32', step_04_refused_then_forced),
        ('source_34', step_05_the_smokes_and_the_incident),
        ('source_36', step_06_the_rollback_timed),
        ('source_39', step_07_the_smokes_and_the_incident_after_the_roll),
        ('source_41', step_08_the_template_from_cloud_run_s_api),
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
