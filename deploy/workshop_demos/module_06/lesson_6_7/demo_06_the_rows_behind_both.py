"""Lesson 6.7: The rows behind both

Do it

Run order inside this file:
1. Do it (source window 18)

Prerequisites: demo_05_another_person_finds_nothing.
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


# Original CLI workflow for step_01_the_rows_behind_both.
COMMANDS_01 = """~/graph-venv/bin/python - <<'PY'
import json, os, subprocess
from urllib.parse import unquote, urlparse
from google.cloud.sql.connector import Connector
gc = lambda *a: subprocess.run(["gcloud", *a, "--project", os.environ["PROJECT"]], capture_output=True, text=True, check=True).stdout.strip()
dsn = urlparse(gc("secrets", "versions", "access", "latest", "--secret", "documind-checkpoint-dsn"))   # the password stays in memory
instance = gc("sql", "instances", "describe", "documind-checkpoint", "--format", "value(connectionName)")
state = json.load(open(os.path.expanduser("~/lesson113.json")))
with Connector() as connector:
    db = connector.connect(instance, "pg8000", user=dsn.username, password=unquote(dsn.password), db=dsn.path.lstrip("/"))
    cur = db.cursor()
    def q(sql, *args):
        cur.execute(sql, args)                  # a tuple, empty or not: pg8000 takes len() of it, and None has none
        return cur.fetchall()
    for brain in ("langchain", "adk"):
        session = f"{state['session']}-{brain}"
        ts = [t for (t,) in q("SELECT checkpoint->>'ts' FROM checkpoints WHERE thread_id LIKE %s ORDER BY checkpoint_id", "%:" + session)]
        before = sum(t[:19] < state["redeployed_at"] for t in ts)
        print(f"  {session}: " + (f"{len(ts)} checkpoints, {before} before the redeploy and {len(ts) - before} after" if ts
                                  else "no rows - the ADK brain keeps none"))
    for person in (os.environ["ME"], "documind-ui-sa@"):
        rows = q("SELECT thread_id, count(*) FROM checkpoints WHERE thread_id LIKE %s GROUP BY thread_id ORDER BY max(checkpoint->>'ts') DESC",
                 f"%:{person}%")
        print(f"  threads of {person.split('@')[0]}: {len(rows)}" + (f"; the latest is session {rows[0][0].split(':', 2)[2]}, {rows[0][1]} checkpoints" if rows else ""))
    db.close()
PY

"""

def step_01_the_rows_behind_both(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the rows behind steps 4 and 5).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lesson113-4242-langchain: 6 checkpoints, 3 before the redeploy and 3 after
      lesson113-4242-adk: no rows - the ADK brain keeps none
      threads of you: 1; the latest is session 3f9c2a1d0b7e, 3 checkpoints
      threads of documind-ui-sa: 2; the latest is session lesson113-4242-langchain, 6 checkpoints
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_the_rows_behind_both),
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
