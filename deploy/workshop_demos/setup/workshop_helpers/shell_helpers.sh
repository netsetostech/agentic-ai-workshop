# Shared CLI identities. The audience is explicit; tokens are minted per request.
tok() {
  gcloud auth print-identity-token --include-email --audiences="$1" \
    --impersonate-service-account="documind-ui-sa@$PROJECT.iam.gserviceaccount.com"
}
otok() {
  gcloud auth print-identity-token --include-email --audiences="$API" \
    --impersonate-service-account="documind-outsider-sa@$PROJECT.iam.gserviceaccount.com"
}
# JSON parsing replaces the fragile tr/grep/sed rendering of an environment list.
svc_env() {
  gcloud run services describe "$1" --region "$REGION" --project "$PROJECT" --format=json |
    "$WORKSHOP_PYTHON" -c 'import json,sys; d=json.load(sys.stdin); print(next((r.get("value", "") for r in d["spec"]["template"]["spec"]["containers"][0].get("env", []) if r["name"]==sys.argv[1]), ""))' "$2"
}
setenv() {
  local value
  value="$(svc_env documind-api "$1")" || return
  if [ -n "$value" ]; then export "$1=$value"; else unset "$1"; fi
}
# Make and child scripts must use the interpreter selected in the IDE.
export PY="$WORKSHOP_PYTHON"
