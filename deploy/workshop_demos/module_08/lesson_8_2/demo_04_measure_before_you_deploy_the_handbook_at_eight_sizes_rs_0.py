"""Lesson 8.2: Measure before you deploy: the handbook at eight sizes, Rs 0

Do it: the handbook through the kit's chunker

Run order inside this file:
1. Do it: the handbook through the kit's chunker (source window 13)

Prerequisites: demo_03_the_kit_s_code_two_lines_one_rule_and_the_test_that_holds_them.
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


def step_01_the_handbook_through_the_kit_s_chunker(session):
    """Run Do it: the handbook through the kit's chunker at this checkpoint.

    Do it: the handbook through the kit's chunker

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; the kit's own chunker, Rs 0).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: pair      chunks reused embedded characters requests  rupees largest
    2000/200     283    283        0          0        0    0.00     599
    1000/100     283    283        0          0        0    0.00     599
     600/100     283    283        0          0        0    0.00     599
     599/50      283    283        0          0        0    0.00     599
     598/50      298    268       30       9735        1    0.02     593
     500/50      555     11      544     170348        4    0.36     443
     400/50      555     11      544     170348        4    0.36     368
     300/50      827     11      816     183948        5    0.39     285
    left whole at 400/50, so reused: preamble, NP-03, PB-02, LV-01, LV-07, EXP-12, 
    """
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from shared import documind_corpus as dc
    hb = open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()
    doc = {"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://x/acme/hr_policy_2026.md", "text": hb}
    def cut(size, overlap):
        """The handbook through the kit's chunker at one pair, set in memory: the files on disk stay as they are.
        
        Example: cut(2000, 200)
        """
        dc.CHUNK_CHARS, dc.CHUNK_OVERLAP = size, overlap
        return dc.chunk_document(doc, "acme")
    now = cut(2000, 200)                                  # what the lane holds: version 1, cut at the kit's pair
    held, whole = {c["chunk_hash"] for c in now}, {c["locator"]: len(c["text"]) for c in now}
    print("pair      chunks reused embedded characters requests  rupees largest")
    for size, overlap in [(2000, 200), (1000, 100), (600, 100), (599, 50), (598, 50), (500, 50), (400, 50), (300, 50)]:
        ch = cut(size, overlap)
        new = [c["text"] for c in ch if c["chunk_hash"] not in held]
        sent = sum(map(len, new))
        print(f"{size:>4}/{overlap:<4} {len(ch):>6} {len(ch) - len(new):>6} {len(new):>8} {sent:>10} {len(dc.embed_batches(new)):>8} "
              f"{sent / 1000 * 0.000025 * 85:>7.2f} {max(len(c['text']) for c in ch):>7}")
    c400 = cut(400, 50)
    kept = [c["locator"] for c in c400 if c["chunk_hash"] in held]
    longest = max(whole.values())
    print("left whole at 400/50, so reused:", ", ".join(kept))
    print(f"cut at 400/50: {len(whole) - len(kept)} sections of {min(v for k, v in whole.items() if k not in kept)} to {longest} "
          f"characters, into {len(c400) - len(kept)} windows")
    print(f"the longest section: {longest} characters ({sum(v == longest for v in whole.values())} of them), so no size from "
          f"{longest} up cuts anything")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_the_handbook_through_the_kit_s_chunker),
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
