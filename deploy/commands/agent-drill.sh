#!/usr/bin/env bash
# make agent-drill (mk/agents.mk): trip the A2A peer's cap on the deployed documind-agent and see a task end `failed`,
# then the same task complete once the cap is put back (workshop lesson 10.7).
# The cap is ADK_MAX_LLM_CALLS, model calls a task: 12, agent.py's default and what commands/lesson-8.4.sh deploys. At 1
# the task's first model call asks for retrieve and the second is never made: ADK raises LlmCallsLimitExceededError and
# to_a2a ends the task `failed`, with "Max number of llm calls limit of `1` exceeded" as its status message.
# It reads the peer's /health first (no max_llm_calls there: an image from before the cap, and nothing changes), checks
# that the latest revision takes all the traffic (else the task would reach the old one), sets the variable (a new
# revision) and sends make smoke-agent's first task as documind-ui-sa, expecting `failed`. Then it puts the variable back
# as it was - from a trap, so a failure restores it too - and sends the same task, which must complete with its answer.
# The peer is capped for the minute or two this takes: every task on it fails. Two tasks, three model calls in all.
# The same without make:  PROJECT=<id> REGION=<region> bash commands/agent-drill.sh
set -euo pipefail
: "${PROJECT:?set PROJECT=<project id>}"
REGION="${REGION:-us-central1}"; PY="${PY:-python3}"; SVC=documind-agent; VAR=ADK_MAX_LLM_CALLS; VAL=1
NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
case "$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; nothing changed.' >&2; exit 1;; esac
export DOCUMIND_AGENT_URL="https://$SVC-$NUMBER.$REGION.run.app"
export DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com"
# One ID token for the drill, minted as make smoke-agent mints it: as documind-ui-sa, for the peer's url (an hour).
DOCUMIND_AGENT_TOKEN=$(gcloud auth print-identity-token --include-email --audiences="$DOCUMIND_AGENT_URL" \
  --impersonate-service-account="$DOCUMIND_IMPERSONATE_SA")
export DOCUMIND_AGENT_TOKEN
svc() { gcloud run services "$@" "$SVC" --project="$PROJECT" --region="$REGION"; }
update() {   # svc update, quietly: gcloud's deploy progress goes to stderr, and is shown only when the update fails
  local log; log=$(mktemp)
  if svc update "$@" --quiet >/dev/null 2>"$log"; then rm -f "$log"; else cat "$log" >&2; rm -f "$log"; return 1; fi
}
env_value() {   # the variable's value on the live service, or nothing when it is not set
  svc describe --format=json | "$PY" -c 'import json, sys
env = json.load(sys.stdin)["spec"]["template"]["spec"]["containers"][0].get("env", [])
print(next((e.get("value", "") for e in env if e["name"] == sys.argv[1]), ""), end="")' "$1"
}
latest_takes_all() {   # the latest revision serves 100 percent: an env change creates a revision that must serve
  svc describe --format=json | "$PY" -c 'import json, sys
t = json.load(sys.stdin)["status"].get("traffic", [])
sys.exit(0 if any(x.get("latestRevision") and x.get("percent") == 100 for x in t) else 1)'
}
peer() {   # the peer as documind-ui-sa, through smoke/smoke_agent.py's own http() and send(): `peer cap` prints the
           # max_llm_calls /health publishes (nothing when it names none); `peer task STATE` sends the smoke's first
           # task and passes when it ends STATE: failed at the cap, or completed with the smoke's expected answer
  "$PY" - "$@" <<'PY'
import os, sys
sys.path.insert(0, "smoke")
import smoke_agent as s
token = os.environ["DOCUMIND_AGENT_TOKEN"]
if sys.argv[1] == "cap":
    status, body = s.http("/health", token)
    cap = body.get("max_llm_calls") if status == 200 and isinstance(body, dict) else None
    print("" if cap is None else cap, end="")
    sys.exit(0)
want = sys.argv[2]
status, j, text = s.send(token, s.QUESTION)
result = j.get("result") if isinstance(j, dict) else None
task_status = result.get("status") if isinstance(result, dict) else None
state = task_status.get("state") if isinstance(task_status, dict) else None
said = " ".join(p.get("text", "") for p in ((task_status or {}).get("message") or {}).get("parts", []) if isinstance(p, dict))
if want == "failed":
    good, detail = status == 200 and state == "failed" and "llm calls limit" in said.lower(), said or text
else:
    expected = s.expected_answer_pattern(s.QUESTION, os.environ.get("DOCUMIND_SMOKE_EXPECTED_PATTERN", ""))
    good, detail = s.task_answer_matches(status, j, text, expected), text or said
print(f"  [{'PASS' if good else 'FAIL'}] task {want}  status={status} state={state}  {detail[:160]!r}")
if want == "failed" and state == "completed":
    print("  (it completed under a cap of 1: a task that asks for no tool needs one model call and never reaches the cap)")
sys.exit(0 if good else 1)
PY
}
CAP=$(peer cap)
[ -n "$CAP" ] || { echo "ERROR: $SVC's /health names no max_llm_calls: its image is from before the peer's cap; nothing changed." >&2
                   echo "       make build deploy-services SERVICES=agent SCRIPTS=commands/lesson-8.4.sh   then run it again." >&2; exit 1; }
latest_takes_all || { echo "ERROR: $SVC's traffic is pinned away from its latest revision; the drill would ask the old one." >&2
                      echo "       gcloud run services update-traffic $SVC --to-latest --region=$REGION   then run it again." >&2; exit 1; }
BEFORE=$(env_value "$VAR")
restore() {
  if [ -n "$BEFORE" ]; then update --update-env-vars="$VAR=$BEFORE"; echo ">> restored $VAR=$BEFORE"
  else update --remove-env-vars="$VAR"; echo ">> restored: $VAR unset, agent.py's default applies"; fi
}
echo ">> $SVC: /health names max_llm_calls $CAP"
trap restore EXIT
echo ">> $SVC: $VAR=$VAL"
update --update-env-vars="$VAR=$VAL"
latest_takes_all || { echo "ERROR: the new revision does not take all the traffic." >&2; exit 1; }
NOW=$(peer cap)
echo ">> /health: max_llm_calls $NOW"
[ "$NOW" = "$VAL" ] || { echo "ERROR: the peer publishes max_llm_calls ${NOW:-none}, not $VAL: the drill's revision is not serving." >&2; exit 1; }
peer task failed
trap - EXIT
restore
latest_takes_all || { echo "ERROR: the restored revision does not take all the traffic." >&2; exit 1; }
echo ">> /health: max_llm_calls $(peer cap); the same task, with the cap put back"
peer task completed
