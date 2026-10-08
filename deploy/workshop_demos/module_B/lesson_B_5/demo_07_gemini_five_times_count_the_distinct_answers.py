"""Lesson B.5: Gemini, five times: count the distinct answers

This is the lesson's proof, on the real model. The prompt is the one generate() builds when retrieval hands it a single clause: the rules from step 6, the handbook's clause NP-03 as [Source 1], and the question of golden row lk-06, whose check is that the answer states 60. The config is _call()'s, setting for setting. The cell asks five times, prints each answer, and counts two things: distinct answers (the exact text, with runs of spaces collapsed), and answers that state 60 by the boundary rule run_eval.py uses, where the figure must stand on its own, so "160" does not count (unlike run_eval.py, the cell does not read "sixty" as 60). The prompt is about 195 tokens by the kit's own estimate (four characters a token); the cell prints what the five calls cost, and they cannot cost more than Rs 6.53 in output even if every call ran to the cap. This cell and the one in step 8 call Gemini on your own Google Cloud project, so they need lesson 0.1's project and the setup's second block (the sign-in and PROJECT). If you have not made the project yet, read the author's recorded output below, go on to lesson 0.1, and come back: the cells will wait.

Run order inside this file:
1. Definition (source window 22)

Prerequisites: demo_05_the_loop_and_five_runs_of_one_prompt_counted.
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

    This is the lesson's proof, on the real model. The prompt is the one generate() builds when retrieval hands it a single clause: the rules from step 6, the handbook's clause NP-03 as [Source 1], and the question of golden row lk-06, whose check is that the answer states 60. The config is _call()'s, setting for setting. The cell asks five times, prints each answer, and counts two things: distinct answers (the exact text, with runs of spaces collapsed), and answers that state 60 by the boundary rule run_eval.py uses, where the figure must stand on its own, so "160" does not count (unlike run_eval.py, the cell does not read "sixty" as 60). The prompt is about 195 tokens by the kit's own estimate (four characters a token); the cell prints what the five calls cost, and they cannot cost more than Rs 6.53 in output even if every call ran to the cap. This cell and the one in step 8 call Gemini on your own Google Cloud project, so they need lesson 0.1's project and the setup's second block (the sign-in and PROJECT). If you have not made the project yet, read the author's recorded output below, go on to lesson 0.1, and come back: the cells will wait.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop after lesson 0.1, in the Basics venv (five calls to gemini-3.6-flash, at most Rs 6.53 in output).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/five_runs.txt]
    """
    import json, os, re, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")   # print any character a model writes, Windows included
    from typing import List, Literal
    from pydantic import BaseModel, Field
    from google import genai
    from google.genai import types
    
    class DraftCitation(BaseModel):
        """What the model cites: the [Source N] number it saw, and the words it is relying on.
        
        Example: See the instance constructed in this lesson step and inspect its state in the debugger.
        """
    
        source: int = Field(ge=1, description="1-based [Source N] in the context")
        quote: str = Field(max_length=200, description="Exact words from that source")
    
    
    class ModelDraft(BaseModel):
        """What the model is asked for. Use this as response_schema; resolve() turns it into a
        RAGAnswer. Asking the model for chunk ids or scores directly invites it to invent them.
        
        Example: See the instance constructed in this lesson step and inspect its state in the debugger.
        """
    
        answer: str
        citations: List[DraftCitation]
        confidence: Literal["high", "medium", "low"]
        answerable: bool
    
    PROMPT = """You are DocuMind, a retrieval-grounded assistant.
Rules:
1. Answer ONLY from the numbered context below. Never invent sources.
2. Cite using [N] where N is the chunk number. Multiple chunks: [1,2].
3. If the context does not contain the answer, set answerable=false and say so.
4. Keep answers under 300 words unless asked for more.
5. A quote is the clause that answers - at most twenty-five words, never a whole section.


Context:
[Source 1] hr_policy_2026.md, p.1, NP-03 — Notice period
NP-03 — Notice period
A confirmed employee at grade E3 or above serves a notice period of 60 days. Notice runs
from the date the resignation is acknowledged in writing. Unused earned leave may not be
set off against the notice period.

Question: What is the notice period for a confirmed E3?"""
    client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")    # generator.py's _client
    config = types.GenerateContentConfig(                     # _call()'s config: no temperature, top_p, top_k or seed
        response_mime_type="application/json", response_schema=ModelDraft, max_output_tokens=2048,
        thinking_config=types.ThinkingConfig(thinking_level="LOW"))
    answers, tokens_in, tokens_out = [], 0, 0
    for run in range(1, 6):
        r = client.models.generate_content(model="gemini-3.6-flash", contents=[PROMPT], config=config)
        u = r.usage_metadata
        tokens_in += u.prompt_token_count or 0
        tokens_out += (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)   # _usage(): thinking is output
        try:
            answers.append(json.loads(r.text)["answer"])
        except (TypeError, ValueError, KeyError):             # cut off or blocked: no draft to read
            answers.append("(no parseable answer)")
        print(f"run {run}: {answers[-1]}")
    distinct = len({" ".join(a.split()) for a in answers})
    states_60 = sum(bool(re.search(r"(?<![\w.])60(?![\w]|\.\d)", a.lower())) for a in answers)   # run_eval.py's rule: 60, not 160
    rupees = (tokens_in * 1.50 + tokens_out * 7.50) / 1_000_000 * 85           # shared/prices.py
    print(f"distinct answers: {distinct} of 5 | answers that state 60 (golden row lk-06): {states_60} of 5")
    print(f"five calls: {tokens_in} tokens in, {tokens_out} out (thinking included) | Rs {rupees:.4f} at the kit's prices")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_definition),
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
