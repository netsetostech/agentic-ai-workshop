"""Lesson 4.7: The policy against a pin: a tenant kept in India, pinned to a store outside it

A pin set, a minute's wait, one question, its usage row, and the pin cleared. The cell pins globex to rag_engine, a managed store in us-central1, then waits a minute, because the API reads each tenant's settings once a minute. It asks one of globex's own questions and reads the question's usage row: which backend served, and policy_fallback. Then it clears the pin. RETRIEVAL_BACKEND is given on each make line on purpose, because a value exported in your shell would otherwise win.

Run order inside this file:
1. The policy against a pin: a tenant kept in India, pinned to a store outside it (source window 19)

Prerequisites: demo_05_residency_each_tenant_s_data_region_and_the_rule_that_applies_it.
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


# Original CLI workflow for step_01_the_policy_against_a_pin_a_tenant_kept_in.
COMMANDS_01 = """make tenant-backend TENANT=globex RETRIEVAL_BACKEND=rag_engine
sleep 65                        # the API reads tenant_settings once a minute
TOKEN="$(tok "$API")" python - <<'PY'
import os, sys; sys.path.insert(0, "evals")
from run_eval import ask
status, body, _ = ask(os.environ["API"], "Who is a Data Fiduciary under the DPDP Act?", "globex", "eval@documind.in", os.environ["TOKEN"])
print(f"globex asked: HTTP {status}, answerable {body.get('answerable')}")
PY
sleep 20
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" AND jsonPayload.tenant="globex"' \\
  --project "$PROJECT" --freshness=10m --limit 1 --format='value(jsonPayload.retrieval_backend,jsonPayload.policy_fallback)'
make tenant-backend TENANT=globex RETRIEVAL_BACKEND=default

"""

def step_01_the_policy_against_a_pin_a_tenant_kept_in(session):
    """Run The policy against a pin: a tenant kept in India, pinned to a store outside it at this checkpoint.

    A pin set, a minute's wait, one question, its usage row, and the pin cleared. The cell pins globex to rag_engine, a managed store in us-central1, then waits a minute, because the API reads each tenant's settings once a minute. It asks one of globex's own questions and reads the question's usage row: which backend served, and policy_fallback. Then it clears the pin. RETRIEVAL_BACKEND is given on each make line on purpose, because a value exported in your shell would otherwise win.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a pin set, one question, its usage row, the pin cleared).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: globex: retrieval_backend=rag_engine
    globex asked: HTTP 200, answerable True
    vector	1
    globex: retrieval_backend=default
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_the_policy_against_a_pin_a_tenant_kept_in),
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
