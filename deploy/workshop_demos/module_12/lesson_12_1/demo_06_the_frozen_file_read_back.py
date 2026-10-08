"""Lesson 12.1: The frozen file, read back

Do it

Run order inside this file:
1. Do it (source window 21)

Prerequisites: demo_05_your_training_file_as_v2.
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


def step_01_the_frozen_file_read_back(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the frozen manifest, from gs://documind-ai-YOUR-ID-datasets/sft/: v2, built 2026-09-24, 315 rows (30 refusals) from 12 documents; generator gemini-3.6-flash
      dropped 15 for the golden set {'evidence': 10, 'question': 5} (jn-10, jn-11, lk-14, lk-17, lk-18, lk-23, lk-24, lk-26, lk-28), 0 for PII
      vertex documind_sft_v2.vertex.jsonl: 315 rows, sha256 as the manifest says
      chat   documind_sft_v2.chat.jsonl: 315 rows, sha256 as the manifest says
    the rows, checked again: the golden set would drop 0 of 315
      quotes in their chunk, line breaks as spaces: 285 of 285; over twenty-five words: 0
      answers that mark their source with [N]: 0 of 285
      rows from the handbook's generated GEN- sections: 58
    """
    import hashlib, json, os, re, sys
    from google.cloud import storage
    sys.path[:0] = [".", "evals"]
    import make_trainset as mt
    P = os.environ["PROJECT"]
    bucket = storage.Client(project=P).bucket(f"{P}-datasets")
    m = json.loads(bucket.blob("sft/documind_sft_v2.manifest.json").download_as_text())
    print(f"the frozen manifest, from gs://{P}-datasets/sft/: {m['version']}, built {m['built_at']}, {m['rows']} rows "
          f"({m['refusals']} refusals) from {len(m['documents'])} documents; generator {m['generator']}")
    print(f"  dropped {m['dropped_golden_overlap']} for the golden set {m['dropped_golden_by_rule']} "
          f"({', '.join(m['dropped_golden_ids']) or 'none'}), {m['dropped_pii']} for PII")
    for fmt, f in m["files"].items():
        data = bucket.blob("sft/" + os.path.basename(f["path"])).download_as_bytes()
        same = hashlib.sha256(data).hexdigest() == f["sha256"]
        print(f"  {fmt:6} {os.path.basename(f['path'])}: {len(data.splitlines())} rows, sha256 {'as the manifest says' if same else 'DIFFERS FROM THE MANIFEST'}")
    chunks = {c["text"].strip(): c for c in mt.load_chunks(m["tenant"])}
    rows = []
    for line in open("evals/sft/documind_sft_v2.vertex.jsonl", encoding="utf-8"):
        v = json.loads(line)
        user = v["contents"][0]["parts"][0]["text"]
        text = user.split("[Source 1] ", 1)[1].rsplit("\n\nQuestion: ", 1)[0]
        c = chunks[text.strip()]
        rows.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "text": text,
                     "question": user.rsplit("\n\nQuestion: ", 1)[1], "draft": json.loads(v["contents"][1]["parts"][0]["text"])})
    golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
    print(f"the rows, checked again: the golden set would drop {len(mt.exclude_golden(rows, golden)[1])} of {len(rows)}")
    quotes = [(r["text"], r["draft"]["citations"][0]["quote"]) for r in rows if r["draft"]["citations"]]
    flat = lambda s: re.sub(r"\s+", " ", s).strip()
    print(f"  quotes in their chunk, line breaks as spaces: {sum(flat(q) in flat(t) for t, q in quotes)} of {len(quotes)}; "
          f"over twenty-five words: {sum(len(q.split()) > 25 for _, q in quotes)}")
    said = [r["draft"]["answer"] for r in rows if r["draft"]["answerable"]]
    marked = sum(bool(re.search(r"\[(\d+(?:\s*,\s*\d+)*)\]", a)) for a in said)
    print(f"  answers that mark their source with [N]: {marked} of {len(said)}")
    print(f"  rows from the handbook's generated GEN- sections: {sum('#GEN-' in r['chunk_id'] for r in rows)}")
    for r in rows[:: max(1, len(rows) // 3)][:3]:
        print(f"  {r['chunk_id']}: {r['question']}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_21', step_01_the_frozen_file_read_back),
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
