"""Lesson 10.5: Three arms on the same twelve rows, compared and combined

Each row goes to POST /v1/route and to POST /v1/desk as its company's eval account, in a fresh session. On arm B the dev gates apply, as in lesson 10.4: 95% route accuracy and 90% recall for each desk. On 12 rows that means all 12 routed right: 8 of 8 handbook rows and 4 of 4 statute rows. One wrong route prints a FAIL line and make ends with Error 1, and the saved run and the report are written all the same. About Rs 13 to 17. Arm C: past the gate and the masking, a direct answer over the doc types the person may read, with no classifier and no calculator. Its report says its route column shows the gate and coverage only, so read its authority and correct rates first. A calculator row asks for a figure that neither its question nor its clause writes, so arm C's model must work it out in its own words, where the figure check can see it. About Rs 5. Arm C: past the gate and the masking, a direct answer over the doc types the person may read, with no classifier and no calculator. Its report says its route column shows the gate and coverage only, so read its authority and correct rates first. A calculator row asks for a figure that neither its question nor its clause writes, so arm C's model must work it out in its own words, where the figure check can see it. About Rs 5. Arm Astar: one agent on every row, lookups included, over every class the person may read, with all seven calculators. The most model calls of the three: about Rs 17 to 24. --compare reads two or three reports of one split, one arm each, on the same rows, and refuses anything else: two reports of one arm, no report of arm B, two splits, or rows that differ. For each arm it prints the correct and authority rates with their Wilson intervals, the desk turns' rupees and model calls, p50 and p95 latency, and the turns in agent mode with their calculator results and refused calls. Then it pairs B against each other arm row by row, through evals/paired.py: Newcombe's interval for the difference, the exact McNemar p, and a verdict read against the margin written there before any run, 3 points, on 8 October 2026. evals/combine.py reads the saved runs as the members of an ensemble, at Rs 0. For each answer row it prints which members were right, by the route eval's own verdict. On a row where any member ran a calculator, the members vote: each proposes the (calculator, value) pairs its answer's calculations hold, which code returned and no model wrote, and the proposal more members made than any other wins. The answer of the first member that made it ships as it stands. A member with no calculation proposes nothing, and a tie abstains: the row goes to a person, since a regulated figure is not settled by a coin. Then come each member's rate, the rows where all, some or none were right, the vote beside the best single arm on the rows it voted on, and the figure check, desk_calc.unsupported(), on every member's answer. Do it: the combiners on scripted members, offline. --selftest runs on scripted members of fig-01, with no model call. Two members' calculators returned Rs 2,40,000; a third writes Rs 2,10,000 itself. With --layers 2 it adds an arbiter, which picks one member's answer from an enum of their names and ships it word for word, and two layers of a mixture-of-agents aggregator, each reading every answer of the layer before and writing a new one. The vote and the arbiter only choose among the members' answers, so neither writes a figure of its own. The aggregator writes new text: this one averages the figures it reads and writes "About Rs 2,25,000", a figure no member computed, and unsupported() flags it at every layer. That is the mixture-of-agents pattern's cost on a regulated figure: every layer is a model writing again, so its figures need the same check as an agent's, while the vote needs no model call at all. --layers goes up to 5. On a lane the arbiter and the aggregator would be model calls of their own; the kit runs them scripted only. Do it: the three saved runs, combined.

Run order inside this file:
1. Do it: arm B, the routed Desk (source window 41)
2. Do it: arm C and arm Astar, on the same rows (source window 43)
3. Do it: arm C and arm Astar, on the same rows (source window 45)
4. The arms side by side (source window 49)
5. The arms as an ensemble (source window 53)
6. The arms as an ensemble (source window 55)

Prerequisites: demo_07_the_rows_and_the_checkpoint.
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


# Original CLI workflow for step_01_arm_b_the_routed_desk.
COMMANDS_01 = """mkdir -p "$HOME/arms"
make route-eval PROJECT="$PROJECT" REGION="$REGION" ROUTES=evals/route_arms.jsonl ARM=B \\
  SAVE="$HOME/arms/arms_B.jsonl" REPORT="$HOME/arms/arms_B.json"

"""

def step_01_arm_b_the_routed_desk(session):
    """Run Do it: arm B, the routed Desk at this checkpoint.

    Each row goes to POST /v1/route and to POST /v1/desk as its company's eval account, in a fresh session. On arm B the dev gates apply, as in lesson 10.4: 95% route accuracy and 90% recall for each desk. On 12 rows that means all 12 routed right: 8 of 8 handbook rows and 4 of 4 statute rows. One wrong route prints a FAIL line and make ends with Error 1, and the saved run and the report are written all the same. About Rs 13 to 17.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — arm B, the routed Desk, on the twelve rows.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/arms_B.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_arm_c_and_arm_astar_on_the_same_rows.
COMMANDS_02 = """make route-eval PROJECT="$PROJECT" REGION="$REGION" ROUTES=evals/route_arms.jsonl ARM=C \\
  SAVE="$HOME/arms/arms_C.jsonl" REPORT="$HOME/arms/arms_C.json"

"""

