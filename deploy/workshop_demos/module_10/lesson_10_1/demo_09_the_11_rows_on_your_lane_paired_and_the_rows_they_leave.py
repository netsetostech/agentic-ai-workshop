"""Lesson 10.1: The 11 rows on your lane, paired, and the rows they leave

The same command as step 7 without OFFLINE=1: every calculator row through every pattern once, at the Desk agent's own thinking level, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes; the report comes when all 33 have run. The same cell as step 7, on your lane's saved runs. Do it: rag-api's rows for those searches

Run order inside this file:
1. Definition (source window 47)
2. Do it: the paired difference and each pattern's calls, at Rs 0 (source window 49)
3. Do it: rag-api's rows for those searches (source window 51)

Prerequisites: demo_08_your_lane_four_thinking_levels_react_a_plan_and_what_a_search_returns.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """make agent-eval PROJECT="$PROJECT" REGION="$REGION" PATTERNS=loop,react_text,plan_first SLICE=calc SAVE="$HOME/bench-101-lane.jsonl"

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    The same command as step 7 without OFFLINE=1: every calculator row through every pattern once, at the Desk agent's own thinking level, each run saved as one JSON line. A run is a full turn, so a progress line on stderr shows each run's calls and rupees as it finishes; the report comes when all 33 have run.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (33 live turns, about Rs 37.79 before thinking).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_patterns.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_paired_difference_and_each_pattern_s_c.
COMMANDS_02 = """export SAVED="$HOME/bench-101-lane.jsonl"
python - <<'PY'
import json, os, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path[:0] = [".", "commands"]
import agent_patterns as ap      # the standard library and shared/ only, at import: read_step() is the bench's own parser

saved, home = os.environ["SAVED"], os.path.expanduser("~")
runs = [json.loads(line) for line in open(saved, encoding="utf-8") if line.strip()]
print(f"{len(runs)} runs in {saved.replace(home, '~')}")
for pattern in [p for p in ap.PATTERNS if any(r["arm"]["pattern"] == p for r in runs)]:
    mine = [r for r in runs if r["arm"]["pattern"] == pattern]
    calls = [c for r in mine for c in r["calls"] if not c.get("error")]
    out = saved[:-len(".jsonl")] + f"-{pattern}.jsonl"
    with open(out, "w", encoding="utf-8", newline="\\n") as f:
        f.writelines(json.dumps(r, ensure_ascii=False) + "\\n" for r in mine)
    n = max(len(calls), 1)
    line = (f"{pattern:<10} {len(mine)} runs, {len(calls)} calls; a call reads {sum(c['tokens_in'] for c in calls) / n:,.0f}, "
            f"thinks {sum(c['thinking_tokens'] for c in calls) / n:,.0f}, writes {sum(c['visible_tokens'] for c in calls) / n:,.0f}; "
            f"Rs {sum(r['inr'] for r in mine):.2f} in all")
    if ap.PATTERNS[pattern].text:
        past = sum(ap.STOP in (c.get("text") or "") for c in calls)
        unread = sum("error" in ap.read_step(c.get("text") or "") for c in calls)
        line += f"; {past} replies ran past the stop, {unread} format errors"
    print(line)
PY
make agent-eval COMPARE="${SAVED%.jsonl}-loop.jsonl ${SAVED%.jsonl}-react_text.jsonl"
make agent-eval COMPARE="${SAVED%.jsonl}-loop.jsonl ${SAVED%.jsonl}-plan_first.jsonl"

"""

def step_02_the_paired_difference_and_each_pattern_s_c(session):
    """Run Do it: the paired difference and each pattern's calls, at Rs 0 at this checkpoint.

    The same cell as step 7, on your lane's saved runs.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Rs 0: your lane's saved runs split by pattern, then paired).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/eval_paired.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_rag_api_s_rows_for_those_searches(session):
    """Run Do it: rag-api's rows for those searches at this checkpoint.

    Do it: rag-api's rows for those searches

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a Python cell; Rs 0: one Cloud Logging read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/passages_rows.txt]
    """
    import json, os, subprocess, warnings
    from collections import Counter
    warnings.filterwarnings("ignore", category=UserWarning)
    flt = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
           'AND jsonPayload.event="passages" AND jsonPayload.brain="desk"')
    out = subprocess.run(["gcloud", "logging", "read", flt, "--project", os.environ["PROJECT"], "--freshness", "1d",
                          "--limit", "500", "--format", "json"], capture_output=True, text=True, check=True).stdout
    rows = [e["jsonPayload"] for e in json.loads(out or "[]")]
    print(f"{len(rows)} passages rows labelled brain desk in the last day; by tenant {dict(Counter(r['tenant'] for r in rows))}")
    print(f"  model {sorted({r['model'] for r in rows})} | tokens {sum(r['tokens_in'] + r['tokens_out'] for r in rows)} | "
          f"cost_usd {sum(r['cost_usd'] for r in rows)} | answerable {sum(bool(r['answerable']) for r in rows)} of {len(rows)}")
    print(f"  asked as {sorted({r['user'].split('@')[0] for r in rows})}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_47', step_01_definition),
        ('source_49', step_02_the_paired_difference_and_each_pattern_s_c),
        ('source_51', step_03_rag_api_s_rows_for_those_searches),
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
