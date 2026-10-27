"""Lesson 3.1: One question, five times, in the Chat page

Golden row jn-03 asked five times as yourself: what moves between the answers, what stays, and what the page sends. Start in the product, where a user meets variance. The Chat page streams each answer from /v1/stream and sends only the question: rag-api keeps no history, so five turns are five independent answers to one prompt. Before you ask, note the time in the operator shell. Step 9 reads the usage rows written since then.

Run order inside this file:
1. One question, five times, in the Chat page (source window 6)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_one_question_five_times_in_the_chat_page.
COMMANDS_01 = """export T0="$(date -u +%Y-%m-%dT%H:%M:%SZ)"; echo "lesson 3.1 from $T0 (UTC): step 9 reads the usage rows written since then"

"""

def step_01_one_question_five_times_in_the_chat_page(session):
    """Run One question, five times, in the Chat page at this checkpoint.

    Golden row jn-03 asked five times as yourself: what moves between the answers, what stays, and what the page sends. Start in the product, where a user meets variance. The Chat page streams each answer from /v1/stream and sends only the question: rag-api keeps no history, so five turns are five independent answers to one prompt. Before you ask, note the time in the operator shell. Step 9 reads the usage rows written since then.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT, before you ask in the UI (Rs 0: it notes the time).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lesson 3.1 from YYYY-MM-DDTHH:MM:SSZ (UTC): step 9 reads the usage rows written since then
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_one_question_five_times_in_the_chat_page),
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
