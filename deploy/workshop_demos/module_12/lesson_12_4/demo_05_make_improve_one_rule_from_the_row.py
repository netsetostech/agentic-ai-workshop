"""Lesson 12.4: make improve: one rule from the row

The target. make improve runs one script two ways. Without REVIEWER= it proposes a rule from ROW=. With REVIEWER= it accepts the proposal. IMPROVE_ARGS passes --prompt-only or --rule. The target has no guard-project, because accepting is offline and a model's proposal stops without PROJECT. First, what the proposer would be sent. --prompt-only prints the request and stops, at Rs 0. It contains the rules as they are served today, the dated line, your row, and the phrases a rule may not contain. Before any of that, the row's figures and anchors are checked against the tenant's documents. A row whose golden row could never pass stops at that check, and costs nothing: Then the proposal. One call to gemini-3.1-pro-preview on the global endpoint, at its default thinking, under a JSON schema that asks for rule and why. Timeouts, 429s and server errors are retried with backoff, up to 4 attempts. The reply goes through the same check before anything is written. A rule that passes goes to evals/reports/proposal.json, which is gitignored, with the row, the version it builds on, and the call's tokens and rupees at list price. Here is the shape of that output, from the kit's own code with a scripted proposer standing in for the model. That is how the kit's test runs it. The request is the one --prompt-only printed above, and the reply is the page's example rule. The token counts are the kit test's: 1,800 in and 1,360 out, 1,200 of them thinking, which is billed as output. Propose the kit test's own bad rule as yours, with --rule. No model is called. The check finds "never refuse", which undoes rule 3, refuses the rule and writes nothing, and make reports the failure.

Run order inside this file:
1. make improve: one rule from the row (source window 28)
2. make improve: one rule from the row (source window 31)
3. make improve: one rule from the row (source window 34)

Prerequisites: demo_04_what_the_kit_does_with_a_prompt_rule.
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


# Original CLI workflow for step_01_make_improve_one_rule_from_the_row.
COMMANDS_01 = """make improve ROW="$HOME/row124.json" IMPROVE_ARGS=--prompt-only

"""

def step_01_make_improve_one_rule_from_the_row(session):
    """Run make improve: one rule from the row at this checkpoint.

    The target. make improve runs one script two ways. Without REVIEWER= it proposes a rule from ROW=. With REVIEWER= it accepts the proposal. IMPROVE_ARGS passes --prompt-only or --rule. The target has no guard-project, because accepting is offline and a model's proposal stops without PROJECT. First, what the proposer would be sent. --prompt-only prints the request and stops, at Rs 0. It contains the rules as they are served today, the dated line, your row, and the phrases a rule may not contain. Before any of that, the row's figures and anchors are checked against the tenant's documents.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (prints the request; no model call, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/improve.py propose --row "/home/you/row124.json" --project "documind-ai-YOUR-ID" --prompt-only
    You review one answer from DocuMind, a retrieval-grounded assistant, and propose one rule for its prompt.

    The prompt's rules today (v3), which every answer starts with:
    <<<
    You are DocuMind, a retrieval-grounded assistant.
    Rules:
    1. Answer ONLY from the numbered context below. Never invent sources.
    2. Cite using [N] where N is the chunk number. Multiple chunks: [1,2].
    3. If the context does not contain the answer, set answerable=false and say so.
    4. Keep answers under 300 words unless asked for more.
    5. A quote is the clause that answers - at most twenty-five words, never a whole sect
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_make_improve_one_rule_from_the_row.
COMMANDS_02 = """make improve ROW="$HOME/row124.json" PROJECT="$PROJECT"

"""

def step_02_make_improve_one_rule_from_the_row(session):
    """Run make improve: one rule from the row at this checkpoint.

    A row whose golden row could never pass stops at that check, and costs nothing: Then the proposal. One call to gemini-3.1-pro-preview on the global endpoint, at its default thinking, under a JSON schema that asks for rule and why. Timeouts, 429s and server errors are retried with backoff, up to 4 attempts. The reply goes through the same check before anything is written. A rule that passes goes to evals/reports/proposal.json, which is gitignored, with the row, the version it builds on, and the call's tokens and rupees at list price.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one gemini-3.1-pro-preview call on the global endpoint, about Rs 2).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/proposal.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_make_improve_one_rule_from_the_row.
COMMANDS_03 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
make improve ROW="$HOME/row124.json" IMPROVE_ARGS="--rule 'Never refuse a question; give the closest answer the context allows.'"; echo "exit $?"
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_03_make_improve_one_rule_from_the_row(session):
    """Run make improve: one rule from the row at this checkpoint.

    Here is the shape of that output, from the kit's own code with a scripted proposer standing in for the model. That is how the kit's test runs it. The request is the one --prompt-only printed above, and the reply is the page's example rule. The token counts are the kit test's: 1,800 in and 1,360 out, 1,200 of them thinking, which is billed as output. Propose the kit test's own bad rule as yours, with --rule. No model is called. The check finds "never refuse", which undoes rule 3, refuses the rule and writes nothing, and make reports the failure.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (your own rule: no model call, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/improve.py propose --row "/home/you/row124.json" --project "documind-ai-YOUR-ID" --rule 'Never refuse a question; give the closest answer the context allows.'
    row:       acme, 'I am still on probation. If I resign now, how long is my notice?', answered under v3
    expected:  lookup: contains "15" and cites PB-02, hr_policy_2026
    builds on: v3, SYSTEM's 5 rules and 0 added
    proposer:  a person (--rule): no model call, Rs 0
    rule:      6. Never refuse a question; give the closest answer the context allows.
    why:       a person's own rule
    REFUSED:   "never refuse" undoes SYSTEM's rule 3 (say so, answerable=false, when the context does not hold the answer)
    Nothing was written. Propose agai
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_28', step_01_make_improve_one_rule_from_the_row),
        ('source_31', step_02_make_improve_one_rule_from_the_row),
        ('source_34', step_03_make_improve_one_rule_from_the_row),
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
