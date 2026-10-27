# ---------- The lane's own bring-up and teardown guards (Module 0: lessons 0.3 and 0.4, 20 October 2026) ----------
# Included by the Makefile (`include mk/*.mk`): PROJECT, REGION, PY and TF_DIR are its variables. make up runs the
# first two, make down-services depends on the third; each recipe is one line of a script under commands/, which runs
# the same way without make. Found on a new lane in an organization project, run end to end from WSL.

# The account Cloud Build runs as, given exactly what a build needs before make build (lesson 0.3's recovery grants).
build-access: guard-project
	@PROJECT=$(PROJECT) REGION=$(REGION) SLM_REGION=$(SLM_REGION) bash commands/build-access.sh

# The views make up applies, deferred until the log sink's table exists (it appears after the API's first answer).
bq-views-when-ready: guard-project
	@PROJECT=$(PROJECT) bash commands/bq-views-when-ready.sh

# make down's region, checked against the one this clone prepared PROJECT's lane in, before anything is deleted.
down-region: guard-project
	@PROJECT=$(PROJECT) REGION=$(REGION) PY=$(PY) TF_DIR=$(TF_DIR) bash commands/down-region.sh
