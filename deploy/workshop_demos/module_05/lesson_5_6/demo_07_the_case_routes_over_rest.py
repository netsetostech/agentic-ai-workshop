"""Lesson 5.6: The case routes, over REST

The cell first asks what evalacme may raise. It raises a grievance as evalacme and sends it twice with one token. Then it tries a second token. evalgrc reads its inbox, then asks for the offer. evalzeta and the outsider ask for the case. The raiser tries to close it, and the committee acknowledges and closes it. It keeps the id in ~/lesson105_case.txt for step 8. smoke/smoke_cases.py checks the whole queue in one run, as the eval accounts, with your email as the Internal Committee member its POSH press names. It closes and withdraws what it opens. make cases lists a tenant's open cases, soonest due first, for you to chase. A sensitive case's type and queue both show as "sensitive", since a queue such as ic:hyderabad would give the type away, and no person is named. make cases-overdue runs the hourly job's scan once, as you.

Run order inside this file:
1. Do it: a case, end to end (source window 43)
2. Do it: the live smoke (source window 45)
3. Do it: the operator's view (source window 47)

Prerequisites: demo_06_roles_and_cases_in_the_code.
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


# Original CLI workflow for step_01_a_case_end_to_end.
COMMANDS_01 = """T_ACME="$(etok evalacme)" T_GRC="$(etok evalgrc)" T_ZETA="$(etok evalzeta)" T_OUT="$(etok outsider)" python - <<'PY'
import json, os, urllib.error, urllib.request, uuid, warnings
from datetime import datetime
warnings.filterwarnings("ignore", category=UserWarning)
def call(who, path, body=None):
    req = urllib.request.Request(os.environ["CHAT"] + path, method="GET" if body is None else "POST",
                                 data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["T_" + who]})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
def span(a, b):
    return str(datetime.fromisoformat(b) - datetime.fromisoformat(a))
s, o = call("ACME", "/v1/cases/offer")
print(f"  offer      {s}  {o['tenant']}, desk_gate {o['desk_gate']}, POSH offices {sorted(o['posh'] or {})}")
print(f"             types {', '.join(o['types'])}")
s, d = call("ACME", "/v1/cases", {"case_type": "grievance", "summary": "Lesson 5.6 test case: please close it."})
cid = d["case_id"]
print(f"  draft      {s}  {d['status']} in {d['queue']} ({d['owner']['queue_name']}), expires {span(d['created_at'], d['expire_at'])} after it was made")
print(f"             basis {d['basis'][0]['instrument']}: {', '.join(b['section'] for b in d['basis'])}")
token = "lesson105-" + uuid.uuid4().hex[:12]                      # the page's own token, as the Desk page makes one
one, two = (call("ACME", f"/v1/cases/{cid}/confirm", {"token": token}) for _ in range(2))
print(f"  confirm x2 {one[0]} {one[1]['status']}, {two[0]} {two[1]['status']}: same case {two[1]['case_id'] == cid},"
      f" opened once {two[1]['opened_at'] == one[1]['opened_at']}")
print(f"             due {span(one[1]['opened_at'], one[1]['due_at'])} after it opened: {one[1]['sla_basis']}")
s, b = call("ACME", f"/v1/cases/{cid}/confirm", {"token": token + "-again"})
print(f"  new token  {s}  {b['detail']}")
s, box = call("GRC", "/v1/cases")
print(f"  inbox      {s}  seen as {box['email'].split('@')[0]} in {box['tenant']}, roles {box['roles']},"
      f" the case in it: {cid in [c['case_id'] for c in box['inbox']]}")
s, b = call("GRC", "/v1/cases/offer")
print(f"  grc offer  {s}  {b['detail']}")
for who in ("ZETA", "OUT"):
    s, b = call(who, f"/v1/cases/{cid}")
    print(f"  {who.lower():10} {s}  {b['detail']}")
