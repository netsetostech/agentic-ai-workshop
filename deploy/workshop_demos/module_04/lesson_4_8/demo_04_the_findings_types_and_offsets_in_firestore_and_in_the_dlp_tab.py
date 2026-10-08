"""Lesson 4.8: The findings: types and offsets, in Firestore and in the DLP tab

Do it: the records The console sits behind IAP and admits only the addresses the lane was deployed with as ADMIN_EMAILS. If it answers 403 - Admins only, your address is not among them; the cell above has already read the records the tab draws.

Run order inside this file:
1. Do it: the records (source window 10)
2. Do it: the DLP tab (source window 12)

Prerequisites: demo_03_the_pii_scan_one_list_and_a_note_that_trips_it.
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


def step_01_the_records(session):
    """Run Do it: the records at this checkpoint.

    Do it: the records

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's newest findings records; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme/lesson83_vendor_note.md: 5 finding(s), INDIA_AADHAAR_INDIVIDUAL, INDIA_GST_INDIVIDUAL, INDIA_PAN_INDIVIDUAL, PERSON_NAME, PHONE_NUMBER
      acme/inv_2026_0412.md: 4 finding(s), EMAIL_ADDRESS, INDIA_GST_INDIVIDUAL, INDIA_PAN_INDIVIDUAL, PHONE_NUMBER
    one finding, whole: {'info_type': 'PERSON_NAME', 'likelihood': 'LIKELY', 'offset': 159, 'chunk_id': 'acme:SHA#0'}
    """
    import os
    from google.cloud import firestore
    db = firestore.Client(project=os.environ["PROJECT"])
    names = {s.get("doc_key"): s.get("name") for s in (d.to_dict() for d in db.collection("sources").stream())}
    rows = [d.to_dict() for d in db.collection("dlp_findings").order_by("scanned_at", direction=firestore.Query.DESCENDING).limit(50).stream()]
    acme = [r for r in rows if r.get("tenant_id") == "acme"]
    for r in acme[:4]:
        types = sorted({f["info_type"] for f in r["findings"]})
        print(f"  {names.get(r.get('doc_key')) or r.get('doc_key') or r.get('chunk_id')}: {r['count']} finding(s), {', '.join(types)}")
    print("one finding, whole:", acme[0]["findings"][0] if acme else "none yet")

# Original CLI workflow for step_02_the_dlp_tab.
COMMANDS_02 = """gcloud run services describe documind-admin --region "$REGION" --project "$PROJECT" --format='value(metadata.name)' >/dev/null 2>&1 \\
  && echo "https://documind-admin-$NUMBER.$REGION.run.app   <- open in your browser, then the DLP tab" \\
  || echo "documind-admin is not deployed on this lane"

"""

def step_02_the_dlp_tab(session):
    """Run Do it: the DLP tab at this checkpoint.

    The console sits behind IAP and admits only the addresses the lane was deployed with as ADMIN_EMAILS. If it answers 403 - Admins only, your address is not among them; the cell above has already read the records the tab draws.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the admin console's address).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: https://documind-admin-NUMBER.asia-south1.run.app   <- open in your browser, then the DLP tab
    """
    manual_checkpoint("Open the deployed admin DLP tab and inspect the synthetic note's findings. Type done to compare them with the source fields printed next.")
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_the_records),
        ('source_12', step_02_the_dlp_tab),
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
