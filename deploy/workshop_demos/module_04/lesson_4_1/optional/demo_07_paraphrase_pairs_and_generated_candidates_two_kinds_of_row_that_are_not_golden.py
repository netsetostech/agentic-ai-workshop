"""Lesson 4.1: Paraphrase pairs and generated candidates: two kinds of row that are not golden

The candidate fails twice. It has no figure, so it would accept any answer. Its anchor names a version by its hash, which no file contains, and which would point at a retired version the day the handbook is re-issued. The reviewed row, with a figure, a code and a slug, is lk-32. That rewrite is what review means: a figure a person checked in the clause, and anchors that survive a new version. Last, the generator itself, if your feed has rows. The chunk feature job and the Dataplex quality scan fill the feed, and lesson 11.5 runs them (make features). Before that, the count is zero and the cell stops there.

Run order inside this file:
1. Generated candidates (source window 41)

Prerequisites: demo_07_paraphrase_pairs_and_generated_candidates_two_kinds_of_row_that_are_not_golden.
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


# Original CLI workflow for step_01_generated_candidates.
COMMANDS_01 = """N=$(bq --project_id="$PROJECT" query --nouse_legacy_sql --format=csv \\
  "SELECT COUNT(*) FROM \\`$PROJECT.rag_data.index_feed\\` WHERE tenant_id = 'acme'" | tail -1)
echo "feed rows for acme: $N"
if [ "${N:-0}" -gt 0 ] 2>/dev/null; then make make-evalset PROJECT="$PROJECT" TENANT=acme ROWS=10 && wc -l evals/golden_generated.jsonl
else echo "no feed rows yet: lesson 11.5 builds the feed (make features)"; fi

"""

def step_01_generated_candidates(session):
    """Run Generated candidates at this checkpoint.

    The candidate fails twice. It has no figure, so it would accept any answer. Its anchor names a version by its hash, which no file contains, and which would point at a retired version the day the handbook is re-issued. The reviewed row, with a figure, a code and a slug, is lk-32. That rewrite is what review means: a figure a person checked in the clause, and anchors that survive a new version. Last, the generator itself, if your feed has rows. The chunk feature job and the Dataplex quality scan fill the feed, and lesson 11.5 runs them (make features). Before that, the count is zero and the cell stops there.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one BigQuery count; ten Gemini calls only if the feed has rows).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: feed rows for acme: 0
    no feed rows yet: lesson 11.5 builds the feed (make features)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_41', step_01_generated_candidates),
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
