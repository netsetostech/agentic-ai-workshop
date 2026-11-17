"""Lesson 0.5: Verify all seven services

Seven services, Ready, on one tag. Every service must be Ready and running an image tagged with the same $GIT_SHA.

Run order inside this file:
1. Verify all seven services (source window 57)

Prerequisites: demo_11_finish_what_make_up_finishes_the_index_wait_the_managed_stores_and_the_bigquery.
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


# Original CLI workflow for step_01_verify_all_seven_services.
COMMANDS_01 = """echo "Expected tag: $GIT_SHA"
for svc in documind-ingest documind-api documind-admin documind-ui documind-chat documind-mcp documind-agent; do
  if line="$(gcloud run services describe "$svc" --project="$PROJECT" --region="$REGION" \\
      --format='value(status.conditions[0].status,spec.template.spec.containers[0].image)' 2>/dev/null)"; then
    read -r ready image <<<"$line"
    if [[ "$ready" == True && "$image" == *":$GIT_SHA" ]]; then
      printf 'OK       %-16s %s\\n' "$svc" "$image"
    else
      printf 'PROBLEM  %-16s ready=%s image=%s\\n' "$svc" "$ready" "$image"
    fi
  else
    printf 'MISSING  %s\\n' "$svc"
  fi
done

"""

def step_01_verify_all_seven_services(session):
    """Run Verify all seven services at this checkpoint.

    Seven services, Ready, on one tag. Every service must be Ready and running an image tagged with the same $GIT_SHA.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash - Verify.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe the printed/saved evidence for this heading; a zero exit alone is not proof.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_57', step_01_verify_all_seven_services),
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
