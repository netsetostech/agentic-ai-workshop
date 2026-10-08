# ---------- Agents (the v5 course's Modules 5 and 10): the agent layer, lessons 5.1, 5.4-5.7 and 10.4; the DocuMind Desk's first ----------
# Included by the Makefile (`include mk/*.mk`); every variable it uses is declared there, except the Desk's own
# below. A recipe longer than a few lines is a script under commands/, a subcommand of commands/lane.py (limits), or,
# for the Desk, a subcommand of commands/desk_ops.py, run the same way without make (commands/lane.py's subcommand set
# is pinned by its test, so the Desk's live in their own file).

# The case queue's hourly overdue job (terraform/desk.tf) runs on the chat image the lane deploys: make desk-job once
# that image is pushed, then DESK_JOB=true on every later make plan and make up, or the next plan would remove the job
# and make plan's guard refuses it. Appended to the Makefile's Terraform variable list, which is recursive, so make
# plan and make up pass both. The Desk's eval accounts are terraform/desk.tf's; desk-operators lets the
# operators mint as them, and nobody may mint as the Google Chat bridge's account, which is not in this list.
DESK_JOB   ?= false
CHAT_IMAGE ?= $(IMAGE_REPO)/chat:$(GIT_SHA)
TF_EXTRA_VARS += -var desk_job=$(DESK_JOB) -var chat_image=$(CHAT_IMAGE)
DESK_EVAL_SAS = documind-evalacme-sa documind-evalzeta-sa documind-evalglobex-sa documind-evalleaver-sa documind-evalgrc-sa

# The router's three alert policies (terraform/desk_alerts.tf: the fallback share, the L2 share, clarify and
# out_of_scope week on week) are PromQL, which Cloud Monitoring may refuse on a metric with no data, so a fresh lane
# has none. Turn them on once the router has run (make desk DESK_ROUTE=shadow or on, and some turns): make plan up
# DESK_ROUTER_ALERTS=true, then DESK_ROUTER_ALERTS=true on every later make plan and make up, and on make desk-job,
# reconcile-job and batch-job, whose plans would remove them and are refused. Appended the same way as DESK_JOB.
DESK_ROUTER_ALERTS ?= false
TF_EXTRA_VARS += -var desk_router_alerts=$(DESK_ROUTER_ALERTS)

# The gate check's alert on its failed share (terraform/desk_alerts.tf) is PromQL too: turn it on once a tenant's
# desk_gate is on and the check has run (make desk DESK_GATE=on, and some questions): make plan up
# DESK_GATE_ALERTS=true, then on every later plan, as DESK_ROUTER_ALERTS. Appended the same way.
DESK_GATE_ALERTS ?= false
TF_EXTRA_VARS += -var desk_gate_alerts=$(DESK_GATE_ALERTS)

# The Google Chat door (terraform/gchat.tf, lesson 10.4) is off unless asked for: GCHAT_DOOR=true on make plan and
# make up declares what its bridge runs on, then GCHAT_DOOR=true on every later plan, as DESK_JOB. make deploy-gchat
# and make smoke-gchat read terraform output gchat_door and refuse while the last apply had it off.
GCHAT_DOOR ?= false
TF_EXTRA_VARS += -var gchat_door=$(GCHAT_DOOR)
GCHAT_DOOR_ON = [ "$$(cd $(TF_DIR) && terraform output -raw gchat_door 2>/dev/null)" = true ] || { echo "ERROR: the Google Chat door is off on this lane: make plan up GCHAT_DOOR=true first (terraform/gchat.tf), then keep GCHAT_DOOR=true on every later plan" >&2; exit 1; }

# The Desk's offline half: no credential, no cost, part of CI (documind-dryrun.yml runs evals/tests): the route set,
# its split, the eval's metrics and the probe's readers, the router on a scripted classifier (route_eval.py --local,
# which exits 1 below the dev gates) and the threshold sweep's arithmetic, then the case queue's and the router and
# desk graph's tests (workshop lessons 5.6 and 10.4) in ~/graph-venv with the chat image's pins. See
# commands/desk-check.sh.
desk-check:
	@PY=$(PY) bash commands/desk-check.sh

