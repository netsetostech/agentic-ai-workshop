"""Lesson B.3: The residual path: add the input back

The cell adds the attention output to X, compares each word's new vector with its old one by cosine (1 is the same direction, 0 unrelated), then applies the attention sub-layer four times over, once without the residual path and once with it.

Run order inside this file:
1. Do it: add, then stack four times with and without it (source window 13)

Prerequisites: demo_05_two_heads_joined_and_what_a_head_may_see.
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


def step_01_add_then_stack_four_times_with_and_without(session):
    """Run Do it: add, then stack four times with and without it at this checkpoint.

    The cell adds the attention output to X, compares each word's new vector with its old one by cosine (1 is the same direction, 0 unrelated), then applies the attention sub-layer four times over, once without the residual path and once with it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the same shell, in the basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: H = X + attention output
                  thing   action   amount who/when slow sin slow cos fast sin fast cos
           the     0.29     0.10     0.17    -0.01     0.00     1.00     0.00     1.00
      employee     1.10     0.40     0.02     1.03     0.71     0.71     1.00     0.00
        serves     0.87     1.05     0.02     0.84     1.00     0.00     0.00    -1.00
        ninety     0.47     0.45     1.05    -0.38     0.71    -0.71    -1.00     0.00
          days     1.09     0.43     0.45    -1.03     0.00    -1.00     0.00     1.00
        notice     1.52     0.40     0.05    -0.42    -0.71    -0.71     1.00     0.00
                cos(X, attention output)  cos(X, H)
           the                      0.00       0.9
    """
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import numpy as np
    
    words = ["the", "employee", "serves", "ninety", "days", "notice"]
    meaning = np.array([[0, 0, 0, 0], [1, 0, 0, 1], [0, 1, 0, 0], [0, 0, 1, 0], [1, 0, 0, -1], [1, 0, 0, 0]])
    p = np.arange(6)[:, None] * np.pi / 4                                          # step 3's positions, as angles
    X = np.hstack([meaning, np.sin(p), np.cos(p), np.sin(2 * p), np.cos(2 * p)])   # step 3's X: 6 words x 8 numbers
    columns = ["thing", "action", "amount", "who/when", "slow sin", "slow cos", "fast sin", "fast cos"]
    
    def show(title, M, d=2, rows=words, cols=words):
        """Print the selected event fields that explain the mirror decision.
        
        Example: show('H = X + attention output', H, cols=columns)
        """
        print(title)
        print(" " * 10 + "".join(f"{c:>9}" for c in cols))
        for name, row in zip(rows, np.round(M, d) + 0.0):
            print(f"{name:>10}" + "".join(f"{v:9.{d}f}" for v in row))
    
    def softmax(S):
        """Turn each row of scores into probabilities that add up to 1 (the row's largest taken off first, against overflow).
        
        Example: softmax(scores)
        """
        e = np.exp(S - S.max(axis=1, keepdims=True))
        return e / e.sum(axis=1, keepdims=True)
    
    c, s = np.cos(np.pi / 4), np.sin(np.pi / 4)                    # head 1: one word back (step 4)
    W_Q1 = np.zeros((8, 4)); W_Q1[4:] = 4 * np.array([[c, s, 0, 0], [-s, c, 0, 0], [0, 0, 0, 1], [0, 0, -1, 0]])
    W_K1 = np.zeros((8, 4)); W_K1[4:] = np.eye(4)
    W_V1 = np.zeros((8, 4)); W_V1[:4] = np.eye(4)
    W_Q2, W_K2, W_V2 = np.zeros((8, 4)), np.zeros((8, 4)), W_V1.copy()   # head 2: the word it fits with
    W_Q2[0, 0], W_K2[1, 0] = 6, 1                                  # a thing asks for an action
    W_Q2[1, 1], W_K2[3, 1] = 6, 1                                  # an action asks for a person
    W_Q2[2, 2], W_K2[3, 2] = 6, -1                                 # an amount asks for a time
    W_O = np.zeros((8, 8)); W_O[:4, :4] = W_O[4:, :4] = 0.5 * np.eye(4)   # half of each head, into the meaning columns
    
    def head(Z, W_Q, W_K, W_V, causal=False):
        """One attention head: scaled dot products of queries and keys, an optional causal mask, softmax, then the weighted sum of values.
        
        Example: head(Z, W_Q1, W_K1, W_V1)
        """
        scores = (Z @ W_Q) @ (Z @ W_K).T / np.sqrt(W_Q.shape[1])
        if causal:                                                  # a word may not look at the words after it
            scores = np.where(np.triu(np.ones(scores.shape), 1) == 1, -np.inf, scores)
        weights = softmax(scores)
        return weights, weights @ (Z @ W_V)
    
    def attention(Z):                                               # both heads, side by side, then W_O
        """Run the lesson's two heads side by side, join their outputs and mix them through W_O.
        
        Example: attention(X)
        """
        return np.hstack([head(Z, W_Q1, W_K1, W_V1)[1], head(Z, W_Q2, W_K2, W_V2)[1]]) @ W_O
    
    attn = attention(X)
    H = X + attn                                               # the residual path: the input, added back
    show("H = X + attention output", H, cols=columns)
    
    def cos(A, B):                                             # per word: 1 is the same direction, 0 unrelated
        """Cosine per word between two matrices: 1 is the same direction, 0 unrelated.
        
        Example: np.cos(np.pi / 4)
        """
        return (A * B).sum(axis=1) / (np.linalg.norm(A, axis=1) * np.linalg.norm(B, axis=1))
    print(f"{'':>10}{'cos(X, attention output)':>26}{'cos(X, H)':>11}")
    for word, a, b in zip(words, np.round(cos(X, attn), 2) + 0.0, np.round(cos(X, H), 2)):
        print(f"{word:>10}{a:26.2f}{b:11.2f}")
    
    def gaps(Z):                                               # the closest two words, and the farthest two
        """Distances between every pair of word vectors: return the closest two and the farthest two, rounded.
        
        Example: gaps(plain)
        """
        d = np.sqrt(((Z[:, None] - Z[None, :]) ** 2).sum(axis=2))[np.triu_indices(6, 1)]
        return np.round(d.min(), 2), np.round(d.max(), 2)
    plain, kept = X, X
    for layer in range(1, 5):                                  # the attention sub-layer, four times over
        plain, kept = attention(plain), kept + attention(kept)
        print(f"layer {layer}: without the residual path the farthest two words are {gaps(plain)[1]:.2f} apart;"
              f" with it the closest two are {gaps(kept)[0]:.2f}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_add_then_stack_four_times_with_and_without),
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