s, b = call("ACME", f"/v1/cases/{cid}/status", {"status": "closed"})
print(f"  raiser     {s}  {b['detail']}")
for step in ("acknowledged", "closed"):
    s, b = call("GRC", f"/v1/cases/{cid}/status", {"status": step})
    print(f"  committee  {s}  {b['status']}")
open(os.path.expanduser("~/lesson105_case.txt"), "w").write(cid)
PY

"""

def step_01_a_case_end_to_end(session):
    """Run Do it: a case, end to end at this checkpoint.

    The cell first asks what evalacme may raise. It raises a grievance as evalacme and sends it twice with one token. Then it tries a second token. evalgrc reads its inbox, then asks for the offer. evalzeta and the outsider ask for the case. The raiser tries to close it, and the committee acknowledges and closes it. It keeps the id in ~/lesson105_case.txt for step 8.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the offer, then a case raised, confirmed twice, read by the committee, refused to others, closed).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: offer      200  acme, desk_gate rules, POSH offices ['hyderabad', 'pune']
                 types posh, grievance, privacy_request, exit_dues, people_query, human_requested
      draft      200  draft in grc (Grievance Redressal Committee), expires 0:30:00 after it was made
                 basis Industrial Relations Code, 2020: s.4(1), s.4(5), s.4(6)
      confirm x2 200 open, 200 open: same case True, opened once True
                 due 15 days, 0:00:00 after it opened: the company's own target: 15 days (case_queues.grc.sla_days)
      new token  409  this case is already open
      inbox      200  seen as documind-evalgrc-sa in acme, roles ['grc_member'], the case in it: True
      grc offer  403  your roles in this co
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_live_smoke.
COMMANDS_02 = """make smoke-cases PROJECT="$PROJECT" REGION="$REGION" IC_EMAIL="$ME"

"""

def step_02_the_live_smoke(session):
    """Run Do it: the live smoke at this checkpoint.

    smoke/smoke_cases.py checks the whole queue in one run, as the eval accounts, with your email as the Internal Committee member its POSH press names. It closes and withdraws what it opens.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the case queue's live smoke).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DocuMind Desk - the case queue, live
      chat: https://documind-chat-NUMBER.asia-south1.run.app
      api:  https://documind-api-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      [PASS] chat door  brain=desk_gate model=none Rs 0  'It sounds as if this may be about sexual harassment at work.'
      [PASS] api door (stream)  model=none cost_usd=0 backend=desk_gate
      [PASS] draft  queue=grc expires=YYYY-MM-DDTHH:MM:SS+00:00
      [PASS] confirm, twice  one case, open, due YYYY-MM-DDTHH:MM:SS+00:00
      [PASS] inbox  status=200 roles=['grc_member'] in inbox=True
      [PASS] status acknowledged  status=200 {'case_id': 'f61615ef83f1165722a5ee805065654b', 'tenant': 'acme', 'reques
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_operator_s_view.
COMMANDS_03 = """make cases PROJECT="$PROJECT" TENANT=acme
make cases-overdue PROJECT="$PROJECT"

"""

def step_03_the_operator_s_view(session):
    """Run Do it: the operator's view at this checkpoint.

    make cases lists a tenant's open cases, soonest due first, for you to chase. A sensitive case's type and queue both show as "sensitive", since a queue such as ic:hyderabad would give the type away, and no person is named. make cases-overdue runs the hourly job's scan once, as you.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (acme's open cases, and the overdue scan the hourly job runs).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: case                              type             queue            status       due_at                     state
    677ddf02cb3576d1097b86284682ad71  sensitive        sensitive        open         YYYY-MM-DDTHH:MM:SS+00:00  open
    b41155df5b60dd3efdb1f1a0afcd94c9  sensitive        sensitive        acknowledged YYYY-MM-DDTHH:MM:SS+00:00  open
    2 open case(s): 0 due, 0 breached
    {"event": "case_overdue_scan", "due": 0, "breached": 0}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_43', step_01_a_case_end_to_end),
        ('source_45', step_02_the_live_smoke),
        ('source_47', step_03_the_operator_s_view),
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
