"""Lesson 3.9: Failure modes: four the kit reproduces, and which ones the alerts see

The cell reads every Terraform file in the kit, lists the alert policies each declares, holds quota.tf's named alerts against them, and prints what the unanswerable rate's denominator counts.

Run order inside this file:
1. Do it: the alerts the kit declares, against the ones it names (source window 29)

Prerequisites: demo_04_architecture_three_designs_rejected_and_the_number_that_would_change_each.
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


def step_01_the_alerts_the_kit_declares_against_the_on(session):
    """Run Do it: the alerts the kit declares, against the ones it names at this checkpoint.

    The cell reads every Terraform file in the kit, lists the alert policies each declares, holds quota.tf's named alerts against them, and prints what the unanswerable rate's denominator counts.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: it reads the kit's files and calls nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: alerts.tf declares api_latency, unanswerable_rate, gpu_left_warm, ingest_failed, reconcile_drift, reconcile_failed, dlq_depth, ingest_backlog
    desk_alerts.tf declares desk_fallback_share, desk_l2_share, desk_clarify_oos_trend, case_overdue, doc_type_pin_miss, desk_delegation_refused, desk_gate_error_share, desk_check_tenants_unread
    quota.tf names unanswerable_rate declared in alerts.tf
    quota.tf names dlq_depth         declared in alerts.tf
    quota.tf names guardrail_blocks  declared by nothing
    quota.tf names cache_hit_low     declared by nothing
    quota.tf names burn_rate         declared by nothing
    the unanswerable rate counts: resource.type="cloud_run_revision" resource.labels.service_name="doc
    """
    import re, warnings
    from pathlib import Path
    warnings.filterwarnings("ignore", category=UserWarning)
    tf = {p.name: p.read_text(encoding="utf-8") for p in sorted(Path("terraform").glob("*.tf"))}
    declared = {n: f for f, t in tf.items() for n in re.findall(r'resource "google_monitoring_alert_policy" "(\w+)"', t)}
    for f in sorted(set(declared.values())):
        print(f"{f} declares {', '.join(n for n, g in declared.items() if g == f)}")
    named = re.findall(r"^\s+(\w+) = \"", tf["quota.tf"].split("documind_alerts = {", 1)[1].split("\n  }", 1)[0], re.M)
    for n in named:
        print(f"quota.tf names {n:17} {'declared in ' + declared[n] if n in declared else 'declared by nothing'}")
    counted = re.search(r'"google_logging_metric" "queries" \{.*?filter\s+= <<EOT(.*?)EOT', tf["alerts.tf"], re.S).group(1)
    print("the unanswerable rate counts:", " ".join(counted.split()))
    print("rows it never counts:", ", ".join(e for e in ("query", "stream", "passages", "desk_gate") if f'event="{e}"' not in counted))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_29', step_01_the_alerts_the_kit_declares_against_the_on),
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
