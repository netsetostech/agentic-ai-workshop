"""Lesson B.5: The loop, and five runs of one prompt counted

Do it: thirty runs and one cut short, Rs 0

Run order inside this file:
1. Do it: thirty runs and one cut short, Rs 0 (source window 9)

Prerequisites: demo_04_reshape_the_odds_temperature_top_k_and_top_p.
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


def step_01_thirty_runs_and_one_cut_short_rs_0(session):
    """Run Do it: thirty runs and one cut short, Rs 0 at this checkpoint.

    Do it: thirty runs and one cut short, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in the Basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: greedy (T=0)    distinct 1 of 5, another figure in 0 of 5
                    60 days . | 60 days . | 60 days . | 60 days . | 60 days .
    T=0.5           distinct 2 of 5, another figure in 0 of 5
                    60 days . | 60 days . | 60 days . | 60 days . | 60 days from acknowledgement .
    T=1.0           distinct 3 of 5, another figure in 0 of 5
                    60 days . | 60 days . | sixty days . | 60 days . | 60 days from acknowledgement .
    T=1.5           distinct 4 of 5, another figure in 1 of 5
                    sixty days . | sixty days . | 45 days . | 60 days . | 60 calendar days .
    T=2.0           distinct 5 of 5, another figure in 2 of 5
                    sixty days from acknowledgement . | 15
    """
    import numpy as np
    FIGURES = ("60", "sixty", "15", "90", "45", "30", "ninety")
    TABLE = {"of": dict(zip(FIGURES, (4.0, 2.6, 0.6, 0.2, -0.2, -0.6, -1.0))),   # the toy model: for the last token written,
             **{f: {"days": 2.4, "calendar": 1.0} for f in FIGURES},             # the logits of the tokens that may follow
             "calendar": {"days": 1.0}, "days": {".": 1.6, "from": 0.9},
             "from": {"acknowledgement": 1.0}, "acknowledgement": {".": 1.0}, ".": {"<end>": 1.0}}
    
    def draws(seed):                                          # a tiny seeded generator: the same seed gives the same draws
        """Yield the seeded draws in [0, 1) the toy decoder picks with, so one seed gives the same picks on every laptop.
        
        Example: draws(seed)
        """
        x = seed
        while True:
            x = (x + 0x9E3779B9) & 0xFFFFFFFF                 # step the state, then mix its bits (MurmurHash3's finaliser)
            z = ((x ^ (x >> 16)) * 0x85EBCA6B) & 0xFFFFFFFF
            z = ((z ^ (z >> 13)) * 0xC2B2AE35) & 0xFFFFFFFF
            yield (z ^ (z >> 16)) / 2**32                     # a number from 0 up to, not including, 1
    
    def shaped(logits, T=1.0, k=None, top_p=None):            # the three knobs, on one step's logits
        """Apply temperature, top-k and top-p to one step's logits and return the probabilities the pick draws from.
        
        Example: shaped(logits, T, k, top_p)
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
    
    def generate(seed, T=1.0, k=None, top_p=None, cap=8):     # the loop: score, shape, pick, append
        """Run the toy decode loop (score, shape, pick, append) from one seed until the end token or the cap.
        
        Example: generate(1, T=0, cap=2)
        """
        u, last, out = draws(seed), "of", []
        while len(out) < cap:
            tokens, logits = list(TABLE[last]), list(TABLE[last].values())
            q = shaped(logits, T, k, top_p)
            pick = tokens[min(int(np.searchsorted(np.cumsum(q), next(u), side="right")), len(q) - 1)]
            if pick == "<end>":
                return " ".join(out), "STOP"                  # the model ended it: finish reason STOP
            out.append(pick)
            last = pick
        return " ".join(out), "MAX_TOKENS"                    # the cap ended it: finish reason MAX_TOKENS
    
    for name, knobs in (("greedy (T=0)", dict(T=0)), ("T=0.5", dict(T=0.5)), ("T=1.0", dict(T=1.0)), ("T=1.5", dict(T=1.5)),
                        ("T=2.0", dict(T=2.0)), ("T=2.0, top-k 2", dict(T=2.0, k=2))):
        runs = [generate(seed, **knobs)[0] for seed in range(1, 6)]   # the same five seeds each time: only the knobs change
        other = sum(run.split()[0] not in ("60", "sixty") for run in runs)
        print(f"{name:15} distinct {len(set(runs))} of 5, another figure in {other} of 5")
        print(" " * 16 + " | ".join(runs))
    print("greedy, capped at 2 tokens:", generate(1, T=0, cap=2))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_thirty_runs_and_one_cut_short_rs_0),
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
