"""Lesson 8.2: REST: which image serves, and how many tokens a new chunk is

gcloud run services describe printed one line in step 5. Underneath it is the Cloud Run Admin API, and its service resource says more: the image in the service's template, the newest revision that is ready, where the traffic goes, and, one call further, every revision the service has kept with the image each one runs. Step 9's revert deploys one of those images again, so read them now, while the edited worker serves. The kit counts characters: the window is 400 characters, and the batcher estimates tokens as characters divided by 3. The embedding model counts tokens, and reads at most 2,048 of one text, cutting the rest unless told not to (lesson B.2 read that on Google's page on 7 October 2026). The largest chunk at 400/50 is GEN-003's first window, 368 characters. The cell cuts the handbook at 400/50 in memory, finds that window, and sends it to text-embedding-005's REST endpoint in us-central1, as the worker's client would, under the worker's task type. The response carries the model's own count beside the vector.

Run order inside this file:
1. Definition (source window 28)
2. The tokens in the largest new chunk (source window 30)

Prerequisites: demo_06_re_issue_the_handbook_as_new_bytes_and_read_the_counts.
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


def step_01_definition(session):
    """Run Definition at this checkpoint.

    gcloud run services describe printed one line in step 5. Underneath it is the Cloud Run Admin API, and its service resource says more: the image in the service's template, the newest revision that is ready, where the traffic goes, and, one call further, every revision the service has kept with the image each one runs. Step 9's revert deploys one of those images again, so read them now, while the edited worker serves.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell (a Python cell: two GETs on the Cloud Run Admin API).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/rest_revisions.txt]
    """
    import json, os, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    P, R = os.environ["PROJECT"], os.environ["REGION"]
    tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    base = f"https://run.googleapis.com/v2/projects/{P}/locations/{R}/services/documind-ingest"
    def get(url):
        """One GET on the Cloud Run Admin API, as JSON.
        
        Example: get(base)
        """
        return json.load(urllib.request.urlopen(urllib.request.Request(url, headers={"Authorization": f"Bearer {tok}"}), timeout=60))
    svc = get(base)
    print("the template's image:", svc["template"]["containers"][0]["image"].rsplit("/", 1)[-1])
    print("latest ready revision:", svc["latestReadyRevision"].rsplit("/", 1)[-1])
    for t in svc.get("trafficStatuses", []):
        print(f"traffic: {t.get('percent', 0)}% to {t.get('revision') or 'the latest ready revision'} ({t.get('type', '').rsplit('_', 1)[-1].lower()})")
    revisions = sorted(get(base + "/revisions").get("revisions", []), key=lambda r: r["createTime"], reverse=True)
    for r in revisions[:3]:
        print(f"  {r['name'].rsplit('/', 1)[-1]:30} {r['createTime'][:19]}  {r['containers'][0]['image'].rsplit('/', 1)[-1]}")

def step_02_the_tokens_in_the_largest_new_chunk(session):
    """Run The tokens in the largest new chunk at this checkpoint.

    The kit counts characters: the window is 400 characters, and the batcher estimates tokens as characters divided by 3. The embedding model counts tokens, and reads at most 2,048 of one text, cutting the rest unless told not to (lesson B.2 read that on Google's page on 7 October 2026). The largest chunk at 400/50 is GEN-003's first window, 368 characters. The cell cuts the handbook at 400/50 in memory, finds that window, and sends it to text-embedding-005's REST endpoint in us-central1, as the worker's client would, under the worker's task type. The response carries the model's own count beside the vector.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell: one embedding, a fraction of a paisa).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/token_check.txt]
    """
    import json, os, subprocess, urllib.request, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    from shared import documind_corpus as dc
    dc.CHUNK_CHARS, dc.CHUNK_OVERLAP = 400, 50              # the pair the worker runs now, set in memory
    hb = open("evals/corpus/acme/hr_policy_2026.md", encoding="utf-8").read()
    chunks = dc.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "source_uri": "gs://x", "text": hb}, "acme")
    big = max(chunks, key=lambda c: len(c["text"]))
    P = os.environ["PROJECT"]
    tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
    url = (f"https://us-central1-aiplatform.googleapis.com/v1/projects/{P}/locations/us-central1"
           "/publishers/google/models/text-embedding-005:predict")
    body = {"instances": [{"content": big["text"], "task_type": "RETRIEVAL_DOCUMENT"}], "parameters": {"outputDimensionality": 768}}
    req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    r = json.load(urllib.request.urlopen(req, timeout=60))
    e = r["predictions"][0]["embeddings"]
    print(f"{big['locator']}: {len(big['text'])} characters; the kit's estimate {len(big['text']) // dc.CHARS_PER_TOKEN} tokens (characters // {dc.CHARS_PER_TOKEN})")
    print(f"the model read {e['statistics']['token_count']} tokens, truncated {e['statistics']['truncated']}, "
          f"{len(e['values'])} numbers back; billable characters {r.get('metadata', {}).get('billableCharacterCount')}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_28', step_01_definition),
        ('source_30', step_02_the_tokens_in_the_largest_new_chunk),
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
