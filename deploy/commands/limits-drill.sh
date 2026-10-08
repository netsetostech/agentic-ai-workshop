#!/usr/bin/env bash
# make limits-drill STOP=model_calls|turn_budget (mk/agents.mk): trip one of a chat turn's limits on the deployed
# documind-chat, and see the turn still answer HTTP 200 with limits.stopped_by naming it (workshop lesson 5.5).
#   STOP=model_calls   CHAT_MAX_MODEL_CALLS=1: the first model call asks for a search; the second is refused
#   STOP=turn_budget   CHAT_TURN_BUDGET_INR=0.01: the first call costs more than a paisa; the second is refused
# It sets the variable on the service (a new revision), checks that the latest revision takes all the traffic (else
# the smoke would ask the old one), runs make smoke-chat's test expecting the stop from every agent brain, puts the
# variable back as it was - from a trap, so a failure restores it too - and runs the smoke again, which must pass.
# The chat is capped for the minute or two this takes: every turn on it stops. About eight turns in all.
# The same without make:  PROJECT=<id> REGION=<region> STOP=model_calls bash commands/limits-drill.sh
set -euo pipefail
: "${PROJECT:?set PROJECT=<project id>}"
REGION="${REGION:-us-central1}"; STOP="${STOP:-model_calls}"; PY="${PY:-python3}"; SVC=documind-chat
case "$STOP" in
  model_calls) VAR=CHAT_MAX_MODEL_CALLS; VAL=1 ;;
  turn_budget) VAR=CHAT_TURN_BUDGET_INR; VAL=0.01 ;;
  *) echo "STOP must be model_calls or turn_budget, not '$STOP'" >&2; exit 2 ;;
esac
NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
case "$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; nothing changed.' >&2; exit 1;; esac
export DOCUMIND_CHAT_URL="https://$SVC-$NUMBER.$REGION.run.app"
export DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com"
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
latest_takes_all || { echo "ERROR: $SVC's traffic is pinned away from its latest revision; the drill would ask the old one." >&2
                      echo "       gcloud run services update-traffic $SVC --to-latest --region=$REGION   then run it again." >&2; exit 1; }
BEFORE=$(env_value "$VAR")
restore() {
  if [ -n "$BEFORE" ]; then update --update-env-vars="$VAR=$BEFORE"; echo ">> restored $VAR=$BEFORE"
  else update --remove-env-vars="$VAR"; echo ">> restored: $VAR unset, the default applies"; fi
}
trap restore EXIT
echo ">> $SVC: $VAR=$VAL (STOP=$STOP)"
update --update-env-vars="$VAR=$VAL"
latest_takes_all || { echo "ERROR: the new revision does not take all the traffic." >&2; exit 1; }
DOCUMIND_EXPECT_STOP="$STOP" "$PY" smoke/smoke_chat.py
trap - EXIT
restore
latest_takes_all || { echo "ERROR: the restored revision does not take all the traffic." >&2; exit 1; }
echo ">> the same smoke with the limit restored: every brain answers"
"$PY" smoke/smoke_chat.py
