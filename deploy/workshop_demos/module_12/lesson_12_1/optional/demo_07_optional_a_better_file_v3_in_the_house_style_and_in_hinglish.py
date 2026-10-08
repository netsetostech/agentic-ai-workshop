"""Lesson 12.1: Optional: a better file, v3, in the house style and in Hinglish

Do it Then read the frozen file back from the bucket and check it with the kit's own functions. The last lines print one chunk's two rows, the English and its Hinglish twin:

Run order inside this file:
1. Do it (source window 24)
2. Do it (source window 26)

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


# Original CLI workflow for step_01_optional_a_better_file_v3_in_the_house_sty.
COMMANDS_01 = """python -m pip install -q google-genai==2.22.0 google-cloud-dlp==3.39.0   # the same pins as step 5
make trainset PROJECT="$PROJECT" TRAINSET_ARGS="--version v3 --style helpdesk"     # v2 stays as it is

"""

def step_01_optional_a_better_file_v3_in_the_house_sty(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (about twenty-five minutes: one teacher call a chunk).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: python evals/make_trainset.py --project documind-ai-YOUR-ID --tenant acme --rows ${ROWS:-300} \\
      --upload gs://documind-ai-YOUR-ID-datasets/sft/ --version v3 --style helpdesk
      300 chunks sampled from acme's corpus mirrors, the handbook's 272 generated GEN- sections left out; gemini-3.1-pro-preview writes each pair and its Hinglish twin
      395 training rows (131 in Hinglish, 27 refusals) and 40 validation rows from 11 documents, each prompt the served one with 2 other sources
      dropped 10 pairs whose quote was not in its chunk or ran over twenty-five words, 0 with no verdict or reason, 5 Hinglish twins that were not Hinglish, 23 rows for golden overlap ['jn-10', 'lk-10', 'lk-14', 'lk-17', 'l
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_optional_a_better_file_v3_in_the_house_sty(session):
    """Run Do it at this checkpoint.

    Then read the frozen file back from the bucket and check it with the kit's own functions. The last lines print one chunk's two rows, the English and its Hinglish twin:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — optional: run in the operator shell, in the kit (reads only).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the frozen manifest: v3, helpdesk style, teacher gemini-3.1-pro-preview: 395 training rows (131 in Hinglish, 27 refusals) and 40 validation rows
      vertex     documind_sft_v3.vertex.jsonl: 395 rows, sha256 as the manifest says
      chat       documind_sft_v3.chat.jsonl: 395 rows, sha256 as the manifest says
      validation documind_sft_v3.validation.vertex.jsonl: 40 rows, sha256 as the manifest says
      rows       documind_sft_v3.rows.jsonl: 435 rows, sha256 as the manifest says
    the prompts: 395 of 395 are the served shape - SYSTEM once, 3 sources under their header lines, the question
    the answers: 368 of 368 mark the source their citation names; 368 of 368 quotes are in their chunk, at most twenty-f
    """
    import hashlib, json, os, re, sys
    from google.cloud import storage
    sys.path[:0] = [".", "evals"]
    import make_trainset as mt
    P = os.environ["PROJECT"]
    bucket = storage.Client(project=P).bucket(f"{P}-datasets")
    m = json.loads(bucket.blob("sft/documind_sft_v3.manifest.json").download_as_text())
    print(f"the frozen manifest: {m['version']}, {m['style']} style, teacher {m['teacher']}: {m['rows']} training rows "
          f"({m['hinglish_rows']} in Hinglish, {m['refusals']} refusals) and {m['validation_rows']} validation rows")
    data = {}
    for key, f in m["files"].items():
        data[key] = bucket.blob("sft/" + os.path.basename(f["path"])).download_as_bytes()
        same = hashlib.sha256(data[key]).hexdigest() == f["sha256"]
        print(f"  {key:10} {os.path.basename(f['path'])}: {len(data[key].splitlines())} rows, sha256 {'as the manifest says' if same else 'DIFFERS FROM THE MANIFEST'}")
    index = [json.loads(l) for l in data["rows"].decode("utf-8").splitlines()]
    train = [json.loads(l) for l in data["vertex"].decode("utf-8").splitlines()]
    rows = [dict(i, prompt=v["contents"][0]["parts"][0]["text"], draft=json.loads(v["contents"][1]["parts"][0]["text"]))
            for i, v in zip([i for i in index if i["split"] == "train"], train)]
    k = 1 + m["distractors"]
    served = sum(r["prompt"].startswith(mt.SYSTEM) and r["prompt"].count("You are DocuMind") == 1 and r["prompt"].count("\n[Source ") == k for r in rows)
    print(f"the prompts: {served} of {len(rows)} are the served shape - SYSTEM once, {k} sources under their header lines, the question")
    chunks = {c["chunk_id"]: c for c in mt.load_chunks(m["tenant"])}
    said = [r for r in rows if r["answerable"]]
    marked = sum(r["draft"]["citations"][0]["source"] == r["position"] and f"[{r['position']}]" in r["draft"]["answer"] for r in said)
    quoted = sum(mt.quote_holds(r["draft"]["citations"][0]["quote"], chunks[r["chunk_id"]]["text"]) for r in said)
    print(f"the answers: {marked} of {len(said)} mark the source their citation names; {quoted} of {len(said)} quotes are in their chunk, "
          f"at most twenty-five words")
    golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
    again = mt.exclude_golden([dict(i, text=chunks[i["chunk_id"]]["text"]) for i in index], golden)[1]
    print(f"the test set: the golden set would drop {len(again)} of {len(index)} rows; rows from the handbook's GEN- sections: "
          f"{sum('#GEN-' in i['chunk_id'] for i in index)}")
    held = {i["chunk_id"] for i in index if i["split"] == "validation"}
    print(f"the split: {len(held)} chunks held out for validation, every twin beside its pair: "
          f"{all((i['chunk_id'] in held) == (i['split'] == 'validation') for i in index)}")
    twins = [r for r in rows if r["lang"] == "hinglish" and r["answerable"]]
    twin = next((r for r in twins if "gratuity" in r["chunk_id"]), twins[0] if twins else None)
    for r in [x for x in rows if twin and x["chunk_id"] == twin["chunk_id"] and x["answerable"]]:
        print(f"\n  {r['lang']}: {r['chunk_id']}, answered from [Source {r['position']}]")
        print("  " + "\n  ".join(line for line in r["prompt"].splitlines() if line.startswith("[Source ")))
        print(f"  Question: {r['question']}")
        print("  " + r["draft"]["answer"].replace("\n", "\n  "))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_24', step_01_optional_a_better_file_v3_in_the_house_sty),
        ('source_26', step_02_optional_a_better_file_v3_in_the_house_sty),
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
