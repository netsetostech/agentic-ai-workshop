"""Lesson 2.3: What the funnel costs, its knobs, and the packed set the citations come from

The cell runs the kit's packer with the API's own budget over three lists: your ranked pool at top_k 5 and 20, and twenty full pages of the CGST Act's mirror, cut by the kit's own chunker from the file in evals/corpus. Then a golden question whose pool is Act pages goes to the API at top_k 20, and the log says what the packer dropped.

Run order inside this file:
1. Do it: the API's packer offline, then a pool of Act pages on the lane (source window 43)
2. Do it: the API's packer offline, then a pool of Act pages on the lane (source window 45)

Prerequisites: demo_07_found_by_stamped_on_every_chunk_counted_on_the_answer_absent_from_the_citation.
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


def step_01_the_api_s_packer_offline_then_a_pool_of_ac(session):
    """Run Do it: the API's packer offline, then a pool of Act pages on the lane at this checkpoint.

    The cell runs the kit's packer with the API's own budget over three lists: your ranked pool at top_k 5 and 20, and twenty full pages of the CGST Act's mirror, cut by the kit's own chunker from the file in evals/corpus. Then a golden question whose pool is Act pages goes to the API at top_k 20, and the log says what the packer dropped.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: pure Python over the saved pool and a file in the kit).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the budget: 7,832 tokens for the chunks, 168 for the fixed prompt, 2,048 reserved for the answer
    your ranked pool, top_k 5    packed  5, dropped  0, context   7xx tokens
    your ranked pool, top_k 20   packed 20, dropped  0, context  2xxx tokens
    twenty full CGST Act pages   packed 15, dropped  5, context  7633 tokens
    the first header the model reads: [Source 1] hr_policy_2026.md
    """
    import ast, sys, json
    sys.path[:0] = [".", "services/rag-api"]
    from context_budget import pack_chunks, estimate_tokens, TokenBudget, source_header     # pure Python: no cloud calls
    from shared import documind_corpus as dc
    d = json.load(open("/tmp/pool53.json"))
    tree = ast.parse(open("services/rag-api/generator.py", encoding="utf-8").read())
    consts = {n.targets[0].id: ast.literal_eval(n.value) for n in tree.body
              if isinstance(n, ast.Assign) and isinstance(n.targets[0], ast.Name) and n.targets[0].id in ("SYSTEM", "DATED_RULE")}
    fixed = f"{consts['SYSTEM']}{consts['DATED_RULE']}\n\nContext:\n\n\nQuestion: {d['question']}"     # generator._budget(), line for line
    budget = TokenBudget.fit(8000, fixed, estimate_tokens, answer=2048)
    print(f"the budget: {budget.chunks} tokens for the chunks, {budget.system} for the fixed prompt, {budget.answer} reserved for the answer")
    ranked = [dict(d["pool"][i], source_uri="gs://uploads/acme/" + d["pool"][i]["source"], rerank_score=s) for i, s in d["ranked"]]   # the ranker's order, step 4
    act = open("evals/corpus/acme/cgst_act_2017.md", encoding="utf-8").read()
    pages = dc.chunk_document({"slug": "cgst_act_2017", "doc_type": "policy", "source_uri": "gs://uploads/acme/cgst_act_2017.md", "text": act}, "acme")
    full = sorted(pages, key=lambda c: -len(c["text"]))[:20]                       # twenty full pages, the kit's mirror cut by the kit's chunker
    for name, chunks in (("your ranked pool, top_k 5", ranked[:5]), ("your ranked pool, top_k 20", ranked[:20]), ("twenty full CGST Act pages", full)):
        context, packed, dropped = pack_chunks(chunks, budget.chunks, estimate_tokens)
        print(f"{name:28} packed {len(packed):2}, dropped {len(dropped):2}, context {estimate_tokens(context):5} tokens")
    print("the first header the model reads:", source_header(1, ranked[0]))

# Original CLI workflow for step_02_the_api_s_packer_offline_then_a_pool_of_ac.
COMMANDS_02 = """curl -s -X POST "$API/v1/query" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query":"What is the maximum rate of central tax the CGST Act allows?","tenant_id":"acme","stream":false,"top_k":20}' \\
  | python -c "import sys, json; j = json.load(sys.stdin); s = j['stages']; print('pool', s['pool'], '| citations', len(j['citations']), '| generate_ms', s['generate_ms'], '| tokens_in', j['tokens_in'], '| sources', sorted({c['source_uri'].split('/')[-1][:20] for c in j['citations']}))"
gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="context_budget_drop"' \\
  --project "$PROJECT" --freshness 1h --limit 3 --format='value(timestamp,jsonPayload.packed,jsonPayload.dropped)'

"""

def step_02_the_api_s_packer_offline_then_a_pool_of_ac(session):
    """Run Do it: the API's packer offline, then a pool of Act pages on the lane at this checkpoint.

    The cell runs the kit's packer with the API's own budget over three lists: your ranked pool at top_k 5 and 20, and twenty full pages of the CGST Act's mirror, cut by the kit's own chunker from the file in evals/corpus. Then a golden question whose pool is Act pages goes to the API at top_k 20, and the log says what the packer dropped.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (one question with twenty Act pages offered to the model, a couple of rupees; one log read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: pool 20 | citations 2 | generate_ms 3xxx | tokens_in 8xxx | sources ['cgst_act_2017.pdf']
    2026-09-2xT1x:xx:xx.xxxxxxZ	1x	x
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_43', step_01_the_api_s_packer_offline_then_a_pool_of_ac),
        ('source_45', step_02_the_api_s_packer_offline_then_a_pool_of_ac),
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
