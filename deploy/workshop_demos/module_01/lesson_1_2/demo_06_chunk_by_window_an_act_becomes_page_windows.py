"""Lesson 1.2: Chunk by window: an Act becomes page windows

Your kit has a text mirror of every Act, made by pypdf when the corpus was fetched, with a form feed between pages. Cut the mirror of the Code on Wages and look at one seam. Read it on the lane, and ask a question that lands on a page

Run order inside this file:
1. Do it: cut the Code on Wages, Rs 0 (source window 22)
2. Read it on the lane, and ask a question that lands on a page (source window 24)
3. Read it on the lane, and ask a question that lands on a page (source window 25)

Prerequisites: demo_05_chunk_by_section_the_handbook_becomes_283_clauses.
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


def step_01_cut_the_code_on_wages_rs_0(session):
    """Run Do it: cut the Code on Wages, Rs 0 at this checkpoint.

    Your kit has a text mirror of every Act, made by pypdf when the corpus was fetched, with a form feed between pages. Cut the mirror of the Code on Wages and look at one seam.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: pages in the mirror: 29
    65 windows; the first six locators: ['p1-0', 'p2-0', 'p2-1', 'p3-0', 'p3-1', 'p4-0']
    p2-0 is 2000 chars; p2-1 is 1201 chars
    end of p2-0 -> 'th or without the knowledge of the\\nprincipal employer and includ'
    start of p2-1 -> 'in or\\nin connection with the work of an establishment when he'
    the overlap: the last 200 characters of p2-0 reappear at the start of p2-1 -> True
    """
    import sys
    sys.path.insert(0, ".")
    from shared import documind_corpus as dc
    text = open("evals/corpus/acme/code_on_wages_2019.md", encoding="utf-8").read()
    print("pages in the mirror:", text.count("\f") + 1)
    chunks = dc.chunk_document({"slug": "code_on_wages_2019", "doc_type": "act", "source_uri": "gs://x", "text": text}, "acme")
    print(len(chunks), "windows; the first six locators:", [c["locator"] for c in chunks[:6]])
    a, b = chunks[1], chunks[2]                      # p2-0 and p2-1: two windows on the same page
    print(f"{a['locator']} is {len(a['text'])} chars; {b['locator']} is {len(b['text'])} chars")
    print("end of", a["locator"], "->", repr(a["text"][-60:]))
    print("start of", b["locator"], "->", repr(b["text"][:60]))
    print("the overlap: the last 200 characters of", a["locator"], "reappear at the start of", b["locator"], "->", a["text"][-200:] == b["text"][:200])

def step_02_on_the_lane_and_ask_a_question_that_lands(session):
    """Run Read it on the lane, and ask a question that lands on a page at this checkpoint.

    Read it on the lane, and ask a question that lands on a page

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    import os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    PROJECT = os.environ["PROJECT"]
    db = firestore.Client(project=PROJECT)
    q = (db.collection("chunks").where("tenant_id", "==", "acme")
         .where("source_uri", "==", f"gs://{PROJECT}-uploads/acme/code_on_wages_2019.pdf")
         .where("current", "==", True))
    rows = sorted(q.stream(), key=lambda c: int(c.id.rsplit("#", 1)[1]))
    print(len(rows), "windows on the lane; first six:", [c.to_dict().get("locator") for c in rows[:6]])
    print("pages seen:", sorted({c.to_dict().get("page_start") for c in rows})[:5], "...", max(c.to_dict().get("page_start") for c in rows))

# Original CLI workflow for step_03_on_the_lane_and_ask_a_question_that_lands.
COMMANDS_03 = """curl -s -X POST $API/v1/query -H "Authorization: Bearer $(tok $API)" -H "Content-Type: application/json" \\
  -d '{"query":"Within how many days must wages be paid after the wage period ends under the Code on Wages?","tenant_id":"acme","stream":false}' \\
  | python -c "import json,sys; j=json.load(sys.stdin); print(j['answer'][:160]); [print(c['chunk_id'].split('#')[1], c['source_uri'].split('/')[-1], 'page', c['page'], '|', c['quote'][:60]) for c in j['citations']]"

"""

def step_03_on_the_lane_and_ask_a_question_that_lands(session):
    """Run Read it on the lane, and ask a question that lands on a page at this checkpoint.

    Read it on the lane, and ask a question that lands on a page

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (acme pinned to vector, see the setup).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 67 windows on the lane; first six: ['p1-0', 'p2-0', 'p2-1', 'p3-0', 'p3-1', 'p4-0']
    pages seen: [1, 2, 3, 4, 5] ... 29
    Under the Code on Wages, wages must be paid within seven days after the end of the wage period ... [Source 1]
    19 code_on_wages_2019.pdf page 9 | (iv) monthly basis, before the expiry of the seventh day of the succ
    20 code_on_wages_2019.pdf page 9 | ...
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_cut_the_code_on_wages_rs_0),
        ('source_24', step_02_on_the_lane_and_ask_a_question_that_lands),
        ('source_25', step_03_on_the_lane_and_ask_a_question_that_lands),
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
