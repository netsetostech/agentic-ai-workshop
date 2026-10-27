"""Lesson 10.1: The 11 calculator rows, scored offline and paired

Do it: check the rows, then run them One cell splits the saved runs by pattern and prints what a call of each pattern read, thought and wrote; for react_text, it also counts the replies that ran past the stop and the Actions code could not read, with the bench's own parser. Then COMPARE= pairs each pattern with the loop, row by row.

Run order inside this file:
1. Do it: check the rows, then run them (source window 33)
2. Do it: check the rows, then run them (source window 35)
3. Do it: the paired difference, at Rs 0 (source window 37)

Prerequisites: demo_06_change_it_delete_the_parser_s_cut.
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
COMMANDS_01 = """make agent-eval CHECK=1 SLICE=calc

"""

def step_01_check_the_rows_then_run_them(session):
    """Run Do it: check the rows, then run them at this checkpoint.

    Do it: check the rows, then run them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0, the standard library: every figure of the slice recomputed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ok    calc-gratuity-7y8m: gratuity_estimate(monthly_wage=52000, years=7, months=8) = Rs 2,40,000 (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3))
    ok    calc-gratuity-7y6m: gratuity_estimate(monthly_wage=52000, years=7, months=6) = Rs 2,10,000 (Code on Social Security, 2020, s.53(1), s.53(2), s.53 Explanation 3, s.53(3))
    ok    calc-gratuity-fixed-term: gratuity_estimate(monthly_wage=30000, years=1, months=5, fixed_term=True, term_expired=True) = Rs 24,519 (Code on Social Security, 2020, s.53(2), s.53 Explanation 3, s.53(2) third proviso, s.53(1) second proviso, s.53(3))
    ok    calc-carry-forward: carry_forward(days=34, cap=30) = 30 days (LV-01)
    ok    calc-carry-fo
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_check_the_rows_then_run_them.
COMMANDS_02 = """make agent-eval OFFLINE=1 PATTERNS=loop,react_text,plan_first SLICE=calc SAVE="$HOME/bench-101-offline.jsonl"

"""

def step_02_check_the_rows_then_run_them(session):
    """Run Do it: check the rows, then run them at this checkpoint.

    Do it: check the rows, then run them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: 33 scripted turns, a few minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 11 rows, 3 arms, 1 run each, in this process (--inproc)
    saved 33 runs to /home/you/bench-101-offline.jsonl: --replay rescores them at Rs 0
    == loop, thinking default (low), desk astar: 11 rows x 1 run
      row                          kind    correct provenance calls thinking visible       Rs  why, first run
      calc-gratuity-7y8m           calc        yes         no   2.0      128      31   0.4324  no gratuity_estimate call returned it; unsupported: 2,40,000
      calc-gratuity-7y6m           calc        yes        yes   3.0      192      48   0.8499  
      calc-gratuity-fixed-term     calc        yes
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_paired_difference_at_rs_0.
COMMANDS_03 = """export SAVED="$HOME/bench-101-offline.jsonl"
python - <<'PY'
import json, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "commands"]
import agent_patterns as ap      # the standard library and shared/ only, at import: read_step() is the bench's own parser

saved, home = os.environ["SAVED"], os.path.expanduser("~")
runs = [json.loads(line) for line in open(saved, encoding="utf-8") if line.strip()]
print(f"{len(runs)} runs in {saved.replace(home, '~')}")
for pattern in [p for p in ap.PATTERNS if any(r["arm"]["pattern"] == p for r in runs)]:
    mine = [r for r in runs if r["arm"]["pattern"] == pattern]
    calls = [c for r in mine for c in r["calls"] if not c.get("error")]
    out = saved[:-len(".jsonl")] + f"-{pattern}.jsonl"
    with open(out, "w", encoding="utf-8", newline="\\n") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\\n" for r in mine)
    n = max(len(calls), 1)
    line = (f"{pattern:<10} {len(mine)} runs, {len(calls)} calls; a call reads {sum(c['tokens_in'] for c in calls) / n:,.0f}, "
            f"thinks {sum(c['thinking_tokens'] for c in calls) / n:,.0f}, writes {sum(c['visible_tokens'] for c in calls) / n:,.0f}; "
            f"Rs {sum(r['inr'] for r in mine):.2f} in all")
    if ap.PATTERNS[pattern].text:
        past = sum(ap.STOP in (c.get("text") or "") for c in calls)
        unread = sum("error" in ap.read_step(c.get("text") or "") for c in calls)
        line += f"; {past} replies ran past the stop, {unread} format errors"
    print(line)
PY
make agent-eval COMPARE="${SAVED%.jsonl}-loop.jsonl ${SAVED%.jsonl}-react_text.jsonl"
make agent-eval COMPARE="${SAVED%.jsonl}-loop.jsonl ${SAVED%.jsonl}-plan_first.jsonl"

"""

def step_03_the_paired_difference_at_rs_0(session):
    """Run Do it: the paired difference, at Rs 0 at this checkpoint.

    One cell splits the saved runs by pattern and prints what a call of each pattern read, thought and wrote; for react_text, it also counts the replies that ran past the stop and the Actions code could not read, with the bench's own parser. Then COMPARE= pairs each pattern with the loop, row by row.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the saved runs split by pattern, then paired).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 33 runs in ~/bench-101-offline.jsonl
    loop       11 runs, 31 calls; a call reads 1,569, thinks 64, writes 14; Rs 7.75 in all
    react_text 11 runs, 31 calls; a call reads 2,881, thinks 64, writes 33; Rs 13.31 in all; 0 replies ran past the stop, 0 format errors
    plan_first 11 runs, 31 calls; a call reads 1,656, thinks 64, writes 31; Rs 8.42 in all
    == /home/you/bench-101-offline-react_text.jsonl (react_text, thinking default (low), desk astar) against /home/you/bench-101-offline-loop.jsonl (loop, thinking default (low), desk astar), each row's first run, Rs 0
      paired (correct), 11 rows: both 11, loop only 0, react_text only 0, neither 0
      react_text - loop = +0.0 points, 95% [-25.9, +25.9] (Newco
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_33', step_01_check_the_rows_then_run_them),
        ('source_35', step_02_check_the_rows_then_run_them),
        ('source_37', step_03_the_paired_difference_at_rs_0),
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
