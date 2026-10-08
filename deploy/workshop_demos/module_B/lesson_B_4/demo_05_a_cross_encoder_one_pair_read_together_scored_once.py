"""Lesson B.4: A cross-encoder: one pair, read together, scored once

Do it: the same pairs, read together, Rs 0

Run order inside this file:
1. Do it: the same pairs, read together, Rs 0 (source window 9)

Prerequisites: demo_04_a_bi_encoder_two_texts_encoded_apart_compared_by_cosine.
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


def step_01_the_same_pairs_read_together_rs_0(session):
    """Run Do it: the same pairs, read together, Rs 0 at this checkpoint.

    Do it: the same pairs, read together, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in your venv (a Python cell; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the question's ideas, in order: leave > reduce > exit
    clause    bi-encoder  cross-encoder
    NP-03          0.926           1.00
            lined up best: Unused earned leave may not be set off against the notice period.
    LV-07          0.679           1.00
            lined up best: Leave cannot be encashed during probation and cannot be used to shorten notice.
    LV-01          0.647           0.33
            lined up best: Earned leave accrues at 1.75 days per completed month.
    PB-02          0.230           0.33
            lined up best: During probation the notice period is 15 days for either side.
    the same words, swapped:
      Leave cannot be used to shorten notice.    0.980           1.00
      Notice cannot be 
    """
    import re, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    import numpy as np
    CLAUSES = {   # four clauses of the kit's handbook, evals/corpus/acme/hr_policy_2026.md
        "NP-03": ("A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice "
                  "runs from the date the resignation is acknowledged in writing. Unused earned leave may "
                  "not be set off against the notice period."),
        "PB-02": ("New joiners serve six months on probation at grade E2. During probation the notice "
                  "period is 15 days for either side. Probation may be extended once, by up to three "
                  "months, with written reasons."),
        "LV-01": ("Earned leave accrues at 1.75 days per completed month. A maximum of 30 days may be "
                  "carried forward into the next calendar year; anything above 30 lapses on 31 December."),
        "LV-07": ("Earned leave is encashed on exit at basic pay, capped at 45 days. Leave cannot be "
                  "encashed during probation and cannot be used to shorten notice."),
    }
    VOCAB = {   # every word the toy knows points along one named axis, with a weight; all other words are ignored
        "leave": {"leave": 1.0, "earned": 0.8, "unused": 0.6, "accrues": 0.6, "lapses": 0.5, "holidays": 0.9},
        "exit": {"notice": 1.0, "resignation": 0.9, "resign": 0.9, "exit": 0.9, "quit": 0.9, "period": 0.6},
        "pay": {"pay": 1.0, "paid": 1.0, "encashed": 1.0, "basic": 0.5},
        "probation": {"probation": 1.0, "joiners": 0.8, "extended": 0.4},
        "reduce": {"shorten": 1.0, "cut": 1.0, "set": 0.8, "off": 0.4},
    }
    AXES = list(VOCAB)
    WORDS = {w: (AXES.index(axis), weight) for axis, ws in VOCAB.items() for w, weight in ws.items()}
    def known(text):
        """Return the words of a text that the toy vocabulary knows, in order.
        
        Example: known(text)
        """
        return [w for w in re.findall(r"[a-z]+", text.lower()) if w in WORDS]
    def encode(text):                          # the bi-encoder: one text in, one vector out, no other text seen
        """The toy bi-encoder: one text in, one vector out, from the axes of the words it knows; no other text is seen.
        
        Example: encode(QUESTION)
        """
        v = np.zeros(len(AXES))
        for w in known(text):
            axis, weight = WORDS[w]
            v[axis] += weight                  # pooling: add up the words' vectors...
        return v / np.linalg.norm(v)           # ...and scale the sum to length 1
    def sentences(text):
        """Split a text into sentences at full stops, semicolons, question marks and exclamation marks.
        
        Example: sentences(passage)
        """
        return [s for s in re.sub(r"([.;?!])\s+", r"\1\n", text).split("\n") if s]
    def ideas(text):                           # the axes of the words it knows, in order, repeats merged
        """The axes of the words a text knows, in order, with repeats merged.
        
        Example: ideas(question)
        """
        out = []
        for w in known(text):
            axis = AXES[WORDS[w][0]]
            if not out or out[-1] != axis:
                out.append(axis)
        return out
    def aligned(q, s):                         # how many of q's ideas s holds in the same order, gaps allowed
        """Count how many of the question's ideas a sentence holds in the same order, gaps allowed.
        
        Example: aligned(q, ideas(best))
        """
        m = [[0] * (len(s) + 1) for _ in range(len(q) + 1)]
        for i in range(len(q)):
            for j in range(len(s)):
                m[i + 1][j + 1] = m[i][j] + 1 if q[i] == s[j] else max(m[i][j + 1], m[i + 1][j])
        return m[-1][-1]
    def cross(question, passage):              # the cross-encoder: the pair in, one score out
        """The toy cross-encoder: read question and passage together and score the passage's best-aligned sentence.
        
        Example: cross(QUESTION, text)
        """
        q = ideas(question)
        best = max(sentences(passage), key=lambda s: aligned(q, ideas(s)))
        return aligned(q, ideas(best)) / len(q), best
    QUESTION = "Can I use my unused leave to shorten my notice period?"
    q = encode(QUESTION)
    print(f"the question's ideas, in order: {' > '.join(ideas(QUESTION))}")
    print(f"{'clause':8}{'bi-encoder':>12}{'cross-encoder':>15}")
    for name, text in sorted(CLAUSES.items(), key=lambda p: -(encode(p[1]) @ q)):
        score, best = cross(QUESTION, text)
        print(f"{name:8}{encode(text) @ q:12.3f}{score:15.2f}")
        print(f"{'':8}lined up best: {best}")
    SAME, SWAPPED = "Leave cannot be used to shorten notice.", "Notice cannot be used to shorten leave."
    print("the same words, swapped:")
    for text in (SAME, SWAPPED):
        print(f"  {text:41}{encode(text) @ q:7.3f}{cross(QUESTION, text)[0]:15.2f}")
    print("the two vectors are identical:", bool(np.array_equal(encode(SAME), encode(SWAPPED))))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_same_pairs_read_together_rs_0),
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
