"""Lesson 12.3: What the kit does with a tuned candidate

Do it

Run order inside this file:
1. Do it (source window 9)

Prerequisites: setup_prepare.
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


def step_01_what_the_kit_does_with_a_tuned_candidate(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the kit's own functions; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: an answer gemini-3.6-flash cached, looked up for the tuned endpoint: alive True
    cost.py with RAG_MODEL_BASE=gemini-3.1-flash-lite  Rs 0.1764 an answer of 7,400 tokens in, 150 out
    cost.py with RAG_MODEL_BASE=gemini-3.6-flash       Rs 1.0391 an answer of 7,400 tokens in, 150 out
    Google, a tuned endpoint at 1.5 x its base          Rs 0.2646

    make usage's model column
    model                  answers    tok_in  tok_out       USD       INR  p95 ms  unans
    ------------------------------------------------------------------------------------
    gemini-3.6-flash             1      7400      210    0.0127      1.08    2100   0.00
    projects/NUMBER/loca         1      7400      150    0.0021      0.18    1000 
    """
    import ast, datetime as dt, os, sys
    sys.path[:0] = ["evals"]
    from usage_rows import group, show
    EP = "projects/NUMBER/locations/us/endpoints/ENDPOINT_ID"
    # 1. the answer cache's test, lifted out of semantic_cache.py (which builds a Firestore client when imported)
    tree = ast.parse(open("services/rag-api/semantic_cache.py", encoding="utf-8").read())
    ns = {"datetime": dt.datetime}
    exec(compile(ast.Module([n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_alive"], []), "semantic_cache.py", "exec"), ns)
    now = dt.datetime.now(dt.timezone.utc)
    entry = {"model": "gemini-3.6-flash", "fingerprint": "f1", "scope": "s1", "expire_at": now + dt.timedelta(hours=20)}
    print(f"an answer gemini-3.6-flash cached, looked up for the tuned endpoint: alive {ns['_alive'](entry, 'f1', 's1', now)}")
    # 2. one answer on the tuned endpoint, priced by cost.py (lifted: it imports BigQuery when loaded) and by Google
    tree = ast.parse(open("services/rag-api/cost.py", encoding="utf-8").read())
    cns = {"os": os, "USD_INR": 85.0}
    cns["FALLBACK"] = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")
    cns["_prices"] = lambda: cns["FALLBACK"]
    exec(compile(ast.Module([n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "price"], []), "cost.py", "exec"), cns)
    TIN, TOUT = 7400, 150
    for base in ("gemini-3.1-flash-lite", "gemini-3.6-flash"):
        os.environ["RAG_MODEL_BASE"] = base
        print(f"cost.py with RAG_MODEL_BASE={base:22} Rs {cns['price'](EP, TIN, TOUT)['inr']:.4f} an answer of {TIN:,} tokens in, {TOUT} out")
    usd_in, usd_out = cns["FALLBACK"]["gemini-3.1-flash-lite"]
    print(f"Google, a tuned endpoint at 1.5 x its base          Rs {1.5 * (TIN * usd_in + TOUT * usd_out) / 1e6 * 85:.4f}")
    # 3. what make usage prints for it
    rows = [{"model": "gemini-3.6-flash", "tokens_in": TIN, "tokens_out": 210, "cost_usd": 0.01268, "latency_ms": 2100},
            {"model": EP, "tokens_in": TIN, "tokens_out": TOUT, "cost_usd": 0.002075, "latency_ms": 1000}]
    show("make usage's model column", group(rows, ("model",)), ("model",))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_what_the_kit_does_with_a_tuned_candidate),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
