"""Lesson 10.4: Two signals and one arbiter, in the code

No lane and no cost: evals/route_eval.py --local runs decide() in process on every scored dev row, with a scripted classifier and offline embeddings. For each row, it takes the row's own group out of the vote first, so a question never finds itself. make desk-check is the proof that the Desk's code holds, with no lane and no cost. It checks that the route set is the one evals/build_routes.py builds and that every row is sound, runs the self-tests and unit tests of the eval and the probe, runs the router on the dev rows as the cell above did, checks that the threshold sweep counts right, and checks that every calculator rule says what its line of the corpus says. Then it runs the chat service's tests for the case queue, the router and the desk graph, which need the chat image's libraries: the first run makes ~/graph-venv and installs services/chat/requirements.txt into it, which takes a few minutes. Every line must pass; a failing one stops the run.

Run order inside this file:
1. Do it: the router on every dev row, on your machine (source window 47)
2. Do it: the Desk's offline check (source window 49)

Prerequisites: demo_05_classes_desks_the_rules_first_and_the_google_chat_door_in_the_code.
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


# Original CLI workflow for step_01_the_router_on_every_dev_row_on_your_machin.
COMMANDS_01 = """python evals/route_eval.py --local

"""

def step_01_the_router_on_every_dev_row_on_your_machin(session):
    """Run Do it: the router on every dev row, on your machine at this checkpoint.

    No lane and no cost: evals/route_eval.py --local runs decide() in process on every scored dev row, with a scripted classifier and offline embeddings. For each row, it takes the row's own group out of the vote first, so a question never finds itself.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the router on every dev row with a scripted classifier; no lane, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: local: the classifier is scripted, so this measures the cascade, not a model
      187 rows scored; 20 left out (the groups of the prompt's examples); index of 198 dev rows
    arm B (the routed Desk)
    split dev
      top-1 route accuracy          186/187 = 99.5% [97.0%, 99.9%]
        recall handbook             43/44 = 97.7% [88.2%, 99.6%]
        recall statute              129/129 = 100.0% [97.1%, 100.0%]
        recall case                 0/0 (no rows)
        recall clarify              0/0 (no rows)
        recall out_of_scope         14/14 = 100.0% [78.5%, 100.0%]
      confusion (rows: expected; columns: predicted)
                           handbook      statute         case      clarify out_of_scope        other
        han
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_desk_s_offline_check.
COMMANDS_02 = """make desk-check   # the first run makes ~/graph-venv and installs the chat image's pins into it

"""

def step_02_the_desk_s_offline_check(session):
    """Run Do it: the Desk's offline check at this checkpoint.

    make desk-check is the proof that the Desk's code holds, with no lane and no cost. It checks that the route set is the one evals/build_routes.py builds and that every row is sound, runs the self-tests and unit tests of the eval and the probe, runs the router on the dev rows as the cell above did, checks that the threshold sweep counts right, and checks that every calculator rule says what its line of the corpus says. Then it runs the chat service's tests for the case queue, the router and the desk graph, which need the chat image's libraries: the first run makes ~/graph-venv and installs services/chat/requirements.txt into it, which takes a few minutes. Every line must pass; a failing one stops the run.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the Desk's offline check: no lane, no cost; the first run installs ~/graph-venv).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: routes.jsonl: 207 derived rows (golden 65, paraphrases 42, SFT rewrites 100), 0 hand-written; checked, all 207 valid
    evals/routes.jsonl: 207 rows
      route            dev  test
      handbook          51     0
      statute          138     0
      case               0     0
      clarify            0     0
      out_of_scope      18     0
      total            207     0
      Wilson: 20 of 20 -> 83.9%, 73 of 73 -> 95.0%, 75 of 75 -> 95.1%, 100 of 100 -> 96.3%
      kNN: no dev row retrieves its own id, group or text (leave-one-group-out over 207 dev rows)
    no cross-split pair
    route_probe selftest: the four facts read correctly from canned yes, partial, no and error responses; 5 calls per probe
    ------------------------------
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_47', step_01_the_router_on_every_dev_row_on_your_machin),
        ('source_49', step_02_the_desk_s_offline_check),
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
