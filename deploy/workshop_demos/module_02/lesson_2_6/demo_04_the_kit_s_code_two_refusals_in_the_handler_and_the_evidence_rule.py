"""Lesson 2.6: The kit's code: two refusals in the handler, and the evidence rule

Do it: the rule's arithmetic on three rows

Run order inside this file:
1. Do it: the rule's arithmetic on three rows (source window 16)

Prerequisites: demo_03_a_refusal_in_the_ui_and_what_it_paid_for.
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


def step_01_the_rule_s_arithmetic_on_three_rows(session):
    """Run Do it: the rule's arithmetic on three rows at this checkpoint.

    Do it: the rule's arithmetic on three rows

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: nothing leaves the machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: rf-01 (acme, refusal, answerable False): What is ACME's sabbatical policy?
       sabbatical     idf  8.09   not in the pool
       policy         idf  4.20   in the pool
       acme           idf  1.77   not in the pool
       share 0.30 against EVIDENCE_FLOOR 0.5: the rule says refuse
    rf-02 (acme, refusal, answerable False): How many casual leave days do I get?
       casual         idf  3.98   in the pool
       leave          idf  3.49   in the pool
       days           idf  1.19   in the pool
       share 1.00 against EVIDENCE_FLOOR 0.5: the rule says answer
    lk-01 (acme, lookup, answerable True): What is the per-trip cap on domestic travel reimbursement?
       trip           idf  6.99   in the pool
       domestic       idf
    """
    import json, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, ".")
    from shared import documind_tools as dt, local_corpus
    
    GOLDEN = {r["id"]: r for r in (json.loads(line) for line in open("evals/golden.jsonl", encoding="utf-8") if line.strip())}
    
    
    def explain(rid, top_k=5):
        """The evidence rule on one golden row, Rs 0: each content word's idf over the tenant's chunks, whether the
        top-k pool holds it, and the share against EVIDENCE_FLOOR, as the local lane's gate computes it.
        
        Example: explain(rid)
        """
        row = GOLDEN[rid]
        ranked, idf = dt._lexical_rank(row["question"], [(c["text"], {}) for c in local_corpus.chunks_for(row["tenant"])])
        covered = {w for _, hit, _, _ in ranked[:top_k] for w in hit}
        share = sum(idf[w] for w in covered) / sum(idf.values()) if idf else 0.0
        print(f"{rid} ({row['tenant']}, {row['shape']}, answerable {row['answerable']}): {row['question']}")
        for w, v in sorted(idf.items(), key=lambda kv: -kv[1]):
            print(f"   {w:<14} idf {v:5.2f}   {'in the pool' if w in covered else 'not in the pool'}")
        common = [w for w in dt._words(row["question"]) if w not in idf]
        if common:
            print(f"   {', '.join(common)}: in more than half of the tenant's chunks, so not evidence")
        verdict = "answer" if ranked and share >= dt.EVIDENCE_FLOOR else "refuse"
        print(f"   share {share:.2f} against EVIDENCE_FLOOR {dt.EVIDENCE_FLOOR}: the rule says {verdict}")
    
    
    for rid in ("rf-01", "rf-02", "lk-01"):
        explain(rid)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_16', step_01_the_rule_s_arithmetic_on_three_rows),
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
