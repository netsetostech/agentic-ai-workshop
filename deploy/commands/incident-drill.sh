#!/usr/bin/env bash
# make incident-drill FAULT=model|model_calls HOLD=1, later RESTORE=1 (mk/operations.mk): hold a fault on the deployed
# documind-chat for make remediate to diagnose, then put it back (workshop lesson 10.11).
#   FAULT=model        CHAT_MODEL=gemini-3.6-flsh, a mistyped model: every agent turn fails with a 500; direct answers
#   FAULT=model_calls  CHAT_MAX_MODEL_CALLS=1: every agent turn stops at its second model call, a 200 with stopped_by
# HOLD=1 records the variable as it is and the revision serving in deploy/.fault-hold, sets the variable (a new
# revision, which takes the traffic), runs make smoke-chat's test once so the lane holds the fault's own turns, and
# stops with the fault in place: make remediate reads them and prints the plan, and you run it. RESTORE=1 puts the
# variable back as .fault-hold recorded it (a new revision), sends the traffic to the latest revision - a rollback pins
# it to a revision by name, and a pinned service leaves every later revision at 0% - checks that the latest takes it
# all, and removes .fault-hold. Until then every agent turn on the chat fails or stops, so restore in the same sitting.
# limits-drill.sh's pattern (lesson 5.5), copied rather than changed: its trap restores at once, and here the hold is
# the point. About four turns for the hold's smoke. Without HOLD=1 or RESTORE=1 it changes nothing and says how.
# The same without make:  PROJECT=<id> REGION=<region> FAULT=model HOLD=1 bash commands/incident-drill.sh   (from deploy/)
set -euo pipefail
: "${PROJECT:?set PROJECT=<project id>}"
REGION="${REGION:-us-central1}"; FAULT="${FAULT:-model}"; PY="${PY:-python3}"; SVC=documind-chat
HOLD="${HOLD:-}"; RESTORE="${RESTORE:-}"; HOLD_FILE=.fault-hold
case "$FAULT" in
  model)       VAR=CHAT_MODEL; VAL=gemini-3.6-flsh ;;
  model_calls) VAR=CHAT_MAX_MODEL_CALLS; VAL=1 ;;
  *) echo "FAULT must be model or model_calls, not '$FAULT'" >&2; exit 2 ;;
esac
if [ -n "$HOLD" ] && [ -n "$RESTORE" ]; then echo "HOLD=1 or RESTORE=1, not both" >&2; exit 2; fi
if [ -z "$HOLD" ] && [ -z "$RESTORE" ]; then
  echo "make incident-drill changes nothing without HOLD=1 or RESTORE=1:" >&2
  echo "  HOLD=1     sets $VAR=$VAL on $SVC (FAULT=$FAULT), runs its smoke once and leaves the fault in place" >&2
  echo "  RESTORE=1  puts it back as deploy/$HOLD_FILE recorded it and sends the traffic to the latest revision" >&2
  exit 2
fi
svc() { gcloud run services "$@" "$SVC" --project="$PROJECT" --region="$REGION"; }
quietly() {   # svc <verb> ..., quietly: gcloud's progress goes to stderr, and is shown only when the call fails
  local log; log=$(mktemp)
  if svc "$@" --quiet >/dev/null 2>"$log"; then rm -f "$log"; else cat "$log" >&2; rm -f "$log"; return 1; fi
}
env_state() {   # 1 and the variable's value when it is set on the live service, 0 when it is not
  svc describe --format=json | "$PY" -c 'import json, sys
env = json.load(sys.stdin)["spec"]["template"]["spec"]["containers"][0].get("env", [])
hit = [e for e in env if e["name"] == sys.argv[1]]
print("1" + hit[0].get("value", "") if hit else "0", end="")' "$1"
}
serving() {   # the revision that takes all the traffic, or nothing
  svc describe --format=json | "$PY" -c 'import json, sys
t = json.load(sys.stdin)["status"].get("traffic", [])
print(next((x.get("revisionName", "") for x in t if x.get("percent") == 100), ""), end="")'
}
latest_takes_all() {   # the latest revision serves 100 percent: an env change creates a revision that must serve
  svc describe --format=json | "$PY" -c 'import json, sys
t = json.load(sys.stdin)["status"].get("traffic", [])
sys.exit(0 if any(x.get("latestRevision") and x.get("percent") == 100 for x in t) else 1)'
}
held() {   # one field of deploy/.fault-hold
  "$PY" -c 'import json, sys
v = json.load(open(sys.argv[1], encoding="utf-8")).get(sys.argv[2])
print("" if v is None else str(v).lower() if isinstance(v, bool) else v, end="")' "$HOLD_FILE" "$1"
}

