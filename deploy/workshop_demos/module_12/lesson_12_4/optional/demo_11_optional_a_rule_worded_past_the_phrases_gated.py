"""Lesson 12.4: Optional: a rule worded past the phrases, gated

A rule that asks for fewer refusals in words the check does not know, accepted, built, and sent to the gate. What the check cannot see. The rule below asks the assistant to give "the closest answer it supports" instead of saying the context does not cover the question. None of the 58 phrases is in it, so make improve accepts it, as the panel in step 1 does. Its meaning reaches only the gate. There, refusal_rate counts the 18 rows the documents cannot answer, and 2 of them answered turn it red. Do not paste the golden row accept prints this time: the question is in the set already. The commit holds the version alone, and the next cell takes it back off.

Run order inside this file:
1. Optional: a rule worded past the phrases, gated (source window 59)
2. Optional: a rule worded past the phrases, gated (source window 61)

Prerequisites: demo_10_the_version_on_every_usage_row.
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


# Original CLI workflow for step_01_optional_a_rule_worded_past_the_phrases_ga.
COMMANDS_01 = """make improve ROW="$HOME/row124.json" IMPROVE_ARGS="--rule 'When the context only partly covers the question, give the closest answer it supports rather than saying it is not covered.'"
make improve REVIEWER="$ME"   # the next version; do not paste this golden row: the question is in the set already
export PAST="$(python -c 'import json; v = json.load(open("services/rag-api/prompt_rules.json"))["versions"]; print(max(v, key=lambda k: int(k[1:])))')"; echo "PAST=$PAST"   # the version just accepted
git -c user.name="$ME" -c user.email="$ME" commit -q -am "Prompt $PAST: a rule worded past the phrases (lesson 12.4, to be reverted)" && git log --oneline -1
make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api 2>&1 | tail -3
make prompt-candidate PROJECT="$PROJECT" REGION="$REGION" PROMPT_VERSION="$PAST"
make gate PROJECT="$PROJECT" REGION="$REGION"

"""

def step_01_optional_a_rule_worded_past_the_phrases_ga(session):
    """Run Optional: a rule worded past the phrases, gated at this checkpoint.

    A rule that asks for fewer refusals in words the check does not know, accepted, built, and sent to the gate. What the check cannot see. The rule below asks the assistant to give "the closest answer it supports" instead of saying the context does not cover the question. None of the 58 phrases is in it, so make improve accepts it, as the panel in step 1 does. Its meaning reaches only the gate. There, refusal_rate counts the 18 rows the documents cannot answer, and 2 of them answered turn it red. Do not paste the golden row accept prints this time: the question is in the set already. The commit holds the version alone, and the next cell takes it back off.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (your own rule, another candidate and gate: about Rs 29).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/gate_past.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_optional_a_rule_worded_past_the_phrases_ga.
COMMANDS_02 = """git -c user.name="$ME" -c user.email="$ME" revert --no-edit HEAD && git log --oneline -1
make build PROJECT="$PROJECT" REGION="$REGION" SERVICES=api 2>&1 | tail -3
make prompt-candidate PROJECT="$PROJECT" REGION="$REGION" PROMPT_VERSION="$PV"   # the version that serves: v3 if you reverted it in step 9

"""

def step_02_optional_a_rule_worded_past_the_phrases_ga(session):
    """Run Optional: a rule worded past the phrases, gated at this checkpoint.

    A rule that asks for fewer refusals in words the check does not know, accepted, built, and sent to the gate. What the check cannot see. The rule below asks the assistant to give "the closest answer it supports" instead of saying the context does not cover the question. None of the 58 phrases is in it, so make improve accepts it, as the panel in step 1 does. Its meaning reaches only the gate. There, refusal_rate counts the 18 rows the documents cannot answer, and 2 of them answered turn it red. Do not paste the golden row accept prints this time: the question is in the set already. The commit holds the version alone, and the next cell takes it back off.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit, after that gate (the version that serves goes back on the template).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_59', step_01_optional_a_rule_worded_past_the_phrases_ga),
        ('source_61', step_02_optional_a_rule_worded_past_the_phrases_ga),
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
