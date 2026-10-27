# Lesson 11.1: Build and deploy using keyless identity

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: set up the shell |
| 3 | [demo_03_your_fork_and_your_project_as_github_and_the_console_show_them.py](demo_03_your_fork_and_your_project_as_github_and_the_console_show_them.py) | Your fork and your project, as GitHub and the console show them |
| 5 | [demo_05_four_variables_from_your_lane_and_a_person_in_front_of_production.py](demo_05_four_variables_from_your_lane_and_a_person_in_front_of_production.py) | Four variables from your lane, and a person in front of production |
| 6 | [demo_06_a_build_and_a_deploy_from_main_with_no_key.py](demo_06_a_build_and_a_deploy_from_main_with_no_key.py) | A build and a deploy from main, with no key |
| 7 | [demo_07_a_branch_dispatch_refused_at_the_auth_step.py](demo_07_a_branch_dispatch_refused_at_the_auth_step.py) | A branch dispatch, refused at the auth step |
| 8 | [demo_08_what_google_holds_and_who_did_what.py](demo_08_what_google_holds_and_who_did_what.py) | What Google holds, and who did what |

## Before starting

Select `/home/user/rag-shell-venv/bin/python`. Run `workshop_demos/setup/bootstrap.py` once and edit `workshop_demos/setup/config/settings.local.json`. The helper sets the working directory and resolves project/API settings; terminal exports are unnecessary.

The shared workshop setup and the deployed/local inputs described in the reading guide.

Each demo contains named Python functions in teaching order. Set breakpoints in those functions. Kit CLI operations stay visible as command constants; Python calls use this interpreter. Repeated session, authentication, configuration and command handling live in `workshop_demos/setup/workshop_helpers/`.

## Resume and recovery

Completed functions are saved and skipped when an unfinished demo is run again. A failed/interrupted function may have made partial changes: inspect its attempt under `workshop_demos/results/`, repair the cause, then set `RETRY_FAILED_STEP = True` in that demo to retry only unfinished functions. `REPEAT = True` deliberately replays the entire file. It is not a repair shortcut.

Manual browser actions and long asynchronous waits pause at a named checkpoint. Type `done` only after performing the action. Stopping there retains completed steps so they are not repeated on resume. This acknowledgement alone is not proof that indexing/monitoring succeeded; inspect the following read.

After upgrading from a previous layout, run the lesson's finish file first, then set this lesson number in `workshop_demos/setup/start_new_session.py` and run it. It archives evidence; it does not delete your fixtures. Old progress is never silently treated as completion of the new section files.

## Conditional recovery

- [recovery/demo_09_what_may_stop_the_first_dispatch_the_trust_that_cannot_move_and_the_path_without.py](recovery/demo_09_what_may_stop_the_first_dispatch_the_trust_that_cannot_move_and_the_path_without.py) — The workflow's two release steps are make targets, and you can run them from the operator shell as yourself: the same image built by Cloud Build, the same revision with no traffic and the tag candidate. It proves the build and the deploy, not the keyless identity, because your own sign-in makes both calls. It also moves the candidate tag to the revision it makes, so run it only if step 6 could not run.

## Finish and restore

- [setup/restore_settings.py](setup/restore_settings.py) — At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's dispatch runs the live gate on the candidate it makes, and the gate asks acme's golden rows; run it as lesson 4.3 ran its gate, with acme on the kit's own index, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.
- [setup/finish.py](setup/finish.py) — Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Functions, observations and effects

The numbered functions below correspond to the source examples. Numerical sample output is illustrative. These files have offline/source checks; live IAM, ingestion, model output and deployed resources must be verified in your workstation.

### setup/prepare.py

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's dispatch runs the live gate on the candidate it makes, and the gate asks acme's golden rows; run it as lesson 4.3 ran its gate, with acme on the kit's own index, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's dispatch runs the live gate on the candidate it makes, and the gate asks acme's golden rows; run it as lesson 4.3 ran its gate, with acme on the kit's own index, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors.

