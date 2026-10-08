"""Lesson 2.3: make usage: where the time went, p95 per stage, and the view behind it

Do it: the selftest, then the lane's last day, then its rows into the reader

Run order inside this file:
1. Do it: the selftest, then the lane's last day, then its rows into the reader (source window 27)
2. Do it: the selftest, then the lane's last day, then its rows into the reader (source window 30)

Prerequisites: demo_05_the_fallback_the_pool_by_retrieval_score_flagged_on_the_row_forced_on_a_candidat.
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


# Original CLI workflow for step_01_the_selftest_then_the_lane_s_last_day_then.
COMMANDS_01 = """python evals/usage_rows.py --selftest
make usage PROJECT=$PROJECT HOURS=24

"""

def step_01_the_selftest_then_the_lane_s_last_day_then(session):
    """Run Do it: the selftest, then the lane's last day, then its rows into the reader at this checkpoint.

    Do it: the selftest, then the lane's last day, then its rows into the reader

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: the selftest touches nothing, and reading the log is free).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: selftest: by tenant
    tenant                 answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ------------------------------------------------------------------------------------
    zeta                         1      1500      120    0.0332      2.82    5200   0.00
    acme                         2      3800      450    0.0091      0.77    1400   0.50

    selftest: where the time went (p95 per stage, by tenant)
    tenant                 answers  p95 ms  retrieve  rerank  generate   pool
    -------------------------------------------------------------------------
    zeta                         1    5200       200     120      4800   20.0
    acme                         2    1400       220     130    
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_selftest_then_the_lane_s_last_day_then.
COMMANDS_02 = """gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND (jsonPayload.event="query" OR jsonPayload.event="stream")' \\
  --project "$PROJECT" --freshness 24h --limit 40 --format=json \\
  | python -c "import sys, json; [print(json.dumps(e['jsonPayload'])) for e in json.load(sys.stdin) if 'jsonPayload' in e]" > /tmp/rows53.jsonl
python -c "import json; rows = [json.loads(l) for l in open('/tmp/rows53.jsonl')]; print(len(rows), 'rows;', sum(int(r.get('rerank_fallback') or 0) for r in rows), 'with rerank_fallback 1;', sum(1 for r in rows if not r.get('pool')), 'with an empty pool')"
head -c 700 /tmp/rows53.jsonl

"""

def step_02_the_selftest_then_the_lane_s_last_day_then(session):
    """Run Do it: the selftest, then the lane's last day, then its rows into the reader at this checkpoint.

    Do it: the selftest, then the lane's last day, then its rows into the reader

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (the rows themselves, one JSON line each, for the reader in step 1).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: NN rows; 1 with rerank_fallback 1; 0 with an empty pool
    {"event": "query", "tenant": "acme", "user": "documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", "tokens_in": xxxx.0, "tokens_out": xxx.0, "cached_tokens": 0.0, "cost_usd": 0.00xxxx, "latency_ms": 2xxx.0, "answerable": true, "retrieve_ms": 6xx.0, "rerank_ms": 3xx.0, "generate_ms": 1xxx.0, "pool": 20.0, "rerank_fallback": 0.0, ...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_27', step_01_the_selftest_then_the_lane_s_last_day_then),
        ('source_30', step_02_the_selftest_then_the_lane_s_last_day_then),
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
