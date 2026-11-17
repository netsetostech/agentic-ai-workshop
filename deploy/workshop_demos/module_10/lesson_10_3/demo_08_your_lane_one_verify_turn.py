"""Lesson 10.3: Your lane: one verify turn

Without OFFLINE=1, make agent-turn needs PROJECT, and commands/agent-turn.sh exports what a live turn needs: the project for Gemini, rag-api's address, built from REGION (pass yours: the Makefile's default is us-central1), and documind-ui-sa as the account rag-api's ID token is minted as. gemini() builds the model as the chat service builds the Desk agent's, gemini-3.6-flash on location global at thinking low, and the reflect call runs on the same model at the same level. Every search is one POST to /v1/passages, the call lesson 10.1 showed, which rag-api books with no tokens and no cost. Each attempt runs under the chat service's limits, 12 calls and Rs 5, with its reflect call counted on it, so a verify turn can spend up to Rs 15.00 in all. By the kit's own count the turn costs about Rs 1.16 before thinking when its first attempt passes, and each retry adds about Rs 1.31; step 10 shows how that count is made.

Run order inside this file:
1. Definition (source window 43)

Prerequisites: demo_07_the_12_calculator_rows_offline_re_roll_choose_retry.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """make agent-turn PROJECT="$PROJECT" REGION="$REGION" PATTERN=verify

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    Without OFFLINE=1, make agent-turn needs PROJECT, and commands/agent-turn.sh exports what a live turn needs: the project for Gemini, rag-api's address, built from REGION (pass yours: the Makefile's default is us-central1), and documind-ui-sa as the account rag-api's ID token is minted as. gemini() builds the model as the chat service builds the Desk agent's, gemini-3.6-flash on location global at thinking low, and the reflect call runs on the same model at the same level. Every search is one POST to /v1/passages, the call lesson 10.1 showed, which rag-api books with no tokens and no cost. Each attempt runs under the chat service's limits, 12 calls and Rs 5, with its reflect call counted on it, so a verify turn can spend up to Rs 15.00 in all. By the kit's own count the turn costs about Rs 1.16 before thinking when its first attempt passes, and each retry adds about Rs 1.31; step 10 shows how that count is made.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one live verify turn, about Rs 1.16 before thinking if its first attempt passes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/turn_verify.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_43', step_01_definition),
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
