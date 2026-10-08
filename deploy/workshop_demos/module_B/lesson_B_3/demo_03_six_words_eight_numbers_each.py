"""Lesson B.3: Six words, eight numbers each

Do it: build X, Rs 0

Run order inside this file:
1. Do it: build X, Rs 0 (source window 5)

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


def step_01_build_x_rs_0(session):
    """Run Do it: build X, Rs 0 at this checkpoint.

    Do it: build X, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the same shell, in the basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: tokens: 6 | numbers per token: 8
    X = word vector + position vector
                  thing   action   amount who/when slow sin slow cos fast sin fast cos
           the     0.00     0.00     0.00     0.00     0.00     1.00     0.00     1.00
      employee     1.00     0.00     0.00     1.00     0.71     0.71     1.00     0.00
        serves     0.00     1.00     0.00     0.00     1.00     0.00     0.00    -1.00
        ninety     0.00     0.00     1.00     0.00     0.71    -0.71    -1.00     0.00
          days     1.00     0.00     0.00    -1.00     0.00    -1.00     0.00     1.00
        notice     1.00     0.00     0.00     0.00    -0.71    -0.71     1.00     0.00
    position . position: one position's waves against an
    """
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import numpy as np
    
    words = ["the", "employee", "serves", "ninety", "days", "notice"]
    # each word's own four numbers, set by hand: thing, action, amount, who/when (+1 a person, -1 a time)
    meaning = np.array([[0, 0, 0, 0],      # the
                        [1, 0, 0, 1],      # employee: a thing, and a person
                        [0, 1, 0, 0],      # serves: an action
                        [0, 0, 1, 0],      # ninety: an amount
                        [1, 0, 0, -1],     # days: a thing, and a time
                        [1, 0, 0, 0]])     # notice: a thing
    # each position's four numbers: a slow wave that turns 45 degrees a word, and a fast one that turns 90
    p = np.arange(6)[:, None] * np.pi / 4
    waves = np.hstack([np.sin(p), np.cos(p), np.sin(2 * p), np.cos(2 * p)])
    word_vec = np.hstack([meaning, np.zeros((6, 4))])     # the word, in columns 0 to 3
    pos_vec = np.hstack([np.zeros((6, 4)), waves])        # its position, in columns 4 to 7
    X = word_vec + pos_vec                                # what the block reads: 6 words x 8 numbers
    columns = ["thing", "action", "amount", "who/when", "slow sin", "slow cos", "fast sin", "fast cos"]
    
    def show(title, M, d=2, rows=words, cols=words):
        """Print the selected event fields that explain the mirror decision.
        
        Example: show('X = word vector + position vector', X, cols=columns)
        """
        print(title)
        print(" " * 10 + "".join(f"{c:>9}" for c in cols))
        for name, row in zip(rows, np.round(M, d) + 0.0):
            print(f"{name:>10}" + "".join(f"{v:9.{d}f}" for v in row))
    
    print("tokens:", X.shape[0], "| numbers per token:", X.shape[1])
    show("X = word vector + position vector", X, cols=columns)
    D = waves @ waves.T
    positions = [f"pos {t}" for t in range(6)]
    show("position . position: one position's waves against another's", D, rows=positions, cols=positions)
    print("the same along every diagonal, so it measures distance only:",
          all(np.allclose(np.diag(D, k), np.diag(D, k)[0]) for k in range(6)))
    print("every position's signal has the same length:", " ".join(f"{v:.2f}" for v in np.round(np.linalg.norm(waves, axis=1), 2)))
    print("adding the two is the same as setting them side by side:", np.array_equal(X, np.hstack([meaning, waves])))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_5', step_01_build_x_rs_0),
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