def step_02_arm_c_and_arm_astar_on_the_same_rows(session):
    """Run Do it: arm C and arm Astar, on the same rows at this checkpoint.

    Arm C: past the gate and the masking, a direct answer over the doc types the person may read, with no classifier and no calculator. Its report says its route column shows the gate and coverage only, so read its authority and correct rates first. A calculator row asks for a figure that neither its question nor its clause writes, so arm C's model must work it out in its own words, where the figure check can see it. About Rs 5.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — arm C, code only, on the same rows.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/arms_C.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_arm_c_and_arm_astar_on_the_same_rows.
COMMANDS_03 = """make route-eval PROJECT="$PROJECT" REGION="$REGION" ROUTES=evals/route_arms.jsonl ARM=Astar \\
  SAVE="$HOME/arms/arms_Astar.jsonl" REPORT="$HOME/arms/arms_Astar.json"

"""

def step_03_arm_c_and_arm_astar_on_the_same_rows(session):
    """Run Do it: arm C and arm Astar, on the same rows at this checkpoint.

    Arm C: past the gate and the masking, a direct answer over the doc types the person may read, with no classifier and no calculator. Its report says its route column shows the gate and coverage only, so read its authority and correct rates first. A calculator row asks for a figure that neither its question nor its clause writes, so arm C's model must work it out in its own words, where the figure check can see it. About Rs 5. Arm Astar: one agent on every row, lookups included, over every class the person may read, with all seven calculators. The most model calls of the three: about Rs 17 to 24.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — arm Astar, one agent, on the same rows.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/arms_Astar.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_the_arms_side_by_side.
COMMANDS_04 = """make route-compare REPORTS="$HOME/arms/arms_B.json $HOME/arms/arms_C.json $HOME/arms/arms_Astar.json"

"""

def step_04_the_arms_side_by_side(session):
    """Run The arms side by side at this checkpoint.

    --compare reads two or three reports of one split, one arm each, on the same rows, and refuses anything else: two reports of one arm, no report of arm B, two splits, or rows that differ. For each arm it prints the correct and authority rates with their Wilson intervals, the desk turns' rupees and model calls, p50 and p95 latency, and the turns in agent mode with their calculator results and refused calls. Then it pairs B against each other arm row by row, through evals/paired.py: Newcombe's interval for the difference, the exact McNemar p, and a verdict read against the margin written there before any run, 3 points, on 8 October 2026.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the three reports side by side (Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/arms_compare.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_the_arms_as_an_ensemble.
COMMANDS_05 = """python evals/combine.py --selftest --layers 2      # scripted members: no model call, Rs 0

"""

def step_05_the_arms_as_an_ensemble(session):
    """Run The arms as an ensemble at this checkpoint.

    evals/combine.py reads the saved runs as the members of an ensemble, at Rs 0. For each answer row it prints which members were right, by the route eval's own verdict. On a row where any member ran a calculator, the members vote: each proposes the (calculator, value) pairs its answer's calculations hold, which code returned and no model wrote, and the proposal more members made than any other wins. The answer of the first member that made it ships as it stands. A member with no calculation proposes nothing, and a tie abstains: the row goes to a person, since a regulated figure is not settled by a coin. Then come each member's rate, the rows where all, some or none were right, the vote beside the best single arm on the rows it voted on, and the figure check, desk_calc.unsupported(), on every member's answer. Do it: the combiners on scripted members, offline. --selftest runs on scripted members of fig-01, with no model call. Two members' calculators returned Rs 2,40,000; a third writes Rs 2,10,000 itself. With --layers 2 it adds an arbiter, which picks one member's answer from an enum of their names and ships it word for word, and two layers of a mixture-of-agents aggregator, each reading every answer of the layer before and writing a new one.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the combiners on scripted members (Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: combine.py --selftest: the combiners on scripted members of fig-01, no model call (Rs 0)
      question   I earn Rs 52,000 a month and leave after 7 years 8 months of continuous service. What gratuity is due to me under the Code on Social Security, 2020?
      right      must_contain 2,40,000
      P1         gratuity_estimate = 240000 by code; right; unsupported: none
      P2         gratuity_estimate = 240000 by code; right; unsupported: none
      P3         no calculation, it writes "About Rs 2,10,000 [1]: fifteen days' wages for each of the 7 completed years."; wrong; unsupported: 2,10,000
      vote       gratuity_estimate = 240000 from 2 of 3 members: P1's answer ships as it stands; right; 0 model calls
      s
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_the_arms_as_an_ensemble.
COMMANDS_06 = """make arms-combine SAVES="$HOME/arms/arms_B.jsonl $HOME/arms/arms_C.jsonl $HOME/arms/arms_Astar.jsonl"

"""

def step_06_the_arms_as_an_ensemble(session):
    """Run The arms as an ensemble at this checkpoint.

    The vote and the arbiter only choose among the members' answers, so neither writes a figure of its own. The aggregator writes new text: this one averages the figures it reads and writes "About Rs 2,25,000", a figure no member computed, and unsupported() flags it at every layer. That is the mixture-of-agents pattern's cost on a regulated figure: every layer is a model writing again, so its figures need the same check as an agent's, while the vote needs no model call at all. --layers goes up to 5. On a lane the arbiter and the aggregator would be model calls of their own; the kit runs them scripted only. Do it: the three saved runs, combined.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the three saved runs as an ensemble (Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/arms_combine.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_41', step_01_arm_b_the_routed_desk),
        ('source_43', step_02_arm_c_and_arm_astar_on_the_same_rows),
        ('source_45', step_03_arm_c_and_arm_astar_on_the_same_rows),
        ('source_49', step_04_the_arms_side_by_side),
        ('source_53', step_05_the_arms_as_an_ensemble),
        ('source_55', step_06_the_arms_as_an_ensemble),
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
