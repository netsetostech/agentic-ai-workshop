"""Lesson B.2: A tokenizer you can read: byte-pair merges on two handbook clauses

Do it: learn the merges, then cut five texts

Run order inside this file:
1. Do it: learn the merges, then cut five texts (source window 5)

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


def step_01_learn_the_merges_then_cut_five_texts(session):
    """Run Do it: learn the merges, then cut five texts at this checkpoint.

    Do it: learn the merges, then cut five texts

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in ~/basics-venv (a Python cell; Rs 0, nothing leaves the machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: training text: 407 characters, 39 distinct; 65 merges learned
    the first ten: ['on', 'ti', 'th', 'er', 'ed', ' a', ' s', 'no', 'ce', ' p']
    the last five: [' months', ' on', ' probation', 'ith', 'ten']
    'What is the notice period for a confirmed E3?'   45 characters -> 23 pieces ['W', 'h', 'a', 't', ' is', ' the', ' notice', ' period', ' f', 'o', 'r', ' a', ' ', 'c', 'on', 'f', 'i', 'r', 'm', 'ed', ' E', '3', '?']
    ' notice'                                          7 characters ->  1 piece  [' notice']
    'notice'                                           6 characters ->  2 pieces ['no', 'tice']
    'Notice'                                           6 characters ->  3 pieces ['N', 'o', 'tice']
    'Bengalu
    """
    import re
    from collections import Counter
    # the whole training text: two clauses of the kit's handbook, NP-03 and PB-02
    TRAIN = ("A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs "
             "from the date the resignation is acknowledged in writing. Unused earned leave may not be set "
             "off against the notice period. New joiners serve six months on probation at grade E2. During "
             "probation the notice period is 15 days for either side. Probation may be extended once, by "
             "up to three months, with written reasons.")
    def words(text):
        """Cut a text into words: a word keeps the space before it, and a digit or a mark stands alone.
        
        Example: words(text)
        """
        return re.findall(r" ?[A-Za-z]+| ?[0-9]| ?[^\sA-Za-z0-9]", text)
    def merge(word, a, b):
        """Join every a followed by b inside one word into the single piece a+b.
        
        Example: merge(w, a, b)
        """
        out, i = [], 0
        while i < len(word):
            if i + 1 < len(word) and (word[i], word[i + 1]) == (a, b):
                out.append(a + b)
                i += 2
            else:
                out.append(word[i])
                i += 1
        return tuple(out)
    counts = Counter(tuple(w) for w in words(TRAIN))   # each word as single characters, and how often it occurs
    merges = []
    while True:                         # learn: merge the commonest neighbouring pair, until no pair occurs twice
        pairs = Counter()
        for w, n in counts.items():
            for pair in zip(w, w[1:]):
                pairs[pair] += n
        (a, b), seen = pairs.most_common(1)[0]
        if seen < 2:
            break
        merges.append((a, b))
        counts = Counter({merge(w, a, b): n for w, n in counts.items()})
    def encode(text):
        """Tokenize: cut the text into words, then apply every merge in the order it was learned.
        
        Example: encode(text)
        """
        out = []
        for w in words(text):
            w = tuple(w)
            for a, b in merges:
                w = merge(w, a, b)
            out += w
        return out
    print(f"training text: {len(TRAIN)} characters, {len(set(TRAIN))} distinct; {len(merges)} merges learned")
    print("the first ten:", [a + b for a, b in merges[:10]])
    print("the last five:", [a + b for a, b in merges[-5:]])
    for text in ("What is the notice period for a confirmed E3?", " notice", "notice", "Notice", "Bengaluru"):
        pieces = encode(text)
        print(f"{text!r:49} {len(text):2} characters -> {len(pieces):2} piece{'s' if len(pieces) > 1 else ' '} {pieces}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_5', step_01_learn_the_merges_then_cut_five_texts),
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
