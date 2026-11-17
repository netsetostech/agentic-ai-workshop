# ---------- Coding agents (the v5 course's Module 10, lesson 10.10): a Ralph loop, an AI code reviewer and paper-to-code ----------
# Included by the Makefile (`include mk/*.mk`): PY and PROJECT are its variables, RALPH_IMAGE is this file's own, and
# the rest are given on the command line. Each recipe runs one script, the same way without make: commands/ralph.py
# (loop, workspace, check, probe) and commands/review_diff.py. Nothing here touches your lane. The loop works in a run
# directory under your temp directory (OUT= puts it elsewhere, never inside the kit), never applies a patch to your
# clone and never runs git push; the live agent's one credential is RALPH_API_KEY, a model-only key the author creates
# for the run and deletes after it, read from your shell and never a make variable.

# The image the live loop runs its containers from, the agent, the oracle and, with RALPH_EGRESS=proxy, the proxy
# (commands/ralph/Dockerfile): Gemini CLI at GEMINI_CLI_VERSION, pinned below (npm's latest release on 22 October 2026,
# which the batch-1 probe confirms or moves), and Python 3.12; no gcloud, no credential. Built from commands/ralph/
# alone, so no other kit file enters it. Cloud Shell's docker storage does not outlive the session: build it again in
# each one.
RALPH_IMAGE ?= documind-ralph
GEMINI_CLI_VERSION ?= 0.65.0

ralph-image:
	@[ -n "$(GEMINI_CLI_VERSION)" ] || (echo "ERROR: GEMINI_CLI_VERSION is empty: leave it at the kit's pin, or set GEMINI_CLI_VERSION=<x.y.z> (npm view @google/gemini-cli version)"; exit 1)
	docker build --build-arg GEMINI_CLI_VERSION=$(GEMINI_CLI_VERSION) -t $(RALPH_IMAGE) -t $(RALPH_IMAGE):$(GEMINI_CLI_VERSION) commands/ralph

# The Ralph loop (commands/ralph.py loop, workshop lesson 10.10): statutory_deadline cut out of a copy of
# shared/desk_calc.py, an agent started fresh each iteration on commands/ralph/PROMPT.md, and an oracle it cannot see
# (commands/ralph/oracle.py) after each one; it stops when the oracle passes, at RALPH_MAX_ITERS (8) or at
# RALPH_BUDGET_INR, and undoes an iteration that changes more than RALPH_MAX_DIFF_LINES (80) lines or anything outside
# the function. TASK=deadline (an engineer's spec, the default) or statute (paper-to-code: the statute's lines alone);
# ORACLE=strong (the default) or weak (desk_calc's own selftest, which a hard-coded date passes). OFFLINE=1: a scripted
# agent, no model, no network, Rs 0. Otherwise Gemini CLI headless in RALPH_IMAGE, gemini-3.6-flash unless RALPH_MODEL:
# RALPH_BUDGET_INR is required (set it from a dry run of RALPH_MAX_ITERS=1), RALPH_API_KEY must be in your shell, and
# RALPH_PROJECT adds GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION=global to the agent's environment when the batch-1
# probe says the key needs them. DRY_RUN=1 prints the two docker run lines and starts nothing. It prints each
# iteration's item, verdict, lines, tokens and rupees, and leaves ralph.patch, kit.patch and summary.json in the run.
ralph:
	@$(PY) commands/ralph.py loop $(if $(OFFLINE),--offline,) $(if $(DRY_RUN),--dry-run,) --task $(or $(TASK),deadline) --oracle $(or $(ORACLE),strong) $(if $(RALPH_MAX_ITERS),--max-iters $(RALPH_MAX_ITERS),) $(if $(RALPH_BUDGET_INR),--budget-inr $(RALPH_BUDGET_INR),) $(if $(RALPH_MAX_DIFF_LINES),--max-diff-lines $(RALPH_MAX_DIFF_LINES),) $(if $(RALPH_MODEL),--model $(RALPH_MODEL),) --image $(RALPH_IMAGE) $(if $(RALPH_PROJECT),--project $(RALPH_PROJECT),) $(if $(OUT),--out "$(OUT)",) $(if $(RALPH_EGRESS),--egress $(RALPH_EGRESS),)

