#!/usr/bin/env bash
# make down-region (mk/lane.mk; make down-services depends on it): refuse a teardown aimed at the wrong region.
#
# make down deletes the services by name in REGION, whose Makefile default is us-central1. On 20 October 2026 a down
# without REGION= looked there, found none of an asia-south1 lane's services, and went on to the destroy. When this
# clone prepared PROJECT's lane (infrastructure.py prepare saves its inputs) in another region, stop before anything is
# deleted and print the command that names it. With no saved inputs for PROJECT there is nothing to compare: it passes.
# Usage: PROJECT=<id> REGION=<region> [PY=python] [TF_DIR=terraform] bash commands/down-region.sh
set -euo pipefail
: "${PROJECT:?set PROJECT}" "${REGION:?set REGION}"
INPUTS="${TF_DIR:-terraform}/runbook-project.auto.tfvars.json"
[ -f "$INPUTS" ] || exit 0
saved="$("${PY:-python}" - "$INPUTS" "$PROJECT" <<'PY'
import json, sys
inputs = json.load(open(sys.argv[1], encoding="utf-8"))
print(inputs.get("region", "") if inputs.get("project_id") == sys.argv[2] else "")
PY
)"
if [ -n "$saved" ] && [ "$saved" != "$REGION" ]; then
  echo "STOP: $PROJECT's lane was prepared in $saved ($INPUTS), not REGION=$REGION: make down PROJECT=$PROJECT REGION=$saved" >&2
  exit 2
fi
