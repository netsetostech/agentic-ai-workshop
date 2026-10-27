# Lesson 0.5: Set up the cloud lane end to end: clone in Cloud Shell, create the infrastructure with Terraform, deploy every service and the UI

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: open Cloud Shell and keep it alive |
| 3 | [demo_03_prepare_the_project_and_the_shell_the_project_the_sign_in_the_variables_the_tool.py](demo_03_prepare_the_project_and_the_shell_the_project_the_sign_in_the_variables_the_tool.py) | Prepare the project and the shell: the project, the sign-in, the variables, the tools |
| 4 | [demo_04_prepare_python_and_the_kit_the_3_12_environment_the_clone_from_main_the_dependen.py](demo_04_prepare_python_and_the_kit_the_3_12_environment_the_clone_from_main_the_dependen.py) | Prepare Python and the kit: the 3.12 environment, the clone from main, the dependencies |
| 5 | [demo_05_prepare_terraform_the_apis_and_the_state_bucket_its_sign_in_the_billing_account.py](demo_05_prepare_terraform_the_apis_and_the_state_bucket_its_sign_in_the_billing_account.py) | Prepare Terraform: the APIs and the state bucket, its sign-in, the billing account, the inputs |
| 6 | [demo_06_run_terraform_init_one_saved_plan_the_apply_the_vector_index.py](demo_06_run_terraform_init_one_saved_plan_the_apply_the_vector_index.py) | Run Terraform: init, one saved plan, the apply, the vector index |
| 7 | [demo_07_restore_the_shell_pin_git_sha_export_the_runtime_settings_and_prepare_the_secret.py](demo_07_restore_the_shell_pin_git_sha_export_the_runtime_settings_and_prepare_the_secret.py) | Restore the shell, pin GIT_SHA, export the runtime settings and prepare the secrets |
| 8 | [demo_08_gate_the_build_then_build_all_seven_images.py](demo_08_gate_the_build_then_build_all_seven_images.py) | Gate the build, then build all seven images |
| 9 | [demo_09_deploy_the_seven_services_the_worker_and_the_api_the_admin_console_chat_the_ui_m.py](demo_09_deploy_the_seven_services_the_worker_and_the_api_the_admin_console_chat_the_ui_m.py) | Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer |
| 10 | [demo_10_tenants_put_people_and_services_on_the_rosters.py](demo_10_tenants_put_people_and_services_on_the_rosters.py) | Tenants: put people and services on the rosters |
| 11 | [demo_11_finish_what_make_up_finishes_the_index_wait_the_managed_stores_and_the_bigquery.py](demo_11_finish_what_make_up_finishes_the_index_wait_the_managed_stores_and_the_bigquery.py) | Finish what make up finishes: the index wait, the managed stores and the BigQuery views |
| 12 | [demo_12_verify_all_seven_services.py](demo_12_verify_all_seven_services.py) | Verify all seven services |
| 13 | [demo_13_open_the_ui_and_ask_a_first_question.py](demo_13_open_the_ui_and_ask_a_first_question.py) | Open the UI and ask a first question |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

Open the Google Cloud console signed in as the account that owns your billing account, and click Activate Cloud Shell. Start a tmux session: builds and the Terraform apply run for a long time, and inside tmux they keep running if the browser drops.

**`step_01_before_you_run_anything_open_cloud_shell_a(session)` — Before you run anything: open Cloud Shell and keep it alive / Before you run anything: open Cloud Shell and keep it alive**

Open the Google Cloud console signed in as the account that owns your billing account, and click Activate Cloud Shell. Start a tmux session: builds and the Terraform apply run for a long time, and inside tmux they keep running if the browser drops.

Operation: bash - Cloud Shell, once per session.

IDE adaptation: Print the version's first line with sed instead of head: gcloud and terraform go on writing after it, and under the demo shell's pipefail their SIGPIPE when head closed first failed the cell with exit 141, by chance (23 October 2026). The line printed is the same.

### demo_03_prepare_the_project_and_the_shell_the_project_the_sign_in_the_variables_the_tool.py