Operation: bash — run in the operator shell now, before the lesson's first step.

IDE adaptation: Save the actual previous pin before selecting vector; cleanup restores it instead of assuming rag_engine.

Expected shape, not a promised result:

```text
acme: retrieval_backend=vector
```

### demo_03_your_fork_and_your_project_as_github_and_the_console_show_them.py

The cell reads the trust from the inputs file and exports the repository as GH_REPO, which every later cell uses. Then it asks GitHub about that repository: whether it is public and a fork, its numeric id, and the state of its workflows.

**`step_01_what_your_lane_trusts_and_what_github_says(session)` — Your fork and your project, as GitHub and the console show them / Do it: what your lane trusts, and what GitHub says about it**

The cell reads the trust from the inputs file and exports the repository as GH_REPO, which every later cell uses. Then it asks GitHub about that repository: whether it is public and a fork, its numeric id, and the state of its workflows.

Operation: bash — run in the operator shell, in the kit (reads one local file, then GitHub; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/fork_check.txt]
```

### demo_05_four_variables_from_your_lane_and_a_person_in_front_of_production.py

Do it: the first make ci-vars The cell creates production through GitHub's REST API with you as its one required reviewer (in the browser: Settings > Environments > New environment, then Required reviewers). It runs make ci-vars again, pipes the four lines it printed into the shell, and reads back what the repository now holds. A shell that never exported REGION sends the Makefile's default. The kit refuses it before any tool runs:

**`step_01_the_first_make_ci_vars(session)` — Four variables from your lane, and a person in front of production / Do it: the first make ci-vars**

Do it: the first make ci-vars

Operation: bash — run in the operator shell, in the kit (terraform output and one GitHub read; writes nothing).

Expected shape, not a promised result:

```text
# documind-cd.yml reads 4 repository variables. Set them on YOUR-GITHUB-USER/YOUR-REPO, the repository wif.tf trusts:
gh variable set GCP_PROJECT --repo YOUR-GITHUB-USER/YOUR-REPO --body documind-ai-YOUR-ID
gh variable set GCP_REGION --repo YOUR-GITHUB-USER/YOUR-REPO --body asia-south1
gh variable set WIF_PROVIDER --repo YOUR-GITHUB-USER/YOUR-REPO --body projects/NUMBER/locations/global/workloadIdentityPools/documind-github/providers/github-oidc
gh variable set CICD_SERVICE_ACCOUNT --repo YOUR-GITHUB-USER/YOUR-REPO --body sa-documind-cicd@documind-ai-YOUR-ID.iam.gserviceaccount.com
# The trust (wif.tf): YOUR-GITHUB-USER/YOUR-REPO, id REPO_ID, ref refs/heads/main. A run from any other ref is refused at the auth step.
# Dispatch from that branch, on the candidate path - path=clouddeploy would replace documind-api's settings with run-service.yaml's:
#   gh workflow run documind-cd.yml --repo YOUR-GITHUB-USER/YOUR-REPO --ref main -f path=candidate
WARNING: YOUR-GITHUB-USER/YOUR-REPO has no production environment, or gh's account cannot see the repository. GitHub creates the environment the first time a job names it, with no required reviewer, and promote would then move traffic with nobody approving. Create it with a reviewer before the first dispatch: Settings > Environments > production > Required reviewers (on a private repository, required reviewers need a paid GitHub plan)
```

**`step_02_a_reviewer_then_the_variables(session)` — Four variables from your lane, and a person in front of production / Do it: a reviewer, then the variables**

The cell creates production through GitHub's REST API with you as its one required reviewer (in the browser: Settings > Environments > New environment, then Required reviewers). It runs make ci-vars again, pipes the four lines it printed into the shell, and reads back what the repository now holds.

Operation: bash — run in the operator shell, in the kit (writes to your fork: one environment, four variables).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/gh_setup.txt]
```

