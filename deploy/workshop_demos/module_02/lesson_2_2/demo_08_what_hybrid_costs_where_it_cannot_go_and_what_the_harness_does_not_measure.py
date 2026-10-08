"""Lesson 2.2: What hybrid costs, where it cannot go, and what the harness does not measure

Two places, one at startup and one at runtime. A managed backend has no sparse leg to fuse and the Firestore rung's vector index takes one dense vector and nothing else, so check_retrieval_modes() refuses both pairs before the service serves; a tenant pinned to a managed store under hybrid mode is served from the deployment's backend with a retrieval_pin_ignored line instead. At runtime the chaos rung applies to hybrid as to dense: an unreachable index degrades to the Firestore rung, which is dense only, with a vector_search_fallback line and never a 500. The cell asks the validator the two questions offline.

Run order inside this file:
1. Where hybrid cannot go (source window 38)

Prerequisites: demo_07_the_knob_hybrid_on_a_candidate_that_takes_no_traffic_compared_then_removed.
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


def step_01_where_hybrid_cannot_go(session):
    """Run Where hybrid cannot go at this checkpoint.

    Two places, one at startup and one at runtime. A managed backend has no sparse leg to fuse and the Firestore rung's vector index takes one dense vector and nothing else, so check_retrieval_modes() refuses both pairs before the service serves; a tenant pinned to a managed store under hybrid mode is served from the deployment's backend with a retrieval_pin_ignored line instead. At runtime the chaos rung applies to hybrid as to dense: an unreachable index degrades to the Firestore rung, which is dense only, with a vector_search_fallback line and never a 500. The cell asks the validator the two questions offline.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: no call leaves the machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: vector     hybrid -> allowed
    firestore  hybrid -> refused: RETRIEVAL_MODE=hybrid needs RETRIEVAL_BACKEND=vector: the Firestore backend is dense-only. Set RETR...
    rag_engine hybrid -> refused: RETRIEVAL_MODE=hybrid needs RETRIEVAL_BACKEND=vector: rag_engine embeds and searches on its own ...
    firestore  dense  -> allowed
    """
    import os, sys
    sys.path[:0] = [".", "services/rag-api"]
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.environ["PROJECT"])
    for k in ("RETRIEVAL_MODE", "RETRIEVAL_BACKEND", "RETRIEVAL_CURRENT_ONLY", "TOP_K_RETRIEVE", "RERANK_TIMEOUT_S", "SEMANTIC_CACHE"):
        if os.environ.get(k) == "":
            del os.environ[k]                                  # an empty export from an earlier names box means the default
    from config import check_retrieval_modes
    for backend, mode in (("vector", "hybrid"), ("firestore", "hybrid"), ("rag_engine", "hybrid"), ("firestore", "dense")):
        try:
            check_retrieval_modes(backend, mode); print(f"{backend:10} {mode:6} -> allowed")
        except ValueError as e:
            print(f"{backend:10} {mode:6} -> refused: {str(e)[:96]}...")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_38', step_01_where_hybrid_cannot_go),
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
