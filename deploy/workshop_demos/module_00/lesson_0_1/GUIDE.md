# Lesson 0.1: source reading guide

Read this beside the section-numbered demo files. The prose below follows the main HTML;
its terminal setup is replaced by the documented Python setup. Read-only code
and sample output are not executable steps. Sample values are not live results.

Source: the lesson's main page, `Netsetos_GCP_Capstone_0.1_Billing_Project_WIX.html`, reviewed at blob `e8752816c7f6df23f638d88cde838439debb5a23`. Learners read that page on the course site; this guide keeps its prose.

Before the kit builds anything, someone has to pay for it, and someone has to be told when it costs more than planned. This lesson sets up the three things every later lesson stands on: a billing account, on the free trial or paid; a project of its own for the lane, linked to that account, with the 40 APIs the kit uses switched on; and a budget that emails at the kit's own thresholds. Then it prices what the lane will cost per day just for existing, from the kit's Terraform, so you know the number before lesson 0.3 starts the meter.

- What a billing account, a budget and a project are

- The words: billing account, credit, project, link, API, budget, standing cost

- Before you run anything: open Cloud Shell

- The billing account: free trial or paid

- The project: create it, link it, make it the default

- The APIs: 40 services in two calls

- The budget: an alert on the billing account

- The kit's side, read verbatim: what make plan checks, and the budget it declares

- The standing cost: what bills by the hour, per day and per weekend

- Verify it yourself: the checklist

You will learn how Google Cloud bills (an account that pays, projects that spend, a budget that only emails) and what the DocuMind lane costs per day just for existing. Then you will set it up: a billing account, the project `documind-ai-YOUR-ID` with the kit's 40 APIs, a budget alert at the kit's thresholds, and the lane's standing cost written down.

### What a billing account, a budget and a project are

Who pays, what spends, who watches, and the two kinds of cost a lane runs up.

A billing account pays; a project spends. Everything you create on Google Cloud lives in a project: a Cloud Run service, a database, an index. A project holds no money of its own. It is linked to a billing account, and the billing account holds the payment method, the currency (an Indian account bills in rupees), any credits, the budgets and the invoices. One billing account can pay for many projects; a project is linked to one billing account at a time, and without one the paid services refuse to start. This lesson creates one project for the lane, `documind-ai-YOUR-ID`, and links it to your billing account.

A budget watches; it does not stop anything. A budget is a rule on the billing account: an amount per month, and percentages of it at which Google sends an email. Google's own budget page is plain about the limit: an alerts-only budget caps neither usage nor spending. The services keep running and the bill keeps growing after every email. The kit declares one (`terraform/budget.tf`, read in step 7): 5000 a month in your account's currency, with emails at 50, 80 and 100 percent of actual spend and at a 120 percent forecast. You make your own in step 6, before anything exists that could spend.

Two kinds of cost. Most of what DocuMind does is paid per use: a Gemini answer, an embedding, a Cloud Run request that wakes a service from zero. Ask nothing and they cost nothing. A few pieces are different: machines the kit's Terraform keeps running whether or not anyone asks a question. The deployed Vector Search index, the Spanner graph instance, two Cloud SQL databases, the GKE lab cluster and its node, and the connector Cloud Run uses to reach the private network bill by the hour from the moment lesson 0.3 creates them until lesson 0.4 takes them down. That is the lane's standing cost. Step 8 prices it from the kit's own files: Rs 1,057 to Rs 2,666 a day, depending on one machine the index is given.

A household electricity connection. The connection is in one name and one bank account pays the bill: that is the billing account. Each flat in the building has its own sub-meter on that connection: a project. The SMS alert you set for when the month's bill crosses Rs 2,500 is the budget: it tells you, and the supply stays on. The refrigerator runs all night whether or not anyone opens its door: that is the standing cost. A Gemini call is the geyser, switched on for one bath and off again. The only switch that stops the refrigerator is the mains, and for the lane that is `make down`, in lesson 0.4.

The billing account is the only thing on this page that can be charged. The project spends through it; the budget reads the account's costs and sends email. Nothing on the right can switch anything in the middle off: that is a command you run, and lesson 0.4 runs it.

#### The meter that runs while nobody asks

