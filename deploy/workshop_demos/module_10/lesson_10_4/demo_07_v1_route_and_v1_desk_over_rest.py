"""Lesson 10.4: /v1/route and /v1/desk, over REST

Five questions to /v1/route as evalacme: the smoke's disclosure, an invoice, a clause code, a named Act, and lk-06 with no identifier. Then lk-06 again, as documind-ui-sa. lk-06 and lk-17 to /v1/desk, each in its own session. For each section, the cell prints the title, the objects cited, whether the answer holds the route set's expected words, and the in-force lines. lk-06 as the leaver; globex's DPDP question as evalglobex; "What is the notice period?" as evalacme. jn-03 asks for a figure: "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?" When L1 marks a question needs_calculation, the handbook desk runs in agent mode. A small agent searches the handbook's passages, and a calculator from shared/desk_calc.py does the arithmetic. The calculator takes the balance only from the person's message and the cap only from clause LV-07 of a passage this turn read; any other number is refused, and the agent is told why. smoke/smoke_desk.py checks the routed Desk in one run, as the eval accounts, then runs 5.6's case-queue smoke. Its questions are the route set's own rows, read by id, and each run uses fresh sessions.

Run order inside this file:
1. Do it: decisions (source window 52)
2. Do it: answers (source window 54)
3. Do it: the leaver, the single desk, and a question back (source window 56)
4. Do it: a figure, worked out in code (source window 58)
5. Do it: the live smoke (source window 60)

Prerequisites: demo_06_two_signals_and_one_arbiter_in_the_code.
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


# Original CLI workflow for step_01_decisions.
COMMANDS_01 = """TOKEN="$(etok evalacme)" T_UI="$(etok ui)" python - <<'PY'
import json, os, urllib.error, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from smoke.smoke_cases import POSH
def post(path, body, token):
    req = urllib.request.Request(os.environ["CHAT"] + path, data=json.dumps(body).encode(), method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ[token]})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, json.load(r)
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")
rows = {r["id"]: r for r in (json.loads(x) for x in open("evals/routes.jsonl", encoding="utf-8") if x.strip())}
for label, q in (("POSH", POSH), ("lk-10", rows["lk-10"]["question"]), ("NP-03", "What does NP-03 say about notice?"),
                 ("lk-18", rows["lk-18"]["question"]), ("lk-06", rows["lk-06"]["question"])):
    status, b = post("/v1/route", {"question": q}, "TOKEN")
    d = b["decision"]
    print(f"  {label:6} {status} route {b['route']:13} method {b['method']:7} anchors {str(d['anchors']):18}"
          f" model_calls {b['model_calls']}  Rs {b['cost_inr']}")
    if d["l1"]:
        print(f"         L1 {d['l1']['route']}; the vote {d['knn_route']}, {round(d['knn_share'] * 7)} of 7, nearest cosine"
              f" {d['knn_sim']}; accepted by rule {d['accepted_by']}")
status, b = post("/v1/route", {"question": rows["lk-06"]["question"]}, "T_UI")
print(f"  as ui-sa {status} {b['detail']}")
PY

