"""Lesson 1.3: Batches: 250 texts and 15,000 tokens per request

The loader's copy of the rule, on the chunks you cut in lesson 1.2. No call is made; a plan is printed.

Run order inside this file:
1. Do it: plan the handbook, Rs 0 (source window 18)

Prerequisites: demo_04_the_call_768_numbers_under_the_document_task_type.
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


def step_01_plan_the_handbook_rs_0(session):
    """Run Do it: plan the handbook, Rs 0 at this checkpoint.

    The loader's copy of the rule, on the chunks you cut in lesson 1.2. No call is made; a plan is printed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: handbook: 283 chunks, 158,692 chars -> 4 requests of [85, 78, 78, 42] texts, est tokens [14833, 14949, 14944, 8057]
    wages mirror: 65 chunks, 102,444 chars -> 3 requests of [28, 28, 9] texts, est tokens [...]
    the handbook in one request would carry about 52,783 estimated tokens: over 20,000, refused whole
    """
    import sys
    sys.path.insert(0, ".")
    from shared import documind_corpus as dc
    def cut(path, slug):
        """Parse and chunk the supplied handbook input with the kit parser; retain its real section identities.
        
        Example: cut('evals/corpus/acme/hr_policy_2026.md', 'hr_policy_2026')
        """
        text = open(path, encoding="utf-8").read()
        return [c["text"] for c in dc.chunk_document({"slug": slug, "doc_type": "x", "source_uri": "gs://x", "text": text}, "acme")]
    for name, texts in (("handbook", cut("evals/corpus/acme/hr_policy_2026.md", "hr_policy_2026")),
                        ("wages mirror", cut("evals/corpus/acme/code_on_wages_2019.md", "code_on_wages_2019"))):
        plan = dc.embed_batches(texts)
        est = [sum(max(1, len(t) // dc.CHARS_PER_TOKEN) for t in b) for b in plan]
        print(f"{name}: {len(texts)} chunks, {sum(map(len, texts)):,} chars -> {len(plan)} requests of {[len(b) for b in plan]} texts, est tokens {est}")
    one = sum(max(1, len(t) // 3) for t in cut("evals/corpus/acme/hr_policy_2026.md", "hr_policy_2026"))
    print(f"the handbook in one request would carry about {one:,} estimated tokens: over 20,000, refused whole")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_plan_the_handbook_rs_0),
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
