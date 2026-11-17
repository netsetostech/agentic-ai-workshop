#!/usr/bin/env bash
# make bq-views-when-ready (mk/lane.mk; the last-but-one step of make up): apply the BigQuery views once the table
# they read exists, and otherwise say when to.
#
# terraform/sql/tenant_daily.sql reads the log sink's table, which BigQuery creates from the first rows the sink
# exports - after the API has answered a request. make up's last steps run before any request, so on a new lane
# make bq-views could only fail ("Not found: Table ...run_googleapis_com_stdout"), and every first make up ended red
# (20 October 2026). make bq-views itself is unchanged: run it after make smoke.
# Usage: PROJECT=<id> bash commands/bq-views-when-ready.sh
set -euo pipefail
: "${PROJECT:?set PROJECT}"
if bq --project_id="$PROJECT" show --format=none documind_observability.run_googleapis_com_stdout >/dev/null 2>&1; then
  make --no-print-directory bq-views PROJECT="$PROJECT"
else
  echo ">> bq-views deferred: the log sink's table appears after the API's first answer - run make bq-views after make smoke"
fi