"""

def step_01_decisions(session):
    """Run Do it: decisions at this checkpoint.

    Five questions to /v1/route as evalacme: the smoke's disclosure, an invoice, a clause code, a named Act, and lk-06 with no identifier. Then lk-06 again, as documind-ui-sa.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (five decisions from POST /v1/route as evalacme, then the same call as ui-sa).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: POSH   200 route case          method rule    anchors []                 model_calls 0  Rs 0.0
      lk-10  200 route out_of_scope  method anchor  anchors ['out_of_scope']   model_calls 0  Rs 0.0
      NP-03  200 route handbook      method anchor  anchors ['handbook']       model_calls 0  Rs 0.0
      lk-18  200 route statute       method anchor  anchors ['statute']        model_calls 0  Rs 0.0
      lk-06  200 route handbook      method model   anchors []                 model_calls 1  Rs N.NNNN
             L1 handbook; the vote handbook, N of 7, nearest cosine N.NNNN; accepted by rule A
      as ui-sa 403 POST /v1/route is for the Desk's eval accounts (desk_eval)
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_answers.
COMMANDS_02 = """T_ACME="$(etok evalacme)" python - <<'PY'
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
for n, rid in enumerate(("lk-06", "lk-17")):
    status, b = post("/v1/desk", {"question": rows[rid]["question"], "session_id": f"lesson106-{n}"}, "T_ACME")
    print(f"  {rid} {status} route {b['route']} method {b['method']} outcome {b['outcome']}  model_calls {b['model_calls']}"
          f"  retrieve_calls {b['retrieve_calls']}  Rs {b['limits']['cost_inr']}")
    for s in b["sections"]:
        objs = sorted({c["source_uri"].split("/", 3)[3] for c in s["citations"]})
        print(f"    {s['title']}: {len(s['citations'])} citations from {', '.join(objs)}")
        print(f"    the answer says {rows[rid]['must_contain']}: {all(w in s['answer'] for w in rows[rid]['must_contain'])}")
        for line in s["in_force"]:
            print(f"    | {line}")
    print(f"    chips {[c['desk'] for c in b['chips']]}")
PY

"""

def step_02_answers(session):
    """Run Do it: answers at this checkpoint.

    lk-06 and lk-17 to /v1/desk, each in its own session. For each section, the cell prints the title, the objects cited, whether the answer holds the route set's expected words, and the in-force lines.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two answers from POST /v1/desk as evalacme).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lk-06 200 route handbook method model outcome answer  model_calls 1  retrieve_calls 1  Rs N.NNNN
        From the company handbook: N citations from acme/hr_policy_2026.md
        the answer says ['60']: True
        chips []
      lk-17 200 route statute method model outcome answer  model_calls 1  retrieve_calls 1  Rs N.NNNN
        What the law says: N citations from acme/code_on_social_security_2020.pdf, acme/industrial_relations_code_2020.pdf, acme/payment_of_gratuity_act_1972.pdf
        the answer says ['fifteen days']: True
        | Payment of Gratuity Act, 1972: the Code on Social Security, 2020, s.164(1) repeals it from the day the Code on Social Security, 2020 comes into force (the date is not shown here unt
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_leaver_the_single_desk_and_a_question.
COMMANDS_03 = """T_ACME="$(etok evalacme)" T_LEAVER="$(etok evalleaver)" T_GLOBEX="$(etok evalglobex)" python - <<'PY'
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
status, b = post("/v1/desk", {"question": rows["lk-06"]["question"], "session_id": "lesson106-leaver"}, "T_LEAVER")
print(f"  leaver  {status} route {b['route']} outcome {b['outcome']}  retrieve_calls {b['retrieve_calls']}"
      f"  model_calls {b['model_calls']}  chips {[c['desk'] for c in b['chips']]}")
print(f"          {b['answer']}")
status, b = post("/v1/desk", {"question": rows["lk-28"]["question"], "session_id": "lesson106-globex"}, "T_GLOBEX")
print(f"  globex  {status} tenant {b['tenant']} mode {b['mode']} route {b['route']} method {b['method']}"
      f"  model_calls {b['model_calls']}  outcome {b['outcome']}")
print(f"          cites {sorted({c['source_uri'].split('/', 3)[3] for c in b['citations']})}")
status, b = post("/v1/desk", {"question": "What is the notice period?", "session_id": "lesson106-clarify"}, "T_ACME")
print(f"  clarify {status} route {b['route']} method {b['method']}: {b['answer']}")
print(f"          chips {[c['label'] for c in b['chips']]}")
PY

