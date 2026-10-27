"""Lesson 5.8: The approval wired in: a withdrawal paused on your lane, decided over REST, run by you

The whole flow runs on the kit's own chat service with a fake Firestore and a scripted model, at Rs 0: the switch off, then on; the pause and its record; the hold; the requester's own approval refused; another company's approver and a colleague without the role seeing nothing; the second person's approval; a rejection beside a search; a question only the asker answers; an expired record, and the hold ending its pause; a lost pause; and --approved on the record. 18 tests, in ~/graph-venv from step 4. make agent-actions writes agent_actions into acme's tenant_settings, beside the Desk's switches, and prints them; the chat service reads it within a minute. make roles gives documind-evalacme-sa the doc_approver role beside employee: the eval account stands in for a colleague who may approve, as it stood in for an acme employee in lesson 5.6. The requester will be documind-ui-sa, on acme's roster since lesson 5.1's smoke. make smoke-approval runs the flow once against your chat service, printing each step. As documind-ui-sa it asks the LangGraph brain to withdraw townhall_2026_q1.md, a small acme document: the turn pauses, and the reply carries the record. The same session's next question is held. The requester's own approval is refused. documind-evalzeta-sa, on zeta's roster, cannot tell the record exists. The approver's list shows it. documind-evalacme-sa approves it, and the turn resumes: the tool runs, records the approved withdrawal, and the model answers that the operator will run it. A second decision is refused. Then a second withdrawal on a new session, which the approver rejects with a reason: the call errors alone and the model says nothing was withdrawn. The smoke withdraws nothing; it ends by printing your next two commands. The approval queued the work; you run it. The cell reads the approved record's id as the requester, runs make withdraw-run for it, and lists acme's sources, where the document's ledger row now says withdrawn. Acme's approval records from Firestore, oldest first, and today's approval events in the audit bucket, read without the chat service. make restore lifts the tombstone, as lesson 1.7 showed, and the worker returns the document. Then make agent-actions writes off, and acme's LangGraph brain is again the one lessons 5.4, 5.5 and 5.7 show, within a minute.

Run order inside this file:
1. Do it: the kit's own tests, offline (source window 51)
2. Do it: switch acme on, and name the second person (source window 53)
3. Do it: the flow, live (source window 55)
4. Do it: run the approved withdrawal (source window 57)
5. Do it: the records and the events, read directly (source window 59)
6. Do it: bring the document back, and switch acme off (source window 61)

Prerequisites: demo_07_the_rows_the_case_and_your_role_read_directly.
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


# Original CLI workflow for step_01_the_kit_s_own_tests_offline.
COMMANDS_01 = """~/graph-venv/bin/python -m unittest commands/tests/test_approval_wired.py -v

"""

def step_01_the_kit_s_own_tests_offline(session):
    """Run Do it: the kit's own tests, offline at this checkpoint.

    The whole flow runs on the kit's own chat service with a fake Firestore and a scripted model, at Rs 0: the switch off, then on; the pause and its record; the hold; the requester's own approval refused; another company's approver and a colleague without the role seeing nothing; the second person's approval; a rejection beside a search; a question only the asker answers; an expired record, and the hold ending its pause; a lost pause; and --approved on the record. 18 tests, in ~/graph-venv from step 4.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the wired approval's own tests, offline, in ~/graph-venv from step 4).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: test_an_event_the_bucket_refused_waits_on_the_record (commands.tests.test_approval_wired.Records.test_an_event_the_bucket_refused_waits_on_the_record) ... ok
    test_expired_is_410_and_decided_is_409_checked_in_code (commands.tests.test_approval_wired.Records.test_expired_is_410_and_decided_is_409_checked_in_code) ... ok
    test_one_pause_is_one_record_with_one_event (commands.tests.test_approval_wired.Records.test_one_pause_is_one_record_with_one_event) ... ok
    test_recheck_refuses_before_the_tombstone (commands.tests.test_approval_wired.Records.test_recheck_refuses_before_the_tombstone) ... ok
    test_the_executor_records_and_withdraws_nothing (commands.tests.test_approval_wired.Records.test_the_exe
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_switch_acme_on_and_name_the_second_person.
COMMANDS_02 = """sa() { echo "documind-$1-sa@$PROJECT.iam.gserviceaccount.com"; }
make agent-actions PROJECT="$PROJECT" TENANT=acme AGENT_ACTIONS=approval
make roles PROJECT="$PROJECT" TENANT=acme EMAIL="$(sa evalacme)" ROLES=employee,doc_approver

"""

def step_02_switch_acme_on_and_name_the_second_person(session):
    """Run Do it: switch acme on, and name the second person at this checkpoint.

    make agent-actions writes agent_actions into acme's tenant_settings, beside the Desk's switches, and prints them; the chat service reads it within a minute. make roles gives documind-evalacme-sa the doc_approver role beside employee: the eval account stands in for a colleague who may approve, as it stood in for an acme employee in lesson 5.6. The requester will be documind-ui-sa, on acme's roster since lesson 5.1's smoke.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's agent_actions to approval; doc_approver for documind-evalacme-sa).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/switch.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_flow_live.
COMMANDS_03 = """make smoke-approval PROJECT="$PROJECT" TENANT=acme

"""

def step_03_the_flow_live(session):
    """Run Do it: the flow, live at this checkpoint.

    make smoke-approval runs the flow once against your chat service, printing each step. As documind-ui-sa it asks the LangGraph brain to withdraw townhall_2026_q1.md, a small acme document: the turn pauses, and the reply carries the record. The same session's next question is held. The requester's own approval is refused. documind-evalzeta-sa, on zeta's roster, cannot tell the record exists. The approver's list shows it. documind-evalacme-sa approves it, and the turn resumes: the tool runs, records the approved withdrawal, and the model answers that the operator will run it. A second decision is refused. Then a second withdrawal on a new session, which the approver rejects with a reason: the call errors alone and the model says nothing was withdrawn. The smoke withdraws nothing; it ends by printing your next two commands.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the whole flow once, against your chat service; about Rs 10-15).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_approval.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_run_the_approved_withdrawal.
