"""Lesson 1.5: The plumbing: read the notification, the topic and the subscription off your lane

Read it off the platform

Run order inside this file:
1. Read it off the platform (source window 10)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_off_the_platform.
COMMANDS_01 = """gcloud storage buckets notifications list "gs://$PROJECT-uploads" --project "$PROJECT"

gcloud pubsub subscriptions describe documind-ingest-push --project "$PROJECT" \\
  --format='yaml(pushConfig.pushEndpoint,pushConfig.oidcToken.serviceAccountEmail,ackDeadlineSeconds,retryPolicy,deadLetterPolicy)'

gcloud pubsub subscriptions describe ingest-dlq-sub --project "$PROJECT" --format='value(topic)'

gcloud run services describe documind-ingest --region "$REGION" --project "$PROJECT" \\
  --format='yaml(spec.template.spec.timeoutSeconds,spec.template.spec.containerConcurrency,spec.template.metadata.annotations)'

"""

def step_01_off_the_platform(session):
    """Run Read it off the platform at this checkpoint.

    Read it off the platform

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (all read-only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ---
    event_types:
    - OBJECT_FINALIZE
    id: '1'
    payload_format: JSON_API_V1
    topic: //pubsub.googleapis.com/projects/documind-ai-YOUR-ID/topics/documind-ingest
    ackDeadlineSeconds: 600
    deadLetterPolicy:
      deadLetterTopic: projects/documind-ai-YOUR-ID/topics/documind-ingest-dlq
      maxDeliveryAttempts: 12
    pushConfig:
      oidcToken:
        serviceAccountEmail: documind-ingest-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com
      pushEndpoint: https://documind-ingest-NUMBER.asia-south1.run.app
    retryPolicy:
      maximumBackoff: 600s
      minimumBackoff: 10s
    projects/documind-ai-YOUR-ID/topics/documind-ingest-dlq
    spec:
      template:
        metadata:
          annotations:
            autoscaling.knative.dev/maxScale: '30'
            run
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_off_the_platform),
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
