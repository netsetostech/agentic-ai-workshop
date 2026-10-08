"""Lesson 6.4: Avoided calls in rupees, and the latency of a hit

Do it: the candidate's rows Do it: the kit's table

Run order inside this file:
1. Do it: the candidate's rows (source window 18)
2. Do it: the kit's table (source window 20)

Prerequisites: demo_04_the_replay_the_same_pairs_asked_live_at_0_95.
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


def step_01_the_candidate_s_rows(session):
    """Run Do it: the candidate's rows at this checkpoint.

    Do it: the candidate's rows

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the candidate's rows since the start: hits, p95, rupees; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 65 answers on the candidate: 10 from the answer cache, 55 from the model
      p95 latency: 236 ms for a hit, 3187 ms for a model answer
      a model answer cost Rs 0.4673 on average: the hits avoided 10 calls, about Rs 4.67
      of those hits, 2 served a wrong answer: pp-25, pp-31
    """
    import json, os, subprocess
    rev = open(".candidate-revision").read().strip()
    f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" '
         f'AND resource.labels.revision_name="{rev}" AND timestamp>="{os.environ["SINCE93"]}"')
    rows = [e["jsonPayload"] for e in json.loads(subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"],
            "--limit", "500", "--format", "json"], capture_output=True, text=True, check=True).stdout or "[]")]
    hits, miss = [r for r in rows if r["model_backend"] == "cache"], [r for r in rows if r["model_backend"] != "cache"]
    p95 = lambda v: sorted(v)[max(0, int(round(0.95 * len(v))) - 1)] if v else 0
    rs = sum(r["cost_usd"] for r in miss) / len(miss) * 85 if miss else 0.0
    wrong = [o["id"] for o in json.load(open(os.path.expanduser("~/cache93_replay.json"), encoding="utf-8")) if o["verdict"] == "FALSE HIT"]
    print(f"  {len(rows)} answers on the candidate: {len(hits)} from the answer cache, {len(miss)} from the model")
    print(f"  p95 latency: {p95([r['latency_ms'] for r in hits])} ms for a hit, {p95([r['latency_ms'] for r in miss])} ms for a model answer")
    print(f"  a model answer cost Rs {rs:.4f} on average: the hits avoided {len(hits)} calls, about Rs {len(hits) * rs:.2f}")
    print(f"  of those hits, {len(wrong)} served a wrong answer: {', '.join(wrong) or 'none'}")

# Original CLI workflow for step_02_the_kit_s_table.
COMMANDS_02 = """make usage PROJECT="$PROJECT" HOURS=1 | sed -n '/by model and backend/,/^$/p'

"""

def step_02_the_kit_s_table(session):
    """Run Do it: the kit's table at this checkpoint.

    Do it: the kit's table

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's own table of the last hour, by model and backend).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: by model and backend (what answered, through which door)
    model                 model_backend          answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ----------------------------------------------------------------------------------------------------------
    gemini-3.6-flash      vertex                      55     97661    20783    0.3024     25.70    3187   0.00
    gemini-3.6-flash      cache                       10         0        0    0.0000      0.00     236   0.00
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_the_candidate_s_rows),
        ('source_20', step_02_the_kit_s_table),
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
