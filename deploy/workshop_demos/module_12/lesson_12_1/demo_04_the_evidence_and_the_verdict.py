"""Lesson 12.1: The evidence, and the verdict

Do it

Run order inside this file:
1. Do it (source window 12)
2. Do it (source window 14)

Prerequisites: demo_03_the_kit_s_rules_and_the_file_it_ships_audited.
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


# Original CLI workflow for step_01_the_evidence_and_the_verdict.
COMMANDS_01 = """make eval-live PROJECT="$PROJECT" REPORT="$HOME/gate171.json"

"""

def step_01_the_evidence_and_the_verdict(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every golden row, as in 7.2: about ten minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://documind-api-NUMBER.asia-south1.run.app
    == eval gate: LIVE ==
      65 rows (47 answerable, 18 not) against https://documind-api-NUMBER.asia-south1.run.app

      [PASS] request_success_rate  100.0%  (threshold 100%; 65 rows)
      [PASS] answerable_rate        97.9%  (threshold 80%; 47 rows)
      [PASS] citation_rate         100.0%  (threshold 95%; 46 rows)
      [PASS] citation_valid_rate   100.0%  (threshold 100%; 46 rows)
      [PASS] must_contain_rate      97.8%  (threshold 85%; 46 rows)
      [PASS] correct_rate           95.7%  (threshold 68%; 47 rows)
      [PASS] refusal_rate          100.0%  (threshold 90%; 18 rows)
      [PASS] media_kind_rate       100.0%  (threshold 80%; 3 rows)
      [PASS] isolation_403_
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_the_evidence_and_the_verdict(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only: the report, a week of logs, the price table).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1. the gate: 65 rows, 2 missed
       jn-06  join     answered without ['EMEA', '11.4']            -> knowledge (retrieval, the corpus, or the row)
       lk-27  lookup   refused                                      -> knowledge (retrieval, the corpus, or the row)
    2. the grammar, last 7 days: 1 repaired, 0 invalid, 0 unparsed, in 360 answers (0.3%)
    3. the price at this lane's tokens (7,389 in and 211 out an answer, 1,543 answers a month):
       gemini-3.6-flash         Rs 1.08 an answer, Rs 1,662 a month
       tuned flash-lite, 1.5 x  Rs 0.28 an answer, Rs 426 a month
    4. the data: 1,542 chunks of 400 characters or more in acme's corpus mirrors
    verdict: not for quality - the misses are knowledge, and the g
    """
    import ast, datetime as dt, json, os, subprocess, sys
    sys.path[:0] = [".", "evals"]
    P = os.environ["PROJECT"]
    rep = json.load(open(os.path.expanduser("~/gate171.json"), encoding="utf-8"))
    HABIT = ("answered without a citation", "answered, should refuse")     # the citation and the refusal: what the rows teach
    failed = [r for r in rep["records"] if not r["pass"]]
    habit = [r for r in failed if r["why"].startswith(HABIT) or r["outcome"] == "malformed"]
    print(f"1. the gate: {rep['rows']} rows, {len(failed)} missed")
    for r in failed:
        kind = "habit" if r in habit else "knowledge (retrieval, the corpus, or the row)"
        print(f"   {r['id']:6} {r['shape']:8} {r['why'][:44]:44} -> {kind}")
    since = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=7)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    
    def logged(event, limit=5000):                                # the API's own lines, from Cloud Logging
        """Read the specified training/evaluation log event so the dataset verdict uses recorded evidence.
        
        Example: logged('query')
        """
        flt = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" '
               f'AND jsonPayload.event="{event}" AND timestamp>="{since}"')
        return json.loads(subprocess.run(["gcloud", "logging", "read", flt, f"--project={P}", "--format=json", f"--limit={limit}"],
                                         capture_output=True, text=True, check=True).stdout)
    
    
    answers = logged("query") + logged("stream")
    broke = {e: len(logged(e, 500)) for e in ("generation_repaired", "generation_invalid", "generation_unparsed")}
    rate = sum(broke.values()) / max(len(answers), 1)
    print(f"2. the grammar, last 7 days: {broke['generation_repaired']} repaired, {broke['generation_invalid']} invalid, "
          f"{broke['generation_unparsed']} unparsed, in {len(answers)} answers ({100 * rate:.1f}%)")
    tree = ast.parse(open("services/rag-api/cost.py", encoding="utf-8").read())
    PRICE = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")
    tin = sum(int(e["jsonPayload"].get("tokens_in") or 0) for e in answers) / max(len(answers), 1)
    tout = sum(int(e["jsonPayload"].get("tokens_out") or 0) for e in answers) / max(len(answers), 1)
    month = len(answers) * 30 / 7
    print(f"3. the price at this lane's tokens ({tin:,.0f} in and {tout:,.0f} out an answer, {month:,.0f} answers a month):")
    TUNED = 1.5                  # Google's pricing page: a tuned Gemini 3 endpoint predicts at 1.5 times its base (cost.py says 1)
    cost = {}
    for model, name, factor in (("gemini-3.6-flash", "gemini-3.6-flash", 1.0), ("gemini-3.1-flash-lite", "tuned flash-lite, 1.5 x", TUNED)):
        usd_in, usd_out = PRICE[model]                            # cost.py's table: USD a million tokens
        each = (tin * usd_in + tout * usd_out) * factor / 1e6 * 85
        cost[model] = each * month
        print(f"   {name:24} Rs {each:.2f} an answer, Rs {cost[model]:,.0f} a month")
    import make_trainset as mt
    print(f"4. the data: {len(mt.load_chunks('acme')):,} chunks of {mt.MIN_CHUNK_CHARS} characters or more in acme's corpus mirrors")
    saving = cost["gemini-3.6-flash"] - cost["gemini-3.1-flash-lite"]
    if habit or rate >= 0.01:
        print("verdict: tune for quality - the misses are the habit the training rows teach")
    elif saving > 0:
        print(f"verdict: not for quality - the misses are knowledge, and the grammar holds.\n"
              f"         for price, only as an experiment: gemini-3.6-flash cannot be tuned; a tuned gemini-3.1-flash-lite would save\n"
              f"         Rs {saving:,.0f} a month at this traffic, if it passes the same gate (lesson 12.3)")
    else:
        print("verdict: do not tune")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_the_evidence_and_the_verdict),
        ('source_14', step_02_the_evidence_and_the_verdict),
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
