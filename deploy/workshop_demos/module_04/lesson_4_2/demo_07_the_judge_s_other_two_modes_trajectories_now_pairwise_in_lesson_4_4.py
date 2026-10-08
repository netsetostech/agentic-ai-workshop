"""Lesson 4.2: The judge's other two modes: trajectories now, pairwise in lesson 4.4

The chat service's tool calls against the one grounded path, and why the pairwise judge needs a candidate. With CHAT_URL, the judge sends a few answerable acme rows to each of the chat service's three brains, langchain, langgraph and adk. It compares the tool calls each brain returns with the reference path: one retrieve, then the answer. The three matches are computed in judge.py: exact, in order and any order. A brain that answers without retrieving scores 0 on all three, whatever its answer says. --no-vertex skips the Evaluation service, and --reuse skips asking the API again, so this costs only the chat turns. CHAT_URL is the service's documind-chat-NUMBER.REGION.run.app address, not the status.url gcloud prints, which is usually its hashed a.run.app address: the judge mints its token for CHAT_URL, and the chat service accepts only a token minted for its own SELF_URL.

Run order inside this file:
1. The judge's other two modes: trajectories now, pairwise in lesson 4.4 (source window 38)

Prerequisites: demo_06_where_the_gate_and_the_judge_disagree_read_the_row.
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


# Original CLI workflow for step_01_the_judge_s_other_two_modes_trajectories_n.
COMMANDS_01 = """if gcloud run services describe documind-chat --region "$REGION" --project "$PROJECT" --format='value(metadata.name)' >/dev/null 2>&1; then
  CHAT_URL="https://documind-chat-$NUMBER.$REGION.run.app"   # its SELF_URL, not status.url: the token is minted for it
  make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" CHAT_URL="$CHAT_URL" \\
    JUDGE_ARGS="--reuse evals/reports/judge72.json --no-vertex --trajectory-rows 3" | grep -E "reused|trajectory"
else echo "no documind-chat service on this lane: trajectories need one"; fi

"""

def step_01_the_judge_s_other_two_modes_trajectories_n(session):
    """Run The judge's other two modes: trajectories now, pairwise in lesson 4.4 at this checkpoint.

    The chat service's tool calls against the one grounded path, and why the pairwise judge needs a candidate. With CHAT_URL, the judge sends a few answerable acme rows to each of the chat service's three brains, langchain, langgraph and adk. It compares the tool calls each brain returns with the reference path: one retrieve, then the answer. The three matches are computed in judge.py: exact, in order and any order. A brain that answers without retrieving scores 0 on all three, whatever its answer says. --no-vertex skips the Evaluation service, and --reuse skips asking the API again, so this costs only the chat turns. CHAT_URL is the service's documind-chat-NUMBER.REGION.run.app address, not the status.url gcloud prints, which is usually its hashed a.run.app address: the judge mints its token for CHAT_URL, and the chat service accepts only a token minted for its own SELF_URL.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (nine chat turns if your lane has the chat service; nothing otherwise).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: no documind-chat service on this lane: trajectories need one
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_38', step_01_the_judge_s_other_two_modes_trajectories_n),
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
