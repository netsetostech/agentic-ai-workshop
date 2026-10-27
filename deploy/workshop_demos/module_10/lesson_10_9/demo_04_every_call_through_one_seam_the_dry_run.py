"""Lesson 10.9: Every call through one seam: the dry run

Do it: up, printed Do it: one question, as each host is asked

Run order inside this file:
1. Do it: up, printed (source window 16)
2. Do it: one question, as each host is asked (source window 18)

Prerequisites: demo_03_what_up_stages_and_what_the_runtime_will_import.
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


# Original CLI workflow for step_01_up_printed.
COMMANDS_01 = """make managed-peer-up DRY_RUN=1 PROJECT="$PROJECT" REGION="$REGION"   # every call printed, none made: no credential, Rs 0

"""

def step_01_up_printed(session):
    """Run Do it: up, printed at this checkpoint.

    Do it: up, printed

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (up, every call printed and none made).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DRY RUN: every call printed, none made (up, project documind-ai-YOUR-ID)
    == up: the A2A peer on Agent Engine in asia-south1, as documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com ==
      would call: GET https://asia-south1-aiplatform.googleapis.com/v1/projects/documind-ai-YOUR-ID/locations/asia-south1/reasoningEngines  # any documind-managed-peer*
      would call: vertexai.Client(project='documind-ai-YOUR-ID', location='asia-south1').agent_engines.create(config={'display_name': 'documind-managed-peer'})
      would call: GET https://cloudresourcemanager.googleapis.com/v1/projects/documind-ai-YOUR-ID  # its number
      would call: POST https://iam.googleapis.com/v1/projects/documind-ai-YOUR-ID/
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_one_question_as_each_host_is_asked.
COMMANDS_02 = """make managed-peer-ask DRY_RUN=1 PROJECT="$PROJECT" REGION="$REGION"                 # the managed peer
make managed-peer-ask DRY_RUN=1 PROJECT="$PROJECT" REGION="$REGION" HOST=cloudrun    # the Cloud Run peer

"""

def step_02_one_question_as_each_host_is_asked(session):
    """Run Do it: one question, as each host is asked at this checkpoint.

    Do it: one question, as each host is asked

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one question, as each host is asked; nothing sent).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DRY RUN: every call printed, none made (ask, project documind-ai-YOUR-ID)
    == ask: the managed peer, as tenant acme's question ==
      would call: GET https://asia-south1-aiplatform.googleapis.com/v1/projects/documind-ai-YOUR-ID/locations/asia-south1/reasoningEngines  # any documind-managed-peer*
      would call: POST https://asia-south1-aiplatform.googleapis.com/v1/projects/NUMBER/locations/asia-south1/reasoningEngines/ENGINE_ID:streamQuery?alt=sse {"class_method": "async_stream_query", "input": {"user_id": "documind-ui-sa", "message": "After how many years of continuous service does gratuity become payable?"}}  # as documind-ui-sa
      question: After how many years of continuous service does gratui
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_up_printed),
        ('source_18', step_02_one_question_as_each_host_is_asked),
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
