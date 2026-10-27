"""Lesson 4.3: The candidate gate: a revision with no traffic, judged before any user meets it

Do it: the candidate This is the workflow's check, by hand: /version on the live URL and on the tag URL, both with a token minted for the live one. Do it: the gate on the candidate Now read the report as a release decision: how many thresholds were judged, what the outsider got, and each required row. The candidate has done its job. Removing its tag ends its URL. Deleting .candidate-revision means a stray make promote stops with an error instead of moving traffic to it; lesson 4.4 explains why both are needed.

Run order inside this file:
1. Do it: the candidate (source window 18)
2. Do it: does the candidate answer as the same build? (source window 20)
3. Do it: the gate on the candidate (source window 22)
4. Do it: the gate on the candidate (source window 24)
5. Do it: remove the candidate (source window 26)

Prerequisites: demo_03_ci_the_offline_gate_on_every_push_and_the_job_every_release_needs_first.
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


# Original CLI workflow for step_01_the_candidate.
COMMANDS_01 = """make candidate PROJECT="$PROJECT"          # no override: the Makefile's settings, the image unchanged
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"

"""

def step_01_the_candidate(session):
    """Run Do it: the candidate at this checkpoint.

    Do it: the candidate

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a new revision with no traffic; nothing moves for users).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\
      --update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flash|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=off|RETRIEVAL_CURRENT_ONLY=off|RETRIEVAL_GRAPH=off|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
    ...
    >> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
    >> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic docu
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_does_the_candidate_answer_as_the_same_buil.
COMMANDS_02 = """for u in "$API" "$CAND"; do echo "$u/version"
  curl -s "$u/version" -H "Authorization: Bearer $(tok "$API")" \\
    | python -c 'import json, sys; v = json.load(sys.stdin); print("  git_sha", v["git_sha"], "| generator", v["generator_model"], "| prompt", v["prompt"])'
done

"""

def step_02_does_the_candidate_answer_as_the_same_buil(session):
    """Run Do it: does the candidate answer as the same build? at this checkpoint.

    This is the workflow's check, by hand: /version on the live URL and on the tag URL, both with a token minted for the live one.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (two GETs: the live revision and the candidate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: https://documind-api-NUMBER.asia-south1.run.app/version
      git_sha COMMIT | generator gemini-3.6-flash | prompt documind-rag@v3
    https://candidate---documind-api-NUMBER.asia-south1.run.app/version
      git_sha COMMIT | generator gemini-3.6-flash | prompt documind-rag@v3
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_the_gate_on_the_candidate(session):
    """Run Do it: the gate on the candidate at this checkpoint.

    Do it: the gate on the candidate

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every row as the member, every isolation row as the outsider: about ten minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/candidate_gate.txt]
    """
    import os
    from workshop_helpers.gates import live_gate
    live_gate(session, report="evals/reports/cand43.json", api=os.environ["CAND"])

def step_04_the_gate_on_the_candidate(session):
    """Run Do it: the gate on the candidate at this checkpoint.

    Now read the report as a release decision: how many thresholds were judged, what the outsider got, and each required row.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the report; changes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: https://candidate---documind-api-NUMBER.asia-south1.run.app
      thresholds judged: 9 of 9; failed: none
      the outsider: isolation_403_rate 100%; let in on: no row
      required rows: 15 of 15 passed
        iso-01  isolation  zeta    pass
        iso-02  isolation  globex  pass
        iso-03  isolation  globex  pass
        iso-04  isolation  zeta    pass
        iso-05  isolation  zeta    pass
        iso-06  isolation  globex  pass
        iso-07  isolation  globex  pass
        iso-08  isolation  zeta    pass
        iso-09  isolation  zeta    pass
        iso-10  isolation  globex  pass
        mm-01   lookup     acme    pass
        mm-02   lookup     acme    pass
        mm-03   lookup     acme    pass
        mm-04   isolation  zeta    pass
  
    """
    import json, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    r = json.load(open("evals/reports/cand43.json", encoding="utf-8"))
    required = json.load(open("evals/required.json", encoding="utf-8"))["ids"]
    rec = {x["id"]: x for x in r["records"]}
    print(r["api_url"])
    print(f"  thresholds judged: {len(r['judged'])} of {len(r['thresholds'])}; failed: {', '.join(r['failed']) or 'none'}")
    print(f"  the outsider: isolation_403_rate {r['scores']['isolation_403_rate']:.0%}; let in on: {', '.join(x.split(':')[0] for x in r['isolation']) or 'no row'}")
    print(f"  required rows: {sum(bool(rec.get(i, {}).get('pass')) for i in required)} of {len(required)} passed")
    for i in required:
        x = rec.get(i)
        verdict = "not asked" if x is None else "pass" if x["pass"] else "FAIL: " + (x["why"] or x["outcome"])
        print(f"    {i:7} {x['shape'] if x else '':10} {x['tenant'] if x else '':7} {verdict}")
    code = 2 if r["leaks"] else 1 if (r["failed"] or r["stale"] or r["required_failed"]) else 0
    print(f"  leaks {len(r['leaks'])}, stale {len(r['stale'])}: the gate's exit was {code}")

# Original CLI workflow for step_05_remove_the_candidate.
COMMANDS_05 = """gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag (lesson 4.4)
curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"

"""

def step_05_remove_the_candidate(session):
    """Run Do it: remove the candidate at this checkpoint.

    The candidate has done its job. Removing its tag ends its URL. Deleting .candidate-revision means a stray make promote stops with an error instead of moving traffic to it; lesson 4.4 explains why both are needed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the candidate's tag and its recorded name removed; the live revision is untouched).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    the candidate URL now: HTTP 404
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_the_candidate),
        ('source_20', step_02_does_the_candidate_answer_as_the_same_buil),
        ('source_22', step_03_the_gate_on_the_candidate),
        ('source_24', step_04_the_gate_on_the_candidate),
        ('source_26', step_05_remove_the_candidate),
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
