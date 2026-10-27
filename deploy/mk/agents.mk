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
	DOCUMIND_CHAT_URL=https://documind-chat-$$NUMBER.$(REGION).run.app $(PY) evals/route_eval.py --live --project $(PROJECT) --split $(or $(SPLIT),dev) $(if $(ARM),--arm $(ARM),) $(if $(SAVE),--save "$(SAVE)",) $(if $(REPORT),--report "$(REPORT)",) $(if $(ROUTES),--routes "$(ROUTES)",)

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

# ---------- the agent bench (workshop lessons 10.1-10.3 and 10.5): one task set, many agent patterns ----------
# Appended below every Desk target, and so are the bench's next targets: lesson 10.4's page reads route-eval's recipe
# by its line number in this file.
#
# One turn of an agent pattern, printed whole (commands/agent_turn.py): each model call with its thinking and visible
# tokens and rupees, each tool it asked for, its arguments and what it returned, then the answer as the Desk shows it
# and the figure check. PATTERN=loop (the Desk agent's own loop, commands/agent_patterns.py, which the patterns of
# lessons 10.1-10.3 join), THINKING=minimal|low|medium|high (unset: the desk agent's, low), DESK=astar|handbook|statute
# (astar by default: one retrieve over every class, every calculator), TENANT, Q (unset: the gratuity row of
# evals/agent_tasks.jsonl) or ROW (a row's id, as chained-exit-e3), and for 10.2's plan_execute and rewoo EXEC_MODEL
# (the act and extract calls' model; unset: the planner's). OFFLINE=1 needs no PROJECT: a scripted model and the kit's
# own corpus, Rs 0, and takes INVENT and LAUNDER (1, or a figure: --invent and --launder, 10.1 and 10.3). Otherwise one
# real turn on your lane: a few gemini-3.6-flash calls on global, under the chat service's 12 calls and Rs 5, and
# rag-api's /v1/passages as documind-ui-sa. In ~/graph-venv with the chat image's pins: commands/agent-turn.sh.
agent-turn: $(if $(OFFLINE),,guard-project)
	@PROJECT=$(PROJECT) REGION=$(REGION) PATTERN=$(PATTERN) THINKING=$(THINKING) DESK=$(DESK) TENANT=$(TENANT) Q="$(Q)" ROW=$(ROW) EXEC_MODEL=$(EXEC_MODEL) OFFLINE=$(OFFLINE) INVENT="$(INVENT)" LAUNDER="$(LAUNDER)" PY=$(PY) bash commands/agent-turn.sh

# The task set scored (evals/agent_eval.py). CHECK=1 recomputes every row's figure with shared/desk_calc.py and runs
# the hard gate on every question; REPLAY=<file> (or several, space-separated) rescores saved runs, BEST_OF=N keeping
# the run of each row the figure check chooses; COMPARE="A B" pairs two saved arms (Newcombe's interval and an exact
# McNemar test, evals/paired.py). Those three are Rs 0 and need no venv. Otherwise every row through each of PATTERNS
# (comma-separated) at each of THINKING (comma-separated; default is the desk agent's own), on DESK (astar, or row for
# each row's own desk), RUNS times (pass@k and pass^k), SLICE (kinds, tags or ids: chained, lesson 10.2's rows),
# SAVE=<file>, and plan_execute and rewoo at each of EXEC_MODEL (comma-separated; default is the planner's own):
# OFFLINE=1 on the scripted model, Rs 0; on your lane each row and run is one agent turn, as make agent-turn's, and a
# verify run up to three (lesson 10.3). PATTERNS=loop,verify, or a REPLAY of both arms' saves, also prints pass@1,
# pass@k re-rolls and best-of-k beside verify's pass@3 with notes, each with its calls and rupees. In ~/graph-venv:
# commands/agent-turn.sh.
agent-eval: $(if $(or $(OFFLINE),$(CHECK),$(REPLAY),$(COMPARE)),,guard-project)
	@$(if $(or $(CHECK),$(REPLAY),$(COMPARE)),$(PY),PROJECT=$(PROJECT) REGION=$(REGION) OFFLINE=$(OFFLINE) PY=$(PY) bash commands/agent-turn.sh) evals/agent_eval.py $(if $(CHECK),--check,$(if $(REPLAY),--replay $(foreach f,$(REPLAY),"$(f)"),$(if $(COMPARE),--compare $(COMPARE),$(if $(OFFLINE),--offline,--live)))) $(if $(PATTERNS),--patterns $(PATTERNS),) $(if $(THINKING),--thinking $(THINKING),) $(if $(DESK),--desk $(DESK),) $(if $(RUNS),--runs $(RUNS),) $(if $(SLICE),--slice $(SLICE),) $(if $(BEST_OF),--best-of $(BEST_OF),) $(if $(SAVE),--save "$(SAVE)",) $(if $(EXEC_MODEL),--exec-model $(EXEC_MODEL),)

