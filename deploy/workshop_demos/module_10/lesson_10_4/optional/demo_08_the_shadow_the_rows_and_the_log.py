"""Lesson 10.4: The shadow, the rows and the log

Optional, only with the door on: the desk rows that came through the Google Chat door, then the bridge's claims in its own Firestore database; reads only.

Run order inside this file:
1. Optional: the Google Chat door's rows (source window 73)

Prerequisites: demo_08_the_shadow_the_rows_and_the_log.
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


def step_01_optional_the_google_chat_door_s_rows(session):
    """Run Optional: the Google Chat door's rows at this checkpoint.

    This needs the door on your lane, step 3's optional part: without it there is no documind-gchat database to read. Two direct reads of what step 4's conversation left, if you had it. The desk rows with via "gchat" are the Desk's own rows for the turns the bridge asked for. The handbook turn names you and the delegate; the disclosure's names nobody, as on the Desk page. The bridge's claims are in its own Firestore database, documind-gchat, never the default one where the rosters and roles live. A claim stops a message that Chat delivers twice, or that Pub/Sub pushes twice, from being answered twice. Its id is a hash of the message's name, it holds no text and no email, and it expires 24 hours after it was made. A TTL policy then deletes it; how soon after is not confirmed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, only with the Google Chat door on (the desk rows that came through the Google Chat door since step 3, then the bridge's claims; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: desk rows through the Google Chat door: 2
        via gchat  delegate gchat  user employee@example.com  route handbook  case_type None  outcome answer
        via gchat  delegate None  user None  route case  case_type sensitive  outcome case
      claims in documind-gchat's gchat_events: 1
        d4f2fa564e03b68e...  fields ['attempts', 'created_at', 'expire_at', 'kind', 'leased_at', 'state']
          kind message  state answered  attempts 1  an email in it: False  expire_at - created_at: 1 day, 0:00:00
    """
    import json, os, subprocess, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND '
         f'jsonPayload.event="desk" AND jsonPayload.via="gchat" AND timestamp>="{os.environ["SINCE106"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    rows = [e["jsonPayload"] for e in json.loads(out or "[]")]
    print(f"  desk rows through the Google Chat door: {len(rows)}")
    for j in rows:
        print(f"    via {j['via']}  delegate {j['delegate']}  user {j['user']}  route {j['route']}  case_type {j['case_type']}"
              f"  outcome {j['outcome']}")
    db = firestore.Client(project=os.environ["PROJECT"], database="documind-gchat")
    claims = list(db.collection("gchat_events").stream())
    print(f"  claims in documind-gchat's gchat_events: {len(claims)}")
    for s in claims:
        d = s.to_dict()
        print(f"    {s.id[:16]}...  fields {sorted(d)}")
        print(f"      kind {d['kind']}  state {d['state']}  attempts {d['attempts']}  an email in it: {any('@' in str(v) for v in d.values())}"
              f"  expire_at - created_at: {d['expire_at'] - d['created_at']}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_73', step_01_optional_the_google_chat_door_s_rows),
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
