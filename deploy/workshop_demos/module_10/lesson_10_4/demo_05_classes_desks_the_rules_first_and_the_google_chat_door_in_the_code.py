"""Lesson 10.4: Classes, desks, the rules first and the Google Chat door, in the code

No lane and no cost: the cell imports the router and runs decide() with no models, as an acme employee, on the smoke's disclosure, four questions with identifiers, and one with none.

Run order inside this file:
1. Do it: the rules on your machine (source window 34)

Prerequisites: demo_04_the_desk_page_and_the_hr_desk_app_in_google_chat.
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


def step_01_the_rules_on_your_machine(session):
    """Run Do it: the rules on your machine at this checkpoint.

    No lane and no cost: the cell imports the router and runs decide() with no models, as an acme employee, on the smoke's disclosure, four questions with identifiers, and one with none.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (decide() with no models: the rules alone; no lane, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gate posh  anchors []             near True  -> case         rule     
      gate None  anchors ['out_of_scope'] near False -> out_of_scope anchor   
      gate None  anchors ['handbook']   near False -> handbook     anchor   
      gate None  anchors ['statute']    near False -> statute      anchor   
      gate None  anchors ['statute']    near True  -> fallback     fallback error:RuntimeError
      gate None  anchors []             near False -> fallback     fallback error:RuntimeError
      K 7 ACCEPT_VOTES 5 CASE_VOTES 3 TAU_OOS 0.7 prompt 2026-10-01.1
    """
    manual_checkpoint("Wait five minutes after make desk switched acme's router on: the chat service reads the switches within 60 s and the example index within 5 minutes. Then open the deployed UI in a new tab, so the Desk starts a new conversation, sign in as yourself and choose Desk. Under Ask the Desk, ask What is the notice period? first, and if the reply asks which desk you mean, press the handbook's button. Ask the lk-06 question the previous section printed: one handbook answer with its citations. Ask the lk-17 question: a statute answer with a line for each Act it cites. Ask the lk-10 question: it is turned away at once, with a Raise a case button. Type done to run the router's rules on your machine.")
    import logging, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["services/chat", "."]
    import desk_router
    logging.getLogger("documind.chat.desk_router").setLevel(logging.ERROR)   # its warning is the reason printed below
    from shared import desk_rules
    from smoke.smoke_cases import POSH
    PREFIXES = ["EXP", "FIN", "GEN", "IT", "LV", "NP", "PB", "PR", "SEC", "WFH"]   # acme's clause-prefix map
    for q in (POSH, "What is the total payable on invoice INV-2026-0412?", "What does NP-03 say about notice?",
              "What is the minimum bonus under the Payment of Bonus Act?", "Under the Payment of Bonus Act, what bonus do I get?",
              "What is the notice period for a confirmed E3?"):
        d = desk_router.decide(q, {"tenant": "acme", "roles": ["employee"], "clause_prefixes": PREFIXES}, models=None)
        print(f"  gate {str(d['gate']):5} anchors {str(d['anchors']):14} near {str(desk_rules.near(q)):5} -> "
              f"{d['route']:12} {d['method']:8} {d['fallback_reason'] or ''}")
    print("  K", desk_router.K, "ACCEPT_VOTES", desk_router.ACCEPT_VOTES, "CASE_VOTES", desk_router.CASE_VOTES,
          "TAU_OOS", desk_router.TAU_OOS, "prompt", desk_router.PROMPT_VERSION)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_the_rules_on_your_machine),
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