The standing cost is easier to respect once you have watched it add up. The meter below runs the kit's six standing declarations at Google's Mumbai list prices, the same table step 8 derives line by line. Move the slider, or pick a span, and switch the index between the two machines it can be given. Under the bars, the same rupees are set against the kit's budget and against the trial's credit.

Each bar is one declaration in the kit's Terraform, its length that item's share against the largest, its figure the rupees for the span you chose at the course's Rs 85 to the dollar. Nothing here is a call: these are the hours a machine stands. With the small shard, Spanner's tenth of a node is the largest single item; with the medium shard, the index is.

It is not your bill. It counts the machines and the disks the Terraform sizes, at list price, in Mumbai, before tax. Your invoice adds storage, network, every per-use call and the taxes on your account, and an Indian account is charged at Google's own rupee prices rather than at Rs 85 to the dollar. It is the floor: what the lane costs on a day when nobody uses it.

### The words: billing account, credit, project, link, API, budget, standing cost

Ten words, each with the value it takes on your account.

The first five are set once, in this lesson, and every later lesson reads them: the kit discovers your billing account from the project rather than asking for it, and its helper refuses to plan in a project that has none. The last five are the vocabulary of money for the rest of the course; lesson 11.6 comes back to budgets from the other side, as the month's spend that changes which model answers.

### Before you run anything: open Cloud Shell

This lesson needs a Google account, a browser, and a shell where the gcloud CLI acts as you. Cloud Shell is the simplest: a terminal in the browser, on a Debian machine Google provisions for you, with the gcloud CLI already installed and 5 GB of free persistent disk as your home directory. Open the Google Cloud console at `console.cloud.google.com`, sign in with the Google account you will use for the whole course, and click Activate Cloud Shell, the terminal icon at the top right. A laptop works too, if the gcloud CLI is installed and signed in; lesson 0.2 sets a laptop up properly. Nothing on this page needs the kit: there is no clone yet, no Python environment and no lane, and every command here costs Rs 0.

Run the block below once per session. It prints gcloud's version, the account it acts as, and its default project, which stays empty until step 4 sets it.

`gcloud: command not found` means this machine has no gcloud CLI: use Cloud Shell for this lesson, and lesson 0.2 installs the CLI on a laptop. An empty account line on a laptop means gcloud is not signed in: run `gcloud auth login`, finish the sign-in in the browser it opens, and run the block again. If Cloud Shell shows a box titled Authorize Cloud Shell, choose Authorize: it lets gcloud in that session act as the account you are signed in with. Cloud Shell ends a session after an hour without activity, and deletes the home directory of an account that has not opened it for 120 days. The two names you export in steps 3 and 4, `BILLING` and `PROJECT`, live only in the session: in a new tab, run those two `export` lines again before anything that uses them.

#### Three kinds of code window on this page

