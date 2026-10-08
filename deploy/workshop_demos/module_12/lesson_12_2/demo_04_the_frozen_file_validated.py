"""Lesson 12.2: The frozen file, validated

Do it

Run order inside this file:
1. Do it (source window 12)

Prerequisites: demo_03_the_checks_that_run_before_the_spend.
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


def step_01_the_frozen_file_validated(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the bucket and Firestore; one DLP scan in asia-south1).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the file make tune VERSION=v2 reads: gs://documind-ai-YOUR-ID-datasets/sft/documind_sft_v2.vertex.jsonl
      vertex sha256 as the manifest says
      chat   sha256 as the manifest says
    1. the shape: 315 of 315 rows are a system instruction, a user turn and a model turn, text only; the chat file says the same in 315; targets that parse as ModelDraft: 315
    2. the test set: the golden set (65 rows) would drop 0 of 315
    3. personal data, by the kit's own scan (DLP in asia-south1, LIKELY or above; findings, never the values):
       in the questions and answers, which make trainset scans: 0 rows
       in the chunks the user turns carry, which it does not: 1 row
         acme:cgst_act_2017#p1-0: EMAIL_ADDRESS
    4. resi
    """
    import hashlib, json, os, sys
    sys.path[:0] = [".", "evals", "services/rag-api"]
    P, V = os.environ["PROJECT"], "v2"
    os.environ.setdefault("GOOGLE_CLOUD_PROJECT", P)              # shared/pii and shared/tenancy find the project here
    from google.cloud import storage
    import make_trainset as mt
    from context_budget import estimate_tokens
    from shared import tenancy
    from shared.documind_schemas import ModelDraft
    from shared.pii import LOCATION, MIN_LIKELIHOOD, inspect_many
    bucket = storage.Client(project=P).bucket(f"{P}-datasets")
    m = json.loads(bucket.blob(f"sft/documind_sft_{V}.manifest.json").download_as_text())
    print(f"the file make tune VERSION={V} reads: gs://{P}-datasets/sft/documind_sft_{V}.vertex.jsonl")
    data, same = {}, True
    for fmt, f in m["files"].items():
        data[fmt] = bucket.blob("sft/" + os.path.basename(f["path"])).download_as_bytes()
        ok = hashlib.sha256(data[fmt]).hexdigest() == f["sha256"]
        same &= ok
        print(f"  {fmt:6} sha256 {'as the manifest says' if ok else 'DIFFERS FROM THE MANIFEST'}")
    vertex = [json.loads(l) for l in data["vertex"].decode("utf-8").splitlines()]
    chat = [json.loads(l) for l in data["chat"].decode("utf-8").splitlines()]
    shape = sum(bool(v["systemInstruction"]["parts"][0].get("text")) and [c["role"] for c in v["contents"]] == ["user", "model"]
                and all(list(p) == ["text"] for c in v["contents"] for p in c["parts"]) for v in vertex)
    twin = sum([x["content"] for x in c["messages"]] == [v["systemInstruction"]["parts"][0]["text"]] + [x["parts"][0]["text"] for x in v["contents"]]
               for v, c in zip(vertex, chat))
    drafts = [ModelDraft.model_validate_json(v["contents"][1]["parts"][0]["text"]) for v in vertex]
    print(f"1. the shape: {shape} of {len(vertex)} rows are a system instruction, a user turn and a model turn, text only; "
          f"the chat file says the same in {twin}; targets that parse as ModelDraft: {len(drafts)}")
    chunks = {c["text"].strip(): c for c in mt.load_chunks(m["tenant"])}
    rows = []
    for v, d in zip(vertex, drafts):
        user = v["contents"][0]["parts"][0]["text"]
        text = user.split("[Source 1] ", 1)[1].rsplit("\n\nQuestion: ", 1)[0]
        c = chunks[text.strip()]
        rows.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "text": text,
                     "question": user.rsplit("\n\nQuestion: ", 1)[1], "answer": d.answer})
    golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
    dropped = mt.exclude_golden(rows, golden)[1]
    print(f"2. the test set: the golden set ({len(golden)} rows) would drop {len(dropped)} of {len(rows)}")
    qa = inspect_many([x for r in rows for x in (r["question"], r["answer"])])
    qa_rows = sum(bool(qa[2 * i] or qa[2 * i + 1]) for i in range(len(rows)))
    hits = [(r["chunk_id"], sorted({f["info_type"] for f in fs})) for r, fs in zip(rows, inspect_many([r["text"] for r in rows])) if fs]
    n_rows = lambda n: f"{n} row" + ("" if n == 1 else "s")
    print(f"3. personal data, by the kit's own scan (DLP in {LOCATION}, {MIN_LIKELIHOOD} or above; findings, never the values):")
    print(f"   in the questions and answers, which make trainset scans: {n_rows(qa_rows)}")
    print(f"   in the chunks the user turns carry, which it does not: {n_rows(len(hits))}")
    for cid, kinds in hits:
        print(f"     {cid}: {', '.join(kinds)}")
    policy = tenancy.policy_for(m["tenant"])
    leaves = tenancy.permits(policy, "us-central1")
    print(f"4. residency: the rows are {m['tenant']}'s, whose data_region is {policy}; may they be held in us-central1? {leaves}")
    toks = [estimate_tokens(v["systemInstruction"]["parts"][0]["text"]) + sum(estimate_tokens(c["parts"][0]["text"]) for c in v["contents"])
            for v in vertex]
    EPOCHS, USD_M = 3, 3.00          # make tune's TUNE_EPOCHS; Google's price to tune gemini-3.1-flash-lite, USD a million training tokens
    print(f"5. the size: about {sum(toks):,} tokens an epoch by the kit's estimate (characters / 4); the longest row about "
          f"{max(toks):,} of the 131,072 Google allows")
    print(f"   {EPOCHS} epochs: about {sum(toks) * EPOCHS:,} training tokens, about Rs {sum(toks) * EPOCHS * USD_M / 1e6 * 85:,.0f} at USD {USD_M:.2f} a million")
    ready = same and shape == twin == len(drafts) == len(vertex) and not dropped and not qa_rows and leaves
    print("verdict: " + ("ready to tune: the manifest's bytes, the trainer's shape, no golden row, nothing where make trainset looks, "
                         f"and {m['tenant']} may leave India" if ready else "do not tune until every line above holds"))
    if ready and hits:
        verb = "carries" if len(hits) == 1 else "carry"
        print(f"         {n_rows(len(hits))} {verb} a finding make trainset never looked for: read the chunks before you pay")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_12', step_01_the_frozen_file_validated),
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
