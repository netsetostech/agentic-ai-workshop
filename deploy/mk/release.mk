# ---------- Release (the v5 course's Module 11): the keyless pipeline's variables and the key check, lesson 11.1 ----------
# Included by the Makefile (`include mk/*.mk`); every variable it uses is declared there, but GATE_FILE (below). Each
# recipe is a subcommand of commands/release.py and runs the same way without make: python commands/release.py ci-vars
# --project <id> --region <region>, python commands/release.py keys --project <id>. Both only read.

# The four repository variables .github/workflows/documind-cd.yml reads, as the gh variable set lines to run against
# the repository wif.tf trusts: GCP_PROJECT and GCP_REGION from the lane's confirmed inputs, which make plan saved in
# terraform/runbook-project.auto.tfvars.json, and WIF_PROVIDER and CICD_SERVICE_ACCOUNT from terraform output. A REGION
# the lane was not planned in is refused: the Makefile's REGION defaults to us-central1, and a workflow told the wrong
# region builds into a repository that does not exist. With gh installed it reads the repository's production
# environment and warns when there is none, or no required reviewer: GitHub creates a missing environment, unprotected,
# the first time a job names it, and promote would then move traffic with nobody approving.
ci-vars: guard-project
	@$(PY) commands/release.py ci-vars --project $(PROJECT) --region $(REGION) --terraform-dir $(TF_DIR)

# Every service account in the project with its user-managed keys, and the project's parent: org_policy.tf's
# enforce_no_sa_keys needs an organization, so on a personal account's project this check is the control. Exit 1 when
# any key exists, 2 when the check could not finish.
keys-check: guard-project
	@$(PY) commands/release.py keys --project $(PROJECT)

# ---------- The gate on the exact candidate revision, lesson 11.2 ----------
# The gate record: make gate writes it, make promote-gated reads it. evals/reports/ is gitignored, as for make eval-live
# REPORT=. GATE_FILE=<another file> tries a record against promote-gated's rules and leaves this one alone. The same
# without make: python commands/release.py gate (or gate-check) --project <id> --region <region>.
GATE_FILE ?= evals/reports/gate.json

# The live gate, bound to the revision it judges. The revision deploy/.candidate-revision names, which the candidate tag
# must route to; its image digest and GIT_SHA (gcloud run revisions describe); GET /version on the tag URL answering as
# that GIT_SHA; then every golden row asked of the tag URL by evals/run_eval.py, as make eval-live asks them, into
# evals/reports/gate-<revision>.json. The record names the revision, digest and GIT_SHA, the report's sha256, the
# verdict and the time. A red gate writes one too, which promote-gated refuses; a gate that stops after its rows have
# started leaves none, not even the one before it. In CI, documind-cd.yml's candidate path waits on its live gate step
# by job dependency and writes no record; its path=clouddeploy would put run-service.yaml's settings on documind-api,
# and is not to be dispatched.
gate: guard-project
	@$(PY) commands/release.py gate --project $(PROJECT) --region $(REGION) --gate-file $(GATE_FILE)

# make promote, only when the gate record lets it: a green verdict on the revision deploy/.candidate-revision names (the
# candidate tag on no other), with the record's digest and GIT_SHA, a report that still hashes to the record's sha256,
# and a record that is not stale - finished within 24 hours, under the evals/ files this checkout holds. Any other
# revision, a red record, an edited report or a stale record stops here, before promote runs. make promote is unchanged
# and reads no record, so Modules 4-12's experiments still promote a candidate by hand. make up and make deploy-services
# release the API with no gate at all: they move traffic to the revision they have just created.
promote-gated: guard-project
	@$(PY) commands/release.py gate-check --project $(PROJECT) --region $(REGION) --gate-file $(GATE_FILE)
	@$(MAKE) --no-print-directory promote PROJECT=$(PROJECT) REGION=$(REGION)

# ---------- Promote, roll back and repair a controlled failure, lesson 11.3 ----------
# The smokes of the services this lane has deployed (13 October 2026). make smoke-all runs eight, the gateway's and the
# SLM's among them, so on a lane without Module 9's services it is red whatever the API does. This runs smoke-all's own
# smokes, through make and with the exports smoke-all gives them, each only when every Cloud Run service its target
# calls is deployed (gcloud run services list in REGION, and in SLM_REGION for documind-slm), and names each one it
# skips. A smoke's own exit status decides, as in smoke-all.
# Each run appends a line to evals/reports/smoke-deployed.jsonl: the time, the revision serving documind-api, what its
# GET /version said, and every smoke's exit status - the evidence make incident reads. A plain make smoke reads
# DOCUMIND_API_URL from the shell and nothing from PROJECT; this hands it the lane's, as smoke-all does. The recipe
# names no $(MAKE), so make -n prints it and runs nothing; release.py runs the smokes with the make on PATH.
smoke-deployed: guard-project
	@$(PY) commands/release.py smoke-deployed --project $(PROJECT) --region $(REGION) --slm-region $(SLM_REGION) --tenant $(TENANT)

# The incident, from the lane and this checkout's records: documind-api's revisions made in the last HOURS (24), the
# gate record and each revision's gate report, every make smoke-deployed run, and the traffic table, .candidate-revision,
# .previous-revision and spec.template as they are now. Then whether the lane is back in the gated state: the serving
# revision judged green, spec.template what serves, and no red candidate recorded. make rollback moves traffic and leaves
# spec.template as the last update made it, so after a forced make promote of a bad candidate and a rollback the
# template still carries the bad setting, and the next make release-candidate starts from it (env vars merge across
# revisions, F43). The repair is a candidate made from what serves, judged by make gate and promoted by make
# promote-gated; this names its make line. Exit 0 in the gated state, 1 with what is not; it only reads.
incident: guard-project
	@$(PY) commands/release.py incident --project $(PROJECT) --region $(REGION) --gate-file $(GATE_FILE) --hours $${HOURS:-24}
