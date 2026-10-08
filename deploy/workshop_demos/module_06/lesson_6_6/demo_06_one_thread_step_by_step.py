"""Lesson 6.6: One thread, step by step

Do it

Run order inside this file:
1. Do it (source window 18)

Prerequisites: demo_05_the_tables_and_one_row_per_thread.
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


# Original CLI workflow for step_01_one_thread_step_by_step.
COMMANDS_01 = """~/graph-venv/bin/python - <<'PY'
import os, subprocess
from urllib.parse import unquote, urlparse
from google.cloud.sql.connector import Connector
gc = lambda *a: subprocess.run(["gcloud", *a, "--project", os.environ["PROJECT"]], capture_output=True, text=True, check=True).stdout.strip()
dsn = urlparse(gc("secrets", "versions", "access", "latest", "--secret", "documind-checkpoint-dsn"))   # the password stays in memory
instance = gc("sql", "instances", "describe", "documind-checkpoint", "--format", "value(connectionName)")
with Connector() as connector:
    db = connector.connect(instance, "pg8000", user=dsn.username, password=unquote(dsn.password), db=dsn.path.lstrip("/"))
    cur = db.cursor()
    def q(sql, *args):
        cur.execute(sql, args)                  # a tuple, empty or not: pg8000 takes len() of it, and None has none
        return cur.fetchall()
    (thread,) = q("SELECT thread_id FROM checkpoints GROUP BY thread_id ORDER BY max(checkpoint->>'ts') DESC LIMIT 1")[0]
    size = dict(q("SELECT version, length(blob) FROM checkpoint_blobs WHERE thread_id = %s AND channel = 'messages'", thread))
    print(f"the latest thread, session {thread.split(':', 2)[2]}: its checkpoints in order")
    seen = []
    for step, source, version in q("SELECT (metadata->>'step')::int, metadata->>'source', checkpoint->'channel_versions'->>'messages' "
                                   "FROM checkpoints WHERE thread_id = %s ORDER BY checkpoint_id", thread):
        new = version is not None and version not in seen
        seen += [version] if new else []
        print(f"  step {step:>2}  {source:5}  " + (f"messages, version {len(seen)}: {size[version]:>6,} bytes" if new else "messages unchanged"))
    print(f"every version kept: {sum(size.values()):,} bytes; the latest alone: {size[max(size)]:,} bytes")
    db.close()
PY

"""

def step_01_one_thread_step_by_step(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the latest thread, step by step).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the latest thread, session lesson111-4242-b: its checkpoints in order
      step -1  input  messages unchanged
      step  0  loop   messages, version 1:    175 bytes
      step  1  loop   messages, version 2:    412 bytes
      step  2  input  messages unchanged
      step  3  loop   messages, version 3:    586 bytes
      step  4  loop   messages, version 4:    866 bytes
      step  5  loop   messages, version 5:  2,325 bytes
      step  6  loop   messages, version 6:  2,562 bytes
    every version kept: 6,926 bytes; the latest alone: 2,562 bytes
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_one_thread_step_by_step),
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
