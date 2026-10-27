"""Lesson 6.9: On your lane today: every turn sends more

Do it

Run order inside this file:
1. Do it (source window 6)

Prerequisites: setup_prepare.
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


def step_01_on_your_lane_today_every_turn_sends_more(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the six chat rows step 3's turns wrote, from Cloud Logging).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/ui_turns.txt]
    """
    import json, os, subprocess, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" '
         f'AND jsonPayload.event="chat" AND jsonPayload.user="{os.environ["ME"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--freshness", "2h",
                          "--limit", "40", "--format", "json"], capture_output=True, text=True, check=True).stdout
    rows = [e["jsonPayload"] for e in reversed(json.loads(out or "[]"))]           # oldest first
    session = rows[-1]["session_id"] if rows else ""
    turns = [r for r in rows if r["session_id"] == session]
    open(os.path.expanduser("~/lesson69-session.txt"), "w").write(session)          # for step 7
    print(f"session {session}: {len(turns)} turns, brain {', '.join(sorted({r['brain'] for r in turns}))}")
    print("  turn  model calls  tokens_in  cached  tokens_out  chat Rs  search Rs")
    for n, r in enumerate(turns, 1):
        print(f"  {n:>4}  {r['model_calls']:>11}  {r['tokens_in']:>9,}  {r['cached_tokens']:>6,}  {r['tokens_out']:>10,}"
              f"  {r['cost_usd'] * 85:>7.2f}  {r['rag_cost_usd'] * 85:>9.2f}")
    if len(turns) > 1:
        print(f"turn {len(turns)} sent {turns[-1]['tokens_in'] / turns[0]['tokens_in']:.1f} times turn 1's input tokens")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_6', step_01_on_your_lane_today_every_turn_sends_more),
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
