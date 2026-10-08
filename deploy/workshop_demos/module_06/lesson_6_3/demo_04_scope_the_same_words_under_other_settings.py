"""Lesson 6.3: Scope: the same words under other settings

Do it

Run order inside this file:
1. Do it (source window 13)

Prerequisites: demo_03_both_caches_and_the_corpus_they_follow.
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


# Original CLI workflow for step_01_scope_the_same_words_under_other_settings.
COMMANDS_01 = """ask92 "$CAND" 8                     # top_k 8: another scope
ask92 "$CAND" 6 '{"kind": "text"}'   # a filter: another scope
python - <<'PY'
import sys
sys.path.insert(0, "services/rag-api")
from semantic_cache import scope_of
for label, f, k, p in [("as asked", None, 6, "v3"), ("top_k 8", None, 8, "v3"), ("kind: text", {"kind": "text"}, 6, "v3"), ("prompt v4", None, 6, "v4")]:
    print(f"  scope {label:10} {scope_of(f, k, p)}")
PY

"""

def step_01_scope_the_same_words_under_other_settings(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same question under two other scopes, and four scope hashes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: vertex none     in  43349 cached  41259  2610 ms | A confirmed employee at grade E3 or above serves a
      vertex none     in  43109 cached  41259  2440 ms | A confirmed employee at grade E3 or above serves a
      scope as asked   7a0875abc72b0f7b
      scope top_k 8    bcc480117460bf66
      scope kind: text 8d8d4a1d9912dc52
      scope prompt v4  1d409edacc15c1d1
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_scope_the_same_words_under_other_settings),
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
