"""Build lesson 9.2 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Serve a supplied or stock model using Ollama. make deploy-slm serves one model under one name, documind-slm, from
either of two builds: a supplied model (a GGUF and the Modelfile generated from its tokenizer, from the datasets
bucket) or a stock model from Ollama's library (SLM_STOCK), the stand-in. The model is created when the image is built;
the service runs on one Cloud Run L4, scales to zero, and is billed by the instance. The gateway's two self-hosted
routes point at it, and the API reaches it with MODEL_BACKEND=gateway and GENERATOR_MODEL=documind-slm.
Offline: a Modelfile generated from a Gemma 4 tokenizer; the waits along a request's path and the GPU's bill, read from
the kit. Live: make deploy-slm SLM_STOCK=gemma3:4b and make smoke-slm; the cold start timed; lesson 9.1's PAN
answered by the sensitive route; the small model behind a candidate revision, one answer and the scoped gate; cleanup.

Build-time proof: make_modelfile.py ran on unsloth/gemma-4-E2B-it's tokenizer under transformers 5 (TF5_PY: a Python
with the cell's transformers pin and jinja2; the tokenizer files come from the Hugging Face cache, HF_HOME), and failed
under the kit's own pin (TF457_PY: a Python with services/slm/requirements.txt plus jinja2, protobuf and sentencepiece).
make smoke-slm and every live cell ran the kit's own code against a stand-in lane (lane182.py, beside this file): an
Ollama that starts cold, lesson 9.1's gateway with the kit's own hook under the real Presidio (PRESIDIO_PY) and the
backend deployed, and a candidate revision answering the golden rows; run_eval.py judged it over HTTP. The panel is a
port of the waits along a request's path, compared with a Python version on every combination it offers.

    PRESIDIO_PY=... TF5_PY=... TF457_PY=... python lessons/09-serving/9.2-ollama-slm/build.py
"""
import html
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "9.2"
title = "<title>Lesson 9.2 Serve a supplied or stock model using Ollama - one name for two builds, a GPU that sleeps, a cold start timed, an answer gated | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
REGION = "asia-south1"
SLM = "https://documind-slm-NUMBER.us-central1.run.app"
GATEWAY = f"https://documind-gateway-NUMBER.{REGION}.run.app"
API = f"https://documind-api-NUMBER.{REGION}.run.app"
CAND = f"https://candidate---documind-api-NUMBER.{REGION}.run.app"
SL, LL = "services/slm", "services/litellm"
DOCKER, MKMF, REQ, SMOKE, CFG, GEN, APICFG, EVAL, RTR, CLS, SCHEMAS = (
    f"{SL}/Dockerfile", f"{SL}/make_modelfile.py", f"{SL}/requirements.txt", "smoke/smoke_slm.py", f"{LL}/config.yaml",
    "services/rag-api/generator.py", "services/rag-api/config.py", "evals/run_eval.py", f"{LL}/documind_router.py",
    f"{LL}/documind_classifier.py", "services/rag-api/schemas.py")
PRESIDIO_PY, TF5_PY, TF457_PY = (os.environ.get(k, "") for k in ("PRESIDIO_PY", "TF5_PY", "TF457_PY"))
assert PRESIDIO_PY and Path(PRESIDIO_PY).exists(), "set PRESIDIO_PY to a Python with the gateway image's presidio pins and en_core_web_lg"
assert TF5_PY and Path(TF5_PY).exists(), "set TF5_PY to a Python with the step 3 cell's transformers pin and jinja2"
assert TF457_PY and Path(TF457_PY).exists(), "set TF457_PY to a Python with services/slm/requirements.txt, jinja2, protobuf and sentencepiece"
HF_HOME = os.environ.get("HF_HOME") or os.path.join(os.path.expanduser("~"), ".cache", "huggingface")
TUNED_FROM = "unsloth/gemma-4-E2B-it"
TF_PIN = "5.17.0"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.sl-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:0 10px;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,140px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.sl-out{margin:6px 0 0;font-size:12.5px;line-height:1.6;}
.sl-out div{margin:0 0 4px;}
.sl-out .pass{color:var(--teal-dark);font-weight:600;}
.sl-out .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()


# ------------------------------------------------------------------ verbatim excerpts
def span(rel: str, start: str, last: str) -> int:
    lines = (KIT / rel).read_text(encoding="utf-8").split("\n")
    i = next(k for k, line in enumerate(lines) if line.startswith(start))
    return next(k for k in range(i, len(lines)) if lines[k].startswith(last)) - i + 1


