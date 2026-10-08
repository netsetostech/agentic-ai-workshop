"""Lesson B.4: A bi-encoder: two texts, encoded apart, compared by cosine

Do it: a five-axis bi-encoder on the four clauses, Rs 0

Run order inside this file:
1. Do it: a five-axis bi-encoder on the four clauses, Rs 0 (source window 7)

Prerequisites: demo_03_the_masked_language_idea_fill_the_blank_from_both_sides.
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


def step_01_a_five_axis_bi_encoder_on_the_four_clauses(session):
    """Run Do it: a five-axis bi-encoder on the four clauses, Rs 0 at this checkpoint.

    Do it: a five-axis bi-encoder on the four clauses, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in your venv (a Python cell; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the toy: 23 words on 5 axes; the store: 4 clause vectors of 5 numbers
      NP-03  [leave 0.416, exit 0.885, pay 0.000, probation 0.000, reduce 0.208]
      PB-02  [leave 0.000, exit 0.356, pay 0.000, probation 0.934, reduce 0.000]
      LV-01  [leave 1.000, exit 0.000, pay 0.000, probation 0.000, reduce 0.000]
      LV-07  [leave 0.552, exit 0.375, pay 0.690, probation 0.197, reduce 0.197]
    the question: Can I use my unused leave to shorten my notice period?
      words it knows: unused, leave, shorten, notice, period
      its vector: [leave 0.647, exit 0.647, pay 0.000, probation 0.000, reduce 0.404]
    the cosine with each stored vector, highest first (for vectors of length 1 the dot product is the cosine):
      NP-03
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
    D = np.array([encode(text) for text in CLAUSES.values()])     # at ingest: once per clause, then stored
    QUESTION = "Can I use my unused leave to shorten my notice period?"
    q = encode(QUESTION)                                          # at query time: once per question
    show = lambda v: "[" + ", ".join(f"{a} {x:.3f}" for a, x in zip(AXES, v)) + "]"
    print(f"the toy: {len(WORDS)} words on {len(AXES)} axes; the store: {D.shape[0]} clause vectors of {D.shape[1]} numbers")
    for name, v in zip(CLAUSES, D):
        print(f"  {name}  {show(v)}")
    print(f"the question: {QUESTION}")
    print(f"  words it knows: {', '.join(known(QUESTION))}")
    print(f"  its vector: {show(q)}")
    print("the cosine with each stored vector, highest first (for vectors of length 1 the dot product is the cosine):")
    for name, score in sorted(zip(CLAUSES, D @ q), key=lambda p: -p[1]):
        print(f"  {name}  {score:.3f}")
    OTHER = "Will my holidays cut my notice short?"
    print(f"the same question in other words: {OTHER}")
    print("  " + "   ".join(f"{name} {score:.3f}" for name, score in sorted(zip(CLAUSES, D @ encode(OTHER)), key=lambda p: -p[1])))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_a_five_axis_bi_encoder_on_the_four_clauses),
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
