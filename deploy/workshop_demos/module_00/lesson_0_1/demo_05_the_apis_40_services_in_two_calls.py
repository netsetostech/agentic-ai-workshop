"""Lesson 0.1: The APIs: 40 services in two calls

An API, in Google Cloud's sense, is a product switched on for one project: Cloud Run, Firestore, Vertex AI. Until it is enabled, every call to it from that project is refused, whoever makes it, with a message that names the API. Enabling costs nothing; using is what bills. The kit needs 40 of them before Terraform can create anything, and keeps the list in one block of commands/lesson-12.1.sh, the one marked ENABLE_APIS. It is two calls rather than one because the Service Usage API takes at most 20 services per request, as the block's own comment records. make apis runs that block unchanged: You have no clone yet, so you paste the same lines. They are the block exactly, taken from the kit when this page was built: the first sets gcloud's project, which step 4 already did, and the next two enable the list. A short loop compares the project's enabled services with the kit's list and names any that is missing. Run it now, and again whenever a later lesson's command complains that an API is disabled.

Run order inside this file:
1. Definition (source window 9)
2. Count them (source window 11)

Prerequisites: demo_04_the_project_create_it_link_it_make_it_the_default.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """gcloud config set project $PROJECT
gcloud services enable \\
  run.googleapis.com \\
  compute.googleapis.com \\
  vpcaccess.googleapis.com \\
  pubsub.googleapis.com \\
  artifactregistry.googleapis.com \\
  secretmanager.googleapis.com \\
  firestore.googleapis.com \\
  storage.googleapis.com \\
  aiplatform.googleapis.com \\
  documentai.googleapis.com \\
  vision.googleapis.com \\
  language.googleapis.com \\
  translate.googleapis.com \\
  speech.googleapis.com \\
  texttospeech.googleapis.com \\
  dlp.googleapis.com \\
  iap.googleapis.com \\
  iamcredentials.googleapis.com \\
  cloudbuild.googleapis.com \\
  orgpolicy.googleapis.com
gcloud services enable \\
  cloudtrace.googleapis.com \\
  monitoring.googleapis.com \\
  logging.googleapis.com \\
  billingbudgets.googleapis.com \\
  bigquery.googleapis.com \\
  discoveryengine.googleapis.com \\
  dataplex.googleapis.com \\
  sqladmin.googleapis.com \\
  eventarc.googleapis.com \\
  workflows.googleapis.com \\
  cloudscheduler.googleapis.com \\
  cloudfunctions.googleapis.com \\
  modelarmor.googleapis.com \\
  cloudbilling.googleapis.com \\
  cloudresourcemanager.googleapis.com \\
  serviceusage.googleapis.com \\
  vectorsearch.googleapis.com \\
  spanner.googleapis.com \\
  container.googleapis.com \\
  clouddeploy.googleapis.com

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    An API, in Google Cloud's sense, is a product switched on for one project: Cloud Run, Firestore, Vertex AI. Until it is enabled, every call to it from that project is refused, whoever makes it, with a message that names the API. Enabling costs nothing; using is what bills. The kit needs 40 of them before Terraform can create anything, and keeps the list in one block of commands/lesson-12.1.sh, the one marked ENABLE_APIS. It is two calls rather than one because the Service Usage API takes at most 20 services per request, as the block's own comment records. make apis runs that block unchanged: You have no clone yet, so you paste the same lines. They are the block exactly, taken from the kit when this page was built: the first sets gcloud's project, which step 4 already did, and the next two enable the list.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in Cloud Shell, once (the kit's ENABLE_APIS block: 40 APIs in 2 calls).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/apis_enable.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_count_them.
COMMANDS_02 = """enabled="$(gcloud services list --enabled --project "$PROJECT" --format='value(config.name)')"
missing=0
for api in run.googleapis.com compute.googleapis.com vpcaccess.googleapis.com pubsub.googleapis.com artifactregistry.googleapis.com \\
           secretmanager.googleapis.com firestore.googleapis.com storage.googleapis.com aiplatform.googleapis.com documentai.googleapis.com \\
           vision.googleapis.com language.googleapis.com translate.googleapis.com speech.googleapis.com texttospeech.googleapis.com \\
           dlp.googleapis.com iap.googleapis.com iamcredentials.googleapis.com cloudbuild.googleapis.com orgpolicy.googleapis.com \\
           cloudtrace.googleapis.com monitoring.googleapis.com logging.googleapis.com billingbudgets.googleapis.com bigquery.googleapis.com \\
           discoveryengine.googleapis.com dataplex.googleapis.com sqladmin.googleapis.com eventarc.googleapis.com workflows.googleapis.com \\
           cloudscheduler.googleapis.com cloudfunctions.googleapis.com modelarmor.googleapis.com cloudbilling.googleapis.com cloudresourcemanager.googleapis.com \\
           serviceusage.googleapis.com vectorsearch.googleapis.com spanner.googleapis.com container.googleapis.com clouddeploy.googleapis.com; do
  grep -qxF "$api" <<< "$enabled" || { echo "MISSING $api"; missing=$((missing + 1)); }
done
echo "the kit's 40: $((40 - missing)) enabled, $missing missing"
echo "enabled on the project in all: $(grep -c . <<< "$enabled")"

"""

def step_02_count_them(session):
    """Run Count them at this checkpoint.

    A short loop compares the project's enabled services with the kit's list and names any that is missing. Run it now, and again whenever a later lesson's command complains that an API is disabled.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in Cloud Shell (read-only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/apis_check.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_definition),
        ('source_11', step_02_count_them),
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
