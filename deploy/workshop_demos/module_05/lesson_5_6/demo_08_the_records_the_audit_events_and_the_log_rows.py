"""Lesson 5.6: The records, the audit events and the log rows

The case from step 7, the smoke's POSH record, and two role documents, read with the Firestore client. Today's case and role events in the audit bucket, the newest six, then the latest case.open and role.grant in full. Every desk_gate row since step 3, from both services.

Run order inside this file:
1. Do it: the records (source window 49)
2. Do it: the audit events (source window 51)
3. Do it: the log rows (source window 53)

Prerequisites: demo_07_the_case_routes_over_rest.
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

    The case from step 7, the smoke's POSH record, and two role documents, read with the Firestore client.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the case, the smoke's POSH case and two role documents, read from Firestore).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: cases/70356c174ba69ae3100d3d830531f27e
        grievance closed in grc, tenant acme, source button, via direct
        summary 'Lesson 5.6 test case: please close it.'  expire_at gone  audit_pending []  token_sha256 64 hex digits
      the smoke's posh case: withdrawn in ic:hyderabad, unit hyderabad, contacts ['you@example.com'], summary None, question_sha256 None
      tenants/acme/roles/you@...: ['employee', 'grc_member', 'ic_member:hyderabad', 'ic_member:pune'], set by you@example.com
      tenants/acme/roles/documind-evalgrc-sa@...: ['grc_member'], set by you@example.com
    """
    import os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    p = os.environ["PROJECT"]
    db = firestore.Client(project=p)
    cid = open(os.path.expanduser("~/lesson105_case.txt")).read().strip()
    c = db.collection("cases").document(cid).get().to_dict()
    print(f"  cases/{cid}")
    print(f"    {c['case_type']} {c['status']} in {c['queue']}, tenant {c['tenant']}, source {c['source']}, via {c['via']}")
    print(f"    summary {c['summary']!r}  expire_at {c.get('expire_at', 'gone')}  audit_pending {c['audit_pending']}"
          f"  token_sha256 {len(c['token_sha256'])} hex digits")
    evalacme = f"documind-evalacme-sa@{p}.iam.gserviceaccount.com"
    mine = (db.collection("cases").where("tenant", "==", "acme").where("requester", "==", evalacme)
            .order_by("created_at", direction=firestore.Query.DESCENDING).limit(10).stream())
    posh = next(s.to_dict() for s in mine if s.to_dict()["case_type"] == "posh")
    print(f"  the smoke's posh case: {posh['status']} in {posh['queue']}, unit {posh['unit']}, contacts {posh['chosen_contacts']},"
          f" summary {posh['summary']!r}, question_sha256 {posh['question_sha256']!r}")
    for who in (os.environ["ME"], f"documind-evalgrc-sa@{p}.iam.gserviceaccount.com"):
        r = db.collection("tenants").document("acme").collection("roles").document(who.lower()).get()
        print(f"  tenants/acme/roles/{who.split('@')[0]}@...: {r.to_dict()['roles']}, set by {r.to_dict()['set_by']}")

def step_02_the_audit_events(session):
    """Run Do it: the audit events at this checkpoint.

    Today's case and role events in the audit bucket, the newest six, then the latest case.open and role.grant in full.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (today's case and role events in the audit bucket).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 14 case and role events today; the last six:
        case.close-04b5496c-0c9a-4c8e-8eb8-8a93b0cb9d4d.json
        case.open-62b1d84e-eb7f-4f4d-815a-2cc512343c7a.json
        case.update-4251c1f7-5d9a-4f35-a81a-95bfa63619dd.json
        case.close-09c060c0-272f-4987-b4a7-cbfb9cae321c.json
        case.open-57204f61-542c-4dd8-83b7-279e956f644e.json
        case.close-08415b1b-e70e-463d-95d9-8c6746037e67.json
      case.open: actor {'tenant_id': 'acme', 'case_ref': 'case:721aa2320010d00117794591262ca9bb'}  target {'case_id': '721aa2320010d00117794591262ca9bb', 'case_type': 'sensitive'}  meta {'status': 'open', 'source': 'button', 'via': 'direct'}
      role.grant: actor {'tenant_id': 'acme', 'email': 'you@example.com'}  targe
    """
    import datetime, json, os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import storage
    p = os.environ["PROJECT"]
    bucket = storage.Client(project=p).bucket(f"{p}-audit")
    day = datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d")
    desk = sorted((b for b in bucket.list_blobs(prefix=f"{day}/acme/") if "/case." in b.name or "/role." in b.name),
                  key=lambda b: b.time_created)
    print(f"  {len(desk)} case and role events today; the last six:")
    for b in desk[-6:]:
        print("   ", b.name.split("/")[-1])
    for action in ("case.open", "role.grant"):
        e = json.loads(next(b for b in reversed(desk) if f"/{action}-" in b.name).download_as_text())
        print(f"  {action}: actor {e['actor']}  target {e['target']}  meta {e['meta']}")

def step_03_the_log_rows(session):
    """Run Do it: the log rows at this checkpoint.

    Every desk_gate row since step 3, from both services.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the desk_gate rows since step 3; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: documind-chat surface chat    tenant acme  user None  class sensitive  rules 2026-10-01.4
      documind-api  surface stream  tenant acme  user None  class sensitive  rules 2026-10-01.4
      documind-api  surface query   tenant acme  user None  class sensitive  rules 2026-10-01.4
      documind-chat surface chat    tenant acme  user None  class sensitive  rules 2026-10-01.4
      documind-chat surface chat    tenant acme  user None  class sensitive  rules 2026-10-01.4
      documind-api  surface stream  tenant acme  user None  class sensitive  rules 2026-10-01.4
    """
    import json, os, subprocess, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    f = f'resource.type="cloud_run_revision" AND jsonPayload.event="desk_gate" AND timestamp>="{os.environ["SINCE105"]}"'
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    for e in json.loads(out or "[]"):
        j = e["jsonPayload"]
        print(f"  {e['resource']['labels']['service_name']:13} surface {j['surface']:7} tenant {j['tenant']}  user {j['user']}"
              f"  class {j['class']}  rules {j['rules_version']}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_49', step_01_the_records),
        ('source_51', step_02_the_audit_events),
        ('source_53', step_03_the_log_rows),
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
