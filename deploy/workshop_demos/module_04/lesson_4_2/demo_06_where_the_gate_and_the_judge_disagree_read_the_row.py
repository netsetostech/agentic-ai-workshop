"""Lesson 4.2: Where the gate and the judge disagree: read the row

Four ways the two can meet, and the gate's misses read against the judge's answers. judge.py prints its summary and writes no per-row ratings, so "read the row" means reading the answers. The cell takes each row the gate failed and prints what the judge's own collection received for it.

Run order inside this file:
1. Where the gate and the judge disagree: read the row (source window 35)

Prerequisites: demo_05_the_judge_the_lane_s_own_answers_read_with_the_context_they_cite.
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


def step_01_where_the_gate_and_the_judge_disagree_read(session):
    """Run Where the gate and the judge disagree: read the row at this checkpoint.

    Four ways the two can meet, and the gate's misses read against the judge's answers. judge.py prints its summary and writes no per-row ratings, so "read the row" means reading the answers. The cell takes each row the gate failed and prints what the judge's own collection received for it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads both files; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 2 row(s) cost the gate a point. The judge's own run answered them:
      jn-06  gate: answered without ['EMEA', '11.4']
             judge's answer: 'EMEA revenue fell in FY2026 [1].', 1 cited
             EMEA present; 11.4 absent
      lk-27  gate: refused
             judge's answer: 'The documents do not say.', 0 cited
             twenty per cent absent
    """
    import json, sys; sys.path.insert(0, "evals")
    from run_eval import contains
    gate = json.load(open("evals/reports/lesson72.json", encoding="utf-8"))["records"]
    judged = {x["id"]: x for x in json.load(open("evals/reports/judge72.json", encoding="utf-8"))}
    missed = [x for x in gate if not x["pass"]]
    print(f"{len(missed)} row(s) cost the gate a point. The judge's own run answered them:")
    for x in missed:
        j = judged.get(x["id"], {})
        figs = [f"{w} {'present' if contains(j.get('response', ''), w) else 'absent'}" for w in j.get("must_contain", [])]
        print(f"  {x['id']:6} gate: {x['why'] or x['outcome']}")
        print(f"         judge's answer: {j.get('response', '')[:80]!r}, {len(j.get('cited') or [])} cited")
        print(f"         {'; '.join(figs) or 'a refusal row: no figure to look for'}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_35', step_01_where_the_gate_and_the_judge_disagree_read),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
