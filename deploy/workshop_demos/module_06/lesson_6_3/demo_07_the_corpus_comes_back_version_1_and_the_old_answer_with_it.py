"""Lesson 6.3: The corpus comes back: version 1, and the old answer with it

Version 1's bytes again, the state, one ask, every row, and the clean-up. The same release command with version 1's file puts the handbook back. The worker finds bytes it retired minutes ago, flips their rows back to current, retires revision 2 in turn, and recomputes the fingerprint. Because the set of current doc_keys is the same as at the start, the fingerprint is the same as at the start too. Every row of the walk

Run order inside this file:
1. The corpus comes back: version 1, and the old answer with it (source window 24)
2. The corpus comes back: version 1, and the old answer with it (source window 26)
3. Every row of the walk (source window 28)

Prerequisites: demo_06_make_cache_again_attached_again_and_what_it_packed.
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


# Original CLI workflow for step_01_the_corpus_comes_back_version_1_and_the_ol.
COMMANDS_01 = """make reindex PROJECT="$PROJECT" TENANT=acme FILE=evals/corpus/acme/hr_policy_2026.md

"""

def step_01_the_corpus_comes_back_version_1_and_the_ol(session):
    """Run The corpus comes back: version 1, and the old answer with it at this checkpoint.

    Version 1's bytes again, the state, one ask, every row, and the clean-up. The same release command with version 1's file puts the handbook back. The worker finds bytes it retired minutes ago, flips their rows back to current, retires revision 2 in turn, and recomputes the fingerprint. Because the set of current doc_keys is the same as at the start, the fingerprint is the same as at the start too.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (version 1's bytes again: the undo).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md - waiting for the worker (up to 5 min)
    >> event doc_key chunks reused embedded retired effective_from
    >> ingest_reactivated	acme_497809ffbaa603c4...	283	283	0	283
    >> the gate, scoped to this document, on a candidate: make eval-live PROJECT=documind-ai-YOUR-ID SOURCE=hr_policy_2026.md API=<candidate url>
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_corpus_comes_back_version_1_and_the_ol.
COMMANDS_02 = """state92
ask92 "$CAND"

"""

def step_02_the_corpus_comes_back_version_1_and_the_ol(session):
    """Run The corpus comes back: version 1, and the old answer with it at this checkpoint.

    Version 1's bytes again, the state, one ask, every row, and the clean-up. The same release command with version 1's file puts the handbook back. The worker finds bytes it retired minutes ago, flips their rows back to current, retires revision 2 in turn, and recomputes the fingerprint. Because the set of current doc_keys is the same as at the start, the fingerprint is the same as at the start too.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the state, and the candidate's ask).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ledger 1ef46119bd89b143 (17 versions, last ingest_reactivated) | context cache packed from 1441fb4775d21e13: STALE
      cache  semantic in      0 cached      0   165 ms | A confirmed employee at grade E3 or above serves a
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_every_row_of_the_walk(session):
    """Run Every row of the walk at this checkpoint.

    Every row of the walk

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every acme usage row since the start; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 00041-kqz  vertex  in  43109  cached  41259  Rs 1.0201   2480 ms
      00045-tqm  vertex  in  43109  cached  41259  Rs 1.0201   2530 ms
      00045-tqm  cache   in      0  cached      0  Rs 0.0000    170 ms
      00045-tqm  vertex  in  43349  cached  41259  Rs 1.0507   2610 ms
      00045-tqm  vertex  in  43109  cached  41259  Rs 1.0201   2440 ms
      00041-kqz  vertex  in   1880  cached      0  Rs 0.4978   2390 ms
      00045-tqm  vertex  in   1880  cached      0  Rs 0.4978   2455 ms
      00041-kqz  vertex  in  43139  cached  41259  Rs 1.0239   2575 ms
      00045-tqm  cache   in      0  cached      0  Rs 0.0000    165 ms
    """
    import json, os, subprocess
    f = ('resource.type="cloud_run_revision" AND resource.labels.service_name="documind-api" AND jsonPayload.event="query" '
         f'AND jsonPayload.tenant="acme" AND timestamp>="{os.environ["SINCE92"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "20",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    for e in json.loads(out or "[]"):
        j, rev = e["jsonPayload"], e["resource"]["labels"]["revision_name"]
        print(f"  {rev[-9:]}  {j['model_backend']:6}  in {j['tokens_in']:>6}  cached {j['cached_tokens']:>6}  Rs {j['cost_usd'] * 85:.4f}  {j['latency_ms']:>5} ms")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_24', step_01_the_corpus_comes_back_version_1_and_the_ol),
        ('source_26', step_02_the_corpus_comes_back_version_1_and_the_ol),
        ('source_28', step_03_every_row_of_the_walk),
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
