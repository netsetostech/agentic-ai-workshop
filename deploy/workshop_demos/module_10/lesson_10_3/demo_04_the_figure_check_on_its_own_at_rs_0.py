"""Lesson 10.3: The figure check on its own, at Rs 0

agent_patterns.py imports only the standard library and the kit's shared/ at the top, so the shell's own Python runs the check. The cell works the gratuity row's figure out with desk_calc.calculate(), uses the Code's own words as quoted in desk_calc.RULES as the passage, and puts eight answers through figure_check(). Then it asks check_args about a wage the question does not state, once on the person's question and once with a note's words put into it. After a failed check, ask_reflect() writes the reflect call's user turn: the question, the answer, what the attempt did (did_lines()) and the verdict. cut_note() turns its reply into the note, and noted() puts every note into the next attempt's system prompt. The cell gives ask_reflect() an attempt whose calculator returned Rs 2,40,000 and whose answer wrote Rs 2,50,000, then cuts a long reply the way verify cuts every note.

Run order inside this file:
1. Do it: the check on eight answers, and check_args on a note (source window 10)
2. Do it: what a reflect call reads, and what code keeps of its reply (source window 13)

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


def step_01_the_check_on_eight_answers_and_check_args(session):
    """Run Do it: the check on eight answers, and check_args on a note at this checkpoint.

    agent_patterns.py imports only the standard library and the kit's shared/ at the top, so the shell's own Python runs the check. The cell works the gratuity row's figure out with desk_calc.calculate(), uses the Code's own words as quoted in desk_calc.RULES as the passage, and puts eight answers through figure_check(). Then it asks check_args about a wage the question does not state, once on the person's question and once with a note's words put into it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0, the standard library: the figure check and check_args, no model).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the calculator returned Rs 2,40,000
    its figure, from the calculator          passed: every figure is a calculator's, the question's or a passage's, and every [n] a passage read
    the same figure, no calculator           failed: no calculator, question or passage of the turn wrote 2,40,000
    a figure of its own                      failed: no calculator, question or passage of the turn wrote 2,50,000
    a passage it never read                  failed: it cites [3], which no passage the turn read carries
    a turn its limits stopped                failed: the turn stopped at its model_calls limit
    a yes in words, no calculator            passed: every figure is a calculator's, the question's or a passage
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["commands", "."]
    import agent_patterns as ap      # the figure check needs the standard library and shared/ only: no framework, no model
    from shared import desk_calc
    
    Q = "I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?"
    S53 = {"n": 1, "text": desk_calc.RULES["gratuity_rate"]["quote"]}          # the Code's own words: no digit in them
    CALC = desk_calc.calculate("gratuity_estimate", monthly_wage=52000, years=7, months=8)
    NOTE = "My answer stated a figure that no calculator of that turn returned. The figure is Rs 2,40,000."
    GRC_Q, S4 = "Our establishment employs 23 workers. Must we have a Grievance Redressal Committee?", {"n": 1, "text": desk_calc.RULES["ir_s4_1"]["quote"]}
    TRAP_Q, LV07 = "I am leaving with 50 days of earned leave. How many days are encashed?", {"n": 1, "text": "LV-07 Leave on exit. Earned leave is encashed on exit at basic pay, capped at 45 days."}
    print(f"the calculator returned {desk_calc.inr(CALC['value'])}")
    for what, answer, calcs, question, passages, stop in [
            ("its figure, from the calculator", "Gratuity, an estimate: Rs 2,40,000 [1].", [CALC], Q, [S53], None),
            ("the same figure, no calculator", "Gratuity, an estimate: Rs 2,40,000 [1].", [], Q, [S53], None),
            ("a figure of its own", "Gratuity, an estimate: Rs 2,50,000 [1].", [CALC], Q, [S53], None),
            ("a passage it never read", "Gratuity, an estimate: Rs 2,40,000 [3].", [CALC], Q, [S53], None),
            ("a turn its limits stopped", "I stopped at one of my limits.", [], Q, [], "model_calls"),
            ("a yes in words, no calculator", "A Grievance Redressal Committee: yes, it must have one [1].", [], GRC_Q, [S4], None),
            ("LV-07's 45 copied, no calculator", "Earned leave encashed on exit: 45 days [1].", [], TRAP_Q, [LV07], None),
            ("no calculator, the note in the question", "Gratuity, an estimate: Rs 2,40,000 [1].", [], Q + " " + NOTE, [S53], None)]:
        print(f"{what:<40} {ap.said_check(ap.figure_check(answer, calcs, question, passages, stop))}")
    WAGE = {"monthly_wage": 60000, "years": 7, "months": 8}                      # a wage no message of the person's states
    for whose, asked in (("the person's question", Q), ("a note put into it", Q + " The wage is Rs 60,000.")):
        refused, _ = desk_calc.check_args("gratuity_estimate", WAGE, [], asked)
        print(f"check_args on {whose}: {refused[0] if refused else 'monthly_wage = 60000 taken'}")