Every window has a label. A label that starts with bash is a block to paste into Cloud Shell, whole, and press Enter; the one Python cell is wrapped in `python - expected is what the command printed when the author ran it. Where a value belongs to your account the page shows a placeholder instead: `XXXXXX-XXXXXX-XXXXXX` for a billing account, `documind-ai-YOUR-ID` for the project, `NUMBER` for its number, `you@example.com` for your sign-in.

### The billing account: free trial or paid

Where the money comes from, what the trial gives and takes away, what is different in India, and the one command that lists your accounts.

#### Definition

A Cloud Billing account is what Google charges. It holds a payment method, a currency fixed when the account is created, the credits, the budgets and the invoices, and it pays for every project linked to it. An Indian account is in rupees: the kit's Makefile says so in a comment, and the kit's budget carries no currency of its own for that reason (step 7). A billing account is either a Free Trial account or a Paid one, and the difference decides what happens on the day the money runs out.

#### Get one in the console

- Open `console.cloud.google.com`, signed in with the account you will use for the course.

- If you have never paid for Google Cloud, Google Maps Platform or Firebase, and never took the Free Trial, you can start it: the sign-up is at `cloud.google.com/free`. If you already have a billing account, keep it and go to the command below.

- Give the payment method it asks for: a card, or another method valid for the length of the trial. Google places a temporary authorisation hold on it, which is not a charge, and in some countries asks you to verify a bank account as well.

The kit calls Gemini through Vertex AI in your own project, with the `google-genai` client given the project and a location, not through AI Studio's Gemini API. The trial also forbids some uses outright, mining cryptocurrency among them.

At the course's rate the credit is Rs 25,500. Step 8 prices the lane's standing cost at Rs 1,057 to Rs 2,666 a day, so the credit covers 24.1 days of a lane left standing with the small index, or 9.5 days with the medium one, before a single question is asked. A month left up, Rs 32,157 to Rs 81,100, outruns the credit either way, and on the day the credit runs out the trial ends and every resource stops. Bringing the lane down between sessions (lesson 0.4) is what lets a trial account last the course.

An Indian billing account is billed in rupees, at Google's own rupee prices; the figures on this page are list prices at the course's rate, before any tax on your invoice. Two things differ from the examples you may read elsewhere.

- Automatic card payments. Under the Reserve Bank of India's rules for recurring payments, your bank may decline an automatic card charge for Google Cloud above its limit. Google's answer is a manual payment, and you can also make one in advance, to add credit to the account before it is needed.

- UPI. Offered to qualified organisations in India paying in rupees, after a prepayment of typically Rs 500 to 1,000.

#### Find it with gcloud

One command lists every billing account your Google account can see. The one you want says `True` under `OPEN`; its `ACCOUNT_ID` is what step 4 links the project to.

gcloud asked the Cloud Billing API, as you, for the billing accounts your sign-in may use. An account missing from this list is one you cannot link a project to; an account with `False` under `OPEN` is closed, which is how a trial that ended without an upgrade looks, and it pays for nothing. Nothing was created: listing is free, and so is everything else in this lesson.

### The project: create it, link it, make it the default

Three names for one box, the rule the kit's helper holds the ID to, and the two commands that make the lane's project.

#### Definition

A project is the box every resource lives in, and the unit that permissions, quotas, APIs and billing attach to. It has three names. The ID is yours to choose, unique across all of Google Cloud and fixed for good: 6 to 30 characters of lower-case letters, digits and hyphens, starting with a letter and ending with a letter or a digit. The number is Google's, assigned at creation; it appears in the services' URLs and in the budget's filter (step 7). The name is a label you can change. The course calls the lane's project `documind-ai-YOUR-ID`: put your own suffix in place of `YOUR-ID`, and keep the project for the lane alone, because deleting a project is the one action that stops every charge in it at once (step 8).

The kit's helper holds the ID to that rule before it plans anything:

#### In the console

The project picker at the top of the console has New project: a name, and an ID the form suggests, which you can edit to `documind-ai-YOUR-ID` before you create the project. The Billing page, with the new project selected, links it to your billing account. The two commands below do the same, and leave a record you can compare with the page.

#### With gcloud

Put your account ID from step 3 and your project ID in the first two lines, then paste the block. `--set-as-default` makes the new project gcloud's default, so every later command in this session finds it without being told, and so do the Basics pages, which read it with `gcloud config get-value project`.

The first command asked Resource Manager for a new project with your ID, and switched gcloud to it. The second linked the project to the billing account and printed its billing information: the account's name and `billingEnabled: true`, the two things the kit reads before it plans (step 7). From this moment the project can spend, but nothing in it can: no resource exists, and the kit's APIs are not on yet. An ID someone already holds answers with an error on the first command: choose another suffix and run the block again.

### The APIs: 40 services in two calls

Why an API has to be switched on, the kit's list and the target that runs it, and a loop that counts them.

#### Definition

An API, in Google Cloud's sense, is a product switched on for one project: Cloud Run, Firestore, Vertex AI. Until it is enabled, every call to it from that project is refused, whoever makes it, with a message that names the API. Enabling costs nothing; using is what bills. The kit needs 40 of them before Terraform can create anything, and keeps the list in one block of `commands/lesson-12.1.sh`, the one marked `ENABLE_APIS`. It is two calls rather than one because the Service Usage API takes at most 20 services per request, as the block's own comment records. `make apis` runs that block unchanged:

You have no clone yet, so you paste the same lines. They are the block exactly, taken from the kit when this page was built: the first sets gcloud's project, which step 4 already did, and the next two enable the list.

#### Count them

A short loop compares the project's enabled services with the kit's list and names any that is missing. Run it now, and again whenever a later lesson's command complains that an API is disabled.

#### What the 40 are for

Two of them belong to this lesson: `cloudbilling` lets Terraform read which billing account pays for the project, and `billingbudgets` lets it create the kit's budget on that account (step 7); your own read-back in step 6 goes through the second. The kit's read-only `make preflight` checks 22 of the 40 by name before a plan, and names `make apis` for any that is missing.

Each `gcloud services enable` became one operation on the Service Usage API, and gcloud waited for it to finish. Nothing that bills was created: an enabled API with no resource behind it costs nothing. The loop's last line counts every service enabled on the project, the kit's and any others, so it is not meant to equal the kit's list; the line before it is the check. The project now accepts calls to every service the kit uses.

### The budget: an alert on the billing account

An amount, four thresholds and the people who hear, set in the console at the kit's own values, then read back with gcloud.

#### Definition

A budget lives on the billing account. It watches a scope (every project the account pays for, or some of them), compares the period's cost with an amount, and holds threshold rules: a percentage of the amount, on actual spend so far or on the forecast for the period. When spend crosses a rule, Google emails the billing account's administrators and users, and can also notify Cloud Monitoring channels or publish to a Pub/Sub topic. That is all it does. You make yours now, on the whole account, before any project has spent a rupee; lesson 0.3 adds the kit's own, scoped to the lane's project.

Google's budget page is explicit: an alerts-only budget does not automatically cap usage or spending. When the email arrives, everything is still running, and it arrives late: the page warns that the first notification can take several hours after a budget is created, and that usage reaches Cloud Billing with a delay of its own. Google also offers spend cap budgets, which pause a service once its estimated cost passes the amount, but only for a few services (the Gemini API, Gemini Enterprise Agent Platform, Cloud Run and Cloud Run functions), on one project at a time, and even then enforcement is not instant and the overage is billed. Spanner, Cloud SQL, GKE and Compute Engine are not on that list, and the kit declares no spend cap. The brake on this course is a command: `make down`, in lesson 0.4.

#### Make it in the console

Every value below that is not a name comes from the kit: the amount is the Makefile's `BUDGET_AMOUNT`, the thresholds are `budget.tf`'s four rules. The one deliberate difference is the credits, explained after the list.

- In the console's menu, open Billing, choose your billing account, then Budgets & alerts and Create budget.

- Define: Alerts only. Name it `Billing account guard`. The kit's budget, which lesson 0.3 creates, is called `DocuMind monthly budget`; a different name keeps the two apart. Next.

- Scope: time range Monthly; all projects and all services, so anything that starts anywhere on the account is counted. Under the savings, untick Promotional credits and leave the rest ticked. Next.

- Amount: Specified amount, target `5000`. There is no currency to choose, because a budget is in the billing account's own: on an Indian account this is Rs 5,000. Next.

- Actions: the console fills in 50, 90 and 100 percent of actual spend. Change 90 to 80, then Add threshold: 120 percent, triggered on Forecasted. Keep Email alerts to billing admins and users ticked; if you created the billing account, you are one of its administrators. Finish.

By default a budget takes every credit off the cost before it checks a threshold, and Google counts the Free Trial's credit as a promotional credit. On a trial account a default budget therefore reads zero for as long as the credit pays, and on the day the credit is gone the trial ends with it: such a budget may never send an email at all. With promotional credits unticked, yours measures what the lane really costs while the trial pays for it, and its 50 percent email, at Rs 2,500 of cost before the credit, is your first warning rather than none. On a paid account with no promotional credits the box changes nothing. The kit's budget keeps the default, every credit taken off; step 7 sets the two side by side.

#### Read it back with gcloud

The Budget API answers for the same budget. `--billing-project` makes the call count against your project, where step 5 enabled the Budget API (the kit's helper names a quota project for its own gcloud calls in the same way); the filter picks yours out of any others on the account, and the format keeps the fields the console asked about.

gcloud read the budget through the Cloud Billing Budget API that step 5 enabled, as you, with your role on the account. The amount came back in the account's currency; the four threshold rules came back as fractions of it, the last one forecasted; and the filter carries the credit treatment you chose, a list of the credit types still taken off, with the promotional ones left out. Those are the same fields the kit's Terraform writes, which the next step reads.

### The kit's side, read verbatim: what make plan checks, and the budget it declares

The helper that refuses a project with no billing account, and terraform/budget.tf line by line: which account, which spend, how much, when, and who hears.

#### What make plan reads about your project first

Lesson 0.3's `make plan` runs `commands/infrastructure.py plan`, and before Terraform plans anything the helper reads the project you made in step 4: that it exists and is active, that it has a number, that billing is enabled, and that the linked account's ID has the shape of a real one. Fail any of these and it stops with a sentence that names what to fix.

The kit's read-only `make preflight` checks the same two facts, and for a miss prints the commands step 4 ran:

#### The budget it declares

Lesson 0.3 creates this budget with everything else, in the same apply; nothing switches it on or off. Three excerpts from `terraform/budget.tf` (which account it goes on, the resource itself, its inputs), then the Makefile lines that set the amount.

Read it as five decisions.

- Which account. The one already linked to the project, read from the project's own record (`data.google_project.current.billing_account`), unless `billing_account_id` is set. The precondition refuses anything that is not a real `XXXXXX-XXXXXX-XXXXXX` ID, and its message names three fixes; step 4's link and step 5's `cloudbilling` are two of them.

- Which spend. `budget_filter` names one project, by number. The comment records why: the ID form passed the plan and was refused by the first real apply. So the kit's budget watches the lane's project only; yours watches the whole account.

- How much. `units = var.budget_amount`, and `make plan` passes `BUDGET_AMOUNT`, 5000, as `-var budget_amount`; run Terraform without make and the variable's own default, 500, applies instead. No currency is sent unless `budget_currency` is set, so the amount is in the account's own: the comment records that `USD` was refused on an Indian account, and the Budget API requires the account's currency.

- When. Four threshold rules: 50, 80 and 100 percent of actual spend, and 120 percent of the forecast for the month, the one rule that can speak before the money is spent.

- Who hears. No notification block at all unless `alert_channels` or `budget_pubsub` is set, so the API's default applies: emails to the billing account's administrators and users, the same people your budget emails. The comment explains the omission: an empty block read back as a change on every plan. The Pub/Sub leg is off by default because it needs a grant to Google's billing budget agent, a system account outside your organisation, which an organisation that restricts sharing to its own domain refuses.

The credits row is the one real difference. On a paid account a credit is money you do not pay, so cost after credits is the bill, and that is what the kit's default measures. Yours is set for the first month of a course that may run on the trial, where the credit hides the rate the lane spends at. While both exist, an email from yours and silence from the kit's is the trial's credit at work.

### The standing cost: what bills by the hour, per day and per weekend

Six declarations in the kit's Terraform, each priced at Google's Mumbai list price, then set against the budget, the trial, and the switches that do and do not stop them.

#### Definition

The standing cost is what a resource bills for existing, by the hour, whether or not anything uses it. Most of DocuMind scales to nothing: its seven Cloud Run services are deployed with no minimum instance, so a service nobody calls is soon running no instance at all and costs nothing. The kit's README names the parts that do not scale away:

It bills while it exists - the Vector Search endpoint, two Cloud SQL instances and the cluster by the hour - which is what `make off` (the night switch), `make down` and the throwaway project are for.

That sentence names the index, the two Cloud SQL instances and the cluster. Read against the Terraform, the list is longer: the cluster is two lines on the bill, its fee and its node; Spanner's own file says it bills by the hour; and the connector Cloud Run reaches the private network through keeps instances running too. Six declarations in all, read verbatim below.

#### The six, as the kit declares them

The index. One replica (`min_replica_count = 1`), on the machine its shard size names. `vector.tf` does not choose the shard size: the index is created without one, the API picks it, and the comment above the map records an existing index that came back `MEDIUM`. A small shard runs one `e2-standard-2`, Rs 230 a day; a medium one runs one `e2-standard-16`, Rs 1,839 a day. Once the index exists its description names its shard size; until then this page carries both.

Spanner. Enterprise edition, which Spanner Graph needs, at 100 processing units: a tenth of a node, the smallest a provisioned instance can be, in `regional-asia-south1`. The comment above it says it bills by the hour while it exists, and asks for it to be priced on the Spanner page for `regional-asia-south1` before a cohort. That pricing is the table below: Rs 351 a day.

Cloud SQL. Two instances of one shape, the chat service's checkpointer and the gateway's database: `db-f1-micro`, zonal, 10 GB of SSD, no backups, running all the time. A running instance's public address costs nothing; its hours and its disk do.

The GKE cluster. `location = var.region` makes it a regional cluster. Every GKE cluster pays a flat management fee of $0.10 an hour (the kit's `gke/README.md` prices the same fee), and the free tier's monthly credit covers zonal and Autopilot clusters, not a regional Standard one. Its lab pool is one `e2-standard-2` node with a 30 GB standard disk.

The connector. Serverless VPC Access keeps at least `min_instances`, 2, running, of the default instance type, `e2-micro`, and Google bills connector instances as Compute Engine VMs.

#### The price of each, per hour and per day

Each line is the declaration's size times Google's list price for Mumbai (`asia-south1`, where the course's lane runs its services and where `spanner.tf` keeps the graph), read from Google's pricing pages on 7 October 2026, at the kit's Rs 85 to the dollar from `shared/prices.py`.

#### Run the arithmetic yourself, Rs 0

The same table as a Python cell: the hourly prices, the kit's rate and the kit's budget, then the sums. It touches no account and no network, so it runs anywhere a `python` does, Cloud Shell included.

#### Against the budget and the trial

- A day of standing cost is Rs 1,057 with the small index and Rs 2,666 with the medium one. A weekend, Saturday and Sunday, is Rs 2,114 or Rs 5,333. A month left up is Rs 32,157 or Rs 81,100.

- The budget. With nothing else running, the standing cost alone crosses the kit's 50 percent, Rs 2,500, after 57 hours with the small index or 23 with the medium one, and 100 percent after 114 or 45 hours. The email follows after Cloud Billing's reporting delay, not at that hour.

- The trial. Rs 25,500 of credit covers 24.1 days of a small-index lane left standing, or 9.5 days of a medium one.

Storage, which bills by the gigabyte-month: Firestore, the buckets, BigQuery, the managed search stores, the container images, the graph's own data. Network traffic. Every per-use call: Gemini, embeddings, Document AI pages, Cloud Run requests. Any address a machine holds while it runs. And tax. It is also list price at the course's rate, while an Indian account is charged at Google's own rupee prices, so your invoice will not match it to the rupee. On a quiet day those additions are usually small beside the machines, which is why the machines are the number to write down.

#### What stops it, and what does not

`make off`, the switch lesson 0.4 teaches, sets four Cloud Run services (the two GPU services, the gateway and the UI) back to zero minimum instances, and removes the vLLM workload from the cluster. None of the six above is a Cloud Run service, and the kit says so as it runs:

The index, Spanner, both databases and the connector are not touched by it either. Only `make down` removes them, by destroying what the Terraform made, and the last lines it prints name the one action that stops everything at once, which is why the lane gets a project of its own:

This is the lesson's proof. In your notes, with today's date: Rs 1,057 a day with a small-shard index, Rs 2,666 a day with a medium one; Rs 2,114 or Rs 5,333 for a weekend left up. Plan for the larger until you know which machine your index got. Lesson 0.4 comes back to this number when it switches the lane off.

### Verify it yourself: the checklist

Eight checks, each one block above, each with the value that proves it on your account.

One more read-only block first: the project's billing information, the record the kit's helper reads in step 7, and gcloud's default project.

There is no lane yet, and nothing bills. Your billing account carries a budget, Billing account guard: 5000 a month in its currency, emails at 50, 80 and 100 percent of actual spend and at a 120 percent forecast, measured before the trial's promotional credit. Your project, `documind-ai-YOUR-ID`, exists, is linked to that account, is gcloud's default in Cloud Shell, and has the kit's 40 APIs enabled, which cost nothing. The lane's standing cost is in your notes: Rs 1,057 to Rs 2,666 a day, from the moment the lane exists. Lesson 0.2 clones the kit and proves a first success at Rs 0; lesson 0.3 deploys the lane into this project, adds the kit's own DocuMind monthly budget for it, and starts that meter.

Netsetos GenAI on GCP · Module 0 Setup · Lesson 0.1 Set up the Google Cloud billing account, budget and project · v5.0

Next: Lesson 0.2 Reproduce the local environment, read the master diagram and prove a first success.
