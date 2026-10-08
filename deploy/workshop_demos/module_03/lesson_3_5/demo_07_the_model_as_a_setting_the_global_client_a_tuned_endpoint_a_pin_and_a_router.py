"""Lesson 3.5: The model as a setting: the global client, a tuned endpoint, a pin and a router

Read the lane, Rs 0

Run order inside this file:
1. Read the lane, Rs 0 (source window 32)

Prerequisites: demo_06_the_model_call_by_hand_the_schema_the_thinking_the_usage_the_price.
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


# Original CLI workflow for step_01_read_the_lane_rs_0.
COMMANDS_01 = """python commands/lane.py tenant-backend acme
python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google.cloud import firestore
ts = firestore.Client(project=os.environ["PROJECT"]).collection("tenant_settings").document("acme").get().to_dict() or {}
print("acme's tenant_settings:", {k: ts.get(k) for k in ("generator_model", "model_backend", "retrieval_backend", "data_region")})
PY
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND (jsonPayload.event="tier_exhausted" OR jsonPayload.event="routing_fallback")' \\
  --project "$PROJECT" --freshness 7d --limit 3 --format='value(timestamp,jsonPayload.event,jsonPayload.model,jsonPayload.fallback)'

"""

def step_01_read_the_lane_rs_0(session):
    """Run Read the lane, Rs 0 at this checkpoint.

    Read the lane, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (three reads).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme: retrieval_backend=vector
    acme's tenant_settings: {'generator_model': None, 'model_backend': None, 'retrieval_backend': 'vector', 'data_region': 'any'}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_32', step_01_read_the_lane_rs_0),
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