# The bench's own tests, offline and free: paired.py's arithmetic and the task set's check and scorer (stdlib), then
# the patterns on a scripted model (commands/tests/test_agent_bench.py, lesson 10.1's test_agent_patterns.py, lesson
# 10.2's test_agent_plans.py and lesson 10.3's test_agent_verify.py) in ~/graph-venv with the chat image's pins, as
# CI's chat-pins step runs them.
agent-tests:
	$(PY) -m unittest discover -s evals/tests -p test_paired.py
	$(PY) -m unittest discover -s evals/tests -p test_agent_eval.py
	@OFFLINE=1 DOCUMIND_REQUIRE_LIBS=1 PY=$(PY) bash commands/agent-turn.sh -m unittest commands/tests/test_agent_bench.py -v
	@OFFLINE=1 DOCUMIND_REQUIRE_LIBS=1 PY=$(PY) bash commands/agent-turn.sh -m unittest commands/tests/test_agent_patterns.py -v
	@OFFLINE=1 DOCUMIND_REQUIRE_LIBS=1 PY=$(PY) bash commands/agent-turn.sh -m unittest commands/tests/test_agent_plans.py -v
	@OFFLINE=1 DOCUMIND_REQUIRE_LIBS=1 PY=$(PY) bash commands/agent-turn.sh -m unittest commands/tests/test_agent_verify.py -v

# Lesson 10.5: a desk run as an agent, beside the other arms on the same rows. ROUTES=evals/route_arms.jsonl on make
# route-eval (its recipe passes ROUTES as --routes) scores lesson 10.5's arms set instead of the route set: five rows a
# calculator decides, jn-03 and six lookups, all dev, every figure recomputed by evals/tests/test_route_arms.py. Run it
# once an arm, ARM=B, C and Astar, each with its own SAVE= and REPORT=: each desk turn keeps its sections' modes,
# refused tool calls and calculations, and its model calls, rupees and latency. On your lane every row is a router turn
# and a desk turn, and an answer in agent mode (every Astar row) a few flash calls of its own.
# route-compare: the arms side by side (evals/route_eval.py --compare, Rs 0). REPORTS= two or three of those reports,
# one split and one arm each: per arm the correct and authority rates with their intervals, the desk turns' rupees,
# model calls and p50 and p95 latency, and the turns in agent mode; then B paired against each other arm by row id,
# through evals/paired.py and the margin registered there before any run. Indicative: dev rows only, and B's exemplar
# index holds the rows taken from evals/routes.jsonl.
route-compare:
	$(PY) evals/route_eval.py --compare $(foreach f,$(REPORTS),"$(f)")

# arms-combine: the arms as an ensemble (evals/combine.py, Rs 0). SAVES= the saved runs (SAVE=) of one split, one arm
# each, on the rows of ROUTES (evals/route_arms.jsonl unless given): each answer row's members right or wrong; where a
# member ran a calculator, a vote over the (calculator, value) pairs code returned, a tie abstaining to a person; and
# every figure a member's answer writes that no calculation returned and no source holds (shared/desk_calc.py's
# unsupported()). python evals/combine.py --selftest --layers 2 adds an arbiter and a mixture-of-agents aggregator, on
# scripted members.
arms-combine:
	$(PY) evals/combine.py $(foreach f,$(SAVES),"$(f)") $(if $(ROUTES),--routes "$(ROUTES)",)

