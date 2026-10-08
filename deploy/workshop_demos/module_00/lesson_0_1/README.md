# Lesson 0.1: Set up the Google Cloud billing account, budget and project

## What to run

Run one complete experiment at a time with the IDE Run/Debug button. Keep the files in the order below; do not use Run All.

The number after `demo_` is the visible HTML section number, not the demo count or Level number. Gaps mean the intervening section is reading/UI-only. Unnumbered HTML setup stays in `setup/prepare.py`. At lesson end, `setup/finish.py` runs the numbered cleanup sections and restores saved settings; completed cleanup sections are skipped.

| HTML section | File | What it demonstrates |
|---|---|---|
| setup | [setup/prepare.py](setup/prepare.py) | Before you run anything: open Cloud Shell |
| 3 | [demo_03_the_billing_account_free_trial_or_paid.py](demo_03_the_billing_account_free_trial_or_paid.py) | The billing account: free trial or paid |
| 4 | [demo_04_the_project_create_it_link_it_make_it_the_default.py](demo_04_the_project_create_it_link_it_make_it_the_default.py) | The project: create it, link it, make it the default |
| 5 | [demo_05_the_apis_40_services_in_two_calls.py](demo_05_the_apis_40_services_in_two_calls.py) | The APIs: 40 services in two calls |
| 6 | [demo_06_the_budget_an_alert_on_the_billing_account.py](demo_06_the_budget_an_alert_on_the_billing_account.py) | The budget: an alert on the billing account |
| 8 | [demo_08_the_standing_cost_what_bills_by_the_hour_per_day_and_per_weekend.py](demo_08_the_standing_cost_what_bills_by_the_hour_per_day_and_per_weekend.py) | The standing cost: what bills by the hour, per day and per weekend |
| 9 | [demo_09_verify_it_yourself_the_checklist.py](demo_09_verify_it_yourself_the_checklist.py) | Verify it yourself: the checklist |

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

This lesson needs a Google account, a browser, and a shell where the gcloud CLI acts as you. Cloud Shell is the simplest: a terminal in the browser, on a Debian machine Google provisions for you, with the gcloud CLI already installed and 5 GB of free persistent disk as your home directory. Open the Google Cloud console at console.cloud.google.com, sign in with the Google account you will use for the whole course, and click Activate Cloud Shell, the terminal icon at the top right. A laptop works too, if the gcloud CLI is installed and signed in; lesson 0.2 sets a laptop up properly. Nothing on this page needs the kit: there is no clone yet, no Python environment and no lane, and every command here costs Rs 0. Run the block below once per session. It prints gcloud's version, the account it acts as, and its default project, which stays empty until step 4 sets it.

**`step_01_before_you_run_anything_open_cloud_shell(session)` — Before you run anything: open Cloud Shell / Before you run anything: open Cloud Shell**

This lesson needs a Google account, a browser, and a shell where the gcloud CLI acts as you. Cloud Shell is the simplest: a terminal in the browser, on a Debian machine Google provisions for you, with the gcloud CLI already installed and 5 GB of free persistent disk as your home directory. Open the Google Cloud console at console.cloud.google.com, sign in with the Google account you will use for the whole course, and click Activate Cloud Shell, the terminal icon at the top right. A laptop works too, if the gcloud CLI is installed and signed in; lesson 0.2 sets a laptop up properly. Nothing on this page needs the kit: there is no clone yet, no Python environment and no lane, and every command here costs Rs 0. Run the block below once per session. It prints gcloud's version, the account it acts as, and its default project, which stays empty until step 4 sets it.

Operation: bash — run in Cloud Shell, once per session (or in a terminal where gcloud is signed in).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/setup_check.txt]
```

### demo_03_the_billing_account_free_trial_or_paid.py

One command lists every billing account your Google account can see. The one you want says True under OPEN; its ACCOUNT_ID is what step 4 links the project to.

**`step_01_find_it_with_gcloud(session)` — The billing account: free trial or paid / Find it with gcloud**

One command lists every billing account your Google account can see. The one you want says True under OPEN; its ACCOUNT_ID is what step 4 links the project to.

Operation: bash — run in Cloud Shell (read-only).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/billing_accounts.txt]
```

### demo_04_the_project_create_it_link_it_make_it_the_default.py

Put your account ID from step 3 and your project ID in the first two lines, then paste the block. --set-as-default makes the new project gcloud's default, so every later command in this session finds it without being told, and so do the Basics pages, which read it with gcloud config get-value project.

**`step_01_with_gcloud(session)` — The project: create it, link it, make it the default / With gcloud**

Put your account ID from step 3 and your project ID in the first two lines, then paste the block. --set-as-default makes the new project gcloud's default, so every later command in this session finds it without being told, and so do the Basics pages, which read it with gcloud config get-value project.

