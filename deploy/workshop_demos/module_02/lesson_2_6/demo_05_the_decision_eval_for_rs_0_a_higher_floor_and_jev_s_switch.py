"""Lesson 2.6: The decision eval for Rs 0, a higher floor, and Jev's switch

Do it: all 65 rows, Rs 0 Raise the floor and the rule buys refusals with answers. The same run at 0.70: shared/system_one.py is the only door to Jev, and decide() its only entry point. It never raises: every outcome is a result with a verdict of answer, refuse, skipped or error, and only the first two are decisions. The mode is read at call time, and off returns at once. An empty pool is refused in code, as rag-api refuses it, before any mode could ask Jev. Recorded mode reads the recorded file and nothing else. Live mode checks the tenant's data_region first, failing closed to in, then builds the payload from the question and the passages' text with identifiers masked, and only then reaches the adapter seam: _headers(), _request() and _parse(), which PR 2.6-C fills once TypeSafe documents its API. Until then _request() raises before any key is read or any socket opens, and decide() turns that into an error row, which no rate counts as a refusal. Run the Rs 0 eval with JEV_MODE=recorded on zeta's 10 rows, then call decide() in each mode, with the data regions make roster writes standing in for the Firestore read:

Run order inside this file:
1. Do it: all 65 rows, Rs 0 (source window 20)
2. Change it: a higher floor (source window 22)
3. Jev's switch, called by hand (source window 29)
4. Jev's switch, called by hand (source window 31)

Prerequisites: demo_04_the_kit_s_code_two_refusals_in_the_handler_and_the_evidence_rule.
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


# Original CLI workflow for step_01_all_65_rows_rs_0.
COMMANDS_01 = """python evals/decide.py --local

"""

def step_01_all_65_rows_rs_0(session):
    """Run Do it: all 65 rows, Rs 0 at this checkpoint.

    Do it: all 65 rows, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: no lane and no model; a few minutes, because it ranks the tenant's whole corpus for every row).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ... 10/65 rows
      ... 20/65 rows
      ... 30/65 rows
      ... 40/65 rows
      ... 50/65 rows
      ... 60/65 rows
    == answer or refuse: the decision eval (lesson 2.6) ==
      rows       65 golden rows: 47 answerable, 18 not
      pool       the Rs 0 lane, top 5: documind_tools.retrieve(passages=True) on the local profile over the kit's
                 corpus (2757 chunks), its gate the evidence rule at 0.50
      rule       an empty pool, or evidence under 0.50 of the question's information, is refused (Rs 0)
      generator  --local has no lane: the generator needs one (replay a saved run: --from FILE)
      jev        JEV_MODE=off: Jev not available, nothing sent

      rule       65 decided (5 by code: an empty pool), 0 errors, 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_change_it_a_higher_floor.
COMMANDS_02 = """python evals/decide.py --local --floor 0.7

"""

def step_02_change_it_a_higher_floor(session):
    """Run Change it: a higher floor at this checkpoint.

    Raise the floor and the rule buys refusals with answers. The same run at 0.70:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the Change-it: the same Rs 0 run with a higher floor).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ... 10/65 rows
      ... 20/65 rows
      ... 30/65 rows
      ... 40/65 rows
      ... 50/65 rows
      ... 60/65 rows
    == answer or refuse: the decision eval (lesson 2.6) ==
      rows       65 golden rows: 47 answerable, 18 not
      pool       the Rs 0 lane, top 5: documind_tools.retrieve(passages=True) on the local profile over the kit's
                 corpus (2757 chunks), its gate the evidence rule at 0.70
      rule       an empty pool, or evidence under 0.70 of the question's information, is refused (Rs 0)
      generator  --local has no lane: the generator needs one (replay a saved run: --from FILE)
      jev        JEV_MODE=off: Jev not available, nothing sent

      rule       65 decided (14 by code: an empty pool), 0 errors,
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_jev_s_switch_called_by_hand.
COMMANDS_03 = """JEV_MODE=recorded python evals/decide.py --local --tenant zeta

