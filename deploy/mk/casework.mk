# ---------- The Case Room (after Module 10): one employee's full and final settlement carried as a case ----------
# Included by the Makefile (`include mk/*.mk`); PY is its variable. The Case Room report of 25 October 2026 designs a
# team of agents that carries one case from the acknowledged resignation to a payroll hand-over, under the Labour
# Codes' clocks. Phase 0 is its case set (evals/ff_cases.jsonl) and the statutory floor under it (shared/ff_floor.py),
# drafted by a model for the author's review. Rs 0 and standard library: no model, no lane, no PROJECT. Its own file:
# lessons quote mk/agents.mk by line, and a target appended there would move them.

# The case set checked (evals/case_eval.py --check): every case's lines recomputed by shared/desk_calc.py from its facts
# and the corpus, each argument bound to the fact it stands for, every note's gate class held, every point a floor
# entry's, and the outcome following from the rest; then the statutory floor's selftest, each corpus quote read at its
# lines. It ends by counting the cases a person has reviewed. REVIEW=1 prints the set and the floor as markdown for that
# review instead.
case-check:
	$(PY) evals/case_eval.py $(if $(REVIEW),--review,--check)

# The Case Room, offline (commands/case_room.py, Phase 1): every case of evals/ff_cases.jsonl through ARMS (comma-
# separated: astar, lplus, swarm; all three unless given), SLICE (case ids or their prefixes, tags or outcomes) and
# SAVE=<file>; each run scored on its answer and, for L+ and S, on the case, then S paired with L+ against the margin
# evals/paired.py registered, and each with A*. CASE=<id> prints that one case's run on ARM (swarm unless given)
# instead: the registrar's events, the board's lines and clocks, the statement and the hand-over. OFFLINE=1 is the only
# mode so far: the scripted model and the kit's corpus, no PROJECT, Rs 0. REPLAY=<file> and COMPARE="A B" rescore saved
# runs at Rs 0 with no venv; the rest runs in ~/graph-venv with the chat image's pins (commands/agent-turn.sh).
case-eval:
	@$(if $(or $(REPLAY),$(COMPARE)),$(PY),OFFLINE=1 PY=$(PY) bash commands/agent-turn.sh) $(if $(CASE),commands/case_room.py --offline --case $(CASE) $(if $(ARM),--arm $(ARM),),evals/case_eval.py $(if $(REPLAY),--replay $(REPLAY),$(if $(COMPARE),--compare $(COMPARE),--offline)) $(if $(ARMS),--arms $(ARMS),) $(if $(SLICE),--slice $(SLICE),) $(if $(SAVE),--save "$(SAVE)",))

# The Case Room's own tests, offline and free: the case set and the floor (stdlib), then the Case Room on its scripted
# model (commands/tests/test_case_room.py) in ~/graph-venv with the chat image's pins, as CI's chat-pins step runs it.
case-tests:
	$(PY) -m unittest discover -s evals/tests -p test_ff_cases.py
	@OFFLINE=1 DOCUMIND_REQUIRE_LIBS=1 PY=$(PY) bash commands/agent-turn.sh -m unittest commands/tests/test_case_room.py -v
