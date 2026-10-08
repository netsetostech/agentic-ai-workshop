"""Lesson 9.2: The small model behind the gateway and the API

Do it

Run order inside this file:
1. Do it (source window 25)
2. Do it (source window 27)
3. Do it (source window 29)
4. Do it (source window 31)
5. Do it (source window 33)
6. Do it (source window 35)

Prerequisites: demo_06_the_cold_start_timed.
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


def step_01_the_small_model_behind_the_gateway_and_the(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (lesson 9.1's three requests, through the gateway).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: USD a million tokens, in and out (config.yaml): documind-general 1.50 and 7.50, documind-sensitive 20.50 and 20.50
      no personal data  HTTP 200  answered by gemini-3.6-flash; 11 tokens in, 1 out; x-litellm-response-cost 2.4e-05
      a bare PAN        HTTP 200  answered by gemini-3.6-flash; 16 tokens in, 1 out; x-litellm-response-cost 3.15e-05
      a PAN and a date  HTTP 200  answered by ollama_chat/documind-slm; 19 tokens in, 30 out; x-litellm-response-cost 0.0010045
                        Your notice period depends on your grade and confirmation status; the documents you shared do not say which applies to you.
    """
    import json, os, re, subprocess, urllib.error, urllib.request
    P, N, R = os.environ["PROJECT"], os.environ["NUMBER"], os.environ["REGION"]
    GW = f"https://documind-gateway-{N}.{R}.run.app"
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email",
                          f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com", f"--audiences={GW}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    rates, group = {}, None                                        # config.yaml's per-token rates, by route
    for line in open("services/litellm/config.yaml", encoding="utf-8"):
        m = re.match(r"  - model_name: (\S+)", line)
        group = m.group(1) if m else group
        m = re.match(r"\s+(input|output)_cost_per_token: ([\d.]+)", line)
        if m:
            rates.setdefault(group, {})[m.group(1)] = float(m.group(2))
    
    
    def ask(text):
        """Send this example request to the selected API and return its response for the following comparison.
        
        Example: ask(text)
        """
        body = json.dumps({"model": "documind-general", "messages": [{"role": "user", "content": text}], "max_tokens": 60}).encode()
        req = urllib.request.Request(f"{GW}/v1/chat/completions", data=body, method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"})
        try:
            with urllib.request.urlopen(req, timeout=150) as r:
                return r.status, json.loads(r.read()), r.headers.get("x-litellm-response-cost")
        except urllib.error.HTTPError as e:
            return e.code, None, None
    
    
    per_m = lambda g: f"{rates[g]['input'] * 1e6:.2f} and {rates[g]['output'] * 1e6:.2f}"
    print(f"USD a million tokens, in and out (config.yaml): documind-general {per_m('documind-general')}, documind-sensitive {per_m('documind-sensitive')}")
    for label, text in (("no personal data", "What is the notice period for a confirmed E3?"),
                        ("a bare PAN", "My PAN is ABCDE1234F. What is the notice period for a confirmed E3?"),
                        ("a PAN and a date", "My PAN is ABCDE1234F and I joined on 5 March 2026. What is my notice period?")):
        status, j, cost = ask(text)
        if status != 200:
            print(f"  {label:17} HTTP {status}  no answer")
            continue
        u = j["usage"]
        print(f"  {label:17} HTTP 200  answered by {j['model']}; {u['prompt_tokens']} tokens in, {u['completion_tokens']} out; "
              f"x-litellm-response-cost {cost}")
        if not j["model"].startswith("gemini"):
            print(f"  {'':17} {j['choices'][0]['message']['content']}")

# Original CLI workflow for step_02_the_small_model_behind_the_gateway_and_the.
COMMANDS_02 = """make candidate PROJECT="$PROJECT" MODEL_BACKEND=gateway GENERATOR_MODEL=documind-slm
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"

"""

def step_02_the_small_model_behind_the_gateway_and_the(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a no-traffic revision; the live one keeps its settings).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\
      --update-env-vars "^|^GENERATOR_MODEL=documind-slm|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|MODEL_BACKEND=gateway|ARMOR=off|SEMANTIC_CACHE=off|RETRIEVAL_CURRENT_ONLY=off|RETRIEVAL_GRAPH=off|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
    ...
    >> candidate revision: documind-api-000NN-xxx (deploy/.candidate-revision - make promote moves traffic to it by name)
    >> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documin
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def step_03_the_small_model_behind_the_gateway_and_the(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one golden question through the candidate).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lk-06: What is the notice period for a confirmed E3?
    answer: A confirmed E3 serves a notice period of 60 days [1].
      cites acme:lk-06#0
    model documind-slm, backend gateway: the route the API asked for, whoever answered
    cost 0.03977 USD for 1900 tokens in and 40 out: documind-slm's rate, so the small model answered
    """
    import json, os, re, subprocess, urllib.request
    P, N, R = os.environ["PROJECT"], os.environ["NUMBER"], os.environ["REGION"]
    API, CAND = f"https://documind-api-{N}.{R}.run.app", os.environ["CAND"]
    tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email",       # the API checks the token against its own URL
                          f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com", f"--audiences={API}"],
                         capture_output=True, text=True, check=True).stdout.strip()
    rates, group = {}, None
    for line in open("services/litellm/config.yaml", encoding="utf-8"):
        m = re.match(r"  - model_name: (\S+)", line)
        group = m.group(1) if m else group
        m = re.match(r"\s+(input|output)_cost_per_token: ([\d.]+)", line)
        if m:
            rates.setdefault(group, {})[m.group(1)] = float(m.group(2))
    q = "What is the notice period for a confirmed E3?"                        # golden row lk-06
    req = urllib.request.Request(f"{CAND}/v1/query", data=json.dumps({"query": q, "tenant_id": "acme"}).encode(), method="POST",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        j = json.loads(r.read())
    print("lk-06:", q)
    print("answer:", j["answer"])
    for c in j["citations"]:
        print("  cites", c["chunk_id"])
    print(f"model {j['model']}, backend {j['backend']}: the route the API asked for, whoever answered")
    tin, tout, cost = j["tokens_in"], j["tokens_out"], j["cost_usd"]
    priced = {g: tin * v["input"] + tout * v["output"] for g, v in rates.items() if g in ("documind-slm", "documind-general")}
    who = [g for g, usd in priced.items() if cost is not None and abs(usd - cost) < 1e-9]
    print(f"cost {cost} USD for {tin} tokens in and {tout} out: " + (f"{who[0]}'s rate, so " + ("the small model answered" if who[0] == "documind-slm"
          else "Gemini answered: the hook moved it") if who else "no route's rate matches"))

# Original CLI workflow for step_04_the_small_model_behind_the_gateway_and_the.
COMMANDS_04 = """make eval-live PROJECT="$PROJECT" API="$CAND" SOURCE=hr_policy_2026.md REPORT="$HOME/slm182.json"

"""

def step_04_the_small_model_behind_the_gateway_and_the(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the gate, scoped to the HR policy's rows).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: >> https://candidate---documind-api-NUMBER.asia-south1.run.app
    == eval gate: LIVE ==
      scoped to hr_policy_2026.md: 10 row(s) cite it
      10 rows (10 answerable, 0 not) against https://candidate---documind-api-NUMBER.asia-south1.run.app

      [PASS] request_success_rate  100.0%  (threshold 100%; 10 rows)
      [PASS] answerable_rate        90.0%  (threshold 80%; 10 rows)
      [PASS] citation_rate         100.0%  (threshold 95%; 9 rows)
      [PASS] citation_valid_rate   100.0%  (threshold 100%; 9 rows)
      [PASS] must_contain_rate      88.9%  (threshold 85%; 9 rows)
      [PASS] correct_rate           80.0%  (threshold 68%; 10 rows)
      [ -- ] refusal_rate            0.0%  (threshold 90%; no rows in scope; 0 rows)

    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def step_05_the_small_model_behind_the_gateway_and_the(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (reads the gate's report).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: lk-06: pass, 1 citation(s); the route it asked for: documind-slm, through the gateway
    8 of 10 rows passed; all thresholds met
    """
    import json, os
    rep = json.load(open(os.path.expanduser("~/slm182.json"), encoding="utf-8"))
    row = next(r for r in rep["records"] if r["id"] == "lk-06")
    print(f"lk-06: {'pass' if row['pass'] else 'fail'}, {row['citations']} citation(s); the route it asked for: {row['model']}, through the {row['backend']}")
    print(f"{sum(r['pass'] for r in rep['records'])} of {len(rep['records'])} rows passed; "
          + ("all thresholds met" if not rep["failed"] else "below the threshold: " + ", ".join(rep["failed"])))

# Original CLI workflow for step_06_the_small_model_behind_the_gateway_and_the.
COMMANDS_06 = """gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet
rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag
make slm-off PROJECT="$PROJECT"

"""

def step_06_the_small_model_behind_the_gateway_and_the(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit, when you are done.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ...
    gcloud run services update documind-slm --region us-central1 --project documind-ai-YOUR-ID --min-instances 0 --quiet
    ...
    documind-slm scaled to zero
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_06)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_the_small_model_behind_the_gateway_and_the),
        ('source_27', step_02_the_small_model_behind_the_gateway_and_the),
        ('source_29', step_03_the_small_model_behind_the_gateway_and_the),
        ('source_31', step_04_the_small_model_behind_the_gateway_and_the),
        ('source_33', step_05_the_small_model_behind_the_gateway_and_the),
        ('source_35', step_06_the_small_model_behind_the_gateway_and_the),
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