EXCERPTS = {
    "render": ("services/slm/make_modelfile.py - the template and the stops, from the tokenizer",
               block(MKMF, "    # Ollama's TEMPLATE is Go templating", n=span(MKMF, "    # Ollama's TEMPLATE is Go templating", "    stops = list(dict.fromkeys(stops))"))),
    "image": ("services/slm/Dockerfile - two builds, one name, created when the image is built",
              block(DOCKER, "# Two builds, one image name", n=span(DOCKER, "# Two builds, one image name", "    pkill ollama"))),
    "deploy": ("Makefile - make deploy-slm: the build staged, then one L4 behind IAM",
               block("Makefile", "deploy-slm: guard-project", n=span("Makefile", "deploy-slm: guard-project", "	  --startup-probe"))),
    "route": ("services/litellm/config.yaml - the gateway's route to the small model",
              block(CFG, "  - model_name: documind-slm", n=8)),
    "gwwait": ("services/rag-api/config.py - how long the API waits for the gateway",
               block(APICFG, 'gateway_timeout_s: float = Field(', n=1)),
    "smokegw": ("smoke/smoke_slm.py - the gateway check",
                block(SMOKE, "    if GATEWAY:", n=6)),
    "messages": ("services/rag-api/generator.py - what the API sends the gateway: its rules as the system turn",
                 block(GEN, "def _gateway_messages(prompt: str) -> list[dict]:", n=5)),
    "named": ("services/rag-api/generator.py - generate(): the answer carries the route it asked for",
              block(GEN, "    return RAGResponse(", n=7)),
}
assert EXCERPTS["render"][1].rstrip().endswith("stops = list(dict.fromkeys(stops))") and 'rendered.replace("__PROMPT__", "{{ .Prompt }}")' in EXCERPTS["render"][1]
assert EXCERPTS["image"][1].rstrip().endswith("pkill ollama") and 'ollama cp "$(cat /build/STOCK)" documind-slm' in EXCERPTS["image"][1]
assert "importing a 2 GB GGUF is time a cold start does not have." in EXCERPTS["image"][1]
assert EXCERPTS["deploy"][1].rstrip().endswith("failureThreshold=30 --quiet") and "--gpu 1 --gpu-type nvidia-l4 --no-gpu-zonal-redundancy" in EXCERPTS["deploy"][1]
assert EXCERPTS["route"][1].rstrip().endswith("output_cost_per_token: 0.0000205") and 'tags: ["residency-in", "tuned"]' in EXCERPTS["route"][1]
assert "timeout: 110                                  # a cold GPU is 30-60 s away; the API waits 90" in EXCERPTS["route"][1]
assert EXCERPTS["gwwait"][1].strip().startswith('gateway_timeout_s: float = Field(90.0, alias="GATEWAY_TIMEOUT_S")')
assert EXCERPTS["smokegw"][1].rstrip().endswith('served by {served!r} in {secs:.1f}s")') and "(ok if status == 200 else bad)" in EXCERPTS["smokegw"][1]
assert EXCERPTS["messages"][1].rstrip().endswith('return [{"role": "system", "content": SYSTEM + GATEWAY_JSON_RULE}, {"role": "user", "content": user}]')
assert EXCERPTS["named"][1].rstrip().endswith(")") and "        model=model," in EXCERPTS["named"][1] and "        backend=backend," in EXCERPTS["named"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (DOCKER, MKMF, REQ, SMOKE, CFG, GEN, APICFG, EVAL, RTR, CLS, SCHEMAS,
                                                          "Makefile", f"{SL}/Modelfile", "commands/lesson-12.2.sh")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
flat = lambda s: re.sub(r"\s+", " ", s)  # noqa: E731
flatc = lambda s: flat(re.sub(r"\n\s*#\s*", " ", s))  # noqa: E731 - a comment's lines as one sentence
assert "FROM ollama/ollama:0.33.3" in src[DOCKER] and "gemma4 support arrived in the 0.33.x line" in flatc(src[DOCKER])
assert "An older Ollama loads the GGUF and produces nonsense rather than refusing" in flatc(src[DOCKER]) and "10.5 fine-tunes unsloth/gemma-4-E2B-it" in flatc(src[DOCKER])
assert "a template that disagrees with the checkpoint produces fluent text that never stops" in flatc(src[DOCKER])
assert "ENV OLLAMA_HOST=0.0.0.0:8080" in src[DOCKER] and "OLLAMA_KEEP_ALIVE" not in src[DOCKER] and "KEEP_ALIVE" not in MK
DEPLOY = MK[MK.index("\ndeploy-slm: guard-project\n") + 1:].split("\n\n", 1)[0]
assert "--cpu 8 --memory 32Gi" in DEPLOY and "--max-instances 1 --min-instances 0 --timeout 600 --concurrency 4" in DEPLOY
assert "--no-allow-unauthenticated --labels slm-source=$(if $(SLM_STOCK),stock,gguf)" in DEPLOY
assert "httpGet.path=/api/tags,httpGet.port=8080,initialDelaySeconds=10,periodSeconds=5,failureThreshold=30" in DEPLOY
assert "for sa in documind-gateway-sa documind-ui-sa; do" in DEPLOY and "gs://$(PROJECT)-datasets/sft/documind-slm.gguf" in DEPLOY
assert 'echo ">> stand-in: $(SLM_STOCK) will be served as documind-slm"' in DEPLOY
assert "SLM_REGION ?= us-central1" in MK and "Cloud Run L4 in asia-south1 is INVITATION-ONLY" in flatc(MK)
assert "asia-south2 (Delhi) has RTX PRO 6000 GA if the data must stay in India, at a different price." in flatc(MK)
assert "it costs Rs 86,904/month if min-instances is left above zero" in flatc(MK) and "$1.42/hr for the whole 8vCPU/32GiB instance" in flatc(MK)
assert "so it is an explicit act and never a side effect of deploying everything else" in flatc(MK)
assert "The startup probe waits for the model, not the process" in flatc(MK)
SLMOFF = MK[MK.index("\nslm-off: guard-project\n") + 1:].split("\n\n", 1)[0]
assert "--min-instances 0 --quiet" in SLMOFF and '@echo "documind-slm scaled to zero"' in SLMOFF
assert not re.search(r"documind-slm[^\n]*--min-instances [1-9]", MK)              # nothing raises it: slm-off sets what deploy-slm set
assert "make candidate MODEL_BACKEND=gateway GENERATOR_MODEL=documind-slm" in MK
assert "LITELLM_URL=https://documind-gateway-$PROJECT_NUMBER.${REGION:-us-central1}.run.app" in src["commands/lesson-12.2.sh"]
assert "MODEL_BACKEND   ?= vertex" in MK and "SLM_STOCK       ?=" in MK
# the stand-in's Ollama facts (the registry's manifest for gemma3:4b, read 24 Sep 2026): 4.3B, Q4_K_M, 3,338,792,448 bytes of weights
STOCK = "gemma3:4b"
# the waits
assert "def call(method: str, url: str, token: str | None, body: dict | None = None, timeout: int = 240):" in src[SMOKE]
assert "with urllib.request.urlopen(req, timeout=90) as r:" in src[EVAL] and "def ask(api_url: str, question: str, tenant: str, email: str, token: str | None, retries: int = 1):" in src[EVAL]
assert "time.sleep(2)" in src[EVAL].split("def ask(", 1)[1].split("def ", 1)[0]
assert src[CFG].count("      timeout: 110") == 4 and "    - documind-slm: [\"documind-general\"]" in src[CFG] and "documind-sensitive:" not in src[CFG].split("fallbacks:", 1)[1].split("num_retries", 1)[0]
assert "TimeoutErrorRetries: 1" in src[CFG] and "A cold GPU means a slow answer, not a leak." in src[CFG]
assert "Self-host cold, scaled to zero or out of quota -> Gemini answers." in src[CFG]
assert 'tags: ["sensitive", "dpdpa"]' in src[CFG]
assert "The self-hosted figure is a RATE, not a price" in flatc(src[CFG])
# the findings
# 1. make_modelfile.py's dependencies: jinja2 is not pinned (asserted with the runs below), transformers 4.57.1 is
REQS = src[REQ].split()
assert REQS == ["httpx==0.28.1", "google-auth==2.57.1", "transformers==4.57.1"], REQS
# 2. the generated template names no .System; the API's rules and JSON shape travel as the system turn - excerpt above
assert "GATEWAY_JSON_RULE = ('\\nReply with JSON only, exactly this shape:" in src[GEN]
# 3. the API names the route: the reply's model is set and never read; generate() returns model=model (the route)
assert "        self.model = j.get(\"model\") or model" in src[GEN] and len(re.findall(r"\.model\b", src[GEN])) == 1
assert "        model = _gateway_route(model)" in src[GEN] and '    if model.startswith("gemini-") or model.startswith("projects/"):' in src[GEN]
assert 'data["model"] = "documind-general"' in src[RTR] and "data = self.mask_pii(data)" in src[RTR]
assert re.search(r'"EMAIL": re\.compile\(', src[CLS]) and re.search(r'"PHONE": re\.compile\(', src[CLS])
assert "gst-cbec@gov.in" in (KIT / "evals/corpus/acme/cgst_act_2017.md").read_text(encoding="utf-8")     # acme's own corpus holds one
assert "gst-cbec@gov.in" not in (KIT / "evals/corpus/acme/hr_policy_2026.md").read_text(encoding="utf-8") and "@" not in (KIT / "evals/corpus/acme/hr_policy_2026.md").read_text(encoding="utf-8")
assert "cost_usd: Optional[float] = None" in src[SCHEMAS]
# 4. the API gives up before the gateway: 90 s against 110 - asserted above
# 5. the smoke's gateway check passes on any 200 - asserted on the excerpt above
# 6. no keep-alive: asserted above (the Dockerfile sets no OLLAMA_KEEP_ALIVE; Ollama's default is 5 minutes)
# 7. no temperature on the gateway path: right for Gemini 3, and a small model samples at its own default
assert '"temperature"' not in src[GEN].split("def _gateway_call(", 1)[1].split("def _gateway_stream(", 1)[0]
assert "NO temperature / top_p / top_k: gemini-3.6-flash ignores all" in src[GEN]
# the placeholder Modelfile: no build reads it (the image copies build/ only)
assert "COPY build/ /build/" in src[DOCKER] and "COPY Modelfile" not in src[DOCKER] and "End every answer with a citation in the form [doc:chunk_id]." in src[f"{SL}/Modelfile"]

# ------------------------------------------------------------------ step 3: a Modelfile from the tokenizer (offline)
T = Path(tempfile.mkdtemp(prefix="lesson182-"))
K2 = T / "kit"
for part in ("services/litellm", "services/slm", "services/rag-api", "smoke", "evals"):
    shutil.copytree(KIT / part, K2 / part, ignore=shutil.ignore_patterns("__pycache__", "build"))
shutil.copy(KIT / "Makefile", K2 / "Makefile")
shutil.copy(HERE / "lane182.py", T / "lane182.py")
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "NUMBER": "NUMBER",
       "REGION": REGION, "HOME": str(T), "USERPROFILE": str(T), "PYTHONPATH": str(T)}
