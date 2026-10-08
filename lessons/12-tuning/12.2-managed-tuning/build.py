"""Build lesson 12.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Validate sanitized datasets and run managed tuning. Before the billed act, the frozen file is held to what 17.1 says
it is: the bytes the manifest records, the shape the trainer reads, no golden row, no personal data where
make_trainset.py looks and where it does not (the chunk in the user turn), and a tenant whose data_region lets its text
leave India (tuning runs in us-central1; Google tunes Gemini 3.1 Flash-Lite only in us-central1 and europe-west4).
Then make tune: evals/tune.py checks the base and the rank before submitting (F37), submits a regional job, and polls
it to a tuned model and an endpoint, which Google serves from the us or eu multi-region only, so the endpoint's path
names its location and the generator reads it there (F41, _endpoint_location).
Offline: the two self-tests, config_for's refusals, the lifted _endpoint_location. Live: the validation; make tune
--no-wait (the job id); the poll (the endpoint path with its location); one call where the path says, two where not.

Build-time proof: every cell ran the kit's own code - make_trainset.py main() to leave the bucket as lesson 12.1 leaves
it, tune.py main() for the submit and the poll, the validation and the call - over a stand-in lane (lane172.py, beside
this file): Gemini's tuning service and the tuned endpoint with Google's documented rules, DLP, Cloud Storage and
Firestore. The panel is tune.config_for and generator._client_for with _endpoint_location, ported and compared with
the kit's functions on every combination it offers.
"""
import ast
import hashlib
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "12.2"
title = "<title>Lesson 12.2 Validate sanitized datasets and run managed tuning - a checked file, a job, an endpoint | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
MT, TUNE, GEN, COST, TEN, PII, BUDGET = ("evals/make_trainset.py", "evals/tune.py", "services/rag-api/generator.py", "services/rag-api/cost.py",
                                         "shared/tenancy.py", "shared/pii.py", "services/rag-api/context_budget.py")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.tj-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:0 10px;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,140px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.tj-out{margin:6px 0 0;font-size:12.5px;line-height:1.6;}
.tj-out code{font-size:11.5px;}
.tj-out .pass{color:var(--teal-dark);font-weight:600;}
.tj-out .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()


# ------------------------------------------------------------------ verbatim excerpts
def span(rel: str, start: str, last: str) -> int:
    """How many lines from the line starting `start` to the first line equal to `last`, inclusive."""
    lines = (KIT / rel).read_text(encoding="utf-8").split("\n")
    i = next(k for k, line in enumerate(lines) if line.startswith(start))
    return next(k for k in range(i, len(lines)) if lines[k] == last) - i + 1


EXCERPTS = {
    "recipe": ("Makefile - make tune: the frozen file by its URI, the base, the epochs, the adapter",
               block("Makefile", "tune: guard-project", n=3)),
    "config": ("evals/tune.py - config_for(): checked before anything is submitted",
               block(TUNE, "def config_for(", n=span(TUNE, "def config_for(", "    return cfg"))),
    "adapter": ("evals/tune.py - the rank, spelled the SDK's way (F37)",
                block(TUNE, "# The LoRA rank is an ENUM in the SDK", n=5)),
    "launch": ("evals/tune.py - launch(): a regional client, the file named by its URI",
               block(TUNE, "def launch(", n=span(TUNE, "def launch(", "                               config=types.CreateTuningJobConfig(**cfg))"))),
    "done": ("evals/tune.py - main(): what a finished job prints",
             block(TUNE, '    if state == "JOB_STATE_SUCCEEDED" and job.tuned_model:', n=8)),
    "location": ("services/rag-api/generator.py - where a tuned endpoint is served from (F41)",
                 block(GEN, "def _endpoint_location(model: str) -> str:", n=span(GEN, "def _endpoint_location(", "    return m.group(1) if m else settings.region"))),
    "permits": ("shared/tenancy.py - permits(): may a store in this region hold a tenant's text?",
                block(TEN, "def permits(", n=span(TEN, "def permits(", "    return str(region or \"\").strip().lower().startswith(INDIA_REGION_PREFIXES)"))),
    "priced": ("services/rag-api/cost.py - how the kit prices a tuned endpoint",
               block(COST, "    # A tuned model (10.1) is an endpoint path", n=3)),
}
assert EXCERPTS["recipe"][1].rstrip().endswith("--adapter $(TUNE_ADAPTER) $(TUNE_ARGS)") and "${VERSION:-v1}" in EXCERPTS["recipe"][1]
assert EXCERPTS["config"][1].rstrip().endswith("return cfg") and "if base not in TUNABLE:" in EXCERPTS["config"][1]
assert EXCERPTS["adapter"][1].rstrip().endswith('16: "ADAPTER_SIZE_SIXTEEN", 32: "ADAPTER_SIZE_THIRTY_TWO"}')
assert EXCERPTS["launch"][1].rstrip().endswith("config=types.CreateTuningJobConfig(**cfg))") and "location=REGION" in EXCERPTS["launch"][1]
assert EXCERPTS["done"][1].rstrip().endswith("return 0") and "RAG_MODEL_BASE={a.base}" in EXCERPTS["done"][1]
assert EXCERPTS["location"][1].rstrip().endswith("return m.group(1) if m else settings.region") and "F41" in EXCERPTS["location"][1]
assert EXCERPTS["permits"][1].rstrip().endswith("startswith(INDIA_REGION_PREFIXES)") and EXCERPTS["priced"][1].rstrip().endswith('or "gemini-3.6-flash"')
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (MT, TUNE, GEN, COST, TEN, PII, BUDGET, "Makefile", "terraform/storage.tf",
                                                          "services/rag-api/config.py", "services/rag-api/main.py")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert "TUNE_BASE       ?= gemini-3.1-flash-lite" in MK and "TUNE_EPOCHS     ?= 3" in MK and "TUNE_ADAPTER    ?= 4" in MK and "PY      ?= python" in MK
