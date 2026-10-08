"""The DocuMind Desk's operations (workshop lessons 5.6 and 10.4): the log sink's Desk events, the desk_daily view
(terraform/sql/desk_daily.sql) and the Desk's log-based metrics and alert policies (terraform/desk_alerts.tf).

    python -m unittest commands/tests/test_desk_operations.py          (from deploy/)

Standard library only, and no cloud: the Terraform and the SQL are read as text and held to the rows the Desk's code
writes, so a renamed field, outcome or method fails here rather than as an empty view or an alert that never fires.
The privacy rules are checked the same way: no view column, metric label or alert names a person, a session, a case or
a question, and a sensitive case is one count. terraform validate and the SQL's dry run (make desk-views) are the
checks a lane gives.
"""
from __future__ import annotations

import ast
import re
import sys
import unittest
from pathlib import Path

KIT = Path(__file__).resolve().parents[2]
for p in (str(KIT / "services/chat"), str(KIT / "evals"), str(KIT)):
    if p not in sys.path:
        sys.path.insert(0, p)
import desk_router  # noqa: E402
import route_threshold  # noqa: E402
from shared import desk_law, desk_recall, prices  # noqa: E402

TF = KIT / "terraform"
SINK = (TF / "sink.tf").read_text(encoding="utf-8")
ALERTS = (TF / "desk_alerts.tf").read_text(encoding="utf-8")
VIEW = (TF / "sql/desk_daily.sql").read_text(encoding="utf-8")
DESK_PY = (KIT / "services/chat/desk.py").read_text(encoding="utf-8")
GRAPH_PY = (KIT / "services/chat/desk_graph.py").read_text(encoding="utf-8")
OVERDUE_PY = (KIT / "services/chat/desk_overdue.py").read_text(encoding="utf-8")
DOOR_PY = (KIT / "services/rag-api/desk_door.py").read_text(encoding="utf-8")
DESK_EVENTS = ["desk", "passages", "desk_shadow", "desk_gate"]
ROUTER_POLICIES = ["desk_fallback_share", "desk_l2_share", "desk_clarify_oos_trend"]
GATE_POLICIES = ["desk_gate_error_share"]
SWITCH = {**{n: "desk_router_alerts" for n in ROUTER_POLICIES}, **{n: "desk_gate_alerts" for n in GATE_POLICIES}}
# What no column, label or alert may carry: a person, a session, a case, or any text a person wrote.
PERSONAL = {"user", "email", "session_id", "requester", "caller", "case_id", "question", "summary", "name", "delegate",
            "chosen_contacts", "assertion"}


def block(text: str, head: str) -> str:
    """One top-level block, from its header line to the closing brace at column 0."""
    i = text.index(head)
    return text[i:text.index("\n}\n", i) + 2]


def heredoc(b: str) -> str:
    """The text of the block's first <<EOT ... EOT."""
    return b.split("<<EOT\n", 1)[1].split("\n  EOT", 1)[0]


def names(kind: str) -> list[str]:
    return re.findall(rf'^resource "{kind}" "(\w+)"', ALERTS, re.M)


def row_keys(func: str) -> set[str]:
    """The keys of the dict literal a desk.py row builder returns."""
    fn = next(n for n in ast.parse(DESK_PY).body if isinstance(n, ast.FunctionDef) and n.name == func)
    ret = next(n for n in ast.walk(fn) if isinstance(n, ast.Return) and isinstance(n.value, ast.Dict))
    return {k.value for k in ret.value.keys if isinstance(k, ast.Constant)}


