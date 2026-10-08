"""Lesson 2.3: found_by: stamped on every chunk, counted on the answer, absent from the citation

Do it: the join, then the kit's own retrieval in your process, then the smoke

Run order inside this file:
1. Do it: the join, then the kit's own retrieval in your process, then the smoke (source window 35)
2. Do it: the join, then the kit's own retrieval in your process, then the smoke (source window 37)
3. Do it: the join, then the kit's own retrieval in your process, then the smoke (source window 39)

Prerequisites: demo_06_make_usage_where_the_time_went_p95_per_stage_and_the_view_behind_it.
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


def step_01_the_join_then_the_kit_s_own_retrieval_in_y(session):
    """Run Do it: the join, then the kit's own retrieval in your process, then the smoke at this checkpoint.

    Do it: the join, then the kit's own retrieval in your process, then the smoke

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell; Rs 0: two files on disk).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the answer's counts: pool 20 | vector_chunks 20 | graph_chunks 0 | managed_chunks 0 | retrieval_backend vector
    a citation's fields: ['chunk_id', 'end', 'kind', 'media_url', 'page', 'quote', 'score', 'source_uri', 'start']
       #  1 hr_policy_2026.md          found_by vector   (by the join)
       #  4 hr_policy_2026.md          found_by vector   (by the join)
       #  2 hr_policy_2026.md          found_by vector   (by the join)
    """
    import json
    ans, d = json.load(open("/tmp/ans53_5.json")), json.load(open("/tmp/pool53.json"))
    stamp = {c["id"]: c["found_by"] for c in d["pool"]}
    s = ans["stages"]
    print(f"the answer's counts: pool {s['pool']} | vector_chunks {s['vector_chunks']} | graph_chunks {s['graph_chunks']} | managed_chunks {s['managed_chunks']} | retrieval_backend {s['retrieval_backend']}")
    print("a citation's fields:", sorted(ans["citations"][0]))
    for c in ans["citations"]:
        print(f"   #{c['chunk_id'].rsplit('#', 1)[1]:>3} {c['source_uri'].split('/')[-1][:26]:26} found_by {stamp.get(c['chunk_id'], 'not in the pool you fetched')}   (by the join)")

def step_02_the_join_then_the_kit_s_own_retrieval_in_y(session):
    """Run Do it: the join, then the kit's own retrieval in your process, then the smoke at this checkpoint.

    Do it: the join, then the kit's own retrieval in your process, then the smoke

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; the kit's retrieve() in this process: one embedding, one index query, one Firestore read).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 20 chunks in the pool, found_by: {'vector': 20}
    first three: [('NP-03', 'vector', 0.7xxx), ('...', 'vector', 0.7xxx), ('...', 'vector', 0.7xxx)]
    """
    import os, sys, warnings, collections
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "services/rag-api"]
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.environ["PROJECT"])          # settings.project_id; REGION and the index names are already exported
    for k in ("RETRIEVAL_MODE", "RETRIEVAL_BACKEND", "RETRIEVAL_CURRENT_ONLY", "TOP_K_RETRIEVE", "RERANK_TIMEOUT_S", "SEMANTIC_CACHE"):
        if os.environ.get(k) == "":
            del os.environ[k]                                                      # an empty export from an earlier names box means the default
    from retriever import retrieve                                                # the kit's own path: the index, the Firestore fan-out, prefer_current, the stamps
    pool = retrieve("What is the notice period for a confirmed E3?", "acme", 5)
    print(len(pool), "chunks in the pool, found_by:", dict(collections.Counter(c["found_by"] for c in pool)))
    print("first three:", [(c.get("locator", "?"), c["found_by"], round(c["score"], 4)) for c in pool[:3]])

# Original CLI workflow for step_03_the_join_then_the_kit_s_own_retrieval_in_y.
COMMANDS_03 = """set +o pipefail   # as the page runs it: make smoke's own status does not stop this filtered read
DOCUMIND_PROJECT=$PROJECT DOCUMIND_API_URL=$API DOCUMIND_TENANT=acme \\
DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$PROJECT.iam.gserviceaccount.com make smoke 2>&1 | grep -E "query|vector tier|no token|PASS|FAIL"

"""

def step_03_the_join_then_the_kit_s_own_retrieval_in_y(session):
    """Run Do it: the join, then the kit's own retrieval in your process, then the smoke at this checkpoint.

    Do it: the join, then the kit's own retrieval in your process, then the smoke

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (the smoke: one question, the same without a token, a version read; a rupee).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [PASS] health  {"status":"ok"}
      [PASS] ready  ...
      [PASS] query  answerable=True citations=3  '...'
      [PASS] vector tier  20 of 20 chunks came from the index
      [PASS] no token refused  status=403
      ...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_35', step_01_the_join_then_the_kit_s_own_retrieval_in_y),
        ('source_37', step_02_the_join_then_the_kit_s_own_retrieval_in_y),
        ('source_39', step_03_the_join_then_the_kit_s_own_retrieval_in_y),
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
