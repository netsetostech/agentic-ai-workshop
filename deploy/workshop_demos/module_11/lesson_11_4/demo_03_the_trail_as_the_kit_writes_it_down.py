"""Lesson 11.4: The trail, as the kit writes it down

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


def step_01_the_trail_as_the_kit_writes_it_down(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the trail as the kit writes it down; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the envelope on every answer, beyond the contract (schemas.py, RAGResponse):
      model, backend, cost_usd, tokens_in, tokens_out, cached_tokens, latency_ms, stages, cache_hit
    stages, as query() fills them (main.py):
      generate_ms, graph_chunks, managed_chunks, policy_fallback, pool, rerank_fallback, rerank_ms, retrieval_backend, retrieve_ms, vector_chunks
    found_by, the rung that put a chunk in the pool (retriever.py):
      firestore, graph, rag_engine, vector, vertex_search
    GET /version, what is serving (main.py):
      model_backend, generator_model, prompt, retrieval_mode, retrieval_backend, retrieval_graph, graph_backend, embedding, retrieval_current_only, semantic_cache, git_sha
    the events a degr
    """
    import ast, re
    root = "services/rag-api/"
    main, ret = (open(root + f, encoding="utf-8").read() for f in ("main.py", "retriever.py"))
    tree = ast.parse(open(root + "schemas.py", encoding="utf-8").read())
    env = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == "RAGResponse")
    print("the envelope on every answer, beyond the contract (schemas.py, RAGResponse):")
    print("  " + ", ".join(n.target.id for n in env.body if isinstance(n, ast.AnnAssign)))
    q = main[main.index("def query("):main.index("def _record(")]
    keys = set(re.findall(r'stages\["(\w+)"\]', q)) | {n + "_ms" for n in re.findall(r'stage\(stages, "(\w+)"\)', q)}
    print("stages, as query() fills them (main.py):")
    print("  " + ", ".join(sorted(keys)))
    print("found_by, the rung that put a chunk in the pool (retriever.py):")
    print("  " + ", ".join(sorted(set(re.findall(r'found_by"\]? ?[:=] ?"(\w+)"', ret)))))
    v = main[main.index("def version():"):main.index('@app.get("/v1/sources")')]
    print("GET /version, what is serving (main.py):")
    print("  " + ", ".join(re.findall(r'"(\w+)":', v)))
    print("the events a degraded answer leaves in documind-api's log:")
    for f in ("main.py", "retriever.py", "generator.py", "cache_manager.py"):
        for i, line in enumerate(open(root + f, encoding="utf-8"), 1):
            for ev in re.findall(r'"event": "(\w+(?:fallback|stale|ignored|exhausted|truncated))"', line):
                print(f"  {ev:24} {f}:{i}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_trail_as_the_kit_writes_it_down),
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
