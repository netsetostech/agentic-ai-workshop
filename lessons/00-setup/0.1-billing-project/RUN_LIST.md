# Lesson 0.1 - the author's run list

The page shows seven outputs only a live run can print. Until each is recorded, the page carries a marked stand-in
(`[awaiting the author's run: data/<file>]`), `python pagekit/build.py 0.1` names the files still awaited, and
`python pagekit/check_lesson.py 0.1` notes the count (a note, not a finding). Everything else on the page, the
standing cost and the meter included, is computed at build time and needs no run.

## Before you start

- **Where:** Cloud Shell (console.cloud.google.com, *Activate Cloud Shell*), signed in as the Google account that
  holds the billing account you want the course to show. One session for the whole list: steps 4 to 9 use the
  `BILLING` and `PROJECT` that step 4 exports.
- **Cost:** Rs 0 for every block below. Listing accounts, creating a project, linking billing, enabling APIs and
  reading a budget bill nothing; no resource is created.
- **A new project, named `documind-ai-...`:** the commands create one. Its ID must start with `documind-ai-` so the
  build's redaction replaces it (a `documind-ai-live-NNNN` name works). It can stay afterwards as the blank project
  lesson 0.3's recorded `make up` starts from.
- **To record a run:** copy what the terminal printed after the block (not the prompt, not the command) into
  `lessons/00-setup/0.1-billing-project/data/<file>`, UTF-8 with LF line endings, then
  `python pagekit/build.py 0.1` and `python pagekit/check_lesson.py 0.1`.
- **What the build redacts** in every file it reads from `data/`: billing account ids become
  `XXXXXX-XXXXXX-XXXXXX`, `documind-ai-...` project ids become `documind-ai-YOUR-ID`, runs of ten or more digits
  (project and operation numbers) become `NUMBER`, email addresses become `you@example.com`. It does not touch a
  billing account's display name: if the NAME column of run 2 carries a personal name, change it in the file to
  `My Billing Account`. The leak scan in `check_lesson.py` fails the page if a real id, number or mailbox is left.

## The runs, in order

| # | Page step | What | Data file | Cost |
|---|---|---|---|---|
| 1 | setup | gcloud's version, account, default project | `setup_check.txt` | Rs 0 |
| 2 | 3 | `gcloud billing accounts list` | `billing_accounts.txt` | Rs 0 |
| 3 | 4 | create the project, set it as default, link billing | `project_link.txt` | Rs 0 |
| 4 | 5 | enable the kit's 40 APIs (its ENABLE_APIS block) | `apis_enable.txt` | Rs 0 |
| 5 | 5 | count them | `apis_check.txt` | Rs 0 |
| - | 6 | the budget, in the console (no file) | - | Rs 0 |
| 6 | 6 | read the budget back | `budgets_list.txt` | Rs 0 |
| 7 | 9 | the project's billing info and gcloud's default project | `verify.txt` | Rs 0 |

### 1. `setup_check.txt` (the setup section)

```bash
gcloud --version | head -n 1
gcloud config get-value account
gcloud config get-value project
```

### 2. `billing_accounts.txt` (step 3)

```bash
gcloud billing accounts list
```

### 3. `project_link.txt` (step 4)

Put the open account's ACCOUNT_ID from run 2 and the new project's ID in the first two lines.

```bash
export BILLING=XXXXXX-XXXXXX-XXXXXX     # yours: the ACCOUNT_ID of the OPEN account in the list above
export PROJECT=documind-ai-YOUR-ID      # yours: 6 to 30 characters, lower case, digits and hyphens, a letter first
gcloud projects create "$PROJECT" --name="DocuMind lane" --set-as-default
gcloud billing projects link "$PROJECT" --billing-account="$BILLING"
```

### 4. `apis_enable.txt` (step 5)

The kit's ENABLE_APIS block from `deploy/commands/lesson-12.1.sh`, as the page shows it (the build generates the
window from the kit; if the kit's block changes, copy the window from the rebuilt page instead).

