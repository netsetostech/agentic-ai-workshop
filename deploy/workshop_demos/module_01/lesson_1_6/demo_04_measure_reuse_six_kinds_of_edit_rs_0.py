"""Lesson 1.6: Measure reuse: six kinds of edit, Rs 0

Do it: the six edits through the worker's planner

Run order inside this file:
1. Do it: the six edits through the worker's planner (source window 13)

Prerequisites: demo_03_the_gate_the_golden_set_scoped_to_one_document.
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


def step_01_the_six_edits_through_the_worker_s_planner(session):
    """Run Do it: the six edits through the worker's planner at this checkpoint.

    Do it: the six edits through the worker's planner

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: a figure in NP-03 (60 to 90)         chunks 283 -> 283  reused 282  embedded  1    234 chars  ['NP-03']
    a figure in PB-02 (15 to 20)         chunks 283 -> 283  reused 282  embedded  1    212 chars  ['PB-02']
    NP-03 re-wrapped (whitespace only)   chunks 283 -> 283  reused 283  embedded  0      0 chars  []
    NP-03's heading renamed              chunks 283 -> 283  reused 282  embedded  1    250 chars  ['NP-03']
    a clause inserted before PB-02       chunks 283 -> 284  reused 283  embedded  1     84 chars  ['NP-04']
    NP-03 and PB-02 swapped              chunks 283 -> 283  reused 283  embedded  0      0 chars  []
    wages: a sentence added on page 2    chunks  65 ->  65  reused  63  embedded  2   3261 cha
    """
    import os, re, sys
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", os.environ["PROJECT"])
    sys.path[:0] = [".", "services/ingest"]
    from shared import documind_corpus as dc
    from indexer import plan_carry_over
    def cut(text, slug="hr_policy_2026"):
        """Parse and chunk the supplied handbook input with the kit parser; retain its real section identities.
        
        Example: cut(old, slug)
        """
        return dc.chunk_document({"slug": slug, "doc_type": "policy", "source_uri": "gs://x", "text": text}, "acme")
    def measure(name, old, new, slug="hr_policy_2026"):
        """Compare old/new chunks through the kit reuse planner and print the changed-versus-reused counts.
        
        Example: measure('a figure in NP-03 (60 to 90)', v1, v1.replace('serves a notice period of 60 days', 'serves a notice period of 90 days', 1))
        """
        a, b = cut(old, slug), cut(new, slug)
        held = {c["chunk_hash"]: ["held"] for c in a}                     # what held_vectors() would lend
        vectors, misses = plan_carry_over(b, held)
        chars = sum(len(b[i]["text"]) for i in misses)
        print(f"{name:36} chunks {len(a):>3} -> {len(b):>3}  reused {len(b) - len(misses):>3}  embedded {len(misses):>2}  {chars:>5} chars  {[b[i]['locator'] for i in misses]}")
    v1 = open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()
    measure("a figure in NP-03 (60 to 90)", v1, v1.replace("serves a notice period of 60 days", "serves a notice period of 90 days", 1))
    measure("a figure in PB-02 (15 to 20)", v1, v1.replace("period is 15 days for either side", "period is 20 days for either side", 1))
    measure("NP-03 re-wrapped (whitespace only)", v1, v1.replace("A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs", "A confirmed employee at grade E3 or above\nserves a notice period of 60 days. Notice runs", 1))
    measure("NP-03's heading renamed", v1, v1.replace("## NP-03 — Notice period", "## NP-03 — Notice period and pay in lieu", 1))
    measure("a clause inserted before PB-02", v1, v1.replace("## PB-02 — Probation", "## NP-04 — Garden leave\n\nGarden leave may be directed for the notice period at full pay.\n\n## PB-02 — Probation", 1))
    m = re.search(r"(## NP-03 — Notice period\n.*?\n\n)(## PB-02 — Probation\n.*?\n\n)", v1, re.S)
    measure("NP-03 and PB-02 swapped", v1, v1.replace(m.group(0), m.group(2) + m.group(1), 1))
    wg = open("evals/corpus/acme/code_on_wages_2019.md", encoding="utf-8").read()
    pages = wg.split("\f"); pages[1] = "A new opening sentence was inserted at the top of this page. " + pages[1]
    measure("wages: a sentence added on page 2", wg, "\f".join(pages), "code_on_wages_2019")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_13', step_01_the_six_edits_through_the_worker_s_planner),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
