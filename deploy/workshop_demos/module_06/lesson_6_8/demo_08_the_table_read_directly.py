"""Lesson 6.8: The table, read directly

Do it

Run order inside this file:
1. Do it (source window 43)

Prerequisites: demo_07_your_thread_replayed_and_forked_on_your_machine.
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


# Original CLI workflow for step_01_the_table_read_directly.
COMMANDS_01 = """~/graph-venv/bin/python - <<'PY'
import json, os, subprocess, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from urllib.parse import unquote, urlparse
from google.cloud.sql.connector import Connector
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
def gc(*args):
    \"\"\"One gcloud read in your project, as text.\"\"\"
    return subprocess.run(["gcloud", *args, "--project", os.environ["PROJECT"]], capture_output=True, text=True, check=True).stdout.strip()
def said(m):
    \"\"\"One message in a few words: the tools it asks for, the citations it returned, or its first words.\"\"\"
    calls = [c["name"] for c in getattr(m, "tool_calls", None) or []]
    text = m.content if isinstance(m.content, str) else " ".join(b.get("text", "") for b in m.content if isinstance(b, dict))
    if calls:
        return "asks " + ", ".join(calls)
    if m.type == "tool" and text.startswith("{"):
        return f"{len(json.loads(text).get('citations', []))} citations"
    return " ".join(text.split())[:64]
dsn = urlparse(gc("secrets", "versions", "access", "latest", "--secret", "documind-checkpoint-dsn"))   # the password stays in memory
instance = gc("sql", "instances", "describe", "documind-checkpoint", "--format", "value(connectionName)")
export = json.load(open(os.path.expanduser("~/lesson68.json"), encoding="utf-8"))   # step 6's file
thread = export["thread_id"]
serde = JsonPlusSerializer(allowed_msgpack_modules=None)            # strict, as thread_read.py builds it
with Connector() as connector:
    db = connector.connect(instance, "pg8000", user=dsn.username, password=unquote(dsn.password), db=dsn.path.lstrip("/"))
    db.autocommit = True
    cur = db.cursor()
    cur.execute("SET default_transaction_read_only = on", ())       # as make thread does: nothing below can write
    def q(sql, *args):
        \"\"\"One read on the read-only session; pg8000 takes a tuple of arguments, empty or not.\"\"\"
        cur.execute(sql, args)
        return cur.fetchall()
    (n,) = q("SELECT count(*) FROM checkpoints WHERE thread_id = %s AND checkpoint_ns = ''", thread)[0]
    print(f"session {export['session']}: {n} checkpoints on the lane; step 6's export holds {len(export['checkpoints'])}")
    (version,) = q("SELECT checkpoint->'channel_versions'->>'messages' FROM checkpoints WHERE thread_id = %s "
                   "AND checkpoint_ns = '' ORDER BY checkpoint_id DESC LIMIT 1", thread)[0]
    typ, blob = q("SELECT type, blob FROM checkpoint_blobs WHERE thread_id = %s AND checkpoint_ns = '' "
                  "AND channel = 'messages' AND version = %s", thread, version)[0]
    messages = serde.loads_typed((typ, bytes(blob)))
    print(f"the newest checkpoint names messages version {int(version.split('.')[0])}: a {typ} blob of {len(blob):,} bytes, decoded:")
    for m in messages:
        print(f"   {type(m).__name__:12} {said(m)}")
    db.close()
PY

"""

def step_01_the_table_read_directly(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (your thread's rows, read directly; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/table_read.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_43', step_01_the_table_read_directly),
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
