"""Lesson 3.9: Architecture: the path a claim takes, station by station

The cell cuts the handbook with the kit's chunker, takes NP-03, the notice-period clause, and holds six quotes against it with quote_holds(): the sentence as written, a sentence that crosses a line break, the same sentence with revision 2's figure, a paraphrase, the whole clause, and the whole clause as _draft() trims an over-long quote. Each line prints both halves of the rule and the kit's verdict.

Run order inside this file:
1. Do it: the quote check on the handbook, offline (source window 15)

Prerequisites: setup_prepare.
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


def step_01_the_quote_check_on_the_handbook_offline(session):
    """Run Do it: the quote check on the handbook, offline at this checkpoint.

    The cell cuts the handbook with the kit's chunker, takes NP-03, the notice-period clause, and holds six quotes against it with quote_holds(): the sentence as written, a sentence that crosses a line break, the same sentence with revision 2's figure, a paraphrase, the whole clause, and the whole clause as _draft() trims an over-long quote. Each line prints both halves of the rule and the kit's verdict.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: NP-03: 212 characters, 38 words under its heading
    the sentence as written         15 words | in the passage True  | 25 words at most True  | quote_holds True
    across a line break             11 words | in the passage True  | 25 words at most True  | quote_holds True
    revision 2's figure             15 words | in the passage False | 25 words at most True  | quote_holds False
    a paraphrase                     9 words | in the passage False | 25 words at most True  | quote_holds False
    the whole clause                38 words | in the passage True  | 25 words at most False | quote_holds False
    the clause as _draft() trims it 36 words | in the passage False | 25 words at most False | quote_holds Fals
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = [".", "evals"]
    from shared import documind_corpus as dc
    from make_trainset import quote_holds          # the kit's rule: in the passage, line breaks as spaces, 25 words at most
    doc = {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://uploads/acme/hr_policy_2026.md",
           "text": open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()}
    passage = next(c for c in dc.chunk_document(doc, "acme") if c["locator"] == "NP-03")["text"]
    flat = lambda s: " ".join(s.split())
    clause = flat(passage.split("\n", 1)[1])                                     # NP-03 under its heading, on one line
    quotes = {"the sentence as written": "A confirmed employee at grade E3 or above serves a notice period of 60 days.",
              "across a line break": "Notice runs from the date the resignation is acknowledged in writing.",
              "revision 2's figure": "A confirmed employee at grade E3 or above serves a notice period of 90 days.",
              "a paraphrase": "Confirmed E3 employees must give 60 days of notice.",
              "the whole clause": clause,
              "the clause as _draft() trims it": clause[:197].rstrip() + "..."}
    print(f"NP-03: {len(clause)} characters, {len(clause.split())} words under its heading")
    for label, q in quotes.items():
        print(f"{label:31} {len(q.split()):2} words | in the passage {str(flat(q) in flat(passage)):5} | "
              f"25 words at most {str(len(q.split()) <= 25):5} | quote_holds {quote_holds(q, passage)}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_15', step_01_the_quote_check_on_the_handbook_offline),
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
