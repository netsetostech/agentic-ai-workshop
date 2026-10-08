"""Lesson B.2: The kit's two estimates against plain character counts

Do it: four texts, five counts each

Run order inside this file:
1. Do it: four texts, five counts each (source window 9)

Prerequisites: demo_03_a_tokenizer_you_can_read_byte_pair_merges_on_two_handbook_clauses.
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


def step_01_four_texts_five_counts_each(session):
    """Run Do it: four texts, five counts each at this checkpoint.

    Do it: four texts, five counts each

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop, in ~/basics-venv (a Python cell; Rs 0, nothing leaves the machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: characters  bytes  words  len // 4  len // 3
    the question (golden row lk-06)          45     45      9        11        15
    the same question in Hindi               48    120     10        12        16
    an Indian amount (FIN-02)                62     62     11        15        20
    a whole clause (NP-03)                  212    212     38        53        70
    """
    TEXTS = {
        "the question (golden row lk-06)": "What is the notice period for a confirmed E3?",
        "the same question in Hindi": "पुष्टि किए गए E3 कर्मचारी की सूचना अवधि क्या है?",
        "an Indian amount (FIN-02)": "Purchases up to Rs 2,00,000 are approved by the function head.",
        "a whole clause (NP-03)": ("A confirmed employee at grade E3 or above serves a notice period of 60 "
                                   "days. Notice runs from the date the resignation is acknowledged in "
                                   "writing. Unused earned leave may not be set off against the notice "
                                   "period."),
    }
    def api_estimate(text):
        """services/rag-api/context_budget.py, estimate_tokens(): four characters a token.
        
        Example: api_estimate(text)
        """
        return max(1, len(text) // 4)
    def worker_estimate(text):
        """services/ingest/indexer.py, batches(): CHARS_PER_TOKEN = 3.
        
        Example: worker_estimate(text)
        """
        return max(1, len(text) // 3)
    print(f"{'':32} {'characters':>10} {'bytes':>6} {'words':>6} {'len // 4':>9} {'len // 3':>9}")
    for name, text in TEXTS.items():
        print(f"{name:32} {len(text):10} {len(text.encode('utf-8')):6} {len(text.split()):6} {api_estimate(text):9} {worker_estimate(text):9}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_four_texts_five_counts_each),
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