COMMANDS_04 = """APPROVAL="$(TOKEN="$(etok ui)" python - <<'PY'
import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
req = urllib.request.Request(os.environ["CHAT"] + "/v1/approvals", headers={"Authorization": "Bearer " + os.environ["TOKEN"]})
mine = json.load(urllib.request.urlopen(req, timeout=60))["mine"]
print(next(r["approval_id"] for r in mine if r["status"] == "approved"))
PY
)"
echo "approval $APPROVAL"
make withdraw-run PROJECT="$PROJECT" APPROVAL="$APPROVAL"
make sources PROJECT="$PROJECT" TENANT_ONLY=acme | grep -E "^source|townhall_2026_q1"

"""

def step_04_run_the_approved_withdrawal(session):
    """Run Do it: run the approved withdrawal at this checkpoint.

    The approval queued the work; you run it. The cell reads the approved record's id as the requester, runs make withdraw-run for it, and lists acme's sources, where the document's ledger row now says withdrawn.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the approved record's id, your run of it, and acme's sources).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/withdraw.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def step_05_the_records_and_the_events_read_directly(session):
    """Run Do it: the records and the events, read directly at this checkpoint.

    Acme's approval records from Firestore, oldest first, and today's approval events in the audit bucket, read without the chat service.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's approval records and today's approval events, from Firestore and the bucket).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/approvals.txt]
    """
    import datetime as dt, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore, storage
    db = firestore.Client(project=os.environ["PROJECT"])
    rows = sorted((s.to_dict() for s in db.collection("approvals").where("tenant", "==", "acme").stream()), key=lambda r: r["created_at"])
    def who(email):
        """An email's local part, the domain elided; - for nobody.
        
        Example: who(r['requester'])
        """
        return email.split("@")[0] + "@..." if email else "-"
    for r in rows:
        print(f"  approvals/{r['approval_id']}")
        print(f"    {r['status']:10} kind {r['kind']}  waiting {[w['tool'] for w in r['waiting']]}  session {r['session_id']}")
        print(f"    asked by {who(r['requester'])}, decided by {who(r.get('decided_by'))}, audit_pending {r.get('audit_pending')}")
        if r.get("withdrawal"):
            w = r["withdrawal"]
            print(f"    withdrawal {w['tenant']}/{w['name']}, approved by {who(w['approved_by'])}, run by {who(r.get('run_by'))}, {r['status']}")
    today = dt.datetime.now(dt.timezone.utc).strftime("%Y/%m/%d")
    blobs = storage.Client(project=os.environ["PROJECT"]).list_blobs(os.environ["PROJECT"] + "-audit", prefix=f"{today}/acme/")
    events = sorted(b.name.rsplit("/", 1)[1].split("-", 1)[0] for b in blobs)
    print("  today's acme events in the audit bucket:", [e for e in events if e.startswith("approval.") or e == "doc.withdraw"])

# Original CLI workflow for step_06_bring_the_document_back_and_switch_acme_of.
COMMANDS_06 = """make restore PROJECT="$PROJECT" SOURCE=acme/townhall_2026_q1.md
make agent-actions PROJECT="$PROJECT" TENANT=acme AGENT_ACTIONS=off

"""

def step_06_bring_the_document_back_and_switch_acme_of(session):
    """Run Do it: bring the document back, and switch acme off at this checkpoint.

    make restore lifts the tombstone, as lesson 1.7 showed, and the worker returns the document. Then make agent-actions writes off, and acme's LangGraph brain is again the one lessons 5.4, 5.5 and 5.7 show, within a minute.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the document back, and acme's switch off).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/restore.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_51', step_01_the_kit_s_own_tests_offline),
        ('source_53', step_02_switch_acme_on_and_name_the_second_person),
        ('source_55', step_03_the_flow_live),
        ('source_57', step_04_run_the_approved_withdrawal),
        ('source_59', step_05_the_records_and_the_events_read_directly),
        ('source_61', step_06_bring_the_document_back_and_switch_acme_of),
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
