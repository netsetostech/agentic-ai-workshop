"""Lesson 10.2: ReWOO: one plan with placeholders, checked and run in waves, offline

These functions need no framework and no model: agent_patterns.py imports only the standard library and the kit's shared/ at the top, so the shell's own Python runs them. The cell reads the plan the scripted planner writes for chained-exit-e3 and prints what each step waits for and the waves. Then it prints what a refused value stops, four plans check_rewoo() refuses, one placeholder filled, and an extract worker's figure held to its quote twice. Offline, the corpus is ranked in Python, and a wave's searches share one interpreter: three cold searches side by side can outlast a search's budget, 25 seconds by default, and come back failed, as a slow rag-api's would. The kit's own docstring warns of it. RAG_TIMEOUT_S=90, the value the chat service is deployed with, gives them room.

Run order inside this file:
1. Do it: the plan's readers, at Rs 0 (source window 23)
2. Do it: ReWOO on a chained row (source window 25)

Prerequisites: demo_04_plan_and_execute_a_plan_an_executor_one_replan_offline.
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


def step_01_the_plan_s_readers_at_rs_0(session):
    """Run Do it: the plan's readers, at Rs 0 at this checkpoint.

    These functions need no framework and no model: agent_patterns.py imports only the standard library and the kit's shared/ at the top, so the shell's own Python runs them. The cell reads the plan the scripted planner writes for chained-exit-e3 and prints what each step waits for and the waves. Then it prints what a refused value stops, four plans check_rewoo() refuses, one placeholder filled, and an extract worker's figure held to its quote twice.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0, the standard library: the plan's readers, no model).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 8 steps read; check_rewoo refuses: nothing
      #E1 retrieve          takes -    runs after -
      #E2 retrieve          takes -    runs after -
      #E3 retrieve          takes -    runs after -
      #E4 extract           takes #E1  runs after -
      #E5 extract           takes #E2  runs after -
      #E6 notice_end        takes #E4  runs after #E1, #E2, #E3
      #E7 encashable_days   takes #E5  runs after #E1, #E2, #E3
      #E8 gratuity_estimate takes -    runs after #E1, #E2, #E3
    wave 1: #E1, #E2, #E3
    wave 2: #E4, #E5, #E8
    wave 3: #E6, #E7
    after #E5 is refused: (['#E6'], {'#E7': '#E5 was refused'})
    refused: #E1 uses #E2 before #E2 runs: a step may use only the steps written above it
    refused: #E2 gives cap the pas
    """
    import json, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["commands", "."]
    import agent_patterns as ap      # the standard library and shared/ at import: the plan's readers need no framework
    
    TOOLS = ["retrieve", "accrued_leave", "carry_forward", "encashable_days", "notice_end", "gratuity_estimate", "statutory_deadline", "threshold_check"]       # the desk's eight
    PLAN = """Plan: Search for the passage each figure rests on; the searches wait on nothing.
#E1 = retrieve[{"query": "notice period confirmed employee acknowledged in writing"}]
#E2 = retrieve[{"query": "earned leave encashed on exit"}]
#E3 = retrieve[{"query": "gratuity fifteen days wages for every completed year of service"}]
Plan: Read each figure a handbook clause states from the passages its search found.
#E4 = extract[{"what": "the days NP-03 states", "from": "#E1"}]
#E5 = extract[{"what": "the cap LV-07 states", "from": "#E2"}]
Plan: Work each figure out with its calculator, from the question's figures and those read.
#E6 = notice_end[{"ack_date": "2026-10-05", "days": "#E4"}]
#E7 = encashable_days[{"balance": 50, "cap": "#E5"}]
#E8 = gratuity_estimate[{"monthly_wage": 52000, "years": 7, "months": 8}]"""
    steps = ap.read_rewoo(PLAN)
    tool = {s["id"]: s["tool"] for s in steps}
    print(f"{len(steps)} steps read; check_rewoo refuses: {ap.check_rewoo(steps, TOOLS, 12) or 'nothing'}")
    for sid, (values, after) in ap.needs(steps).items():
        print(f"  {sid} {tool[sid]:<17} takes {', '.join(values) or '-':<4} runs after {', '.join(after) or '-'}")
    outcome, wave = {}, 0
    while len(outcome) < len(steps):                     # every step returns: the waves
        ready, never = ap.next_wave(steps, outcome)
        wave += 1
        print(f"wave {wave}: {', '.join(ready)}")
        outcome.update({sid: {"state": "ok", "value": 1} for sid in ready})
    done = {sid: {"state": "ok", "value": 1} for sid in ("#E1", "#E2", "#E3", "#E4", "#E8")}
    done["#E5"] = {"state": "refused"}                   # suppose LV-07's cap could not be read
    print("after #E5 is refused:", ap.next_wave(steps, done))
    for bad in ('#E1 = notice_end[{"ack_date": "2026-10-05", "days": "#E2"}]\n#E2 = retrieve[{"query": "notice period"}]',
                '#E1 = retrieve[{"query": "earned leave encashed on exit"}]\n#E2 = encashable_days[{"balance": 80, "cap": "#E1"}]',
                '#E1 = payroll_update[{"days": 45}]',
                "\n".join(f'#E{i} = retrieve[{{"query": "q{i}"}}]' for i in range(1, 14))):
        print("refused:", ap.check_rewoo(ap.read_rewoo(bad), TOOLS, 12))
    print(ap.resolve({"balance": 50, "cap": "#E5"}, {"#E5": 45}))
    lv07 = [{"n": 6, "text": "Earned leave is encashed on exit at basic pay, capped at 45 days."}]       # a passage that writes LV-07's sentence
    for quote in ("Earned leave is encashed on exit at basic pay, capped at 45 days.", "Leave is encashed up to 45 days."):
        print(ap.read_figure(json.dumps({"value": 45, "quote": quote}), lv07))

# Original CLI workflow for step_02_rewoo_on_a_chained_row.
COMMANDS_02 = """RAG_TIMEOUT_S=90 make agent-turn OFFLINE=1 PATTERN=rewoo ROW=chained-exit-e3

"""

def step_02_rewoo_on_a_chained_row(session):
    """Run Do it: ReWOO on a chained row at this checkpoint.

    Offline, the corpus is ranked in Python, and a wave's searches share one interpreter: three cold searches side by side can outlast a search's budget, 25 seconds by default, and come back failed, as a slow rag-api's would. The kit's own docstring warns of it. RAG_TIMEOUT_S=90, the value the chat service is deployed with, gives them room.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: rewoo on the first chained row; RAG_TIMEOUT_S gives a cold wave room).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: agent turn: pattern rewoo, desk astar, tenant acme
      the desk: one retrieve over policy, statute, guidance, and 7 calculators: accrued_leave, carry_forward, encashable_days, notice_end, gratuity_estimate, statutory_deadline, threshold_check
      thinking: low, the desk agent's own (THINKING= sends minimal, low, medium or high with every call)
      rewoo (lesson 10.2): plan once (ReWOO): one planner call writes every step, a later one naming an earlier result by placeholder (#E1); code runs them in waves, the steps that wait on nothing together, an extract worker reading a figure from a search's passages; one solver call writes the answer from the evidence, and nothing replans
      the planner: gemini
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_the_plan_s_readers_at_rs_0),
        ('source_25', step_02_rewoo_on_a_chained_row),
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
