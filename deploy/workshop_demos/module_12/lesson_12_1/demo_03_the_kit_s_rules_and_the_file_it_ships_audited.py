"""Lesson 12.1: The kit's rules, and the file it ships, audited

Do it

Run order inside this file:
1. Do it (source window 9)

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


# Original CLI workflow for step_01_the_kit_s_rules_and_the_file_it_ships_audi.
COMMANDS_01 = """python evals/make_trainset.py --selftest
python - <<'PY'
import json, re, sys
sys.path[:0] = [".", "evals", "services/rag-api"]
import make_trainset as mt                                    # the kit's rules and its corpus loader
from context_budget import source_header                    # the header the generator serves above each chunk
from shared.documind_schemas import ModelDraft
V = "evals/sft/documind_sft_v1"
m = json.load(open(V + ".manifest.json", encoding="utf-8"))
vertex = [json.loads(l) for l in open(V + ".vertex.jsonl", encoding="utf-8")]
chat = [json.loads(l) for l in open(V + ".chat.jsonl", encoding="utf-8")]
print(f"the manifest: {m['version']}, built {m['built_at']}, {m['rows']} rows ({m['refusals']} refusals) from "
      f"{len(m['documents'])} documents; dropped {m['dropped_golden_overlap']} for the golden set, {m['dropped_pii']} for PII")
same = all(c["messages"][2]["content"] == v["contents"][1]["parts"][0]["text"] for v, c in zip(vertex, chat))
drafts = [ModelDraft.model_validate_json(v["contents"][1]["parts"][0]["text"]) for v in vertex]
system_same = ('SYSTEM = \"\"\"' + mt.SYSTEM + '\"\"\"') in open("services/rag-api/generator.py", encoding="utf-8").read()
print(f"the two formats agree row by row: {same}; targets that parse as ModelDraft: {len(drafts)} of {len(vertex)}; "
      f"SYSTEM is the generator's: {system_same}")
chunks = {c["text"].strip(): c for c in mt.load_chunks("acme")}
rows = []
for v, d in zip(vertex, drafts):
    user = v["contents"][0]["parts"][0]["text"]
    text = user.split("[Source 1] ", 1)[1].rsplit("\\n\\nQuestion: ", 1)[0]
    c = chunks[text.strip()]
    rows.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "text": text, "draft": d,
                 "question": user.rsplit("\\n\\nQuestion: ", 1)[1]})
quotes = [(r["text"], r["draft"].citations[0].quote) for r in rows if r["draft"].citations]
flat = lambda s: re.sub(r"\\s+", " ", s).strip()
print(f"quotes: {len(quotes)}; in their chunk as written: {sum(q in t for t, q in quotes)}, once line breaks are spaces: "
      f"{sum(flat(q) in flat(t) for t, q in quotes)}; over twenty-five words: {sum(len(q.split()) > 25 for _, q in quotes)}")
said = [r["draft"].answer for r in rows if r["draft"].answerable]
marked = sum(bool(re.search(r"\\[(\\d+(?:\\s*,\\s*\\d+)*)\\]", a)) for a in said)   # the UI's own pattern: [1], [1,2]
print(f"answers that mark their source with [N], as SYSTEM's rule 2 asks: {marked} of {len(said)}")
print(f"rows from the handbook: {sum(r['chunk_id'].startswith('acme:hr_policy_2026') for r in rows)}, every one from a generated "
      f"GEN- section: its clauses are all under {mt.MIN_CHUNK_CHARS} characters")
golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
print(f"today's golden set ({len(golden)} rows) would drop {len(mt.exclude_golden(rows, golden)[1])} of v1's rows")
r = next(x for x in rows if x["text"][:1].isupper())             # a chunk that starts at a word
print("the prompt v1 trains on shows a chunk as: " + repr(("[Source 1] " + r["text"])[:64]) + "...")
print("the prompt the generator serves shows it as: " + repr((source_header(1, {"source_uri": r["source_uri"]}) + "\\n" + r["text"])[:64]) + "...")
PY

"""

def step_01_the_kit_s_rules_and_the_file_it_ships_audi(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the rules on fixtures, then the kit's own v1; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: selftest: the evidence rule dropped jn-06's chunk and kept EMEA elsewhere and lk-09's 8, the question rule dropped lk-06's twin, the PAN row dropped, two formats agree, ModelDraft parses, the batch round trip holds
    selftest: the helpdesk rows mark the source they cite, carry the served prompt with SYSTEM once, drop a quote not in its chunk, keep Hinglish twins and refusals, and a PAN in a distractor drops its row
    the manifest: v1, built 2026-09-10, 317 rows (30 refusals) from 12 documents; dropped 13 for the golden set, 0 for PII
    the two formats agree row by row: True; targets that parse as ModelDraft: 317 of 317; SYSTEM is the generator's: True
    quotes: 287; in their chunk as written: 22, on
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_9', step_01_the_kit_s_rules_and_the_file_it_ships_audi),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