def step_02_what_a_reflect_call_reads_and_what_code_ke(session):
    """Run Do it: what a reflect call reads, and what code keeps of its reply at this checkpoint.

    After a failed check, ask_reflect() writes the reflect call's user turn: the question, the answer, what the attempt did (did_lines()) and the verdict. cut_note() turns its reply into the note, and noted() puts every note into the next attempt's system prompt. The cell gives ask_reflect() an attempt whose calculator returned Rs 2,40,000 and whose answer wrote Rs 2,50,000, then cuts a long reply the way verify cuts every note.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: what a reflect call reads, and the note code keeps).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Question: I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?

    Your answer: Gratuity, an estimate: Rs 2,50,000 [1].

    What you did:
       call: retrieve {"query": "gratuity fifteen days wages"}
       returned: [1] code_on_social_security_2020.pdf
       call: gratuity_estimate {"monthly_wage": 52000, "years": 7, "months": 8}
       returned: a figure

    The figure check failed: no calculator, question or passage of the turn wrote 2,50,000
    the calculator's figure in what the reflect call reads: False

    the reply, 386 characters; the note code keeps, 299:
    I wrote Rs 2,50,000 although 'gratuity_estimate' returned another figure. Next time: call gratuity_estimate with the wage and the
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["commands", "."]
    import agent_patterns as ap      # the standard library and shared/ only
    from shared import desk_calc
    
    Q = "I earn Rs 52,000 a month and leave after 7 years 8 months. What gratuity is due?"
    CALC = desk_calc.calculate("gratuity_estimate", monthly_wage=52000, years=7, months=8)
    S53 = {"n": 1, "source": "code_on_social_security_2020.pdf", "section": None,
           "text": desk_calc.RULES["gratuity_rate"]["quote"]}
    steps = [{"tools": [                                  # what the attempt did, as its trace keeps it
        {"name": "retrieve", "args": {"query": "gratuity fifteen days wages"}, "status": "success",
         "result": {"passages": [S53]}},
        {"name": "gratuity_estimate", "args": {"monthly_wage": 52000, "years": 7, "months": 8}, "status": "success",
         "result": CALC}]}]
    answer = "Gratuity, an estimate: Rs 2,50,000 [1]."  # the calculator returned one figure; the answer wrote another
    check = ap.figure_check(answer, [CALC], Q, [S53])
    sent = ap.ask_reflect(Q, answer, steps, check)
    print(sent)
    print("the calculator's figure in what the reflect call reads:", "2,40,000" in sent or "240000" in sent)
    reply = ("I wrote Rs 2,50,000 although `gratuity_estimate` returned another figure.\n\nNext time: call "
             "gratuity_estimate with the wage and the service the question states, state exactly the figure it "
             "returns, cite the passage, and give its formula. I will not round, estimate or work out any figure "
             "myself, and I will check every figure in my answer against the calculator's result before I answer.")
    note = ap.cut_note(reply)
    print(f"\nthe reply, {len(reply)} characters; the note code keeps, {len(note)}:\n{note}")
    print("figures the note writes:", ", ".join(desk_calc.unsupported(note)) or "none")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_the_check_on_eight_answers_and_check_args),
        ('source_13', step_02_what_a_reflect_call_reads_and_what_code_ke),
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