**`step_03_change_it_the_makefile_s_region(session)` — Four variables from your lane, and a person in front of production / Change it: the Makefile's region**

A shell that never exported REGION sends the Makefile's default. The kit refuses it before any tool runs:

Operation: bash — run in the operator shell, in the kit, if you want to see the refusal (nothing runs).

IDE adaptation: Run with the page's shell semantics: the page's expected output shows a command in this cell failing (a refusal, a red check, an oracle's FAIL), which is the cell's answer. Every line runs, a put-back line included, and the step ends green; compare the output with the expected window.

Expected shape, not a promised result:

```text
STOP: REGION is us-central1, but lane documind-ai-YOUR-ID was planned in asia-south1 (runbook-project.auto.tfvars.json), where its image repository and services are: make ci-vars PROJECT=documind-ai-YOUR-ID REGION=asia-south1
```

### demo_06_a_build_and_a_deploy_from_main_with_no_key.py

The cell starts the run, finds its id, prints its page, waits until release-candidate has finished, and prints the run's summary. Open the page while it waits and watch the jobs and their steps. In the browser the same start is Actions > documind-cd > Run workflow, on main, with candidate as the path. On the run's page: Review deployments, tick production, then Reject. The cell does the same through GitHub's REST API, as the reviewer: The cell reads documind-api's traffic and the candidate revision, then asks GitHub which commit the run built and how the run ended.

**`step_01_dispatch_and_wait_for_the_build_and_the_ga(session)` — A build and a deploy from main, with no key / Do it: dispatch, and wait for the build and the gate**

The cell starts the run, finds its id, prints its page, waits until release-candidate has finished, and prints the run's summary. Open the page while it waits and watch the jobs and their steps. In the browser the same start is Actions > documind-cd > Run workflow, on main, with candidate as the path.

Operation: bash — run in the operator shell (starts one run on your fork, then waits about fifteen minutes).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/run_main.txt]
```

**`step_02_say_no_at_promote(session)` — A build and a deploy from main, with no key / Do it: say no at promote**

On the run's page: Review deployments, tick production, then Reject. The cell does the same through GitHub's REST API, as the reviewer:

Operation: bash — run in the operator shell, or press Reject on the run's page (a person's no).

**`step_03_what_the_run_left_on_cloud_run(session)` — A build and a deploy from main, with no key / Do it: what the run left on Cloud Run**

The cell reads documind-api's traffic and the candidate revision, then asks GitHub which commit the run built and how the run ended.

Operation: bash — run in the operator shell, in the kit (two Cloud Run reads and two GitHub reads; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/candidate.txt]
```

### demo_07_a_branch_dispatch_refused_at_the_auth_step.py

The cell makes a branch at main's commit through GitHub's REST API, dispatches the workflow on it, waits for the run to finish, prints its summary and the error lines of the failed step, and deletes the branch. In the browser: the branch menu on your fork's code page, then Run workflow with that branch chosen.

**`step_01_a_branch_a_run_a_refusal(session)` — A branch dispatch, refused at the auth step / Do it: a branch, a run, a refusal**

The cell makes a branch at main's commit through GitHub's REST API, dispatches the workflow on it, waits for the run to finish, prints its summary and the error lines of the failed step, and deletes the branch. In the browser: the branch menu on your fork's code page, then Run workflow with that branch chosen.

Operation: bash — run in the operator shell (a branch, a run that fails on purpose, the branch deleted).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/run_branch.txt]
```

### demo_08_what_google_holds_and_who_did_what.py

Do it: the trust and the binding, from IAM's REST API Do it: the audit trail of step 6's run Do it: zero user-managed keys

**`step_01_the_trust_and_the_binding_from_iam_s_rest(session)` — What Google holds, and who did what / Do it: the trust and the binding, from IAM's REST API**

Do it: the trust and the binding, from IAM's REST API

Operation: bash — run in the operator shell (three IAM REST reads; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/iam_rest.txt]
```

