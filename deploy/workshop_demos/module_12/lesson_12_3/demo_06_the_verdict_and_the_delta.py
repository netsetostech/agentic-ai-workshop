"""Lesson 12.3: The verdict and the delta

Do it: the verdict The gates and the judge asked both revisions the same questions, so their usage rows are like for like. The cell prints make usage's model table, groups the rows by model, and prices the endpoint's rows at 1.5 times what they log. The gate and the judge set the tuned flash-lite against the live flash, so every difference mixes two changes: a smaller model, and the tuning on top of it. A third revision pulls them apart: gemini-3.1-flash-lite as Google serves it, the base v2 was tuned from (TUNE_BASE, lesson 12.2), with every other setting the candidate's. Live against untuned is then the smaller model, and untuned against tuned is the tuning. The cell makes it with gcloud, not make candidate. That target would move the candidate tag to the new revision and record it in .candidate-revision: the tuned candidate would lose its address, and make promote would move traffic to the untuned model. A service update starts from the service's latest settings, which have been the candidate's since step 4, so with --update-env-vars the model is the one setting that changes. A model name is served on the global endpoint, as the live model is; only an endpoint path is served from its own location. The cell makes it with gcloud, not make candidate. That target would move the candidate tag to the new revision and record it in .candidate-revision: the tuned candidate would lose its address, and make promote would move traffic to the untuned model. A service update starts from the service's latest settings, which have been the candidate's since step 4, so with --update-env-vars the model is the one setting that changes. A model name is served on the global endpoint, as the live model is; only an endpoint path is served from its own location. Then the gate on it, and the three reports side by side: each judged rate, the rows passed, the generation time at p50 and p95 as the gate measures it, the model that answered each, and the rows each change moved.

Run order inside this file:
1. Do it: the verdict (source window 21)
2. Do it: the delta (source window 23)
3. Compare the models: the untuned base (source window 25)
4. Compare the models: the untuned base (source window 27)
5. Compare the models: the untuned base (source window 29)

Prerequisites: demo_05_the_gate_on_both_revisions.
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


# Original CLI workflow for step_01_the_verdict.
COMMANDS_01 = """make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" API_B="$CAND"

