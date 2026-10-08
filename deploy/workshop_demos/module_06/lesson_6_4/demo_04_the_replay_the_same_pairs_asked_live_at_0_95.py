"""Lesson 6.4: The replay: the same pairs, asked live at 0.95

Do it: the candidate Do it: the replay

Run order inside this file:
1. Do it: the candidate (source window 12)
2. Do it: the replay (source window 14)

Prerequisites: demo_03_the_curve_every_candidate_threshold_on_the_labelled_pairs.
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


# Original CLI workflow for step_01_the_candidate.
COMMANDS_01 = """make candidate PROJECT="$PROJECT" SEMANTIC_CACHE=on
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app" SINCE93="$(date -u +%FT%TZ)"; echo "CAND=$CAND"

"""

def step_01_the_candidate(session):
    """Run Do it: the candidate at this checkpoint.

    Do it: the candidate

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a revision with SEMANTIC_CACHE=on at the kit's 0.95, and a start time).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\
      --update-env-vars "^|^GENERATOR_MODEL=gemini-3.6-flash|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=on|..."
    ...
    >> candidate revision: documind-api-00046-wpk (deploy/.candidate-revision - make promote moves traffic to it by name)
    >> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)
    CAND=https://candidate---documind-api-NUMBER.asia-south1.run.app
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_replay.
COMMANDS_02 = """TOKEN="$(tok "$API")" python - <<'PY'
import json, os, time, urllib.error, urllib.request
URL, TOKEN = os.environ["CAND"], os.environ["TOKEN"]
gold = {r["id"]: r for r in (json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip())}
pairs = [json.loads(l) for l in open("evals/paraphrases.jsonl", encoding="utf-8") if l.strip()]
retried, failed = [], []
def ask(q, tenant):
    body = json.dumps({"query": q, "tenant_id": tenant, "top_k": 6}).encode()
    for attempt in range(2):                     # a 5xx or a timeout gets one more try, as run_eval.py gives it
        if attempt:
            time.sleep(2)
        req = urllib.request.Request(URL + "/v1/query", data=body, method="POST",
                                     headers={"Content-Type": "application/json", "Authorization": "Bearer " + TOKEN})
        try:
            a = json.load(urllib.request.urlopen(req, timeout=120))
            if attempt:
                retried.append(why)
            return a["backend"], a["answer"], a["latency_ms"]
        except urllib.error.HTTPError as e:
            why = f"HTTP {e.code}"
            if e.code < 500:
                break
        except OSError as e:                     # a timeout or a dropped connection
            why = type(e).__name__
    failed.append(f"{tenant} {q[:50]!r}: {why}")
    return "error", None, 0
first = {of: ask(gold[of]["question"], gold[of]["tenant"]) for of in sorted({p["of"] for p in pairs})}   # misses, stored when answerable
out = []
for p in pairs:
    backend, answer, ms = ask(p["question"], p["tenant"])
    src = next((of for of, (_, a, _) in first.items() if a is not None and a == answer), None) if backend == "cache" else None
    verdict = ("error" if backend == "error" else "miss" if backend != "cache" else "right hit" if p["same"] and src == p["of"]
               else "FALSE HIT" if src == p["of"] else f"hit from {src}")
    out.append({**p, "backend": backend, "ms": ms, "served_from": src, "verdict": verdict})
    if verdict not in ("miss", "error"):
        print(f"  {p['id']} {'same' if p['same'] else 'diff'} {verdict:12} {ms:>5} ms  {p['question'][:52]}")
json.dump(out, open(os.path.expanduser("~/cache93_replay.json"), "w", encoding="utf-8"), indent=1)
for same in (True, False):
    grp = [o for o in out if o["same"] is same]
    print(f"  {'same-fact' if same else 'different'} pairs served from the cache: {sum(o['backend'] == 'cache' for o in grp)} of {len(grp)}")
if retried:
    print(f"  {len(retried)} question(s) answered on a second try ({', '.join(sorted(set(retried)))} the first time): a blip, not an outage")
if failed:
    print(f"  {len(failed)} question(s) got no answer after a second try - the cell below reads the API's traceback:")
    for f in failed[:5]:
        print(f"    {f}")
PY

"""

def step_02_the_replay(session):
    """Run Do it: the replay at this checkpoint.

    Do it: the replay

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the 23 golden questions, then the 42 pairs, to the candidate; a few minutes).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: pp-01 same right hit      211 ms  How much can I claim per trip for domestic travel?
      pp-15 same right hit      188 ms  Gratuity is paid at what rate per completed year?
      pp-16 same right hit      221 ms  What is the minimum bonus payable under the Bonus Ac
      pp-17 same right hit      209 ms  Under the Code on Wages, what is the rate for overti
      pp-18 same right hit      208 ms  Under the Code on Wages, what is the deadline for pa
      pp-19 same right hit      217 ms  The standing orders chapter of the IR Code applies f
      pp-20 same right hit      194 ms  Under the OSH Code, how many days of work earn a day
      pp-21 same right hit      153 ms  Under the DPDP Act, what is a Consent Manager?
 
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_the_candidate),
        ('source_14', step_02_the_replay),
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
