"""Lesson 6.4: The replay: the same pairs, asked live at 0.95

Each question gets a second try, two seconds after a 5xx or a timeout, as the kit's own run_eval.py gives it: one retry separates a blip from an outage. A blip, such as the first request to a fresh revision failing once, shows as a line saying how many questions were answered on a second try. A question that fails twice is listed with its HTTP status, and the replay carries on without it. The status is all the client sees. The reason is in the API's own log, and this reads the last three tracebacks, with the revision that threw each one:

Run order inside this file:
1. Do it: the replay (source window 16)

Prerequisites: workshop setup; see this lesson README.
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


# Original CLI workflow for step_01_the_replay.
COMMANDS_01 = """gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND textPayload:"Traceback"' --project "$PROJECT" --freshness=30m --limit 3 --format='value(timestamp,resource.labels.revision_name,textPayload)'

"""

def step_01_the_replay(session):
    """Run Do it: the replay at this checkpoint.

    Each question gets a second try, two seconds after a 5xx or a timeout, as the kit's own run_eval.py gives it: one retry separates a blip from an outage. A blip, such as the first request to a fresh revision failing once, shows as a line saying how many questions were answered on a second try. A question that fails twice is listed with its HTTP status, and the replay carries on without it. The status is all the client sees. The reason is in the API's own log, and this reads the last three tracebacks, with the revision that threw each one:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, only if the replay listed questions with no answer (the API's last three tracebacks).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_the_replay),
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
