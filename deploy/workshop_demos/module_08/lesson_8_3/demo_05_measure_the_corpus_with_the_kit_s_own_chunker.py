"""Lesson 8.3: Measure the corpus with the kit's own chunker

The averages the arithmetic multiplies, from the kit's code on the kit's files, in a second, with no network. The cell below loads every text document of the three tenants with shared/documind_corpus.py, the loader, chunker and batcher the notebooks share. They apply the worker's two rules, 2,000 characters with 200 of overlap and a section per ## heading, and the worker's two ceilings on a request. It counts, by document type, the characters, the chunks, the characters sent and the requests, then multiplies by 10,000,000. It reads only files in your clone of the kit: nothing on the lane, nothing billed.

Run order inside this file:
1. Measure the corpus with the kit's own chunker (source window 22)

Prerequisites: demo_03_the_ui_your_corpus_counted_by_the_lane.
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


def step_01_measure_the_corpus_with_the_kit_s_own_chun(session):
    """Run Measure the corpus with the kit's own chunker at this checkpoint.

    The averages the arithmetic multiplies, from the kit's code on the kit's files, in a second, with no network. The cell below loads every text document of the three tenants with shared/documind_corpus.py, the loader, chunker and batcher the notebooks share. They apply the worker's two rules, 2,000 characters with 200 of overlap and a section per ## heading, and the worker's two ceilings on a request. It counts, by document type, the characters, the chunks, the characters sent and the requests, then multiplies by 10,000,000. It reads only files in your clone of the kit: nothing on the lane, nothing billed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (no network: the kit's own code on the kit's own files).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: doc_type   docs characters chunks       sent requests
    contract      3      2,787     18      2,697        3
    guidance      2    100,480    100    104,126        4
    invoice       1        780      1        780        1
    policy        2    320,769    566    317,383        8
    report        1        707      4        689        1
    statute      17  2,837,331  2,067  3,044,540       77
    transcript    1      1,698      1      1,698        1
    all          27  3,264,552  2,757  3,471,913       95

    per document: 102.11 chunks, 128,589 characters sent, 3.52 requests
    at 10,000,000 documents of this mix:
      vectors              1,021,111,111
      embedding requests   35,185,185
      dense index          2,921.4 GiB (7
    """
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from shared import documind_corpus as dc     # the loader, the chunker and the batcher: the worker's rules (step 4)
    from shared.prices import USD_INR             # the course's rate, Rs 85 to the dollar
    N, DIMS, GIB = 10_000_000, 768, 1 << 30     # the target; indexer.py's EMBEDDING_DIMENSIONS; a gibibyte
    USD_PER_1K = 0.000025                 # text-embedding-005 input, online, per 1,000 characters (step 8)
    rows = []
    for tenant in ("acme", "globex", "zeta"):
        for d in dc.load_documents(tenant, "evals", "documind-ai-YOUR-ID"):
            texts = [c["text"] for c in dc.chunk_document(d, tenant)]
            rows.append((d["doc_type"], len(d["text"]), len(texts), sum(map(len, texts)), len(dc.embed_batches(texts))))
    
    
    def line(name, group):
        """Print one row of the measuring table: a group's documents, characters, chunks, characters sent and requests.
        
        Example: line('all', rows)
        """
        print(f"{name:10} {len(group):>4} {sum(r[1] for r in group):>10,} {sum(r[2] for r in group):>6,} "
              f"{sum(r[3] for r in group):>10,} {sum(r[4] for r in group):>8,}")
    
    
    print(f"{'doc_type':10} {'docs':>4} {'characters':>10} {'chunks':>6} {'sent':>10} {'requests':>8}")
    for t in sorted({r[0] for r in rows}):
        line(t, [r for r in rows if r[0] == t])
    line("all", rows)
    docs, chunks, sent, requests = len(rows), *(sum(r[i] for r in rows) for i in (2, 3, 4))
    k = N / docs
    print(f"\nper document: {chunks / docs:.2f} chunks, {sent / docs:,.0f} characters sent, {requests / docs:.2f} requests")
    print(f"at {N:,} documents of this mix:")
    print(f"  vectors              {chunks * k:,.0f}")
    print(f"  embedding requests   {requests * k:,.0f}")
    print(f"  dense index          {chunks * k * DIMS * 4 / GIB:,.1f} GiB ({DIMS} numbers x 4 bytes a vector)")
    print(f"  embedding, once      Rs {sent * k / 1000 * USD_PER_1K * USD_INR / 1e5:,.2f} lakh")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_measure_the_corpus_with_the_kit_s_own_chun),
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
