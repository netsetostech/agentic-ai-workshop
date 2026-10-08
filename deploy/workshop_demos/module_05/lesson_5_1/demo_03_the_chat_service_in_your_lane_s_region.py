"""Lesson 5.1: The chat service, in your lane's region

Do it: deploy Do it: where it points, and its brains

Run order inside this file:
1. Do it: deploy (source window 6)
2. Do it: where it points, and its brains (source window 8)

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


# Original CLI workflow for step_01_deploy.
COMMANDS_01 = """make deploy-services PROJECT="$PROJECT" REGION="$REGION" SCRIPTS=commands/lesson-12.8.sh ADMIN_EMAILS="$ME"

"""

def step_01_deploy(session):
    """Run Do it: deploy at this checkpoint.

    Do it: deploy

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the chat service built and deployed in your region; several minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> commands/lesson-12.8.sh (DEPLOY block)
    Creating temporary archive of ... file(s) totalling ... MiB before compression.
    ...
    DONE ... asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/chat:COMMIT
    Deploying container to Cloud Run service [documind-chat] in project [documind-ai-YOUR-ID] region [asia-south1]
    ...
    Service URL: https://documind-chat-NUMBER.asia-south1.run.app
    Updated IAM policy for service [documind-chat].   (seven times, one per account: documind-ui-sa, documind-outsider-sa, documind-evalacme-sa,
       documind-evalzeta-sa, documind-evalglobex-sa, documind-evalleaver-sa,
       documind-evalgrc-sa)
    >> documind-gchat-sa does not exist yet (terraform/desk.tf: make plan up; documind
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_where_it_points_and_its_brains.
COMMANDS_02 = """export CHAT="https://documind-chat-$NUMBER.$REGION.run.app"
gcloud run services describe documind-chat --region "$REGION" --project "$PROJECT" --format=json \\
  | python -c 'import json, sys; s = json.load(sys.stdin); env = {e["name"]: e.get("value") for e in s["spec"]["template"]["spec"]["containers"][0].get("env", [])}; print("  RAG_API_URL", env.get("RAG_API_URL"), "| SELF_URL", env.get("SELF_URL"), "| DOCUMIND_BRAIN", env.get("DOCUMIND_BRAIN"))'
curl -s "$CHAT/health" -H "Authorization: Bearer $(tok "$CHAT")"; echo

"""

def step_02_where_it_points_and_its_brains(session):
    """Run Do it: where it points, and its brains at this checkpoint.

    Do it: where it points, and its brains

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (where the chat service points, and its brains).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: RAG_API_URL https://documind-api-NUMBER.asia-south1.run.app | SELF_URL https://documind-chat-NUMBER.asia-south1.run.app | DOCUMIND_BRAIN langchain
    {"status":"ok","profile":"gcp","brains":["langchain","langgraph","adk","direct"],"default_brain":"langchain","limits":{"max_model_calls":12,"budget_inr":5.0,"deadline_s":100.0,"model_timeout_s":30.0,"model_attempts":2,"min_model_s":5.0,"tool_budgets_s":{"retrieve":95.0,"calculate_processing_cost":10}}}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_deploy),
        ('source_8', step_02_where_it_points_and_its_brains),
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
