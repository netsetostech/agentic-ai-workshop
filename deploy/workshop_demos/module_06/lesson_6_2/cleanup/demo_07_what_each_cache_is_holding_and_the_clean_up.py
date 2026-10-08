"""Lesson 6.2: What each cache is holding, and the clean-up

At lesson end: The cell prints tenant_caches/acme, then the answer-cache entry for the question's words. It uses the kit's own qhash, imported from services/rag-api, so the key is computed exactly as the API computes it. The two records show where each cache keeps its weight. For the context cache, Firestore holds only a pointer and a few facts, and the pack's forty-odd thousand tokens sit on Google's side, billed by the hour until they expire or are deleted. For the answer cache, Firestore holds everything: the answer, its citations and the question's 768-number embedding. That costs Firestore storage and reads, for 24 hours. The clean-up removes the candidate's tag and recorded name, and deletes the context cache. The next acme question to the live API finds no record and runs uncached at once.

Run order inside this file:
1. What each cache is holding, and the clean-up (source window 31)

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


# Original CLI workflow for step_01_what_each_cache_is_holding_and_the_clean_u.
COMMANDS_01 = """gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
rm -f .candidate-revision      # make promote would otherwise flip traffic to the recorded revision
make cache PROJECT="$PROJECT" TENANT=acme CACHE_OP=delete

"""

def step_01_what_each_cache_is_holding_and_the_clean_u(session):
    """Run What each cache is holding, and the clean-up at this checkpoint.

    The cell prints tenant_caches/acme, then the answer-cache entry for the question's words. It uses the kit's own qhash, imported from services/rag-api, so the key is computed exactly as the API computes it. The two records show where each cache keeps its weight. For the context cache, Firestore holds only a pointer and a few facts, and the pack's forty-odd thousand tokens sit on Google's side, billed by the hour until they expire or are deleted. For the answer cache, Firestore holds everything: the answer, its citations and the question's 768-number embedding. That costs Firestore storage and reads, for 24 hours. The clean-up removes the candidate's tag and recorded name, and deletes the context cache. The next acme question to the live API finds no record and runs uncached at once.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the candidate's tag and recorded name removed, the context cache deleted).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Updating traffic...done.
    Done.
    URL: https://documind-api-...run.app
    Traffic:
      100% documind-api-00041-kqz      (the live revision, as before; no candidate tag)
    cd services/rag-api && GOOGLE_CLOUD_PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=gemini-3.6-flash \\
      python cache_admin.py ${CACHE_OP:-create} --project documind-ai-YOUR-ID --tenant acme
      deleted acme's cache
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_31', step_01_what_each_cache_is_holding_and_the_clean_u),
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