def promql(name: str) -> str:
    """A query local (desk_fallback_query, desk_l2_query, desk_trend_query, desk_gate_error_query) as Terraform renders
    it: the join of its lines, each ${local.x} and each bare local.x element replaced by that local's string."""
    loc = "".join(re.findall(r"^locals \{\n.*?^\}\n", ALERTS, re.M | re.S))
    one = {k: v.replace('\\"', '"') for k, v in re.findall(r'^  (desk_\w+) += "(.*)"$', loc, re.M)}

    def sub(x: str) -> str:
        return re.sub(r"\$\{local\.(\w+)\}", lambda m: sub(one[m.group(1)]), x)
    body = loc.split(f"  {name}", 1)[1].split("join(", 1)[1].split("\n  ])", 1)[0]
    lines = []
    for el in re.findall(r'^    ("(.*)"|local\.(\w+)),$', body, re.M):
        lines.append(sub(el[1].replace('\\"', '"')) if el[0].startswith('"') else sub(one[el[2]]))
    return "\n".join(lines)


class SinkTests(unittest.TestCase):
    def test_the_sink_copies_the_desk_events_and_still_never_media(self):
        f = heredoc(block(SINK, 'resource "google_logging_project_sink" "api_to_bq" {'))
        self.assertEqual(re.findall(r'jsonPayload\.event = "(\w+)"', f), ["query", "stream", "chat"] + DESK_EVENTS)
        self.assertEqual(re.findall(r'service_name = "([\w-]+)"', f), ["documind-api", "documind-chat", "documind-chat"])
        self.assertNotIn("media", f)

    def test_no_sensitive_row_is_copied_beside_its_turns_chat_row(self):
        f = heredoc(block(SINK, 'resource "google_logging_project_sink" "api_to_bq" {'))
        # rag-api's door answers a brain's search words inside a chat turn, whose chat row names the person: only the
        # chat door's desk_gate rows are copied, and a sensitive shadow row stays in Cloud Logging
        self.assertIn('(jsonPayload.event = "desk_gate" AND resource.labels.service_name = "documind-chat")', f)
        self.assertIn('(jsonPayload.event = "desk_shadow" AND NOT jsonPayload.case_type = "sensitive")', f)
        self.assertEqual(f.count('jsonPayload.event = "desk_gate"'), 1)
        self.assertEqual(f.count('jsonPayload.event = "desk_shadow"'), 1)
        # a shadow row names nobody exactly when its case_type is "sensitive" (desk_router.record())
        self.assertIn('"user": None if sensitive else email', DESK_PY)
        self.assertIn('sensitive = rec["sensitivity_tier"] == "sensitive"', DESK_PY)
        self.assertIn('if out["sensitivity_tier"] == "sensitive":\n        out["case_type"] = "sensitive"',
                      (KIT / "services/chat/desk_router.py").read_text(encoding="utf-8"))
        self.assertIn('"case_type": rec["case_type"]', DESK_PY.split("def _shadow_row(", 1)[1])

    def test_the_chat_doors_gate_hit_runs_no_brain(self):
        """The chat door logs desk_gate and answers the turn itself: chat() never runs, so there is no chat row for
        that turn, and no shadow row either (the shadow runs in _pass, beside chat())."""
        door = DESK_PY.split("class ChatDoor:", 1)[1].split("\n# ----", 1)[0]
        call = door.split("    async def __call__(self, scope, receive, send):", 1)[1]
        after = call.split('log.info(json.dumps({"event": "desk_gate", "surface": "chat",', 1)[1]
        self.assertTrue(after.split("\n        return ", 1)[1].startswith("await _reply(send, 200, "))
        self.assertNotIn("self.app", after)
        self.assertNotIn("_pass(", after)
        self.assertIn("_shadow(scope, question, tenant)", door.split("async def _pass(", 1)[1].split("async def __call__", 1)[0])

    def test_each_desk_event_is_a_line_the_kit_writes(self):
        self.assertIn('return {"event": "desk", "surface": surface,', DESK_PY)
        self.assertIn('return {"event": "desk_shadow", "surface": "chat",', DESK_PY)
        self.assertIn('{"event": "desk_gate", "surface": "chat",', DESK_PY)
        self.assertIn('{"event": "desk_gate", "surface": surface,', (KIT / "services/rag-api/desk_door.py").read_text(encoding="utf-8"))
        self.assertIn('"passages", modality=', (KIT / "services/rag-api/main.py").read_text(encoding="utf-8"))

    def test_no_desk_row_carries_the_question(self):
        for func in ("_desk_row", "_shadow_row"):
            self.assertFalse(row_keys(func) & {"question", "summary", "masked_question", "text"}, func)


