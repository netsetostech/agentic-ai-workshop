"""Lesson 12.3: The candidate, audited

Do it: the candidate The cell makes the four checks from step 1:

Run order inside this file:
1. Do it: the candidate (source window 12)
2. Do it: the audit (source window 14)

Prerequisites: demo_03_what_the_kit_does_with_a_tuned_candidate.
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
COMMANDS_01 = """export ENDPOINT="${ENDPOINT:-$(grep -o 'projects/[^ ]*/endpoints/[0-9]*' ~/poll172.log | head -1)}"     # lesson 12.2's endpoint
make candidate PROJECT="$PROJECT" GENERATOR_MODEL="$ENDPOINT" RAG_MODEL_BASE=gemini-3.1-flash-lite
export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"

"""

def step_01_the_candidate(session):
    """Run Do it: the candidate at this checkpoint.

    Do it: the candidate

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (a revision with no traffic; nothing is billed until it answers).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: gcloud run services update documind-api --region asia-south1 --project documind-ai-YOUR-ID --no-traffic --tag candidate \\
      --update-env-vars "^|^GENERATOR_MODEL=projects/NUMBER/locations/us/endpoints/9136961803583303949|RAG_MODEL_BASE=gemini-3.1-flash-lite|ROUTING=off|MODEL_BACKEND=vertex|ARMOR=off|SEMANTIC_CACHE=off|RETRIEVAL_CURRENT_ONLY=off|RETRIEVAL_GRAPH=off|GRAPH_BACKEND=firestore|SPANNER_INSTANCE=documind-graph|SPANNER_DATABASE=documind" --remove-env-vars GENERATOR_LOCATION
    ...
    >> candidate revision: documind-api-000NN-yyy (deploy/.candidate-revision - make promote moves traffic to it by name)
    >> candidate: https://candidate---documind-api-NUMBER.asia-south1.run.app (no traffic; remo
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_the_audit(session):
    """Run Do it: the audit at this checkpoint.

    The cell makes the four checks from step 1:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads both revisions, ~/tune172.log, the bucket and Firestore).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 1. one change: 2 settings differ between documind-api-000NN-xxx (live) and documind-api-000NN-yyy
       GENERATOR_MODEL  gemini-3.6-flash -> projects/NUMBER/locations/us/endpoints/9136961803583303949
       RAG_MODEL_BASE   gemini-3.6-flash -> gemini-3.1-flash-lite
       the model and the base it is priced at, and nothing else
    2. the answer cache: off on the live revision, off on the candidate
    3. the test set: the endpoint was tuned on documind_sft_v2.vertex.jsonl, 315 rows; building it dropped 15 for the golden set, and today's golden set would drop 0 more
    4. the context cache: none for acme, so both revisions pay full price for their input
    verdict: uncontaminated - one change, no answer cache, a tra
    """
    import json, os, re, subprocess, sys
    sys.path[:0] = [".", "evals"]
    P, R = os.environ["PROJECT"], os.environ["REGION"]
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", P)
    
    
    def gcloud(*a):
        """Run this cell's gcloud command with its project/region context and decode the requested output.
        
        Example: gcloud('run', 'services', 'describe', 'documind-api')
        """
        cmd = ["gcloud", *a, "--region", R, "--project", P, "--format=json"]
        return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)
    
    
    traffic = gcloud("run", "services", "describe", "documind-api")["status"]["traffic"]
    live = max((t for t in traffic if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
    cand = next(t["revisionName"] for t in traffic if t.get("tag") == "candidate")
    env = lambda rev: {e["name"]: e.get("value", "") for e in gcloud("run", "revisions", "describe", rev)["spec"]["containers"][0].get("env", [])}
    a, b = env(live), env(cand)
    diff = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
    print(f"1. one change: {len(diff)} settings differ between {live} (live) and {cand}")
    for k in diff:
        print(f"   {k:16} {a.get(k, '(unset)')} -> {b.get(k, '(unset)')}")
    one = set(diff) == {"GENERATOR_MODEL", "RAG_MODEL_BASE"} and b["RAG_MODEL_BASE"] == "gemini-3.1-flash-lite"
    print("   " + ("the model and the base it is priced at, and nothing else" if one else "more than the model differs: run make candidate again with the live values"))
    cache = (a.get("SEMANTIC_CACHE", "off"), b.get("SEMANTIC_CACHE", "off"))
    print(f"2. the answer cache: {cache[0]} on the live revision, {cache[1]} on the candidate"
          + ("" if cache == ("off", "off") else " - its lookup never reads the model: turn it off on both first"))
    from google.cloud import firestore, storage
    import make_trainset as mt
    uri = re.search(r", dataset (gs://\S+\.vertex\.jsonl)", open(os.path.expanduser("~/tune172.log"), encoding="utf-8").read()).group(1)
    bucket_name, name = uri[len("gs://"):].split("/", 1)                       # what lesson 12.2 tuned on
    bucket = storage.Client(project=P).bucket(bucket_name)
    m = json.loads(bucket.blob(name.replace(".vertex.jsonl", ".manifest.json")).download_as_text())
    chunks = {c["text"].strip(): c for c in mt.load_chunks(m["tenant"])}
    rows = []
    for line in bucket.blob(name).download_as_text().splitlines():
        user = json.loads(line)["contents"][0]["parts"][0]["text"]
        c = chunks[user.split("[Source 1] ", 1)[1].rsplit("\n\nQuestion: ", 1)[0].strip()]
        rows.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "text": c["text"], "question": user.rsplit("\n\nQuestion: ", 1)[1]})
    golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
    left = mt.exclude_golden(rows, golden)[1]
    print(f"3. the test set: the endpoint was tuned on {name.rsplit('/', 1)[-1]}, {len(rows)} rows; building it dropped "
          f"{m['dropped_golden_overlap']} for the golden set, and today's golden set would drop {len(left)} more")
    rec = firestore.Client(project=P).collection("tenant_caches").document(m["tenant"]).get()
    print("4. the context cache: " + (f"{m['tenant']} has one, made for {rec.to_dict().get('model')}: the live revision reads it and the "
                                       f"candidate cannot - delete it for the hour (make cache TENANT={m['tenant']} CACHE_OP=delete)" if rec.exists
                                       else f"none for {m['tenant']}, so both revisions pay full price for their input"))
    clean = one and cache == ("off", "off") and not left and not rec.exists
    print("verdict: " + ("uncontaminated - one change, no answer cache, a training file the test set never entered, the same input price"
                         if clean else "not yet: fix the lines above, then run this cell again"))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_the_candidate),
        ('source_14', step_02_the_audit),
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
