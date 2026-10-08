"""Lesson 5.6: One fixed reply at every door

No lane and no cost: the cell imports the kit's rules and runs them on the smoke's disclosure, a near miss, a plain question and two numbers. The disclosure to /v1/stream and /v1/query as acme, with tok's token for documind-ui-sa, the account make smoke calls as. The cell takes the words from the smoke's own file. The same words to the chat service as evalacme, asking for the langchain brain, which would send them to Gemini first. The cell also prints case_offer, the field the Desk page reads.

Run order inside this file:
1. Do it: the gate on your machine (source window 20)
2. Do it: rag-api's door (source window 25)
3. Do it: the chat door (source window 27)

Prerequisites: demo_04_the_desk_page_tell_raise_read.
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


def step_01_the_gate_on_your_machine(session):
    """Run Do it: the gate on your machine at this checkpoint.

    No lane and no cost: the cell imports the kit's rules and runs them on the smoke's disclosure, a near miss, a plain question and two numbers.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (gate() and mask() on your machine; no lane, no cost).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gate posh   mask []        My manager keeps making sexual comments about my body. What can I do?
      gate None   mask []        Can I file a POSH complaint after three months?
      gate None   mask []        Can I carry forward my earned leave?
      gate None   mask ['card']  Please refund the hotel booking to my card [card no.].
      gate None   mask []        My Aadhaar 2234 5678 9012 is on the travel form.
      rules 2026-10-01.4
    """
    manual_checkpoint("In the deployed UI, signed in as yourself, choose Desk: acme has the gate's rules with nothing switched on, and your roles are read on every request, so there is nothing to wait for. Paste the sentence the previous section printed into Tell the Desk and Send: the fixed reply comes back and the POSH card opens under Raise a case. Choose Hyderabad and yourself, and Create a confidential record; then, under What is it about?, raise a grievance, check it and Send; in Your inbox, change the grievance to Acknowledged and Update. Type done to run the gate on your machine and through both doors.")
    import warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from shared import desk_rules
    from smoke.smoke_cases import POSH                  # the disclosure make smoke-cases sends
    for words in (POSH, "Can I file a POSH complaint after three months?", "Can I carry forward my earned leave?",
                  "Please refund the hotel booking to my card 4111 1111 1111 1111.", "My Aadhaar 2234 5678 9012 is on the travel form."):
        masked, kinds = desk_rules.mask(words)
        print(f"  gate {str(desk_rules.gate(words)):5}  mask {str(kinds):9} {masked}")
    print("  rules", desk_rules.RULES_VERSION)

# Original CLI workflow for step_02_rag_api_s_door.
COMMANDS_02 = """TOKEN="$(tok "$API")" python - <<'PY'
import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from smoke.smoke_cases import POSH                  # the disclosure make smoke-cases sends
def post(path):
    req = urllib.request.Request(os.environ["API"] + path, data=json.dumps({"query": POSH, "tenant_id": "acme"}).encode(),
                                 method="POST", headers={"Content-Type": "application/json",
                                                         "Authorization": "Bearer " + os.environ["TOKEN"]})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.headers.get("Content-Type"), r.read().decode()
kind, sse = post("/v1/stream")
events = [b.split("\\n") for b in sse.strip().split("\\n\\n")]
done = json.loads(events[-1][1][len("data: "):])
print("  /v1/stream", kind, "|", " then ".join(e[0] for e in events))
text = json.loads(events[0][1][len("data: "):])["t"]
print("    token:", text.split(". ")[0] + ".", f"({len(text)} characters in all)")
print("    done: ", {k: done[k] for k in ("model", "backend", "cost_usd", "tokens_in", "tokens_out", "cache_hit")})
kind, raw = post("/v1/query")
r = json.loads(raw)
print("  /v1/query ", kind, "|", {k: r[k] for k in ("model", "backend", "cost_usd", "answerable", "confidence", "citations")})
PY

"""

def step_02_rag_api_s_door(session):
    """Run Do it: rag-api's door at this checkpoint.

    The disclosure to /v1/stream and /v1/query as acme, with tok's token for documind-ui-sa, the account make smoke calls as. The cell takes the words from the smoke's own file.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the disclosure to rag-api's /v1/stream and /v1/query, as documind-ui-sa).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: /v1/stream text/event-stream; charset=utf-8 | event: token then event: done
        token: It sounds as if this may be about sexual harassment at work. (530 characters in all)
        done:  {'model': 'none', 'backend': 'desk_gate', 'cost_usd': 0.0, 'tokens_in': 0, 'tokens_out': 0, 'cache_hit': 'none'}
      /v1/query  application/json | {'model': 'none', 'backend': 'desk_gate', 'cost_usd': 0.0, 'answerable': False, 'confidence': 'low', 'citations': []}
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_chat_door.
COMMANDS_03 = """TOKEN="$(etok evalacme)" python - <<'PY'
import json, os, urllib.request, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from smoke.smoke_cases import POSH
body = json.dumps({"question": POSH, "session_id": "lesson105", "brain": "langchain"}).encode()
req = urllib.request.Request(os.environ["CHAT"] + "/v1/chat", data=body, method="POST",
                             headers={"Content-Type": "application/json", "Authorization": "Bearer " + os.environ["TOKEN"]})
a = json.load(urllib.request.urlopen(req, timeout=60))
print(f"  brain {a['brain']}  model {a['model']}  tool_calls {a['tool_calls']}  citations {a['citations']}"
      f"  model_calls {a['limits']['model_calls']}  Rs {a['limits']['cost_inr']}")
print(f"  case_offer {a['case_offer']}")
print("  " + a["answer"].replace("\\n\\n", "\\n  "))
PY

"""

def step_03_the_chat_door(session):
    """Run Do it: the chat door at this checkpoint.

    The same words to the chat service as evalacme, asking for the langchain brain, which would send them to Gemini first. The cell also prints case_offer, the field the Desk page reads.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same words to the chat service, as an acme employee, asking for an agent brain).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: brain desk_gate  model none  tool_calls []  citations []  model_calls 0  Rs 0.0
      case_offer {'case_type': 'posh'}
      It sounds as if this may be about sexual harassment at work. DocuMind does not answer this itself: it did not search its documents for this or write an answer to it.
      Under the Sexual Harassment of Women at Workplace (Prevention, Prohibition and Redressal) Act, 2013, your employer's Internal Committee receives complaints. Each district also has a Local Committee, which receives complaints in the cases the Act names. You choose what to share with them.
      If the Act does not cover you, your company's own policy may still apply.
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_20', step_01_the_gate_on_your_machine),
        ('source_25', step_02_rag_api_s_door),
        ('source_27', step_03_the_chat_door),
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
