"""Lesson 12.2: The endpoint, and where it answers

The first cell polls the job once a minute until it ends. The poll only reads, so it costs nothing, and after a disconnect it is safe to run again: it takes the job from step 5's log. When the job succeeds, tune.py prints: The cell keeps the endpoint in ~/poll172.log and in ENDPOINT. The cell keeps the endpoint in ~/poll172.log and in ENDPOINT. The second cell asks the endpoint one question the way the generator would. It sends SYSTEM, one source under its header and the question, with generator._call's settings: ModelDraft's schema, 2,048 tokens and thinking at LOW. The chunk is not one the rows were written from, and the question is not a golden one. The cell asks in three places: us-central1, the job's region; global, where the served model answers; and the location the generator would use, from the path.

Run order inside this file:
1. Definition (source window 19)
2. Definition (source window 21)

Prerequisites: demo_05_the_job_submitted.
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
COMMANDS_01 = """JOB="${JOB:-$(grep -o 'projects/[^ ]*/tuningJobs/[0-9]*' ~/tune172.log | head -1)}"     # after a reconnect: the job, from step 5's log
python evals/tune.py --project "$PROJECT" --poll "$JOB" | tee ~/poll172.log   # a line a minute until the job ends; safe to re-run
export ENDPOINT="$(grep -o 'projects/[^ ]*/endpoints/[0-9]*' ~/poll172.log | head -1)"; echo "ENDPOINT=$ENDPOINT"

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    The first cell polls the job once a minute until it ends. The poll only reads, so it costs nothing, and after a disconnect it is safe to run again: it takes the job from step 5's log. When the job succeeds, tune.py prints: The cell keeps the endpoint in ~/poll172.log and in ENDPOINT.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (waits for the job, a line a minute).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 09:53:00 JobState.JOB_STATE_PENDING
      09:54:00 JobState.JOB_STATE_PENDING
      09:55:00 JobState.JOB_STATE_RUNNING
      ...      (a line a minute while the job runs: 33 more here)
      10:29:00 JobState.JOB_STATE_RUNNING
      JOB_STATE_SUCCEEDED
      tuned model : projects/NUMBER/locations/us/models/6156234374247085944@1
      endpoint    : projects/NUMBER/locations/us/endpoints/9136961803583303949

      serve it as a candidate revision, no traffic, and judge it:
        make candidate PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=projects/NUMBER/locations/us/endpoints/9136961803583303949 RAG_MODEL_BASE=gemini-3.1-flash-lite
        make eval-live PROJECT=documind-ai-YOUR-ID API=<the candidate url>
        make judge PROJECT=d
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_definition(session):
    """Run Definition at this checkpoint.

    The cell keeps the endpoint in ~/poll172.log and in ENDPOINT. The second cell asks the endpoint one question the way the generator would. It sends SYSTEM, one source under its header and the question, with generator._call's settings: ModelDraft's schema, 2,048 tokens and thinking at LOW. The chunk is not one the rows were written from, and the question is not a golden one. The cell asks in three places: us-central1, the job's region; global, where the served model answers; and the location the generator would use, from the path.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one answer from the endpoint, and two calls that are not found).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the endpoint's path says us; the generator would call it at us
      us-central1  404 NOT_FOUND
      global       404 NOT_FOUND
      us           answered: 429 tokens in, 97 out; a ModelDraft, answerable True, 1 citation(s), 0 [N] marks in the answer
      the answer: No. A loss of wages from withholding an increment for a good and sufficient cause is not deemed a deduction from wages, where the employer's provisions meet the requirements the appropriate Government notifies.
      the price: Rs 0.0322 as Google bills a tuned Gemini 3 endpoint (1.5 x flash-lite); cost.py would log Rs 0.0215
    """
    import ast, os, re, sys, types as pytypes
    sys.path[:0] = [".", "evals", "services/rag-api"]
    from google import genai
    from google.genai import errors, types
    import make_trainset as mt
    from context_budget import source_header
    from shared.documind_schemas import ModelDraft
    P, EP = os.environ["PROJECT"], os.environ["ENDPOINT"]
    fn = next(n for n in ast.parse(open("services/rag-api/generator.py", encoding="utf-8").read()).body
              if isinstance(n, ast.FunctionDef) and n.name == "_endpoint_location")
    ns = {"re": re, "settings": pytypes.SimpleNamespace(generator_location=os.environ.get("GENERATOR_LOCATION", ""), region=os.environ["REGION"])}
    exec(compile(ast.Module([fn], []), "generator.py", "exec"), ns)       # lifted: generator.py builds its clients when imported
    where = ns["_endpoint_location"](EP)
    print(f"the endpoint's path says {EP.split('/locations/', 1)[1].split('/', 1)[0]}; the generator would call it at {where}")
    c = next(c for c in mt.load_chunks("acme") if c["chunk_id"] == "acme:code_on_wages_2019#p9-1")       # not a training row's chunk
    q = "Is withholding an employee's increment a deduction from wages under the Code on Wages?"         # not a golden question
    prompt = f"{mt.SYSTEM}\n\nContext:\n{source_header(1, c)}\n{c['text']}\n\nQuestion: {q}"      # the generator's shape, one source
    cfg = types.GenerateContentConfig(response_mime_type="application/json", response_schema=ModelDraft, max_output_tokens=2048,
                                      thinking_config=types.ThinkingConfig(thinking_level="LOW"))      # generator._call's settings
    tree = ast.parse(open("services/rag-api/cost.py", encoding="utf-8").read())
    usd_in, usd_out = next(ast.literal_eval(n.value) for n in tree.body
                           if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")["gemini-3.1-flash-lite"]
    for loc in dict.fromkeys(("us-central1", "global", where)):
        try:
            r = genai.Client(enterprise=True, project=P, location=loc).models.generate_content(model=EP, contents=prompt, config=cfg)
        except errors.APIError as e:
            print(f"  {loc:12} {e.code} {e.status}")
            continue
        d, u = ModelDraft.model_validate_json(r.text), r.usage_metadata
        out = (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)
        marks = re.findall(r"\[(\d+(?:\s*,\s*\d+)*)\]", d.answer)
        rs = (u.prompt_token_count * usd_in + out * usd_out) / 1e6 * 85
        print(f"  {loc:12} answered: {u.prompt_token_count:,} tokens in, {out:,} out; a ModelDraft, answerable {d.answerable}, "
              f"{len(d.citations)} citation(s), {len(marks)} [N] marks in the answer")
        print(f"  the answer: {d.answer}")
        print(f"  the price: Rs {1.5 * rs:.4f} as Google bills a tuned Gemini 3 endpoint (1.5 x flash-lite); cost.py would log Rs {rs:.4f}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_definition),
        ('source_21', step_02_definition),
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
