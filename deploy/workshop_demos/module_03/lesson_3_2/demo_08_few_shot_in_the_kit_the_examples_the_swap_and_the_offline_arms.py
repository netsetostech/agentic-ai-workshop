"""Lesson 3.2: Few-shot in the kit: the examples, the swap and the offline arms

Do it, offline: the swap, and the rows it scores LOCAL=1 runs the same eval with route_eval.py's scripted classifier and offline embeddings: no project and no cost. The scripted L1 gives each row its own label, deliberately wrong on about one row in eight, and reads no example. So offline the two arms must agree on every route. What differs is the prompt's length, and so the router's cost.

Run order inside this file:
1. Do it, offline: the swap, and the rows it scores (source window 40)
2. Do it, offline: both arms on the scripted classifier (source window 42)
3. Do it, offline: both arms on the scripted classifier (source window 44)

Prerequisites: demo_07_change_it_one_prompted_reasoning_rule_against_native_thinking.
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


def step_01_offline_the_swap_and_the_rows_it_scores(session):
    """Run Do it, offline: the swap, and the rows it scores at this checkpoint.

    Do it, offline: the swap, and the rows it scores

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: with the examples: 2,121 characters, 8 example lines
    inside the swap:   1,576 characters, 0 example lines
    every other line unchanged: True
    after the swap, the kit's tuple again: True
    207 dev rows: 20 in the examples' 8 groups, out of every arm's score; 187 scored
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, "evals")
    import route_eval
    desk_router, desk_routes = route_eval.router()
    QUESTION = "What is the per-trip cap on domestic travel reimbursement?"
    
    
    def example_lines(prompt):
        """The L1 prompt's example lines: <<<question>>> desk.
        
        Example: example_lines(kit)
        """
        return [line for line in prompt.splitlines() if line.startswith("<<<")]
    
    
    kit = desk_router.prompt(QUESTION)
    with route_eval.exemplars_in_prompt(desk_router, ()):
        bare = desk_router.prompt(QUESTION)
    print(f"with the examples: {len(kit):,} characters, {len(example_lines(kit))} example lines")
    print(f"inside the swap:   {len(bare):,} characters, {len(example_lines(bare))} example lines")
    print("every other line unchanged:", [line for line in kit.splitlines() if line not in example_lines(kit)] == bare.splitlines())
    print("after the swap, the kit's tuple again:", desk_router.PROMPT_EXEMPLARS is desk_routes.PROMPT_EXEMPLARS)
    rows = route_eval.load_rows()
    held = route_eval.prompt_groups(rows)
    dev = [r for r in rows if r["split"] == "dev"]
    print(f"{len(dev)} dev rows: {sum(r['group'] in held for r in dev)} in the examples' {len(held)} groups, out of every arm's score; "
          f"{sum(r['group'] not in held for r in dev)} scored")

# Original CLI workflow for step_02_offline_both_arms_on_the_scripted_classifi.
COMMANDS_02 = """make exemplars LOCAL=1

"""

def step_02_offline_both_arms_on_the_scripted_classifi(session):
    """Run Do it, offline: both arms on the scripted classifier at this checkpoint.

    LOCAL=1 runs the same eval with route_eval.py's scripted classifier and offline embeddings: no project and no cost. The scripted L1 gives each row its own label, deliberately wrong on about one row in eight, and reads no example. So offline the two arms must agree on every route. What differs is the prompt's length, and so the router's cost.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (offline: no project, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/route_eval.py --local --exemplars kit
    local: the classifier is scripted, so this measures the cascade, not a model
      187 rows scored; 20 left out (the groups of the prompt's examples); index of 198 dev rows
      exemplars: the kit's own, desk_routes.PROMPT_EXEMPLARS - 8 in the L1 prompt; the rows of the kit's 8 stay out of the score in every arm
    arm B (the routed Desk)
    split dev
      top-1 route accuracy          186/187 = 99.5% [97.0%, 99.9%]
        recall handbook             43/44 = 97.7% [88.2%, 99.6%]
        recall statute              129/129 = 100.0% [97.1%, 100.0%]
        recall case                 0/0 (no rows)
        recall clarify              0/0 (no rows)
        recall out_of_scope    
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_offline_both_arms_on_the_scripted_classifi.
COMMANDS_03 = """make exemplars LOCAL=1 EXEMPLARS=none

"""

def step_03_offline_both_arms_on_the_scripted_classifi(session):
    """Run Do it, offline: both arms on the scripted classifier at this checkpoint.

    LOCAL=1 runs the same eval with route_eval.py's scripted classifier and offline embeddings: no project and no cost. The scripted L1 gives each row its own label, deliberately wrong on about one row in eight, and reads no example. So offline the two arms must agree on every route. What differs is the prompt's length, and so the router's cost.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (offline, the examples out: Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/route_eval.py --local --exemplars none
    ...
      exemplars: none - 0 in the L1 prompt; the rows of the kit's 8 stay out of the score in every arm
    ...
      router cost                   Rs 3.4761 in all, Rs 0.01859 a turn
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_40', step_01_offline_the_swap_and_the_rows_it_scores),
        ('source_42', step_02_offline_both_arms_on_the_scripted_classifi),
        ('source_44', step_03_offline_both_arms_on_the_scripted_classifi),
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
