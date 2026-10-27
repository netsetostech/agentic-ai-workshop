"""Lesson 8.4: Evals: a change is a release, and the check that cannot fail

Do it: the gate offline, and what moves with a document

Run order inside this file:
1. Do it: the gate offline, and what moves with a document (source window 51)

Prerequisites: demo_07_cost_standing_still_staying_fresh_and_one_change_at_1k_100k_and_10m_documents.
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


# Original CLI workflow for step_01_the_gate_offline_and_what_moves_with_a_doc.
COMMANDS_01 = """python evals/run_eval.py
python - <<'PY'
import sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = ["evals"]
from run_eval import check_anchors, in_scope, load_corpus, load_golden, load_required, THRESHOLDS
golden, corpus, required = load_golden(), load_corpus(), set(load_required())
scope = [r["id"] for r in golden if in_scope(r, "hr_policy_2026.md", corpus)]
print(f"make eval-live SOURCE=hr_policy_2026.md sends {len(scope)} of {len(golden)} rows: {', '.join(scope)}")
for r in golden:
    if r["shape"] == "version":
        demo = open("evals/demo/hr_policy_2026_v2.md", encoding="utf-8").read()
        print(f"{r['id']} ({'required' if r['id'] in required else 'optional'}): must not say {r['must_not_contain']}, which only "
              f"revision 2 holds ({r['must_not_contain'][0] in demo}); re-issue the handbook and this row moves with it, in one commit")
print(f"anchors over whole documents: {len(check_anchors(golden, corpus))} problems - it reads files and never a chunk, "
      f"so no chunker change and no carry-over bug can turn it red")
print(f"what blocks live: {len(THRESHOLDS)} thresholds and {len(required)} required rows; must_retrieve recall is printed as [info]")
PY

"""

def step_01_the_gate_offline_and_what_moves_with_a_doc(session):
    """Run Do it: the gate offline, and what moves with a document at this checkpoint.

    Do it: the gate offline, and what moves with a document

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the offline gate, then a Python cell; Rs 0: no credential, no call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == eval gate: OFFLINE (no credentials, no cost) ==
      65 golden rows over 3 tenants, 27 documents

      [PASS] falsifiable
      [PASS] anchors
      [PASS] coverage

      The golden set is sound. It can go red, and it still contains the rows that would.
    make eval-live SOURCE=hr_policy_2026.md sends 10 of 65 rows: lk-01, lk-02, lk-03, lk-04, lk-05, lk-06, lk-07, lk-08, lk-09, vr-01
    vr-01 (required): must not say ['90 days'], which only revision 2 holds (True); re-issue the handbook and this row moves with it, in one commit
    anchors over whole documents: 0 problems - it reads files and never a chunk, so no chunker change and no carry-over bug can turn it red
    what blocks live: 9 thresholds and 15 required row
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_51', step_01_the_gate_offline_and_what_moves_with_a_doc),
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
