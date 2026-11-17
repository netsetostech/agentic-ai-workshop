"""Lesson 8.4: Cost: standing still, staying fresh, and one change, at 1k, 100k and 10M documents

This is component 6's COST-MODEL.md as something a reviewer can rerun. It measures the kit's corpus with the kit's own chunker, carries lesson 8.3's prices as dated constants, and uses the edit's counts from this page: its characters, its datapoints, and the Firestore writes and reads the kit's functions made.

Run order inside this file:
1. Do it: the cost model as a script (source window 46)

Prerequisites: demo_06_failure_modes_what_pages_what_does_not_and_what_the_design_does_about_it.
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


def step_01_the_cost_model_as_a_script(session):
    """Run Do it: the cost model as a script at this checkpoint.

    This is component 6's COST-MODEL.md as something a reviewer can rerun. It measures the kit's corpus with the kit's own chunker, carries lesson 8.3's prices as dated constants, and uses the edit's counts from this page: its characters, its datapoints, and the Firestore writes and reads the kit's functions made.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the kit's corpus: 27 documents, 102.11 chunks and 128,589 characters each; one edit like the handbook's Rs 0.14 before the fingerprint
         1,000 documents: Rs 7,488 a month standing, Rs 273 to embed once, Rs 0.17 an edit; 43,769 edits a month cost as much as standing still
       100,000 documents: Rs 1.25 lakh a month standing, Rs 27,325 to embed once, Rs 3.12 an edit; 40,150 edits a month cost as much as standing still
    10,000,000 documents: Rs 94.18 lakh a month standing, Rs 27.33 lakh to embed once, Rs 297.64 an edit; 31,643 edits a month cost as much as standing still
    """
    import sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path[:0] = ["."]
    from shared import documind_corpus as dc
    from shared.prices import USD_INR
    # Google's prices the kit does not hold: lesson 8.3's, read on 12 October 2026 (Mumbai for Vector Search and Firestore) - verify them
    EMBED_1K, STREAM_GIB, BUILD_GIB = 0.000025, 0.45, 3.00                 # per 1,000 characters; per GiB in; per GiB rebuilt
    READ, WRITE, STORE = 3.5000000000000004e-07, 1.04e-06, 0.104                  # Firestore: per read, per write, per GiB a month
    NODE = {"SMALL": (2, 0.1126804), "MEDIUM": (20, 0.9014432), "LARGE": (50, 1.2160288)}                                    # a serving node an hour, by shard size (GiB a shard, USD)
    CHUNK_BYTES = 59091.64961915125                    # Firestore bytes a chunk with its eight vector-index entries (8.3's floor)
    docs = chunks = 0
    chars = 0
    for t in ("acme", "globex", "zeta"):
        for d in dc.load_documents(t, "evals", "documind-ai-YOUR-ID"):
            cs = dc.chunk_document(d, t)
            docs, chunks, chars = docs + 1, chunks + len(cs), chars + sum(len(c["text"]) for c in cs)
    per_doc, chars_doc = chunks / docs, chars / docs
    EDIT = {"chars": 453, "datapoints": 283, "writes": 855, "reads": 1137}   # the handbook's edit, counted on this page
    edit = (EDIT["chars"] / 1000 * EMBED_1K + EDIT["datapoints"] * 768 * 4 / 2**30 * STREAM_GIB
            + EDIT["writes"] * WRITE + EDIT["reads"] * READ)
    print(f"the kit's corpus: {docs} documents, {per_doc:.2f} chunks and {chars_doc:,.0f} characters each; one edit like the handbook's "
          f"Rs {edit * USD_INR:.2f} before the fingerprint")
    
    
    def month(n):
        """Standing still and staying fresh for n documents: serving on the cheapest shard size, six compactions, storage.
        
        Example: month(n)
        """
        rows = n * per_doc
        gib = rows * 768 * 4 / 2**30
        serve = min(1 * max(1, -(-gib // size)) * usd * 730 for size, usd in NODE.values())
        return serve + gib * BUILD_GIB * 6 + rows * CHUNK_BYTES / 2**30 * STORE, n * chars_doc / 1000 * EMBED_1K
    
    
    def rupees(x):
        """Rupees as the page's tables write them: crore and lakh above a lakh, whole rupees grouped the Indian way below.
        
        Example: rupees(standing * USD_INR)
        """
        if x >= 1e7:
            return f"Rs {x / 1e7:,.2f} crore"
        if x >= 1e5:
            return f"Rs {x / 1e5:,.2f} lakh"
        s = str(int(x + 0.5))
        head, tail = s[:-3], s[-3:]
        while len(head) > 2:
            head, tail = head[:-2], head[-2:] + "," + tail
        return f"Rs {head},{tail}" if head else f"Rs {tail}"
    
    
    for n in (1_000, 100_000, 10_000_000):
        standing, embed = month(n)
        each = edit + n * READ                          # every change re-reads the tenant's n ledger rows (the fingerprint)
        print(f"{n:>10,} documents: {rupees(standing * USD_INR)} a month standing, {rupees(embed * USD_INR)} to embed once, "
              f"Rs {each * USD_INR:,.2f} an edit; {standing / each:,.0f} edits a month cost as much as standing still")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_46', step_01_the_cost_model_as_a_script),
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
