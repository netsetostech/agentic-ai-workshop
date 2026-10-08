"""Lesson B.3: Layer normalization: mean 0, variance 1, then a scale and a shift

Do it: normalize H, Rs 0

Run order inside this file:
1. Do it: normalize H, Rs 0 (source window 15)

Prerequisites: demo_06_the_residual_path_add_the_input_back.
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


def step_01_normalize_h_rs_0(session):
    """Run Do it: normalize H, Rs 0 at this checkpoint.

    Do it: normalize H, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the same shell, in the basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: each word's mean and variance, before and after
                   mean  variance  ->       mean   variance
           the   0.3196    0.1635  ->   0.000000   0.999939
      employee   0.6210    0.1686  ->   0.000000   0.999941
        serves   0.3482    0.4504  ->   0.000000   0.999978
        ninety   0.0743    0.4550  ->   0.000000   0.999978
          days   0.1183    0.5675  ->   0.000000   0.999982
        notice   0.1418    0.5611  ->   0.000000   0.999982
    H_hat = (H - mean) / sqrt(variance + eps)
                  thing   action   amount who/when slow sin slow cos fast sin fast cos
           the    -0.06    -0.53    -0.37    -0.81    -0.79     1.68    -0.79     1.68
      employee     1.18    -0.53    -1.46     0.99     0
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
        
        Example: show('H_hat = (H - mean) / sqrt(variance + eps)', H_hat, cols=columns)
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
    
    H = X + attention(X)                                       # step 6's H
    mean = H.mean(axis=1, keepdims=True)                       # one mean per word, over its own 8 numbers
    var = H.var(axis=1, keepdims=True)                         # one variance per word: the mean squared distance from it
    eps = 1e-5                                                 # keeps a word of eight equal numbers from dividing by zero
    H_hat = (H - mean) / np.sqrt(var + eps)
    print("each word's mean and variance, before and after")
    print(f"{'':>10}{'mean':>9}{'variance':>10}  ->{'mean':>11}{'variance':>11}")
    for word, m0, v0, m1, v1 in zip(words, np.round(mean[:, 0], 4), np.round(var[:, 0], 4),
                                    np.round(H_hat.mean(axis=1), 6) + 0.0, np.round(H_hat.var(axis=1), 6)):
        print(f"{word:>10}{m0:9.4f}{v0:10.4f}  ->{m1:11.6f}{v1:11.6f}")
    show("H_hat = (H - mean) / sqrt(variance + eps)", H_hat, cols=columns)
    print("every word's length is now the square root of 8:", " ".join(f"{v:.2f}" for v in np.round(np.linalg.norm(H_hat, axis=1), 2)))
    
    gamma = np.array([1.5, 1.5, 1.5, 1.5, 0.5, 0.5, 0.5, 0.5])    # the learned scale, set by hand here
    beta = np.array([0.2, 0.2, 0.2, 0.2, 0.0, 0.0, 0.0, 0.0])     # the learned shift, set by hand here
    show("gamma * H_hat + beta: the meaning columns turned up, the position columns down", gamma * H_hat + beta, cols=columns)
    
    def layer_norm(Z):
        """Layer normalization per word: subtract the mean, divide by the standard deviation, then scale and shift when given.
        
        Example: layer_norm(10 * H)
        """
        return (Z - Z.mean(axis=1, keepdims=True)) / np.sqrt(Z.var(axis=1, keepdims=True) + eps)
    print("a word ten times as loud comes out the same:", np.allclose(layer_norm(10 * H), H_hat, atol=1e-3))
    changed = H.copy()
    changed[2] = -3 * H[2]                                     # change serves, and only serves
    print("changing one word moves no other word:", np.allclose(np.delete(layer_norm(changed), 2, axis=0), np.delete(H_hat, 2, axis=0)))
    R = H / np.sqrt((H ** 2).mean(axis=1, keepdims=True) + eps)   # RMSNorm: no mean taken off, and no shift
    print("RMSNorm per word, mean:           ", " ".join(f"{v:6.3f}" for v in np.round(R.mean(axis=1), 3)))
    print("RMSNorm per word, mean of squares:", " ".join(f"{v:6.3f}" for v in np.round((R ** 2).mean(axis=1), 3)))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_normalize_h_rs_0),
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
