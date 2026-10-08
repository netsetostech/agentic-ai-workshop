"""Lesson 3.8: The UI's account: what it may do, and the checks the page makes first

Do it: read the account's grants, Rs 0

Run order inside this file:
1. Do it: read the account's grants, Rs 0 (source window 33)

Prerequisites: demo_06_citations_the_pills_the_sources_and_the_link_signed_through_iam.
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


# Original CLI workflow for step_01_read_the_account_s_grants_rs_0.
COMMANDS_01 = """SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com"
echo "project roles:"; gcloud projects get-iam-policy "$PROJECT" --flatten=bindings --filter="bindings.members:serviceAccount:$SA" --format='value(bindings.role)'
has() { python -c "import json,sys; raw=sys.stdin.read(); m='serviceAccount:$SA'; j=json.loads(raw) if raw.strip() else None; print('no such service' if j is None else [b['role'] for b in j.get('bindings', []) if m in b.get('members', [])] or 'none')"; }
echo "uploads bucket: $(gcloud storage buckets get-iam-policy "gs://$PROJECT-uploads" --format=json | has)"
for S in documind-api documind-chat documind-ingest; do echo "may invoke $S: $(gcloud run services get-iam-policy "$S" --region "$REGION" --project "$PROJECT" --format=json 2>/dev/null | has)"; done
echo "on itself: $(gcloud iam service-accounts get-iam-policy "$SA" --project "$PROJECT" --format=json | has)"

"""

def step_01_read_the_account_s_grants_rs_0(session):
    """Run Do it: read the account's grants, Rs 0 at this checkpoint.

    Do it: read the account's grants, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: project roles:
    roles/aiplatform.user
    roles/datastore.user
    roles/documentai.apiUser
    roles/secretmanager.secretAccessor
    roles/speech.editor
    uploads bucket: ['roles/storage.objectAdmin']
    may invoke documind-api: ['roles/run.invoker']
    may invoke documind-chat: ['roles/run.invoker']
    may invoke documind-ingest: none
    on itself: ['roles/iam.serviceAccountTokenCreator']
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_33', step_01_read_the_account_s_grants_rs_0),
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
