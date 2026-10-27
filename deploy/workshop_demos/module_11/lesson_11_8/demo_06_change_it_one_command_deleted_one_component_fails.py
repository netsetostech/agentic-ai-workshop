"""Lesson 11.8: Change it: one command deleted, one component fails

An entry of FAILURE-MODES.md without a command is a symptom nobody can reproduce. The canned fork's first entry, "Pinned traffic hides a change", is proved by make gotcha-drill ID=pinned-traffic, lesson 11.7's offline drill. The cell deletes that one line with sed, runs the check, then copies the kit's canned file back and runs it once more, printing only the exit code.

Run order inside this file:
1. Definition (source window 28)

Prerequisites: demo_05_the_check_offline_the_kit_as_it_ships_a_canned_capstone_your_fork.
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
COMMANDS_01 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
sed -i '/^Command: `make gotcha-drill ID=pinned-traffic`$/d' /tmp/sahyadri/FAILURE-MODES.md   # one command gone
make capstone-check FORK=/tmp/sahyadri; echo "exit $?"
cp commands/tests/capstone_fork/FAILURE-MODES.md /tmp/sahyadri/      # the file back as it was
make capstone-check FORK=/tmp/sahyadri >/dev/null; echo "exit $?"
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    An entry of FAILURE-MODES.md without a command is a symptom nobody can reproduce. The canned fork's first entry, "Pinned traffic hides a change", is proved by make gotcha-drill ID=pinned-traffic, lesson 11.7's offline drill. The cell deletes that one line with sed, runs the check, then copies the kit's canned file back and runs it once more, printing only the exit code.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (edits the canned fork's copy, then puts it back; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> capstone-check: the fork at /tmp/sahyadri, offline: its files and records, and make eval. PROJECT= adds the lane's
       reads
       1  PASS  A live URL behind IAP
                the fork deploys documind-ui behind IAP: --iap and --no-allow-unauthenticated (commands/lesson-12.4.sh)
                a member was answered: GET /version said git_sha abc1234, gemini-3.6-flash, documind-rag@v3 (make
                smoke-deployed, 2026-11-17T10:30:00Z)
                a non-member was refused: every isolation row (11) answered 403 to the outsider
                (evals/reports/gate-documind-api-00043-fix.json)
       2  PASS  Your own corpus, 30 pages or more, ingested
                sahyadri's corpus: 2 documents, 32 pages a
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_28', step_01_definition),
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
