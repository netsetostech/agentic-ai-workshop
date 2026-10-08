"""Lesson B.3: The block, assembled

Do it: one block, both orders, Rs 0

Run order inside this file:
1. Do it: one block, both orders, Rs 0 (source window 17)

Prerequisites: demo_07_layer_normalization_mean_0_variance_1_then_a_scale_and_a_shift.
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


def step_01_one_block_both_orders_rs_0(session):
    """Run Do it: one block, both orders, Rs 0 at this checkpoint.

    Do it: one block, both orders, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the same shell, in the basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: Y = block(X)
                  thing   action   amount who/when slow sin slow cos fast sin fast cos
           the    -0.12    -0.43    -0.44    -0.67    -0.85     1.68    -0.87     1.69
      employee     1.20    -0.57    -1.39     0.92     0.27     0.15     0.97    -1.55
        serves     0.77     1.08    -0.53     0.77     0.93    -0.48    -0.59    -1.98
        ninety     0.61     0.52     1.47    -0.70     0.96    -1.18    -1.55    -0.13
          days     1.21     0.55     0.24    -1.34    -0.46    -1.22    -0.52     1.54
        notice     1.84     0.53    -0.41    -0.52    -1.62    -0.82     0.74     0.27
    in (6, 8) -> out (6, 8) -> a second block reads Y and returns (6, 8)
    per word, mean:      0.000  0.000  0.
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
        
        Example: show('Y = block(X)', Y, cols=columns)
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
        
        Example: attention(layer_norm(Z, gamma1, beta1))
        """
        return np.hstack([head(Z, W_Q1, W_K1, W_V1)[1], head(Z, W_Q2, W_K2, W_V2)[1]]) @ W_O
    
    def layer_norm(Z, gamma, beta, eps=1e-5):
        """Layer normalization per word: subtract the mean, divide by the standard deviation, then scale and shift when given.
        
        Example: layer_norm(Z + attention(Z), gamma1, beta1)
        """
        return gamma * (Z - Z.mean(axis=1, keepdims=True)) / np.sqrt(Z.var(axis=1, keepdims=True) + eps) + beta
    gamma1, beta1, gamma2, beta2 = np.ones(8), np.zeros(8), np.ones(8), np.zeros(8)   # where training starts them
    r8, r32 = np.arange(8), np.arange(32)
    W_1, b_1 = np.cos(r8[:, None] + 2 * r32) / 2, np.zeros(32)    # 8 x 32: a formula standing in for trained weights
    W_2, b_2 = np.sin(r32[:, None] + 3 * r8) / 4, np.zeros(8)     # 32 x 8
    
    def feed_forward(Z):                                       # each word alone: 8 -> 32 -> 8, with ReLU between
        """The block's feed-forward part, each word alone: widen, ReLU, narrow back.
        
        Example: feed_forward(layer_norm(H1, gamma2, beta2))
        """
        return np.maximum(0, Z @ W_1 + b_1) @ W_2 + b_2
    
    def block(Z):                                              # the 2017 paper's order: add, then norm
        """One transformer block in the 2017 paper's order: attention, add, norm; then feed-forward, add, norm.
        
        Example: block(X)
        """
        H1 = layer_norm(Z + attention(Z), gamma1, beta1)
        return layer_norm(H1 + feed_forward(H1), gamma2, beta2)
    
    def block_norm_first(Z):                                   # GPT-2's order, and most models' since: norm, then add
        """One transformer block in GPT-2's order: norm first inside each part, then add the residual.
        
        Example: block_norm_first(X)
        """
        H1 = Z + attention(layer_norm(Z, gamma1, beta1))
        return H1 + feed_forward(layer_norm(H1, gamma2, beta2))
    
    Y = block(X)
    show("Y = block(X)", Y, cols=columns)
    print("in", X.shape, "-> out", Y.shape, "-> a second block reads Y and returns", block(Y).shape)
    print("per word, mean:    ", " ".join(f"{v:6.3f}" for v in np.round(Y.mean(axis=1), 3) + 0.0))
    print("per word, variance:", " ".join(f"{v:6.3f}" for v in np.round(Y.var(axis=1), 3)))
    Yn = block_norm_first(X)
    print("norm first, mean:    ", " ".join(f"{v:6.3f}" for v in np.round(Yn.mean(axis=1), 3) + 0.0))
    print("norm first, variance:", " ".join(f"{v:6.3f}" for v in np.round(Yn.var(axis=1), 3)))
    learned = {"attention": [W_Q1, W_K1, W_V1, W_Q2, W_K2, W_V2, W_O], "feed-forward": [W_1, b_1, W_2, b_2],
               "layer norms": [gamma1, beta1, gamma2, beta2]}
    sizes = {part: sum(w.size for w in ws) for part, ws in learned.items()}
    print("numbers a trained block learns:", sum(sizes.values()), sizes)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_17', step_01_one_block_both_orders_rs_0),
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
