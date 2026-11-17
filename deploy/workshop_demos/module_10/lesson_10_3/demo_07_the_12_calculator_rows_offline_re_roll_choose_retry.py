"""Lesson 10.3: The 12 calculator rows offline: re-roll, choose, retry

Do it: check the rows, then run them Do it: side by side, at Rs 0 Each saved run is one JSON line, the turn's record. A verify run's record carries every attempt, with the note it started from and the figures that note writes. The cell rescores every run with the eval's own functions and prints, row by row, the check's verdict on each of the loop's runs, the run best-of-3 ships, verify's attempts, and each note.

Run order inside this file:
1. Do it: check the rows, then run them (source window 33)
2. Do it: check the rows, then run them (source window 35)
3. Do it: check the rows, then run them (source window 37)
4. Do it: side by side, at Rs 0 (source window 39)
5. Do it: the saved runs, read back (source window 41)

Prerequisites: demo_06_change_it_put_the_notes_into_the_question.
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
COMMANDS_01 = """make agent-eval CHECK=1 SLICE=calc,trap

"""

def step_01_check_the_rows_then_run_them(session):
    """Run Do it: check the rows, then run them at this checkpoint.

    Do it: check the rows, then run them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0, the standard library: every figure of the 12 rows recomputed).
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
COMMANDS_02 = """make agent-eval OFFLINE=1 PATTERNS=loop SLICE=calc,trap RUNS=3 SAVE="$HOME/plain-offline.jsonl"

"""

def step_02_check_the_rows_then_run_them(session):
    """Run Do it: check the rows, then run them at this checkpoint.

    Do it: check the rows, then run them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the loop, three scripted runs a row, saved).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 12 rows, 1 arm, 3 runs each, in this process (--inproc)
    saved 36 runs to /home/you/plain-offline.jsonl: --replay rescores them at Rs 0
    == loop, thinking default (low), desk astar: 12 rows x 3 runs
      row                          kind    correct provenance calls thinking visible       Rs  why, first run
      calc-gratuity-7y8m           calc        3/3        2/3   2.7      171      42   0.7082  no gratuity_estimate call returned it; unsupported: 2,40,000
      calc-gratuity-7y6m           calc        3/3        2/3   2.7      171      42   0.7116  
      calc-gratuity-fixed-term     calc        3/3   
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_check_the_rows_then_run_them.
COMMANDS_03 = """make agent-eval OFFLINE=1 PATTERNS=verify SLICE=calc,trap SAVE="$HOME/verify-offline.jsonl"

"""

def step_03_check_the_rows_then_run_them(session):
    """Run Do it: check the rows, then run them at this checkpoint.

    Do it: check the rows, then run them

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: verify, one scripted run a row, saved).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: OFFLINE: the scripted model and the kit's corpus, no credential, no cost; every count is the script's | 12 rows, 1 arm, 1 run each, in this process (--inproc)
    saved 12 runs to /home/you/verify-offline.jsonl: --replay rescores them at Rs 0
    == verify, thinking default (low), desk astar: 12 rows x 1 run
      row                          kind    correct provenance calls thinking visible       Rs  why, first run
      calc-gratuity-7y8m           calc        yes        yes   6.0      384     137   1.4703  
      calc-gratuity-7y6m           calc        yes        yes   3.0      192      48   0.8499  
      calc-gratuity-fixed-term     calc        yes        yes   3.0      192      54   0.8982  
      calc-carry-for
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_side_by_side_at_rs_0.
COMMANDS_04 = """make agent-eval REPLAY="$HOME/plain-offline.jsonl $HOME/verify-offline.jsonl" BEST_OF=3 | sed -n '1p;/^  paired (correct)/,$p'

"""

