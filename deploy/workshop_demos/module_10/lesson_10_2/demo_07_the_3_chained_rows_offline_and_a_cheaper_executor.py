"""Lesson 10.2: The 3 chained rows offline, and a cheaper executor

Do it: check the rows, then run them Do it: a flash-lite executor Each saved run is one JSON line: make agent-turn's record of the turn, with its plan and its roles. The cell prints each run's calls and rupees by role, and what its plan did: a replan and why, or the waves.

Run order inside this file:
1. Do it: check the rows, then run them (source window 34)
2. Do it: check the rows, then run them (source window 36)
3. Do it: a flash-lite executor (source window 38)
4. Do it: the saved runs, read back (source window 40)

Prerequisites: demo_06_change_it_switch_the_replan_off.
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


# Original CLI workflow for step_01_check_the_rows_then_run_them.
COMMANDS_01 = """make agent-eval CHECK=1 SLICE=chained

"""

def step_01_check_the_rows_then_run_them(session):
    """Run Do it: check the rows, then run them at this checkpoint.

    Do it: check the rows, then run them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0, the standard library: every figure of the three rows recomputed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ok    chained-exit-e3: notice_end(ack_date=2026-10-05, days=60) = 2026-12-04 (NP-03); encashable_days(balance=50, cap=45) = 45 days (LV-07); gratuity_estimate(monthly_wage=52000, years=7, months=8) = Rs 2,40,000 (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3))
    ok    chained-exit-saturday: notice_end(ack_date=2026-10-06, days=60) = 2026-12-05 (NP-03); encashable_days(balance=80, cap=45) = 45 days (LV-07); gratuity_estimate(monthly_wage=52000, years=7, months=6) = Rs 2,10,000 (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3))
    ok    chained-exit-stated-cap: notice_end(ack_date=2026-10-05, days=60) = 2026-12-04 (NP-03); encashable_days(ba
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_check_the_rows_then_run_them.
COMMANDS_02 = """make agent-eval OFFLINE=1 PATTERNS=loop,plan_execute,rewoo SLICE=chained SAVE="$HOME/plans-offline.jsonl"

"""

def step_02_check_the_rows_then_run_them(session):
    """Run Do it: check the rows, then run them at this checkpoint.

    Do it: check the rows, then run them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: 9 scripted turns, about a minute).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 3 rows, 3 arms, 1 run each, in this process (--inproc)
    saved 9 runs to /home/you/plans-offline.jsonl: --replay rescores them at Rs 0
    == loop, thinking default (low), desk astar: 3 rows x 1 run
      row                          kind    correct provenance calls thinking visible       Rs  why, first run
      chained-exit-e3              chained     yes        yes   7.0      448     126   3.7366  
      chained-exit-saturday        chained     yes        yes   7.0      448     126   3.7373  
      chained-exit-stated-cap      chained     yes        yes   7.0      448     126   3.7474  
      first runs: correct
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_a_flash_lite_executor.
COMMANDS_03 = """make agent-eval OFFLINE=1 PATTERNS=plan_execute,rewoo SLICE=chained EXEC_MODEL=gemini-3.1-flash-lite SAVE="$HOME/plans-lite-offline.jsonl"

"""

def step_03_a_flash_lite_executor(session):
    """Run Do it: a flash-lite executor at this checkpoint.

    Do it: a flash-lite executor

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the two planning patterns with a flash-lite executor).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's; an executor on gemini-3.1-flash-lite | 3 rows, 2 arms, 1 run each, in this process (--inproc)
    saved 6 runs to /home/you/plans-lite-offline.jsonl: --replay rescores them at Rs 0
    == plan_execute, thinking default (low), desk astar, executor gemini-3.1-flash-lite: 3 rows x 1 run
      row                          kind    correct provenance calls thinking visible       Rs  why, first run
      chained-exit-e3              chained     yes        yes   8.0      512     276   1.5005  
      chained-exit-saturday        chained     yes        yes   8.0      512     276   1.5007  
      chained-exit-stated-cap     
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def step_04_the_saved_runs_read_back(session):
    """Run Do it: the saved runs, read back at this checkpoint.

    Each saved run is one JSON line: make agent-turn's record of the turn, with its plan and its roles. The cell prints each run's calls and rupees by role, and what its plan did: a replan and why, or the waves.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: the saved runs read back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ~/plans-offline.jsonl: 9 runs
      chained-exit-e3          loop                                 7 calls, Rs 3.74
      chained-exit-saturday    loop                                 7 calls, Rs 3.74
      chained-exit-stated-cap  loop                                 7 calls, Rs 3.75
      chained-exit-e3          plan_execute                         8 calls, Rs 2.44 | plan 1, Rs 0.34; act 6, Rs 1.14; solve 1, Rs 0.96
      chained-exit-saturday    plan_execute                         8 calls, Rs 2.44 | plan 1, Rs 0.34; act 6, Rs 1.14; solve 1, Rs 0.96
      chained-exit-stated-cap  plan_execute                        10 calls, Rs 3.04 | plan 1, Rs 0.33; act 7, Rs 1.36; replan 1, Rs 0.38; solve 1, Rs 0.97
          rep
    """
    import json, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    SAVED = ["~/plans-offline.jsonl", "~/plans-lite-offline.jsonl"]      # the files make agent-eval's SAVE= wrote
    for name in SAVED:
        runs = [json.loads(line) for line in open(os.path.expanduser(name), encoding="utf-8") if line.strip()]
        print(f"{name}: {len(runs)} runs")
        for r in runs:
            arm, plan = r["arm"]["pattern"] + (" on " + r["arm"]["executor"] if r["arm"].get("executor") else ""), r.get("plan") or {}
            roles = "; ".join(f"{k} {v['calls']}, Rs {v['inr']:.2f}" for k, v in (r.get("roles") or {}).items())
            print(f"  {r['row']:<24} {arm:<35} {r['model_calls']:>2} calls, Rs {r['inr']:.2f}" + (f" | {roles}" if roles else ""))
            for e in plan.get("log") or ():
                if e["event"] == "replan":
                    print(f"      replanned after: {e['why'][:100]}")
                if e["event"] == "stop":
                    print(f"      stopped by its limits before its {e['before']} call")
            if plan.get("refused"):
                print(f"      refused before any tool ran: {plan['refused'][:100]}")
            if plan.get("waves"):
                print("      waves: " + " | ".join(", ".join(w) for w in plan["waves"]))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_check_the_rows_then_run_them),
        ('source_36', step_02_check_the_rows_then_run_them),
        ('source_38', step_03_a_flash_lite_executor),
        ('source_40', step_04_the_saved_runs_read_back),
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
