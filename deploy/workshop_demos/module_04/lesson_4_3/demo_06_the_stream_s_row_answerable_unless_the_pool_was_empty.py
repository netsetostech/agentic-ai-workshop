"""Lesson 4.3: The stream's row: answerable, unless the pool was empty

The cell streams rf-01's question for acme as the eval identity, prints what the stream said, then waits for the row in Cloud Logging and prints its verdict. If you asked the same question in the UI in step 5, it prints your row too, without your email.

Run order inside this file:
1. Do it: one refusal through the stream, and its row (source window 37)

Prerequisites: demo_05_live_traffic_the_usage_rows_and_the_gate_s_rows_among_them.
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


# Original CLI workflow for step_01_one_refusal_through_the_stream_and_its_row.
COMMANDS_01 = """TOKEN="$(tok "$API")" python - <<'PY'
import datetime as dt, json, os, subprocess, time, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
P, API, ME = os.environ["PROJECT"], os.environ["API"], os.environ.get("ME", "").lower()
EVAL = f"documind-ui-sa@{P}.iam.gserviceaccount.com"
QUESTION = "What is ACME's sabbatical policy?"            # golden row rf-01: no acme document answers it
since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(seconds=10)).strftime("%Y-%m-%dT%H:%M:%SZ")
req = urllib.request.Request(f"{API}/v1/stream", method="POST",
                             data=json.dumps({"query": QUESTION, "tenant_id": "acme", "top_k": 5}).encode(),
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
event, text, done = "", [], {}
with urllib.request.urlopen(req, timeout=120) as resp:
    for raw in resp:
        line = raw.decode("utf-8").rstrip("\\r\\n")
        if line.startswith("event: "):
            event = line[7:]
        elif line.startswith("data: ") and event == "token":
            text.append(json.loads(line[6:])["t"])
        elif line.startswith("data: ") and event == "done":
            done = json.loads(line[6:])
print("the stream:", " ".join("".join(text).split())[:240])
print(f"  pool {done['stages']['pool']}, backend {done['backend']}, model {done['model']}, tokens out {done.get('tokens_out')}")


def stream_rows(start):
    \"\"\"The stream usage rows documind-api logged since this time, newest first, from Cloud Logging.\"\"\"
    flt = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
           f'AND jsonPayload.event="stream" AND timestamp>="{start}"')
    out = subprocess.run(["gcloud", "logging", "read", flt, "--project", P, "--limit", "20", "--format=json"],
                         capture_output=True, text=True, check=True).stdout
    return [e["jsonPayload"] for e in json.loads(out or "[]")]


mine = []
for _ in range(18):                        # a row reaches Cloud Logging a few seconds after the stream ends
    mine = [r for r in stream_rows(since) if r.get("user") == EVAL]
    if mine:
        break
    time.sleep(5)
if not mine:
    raise SystemExit("no stream row from the eval identity after 90 s: run the cell again")
row = mine[0]
print(f"its usage row: answerable {row['answerable']}, unanswerable_flag {row['unanswerable_flag']}, "
      f"confidence {row['confidence']}, pool {row['pool']}")
print(f"  {len(row)} fields; holding the question or the answer: {[k for k in row if k in ('query', 'question', 'answer', 'text')] or 'none'}")
recent = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(minutes=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
for r in stream_rows(recent):
    if ME and r.get("user") == ME:
        print(f"your stream in the UI ({r['tenant']}): answerable {r['answerable']}, unanswerable_flag {r['unanswerable_flag']}, pool {r['pool']}")
PY

"""

def step_01_one_refusal_through_the_stream_and_its_row(session):
    """Run Do it: one refusal through the stream, and its row at this checkpoint.

    The cell streams rf-01's question for acme as the eval identity, prints what the stream said, then waits for the row in Cloud Logging and prints its verdict. If you asked the same question in the UI in step 5, it prints your row too, without your email.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one streamed answer, then its row from Cloud Logging).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/stream_refusal.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_37', step_01_one_refusal_through_the_stream_and_its_row),
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
