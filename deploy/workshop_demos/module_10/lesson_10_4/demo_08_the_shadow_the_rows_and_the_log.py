"""Lesson 10.4: The shadow, the rows and the log

zeta's router in shadow beside ordinary chat turns; a chunk, its registry entry and an exemplar in Firestore; every row the router logged; the Google Chat door's rows and claims; the Desk's day in BigQuery; then zeta on. Shadow first. A company that is not ready to route can let the router watch. With desk_route at shadow, every /v1/chat turn for that company is answered by its brain as before, and the router decides the same question beside it, with its own Meter, and logs a desk_shadow row. It answers nothing and keeps nothing. Shadow needs desk_gate not off, so the door answers every disclosure before the router could see it; zeta already has the gate's rules, because nothing has switched them off. zeta goes on to desk_route on later in this step, and the routed Desk waits for a complete POSH queue. So zeta gets its queues, with evalzeta as head office's committee, then the role, then the shadow. Three of zeta's route-set questions to /v1/chat as evalzeta, with the direct brain: a travel cap from zeta's handbook, the Code on Wages, and zeta's own contract. acme's chunk for NP-03, the handbook's registry entry, the exemplar for lk-06, and the three companies' switches, read with the Firestore client. Every desk and desk_shadow row the chat service logged since step 3. Since step 3's apply, the log sink copies the chat service's desk rows into BigQuery. make desk-views checks terraform/sql/desk_daily.sql with a dry run, then creates the view documind_observability.desk_daily: one row per India day, company, desk and kind of caller, with the turns, their outcomes, the escalations, how each turn was decided, the arbiter's share, the chip turns, the rupees and the latencies. No column names a person, a session or a question. The bq query then reads today's rows. Run it a few minutes after step 7, since the sink takes a little while to deliver rows and BigQuery types the table's columns from the rows it has seen. This is a preview; lesson 11.5 explains the sink and the views. The shadow rows are what a company reads before it switches. On the stand-in they agree with the route set's labels. Read yours first, and switch zeta on when they do.

Run order inside this file:
1. The shadow, the rows and the log (source window 64)
2. Do it: three ordinary chat turns (source window 66)
3. Do it: the rows in Firestore (source window 68)
4. Do it: the log (source window 70)
5. Do it: the Desk's day in BigQuery (source window 75)
6. Do it: zeta on (source window 77)

Prerequisites: demo_07_v1_route_and_v1_desk_over_rest.
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


# Original CLI workflow for step_01_the_shadow_the_rows_and_the_log.
COMMANDS_01 = """sed "s/you@example.com/$(sa evalzeta)/g" evals/desk/queues.zeta.json > "$HOME/queues.zeta.json"
make desk-queues PROJECT="$PROJECT" TENANT=zeta FILE="$HOME/queues.zeta.json"
make roles PROJECT="$PROJECT" TENANT=zeta EMAIL="$(sa evalzeta)" ROLES=employee,desk_eval,ic_member:head_office
make desk PROJECT="$PROJECT" TENANT=zeta DESK_ROUTE=shadow   # the gate already runs as rules for zeta