TF_ENV = {"HF_HOME": HF_HOME, "HF_HUB_OFFLINE": "1", "HF_HUB_DISABLE_PROGRESS_BARS": "1"}


def run(py: str, code: str, cwd: Path, env: dict | None = None) -> str:
    r = subprocess.run([py, "-"], input=code, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


def modelfile(py: str) -> subprocess.CompletedProcess:
    return subprocess.run([py, "make_modelfile.py", "--model", TUNED_FROM, "--gguf", "documind-slm.gguf"], cwd=str(K2 / SL),
                          capture_output=True, text=True, encoding="utf-8", env={**ENV, **TF_ENV})


ver5 = run(TF5_PY, "import importlib.metadata as m\nprint(m.version('transformers'), m.version('jinja2'))\n"
           "print(any('jinja2' in r.lower() and 'extra' not in r for r in m.requires('transformers') or []))", T).split()
assert ver5[0] == TF_PIN and ver5[2] == "False", ver5                     # jinja2 is an extra of transformers, never a dependency
jinja_msg = run(TF5_PY, "import importlib.metadata as m\nf = next(f for f in m.files('transformers') if str(f).endswith('utils/chat_template_utils.py'))\n"
                "print('apply_chat_template requires jinja2 to be installed' in f.read_text(encoding='utf-8'))", T).strip()   # read, not imported
assert jinja_msg == "True"
mf = modelfile(TF5_PY)
assert mf.returncode == 0, mf.stderr[-2000:]
MODELFILE = mf.stdout
MF_WARN = [line for line in mf.stderr.splitlines() if line.strip()]
assert MF_WARN == ["[transformers] PyTorch was not found. Models won't be available and only tokenizers, configuration and file/data utilities can be used."], MF_WARN
assert "TEMPLATE \"\"\"<bos><|turn>user\n{{ .Prompt }}<turn|>\n<|turn>model\n\"\"\"" in MODELFILE and 'PARAMETER stop "<turn|>"' in MODELFILE, MODELFILE
assert "FROM ./documind-slm.gguf" in MODELFILE and "PARAMETER num_ctx 4096" in MODELFILE and ".System" not in MODELFILE and "SYSTEM" not in MODELFILE
old = modelfile(TF457_PY)
ver457 = run(TF457_PY, "import importlib.metadata as m\nprint(m.version('transformers'), m.version('jinja2'), m.version('protobuf'), m.version('sentencepiece'))", T).split()
assert ver457[0] == "4.57.1" and old.returncode != 0 and "AttributeError: 'list' object has no attribute 'keys'" in old.stderr, (ver457, old.stderr[-800:])
CELLS = {"tfvenv": f'python3 -m venv ~/tf-venv && ~/tf-venv/bin/pip install -q "transformers=={TF_PIN}" jinja2   # not the kit\'s pin: see below',
         "modelfile": (f"cd services/slm && HF_HUB_DISABLE_PROGRESS_BARS=1 ~/tf-venv/bin/python make_modelfile.py --model {TUNED_FROM} "
                       "--gguf documind-slm.gguf > ~/Modelfile.182\ncd ../.. && cat ~/Modelfile.182")}
OUT = {"tfvenv": "", "modelfile": "\n".join(MF_WARN) + "\n" + MODELFILE}

# ------------------------------------------------------------------ step 4: the waits along a request's path, and the bill (offline)
WAITS_PY = r'''import re
mk, cfg, api, ev, sm = (open(p, encoding="utf-8").read() for p in ("Makefile", "services/litellm/config.yaml",
                        "services/rag-api/config.py", "evals/run_eval.py", "smoke/smoke_slm.py"))
deploy = mk.split("\ndeploy-slm:", 1)[1].split("\n\n", 1)[0]
flag = dict(re.findall(r"--([a-z-]+) (\S+)", deploy))
d, p, f = (int(x) for x in re.search(r"initialDelaySeconds=(\d+),periodSeconds=(\d+),failureThreshold=(\d+)", deploy).groups())
smoke = re.search(r"timeout: int = (\d+)", sm).group(1)
row = re.search(r"urlopen\(req, timeout=(\d+)\)", ev).group(1)
gw = float(re.search(r'Field\(([\d.]+), alias="GATEWAY_TIMEOUT_S"\)', api).group(1))
timeout, group = {}, None
for line in cfg.splitlines():
    m = re.match(r"  - model_name: (\S+)", line)
    group = m.group(1) if m else group
    m = re.match(r"\s+timeout: (\d+)", line)
    if m:
        timeout[group] = int(m.group(1))
fall = {k: v.replace('"', "") for k, v in re.findall(r"- (documind-[a-z]+): \[([^\]]*)\]", cfg)}
print(f"the SLM: {flag['gpu']} {flag['gpu-type']}, {flag['cpu']} vCPU, {flag['memory']}; {flag['min-instances']} to {flag['max-instances']} instance; "
      f"{flag['concurrency']} requests at a time; {flag['timeout']} s a request")
print(f"its startup probe: /api/tags after {d} s, every {p} s, {f} failures allowed: {d + p * f} s for Ollama to list the model")
print(f"make smoke-slm waits {smoke} s a call")
print(f"a gate row: run_eval waits {row} s for the API, and asks once more two seconds after a timeout")
print(f"the API waits {gw:.0f} s for the gateway (GATEWAY_TIMEOUT_S)")
for route in ("documind-slm", "documind-sensitive"):
    print(f"the gateway waits {timeout[route]} s for {route}, then " + (f"falls back to {fall[route]}" if route in fall else "stops: it has no fallback"))
L4, CPU, MEM = 0.0001867, 0.000018, 0.000002       # Google's us-central1 rates, USD a second (Cloud Run pricing, 24 September 2026)
cpu, mem = int(flag["cpu"]), int(flag["memory"].rstrip("Gi"))
hour = (L4 + cpu * CPU + mem * MEM) * 3600
print(f"the bill, by the instance: ({L4:.7f} + {cpu} x {CPU:.6f} + {mem} x {MEM:.6f}) USD a second = {hour:.4f} USD an hour = Rs {hour * 85:.2f}")
print(f"  up to 10 idle minutes after the last request: Rs {hour * 85 / 6:.2f}; min-instances 1 for a 720-hour month: Rs {hour * 85 * 720:,.0f}")
print("  the kit's own figure: " + re.search(r"costs (Rs [\d,]+/month)", mk).group(1) + ", at $1.42 an hour")'''
CELLS["waits"] = "python3 - <<'PY'\n" + WAITS_PY + "\nPY"
OUT["waits"] = run(sys.executable, WAITS_PY, K2)
WA = OUT["waits"]
assert WA.startswith("the SLM: 1 nvidia-l4, 8 vCPU, 32Gi; 0 to 1 instance; 4 requests at a time; 600 s a request\n"), WA
assert "its startup probe: /api/tags after 10 s, every 5 s, 30 failures allowed: 160 s for Ollama to list the model" in WA, WA
assert "make smoke-slm waits 240 s a call\na gate row: run_eval waits 90 s for the API" in WA and "the API waits 90 s for the gateway (GATEWAY_TIMEOUT_S)" in WA, WA
assert "the gateway waits 110 s for documind-slm, then falls back to documind-general\nthe gateway waits 110 s for documind-sensitive, then stops: it has no fallback" in WA, WA
assert "= 1.4209 USD an hour = Rs 120.78\n" in WA and "Rs 20.13; min-instances 1 for a 720-hour month: Rs 86,960" in WA and "the kit's own figure: Rs 86,904/month, at $1.42 an hour" in WA, WA
HOUR = 0.0001867 + 8 * 0.000018 + 32 * 0.000002
W = {"probe": 160, "smoke": 240, "row": 90, "api": 90, "route": 110, "slm": 600, "retry_gap": 2}

# ------------------------------------------------------------------ steps 5 to 7: the stand-in lane
def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


P_SLM, P_GW, P_CAND = free_port(), free_port(), free_port()
L_SLM, L_GW, L_CAND = (f"http://127.0.0.1:{p}" for p in (P_SLM, P_GW, P_CAND))
LANE = {"LANE182_SLM": f"{SLM}={L_SLM}", "LANE182_GATEWAY": f"{GATEWAY}={L_GW}", "LANE182_CAND": f"{CAND}={L_CAND}", "LANE182_AUD": API}
servers = [subprocess.Popen([sys.executable, str(T / "lane182.py"), "slm", str(P_SLM), SLM], cwd=str(T), stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, env={**ENV, **LANE, "LANE182_WARM": "1"}),
           subprocess.Popen([PRESIDIO_PY, str(T / "lane182.py"), "gateway", str(P_GW), GATEWAY, str(K2 / LL), L_SLM], cwd=str(T),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env={**ENV, **LANE}),
           subprocess.Popen([sys.executable, str(T / "lane182.py"), "candidate", str(P_CAND), CAND, str(K2 / "evals")], cwd=str(T),
                            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env={**ENV, **LANE})]
for port, proc in zip((P_SLM, P_GW, P_CAND), servers):
    for _ in range(600):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            break
        except OSError:
            assert proc.poll() is None, proc.stderr.read().decode()[-2000:]
            time.sleep(0.5)
CLIENT = "import lane182\nlane182.install_client()\n"
UI = f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"
try:
    # ---- step 5: deploy the stand-in, smoke it (the probe's instance is still up; the model is not loaded)
    CELLS["deploy"] = f'make deploy-slm PROJECT="$PROJECT" SLM_STOCK={STOCK}      # the first build pulls 3.3 GB into the image: minutes'
    DL = DEPLOY.split("\n")
    i0 = next(k for k, line in enumerate(DL) if line.startswith("\tgcloud run deploy documind-slm"))
    GC = DL[i0:next(k for k, line in enumerate(DL) if "--startup-probe" in line) + 1]      # make echoes this recipe line; the others start with @
    ECHO = "\n".join(line[1:] if line.startswith("\t") else line for line in GC)
    ECHO = ECHO.replace("$(SLM_REGION)", "us-central1").replace("$(PROJECT)", PROJ).replace("$(if $(SLM_STOCK),stock,gguf)", "stock")
    assert ECHO.startswith("gcloud run deploy documind-slm \\\n  --source services/slm --region us-central1") and "$(" not in ECHO and ECHO.endswith("--quiet"), ECHO
    OUT["deploy"] = (f">> stand-in: {STOCK} will be served as documind-slm\n" + ECHO + "\n...\n"
                     f">> slm: {SLM} (min-instances 0; make slm-off after every session anyway)\n")
    CELLS["smoke"] = 'make smoke-slm PROJECT="$PROJECT"'
    OUT["smoke"] = run(sys.executable, CLIENT + "import runpy, sys\nsys.argv = ['smoke_slm.py']\ntry:\n    runpy.run_path('smoke/smoke_slm.py', run_name='__main__')\n"
                       "except SystemExit as e:\n    assert not e.code, e.code\n", K2,
                       {**LANE, "DOCUMIND_SLM_URL": SLM, "DOCUMIND_GATEWAY_URL": GATEWAY, "DOCUMIND_IMPERSONATE_SA": UI,
                        "DOCUMIND_PROJECT": PROJ, "SLM_REGION": "us-central1"})
    SM = OUT["smoke"]
    assert "[PASS] /api/tags lists documind-slm  HTTP 200 in 0.1s (cold start included): ['documind-slm:latest']" in SM, SM
    assert "[PASS] /api/generate answers  'OK' in 12.0s" in SM and "[PASS] /v1/chat/completions answers (the OpenAI-compatible door)  'OK' in 0.6s" in SM, SM
    assert "[PASS] through the gateway's documind-slm route  HTTP 200, served by 'ollama_chat/documind-slm' in 0.6s" in SM, SM
    assert f"[PASS] what the service serves  stock\tus-central1-docker.pkg.dev/{PROJ}/cloud-run-source-deploy/documind-slm@sha256:DIGEST" in SM and "5 passed, 0 failed" in SM, SM

    # ---- step 6: idle past the window, then the cold start, timed
    urllib.request.urlopen(f"{L_SLM}/_standin/idle", timeout=10).read()
    TIME_PY = r'''import json, os, subprocess, time, urllib.request
P, N = os.environ["PROJECT"], os.environ["NUMBER"]
SLM = f"https://documind-slm-{N}.{os.environ.get('SLM_REGION', 'us-central1')}.run.app"
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com", f"--audiences={SLM}"],
                     capture_output=True, text=True, check=True).stdout.strip()


def call(path, body=None):
    req = urllib.request.Request(SLM + path, data=json.dumps(body).encode() if body else None, method="POST" if body else "GET",
                                 headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=300) as r:
        j = json.loads(r.read())
    return time.time() - t0, j


gen = {"model": "documind-slm", "prompt": "Reply with the single word OK.", "stream": False}
a, tags = call("/api/tags")                                    # waits for an instance, if there is none
b, first = call("/api/generate", gen)                          # loads the model into the GPU, if it is not loaded
c, again = call("/api/generate", gen)                          # warm
m = tags["models"][0]
print(f"/api/tags             {a:5.1f} s   {m['name']} ({m['details']['parameter_size']}, {m['details']['quantization_level']})")
print(f"/api/generate, first  {b:5.1f} s   {first['response'].strip()!r}")
print(f"/api/generate, again  {c:5.1f} s   {again['response'].strip()!r}")
if a > 10:
    print(f"a cold start: {a + b:.1f} s to the first answer - {a:.1f} s for an instance, then {b - c:.1f} s to load the model into the GPU")
else:
    print(f"the instance was still up ({a:.1f} s): Cloud Run keeps an idle GPU instance up to 10 minutes. Wait longer and run this again.")'''
    CELLS["time"] = "python3 - <<'PY'\n" + TIME_PY + "\nPY"
    OUT["time"] = run(sys.executable, CLIENT + TIME_PY, K2, LANE)
    TI = OUT["time"]
    assert "/api/tags              41.4 s   documind-slm:latest (4.3B, Q4_K_M)" in TI and "/api/generate, first   12.0 s   'OK'" in TI, TI
    assert "/api/generate, again    0.6 s   'OK'" in TI and "a cold start: 53.4 s to the first answer - 41.4 s for an instance, then 11.4 s to load the model into the GPU" in TI, TI
    COLD, START_S, LOAD_S = 53.4, 41.4, 11.4

    # ---- step 7a: lesson 9.1's three requests, the sensitive route's backend deployed
    ROUTE_PY = r'''import json, os, re, subprocess, urllib.error, urllib.request
P, N, R = os.environ["PROJECT"], os.environ["NUMBER"], os.environ["REGION"]
GW = f"https://documind-gateway-{N}.{R}.run.app"
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email",
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com", f"--audiences={GW}"],
                     capture_output=True, text=True, check=True).stdout.strip()
rates, group = {}, None                                        # config.yaml's per-token rates, by route
for line in open("services/litellm/config.yaml", encoding="utf-8"):
    m = re.match(r"  - model_name: (\S+)", line)
    group = m.group(1) if m else group
    m = re.match(r"\s+(input|output)_cost_per_token: ([\d.]+)", line)
    if m:
        rates.setdefault(group, {})[m.group(1)] = float(m.group(2))


def ask(text):
    body = json.dumps({"model": "documind-general", "messages": [{"role": "user", "content": text}], "max_tokens": 60}).encode()
    req = urllib.request.Request(f"{GW}/v1/chat/completions", data=body, method="POST",
                                 headers={"Content-Type": "application/json", "Authorization": f"Bearer {tok}"})
    try:
        with urllib.request.urlopen(req, timeout=150) as r:
            return r.status, json.loads(r.read()), r.headers.get("x-litellm-response-cost")
    except urllib.error.HTTPError as e:
        return e.code, None, None


per_m = lambda g: f"{rates[g]['input'] * 1e6:.2f} and {rates[g]['output'] * 1e6:.2f}"
print(f"USD a million tokens, in and out (config.yaml): documind-general {per_m('documind-general')}, documind-sensitive {per_m('documind-sensitive')}")
for label, text in (("no personal data", "What is the notice period for a confirmed E3?"),
                    ("a bare PAN", "My PAN is ABCDE1234F. What is the notice period for a confirmed E3?"),
                    ("a PAN and a date", "My PAN is ABCDE1234F and I joined on 5 March 2026. What is my notice period?")):
    status, j, cost = ask(text)
    if status != 200:
        print(f"  {label:17} HTTP {status}  no answer")
        continue
    u = j["usage"]
    print(f"  {label:17} HTTP 200  answered by {j['model']}; {u['prompt_tokens']} tokens in, {u['completion_tokens']} out; "
          f"x-litellm-response-cost {cost}")
    if not j["model"].startswith("gemini"):
        print(f"  {'':17} {j['choices'][0]['message']['content']}")'''
    CELLS["route"] = "python3 - <<'PY'\n" + ROUTE_PY + "\nPY"
    OUT["route"] = run(sys.executable, CLIENT + ROUTE_PY, K2, LANE)
    RO = OUT["route"]
    assert "USD a million tokens, in and out (config.yaml): documind-general 1.50 and 7.50, documind-sensitive 20.50 and 20.50" in RO, RO
    assert "  no personal data  HTTP 200  answered by gemini-3.6-flash" in RO and "  a bare PAN        HTTP 200  answered by gemini-3.6-flash" in RO, RO
    m = re.search(r"  a PAN and a date  HTTP 200  answered by ollama_chat/documind-slm; (\d+) tokens in, (\d+) out; x-litellm-response-cost ([\d.e-]+)", RO)
    assert m and "the documents you shared do not say which applies to you." in RO, RO
    PTIN, PTOUT, PCOST = int(m.group(1)), int(m.group(2)), float(m.group(3))
    assert abs(PCOST - (PTIN + PTOUT) * 20.5e-6) < 1e-12, (PTIN, PTOUT, PCOST)

    # ---- step 7b: the small model behind a candidate revision
    CELLS["candidate"] = ('make candidate PROJECT="$PROJECT" MODEL_BACKEND=gateway GENERATOR_MODEL=documind-slm\n'
                          'export CAND="https://candidate---documind-api-$NUMBER.$REGION.run.app"; echo "CAND=$CAND"')
    RECIPE = MK[MK.index("\ncandidate: guard-project\n") + 1:].split("\n\n", 1)[0]
    ENV_STR = RECIPE.split('--update-env-vars "^|^', 1)[1].split('"', 1)[0]
    PAIRS = re.findall(r"([A-Z_]+)=\$\(([A-Z_]+)\)", ENV_STR.split("$(if", 1)[0])
    DEFAULTS = {v: (re.search(rf"^{v}\s*\?=[ \t]*(.*)$", MK, re.M).group(1).strip() if re.search(rf"^{v}\s*\?=", MK, re.M) else "") for _, v in PAIRS}
    OVER = {"MODEL_BACKEND": "gateway", "GENERATOR_MODEL": "documind-slm"}
    ECHO = "\n".join(RECIPE.split("\n")[1:3]).replace("\t", "").replace("$(REGION)", REGION).replace("$(PROJECT)", PROJ)
    for _, v in PAIRS:
        ECHO = ECHO.replace(f"$({v})", OVER.get(v, DEFAULTS[v]))
    ECHO = (ECHO.replace("$(if $(RETRIEVAL_BACKEND),|RETRIEVAL_BACKEND=$(RETRIEVAL_BACKEND)|RAG_LOCATION=$(RAG_LOCATION),)", "")
            .replace("$(if $(GENERATOR_LOCATION),|GENERATOR_LOCATION=$(GENERATOR_LOCATION),)", "")
            .replace("$(if $(GENERATOR_LOCATION),,--remove-env-vars GENERATOR_LOCATION)", "--remove-env-vars GENERATOR_LOCATION"))
    assert "$(" not in ECHO and "GENERATOR_MODEL=documind-slm|RAG_MODEL_BASE=gemini-3.6-flash|ROUTING=off|MODEL_BACKEND=gateway|" in ECHO, ECHO
    OUT["candidate"] = (ECHO + "\n...\n>> candidate revision: documind-api-000NN-xxx (deploy/.candidate-revision - make promote moves traffic to it by name)\n"
                        f">> candidate: {CAND} (no traffic; remove with gcloud run services update-traffic documind-api --remove-tags candidate)\nCAND={CAND}\n")
    ASK_PY = r'''import json, os, re, subprocess, urllib.request
P, N, R = os.environ["PROJECT"], os.environ["NUMBER"], os.environ["REGION"]
API, CAND = f"https://documind-api-{N}.{R}.run.app", os.environ["CAND"]
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email",       # the API checks the token against its own URL
                      f"--impersonate-service-account=documind-ui-sa@{P}.iam.gserviceaccount.com", f"--audiences={API}"],
                     capture_output=True, text=True, check=True).stdout.strip()
rates, group = {}, None
for line in open("services/litellm/config.yaml", encoding="utf-8"):
    m = re.match(r"  - model_name: (\S+)", line)
    group = m.group(1) if m else group
    m = re.match(r"\s+(input|output)_cost_per_token: ([\d.]+)", line)
    if m:
        rates.setdefault(group, {})[m.group(1)] = float(m.group(2))
q = "What is the notice period for a confirmed E3?"                        # golden row lk-06
req = urllib.request.Request(f"{CAND}/v1/query", data=json.dumps({"query": q, "tenant_id": "acme"}).encode(), method="POST",
                             headers={"Authorization": f"Bearer {tok}", "Content-Type": "application/json"})
with urllib.request.urlopen(req, timeout=180) as r:
    j = json.loads(r.read())
print("lk-06:", q)
print("answer:", j["answer"])
for c in j["citations"]:
    print("  cites", c["chunk_id"])
print(f"model {j['model']}, backend {j['backend']}: the route the API asked for, whoever answered")
tin, tout, cost = j["tokens_in"], j["tokens_out"], j["cost_usd"]
priced = {g: tin * v["input"] + tout * v["output"] for g, v in rates.items() if g in ("documind-slm", "documind-general")}
who = [g for g, usd in priced.items() if cost is not None and abs(usd - cost) < 1e-9]
print(f"cost {cost} USD for {tin} tokens in and {tout} out: " + (f"{who[0]}'s rate, so " + ("the small model answered" if who[0] == "documind-slm"
      else "Gemini answered: the hook moved it") if who else "no route's rate matches"))'''
    CELLS["ask"] = "python3 - <<'PY'\n" + ASK_PY + "\nPY"
    OUT["ask"] = run(sys.executable, CLIENT + ASK_PY, K2, {**LANE, "CAND": CAND})
    AS = OUT["ask"]
    assert "answer: A confirmed E3 serves a notice period of 60 days [1]." in AS and "  cites acme:lk-06#0" in AS, AS
    assert "model documind-slm, backend gateway: the route the API asked for, whoever answered" in AS, AS
    assert "cost 0.03977 USD for 1900 tokens in and 40 out: documind-slm's rate, so the small model answered" in AS, AS

    # ---- step 7c: the scoped gate on the candidate, then lk-06's row in its report
    CELLS["gate"] = 'make eval-live PROJECT="$PROJECT" API="$CAND" SOURCE=hr_policy_2026.md REPORT="$HOME/slm182.json"'
    gate = run(sys.executable, CLIENT + "import runpy, sys\nsys.argv = ['run_eval.py', '--api-url', " + repr(CAND) + ", '--source', 'hr_policy_2026.md', "
               "'--report', " + repr(str(T / "slm182.json")) + "]\ntry:\n    runpy.run_path('evals/run_eval.py', run_name='__main__')\n"
               "except SystemExit as e:\n    print('EXIT', e.code)\n", K2,
               {**LANE, "DOCUMIND_ID_TOKEN": f"tok:{API}", "DOCUMIND_OUTSIDER_TOKEN": f"tok:{API}"})
    GATE_RC = int(re.search(r"EXIT (\S+)", gate).group(1).replace("None", "0"))
    gate = gate.split("EXIT", 1)[0]
    lines = []
    for line in gate.splitlines():
        if line.startswith(("  latency ms", "  retrieve_ms", "  rerank_ms", "  generate_ms", "  pool")):
            line = re.sub(r"(p50|p95|avg)\s+[\d.]+", lambda mm: f"{mm.group(1)}   ...", line)
        if "[info] quote_support_rate" in line:
            line = re.sub(r"\d+\.\d%", "  ...", line)
        lines.append(line.replace(str(T / "slm182.json"), "/home/YOU/slm182.json"))
    OUT["gate"] = f">> {CAND}\n" + "\n".join(lines).rstrip("\n") + "\n"
    GA = OUT["gate"]
    REP = json.loads((T / "slm182.json").read_text(encoding="utf-8"))
    GATED_PY = r'''import json, os
rep = json.load(open(os.path.expanduser("~/slm182.json"), encoding="utf-8"))
row = next(r for r in rep["records"] if r["id"] == "lk-06")
print(f"lk-06: {'pass' if row['pass'] else 'fail'}, {row['citations']} citation(s); the route it asked for: {row['model']}, through the {row['backend']}")
print(f"{sum(r['pass'] for r in rep['records'])} of {len(rep['records'])} rows passed; "
      + ("all thresholds met" if not rep["failed"] else "below the threshold: " + ", ".join(rep["failed"])))'''
    CELLS["gated"] = "python3 - <<'PY'\n" + GATED_PY + "\nPY"
    OUT["gated"] = run(sys.executable, GATED_PY, K2)
    GD = OUT["gated"]
    assert GD == "lk-06: pass, 1 citation(s); the route it asked for: documind-slm, through the gateway\n8 of 10 rows passed; all thresholds met\n", GD
    assert "rows that cost a point (2):" in GA and "lk-02  lookup    acme    answered without ['15 June']" in GA and "lk-08  lookup    acme    REFUSED" in GA, GA
    assert "  10 rows (10 answerable, 0 not) against " + CAND in GA and GA.rstrip().endswith("All thresholds met.") and GATE_RC == 0, GA[-600:]
finally:
    for proc in servers:
        proc.terminate()
        proc.wait(timeout=30)

CELLS["cleanup"] = ('gcloud run services update-traffic documind-api --region "$REGION" --project "$PROJECT" --remove-tags candidate --quiet\n'
                    'rm -f .candidate-revision      # make promote flips to the revision this file names, tag or no tag\n'
                    'make slm-off PROJECT="$PROJECT"')
SLMOFF_ECHO = SLMOFF.split("\n")[1].lstrip("\t").replace("$(SLM_REGION)", "us-central1").replace("$(PROJECT)", PROJ)
assert SLMOFF_ECHO == f"gcloud run services update documind-slm --region us-central1 --project {PROJ} --min-instances 0 --quiet", SLMOFF_ECHO
OUT["cleanup"] = "...\n" + SLMOFF_ECHO + "\n...\ndocumind-slm scaled to zero\n"
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ the panel: one request's wait, the timeouts along its path, the bill
IDLE = {"deployed": [True, False], "under5": [True, True], "5to10": [True, False], "over10": [False, False]}
GEN_S = 1                                                   # a short answer, warm


def request(idle: str, start: int, load: int, caller: str) -> list:
    """What one request waits for and what its caller gets: [wait, verdict, seconds]. The waits are the kit's (W above)."""
    up, loaded = IDLE[idle]
    wait = (0 if up else start) + (0 if loaded else load) + GEN_S
    if caller == "smoke":
        return [wait, "answered", wait] if wait <= W["smoke"] else [wait, "smoke-gives-up", W["smoke"]]
    if caller in ("api-slm", "api-sensitive"):
        if wait < W["api"]:
            return [wait, "answered", wait]
        return [wait, "api-502-then-gateway-answers" if wait < W["route"] else "api-502-then-gateway-times-out", W["api"]]
    if wait < W["row"]:
        return [wait, "answered", wait]
    at = W["row"] + W["retry_gap"]                           # run_eval asks again two seconds after its timeout
    again = max(0, wait - GEN_S - at) + GEN_S                # the first try woke the instance and loaded the model meanwhile
    return [wait, "answered-on-retry", at + again] if again < W["row"] else [wait, "row-fails", at + W["row"]]


STARTS, LOADS = [20, 40, 60, 90], [5, 10, 20, 40]
CALLERS = ["api-slm", "api-sensitive", "gate", "smoke"]
CASES = [[i, s, ld, c, request(i, s, ld, c)] for i in IDLE for s in STARTS for ld in LOADS for c in CALLERS]
assert {c[4][1] for c in CASES} == {"answered", "api-502-then-gateway-answers", "api-502-then-gateway-times-out", "answered-on-retry"}, {c[4][1] for c in CASES}
assert request("over10", 40, 10, "api-slm") == [51, "answered", 51] and request("over10", 90, 20, "gate")[1] == "answered-on-retry"
UI_JS = r"""var root = document.getElementById('sl'); if (!root) return;
  var W = __W__, IDLE = __IDLE__, GEN_S = __GEN__, HOUR = __HOUR__, INR = 85;
  function request(idle, start, load, caller){ var up = IDLE[idle][0], loaded = IDLE[idle][1];
    var wait = (up ? 0 : start) + (loaded ? 0 : load) + GEN_S;
    if (caller === 'smoke') { return wait <= W.smoke ? [wait, 'answered', wait] : [wait, 'smoke-gives-up', W.smoke]; }
    if (caller === 'api-slm' || caller === 'api-sensitive') { if (wait < W.api) { return [wait, 'answered', wait]; }
      return [wait, wait < W.route ? 'api-502-then-gateway-answers' : 'api-502-then-gateway-times-out', W.api]; }
    if (wait < W.row) { return [wait, 'answered', wait]; }
    var at = W.row + W.retry_gap, again = Math.max(0, wait - GEN_S - at) + GEN_S;
    return again < W.row ? [wait, 'answered-on-retry', at + again] : [wait, 'row-fails', at + W.row]; }
  window.__sl = {request: request};
  var $ = function(id){ return document.getElementById(id); };
  function line(out, cls, text){ var d = document.createElement('div'); if (cls) { d.className = cls; } d.textContent = text; out.appendChild(d); }
  function rs(x){ return 'Rs ' + x.toLocaleString('en-IN', {minimumFractionDigits: 2, maximumFractionDigits: 2}); }
  function show(){ var idle = $('sl-idle').value, start = Number($('sl-start').value), load = Number($('sl-load').value), caller = $('sl-caller').value;
    var r = request(idle, start, load, caller), up = IDLE[idle][0], loaded = IDLE[idle][1];
    var a = $('sl-wait'), b = $('sl-path'), c = $('sl-bill'); a.textContent = ''; b.textContent = ''; c.textContent = '';
    line(a, '', up ? 'An instance is up' + (idle === '5to10' ? ' (Cloud Run may keep an idle GPU instance up to 10 minutes; it may stop it sooner).' : '.') : 'No instance: Cloud Run stopped it after the idle window.');
    line(a, '', loaded ? 'The model is in the GPU: Ollama keeps it 5 minutes after the last request.' : (up ? 'The model is not in the GPU: ' + (idle === 'deployed' ? 'the startup probe asked /api/tags only.' : 'Ollama unloaded it at 5 minutes.') : 'The model is on the image, not in the GPU.'));
    line(a, '', (up ? '' : start + ' s for an instance, then ') + (loaded ? '' : load + ' s to load the model, then ') + 'about ' + GEN_S + ' s for a short answer.');
    line(a, r[0] > 10 ? 'stop' : 'pass', 'The request waits about ' + r[0] + ' s.');
    if (caller === 'smoke') { line(b, '', 'make smoke-slm calls the SLM directly, and waits ' + W.smoke + ' s a call.'); }
    else if (caller === 'gate') { line(b, '', 'run_eval waits ' + W.row + ' s for the API, which waits ' + W.api + ' s for the gateway, which waits ' + W.route + ' s for documind-slm.'); }
    else { line(b, '', 'The API waits ' + W.api + ' s for the gateway, which waits ' + W.route + ' s for documind-' + caller.slice(4) + '; the SLM allows ' + W.slm + ' s a request.'); }
    var v = r[1];
    if (v === 'answered') { line(b, 'pass', 'Answered by the small model after about ' + r[2] + ' s.'); }
    else if (v === 'smoke-gives-up') { line(b, 'stop', 'The smoke gives up at ' + W.smoke + ' s: [FAIL].'); }
    else if (v === 'answered-on-retry') { line(b, 'stop', 'The first try times out at ' + W.row + ' s.'); line(b, 'pass', 'run_eval asks again 2 s later; the first try woke the instance, and the retry is answered at about ' + r[2] + ' s.'); }
    else if (v === 'row-fails') { line(b, 'stop', 'Both tries time out: the row fails as a request error at about ' + r[2] + ' s.'); }
    else { line(b, 'stop', 'The API gives up at ' + W.api + ' s and returns 502.');
      if (v === 'api-502-then-gateway-answers') { line(b, '', 'The small model answers the gateway at about ' + r[0] + ' s, after the API has gone.'); }
      else { line(b, '', 'The gateway times out at ' + W.route + ' s and retries once, ' + (caller === 'api-slm' ? 'then falls back to Gemini. Its answer reaches nobody.' : 'with no fallback.')); } }
    line(c, '', up ? 'The instance was already up, and billing.' : 'A new instance bills from its start: at least a minute.');
    line(c, '', 'By the instance, not the request: $' + HOUR.toFixed(4) + ' an hour, ' + rs(HOUR * INR) + '.');
    line(c, 'stop', 'After the last request, up to 10 idle minutes: ' + rs(HOUR * INR / 6) + '.');
    line(c, '', 'Left at min-instances 1: Rs ' + Math.round(HOUR * INR * 720).toLocaleString('en-IN') + ' for a 720-hour month (the kit says Rs 86,904, at $1.42).'); }
  ['sl-idle', 'sl-start', 'sl-load', 'sl-caller'].forEach(function(id){ $(id).addEventListener('change', show); });
  show();"""
UI_JS = (UI_JS.replace("__W__", json.dumps(W)).replace("__IDLE__", json.dumps(IDLE)).replace("__GEN__", str(GEN_S))
         .replace("__HOUR__", repr(HOUR * 3600)))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
PORT_JS = UI_JS.split("var $ = function(id)")[0].replace("var root = document.getElementById('sl'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var C = " + json.dumps([c[:4] for c in CASES]) + ";\n"
        "process.stdout.write(JSON.stringify(C.map(function(c){ return window.__sl.request(c[0], c[1], c[2], c[3]); })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
for case, got in zip(CASES, json.loads(node.stdout)):
    assert got == case[4], (case, got)
N_CHECKED = len(CASES)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "tfvenv": "run in the operator shell (once: a venv with a transformers that can read the tokenizer)",
    "modelfile": "run in the operator shell, in the kit (downloads the tokenizer's files, about 31 MB; no GPU, no Google Cloud)",
    "waits": "run in the operator shell, in the kit (reads the kit's files; no network)",
    "deploy": "run in the operator shell, in the kit (a GPU service: it bills while an instance lives)",
    "smoke": "run in the operator shell, in the kit, right after the deploy",
    "time": "run in the operator shell, after documind-slm has been idle for more than 10 minutes",
    "route": "run in the operator shell, in the kit (lesson 9.1's three requests, through the gateway)",
    "candidate": "run in the operator shell, in the kit (a no-traffic revision; the live one keeps its settings)",
    "ask": "run in the operator shell, in the kit (one golden question through the candidate)",
    "gate": "run in the operator shell, in the kit (the gate, scoped to the HR policy's rows)",
    "gated": "run in the operator shell (reads the gate's report)",
    "cleanup": "run in the operator shell, in the kit, when you are done",
}
OUT_LABELS = {
    "modelfile": "(this cell's output, run on the kit's make_modelfile.py; the warning is transformers' own: the tokenizer needs no PyTorch)",
    "waits": "(this cell, run on the kit's files; the rates are Google's, typed into the cell)",
    "deploy": "(Cloud Build's and gcloud's lines are left out)",
    "smoke": "(the kit's own smoke, against a stand-in Ollama and gateway; your times differ)",
    "time": "(this cell, against a stand-in that starts cold: its times are illustrations, yours are your lane's)",
    "route": "(this cell, against a stand-in gateway with the kit's own hook and the real Presidio: your tokens, cost and answer differ)",
    "candidate": "(gcloud's lines are left out)",
    "ask": "(this cell, against a stand-in candidate; the answer and its token counts are illustrations)",
    "gate": "(run_eval.py's own code over HTTP, against a stand-in candidate that misses two rows the way a small model can; your rows are your lane's)",
    "gated": "(this cell, on the report the gate above wrote)",
    "cleanup": "(gcloud's lines are left out)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items() if v})
opts = lambda pairs, sel: "".join(f'<option value="{html.escape(str(v))}"{" selected" if v == sel else ""}>{html.escape(t)}</option>' for v, t in pairs)  # noqa: E731
MISSES = [r["id"] for r in REP["records"] if not r["pass"]]
STATS = {"N_CHECKED": str(N_CHECKED), "COLD": f"{COLD:.1f}", "START_S": f"{START_S:.1f}", "LOAD_S": f"{LOAD_S:.1f}",
         "HOUR_USD": f"{HOUR * 3600:.2f}", "HOUR_INR": f"{HOUR * 3600 * 85:.2f}", "IDLE_INR": f"{HOUR * 3600 * 85 / 6:.2f}",
         "MONTH_INR": f"{HOUR * 3600 * 85 * 720:,.0f}", "TF_PIN": TF_PIN, "STOCK": STOCK, "TUNED_FROM": TUNED_FROM,
         "PTIN": str(PTIN), "PTOUT": str(PTOUT), "PCOST": repr(PCOST), "N_ROWS": str(len(REP["records"])),
         "N_PASS": str(sum(r["pass"] for r in REP["records"])), "MISSES": " and ".join(MISSES),
         "IDLE_OPTIONS": opts([("deployed", "just deployed"), ("under5", "under 5 minutes"), ("5to10", "5 to 10 minutes"), ("over10", "over 10 minutes")], "over10"),
         "START_OPTIONS": opts([(s, f"{s} s") for s in STARTS], 40),
         "LOAD_OPTIONS": opts([(ld, f"{ld} s") for ld in LOADS], 10),
         "CALLER_OPTIONS": opts([("api-slm", "the API, route documind-slm"), ("api-sensitive", "the API, route documind-sensitive"),
                                 ("gate", "a gate row, through the API"), ("smoke", "make smoke-slm, direct")], "api-slm")}

if os.environ.get("CELLS_ONLY"):
    for k, v in OUT.items():
        print(f"===== {k}\n{v}")
    print("GATE_RC", GATE_RC, {k: v for k, v in STATS.items() if not k.endswith("_OPTIONS")})
    sys.exit(0)


def subst(text: str) -> str:
    for k, v in {**WIN, **STATS}.items():
        text = text.replace(f"%%{k}%%", v)
    return text


body = "".join([subst(fill(pb.part(LESSON, "a"))), setup, subst(fill(pb.part(LESSON, "b"))), subst(fill(pb.part(LESSON, "c")))])
finish(LESSON, title, EXTRA_CSS, body, JS)
print(f"kit: make_modelfile.py under transformers {TF_PIN} (and refused by 4.57.1), make smoke-slm, run_eval.py against the stand-in | "
      f"cold start {COLD} s | gate {STATS['N_PASS']} of {STATS['N_ROWS']} | panel checked on {N_CHECKED} cases")
