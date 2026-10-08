"""Lesson B.5: Reshape the odds: temperature, top-k and top-p

Do it: eight settings on one turn, Rs 0

Run order inside this file:
1. Do it: eight settings on one turn, Rs 0 (source window 7)

Prerequisites: demo_03_from_scores_to_one_token_greedy_and_sampling.
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


def step_01_eight_settings_on_one_turn_rs_0(session):
    """Run Do it: eight settings on one turn, Rs 0 at this checkpoint.

    Do it: eight settings on one turn, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in the Basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: setting             P(60) P(sixty) P(another figure) left
    T=0 (greedy)        1.000    0.000             0.000    1
    T=0.5               0.941    0.057             0.002    7
    T=1.0               0.750    0.185             0.066    7
    T=1.5               0.582    0.229             0.190    7
    T=2.0               0.469    0.233             0.299    7
    T=1.0, top-k 2      0.802    0.198             0.000    2
    T=1.0, top-p 0.90   0.802    0.198             0.000    2
    T=1.0, top-p 0.95   0.781    0.193             0.026    3
    """
    import numpy as np
    NEXT = ["60", "sixty", "15", "90", "45", "30", "ninety"]  # the toy's candidates after "...serves a notice period of"
    logits = np.array([4.0, 2.6, 0.6, 0.2, -0.2, -0.6, -1.0])  # the model's raw scores, one per candidate
    
    def shaped(logits, T=1.0, k=None, top_p=None):            # the three knobs, on one step's logits
        """Apply temperature, top-k and top-p to one step's logits and return the probabilities the pick draws from.
        
        Example: shaped(logits, **knobs)
        """
        z = np.asarray(logits, dtype=float)
        if T == 0:                                            # temperature 0 is greedy: all the probability on the top token
            q = (z == z.max()).astype(float)
            return q / q.sum()
        q = np.exp((z - z.max()) / T)                         # temperature divides the logits, then the softmax
        q /= q.sum()
        order = np.argsort(-q, kind="stable")                 # the candidates, likeliest first
        n = len(q) if k is None else min(k, len(q))           # top-k keeps the k likeliest
        if top_p is not None:                                 # top-p keeps the fewest whose probabilities reach top_p
            n = min(n, int(np.searchsorted(np.cumsum(q[order]), top_p)) + 1)
        q[order[n:]] = 0.0                                    # the rest can no longer be picked,
        return q / q.sum()                                    # and what is left adds up to 1 again
    
    print(f"{'setting':18} {'P(60)':>6} {'P(sixty)':>8} {'P(another figure)':>17} {'left':>4}")
    for name, knobs in (("T=0 (greedy)", dict(T=0)), ("T=0.5", dict(T=0.5)), ("T=1.0", dict(T=1.0)),
                        ("T=1.5", dict(T=1.5)), ("T=2.0", dict(T=2.0)), ("T=1.0, top-k 2", dict(k=2)),
                        ("T=1.0, top-p 0.90", dict(top_p=0.90)), ("T=1.0, top-p 0.95", dict(top_p=0.95))):
        q = shaped(logits, **knobs)
        print(f"{name:18} {q[0]:6.3f} {q[1]:8.3f} {q[2:].sum():17.3f} {int((q > 0).sum()):4d}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_eight_settings_on_one_turn_rs_0),
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
