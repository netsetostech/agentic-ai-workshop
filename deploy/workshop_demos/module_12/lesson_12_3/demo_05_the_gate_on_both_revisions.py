"""Lesson 12.3: The gate on both revisions

Do it

Run order inside this file:
1. Do it (source window 16)
2. Do it (source window 18)

Prerequisites: demo_04_the_candidate_audited.
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


def step_01_the_gate_on_both_revisions(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every golden row, on each revision: about twenty minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: report: /home/YOU/base173.json
      All thresholds met.
    >> https://candidate---documind-api-NUMBER.asia-south1.run.app
      65 rows (47 answerable, 18 not) against https://candidate---documind-api-NUMBER.asia-south1.run.app

      [PASS] request_success_rate  100.0%  (threshold 100%; 65 rows)
      [PASS] answerable_rate        97.9%  (threshold 80%; 47 rows)
      [PASS] citation_rate         100.0%  (threshold 95%; 46 rows)
      [PASS] citation_valid_rate   100.0%  (threshold 100%; 46 rows)
      [PASS] must_contain_rate      95.7%  (threshold 85%; 46 rows)
      [PASS] correct_rate           93.6%  (threshold 68%; 47 rows)
      [PASS] refusal_rate          100.0%  (threshold 90%; 18 rows)
      [PASS] media_kind_rate       
    """
    import os
    from pathlib import Path
    from workshop_helpers.gates import live_gate
    live_gate(session, report=Path.home() / "base173.json")
    live_gate(session, report=Path.home() / "cand173.json", api=os.environ["CAND"])

def step_02_the_gate_on_both_revisions(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the two reports).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: live  candidate  needs
      request_success_rate   100.0%     100.0%   100%
      answerable_rate         97.9%      97.9%    80%
      citation_rate          100.0%     100.0%    95%
      citation_valid_rate    100.0%     100.0%   100%
      must_contain_rate       97.8%      95.7%    85%
      correct_rate            95.7%      93.6%    68%
      refusal_rate           100.0%     100.0%    90%
      media_kind_rate        100.0%     100.0%    80%
      isolation_403_rate     100.0%     100.0%   100%
      jn-03: pass on live, fail on the candidate (answered without ['45', '60'])
      jn-06: fail on live, pass on the candidate (ok)
      jn-09: pass on live, fail on the candidate (answered without ['8.33', 'twenty per cent'])
      3 row(
    """
    import json, os
    base, cand = (json.load(open(os.path.expanduser(f"~/{n}173.json"), encoding="utf-8")) for n in ("base", "cand"))
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
        ('source_16', step_01_the_gate_on_both_revisions),
        ('source_18', step_02_the_gate_on_both_revisions),
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