"""

def step_01_the_shadow_the_rows_and_the_log(session):
    """Run The shadow, the rows and the log at this checkpoint.

    zeta's router in shadow beside ordinary chat turns; a chunk, its registry entry and an exemplar in Firestore; every row the router logged; the Google Chat door's rows and claims; the Desk's day in BigQuery; then zeta on. Shadow first. A company that is not ready to route can let the router watch. With desk_route at shadow, every /v1/chat turn for that company is answered by its brain as before, and the router decides the same question beside it, with its own Meter, and logs a desk_shadow row. It answers nothing and keeps nothing. Shadow needs desk_gate not off, so the door answers every disclosure before the router could see it; zeta already has the gate's rules, because nothing has switched them off. zeta goes on to desk_route on later in this step, and the routed Desk waits for a complete POSH queue. So zeta gets its queues, with evalzeta as head office's committee, then the role, then the shadow.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (zeta's queues with its eval account as the committee, then the router in shadow).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"tenant": "zeta",
     "sections": ["grc", "payroll", "people", "posh", "privacy"],
     "posh_units": ["head_office"],
     "posh_missing": [],
     "not_readers": ["ic head_office: documind-evalzeta-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com", "queue grc: no member holds a role that reads it", "queue privacy: no member holds a role that reads it", "queue payroll: no member holds a role that reads it", "queue people: no member holds a role that reads it"],
     "action": "written"}
    {"tenant": "zeta",
     "email": "documind-evalzeta-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com",
     "before": ["employee"],
     "after": ["desk_eval", "employee", "ic_member:head_office"],
     "granted": ["desk_eval", "ic_member:head_o
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_three_ordinary_chat_turns.
COMMANDS_02 = """T_ZETA="$(etok evalzeta)" python - <<'PY'
import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
def post(path, body, token):
    req = urllib.request.Request(os.environ["CHAT"] + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ[token]})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
rows = {r["id"]: r for r in (json.loads(x) for x in open("evals/routes.jsonl", encoding="utf-8") if x.strip())}
for rid in ("iso-01", "lk-21", "lk-13"):
    status, b = post("/v1/chat", {"question": rows[rid]["question"], "session_id": "lesson106-shadow", "brain": "direct"}, "T_ZETA")
    says = rows[rid]["must_contain"]
    print(f"  {rid:6} {status} brain {b['brain']}  citations {len(b['citations'])}  model_calls {b['limits']['model_calls']}"
          + (f"  the answer says {says}: {all(w in b['answer'] for w in says)}" if says else ""))
PY

"""

def step_02_three_ordinary_chat_turns(session):
    """Run Do it: three ordinary chat turns at this checkpoint.

    Three of zeta's route-set questions to /v1/chat as evalzeta, with the direct brain: a travel cap from zeta's handbook, the Code on Wages, and zeta's own contract.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (three ordinary chat turns on zeta, which the router decides beside).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: iso-01 200 brain direct  citations N  model_calls 0  the answer says ['25,000']: True
      lk-21  200 brain direct  citations N  model_calls 0  the answer says ['seventh day']: True
      lk-13  200 brain direct  citations N  model_calls 0
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_the_rows_in_firestore(session):
    """Run Do it: the rows in Firestore at this checkpoint.

    acme's chunk for NP-03, the handbook's registry entry, the exemplar for lk-06, and the three companies' switches, read with the Firestore client.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a chunk, its registry entry, an exemplar and the three tenants' switches, from Firestore).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: chunks/acme:497809ffbaa603c49577add351033f4374ad1aefa3394f761be0c9df5e3f3173#1
        doc_type policy  kind text  current True  acme/hr_policy_2026.md
      tenants/acme/doc_types/acme~hr_policy_2026.md: policy, pin acme_497809ffbaa6..., set by you@example.com, source manifest
        the pin is the chunk's doc_key: True
      tenants/acme/desk_exemplars/lk-06: route handbook, group lk-06, 768 dimensions, text-embedding-005, index d15e143dd357
      tenant_settings/acme: desk_gate rules, desk_route on, desk_single None, data_region any
      tenant_settings/zeta: desk_gate rules, desk_route shadow, desk_single None, data_region any
      tenant_settings/globex: desk_gate rules, desk_route single, desk_single statute, 
    """
    import os, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from google.cloud import firestore
    db = firestore.Client(project=os.environ["PROJECT"])
    hits = [s for s in db.collection("chunks").where("tenant_id", "==", "acme").where("locator", "==", "NP-03").stream()
            if s.to_dict().get("current")]
    c = hits[0].to_dict()
    print(f"  chunks/{hits[0].id}")
    print(f"    doc_type {c['doc_type']}  kind {c['kind']}  current {c['current']}  {c['source_uri'].split('/', 3)[3]}")
    e = db.document("tenants/acme/doc_types/acme~hr_policy_2026.md").get().to_dict()
    print(f"  tenants/acme/doc_types/acme~hr_policy_2026.md: {e['doc_type']}, pin {e['pin'][:17]}..., set by {e['set_by']}, source {e['source']}")
    print(f"    the pin is the chunk's doc_key: {e['pin'] == c['doc_key']}")
    x = db.document("tenants/acme/desk_exemplars/lk-06").get().to_dict()
    print(f"  tenants/acme/desk_exemplars/lk-06: route {x['route']}, group {x['group']}, {len(list(x['vector']))} dimensions,"
          f" {x['embedding_model']}, index {x['index_version']}")
    for t in ("acme", "zeta", "globex"):
        s = db.document(f"tenant_settings/{t}").get().to_dict()
        print(f"  tenant_settings/{t}: desk_gate {s.get('desk_gate', 'rules')}, desk_route {s.get('desk_route', 'off')},"
              f" desk_single {s.get('desk_single')}, data_region {s.get('data_region')}")

def step_04_the_log(session):
    """Run Do it: the log at this checkpoint.

    Every desk and desk_shadow row the chat service logged since step 3.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (every desk and desk_shadow row since step 3; reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: desk        desk  acme   you                       clarify      arbiter F    calls 2  clarify
      desk        desk  acme   you                       handbook     user    None calls 0  answer
      desk        desk  acme   you                       handbook     model   A    calls 1  answer
      desk        desk  acme   you                       statute      model   A    calls 1  answer
      desk        desk  acme   you                       out_of_scope anchor  None calls 0  oos
      desk        route acme   None                      case         rule    None calls 0  
      desk        route acme   documind-evalacme-sa      out_of_scope anchor  None calls 0  
      desk        route acme   documind-evalacme-sa    
    """
    import json, os, subprocess, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    f = (f'resource.type="cloud_run_revision" AND resource.labels.service_name="documind-chat" AND '
         f'(jsonPayload.event="desk" OR jsonPayload.event="desk_shadow") AND timestamp>="{os.environ["SINCE106"]}"')
    out = subprocess.run(["gcloud", "logging", "read", f, "--project", os.environ["PROJECT"], "--order", "asc", "--limit", "60",
                          "--format", "json"], capture_output=True, text=True, check=True).stdout
    for e in json.loads(out or "[]"):
        j = e["jsonPayload"]
        who = (j["user"] or "None").split("@")[0]
        print(f"  {j['event']:11} {j['surface']:5} {j['tenant']:6} {who:25} {j['route']:12} {j['method']:7}"
              f" {str(j['accepted_by']):4} calls {j['model_calls']}  {j.get('outcome') or ''}")

# Original CLI workflow for step_05_the_desk_s_day_in_bigquery.
COMMANDS_05 = """make desk-views PROJECT="$PROJECT"
bq --project_id="$PROJECT" query --use_legacy_sql=false --format=pretty \\
  'SELECT tenant, desk, callers, turns, answered, clarified, escalations, to_l2, cost_inr
   FROM `documind_observability.desk_daily`
   WHERE day = CURRENT_DATE("Asia/Kolkata") ORDER BY tenant, desk, callers'

"""

def step_05_the_desk_s_day_in_bigquery(session):
    """Run Do it: the Desk's day in BigQuery at this checkpoint.

    Since step 3's apply, the log sink copies the chat service's desk rows into BigQuery. make desk-views checks terraform/sql/desk_daily.sql with a dry run, then creates the view documind_observability.desk_daily: one row per India day, company, desk and kind of caller, with the turns, their outcomes, the escalations, how each turn was decided, the arbiter's share, the chip turns, the rupees and the latencies. No column names a person, a session or a question. The bq query then reads today's rows. Run it a few minutes after step 7, since the sink takes a little while to deliver rows and BigQuery types the table's columns from the rows it has seen. This is a preview; lesson 11.5 explains the sink and the views.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the desk_daily view applied, then today's rows read with bq).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: bq --project_id=documind-ai-YOUR-ID query --use_legacy_sql=false --dry_run < terraform/sql/desk_daily.sql
    ...
    bq --project_id=documind-ai-YOUR-ID query --use_legacy_sql=false < terraform/sql/desk_daily.sql
    ...
    >> the router's three alert policies (terraform/desk_alerts.tf) exist only on a lane planned with DESK_ROUTER_ALERTS=true: now that the router has run, make plan up DESK_ROUTER_ALERTS=true, and keep it on every later plan
    +--------+--------------+------------------+-------+----------+-----------+-------------+-------+----------+
    | tenant |     desk     |     callers      | turns | answered | clarified | escalations | to_l2 | cost_inr |
    +--------+--------------+------------------+------
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

# Original CLI workflow for step_06_zeta_on.
COMMANDS_06 = """make desk PROJECT="$PROJECT" TENANT=zeta DESK_ROUTE=on

"""

def step_06_zeta_on(session):
    """Run Do it: zeta on at this checkpoint.

    The shadow rows are what a company reads before it switches. On the stand-in they agree with the route set's labels. Read yours first, and switch zeta on when they do.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (zeta from shadow to on).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: {"tenant": "zeta",
     "desk_gate": "rules",
     "desk_max_parts": 1,
     "desk_route": "on",
     "desk_single": null,
     "desk_off": [],
     "note": "rag-api and the chat service read it within 60 s"}
    >> the router's three alert policies (terraform/desk_alerts.tf): make plan up DESK_ROUTER_ALERTS=true after the router has taken some turns; then keep DESK_ROUTER_ALERTS=true on every later plan
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_64', step_01_the_shadow_the_rows_and_the_log),
        ('source_66', step_02_three_ordinary_chat_turns),
        ('source_68', step_03_the_rows_in_firestore),
        ('source_70', step_04_the_log),
        ('source_75', step_05_the_desk_s_day_in_bigquery),
        ('source_77', step_06_zeta_on),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
