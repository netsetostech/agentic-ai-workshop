# ---------- Evaluation (the v5 course's Module 4): the LLM judge against people, lesson 4.5; failures and attacks, 4.9 ----------
# Included by the Makefile (`include mk/*.mk`); every variable it uses is declared there, and each target's own inputs
# take their defaults in the recipe. Each recipe runs one of the kit's own Python scripts, which runs the same way
# without make: evals/build_judge_set.py, evals/judge_agree.py and evals/triage.py (standard library only, Rs 0),
# evals/judge.py, and evals/run_attacks.py - offline, or live once attack-eval has minted the tokens eval-live mints.

# The judge set (lesson 4.5): about twenty of a lane's answers, frozen with the full text of the chunks they cite
# (evals/judge_set.json), so every reader - you, the author, a peer and the judge - reads the same rows. A blank label
# sheet for one person: groundedness and answers_the_question, yes or no, on every row, with the question, the answer
# and the context to read by. It never overwrites a sheet. LABELS= the file (default evals/reports/judge_labels.csv);
# READER= the pseudonymous id on it (default you). Check a filled one: python evals/build_judge_set.py --check FILE.
label-sheet:
	$(PY) evals/build_judge_set.py --emit $(or $(LABELS),evals/reports/judge_labels.csv) --reader $(or $(READER),you)

# Agreement on the judge set, Rs 0. PEOPLE=1: your sheet (LABELS=) against the author's labels of the same rows, or
# AGAINST= another reader's - Cohen's kappa per rubric, the 2x2, the rows you differ on. Without PEOPLE: the judge's
# ratings of the same rows (RUN=, default the author's capture evals/judge_set.ratings.jsonl; make judge-frozen writes
# your own) against your sheet - the true-pass and false-pass rates with Wilson intervals, and kappa. The judge's 1-5
# metric passes at CUT or more (default 4); SWEEP=1 prints every cut.
judge-agree:
	$(PY) evals/judge_agree.py $(if $(PEOPLE),people $(or $(LABELS),evals/reports/judge_labels.csv) $(or $(AGAINST),evals/judge_labels.L1.csv),judge $(or $(RUN),evals/judge_set.ratings.jsonl) $(or $(LABELS),evals/reports/judge_labels.csv) --cut $(or $(CUT),4) $(if $(SWEEP),--sweep,))

# Your lane's judge on the frozen rows (lesson 4.5): judge.py rates the frozen set as it stands - the kit's
# evals/judge_set.json, or your own evals/reports/judge_set.json (4.5's step 3) while the kit has none - with --reuse and
# --no-enrich (the context people labelled), two Vertex AI Evaluation requests a row, nothing asked of the API. Ratings go
# to RUN= (default evals/reports/judge_set.ratings.jsonl). In the judge's venv: PY="$HOME/judge-venv/bin/python".
judge-frozen: guard-project
	@test -n "$(wildcard evals/judge_set.json evals/reports/judge_set.json)" || { echo "no frozen set yet: freeze your own into evals/reports/judge_set.json (lesson 4.5, step 3); the author's evals/judge_set.json ships once recorded" >&2; exit 2; }
	$(PY) evals/judge.py --api-url frozen:$(firstword $(wildcard evals/judge_set.json evals/reports/judge_set.json)) --project $(PROJECT) --reuse $(firstword $(wildcard evals/judge_set.json evals/reports/judge_set.json)) --no-enrich --label frozen --save-rows $(or $(RUN),evals/reports/judge_set.ratings.jsonl) $(JUDGE_ARGS)

# Read the failures first (lesson 4.9): the failing rows of a saved live eval as the gate saw them - the question, the
# verdict, the answer it kept, the citations and, from a run with DOCUMIND_EVAL_PASSAGES=1, the pool - and no cause
# named yet. REPORT= one or more run_eval.py --report files (make eval-live REPORT=...). TEMPLATE= writes the rows to a
# sheet for your notes and causes (never over a file); CLASSES=1 prints the eight causes, each with its lever, and the
# kit's reading of each row; LABELS= your filled sheet, counted by cause. Standard library, offline, Rs 0.
triage:
	$(PY) evals/triage.py $(REPORT) $(if $(TEMPLATE),--template $(TEMPLATE),) $(if $(CLASSES),--classes,) $(if $(LABELS),--labels $(LABELS),)

# The attack set on rag-api's doors (lesson 4.9; lesson 10.8 adds its rows), evals/adversarial/attacks.jsonl, against a
# stand-in that runs rag-api's own door functions: the set checked, every row held with every control on, every
# structural row opened by switching its control off. OFF= switches controls off (roster, iap_identity, filter_check,
# tenant_filter, armor_prompt, refusal_rule) and prints that lane row by row; COMPARE="A B" prints two make attack-eval
# reports side by side instead; SURFACES= the surfaces whose rows run (default api). No credentials, Rs 0.
attack-offline:
	$(PY) evals/run_attacks.py $(if $(COMPARE),--compare $(COMPARE),--offline $(if $(OFF),--off $(OFF),) $(if $(SURFACES),--surfaces $(SURFACES),))

# The attack set against your lane: the member rows as documind-ui-sa, the outsider's as documind-outsider-sa, with
# tokens minted for the API's canonical URL as make eval-live mints them; API= picks the URL to call. REPORT= writes
# every row; LABEL= names the run ("guard off"). The guard is the revision's: run the live revision, then make candidate
# ARMOR=on and run again with API=https://candidate---documind-api-NUMBER.REGION.run.app. Exit 1 when a structural row
# opens or a reply holds another tenant's text. At most eight Gemini answers a run, and on a revision with ARMOR=on one
# Model Armor call for each question that reaches the screen and each answer it screens.
attack-eval: guard-project
	@AUD=https://documind-api-$$(gcloud projects describe $(PROJECT) --format='value(projectNumber)').$(REGION).run.app; \
	API=$${API:-$$AUD}; \
	TOKEN=$${DOCUMIND_ID_TOKEN:-$$(gcloud auth print-identity-token --include-email \
	  --impersonate-service-account=documind-ui-sa@$(PROJECT).iam.gserviceaccount.com --audiences=$$AUD)}; \
	OUTSIDER=$${DOCUMIND_OUTSIDER_TOKEN:-$$(gcloud auth print-identity-token --include-email \
	  --impersonate-service-account=documind-outsider-sa@$(PROJECT).iam.gserviceaccount.com --audiences=$$AUD)}; \
	echo ">> $$API"; DOCUMIND_ID_TOKEN=$$TOKEN DOCUMIND_OUTSIDER_TOKEN=$$OUTSIDER \
	  DOCUMIND_FORGE_EMAIL=$${DOCUMIND_FORGE_EMAIL:-documind-ui-sa@$(PROJECT).iam.gserviceaccount.com} \
	  $(PY) evals/run_attacks.py --api-url $$API $(if $(REPORT),--report $(REPORT),) $(if $(LABEL),--label "$(LABEL)",) $(if $(SURFACES),--surfaces $(SURFACES),)
