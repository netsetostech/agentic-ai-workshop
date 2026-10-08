-- The DocuMind Desk's day (workshop lesson 10.4): one row per India day, tenant, desk and kind of caller, from the
-- "desk" rows POST /v1/desk writes (services/chat/desk.py, _desk_row). Surface "route" rows are the eval's dry runs
-- on POST /v1/route, and are not turns. Applied by make desk-views, not by terraform and not by make bq-views.
--
-- What it never holds: a person, a session or a question. The rows carry no question text. The inner SELECT keeps
-- no user and no session column, and nothing is joined to it, so no column of the view can say who asked. A posh,
-- grievance or privacy_request turn arrives with user null and case_type "sensitive", and is one "sensitive" count.
CREATE OR REPLACE VIEW `documind_observability.desk_daily` AS
WITH turns AS (
  SELECT
    DATE(timestamp, "Asia/Kolkata") AS day,
    jsonPayload.tenant AS tenant,
    -- The desk a turn was for: its route; for a denied or not_covered turn, the desk it was routed to (the row's desk
    -- field, as evals/route_eval.py scores it); "fallback" when the router itself failed.
    COALESCE(JSON_VALUE(TO_JSON_STRING(jsonPayload), "$.desk"), jsonPayload.route) AS desk,
    -- people, or service_accounts: the eval accounts (make smoke-desk, make route-eval, every arm but B) and any other
    -- service account. A sensitive turn names nobody, so it counts as people whoever sent it (the smoke's POSH turn).
    IF(ENDS_WITH(IFNULL(jsonPayload.user, ""), ".iam.gserviceaccount.com") OR IFNULL(jsonPayload.arm, "B") != "B",
       "service_accounts", "people") AS callers,
    jsonPayload.outcome AS outcome,
    jsonPayload.method AS method,
    -- desk, case_type, accepted_by and chip are null until something happens (a denial, a case, a model's vote, a
    -- pressed chip), and BigQuery types the sink's jsonPayload only from values it has seen: these four are read from
    -- the row's JSON, so a lane where nobody has pressed a chip yet still gets the view, with no chip turns in it.
    JSON_VALUE(TO_JSON_STRING(jsonPayload), "$.case_type") AS case_type,
    JSON_VALUE(TO_JSON_STRING(jsonPayload), "$.accepted_by") AS accepted_by,
    JSON_VALUE(TO_JSON_STRING(jsonPayload), "$.chip") AS chip,
    CAST(jsonPayload.latency_ms AS INT64) AS latency_ms,
    CAST(jsonPayload.router_ms AS INT64) AS router_ms,
    IFNULL(CAST(jsonPayload.cost_usd AS FLOAT64), 0) AS model_usd,
    IFNULL(CAST(jsonPayload.rag_cost_usd AS FLOAT64), 0) AS rag_usd
  FROM `documind_observability.run_googleapis_com_stdout`
  WHERE jsonPayload.event = "desk" AND jsonPayload.surface = "desk"
)
SELECT
  day,
  tenant,
  desk,
  callers,
  COUNT(*) AS turns,
  -- the outcomes, as services/chat/desk_graph.py outcome() names them
  COUNTIF(outcome = "answer") AS answered,
  COUNTIF(outcome = "grounded_refusal") AS refused,
  COUNTIF(outcome = "clarify") AS clarified,
  COUNTIF(outcome = "denied") AS denied,
  COUNTIF(outcome = "not_covered") AS not_covered,
  COUNTIF(outcome = "oos") AS out_of_scope,
  -- escalations: a case offered or drafted, by type, and posh, grievance and privacy_request as one number; a turn
  -- sent while the person's own draft was open is a draft turn, not a new escalation
  COUNTIF(outcome = "case" AND method != "draft") AS escalations,
  COUNTIF(outcome = "case" AND method != "draft" AND case_type = "exit_dues") AS escalated_exit_dues,
  COUNTIF(outcome = "case" AND method != "draft" AND case_type = "people_query") AS escalated_people_query,
  COUNTIF(outcome = "case" AND method != "draft" AND case_type = "human_requested") AS escalated_human_requested,
  COUNTIF(outcome = "case" AND method != "draft" AND case_type = "sensitive") AS escalated_sensitive,
  COUNTIF(outcome = "case" AND method = "draft") AS draft_turns,
  -- how each turn was decided (desk_router.METHODS)
  COUNTIF(method = "rule") AS method_rule,
  COUNTIF(method = "draft") AS method_draft,
  COUNTIF(method = "single") AS method_single,
  COUNTIF(method = "user") AS method_user,
  COUNTIF(method = "anchor") AS method_anchor,
  COUNTIF(method = "model") AS method_model,
  COUNTIF(method = "arbiter") AS method_arbiter,
  COUNTIF(method = "sticky") AS method_sticky,
  COUNTIF(method = "fallback") AS method_fallback,
  -- the L2 share: turns sent to the arbiter (rule F), as evals/route_eval.py counts "sent to L2"
  COUNTIF(accepted_by = "F") AS to_l2,
  ROUND(SAFE_DIVIDE(COUNTIF(accepted_by = "F"), COUNT(*)), 4) AS l2_share,
  -- the chip re-route rate: turns that reached this desk because the person pressed one of its chips
  COUNTIF(chip IS NOT NULL) AS chip_turns,
  ROUND(SAFE_DIVIDE(COUNTIF(chip IS NOT NULL), COUNT(*)), 4) AS chip_rate,
  -- rupees at 85: the turn's own model calls and the rag-api answers it was billed. rag-api logs those answers on its
  -- own rows too (brain "desk"), which tenant_daily counts, so model_cost_inr is the part tenant_daily lacks.
  ROUND(SUM(model_usd + rag_usd) * 85, 2) AS cost_inr,
  ROUND(SUM(model_usd) * 85, 2) AS model_cost_inr,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(50)] AS p50_ms,
  APPROX_QUANTILES(latency_ms, 100)[OFFSET(95)] AS p95_ms,
  APPROX_QUANTILES(router_ms, 100)[OFFSET(50)] AS p50_router_ms,
  APPROX_QUANTILES(router_ms, 100)[OFFSET(95)] AS p95_router_ms
FROM turns
GROUP BY day, tenant, desk, callers;
