"""Lesson 2.6: Against the gate: refusal recall, false answers, calibration, latency and rupees

All 65 rows on the author's lane, each arm held against the gate's 0.90, the false answers by id, what refusing first would save and lose, and where Jev could sit after the cohort. The author ran all 65 rows on the author's lane and saved the run. Its report is below. Every figure in this step's tables that is not the Rs 0 lane's is computed from that saved file, when this page is built, by decide.py's own summarise(), calibration(), by_confidence() and latency(). The same command runs on your lane if you want your own.

Run order inside this file:
1. Against the gate: refusal recall, false answers, calibration, latency and rupees (source window 37)

Prerequisites: demo_06_the_rule_and_the_generator_on_your_lane_s_pools.
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


# Original CLI workflow for step_01_against_the_gate_refusal_recall_false_answ.
COMMANDS_01 = """make decide PROJECT="$PROJECT" REGION="$REGION" DECIDE_ARGS="--save evals/reports/decide-live.json"

"""

def step_01_against_the_gate_refusal_recall_false_answ(session):
    """Run Against the gate: refusal recall, false answers, calibration, latency and rupees at this checkpoint.

    All 65 rows on the author's lane, each arm held against the gate's 0.90, the false answers by id, what refusing first would save and lose, and where Jev could sit after the cohort. The author ran all 65 rows on the author's lane and saved the run. Its report is below. Every figure in this step's tables that is not the Rs 0 lane's is computed from that saved file, when this page is built, by decide.py's own summarise(), calibration(), by_confidence() and latency(). The same command runs on your lane if you want your own.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (optional: all 65 rows, about Rs 17.57 of input and at most Rs 102.43 in all).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/decide_live.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_37', step_01_against_the_gate_refusal_recall_false_answ),
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
