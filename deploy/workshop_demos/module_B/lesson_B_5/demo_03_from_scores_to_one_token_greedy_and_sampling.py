"""Lesson B.5: From scores to one token: greedy and sampling

Do it: one turn of the loop, Rs 0

Run order inside this file:
1. Do it: one turn of the loop, Rs 0 (source window 5)

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


def step_01_one_turn_of_the_loop_rs_0(session):
    """Run Do it: one turn of the loop, Rs 0 at this checkpoint.

    Do it: one turn of the loop, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in the Basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 60  logit +4.0  probability 0.750
     sixty  logit +2.6  probability 0.185
        15  logit +0.6  probability 0.025
        90  logit +0.2  probability 0.017
        45  logit -0.2  probability 0.011
        30  logit -0.6  probability 0.008
    ninety  logit -1.0  probability 0.005
    total 1.000 | 60 or sixty 0.934, another figure 0.066 | greedy picks '60'
    seed 1, ten draws: 60 60 60 60 60 sixty 90 60 60 60
    seed 2, ten draws: 60 60 60 60 60 60 60 60 60 60
    seed 1, ten draws: 60 60 60 60 60 sixty 90 60 60 60
    seed 7, 10,000 draws: 60 0.747, sixty 0.190, 15 0.024, 90 0.015, 45 0.011, 30 0.007, ninety 0.006
    """
    import numpy as np
    NEXT = ["60", "sixty", "15", "90", "45", "30", "ninety"]  # the toy's candidates after "...serves a notice period of"
    logits = np.array([4.0, 2.6, 0.6, 0.2, -0.2, -0.6, -1.0])  # the model's raw scores, one per candidate
    e = np.exp(logits - logits.max())                         # softmax: exponentiate (less the largest, so nothing overflows)
    p = e / e.sum()                                           # and divide by the total, so the probabilities add up to 1
    for token, z, q in zip(NEXT, logits, p):
        print(f"{token:>6}  logit {z:+.1f}  probability {q:.3f}")
    print(f"total {p.sum():.3f} | 60 or sixty {p[:2].sum():.3f}, another figure {p[2:].sum():.3f} | greedy picks {NEXT[int(np.argmax(p))]!r}")
    
    def draws(seed):                                          # a tiny seeded generator: the same seed gives the same draws
        """Yield the seeded draws in [0, 1) the toy decoder picks with, so one seed gives the same picks on every laptop.
        
        Example: draws(7)
        """
        x = seed
        while True:
            x = (x + 0x9E3779B9) & 0xFFFFFFFF                 # step the state, then mix its bits (MurmurHash3's finaliser)
            z = ((x ^ (x >> 16)) * 0x85EBCA6B) & 0xFFFFFFFF
            z = ((z ^ (z >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
            yield (z ^ (z >> 16)) / 2**32                     # a number from 0 up to, not including, 1
    
    def sample(p, u):                                         # sampling: the first candidate whose running total passes u
        """Pick the first candidate whose running total of probability passes the draw u.
        
        Example: sample(p, next(u))
        """
        return min(int(np.searchsorted(np.cumsum(p), u, side="right")), len(p) - 1)
    
    for seed in (1, 2, 1):
        u = draws(seed)
        print(f"seed {seed}, ten draws:", " ".join(NEXT[sample(p, next(u))] for _ in range(10)))
    u = draws(7)
    counts = np.bincount([sample(p, next(u)) for _ in range(10_000)], minlength=len(NEXT))
    print("seed 7, 10,000 draws:", ", ".join(f"{t} {c / 10_000:.3f}" for t, c in zip(NEXT, counts)))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_5', step_01_one_turn_of_the_loop_rs_0),
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