# Before the router is built (lesson 10.4): four facts it depends on, measured on your lane - top-two logprobs on
# flash-lite at global, zero thinking tokens at thinking_budget 0, the enum schema's output tokens, and whether
# flash takes thinking level MINIMAL. Five small calls on location=global, well under Rs 1; prints, writes nothing.
# Needs google-genai in the shell (make ablate's line); --dry-run shows the requests without sending them.
route-probe: guard-project
	$(PY) evals/route_probe.py --project $(PROJECT)

# The router's exemplar index for TENANT (lesson 10.4): evals/routes.jsonl's dev rows on the routes TENANT's doc_type
# registry covers (make doc-types first), embedded with text-embedding-005 on us-central1 into
# tenants/{TENANT}/desk_exemplars, the stale entries deleted after: about 200 short questions, one embedding each.
# DRY_RUN=1 prints the rows per route and the index version and embeds nothing. The chat service reads it within 5 min.
route-index: guard-project
	@GOOGLE_CLOUD_PROJECT=$(PROJECT) $(PY) commands/desk_ops.py --project $(PROJECT) route-index --tenant $(TENANT) $(if $(DRY_RUN),--dry-run,)

# The router's two thresholds (TAU_OOS, ACCEPT_VOTES) swept on the dev split with the real flash-lite and embeddings:
# about 130 flash-lite calls (about Rs 2 at four characters a token) and 200 embeddings. It prints each pair's accepted
# accuracy, L1 errors sent to L2 and L2 share, and the pair to ship, and writes nothing. LOCAL=1 runs the sweep
# offline on a scripted classifier, and needs no PROJECT.
route-calibrate: $(if $(LOCAL),,guard-project)
	$(PY) evals/route_threshold.py $(if $(LOCAL),--local,--project $(PROJECT))

# The doc_type registry (shared/doc_types.py): the class an operator gives each object of TENANT and the version
# (the pin) it was reviewed at; the worker classes a version at ingest only when it is the pin. SEED=manifest writes
# the registry from evals/manifest.json; FOLLOW=<name> re-pins one object to the version the ledger holds now, after
# a person has read it; EXPORT=<file> writes the registry for evals/route_eval.py --registry. The view follows -
# name, current label, class, pin, chunk count - then the relabel's plan for the stored rows
# (services/ingest/relabel.py). APPLY=1 applies it: the Firestore rows, the Vector Search restricts,
# the Vertex AI Search structData, BigQuery's chunk_source, the tenant's answer cache expired; it exits 3 when BigQuery
# deferred a statement (rows still in the streaming buffer: run it again later). RESET=1 plans every row back to
# unknown (the state of workshop lessons 2.1 and 5.5, for rehearsing them), the registry kept. One tenant a run.
# Like make backfill-vectors, best run between ingests: a swap racing the upsert is caught and taken off the tier.
doc-types: guard-project
	@GOOGLE_CLOUD_PROJECT=$(PROJECT) $(PY) commands/desk_ops.py --project $(PROJECT) doc-types --tenant $(TENANT) $(if $(SEED),--seed $(SEED),) $(if $(FOLLOW),--follow "$(FOLLOW)",) $(if $(EXPORT),--export "$(EXPORT)",)
	@PYTHONPATH=.:services/ingest GOOGLE_CLOUD_PROJECT=$(PROJECT) MANAGED_MIRROR=$(MANAGED_MIRROR) BQ_CHUNK_TABLE=$(PROJECT).rag_data.chunk_source \
	  VECTOR_INDEX_NAME=$${VECTOR_INDEX_NAME:-$$(cd $(TF_DIR) && terraform output -raw vector_index_name 2>/dev/null)} \
	  $(PY) services/ingest/relabel.py --project $(PROJECT) --tenant $(TENANT) $(if $(APPLY),--apply,) $(if $(RESET),--reset,)

# A chat turn's limits (workshop lesson 5.5): model calls, rupees and a deadline, from the deployed /health, and the
# A2A peer's own call cap when its /health names one. Reads only; no model call.
limits: guard-project
	@$(PY) commands/lane.py --project $(PROJECT) --region $(REGION) limits

