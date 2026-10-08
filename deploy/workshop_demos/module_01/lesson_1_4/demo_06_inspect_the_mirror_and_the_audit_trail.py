"""Lesson 1.4: Inspect the mirror and the audit trail

Read the mirror rows, then the audit event

Run order inside this file:
1. Read the mirror rows, then the audit event (source window 32)

Prerequisites: demo_05_inspect_vector_search_the_datapoint_its_restricts_and_a_search_for_itself.
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


# Original CLI workflow for step_01_read_the_mirror_rows_then_the_audit_event.
COMMANDS_01 = """bq --project_id="$PROJECT" query --use_legacy_sql=false --format=pretty \\
  "SELECT chunk_id, heading_path, kind, doc_type, pii_flag, FORMAT_TIMESTAMP('%H:%M:%S', ingested_at) AS at
   FROM \\`$BQ_CHUNK_TABLE\\` WHERE tenant_id = 'acme' AND source_uri = 'gs://$PROJECT-uploads/acme/smoke_note_v1.md' ORDER BY chunk_id"

bq --project_id="$PROJECT" query --use_legacy_sql=false --format=pretty \\
  "SELECT COUNT(*) AS rows_ever, COUNT(DISTINCT source_uri) AS documents FROM \\`$BQ_CHUNK_TABLE\\` WHERE tenant_id = 'acme'"

gcloud storage cat "gs://$AUDIT_BUCKET/$(date -u +%Y/%m/%d)/acme/doc.upload-*.json" \\
  | python -c "import json,sys,hashlib,os; sha=hashlib.sha256(open(os.environ.get('NOTE', os.path.expanduser('~/lesson34_note.md')),'rb').read()).hexdigest(); [print(json.dumps(e, indent=1)) for e in map(json.loads, sys.stdin.read().replace('}{', '}\\n{').split('\\n')) if e['target']['id'].endswith(sha)]"

"""

def step_01_read_the_mirror_rows_then_the_audit_event(session):
    """Run Read the mirror rows, then the audit event at this checkpoint.

    Read the mirror rows, then the audit event

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (two BigQuery queries, then one read from the audit bucket).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: +--------------------------------------------------+---------------------------+------+----------+----------+----------+
    |                     chunk_id                     |       heading_path        | kind | doc_type | pii_flag |    at    |
    +--------------------------------------------------+---------------------------+------+----------+----------+----------+
    | acme:9c41d0e2b7f5...#0                           | NULL                      | text | unknown  |    false | 10:39:52 |
    | acme:9c41d0e2b7f5...#1                           | SM-01 - The smoke lantern | text | unknown  |    false | 10:39:52 |
    | acme:9c41d0e2b7f5...#2                           | SM-02 - The ladder        | text | unknown
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_32', step_01_read_the_mirror_rows_then_the_audit_event),
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