```bash
gcloud config set project $PROJECT
gcloud services enable \
  run.googleapis.com \
  compute.googleapis.com \
  vpcaccess.googleapis.com \
  pubsub.googleapis.com \
  artifactregistry.googleapis.com \
  secretmanager.googleapis.com \
  firestore.googleapis.com \
  storage.googleapis.com \
  aiplatform.googleapis.com \
  documentai.googleapis.com \
  vision.googleapis.com \
  language.googleapis.com \
  translate.googleapis.com \
  speech.googleapis.com \
  texttospeech.googleapis.com \
  dlp.googleapis.com \
  iap.googleapis.com \
  iamcredentials.googleapis.com \
  cloudbuild.googleapis.com \
  orgpolicy.googleapis.com
gcloud services enable \
  cloudtrace.googleapis.com \
  monitoring.googleapis.com \
  logging.googleapis.com \
  billingbudgets.googleapis.com \
  bigquery.googleapis.com \
  discoveryengine.googleapis.com \
  dataplex.googleapis.com \
  sqladmin.googleapis.com \
  eventarc.googleapis.com \
  workflows.googleapis.com \
  cloudscheduler.googleapis.com \
  cloudfunctions.googleapis.com \
  modelarmor.googleapis.com \
  cloudbilling.googleapis.com \
  cloudresourcemanager.googleapis.com \
  serviceusage.googleapis.com \
  vectorsearch.googleapis.com \
  spanner.googleapis.com \
  container.googleapis.com \
  clouddeploy.googleapis.com
```

### 5. `apis_check.txt` (step 5)

```bash
enabled="$(gcloud services list --enabled --project "$PROJECT" --format='value(config.name)')"
missing=0
for api in run.googleapis.com compute.googleapis.com vpcaccess.googleapis.com pubsub.googleapis.com artifactregistry.googleapis.com \
           secretmanager.googleapis.com firestore.googleapis.com storage.googleapis.com aiplatform.googleapis.com documentai.googleapis.com \
           vision.googleapis.com language.googleapis.com translate.googleapis.com speech.googleapis.com texttospeech.googleapis.com \
           dlp.googleapis.com iap.googleapis.com iamcredentials.googleapis.com cloudbuild.googleapis.com orgpolicy.googleapis.com \
           cloudtrace.googleapis.com monitoring.googleapis.com logging.googleapis.com billingbudgets.googleapis.com bigquery.googleapis.com \
           discoveryengine.googleapis.com dataplex.googleapis.com sqladmin.googleapis.com eventarc.googleapis.com workflows.googleapis.com \
           cloudscheduler.googleapis.com cloudfunctions.googleapis.com modelarmor.googleapis.com cloudbilling.googleapis.com cloudresourcemanager.googleapis.com \
           serviceusage.googleapis.com vectorsearch.googleapis.com spanner.googleapis.com container.googleapis.com clouddeploy.googleapis.com; do
  grep -qxF "$api" <<< "$enabled" || { echo "MISSING $api"; missing=$((missing + 1)); }
done
echo "the kit's 40: $((40 - missing)) enabled, $missing missing"
echo "enabled on the project in all: $(grep -c . <<< "$enabled")"
```

### The budget, in the console (step 6, no file)

Console, *Billing*, the billing account from run 2, *Budgets & alerts*, *Create budget*:

1. **Define:** *Alerts only*; name `Billing account guard`. Next.
2. **Scope:** *Monthly*; all projects, all services; under the savings untick *Promotional credits* only. Next.
3. **Amount:** *Specified amount*, target `5000` (the kit's `BUDGET_AMOUNT`). Next.
4. **Actions:** the console pre-fills 50, 90 and 100 percent actual; change 90 to 80, add 120 percent *Forecasted*;
   keep *Email alerts to billing admins and users* ticked. Finish.

On an account that already pays for other projects, an account-wide budget of 5000 can be past its thresholds the
moment it exists and will email at once. Delete it after recording if it is noise; if you scope it to the new
project instead, the read-back in run 6 shows a `projects` filter the page's prose does not mention.

### 6. `budgets_list.txt` (step 6)

```bash
gcloud billing budgets list --billing-account="$BILLING" --billing-project="$PROJECT" \
  --filter='displayName="Billing account guard"' \
  --format='yaml(displayName,amount,thresholdRules,budgetFilter.calendarPeriod,budgetFilter.creditTypesTreatment,budgetFilter.creditTypes)'
```

The page's prose after this window says the four rules come back as fractions, the last one forecasted, and the
filter lists the credit types still taken off, without the promotional ones. If the output differs, tell the writer.

### 7. `verify.txt` (step 9)

```bash
gcloud billing projects describe "$PROJECT"
gcloud config get-value project
```

## Not a run, but dated

The standing cost (steps 1 and 8, Rs 1,057 a day with a small-shard index, Rs 2,666 with a medium one) multiplies
the kit's Terraform sizes by Google's Mumbai list prices read on 7 October 2026; the price table and its URLs are in
`build.py` (`PRICES`). Re-read them before the cohort. The trial and budget facts the page states were read the
same day; their URLs are in `build.py`'s comments.
