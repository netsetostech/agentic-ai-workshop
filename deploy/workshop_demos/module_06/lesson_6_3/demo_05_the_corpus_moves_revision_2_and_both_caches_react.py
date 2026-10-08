"""Lesson 6.3: The corpus moves: revision 2, and both caches react

Do it: the release Do it: the state, both asks, and the log

Run order inside this file:
1. Do it: the release (source window 17)
2. Do it: the state, both asks, and the log (source window 19)

Prerequisites: demo_04_scope_the_same_words_under_other_settings.
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


# Original CLI workflow for step_01_the_release.
COMMANDS_01 = """make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/demo/hr_policy_2026_v2.md NAME=hr_policy_2026.md

"""

def step_01_the_release(session):
    """Run Do it: the release at this checkpoint.

    Do it: the release

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (revision 2 of the handbook, as a release).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
    >> event doc_key chunks reused embedded retired effective_from
    >> ingest_reactivated	acme_5560308823a62dc8...	283	283	0	283
    >> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_state_both_asks_and_the_log.
COMMANDS_02 = """state92
ask92 "$API"            # the live revision
ask92 "$CAND"           # the candidate
python - <<'PY'
import json, os, subprocess
f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="cache_stale" '
     f'AND timestamp>="{os.environ["SINCE92"]}"')
out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "5",
                      "--format", "json"], capture_output=True, text=True, check=True).stdout
for e in json.loads(out or "[]"):
    j = e["jsonPayload"]
    print(f"  cache_stale {j['tenant']}: packed from {j['cache_fingerprint']}, ledger now {j['ledger_fingerprint']}")
PY

"""

def step_02_the_state_both_asks_and_the_log(session):
    """Run Do it: the state, both asks, and the log at this checkpoint.

    Do it: the state, both asks, and the log

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the state, both asks again, and the API's cache_stale lines).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ledger 1441fb4775d21e13 (17 versions, last ingest_reactivated) | context cache packed from 1ef46119bd89b143: STALE
      vertex none     in   1880 cached      0  2390 ms | From 1 October 2026 the notice period for a confir
      vertex none     in   1880 cached      0  2455 ms | From 1 October 2026 the notice period for a confir
      cache_stale acme: packed from 1ef46119bd89b143, ledger now 1441fb4775d21e13
      cache_stale acme: packed from 1ef46119bd89b143, ledger now 1441fb4775d21e13
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_the_release),
        ('source_19', step_02_the_state_both_asks_and_the_log),
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
