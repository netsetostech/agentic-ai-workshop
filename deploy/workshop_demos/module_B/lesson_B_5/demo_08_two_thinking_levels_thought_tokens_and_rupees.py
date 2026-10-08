"""Lesson B.5: Two thinking levels: thought tokens and rupees

Golden row jn-01 joins two clauses: probation's notice (PB-02) and leave on exit (LV-07), and its check is that the answer says 15 days and that leave cannot be encashed. The prompt is again generate()'s, with both clauses packed, about 252 tokens by the kit's estimate. The cell sends it at LOW, the kit's level, and at HIGH, and gives both the 6,144-token room that generate() gives its one retry, so that a long think at HIGH is not cut off. For each level it prints the thought tokens, the answer tokens, the prompt tokens, the finish reason, the cost at the kit's prices and the answer. Two calls: at most Rs 7.83 in output, even if both ran to the cap.

Run order inside this file:
1. Definition (source window 25)

Prerequisites: demo_07_gemini_five_times_count_the_distinct_answers.
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

    Golden row jn-01 joins two clauses: probation's notice (PB-02) and leave on exit (LV-07), and its check is that the answer says 15 days and that leave cannot be encashed. The prompt is again generate()'s, with both clauses packed, about 252 tokens by the kit's estimate. The cell sends it at LOW, the kit's level, and at HIGH, and gives both the 6,144-token room that generate() gives its one retry, so that a long think at HIGH is not cut off. For each level it prints the thought tokens, the answer tokens, the prompt tokens, the finish reason, the cost at the kit's prices and the answer. Two calls: at most Rs 7.83 in output, even if both ran to the cap.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop after lesson 0.1, in the Basics venv (two calls to gemini-3.6-flash, at most Rs 7.83 in output).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/thinking_levels.txt]
    """
    import json, os, sys, warnings
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
[Source 1] hr_policy_2026.md, p.1, PB-02 — Probation
PB-02 — Probation
New joiners serve six months on probation at grade E2. During probation the notice
period is 15 days for either side. Probation may be extended once, by up to three
months, with written reasons.

[Source 2] hr_policy_2026.md, p.1, LV-07 — Leave on exit
LV-07 — Leave on exit
Earned leave is encashed on exit at basic pay, capped at 45 days. Leave cannot be
encashed during probation and cannot be used to shorten notice.

Question: If I resign during probation, what notice applies and can I encash leave?"""
    client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")    # generator.py's _client
    rupees = {}
    for level in ("LOW", "HIGH"):                             # the kit's level, then the deepest
        r = client.models.generate_content(model="gemini-3.6-flash", contents=[PROMPT], config=types.GenerateContentConfig(
            response_mime_type="application/json", response_schema=ModelDraft,
            max_output_tokens=6144,                         # the room generate() gives its one retry
            thinking_config=types.ThinkingConfig(thinking_level=level)))
        u = r.usage_metadata
        prompt, answer, thoughts = u.prompt_token_count or 0, u.candidates_token_count or 0, u.thoughts_token_count or 0
        rupees[level] = (prompt * 1.50 + (answer + thoughts) * 7.50) / 1_000_000 * 85   # shared/prices.py
        finish = getattr(r.candidates[0].finish_reason, "name", "UNKNOWN") if r.candidates else "NO_CANDIDATES"
        print(f"{level:4}: thoughts {thoughts} | answer {answer} | prompt {prompt} | finish {finish} | Rs {rupees[level]:.4f}")
        try:
            print("      " + json.loads(r.text)["answer"])
        except (TypeError, ValueError, KeyError):             # cut off or blocked: no draft to read
            print("      (no parseable answer)")
    print(f"HIGH cost Rs {rupees['HIGH'] - rupees['LOW']:+.4f} against LOW, at the kit's prices")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_25', step_01_definition),
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