# The same limits offline, free: the kit's three agent brains against scripted models and a stand-in rag-api, in
# ~/graph-venv with the chat image's pins (made, or completed with google-adk, here). See commands/limits-check.sh.
limits-check:
	@PY=$(PY) bash commands/limits-check.sh

# Trip one limit on the deployed documind-chat, STOP=model_calls or STOP=turn_budget: every agent brain answers 200
# with stopped_by, the variable is put back from a trap, and the smoke passes again. About eight turns.
limits-drill: guard-project
	@PROJECT=$(PROJECT) REGION=$(REGION) STOP=$(STOP) PY=$(PY) bash commands/limits-drill.sh

# The Desk's switches for one tenant, in tenant_settings/{TENANT} (a merge write: data_region and the pins kept).
# The hard gate stands in front of rag-api's /v1/query, /v1/stream and /v1/passages and the chat service's /v1/chat for
# every tenant unless DESK_GATE=off: a POSH disclosure, a grievance, a privacy request, unpaid exit dues or "let me
# talk to a person" (shared/desk_rules.py) gets the fixed reply of shared/desk_law.py with model none and cost 0, and
# Aadhaar and card numbers are masked out of every other question - DESK_GATE=rules, what a tenant has until an
# operator writes anything else. DESK_GATE=on adds the model check (shared/desk_recall.py): one flash-lite call for each
# question to that company the rules let through, at the chat door and on rag-api's /v1/query and /v1/stream for a body
# with no brain label or "ui" (eval scripts included); while any company is on, the chat door looks up every company's
# caller. Both services read the document once a minute. No value needs a case queue. Without DESK_GATE it prints the
# switch, and beside desk_gate on what it costs.
# DESK_MAX_PARTS=2 lets the routed Desk (lesson 10.4) run two desks for one question, one after the other; 1, the
# default, offers the second as a button. DESK_ROUTE is the routed Desk's mode: off; shadow (each /v1/chat turn is also
# decided by the router and logged as a desk_shadow row, nothing more); on (POST /v1/desk answers, and the Desk page
# shows Ask the Desk); single (the same with one desk, DESK_SINGLE=handbook|statute, and no classifier). on and single
# are refused while the POSH queue is incomplete or a unit has no member holding its ic_member role (route_refusal),
# and shadow while DESK_GATE is off.
# DESK_OFF=statute (or handbook,statute; none clears it) switches answer desks off: the routed Desk answers them as
# not covered, with no search.
# NOTES=evals/desk/clause_notes.acme.json writes the company's notes on handbook clauses (none clears them): the
# handbook desk shows one beside an answer citing its clause.
# DESK_GCHAT=on|off opens or closes the Google Chat door (lesson 10.4) for the tenant: on is refused while
# DESK_GATE is off, and unless DESK_ROUTE is on or single, and for a tenant whose data_region is in it also needs
# CONFIRM_RESIDENCY=1, because the answers and their quotes then sit in the company's Google Chat. The chat service
# reads it within 60 s.
desk: guard-project
	@GOOGLE_CLOUD_PROJECT=$(PROJECT) $(PY) commands/desk_ops.py --project $(PROJECT) desk --tenant $(TENANT) $(if $(DESK_GATE),--gate $(DESK_GATE),) $(if $(DESK_MAX_PARTS),--max-parts $(DESK_MAX_PARTS),) $(if $(DESK_ROUTE),--route $(DESK_ROUTE),) $(if $(DESK_SINGLE),--single $(DESK_SINGLE),) $(if $(DESK_OFF),--off $(DESK_OFF),) $(if $(NOTES),--notes "$(NOTES)",) $(if $(DESK_GCHAT),--gchat $(DESK_GCHAT),) $(if $(CONFIRM_RESIDENCY),--confirm-residency,)
	$(if $(filter shadow on,$(DESK_ROUTE)),@echo ">> the router's three alert policies (terraform/desk_alerts.tf): make plan up DESK_ROUTER_ALERTS=true after the router has taken some turns; then keep DESK_ROUTER_ALERTS=true on every later plan")
	$(if $(filter on,$(DESK_GATE)),@echo ">> the gate check's alert on its failed share (terraform/desk_alerts.tf): make plan up DESK_GATE_ALERTS=true after the check has run on some questions; then keep DESK_GATE_ALERTS=true on every later plan")

