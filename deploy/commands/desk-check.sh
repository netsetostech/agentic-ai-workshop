#!/usr/bin/env bash
# make desk-check (mk/agents.mk): the DocuMind Desk's offline half - no credential, no cost, part of CI.
# The route set is what build_routes.py builds and every row is sound (--check); the split is by group with no
# identical question across it and no dev row can retrieve itself (--selftest); the eval's metrics, the Wilson figures
# and the probe's readers hold (the tests); the router meets the dev gates on a scripted classifier (--local), the
# threshold sweep counts right (route_threshold.py --selftest), and every calculator rule says what its corpus line
# says (shared/desk_calc.py --selftest). Then the case queue's tests (workshop lesson 5.6), the router's and the
# desk graph's, and the Google Chat door's (10.6), whose second halves need the chat image's libraries: they run in
# ~/graph-venv, made here if it is missing and given the chat pins, as commands/limits-check.sh does and as CI's
# chat-pins step runs them.
# The same without make:  bash commands/desk-check.sh        (from deploy/)
set -euo pipefail
PY="${PY:-python3}"
"$PY" evals/build_routes.py --check
"$PY" evals/route_eval.py --selftest
"$PY" evals/route_probe.py --selftest
"$PY" -m unittest discover -s evals/tests -p test_route_eval.py
"$PY" evals/route_eval.py --local
"$PY" evals/route_threshold.py --selftest
"$PY" shared/desk_calc.py --selftest
VENV="${GRAPH_VENV:-$HOME/graph-venv}"
[ -x "$VENV/bin/python" ] || "$PY" -m venv "$VENV"
"$VENV/bin/pip" install -q -r services/chat/requirements.txt
DOCUMIND_REQUIRE_LIBS=1 "$VENV/bin/python" -m unittest commands/tests/test_cases.py commands/tests/test_desk.py \
  commands/tests/test_gchat.py
