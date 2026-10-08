"""Lesson B.4: The masked-language idea: fill the blank from both sides

Do it: hide three words and ask the text for them, Rs 0

Run order inside this file:
1. Do it: hide three words and ask the text for them, Rs 0 (source window 5)

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


def step_01_hide_three_words_and_ask_the_text_for_them(session):
    """Run Do it: hide three words and ask the text for them, Rs 0 at this checkpoint.

    Do it: hide three words and ask the text for them, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in your venv (a Python cell; no network, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the text: 4 clauses, 11 sentences, 128 words

    NP-03, sentence 1: a confirmed employee at grade e3 or above serves a [MASK] period of 60 days
      left only   (a _): confirmed 1, maximum 1  -> a tie: confirmed, maximum; the hidden word is not among them
      both sides  (a _ period): notice 2, confirmed 1, maximum 1  -> notice, the hidden word

    PB-02, sentence 2: during probation the notice period is [MASK] days for either side
      left only   (is _): acknowledged 1, encashed 1  -> a tie: acknowledged, encashed; the hidden word is not among them
      both sides  (is _ days): acknowledged 1, encashed 1, 60 1, 1.75 1, 30 1, 45 1  -> a tie: acknowledged, encashed, 60, 1.75, 30, 45; the hidden word is not a
    """
    import re, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from collections import Counter
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
    def sentences(text):
        """Split a text into sentences at full stops, semicolons, question marks and exclamation marks.
        
        Example: sentences(t)
        """
        return [s for s in re.sub(r"([.;?!])\s+", r"\1\n", text).split("\n") if s]
    def words(sentence):
        """Lower-case a sentence and return its words and numbers, decimals kept whole.
        
        Example: words(s)
        """
        return re.findall(r"[a-z0-9]+(?:\.[0-9]+)?", sentence.lower())
    def fill(clause, n, hidden):
        """Hide one word of a clause's sentence and count which words the rest of the text puts in that gap.
        
        Example: fill(clause, n, hidden)
        """
        text = {(c, k): words(s) for c, t in CLAUSES.items() for k, s in enumerate(sentences(t), 1)}
        toks = text[(clause, n)]
        j = toks.index(hidden)
        toks[j] = "[mask]"                     # the training text has a blank here, so the hidden word itself is never counted
        left, right = toks[j - 1], toks[j + 1]
        after_left = Counter(t[k + 1] for t in text.values() for k in range(len(t) - 1) if t[k] == left and t[k + 1] != "[mask]")
        before_right = Counter(t[k] for t in text.values() for k in range(len(t) - 1) if t[k + 1] == right and t[k] != "[mask]")
        return " ".join(toks).replace("[mask]", "[MASK]"), left, right, after_left, after_left + before_right
    def verdict(counts, hidden):
        """Name the candidate the counts favour, a tie, or that nothing in the text fits.
        
        Example: verdict(one, hidden)
        """
        if not counts:
            return "nothing in the text fits"
        top = [w for w, n in counts.items() if n == max(counts.values())]
        if len(top) > 1:
            return "a tie: " + ", ".join(top) + ("" if hidden in top else "; the hidden word is not among them")
        return top[0] + (", the hidden word" if top[0] == hidden else ", not the hidden word")
    n_sentences = sum(len(sentences(t)) for t in CLAUSES.values())
    n_words = sum(len(words(s)) for t in CLAUSES.values() for s in sentences(t))
    print(f"the text: {len(CLAUSES)} clauses, {n_sentences} sentences, {n_words} words")
    for clause, n, hidden in (("NP-03", 1, "notice"), ("PB-02", 2, "15"), ("NP-03", 3, "leave")):
        shown, left, right, one, both = fill(clause, n, hidden)
        print(f"\n{clause}, sentence {n}: {shown}")
        print(f"  left only   ({left} _): " + ", ".join(f"{w} {c}" for w, c in one.most_common()) + f"  -> {verdict(one, hidden)}")
        print(f"  both sides  ({left} _ {right}): " + ", ".join(f"{w} {c}" for w, c in both.most_common()) + f"  -> {verdict(both, hidden)}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_5', step_01_hide_three_words_and_ask_the_text_for_them),
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
