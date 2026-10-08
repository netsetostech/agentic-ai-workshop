"""Lesson 1.8: How reconciliation decides

Explain the page's two-PDF illustration. Reconciliation leaves the matching queued generation to the batch lane; only the new Act contributes to drift. Reproduce the five default widget documents before exploring its known-bytes and queued variations. The real plan(), decide_bytes() and drift_of() functions make the decisions.

Run order inside this file:
1. How do we know a PDF is queued? (source window queued-example)
2. Explore a different bucket and ledger (source window widget)

Prerequisites: workshop setup; see this lesson README.
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


def step_01_how_do_we_know_a_pdf_is_queued(session):
    """Run How do we know a PDF is queued? at this checkpoint.

    Explain the page's two-PDF illustration. Reconciliation leaves the matching queued generation to the batch lane; only the new Act contributes to drift.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: Python — simulated facts, actual kit planner; no network.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: reingest 1, queued 1, drift 1; applied false
    """
    from workshop_helpers.kit import KitAdapter
    from workshop_helpers.reconciliation import evaluate, print_plan
    kit = KitAdapter(session.config.kit_root)
    objects = [dict(name="acme/cgst_act_2017.pdf", generation="1", tenant_id="acme"),
               dict(name="acme/cgst_it_bundle.pdf", generation="4", tenant_id="acme")]
    claims = {"acme_bundle": {"status": "queued", "generation": "4",
                              "gcs_uri": "gs://example-uploads/acme/cgst_it_bundle.pdf"}}
    report = evaluate(kit, objects, {}, claims, lambda action: "new-act-bytes")
    print_plan(report)
    assert report["summary"]["reingest"] == report["summary"]["queued"] == 1
    assert report["summary"]["drift"] == 1
    print("The queued claim names this object AND generation. It does not prove the batch job finished.")

def step_02_explore_a_different_bucket_and_ledger(session):
    """Run Explore a different bucket and ledger at this checkpoint.

    Reproduce the five default widget documents before exploring its known-bytes and queued variations. The real plan(), decide_bytes() and drift_of() functions make the decisions.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: Python — simulated facts, actual kit planner; no network.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ok 1, retire 1, touch 1, reingest 1, withdrawn 1; drift 2
    """
    from copy import deepcopy
    from workshop_helpers.kit import KitAdapter
    from workshop_helpers.reconciliation import evaluate_widget, print_plan
    # These are the exact default rows from the HTML widget; edit a copy for variations.
    rows = [{'name': 'acme/hr_policy_2026.md', 'bucket': 'same', 'ledger': 'indexed', 'bytes': 'same', 'queued': False}, {'name': 'acme/smoke_note_v1.md', 'bucket': 'absent', 'ledger': 'indexed', 'bytes': 'same', 'queued': False}, {'name': 'acme/dpdp_act_2023.pdf', 'bucket': 'newer', 'ledger': 'indexed', 'bytes': 'same', 'queued': False}, {'name': 'acme/new_circular.md', 'bucket': 'same', 'ledger': 'none', 'bytes': 'new', 'queued': False}, {'name': 'acme/old_policy.md', 'bucket': 'same', 'ledger': 'withdrawn', 'bytes': 'same', 'queued': False}]
    kit = KitAdapter(session.config.kit_root)
    report = evaluate_widget(kit, rows)
    print_plan(report)
    assert report["summary"]["drift"] == 2
    assert all(report["summary"][name] == 1 for name in ("ok", "retire", "touch", "reingest", "withdrawn"))
    known = deepcopy(rows)
    known[3]["bytes"] = "known"
    print("\nVariation: the circular's bytes already have an indexed claim.")
    print_plan(evaluate_widget(kit, known))
    queued = deepcopy(rows)
    queued[3]["queued"] = True
    print("\nVariation: a queued claim owns the circular's generation.")
    print_plan(evaluate_widget(kit, queued))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_queued-example', step_01_how_do_we_know_a_pdf_is_queued),
        ('source_widget', step_02_explore_a_different_bucket_and_ledger),
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