"""

def step_01_the_verdict(session):
    """Run Do it: the verdict at this checkpoint.

    Do it: the verdict

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the judge's venv from lesson 4.2: 65 answers from each revision, then Vertex AI Evaluation).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://documind-api-NUMBER.asia-south1.run.app
      65/65 answers collected from https://documind-api-NUMBER.asia-south1.run.app in ...s (model gemini-3.6-flash)
      65/65 candidate answers from https://candidate---documind-api-NUMBER.asia-south1.run.app
      context: 46/46 cited chunks read in full from the store
      trajectories: off (no --chat-url)
      pointwise: GROUNDEDNESS + INSTRUCTION_FOLLOWING  (templates cd7070; run api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070)
      judge: the service default (pass --judge-model to pin one)

      Experiments run documind-eval/api-GITSHA-YYYYMMDD-HHMM-vs-candidate-tcd7070:
        groundedness/mean                                1.000
        groundedness/mean[isolation
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_delta.
COMMANDS_02 = """make usage PROJECT="$PROJECT" HOURS=2 | sed -n '/^by model and backend/,/^$/p'
python - <<'PY'
import os, sys
sys.path.insert(0, "evals")
from usage_rows import group, read_rows
EP, TUNED = os.environ["ENDPOINT"], 1.5      # Google's pricing page: a tuned Gemini 3 endpoint answers at 1.5 x its base
per = {g["model"]: g for g in group(read_rows(os.environ["PROJECT"], 2), ("model",))}
live, cand = per["gemini-3.6-flash"], per[EP]
a, logged = live["inr"] / live["answers"], cand["inr"] / cand["answers"]
print(f"  live       {live['answers']:4} answers  Rs {a:.4f} an answer")
print(f"  candidate  {cand['answers']:4} answers  Rs {logged:.4f} an answer as logged, Rs {logged * TUNED:.4f} as Google bills it")
d = a - logged * TUNED
print(f"the rupee delta: the tuned endpoint costs Rs {d:.4f} less an answer, Rs {d * 1000:,.0f} per 1,000 answers")
print(f"  (the usage rows alone say Rs {a - logged:.4f}: they log the endpoint at its base's rate)")
PY

"""

def step_02_the_delta(session):
    """Run Do it: the delta at this checkpoint.

    The gates and the judge asked both revisions the same questions, so their usage rows are like for like. The cell prints make usage's model table, groups the rows by model, and prices the endpoint's rows at 1.5 times what they log.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the last two hours of usage rows).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: by model and backend (what answered, through which door)
    model                 model_backend          answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ----------------------------------------------------------------------------------------------------------
    gemini-3.6-flash      vertex                     130    952849    28030    1.6395    139.36    2100   0.00
    projects/NUMBER/loca  vertex                     130    970907    17751    0.2694     22.89    1000   0.00

      live        130 answers  Rs 1.0720 an answer
      candidate   130 answers  Rs 0.1761 an answer as logged, Rs 0.2641 as Google bills it
    the rupee delta: the tuned endpoint costs Rs 0.8079 less an answer, Rs 808 per 1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_compare_the_models_the_untuned_base.
COMMANDS_03 = """gcloud run services update documind-api --region "$REGION" --project "$PROJECT" --no-traffic --tag untuned \\
  --update-env-vars GENERATOR_MODEL=gemini-3.1-flash-lite     # the candidate's settings, the untuned model in the endpoint's place
export UNTUNED="https://untuned---documind-api-$NUMBER.$REGION.run.app"; echo "UNTUNED=$UNTUNED"

"""

def step_03_compare_the_models_the_untuned_base(session):
    """Run Compare the models: the untuned base at this checkpoint.

    The gate and the judge set the tuned flash-lite against the live flash, so every difference mixes two changes: a smaller model, and the tuning on top of it. A third revision pulls them apart: gemini-3.1-flash-lite as Google serves it, the base v2 was tuned from (TUNE_BASE, lesson 12.2), with every other setting the candidate's. Live against untuned is then the smaller model, and untuned against tuned is the tuning. The cell makes it with gcloud, not make candidate. That target would move the candidate tag to the new revision and record it in .candidate-revision: the tuned candidate would lose its address, and make promote would move traffic to the untuned model. A service update starts from the service's latest settings, which have been the candidate's since step 4, so with --update-env-vars the model is the one setting that changes. A model name is served on the global endpoint, as the live model is; only an endpoint path is served from its own location.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one more revision with no traffic, at a tag of its own).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    UNTUNED=https://untuned---documind-api-NUMBER.asia-south1.run.app
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def step_04_compare_the_models_the_untuned_base(session):
    """Run Compare the models: the untuned base at this checkpoint.

    The cell makes it with gcloud, not make candidate. That target would move the candidate tag to the new revision and record it in .candidate-revision: the tuned candidate would lose its address, and make promote would move traffic to the untuned model. A service update starts from the service's latest settings, which have been the candidate's since step 4, so with --update-env-vars the model is the one setting that changes. A model name is served on the global endpoint, as the live model is; only an endpoint path is served from its own location. Then the gate on it, and the three reports side by side: each judged rate, the rows passed, the generation time at p50 and p95 as the gate measures it, the model that answered each, and the rows each change moved.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every golden row on the untuned base: about ten minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://untuned---documind-api-NUMBER.asia-south1.run.app
      65 rows (47 answerable, 18 not) against https://untuned---documind-api-NUMBER.asia-south1.run.app

      [PASS] request_success_rate  100.0%  (threshold 100%; 65 rows)
      [PASS] answerable_rate        97.9%  (threshold 80%; 47 rows)
      [PASS] citation_rate         100.0%  (threshold 95%; 46 rows)
      [PASS] citation_valid_rate   100.0%  (threshold 100%; 46 rows)
      [PASS] must_contain_rate      97.8%  (threshold 85%; 46 rows)
      [PASS] correct_rate           95.7%  (threshold 68%; 47 rows)
      [PASS] refusal_rate          100.0%  (threshold 90%; 18 rows)
      [PASS] media_kind_rate       100.0%  (threshold 80%; 3 rows)
      [PASS] isolation_403_ra
    """
    import os
    from pathlib import Path
    from workshop_helpers.gates import live_gate
    live_gate(session, report=Path.home() / "untuned173.json", api=os.environ["UNTUNED"])

def step_05_compare_the_models_the_untuned_base(session):
    """Run Compare the models: the untuned base at this checkpoint.

    The cell makes it with gcloud, not make candidate. That target would move the candidate tag to the new revision and record it in .candidate-revision: the tuned candidate would lose its address, and make promote would move traffic to the untuned model. A service update starts from the service's latest settings, which have been the candidate's since step 4, so with --update-env-vars the model is the one setting that changes. A model name is served on the global endpoint, as the live model is; only an endpoint path is served from its own location. Then the gate on it, and the three reports side by side: each judged rate, the rows passed, the generation time at p50 and p95 as the gate measures it, the model that answered each, and the rows each change moved.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the three reports).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: live  untuned    tuned  needs
      request_success_rate    100.0%   100.0%   100.0%   100%
      answerable_rate          97.9%    97.9%    97.9%    80%
      citation_rate           100.0%   100.0%   100.0%    95%
      citation_valid_rate     100.0%   100.0%   100.0%   100%
      must_contain_rate        97.8%    97.8%    95.7%    85%
      correct_rate             95.7%    95.7%    93.6%    68%
      refusal_rate            100.0%   100.0%   100.0%    90%
      media_kind_rate         100.0%   100.0%   100.0%    80%
      isolation_403_rate      100.0%   100.0%   100.0%   100%
      rows passed              63/65    63/65    62/65
      generate_ms p50            ...      ...      ...
      generate_ms p95            ...      ...     
    """
    import json, os, sys
    sys.path[:0] = ["evals"]
    from run_eval import pct                          # the gate's own percentile, as its generate_ms line uses it
    rep = {k: json.load(open(os.path.expanduser(f"~/{f}173.json"), encoding="utf-8"))
           for k, f in (("live", "base"), ("untuned", "untuned"), ("tuned", "cand"))}
    print(f"  {'':21} " + " ".join(f"{k:>8}" for k in rep) + f"  {'needs':>5}")
    for s in rep["live"]["scores"]:
        if any(s in r["judged"] for r in rep.values()):
            print(f"  {s:21} " + " ".join(f"{r['scores'][s]:8.1%}" for r in rep.values()) + f"  {rep['live']['thresholds'][s]:5.0%}")
    print(f"  {'rows passed':21} " + " ".join(f"{sum(x['pass'] for x in r['records']):5}/{len(r['records'])}" for r in rep.values()))
    for q in (0.5, 0.95):                             # over the answered rows, as the gate prints it
        ms = [[int(x["stages"].get("generate_ms", 0)) for x in r["records"] if x["outcome"] == "ok" and x.get("stages")] for r in rep.values()]
        print(f"  {'generate_ms p' + format(q * 100, '.0f'):21} " + " ".join(f"{pct(m, q):8}" for m in ms))
    for k, r in rep.items():
        names = sorted({x["model"] for x in r["records"] if x.get("model")})
        print(f"  {k:8} answered by " + ", ".join("endpoint " + m.rsplit("/", 1)[1] if m.startswith("projects/") else m for m in names))
    for a, b, what in (("live", "untuned", "the smaller model"), ("untuned", "tuned", "the tuning")):
        was = {x["id"]: x["pass"] for x in rep[a]["records"]}
        moved = [x for x in rep[b]["records"] if was.get(x["id"]) != x["pass"]]
        print(f"  {a} to {b}, what {what} moved: {len(moved)} row(s)")
        for x in moved:
            print(f"    {x['id']}: {'pass' if was.get(x['id']) else 'fail'} to {'pass' if x['pass'] else 'fail'} ({x['why'] or x['outcome']})")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_the_verdict),
        ('source_23', step_02_the_delta),
        ('source_25', step_03_compare_the_models_the_untuned_base),
        ('source_27', step_04_compare_the_models_the_untuned_base),
        ('source_29', step_05_compare_the_models_the_untuned_base),
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
