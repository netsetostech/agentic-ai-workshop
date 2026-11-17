"""Lesson 10.2: The 3 rows on your lane, and the plans they saved

The same two commands as step 7 without OFFLINE=1: every chained row through the loop, plan-and-execute and ReWOO once each, then the two planning patterns again with a flash-lite executor, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in. Do it: rescore the saved runs, at Rs 0 The same cell as step 7, on your lane's saved runs.

Run order inside this file:
1. Definition (source window 51)
2. Definition (source window 53)
3. Do it: rescore the saved runs, at Rs 0 (source window 55)
4. Do it: read the plans back, at Rs 0 (source window 57)

Prerequisites: demo_08_your_lane_plan_and_execute_rewoo_and_a_flash_lite_executor.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=loop,plan_execute,rewoo SLICE=chained SAVE="$HOME/plans.jsonl"

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    The same two commands as step 7 without OFFLINE=1: every chained row through the loop, plan-and-execute and ReWOO once each, then the two planning patterns again with a flash-lite executor, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (9 live turns, about Rs 27.85 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_plans.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_definition.
COMMANDS_02 = """make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=plan_execute,rewoo SLICE=chained EXEC_MODEL=gemini-3.1-flash-lite SAVE="$HOME/plans_lite.jsonl"

"""

def step_02_definition(session):
    """Run Definition at this checkpoint.

    The same two commands as step 7 without OFFLINE=1: every chained row through the loop, plan-and-execute and ReWOO once each, then the two planning patterns again with a flash-lite executor, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes, and the report comes when every run is in.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (6 live turns, about Rs 8.75 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_lite.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_rescore_the_saved_runs_at_rs_0.
COMMANDS_03 = """make agent-eval REPLAY="$HOME/plans.jsonl"

"""

def step_03_rescore_the_saved_runs_at_rs_0(session):
    """Run Do it: rescore the saved runs, at Rs 0 at this checkpoint.

    Do it: rescore the saved runs, at Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the saved runs rescored, no model call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/replay.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def step_04_read_the_plans_back_at_rs_0(session):
    """Run Do it: read the plans back, at Rs 0 at this checkpoint.

    The same cell as step 7, on your lane's saved runs.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: your lane's saved runs read back).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/plans_read.txt]
    """
    import json, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    SAVED = ["~/plans.jsonl", "~/plans_lite.jsonl"]      # the files make agent-eval's SAVE= wrote
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
        ('source_51', step_01_definition),
        ('source_53', step_02_definition),
        ('source_55', step_03_rescore_the_saved_runs_at_rs_0),
        ('source_57', step_04_read_the_plans_back_at_rs_0),
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
