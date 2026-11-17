"""Lesson 11.4: Trace it, name the cause, put it back

At lesson end: Do it: put version 1 back

Run order inside this file:
1. Do it: put version 1 back (source window 20)

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


# Original CLI workflow for step_01_put_version_1_back.
COMMANDS_01 = """CUR="$(python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore")
from google.cloud import firestore
rows = firestore.Client(project=os.environ["PROJECT"]).collection("sources").where("tenant_id", "==", "acme").stream()
print(next((r.to_dict().get("doc_key") or "" for r in rows if (r.to_dict().get("name") or "").endswith("hr_policy_2026.md")), ""))
PY
)"
if [ "$CUR" != "acme_$(sha256sum evals/corpus/acme/hr_policy_2026.md | cut -c1-64)" ]; then
  make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/corpus/acme/hr_policy_2026.md
else echo "acme's handbook is already version 1: nothing to put back"; fi
type ask131 >/dev/null 2>&1 && ask131 restored   # the lesson's question, when its helper is defined
GOOGLE_CLOUD_PROJECT="$PROJECT" python commands/check-firestore-fallback.py | tail -1

"""

def step_01_put_version_1_back(session):
    """Run Do it: put version 1 back at this checkpoint.

    Do it: put version 1 back

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (version 1 back, the question again, the probe again).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
    >> event doc_key chunks reused embedded retired effective_from
    >> ingest_reactivated	acme_497809ffbaa603c4...	283	283	0	283
    >> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
    A confirmed employee at grade E3 or above serves a notice period of 60 days [1].
      [1] hr_policy_2026.md  version 497809ffbaa6  chunk 1  'serves a notice period of 60 days'
      cache_hit none | backend vertex | answerable True
      store vector | vector_chunks 20 | pool 20 | rerank_fallback 0 | policy_fallback 0
      kept in ~/ask131-restored
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_put_version_1_back),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=True, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
