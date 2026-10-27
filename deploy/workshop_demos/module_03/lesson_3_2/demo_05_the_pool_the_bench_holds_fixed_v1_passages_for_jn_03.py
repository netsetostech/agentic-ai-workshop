"""Lesson 3.2: The pool the bench holds fixed: /v1/passages for jn-03

The curl saves the route's reply. The Python cell lists the passages and checks them with run_eval's own rules: which passage holds each figure the gate wants (contains()), and whether each anchor the row names is in the pool (anchors_found(), the rule DOCUMIND_EVAL_PASSAGES=1 uses).

Run order inside this file:
1. Do it: jn-03's pool, and where its two facts sit (source window 22)

Prerequisites: demo_04_chain_of_thought_in_the_kit_the_level_the_schema_the_zero_shot_prompt_and_the_be.
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


# Original CLI workflow for step_01_jn_03_s_pool_and_where_its_two_facts_sit.
COMMANDS_01 = """curl -s -X POST "$API/v1/passages" -H "Authorization: Bearer $(tok "$API")" -H "Content-Type: application/json" \\
  -d '{"query": "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?", "tenant_id": "acme", "top_k": 6}' -o /tmp/jn03_pool.json
python - <<'PY'
import json, sys, warnings
warnings.filterwarnings("ignore", category=UserWarning)
sys.path.insert(0, "evals")
from run_eval import anchors_found, contains, load_golden
row = next(r for r in load_golden() if r["id"] == "jn-03")
body = json.load(open("/tmp/jn03_pool.json", encoding="utf-8"))
pool, usage = body["passages"], body["usage"]
print(f"{len(pool)} passages from {usage['stages'].get('retrieval_backend')}; the route's own bill: {usage['tokens_in']} tokens in, "
      f"{usage['tokens_out']} out")
for p in pool:
    text = " ".join(p["text"].split())
    found = [f for f in row["must_contain"] if contains(text, f)]
    name = p["source_uri"].rsplit("/", 1)[-1]
    print(f"  [{p['n']}] {name} {p.get('section') or 'p.' + str(p.get('page'))} | figures: {', '.join(found) or '-'} | {text[:60]}")
print("anchors in the pool:", anchors_found(row, pool))
PY

"""

def step_01_jn_03_s_pool_and_where_its_two_facts_sit(session):
    """Run Do it: jn-03's pool, and where its two facts sit at this checkpoint.

    The curl saves the route's reply. The Python cell lists the passages and checks them with run_eval's own rules: which passage holds each figure the gate wants (contains()), and whether each anchor the row names is in the pool (anchors_found(), the rule DOCUMIND_EVAL_PASSAGES=1 uses).

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (one /v1/passages call, then a Python cell; no model call).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/passages_jn03.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_jn_03_s_pool_and_where_its_two_facts_sit),
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
