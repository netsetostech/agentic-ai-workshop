"""Lesson 4.2: The live half: every row, two identities, nine rates, three exit codes

Do it: the live gate, with a report Now take the report apart. The cell recounts the four rates whose denominators people misread, from the report's own rows, then prints all nine with their verdicts and the rows that cost a point. Now take the report apart. The cell recounts the four rates whose denominators people misread, from the report's own rows, then prints all nine with their verdicts and the rows that cost a point. Last, what the run cost. The API priced every answer on its usage row; make usage groups the last hour of those rows. Run it straight after the gate, before step 5 asks the lane again.

Run order inside this file:
1. Do it: the live gate, with a report (source window 18)
2. Do it: the live gate, with a report (source window 20)
3. Do it: the live gate, with a report (source window 22)

Prerequisites: demo_03_the_offline_half_on_every_push_and_ci_s_verdict_on_the_commit_you_run.
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


def step_01_the_live_gate_with_a_report(session):
    """Run Do it: the live gate, with a report at this checkpoint.

    Do it: the live gate, with a report

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every row as the member, every isolation row as the outsider: about ten minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://documind-api-NUMBER.asia-south1.run.app
    == eval gate: LIVE ==
      65 rows (47 answerable, 18 not) against https://documind-api-NUMBER.asia-south1.run.app

      [PASS] request_success_rate  100.0%  (threshold 100%; 65 rows)
      [PASS] answerable_rate        97.9%  (threshold 80%; 47 rows)
      [PASS] citation_rate         100.0%  (threshold 95%; 46 rows)
      [PASS] citation_valid_rate   100.0%  (threshold 100%; 46 rows)
      [PASS] must_contain_rate      97.8%  (threshold 85%; 46 rows)
      [PASS] correct_rate           95.7%  (threshold 68%; 47 rows)
      [PASS] refusal_rate          100.0%  (threshold 90%; 18 rows)
      [PASS] media_kind_rate       100.0%  (threshold 80%; 3 rows)
      [PASS] isolation_403_
    """
    from workshop_helpers.gates import live_gate
    live_gate(session, report="evals/reports/lesson72.json")

def step_02_the_live_gate_with_a_report(session):
    """Run Do it: the live gate, with a report at this checkpoint.

    Now take the report apart. The cell recounts the four rates whose denominators people misread, from the report's own rows, then prints all nine with their verdicts and the rows that cost a point.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the report; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: answerable_rate    46 answered          of 47 answerable rows
      must_contain_rate  45 with the figure   of 46 ANSWERED
      correct_rate       45 right             of 47 ANSWERABLE
      refusal_rate       18 refused           of 18 unanswerable rows
      pass  request_success_rate  100.0%  (needs 100%)
      pass  answerable_rate        97.9%  (needs 80%)
      pass  citation_rate         100.0%  (needs 95%)
      pass  citation_valid_rate   100.0%  (needs 100%)
      pass  must_contain_rate      97.8%  (needs 85%)
      pass  correct_rate           95.7%  (needs 68%)
      pass  refusal_rate          100.0%  (needs 90%)
      pass  media_kind_rate       100.0%  (needs 80%)
      pass  isolation_403_rate    100.0%  (needs 100%)
      c
    """
    import json
    r = json.load(open("evals/reports/lesson72.json", encoding="utf-8"))
    gold = {g["id"]: g for g in map(json.loads, open("evals/golden.jsonl", encoding="utf-8"))}
    rec = r["records"]
    A = [x for x in rec if gold[x["id"]]["answerable"]]
    answered = [x for x in A if x["outcome"] == "ok" and x["answerable"]]
    contained = [x for x in answered if not x["why"].startswith("answered without")]
    U = [x for x in rec if not gold[x["id"]]["answerable"]]
    refused = [x for x in U if x["outcome"] == "ok" and not x["answerable"]]
    print(f"  answerable_rate    {len(answered):2} answered          of {len(A)} answerable rows")
    print(f"  must_contain_rate  {len(contained):2} with the figure   of {len(answered)} ANSWERED")
    print(f"  correct_rate       {sum(x['pass'] for x in A):2} right             of {len(A)} ANSWERABLE")
    print(f"  refusal_rate       {len(refused):2} refused           of {len(U)} unanswerable rows")
    for k, v in r["scores"].items():
        verdict = "FAIL" if k in r["failed"] else "pass" if k in r["judged"] else " -- "
        print(f"  {verdict}  {k:21} {v:6.1%}  (needs {r['thresholds'][k]:.0%})")
    print("  cost a point:", ", ".join(f"{x['id']} ({x['why'] or x['outcome']})" for x in rec if not x["pass"]) or "nothing")

# Original CLI workflow for step_03_the_live_gate_with_a_report.
COMMANDS_03 = """make usage PROJECT="$PROJECT" HOURS=1 | sed -n '1,8p'

"""

def step_03_the_live_gate_with_a_report(session):
    """Run Do it: the live gate, with a report at this checkpoint.

    Now take the report apart. The cell recounts the four rates whose denominators people misread, from the report's own rows, then prints all nine with their verdicts and the rows that cost a point. Last, what the run cost. The API priced every answer on its usage row; make usage groups the last hour of those rows. Run it straight after the gate, before step 5 asks the lane again.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the usage rows of the last hour, priced).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 65 answers from documind-api in the last 1 h; USD_INR=85

    by tenant
    tenant                 answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ----------------------------------------------------------------------------------
    acme                        47       ...      ...       ...       ...     ...    ...
    zeta                        10       ...      ...       ...       ...     ...    ...
    globex                       8       ...      ...       ...       ...     ...    ...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_the_live_gate_with_a_report),
        ('source_20', step_02_the_live_gate_with_a_report),
        ('source_22', step_03_the_live_gate_with_a_report),
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
