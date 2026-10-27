"""Lesson 10.5: The agent, its calculators and check_args, in the code

Three of commands/tests/test_desk.py's agent tests. In the first, the agent passes a cap of 40, which neither LV-07 nor the message writes: refused, no calculation, no "Worked out in code". The second sends a gratuity question to the statute desk with the Code on Wages, not the Code on Social Security, among the passages, and has the agent ask for encashable_days, which the statute desk does not hold: two refusals, one by the Code check and one as an unknown tool. In the third the model raises a 429, and the section is the direct answer under the same Meter. A scripted model plays the agent and a table plays rag-api, so no model is called. commands/agent-turn.sh, given arguments, runs them in ~/graph-venv, which it makes with the chat image's pins if it is missing; with OFFLINE=1 it needs no project. The same check, on what your lane's rag-api returns. The cell asks POST /v1/passages, as documind-ui-sa, the account on every company's roster, for acme's handbook passages on "earned leave encashed on exit": the retrieval the agent's search makes, with no model call. Then it runs check_args() on jn-03's question twice, with a cap of 60 and then 45. 60 is NP-03's notice days: when NP-03 is among the passages, 60 is a number the turn has read, but it is not in LV-07's words, so the check refuses it with "refused: cap = 60 is not written in LV-07 of a handbook passage this turn read: search for that clause and use the figure it states". 45 is accepted, found in LV-07 at its passage's place in the list.

Run order inside this file:
1. Do it: three tests, offline (source window 19)
2. Do it: the check on your lane's own passages (source window 21)

Prerequisites: demo_03_the_desk_page_a_figure_worked_out_in_code_and_a_cap_nobody_wrote.
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


# Original CLI workflow for step_01_three_tests_offline.
COMMANDS_01 = """# three of the Desk's agent tests: a scripted model, rag-api as a table; no lane, no model call, Rs 0
OFFLINE=1 DOCUMIND_REQUIRE_LIBS=1 bash commands/agent-turn.sh -m unittest commands/tests/test_desk.py -v \\
  -k test_a_number_in_neither -k test_a_codes_calculator -k test_a_model_error

"""

def step_01_three_tests_offline(session):
    """Run Do it: three tests, offline at this checkpoint.

    Three of commands/tests/test_desk.py's agent tests. In the first, the agent passes a cap of 40, which neither LV-07 nor the message writes: refused, no calculation, no "Worked out in code". The second sends a gratuity question to the statute desk with the Code on Wages, not the Code on Social Security, among the passages, and has the agent ask for encashable_days, which the statute desk does not hold: two refusals, one by the Code check and one as an unknown tool. In the third the model raises a 429, and the section is the direct answer under the same Meter. A scripted model plays the agent and a table plays rag-api, so no model is called. commands/agent-turn.sh, given arguments, runs them in ~/graph-venv, which it makes with the chat image's pins if it is missing; with OFFLINE=1 it needs no project.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — three agent tests, offline.
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
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_check_on_your_lane_s_own_passages.
COMMANDS_02 = """TOKEN="$(tok "$API")" python - <<'PY'
import json, os, sys, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, ".")
from shared import desk_calc
row = next(r for r in map(json.loads, open("evals/route_arms.jsonl", encoding="utf-8")) if r["id"] == "jn-03")


def passages(query):
    \"\"\"acme's handbook passages for a query: rag-api's POST /v1/passages as documind-ui-sa, no model call.\"\"\"
    body = {"query": query, "tenant_id": "acme", "user_id": "agent", "top_k": 5, "stream": False,
            "filters": {"doc_type": ["policy"]}, "brain": "desk"}
    req = urllib.request.Request(os.environ["API"] + "/v1/passages", data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json",
                                          "Authorization": "Bearer " + os.environ["TOKEN"]})
    with urllib.request.urlopen(req, timeout=120) as r:
        return json.load(r).get("passages") or []


read = [p for p in passages("earned leave encashed on exit") if p.get("doc_type") == "policy"]
for i, p in enumerate(read, 1):                       # numbered from 1, as the desk's agent numbers what it reads
    print(f"[{i}] {p['section']}: {' '.join(p['text'].split())[:72]}...")
for cap in (60, 45):
    refused, found = desk_calc.check_args("encashable_days", {"balance": 50, "cap": cap}, read, row["question"])
    if refused:
        print(f"cap = {cap}: refused: {' '.join(refused)}")
    else:
        print(f"cap = {cap}: accepted: the balance from the message, the cap from "
              f"{found['cap']['clause']} [{found['cap']['n']}]")
PY

"""

def step_02_the_check_on_your_lane_s_own_passages(session):
    """Run Do it: the check on your lane's own passages at this checkpoint.

    The same check, on what your lane's rag-api returns. The cell asks POST /v1/passages, as documind-ui-sa, the account on every company's roster, for acme's handbook passages on "earned leave encashed on exit": the retrieval the agent's search makes, with no model call. Then it runs check_args() on jn-03's question twice, with a cap of 60 and then 45. 60 is NP-03's notice days: when NP-03 is among the passages, 60 is a number the turn has read, but it is not in LV-07's words, so the check refuses it with "refused: cap = 60 is not written in LV-07 of a handbook passage this turn read: search for that clause and use the figure it states". 45 is accepted, found in LV-07 at its passage's place in the list.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — your lane's passages for LV-07, then check_args with cap 60, then 45 (Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/passages_check.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_three_tests_offline),
        ('source_21', step_02_the_check_on_your_lane_s_own_passages),
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
