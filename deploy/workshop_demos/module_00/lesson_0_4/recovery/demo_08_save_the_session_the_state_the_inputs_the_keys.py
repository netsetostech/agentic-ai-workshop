"""Lesson 0.4: Save the session: the state, the inputs, the keys

It refuses to save without PROJECT, REGION and DEMO_ROOT, which the setup block sets. Then it checks the source session, the record of which commit of the kit the lane was deployed from, and the resume checks it again: If ~/rag-source-session.env does not exist, the save stops with STOP: Missing rag-source-session.env; restore the original source setup. The kit's commands/git-source.sh writes that file for a source repository that keeps the kit under deploy/; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit:

Run order inside this file:
1. The session keys, in your home directory (source window 47)

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


# Original CLI workflow for step_01_the_session_keys_in_your_home_directory.
COMMANDS_01 = """# once per machine, and only if rag_save_session stops with "Missing rag-source-session.env": the git helper rag_resume
# sources, and the source snapshot the helper checks, in the format commands/git-source.sh writes, for your clone
[ -s ~/rag-git-source.sh ] || cp commands/git-source.sh ~/rag-git-source.sh
[ -s ~/rag-source-session.env ] || ( umask 077; C=$(git -C "$DEMO_ROOT" rev-parse HEAD)
  printf 'export %s=%q\\n' SOURCE_BRANCH main SOURCE_COMMIT "$C" GIT_SHA "$C" RAG_SOURCE_REPO "$DEMO_ROOT" \\
    DEMO_ROOT "$DEMO_ROOT" RAG_SOURCE_BACKUP "$(mktemp -d ~/rag-source-backup.XXXXXXXX)" > ~/rag-source-session.env )

"""

def step_01_the_session_keys_in_your_home_directory(session):
    """Run The session keys, in your home directory at this checkpoint.

    It refuses to save without PROJECT, REGION and DEMO_ROOT, which the setup block sets. Then it checks the source session, the record of which commit of the kit the lane was deployed from, and the resume checks it again: If ~/rag-source-session.env does not exist, the save stops with STOP: Missing rag-source-session.env; restore the original source setup. The kit's commands/git-source.sh writes that file for a source repository that keeps the kit under deploy/; your clone keeps it at the root, so if the save stops on it, write the file once yourself, in the same format, from your clone's current commit:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, once per machine and only if the save below stops on it.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_47', step_01_the_session_keys_in_your_home_directory),
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