# The workspace a loop starts from, and nothing else (TASK=, OUT=): the cut shared/desk_calc.py, PROMPT.md, spec.md,
# fix_plan.md, GEMINI.md and oracle.md, with its git repository beside it and no remote. For one iteration by hand: run
# gemini in it in its default approval mode, then make ralph-check WORKSPACE=<its path>. Offline, Rs 0.
ralph-workspace:
	@$(PY) commands/ralph.py workspace --task $(or $(TASK),deadline) $(if $(OUT),--out "$(OUT)",)

# The oracles' verdicts, offline and free (commands/ralph.py check). With nothing given: the task's start, the kit's
# own statutory_deadline and the six seeded defects of commands/ralph/seeds.json under the weak and the strong oracle,
# each verdict held to its label (exit 1 when one differs, or when a seed no longer fits the kit's function); SHOW=<name>
# prints a version's diff and its failed checks. PATCH=<file> judges a patch, against the task's start or the kit's own
# file; WORKSPACE=<dir> judges a workspace as you left it, and writes its change beside it as by-hand.patch.
ralph-check:
	@$(PY) commands/ralph.py check --task $(or $(TASK),deadline) $(if $(PATCH),--patch "$(PATCH)",) $(if $(WORKSPACE),--workspace "$(WORKSPACE)",) $(if $(SHOW),--show $(SHOW),)

# The batch-1 probe (commands/ralph.py probe): docker's server, the image's Gemini CLI version, that the oracle's
# container (--network none) cannot reach example.com, and what the agent's container holds - its environment's names
# and its mount points, read from inside it on the loop's own docker run line with a dummy key - all free; with YES=1
# and RALPH_API_KEY in your shell, two headless calls in the agent's container: one prints Gemini CLI's JSON stats as
# the loop prices them, one asks for a web fetch, which the excluded web tools must refuse. A few rupees: Gemini CLI
# sends its own long system prompt with every request.
# RALPH_EGRESS=proxy, here and on make ralph (off unless given; off, nothing changes): each agent container joins an
# internal network of its own, with no route out, and reaches only aiplatform.googleapis.com:443, through a proxy the
# loop starts beside it for the iteration and removes after it (commands/ralph/egress.py, in a third container of
# RALPH_IMAGE), keeping its log in the run. The probe then adds three free checks from inside the agent's container:
# example.com and the metadata server's address unreachable directly, the proxy refusing example.com and opening a
# tunnel to the model endpoint; with YES=1 its two calls go through the proxy, whose log names each host they asked for.
ralph-probe:
	@$(PY) commands/ralph.py probe --image $(RALPH_IMAGE) $(if $(RALPH_MODEL),--model $(RALPH_MODEL),) $(if $(RALPH_PROJECT),--project $(RALPH_PROJECT),) $(if $(YES),--yes,) $(if $(RALPH_EGRESS),--egress $(RALPH_EGRESS),)

# An AI code reviewer on one diff of shared/desk_calc.py (commands/review_diff.py): DIFF= a run's ralph.patch, or the
# by-hand.patch make ralph-check WORKSPACE= wrote. Its findings, each a rule of the reviewer's rubric with a line and a
# reason. One gemini-3.6-flash call on location global (MODEL=, THINKING=), as you, with google-genai in your shell;
# OFFLINE=1: a linter stands in, Rs 0.
review-diff: $(if $(OFFLINE),,guard-project)
	@[ -n "$(DIFF)" ] || (echo "ERROR: DIFF=<a patch of shared/desk_calc.py>: a run's ralph.patch, or by-hand.patch"; exit 1)
	@$(PY) commands/review_diff.py --diff "$(DIFF)" $(if $(OFFLINE),--offline,--project $(PROJECT)) $(if $(MODEL),--model $(MODEL),) $(if $(THINKING),--thinking $(THINKING),)

# The reviewer scored on the seeded defects (commands/review_diff.py --eval): the kit's own statutory_deadline and the
# six seeded versions, each diff reviewed REPEAT times (1 unless given); per diff, the runs that found its seeded rule
# and the false alarms, then the catch count a run and the rupees. Seven calls a repeat, on your lane; OFFLINE=1, the
# linter, Rs 0; SAVE=<file> keeps every finding with the model and the date, FROM=<file> rescores one at Rs 0.
review-eval: $(if $(or $(OFFLINE),$(FROM)),,guard-project)
	@$(PY) commands/review_diff.py --eval $(if $(FROM),--from "$(FROM)",$(if $(OFFLINE),--offline,--project $(PROJECT))) --repeat $(or $(REPEAT),1) $(if $(MODEL),--model $(MODEL),) $(if $(THINKING),--thinking $(THINKING),) $(if $(SAVE),--save "$(SAVE)",)
