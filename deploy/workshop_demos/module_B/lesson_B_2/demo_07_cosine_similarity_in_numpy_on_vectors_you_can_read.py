"""Lesson B.2: Cosine similarity in numpy, on vectors you can read

Do it: four cosines, then word counts against meaning

Run order inside this file:
1. Do it: four cosines, then word counts against meaning (source window 19)

Prerequisites: demo_06_the_model_s_own_count_count_tokens_on_gemini_3_6_flash.
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


def step_01_four_cosines_then_word_counts_against_mean(session):
    """Run Do it: four cosines, then word counts against meaning at this checkpoint.

    Do it: four cosines, then word counts against meaning

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in ~/basics-venv (a Python cell; Rs 0, nothing leaves the machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: a [3. 4.]  b [4. 3.]
    cosine(a, b)        0.9600
    cosine(a, 10 * a)   1.0000   the length does not count, only the direction
    cosine(a, [-4, 3])  0.0000   at right angles
    cosine(a, -a)      -1.0000   opposite
    at length 1 the dot product is the cosine: 0.9600

    word-count vectors: 78 dimensions, one per distinct word
    lk-05     IT-SEC-04 0.2887  EXP-12 0.0000  PR-05 0.0680   shared with IT-SEC-04: ['are', 'company', 'on', 'usb']
    reworded  IT-SEC-04 0.0000  EXP-12 0.0550  PR-05 0.0000   shared with IT-SEC-04: []
    """
    import re
    import numpy as np
    def cosine(a, b):
        """The cosine of the angle between a and b: 1 the same direction, 0 at right angles, -1 opposite.
        
        Example: cosine(a, b)
        """
        return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
    a, b = np.array([3.0, 4.0]), np.array([4.0, 3.0])
    print("a", a, " b", b)
    print(f"cosine(a, b)       {cosine(a, b):7.4f}")
    print(f"cosine(a, 10 * a)  {cosine(a, 10 * a):7.4f}   the length does not count, only the direction")
    print(f"cosine(a, [-4, 3]) {cosine(a, np.array([-4.0, 3.0])):7.4f}   at right angles")
    print(f"cosine(a, -a)      {cosine(a, -a):7.4f}   opposite")
    u, v = a / np.linalg.norm(a), b / np.linalg.norm(b)
    print(f"at length 1 the dot product is the cosine: {float(u @ v):.4f}")
    CLAUSES = {
        "IT-SEC-04": ("USB mass-storage devices are blocked on all company laptops. No exception is "
                      "granted for contractors. Data transfer uses the approved cloud bucket only."),
        "EXP-12": ("Domestic travel is reimbursed against original receipts, capped at Rs 40,000 per trip. "
                   "Anything above the cap needs written approval from the function head before travel, "
                   "not after."),
        "PR-05": ("Salary is credited on the last working day of each month. Form 16 is issued by 15 June "
                  "for the preceding financial year."),
    }
    QUESTIONS = {"lk-05": "Are USB drives allowed on a company laptop?",
                 "reworded": "Can I copy files to a pen drive at work?"}
    def words(text):
        """The text's words: lower-case runs of letters and digits.
        
        Example: words(text)
        """
        return re.findall(r"[a-z0-9]+", text.lower())
    vocab = sorted({w for text in [*CLAUSES.values(), *QUESTIONS.values()] for w in words(text)})
    def counts(text):
        """A vector you can read: one dimension per word of the vocabulary, its value the word's count in the text.
        
        Example: counts(question)
        """
        return np.array([words(text).count(w) for w in vocab], dtype=float)
    print(f"\nword-count vectors: {len(vocab)} dimensions, one per distinct word")
    for q, question in QUESTIONS.items():
        print(f"{q:9}", "  ".join(f"{name} {cosine(counts(question), counts(clause)):.4f}" for name, clause in CLAUSES.items()),
              "  shared with IT-SEC-04:", sorted(set(words(question)) & set(words(CLAUSES["IT-SEC-04"]))))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_19', step_01_four_cosines_then_word_counts_against_mean),
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