class ViewTests(unittest.TestCase):
    turns = VIEW.split("WITH turns AS (", 1)[1].split("\n)\nSELECT", 1)[0]
    outer = VIEW.split("\n)\nSELECT", 1)[1]

    def test_it_reads_the_desk_turns_only(self):
        self.assertIn('WHERE jsonPayload.event = "desk" AND jsonPayload.surface = "desk"', self.turns)
        self.assertIn("FROM `documind_observability.run_googleapis_com_stdout`", self.turns)
        self.assertEqual(self.outer.rstrip().splitlines()[-1], "GROUP BY day, tenant, desk, callers;")

    def test_no_column_names_a_person_and_nothing_is_joined(self):
        code = "\n".join(line.split("--", 1)[0] for line in VIEW.splitlines())
        self.assertNotRegex(code.upper(), r"\bJOIN\b|\bUNNEST\b|\bUNION\b")
        inner = re.findall(r"\bAS (\w+),?$", self.turns.split("\n  FROM", 1)[0], re.M)       # each column's alias
        outer = re.findall(r"\bAS (\w+),?$", self.outer, re.M)
        self.assertFalse(set(inner + outer) & PERSONAL, (inner, outer))
        self.assertEqual(inner, ["day", "tenant", "desk", "callers", "outcome", "method", "case_type", "accepted_by", "chip",
                                 "latency_ms", "router_ms", "model_usd", "rag_usd"])
        # the person is read once, to tell people from service accounts, and kept nowhere
        self.assertEqual(len(re.findall(r"jsonPayload\.user\b", code)), 1)
        self.assertIn('ENDS_WITH(IFNULL(jsonPayload.user, ""), ".iam.gserviceaccount.com")', code)

    def test_every_field_it_reads_is_a_field_of_the_desk_row(self):
        keys = row_keys("_desk_row")
        direct = set(re.findall(r"jsonPayload\.(\w+)", self.turns))
        by_json = set(re.findall(r'JSON_VALUE\(TO_JSON_STRING\(jsonPayload\), "\$\.(\w+)"\)', self.turns))
        self.assertEqual(by_json, {"desk", "case_type", "accepted_by", "chip"})
        self.assertLessEqual(direct | by_json, keys | {"event"})

    def test_the_outcomes_are_the_desk_graphs(self):
        graph = next(n for n in ast.parse(GRAPH_PY).body if isinstance(n, ast.Assign)
                     and getattr(n.targets[0], "id", "") == "OUTCOMES")
        named = set(ast.literal_eval(graph.value).values()) | {"answer", "grounded_refusal"}
        self.assertIn('return "answer" if any(s.get("answerable") for s in sections) else "grounded_refusal"', GRAPH_PY)
        self.assertEqual(set(re.findall(r'outcome = "(\w+)"', self.outer)), named)

    def test_one_sensitive_count_and_the_other_types_by_name(self):
        types = set(re.findall(r'case_type = "(\w+)"', self.outer))
        self.assertEqual(types, (set(desk_law.CASE_TYPES) - desk_law.SENSITIVE_CASES) | {"sensitive"})
        self.assertFalse(types & desk_law.SENSITIVE_CASES)
        self.assertIn('COUNTIF(outcome = "case" AND method != "draft" AND case_type = "sensitive") AS escalated_sensitive', self.outer)

    def test_the_method_mix_is_the_routers(self):
        self.assertEqual(re.findall(r'COUNTIF\(method = "(\w+)"\) AS method_\1', self.outer), list(desk_router.METHODS))

    def test_l2_share_chip_rate_rupees_and_the_quantiles(self):
        self.assertIn('ROUND(SAFE_DIVIDE(COUNTIF(accepted_by = "F"), COUNT(*)), 4) AS l2_share', self.outer)
        self.assertIn("ROUND(SAFE_DIVIDE(COUNTIF(chip IS NOT NULL), COUNT(*)), 4) AS chip_rate", self.outer)
        self.assertIn(f"ROUND(SUM(model_usd + rag_usd) * {prices.USD_INR}, 2) AS cost_inr", self.outer)
        for col in ("latency_ms", "router_ms"):
            for q in (50, 95):
                self.assertRegex(self.outer, rf"APPROX_QUANTILES\({col}, 100\)\[OFFSET\({q}\)\] AS p{q}_")

    def test_desk_views_dry_runs_then_creates(self):
        mk = (KIT / "mk/agents.mk").read_text(encoding="utf-8")
        rec = mk.split("desk-views: guard-project\n", 1)[1].split("\n\n", 1)[0].splitlines()
        self.assertEqual(rec[:2], ["\tbq --project_id=$(PROJECT) query --use_legacy_sql=false --dry_run < terraform/sql/desk_daily.sql",
                                   "\tbq --project_id=$(PROJECT) query --use_legacy_sql=false < terraform/sql/desk_daily.sql"])
        self.assertEqual(len(rec), 3)
        self.assertTrue(rec[2].startswith('\t@echo ">> ') and "DESK_ROUTER_ALERTS=true" in rec[2])     # the router's alerts
        makefile = (KIT / "Makefile").read_text(encoding="utf-8")
        self.assertRegex(makefile, r"\.PHONY:(?:[^\n]*\\\n)*[^\n]* desk-views\b")
        self.assertNotIn("desk_daily", makefile)               # make bq-views and make up stay as they were


