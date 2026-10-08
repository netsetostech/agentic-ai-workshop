# Lesson B.2 run list: the live outputs the page still needs

The page `Netsetos_GCP_Capstone_B.2_Tokens_Embeddings_WIX.html` computes every number when it is built, except the
outputs of its two cells that call Vertex AI. Those come from this lesson's `data/` folder through `pagebuild.recorded()`;
until a file exists the page shows a marked stand-in in its place, `finish()` names it, and `check_lesson.py` counts it
as a note. Two runs fill both.

**Where to run them.** On a laptop, in a bash shell (Git Bash on Windows), inside the Basics venv, exactly as a learner
would: first the page's setup section, its two blocks in order (the venv block, then the block for the cells that call
Gemini: `gcloud auth application-default login`, `export PROJECT=...`, `gcloud services enable
aiplatform.googleapis.com`), then each cell below, pasted whole. The cells read only `PROJECT` from the environment and
print nothing that names the project, the account or the machine.

**How to record.** Paste everything the cell printed, and nothing else (no prompt, no command line), into the data
file named below, UTF-8 with LF line endings. Then rebuild with the Basics interpreter and run the two checks:

```bash
python pagekit/build.py B.2
python pagekit/check_lesson.py B.2
python pagekit/audit_pages.py B.2
```

The build checks each file before it uses it. The count file must be three lines, each with the text's real length,
the kit's estimate, and a rupee line equal to `shared/prices.py`'s arithmetic on the count it printed. The embeddings
file must show the shapes `(3, 768)` and `(2, 768)`, and every cosine between -1 and 1.

## 1. data/count_tokens.txt (step 6: the model's own count, and the rupee line)

- Calls: three `count_tokens` requests to `gemini-3.6-flash` on the `global` location.
- Cost: Rs 0. Nothing is generated, and Google's CountTokens page says "There is no charge or quota restriction for
  using the CountTokens API"
  (https://docs.cloud.google.com/gemini-enterprise-agent-platform/models/capabilities/get-token-count, read
  7 October 2026).
- What it prints: three lines, `the question`, `the same in Hindi` and `an Indian amount`, each with the characters,
  the API's estimate (`len // 4`), the model's count, and the rupee line on that count at the kit's prices (USD 1.50
  per 1M input tokens, Rs 85 to the dollar).

```bash
python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
from google import genai
client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="global")   # Gemini 3 is served from global, as in the kit
MODEL = "gemini-3.6-flash"
PRICES = {MODEL: (1.50, 7.50)}     # shared/prices.py, as in step 5
USD_INR = 85
def price(tokens_in, tokens_out=0):
    """Dollars, then rupees, as in step 5."""
    usd_in, usd_out = PRICES[MODEL]
    usd = (tokens_in * usd_in + tokens_out * usd_out) / 1_000_000
    return usd, usd * USD_INR
TEXTS = {
    "the question": "What is the notice period for a confirmed E3?",
    "the same in Hindi": "पुष्टि किए गए E3 कर्मचारी की सूचना अवधि क्या है?",
    "an Indian amount": "Purchases up to Rs 2,00,000 are approved by the function head.",
}
for name, text in TEXTS.items():
    n = client.models.count_tokens(model=MODEL, contents=text).total_tokens   # the model's own count: no charge
    usd, inr = price(n)
    print(f"{name:17} {len(text):2} characters  estimate {max(1, len(text) // 4):2}  counted {n:2}  "
          f"as input ${usd:.6f} = Rs {inr:.4f} at {USD_INR}")
PY
```

## 2. data/embeddings.txt (step 8: real embeddings and their cosine similarities)

- Calls: two `embed_content` requests to `text-embedding-005` on `us-central1`: the three clauses under
  `RETRIEVAL_DOCUMENT`, the two questions under `RETRIEVAL_QUERY`, 768 numbers each.
- Cost: at most Rs 0.0011 (0.11 paise). The two requests carry 536 characters; Google's list price for text
  embeddings is USD 0.000025 per 1,000 characters online
  (https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing, read 7 October 2026), and the
  kit's rate is Rs 85 to the dollar (`shared/prices.py`). The kit's own price table has no embedding price, so the list
  price is the source. The cell prices every character sent, spaces included; the bill uses the billable characters
  the API reports with each response, which the cell also prints.
- What it prints: the shapes and lengths of the vectors, the first four numbers of IT-SEC-04's vector, the tokens per
  text as the model read them, two rows of cosines (`lk-05` and `reworded`, each against IT-SEC-04, EXP-12 and PR-05),
  and the characters with their cost.

```bash
python - <<'PY'
import os, warnings
warnings.filterwarnings("ignore", category=UserWarning)
import numpy as np
from google import genai
client = genai.Client(enterprise=True, project=os.environ["PROJECT"], location="us-central1")   # embeddings are regional, as in the kit
MODEL, DIMS = "text-embedding-005", 768
CLAUSES = {
    "IT-SEC-04": ("USB mass-storage devices are blocked on all company laptops. No exception is "
                  "granted for contractors. Data transfer uses the approved cloud bucket only."),
    "EXP-12": ("Domestic travel is reimbursed against original receipts, capped at Rs 40,000 per trip. "
               "Anything above the cap needs written approval from the function head before travel, "
               "not after."),
    "PR-05": ("Salary is credited on the last working day of each month. Form 16 is issued by 15 June "
              "for the preceding financial year."),
}
QUESTIONS = {"lk-05": "Are USB drives allowed on a company laptop?",
             "reworded": "Can I copy files to a pen drive at work?"}
def embed(texts, task_type):
    """One request: DIMS numbers per text, under the task type given. Returns the response and the vectors."""
    r = client.models.embed_content(model=MODEL, contents=list(texts),
                                    config={"output_dimensionality": DIMS, "task_type": task_type})
    return r, np.array([e.values for e in r.embeddings])
def cosine(a, b):
    """Step 7's cosine: the dot product over the product of the lengths."""
    return float(a @ b / (np.linalg.norm(a) * np.linalg.norm(b)))
rd, D = embed(CLAUSES.values(), "RETRIEVAL_DOCUMENT")    # the worker's task type for passages (indexer.py)
rq, Q = embed(QUESTIONS.values(), "RETRIEVAL_QUERY")     # the API's task type for questions (retriever.py)
print("clauses", D.shape, " questions", Q.shape, " lengths", np.linalg.norm(D, axis=1).round(4), np.linalg.norm(Q, axis=1).round(4))
print("IT-SEC-04 begins", D[0, :4].round(4))
print("tokens per text, as the model read them:", [getattr(e.statistics, "token_count", None) for e in [*rd.embeddings, *rq.embeddings]])
for q, qv in zip(QUESTIONS, Q):
    print(f"{q:9}", "  ".join(f"{name} {cosine(qv, dv):.4f}" for name, dv in zip(CLAUSES, D)))
sent = sum(len(t) for t in [*CLAUSES.values(), *QUESTIONS.values()])
billed = [getattr(r.metadata, "billable_character_count", None) for r in (rd, rq)]
print(f"characters sent {sent}, billable as reported {billed}: at most Rs {sent / 1000 * 0.000025 * 85:.4f}")
PY
```

Both runs together: at most Rs 0.0011.
