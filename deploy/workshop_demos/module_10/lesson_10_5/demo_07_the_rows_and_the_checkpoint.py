"""Lesson 10.5: The rows and the checkpoint

Every POST /v1/desk turn logs one desk row from the chat service. It names every field it carries, and never the question. Two of its fields are easy to misread. mode is the company's: desk_route as the chat service read it, on for acme, not the section's agent or direct; a row shows agent mode by its tool_calls and refusals. arm is B unless an eval account sent another. The cell reads the rows since SINCE105: your two Desk page turns and evalacme's two. Run it in the shell where step 3 set SINCE105 and step 6 defined sa, a minute after step 6, so that Cloud Logging has the rows. Then make thread, lesson 6.8's reader of the chat service's Cloud SQL checkpoints, lists evalacme's threads, the latest first.

Run order inside this file:
1. The rows and the checkpoint (source window 34)

Prerequisites: demo_06_one_question_two_arms_over_rest.
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


# Original CLI workflow for step_01_the_rows_and_the_checkpoint.
COMMANDS_01 = """python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND '
     f'jsonPayload.event="desk" AND timestamp>="{os.environ["SINCE105"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc",
                      "--limit", "20", "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j = e["jsonPayload"]
    who = "evalacme" if str(j["user"]).startswith("documind-evalacme-sa@") else "you"
    print(f"{who:8} mode {j['mode']}  arm {j['arm']:5} route {j['route']:9} method {j['method']:8} outcome {j['outcome']}")
    print(f"         model_calls {j['model_calls']}  tool_calls {j['tool_calls']}  refusals {j['refusals']}"
          f"  cost_usd {j['cost_usd']}  latency_ms {j['latency_ms']}")
PY
make thread PROJECT="$PROJECT" EMAIL="$(sa evalacme)" | sed -n '1,6p'   # its label, then the latest threads first

"""

def step_01_the_rows_and_the_checkpoint(session):
    """Run The rows and the checkpoint at this checkpoint.

    Every POST /v1/desk turn logs one desk row from the chat service. It names every field it carries, and never the question. Two of its fields are easy to misread. mode is the company's: desk_route as the chat service read it, on for acme, not the section's agent or direct; a row shows agent mode by its tool_calls and refusals. arm is B unless an eval account sent another. The cell reads the rows since SINCE105: your two Desk page turns and evalacme's two. Run it in the shell where step 3 set SINCE105 and step 6 defined sa, a minute after step 6, so that Cloud Logging has the rows. Then make thread, lesson 6.8's reader of the chat service's Cloud SQL checkpoints, lists evalacme's threads, the latest first.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the Desk's rows since step 3, then evalacme's threads.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/desk_rows.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_34', step_01_the_rows_and_the_checkpoint),
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
