"""Lesson 6.4: Choosing the threshold, and the clean-up

At lesson end: What the numbers allow, where the threshold lives, and the candidate put away. The kit's rule is the lowest candidate with no false hit on the set, and your curve names it. Before moving the switch, weigh three things. First, the rule of three: 18 different pairs with no false hit still allow a true rate of about 17%. The honest next step is more different pairs, written from real questions one word away, not a lower threshold. Second, the saving at that threshold: if it hits only a few same-fact pairs, the exact rung (the same words, no threshold at all) may be most of what the cache is worth. Third, the replay's hit from lines, which the curve cannot see. The threshold is an environment variable, SEMANTIC_CACHE_THRESHOLD, read once when a revision starts. No make target passes it, so trying 0.97 on a candidate takes gcloud run services update documind-api --no-traffic --tag candidate --update-env-vars SEMANTIC_CACHE_THRESHOLD=0.97, with your region and project, and then the replay again.

Run order inside this file:
1. Choosing the threshold, and the clean-up (source window 22)

Prerequisites: workshop setup; see this lesson README.
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


# Original CLI workflow for step_01_choosing_the_threshold_and_the_clean_up.
COMMANDS_01 = """gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate
rm -f .candidate-revision      # make promote would otherwise flip traffic to the recorded revision

"""

def step_01_choosing_the_threshold_and_the_clean_up(session):
    """Run Choosing the threshold, and the clean-up at this checkpoint.

    What the numbers allow, where the threshold lives, and the candidate put away. The kit's rule is the lowest candidate with no false hit on the set, and your curve names it. Before moving the switch, weigh three things. First, the rule of three: 18 different pairs with no false hit still allow a true rate of about 17%. The honest next step is more different pairs, written from real questions one word away, not a lower threshold. Second, the saving at that threshold: if it hits only a few same-fact pairs, the exact rung (the same words, no threshold at all) may be most of what the cache is worth. Third, the replay's hit from lines, which the curve cannot see. The threshold is an environment variable, SEMANTIC_CACHE_THRESHOLD, read once when a revision starts. No make target passes it, so trying 0.97 on a candidate takes gcloud run services update documind-api --no-traffic --tag candidate --update-env-vars SEMANTIC_CACHE_THRESHOLD=0.97, with your region and project, and then the replay again.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the candidate's tag and recorded name removed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Updating traffic...done.
    Done.
    URL: https://documind-api-...run.app
    Traffic:
      100% documind-api-000MM-xxx      (the live revision, as before; no candidate tag)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_choosing_the_threshold_and_the_clean_up),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=True, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
