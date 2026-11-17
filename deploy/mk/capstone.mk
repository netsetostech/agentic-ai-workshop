# ---------- Capstone (the v5 course's Module 11): the independent capstone and the operational handover, lesson 11.8 ----------
# Included by the Makefile (`include mk/*.mk`); PY, PROJECT, REGION and SLM_REGION are its variables. FORK, the fork's
# checkout (. unless given, the kit), is given on the command line and declared nowhere: make replay (mk/memory.mk)
# reads a FORK of its own. Both recipes run commands/capstone_check.py, standard library, and only read; the same
# without make: python commands/capstone_check.py check --fork <dir> [--project <id> --region <region>], and handover
# the same way. Neither needs PROJECT, so neither has guard-project. Its own file, not mk/release.mk, where the plan put
# it (13 October 2026): lessons 11.1-11.3 quote release.mk from their sections to its last line.

# The capstone rubric's eight components, PASS or FAIL each, and never a score: whether each exists in the fork and a
# stranger can verify it. Without PROJECT it reads the fork's files at Rs 0 with no credential - ARCHITECTURE.md,
# COST-MODEL.md, FAILURE-MODES.md and RUNBOOK.md, the corpus and golden rows, and the records make smoke-deployed and
# make gate leave in evals/reports/ - and runs the fork's evals/run_eval.py offline, as make eval does. PROJECT= adds
# the lane's reads, still Rs 0: GET /version as documind-ui-sa, GET /v1/sources as documind-ui-sa and as the outsider
# (a 403), documind-ui's IAP, the services deployed and documind-api's revisions. Exit 1 when a component fails: an
# incomplete submission, which the defence does not run. The four documents start from capstone/templates/ (13 October
# 2026): copied as they ship they still fail, until their {{...}} placeholders are replaced.
# PROJECT counts only from make's command line, in both recipes: every lesson's shell exports one, and on 22 October 2026
# the offline check of the canned fork read the lane instead, and failed components 1, 2, 4 and 8.
capstone-check:
	@$(PY) commands/capstone_check.py check --fork "$(or $(FORK),.)" $(if $(filter command line,$(origin PROJECT)),--project $(PROJECT) --region $(REGION) --slm-region $(SLM_REGION),)

# HANDOVER.md, written into the fork whole: the alert policies, the night job, the floors, the revisions, the CI trust,
# the budget and the state bucket, as this checkout states them and, with PROJECT, as the lane shows them. On the lane
# it only reads (gcloud's describe and list calls, and the Monitoring API's alert policies); a read that fails is
# listed under Not read, the rest is written, and the exit is 1.
handover:
	@$(PY) commands/capstone_check.py handover --fork "$(or $(FORK),.)" $(if $(filter command line,$(origin PROJECT)),--project $(PROJECT) --region $(REGION) --slm-region $(SLM_REGION),)
