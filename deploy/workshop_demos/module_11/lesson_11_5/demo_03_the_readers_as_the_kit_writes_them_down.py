"""Lesson 11.5: The readers, as the kit writes them down

Do it

Run order inside this file:
1. Do it (source window 9)

Prerequisites: setup_prepare.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


def step_01_the_readers_as_the_kit_writes_them_down(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the readers as the kit writes them down; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: reader                         services                     window
    the sink, into BigQuery        documind-api, documind-chat  every row, as it is written
                                   events: query, stream, chat, desk, passages, desk_shadow, desk_gate
                                   desk_shadow only where NOT jsonPayload.case_type = "sensitive"
                                   desk_gate only where resource.labels.service_name = "documind-chat"
    tenant_daily, the view         what the sink copied         one row per India day and 7 dimensions
                                   events: query, stream, media
    make usage                     documind-api                 the last N hours (default 24), at 
    """
    import re
    def between(text, start, end):
        """Select the source excerpt between two markers so the inspection uses the current kit code.
        
        Example: between(open('terraform/sink.tf', encoding='utf-8').read(), 'filter', 'EOT\\n  unique')
        """
        return text.split(start, 1)[1].split(end, 1)[0]
    sink = between(open("terraform/sink.tf", encoding="utf-8").read(), "filter", "EOT\n  unique")
    view = open("terraform/sql/tenant_daily.sql", encoding="utf-8").read()
    tool = open("evals/usage_rows.py", encoding="utf-8").read()
    alerts = open("terraform/alerts.tf", encoding="utf-8").read()
    desk_view = open("terraform/sql/desk_daily.sql", encoding="utf-8").read()
    desk_alerts = open("terraform/desk_alerts.tf", encoding="utf-8").read()
    queries = between(alerts, 'name    = "documind/queries"', "EOT\n  metric")
    readers = [
        ("the sink, into BigQuery", list(dict.fromkeys(re.findall(r'service_name = "([\w-]+)"', sink))), re.findall(r'event = "(\w+)"', sink),
         "every row, as it is written"),
        ("tenant_daily, the view", ["what the sink copied"], re.findall(r'"(\w+)"', between(view, "WHERE jsonPayload.event IN (", ")")),
         "one row per India day and " + str(len(between(view, "GROUP BY day,", ";").split(","))) + " dimensions"),
        ("make usage", [re.search(r'"--service", default="([\w-]+)"', tool).group(1)], re.findall(r'event="(\w+)"', between(tool, "def read_rows", "def p95")),
         "the last N hours (default " + re.search(r'"--hours", type=int, default=(\d+)', tool).group(1) + "), at most "
         + re.search(r"limit: int = (\d+)", tool).group(1) + " rows"),
        ("documind/queries, for alerts", re.findall(r'service_name="([\w-]+)"', queries), re.findall(r'event="(\w+)"', queries), "counted as written"),
    ]
    print(f"{'reader':30} {'services':28} window")
    for name, services, events, when in readers:
        print(f"{name:30} {', '.join(services):28} {when}")
        print(f"{'':30} events: {', '.join(events)}")
        for ev, cond in re.findall(r'\(jsonPayload\.event = "(\w+)" AND ([^)]+)\)', sink) if name.startswith("the sink") else ():
            print(f"{'':30} {ev} only where {cond}")
    inr = re.search(r"\* (\d+), 2\) AS cost_inr", view).group(1)
    usd_inr = re.search(r"USD_INR = (\d+)", tool).group(1)
    print(f"rupees: tenant_daily's cost_inr is cost_usd x {inr}; make usage's USD_INR is {usd_inr}")
    events = {name: set(e) for name, _, e, _ in readers}
    for ev in sorted(set().union(*events.values())):
        print(f"  {ev:11} read by: " + ", ".join(n for n, _, e, _ in readers if ev in e))
    print("the Desk's own view, desk_daily (make desk-views), reads: " + ", ".join(re.findall(r'jsonPayload\.event = "(\w+)"', desk_view)))
    policies = re.findall(r'resource "google_monitoring_alert_policy" "(\w+)"', alerts)
    print(f"alert policies in terraform/alerts.tf: {len(policies)} - " + ", ".join(policies))
    desk_policies = re.findall(r'resource "google_monitoring_alert_policy" "(\w+)" \{\n(?:  count += var\.(\w+) \? 1 : 0\n)?', desk_alerts)
    switches = list(dict.fromkeys(s for _, s in desk_policies if s))
    mark = {s: "*" * (i + 1) for i, s in enumerate(switches)}
    print(f"alert policies in terraform/desk_alerts.tf: {len(desk_policies)} - " + ", ".join(n + mark.get(s, "") for n, s in desk_policies)
          + " (" + ", ".join(f"{mark[s]} only on a lane planned with {s.upper()}=true" for s in switches) + ")")
    print("the one that reads the dead-letter queue: " + ", ".join(p for p in policies
          if "ingest_dlq_sub" in between(alerts, f'"google_monitoring_alert_policy" "{p}"', "\n}\n")))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_readers_as_the_kit_writes_them_down),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