"""

def step_03_the_leaver_the_single_desk_and_a_question(session):
    """Run Do it: the leaver, the single desk, and a question back at this checkpoint.

    lk-06 as the leaver; globex's DPDP question as evalglobex; "What is the notice period?" as evalacme.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the leaver, globex in single mode, and a question with no desk in it).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: leaver  200 route denied outcome denied  retrieve_calls 0  model_calls 1  chips ['case']
              Your roles in this company do not include asking the company handbook, so DocuMind did not search for this. You can raise a case for a person.
      globex  200 tenant globex mode single route statute method single  model_calls 0  outcome answer
              cites ['globex/dpdp_act_2023.pdf']
      clarify 200 route clarify method arbiter: Should I answer this from the company handbook or from the law?
              chips ['Ask what the company handbook says', 'Ask what the law says']
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_a_figure_worked_out_in_code.
COMMANDS_04 = """T_ACME="$(etok evalacme)" python - <<'PY'
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
row = rows["jn-03"]
status, b = post("/v1/desk", {"question": row["question"], "session_id": "lesson106-figure"}, "T_ACME")
s = b["sections"][0]
print(f"  jn-03 {status} route {b['route']} method {b['method']} mode {s['mode']}  tool_calls {b['tool_calls']}")
print(f"        retrieve_calls {b['retrieve_calls']}  model_calls {b['model_calls']}  Rs {b['limits']['cost_inr']}")
print(f"        the answer says {row['must_contain']}: {all(w in s['answer'] for w in row['must_contain'])}")
print()
print(s["answer"])
PY

"""

def step_04_a_figure_worked_out_in_code(session):
    """Run Do it: a figure, worked out in code at this checkpoint.

    jn-03 asks for a figure: "I am an E3 leaving with 50 days of earned leave. How much is encashed and what notice do I serve?" When L1 marks a question needs_calculation, the handbook desk runs in agent mode. A small agent searches the handbook's passages, and a calculator from shared/desk_calc.py does the arithmetic. The calculator takes the balance only from the person's message and the cap only from clause LV-07 of a passage this turn read; any other number is refused, and the agent is told why.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (jn-03, a figure, to POST /v1/desk as evalacme: the handbook desk in agent mode).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: jn-03 200 route handbook method model mode agent  tool_calls ['retrieve', 'encashable_days']
            retrieve_calls 1  model_calls N  Rs N.NNNN
            the answer says ['45', '60']: True

    Of your 50 days of earned leave, 45 are encashed on exit, at basic pay [1]. A confirmed employee at grade E3 or above serves a notice period of 60 days [2].

    Worked out in code:
    - Earned leave encashed on exit (LV-07): min(50, 45) = 45 days. The balance from your message; the cap from LV-07 [1]. Condition: LV-07 bars encashment during probation: this figure holds only once probation is over.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

# Original CLI workflow for step_05_the_live_smoke.
COMMANDS_05 = """make smoke-desk PROJECT="$PROJECT" REGION="$REGION" TENANT=acme IC_EMAIL="$ME"

"""

def step_05_the_live_smoke(session):
    """Run Do it: the live smoke at this checkpoint.

    smoke/smoke_desk.py checks the routed Desk in one run, as the eval accounts, then runs 5.6's case-queue smoke. Its questions are the route set's own rows, read by id, and each run uses fresh sessions.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the routed Desk's live smoke, then the case queue's).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: DocuMind Desk - the routed Desk, live
      chat: https://documind-chat-NUMBER.asia-south1.run.app
      --------------------------------------------------------
      [PASS] handbook  N citations, method model, Rs N.NNNN
      [PASS] statute  in force: 'Code on Social Security, 2020: it comes into force on such date as the'
      [PASS] posh  no model call, no case written, offices ['hyderabad', 'pune']
      [PASS] out_of_scope  method anchor: "This is outside what DocuMind's desks answer: it is not in t"
      [PASS] leaver denied  zero retrieve calls, a case offered
      [PASS] globex single  outcome answer, model calls 0
      [PASS] /v1/route  status=200 {'email': 'documind-evalacme-sa@documind-ai-YOUR-ID.iam.gserviceac
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_05)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_52', step_01_decisions),
        ('source_54', step_02_answers),
        ('source_56', step_03_the_leaver_the_single_desk_and_a_question),
        ('source_58', step_04_a_figure_worked_out_in_code),
        ('source_60', step_05_the_live_smoke),
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
