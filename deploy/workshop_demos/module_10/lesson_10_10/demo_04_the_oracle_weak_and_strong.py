"""Lesson 10.10: The oracle, weak and strong

With no arguments, make ralph-check judges all 8 versions under both oracles, and holds each verdict to the label seeds.json gives it. SHOW= adds one version's diff and its failed checks. The oracle's docstring names the change to try: delete the strong oracle's sweep over 2026. The cell copies oracle.py to a scratch directory without the sweep's two lines, then runs that copy on three versions, each spliced into the kit's own file as the loop does it.

Run order inside this file:
1. Do it (source window 20)
2. Change it: delete the sweep (source window 22)

Prerequisites: demo_03_one_iteration_by_hand.
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


# Original CLI workflow for step_01_the_oracle_weak_and_strong.
COMMANDS_01 = """make ralph-check SHOW=date_contract

"""

def step_01_the_oracle_weak_and_strong(session):
    """Run Do it at this checkpoint.

    With no arguments, make ralph-check judges all 8 versions under both oracles, and holds each verdict to the label seeds.json gives it. SHOW= adds one version's diff and its failed checks.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every version under both oracles, and one seed shown; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ralph-check: the oracles on statutory_deadline in a copy of shared/desk_calc.py, task deadline (offline, Rs 0)
      version               weak   strong  seeded defect
      the task              FAIL   FAIL    
      reference             PASS   PASS    
      placeholder           PASS   FAIL    placeholder
      calendar_days         FAIL   FAIL    calendar_days
      start_day_counted     FAIL   FAIL    off_by_one
      closure_counted       FAIL   FAIL    event_scope
      date_contract         PASS   FAIL    error_contract
      holiday_note_dropped  FAIL   FAIL    hidden_assumption

    date_contract: day_of() re-written by hand: a date not written YYYY-MM-DD now raises Python's ValueError, which the Desk's tool does not tu
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_change_it_delete_the_sweep(session):
    """Run Change it: delete the sweep at this checkpoint.

    The oracle's docstring names the change to try: delete the strong oracle's sweep over 2026. The cell copies oracle.py to a scratch directory without the sweep's two lines, then runs that copy on three versions, each spliced into the kit's own file as the loop does it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Change it: the strong oracle without its sweep; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the strong oracle with its sweep over 2026 deleted:
      placeholder    PASS, 10 checks
      reference      PASS, 10 checks
      calendar_days  FAIL, 10 checks: desk_calc's own selftest; the due date is never a Saturday or a Sunday
    """
    import subprocess, sys, tempfile, warnings
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, "commands")
    import ralph
    text = ralph.ORACLE_PY.read_text(encoding="utf-8")
    sweep = ('            ("every day of 2026, for each event: the second working day after the last working day, '
             'Monday to Friday",\n             False, self.sweep),\n')
    assert text.count(sweep) == 1, "the oracle changed: find the sweep's line in commands/ralph/oracle.py"
    tmp = Path(tempfile.mkdtemp(prefix="change-it-"))
    (tmp / "oracle.py").write_text(text.replace(sweep, ""), encoding="utf-8")       # the strong oracle, minus its sweep
    print("the strong oracle with its sweep over 2026 deleted:")
    for name in ("placeholder", "reference", "calendar_days"):
        kit = ralph.oracle_dir(tmp / name, ralph.versions()[name])                   # the version spliced into the kit's file
        r = subprocess.run([sys.executable, "-I", "-B", "-X", "utf8", str(tmp / "oracle.py"), "--kit", str(kit), "--json"],
                           capture_output=True, text=True, encoding="utf-8", env=ralph.quiet_env(kit / "home"))
        v = ralph.parse_verdict(r.stdout)
        bad = [c["what"] for c in v["checks"] if not c["ok"]]
        print(f"  {name:<14} {'PASS' if v['passed'] else 'FAIL'}, {len(v['checks'])} checks" + (f": {'; '.join(bad)}" if bad else ""))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_the_oracle_weak_and_strong),
        ('source_22', step_02_change_it_delete_the_sweep),
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
