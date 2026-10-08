"""Lesson 1.2: Count pages first: slices, and the 250-page line

The same count, on the PDFs in your kit folder, with the same library. The cell prints pages and slices per PDF, then the totals and what one parse of the whole corpus would cost at each processor's list price - the rates as the course reads them on the pricing page, to re-verify before quoting. The amendment Act is four pages and globex does not hold it, so ingesting it there is a fresh source, one Document AI request, and a few paise. Then read the worker's line for it, which carries the page count as pages.

Run order inside this file:
1. Do it: count the corpus, Rs 0 (source window 12)
2. Prove it on the lane: one small PDF, four pages (source window 14)

Prerequisites: demo_03_parse_document_ai_chosen_by_residency.
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


def step_01_count_the_corpus_rs_0(session):
    """Run Do it: count the corpus, Rs 0 at this checkpoint.

    The same count, on the PDFs in your kit folder, with the same library. The cell prints pages and slices per PDF, then the totals and what one parse of the whole corpus would cost at each processor's list price - the rates as the course reads them on the pricing page, to re-verify before quoting.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: acme/cgst_act_2017.pdf                           pages= 236 slices= 16 inline
    acme/code_on_social_security_2020.pdf            pages= 116 slices=  8 inline
    acme/code_on_wages_2019.pdf                      pages=  29 slices=  2 inline
    acme/maternity_benefit_amendment_act_2017.pdf    pages=   4 slices=  1 inline
    acme/posh_act_2013.pdf                           pages=  13 slices=  1 inline
    ...
    zeta/osh_code_2020.pdf                           pages=  86 slices=  6 inline

    1065 pages in 79 Document AI requests
    one full parse: OCR Rs 136   Layout Parser Rs 905
    """
    import glob, math, os
    from pypdf import PdfReader
    LIMIT, INLINE, USD_INR = 15, 250, 85
    OCR_USD, LAYOUT_USD = 1.50, 10.00            # per 1,000 pages, list price as read on the pricing page - re-verify
    total = calls = 0
    for path in sorted(glob.glob("evals/corpus/*/*.pdf")):
        n = len(PdfReader(path).pages)
        s = math.ceil(n / LIMIT)
        total += n; calls += s
        lane = "BATCH LANE" if n > INLINE else "inline"
        print(f"{path[13:]:48} pages={n:4} slices={s:3} {lane}")
    print(f"\n{total} pages in {calls} Document AI requests")
    print(f"one full parse: OCR Rs {total/1000*OCR_USD*USD_INR:,.0f}   Layout Parser Rs {total/1000*LAYOUT_USD*USD_INR:,.0f}")

# Original CLI workflow for step_02_prove_it_on_the_lane_one_small_pdf_four_pa.
COMMANDS_02 = """make ingest-one PROJECT=$PROJECT TENANT=globex FILE=evals/corpus/acme/maternity_benefit_amendment_act_2017.pdf

gcloud logging read 'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-ingest" AND jsonPayload.event="ingest_ok" AND jsonPayload.tenant="globex"' \\
  --project "$PROJECT" --limit 1 --format='value(jsonPayload.doc_key,jsonPayload.pages,jsonPayload.chunks,jsonPayload.embedded)'

"""

def step_02_prove_it_on_the_lane_one_small_pdf_four_pa(session):
    """Run Prove it on the lane: one small PDF, four pages at this checkpoint.

    The amendment Act is four pages and globex does not hold it, so ingesting it there is a fresh source, one Document AI request, and a few paise. Then read the worker's line for it, which carries the page count as pages.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (costs about four pages of Document AI).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: globex_e7a1c0...    4    5    5
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_count_the_corpus_rs_0),
        ('source_14', step_02_prove_it_on_the_lane_one_small_pdf_four_pa),
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
