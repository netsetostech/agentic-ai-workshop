"""Lesson B.3: Two heads, joined, and what a head may see

Head 2 reads only the meaning columns, and each of its first three columns is one question and the answer it wants. A thing asks for an action (WQ reads thing, WK reads action). An action asks for a person (who/when at +1). An amount asks for a time (who/when at −1). Its fourth column is left empty. WO adds half of each head's output into the meaning columns and writes nothing into the position columns. An encoder, the BERT-style model of lesson B.4, lets every word attend to every word. A decoder, the GPT-style model of lesson B.5, writes one token after another, so a word must not attend to the words after it: when it is written, they do not exist yet. Before the softmax the decoder sets those scores to minus infinity, which the softmax turns into a share of exactly 0. That is the causal mask. The second half of the cell is the reason for step 3's position columns: reverse the six words, keep the positions where they were, and see which head notices.

Run order inside this file:
1. Head 2: the word it fits with (source window 9)
2. What a head may see: the mask, and the order of the words (source window 11)

Prerequisites: demo_04_one_head_queries_keys_values_and_the_weights.
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


def step_01_head_2_the_word_it_fits_with(session):
    """Run Head 2: the word it fits with at this checkpoint.

    Head 2 reads only the meaning columns, and each of its first three columns is one question and the answer it wants. A thing asks for an action (WQ reads thing, WK reads action). An action asks for a person (who/when at +1). An amount asks for a time (who/when at −1). Its fourth column is left empty. WO adds half of each head's output into the meaning columns and writes nothing into the position columns.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the same shell, in the basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: W_Q2 | W_K2 (rows: X's columns)
                     q1       q2       q3       q4       k1       k2       k3       k4
         thing     6.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
        action     0.00     6.00     0.00     0.00     1.00     0.00     0.00     0.00
        amount     0.00     0.00     6.00     0.00     0.00     0.00     0.00     0.00
      who/when     0.00     0.00     0.00     0.00     0.00     1.00    -1.00     0.00
      slow sin     0.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
      slow cos     0.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
      fast sin     0.00     0.00     0.00     0.00     0.00     0.00     0.00     0.00
      fa
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
        
        Example: show("W_Q2 | W_K2 (rows: X's columns)", np.hstack([W_Q2, W_K2]), rows=columns, cols=['q1', 'q2', 'q3', 'q4', 'k1', 'k2', 'k3', 'k4'])
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
        
        Example: head(X, W_Q1, W_K1, W_V1)
        """
        scores = (Z @ W_Q) @ (Z @ W_K).T / np.sqrt(W_Q.shape[1])
        if causal:                                                  # a word may not look at the words after it
            scores = np.where(np.triu(np.ones(scores.shape), 1) == 1, -np.inf, scores)
        weights = softmax(scores)
        return weights, weights @ (Z @ W_V)
    
    def attention(Z):                                               # both heads, side by side, then W_O
        """Run the lesson's two heads side by side, join their outputs and mix them through W_O.
        
        Example: attention(Z) in the owning lesson/helper context
        """
        return np.hstack([head(Z, W_Q1, W_K1, W_V1)[1], head(Z, W_Q2, W_K2, W_V2)[1]]) @ W_O
    
    weights1, out1 = head(X, W_Q1, W_K1, W_V1)
    weights2, out2 = head(X, W_Q2, W_K2, W_V2)
    show("W_Q2 | W_K2 (rows: X's columns)", np.hstack([W_Q2, W_K2]), rows=columns, cols=["q1", "q2", "q3", "q4", "k1", "k2", "k3", "k4"])
    show("head 2's weights", weights2)
    for word, row in zip(words, weights2):
        if np.round(row.max() - row.min(), 2) == 0:
            print(f"{word:>10} asks nothing, so its attention spreads evenly")
        else:
            print(f"{word:>10} looks at {words[row.argmax()]:<9}{np.round(row.max(), 2):.2f}")
    both = np.hstack([out1, out2])                       # 6 x 8: head 1's four numbers, then head 2's
    attn = both @ W_O                                    # 6 x 8: back in X's own eight columns
    heads8 = ["1 thing", "1 action", "1 amount", "1 who", "2 thing", "2 action", "2 amount", "2 who"]
    show("concat = [head 1 | head 2]", both, cols=heads8)
    show("W_O (rows: the concat's columns)", W_O, rows=heads8, cols=columns)
    show("attention output = concat @ W_O", attn, cols=columns)

def step_02_what_a_head_may_see_the_mask_and_the_order(session):
    """Run What a head may see: the mask, and the order of the words at this checkpoint.

    An encoder, the BERT-style model of lesson B.4, lets every word attend to every word. A decoder, the GPT-style model of lesson B.5, writes one token after another, so a word must not attend to the words after it: when it is written, they do not exist yet. Before the softmax the decoder sets those scores to minus infinity, which the softmax turns into a share of exactly 0. That is the causal mask. The second half of the cell is the reason for step 3's position columns: reverse the six words, keep the positions where they were, and see which head notices.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the same shell, in the basics venv (numpy only, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: head 1's weights under the causal mask: each word sees itself and the words before it
                    the employee   serves   ninety     days   notice
           the     1.00     0.00     0.00     0.00     0.00     0.00
      employee     0.93     0.07     0.00     0.00     0.00     0.00
        serves     0.07     0.87     0.07     0.00     0.00     0.00
        ninety     0.00     0.07     0.87     0.07     0.00     0.00
          days     0.00     0.00     0.07     0.86     0.07     0.00
        notice     0.02     0.00     0.00     0.06     0.85     0.06
    head 2's weights under the causal mask
                    the employee   serves   ninety     days   notice
           the     1.00     0.00     0.00     0.00     0.00
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
        
        Example: show("head 1's weights under the causal mask: each word sees itself and the words before it", masked1)
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
        
        Example: head(X, W_Q1, W_K1, W_V1, causal=True)
        """
        scores = (Z @ W_Q) @ (Z @ W_K).T / np.sqrt(W_Q.shape[1])
        if causal:                                                  # a word may not look at the words after it
            scores = np.where(np.triu(np.ones(scores.shape), 1) == 1, -np.inf, scores)
        weights = softmax(scores)
        return weights, weights @ (Z @ W_V)
    
    def attention(Z):                                               # both heads, side by side, then W_O
        """Run the lesson's two heads side by side, join their outputs and mix them through W_O.
        
        Example: attention(Z) in the owning lesson/helper context
        """
        return np.hstack([head(Z, W_Q1, W_K1, W_V1)[1], head(Z, W_Q2, W_K2, W_V2)[1]]) @ W_O
    
    masked1, _ = head(X, W_Q1, W_K1, W_V1, causal=True)
    masked2, _ = head(X, W_Q2, W_K2, W_V2, causal=True)
    show("head 1's weights under the causal mask: each word sees itself and the words before it", masked1)
    show("head 2's weights under the causal mask", masked2)
    _, out1 = head(X, W_Q1, W_K1, W_V1)
    _, out2 = head(X, W_Q2, W_K2, W_V2)
    order = [5, 4, 3, 2, 1, 0]                                 # the same six words, back to front
    Xr = np.hstack([meaning[order], X[:, 4:]])                 # the words move; the positions stay where they were
    weights1r, out1r = head(Xr, W_Q1, W_K1, W_V1)
    _, out2r = head(Xr, W_Q2, W_K2, W_V2)
    print("reversed:", " ".join(words[i] for i in order))
    print("head 2 hands every word the same numbers as before:", np.allclose(out2r, out2[order]))
    print("head 1 hands every word the same numbers as before:", np.allclose(out1r, out1[order]))
    print("one word back from serves is now:", words[order[weights1r[order.index(2)].argmax()]])

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_head_2_the_word_it_fits_with),
        ('source_11', step_02_what_a_head_may_see_the_mask_and_the_order),
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
