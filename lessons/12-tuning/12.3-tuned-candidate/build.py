"""Build lesson 12.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Compare the tuned candidate with an uncontaminated baseline. Lesson 4.4's method - a no-traffic candidate, a diff of
its settings against the live revision's, the gate on both, the pairwise judge, the rupees from the usage rows - with
a tuned endpoint behind the candidate, and the four ways that comparison can be contaminated: the test set in the
training file (exclude_golden, 17.1), the answer cache (its lookup never reads the model), a second setting riding
along with the model (make candidate writes eleven), and a context cache only the baseline can read. The chapter's
gate: the tuned candidate passes make eval-live. The proofs: the pairwise verdict, and the rupee delta - with the
tuned endpoint priced at 1.5 times its base, as Google prices it, where the usage rows log the base (cost.py).
Offline: the answer cache's test (semantic_cache._alive, lifted), cost.price() for the endpoint two ways against
Google's, and make usage's model column. Live: make candidate; the audit; both gates and the rows that moved; make
judge API_B=; make usage and the delta; the candidate's tag removed.

Build-time proof: every cell ran the kit's own code - run_eval.live() for both gates, judge.py main() for the pairwise
judge, usage_rows.py for make usage, make_trainset.py main() to leave the bucket as lesson 12.1 leaves it - over a
stand-in lane (lane173.py, beside this file): the two revisions' answers, their settings, the usage rows (priced by
the kit's cost.price()), Vertex AI Evaluation, Firestore and Cloud Storage. The panel is make candidate's settings,
parsed from the Makefile, and cost.price(), ported and compared with the kit's on every combination it offers.
"""
import ast
import contextlib
import hashlib
import html
import io
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "12.3"
title = "<title>Lesson 12.3 Compare the tuned candidate with an uncontaminated baseline - one change, a clean test, a verdict, a delta | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
API = "https://documind-api-NUMBER.asia-south1.run.app"
CAND = "https://candidate---documind-api-NUMBER.asia-south1.run.app"
ENDPOINT = "projects/NUMBER/locations/us/endpoints/9136961803583303949"          # lesson 12.2's stand-in endpoint
REVS = ["documind-api-000NN-xxx", "documind-api-000NN-yyy"]
MT, JG, UR, COST, SC, MAIN = ("evals/make_trainset.py", "evals/judge.py", "evals/usage_rows.py", "services/rag-api/cost.py",
                              "services/rag-api/semantic_cache.py", "services/rag-api/main.py")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.tc-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:0 10px;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,140px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.tc-out{margin:6px 0 0;font-size:12.5px;line-height:1.6;}
