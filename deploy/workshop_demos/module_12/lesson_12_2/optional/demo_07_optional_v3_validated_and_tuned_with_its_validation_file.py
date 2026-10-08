"""Lesson 12.2: Optional: v3, validated and tuned with its validation file

Do it Then submit the job with a name that says v3 and the validation file, and return at once: Then submit the job with a name that says v3 and the validation file, and return at once: Then wait for it. The poll only reads, so after a disconnect it is safe to run again:

Run order inside this file:
1. Do it (source window 23)
2. Do it (source window 25)
3. Do it (source window 27)

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


def step_01_optional_v3_validated_and_tuned_with_its_v(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (reads the bucket and Firestore; DLP over every prompt).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the files make tune VERSION=v3 reads: documind_sft_v3.vertex.jsonl, and with --validation documind_sft_v3.validation.vertex.jsonl
      vertex     sha256 as the manifest says
      chat       sha256 as the manifest says
      validation sha256 as the manifest says
      rows       sha256 as the manifest says
    1. the shape: 435 of 435 rows are one user turn that is the served prompt and one model turn, text only; the chat file says the same in 395 of 395; targets that parse as ModelDraft: 435
    2. the test set: the golden set would drop 0 of 435 rows; 0 of the 598 chunks in the prompts are a golden row's evidence
    3. personal data: DLP over every prompt and every answer, so over every chunk: 0 with a finding
    4. 
    """
    import hashlib, json, os, sys
    sys.path[:0] = [".", "evals", "services/rag-api"]
    P, V = os.environ["PROJECT"], "v3"
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", P)
    from google.cloud import storage
    import make_trainset as mt
    from context_budget import estimate_tokens
    from shared import tenancy
    from shared.documind_schemas import ModelDraft
    from shared.pii import inspect_many
    bucket = storage.Client(project=P).bucket(f"{P}-datasets")
    m = json.loads(bucket.blob(f"sft/documind_sft_{V}.manifest.json").download_as_text())
    print(f"the files make tune VERSION={V} reads: documind_sft_{V}.vertex.jsonl, and with --validation documind_sft_{V}.validation.vertex.jsonl")
    data = {}
    for key, f in m["files"].items():
        data[key] = bucket.blob("sft/" + os.path.basename(f["path"])).download_as_bytes()
        print(f"  {key:10} sha256 {'as the manifest says' if hashlib.sha256(data[key]).hexdigest() == f['sha256'] else 'DIFFERS FROM THE MANIFEST'}")
    rows_of = lambda key: [json.loads(l) for l in data[key].decode("utf-8").splitlines()]
    train, held, chat, index = rows_of("vertex"), rows_of("validation"), rows_of("chat"), rows_of("rows")
    shape = sum("systemInstruction" not in v and [c["role"] for c in v["contents"]] == ["user", "model"]
                and all(list(p) == ["text"] for c in v["contents"] for p in c["parts"])
                and v["contents"][0]["parts"][0]["text"].startswith(mt.SYSTEM) for v in train + held)
    twin = sum([x["content"] for x in c["messages"]] == [x["parts"][0]["text"] for x in v["contents"]] for v, c in zip(train, chat))
    drafts = [ModelDraft.model_validate_json(v["contents"][1]["parts"][0]["text"]) for v in train + held]
    print(f"1. the shape: {shape} of {len(train) + len(held)} rows are one user turn that is the served prompt and one model turn, text only; "
          f"the chat file says the same in {twin} of {len(chat)}; targets that parse as ModelDraft: {len(drafts)}")
    chunks = {c["chunk_id"]: c for c in mt.load_chunks(m["tenant"])}
    golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
    dropped = mt.exclude_golden([dict(i, text=chunks[i["chunk_id"]]["text"]) for i in index], golden)[1]
    beside = {c for i in index for c in i["context_ids"]}
    evidence = sum(bool(mt.exclude_golden([dict(chunks[c], question="")], golden)[1]) for c in beside)
    print(f"2. the test set: the golden set would drop {len(dropped)} of {len(index)} rows; {evidence} of the {len(beside)} chunks in the prompts "
          f"are a golden row's evidence")
    texts = [t for v in train + held for t in (v["contents"][0]["parts"][0]["text"], v["contents"][1]["parts"][0]["text"])]
    found = sum(bool(f) for f in inspect_many(texts))
    print(f"3. personal data: DLP over every prompt and every answer, so over every chunk: {found} with a finding")
    policy = tenancy.policy_for(m["tenant"])
    leaves = tenancy.permits(policy, "us-central1")
    print(f"4. residency: the rows are {m['tenant']}'s, whose data_region is {policy}; may they be held in us-central1? {leaves}")
    tokens = lambda rows: [sum(estimate_tokens(c["parts"][0]["text"]) for c in v["contents"]) for v in rows]
    t_train, t_held = tokens(train), tokens(held)
    EPOCHS, USD_M = 3, 3.00          # make tune's TUNE_EPOCHS; Google's price to tune gemini-3.1-flash-lite, USD a million training tokens
    print(f"5. the size: about {sum(t_train):,} tokens an epoch, the longest row about {max(t_train + t_held):,} of the 131,072 Google allows; "
          f"the validation file about {sum(t_held):,}, scored and never trained on")
    print(f"   {EPOCHS} epochs: about {sum(t_train) * EPOCHS:,} training tokens, about Rs {sum(t_train) * EPOCHS * USD_M / 1e6 * 85:,.0f} at USD {USD_M:.2f} a million")
    same = all(hashlib.sha256(data[k]).hexdigest() == f["sha256"] for k, f in m["files"].items())
    ready = same and shape == len(drafts) == len(train) + len(held) and twin == len(chat) and not dropped and not evidence and not found and leaves
    print("verdict: " + ("ready to tune: the manifest's bytes, the served shape, no golden row or evidence in any prompt, no finding in any chunk, "
                         f"and {m['tenant']} may leave India" if ready else "do not tune until every line above holds"))

