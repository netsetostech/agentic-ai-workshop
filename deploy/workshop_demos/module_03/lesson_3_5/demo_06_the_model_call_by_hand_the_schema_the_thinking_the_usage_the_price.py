"""Lesson 3.5: The model call by hand: the schema, the thinking, the usage, the price

Do it: the same call, from the shell

Run order inside this file:
1. Do it: the same call, from the shell (source window 26)

Prerequisites: demo_05_three_refusals_the_model_s_twice_the_api_s_once_and_how_their_envelopes_differ.
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


def step_01_the_same_call_from_the_shell(session):
    """Run Do it: the same call, from the shell at this checkpoint.

    Do it: the same call, from the shell

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; one model call at the generator's rate, a few paise).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: finish: STOP | the draft: {"answer": "A confirmed employee in grade E3 ... [1]", "citations": [{"source": 1, "quote": "..."}], "confidence": "high", "answerable": true} ...
    resolved: [('acme:hr_policy_2026#NP-03', 1, 0.0)] | answerable True | confidence high
    usage: prompt 4xx | candidates 1xx | thoughts xxx | cached 0
    priced as the API would: $0.00xxxx = Rs 0.xxxx at 85.0
    """
    import os, sys, ast, json
    sys.path[:0] = [".", "services/rag-api"]
    from google import genai
    from google.genai import types
    from shared.documind_schemas import ModelDraft, resolve
    from shared import documind_corpus as dc
    from context_budget import pack_chunks, estimate_tokens
    K = {n.targets[0].id: ast.literal_eval(n.value) for n in ast.parse(open("services/rag-api/generator.py", encoding="utf-8").read()).body
         if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id == "SYSTEM"}
    client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")          # _client: a model NAME is served on the global endpoint
    MODEL = os.environ.get("GENERATOR_MODEL", "gemini-3.6-flash")
    handbook = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://uploads/acme/hr_policy_2026.md",
                                  "text": open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()}, "acme")
    context, packed, dropped = pack_chunks([next(c for c in handbook if c["locator"] == L) for L in ("NP-03", "PB-02")], 7832, estimate_tokens)
    Q = "What is the notice period for a confirmed E3?"
    prompt = f"{K['SYSTEM']}\n\nContext:\n{context}\n\nQuestion: {Q}"                                # generate(): no dated rule, no packed chunk carries a date
    r = client.models.generate_content(model=MODEL, contents=[prompt], config=types.GenerateContentConfig(
        response_mime_type="application/json", response_schema=ModelDraft, max_output_tokens=2048,
        thinking_config=types.ThinkingConfig(thinking_level="LOW")))                                 # _call(), without a tenant cache
    draft = r.parsed if isinstance(r.parsed, ModelDraft) else ModelDraft.model_validate(json.loads(r.text))
    print("finish:", r.candidates[0].finish_reason.name, "| the draft:", json.dumps(draft.model_dump(), ensure_ascii=False)[:200], "...")
    ans = resolve(draft, packed)
    print("resolved:", [(c.chunk_id, c.page, c.score) for c in ans.citations], "| answerable", ans.answerable, "| confidence", ans.confidence)
    u = r.usage_metadata
    thoughts = getattr(u, "thoughts_token_count", None) or 0
    print("usage: prompt", u.prompt_token_count, "| candidates", u.candidates_token_count, "| thoughts", thoughts, "| cached", getattr(u, "cached_content_token_count", None) or 0)
    try:
        from cost import price                                                                        # the API's own arithmetic
        p = price(MODEL, u.prompt_token_count or 0, (u.candidates_token_count or 0) + thoughts, 0)
        print(f"priced as the API would: ${p['usd']} = Rs {p['inr']} at {p['usd_inr_rate']}")
    except ImportError as e:
        print("cost.price() needs google-cloud-bigquery in the venv:", e)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_26', step_01_the_same_call_from_the_shell),
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
