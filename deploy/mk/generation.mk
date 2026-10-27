# ---------- Generation (the v5 course's Module 3): the generator's prompt, its knobs and its version ----------
# Included by the Makefile (`include mk/*.mk`); every variable it uses is declared there. Each target runs one script,
# and the script runs the same way without make.

# The prompt bench (evals/prompt_bench.py, lessons 3.1, 3.2 and 3.3): each golden row's pool read once from your lane's
# /v1/passages, as documind-ui-sa, then held fixed while the kit's own generate() (services/rag-api/generator.py,
# imported in your shell: pip install -r services/rag-api/requirements.txt once) answers it at each thinking level, with
# or without a temperature, with SYSTEM's rules edited in memory; generator.py is never written. Every answer is judged
# by the eval gate's rule. BENCH_ARGS names the rows and the arms: "--rows lk-06 --runs 5 --levels LOW,HIGH",
# "--shape join --levels LOW,MEDIUM,HIGH", "--from-report evals/reports/live.json --failing --shape refusal
# --add-rule '...'", "--temperature 2.0", "--drop-rule 5", "--model gemini-3.1-flash-lite", "--show", "--report FILE".
# One Gemini call an answer (two when one is cut off and asked again), billed to your lane; it prints the rupees.
bench: guard-project
	@AUD=https://documind-api-$$(gcloud projects describe $(PROJECT) --format='value(projectNumber)').$(REGION).run.app; \
	API=$${API:-$$AUD}; \
	TOKEN=$${DOCUMIND_ID_TOKEN:-$$(gcloud auth print-identity-token --include-email \
	  --impersonate-service-account=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com --audiences=$$AUD)}; \
	echo ">> $$API"; DOCUMIND_ID_TOKEN=$$TOKEN GOOGLE_CLOUD_PROJECT=$(PROJECT) \
	  $(PY) evals/prompt_bench.py --api-url $$API $(BENCH_ARGS)

# The prompt bound to its version (lesson 3.6): the label the rag-api answers under (config.py's prompt_id@prompt_version,
# what /version reports), the sha256 of generator.py's SYSTEM followed by DATED_RULE, and whether
# services/rag-api/prompt_versions.json registers that label with that sha256. Exit 1 when the text changed and the
# version did not: a changed prompt needs a new version, registered beside the old ones. Offline: no project, no
# credential, Rs 0.
prompt-version:
	$(PY) commands/prompt_pin.py

# Eval-gated self-improvement (lesson 12.4), beside prompt-version because it changes the generator's prompt by version.
# A production answer that went wrong becomes a proposed rule, a person accepts it as the next prompt version, and the
# gate judges that version on a candidate before any traffic moves. ROW= is the production row, a JSON file (the shape is
# in evals/improve.py's docstring): the question in your own words, the lane's answer, and what a right answer holds.
# make improve ROW=... asks gemini-3.1-pro-preview, on the global endpoint and under a JSON schema, for one rule (about
# Rs 2, printed), checks it with services/rag-api/prompt_rules.py and writes evals/reports/proposal.json;
# IMPROVE_ARGS="--rule '...'" proposes your own rule with no model call, and IMPROVE_ARGS=--prompt-only prints what the
# proposer is sent. make improve REVIEWER=you@example.com accepts the proposal: the next version in
# services/rag-api/prompt_rules.json, and the R(...) row to paste into evals/build_golden.py (lesson 4.1). improve.py
# never writes run_eval.py, required.json or the golden set. No guard-project: accepting is offline, and a model's
# proposal stops without PROJECT.
improve:
	$(PY) evals/improve.py $(if $(REVIEWER),accept --reviewer "$(REVIEWER)",propose --row "$(ROW)" --project "$(PROJECT)") $(IMPROVE_ARGS)

# The accepted version on a candidate: make release-candidate's update of documind-api (the image make build pushed for
# this commit, no traffic, tagged candidate, recorded by name for make promote) with PROMPT_VERSION set on it, so
# config.py's default stays v3 and the new version answers only where the variable is set. make gate judges it; make
# promote-gated moves traffic to it. The variable stays in the service's template, promoted or not: make
# release-candidate and make candidate carry it to their revisions (an update merges the environment) until make
# deploy-services sets the environment whole (lesson 12.2's script) or make prompt-candidate PROMPT_VERSION=v3 puts the
# default back. A version prompt_rules.json does not list stops here, before gcloud; an image without it does not start.
prompt-candidate: guard-project
	@$(PY) evals/improve.py version "$(PROMPT_VERSION)"
	gcloud run services update documind-api --region $(REGION) --project $(PROJECT) --image $(IMAGE_REPO)/api:$(GIT_SHA) --no-traffic --tag candidate --update-env-vars GIT_SHA=$(GIT_SHA),PROMPT_VERSION=$(PROMPT_VERSION) --quiet
	@$(MAKE) --no-print-directory record-candidate PROJECT=$(PROJECT) REGION=$(REGION)
	@NUMBER=$$(gcloud projects describe $(PROJECT) --format='value(projectNumber)'); \
	echo ">> candidate: https://candidate---documind-api-$$NUMBER.$(REGION).run.app answers as $(PROMPT_VERSION) (make gate, then make promote-gated)"