if [ -n "$RESTORE" ]; then
  [ -s "$HOLD_FILE" ] || { echo "ERROR: no fault is held here: deploy/$HOLD_FILE is missing (make incident-drill HOLD=1 writes it)." >&2; exit 1; }
  if [ "$(held service)" != "$SVC" ] || [ "$(held project)" != "$PROJECT" ]; then
    echo "ERROR: deploy/$HOLD_FILE holds a fault on $(held service) in $(held project), not on $SVC in $PROJECT." >&2; exit 1
  fi
  VAR=$(held var); BEFORE=$(held before)
  case "$VAR" in CHAT_MODEL|CHAT_MAX_MODEL_CALLS) ;; *) echo "ERROR: deploy/$HOLD_FILE names $VAR, not a variable this drill sets." >&2; exit 1;; esac
  if [ "$(held before_set)" = true ]; then
    quietly update --update-env-vars="$VAR=$BEFORE"; echo ">> $SVC: $VAR=$BEFORE again (a new revision)"
  else
    quietly update --remove-env-vars="$VAR"; echo ">> $SVC: $VAR unset again, so the default applies (a new revision)"
  fi
  quietly update-traffic --to-latest
  latest_takes_all || { echo "ERROR: the latest revision does not take all the traffic: gcloud run services update-traffic $SVC --to-latest --region=$REGION" >&2; exit 1; }
  rm -f "$HOLD_FILE"
  echo ">> restored: $(serving) takes all the traffic, following the latest revision; deploy/$HOLD_FILE removed"
  echo ">> verify: make smoke-chat PROJECT=$PROJECT (every brain answers), then make remediate PROJECT=$PROJECT"
  exit 0
fi

[ ! -e "$HOLD_FILE" ] || { echo "ERROR: deploy/$HOLD_FILE says a fault is already held ($(held var) on $(held revision)): make incident-drill RESTORE=1 first." >&2; exit 1; }
NUMBER=$(gcloud projects describe "$PROJECT" --format='value(projectNumber)')
case "$NUMBER" in ''|*[!0-9]*) echo 'ERROR: gcloud did not return a project number; nothing changed.' >&2; exit 1;; esac
latest_takes_all || { echo "ERROR: $SVC's traffic is pinned away from its latest revision; the fault's revision would take none." >&2
                      echo "       gcloud run services update-traffic $SVC --to-latest --region=$REGION   then run it again." >&2; exit 1; }
STATE=$(env_state "$VAR"); PREV=$(serving)
[ -n "$PREV" ] || { echo "ERROR: no revision of $SVC takes all the traffic; nothing changed." >&2; exit 1; }
# The record first, so that RESTORE=1 always has one. It holds what the variable was: a model name or a call cap.
H_SERVICE="$SVC" H_PROJECT="$PROJECT" H_REGION="$REGION" H_FAULT="$FAULT" H_VAR="$VAR" H_VAL="$VAL" H_STATE="$STATE" \
  H_PREV="$PREV" "$PY" - "$HOLD_FILE" <<'PY'
import datetime, json, os, sys
e = os.environ
record = {"service": e["H_SERVICE"], "project": e["H_PROJECT"], "region": e["H_REGION"], "fault": e["H_FAULT"],
          "var": e["H_VAR"], "value": e["H_VAL"], "before_set": e["H_STATE"][:1] == "1", "before": e["H_STATE"][1:],
          "previous": e["H_PREV"], "revision": "",
          "held_at": datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")}
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(record, f, indent=1)
PY
echo ">> $SVC: $VAR=$VAL (FAULT=$FAULT), held until make incident-drill RESTORE=1"
quietly update --update-env-vars="$VAR=$VAL" || { rm -f "$HOLD_FILE"; echo "ERROR: the update failed; nothing is held." >&2; exit 1; }
latest_takes_all || echo "WARNING: the fault's revision does not take all the traffic." >&2
REV=$(serving)
"$PY" - "$HOLD_FILE" "$REV" <<'PY'
import json, sys
with open(sys.argv[1], encoding="utf-8") as f:
    record = json.load(f)
record["revision"] = sys.argv[2]
with open(sys.argv[1], "w", encoding="utf-8") as f:
    json.dump(record, f, indent=1)
PY
export DOCUMIND_CHAT_URL="https://$SVC-$NUMBER.$REGION.run.app"
export DOCUMIND_IMPERSONATE_SA="documind-ui-sa@$PROJECT.iam.gserviceaccount.com"
rc=0
if [ "$FAULT" = model_calls ]; then
  echo ">> the smoke once, on the fault: every agent brain stops at its second model call"
  DOCUMIND_EXPECT_STOP=model_calls "$PY" smoke/smoke_chat.py || rc=$?
  [ "$rc" = 0 ] || echo "WARNING: the smoke expected every agent brain to stop, and it did not (exit $rc)." >&2
else
  echo ">> the smoke once, on the fault: the three agent brains fail with a 500, and direct answers"
  "$PY" smoke/smoke_chat.py || rc=$?
  [ "$rc" != 0 ] || echo "WARNING: the smoke passed on the fault: did $VAR reach the revision?" >&2
fi
echo ">> held: $REV carries $VAR=$VAL; $PREV served before it (deploy/$HOLD_FILE)"
echo ">> next, once the smoke's lines reach Cloud Logging (a few seconds after they are written): make remediate PROJECT=$PROJECT,"
echo "   run the plan it prints, then make incident-drill RESTORE=1 PROJECT=$PROJECT"