# The case queue (workshop lesson 5.6): shared/roles.py, shared/cases.py, and the routes on the chat service.
# A person's roles in TENANT: ROLES=employee,grc_member sets exactly those; REVOKE=grc_member (or all: an employee
# again) takes some away; EMAIL alone prints that person's roles; neither lists the tenant's role documents. The person
# must be on the roster first (make roster). Each grant and each revoke is an audit event (role.grant, role.revoke).
# While DESK_ROUTE is on or single, a change that would leave a POSH unit unread is refused.
roles: guard-project
	@GOOGLE_CLOUD_PROJECT=$(PROJECT) $(PY) commands/desk_ops.py --project $(PROJECT) roles --tenant $(TENANT) $(if $(EMAIL),--email "$(EMAIL)",) $(if $(ROLES),--set "$(ROLES)",) $(if $(REVOKE),--revoke "$(REVOKE)",)

# TENANT's case queues from FILE (evals/desk/queues.acme.json is the synthetic tenant's): the POSH units with their
# Internal Committees and Local Committees, the Grievance Redressal Committee, privacy, payroll, the People team and
# the clause-prefix map, into tenant_settings/{TENANT}.case_queues. The file is checked and refused whole when anything
# is wrong; DRY_RUN=1 checks it and writes nothing. Without FILE it prints what is stored and what POSH lacks. Either
# way it lists who could read no case here yet (not_readers): give them their roles with make roles.
desk-queues: guard-project
	@GOOGLE_CLOUD_PROJECT=$(PROJECT) $(PY) commands/desk_ops.py --project $(PROJECT) queues --tenant $(TENANT) $(if $(FILE),--file "$(FILE)",) $(if $(DRY_RUN),--dry-run,)

# TENANT's open cases, soonest due first: id, type (posh, grievance and privacy requests as "sensitive"), queue (in
# your own terminal, so you know whom to chase), status, due_at, and whether each is due within 24 hours
# unacknowledged or breached. No person, no summary.
cases: guard-project
	@GOOGLE_CLOUD_PROJECT=$(PROJECT) $(PY) commands/desk_ops.py --project $(PROJECT) cases --tenant $(TENANT)

# The hourly overdue scan, run once from here, as you: every tenant's due and breached cases, one log line each with
# the id, the queue ("sensitive" for posh, grievance and privacy cases) and due_at only. The job (make desk-job) runs
# the same file on the chat image as chat-sa.
cases-overdue: guard-project
	@PYTHONPATH=. GOOGLE_CLOUD_PROJECT=$(PROJECT) $(PY) services/chat/desk_overdue.py --project $(PROJECT)

# The case queue, live (smoke/smoke_cases.py), after make desk-queues for acme (the gate needs no switch): a POSH
# disclosure through /v1/chat (as documind-evalacme-sa) and /v1/stream (as ui-sa) answered with model none and cost 0;
# a grievance drafted, confirmed twice with one token (one case), seen in documind-evalgrc-sa's inbox, acknowledged
# and closed there; documind-evalzeta-sa's 404 on it; a POSH case pressed twice with one token (one case, no text) for
# IC_EMAIL (default: your gcloud account, which needs ic_member:hyderabad), then withdrawn; the outsider's 403. The
# eval accounts must be on their rosters, the grc account with grc_member (the steps are in the smoke's docstring).
smoke-cases: guard-project
	@NUMBER=$$(gcloud projects describe "$(PROJECT)" --format='value(projectNumber)') || exit 1; \
	case "$$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; no smoke request sent.' >&2; exit 1;; esac; \
	DOCUMIND_CHAT_URL=https://documind-chat-$$NUMBER.$(REGION).run.app DOCUMIND_API_URL=https://documind-api-$$NUMBER.$(REGION).run.app \
	DOCUMIND_OUTSIDER_SA=documind-outsider-sa@$(PROJECT).iam.gserviceaccount.com DOCUMIND_PROJECT=$(PROJECT) DOCUMIND_TENANT=$(TENANT) \
	$(if $(IC_EMAIL),DOCUMIND_IC_EMAIL=$(IC_EMAIL),) $(PY) smoke/smoke_cases.py

