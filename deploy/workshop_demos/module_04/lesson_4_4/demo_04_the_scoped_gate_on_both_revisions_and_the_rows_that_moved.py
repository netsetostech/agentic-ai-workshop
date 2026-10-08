"""Lesson 4.4: The scoped gate on both revisions, and the rows that moved

Do it: the gate on the live revision, then on the candidate Now set the two reports side by side: each judged threshold on both revisions, every row whose verdict changed, and the median round trip of each.

Run order inside this file:
1. Do it: the gate on the live revision, then on the candidate (source window 14)
2. Do it: the gate on the live revision, then on the candidate (source window 16)

Prerequisites: demo_03_the_candidate_a_new_revision_with_no_traffic_and_the_proof_that_one_setting_diff.
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


def step_01_the_gate_on_the_live_revision_then_on_the(session):
    """Run Do it: the gate on the live revision, then on the candidate at this checkpoint.

    Do it: the gate on the live revision, then on the candidate

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the 10 rows that cite the handbook, on each revision: a few minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://documind-api-NUMBER.asia-south1.run.app

      report: evals/reports/base73.json
      All thresholds met.
    >> https://candidate---documind-api-NUMBER.asia-south1.run.app
    == eval gate: LIVE ==
      scoped to hr_policy_2026.md: 10 row(s) cite it
      10 rows (10 answerable, 0 not) against https://candidate---documind-api-NUMBER.asia-south1.run.app

      [PASS] request_success_rate  100.0%  (threshold 100%; 10 rows)
      [PASS] answerable_rate       100.0%  (threshold 80%; 10 rows)
      [PASS] citation_rate         100.0%  (threshold 95%; 10 rows)
      [PASS] citation_valid_rate   100.0%  (threshold 100%; 10 rows)
      [PASS] must_contain_rate      90.0%  (threshold 85%; 10 rows)
      [PASS] correct_rate           
    """
    import os
    from workshop_helpers.gates import live_gate
    live_gate(session, report="evals/reports/base73.json", source="hr_policy_2026.md")
    live_gate(session, report="evals/reports/cand73.json", source="hr_policy_2026.md", api=os.environ["CAND"])

def step_02_the_gate_on_the_live_revision_then_on_the(session):
    """Run Do it: the gate on the live revision, then on the candidate at this checkpoint.

    Now set the two reports side by side: each judged threshold on both revisions, every row whose verdict changed, and the median round trip of each.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the two reports; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: live  candidate  needs
      request_success_rate   100.0%     100.0%   100%
      answerable_rate        100.0%     100.0%    80%
      citation_rate          100.0%     100.0%    95%
      citation_valid_rate    100.0%     100.0%   100%
      must_contain_rate      100.0%      90.0%    85%
      correct_rate           100.0%      90.0%    68%
      lk-04: pass on live, fail on the candidate (answered without ['15'])
      1 row(s) changed verdict; median round trip ... ms live, ... ms candidate
    """
    import json
    base, cand = (json.load(open(f"evals/reports/{n}73.json", encoding="utf-8")) for n in ("base", "cand"))
    print(f"  {'':21} {'live':>7} {'candidate':>10}  {'needs':>5}")
    for k in base["scores"]:
        if k in base["judged"] or k in cand["judged"]:
            flag = "  FAIL" if k in cand["failed"] else ""
            print(f"  {k:21} {base['scores'][k]:7.1%} {cand['scores'][k]:10.1%}  {base['thresholds'][k]:5.0%}{flag}")
    was = {r["id"]: r["pass"] for r in base["records"]}
    moved = [r for r in cand["records"] if was.get(r["id"]) != r["pass"]]
    for r in moved:
        print(f"  {r['id']}: {'pass' if was.get(r['id']) else 'fail'} on live, {'pass' if r['pass'] else 'fail'} on the candidate ({r['why'] or r['outcome']})")
    med = lambda rep: sorted(x["latency_ms"] for x in rep["records"])[len(rep["records"]) // 2]
    print(f"  {len(moved)} row(s) changed verdict; median round trip {med(base)} ms live, {med(cand)} ms candidate")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_14', step_01_the_gate_on_the_live_revision_then_on_the),
        ('source_16', step_02_the_gate_on_the_live_revision_then_on_the),
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