.tc-out .pass{color:var(--teal-dark);font-weight:600;}
.tc-out .stop{color:#9a3412;font-weight:600;}
.tc-out .mono{font-family:var(--mono);font-size:11.5px;}
"""

setup = setup_section()

# ------------------------------------------------------------------ verbatim excerpts
EXCERPTS = {
    "recipe": ("Makefile - make candidate: the tuned endpoint as a setting, on a revision with no traffic",
               block("Makefile", "# A candidate revision of the API with another model behind it and NO traffic", n=10)),
    "alive": ("services/rag-api/semantic_cache.py - _alive(): the answer cache's test, which never reads the model",
              block(SC, "def _alive(d: dict, fingerprint: str | None, scope: str, now: datetime) -> bool:", n=8)),
    "priced": ("services/rag-api/cost.py - how the usage row prices a tuned endpoint",
               block(COST, "    # A tuned model (10.1) is an endpoint path", n=3)),
    "pairwise": ("evals/judge.py - main(): the candidate is judged, the live revision is the baseline",
                 block(JG, "    if a.api_b:", n=9)),
    "column": ("evals/usage_rows.py - show(): the model column, cut at twenty characters",
               block(UR, '        print("".join(f"{str(row[k])[:20]:22}" for k in keys)', n=2)),
    "pin": ("services/rag-api/main.py - choose_for(): a tenant's pinned model, before the service's",
            block(MAIN, '    model = ts["generator_model"] if ts.get("generator_model") else choose_model_for(req.query)', n=1)),
}
assert "--no-traffic --tag candidate" in EXCERPTS["recipe"][1] and EXCERPTS["recipe"][1].rstrip().endswith("--remove-env-vars GENERATOR_LOCATION)")
assert EXCERPTS["alive"][1].rstrip().endswith("return exp is None or exp > now                  # expired entries wait for the TTL policy; they are not served")
assert "model" not in EXCERPTS["alive"][1].split('"""', 2)[2]
assert EXCERPTS["pairwise"][1].rstrip().endswith("# the candidate is judged; the live revision is the baseline")
assert EXCERPTS["column"][1].rstrip().endswith("{row['p95_ms']:>7} {row['unanswerable_rate']:>6.2f}\")")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (MT, JG, UR, COST, SC, MAIN, "Makefile", "services/rag-api/cache_manager.py",
                                                          "evals/run_eval.py", "terraform/sql/tenant_daily.sql")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
assert "RAG_MODEL_BASE  ?= gemini-3.6-flash" in MK and "SEMANTIC_CACHE  ?= off" in MK and "GENERATOR_LOCATION ?=" in MK
assert "A tuned model (10.1) is an endpoint path, billed at its BASE model's rate: RAG_MODEL_BASE names it." in src[COST]
assert 'model = os.environ.get("RAG_MODEL_BASE") or "gemini-3.6-flash"' in src[COST]
assert '"embedding": Vector(qvec), "answer": answer, "model": model,' in src[SC] and "TTL_HOURS = int(os.environ.get(\"SEMANTIC_CACHE_TTL_H\", \"24\"))" in src[SC]
assert "if not rec or (model and rec.get(\"model\") != model):" in src["services/rag-api/cache_manager.py"]            # a context cache is one model's
assert "make cache PROJECT=... TENANT=acme CACHE_OP=show   # show | refresh | delete" in (KIT / "services/rag-api/cache_admin.py").read_text(encoding="utf-8")
assert 'print("\\n  the gate (run_eval.py) still decides; this judge explains. Where they disagree, read the row.")' in src[JG]
assert '"model": model,' in src[MAIN] and 'cost = cost_usd if cost_usd is not None else price(model, ans_tokens_in, ans_tokens_out, cached)["usd"]' in src[MAIN]
assert "_record(row[\"cost_usd\"])" in src[MAIN] and "SUM(CAST(jsonPayload.cost_usd AS FLOAT64))" in src["terraform/sql/tenant_daily.sql"]
assert "tenant_settings/{tenant} may name a model_backend and a generator_model" in src[MAIN]
assert "generator_model" not in MK and "generator_model" not in (KIT / "commands/lane.py").read_text(encoding="utf-8")   # no target writes the pin
assert "--no-traffic --tag candidate" in MK and "record-candidate" in MK and "promote: guard-project" in MK and "rollback: guard-project" in MK
assert "(deploy/.candidate-revision - make promote moves traffic to it by name)" in MK
assert "(no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)" in MK
assert "Weights cannot be filtered per tenant afterwards." in src[MT] and "TENANT        ?= acme" in MK
# step 7's reasons, in the kit's own words; the prices the page states
GEN_SRC = (KIT / "services/rag-api/generator.py").read_text(encoding="utf-8")
assert "every surface above the API (MCP, the agents,\n    the UI) changes nothing" in GEN_SRC
assert "the live revision keeps serving, and the tagged URL answers the gate and the judge" in MK
assert 'moves traffic to that name - never "the latest revision", which promotes whatever is newest' in MK
assert "a tuned endpoint or a routed tier must not be handed gemini-3.6-flash's cache" in re.sub(r"\s+", " ", src["services/rag-api/cache_manager.py"])
assert "cached_tokens * usd_in * 0.10      # cached input: 90% off" in src[COST]
assert "make candidate PROJECT={a.project} GENERATOR_MODEL={ep} RAG_MODEL_BASE={a.base}" in (KIT / "evals/tune.py").read_text(encoding="utf-8")
# make candidate's settings, as the recipe writes them: eleven NAME=$(VAR) pairs, GENERATOR_LOCATION removed unless given
RECIPE = MK[MK.index("\ncandidate: guard-project\n") + 1:].split("\n\n", 1)[0]
ENV_STR = RECIPE.split('--update-env-vars "^|^', 1)[1].split('"', 1)[0]
PAIRS = re.findall(r"([A-Z_]+)=\$\(([A-Z_]+)\)", ENV_STR.split("$(if", 1)[0])
DEFAULTS = {v: (re.search(rf"^{v}\s*\?=[ \t]*(.*)$", MK, re.M).group(1).strip() if re.search(rf"^{v}\s*\?=", MK, re.M) else "") for _, v in PAIRS}
assert len(PAIRS) == 11 and PAIRS[0] == ("GENERATOR_MODEL", "GENERATOR_MODEL") and PAIRS[1] == ("RAG_MODEL_BASE", "RAG_MODEL_BASE"), PAIRS
assert "$(if $(GENERATOR_LOCATION),|GENERATOR_LOCATION=$(GENERATOR_LOCATION),)" in ENV_STR and "$(if $(GENERATOR_LOCATION),,--remove-env-vars GENERATOR_LOCATION)" in RECIPE
LIVE_ENV = {k: DEFAULTS[v] for k, v in PAIRS}
LIVE_ENV.update({"GIT_SHA": "abc1234", "DEMO_MODE": "1"})


def candidate_env(live: dict, over: dict) -> dict:
    """What make candidate leaves on the new revision: the live settings, the eleven pairs written over them (an override, else the
    Makefile's default), GENERATOR_LOCATION set when given and removed when not."""
    env = dict(live)
    for k, v in PAIRS:
        env[k] = over.get(v, DEFAULTS[v])
    if over.get("GENERATOR_LOCATION"):
        env["GENERATOR_LOCATION"] = over["GENERATOR_LOCATION"]
    else:
        env.pop("GENERATOR_LOCATION", None)
    return env


OVER = {"GENERATOR_MODEL": ENDPOINT, "RAG_MODEL_BASE": "gemini-3.1-flash-lite"}
CAND_ENV = candidate_env(LIVE_ENV, OVER)
assert sorted(k for k in LIVE_ENV.keys() | CAND_ENV.keys() if LIVE_ENV.get(k) != CAND_ENV.get(k)) == ["GENERATOR_MODEL", "RAG_MODEL_BASE"]
# cost.price(), lifted: cost.py imports BigQuery when loaded, and the fallback table is what the lane prices at
CTREE = ast.parse(src[COST])
FALLBACK = next(ast.literal_eval(n.value) for n in CTREE.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")
cns = {"os": os, "USD_INR": 85.0, "FALLBACK": FALLBACK, "_prices": lambda: FALLBACK}
exec(compile(ast.Module([n for n in CTREE.body if isinstance(n, ast.FunctionDef) and n.name == "price"], []), "cost.py", "exec"), cns)


def kit_price(model: str, tin: int, tout: int, base: str | None) -> dict:
    old = os.environ.get("RAG_MODEL_BASE")
    if base is None:
        os.environ.pop("RAG_MODEL_BASE", None)
    else:
        os.environ["RAG_MODEL_BASE"] = base
    try:
        return cns["price"](model, tin, tout)
    finally:
        if old is None:
            os.environ.pop("RAG_MODEL_BASE", None)
        else:
            os.environ["RAG_MODEL_BASE"] = old


TUNED = 1.5                                       # Google's pricing page, 24 September 2026: a tuned Gemini 3 endpoint predicts at 1.5 x its base

# ------------------------------------------------------------------ the lane: the bucket as 17.1 leaves it, and ~/tune172.log from 17.2
sys.path[:0] = [str(KIT), str(KIT / "evals")]
import make_trainset as mt  # noqa: E402
import run_eval as rv  # noqa: E402
GOLDEN = rv.load_golden()
CHUNKS = mt.load_chunks("acme")
T = Path(tempfile.mkdtemp(prefix="lesson173-"))
K2 = T / "kit"
for part in ("evals", "shared", "services/rag-api"):
    shutil.copytree(KIT / part, K2 / part, ignore=shutil.ignore_patterns("__pycache__", "reports"))
shutil.copy(KIT / "Makefile", K2 / "Makefile")
shutil.copy(HERE / "lane173.py", T / "lane173.py")
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "HOME": str(T),
       "USERPROFILE": str(T), "REGION": "asia-south1", "PYTHONPATH": str(T), "LANE173_ENDPOINT": ENDPOINT, "ENDPOINT": ENDPOINT,
       **{f"LANE173_{k.upper()}": str(T / f"{k}.json") for k in ("gcs", "run", "logs")}}
for k in [k for k in ENV if k.startswith(("TRAINSET_", "DOCUMIND_", "GENERATOR_", "GOOGLE_CLOUD_PROJECT", "RAG_MODEL_BASE", "GIT_SHA"))]:
    ENV.pop(k)
(T / "run.json").write_text(json.dumps({"live": LIVE_ENV, "cand": CAND_ENV, "revs": REVS, "cand_url": CAND}), encoding="utf-8")
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
ENV["LANE173_TITLES"] = str(T / "titles.json")


def run(cmd: list, stdin: str | None = None, env: dict | None = None) -> str:
    r = subprocess.run(cmd, input=stdin, cwd=str(K2), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (cmd[:3], r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


LANE = "import lane173\nlane173.freeze()\nlane173.install()\n"


def main_of(script: str, argv: list, now: str, env: dict | None = None) -> str:
    code = (LANE + "import runpy, sys\nsys.argv = " + repr(argv) + "\n"
            "try:\n    runpy.run_path(" + repr(script) + ", run_name='__main__')\nexcept SystemExit as e:\n    assert not e.code, e.code\n")
    return run([sys.executable, "-"], code, {"LANE173_NOW": now, **(env or {})})


made = main_of("evals/make_trainset.py", ["make_trainset.py", "--project", PROJ, "--tenant", "acme", "--rows", "300",
                                          "--upload", f"gs://{PROJ}-datasets/sft/", "--version", "v2"], "2026-09-24T09:10:00+00:00")
M2 = json.loads((K2 / "evals/sft/documind_sft_v2.manifest.json").read_text(encoding="utf-8"))
assert (M2["rows"], M2["dropped_golden_overlap"]) == (315, 15) and "sha ac73343d2550" in made, (M2, made[-300:])   # 17.1's v2, byte for byte
(T / "tune172.log").write_text(f"python evals/tune.py --project {PROJ} --dataset gs://{PROJ}-datasets/sft/documind_sft_${{VERSION:-v1}}.vertex.jsonl \\\n"
                               f"  --base gemini-3.1-flash-lite --epochs 3 --adapter 4 --display-name documind-sft-v2 --no-wait\n"
                               f"  submitted projects/NUMBER/locations/us-central1/tuningJobs/7240862654976436473 on gemini-3.1-flash-lite: 3 epochs, adapter 4, "
                               f"dataset gs://{PROJ}-datasets/sft/documind_sft_v2.vertex.jsonl\n", encoding="utf-8")
(T / "poll172.log").write_text(f"  endpoint    : {ENDPOINT}\n", encoding="utf-8")

# ------------------------------------------------------------------ step 3: what the kit does with a tuned candidate (offline)
CHECKS_PY = """import ast, datetime as dt, os, sys
sys.path[:0] = ["evals"]
from usage_rows import group, show
EP = "projects/NUMBER/locations/us/endpoints/ENDPOINT_ID"
# 1. the answer cache's test, lifted out of semantic_cache.py (which builds a Firestore client when imported)
tree = ast.parse(open("services/rag-api/semantic_cache.py", encoding="utf-8").read())
ns = {"datetime": dt.datetime}
exec(compile(ast.Module([n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "_alive"], []), "semantic_cache.py", "exec"), ns)
now = dt.datetime.now(dt.timezone.utc)
entry = {"model": "gemini-3.6-flash", "fingerprint": "f1", "scope": "s1", "expire_at": now + dt.timedelta(hours=20)}
print(f"an answer gemini-3.6-flash cached, looked up for the tuned endpoint: alive {ns['_alive'](entry, 'f1', 's1', now)}")
# 2. one answer on the tuned endpoint, priced by cost.py (lifted: it imports BigQuery when loaded) and by Google
tree = ast.parse(open("services/rag-api/cost.py", encoding="utf-8").read())
cns = {"os": os, "USD_INR": 85.0}
cns["FALLBACK"] = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")
cns["_prices"] = lambda: cns["FALLBACK"]
exec(compile(ast.Module([n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "price"], []), "cost.py", "exec"), cns)
TIN, TOUT = 7400, 150
for base in ("gemini-3.1-flash-lite", "gemini-3.6-flash"):
    os.environ["RAG_MODEL_BASE"] = base
    print(f"cost.py with RAG_MODEL_BASE={base:22} Rs {cns['price'](EP, TIN, TOUT)['inr']:.4f} an answer of {TIN:,} tokens in, {TOUT} out")
usd_in, usd_out = cns["FALLBACK"]["gemini-3.1-flash-lite"]
print(f"Google, a tuned endpoint at 1.5 x its base          Rs {1.5 * (TIN * usd_in + TOUT * usd_out) / 1e6 * 85:.4f}")
# 3. what make usage prints for it
rows = [{"model": "gemini-3.6-flash", "tokens_in": TIN, "tokens_out": 210, "cost_usd": 0.01268, "latency_ms": 2100},
        {"model": EP, "tokens_in": TIN, "tokens_out": TOUT, "cost_usd": 0.002075, "latency_ms": 1000}]
show("make usage's model column", group(rows, ("model",)), ("model",))"""
CELLS = {"checks": "python - <<'PY'\n" + CHECKS_PY + "\nPY"}
OUT = {"checks": run([sys.executable, "-"], CHECKS_PY)}
CK = OUT["checks"]
assert "an answer gemini-3.6-flash cached, looked up for the tuned endpoint: alive True" in CK, CK
assert "RAG_MODEL_BASE=gemini-3.1-flash-lite  Rs 0.1764" in CK and "RAG_MODEL_BASE=gemini-3.6-flash       Rs 1.0391" in CK and "1.5 x its base          Rs 0.2646" in CK, CK
assert "\nprojects/NUMBER/loca  " in CK, CK
EX = {k: kit_price(ENDPOINT, 7400, 150, b)["inr"] for k, b in (("lite", "gemini-3.1-flash-lite"), ("flash", "gemini-3.6-flash"))}
assert (EX["lite"], EX["flash"]) == (0.1764, 1.0391) and round(1.5 * EX["lite"], 4) == 0.2646
PIN_RATIO = kit_price(ENDPOINT, 7400, 140, "gemini-3.6-flash")["usd"] / (TUNED * kit_price(ENDPOINT, 7400, 140, "gemini-3.1-flash-lite")["usd"])
assert 3.5 < PIN_RATIO < 4.5, PIN_RATIO                # a pinned endpoint priced at the live revision's base: about four times Google's

# ------------------------------------------------------------------ step 4: make candidate, and the audit
CELLS["candidate"] = ("export ENDPOINT=\"${ENDPOINT:-$(grep -o 'projects/[^ ]*/endpoints/[0-9]*' ~/poll172.log | head -1)}\"     # lesson 12.2's endpoint\n"
                      'make candidate PROJECT="$PROJECT" GENERATOR_MODEL="$ENDPOINT" RAG_MODEL_BASE=gemini-3.1-flash-lite\n'
                      'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"')
GC_LINE = RECIPE.split("\n")[1:3]
ECHO = "\n".join(GC_LINE).replace("\t", "").replace("$(REGION)", "asia-south1").replace("$(PROJECT)", PROJ)
for k, v in PAIRS:
    ECHO = ECHO.replace(f"$({v})", OVER.get(v, DEFAULTS[v]))
ECHO = (ECHO.replace("$(if $(RETRIEVAL_BACKEND),|RETRIEVAL_BACKEND=$(RETRIEVAL_BACKEND)|RAG_LOCATION=$(RAG_LOCATION),)", "")
        .replace("$(if $(GENERATOR_LOCATION),|GENERATOR_LOCATION=$(GENERATOR_LOCATION),)", "")
        .replace("$(if $(GENERATOR_LOCATION),,--remove-env-vars GENERATOR_LOCATION)", "--remove-env-vars GENERATOR_LOCATION"))
assert "$(" not in ECHO and ECHO.startswith("gcloud run services update documind-api --region asia-south1") and f"GENERATOR_MODEL={ENDPOINT}|RAG_MODEL_BASE=gemini-3.1-flash-lite|" in ECHO, ECHO
OUT["candidate"] = (ECHO + "\n...\n"
                    f">> candidate revision: {REVS[1]} (deploy/.candidate-revision - make promote moves traffic to it by name)\n"
                    f">> candidate: {CAND} (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)\n"
                    f"CAND={CAND}\n")

AUDIT_PY = """import json, os, re, subprocess, sys
sys.path[:0] = [".", "evals"]
P, R = os.environ["PROJECT"], os.environ["REGION"]
os.environ.setdefault("GOOGLE_CLOUD_PROJECT", P)


def gcloud(*a):
    cmd = ["gcloud", *a, "--region", R, "--project", P, "--format=json"]
    return json.loads(subprocess.run(cmd, capture_output=True, text=True, check=True).stdout)


traffic = gcloud("run", "services", "describe", "documind-api")["status"]["traffic"]
live = max((t for t in traffic if t.get("percent")), key=lambda t: t["percent"])["revisionName"]
cand = next(t["revisionName"] for t in traffic if t.get("tag") == "candidate")
env = lambda rev: {e["name"]: e.get("value", "") for e in gcloud("run", "revisions", "describe", rev)["spec"]["containers"][0].get("env", [])}
a, b = env(live), env(cand)
diff = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
print(f"1. one change: {len(diff)} settings differ between {live} (live) and {cand}")
for k in diff:
    print(f"   {k:16} {a.get(k, '(unset)')} -> {b.get(k, '(unset)')}")
one = set(diff) == {"GENERATOR_MODEL", "RAG_MODEL_BASE"} and b["RAG_MODEL_BASE"] == "gemini-3.1-flash-lite"
print("   " + ("the model and the base it is priced at, and nothing else" if one else "more than the model differs: run make candidate again with the live values"))
cache = (a.get("SEMANTIC_CACHE", "off"), b.get("SEMANTIC_CACHE", "off"))
print(f"2. the answer cache: {cache[0]} on the live revision, {cache[1]} on the candidate"
      + ("" if cache == ("off", "off") else " - its lookup never reads the model: turn it off on both first"))
from google.cloud import firestore, storage
import make_trainset as mt
uri = re.search(r", dataset (gs://\\S+\\.vertex\\.jsonl)", open(os.path.expanduser("~/tune172.log"), encoding="utf-8").read()).group(1)
bucket_name, name = uri[len("gs://"):].split("/", 1)                       # what lesson 12.2 tuned on
bucket = storage.Client(project=P).bucket(bucket_name)
m = json.loads(bucket.blob(name.replace(".vertex.jsonl", ".manifest.json")).download_as_text())
chunks = {c["text"].strip(): c for c in mt.load_chunks(m["tenant"])}
rows = []
for line in bucket.blob(name).download_as_text().splitlines():
    user = json.loads(line)["contents"][0]["parts"][0]["text"]
    c = chunks[user.split("[Source 1] ", 1)[1].rsplit("\\n\\nQuestion: ", 1)[0].strip()]
    rows.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "text": c["text"], "question": user.rsplit("\\n\\nQuestion: ", 1)[1]})
golden = [json.loads(l) for l in open("evals/golden.jsonl", encoding="utf-8") if l.strip()]
left = mt.exclude_golden(rows, golden)[1]
print(f"3. the test set: the endpoint was tuned on {name.rsplit('/', 1)[-1]}, {len(rows)} rows; building it dropped "
      f"{m['dropped_golden_overlap']} for the golden set, and today's golden set would drop {len(left)} more")
rec = firestore.Client(project=P).collection("tenant_caches").document(m["tenant"]).get()
print("4. the context cache: " + (f"{m['tenant']} has one, made for {rec.to_dict().get('model')}: the live revision reads it and the "
                                   f"candidate cannot - delete it for the hour (make cache TENANT={m['tenant']} CACHE_OP=delete)" if rec.exists
                                   else f"none for {m['tenant']}, so both revisions pay full price for their input"))
clean = one and cache == ("off", "off") and not left and not rec.exists
print("verdict: " + ("uncontaminated - one change, no answer cache, a training file the test set never entered, the same input price"
                     if clean else "not yet: fix the lines above, then run this cell again"))"""
CELLS["audit"] = "python - <<'PY'\n" + AUDIT_PY + "\nPY"
OUT["audit"] = run([sys.executable, "-"], LANE + AUDIT_PY, {"LANE173_NOW": "2026-09-24T10:40:00+00:00"})
AU = OUT["audit"]
assert f"1. one change: 2 settings differ between {REVS[0]} (live) and {REVS[1]}" in AU and f"GENERATOR_MODEL  gemini-3.6-flash -> {ENDPOINT}" in AU, AU
assert "RAG_MODEL_BASE   gemini-3.6-flash -> gemini-3.1-flash-lite" in AU and "the model and the base it is priced at, and nothing else" in AU, AU
assert "2. the answer cache: off on the live revision, off on the candidate\n" in AU, AU
assert "3. the test set: the endpoint was tuned on documind_sft_v2.vertex.jsonl, 315 rows; building it dropped 15 for the golden set, and today's golden set would drop 0 more" in AU, AU
assert "4. the context cache: none for acme" in AU and "verdict: uncontaminated" in AU, AU

# ------------------------------------------------------------------ step 5: the gate on both revisions, and the rows that moved
for k in ("DOCUMIND_ID_TOKEN", "DOCUMIND_OUTSIDER_TOKEN", "DOCUMIND_USER_EMAIL", "DOCUMIND_OUTSIDER_EMAIL"):
    os.environ.pop(k, None)
os.environ["LANE173_ENDPOINT"] = ENDPOINT
sys.path.insert(0, str(HERE))
import lane173  # noqa: E402
rv.ask = lane173.ask
rv.fetch_current_shas = lambda *a, **k: set()
HOME = T


def gate(api: str, name: str) -> str:
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        rc = rv.live(api, report=str(HOME / name))
    assert rc == 0, (name, rc, buf.getvalue()[-800:])
    out = []
    for line in buf.getvalue().splitlines():
        if line.startswith(("  latency ms", "  retrieve_ms", "  rerank_ms", "  generate_ms", "  pool")):
            line = re.sub(r"(p50|p95|avg)\s+[\d.]+", lambda m: f"{m.group(1)}   ...", line)
            line = re.sub(r"semantic cache hits \d+", "semantic cache hits ...", line)
        if "[info] quote_support_rate" in line:
            line = re.sub(r"\d+\.\d%", "  ...", line)
        out.append(line.replace(str(HOME / name), f"/home/YOU/{name}"))
    return f">> {api}\n" + "\n".join(out) + "\n"


BASE_OUT, CAND_OUT = gate(API, "base173.json"), gate(CAND, "cand173.json")
CELLS["gates"] = ('make eval-live PROJECT="$PROJECT" REPORT="$HOME/base173.json" | tail -3\n'
                  'make eval-live PROJECT="$PROJECT" API="$CAND" REPORT="$HOME/cand173.json"')
OUT["gates"] = "\n".join(BASE_OUT.rstrip("\n").split("\n")[-3:]) + "\n" + CAND_OUT
assert BASE_OUT.rstrip().endswith("All thresholds met.") and CAND_OUT.rstrip().endswith("All thresholds met."), CAND_OUT[-600:]
assert "rows that cost a point (3):" in CAND_OUT and "jn-03  join      acme    answered without ['45', '60']" in CAND_OUT and "jn-09" in CAND_OUT, CAND_OUT[-900:]
BASE, CANDR = (json.loads((HOME / n).read_text(encoding="utf-8")) for n in ("base173.json", "cand173.json"))
COMPARE_PY = """import json, os
base, cand = (json.load(open(os.path.expanduser(f"~/{n}173.json"), encoding="utf-8")) for n in ("base", "cand"))
print(f"  {'':21} {'live':>7} {'candidate':>10}  {'needs':>5}")
for k in base["scores"]:
    if k in base["judged"] or k in cand["judged"]:
        flag = "  FAIL" if k in cand["failed"] else ""
        print(f"  {k:21} {base['scores'][k]:7.1%} {cand['scores'][k]:10.1%}  {base['thresholds'][k]:5.0%}{flag}")
was = {r["id"]: r["pass"] for r in base["records"]}
moved = [r for r in cand["records"] if was.get(r["id"]) != r["pass"]]
for r in moved:
    print(f"  {r['id']}: {'pass' if was.get(r['id']) else 'fail'} on live, {'pass' if r['pass'] else 'fail'} on the candidate ({r['why'] or r['outcome']})")
med = lambda rep: sorted(x["latency_ms"] for x in rep["records"])[len(rep["records"]) // 2]
print(f"  {len(moved)} row(s) changed verdict; median round trip {med(base)} ms live, {med(cand)} ms candidate")"""
CELLS["compare"] = "python - <<'PY'\n" + COMPARE_PY + "\nPY"
OUT["compare"] = run([sys.executable, "-"], COMPARE_PY)
OUT["compare"] = re.sub(r"median round trip \d+ ms live, \d+ ms candidate", "median round trip ... ms live, ... ms candidate", OUT["compare"])
CO = OUT["compare"]
assert "jn-06: fail on live, pass on the candidate" in CO and "jn-03: pass on live, fail on the candidate (answered without ['45', '60'])" in CO, CO
assert "jn-09: pass on live, fail on the candidate" in CO and "3 row(s) changed verdict" in CO and "FAIL" not in CO, CO

# ------------------------------------------------------------------ step 6: the pairwise judge (the verdict), and the rupee delta
CELLS["judge"] = 'make judge PROJECT="$PROJECT" PY="$HOME/judge-venv/bin/python" API_B="$CAND"'
judged = main_of("evals/judge.py", ["judge.py", "--api-url", API, "--project", PROJ, "--api-b", CAND], "2026-09-24T11:05:00+00:00")
STUB_HASH = hashlib.sha256("\n".join(f"{n}: the stand-in's template" for n in ("groundedness", "instruction_following")).encode("utf-8")).hexdigest()[:6]
assert judged.count(STUB_HASH) == 3 and f"(templates {STUB_HASH};" in judged, judged[:600]
judged = (judged.replace(STUB_HASH, "cd7070").replace("api-dev-20260924-1105-vs-candidate", "api-GITSHA-YYYYMMDD-HHMM-vs-candidate"))
judged = re.sub(r" in \d+s \(model", " in ...s (model", judged)
OUT["judge"] = f">> {API}\n" + judged
JU = OUT["judge"]
WIN = {k: float(re.search(rf"pairwise_question_answering_quality/{k}_model_win_rate\s+([\d.]+)", JU).group(1)) for k in ("candidate", "baseline")}
assert "65/65 answers collected" in JU and "65/65 candidate answers from " + CAND in JU and "pointwise: GROUNDEDNESS + INSTRUCTION_FOLLOWING  (templates cd7070" in JU, JU
assert (WIN["candidate"], WIN["baseline"]) == (0.015, 0.031) and "row_count                                        65.000" in JU, (WIN, JU[-1500:])
assert JU.rstrip().endswith("the gate (run_eval.py) still decides; this judge explains. Where they disagree, read the row."), JU[-300:]
N_CWIN, N_BWIN = round(WIN["candidate"] * len(GOLDEN)), round(WIN["baseline"] * len(GOLDEN))
assert (N_CWIN, N_BWIN) == (1, 2)                     # jn-06 to the candidate; jn-03 and jn-09 to the baseline; the rest ties
# the usage rows those four runs left: 65 answers from each revision in each gate, 65 in each judge collection, priced by cost.price()
rnd = random.Random(173)
NOW_DELTA = datetime.fromisoformat("2026-09-24T11:40:00+00:00")
entries = []
for rev, model, base in (("live", "gemini-3.6-flash", "gemini-3.6-flash"), ("cand", ENDPOINT, "gemini-3.1-flash-lite")):
    for run_no in range(2):
        for g in GOLDEN:
            tin = max(900, int(rnd.gauss(7400, 900)))
            tout = max(40, int(rnd.gauss(210 if rev == "live" else 140, 50)))
            at = NOW_DELTA - timedelta(minutes=rnd.randint(5, 100))
            entries.append({"timestamp": at.isoformat().replace("+00:00", "Z"), "jsonPayload": {
                "event": "query", "tenant": g["tenant"], "user": "documind-ui-sa", "tokens_in": tin, "tokens_out": tout, "cached_tokens": 0,
                "cost_usd": kit_price(model, tin, tout, base)["usd"], "latency_ms": 2100 if rev == "live" else 1000,
                "answerable": True, "model": model, "model_backend": "vertex", "unanswerable_flag": 0, "event_rev": rev}})
(T / "logs.json").write_text(json.dumps({"entries": entries}), encoding="utf-8")
DELTA_PY = """import os, sys
sys.path.insert(0, "evals")
from usage_rows import group, read_rows
EP, TUNED = os.environ["ENDPOINT"], 1.5      # Google's pricing page: a tuned Gemini 3 endpoint answers at 1.5 x its base
per = {g["model"]: g for g in group(read_rows(os.environ["PROJECT"], 2), ("model",))}
live, cand = per["gemini-3.6-flash"], per[EP]
a, logged = live["inr"] / live["answers"], cand["inr"] / cand["answers"]
print(f"  live       {live['answers']:4} answers  Rs {a:.4f} an answer")
print(f"  candidate  {cand['answers']:4} answers  Rs {logged:.4f} an answer as logged, Rs {logged * TUNED:.4f} as Google bills it")
d = a - logged * TUNED
print(f"the rupee delta: the tuned endpoint costs Rs {d:.4f} less an answer, Rs {d * 1000:,.0f} per 1,000 answers")
print(f"  (the usage rows alone say Rs {a - logged:.4f}: they log the endpoint at its base's rate)")"""
CELLS["delta"] = ("make usage PROJECT=\"$PROJECT\" HOURS=2 | sed -n '/^by model and backend/,/^$/p'\n"
                  "python - <<'PY'\n" + DELTA_PY + "\nPY")
usage = main_of("evals/usage_rows.py", ["usage_rows.py", "--project", PROJ, "--hours", "2"], "2026-09-24T11:40:00+00:00")
ul = usage.split("\n")
start = next(i for i, line in enumerate(ul) if line.startswith("by model and backend"))
end = next(i for i in range(start + 1, len(ul)) if ul[i] == "")
OUT["delta"] = "\n".join(ul[start:end + 1]) + "\n" + run([sys.executable, "-"], LANE + DELTA_PY, {"LANE173_NOW": "2026-09-24T11:40:00+00:00"})
DE = OUT["delta"]
assert "\nprojects/NUMBER/loca  vertex" in DE and "gemini-3.6-flash      vertex" in DE and "  live        130 answers" in DE, DE
DELTA = re.search(r"the rupee delta: the tuned endpoint costs Rs ([\d.]+) less an answer, Rs ([\d,]+) per 1,000 answers", DE).groups()
LIVE_EACH, LOGGED, BILLED = re.search(r"live +130 answers +Rs ([\d.]+) an answer\n  candidate +130 answers +Rs ([\d.]+) an answer as logged, Rs ([\d.]+) as Google bills it", DE).groups()
CELLS["cleanup"] = ('gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate\n'
                    'rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag\n'
                    'curl -s -o /dev/null -w "the candidate URL now: HTTP %{http_code}\\n" -H "Authorization: Bearer $(tok "$API")" "$CAND/health"')
OUT["cleanup"] = "...\nthe candidate URL now: HTTP 404\n"

# ------------------------------------------------------------------ step 7 (optional): v3's endpoint on the candidate, and the gate on it
ENDPOINT_V3 = "projects/NUMBER/locations/us/endpoints/3784707595493887459"       # lesson 12.2's step 7 stand-in endpoint (its build prints it)
os.environ["LANE173_ENDPOINT_V3"] = ENV["LANE173_ENDPOINT_V3"] = ENDPOINT_V3
CELLS["cand3"] = ("export ENDPOINT_V3=\"${ENDPOINT_V3:-$(grep -o 'projects/[^ ]*/endpoints/[0-9]*' ~/poll172v3.log | head -1)}\"     # lesson 12.2's step 7\n"
                  'make candidate PROJECT="$PROJECT" GENERATOR_MODEL="$ENDPOINT_V3" RAG_MODEL_BASE=gemini-3.1-flash-lite\n'
                  'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"')
ECHO3 = ECHO.replace(f"GENERATOR_MODEL={ENDPOINT}|", f"GENERATOR_MODEL={ENDPOINT_V3}|")
assert ECHO3 != ECHO and ENDPOINT not in ECHO3
OUT["cand3"] = (ECHO3 + "\n...\n"
                f">> candidate revision: documind-api-000NN-zzz (deploy/.candidate-revision - make promote moves traffic to it by name)\n"
                f">> candidate: {CAND} (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)\n"
                f"CAND={CAND}\n")
os.environ["LANE173_CANDIDATE"] = "v3"
GATE3_OUT = gate(CAND, "cand173v3.json")
os.environ.pop("LANE173_CANDIDATE")
CELLS["gate3"] = 'make eval-live PROJECT="$PROJECT" API="$CAND" REPORT="$HOME/cand173v3.json"'
OUT["gate3"] = GATE3_OUT
C3 = json.loads((HOME / "cand173v3.json").read_text(encoding="utf-8"))
assert GATE3_OUT.rstrip().endswith("All thresholds met.") and "rows that cost a point (3):" in GATE3_OUT, GATE3_OUT[-900:]
assert {r["id"] for r in C3["records"] if not r["pass"]} == {r["id"] for r in CANDR["records"] if not r["pass"]} == {"jn-03", "jn-09", "lk-27"}
assert "| '**answer:** 45 days." in GATE3_OUT and "**why:** at most 45 days" in GATE3_OUT, GATE3_OUT[-900:]   # run_eval prints it normalised                        # the house style, in the rows that cost a point

# ------------------------------------------------------------------ step 8 (optional): one question, two models
DEMO_PY = """import ast, json, os, re, subprocess, sys
sys.path[:0] = ["evals"]
from run_eval import ask                         # the gate's own client: POST /v1/query, the call the UI's API receives
P, R, API = os.environ["PROJECT"], os.environ["REGION"], os.environ["API"]
CAND = os.environ.get("CAND") or f"https://candidate---documind-api-{os.environ['NUMBER']}.{R}.run.app"
SA = f"documind-ui-sa@{P}.iam.gserviceaccount.com"
token = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}", f"--impersonate-service-account={SA}"],
                       capture_output=True, text=True, check=True).stdout.strip()
mine = os.path.expanduser("~/demo_questions.txt")                      # your own questions, one a line, asked instead
QUESTIONS = [q.strip() for q in open(mine, encoding="utf-8") if q.strip()] if os.path.exists(mine) else [
    "Can unused leave shorten my notice period?",                             # golden jn-02: in neither training file
    "Kya main apni bachi hui leave se notice period chhota kar sakta hoon?",  # the same question, in Hinglish
    "How much is ACME's referral bonus?"]                                      # the handbook names it, and never says
tree = ast.parse(open("services/rag-api/cost.py", encoding="utf-8").read())
PRICE = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "FALLBACK")
for q in QUESTIONS:
    print(f"\\nQ: {q}")
    for name, url in (("live, as the UI answers", API), ("tuned candidate", CAND)):
        status, body, ms = ask(url, q, "acme", SA, token)
        if status != 200:
            print(f"  {name}: HTTP {status}")
            continue
        tuned = body["model"].startswith("projects/")
        usd_in, usd_out = PRICE["gemini-3.1-flash-lite" if tuned else "gemini-3.6-flash"]
        rs = (body["tokens_in"] * usd_in + body["tokens_out"] * usd_out) * (1.5 if tuned else 1.0) / 1e6 * 85   # a tuned endpoint: 1.5 x
        marks = len(re.findall(r"\\[(\\d+(?:\\s*,\\s*\\d+)*)\\]", body["answer"]))
        model = "endpoint " + body["model"].rsplit("/", 1)[1] if tuned else body["model"]
        print(f"  {name} ({model}): {len(body['citations'])} citation(s), {marks} [N] mark(s), {ms} ms, about Rs {rs:.2f}")
        print("    " + body["answer"].replace("\\n", "\\n    "))
svc = json.loads(subprocess.run(["gcloud", "run", "services", "describe", "documind-api", "--region", R, "--project", P, "--format=json"],
                                capture_output=True, text=True, check=True).stdout)
live = max((t for t in svc["status"]["traffic"] if t.get("percent")), key=lambda t: t["percent"])
print(f"\\nthe UI's URL sends {live['percent']}% of its traffic to {live['revisionName']}; the candidate answers only at its own URL")"""
CELLS["demo"] = "python - <<'PY'\n" + DEMO_PY + "\nPY"
OUT["demo"] = run([sys.executable, "-"], LANE + DEMO_PY, {"LANE173_NOW": "2026-09-27T11:10:00+00:00", "LANE173_CANDIDATE": "v3", "LANE173_DEMO": "1",
                                                         "API": API, "CAND": CAND, "NUMBER": "NUMBER"})
DM = OUT["demo"]
EP3 = ENDPOINT_V3.rsplit("/", 1)[1]
assert DM.count("  live, as the UI answers (gemini-3.6-flash): ") == 3 and DM.count(f"  tuned candidate (endpoint {EP3}): ") == 3, DM
assert "(gemini-3.6-flash): 2 citation(s), 2 [N] mark(s), 2100 ms" in DM and f"(endpoint {EP3}): 1 citation(s), 1 [N] mark(s), 1000 ms" in DM, DM
assert "    **Answer:** No.\n    **Why:** Unused earned leave may not be set off against the notice period [1].\n    **Clause:** NP-03, hr_policy_2026.md" in DM, DM
assert "    **Answer:** Nahi.\n" in DM and "    **Answer:** Not in the documents.\n" in DM and "0 citation(s), 0 [N] mark(s)" in DM, DM
assert f"the UI's URL sends 100% of its traffic to {REVS[0]}; the candidate answers only at its own URL" in DM, DM
DEMO_RS = [float(x) for x in re.findall(r"about Rs ([\d.]+)", DM)]
LIVE_RS, CAND_RS = DEMO_RS[0], DEMO_RS[1]
assert 3 < LIVE_RS / CAND_RS < 6 and sum(DEMO_RS) < 10, DEMO_RS                     # about a quarter, at Google's 1.5 times; a few rupees in all
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ the panel: make candidate's settings, the contamination, cost.price()
LIVE_PANEL = {k: DEFAULTS[v] for k, v in PAIRS}
TOK = {"live": (7400, 210), "cand": (7400, 140)}
DROPPED = M2["dropped_golden_ids"]
CASES = []
for base in ("gemini-3.1-flash-lite", ""):
    for cache_live in ("off", "on"):
        for cache_cand in ("off", "on"):
            for loc in ("", "us-central1", "us"):
                CASES.append([base, cache_live, cache_cand, loc])


def py_case(base, cache_live, cache_cand, loc):
    live = {**LIVE_PANEL, "SEMANTIC_CACHE": cache_live}
    over = {"GENERATOR_MODEL": ENDPOINT, "SEMANTIC_CACHE": cache_cand, **({"RAG_MODEL_BASE": base} if base else {}), **({"GENERATOR_LOCATION": loc} if loc else {})}
    cand = candidate_env(live, over)
    diff = sorted(k for k in live.keys() | cand.keys() if live.get(k) != cand.get(k))
    logged = kit_price(ENDPOINT, *TOK["cand"], cand["RAG_MODEL_BASE"])["inr"]
    return {"diff": [[k, live.get(k, "(unset)"), cand.get(k, "(unset)")] for k in diff], "logged": logged,
            "live": kit_price("gemini-3.6-flash", *TOK["live"], None)["inr"]}


PY_SIDE = [py_case(*c) for c in CASES]
UI_JS = r"""var root = document.getElementById('tc'); if (!root) return;
  var PAIRS = __PAIRS__, DEFAULTS = __DEFAULTS__, PRICES = __PRICES__, EP = __EP__, TOK = __TOK__, DROPPED = __DROPPED__, TUNED = 1.5;
  function candidateEnv(live, over){ var env = {}, k; for (k in live) { env[k] = live[k]; }
    PAIRS.forEach(function(p){ env[p[0]] = over.hasOwnProperty(p[1]) ? over[p[1]] : DEFAULTS[p[1]]; });
    if (over.GENERATOR_LOCATION) { env.GENERATOR_LOCATION = over.GENERATOR_LOCATION; } else { delete env.GENERATOR_LOCATION; } return env; }
  function price(model, tin, tout, base){ if (model.indexOf('projects/') === 0) { model = base || 'gemini-3.6-flash'; }
    var p = PRICES[model] || PRICES['gemini-3.6-flash'], usd = (tin * p[0] + tout * p[1]) / 1e6;
    return Math.round(usd * 1e6) / 1e6 * 85; }
  function r4(x){ return Math.round(x * 1e4) / 1e4; }
  function caseOf(base, cacheLive, cacheCand, loc){ var live = {}; PAIRS.forEach(function(p){ live[p[0]] = DEFAULTS[p[1]]; }); live.SEMANTIC_CACHE = cacheLive;
    var over = {GENERATOR_MODEL: EP, SEMANTIC_CACHE: cacheCand}; if (base) { over.RAG_MODEL_BASE = base; } if (loc) { over.GENERATOR_LOCATION = loc; }
    var cand = candidateEnv(live, over), keys = {}, k, diff = [];
    for (k in live) { keys[k] = 1; } for (k in cand) { keys[k] = 1; }
    Object.keys(keys).sort().forEach(function(key){ if (live[key] !== cand[key]) { diff.push([key, live.hasOwnProperty(key) ? live[key] : '(unset)', cand.hasOwnProperty(key) ? cand[key] : '(unset)']); } });
    return {diff: diff, logged: r4(price(EP, TOK.cand[0], TOK.cand[1], cand.RAG_MODEL_BASE)), live: r4(price('gemini-3.6-flash', TOK.live[0], TOK.live[1], null))}; }
  window.__tc = {caseOf: caseOf};
  var $ = function(id){ return document.getElementById(id); };
  function line(out, cls, text){ var d = document.createElement('div'); if (cls) { d.className = cls; } d.textContent = text; out.appendChild(d); }
  function show(){ var base = $('tc-base').value, cl = $('tc-cl').value, cc = $('tc-cc').value, loc = $('tc-loc').value, file = $('tc-file').value, vol = Number($('tc-vol').value);
    var r = caseOf(base, cl, cc, loc), out = $('tc-audit'), money = $('tc-money'), names = r.diff.map(function(d){ return d[0]; }), bad = 0;
    out.textContent = ''; money.textContent = '';
    line(out, '', r.diff.length + ' settings differ between the live revision and the candidate:');
    r.diff.forEach(function(d){ line(out, 'mono', d[0] + '  ' + d[1] + ' \u2192 ' + d[2]); });
    var extra = names.filter(function(n){ return n !== 'GENERATOR_MODEL' && n !== 'RAG_MODEL_BASE'; });
    if (extra.length) { bad++; line(out, 'stop', 'Not one change: ' + extra.join(', ') + ' moved with the model.'); }
    if (names.indexOf('RAG_MODEL_BASE') < 0) { bad++; line(out, 'stop', 'RAG_MODEL_BASE stayed gemini-3.6-flash: the usage rows price the tuned endpoint at the served model\u2019s rates.'); }
    if (cc === 'on') { bad++; line(out, 'stop', 'The candidate reads the answer cache, whose test never reads the model: a golden question asked in the last 24 hours gets gemini-3.6-flash\u2019s stored answer, scored as the tuned model\u2019s.'); }
    if (cl === 'on' && cc !== 'on') { line(out, 'stop', 'The live revision reads the answer cache: some baseline answers are stored ones, not answers of this hour.'); }
    if (loc && loc !== 'us') { bad++; line(out, 'stop', 'GENERATOR_LOCATION=' + loc + ': the endpoint answers only from us, so every candidate row is a 404.'); }
    if (file === 'raw') { bad++; line(out, 'stop', 'Without exclude_golden, the file keeps the rows it dropped, written from the evidence or the questions of golden rows ' + DROPPED.join(', ') + ': on those rows the gate measures memory.'); }
    if (!bad) { line(out, 'pass', 'Uncontaminated: one change, the model with its price base, and a test the training never saw.'); }
    var google = r4(price(EP, TOK.cand[0], TOK.cand[1], 'gemini-3.1-flash-lite') * TUNED);
    line(money, '', 'The live revision: Rs ' + r.live.toFixed(4) + ' an answer.');
    line(money, '', 'The candidate, as its usage rows log it: Rs ' + r.logged.toFixed(4) + ' an answer.');
    line(money, '', 'The candidate, as Google bills a tuned endpoint (1.5 \u00d7 flash-lite): Rs ' + google.toFixed(4) + ' an answer.');
    var dl = r.live - r.logged, dg = r.live - google;
    line(money, 'pass', 'The rupee delta: Rs ' + dg.toFixed(4) + ' an answer, Rs ' + Math.round(dg * vol).toLocaleString('en-US') + ' for ' + vol.toLocaleString('en-US') + ' answers.');
    line(money, (Math.abs(dl - dg) > 0.00005 ? 'stop' : ''), 'By the usage rows alone: Rs ' + dl.toFixed(4) + ' an answer, Rs ' + Math.round(dl * vol).toLocaleString('en-US') + ' for ' + vol.toLocaleString('en-US') + '.'); }
  ['tc-base', 'tc-cl', 'tc-cc', 'tc-loc', 'tc-file', 'tc-vol'].forEach(function(id){ $(id).addEventListener('change', show); });
  show();"""
UI_JS = (UI_JS.replace("__PAIRS__", json.dumps([list(p) for p in PAIRS])).replace("__DEFAULTS__", json.dumps(DEFAULTS))
         .replace("__PRICES__", json.dumps({k: list(v) for k, v in FALLBACK.items()})).replace("__EP__", json.dumps(ENDPOINT))
         .replace("__TOK__", json.dumps(TOK)).replace("__DROPPED__", json.dumps(DROPPED)))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
PORT_JS = UI_JS.split("var $ = function(id)")[0].replace("var root = document.getElementById('tc'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var C = " + json.dumps(CASES) + ";\n"
        "process.stdout.write(JSON.stringify(C.map(function(c){ return window.__tc.caseOf(c[0], c[1], c[2], c[3]); })));\n")
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
    "checks": "run in the operator shell, in the kit (the kit's own functions; no network)",
    "candidate": "run in the operator shell, in the kit (a revision with no traffic; nothing is billed until it answers)",
    "audit": "run in the operator shell, in the kit (reads both revisions, ~/tune172.log, the bucket and Firestore)",
    "gates": "run in the operator shell, in the kit (every golden row, on each revision: about twenty minutes)",
    "compare": "run in the operator shell, in the kit (reads the two reports)",
    "judge": "run in the operator shell, in the kit (the judge's venv from lesson 4.2: 65 answers from each revision, then Vertex AI Evaluation)",
    "delta": "run in the operator shell, in the kit (reads the last two hours of usage rows)",
    "cleanup": "run in the operator shell, in the kit (removes the candidate's address; the revision stays, with no traffic)",
    "cand3": "optional: run in the operator shell, in the kit (v3's endpoint behind the candidate address; still no traffic)",
    "gate3": "optional: run in the operator shell, in the kit (every golden row on the v3 candidate: about ten minutes)",
    "demo": "optional: run in the operator shell, in the kit (three questions on each revision; ask again as often as you like)",
}
OUT_LABELS = {
    "checks": "(the kit's own functions)",
    "candidate": "(the echo is the kit's recipe with this page's values; gcloud's own progress lines are left out, and your revision's name differs)",
    "audit": "(this cell over the stand-in lane: two revisions' settings, the v2 lesson 12.1's stand-in built, no context cache)",
    "gates": "(run_eval.py's own code over two stand-in revisions: the candidate misses a figure on two joins and states jn-06's; your rows and times are your lane's)",
    "compare": "(this cell over the two reports above)",
    "judge": "(judge.py's own code over a stand-in Evaluation service that chooses by each row's must_contain phrases; the template hash is SDK 2.1.0's, as in lesson 4.2; your judge is Gemini, and your rates are your lane's)",
    "delta": "(make usage and this cell over the usage rows those runs leave, priced by the kit's own cost.price(); your rupees are your lane's)",
    "cleanup": "(the removal's own output is left out)",
    "cand3": "(the echo is the kit's recipe with lesson 12.2's step 7 endpoint; gcloud's progress lines are left out, and your revision's name differs)",
    "gate3": "(run_eval.py's own code over the stand-in v3 candidate: the house style, and the v2 candidate's misses; your rows are your lane's)",
    "demo": "(this cell over the stand-in revisions: the live answers as gemini-3.6-flash writes them, the candidate's as v3's rows teach; your answers are the models' own)",
}
WIN_ = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN_.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
opts = lambda pairs, sel: "".join(f'<option value="{html.escape(str(v))}"{" selected" if v == sel else ""}>{html.escape(t)}</option>' for v, t in pairs)  # noqa: E731
STATS = {"N_CHECKED": str(N_CHECKED), "N_GOLD": str(len(GOLDEN)), "WIN_C": f"{WIN['candidate']:.3f}", "WIN_B": f"{WIN['baseline']:.3f}",
         "DELTA_EACH": DELTA[0], "DELTA_1K": DELTA[1], "LIVE_EACH": LIVE_EACH, "LOGGED": LOGGED, "BILLED": BILLED,
         "N_DROP": str(M2["dropped_golden_overlap"]), "DROPPED_IDS": ", ".join(DROPPED), "N_DROPPED_IDS": str(len(DROPPED)),
         "EX_LITE": f"{EX['lite']:.4f}", "EX_FLASH": f"{EX['flash']:.4f}", "EX_GOOGLE": f"{1.5 * EX['lite']:.4f}",
         "N_CWIN": str(N_CWIN), "N_BWIN": str(N_BWIN), "N_TIE": str(len(GOLDEN) - N_CWIN - N_BWIN), "N_ANSWERS": str(4 * len(GOLDEN)),
         "GATE_LIVE": f"{len(GOLDEN) * float(LIVE_EACH):,.0f}", "GATE_CAND": f"{len(GOLDEN) * float(BILLED):,.0f}",
         "DEMO_LIVE_RS": f"{LIVE_RS:.2f}", "DEMO_CAND_RS": f"{CAND_RS:.2f}", "DEMO_ALL_RS": f"{sum(DEMO_RS):.0f}",
         "BASE_OPTIONS": opts([("gemini-3.1-flash-lite", "gemini-3.1-flash-lite (step 4's)"), ("", "left out: the Makefile's gemini-3.6-flash")], "gemini-3.1-flash-lite"),
         "CL_OPTIONS": opts([("off", "off (the lane's)"), ("on", "on")], "off"),
         "CC_OPTIONS": opts([("off", "off (the Makefile's)"), ("on", "on")], "off"),
         "LOC_OPTIONS": opts([("", "unset (step 4's)"), ("us-central1", "us-central1"), ("us", "us")], ""),
         "FILE_OPTIONS": opts([("v2", "v2, built with exclude_golden"), ("raw", "the same rows without exclude_golden")], "v2"),
         "VOL_OPTIONS": opts([(1000, "1,000"), (10000, "10,000"), (100000, "100,000")], 10000)}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print({k: v for k, v in STATS.items() if not k.endswith("_OPTIONS")})
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN_, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: run_eval.live() on both revisions, judge.py main() pairwise, usage_rows.py and cost.price() | verdict {WIN['candidate']:.3f} "
      f"vs {WIN['baseline']:.3f}, delta Rs {DELTA[0]} an answer | panel checked against make candidate's settings and cost.price() on {N_CHECKED} cases")
