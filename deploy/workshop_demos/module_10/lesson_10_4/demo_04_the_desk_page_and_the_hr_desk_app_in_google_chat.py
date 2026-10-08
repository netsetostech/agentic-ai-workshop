"""Lesson 10.4: The Desk page, and the HR Desk app in Google Chat

Do it: the questions, and the page

Run order inside this file:
1. Do it: the questions, and the page (source window 23)

Prerequisites: demo_03_your_lane_the_classes_the_example_index_and_the_switches.
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


# Original CLI workflow for step_01_the_questions_and_the_page.
COMMANDS_01 = """python - <<'PY'
import json, warnings
warnings.filterwarnings("ignore", category=UserWarning)
rows = {r["id"]: r for r in (json.loads(x) for x in open("evals/routes.jsonl", encoding="utf-8") if x.strip())}
for rid in ("lk-06", "lk-17", "lk-10"):
    print(f"{rid}: {rows[rid]['question']}")
PY
echo "$UI   <- open it signed in as $ME, then choose Desk"

"""

def step_01_the_questions_and_the_page(session):
    """Run Do it: the questions, and the page at this checkpoint.

    Do it: the questions, and the page

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the three route-set questions to paste, and the page's address).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lk-06: What is the notice period for a confirmed E3?
    lk-17: At what rate is gratuity paid for each completed year of service?
    lk-10: What is the total payable on invoice INV-2026-0412?
    https://documind-ui-NUMBER.asia-south1.run.app   <- open it signed in as you@example.com, then choose Desk
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_the_questions_and_the_page),
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
