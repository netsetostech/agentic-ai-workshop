# ---------- Operations: a lane once it is released (Modules 10 and 11: lessons 11.7 and 10.11) ----------
# Included by the Makefile (`include mk/*.mk`): PROJECT, REGION and PY are its variables; every other name below (ID,
# LIVE, HOURS; SERVICE, POLICY, SINCE, SAVE, OFFLINE, FIXTURE, RUNBOOKS, FAULT, HOLD, RESTORE) is given on the command
# line and read by these targets alone. Each recipe is one line of a script under commands/, which runs the same way
# without make. Its own file, not mk/release.mk: the release's targets are lessons 11.1-11.3's, and these operate the
# lane after it is released (one header, two sections: 13 October 2026).

# ---- Production gotchas, lesson 11.7: each recipe is a subcommand of commands/gotchas.py - python commands/gotchas.py
# list | show <id> | drill [<id>] [--live --project <id> --region <region>] | detect [<id>] --project <id> --region
# <region>. The registry they read is ops/gotchas.json. ----

# The registry, one line a gotcha; ID=<id> prints every field of one. Reads one file.
gotchas:
	@$(PY) commands/gotchas.py $(if $(ID),show $(ID),list)

# A gotcha's offline drill: a stand-in of Cloud Run, or the kit's own code, at Rs 0 with no lane and no credential;
# without ID, every offline drill, each checked for the marker it must print. LIVE=1 runs it on the lane instead, for
# the two drills that have a lane form (pinned-traffic and deploy-drops-hotfix, on documind-chat, each setting put back
# from a finally block); deploy-drops-hotfix's make deploy-services needs ADMIN_EMAILS, as the deploy pages pass it.
gotcha-drill:
	@$(PY) commands/gotchas.py drill $(ID) $(if $(LIVE),--live --project "$(PROJECT)" --region "$(REGION)" --admin-emails "$(ADMIN_EMAILS)",)

# What the lane shows of a gotcha, or of every one without ID. Only reads: gcloud's describe and logging read calls,
# this checkout's deploy/.candidate-revision and deploy/.previous-revision, and one GET of the repository's production
# environment through gh, as make ci-vars makes it. HOURS (24 unless given) is the log reads' window, as for make usage.
gotcha-detect: guard-project
	@$(PY) commands/gotchas.py detect $(ID) --project $(PROJECT) --region $(REGION) $(if $(HOURS),--hours $(HOURS),)

# ---- An incident's plan from rules, and a fault held for it, lesson 10.11: the release's promote, rollback and repair
# are lesson 11.3's, and remediate prints them (make rollback for documind-api) rather than owning them. ----

# An incident's plan, from rules (commands/remediate.py, lesson 10.11). Three gcloud reads at Rs 0 - the service's
# traffic and template, its revisions, and its own log lines of the window (SINCE=, default 1h) - then rules, never a
# model: a revision created inside the window that fails where the revision before it did not gets the rollback, the
# verify and the restore, printed for you to run; remediate runs none of them. SERVICE= the Cloud Run service (default
# documind-chat, or the one the policy watches); POLICY='<display name>' the alert policy that paged: its runbook is the
# policy's own documentation, and a policy ops/runbooks.json gives a person reads nothing. SAVE=<file> keeps what was
# read as a fixture. OFFLINE=1 reads one instead, no PROJECT and no credential: FIXTURE= (default
# ops/incidents/held_model.json, make incident-drill's fault). RUNBOOKS=1 lists every policy and what remediate may do.
remediate: $(if $(or $(OFFLINE),$(RUNBOOKS)),,guard-project)
	@$(PY) commands/remediate.py $(if $(RUNBOOKS),--runbooks,$(if $(OFFLINE),--offline "$(or $(FIXTURE),ops/incidents/held_model.json)",--project $(PROJECT) --region $(REGION) $(if $(SERVICE),--service $(SERVICE),) $(if $(SINCE),--since $(SINCE),) $(if $(SAVE),--save "$(SAVE)",)) $(if $(POLICY),--policy "$(POLICY)",))

# A fault held on the deployed documind-chat for make remediate to diagnose (commands/incident-drill.sh, lesson 10.11).
# FAULT=model (the default): CHAT_MODEL=gemini-3.6-flsh, a mistyped model, and every agent turn fails with a 500.
# FAULT=model_calls: CHAT_MAX_MODEL_CALLS=1, and every agent turn stops at its second model call. HOLD=1 sets it (a new
# revision, which takes the traffic), records it in deploy/.fault-hold, runs make smoke-chat's test once (about four
# turns) and leaves the fault in place; RESTORE=1 puts it back and sends the traffic to the latest revision. Neither:
# nothing changes.
incident-drill: guard-project
	@PROJECT=$(PROJECT) REGION=$(REGION) FAULT=$(FAULT) HOLD=$(HOLD) RESTORE=$(RESTORE) PY=$(PY) bash commands/incident-drill.sh
