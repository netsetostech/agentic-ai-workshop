"""Lesson 10.5: Change it: delete the prompt's rule

The rule is advice to the model; the check is code. Delete the rule, run the tests and two turns on your lane, then put it back. One sentence of the system prompt tells the model where a calculator's numbers may come from: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Delete it, in your checkout only, and keep "Work every figure out with a calculator, never yourself." The deployed Desk is not touched: the change lives in your copy of services/chat/desk_agent.py, which the offline tests and make agent-turn import, and nothing here redeploys the chat service. One sentence of the system prompt tells the model where a calculator's numbers may come from: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Delete it, in your checkout only, and keep "Work every figure out with a calculator, never yourself." The deployed Desk is not touched: the change lives in your copy of services/chat/desk_agent.py, which the offline tests and make agent-turn import, and nothing here redeploys the chat service. Offline: the same three tests. They pass unchanged. Each refusal comes from _calc() and check_args(), and neither reads the prompt. Offline: the same three tests. They pass unchanged. Each refusal comes from _calc() and check_args(), and neither reads the prompt. On your lane: two agent turns with the rule gone. make agent-turn runs the handbook desk's agent in your shell, built as the Desk builds it, on gemini-3.6-flash and your lane's rag-api, and prints every model call, every tool call with its arguments, what each returned, the answer and the figure check. First jn-03; then "I am an E3 and I am leaving. How many days of earned leave will be encashed?", which gives no balance. About Rs 1.7 to 2.3 a turn. On your lane: two agent turns with the rule gone. make agent-turn runs the handbook desk's agent in your shell, built as the Desk builds it, on gemini-3.6-flash and your lane's rag-api, and prints every model call, every tool call with its arguments, what each returned, the answer and the figure check. First jn-03; then "I am an E3 and I am leaving. How many days of earned leave will be encashed?", which gives no balance. About Rs 1.7 to 2.3 a turn. What to read. Each encashable_days call's arguments, and what came back. Without the rule a model may try a number of its own more often: a balance for the second question, which gives none, or a cap from the wrong clause. Every such call comes back refused, in the check's words; for a balance nobody wrote: "refused: balance = 50 is a fact about the person that their message does not state: ask them for it". The model then asks for the missing number or answers without a calculation, and the figure check at the end says whether any figure in its words has no source. Whether this model tries a wrong number at all on the day you run it is the model's own behaviour; what the run shows is that none gets past the check. The rule makes a refused call less likely, which saves a model call. It was never what made the figure right.

Run order inside this file:
1. Change it: delete the prompt's rule (source window 23)
2. Change it: delete the prompt's rule (source window 25)
3. Change it: delete the prompt's rule (source window 27)
4. Change it: delete the prompt's rule (source window 29)

Prerequisites: demo_04_the_agent_its_calculators_and_check_args_in_the_code.
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


# Original CLI workflow for step_01_change_it_delete_the_prompt_s_rule.
COMMANDS_01 = """python - <<'PY'
from pathlib import Path
p = Path("services/chat/desk_agent.py")
lines = p.read_text(encoding="utf-8").split("\\n")
i = next(k for k, line in enumerate(lines) if "Give a calculator only numbers" in line)
print("before:", *(line.strip() for line in lines[i:i + 3]), sep="\\n  ")
lines[i:i + 3] = ['            "- Work every figure out with a calculator, never yourself.\\\\n"']
p.write_text("\\n".join(lines), encoding="utf-8")
print("after:", lines[i].strip(), sep="\\n  ")
PY
git status --short services/chat/

"""

def step_01_change_it_delete_the_prompt_s_rule(session):
    """Run Change it: delete the prompt's rule at this checkpoint.

    The rule is advice to the model; the check is code. Delete the rule, run the tests and two turns on your lane, then put it back. One sentence of the system prompt tells the model where a calculator's numbers may come from: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Delete it, in your checkout only, and keep "Work every figure out with a calculator, never yourself." The deployed Desk is not touched: the change lives in your copy of services/chat/desk_agent.py, which the offline tests and make agent-turn import, and nothing here redeploys the chat service.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the Change-it: delete the prompt's rule, in your checkout only.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: before:
      "- Work every figure out with a calculator, never yourself. Give a calculator only numbers and dates "
      "written in the person's question or in a passage, as they are written there: it refuses any other. When "
      "a number you need is in neither, say which one is missing.\\n"
    after:
      "- Work every figure out with a calculator, never yourself.\\n"
     M services/chat/desk_agent.py
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_change_it_delete_the_prompt_s_rule.
COMMANDS_02 = """# three of the Desk's agent tests: a scripted model, rag-api as a table; no lane, no model call, Rs 0
OFFLINE=1 DOCUMIND_REQUIRE_LIBS=1 bash commands/agent-turn.sh -m unittest commands/tests/test_desk.py -v \\
  -k test_a_number_in_neither -k test_a_codes_calculator -k test_a_model_error

"""

