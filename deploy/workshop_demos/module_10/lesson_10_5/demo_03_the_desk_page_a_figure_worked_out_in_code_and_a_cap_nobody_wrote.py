"""Lesson 10.5: The Desk page: a figure worked out in code, and a cap nobody wrote

make desk with NOTES= writes tenant_settings/acme.clause_notes from evals/desk/clause_notes.acme.json: a note on LV-01 and LV-07. Each note says what the OSH Code's text says about that leave, and leaves it to the People team whether it covers the person's role. The handbook desk adds a clause's note under an answer that cites the clause, in agent mode as in a direct answer. The command prints one line: acme's switches as they stand, "clause_notes": ["LV-01", "LV-07"], and that rag-api and the chat service read the change within 60 seconds. The cell also notes the time in SINCE105, from which step 7 reads the Desk's rows, and prints the Desk page's address.

Run order inside this file:
1. Do it: acme's notes on two clauses (source window 6)

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


# Original CLI workflow for step_01_acme_s_notes_on_two_clauses.
COMMANDS_01 = """export SINCE105="$(date -u +%FT%TZ)" UI="https://documind-ui-$NUMBER.$REGION.run.app"
make desk PROJECT="$PROJECT" TENANT=acme NOTES=evals/desk/clause_notes.acme.json
echo "the Desk page: $UI"

"""

def step_01_acme_s_notes_on_two_clauses(session):
    """Run Do it: acme's notes on two clauses at this checkpoint.

    make desk with NOTES= writes tenant_settings/acme.clause_notes from evals/desk/clause_notes.acme.json: a note on LV-01 and LV-07. Each note says what the OSH Code's text says about that leave, and leaves it to the People team whether it covers the person's role. The handbook desk adds a clause's note under an answer that cites the clause, in agent mode as in a direct answer. The command prints one line: acme's switches as they stand, "clause_notes": ["LV-01", "LV-07"], and that rag-api and the chat service read the change within 60 seconds. The cell also notes the time in SINCE105, from which step 7 reads the Desk's rows, and prints the Desk page's address.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — acme's clause notes, and the time this lesson starts.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/desk_page.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_acme_s_notes_on_two_clauses),
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
