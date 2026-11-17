"""Lesson 10.10: The reviewer: a linter first, then Gemini on your lane

Offline, a linter takes the reviewer's seat: a few regular expressions over the diff's added lines, and a check that added code which writes notes names NO_HOLIDAYS. It shows how the score is kept, at Rs 0. The first cell scores it on the seven diffs, and the second runs it on the diff of your hand iteration from step 3. With PROJECT, make review-eval reviews the seven diffs with gemini-3.6-flash on location global, thinking low. It runs as you: a review reads a diff and calls no tool, so it uses your own sign-in, unlike the loop's agent. REPEAT=3 reviews each diff three times, because a model's review differs from run to run. That is 21 calls, about Rs 5.48 of input (each request is 2,042 to 2,054 tokens by the kit's four-characters-a-token count), plus output and thinking, which the kit does not cap. REPEAT=1 costs a third. SAVE keeps every finding with the model and the date, and make review-eval FROM= with that file rescores it at Rs 0.

Run order inside this file:
1. Do it: the linter, offline (source window 48)
2. Do it: the linter, offline (source window 50)
3. Do it: Gemini, on your lane (source window 52)

Prerequisites: demo_06_paper_to_code_the_same_function_from_the_statute_alone.
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


# Original CLI workflow for step_01_the_linter_offline.
COMMANDS_01 = """make review-eval OFFLINE=1

"""

def step_01_the_linter_offline(session):
    """Run Do it: the linter, offline at this checkpoint.

    Offline, a linter takes the reviewer's seat: a few regular expressions over the diff's added lines, and a check that added code which writes notes names NO_HOLIDAYS. It shows how the score is kept, at Rs 0. The first cell scores it on the seven diffs, and the second runs it on the diff of your hand iteration from step 3.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the linter in the reviewer's seat, on the seven diffs; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: review-eval: a linter (offline: regular expressions, not a model)
      7 diffs from the Ralph task's start: the kit's own statutory_deadline (no defect) and 6 seeded with one defect each; each reviewed 1 time
      diff                  seeded rule         found   near   false alarms
      reference             (none)              -       -      1 (wrong_citation)
      placeholder           placeholder         1/1     1/1    1 (wrong_citation)
      calendar_days         calendar_days       1/1     1/1    1 (wrong_citation)
      start_day_counted     off_by_one          0/1     0/1    1 (wrong_citation)
      closure_counted       event_scope         1/1     1/1    1 (wrong_citation)
      date_contract         error_co
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_linter_offline.
COMMANDS_02 = """make review-diff OFFLINE=1 DIFF="$(dirname "$WS")/by-hand.patch"

"""

def step_02_the_linter_offline(session):
    """Run Do it: the linter, offline at this checkpoint.

    Offline, a linter takes the reviewer's seat: a few regular expressions over the diff's added lines, and a check that added code which writes notes names NO_HOLIDAYS. It shows how the score is kept, at Rs 0. The first cell scores it on the seven diffs, and the second runs it on the diff of your hand iteration from step 3.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the linter on your hand iteration's diff; Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: review-diff: by-hand.patch, by a linter (offline: regular expressions, not a model)
      line 363: wrong_citation - s.17(3) is cited, but the deadline is s.17(2)'s
      1 finding; Rs 0.0000
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_gemini_on_your_lane.
COMMANDS_03 = """make review-eval PROJECT="$PROJECT" REPEAT=3 SAVE="$HOME/review-eval.json"

"""

def step_03_gemini_on_your_lane(session):
    """Run Do it: Gemini, on your lane at this checkpoint.

    With PROJECT, make review-eval reviews the seven diffs with gemini-3.6-flash on location global, thinking low. It runs as you: a review reads a diff and calls no tool, so it uses your own sign-in, unlike the loop's agent. REPEAT=3 reviews each diff three times, because a model's review differs from run to run. That is 21 calls, about Rs 5.48 of input (each request is 2,042 to 2,054 tokens by the kit's four-characters-a-token count), plus output and thinking, which the kit does not cap. REPEAT=1 costs a third. SAVE keeps every finding with the model and the date, and make review-eval FROM= with that file rescores it at Rs 0.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (Gemini on your lane: 21 calls; REPEAT=1 makes it 7).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/review_eval.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_48', step_01_the_linter_offline),
        ('source_50', step_02_the_linter_offline),
        ('source_52', step_03_gemini_on_your_lane),
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