def step_02_change_it_delete_the_prompt_s_rule(session):
    """Run Change it: delete the prompt's rule at this checkpoint.

    One sentence of the system prompt tells the model where a calculator's numbers may come from: "Give a calculator only numbers and dates written in the person's question or in a passage, as they are written there: it refuses any other. When a number you need is in neither, say which one is missing." Delete it, in your checkout only, and keep "Work every figure out with a calculator, never yourself." The deployed Desk is not touched: the change lives in your copy of services/chat/desk_agent.py, which the offline tests and make agent-turn import, and nothing here redeploys the chat service. Offline: the same three tests. They pass unchanged. Each refusal comes from _calc() and check_args(), and neither reads the prompt.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the same three tests, with the rule gone.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: test_a_codes_calculator_runs_only_on_its_codes_passage_and_its_own_desk (commands.tests.test_desk.GraphTests.test_a_codes_calculator_runs_only_on_its_codes_passage_and_its_own_desk) ... ok
    test_a_model_error_is_the_direct_answer_under_the_same_limits (commands.tests.test_desk.GraphTests.test_a_model_error_is_the_direct_answer_under_the_same_limits) ... ok
    test_a_number_in_neither_the_passages_nor_the_message_is_refused (commands.tests.test_desk.GraphTests.test_a_number_in_neither_the_passages_nor_the_message_is_refused) ... ok

    ----------------------------------------------------------------------
    Ran 3 tests in N.NNNs

    OK
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_change_it_delete_the_prompt_s_rule.
COMMANDS_03 = """make agent-turn PROJECT="$PROJECT" REGION="$REGION" DESK=handbook TENANT=acme \\
  Q="I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?"
make agent-turn PROJECT="$PROJECT" REGION="$REGION" DESK=handbook TENANT=acme \\
  Q="I am an E3 and I am leaving. How many days of earned leave will be encashed?"

"""

def step_03_change_it_delete_the_prompt_s_rule(session):
    """Run Change it: delete the prompt's rule at this checkpoint.

    Offline: the same three tests. They pass unchanged. Each refusal comes from _calc() and check_args(), and neither reads the prompt. On your lane: two agent turns with the rule gone. make agent-turn runs the handbook desk's agent in your shell, built as the Desk builds it, on gemini-3.6-flash and your lane's rag-api, and prints every model call, every tool call with its arguments, what each returned, the answer and the figure check. First jn-03; then "I am an E3 and I am leaving. How many days of earned leave will be encashed?", which gives no balance. About Rs 1.7 to 2.3 a turn.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — two agent turns on your lane, with the rule gone.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/turn_changeit.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_change_it_delete_the_prompt_s_rule.
COMMANDS_04 = """git checkout -- services/chat/desk_agent.py
git status --short services/chat/     # prints nothing: the rule is back

"""

def step_04_change_it_delete_the_prompt_s_rule(session):
    """Run Change it: delete the prompt's rule at this checkpoint.

    On your lane: two agent turns with the rule gone. make agent-turn runs the handbook desk's agent in your shell, built as the Desk builds it, on gemini-3.6-flash and your lane's rag-api, and prints every model call, every tool call with its arguments, what each returned, the answer and the figure check. First jn-03; then "I am an E3 and I am leaving. How many days of earned leave will be encashed?", which gives no balance. About Rs 1.7 to 2.3 a turn. What to read. Each encashable_days call's arguments, and what came back. Without the rule a model may try a number of its own more often: a balance for the second question, which gives none, or a cap from the wrong clause. Every such call comes back refused, in the check's words; for a balance nobody wrote: "refused: balance = 50 is a fact about the person that their message does not state: ask them for it". The model then asks for the missing number or answers without a calculation, and the figure check at the end says whether any figure in its words has no source. Whether this model tries a wrong number at all on the day you run it is the model's own behaviour; what the run shows is that none gets past the check. The rule makes a refused call less likely, which saves a model call. It was never what made the figure right.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — put the rule back.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: (no output)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_change_it_delete_the_prompt_s_rule),
        ('source_25', step_02_change_it_delete_the_prompt_s_rule),
        ('source_27', step_03_change_it_delete_the_prompt_s_rule),
        ('source_29', step_04_change_it_delete_the_prompt_s_rule),
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
