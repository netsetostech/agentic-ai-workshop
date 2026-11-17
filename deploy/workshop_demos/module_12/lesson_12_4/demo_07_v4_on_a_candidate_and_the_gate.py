"""Lesson 12.4: v4 on a candidate, and the gate

The target. make prompt-candidate is make release-candidate's update with one more variable: PROMPT_VERSION beside GIT_SHA. Before any gcloud call it runs improve.py version, which stops on a version prompt_rules.json does not list. Then make record-candidate writes the new revision's name to .candidate-revision, the name make gate and make promote read. config.py's default stays v3, so v4 answers only where the variable is set. The check runs offline, and you can run it yourself. The cell reads the version accept wrote as PV, and every cell after it uses $PV. This page's run wrote v4. On a lane where lesson 3.6 committed its v4, accept writes v5, because it takes the version after the highest that any commit in your history has registered, so a label is never given a second meaning. The commits pass your name as $ME, as 3.6's did, so they work on a shell with no git identity of its own. A revision whose image does not carry its version does not start. If PROMPT_VERSION names a version that the image's prompt_rules.json does not list and lesson 3.6's registry does not hold, generator.py's last line raises at import, and Cloud Run keeps the traffic where it was: Commit, build, and make the candidate. The commit holds the new version and its golden row together, because the gate judges them together. make build pushes the API image tagged with that commit, so the image carries v4. The last line reads the variable back from the revision itself. Commit, build, and make the candidate. The commit holds the new version and its golden row together, because the gate judges them together. make build pushes the API image tagged with that commit, so the image carries v4. The last line reads the variable back from the revision itself. The gate. make gate is lesson 11.2's, unchanged. It judges the revision .candidate-revision names, once the candidate tag routes to it and its /version answers as its GIT_SHA. Its first lines print the prompt label the tag URL answers as, which should be v4's. Then run_eval.py asks every golden row of the tag URL, the one you pasted among them, and the record binds the verdict to that revision and to the files it was judged by (lesson 11.2). A rule that slips past the phrases and refuses less meets refusal_rate here.

Run order inside this file:
1. v4 on a candidate, and the gate (source window 45)
2. v4 on a candidate, and the gate (source window 48)
3. v4 on a candidate, and the gate (source window 50)

Prerequisites: demo_06_a_person_accepts_it_v4_and_its_golden_row.
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


# Original CLI workflow for step_01_v4_on_a_candidate_and_the_gate.
COMMANDS_01 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
export PV="$(python -c 'import json; v = json.load(open("services/rag-api/prompt_rules.json"))["versions"]; print(max(v, key=lambda k: int(k[1:])))')"; echo "PV=$PV"   # the version accept wrote: v4, or v5 where lesson 3.6 spent v4
python evals/improve.py version "$PV"
python evals/improve.py version "v$(( ${PV#v} + 1 ))"; echo "exit $?"
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_01_v4_on_a_candidate_and_the_gate(session):
    """Run v4 on a candidate, and the gate at this checkpoint.

    The target. make prompt-candidate is make release-candidate's update with one more variable: PROMPT_VERSION beside GIT_SHA. Before any gcloud call it runs improve.py version, which stops on a version prompt_rules.json does not list. Then make record-candidate writes the new revision's name to .candidate-revision, the name make gate and make promote read. config.py's default stays v3, so v4 answers only where the variable is set. The check runs offline, and you can run it yourself. The cell reads the version accept wrote as PV, and every cell after it uses $PV. This page's run wrote v4. On a lane where lesson 3.6 committed its v4, accept writes v5, because it takes the version after the highest that any commit in your history has registered, so a label is never given a second meaning. The commits pass your name as $ME, as 3.6's did, so they work on a shell with no git identity of its own.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the check make prompt-candidate runs first; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: PV=v4
    documind-rag@v4: SYSTEM's 5 rules and 1 added, accepted by you@your-company.com on 2026-10-13
      6. When the context gives different figures for different conditions, give the figure whose condition matches the question, and name that condition.
    PROMPT_VERSION=v5 is not in services/rag-api/prompt_rules.json, which lists v3, v4. A version is listed once a person accepts its rule (make improve REVIEWER=); commit it and make build before its candidate. A version made by editing SYSTEM (lesson 3.6) goes out with make release-candidate.
    exit 1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_v4_on_a_candidate_and_the_gate.
COMMANDS_02 = """git add services/rag-api/prompt_rules.json evals/build_golden.py evals/golden.jsonl
git -c user.name="$ME" -c user.email="$ME" commit -q -m "Prompt $PV: a rule from a production answer (lesson 12.4)" && git log --oneline -1
make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api 2>&1 | tail -3
make prompt-candidate PROJECT="$PROJECT" REGION="$REGION" PROMPT_VERSION="$PV"
gcloud run revisions describe "$(cat .candidate-revision)" --region "$REGION" --project "$PROJECT" --format=json \\
  | python -c 'import json, sys; e = {x["name"]: x.get("value") for x in json.load(sys.stdin)["spec"]["containers"][0]["env"]}; print("on the revision: PROMPT_VERSION", e.get("PROMPT_VERSION"), "| GIT_SHA", e.get("GIT_SHA"))'

"""

def step_02_v4_on_a_candidate_and_the_gate(session):
    """Run v4 on a candidate, and the gate at this checkpoint.

    A revision whose image does not carry its version does not start. If PROMPT_VERSION names a version that the image's prompt_rules.json does not list and lesson 3.6's registry does not hold, generator.py's last line raises at import, and Cloud Run keeps the traffic where it was: Commit, build, and make the candidate. The commit holds the new version and its golden row together, because the gate judges them together. make build pushes the API image tagged with that commit, so the image carries v4. The last line reads the variable back from the revision itself.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one commit, one Cloud Build, a revision with no traffic).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/prompt_candidate.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_v4_on_a_candidate_and_the_gate.
COMMANDS_03 = """make gate PROJECT="$PROJECT" REGION="$REGION"

"""

def step_03_v4_on_a_candidate_and_the_gate(session):
    """Run v4 on a candidate, and the gate at this checkpoint.

    Commit, build, and make the candidate. The commit holds the new version and its golden row together, because the gate judges them together. make build pushes the API image tagged with that commit, so the image carries v4. The last line reads the variable back from the revision itself. The gate. make gate is lesson 11.2's, unchanged. It judges the revision .candidate-revision names, once the candidate tag routes to it and its /version answers as its GIT_SHA. Its first lines print the prompt label the tag URL answers as, which should be v4's. Then run_eval.py asks every golden row of the tag URL, the one you pasted among them, and the record binds the verdict to that revision and to the files it was judged by (lesson 11.2). A rule that slips past the phrases and refuses less meets refusal_rate here.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every golden row on the candidate: about Rs 29).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/gate_v4.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_45', step_01_v4_on_a_candidate_and_the_gate),
        ('source_48', step_02_v4_on_a_candidate_and_the_gate),
        ('source_50', step_03_v4_on_a_candidate_and_the_gate),
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