"""

def step_03_jev_s_switch_called_by_hand(session):
    """Run Jev's switch, called by hand at this checkpoint.

    shared/system_one.py is the only door to Jev, and decide() its only entry point. It never raises: every outcome is a result with a verdict of answer, refuse, skipped or error, and only the first two are decisions. The mode is read at call time, and off returns at once. An empty pool is refused in code, as rag-api refuses it, before any mode could ask Jev. Recorded mode reads the recorded file and nothing else. Live mode checks the tenant's data_region first, failing closed to in, then builds the payload from the question and the passages' text with identifiers masked, and only then reaches the adapter seam: _headers(), _request() and _parse(), which PR 2.6-C fills once TypeSafe documents its API. Until then _request() raises before any key is read or any socket opens, and decide() turns that into an error row, which no rate counts as a refusal. Run the Rs 0 eval with JEV_MODE=recorded on zeta's 10 rows, then call decide() in each mode, with the data regions make roster writes standing in for the Firestore read:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: Jev's recorded mode, on zeta's ten rows).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == answer or refuse: the decision eval (lesson 2.6) ==
      rows       10 golden rows: 5 answerable, 5 not
      pool       the Rs 0 lane, top 5: documind_tools.retrieve(passages=True) on the local profile over the kit's
                 corpus (1002 chunks), its gate the evidence rule at 0.50
      rule       an empty pool, or evidence under 0.50 of the question's information, is refused (Rs 0)
      generator  --local has no lane: the generator needs one (replay a saved run: --from FILE)
      jev        JEV_MODE=recorded: no recordings: evals/system_one/recorded.jsonl does not exist - none ship until decisions are recorded against TypeSafe's API (PR 2.6-C), and none are written by hand

      rule       10 decided 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def step_04_jev_s_switch_called_by_hand(session):
    """Run Jev's switch, called by hand at this checkpoint.

    shared/system_one.py is the only door to Jev, and decide() its only entry point. It never raises: every outcome is a result with a verdict of answer, refuse, skipped or error, and only the first two are decisions. The mode is read at call time, and off returns at once. An empty pool is refused in code, as rag-api refuses it, before any mode could ask Jev. Recorded mode reads the recorded file and nothing else. Live mode checks the tenant's data_region first, failing closed to in, then builds the payload from the question and the passages' text with identifiers masked, and only then reaches the adapter seam: _headers(), _request() and _parse(), which PR 2.6-C fills once TypeSafe documents its API. Until then _request() raises before any key is read or any socket opens, and decide() turns that into an error row, which no rate counts as a refusal. Run the Rs 0 eval with JEV_MODE=recorded on zeta's 10 rows, then call decide() in each mode, with the data regions make roster writes standing in for the Firestore read:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: no socket opens in any mode).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: off      acme    skipped  source off       JEV_MODE=off: Jev not available, nothing sent
    recorded acme    skipped  source recorded  no recordings: evals/system_one/recorded.jsonl does not exist - none ship until decisions are recorded against TypeSafe's API (PR 2.6-C), and none are written by hand
    live     globex  skipped  source policy    tenant globex: data_region in - its text stays in India and Jev's region is undocumented: not sent
    live     acme    error    source live      the question and 1 passages were ready to send; masked pan | error: TypeSafe adapter not configured (PR 2.6-C)

    what live mode would send: ['passages', 'question'] | masked: pan
       PAN: [PAN]
       GSTIN: 27AAAPZ1234C1Z
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, ".")
    from shared import local_corpus, system_one
    
    ROSTER = {"acme": "any", "zeta": "any", "globex": "in"}          # the data_region make roster writes (commands/lane.py)
    invoice = next(c for c in local_corpus.chunks_for("acme") if "AAAPZ1234C" in c["text"])
    POOL = [{"n": 1, "chunk_id": invoice["chunk_id"], "text": invoice["text"]}]
    Q = "What is the total payable on invoice INV-2026-0412?"
    
    
    def ask_jev(mode, tenant):
        """One system_one.decide() in a JEV_MODE, with make roster's data_region standing in for the Firestore read.
        
        Example: ask_jev(mode, tenant)
        """
        res = system_one.decide(Q, POOL, "lk-10", tenant, jev_mode=mode, policy_for=ROSTER.get)
        print(f"{mode:<9}{tenant:<7} {res['verdict']:<8} source {res['source']:<9} {res['reason']}"
              + (f" | error: {res['error']}" if res["error"] else ""))
    
    
    for mode, tenant in (("off", "acme"), ("recorded", "acme"), ("live", "globex"), ("live", "acme")):
        ask_jev(mode, tenant)
    payload, kinds = system_one._payload(Q, POOL)
    print(f"\nwhat live mode would send: {sorted(payload)} | masked: {', '.join(kinds) or 'nothing'}")
    for line in payload["passages"][0].splitlines():
        if line.startswith(("PAN", "GSTIN", "Contact", "Email")):
            print("   " + line)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_all_65_rows_rs_0),
        ('source_22', step_02_change_it_a_higher_floor),
        ('source_29', step_03_jev_s_switch_called_by_hand),
        ('source_31', step_04_jev_s_switch_called_by_hand),
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