Operation: bash — run in Cloud Shell, once (put your own account id and project id in the first two lines).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/project_link.txt]
```

### demo_05_the_apis_40_services_in_two_calls.py

An API, in Google Cloud's sense, is a product switched on for one project: Cloud Run, Firestore, Vertex AI. Until it is enabled, every call to it from that project is refused, whoever makes it, with a message that names the API. Enabling costs nothing; using is what bills. The kit needs 40 of them before Terraform can create anything, and keeps the list in one block of commands/lesson-12.1.sh, the one marked ENABLE_APIS. It is two calls rather than one because the Service Usage API takes at most 20 services per request, as the block's own comment records. make apis runs that block unchanged: You have no clone yet, so you paste the same lines. They are the block exactly, taken from the kit when this page was built: the first sets gcloud's project, which step 4 already did, and the next two enable the list. A short loop compares the project's enabled services with the kit's list and names any that is missing. Run it now, and again whenever a later lesson's command complains that an API is disabled.

**`step_01_definition(session)` — The APIs: 40 services in two calls / Definition**

An API, in Google Cloud's sense, is a product switched on for one project: Cloud Run, Firestore, Vertex AI. Until it is enabled, every call to it from that project is refused, whoever makes it, with a message that names the API. Enabling costs nothing; using is what bills. The kit needs 40 of them before Terraform can create anything, and keeps the list in one block of commands/lesson-12.1.sh, the one marked ENABLE_APIS. It is two calls rather than one because the Service Usage API takes at most 20 services per request, as the block's own comment records. make apis runs that block unchanged: You have no clone yet, so you paste the same lines. They are the block exactly, taken from the kit when this page was built: the first sets gcloud's project, which step 4 already did, and the next two enable the list.

Operation: bash — run in Cloud Shell, once (the kit's ENABLE_APIS block: 40 APIs in 2 calls).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/apis_enable.txt]
```

**`step_02_count_them(session)` — The APIs: 40 services in two calls / Count them**

A short loop compares the project's enabled services with the kit's list and names any that is missing. Run it now, and again whenever a later lesson's command complains that an API is disabled.

Operation: bash — run in Cloud Shell (read-only).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/apis_check.txt]
```

### demo_06_the_budget_an_alert_on_the_billing_account.py

The Budget API answers for the same budget. --billing-project makes the call count against your project, where step 5 enabled the Budget API (the kit's helper names a quota project for its own gcloud calls in the same way); the filter picks yours out of any others on the account, and the format keeps the fields the console asked about.

**`step_01_back_with_gcloud(session)` — The budget: an alert on the billing account / Read it back with gcloud**

The Budget API answers for the same budget. --billing-project makes the call count against your project, where step 5 enabled the Budget API (the kit's helper names a quota project for its own gcloud calls in the same way); the filter picks yours out of any others on the account, and the format keeps the fields the console asked about.

Operation: bash — run in Cloud Shell after the console steps (read-only).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/budgets_list.txt]
```

### demo_08_the_standing_cost_what_bills_by_the_hour_per_day_and_per_weekend.py

The same table as a Python cell: the hourly prices, the kit's rate and the kit's budget, then the sums. It touches no account and no network, so it runs anywhere a python does, Cloud Shell included.

**`step_01_run_the_arithmetic_yourself_rs_0(session)` — The standing cost: what bills by the hour, per day and per weekend / Run the arithmetic yourself, Rs 0**

The same table as a Python cell: the hourly prices, the kit's rate and the kit's budget, then the sums. It touches no account and no network, so it runs anywhere a python does, Cloud Shell included.

Operation: bash — run in Cloud Shell (a Python cell, arithmetic only: no network, no credentials, Rs 0).

Expected shape, not a promised result:

```text
small  shard: USD 0.5182 an hour = Rs 1,057 a day, Rs 2,114 a weekend, Rs 32,157 a month
              the budget's 50% (Rs 2,500) after 57 hours of this alone
medium shard: USD 1.3070 an hour = Rs 2,666 a day, Rs 5,333 a weekend, Rs 81,100 a month
              the budget's 50% (Rs 2,500) after 23 hours of this alone
```

### demo_09_verify_it_yourself_the_checklist.py

Eight checks, each one block above, each with the value that proves it on your account. One more read-only block first: the project's billing information, the record the kit's helper reads in step 7, and gcloud's default project.

**`step_01_verify_it_yourself_the_checklist(session)` — Verify it yourself: the checklist / Verify it yourself: the checklist**

Eight checks, each one block above, each with the value that proves it on your account. One more read-only block first: the project's billing information, the record the kit's helper reads in step 7, and gcloud's default project.

Operation: bash — run in Cloud Shell (read-only).

Expected shape, not a promised result:

```text
[awaiting the author's run: data/verify.txt]
```

## Source and coverage

[Reading guide](GUIDE.md) retains explanatory prose and UI instructions from the lesson's main page, `Netsetos_GCP_Capstone_0.1_Billing_Project_WIX.html`. All 32 original windows are accounted for in `lesson_map.json`: executable steps, shared setup, or read-only examples. Reviewed source: `e8752816c7f6df23f638d88cde838439debb5a23`.

Source line numbers refer to the teaching HTML before generated IDE-link blocks. Use the numbered section anchor/heading to find the example in the rendered page; its link opens this same learner file.