# Original CLI workflow for step_02_optional_v3_validated_and_tuned_with_its_v.
COMMANDS_02 = """VAL="gs://$PROJECT-datasets/sft/documind_sft_v3.validation.vertex.jsonl"     # lesson 12.1's step 7 wrote it
make tune PROJECT="$PROJECT" VERSION=v3 TUNE_ARGS="--display-name documind-sft-v3 --validation $VAL --no-wait" | tee ~/tune172v3.log
export JOB_V3="$(grep -o 'projects/[^ ]*/tuningJobs/[0-9]*' ~/tune172v3.log | head -1)"; echo "JOB_V3=$JOB_V3"

"""

def step_02_optional_v3_validated_and_tuned_with_its_v(session):
    """Run Do it at this checkpoint.

    Then submit the job with a name that says v3 and the validation file, and return at once:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (submits the v3 job and returns: a second billed act).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/tune.py --project documind-ai-YOUR-ID --dataset gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_${VERSION:-v1}.vertex.jsonl \\
      --base gemini-3.1-flash-lite --epochs 3 --adapter 4 --display-name documind-sft-v3 --validation gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v3.validation.vertex.jsonl --no-wait
      submitted projects/NUMBER/locations/us-central1/tuningJobs/4763636347812545555 on gemini-3.1-flash-lite: 3 epochs, adapter 4, dataset gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v3.vertex.jsonl
      poll later: python evals/tune.py --project documind-ai-YOUR-ID --poll projects/NUMBER/locations/us-central1/tuningJobs/4763636347812545555
    JOB_V3=projects/NUMBER/locat
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_optional_v3_validated_and_tuned_with_its_v.
COMMANDS_03 = """JOB_V3="${JOB_V3:-$(grep -o 'projects/[^ ]*/tuningJobs/[0-9]*' ~/tune172v3.log | head -1)}"     # after a reconnect: from the log
python evals/tune.py --project "$PROJECT" --poll "$JOB_V3" | tee ~/poll172v3.log   # a line a minute; safe to re-run
export ENDPOINT_V3="$(grep -o 'projects/[^ ]*/endpoints/[0-9]*' ~/poll172v3.log | head -1)"; echo "ENDPOINT_V3=$ENDPOINT_V3"

"""

def step_03_optional_v3_validated_and_tuned_with_its_v(session):
    """Run Do it at this checkpoint.

    Then submit the job with a name that says v3 and the validation file, and return at once: Then wait for it. The poll only reads, so after a disconnect it is safe to run again:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (waits for the v3 job, a line a minute).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: 10:03:00 JobState.JOB_STATE_PENDING
      10:04:00 JobState.JOB_STATE_PENDING
      10:05:00 JobState.JOB_STATE_RUNNING
      ...      (a line a minute while the job runs: 33 more here)
      10:39:00 JobState.JOB_STATE_RUNNING
      JOB_STATE_SUCCEEDED
      tuned model : projects/NUMBER/locations/us/models/8366872049017976783@1
      endpoint    : projects/NUMBER/locations/us/endpoints/3784707595493887459

      serve it as a candidate revision, no traffic, and judge it:
        make candidate PROJECT=documind-ai-YOUR-ID GENERATOR_MODEL=projects/NUMBER/locations/us/endpoints/3784707595493887459 RAG_MODEL_BASE=gemini-3.1-flash-lite
        make eval-live PROJECT=documind-ai-YOUR-ID API=<the candidate url>
        make judge PROJECT=d
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_optional_v3_validated_and_tuned_with_its_v),
        ('source_25', step_02_optional_v3_validated_and_tuned_with_its_v),
        ('source_27', step_03_optional_v3_validated_and_tuned_with_its_v),
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