class AlertTests(unittest.TestCase):
    def test_the_metrics_and_the_policies(self):
        self.assertEqual(names("google_logging_metric"), ["desk_router", "case_overdue", "doc_type_pin_miss",
                                                          "desk_delegation_refused", "desk_gate_check",
                                                          "desk_check_tenants_unread"])
        self.assertEqual(names("google_monitoring_alert_policy"), ["desk_fallback_share", "desk_l2_share",
                                                                   "desk_clarify_oos_trend", "case_overdue",
                                                                   "doc_type_pin_miss", "desk_delegation_refused",
                                                                   "desk_gate_error_share", "desk_check_tenants_unread"])
        alerts_tf = (TF / "alerts.tf").read_text(encoding="utf-8")
        for n in names("google_logging_metric") + names("google_monitoring_alert_policy"):
            self.assertNotIn(f'"{n}"', alerts_tf, n)

    def test_no_label_names_a_person_a_case_or_text(self):
        allowed = {"tenant", "event", "route", "method", "accepted_by", "queue", "state", "outcome"}
        for n in names("google_logging_metric"):
            b = block(ALERTS, f'resource "google_logging_metric" "{n}" {{')
            keys = re.findall(r'key += "(\w+)"', b)
            extracted = re.findall(r'^    (\w+) += "EXTRACT\(jsonPayload\.(\w+)\)"', b, re.M)
            self.assertEqual(sorted(keys), sorted(k for k, _ in extracted), n)
            self.assertLessEqual({k for k, _ in extracted} | {f for _, f in extracted}, allowed, n)
            self.assertNotIn("value_extractor", b, n)
        for n in ("desk_delegation_refused", "desk_check_tenants_unread"):
            self.assertEqual(re.findall(r'key += "(\w+)"', block(ALERTS, f'resource "google_logging_metric" "{n}" {{')), [], n)

    def test_the_router_counts_people_on_the_desk_and_in_shadow(self):
        f = heredoc(block(ALERTS, 'resource "google_logging_metric" "desk_router" {'))
        self.assertIn('resource.labels.service_name="documind-chat"', f)
        self.assertIn('((jsonPayload.event="desk" AND jsonPayload.surface="desk" AND jsonPayload.arm="B") OR '
                      'jsonPayload.event="desk_shadow")', f)
        self.assertIn('NOT jsonPayload.user=~"[.]iam[.]gserviceaccount[.]com$"', f)
        self.assertIn('"arm": arm or "B"', DESK_PY)                     # every person's turn is arm B
        for field in ("route", "method", "accepted_by", "tenant"):
            self.assertIn(field, row_keys("_desk_row") & row_keys("_shadow_row"))

    def test_every_policy_reads_a_metric_this_file_declares_and_pages_the_lane(self):
        declared = {re.search(r'name    = "([^"]+)"', block(ALERTS, f'resource "google_logging_metric" "{n}" {{')).group(1): n
                    for n in names("google_logging_metric")}
        for n in names("google_monitoring_alert_policy"):
            b = block(ALERTS, f'resource "google_monitoring_alert_policy" "{n}" {{')
            read = set(re.findall(r'logging\.googleapis\.com/user/([\w/]+)', b))
            if "condition_prometheus_query_language" in b:
                q = re.search(r"query += local\.(\w+)", b).group(1)
                read = {f"documind/{m}" for m in re.findall(r"logging_googleapis_com:user_documind_(\w+)\{", promql(q))}
            self.assertTrue(read and read <= set(declared), (n, read))
            self.assertIn("notification_channels = local.alert_channel_ids", b, n)
            self.assertEqual(re.findall(r"depends_on += \[google_logging_metric\.(\w+)\]", b), [declared[m] for m in sorted(read)], n)
            doc = b.split("documentation {", 1)[1]
            self.assertNotRegex(doc, r"[\w.-]+@[\w-]+\.", n)          # no address in the text an incident carries
            self.assertNotRegex(b, r"\$\{each\.", n)
            counts = re.findall(r"^  count +=.*$", b, re.M)
            self.assertEqual(counts, [f"  count        = var.{SWITCH[n]} ? 1 : 0"] if n in SWITCH else [], n)

    def test_the_router_policies_are_opt_in(self):
        v = block(ALERTS, 'variable "desk_router_alerts" {')
        self.assertIn("type        = bool", v)
        self.assertIn("default     = false", v)
        self.assertEqual(names("google_monitoring_alert_policy")[:3], ROUTER_POLICIES)
        for n in ROUTER_POLICIES:
            self.assertIn("condition_prometheus_query_language {", block(ALERTS, f'resource "google_monitoring_alert_policy" "{n}" {{'))
        self.assertNotRegex(block(ALERTS, 'resource "google_logging_metric" "desk_router" {'), r"count\s+=")   # its series come first
        mk = (KIT / "mk/agents.mk").read_text(encoding="utf-8")
        self.assertIn("\nDESK_ROUTER_ALERTS ?= false\nTF_EXTRA_VARS += -var desk_router_alerts=$(DESK_ROUTER_ALERTS)\n", mk)
        self.assertNotIn("DESK_ROUTER_ALERTS", (KIT / "Makefile").read_text(encoding="utf-8"))

    def test_the_gate_checks_share_is_opt_in(self):
        v = block(ALERTS, 'variable "desk_gate_alerts" {')
        self.assertIn("type        = bool", v)
        self.assertIn("default     = false", v)
        for n in GATE_POLICIES:
            self.assertIn("condition_prometheus_query_language {", block(ALERTS, f'resource "google_monitoring_alert_policy" "{n}" {{'))
        for n in ("desk_gate_check", "desk_check_tenants_unread"):          # their series come first, on every lane
            self.assertNotRegex(block(ALERTS, f'resource "google_logging_metric" "{n}" {{'), r"count\s+=", n)
        self.assertNotIn("condition_prometheus_query_language",
                         block(ALERTS, 'resource "google_monitoring_alert_policy" "desk_check_tenants_unread" {'))
        mk = (KIT / "mk/agents.mk").read_text(encoding="utf-8")
        self.assertIn("\nDESK_GATE_ALERTS ?= false\nTF_EXTRA_VARS += -var desk_gate_alerts=$(DESK_GATE_ALERTS)\n", mk)
        self.assertNotIn("DESK_GATE_ALERTS", (KIT / "Makefile").read_text(encoding="utf-8"))
        rec = mk.split("\ndesk: guard-project\n", 1)[1].split("\n\n", 1)[0].splitlines()
        self.assertTrue(rec[-1].startswith('\t$(if $(filter on,$(DESK_GATE)),@echo ">> ') and "DESK_GATE_ALERTS=true" in rec[-1])
        infra = (KIT / "commands/infrastructure.py").read_text(encoding="utf-8")
        self.assertIn('"DESK_ROUTER_ALERTS", "DESK_GATE_ALERTS",', infra)    # the plan's refusal names it

    def test_the_gate_check_metric_reads_the_lines_both_doors_write(self):
        b = block(ALERTS, 'resource "google_logging_metric" "desk_gate_check" {')
        f = heredoc(b)
        self.assertIn('(resource.labels.service_name="documind-chat" OR resource.labels.service_name="documind-api")', f)
        self.assertIn('jsonPayload.event="desk_gate_check"', f)
        self.assertEqual(re.findall(r'EXTRACT\(jsonPayload\.(\w+)\)', b), ["tenant", "outcome"])
        row = desk_recall.row("chat", "acme", desk_recall.unavailable())
        self.assertEqual(row["event"], "desk_gate_check")
        self.assertLessEqual({"tenant", "outcome"}, set(row))
        self.assertFalse(set(row) & PERSONAL)
        self.assertEqual(row["outcome"], "error")                             # no model client: an error, so no class
        self.assertIn('out.update(case=got, outcome="case")', (KIT / "shared/desk_recall.py").read_text(encoding="utf-8"))
        # one row per check, at WARNING when it failed: the chat door's (surface chat) and rag-api's (query, stream)
        logged = '(log.warning if got["outcome"] == "error" else log.info)(json.dumps(desk_recall.row({}, tenant, got)))'
        self.assertIn(logged.format('"chat"'), DESK_PY)
        self.assertIn(logged.format("surface"), DOOR_PY)
        self.assertIn('CHECKED = ("query", "stream")', DOOR_PY)

    def test_the_unread_alert_reads_the_tenants_read_line(self):
        f = heredoc(block(ALERTS, 'resource "google_logging_metric" "desk_check_tenants_unread" {'))
        self.assertIn('(resource.labels.service_name="documind-chat" OR resource.labels.service_name="documind-api")', f)
        self.assertIn('jsonPayload.event="desk_check_tenants_unread"', f)
        recall = (KIT / "shared/desk_recall.py").read_text(encoding="utf-8")
        self.assertIn('event: str = "desk_check_tenants_unread"):', recall)     # the doors' line unless named
        self.assertIn('self._log.warning(json.dumps({"event": self._event, "surface": self._surface,', recall)
        self.assertIn('event="desk_shadow_tenants_unread")', DESK_PY)              # the shadow's own: not paged
        self.assertIn('CHECKED = desk_recall.OnTenants(lambda: desk_recall.read_on_tenants(_client()), log, "chat")', DESK_PY)
        self.assertIn('desk_recall.OnTenants(lambda: desk_recall.read_on_tenants(_fs()), log, "api")',
                      (KIT / "services/rag-api/main.py").read_text(encoding="utf-8"))
        p = block(ALERTS, 'resource "google_monitoring_alert_policy" "desk_check_tenants_unread" {')
        self.assertIn('group_by_fields      = ["resource.label.service_name"]', p)

    def test_the_thresholds(self):
        def threshold(n):
            return float(re.search(r"threshold_value +=\s*([\d.]+)", block(ALERTS, f'resource "google_monitoring_alert_policy" "{n}" {{')).group(1))
        for n in ("case_overdue", "doc_type_pin_miss", "desk_delegation_refused", "desk_check_tenants_unread"):
            self.assertEqual(threshold(n), 0, n)
        floor = "\nand on (tenant, event) sum by (tenant, event) (increase(logging_googleapis_com:user_documind_desk_router{monitored_resource=\"cloud_run_revision\"}[1h])) >= 100"
        for name, label, cap in (("desk_fallback_query", 'method="fallback"', 0.01),
                                 ("desk_l2_query", 'accepted_by="F"', route_threshold.TARGETS["l2_share"])):
            q = promql(name)
            self.assertEqual(q, f'sum by (tenant, event) (increase(logging_googleapis_com:user_documind_desk_router{{monitored_resource="cloud_run_revision",{label}}}[1h]))\n'
                                '  / on (tenant, event)\n'
                                'sum by (tenant, event) (increase(logging_googleapis_com:user_documind_desk_router{monitored_resource="cloud_run_revision"}[1h]))\n'
                                f"> {cap}" + floor, name)
        self.assertIn("fallback", desk_router.METHODS)
        gate = 'logging_googleapis_com:user_documind_desk_gate_check{monitored_resource="cloud_run_revision"'
        self.assertEqual(promql("desk_gate_error_query"),
                         f'sum by (tenant) (increase({gate},outcome="error"}}[30m]))\n'
                         '  / on (tenant)\n'
                         f'sum by (tenant) (increase({gate}}}[30m]))\n'
                         '> 0.2\n'
                         f'and on (tenant) sum by (tenant) (increase({gate}}}[30m])) >= 20')
        for policy, query in (("desk_fallback_share", "desk_fallback_query"), ("desk_l2_share", "desk_l2_query"),
                              ("desk_clarify_oos_trend", "desk_trend_query"), ("desk_gate_error_share", "desk_gate_error_query")):
            self.assertIn(f"query               = local.{query}\n", block(ALERTS, f'resource "google_monitoring_alert_policy" "{policy}" {{'))

    def test_the_week_on_week_query(self):
        q = promql("desk_trend_query")
        for a, b in (("(", ")"), ("{", "}"), ("[", "]")):
            self.assertEqual(q.count(a), q.count(b), a)
        self.assertEqual(q.count("logging_googleapis_com:user_documind_desk_router{"), 7)
        self.assertEqual(q.count('route=~"clarify|out_of_scope"'), 3)
        self.assertEqual(q.count("offset 7d"), 3)
        self.assertIn("\n> 0.05\n", q)
        self.assertEqual(q.count(">= 100"), 2)
        self.assertTrue({"clarify", "out_of_scope"} <= set(desk_routes_routes()))

    def test_the_overdue_alert_names_a_queue_and_a_state(self):
        b = block(ALERTS, 'resource "google_logging_metric" "case_overdue" {')
        self.assertEqual(re.findall(r'EXTRACT\(jsonPayload\.(\w+)\)', b), ["queue", "state"])
        self.assertIn('resource.labels.job_name="documind-cases-overdue"', b)
        self.assertIn('name     = "documind-cases-overdue"', (TF / "desk.tf").read_text(encoding="utf-8"))
        line = re.search(r'log\.info\(json\.dumps\(\{"event": "case_overdue",(.*?)\}\)\)', OVERDUE_PY, re.S).group(1)
        self.assertEqual(re.findall(r'"(\w+)": ', line), ["case_id", "queue", "due_at", "state"])
        p = block(ALERTS, 'resource "google_monitoring_alert_policy" "case_overdue" {')
        self.assertIn('group_by_fields      = ["metric.label.queue", "metric.label.state"]', p)

    def test_the_pin_miss_alert_reads_both_lanes(self):
        b = block(ALERTS, 'resource "google_logging_metric" "doc_type_pin_miss" {')
        self.assertIn('resource.labels.service_name="documind-ingest"', b)
        self.assertIn('resource.labels.job_name="documind-ingest-batch"', b)
        self.assertIn('name     = "documind-ingest-batch"', (TF / "batch.tf").read_text(encoding="utf-8"))
        self.assertIn('{"event": "doc_type_pin_miss", "tenant": doc.tenant_id,', (KIT / "shared/doc_types.py").read_text(encoding="utf-8"))
        p = block(ALERTS, 'resource "google_monitoring_alert_policy" "doc_type_pin_miss" {')
        self.assertEqual(re.findall(r'filter += "resource\.type=\\"(\w+)\\"', p), ["cloud_run_revision", "cloud_run_job"])


def desk_routes_routes() -> tuple:
    import desk_routes
    return desk_routes.ROUTES


if __name__ == "__main__":
    unittest.main()
