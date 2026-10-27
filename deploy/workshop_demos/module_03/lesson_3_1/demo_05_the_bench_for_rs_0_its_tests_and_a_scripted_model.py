"""Lesson 3.1: The bench for Rs 0: its tests, and a scripted model

Before you spend a rupee, run the bench where nothing can be billed. First its tests, 21 of them in evals/tests/test_prompt_bench.py. They answer with the kit's own generate() over a scripted model and stand-ins for the lane, and they check what step 4 claimed: each row's pool is read once and held fixed, the level and the temperature are sent and nothing else changes, generator.py is never written, every answer is judged by the gate's rule, and the rupees are list price. The one test that runs the recorder on google-genai's own types needs that library, which Module 0 installed in your venv. Before you spend a rupee, run the bench where nothing can be billed. First its tests, 21 of them in evals/tests/test_prompt_bench.py. They answer with the kit's own generate() over a scripted model and stand-ins for the lane, and they check what step 4 claimed: each row's pool is read once and held fixed, the level and the temperature are sent and nothing else changes, generator.py is never written, every answer is judged by the gate's rule, and the rupees are list price. The one test that runs the recorder on google-genai's own types needs that library, which Module 0 installed in your venv. Then the bench itself. The cell below runs prompt_bench.main(), the function make bench runs, over generator.py imported in your shell, with two things stood in. /v1/passages returns the handbook's first six clauses, cut by the kit's own chunker as the kit's tests cut them, so NP-03 is [Source 1] and LV-07 is [Source 4]. The model is a script behind generator._client. It writes five wordings of an answer to jn-03 in turn, the same five at every level and temperature, and "thinks" 120 tokens at LOW and 900 at HIGH, the numbers the kit's tests script. Its fifth wording has all 50 days encashed, so that you can see a failure printed. It also counts the thinking level and the temperature each call was sent with. The cell runs the bench twice: the two levels with --show, then a temperature of 2.0.

Run order inside this file:
1. Definition (source window 22)
2. Definition (source window 24)

Prerequisites: demo_03_one_question_five_times_in_the_chat_page.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """python -m unittest discover -s evals/tests -p test_prompt_bench.py -v

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    Before you spend a rupee, run the bench where nothing can be billed. First its tests, 21 of them in evals/tests/test_prompt_bench.py. They answer with the kit's own generate() over a scripted model and stand-ins for the lane, and they check what step 4 claimed: each row's pool is read once and held fixed, the level and the temperature are sent and nothing else changes, generator.py is never written, every answer is judged by the gate's rule, and the rupees are list price. The one test that runs the recorder on google-genai's own types needs that library, which Module 0 installed in your venv.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (Rs 0: the kit's tests of the bench, no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: test_bench_redact_0_prints_them_as_they_are (test_prompt_bench.IdentifierTests.test_bench_redact_0_prints_them_as_they_are) ... ok
    test_the_lanes_project_id_and_number_are_printed_and_reported_as_the_pages_print_them (test_prompt_bench.IdentifierTests.test_the_lanes_project_id_and_number_are_printed_and_reported_as_the_pages_print_them) ... ok
    test_what_the_redactor_replaces (test_prompt_bench.IdentifierTests.test_what_the_redactor_replaces) ... ok
    test_the_level_and_the_temperature_are_sent_and_nothing_else_changes (test_prompt_bench.RecorderTests.test_the_level_and_the_temperature_are_sent_and_nothing_else_changes) ... ok
    test_the_recorder_on_google_genais_own_types (test_prompt_bench.Reco
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_definition(session):
    """Run Definition at this checkpoint.

    Before you spend a rupee, run the bench where nothing can be billed. First its tests, 21 of them in evals/tests/test_prompt_bench.py. They answer with the kit's own generate() over a scripted model and stand-ins for the lane, and they check what step 4 claimed: each row's pool is read once and held fixed, the level and the temperature are sent and nothing else changes, generator.py is never written, every answer is judged by the gate's rule, and the rupees are list price. The one test that runs the recorder on google-genai's own types needs that library, which Module 0 installed in your venv. Then the bench itself. The cell below runs prompt_bench.main(), the function make bench runs, over generator.py imported in your shell, with two things stood in. /v1/passages returns the handbook's first six clauses, cut by the kit's own chunker as the kit's tests cut them, so NP-03 is [Source 1] and LV-07 is [Source 4]. The model is a script behind generator._client. It writes five wordings of an answer to jn-03 in turn, the same five at every level and temperature, and "thinks" 120 tokens at LOW and 900 at HIGH, the numbers the kit's tests script. Its fifth wording has all 50 days encashed, so that you can see a failure printed. It also counts the thinking level and the temperature each call was sent with. The cell runs the bench twice: the two levels with --show, then a temperature of 2.0.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in $DEMO_ROOT (a Python cell; Rs 0: the kit's generate() over a scripted model, nothing leaves the machine).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: == prompt bench: gemini-3.6-flash, against http://stand-in.invalid ==
      1 row(s) x 1 arm(s) x 2 level(s) x 5 run(s): up to 10 answers, one generate() each
      pools: POST /v1/passages once a row (top_k 6), held fixed for every arm, level and run
        jn-03   join      acme    6 passages: hr_policy_2026.md x6
      arms (prompt sha256: SYSTEM followed by DATED_RULE, the text every prompt starts with)
        kit   generator.py's SYSTEM - 5 rules; no temperature
              prompt sha256 543ed8060f1b177cc26159b1af609d16dabeeafa88097945f5a74e884aca4e1e
        (the kit arm at LOW is the API's own request: generator.py's SYSTEM, thinking_level LOW, no temperature)

      answers
        jn-03   kit   LOW     run 1  pass
    """
    import hashlib, json, os, re, sys, warnings
    warnings.filterwarnings("ignore", category=UserWarning)
    os.environ["GOOGLE_CLOUD_PROJECT"] = "documind-ai-YOUR-ID"   # config.py wants a project id; nothing here calls Google
    sys.path[:0] = ["evals", "."]
    import prompt_bench as pb
    from shared import documind_corpus
    from types import SimpleNamespace as NS
    
    gen = pb.load_generator()                       # services/rag-api/generator.py, imported as make bench imports it
    RAW = open("evals/corpus/acme/hr_policy_2026.md", "rb").read()
    SHA, URI = hashlib.sha256(RAW).hexdigest(), "gs://documind-ai-YOUR-ID-uploads/acme/hr_policy_2026.md"
    CLAUSES = documind_corpus.chunk_document({"slug": "hr_policy_2026", "doc_type": "policy", "text": RAW.decode("utf-8"),
                                              "source_uri": URI}, "acme")
    POOL = [{"n": n, "chunk_id": f"acme:{SHA}#{i}", "source_uri": URI, "page": CLAUSES[i]["page_start"], "doc_type": "policy",
             "kind": "text", "section": CLAUSES[i]["section"], "text": CLAUSES[i]["text"]} for n, i in enumerate(range(1, 7), 1)]
    WORDINGS = [                                    # the script's answers, in turn; {LV} and {NP} become the [Source N] it saw
        "You can encash 45 of your 50 days, the cap on exit, and you serve a notice period of 60 days [{LV}, {NP}].",
        "Encashment is capped at 45 days, so 45 days are paid at basic pay [{LV}]. As a confirmed E3 you serve 60 days' notice [{NP}].",
        "Forty-five days are encashed and the notice period is sixty days [{LV}, {NP}].",
        "You can encash 45 of your 50 days, the cap on exit, and you serve a notice period of 60 days [{LV}, {NP}].",
        "All 50 days of earned leave are encashed at basic pay, and the notice period is 60 days [{LV}, {NP}].",
    ]
    QUOTES = {"LV": ("LV-07", "capped at 45 days"), "NP": ("NP-03", "serves a notice period of 60 days")}
    THOUGHT = {"LOW": 120, "HIGH": 900}             # the thought tokens evals/tests/test_prompt_bench.py scripts
    
    
    class Script:
        """Gemini, stood in behind generator._client: the five wordings in turn, its thought tokens set by the level.
        
        Example: Script()
        """
    
        def __init__(self):
            """Count the calls per level and temperature, and keep what each one was sent.
            
            Example: Construct the owning class with the arguments shown above; subsequent methods reuse these settings.
            """
            self.turn, self.sent = {}, []
    
        @property
        def models(self):
            """client.models, as google-genai's client has it.
            
            Example: self.models() in the owning lesson/helper context
            """
            return self
    
        def generate_content(self, *, model, contents, config=None):
            """One reply in the shape generator._draft(), _usage() and _finish_reason() read.
            
            Example: self.generate_content(model, contents, config) in the owning lesson/helper context
            """
            key = (config.thinking_config.thinking_level.value, config.temperature)
            self.sent.append(key)
            k = self.turn[key] = self.turn.get(key, -1) + 1
            n = {code: int(i) for i, code in re.findall(r"\[Source (\d+)\] [^\n]*?(LV-07|NP-03)", contents[0])}
            src = {tag: n[code] for tag, (code, _) in QUOTES.items()}
            draft = {"answer": WORDINGS[k % len(WORDINGS)].format(**src), "confidence": "high", "answerable": True,
                     "citations": [{"source": src[tag], "quote": quote} for tag, (_, quote) in QUOTES.items()]}
            text = json.dumps(draft)
            usage = NS(prompt_token_count=len(contents[0]) // 4, candidates_token_count=len(text) // 4,
                       thoughts_token_count=THOUGHT[key[0]], cached_content_token_count=None)
            return NS(parsed=None, text=text, candidates=[NS(finish_reason=NS(name="STOP"))], usage_metadata=usage,
                      prompt_feedback=None)
    
    
    def passages(api_url, question, tenant, email, token, top_k=6):
        """POST /v1/passages, stood in: the handbook's first six clauses, in the route's shape.
        
        Example: passages(api_url, question, tenant, email, token, top_k) in the owning lesson/helper context
        """
        return POOL
    
    
    def sources(api_url, tenant, token):
        """GET /v1/sources, stood in: the handbook's sha256 is acme's current version.
        
        Example: sources(api_url, tenant, token) in the owning lesson/helper context
        """
        return {SHA}
    
    
    for arm in (["--levels", "LOW,HIGH", "--show"], ["--temperature", "2.0"]):
        gen._client = script = Script()
        pb.main(["--rows", "jn-03", "--runs", "5", "--api-url", "http://stand-in.invalid"] + arm,
                generator=gen, passages=passages, sources=sources)
        print("  the script was sent: " + "; ".join(f"thinking_level {lv}, temperature {t}: {script.sent.count((lv, t))} calls"
                                                    for lv, t in sorted(set(script.sent), key=str)) + "\n")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_22', step_01_definition),
        ('source_24', step_02_definition),
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