# The routed Desk, live (smoke/smoke_desk.py, lesson 10.4), after make desk DESK_ROUTE=on for acme and
# DESK_ROUTE=single DESK_SINGLE=statute for globex: a handbook answer citing acme's objects, a statute answer with its
# in-force lines, a POSH disclosure answered by rule with the POSH card and no model call, an invoice question answered
# out of scope by its anchor, the leaver's denied turn with no retrieval, globex in single mode, /v1/route as an eval
# account and its 403 for ui-sa; then everything make smoke-cases checks. The lane steps are in the smoke's docstring.
smoke-desk: guard-project
	@NUMBER=$$(gcloud projects describe "$(PROJECT)" --format='value(projectNumber)') || exit 1; \
	case "$$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; no smoke request sent.' >&2; exit 1;; esac; \
	DOCUMIND_CHAT_URL=https://documind-chat-$$NUMBER.$(REGION).run.app DOCUMIND_API_URL=https://documind-api-$$NUMBER.$(REGION).run.app \
	DOCUMIND_OUTSIDER_SA=documind-outsider-sa@$(PROJECT).iam.gserviceaccount.com DOCUMIND_PROJECT=$(PROJECT) DOCUMIND_TENANT=$(TENANT) \
	$(if $(IC_EMAIL),DOCUMIND_IC_EMAIL=$(IC_EMAIL),) $(PY) smoke/smoke_desk.py

# The Google Chat door (lesson 10.4): documind-gchat, the bridge (services/gchat/), built and deployed by
# commands/gchat.sh after make plan up GCHAT_DOOR=true has created terraform/gchat.tf's accounts, claims database, topic
# and push subscription (make up also deploys chat again, which lets the bridge's account call it). Deployed only on
# request: a default lane has no bridge, and this refuses. The chat service carries the Desk's side of the door
# (services/chat/delegation.py), so deploy chat again after a kit update. The bridge's image carries its own copy of
# shared/desk_rules.py and shared/desk_law.py (the gate and the fixed replies), so run this again too after a change to
# either, or the door gates by the old rules. Then configure the app in the Google Cloud console (Google Chat API,
# Configuration) and run this again, which binds the app's add-on agent.
deploy-gchat: guard-project tf-backend
	@$(GCHAT_DOOR_ON)
	$(MAKE) build deploy-services SERVICES=gchat SCRIPTS=commands/gchat.sh

# The door's refusals, live (smoke/smoke_gchat.py): POST / and POST /work on the bridge as the outsider are the
# code's 401, not the network's; POST /v1/desk on the chat service with X-DocuMind-Principal, as an eval account and as
# ui-sa, is the 403 "not an allowed delegate". Then the latest gchat, gchat_answer, desk (via gchat) and delegation
# rows. Nobody can mint as the bridge, by design, so the accepted path is proven by a person in Google Chat. Not in
# make smoke-all: a default lane has no bridge, and this refuses.
smoke-gchat: guard-project tf-backend
	@$(GCHAT_DOOR_ON)
	@NUMBER=$$(gcloud projects describe "$(PROJECT)" --format='value(projectNumber)') || exit 1; \
	case "$$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; no smoke request sent.' >&2; exit 1;; esac; \
	DOCUMIND_GCHAT_URL=https://documind-gchat-$$NUMBER.$(REGION).run.app DOCUMIND_CHAT_URL=https://documind-chat-$$NUMBER.$(REGION).run.app \
	DOCUMIND_OUTSIDER_SA=documind-outsider-sa@$(PROJECT).iam.gserviceaccount.com DOCUMIND_PROJECT=$(PROJECT) DOCUMIND_TENANT=$(TENANT) \
	$(PY) smoke/smoke_gchat.py