# A person in the loop (workshop lesson 5.8), offline and free: services/chat/approval.py, which the chat service does
# not import, on scripted models. A withdrawal waits for a second person (the requester's own approval is refused) and
# a second process resumes it from the same SQLite checkpoint file; a rejection errors that call alone; the person who
# asked answers a clarifying question; a case is offered with nothing written. In ~/graph-venv with the chat image's
# pins and the local lane's SQLite checkpointer (made, or completed, here). See commands/approval-check.sh.
approval-check:
	@PY=$(PY) bash commands/approval-check.sh

# The classifier's examples on and off (workshop lesson 3.2): evals/route_eval.py with the L1 prompt's examples swapped
# for one run, in process - EXEMPLARS=kit (desk_routes.PROMPT_EXEMPLARS, the eight; the default), none, or a JSON file
# of [row id, route, question] - on the same 187 dev rows, the groups of the kit's eight still left out of the score. It
# prints the usual report, the examples used and "L1 alone": flash-lite's own route on the turns it was asked, before
# the vote and the arbiter; REPORT=<file> writes each row's verdict and decision as JSON. On your lane (--live-l1,
# google-genai in the shell): 126 rows reach flash-lite, the disputed ones flash, one embedding each, the 198-row index
# embedded first; RUNS=3 asks every row three times. LOCAL=1 runs it offline on the scripted classifier, which reads no
# example: the arms then differ in the router's cost alone, what the eight cost in prompt tokens (Rs 0, no PROJECT).
exemplars: $(if $(LOCAL),,guard-project)
	$(PY) evals/route_eval.py $(if $(LOCAL),--local,--live-l1 --project $(PROJECT)) --exemplars $(or $(EXEMPLARS),kit) $(if $(RUNS),--runs $(RUNS),) $(if $(REPORT),--report "$(REPORT)",)

# The A2A peer's own cap (workshop lesson 10.7): ADK_MAX_LLM_CALLS=1 on the deployed documind-agent for a minute or
# two, make smoke-agent's first task ends `failed` with the limit in its status message, the variable is put back from
# a trap, and the same task completes. Two tasks, three model calls. See commands/agent-drill.sh.
agent-drill: guard-project
	@PROJECT=$(PROJECT) REGION=$(REGION) PY=$(PY) bash commands/agent-drill.sh

# The chat's hand-off to the A2A peer (workshop lesson 10.7), on, or off with OFF=1: PEER_URL and PEER_ACCOUNT on
# documind-chat, one env update and a new revision. The ADK brain may then hand a question to the peer, two a turn and
# 75 s each at most, and only for a tenant whose roster is the peer account's one roster. The next make
# deploy-services switches it off again. No model call. See commands/handoff.sh.
handoff: guard-project
	@PROJECT=$(PROJECT) REGION=$(REGION) OFF=$(OFF) PY=$(PY) bash commands/handoff.sh

# The hand-off, live: a question about what the corpus holds, to the ADK brain as documind-ui-sa, comes back with
# documind_peer among its tool calls and the hand-off in the response's handoffs; the LangChain brain answers the same
# question with none. Two turns. See smoke/smoke_handoff.py.
smoke-handoff: guard-project
	@NUMBER=$$(gcloud projects describe $(PROJECT) --format='value(projectNumber)'); \
	DOCUMIND_CHAT_URL=https://documind-chat-$$NUMBER.$(REGION).run.app \
	DOCUMIND_IMPERSONATE_SA=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com \
	  $(PY) smoke/smoke_handoff.py

# The caller graph (workshop lesson 10.7), offline and free: the account each request-path service runs as and the
# accounts its deploy script binds roles/run.invoker, read from the scripts terraform/sa.tf's graph names, as service
# edges; then `acyclic` with an order, or the first cycle and exit 1. GRAPH=1 is the only mode so far: no gcloud, so
# the bindings as the scripts make them, not as the lane holds them. See commands/check_callers.py.
check-callers:
	$(PY) commands/check_callers.py $(if $(GRAPH),--graph,)