def step_04_side_by_side_at_rs_0(session):
    """Run Do it: side by side, at Rs 0 at this checkpoint.

    Do it: side by side, at Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: the two saves side by side; the first line, then what the two reports above do not print).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: replayed 48 saved runs of /home/you/plain-offline.jsonl, /home/you/verify-offline.jsonl: rescored at Rs 0, no model call (they cost Rs 34.4720 when they ran; offline, the script)
      paired (correct), 12 rows: both 12, loop only 0, verify only 0, neither 0
      verify - loop = +0.0 points, 95% [-24.3, +24.3] (Newcombe), exact McNemar p = 1.000
      no conclusion at this many rows: the interval crosses the margin (margin 3 points, registered 2026-10-08); indicative: the task set's model-written rows, one run each
      paired (verified), 12 rows: both 9, loop only 0, verify only 1, neither 2
      verify - loop = +8.3 points, 95% [-10.3, +28.7] (Newcombe), exact McNemar p = 1.000
      no conclusion at this many
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def step_05_the_saved_runs_read_back(session):
    """Run Do it: the saved runs, read back at this checkpoint.

    Each saved run is one JSON line, the turn's record. A verify run's record carries every attempt, with the note it started from and the figures that note writes. The cell rescores every run with the eval's own functions and prints, row by row, the check's verdict on each of the loop's runs, the run best-of-3 ships, verify's attempts, and each note.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: the saved runs read back, row by row).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: calc-gratuity-7y8m
      loop runs: check fail/pass/pass, verified no/yes/yes; best-of-3 ships run 2
      verify: check fail -> pass; ships attempt 2, verified yes
        the note before attempt 2: My answer stated a figure that no calculator of that turn returned. Next time: search first, call gratuity_estimate with the numbers the question and the passages state, and state only the figures it returns, citing their passages.
        figures it writes: none
    calc-gratuity-7y6m
      loop runs: check pass/pass/fail, verified yes/yes/no; best-of-3 ships run 1
      verify: check pass; ships attempt 1, verified yes
    calc-gratuity-fixed-term
      loop runs: check pass/pass/pass, verified yes/yes/yes; best-of-3 ships run 1
    """
    import json, os, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["evals", "commands", "."]
    import agent_eval as ae          # the scorer, the figure check and best-of: the standard library and shared/ only
    
    SAVED = ["~/plain-offline.jsonl", "~/verify-offline.jsonl"]      # the files make agent-eval's SAVE= wrote
    rows = {r["id"]: r for r in ae.load_tasks()}
    runs = [json.loads(line) for name in SAVED for line in open(os.path.expanduser(name), encoding="utf-8") if line.strip()]
    word = {True: "pass", False: "fail"}
    for rid in dict.fromkeys(r["row"] for r in runs):
        loop = sorted((r for r in runs if r["row"] == rid and r["arm"]["pattern"] == "loop"), key=lambda r: r["run"])
        ver = next((r for r in runs if r["row"] == rid and r["arm"]["pattern"] == "verify"), None)
        print(rid)
        if loop:
            good = ["yes" if ae.passed(ae.score(rows[rid], r), "verified") else "no" for r in loop]
            print(f"  loop runs: check {'/'.join(word[ae.passes(r)] for r in loop)}, verified {'/'.join(good)}; "
                  f"best-of-{len(loop)} ships run {ae.best_of(loop, len(loop))['run'] + 1}")
        if ver:
            good = "yes" if ae.passed(ae.score(rows[rid], ver), "verified") else "no"
            print(f"  verify: check {' -> '.join(word[a['check']['passed']] for a in ver['attempts'])}; "
                  f"ships attempt {ver['shipped']}, verified {good}")
            for a in ver["attempts"][1:]:
                print(f"    the note before attempt {a['n']}: {a['note'] or '(none: the reflect call wrote nothing)'}")
                print(f"    figures it writes: {', '.join(a['note_figures']) or 'none'}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_33', step_01_check_the_rows_then_run_them),
        ('source_35', step_02_check_the_rows_then_run_them),
        ('source_37', step_03_check_the_rows_then_run_them),
        ('source_39', step_04_side_by_side_at_rs_0),
        ('source_41', step_05_the_saved_runs_read_back),
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
