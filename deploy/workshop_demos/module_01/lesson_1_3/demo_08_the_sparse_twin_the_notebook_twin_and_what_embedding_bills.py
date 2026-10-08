"""Lesson 1.3: The sparse twin, the notebook twin, and what embedding bills

Run it on the lane's text, Rs 0

Run order inside this file:
1. Run it on the lane's text, Rs 0 (source window 44)

Prerequisites: demo_07_carry_over_re_issue_the_handbook_embed_only_what_changed.
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


def step_01_on_the_lane_s_text_rs_0(session):
    """Run Run it on the lane's text, Rs 0 at this checkpoint.

    Run it on the lane's text, Rs 0

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell, wrapped so it pastes straight into bash).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: row stamp: blake2b-tf-v1 | encoder here: blake2b-tf-v1
    NP-03: 41 words, 33 distinct -> 33 sparse dimensions, max weight 2.5
    the question: 13 dimensions, 9 shared with NP-03: ['a', 'at', 'confirmed', 'days', 'e3', 'employee', 'grade', 'notice', 'of']
    same text twice, same dimensions: True
    """
    import os, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.path.insert(0, ".")
    from google.cloud import firestore
    from shared.sparse_encoder import sparse_encode, SPARSE_ENCODER_VERSION, _tokens
    PROJECT = os.environ["PROJECT"]
    db = firestore.Client(project=PROJECT)
    row = next(db.collection("chunks").where("tenant_id", "==", "acme")
                 .where("source_uri", "==", f"gs://{PROJECT}-uploads/acme/hr_policy_2026.md")
                 .where("current", "==", True).where("locator", "==", "NP-03").stream()).to_dict()
    dv, dd = sparse_encode(row["text"])
    print("row stamp:", row["sparse_encoder_version"], "| encoder here:", SPARSE_ENCODER_VERSION)
    print(f"NP-03: {len(_tokens(row['text']))} words, {len(dd)} distinct -> {len(dd)} sparse dimensions, max weight {max(dv)}")
    q = "How many days of notice does a confirmed employee at grade E3 serve?"
    qv, qd = sparse_encode(q)
    print(f"the question: {len(qd)} dimensions, {len(set(qd) & set(dd))} shared with NP-03:", sorted(set(_tokens(q)) & set(_tokens(row['text']))))
    print("same text twice, same dimensions:", sparse_encode(row["text"]) == (dv, dd))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_44', step_01_on_the_lane_s_text_rs_0),
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
