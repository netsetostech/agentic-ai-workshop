"""Lesson 1.1 / HTML section 8: Why it is built this way: the failures behind each rule

Run the actual kit validators locally. This extends the section explanation and
verification checklist into Python: rewrapping changes bytes but preserves chunk
identity; a root-level upload event is rejected for lacking a tenant prefix.
No live poison object is uploaded and no worker-log result is claimed.

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


def prove_local_contract_rules():
    """Call the actual kit validators; rewrapping changes bytes but preserves chunk identity.
    
    Example: prove_local_contract_rules() checks whitespace-only rewrapping locally.
    Failures propagate; compare the saved/printed evidence with this section.
    """
    from pydantic import ValidationError
    from services.ingest.contracts import IngestMessage, chunk_hash, sha256_of
    original, rewrapped = "Notice period is ninety days.", " Notice\nperiod  is ninety\tdays. "
    require(sha256_of(original.encode()) != sha256_of(rewrapped.encode()), "The example must change file bytes.")
    require(chunk_hash(original) == chunk_hash(rewrapped), "Rewrapped text should keep its chunk hash.")
    require(chunk_hash(original) != chunk_hash("Notice period is thirty days."), "Changed words should change the chunk hash.")
    event = dict(bucket="example-uploads", name="acme/note.md", size=1, contentType="text/markdown", generation="1")
    require(IngestMessage(**event).tenant_id == "acme", "Tenant should derive from the object prefix.")
    try:
        IngestMessage(**{**event, "name": "note.md"})
    except ValidationError as error:
        require("tenant prefix" in str(error), "Validator rejected the event for an unexpected reason.")
        print("Local contracts: rewrapped chunk hash unchanged; root-level object rejected.")
    else:
        raise RuntimeError("A root-level object unexpectedly passed validation.")


def demonstrate(session):
    """Run this section in order and checkpoint each completed function.

    Example: main() supplies the active session; a failed read resumes after an explicit retry.
    """
    require(not session.state.get("lesson31_closed"), "Run was cleaned up; start a new lesson session.")
    run_steps(session, [
        ("source_prose_rules", contract_step(prove_local_contract_rules, local=True)),
    ], retry_failed=RETRY_FAILED_STEP)


def main():
    """Run this HTML section with the IDE interpreter.

    Example: choose Run or Debug on this file after the README prerequisites.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
