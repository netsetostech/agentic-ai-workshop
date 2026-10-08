# Lesson 11.1: Build and deploy using keyless identity

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

This lesson has no authored main HTML. Its file numbers follow the explicitly listed course-plan experiments; they do not claim an HTML heading match. Run those plan steps in the order below.

| HTML section | File | What it demonstrates |
|---|---|---|
| Plan step 1 | [demo_01_inspect_the_keyless_build_identity.py](demo_01_inspect_the_keyless_build_identity.py) | Inspect the keyless build identity |
| Plan step 2 | [demo_02_build_the_deployment_images.py](demo_02_build_the_deployment_images.py) | Build the deployment images |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/grant_the_build_account_what_a_build_needs.py](recovery/grant_the_build_account_what_a_build_needs.py) — Only if the build stopped at storage.objects.get: 'could not resolve source' and a 403 naming the Compute Engine default account. The kit names no account for Cloud Build, so a build runs as the project's default build account, and in an organization created on or after 3 May 2024 that account is created without the Editor role. Run once, as a project owner: read access to its source in the PROJECT_cloudbuild bucket only, push access to the documind repository, and log writing. Not Editor or roles/cloudbuild.builds.builder: granted on the project, either one can read, write and delete every object in every bucket, the uploads bucket included. IAM applies a grant in about two minutes, sometimes seven or more; then run the build again.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### demo_01_inspect_the_keyless_build_identity.py

Read the kit's workload-identity and build definitions. Verify repository/ref conditions in the real deployment configuration before submitting a build; no service-account key is generated.

**`step_01_inspect_the_keyless_build_identity(session)` — Inspect the keyless build identity / Inspect the keyless build identity**

Read the kit's workload-identity and build definitions. Verify repository/ref conditions in the real deployment configuration before submitting a build; no service-account key is generated.

Operation: Course-plan experiment — local Python/kit inspection.

### demo_02_build_the_deployment_images.py

Use the actual kit build target and the current authenticated identity. Record the build output and image tags; a successful local credential check alone does not prove a deployed GitHub workload-identity run.

**`step_01_build_the_deployment_images(session)` — Build the deployment images / Build the deployment images**

Use the actual kit build target and the current authenticated identity. Record the build output and image tags; a successful local credential check alone does not prove a deployed GitHub workload-identity run.

Operation: Course-plan experiment — live deployment.

### recovery/grant_the_build_account_what_a_build_needs.py

Only if the build stopped at storage.objects.get: 'could not resolve source' and a 403 naming the Compute Engine default account. The kit names no account for Cloud Build, so a build runs as the project's default build account, and in an organization created on or after 3 May 2024 that account is created without the Editor role. Run once, as a project owner: read access to its source in the PROJECT_cloudbuild bucket only, push access to the documind repository, and log writing. Not Editor or roles/cloudbuild.builds.builder: granted on the project, either one can read, write and delete every object in every bucket, the uploads bucket included. IAM applies a grant in about two minutes, sometimes seven or more; then run the build again.

**`step_01_grant_the_build_account_what_a_build_needs(session)` — Grant the build account what a build needs / Grant the build account what a build needs**

Only if the build stopped at storage.objects.get: 'could not resolve source' and a 403 naming the Compute Engine default account. The kit names no account for Cloud Build, so a build runs as the project's default build account, and in an organization created on or after 3 May 2024 that account is created without the Editor role. Run once, as a project owner: read access to its source in the PROJECT_cloudbuild bucket only, push access to the documind repository, and log writing. Not Editor or roles/cloudbuild.builds.builder: granted on the project, either one can read, write and delete every object in every bucket, the uploads bucket included. IAM applies a grant in about two minutes, sometimes seven or more; then run the build again.

Operation: Course-plan experiment — live deployment.

Expected shape, not a promised result:

```text
Three bindings added for the account the 403 named; the next build reads its source.
```

## Source and coverage

This lesson has no authored main HTML yet. These experiments come from the course plan and actual kit entry points, not an invented HTML sequence. `lesson_map.json` records their attribution.
