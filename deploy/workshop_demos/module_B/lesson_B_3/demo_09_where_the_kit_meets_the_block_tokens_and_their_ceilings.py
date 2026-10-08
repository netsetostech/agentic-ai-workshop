"""Lesson B.3: Where the kit meets the block: tokens and their ceilings

The cell copies those constants, the toy sentence's six tokens beside them, and puts each through the square, then fills one embedding request the way batches() does.

Run order inside this file:
1. Do it: the kit's numbers, squared, Rs 0 (source window 25)

Prerequisites: demo_08_the_block_assembled.
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


def step_01_the_kit_s_numbers_squared_rs_0(session):
    """Run Do it: the kit's numbers, squared, Rs 0 at this checkpoint.

    The cell copies those constants, the toy sentence's six tokens beside them, and puts each through the square, then fills one embedding request the way batches() does.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the same shell (plain Python, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: one sequence: its tokens, and the scores one head computes in one layer of a block like this page's
      the toy sentence                    6 tokens           36 scores
      one chunk of 2,000 characters     666 tokens      443,556 scores
      the API's prompt budget         8,000 tokens   64,000,000 scores
    one embedding request of full chunks: 22 texts, 14,652 estimated tokens
      each text its own sequence: 22 x 443,556 = 9,758,232 scores
      the same tokens as one sequence: 214,681,104 scores, 22 times as many
    """
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    
    CHUNK_CHARS = 2000                       # services/ingest/main.py: the longest chunk, in characters
    CHARS_PER_TOKEN = 3                      # services/ingest/indexer.py: the worker's token estimate
    EMBED_BATCH, EMBED_TOKENS = 250, 15_000  # indexer.py: the most texts, and estimated tokens, in one request
    MAX_CONTEXT_TOKENS = 8000                # services/rag-api/config.py: the prompt budget for one answer
    
    def pairs(n):                            # one head in one layer scores every token against every token
        """How many token pairs one attention head scores in one layer for n tokens: n times n.
        
        Example: pairs(chunk)
        """
        return n * n
    
    chunk = CHUNK_CHARS // CHARS_PER_TOKEN
    print("one sequence: its tokens, and the scores one head computes in one layer of a block like this page's")
    for name, n in (("the toy sentence", 6), ("one chunk of 2,000 characters", chunk), ("the API's prompt budget", MAX_CONTEXT_TOKENS)):
        print(f"  {name:31}{n:>6,} tokens{pairs(n):>13,} scores")
    texts, tokens = 0, 0                     # batches() in indexer.py: stop at 250 texts or 15,000 estimated tokens
    while texts < EMBED_BATCH and tokens + chunk <= EMBED_TOKENS:
        texts, tokens = texts + 1, tokens + chunk
    print(f"one embedding request of full chunks: {texts} texts, {tokens:,} estimated tokens")
    print(f"  each text its own sequence: {texts} x {pairs(chunk):,} = {texts * pairs(chunk):,} scores")
    print(f"  the same tokens as one sequence: {pairs(tokens):,} scores, {pairs(tokens) // (texts * pairs(chunk))} times as many")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_the_kit_s_numbers_squared_rs_0),
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