# The A2A peer's tool pins (workshop lesson 10.8): review the tools the peer gets from its MCP server and pin each
# one's name, description and input schema, or, with CHECK=1, fail when the server's tools have drifted from the pins.
# URL=... lists a running server over the MCP wire; the default lists the kit's own server in process (offline, no
# gcloud, no model call). The peer only enforces the pins when TOOL_PINS=on. See commands/pin_tools.py.
pin-tools:
	$(PY) commands/pin_tools.py $(if $(CHECK),--check,) $(if $(URL),--url $(URL),--server-local)

# A poisoned MCP server on 127.0.0.1 for the pins drill (workshop lesson 10.8), a fixture that binds nowhere real and
# names only .invalid hosts: an extra unpinned tool, or RUG=1 for a rug-pulled description. Point the peer at it
# (MCP_URL) with TOOL_PINS off, then on, to watch the pins refuse it. See evals/adversarial/evil_mcp.py.
evil-mcp:
	@PORT=$(or $(PORT),8900) RUG=$(RUG) $(PY) evals/adversarial/evil_mcp.py

# The kit's MCP server in the local profile (workshop lesson 10.8), as make chat-local serves the chat service: no token
# and no roster (services/mcp/server.py's LOCAL_USER and LOCAL_TENANT), acme's corpus in the Chroma directory make
# chat-local seeds, served on 127.0.0.1:8000 (PORT= another). The A2A peer runs beside it on your machine with
# MCP_URL=http://127.0.0.1:8000 and MCP_AUTH=none, so make attack-agents SURFACES=peer needs nobody to mint a token as
# documind-agent-sa. With no roster, a tenant the model names is taken as given (server.py's _tenant_for): a question
# about another tenant finds only what this store holds, acme's corpus, where the lane's server refuses it by the
# roster. PY's venv needs services/mcp/requirements.txt and the Chroma pins of services/chat/requirements-local.txt
# (langchain-chroma, chromadb); no Ollama and no embedding model, since the local retrieve ranks chunks by their words.
# No model call, Rs 0. Seeding upserts, so re-running is harmless.
mcp-local:
	DOCUMIND_PROFILE=local DOCUMIND_CHROMA_DIR="$(CURDIR)/documind_chroma" $(PY) -m shared.local_corpus acme
	cd services/mcp && DOCUMIND_PROFILE=local DOCUMIND_CHROMA_DIR="$(CURDIR)/documind_chroma" PYTHONPATH=../.. \
	  $(PY) -m uvicorn server:app --host 127.0.0.1 --port $(or $(PORT),8000)

# The attack set on the agents' doors (workshop lesson 10.8), as make attack-eval runs it on rag-api's: lesson 10.8's
# rows to documind-chat's /v1/chat and /v1/desk as documind-ui-sa, with a token minted for the chat service's canonical
# URL as make eval-live mints rag-api's (DOCUMIND_ID_TOKEN, when set, instead); CHAT= picks the URL to call. SURFACES=
# the surfaces whose rows run (default chat,desk): peer sends the A2A peer's row to the peer on your own machine
# (DOCUMIND_PEER_URL, default http://127.0.0.1:8080) over make mcp-local's server, and SURFACES=peer alone mints
# nothing and needs no PROJECT. REPORT= writes every row, LABEL= names the run; make attack-offline COMPARE="A B" sets
# two side by side. Exit 1 when a structural row opens or a reply holds another tenant's text. Each chat or Desk row is
# one turn on your lane (a few flash calls and one rag-api answer); the peer row one task. See commands/attack-agents.sh.
attack-agents: $(if $(filter peer,$(SURFACES)),,guard-project)
	@PROJECT=$(PROJECT) REGION=$(REGION) SURFACES=$(SURFACES) CHAT=$(CHAT) REPORT="$(REPORT)" LABEL="$(LABEL)" PY=$(PY) bash commands/attack-agents.sh