The account every later command runs as. One set of variables, checked, then saved for new terminals. Change PROJECT to your project ID. The block stops at the first failed check. Ends with PASS: project <id> (<number>) is active, billed, operator <email>. Write the helper that saves your settings for new terminals, then save. It now also keeps GIT_SHA, the source snapshot your images are built from (pinned in Phase 3). Terraform 1.9 or newer, git, jq, make and file. Terraform v1.9.0 or newer and no MISSING lines: skip to S5. Otherwise run the matching install below. Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository: Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository: The fingerprint identifies HashiCorp's package-signing key. Do not continue if the download or conversion failed. The last command prints Terraform v1.9.0 or newer. Only if terraform still isn't found, or an older binary shadows it: Packages installed outside your home directory may need reinstalling after a Cloud Shell VM reset. Never loosen required_version or provider constraints, and never use insecure TLS or unsigned-package flags. Install git, jq, make or file (only if one is missing):

**`step_01_s2_sign_in_the_gcloud_cli(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S2. Sign in the gcloud CLI**

The account every later command runs as.

Operation: bash - Check sign-in.

**`step_02_s3_set_the_project_and_session_variables(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S3. Set the project and session variables**

One set of variables, checked, then saved for new terminals. Change PROJECT to your project ID. The block stops at the first failed check.

Operation: bash - Project and variables.

**`step_03_s3_set_the_project_and_session_variables(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S3. Set the project and session variables**

Ends with PASS: project <id> (<number>) is active, billed, operator <email>. Write the helper that saves your settings for new terminals, then save. It now also keeps GIT_SHA, the source snapshot your images are built from (pinned in Phase 3).

Operation: bash - Save settings.

**`step_04_s4_check_terraform_and_command_line_tools(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S4. Check Terraform and command-line tools**

Terraform 1.9 or newer, git, jq, make and file.

Operation: bash - Check tools.

IDE adaptation: Print the version's first line with sed instead of head: gcloud and terraform go on writing after it, and under the demo shell's pipefail their SIGPIPE when head closed first failed the cell with exit 141, by chance (23 October 2026). The line printed is the same.

**`step_05_s4_check_terraform_and_command_line_tools(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S4. Check Terraform and command-line tools**

Terraform v1.9.0 or newer and no MISSING lines: skip to S5. Otherwise run the matching install below. Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository:

Operation: bash - Prerequisites.

**`step_06_s4_check_terraform_and_command_line_tools(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S4. Check Terraform and command-line tools**

Terraform v1.9.0 or newer and no MISSING lines: skip to S5. Otherwise run the matching install below. Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository:

Operation: bash - Signing key.

**`step_07_s4_check_terraform_and_command_line_tools(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S4. Check Terraform and command-line tools**

Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository: The fingerprint identifies HashiCorp's package-signing key. Do not continue if the download or conversion failed.

Operation: bash - Repository.

**`step_08_s4_check_terraform_and_command_line_tools(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S4. Check Terraform and command-line tools**

Install Terraform (only if missing or older than 1.9.0). First the utilities for HashiCorp's signed repository: The fingerprint identifies HashiCorp's package-signing key. Do not continue if the download or conversion failed.

Operation: bash - Install Terraform.

**`step_09_s4_check_terraform_and_command_line_tools(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S4. Check Terraform and command-line tools**

The last command prints Terraform v1.9.0 or newer. Only if terraform still isn't found, or an older binary shadows it:

Operation: bash - Fix PATH.

**`step_10_s4_check_terraform_and_command_line_tools(session)` — Prepare the project and the shell: the project, the sign-in, the variables, the tools / S4. Check Terraform and command-line tools**

Packages installed outside your home directory may need reinstalling after a Cloud Shell VM reset. Never loosen required_version or provider constraints, and never use insecure TLS or unsigned-package flags. Install git, jq, make or file (only if one is missing):

Operation: bash - Install utilities.

### demo_04_prepare_python_and_the_kit_the_3_12_environment_the_clone_from_main_the_dependen.py

Python 3.12 in ~/rag-shell-venv, outside the source tree. The environment lives at $HOME/rag-shell-venv; project files stay in $HOME/deploy_module_rag. Clones main into $DEMO_ROOT the first time and fast-forwards to the latest main afterwards. Once you have built images in Build and deploy, they are tied to the commit saved in GIT_SHA. Pulling newer code afterwards does not change the running services; the pin block in Phase 3 will notice the difference and tell you to either go back to the saved commit or rebuild every image. The operator's Python packages, checked against the kit's pins. Needed for the build gate, ingestion, evaluation and smoke tests. Terraform does not need it. Restores your saved settings in a new terminal. To also pull the latest code, rerun S6.

**`step_01_s5_create_the_python_3_12_environment(session)` — Prepare Python and the kit: the 3.12 environment, the clone from main, the dependencies / S5. Create the Python 3.12 environment**

Python 3.12 in ~/rag-shell-venv, outside the source tree. The environment lives at $HOME/rag-shell-venv; project files stay in $HOME/deploy_module_rag.

Operation: bash - Install uv and Python 3.12.

**`step_02_s5_create_the_python_3_12_environment(session)` — Prepare Python and the kit: the 3.12 environment, the clone from main, the dependencies / S5. Create the Python 3.12 environment**

Python 3.12 in ~/rag-shell-venv, outside the source tree. The environment lives at $HOME/rag-shell-venv; project files stay in $HOME/deploy_module_rag.

Operation: bash - Activate and verify.

**`step_03_s6_get_all_files_from_the_latest_main(session)` — Prepare Python and the kit: the 3.12 environment, the clone from main, the dependencies / S6. Get all files from the latest main**

Clones main into $DEMO_ROOT the first time and fast-forwards to the latest main afterwards. Once you have built images in Build and deploy, they are tied to the commit saved in GIT_SHA. Pulling newer code afterwards does not change the running services; the pin block in Phase 3 will notice the difference and tell you to either go back to the saved commit or rebuild every image.

Operation: bash - Clone or update.

**`step_04_s7_install_python_dependencies(session)` — Prepare Python and the kit: the 3.12 environment, the clone from main, the dependencies / S7. Install Python dependencies**

The operator's Python packages, checked against the kit's pins. Needed for the build gate, ingestion, evaluation and smoke tests. Terraform does not need it.

Operation: bash - Install.

**`step_05_reopening_a_terminal_later(session)` — Prepare Python and the kit: the 3.12 environment, the clone from main, the dependencies / Reopening a terminal later**

Restores your saved settings in a new terminal. To also pull the latest code, rerun S6.

Operation: bash - a new terminal: restore your settings.

### demo_05_prepare_terraform_the_apis_and_the_state_bucket_its_sign_in_the_billing_account.py

40 APIs, the service agents, the versioned state bucket. Before you start, finish Phase 1 (S1 to S6) in this terminal with the Python environment active. The API list is the block make apis runs; this step adds the service agents and the state bucket. Application Default Credentials and the quota project. Run this alone, open the URL and sign in with your operator account: The billing account Terraform's budget needs, verified and saved. Every input the kit's make plan would pass, and the CI trust, saved into the same inputs file. Inputs not listed keep their variables.tf defaults: the Google Chat door, the Desk job and GKE Autopilot stay off. The CI trust (terraform/wif.tf) lets GitHub Actions workflows from one repository, on one branch, become sa-documind-cicd in your project with no key file. That account can deploy code that runs as your services, so the repository must be one you own. It is never the repository you cloned: netsetos/agents_workshop_learner is the course author's, and trusting it would let the author's workflows deploy into your lane. On GitHub, open that repository and choose Fork; your fork is YOUR-GITHUB-USER/agents_workshop_learner. Lesson 11.1 builds and deploys through this trust. Name your fork in GH_REPO; the block looks up its numeric id, the value the trust is really keyed on, and stops on the author's repository or an empty answer.

**`step_01_t1_enable_apis_service_agents_and_the_stat(session)` — Prepare Terraform: the APIs and the state bucket, its sign-in, the billing account, the inputs / T1. Enable APIs, service agents and the state bucket**

40 APIs, the service agents, the versioned state bucket. Before you start, finish Phase 1 (S1 to S6) in this terminal with the Python environment active. The API list is the block make apis runs; this step adds the service agents and the state bucket.

Operation: bash - APIs and state bucket.

**`step_02_t2_sign_in_terraform_and_set_its_quota_pro(session)` — Prepare Terraform: the APIs and the state bucket, its sign-in, the billing account, the inputs / T2. Sign in Terraform and set its quota project**

Application Default Credentials and the quota project. Run this alone, open the URL and sign in with your operator account:

Operation: bash - ADC login.

**`step_03_t2_sign_in_terraform_and_set_its_quota_pro(session)` — Prepare Terraform: the APIs and the state bucket, its sign-in, the billing account, the inputs / T2. Sign in Terraform and set its quota project**

Application Default Credentials and the quota project. Run this alone, open the URL and sign in with your operator account:

Operation: bash - Quota project.

**`step_04_t3_save_the_billing_account_for_terraform(session)` — Prepare Terraform: the APIs and the state bucket, its sign-in, the billing account, the inputs / T3. Save the billing account for Terraform**

The billing account Terraform's budget needs, verified and saved.

Operation: bash - Billing lookup.

**`step_05_t4_set_the_terraform_inputs(session)` — Prepare Terraform: the APIs and the state bucket, its sign-in, the billing account, the inputs / T4. Set the Terraform inputs**

Every input the kit's make plan would pass, and the CI trust, saved into the same inputs file. Inputs not listed keep their variables.tf defaults: the Google Chat door, the Desk job and GKE Autopilot stay off. The CI trust (terraform/wif.tf) lets GitHub Actions workflows from one repository, on one branch, become sa-documind-cicd in your project with no key file. That account can deploy code that runs as your services, so the repository must be one you own. It is never the repository you cloned: netsetos/agents_workshop_learner is the course author's, and trusting it would let the author's workflows deploy into your lane. On GitHub, open that repository and choose Fork; your fork is YOUR-GITHUB-USER/agents_workshop_learner. Lesson 11.1 builds and deploys through this trust. Name your fork in GH_REPO; the block looks up its numeric id, the value the trust is really keyed on, and stops on the author's repository or an empty answer.

Operation: bash - Inputs (your fork, not the example's).

### demo_06_run_terraform_init_one_saved_plan_the_apply_the_vector_index.py

Point Terraform at its state in your bucket. A saved plan file, after validate and an input check. Apply that exact plan, then prove nothing is left to change. Run alone, in the same terminal as T6 (the plan file name is only in that shell). Run alone, in the same terminal as T6 (the plan file name is only in that shell). Confirm nothing is left to change: The index, the endpoint and the deployed ID, still empty.

**`step_01_t5_initialize_terraform(session)` — Run Terraform: init, one saved plan, the apply, the vector index / T5. Initialize Terraform**

Point Terraform at its state in your bucket.

Operation: bash - Init.

**`step_02_t5_initialize_terraform(session)` — Run Terraform: init, one saved plan, the apply, the vector index / T5. Initialize Terraform**

Point Terraform at its state in your bucket.

Operation: bash - State list.

**`step_03_t6_plan_the_full_infrastructure(session)` — Run Terraform: init, one saved plan, the apply, the vector index / T6. Plan the full infrastructure**

A saved plan file, after validate and an input check.

Operation: bash - Plan.

**`step_04_t7_apply(session)` — Run Terraform: init, one saved plan, the apply, the vector index / T7. Apply**

Apply that exact plan, then prove nothing is left to change. Run alone, in the same terminal as T6 (the plan file name is only in that shell).

Operation: bash - Apply.

**`step_05_t7_apply(session)` — Run Terraform: init, one saved plan, the apply, the vector index / T7. Apply**

Run alone, in the same terminal as T6 (the plan file name is only in that shell). Confirm nothing is left to change:

Operation: bash - Confirm.

**`step_06_t8_verify_the_vector_index(session)` — Run Terraform: init, one saved plan, the apply, the vector index / T8. Verify the vector index**

The index, the endpoint and the deployed ID, still empty.

Operation: bash - Verify.

### demo_07_restore_the_shell_pin_git_sha_export_the_runtime_settings_and_prepare_the_secret.py

Settings back, Python checked, and the commit every image is built from. Run this first in every new terminal. It restores the settings saved in Phases 1 and 2, activates Python 3.12, loads the repository helpers from commands/session-restart.sh and checks Terraform and the Python dependencies. It changes nothing in the cloud. Ends with PASS: shell restored. A Python STOP means rerun S7; a sign-in error means gcloud auth login, and for Terraform also T2. Now pin GIT_SHA: the exact commit every image is built from and every service is deployed with. The first time, it records the commit you have checked out. After that, it checks the checkout still matches. Its form is the short hash, the one the kit's own make build tags images with (GIT_SHA ?= git rev-parse --short HEAD in the Makefile), so a later make deploy-services or make promote finds these images. Never set GIT_SHA by hand to a value that was not built. If you see the “not the checked-out commit” STOP, choose one of the two options it prints; do not mix images from different commits. Check Python syntax in the build inputs: The runtime settings every deploy reads, from Terraform's outputs. Run only after the full reviewed Terraform plan has been applied. A missing or empty output is a stop condition. This block must run in your main shell (not a subshell) because it exports variables for every later step. Rerun it after any restart. The UI's cookie secret and the chat checkpoint DSN. Terraform creates cookie-secret as an empty holder. The UI and admin services mount :latest, so it needs one enabled version. A permission error must be fixed; it is not evidence that no version exists.

**`step_01_restore_the_shell_and_pin_git_sha(session)` — Restore the shell, pin GIT_SHA, export the runtime settings and prepare the secrets / Restore the shell and pin GIT_SHA**

Settings back, Python checked, and the commit every image is built from. Run this first in every new terminal. It restores the settings saved in Phases 1 and 2, activates Python 3.12, loads the repository helpers from commands/session-restart.sh and checks Terraform and the Python dependencies. It changes nothing in the cloud.

Operation: bash - Restore.

**`step_02_restore_the_shell_and_pin_git_sha(session)` — Restore the shell, pin GIT_SHA, export the runtime settings and prepare the secrets / Restore the shell and pin GIT_SHA**

Ends with PASS: shell restored. A Python STOP means rerun S7; a sign-in error means gcloud auth login, and for Terraform also T2. Now pin GIT_SHA: the exact commit every image is built from and every service is deployed with. The first time, it records the commit you have checked out. After that, it checks the checkout still matches. Its form is the short hash, the one the kit's own make build tags images with (GIT_SHA ?= git rev-parse --short HEAD in the Makefile), so a later make deploy-services or make promote finds these images.

Operation: bash - Pin GIT_SHA.

**`step_03_restore_the_shell_and_pin_git_sha(session)` — Restore the shell, pin GIT_SHA, export the runtime settings and prepare the secrets / Restore the shell and pin GIT_SHA**

Never set GIT_SHA by hand to a value that was not built. If you see the “not the checked-out commit” STOP, choose one of the two options it prints; do not mix images from different commits. Check Python syntax in the build inputs:

Operation: bash - Syntax check.

**`step_04_f1_export_runtime_settings_from_terraform(session)` — Restore the shell, pin GIT_SHA, export the runtime settings and prepare the secrets / F1. Export runtime settings from Terraform state**

The runtime settings every deploy reads, from Terraform's outputs. Run only after the full reviewed Terraform plan has been applied. A missing or empty output is a stop condition. This block must run in your main shell (not a subshell) because it exports variables for every later step. Rerun it after any restart.

Operation: bash - F1.

**`step_05_f1_export_runtime_settings_from_terraform(session)` — Restore the shell, pin GIT_SHA, export the runtime settings and prepare the secrets / F1. Export runtime settings from Terraform state**

The runtime settings every deploy reads, from Terraform's outputs. Run only after the full reviewed Terraform plan has been applied. A missing or empty output is a stop condition. This block must run in your main shell (not a subshell) because it exports variables for every later step. Rerun it after any restart.

Operation: bash - F1 guard.

**`step_06_f2_prepare_cookie_secret_and_the_checkpoin(session)` — Restore the shell, pin GIT_SHA, export the runtime settings and prepare the secrets / F2. Prepare cookie-secret and the checkpoint DSN**

The UI's cookie secret and the chat checkpoint DSN. Terraform creates cookie-secret as an empty holder. The UI and admin services mount :latest, so it needs one enabled version. A permission error must be fixed; it is not evidence that no version exists.

Operation: bash - F2.

### demo_08_gate_the_build_then_build_all_seven_images.py

The kit's own regression tests, before anything is built. Run the regression tests that ship with the pinned commit against the local source. Stop if the task-type, carry-over or repair tests fail. Seven images, all tagged with the same GIT_SHA. First prepare the build-source bucket. On an existing demo the bucket is reused; it is only created when the lookup says it does not exist. First prepare the build-source bucket. On an existing demo the bucket is reused; it is only created when the lookup says it does not exist. Then prepare a fresh temporary build context from the original source directories and cloudbuild.yaml. It excludes Terraform state, providers and plan files. Rerun this block whenever any source file changes. Then prepare a fresh temporary build context from the original source directories and cloudbuild.yaml. It excludes Terraform state, providers and plan files. Rerun this block whenever any source file changes. Build the images. The helper submits one build; the chain runs them in order and stops at the first build that does not report SUCCESS. The UI is built from its own directory because its Dockerfile expects requirements.txt at the context root.

**`step_01_build_gate_regression_tests_and_shared_imp(session)` — Gate the build, then build all seven images / Build gate: regression tests and shared imports**

The kit's own regression tests, before anything is built. Run the regression tests that ship with the pinned commit against the local source. Stop if the task-type, carry-over or repair tests fail.

Operation: bash - Build gate.

**`step_02_f3_build_all_seven_images(session)` — Gate the build, then build all seven images / F3. Build all seven images**

Seven images, all tagged with the same GIT_SHA. First prepare the build-source bucket. On an existing demo the bucket is reused; it is only created when the lookup says it does not exist.

Operation: bash - Build bucket.

**`step_03_f3_build_all_seven_images(session)` — Gate the build, then build all seven images / F3. Build all seven images**

First prepare the build-source bucket. On an existing demo the bucket is reused; it is only created when the lookup says it does not exist. Then prepare a fresh temporary build context from the original source directories and cloudbuild.yaml. It excludes Terraform state, providers and plan files. Rerun this block whenever any source file changes.

Operation: bash - Build context.

**`step_04_f3_build_all_seven_images(session)` — Gate the build, then build all seven images / F3. Build all seven images**

Then prepare a fresh temporary build context from the original source directories and cloudbuild.yaml. It excludes Terraform state, providers and plan files. Rerun this block whenever any source file changes. Build the images. The helper submits one build; the chain runs them in order and stops at the first build that does not report SUCCESS. The UI is built from its own directory because its Dockerfile expects requirements.txt at the context root.

Operation: bash - Build images.

### demo_09_deploy_the_seven_services_the_worker_and_the_api_the_admin_console_chat_the_ui_m.py

The worker Pub/Sub pushes to, and the API every surface calls. The worker Pub/Sub pushes to, and the API every surface calls. Promote the ready API revision. Keep other service updates idle while this runs. The operator console, behind Google sign-in. This deployment creates documind-admin; Terraform and the image build do not. Confirm the project (yours, documind-ai-YOUR-ID) and region (asia-south1), and complete F2 first. The chat memory schema, then the chat backend. services/chat/migrate.py runs PostgresSaver.setup() once in a job; the app never runs the migration on startup. The job execution succeeds. Chat is deployed as the kit's own script deploys it (commands/lesson-12.8.sh): a private service the UI reaches with the person's forwarded IAP assertion (services/frontend/chat.py, shared/iap.py), its callers bound one by one, and then IAP in front of it as well, the same door the UI and the admin console have. The Desk's five eval accounts are bound as soon as Terraform has made them, so make smoke-cases works later. The page people open, behind IAP. The tool server, then the agent that calls it. The MCP server calls the RAG API through shared.documind_tools. The A2A agent calls MCP and contains no shared RAG code.

**`step_01_f4_deploy_the_ingest_worker_and_rag_api(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F4. Deploy the ingest worker and RAG API**

The worker Pub/Sub pushes to, and the API every surface calls.

Operation: bash - Ingest.

**`step_02_f4_deploy_the_ingest_worker_and_rag_api(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F4. Deploy the ingest worker and RAG API**

The worker Pub/Sub pushes to, and the API every surface calls.

Operation: bash - RAG API.

**`step_03_f4_deploy_the_ingest_worker_and_rag_api(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F4. Deploy the ingest worker and RAG API**

The worker Pub/Sub pushes to, and the API every surface calls. Promote the ready API revision. Keep other service updates idle while this runs.

Operation: bash - Promote API.

**`step_04_f5_deploy_the_admin_console_with_iap(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F5. Deploy the admin console with IAP**

The operator console, behind Google sign-in. This deployment creates documind-admin; Terraform and the image build do not. Confirm the project (yours, documind-ai-YOUR-ID) and region (asia-south1), and complete F2 first.

Operation: bash - Admin.

**`step_05_f6_initialize_the_checkpoint_schema_then_d(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F6. Initialize the checkpoint schema, then deploy chat**

The chat memory schema, then the chat backend. services/chat/migrate.py runs PostgresSaver.setup() once in a job; the app never runs the migration on startup.

Operation: bash - Checkpoint job.

**`step_06_f6_initialize_the_checkpoint_schema_then_d(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F6. Initialize the checkpoint schema, then deploy chat**

The chat memory schema, then the chat backend. services/chat/migrate.py runs PostgresSaver.setup() once in a job; the app never runs the migration on startup.

Operation: bash - Rerun existing job (only after review).

**`step_07_f6_initialize_the_checkpoint_schema_then_d(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F6. Initialize the checkpoint schema, then deploy chat**

The job execution succeeds. Chat is deployed as the kit's own script deploys it (commands/lesson-12.8.sh): a private service the UI reaches with the person's forwarded IAP assertion (services/frontend/chat.py, shared/iap.py), its callers bound one by one, and then IAP in front of it as well, the same door the UI and the admin console have. The Desk's five eval accounts are bound as soon as Terraform has made them, so make smoke-cases works later.

Operation: bash - Chat.

**`step_08_f7_deploy_the_ui(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F7. Deploy the UI**

The page people open, behind IAP.

Operation: bash - UI.

**`step_09_f8_deploy_mcp_then_the_a2a_agent(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F8. Deploy MCP, then the A2A agent**

The tool server, then the agent that calls it. The MCP server calls the RAG API through shared.documind_tools. The A2A agent calls MCP and contains no shared RAG code.

Operation: bash - MCP.

**`step_10_f8_deploy_mcp_then_the_a2a_agent(session)` — Deploy the seven services: the worker and the API, the admin console, chat, the UI, MCP and the peer / F8. Deploy MCP, then the A2A agent**

The tool server, then the agent that calls it. The MCP server calls the RAG API through shared.documind_tools. The A2A agent calls MCP and contains no shared RAG code.

Operation: bash - A2A agent.

### demo_10_tenants_put_people_and_services_on_the_rosters.py

So the UI, MCP and chat accounts go on all three golden tenants (acme, zeta and globex), the A2A agent's account on acme only, and the policies become acme any, zeta any, globex in. The command writes to Firestore with your Application Default Credentials; if it fails with a permission error, run gcloud auth application-default login --no-launch-browser again (Phase 2, T2). Preview first. The dry run writes nothing: Preview first. The dry run writes nothing: Now write it. The command adds members only to the tenant named by --tenant, so put yourself on each tenant in turn. Repeating the service-account entries is harmless: each one is the same Firestore document every time. Each pass prints one ... is on <tenant> line per member and service account, then acme: data_region=any, zeta: data_region=any and globex: data_region=in. Read the rosters back from Firestore, the same documents the API checks on every request: Your email and documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com appear under every tenant; documind-agent-sa appears under acme only. To let a colleague in, they need both the door and the list: IAP access on the UI, and a place on the tenant they work in. Add several at once with a comma-separated list.

**`step_01_tenants_put_people_and_services_on_the_ros(session)` — Tenants: put people and services on the rosters / Tenants: put people and services on the rosters**

So the UI, MCP and chat accounts go on all three golden tenants (acme, zeta and globex), the A2A agent's account on acme only, and the policies become acme any, zeta any, globex in. The command writes to Firestore with your Application Default Credentials; if it fails with a permission error, run gcloud auth application-default login --no-launch-browser again (Phase 2, T2). Preview first. The dry run writes nothing:

Operation: bash - the roster plan, written nowhere.

Expected shape, not a promised result:

```text
would put you@your-domain on acme
would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
...
would put documind-agent-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
would set acme: data_region=any
would set zeta: data_region=any
would set globex: data_region=in
```

**`step_02_tenants_put_people_and_services_on_the_ros(session)` — Tenants: put people and services on the rosters / Tenants: put people and services on the rosters**

Preview first. The dry run writes nothing: Now write it. The command adds members only to the tenant named by --tenant, so put yourself on each tenant in turn. Repeating the service-account entries is harmless: each one is the same Firestore document every time.

Operation: bash - you on all three tenants.

**`step_03_tenants_put_people_and_services_on_the_ros(session)` — Tenants: put people and services on the rosters / Tenants: put people and services on the rosters**

Each pass prints one ... is on <tenant> line per member and service account, then acme: data_region=any, zeta: data_region=any and globex: data_region=in. Read the rosters back from Firestore, the same documents the API checks on every request:

Operation: bash - who is on each roster.

**`step_04_tenants_put_people_and_services_on_the_ros(session)` — Tenants: put people and services on the rosters / Tenants: put people and services on the rosters**

Your email and documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com appear under every tenant; documind-agent-sa appears under acme only. To let a colleague in, they need both the door and the list: IAP access on the UI, and a place on the tenant they work in. Add several at once with a comma-separated list.

Operation: bash - a colleague: IAP access plus one roster.

### demo_11_finish_what_make_up_finishes_the_index_wait_the_managed_stores_and_the_bigquery.py

The kit's own make up does not stop at the deploy. Its recipe names what follows, and this runbook has done most of it by hand: the drift check in T7, the cookie secret in F2, the builds in F3, the deploys in F4 to F8 and the roster in the step before this one: Four remain, and they are the kit's targets, run as they are. wait-index blocks until Firestore's composite indexes leave CREATING. managed-stores switches RAG Engine on once for the project, makes a corpus for each tenant whose text may travel (acme and zeta) and pins acme to rag_engine and zeta to vertex_search, so one deployment answers from all three stores; the data stores themselves were declared by Terraform (managed_search=true). bq-views-when-ready creates the usage views the admin console reads, once the table they read exists: the log sink's table appears only after the API has answered a first request, so on a new lane it prints that the views are deferred and you create them after the first answer (step 13). vector-status prints the index's own vector count, 0 until the first document is ingested. These targets read the state Phase 2 wrote, because the bucket and prefix are the kit's.

**`step_01_finish_what_make_up_finishes_the_index_wai(session)` — Finish what make up finishes: the index wait, the managed stores and the BigQuery views / Finish what make up finishes: the index wait, the managed stores and the BigQuery views**

The kit's own make up does not stop at the deploy. Its recipe names what follows, and this runbook has done most of it by hand: the drift check in T7, the cookie secret in F2, the builds in F3, the deploys in F4 to F8 and the roster in the step before this one: Four remain, and they are the kit's targets, run as they are. wait-index blocks until Firestore's composite indexes leave CREATING. managed-stores switches RAG Engine on once for the project, makes a corpus for each tenant whose text may travel (acme and zeta) and pins acme to rag_engine and zeta to vertex_search, so one deployment answers from all three stores; the data stores themselves were declared by Terraform (managed_search=true). bq-views-when-ready creates the usage views the admin console reads, once the table they read exists: the log sink's table appears only after the API has answered a first request, so on a new lane it prints that the views are deferred and you create them after the first answer (step 13). vector-status prints the index's own vector count, 0 until the first document is ingested. These targets read the state Phase 2 wrote, because the bucket and prefix are the kit's.

Operation: bash - the four closing targets, from the kit root.

### demo_12_verify_all_seven_services.py

Seven services, Ready, on one tag. Every service must be Ready and running an image tagged with the same $GIT_SHA.

**`step_01_verify_all_seven_services(session)` — Verify all seven services / Verify all seven services**

Seven services, Ready, on one tag. Every service must be Ready and running an image tagged with the same $GIT_SHA.

Operation: bash - Verify.

### demo_13_open_the_ui_and_ask_a_first_question.py

The end-to-end check a person makes. Print the UI's address and open it in a browser signed in as your operator account: A 403 after you signed in means the roster, not IAP: rerun the tenants step and read the rosters back. A first-time IAP setup on a project without an organization may also ask for the OAuth consent screen in the console (Cloud Run, the service, Security, Identity-Aware Proxy); complete it there and retry the failed command. Never switch authentication off to make the page load. That first answer is what the usage views were waiting for: the log sink has now exported the API's first rows, so BigQuery has the table the views read. Create them, from the kit root:

**`step_01_open_the_ui_and_ask_a_first_question(session)` — Open the UI and ask a first question / Open the UI and ask a first question**

The end-to-end check a person makes. Print the UI's address and open it in a browser signed in as your operator account:

Operation: bash - the UI's address.

**`step_02_open_the_ui_and_ask_a_first_question(session)` — Open the UI and ask a first question / Open the UI and ask a first question**

A 403 after you signed in means the roster, not IAP: rerun the tenants step and read the rosters back. A first-time IAP setup on a project without an organization may also ask for the OAuth consent screen in the console (Cloud Run, the service, Security, Identity-Aware Proxy); complete it there and retry the failed command. Never switch authentication off to make the page load. That first answer is what the usage views were waiting for: the log sink has now exported the API's first rows, so BigQuery has the table the views read. Create them, from the kit root:

Operation: bash - the usage views, after the first answer.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_0.5_Setup_Cloud_WIX.html`. All 59 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `d125af97fa93a38ec6b6abb8e4706f9be0d783fa`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