**`step_02_the_audit_trail_of_step_6_s_run(session)` — What Google holds, and who did what / Do it: the audit trail of step 6's run**

Do it: the audit trail of step 6's run

Operation: bash — run in the operator shell (one Cloud Logging read; writes nothing).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/audit.txt]
```

**`step_03_zero_user_managed_keys(session)` — What Google holds, and who did what / Do it: zero user-managed keys**

Do it: zero user-managed keys

Operation: bash — run in the operator shell, in the kit (gcloud describe and list calls; writes nothing).

IDE adaptation: Run with the page's shell semantics: the cell prints its own exit status after a command (cmd; echo "exit $?"), and the page's prose says which commands here fail on purpose. Its expected output is not recorded yet, so the demo cannot read the failure from it. Every line runs, a put-back line included, and the step ends green; compare the printed status with the page.

Expected shape, not a promised result:

```text
[awaiting the author's run: data/keys.txt]
```

### recovery/demo_09_what_may_stop_the_first_dispatch_the_trust_that_cannot_move_and_the_path_without.py

The workflow's two release steps are make targets, and you can run them from the operator shell as yourself: the same image built by Cloud Build, the same revision with no traffic and the tag candidate. It proves the build and the deploy, not the keyless identity, because your own sign-in makes both calls. It also moves the candidate tag to the revision it makes, so run it only if step 6 could not run.

**`step_01_without_github_the_local_operator_path(session)` — What may stop the first dispatch, the trust that cannot move, and the path without GitHub / Without GitHub: the local operator path**

The workflow's two release steps are make targets, and you can run them from the operator shell as yourself: the same image built by Cloud Build, the same revision with no traffic and the tag candidate. It proves the build and the deploy, not the keyless identity, because your own sign-in makes both calls. It also moves the candidate tag to the revision it makes, so run it only if step 6 could not run.

Operation: bash — run in the operator shell, in the kit, only if you could not dispatch (a build, and a candidate as you).

Expected shape, not a promised result:

```text
>> building asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:COMMIT from services/rag-api
...
gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --image asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/api:COMMIT --no-traffic --tag candidate --update-env-vars GIT_SHA=COMMIT --quiet
...
>> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
>> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app  (make eval-live API=that, then make promote)
```

### setup/restore_settings.py

At lesson end: DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's dispatch runs the live gate on the candidate it makes, and the gate asks acme's golden rows; run it as lesson 4.3 ran its gate, with acme on the kit's own index, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

**`step_01_which_store_answers_acme_pin_it_to_the_kit(session)` — Before you run anything: set up the shell / Which store answers acme? Pin it to the kit's own index for this lesson**

DocuMind can answer a tenant's questions from four stores: its own Vector Search index (the ANN tier), the Firestore rung beneath it, or two managed mirrors, Vertex AI RAG Engine and Vertex AI Search. make up pins acme to RAG Engine and zeta to Vertex AI Search so every store the course teaches is exercised. A managed store holds the text of every current version, but not the kit's addresses: its citations come back with ids like acme:acme_497809ff...#rag-532341da71fe, a page of null even for a PDF, and stages.retrieval_backend: rag_engine. This lesson's dispatch runs the live gate on the candidate it makes, and the gate asks acme's golden rows; run it as lesson 4.3 ran its gate, with acme on the kit's own index, and put the pin back at the end. Module 2 compares the four stores; Module 7 studies the mirrors. The pin back is a separate window on purpose: pasted together with the line above, it would put acme straight back on RAG Engine before the lesson began. Leave it until the lesson's last step is done.

Operation: bash — run in the operator shell when you finish the lesson, not now.

IDE adaptation: Run at lesson end despite its early HTML position, as the source label explicitly instructs.

### setup/finish.py

Run the listed cleanup sections in order, even after a failure; retain evidence and restore saved settings.

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_11.1_Keyless_Deploy_WIX.html`. All 45 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `b6503d98ae36784f66986f9b9ccf0d61b9e9b167`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
