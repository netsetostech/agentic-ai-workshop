"""Lesson 2.5: The stage in the kit: the call, the guard, one line in /v1/query, and two lines that did not change

The cell asks the kit's guard about one question and five rewrites of it: a faithful one, the same one spelt with an en dash, the rupee sign and Devanagari digits, the amount written without its comma, the unit given another word, and the section spelt out. Nothing leaves the machine. evals/tests/test_query_rewrite.py holds 20 tests that need neither a model nor a lane: the guard on the design's examples and on the golden rows, every outcome against a fake client, the request against google-genai's own config class, the line with no question text, search_query() lifted from rewrite.py with the switch off and on, and the ablation's rewrite arm and paraphrase rows against a stand-in lane. The pipe keeps the summary and drops the timing.

Run order inside this file:
1. Do it, offline: the guard on the module's own example (source window 23)
2. Do it, offline: the kit's own tests (source window 25)

Prerequisites: demo_03_the_chat_page_with_the_stage_off_the_stream_never_asks_for_a_rewrite.
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


def step_01_offline_the_guard_on_the_module_s_own_exam(session):
    """Run Do it, offline: the guard on the module's own example at this checkpoint.

    The cell asks the kit's guard about one question and five rewrites of it: a faithful one, the same one spelt with an en dash, the rupee sign and Devanagari digits, the amount written without its comma, the unit given another word, and the section spelt out. Nothing leaves the machine.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: no call leaves the machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the question's literals: ['lv-07', 's.53', 'rs 52,000', '45 days']
    kept    leave encashment LV-07 s.53 Rs 52,000 monthly wages 45 days
    kept    lv–07 encashment, s.53, ₹५२,००० a month, 45 days
    refused leave encashment LV-07 s.53 Rs 52000 45 days   (dropped rs 52,000)
    refused leave encashment LV-07 s.53 Rs 52,000 45 working days   (dropped 45 days)
    refused LV-07 encashment under section 53, Rs 52,000, 45 days   (dropped s.53)
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, ".")
    from shared import query_rewrite as qr
    Q = "Can I encash LV-07 leave under s.53 on Rs 52,000 a month after 45 days?"
    print("the question's literals:", qr.literals(Q))
    for rewrite in ("leave encashment LV-07 s.53 Rs 52,000 monthly wages 45 days",
                    "lv\u201307 encashment, s.53, \u20b9\u096b\u0968,\u0966\u0966\u0966 a month, 45 days",
                    "leave encashment LV-07 s.53 Rs 52000 45 days",
                    "leave encashment LV-07 s.53 Rs 52,000 45 working days",
                    "LV-07 encashment under section 53, Rs 52,000, 45 days"):
        lost = qr.dropped(Q, rewrite)
        print(f"{'refused' if lost else 'kept':8}{rewrite}" + (f"   (dropped {', '.join(lost)})" if lost else ""))

# Original CLI workflow for step_02_offline_the_kit_s_own_tests.
COMMANDS_02 = """python -m unittest discover -s evals/tests -p test_query_rewrite.py 2>&1 | grep -E "^(Ran|OK|FAILED)" | sed -E "s/ in [0-9.]+s$//"

"""

def step_02_offline_the_kit_s_own_tests(session):
    """Run Do it, offline: the kit's own tests at this checkpoint.

    evals/tests/test_query_rewrite.py holds 20 tests that need neither a model nor a lane: the guard on the design's examples and on the golden rows, every outcome against a fake client, the request against google-genai's own config class, the line with no question text, search_query() lifted from rewrite.py with the switch off and on, and the ablation's rewrite arm and paraphrase rows against a stand-in lane. The pipe keeps the summary and drops the timing.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the kit's own tests: fakes for the model and the lane; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Ran 20 tests
    OK
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_offline_the_guard_on_the_module_s_own_exam),
        ('source_25', step_02_offline_the_kit_s_own_tests),
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