assert 'TUNABLE = {"gemini-3.5-flash", "gemini-3.1-flash-lite"}' in src[TUNE] and 'REGION = "us-central1"' in src[TUNE]
assert "it bills per training token and nothing else on the lane triggers it" in src[TUNE] and "failing here costs nothing and says why" in src[TUNE]
assert "Tuning is REGIONAL (us-central1) and so is the endpoint it produces" in src[TUNE]                       # the docstring F41 overtook
assert "put its\n    endpoint in the `us` multi-region while the service assumed us-central1 (F41)" in src[GEN]
assert 'generator_location: str = Field("", alias="GENERATOR_LOCATION")' in src["services/rag-api/config.py"]
assert "return _client_at(_endpoint_location(model)) if model.startswith(\"projects/\") else _client" in src[GEN]
assert "def poll(project: str, name: str, every_s: int = 60):" in src[TUNE] and 'print(f"  {time.strftime(\'%H:%M:%S\')} {job.state}")' in src[TUNE]
assert 'print(f"  poll later: python evals/tune.py --project {a.project} --poll {job.name}")' in src[TUNE]
assert "response_schema=ModelDraft," in src[GEN] and 'thinking_config=types.ThinkingConfig(thinking_level="LOW"),' in src[GEN]
assert "max_answer_tokens: int = 2048" in src["services/rag-api/config.py"]
assert "A request takes half a megabyte" in src[PII] or "content.inspect takes at most 0.5 MiB per request" in src[PII]
assert 'LOCATION = os.environ.get("DLP_LOCATION", "asia-south1")' in src[PII] and 'MIN_LIKELIHOOD = "LIKELY"' in src[PII]
assert "so a scan\nof the whole corpus is cents" in src[PII] and "def estimate_tokens(text: str) -> int:\n    return max(1, len(text) // 4)" in src[BUDGET]
assert 'location                    = var.india_region' in src["terraform/storage.tf"].split('resource "google_storage_bucket" "datasets"', 1)[1][:200]
# 1. nothing checks the file before the job: tune.py passes a URI and never reads the manifest, the bytes or the rows
assert "training_dataset=types.TuningDataset(gcs_uri=dataset)" in src[TUNE] and "manifest" not in src[TUNE] and "sha256" not in src[TUNE]
assert "download" not in src[TUNE] and "open(" not in src[TUNE]                                                  # and it writes nothing down
# 2. nothing checks residency: tune.py's region is fixed, make trainset takes any TENANT, neither reads tenant_settings
assert "tenancy" not in src[TUNE] + src[MT] and "data_region" not in src[TUNE] + src[MT] and "TENANT        ?= acme" in MK
assert "globex (data_region in) from the kit's own rows" in MK and '"globex": {"data_region": "in"}' not in src[TUNE]
# 3. no validation split: tune.py takes one, make trainset's plain style writes none, make tune passes none; v3 (12.1's step 7) writes one
WRITE_FN = src[MT].split("def write(", 1)[1].split("\ndef upload(", 1)[0]
assert 'ap.add_argument("--validation", default="")' in src[TUNE] and "validation" not in WRITE_FN.lower() and "--validation" not in EXCERPTS["recipe"][1]
assert '"validation": base + ".validation.vertex.jsonl"' in src[MT] and "VALIDATION_EVERY = 10" in src[MT]
assert 'cfg["validation_dataset"] = types.TuningValidationDataset(gcs_uri=validation)' in src[TUNE]
# 4. the display name says v1 whatever version is tuned
assert 'ap.add_argument("--display-name", default="documind-sft-v1")' in src[TUNE] and "--display-name" not in EXCERPTS["recipe"][1]
# 5. the kit accepts a rank Google does not list for either tunable base (Google: 1, 2, 4, 8 and 16, checked 24 September 2026)
assert '32: "ADAPTER_SIZE_THIRTY_TWO"' in src[TUNE]
# 6. a tuned endpoint priced at its base's rate (Google's pricing page: 1.5 times, from Gemini 3)
assert "A tuned model (10.1) is an endpoint path, billed at its BASE model's rate: RAG_MODEL_BASE names it." in src[COST]
assert 'cost = cost_usd if cost_usd is not None else price(model, ans_tokens_in, ans_tokens_out, cached)["usd"]' in src["services/rag-api/main.py"]
assert "SUM(CAST(jsonPayload.cost_usd AS FLOAT64))" in (KIT / "terraform/sql/tenant_daily.sql").read_text(encoding="utf-8")
assert 'a["usd"] += float(r.get("cost_usd") or 0.0)' in (KIT / "evals/usage_rows.py").read_text(encoding="utf-8") and "evals/usage_rows.py" in MK
# step 7's reasons, in the kit's own words; 12.3's candidate takes no traffic
assert "Weights cannot be filtered per tenant afterwards." in src[MT] and "--no-traffic --tag candidate" in MK
assert "GENERATOR_MODEL=$(GENERATOR_MODEL)|RAG_MODEL_BASE=$(RAG_MODEL_BASE)" in MK
# 7. --poll prints RAG_MODEL_BASE from its own default, not from the job
assert 'ap.add_argument("--base", default="gemini-3.1-flash-lite")' in src[TUNE] and "base_model" not in src[TUNE].split("def main(", 1)[1]
FALLBACK = next(ast.literal_eval(n.value) for n in ast.parse(src[COST]).body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")
assert FALLBACK["gemini-3.1-flash-lite"] == (0.25, 1.50)
# Google's figures the page states, checked on its pages on 24 September 2026 (the tuning pricing table; "About supervised
# fine-tuning for Gemini models", last updated 2026-09-22): USD a million training tokens, the ranks, the regions
USD_M = {"gemini-3.1-flash-lite": 3.00, "gemini-3.5-flash": 10.00}
GOOGLE_ADAPTERS = [1, 2, 4, 8, 16]

# ------------------------------------------------------------------ the lane: the bucket as lesson 12.1 leaves it
sys.path[:0] = [str(KIT), str(KIT / "evals"), str(KIT / "services/rag-api")]
import make_trainset as mt  # noqa: E402
import tune  # noqa: E402
from context_budget import estimate_tokens  # noqa: E402
GOLDEN = [json.loads(line) for line in (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
CHUNKS = mt.load_chunks("acme")
T = Path(tempfile.mkdtemp(prefix="lesson172-"))
K2 = T / "kit"
for part in ("evals", "shared", "services/rag-api"):
    shutil.copytree(KIT / part, K2 / part, ignore=shutil.ignore_patterns("__pycache__", "reports"))
shutil.copy(HERE / "lane172.py", T / "lane172.py")
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "HOME": str(T),
       "USERPROFILE": str(T), "REGION": "asia-south1", "LANE172_GCS": str(T / "gcs.json"), "LANE172_JOBS": str(T / "jobs.json"),
       "PYTHONPATH": str(T)}
for k in [k for k in ENV if k.startswith(("TRAINSET_", "DOCUMIND_", "GENERATOR_", "GOOGLE_CLOUD_PROJECT"))]:
    ENV.pop(k)
# lesson 12.1's stand-in names a passage the way a reader would, so v2 here is v2 there, byte for byte
DOC_TITLES = {"cgst_act_2017": "the CGST Act, 2017", "hr_policy_2026": "ACME's HR handbook", "code_on_social_security_2020": "the Code on Social Security, 2020",
              "osh_code_2020": "the OSH Code, 2020", "industrial_relations_code_2020": "the Industrial Relations Code, 2020", "it_act_2000": "the IT Act, 2000",
              "code_on_wages_2019": "the Code on Wages, 2019", "payment_of_bonus_act_1965": "the Payment of Bonus Act, 1965", "dpdp_act_2023": "the DPDP Act, 2023",
              "labour_codes_compliance_handbook": "the labour codes compliance handbook", "payment_of_gratuity_act_1972": "the Payment of Gratuity Act, 1972",
              "maternity_benefit_act_1961": "the Maternity Benefit Act, 1961", "maternity_benefit_amendment_act_2017": "the Maternity Benefit (Amendment) Act, 2017",
              "inv_2026_0412": "invoice INV-2026-0412", "townhall_2026_q1": "the FY2026 town hall transcript"}
SECTION = re.compile(r"(?:^|\s)(\d{1,3}[A-Z]?)\.\s+([A-Z][a-z][A-Za-z ,'()]{2,60}?)\.?\s*[—–]")
TERMS = ["input tax credit", "composition levy", "registration", "tax invoice", "returns", "refund", "gratuity", "bonus", "minimum wages",
         "overtime", "trade union", "strike", "lay-off", "retrenchment", "standing orders", "grievance redressal", "maternity benefit", "creche",
         "provident fund", "employees' state insurance", "social security fund", "gig workers", "platform workers", "safety committee",
         "working hours", "annual leave", "contract labour", "migrant workers", "inspector-cum-facilitator", "appropriate government",
         "penalty", "offences", "appeal", "personal data", "data fiduciary", "consent", "electronic record", "digital signature",
         "certifying authority", "wages", "employer", "establishment"]


def heading_of(c: dict) -> str:
    first = c["text"].strip().splitlines()[0]
    m = re.match(r"GEN-\d+\s*[—–-]\s*(.+)$", first)
    if m:
        return m.group(1).strip().lower()
    m = SECTION.search(c["text"])
    if m:
        return f"{m.group(2).strip().lower()} (section {m.group(1)})"
    low = c["text"].lower()
    hits = sorted((low.find(t), t) for t in TERMS if low.find(t) >= 0)
    if not hits:
        return "its scope"
    return ("the " + hits[0][1]) if hits[0][1] in ("employer", "establishment", "appropriate government", "inspector-cum-facilitator",
                                                   "certifying authority", "data fiduciary", "safety committee", "social security fund") else hits[0][1]


(T / "titles.json").write_text(json.dumps({hashlib.sha256(c["text"][:2400].encode("utf-8")).hexdigest():
                                            {"title": DOC_TITLES[c["chunk_id"].split(":", 1)[1].split("#", 1)[0]], "heading": heading_of(c)}
                                            for c in CHUNKS}), encoding="utf-8")
ENV["LANE172_TITLES"] = str(T / "titles.json")


def run(cmd: list, stdin: str | None = None, env: dict | None = None) -> str:
    r = subprocess.run(cmd, input=stdin, cwd=str(K2), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (cmd[:3], r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


LANE = "import lane172\nlane172.freeze()\nlane172.install()\n"


def main_of(script: str, argv: list, now: str, env: dict | None = None) -> str:
    """A kit script's own main(), under the stand-ins, as its command line runs it."""
    code = (LANE + "import runpy, sys\nsys.path[:0] = ['.']\nsys.argv = " + repr(argv) + "\n"
            "try:\n    runpy.run_path(" + repr(script) + ", run_name='__main__')\nexcept SystemExit as e:\n    assert not e.code, e.code\n")
    return run([sys.executable, "-"], code, {"LANE172_NOW": now, **(env or {})})


made = main_of("evals/make_trainset.py", ["make_trainset.py", "--project", PROJ, "--tenant", "acme", "--rows", "300",
                                          "--upload", f"gs://{PROJ}-datasets/sft/", "--version", "v2"], "2026-09-24T09:10:00+00:00")
M2 = json.loads((K2 / "evals/sft/documind_sft_v2.manifest.json").read_text(encoding="utf-8"))
assert (M2["rows"], M2["refusals"], M2["dropped_golden_overlap"]) == (315, 30, 15) and "sha ac73343d2550" in made, (M2, made[-400:])   # 17.1's v2
V2 = [json.loads(line) for line in (K2 / "evals/sft/documind_sft_v2.vertex.jsonl").read_text(encoding="utf-8").splitlines()]
TOKS = [estimate_tokens(v["systemInstruction"]["parts"][0]["text"]) + sum(estimate_tokens(c["parts"][0]["text"]) for c in v["contents"]) for v in V2]
TOK_EPOCH, TOK_MAX = sum(TOKS), max(TOKS)
TRAIN_TOKENS = TOK_EPOCH * 3
TRAIN_RS = TRAIN_TOKENS * USD_M["gemini-3.1-flash-lite"] / 1e6 * 85
SYS_TOK = estimate_tokens(mt.SYSTEM) * len(V2) * 3                                 # the second SYSTEM in every row (12.1), three epochs
SCANNED = sum(len(x.encode("utf-8")) for v in V2 for x in (v["contents"][0]["parts"][0]["text"], v["contents"][1]["parts"][0]["text"]))
assert SCANNED < 1_000_000, SCANNED                                                # what the validation's DLP scans: under a megabyte
# and lesson 12.1's step 7: v3, --style helpdesk, as that lesson leaves it (the same stand-in teacher, byte for byte)
V3_SHA = "fc16d910b684"                                                            # lesson 12.1's build asserts the same
made3 = main_of("evals/make_trainset.py", ["make_trainset.py", "--project", PROJ, "--tenant", "acme", "--rows", "300",
                                           "--upload", f"gs://{PROJ}-datasets/sft/", "--version", "v3", "--style", "helpdesk"], "2026-09-27T09:10:00+00:00")
M3 = json.loads((K2 / "evals/sft/documind_sft_v3.manifest.json").read_text(encoding="utf-8"))
assert f"(sha {V3_SHA})" in made3 and M3["style"] == "helpdesk", made3[-500:]
V3T = [json.loads(line) for line in (K2 / "evals/sft/documind_sft_v3.vertex.jsonl").read_text(encoding="utf-8").splitlines()]
V3H = [json.loads(line) for line in (K2 / "evals/sft/documind_sft_v3.validation.vertex.jsonl").read_text(encoding="utf-8").splitlines()]
TOKS3 = [sum(estimate_tokens(c["parts"][0]["text"]) for c in v["contents"]) for v in V3T]
TOK3_EPOCH, TOK3_HELD = sum(TOKS3), sum(sum(estimate_tokens(c["parts"][0]["text"]) for c in v["contents"]) for v in V3H)
TRAIN3_TOKENS = TOK3_EPOCH * 3
TRAIN3_RS = TRAIN3_TOKENS * USD_M["gemini-3.1-flash-lite"] / 1e6 * 85
assert 2.0 < TOK3_EPOCH / TOK_EPOCH < 3.5 and 300 < TRAIN3_RS < 600, (TOK3_EPOCH, TRAIN3_RS)

# ------------------------------------------------------------------ step 3: the checks that run before the spend (offline)
CHECKS_PY = """import ast, re, sys, types
sys.path[:0] = ["evals"]
import tune                                          # stdlib only when imported: no SDK, no project, no network
for base, adapter in (("gemini-3.6-flash", 4), ("gemini-3.1-flash-lite", 3), ("gemini-3.1-flash-lite", 32)):
    try:
        print(f"{base}, adapter {adapter}: accepted, {tune.config_for(base, 3, adapter, 'documind-sft-v2')['adapter_size']}")
    except SystemExit as e:
        print(f"{base}, adapter {adapter}: refused before submission: {str(e).split(': ', 1)[1].split('. ', 1)[0]}")
print(f"make tune's defaults: {tune.config_for('gemini-3.1-flash-lite', 3, 4, 'documind-sft-v1')}")
fn = next(n for n in ast.parse(open("services/rag-api/generator.py", encoding="utf-8").read()).body
          if isinstance(n, ast.FunctionDef) and n.name == "_endpoint_location")


def location(model, override="", region="asia-south1"):     # generator.py builds its clients when imported: the rule is lifted out
    ns = {"re": re, "settings": types.SimpleNamespace(generator_location=override, region=region)}
    exec(compile(ast.Module([fn], []), "generator.py", "exec"), ns)
    return ns["_endpoint_location"](model)


EP = "projects/NUMBER/locations/us/endpoints/ENDPOINT_ID"
print(f"an endpoint whose path says us is called at: {location(EP)}; with GENERATOR_LOCATION=us-central1: {location(EP, 'us-central1')}")"""
CELLS = {"checks": "python evals/make_trainset.py --selftest\npython evals/tune.py --selftest\npython - <<'PY'\n" + CHECKS_PY + "\nPY"}
OUT = {"checks": run([sys.executable, "evals/make_trainset.py", "--selftest"]) + run([sys.executable, "evals/tune.py", "--selftest"])
       + run([sys.executable, "-"], CHECKS_PY)}
CK = OUT["checks"]
assert "adapter 4 is ADAPTER_SIZE_FOUR and the SDK accepts it" in CK and "gemini-3.6-flash, adapter 4: refused before submission: managed SFT accepts" in CK, CK
assert "gemini-3.1-flash-lite, adapter 3: refused before submission: the LoRA rank must be one of [1, 2, 4, 8, 16, 32]" in CK, CK
assert "gemini-3.1-flash-lite, adapter 32: accepted, ADAPTER_SIZE_THIRTY_TWO" in CK and "'tuned_model_display_name': 'documind-sft-v1'}" in CK, CK
assert "an endpoint whose path says us is called at: us; with GENERATOR_LOCATION=us-central1: us-central1" in CK, CK

# ------------------------------------------------------------------ step 4: the frozen file, validated (live)
VALIDATE_PY = """import hashlib, json, os, sys
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
    text = user.split("[Source 1] ", 1)[1].rsplit("\\n\\nQuestion: ", 1)[0]
    c = chunks[text.strip()]
    rows.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "text": text,
                 "question": user.rsplit("\\n\\nQuestion: ", 1)[1], "answer": d.answer})
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
    print(f"         {n_rows(len(hits))} {verb} a finding make trainset never looked for: read the chunks before you pay")"""
CELLS["validate"] = "python - <<'PY'\n" + VALIDATE_PY + "\nPY"
OUT["validate"] = run([sys.executable, "-"], LANE + VALIDATE_PY, {"LANE172_NOW": "2026-09-24T09:45:00+00:00"})
VA = OUT["validate"]
assert VA.count("sha256 as the manifest says") == 2 and "1. the shape: 315 of 315 rows are" in VA and "the chat file says the same in 315" in VA, VA
assert "targets that parse as ModelDraft: 315" in VA and "2. the test set: the golden set (65 rows) would drop 0 of 315" in VA, VA
assert "which make trainset scans: 0 rows" in VA and "which it does not: 1 row\n     acme:cgst_act_2017#p1-0: EMAIL_ADDRESS" in VA, VA
assert "1 row carries a finding make trainset never looked for" in VA, VA
assert "whose data_region is any; may they be held in us-central1? True" in VA and "verdict: ready to tune" in VA, VA
assert f"about {TOK_EPOCH:,} tokens an epoch" in VA and f"the longest row about {TOK_MAX:,} of the 131,072" in VA and f"about {TRAIN_TOKENS:,} training tokens" in VA, VA
assert "gst-cbec@gov.in" in re.sub(r"\s+", " ", next(c for c in CHUNKS if c["chunk_id"] == "acme:cgst_act_2017#p1-0")["text"])  # what the finding is
assert '{"name": "EMAIL_ADDRESS"},' in src[PII] and '{"name": "PERSON_NAME"},' in src[PII]
G_CH = mt.load_chunks("globex")
assert len(G_CH) == 118 and {c["chunk_id"].split("#")[0] for c in G_CH} == {"globex:dpdp_act_2023", "globex:it_act_2000"}

# ------------------------------------------------------------------ step 5: make tune, submitted (the job id)
RECIPE = MK[MK.index("\ntune: guard-project\n") + 1:].split("\n\n", 1)[0].split("\n", 1)[1]
TUNE_ARGS = "--display-name documind-sft-v2 --no-wait"
ECHO = (RECIPE.replace("\t", "").replace("$(PY)", "python").replace("$(PROJECT)", PROJ).replace("$(TUNE_BASE)", "gemini-3.1-flash-lite")
        .replace("$(TUNE_EPOCHS)", "3").replace("$(TUNE_ADAPTER)", "4").replace("$(TUNE_ARGS)", TUNE_ARGS).replace("$$", "$") + "\n")
assert ECHO == (f"python evals/tune.py --project {PROJ} --dataset gs://{PROJ}-datasets/sft/documind_sft_${{VERSION:-v1}}.vertex.jsonl \\\n"
                f"  --base gemini-3.1-flash-lite --epochs 3 --adapter 4 {TUNE_ARGS}\n"), ECHO
ARGV = ECHO.replace("${VERSION:-v1}", "v2").replace("\\\n", " ").split()                     # what the shell runs, VERSION=v2
CELLS["tune"] = (f'make tune PROJECT="$PROJECT" VERSION=v2 TUNE_ARGS="{TUNE_ARGS}" | tee ~/tune172.log\n'
                 "export JOB=\"$(grep -o 'projects/[^ ]*/tuningJobs/[0-9]*' ~/tune172.log | head -1)\"; echo \"JOB=$JOB\"")
submitted = main_of("evals/tune.py", ARGV[1:], "2026-09-24T09:52:00+00:00")
JOB = re.search(r"projects/[^ ]*/tuningJobs/[0-9]*", ECHO + submitted).group(0)
OUT["tune"] = ECHO + submitted + f"JOB={JOB}\n"
assert JOB.startswith("projects/NUMBER/locations/us-central1/tuningJobs/") and f"  submitted {JOB} on gemini-3.1-flash-lite: 3 epochs, adapter 4, dataset gs://{PROJ}-datasets/sft/documind_sft_v2.vertex.jsonl" in submitted, submitted
assert f"  poll later: python evals/tune.py --project {PROJ} --poll {JOB}" in submitted

# ------------------------------------------------------------------ step 6: the poll (the endpoint path with its location), then the call
CELLS["poll"] = ("JOB=\"${JOB:-$(grep -o 'projects/[^ ]*/tuningJobs/[0-9]*' ~/tune172.log | head -1)}\"     # after a reconnect: the job, from step 5's log\n"
                 'python evals/tune.py --project "$PROJECT" --poll "$JOB" | tee ~/poll172.log   # a line a minute until the job ends; safe to re-run\n'
                 "export ENDPOINT=\"$(grep -o 'projects/[^ ]*/endpoints/[0-9]*' ~/poll172.log | head -1)\"; echo \"ENDPOINT=$ENDPOINT\"")
polled = main_of("evals/tune.py", ["tune.py", "--project", PROJ, "--poll", JOB], "2026-09-24T09:53:00+00:00")
ENDPOINT = re.search(r"projects/[^ ]*/endpoints/[0-9]*", polled).group(0)
STATES = [line for line in polled.splitlines() if re.match(r"  \d\d:\d\d:\d\d JobState\.", line)]
assert STATES[0].endswith("JobState.JOB_STATE_PENDING") and STATES[-1].endswith("JobState.JOB_STATE_RUNNING") and len(STATES) > 20, STATES[:3]
KEEP = 3
lines = polled.splitlines()
first_state = lines.index(STATES[0])
POLL_OUT = "\n".join(lines[:first_state + KEEP] + [f"  ...      (a line a minute while the job runs: {len(STATES) - KEEP - 1} more here)", STATES[-1]]
                     + lines[first_state + len(STATES):]) + "\n"
OUT["poll"] = POLL_OUT + f"ENDPOINT={ENDPOINT}\n"
POLL_MIN = len(STATES) + 1
assert ENDPOINT.startswith("projects/NUMBER/locations/us/endpoints/") and "  JOB_STATE_SUCCEEDED\n  tuned model : projects/NUMBER/locations/us/models/" in polled, polled[-900:]
assert f"make candidate PROJECT={PROJ} GENERATOR_MODEL={ENDPOINT} RAG_MODEL_BASE=gemini-3.1-flash-lite" in polled

CHUNK_ID, QUESTION = "acme:code_on_wages_2019#p9-1", "Is withholding an employee's increment a deduction from wages under the Code on Wages?"
CH = next(c for c in CHUNKS if c["chunk_id"] == CHUNK_ID)
assert CH not in mt.sample(CHUNKS, 300) and mt.exclude_golden([{**CH, "question": QUESTION}], GOLDEN)[0], "the served question must be neither trained nor tested"
assert "the withholding of increment or promotion, including the stoppage of an increment" in re.sub(r"\s+", " ", CH["text"])
SERVE_PY = """import ast, os, re, sys, types as pytypes
sys.path[:0] = [".", "evals", "services/rag-api"]
from google import genai
from google.genai import errors, types
import make_trainset as mt
from context_budget import source_header
from shared.documind_schemas import ModelDraft
P, EP = os.environ["PROJECT"], os.environ["ENDPOINT"]
fn = next(n for n in ast.parse(open("services/rag-api/generator.py", encoding="utf-8").read()).body
          if isinstance(n, ast.FunctionDef) and n.name == "_endpoint_location")
ns = {"re": re, "settings": pytypes.SimpleNamespace(generator_location=os.environ.get("GENERATOR_LOCATION", ""), region=os.environ["REGION"])}
exec(compile(ast.Module([fn], []), "generator.py", "exec"), ns)       # lifted: generator.py builds its clients when imported
where = ns["_endpoint_location"](EP)
print(f"the endpoint's path says {EP.split('/locations/', 1)[1].split('/', 1)[0]}; the generator would call it at {where}")
c = next(c for c in mt.load_chunks("acme") if c["chunk_id"] == "acme:code_on_wages_2019#p9-1")       # not a training row's chunk
q = "Is withholding an employee's increment a deduction from wages under the Code on Wages?"         # not a golden question
prompt = f"{mt.SYSTEM}\\n\\nContext:\\n{source_header(1, c)}\\n{c['text']}\\n\\nQuestion: {q}"      # the generator's shape, one source
cfg = types.GenerateContentConfig(response_mime_type="application/json", response_schema=ModelDraft, max_output_tokens=2048,
                                  thinking_config=types.ThinkingConfig(thinking_level="LOW"))      # generator._call's settings
tree = ast.parse(open("services/rag-api/cost.py", encoding="utf-8").read())
usd_in, usd_out = next(ast.literal_eval(n.value) for n in tree.body
                       if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")["gemini-3.1-flash-lite"]
for loc in dict.fromkeys(("us-central1", "global", where)):
    try:
        r = genai.Client(enterprise=True, project=P, location=loc).models.generate_content(model=EP, contents=prompt, config=cfg)
    except errors.APIError as e:
        print(f"  {loc:12} {e.code} {e.status}")
        continue
    d, u = ModelDraft.model_validate_json(r.text), r.usage_metadata
    out = (u.candidates_token_count or 0) + (u.thoughts_token_count or 0)
    marks = re.findall(r"\\[(\\d+(?:\\s*,\\s*\\d+)*)\\]", d.answer)
    rs = (u.prompt_token_count * usd_in + out * usd_out) / 1e6 * 85
    print(f"  {loc:12} answered: {u.prompt_token_count:,} tokens in, {out:,} out; a ModelDraft, answerable {d.answerable}, "
          f"{len(d.citations)} citation(s), {len(marks)} [N] marks in the answer")
    print(f"  the answer: {d.answer}")
    print(f"  the price: Rs {1.5 * rs:.4f} as Google bills a tuned Gemini 3 endpoint (1.5 x flash-lite); cost.py would log Rs {rs:.4f}")"""
CELLS["serve"] = "python - <<'PY'\n" + SERVE_PY + "\nPY"
OUT["serve"] = run([sys.executable, "-"], LANE + SERVE_PY, {"LANE172_NOW": "2026-09-24T10:32:00+00:00", "ENDPOINT": ENDPOINT})
SV = OUT["serve"]
assert "the endpoint's path says us; the generator would call it at us" in SV and "  us-central1  404 NOT_FOUND\n  global       404 NOT_FOUND\n  us           answered:" in SV, SV
assert "a ModelDraft, answerable True, 1 citation(s), 0 [N] marks in the answer" in SV and "cost.py would log Rs" in SV, SV

# ------------------------------------------------------------------ step 7 (optional): v3 validated, then tuned with its validation file
V3CHECK_PY = """import hashlib, json, os, sys
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
                     f"and {m['tenant']} may leave India" if ready else "do not tune until every line above holds"))"""
CELLS["v3check"] = "python - <<'PY'\n" + V3CHECK_PY + "\nPY"
OUT["v3check"] = run([sys.executable, "-"], LANE + V3CHECK_PY, {"LANE172_NOW": "2026-09-27T09:45:00+00:00"})
VC = OUT["v3check"]
N3T, N3H = len(V3T), len(V3H)
assert VC.count("sha256 as the manifest says") == 4 and f"1. the shape: {N3T + N3H} of {N3T + N3H} rows are one user turn that is the served prompt" in VC, VC
assert f"the chat file says the same in {N3T} of {N3T}; targets that parse as ModelDraft: {N3T + N3H}" in VC and "2. the test set: the golden set would drop 0 of " in VC, VC
assert "; 0 of the " in VC and "3. personal data: DLP over every prompt and every answer, so over every chunk: 0 with a finding" in VC, VC
assert f"about {TOK3_EPOCH:,} tokens an epoch" in VC and f"about {TRAIN3_TOKENS:,} training tokens" in VC and "verdict: ready to tune" in VC, VC
VAL = f"gs://{PROJ}-datasets/sft/documind_sft_v3.validation.vertex.jsonl"
TUNE3_ARGS = f"--display-name documind-sft-v3 --validation {VAL} --no-wait"
ECHO3 = ECHO.replace(TUNE_ARGS, TUNE3_ARGS)
ARGV3 = ECHO3.replace("${VERSION:-v1}", "v3").replace("\\\n", " ").split()
CELLS["tune3"] = ('VAL="gs://$PROJECT-datasets/sft/documind_sft_v3.validation.vertex.jsonl"     # lesson 12.1\'s step 7 wrote it\n'
                  'make tune PROJECT="$PROJECT" VERSION=v3 TUNE_ARGS="--display-name documind-sft-v3 --validation $VAL --no-wait" | tee ~/tune172v3.log\n'
                  "export JOB_V3=\"$(grep -o 'projects/[^ ]*/tuningJobs/[0-9]*' ~/tune172v3.log | head -1)\"; echo \"JOB_V3=$JOB_V3\"")
submitted3 = main_of("evals/tune.py", ARGV3[1:], "2026-09-27T10:02:00+00:00")
JOB3 = re.search(r"projects/[^ ]*/tuningJobs/[0-9]*", submitted3).group(0)
OUT["tune3"] = ECHO3 + submitted3 + f"JOB_V3={JOB3}\n"
assert JOB3 != JOB and f"  submitted {JOB3} on gemini-3.1-flash-lite: 3 epochs, adapter 4, dataset gs://{PROJ}-datasets/sft/documind_sft_v3.vertex.jsonl" in submitted3, submitted3
JOBS = json.loads((T / "jobs.json").read_text(encoding="utf-8"))
assert (JOBS[JOB3]["validation_rows"], JOBS[JOB3]["rows"], JOBS[JOB3]["display"], JOBS[JOB]["validation_rows"]) == (N3H, N3T, "documind-sft-v3", 0), JOBS[JOB3]
CELLS["poll3"] = ("JOB_V3=\"${JOB_V3:-$(grep -o 'projects/[^ ]*/tuningJobs/[0-9]*' ~/tune172v3.log | head -1)}\"     # after a reconnect: from the log\n"
                  'python evals/tune.py --project "$PROJECT" --poll "$JOB_V3" | tee ~/poll172v3.log   # a line a minute; safe to re-run\n'
                  "export ENDPOINT_V3=\"$(grep -o 'projects/[^ ]*/endpoints/[0-9]*' ~/poll172v3.log | head -1)\"; echo \"ENDPOINT_V3=$ENDPOINT_V3\"")
polled3 = main_of("evals/tune.py", ["tune.py", "--project", PROJ, "--poll", JOB3], "2026-09-27T10:03:00+00:00")
ENDPOINT3 = re.search(r"projects/[^ ]*/endpoints/[0-9]*", polled3).group(0)
STATES3 = [line for line in polled3.splitlines() if re.match(r"  \d\d:\d\d:\d\d JobState\.", line)]
lines3 = polled3.splitlines()
first3 = lines3.index(STATES3[0])
OUT["poll3"] = ("\n".join(lines3[:first3 + KEEP] + [f"  ...      (a line a minute while the job runs: {len(STATES3) - KEEP - 1} more here)", STATES3[-1]]
                          + lines3[first3 + len(STATES3):]) + f"\nENDPOINT_V3={ENDPOINT3}\n")
assert ENDPOINT3.startswith("projects/NUMBER/locations/us/endpoints/") and ENDPOINT3 != ENDPOINT, ENDPOINT3
assert f"make candidate PROJECT={PROJ} GENERATOR_MODEL={ENDPOINT3} RAG_MODEL_BASE=gemini-3.1-flash-lite" in polled3
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ the panel: submit (config_for) and serve (_client_for, _endpoint_location)
TUNABLE_DATE = re.search(r'TUNABLE_DATE = "([\d-]+)"', src[TUNE]).group(1)
BASES, EPOCHS, ADAPTERS, NAMES = ["gemini-3.1-flash-lite", "gemini-3.5-flash", "gemini-3.6-flash"], [1, 2, 3, 4, 5], [1, 2, 3, 4, 8, 16, 32], ["documind-sft-v1", "documind-sft-v2"]
MODELS = {"name": "gemini-3.6-flash", "us": "projects/NUMBER/locations/us/endpoints/ENDPOINT_ID", "eu": "projects/NUMBER/locations/eu/endpoints/ENDPOINT_ID"}
OVERRIDES = ["", "us-central1", "global", "us", "eu"]
genfns = {n.name: n for n in ast.parse(src[GEN]).body if isinstance(n, ast.FunctionDef) and n.name in ("_endpoint_location", "_client_for")}


def client_for(model: str, override: str) -> str:
    ns = {"re": re, "settings": SimpleNamespace(generator_location=override, region="asia-south1"), "_client_at": lambda loc: loc, "_client": "global",
          "genai": SimpleNamespace(Client=object)}                   # the return annotation is evaluated at def time
    exec(compile(ast.Module([genfns["_endpoint_location"], genfns["_client_for"]], []), "generator.py", "exec"), ns)
    return ns["_client_for"](model)


def config_case(base, epochs, adapter, name):
    try:
        return {"cfg": tune.config_for(base, epochs, adapter, name)}
    except SystemExit as e:
        return {"refused": str(e)}


CASES = [["submit", b, e, a, n] for b in BASES for e in EPOCHS for a in ADAPTERS for n in NAMES] + [["serve", k, o] for k in MODELS for o in OVERRIDES]
PY_SIDE = [config_case(*c[1:]) if c[0] == "submit" else client_for(MODELS[c[1]], c[2]) for c in CASES]
assert client_for(MODELS["us"], "") == "us" and client_for(MODELS["name"], "us") == "global" and client_for(MODELS["us"], "global") == "global"

UI_JS = r"""var root = document.getElementById('tj'); if (!root) return;
  var TUNABLE = __TUNABLE__, TUNABLE_DATE = __TDATE__, ADAPTER = __ADAPTER__, GOOGLE_ADAPTERS = __GADAPTERS__, USD_M = __USDM__, TOK = __TOK__, MODELS = __MODELS__;
  var has = function(o, k){ return Object.prototype.hasOwnProperty.call(o, k); };
  function configFor(base, epochs, adapter, name){
    if (TUNABLE.indexOf(base) < 0) { return {refused: base + " is not tunable: managed SFT accepts ['" + TUNABLE.slice().sort().join("', '") + "'] as of " + TUNABLE_DATE + ". gemini-3.6-flash is the course default for inference and is NOT tunable - re-check the tuning page, then update TUNABLE here and in 10.1."}; }
    if (!has(ADAPTER, String(adapter))) { return {refused: 'adapter ' + adapter + ': the LoRA rank must be one of [' + Object.keys(ADAPTER).map(Number).sort(function(a, b){ return a - b; }).join(', ') + ']'}; }
    return {cfg: {epoch_count: epochs, adapter_size: ADAPTER[String(adapter)], tuned_model_display_name: name}}; }
  function endpointLocation(model, override){ if (override) { return override; } var m = /\/locations\/([^/]+)\//.exec(model); return m ? m[1] : 'asia-south1'; }
  function clientFor(model, override){ return model.indexOf('projects/') === 0 ? endpointLocation(model, override) : 'global'; }
  window.__tj = {configFor: configFor, clientFor: clientFor};
  var $ = function(id){ return document.getElementById(id); };
  function line(out, cls, text){ var d = document.createElement('div'); if (cls) { d.className = cls; } d.textContent = text; out.appendChild(d); return d; }
  function submit(){ var base = $('tj-base').value, epochs = Number($('tj-epochs').value), adapter = Number($('tj-adapter').value), name = $('tj-name').value, out = $('tj-submit'), r = configFor(base, epochs, adapter, name);
    out.textContent = '';
    if (r.refused) { line(out, 'stop', 'Refused before submission, free:'); line(out, '', r.refused); return; }
    line(out, 'pass', 'Submitted from us-central1, tune.py\u2019s REGION.');
    line(out, '', 'The config the SDK receives: ' + JSON.stringify(r.cfg).split('":').join('": ').split(',"').join(', "'));
    var tokens = TOK * epochs, rs = tokens * USD_M[base] / 1e6 * 85;
    line(out, '', 'It bills about ' + tokens.toLocaleString('en-US') + ' training tokens (' + TOK.toLocaleString('en-US') + ' an epoch \u00d7 ' + epochs + '): about Rs ' + Math.round(rs).toLocaleString('en-US') + ' at USD ' + USD_M[base].toFixed(2) + ' a million, Google\u2019s price for ' + base + '.');
    if (GOOGLE_ADAPTERS.indexOf(adapter) < 0) { line(out, 'stop', 'The kit accepts this rank. Google\u2019s page lists 1, 2, 4, 8 and 16 for this base.'); }
    if (name === 'documind-sft-v1') { line(out, 'stop', 'The tuned model is named documind-sft-v1, whatever version it was tuned on.'); } }
  function serve(){ var key = $('tj-model').value, model = MODELS[key], override = $('tj-loc').value, loc = clientFor(model, override), out = $('tj-serve');
    out.textContent = '';
    var why = model.indexOf('projects/') !== 0 ? 'a model name is served on the global endpoint' : (override ? 'GENERATOR_LOCATION wins' : 'the path\u2019s own /locations/ segment');
    line(out, '', 'The generator\u2019s client: ' + loc + ' (' + why + ').');
    var home = model.indexOf('projects/') === 0 ? /\/locations\/([^/]+)\//.exec(model)[1] : 'global';
    if (loc === home) { line(out, 'pass', 'It answers.'); } else { line(out, 'stop', '404 NOT_FOUND: ' + (model.indexOf('projects/') === 0 ? 'the endpoint is served only from ' + home + '.' : 'a Gemini 3 model is served only on global.')); } }
  ['tj-base', 'tj-epochs', 'tj-adapter', 'tj-name'].forEach(function(id){ $(id).addEventListener('change', submit); });
  ['tj-model', 'tj-loc'].forEach(function(id){ $(id).addEventListener('change', serve); });
  submit(); serve();"""
UI_JS = (UI_JS.replace("__TUNABLE__", json.dumps(sorted(tune.TUNABLE))).replace("__TDATE__", json.dumps(TUNABLE_DATE))
         .replace("__ADAPTER__", json.dumps({str(k): v for k, v in tune.ADAPTER_SIZE.items()})).replace("__GADAPTERS__", json.dumps(GOOGLE_ADAPTERS))
         .replace("__USDM__", json.dumps(USD_M)).replace("__TOK__", str(TOK_EPOCH)).replace("__MODELS__", json.dumps(MODELS)))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
PORT_JS = UI_JS.split("var $ = function(id)")[0].replace("var root = document.getElementById('tj'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var C = " + json.dumps(CASES) + ", M = " + json.dumps(MODELS) + ";\n"
        "process.stdout.write(JSON.stringify(C.map(function(c){ return c[0] === 'submit' ? window.__tj.configFor(c[1], c[2], c[3], c[4]) : window.__tj.clientFor(M[c[1]], c[2]); })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
for case, a_, b_ in zip(CASES, json.loads(node.stdout), PY_SIDE):
    assert a_ == b_, (case, a_, b_)
N_CHECKED = len(CASES)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "checks": "run in the operator shell, in the kit (the two self-tests and the rules; no network)",
    "validate": "run in the operator shell, in the kit (reads the bucket and Firestore; one DLP scan in asia-south1)",
    "tune": "run in the operator shell, in the kit (submits the job and returns: the billed act)",
    "poll": "run in the operator shell, in the kit (waits for the job, a line a minute)",
    "serve": "run in the operator shell, in the kit (one answer from the endpoint, and two calls that are not found)",
    "v3check": "optional: run in the operator shell, in the kit (reads the bucket and Firestore; DLP over every prompt)",
    "tune3": "optional: run in the operator shell, in the kit (submits the v3 job and returns: a second billed act)",
    "poll3": "optional: run in the operator shell, in the kit (waits for the v3 job, a line a minute)",
}
OUT_LABELS = {
    "checks": "(the kit's own self-tests and functions)",
    "validate": "(this cell over the v2 lesson 12.1's stand-in built, with DLP stood in: your findings are what DLP finds on your lane)",
    "tune": "(tune.py's own main(), with the tuning service stood in: your job's number is your own)",
    "poll": f"(tune.py's own poll, over a stand-in job that ends after {POLL_MIN} minutes: yours takes as long as Vertex AI's queue and three epochs take)",
    "serve": "(a stand-in endpoint that answers only where its path says, in the way the training rows are written: your tuned model writes its own answer)",
    "v3check": "(this cell over the v3 lesson 12.1's stand-in built, with DLP stood in: your counts are your v3's)",
    "tune3": "(tune.py's own main(), with the tuning service stood in: your job's number is your own)",
    "poll3": f"(tune.py's own poll over the same stand-in job, which takes as long as step 6's: v3 is about {TOK3_EPOCH / TOK_EPOCH:.1f} times v2's tokens, so yours takes longer)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
opts = lambda pairs, sel: "".join(f'<option value="{html.escape(str(v))}"{" selected" if v == sel else ""}>{html.escape(t)}</option>' for v, t in pairs)  # noqa: E731
STATS = {"N_CHECKED": str(N_CHECKED), "N2": str(M2["rows"]), "TOK_EPOCH": f"{TOK_EPOCH:,}", "TOK_MAX": f"{TOK_MAX:,}", "TRAIN_TOKENS": f"{TRAIN_TOKENS:,}",
         "TRAIN_RS": f"{TRAIN_RS:,.0f}", "SYS_TOK": f"{SYS_TOK:,}", "SYS_RS": f"{SYS_TOK * USD_M['gemini-3.1-flash-lite'] / 1e6 * 85:,.0f}",
         "POLL_MIN": str(POLL_MIN), "N_GOLD": str(len(GOLDEN)), "N_GLOBEX": str(len(G_CH)),
         "N3T": str(N3T), "N3H": str(N3H), "TOK3_EPOCH": f"{TOK3_EPOCH:,}", "TOK3_HELD": f"{TOK3_HELD:,}", "TRAIN3_TOKENS": f"{TRAIN3_TOKENS:,}",
         "TRAIN3_RS": f"{TRAIN3_RS:,.0f}", "V3_RATIO": f"{TOK3_EPOCH / TOK_EPOCH:.1f}",
         "BASE_OPTIONS": opts([("gemini-3.1-flash-lite", "gemini-3.1-flash-lite (the kit's)"), ("gemini-3.5-flash", "gemini-3.5-flash"),
                               ("gemini-3.6-flash", "gemini-3.6-flash (the served model)")], "gemini-3.1-flash-lite"),
         "EPOCH_OPTIONS": opts([(e, f"{e}{' (the kit' + chr(39) + 's)' if e == 3 else ''}") for e in EPOCHS], 3),
         "ADAPTER_OPTIONS": opts([(a, f"{a}{' (the kit' + chr(39) + 's)' if a == 4 else ''}") for a in ADAPTERS], 4),
         "NAME_OPTIONS": opts([("documind-sft-v2", "documind-sft-v2 (step 5's)"), ("documind-sft-v1", "the default: documind-sft-v1")], "documind-sft-v2"),
         "MODEL_OPTIONS": opts([("us", "the tuned endpoint (locations/us)"), ("eu", "a tuned endpoint in locations/eu"), ("name", "gemini-3.6-flash (a model name)")], "us"),
         "LOC_OPTIONS": opts([("", "unset (the lane's)"), ("us-central1", "us-central1"), ("global", "global"), ("us", "us"), ("eu", "eu")], "")}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print({k: v for k, v in STATS.items() if not k.endswith("_OPTIONS")})
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: make_trainset main() for 12.1's v2 and v3, tune.py main() to submit and poll, the validation and the call | v2: {M2['rows']} rows, "
      f"about {TRAIN_TOKENS:,} training tokens; v3: {N3T} rows, about {TRAIN3_TOKENS:,}, endpoint {ENDPOINT3} | panel checked against config_for and "
      f"_client_for on {N_CHECKED} cases")
