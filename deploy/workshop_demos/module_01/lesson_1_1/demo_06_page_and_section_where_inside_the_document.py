"""Lesson 1.1 / HTML section 6: Page and section: where inside the document

Ask the Markdown and PDF questions, resolve every citation to its current row,
then inspect section/page locators. The two questions incur retrieval/generation work.
Expected: citations refer to the intended seeded sources and agree with stored page fields.

Example: open this file at the matching HTML heading and choose Run/Debug
with rag-shell-venv. Complete the preceding required files in README.md.
Set breakpoints in the named functions below; demonstrate() shows their order.
After this lesson, run setup/finish.py even if a live observation failed.
"""
from collections import Counter
from workshop_helpers.lesson31 import LessonCloud, require, contract_step
from workshop_helpers.steps import run_steps
from workshop_helpers.session import DemoSession
REPEAT = False
# Inspect the failed attempt before explicitly retrying an unfinished function.
RETRY_FAILED_STEP = False
QUESTIONS = [
    ("markdown", "What is the notice period for a confirmed E3?", "hr_policy_2026.md"),
    ("pdf", "What does the Code on Wages say about the payment of wages?", "code_on_wages_2019.pdf"),
]


def inspect_citations(cloud):
    """HTML 6: ask both source questions and resolve each citation back to Firestore.
    
    Example: inspect_citations(cloud) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    for label, question, expected_source in QUESTIONS:
        answer = cloud.query(label + "_answer", question)
        require(answer.get("answerable") and answer.get("citations"), f"{label}: no cited answer; inspect the saved response and seeded corpus.")
        require(any(c["source_uri"].endswith("/" + expected_source) for c in answer["citations"]),
                f"{label}: the expected lesson source was not cited. This live observation did not reproduce the example.")
        print(question, "\n", answer["answer"])
        for citation in answer["citations"]:
            row = cloud.document("chunks/" + citation["chunk_id"])
            require(row.get("tenant_id") == "acme" and row.get("current") is True
                    and row.get("source_uri") == citation["source_uri"], "Citation did not resolve to its current ACME chunk.")
            require(citation.get("page") == (row.get("page_start") or row.get("page")), "Citation page disagrees with the stored chunk.")
            print("  cited:", citation["chunk_id"], "page", citation.get("page"), "locator", row.get("locator"))


def inspect_locators(cloud):
    """HTML 6: section labels locate Markdown passages; page numbers locate PDF passages.
    
    Example: inspect_locators(cloud) runs after the preceding function in demonstrate().
    Failures propagate; compare the saved/printed evidence with this section.
    """
    for _, _, filename in QUESTIONS:
        rows = cloud.chunks("acme", filename)
        require(rows, f"No current chunks for {filename}; ingest the lesson fixture first.")
        cloud.save(filename.replace(".", "_") + "_locators", rows)
        print(filename, "->", len(rows), "current chunks")
        for cid, row in sorted(rows.items())[:5]:
            print(" ", cid, "locator", row.get("locator"), "page_start", row.get("page_start"), "section", row.get("section"))
        require(all(row.get("locator") for row in rows.values()), "Some chunks lack locators; inspect the ingest schema/backfill.")
        if filename.endswith(".pdf"):
            require(all(isinstance(row.get("page_start"), int) and row["page_start"] > 0 for row in rows.values()), "PDF rows need positive page_start values.")


def demonstrate(session):
    """Run this section in order and checkpoint each completed function.

    Example: main() supplies the active session; a failed read resumes after an explicit retry.
    """
    require(not session.state.get("lesson31_closed"), "Run was cleaned up; start a new lesson session.")
    run_steps(session, [
        ("source_26", contract_step(inspect_citations)),
        ("source_28", contract_step(inspect_locators)),
    ], retry_failed=RETRY_FAILED_STEP)


def main():
    """Run this HTML section with the IDE interpreter.

    Example: choose Run or Debug on this file after the README prerequisites.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
