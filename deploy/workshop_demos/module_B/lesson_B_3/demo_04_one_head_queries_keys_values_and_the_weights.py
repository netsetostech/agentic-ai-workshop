"""Lesson B.3: One head: queries, keys, values and the weights

WQ is the matrix to read. It takes only the four wave columns, turns each wave back by one word's angle (45 degrees for the slow wave, 90 for the fast), and multiplies by 4. So the query of the word at position t is four times the waves of position t − 1. WK leaves each key as the word's own waves. By step 3's table, two positions' waves have their largest dot product when they are the same position, so every query scores highest against the key one word back. WV copies the meaning columns: what head 1 hands each word is, mostly, the meaning of the word before it.

Run order inside this file:
1. Head 1: one word back (source window 7)

Prerequisites: demo_03_six_words_eight_numbers_each.
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


def step_01_head_1_one_word_back(session):
    """Run Head 1: one word back at this checkpoint.

    WQ is the matrix to read. It takes only the four wave columns, turns each wave back by one word's angle (45 degrees for the slow wave, 90 for the fast), and multiplies by 4. So the query of the word at position t is four times the waves of position t − 1. WK leaves each key as the word's own waves. By step 3's table, two positions' waves have their largest dot product when they are the same position, so every query scores highest against the key one word back. WV copies the meaning columns: what head 1 hands each word is, mostly, the meaning of the word before it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the same shell, in the basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: W_Q: both waves turned back one word, times 4 (rows: X's columns)
                     q1       q2       q3       q4
         thing     0.00     0.00     0.00     0.00
        action     0.00     0.00     0.00     0.00
        amount     0.00     0.00     0.00     0.00
      who/when     0.00     0.00     0.00     0.00
      slow sin     2.83     2.83     0.00     0.00
      slow cos    -2.83     2.83     0.00     0.00
      fast sin     0.00     0.00     0.00     4.00
      fast cos     0.00     0.00    -4.00     0.00
    Q | K
                     q1       q2       q3       q4       k1       k2       k3       k4
           the    -2.83     2.83    -4.00     0.00     0.00     1.00     0.00     1.00
      employee     0.00     4.00     0.00  
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
        
        Example: show("W_Q: both waves turned back one word, times 4 (rows: X's columns)", W_Q, rows=columns, cols=['q1', 'q2', 'q3', 'q4'])
        """
        print(title)
        print(" " * 10 + "".join(f"{c:>9}" for c in cols))
        for name, row in zip(rows, np.round(M, d) + 0.0):
            print(f"{name:>10}" + "".join(f"{v:9.{d}f}" for v in row))
    
    def softmax(S):                                      # row by row: e to each score, over the row's total
        """Turn each row of scores into probabilities that add up to 1 (the row's largest taken off first, against overflow).
        
        Example: softmax(scores)
        """
        e = np.exp(S - S.max(axis=1, keepdims=True))     # taking the row's largest off first changes nothing but overflow
        return e / e.sum(axis=1, keepdims=True)
    
    # head 1's three weight matrices, 8 x 4 each
    c, s = np.cos(np.pi / 4), np.sin(np.pi / 4)
    W_Q = np.zeros((8, 4)); W_Q[4:] = 4 * np.array([[c, s, 0, 0], [-s, c, 0, 0], [0, 0, 0, 1], [0, 0, -1, 0]])
    W_K = np.zeros((8, 4)); W_K[4:] = np.eye(4)          # a key: the word's own position, as it is
    W_V = np.zeros((8, 4)); W_V[:4] = np.eye(4)          # a value: the word's own meaning, as it is
    
    Q, K, V = X @ W_Q, X @ W_K, X @ W_V                  # 6 x 4 each
    scores = Q @ K.T / np.sqrt(4)                        # 6 x 6: every query against every key
    weights = softmax(scores)                            # 6 x 6: each row, one word's attention in shares
    out = weights @ V                                    # 6 x 4: each word's weighted sum of the values
    
    show("W_Q: both waves turned back one word, times 4 (rows: X's columns)", W_Q, rows=columns, cols=["q1", "q2", "q3", "q4"])
    show("Q | K", np.hstack([Q, K]), cols=["q1", "q2", "q3", "q4", "k1", "k2", "k3", "k4"])
    show("scores = Q @ K.T / 2 (rows: the word asking; columns: the word it looks at)", scores)
    show("weights = softmax(scores)", weights)
    print("each row sums to:", " ".join(f"{v:.2f}" for v in np.round(weights.sum(axis=1), 2)))
    show("out = weights @ V: what head 1 hands each word", out, cols=columns[:4])
    for word, row in zip(words, weights):
        print(f"{word:>10} looks at {words[row.argmax()]:<9}{np.round(row.max(), 2):.2f}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_head_1_one_word_back),
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
