"""Lesson 10.10: One iteration by hand

Do it: the workspace The second cell plays iteration 1 the way a hurried agent might. It writes the kit's function with one line hard-coded, as seeds.json's placeholder has it. Then it runs the fast test that the prompt names, and asks both oracles about the workspace. Now write the body that spec.md describes, in $WS/shared/desk_calc.py, by hand or with a coding agent under your eye. Gemini CLI started in the workspace with no flags runs in its default approval mode: it asks before every edit and every command. Approve each edit to the function, and decline anything that reaches for gcloud, git or the network. It loads the workspace's GEMINI.md, the loop's notes, which carry that name only inside a workspace: a Gemini CLI session opened in the kit itself never loads them. How Gemini CLI signs in on your machine is your own setup, and nothing else on this page uses it. Then run the fast test and check again.

Run order inside this file:
1. Do it: the workspace (source window 7)
2. Do it: iteration 1, in a hurry (source window 9)
3. Do it: iteration 1, done properly (source window 11)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_the_workspace.
COMMANDS_01 = """make ralph-workspace OUT=/tmp/ralph-hand
export WS="$(ls -dt /tmp/ralph-hand/ralph-*/workspace | head -n 1)"
cat "$WS/fix_plan.md" "$WS/oracle.md"
sed -n '/^def statutory_deadline/,/NotImplementedError/p' "$WS/shared/desk_calc.py"

"""

def step_01_the_workspace(session):
    """Run Do it: the workspace at this checkpoint.

    Do it: the workspace

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the workspace a loop starts from; offline, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ralph-workspace: task deadline (statutory_deadline written to an engineer's spec), the workspace a loop starts from
      /tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/workspace
      PROMPT.md, spec.md, fix_plan.md, GEMINI.md and oracle.md at its root; no oracle checks and no seeds in it; its git repository beside it, with no remote: git --git-dir=/tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/git --work-tree=/tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/workspace log
      one iteration by hand: cd into it, run gemini in its default approval mode and ask it to follow PROMPT.md, approving or declining each edit and command; then make ralph-check WORKSPACE=<that path>
    # Fix 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_iteration_1_in_a_hurry.
COMMANDS_02 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
python - <<'PY'
import os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "commands")
import ralph                                         # the kit's loop: its seeds, splice() and the kit's own function
path = os.path.join(os.environ["WS"], "shared", "desk_calc.py")
hurried = ralph.versions()["placeholder"]            # the kit's function, one line hard-coded as seeds.json has it
ralph._write(path, ralph.splice(ralph._read(path), hurried))   # the kit's own writer: UTF-8, LF
print("wrote the body, with:", next(line.strip() for line in hurried.splitlines() if "due = " in line))
PY
(cd "$WS" && python3 shared/desk_calc.py --selftest | tail -n 2)   # the fast test the prompt names
make ralph-check WORKSPACE="$WS"
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_02_iteration_1_in_a_hurry(session):
    """Run Do it: iteration 1, in a hurry at this checkpoint.

    The second cell plays iteration 1 the way a hurried agent might. It writes the kit's function with one line hard-coded, as seeds.json's placeholder has it. Then it runs the fast test that the prompt names, and asks both oracles about the workspace.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (iteration 1 in a hurry, then the oracles; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: wrote the body, with: due = date(2026, 10, 6)
    ok    lakh is read, and a figure worked out in the head is not the calculator's
    every rule says what its corpus line says, and the figures hold
    ralph-check: the oracles on statutory_deadline in a change of shared/desk_calc.py (offline, Rs 0)
      the oracle runs the change's code on this machine, with the network and new processes refused inside Python: that is not a sandbox, so judge only a change you have read
      the workspace's change: /tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/by-hand.patch (make review-diff DIFF= reads it)
      weak oracle (desk_calc's own selftest): PASS
      strong oracle: FAIL
        FAIL  every day of 2026, for each even
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_iteration_1_done_properly.
COMMANDS_03 = """(cd "$WS" && python3 shared/desk_calc.py --selftest | tail -n 1)
make ralph-check WORKSPACE="$WS"

"""

def step_03_iteration_1_done_properly(session):
    """Run Do it: iteration 1, done properly at this checkpoint.

    Now write the body that spec.md describes, in $WS/shared/desk_calc.py, by hand or with a coding agent under your eye. Gemini CLI started in the workspace with no flags runs in its default approval mode: it asks before every edit and every command. Approve each edit to the function, and decline anything that reaches for gcloud, git or the network. It loads the workspace's GEMINI.md, the loop's notes, which carry that name only inside a workspace: a Gemini CLI session opened in the kit itself never loads them. How Gemini CLI signs in on your machine is your own setup, and nothing else on this page uses it. Then run the fast test and check again.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (after you write the body: the fast test, then the oracles).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: every rule says what its corpus line says, and the figures hold
    ralph-check: the oracles on statutory_deadline in a change of shared/desk_calc.py (offline, Rs 0)
      the oracle runs the change's code on this machine, with the network and new processes refused inside Python: that is not a sandbox, so judge only a change you have read
      the workspace's change: /tmp/ralph-hand/ralph-deadline-YYYYMMDD-HHMMSS-XXXXXXXX/by-hand.patch (make review-diff DIFF= reads it)
      weak oracle (desk_calc's own selftest): PASS
      strong oracle: PASS
    """
    manual_checkpoint('Write the body spec.md describes in $WS/shared/desk_calc.py (the workspace the first cell printed), replacing the hurried one: by hand, or with Gemini CLI started in the workspace with no flags, which asks before every edit and command. Approve each edit to the function, and decline anything that reaches for gcloud, git or the network. Type done to run the fast test and both oracles: the strong one passes only for a body that does what spec.md says.')
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_the_workspace),
        ('source_9', step_02_iteration_1_in_a_hurry),
        ('source_11', step_03_iteration_1_done_properly),
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