# The router's eval on the deployed Desk (evals/route_eval.py --live, lesson 10.4): every row of SPLIT (dev unless
# given), as the row's eval account, to POST /v1/route for the decision, and each handbook, statute and denial row to
# POST /v1/desk too, for its answer and citations. It prints the confusion matrix with intervals, escalation recall,
# authority_rate, the router's cost and the p50 and p95 of router_ms and of the desk's latency. ARM=C runs arm C (code
# only, no classifier) on the same rows; ARM=Astar arm A* (one agent with every calculator, no classifier). SAVE=<file>
# keeps the run for route_eval.py --predictions, REPORT=<file> every row's verdict. Every scored row is one router turn
# on your lane (flash-lite, sometimes flash, one embedding) and every answer row one rag-api answer as well; an Astar or
# a calculator row's answer is a few flash calls of its own.
route-eval: guard-project
	@NUMBER=$$(gcloud projects describe "$(PROJECT)" --format='value(projectNumber)') || exit 1; \
	case "$$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; no request sent.' >&2; exit 1;; esac; \
	DOCUMIND_CHAT_URL=https://documind-chat-$$NUMBER.$(REGION).run.app $(PY) evals/route_eval.py --live --project $(PROJECT) --split $(or $(SPLIT),dev) $(if $(ARM),--arm $(ARM),) $(if $(SAVE),--save "$(SAVE)",) $(if $(REPORT),--report "$(REPORT)",)

# The Desk's day in BigQuery (terraform/sql/desk_daily.sql, lesson 10.4): per India day, tenant, desk and kind of
# caller, the turns and their outcomes, the escalations by type with one count for every sensitive case, the method
# mix, the L2 share, the chip re-route rate, the rupees and the p50 and p95 of latency and router_ms; no person, no
# session, no question. Run after the desk rows have landed once, as bq-views is: the sink copies only what is logged
# after make plan up widened it (make smoke-desk writes the first rows), and BigQuery types the sink table's jsonPayload
# from the rows it has seen. The dry run checks the SQL against that table first and creates nothing.
desk-views: guard-project
	bq --project_id=$(PROJECT) query --use_legacy_sql=false --dry_run < terraform/sql/desk_daily.sql
	bq --project_id=$(PROJECT) query --use_legacy_sql=false < terraform/sql/desk_daily.sql
	@echo ">> the router's three alert policies (terraform/desk_alerts.tf) exist only on a lane planned with DESK_ROUTER_ALERTS=true: now that the router has run, make plan up DESK_ROUTER_ALERTS=true, and keep it on every later plan"

# The operators mint ID tokens as the Desk's eval accounts (make smoke-cases, the routed Desk's eval), as make
# operators lets them mint as ui-sa and the outsider; that loop is unchanged. Never the Google Chat bridge's account:
# DESK_EVAL_SAS does not name it, and tools/check_authz.py fails any line in the kit that would let anyone mint as it.
# The overdue job, declared and scheduled hourly (terraform/desk.tf) on the chat image the lane deployed, as
# make reconcile-job declares the nightly reconcile. It is make plan with DESK_JOB=true, then make up's apply: a switch
# the lane was applied with and this run left off would delete something, and the plan's guard refuses that first.
# Without make: commands/infrastructure.py plan with --var desk_job=true and the lane's other --var flags, then apply.
desk-job: DESK_JOB = true
desk-job: guard-project tf-backend
	$(INFRA) plan $(INFRA_FLAGS) $(INFRA_VARS)
	$(INFRA) apply $(INFRA_FLAGS)
	@echo ">> documind-cases-overdue declared on $(CHAT_IMAGE) and scheduled hourly (desk.tf); make cases-overdue runs the same scan now"
	@echo ">> keep DESK_JOB=true on every later make plan, make up, make reconcile-job and make batch-job: without it their plan would delete the job, and the guard refuses it"

desk-operators: guard-project
	@for who in $$(echo "$(ADMIN_EMAILS)" | tr ',' ' '); do for sa in $(DESK_EVAL_SAS); do \
	  gcloud iam service-accounts add-iam-policy-binding $$sa@$(PROJECT).iam.gserviceaccount.com --project=$(PROJECT) \
	    --member="user:$$who" --role=roles/iam.serviceAccountTokenCreator --condition=None --quiet >/dev/null \
	  && echo ">> $$who may mint tokens as $$sa"; done; done