# Two agents that hand one question back and forth, and the cap that ends it (workshop lesson 10.7's loops and
# deadlocks), offline and free: two ADK desks that may transfer the turn to each other and to their root, under a
# TransferCap plugin that ends the turn after 3 transfers, once with transfers between the desks allowed and once with
# them disallowed. OFFLINE=1 is the only mode so far: scripted models, no PROJECT, Rs 0. In ~/graph-venv with the chat
# image's pins (commands/agent-turn.sh). See commands/agent_shapes.py.
agent-shapes:
	@OFFLINE=1 PY=$(PY) bash commands/agent-turn.sh commands/agent_shapes.py $(if $(OFFLINE),--offline,)

# A company's agent_actions switch (workshop lesson 5.8), in tenant_settings/{TENANT} beside the Desk's (a merge write).
# AGENT_ACTIONS=approval gives the LangGraph brain services/chat/approval.py's approve node for that company: a
# withdrawal a model asks for pauses the turn as an approval record (shared/approvals.py) that a second person holding
# doc_approver decides at POST /v1/approvals/{id}/decide, and the paused conversation answers 409 until then; the model
# may also ask the person one question (ask_user) or offer a case (offer_case). AGENT_ACTIONS=off, what every company
# has until an operator writes approval, is the brain as lessons 5.4, 5.5 and 5.7 show it. The chat service reads it
# within 60 s. Without AGENT_ACTIONS it prints the company's switches. The approver is a role: make roles TENANT=acme
# EMAIL=<second person> ROLES=employee,doc_approver.
agent-actions: guard-project
	@GOOGLE_CLOUD_PROJECT=$(PROJECT) $(PY) commands/desk_ops.py --project $(PROJECT) desk --tenant $(TENANT) $(if $(AGENT_ACTIONS),--actions $(AGENT_ACTIONS),)

# An approved withdrawal, run by the operator (workshop lesson 5.8): services/ingest/reconcile.py --approved re-reads
# approvals/{APPROVAL}, checks it again (approved and not yet run, by a second person who still holds doc_approver in
# that company, for that company's document), withdraws the document exactly as make retire does (the tombstone; make
# restore SOURCE= is the way back) and marks the record withdrawn, with the kit's one doc.withdraw audit event. The
# approval on the chat service withdraws nothing by itself: this run does. DRY=1 runs the checks and writes nothing.
withdraw-run: guard-project
	@test -n "$(APPROVAL)" || (echo "APPROVAL=<approval id> is required (GET /v1/approvals lists them)"; exit 2); 	PYTHONPATH=. MANAGED_MIRROR=$(MANAGED_MIRROR) RAG_LOCATION=$(RAG_LOCATION) AUDIT_BUCKET=$(PROJECT)-audit GOOGLE_CLOUD_PROJECT=$(PROJECT) 	DOCUMIND_OPERATOR=$${DOCUMIND_OPERATOR:-$$(gcloud config get-value account 2>/dev/null)} 	  $(PY) services/ingest/reconcile.py --project $(PROJECT) --approved "$(APPROVAL)" $(if $(DRY),,--apply)

# The approval wired in, live (smoke/smoke_approval.py; about Rs 10-15 of model calls), after make agent-actions
# TENANT=acme AGENT_ACTIONS=approval and doc_approver for documind-evalacme-sa: a withdrawal asked for as documind-ui-sa
# pauses the turn (200, approval pending); the same session's next question is held (409); the requester's own approval
# is refused (403); documind-evalzeta-sa cannot see the record (404); documind-evalacme-sa approves it (200, approved,
# the resumed turn's answer) and a second decision is refused (409); a second withdrawal is rejected with a reason, and
# the resumed turn's refusals name the tool. It withdraws nothing: it prints the make withdraw-run for the approval it
# left, and the make restore after that. DOC= names the document (default townhall_2026_q1.md). Not in make smoke-all.
smoke-approval: guard-project
	@NUMBER=$$(gcloud projects describe "$(PROJECT)" --format='value(projectNumber)') || exit 1; 	case "$$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; no smoke request sent.' >&2; exit 1;; esac; 	DOCUMIND_CHAT_URL=https://documind-chat-$$NUMBER.$(REGION).run.app DOCUMIND_PROJECT=$(PROJECT) DOCUMIND_TENANT=$(TENANT) 	$(if $(DOC),DOCUMIND_DOC=$(DOC),) $(PY) smoke/smoke_approval.py
