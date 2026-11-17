"""Lesson 8.4: Architecture: the path a change takes, station by station

The cell cuts version 1 and revision 2 of the handbook with shared/documind_corpus.py, the notebooks' twin of the worker's chunker, which mints the same chunk texts and hashes. It applies the carry-over's rule: a chunk is reused when its hash is held. Then it cuts the same two texts as whole-document windows, the way the worker cut a handbook before 12 September 2026.

Run order inside this file:
1. Do it: the re-issue, offline (source window 21)

Prerequisites: demo_03_the_ui_and_the_ledger_where_a_change_lands_on_your_lane.
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


def step_01_the_re_issue_offline(session):
    """Run Do it: the re-issue, offline at this checkpoint.

    The cell cuts version 1 and revision 2 of the handbook with shared/documind_corpus.py, the notebooks' twin of the worker's chunker, which mints the same chunk texts and hashes. It applies the carry-over's rule: a chunk is reused when its hash is held. Then it cuts the same two texts as whole-document windows, the way the worker cut a handbook before 12 September 2026.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: by section: 283 chunks, 281 reused, 2 embedded (preamble, NP-03), 453 characters sent
    by whole-document windows: 92 chunks, 0 reused, 92 embedded, 178,706 characters sent
    revision 2's first lines: '# ACME Employee Handbook 2026 (revision 2)', then 'Effective from: 2026-10-01. Revision 2 changes NP-03: the no'
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["."]
    from shared import documind_corpus as dc     # the notebooks' twin of the worker's chunker: the same texts, hashes and locators
    v1, v2 = (open(p, encoding="utf-8").read() for p in ("evals/corpus/acme/hr_policy_2026.md", "evals/demo/hr_policy_2026_v2.md"))
    doc = lambda text: {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md", "text": text}
    old, new = dc.chunk_document(doc(v1), "acme"), dc.chunk_document(doc(v2), "acme")
    held = {c["chunk_hash"] for c in old}                       # the carry-over's rule: a vector is reused when its chunk_hash is held
    fresh = [c for c in new if c["chunk_hash"] not in held]
    print(f"by section: {len(new)} chunks, {len(new) - len(fresh)} reused, {len(fresh)} embedded "
          f"({', '.join(c['locator'] for c in fresh)}), {sum(len(c['text']) for c in fresh):,} characters sent")
    w_old, w_new = dc.windows(v1), dc.windows(v2)              # the same two texts, cut as whole-document windows
    w_held = {dc.chunk_hash(t) for t in w_old}
    w_fresh = [t for t in w_new if dc.chunk_hash(t) not in w_held]
    print(f"by whole-document windows: {len(w_new)} chunks, {len(w_new) - len(w_fresh)} reused, {len(w_fresh)} embedded, "
          f"{sum(map(len, w_fresh)):,} characters sent")
    print(f"revision 2's first lines: {v2.splitlines()[0]!r}, then {v2.splitlines()[2][:60]!r}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_the_re_issue_offline),
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
