"""Build lesson 9.1 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Trace and authorize gateway routes. The LiteLLM gateway is one door for every model: a Cloud Run service behind IAM,
the caller's ID token as the key and no master key; model groups for Gemini and for the self-hosted backends, with
fallbacks to Gemini - except the sensitive route, whose point is that the text does not leave; a pre-call hook
(documind_router.py) that classifies every request (documind_classifier.py) and re-routes RESTRICTED text to that
route and masks CONFIDENTIAL text; a token proxy that fronts the self-hosted backends with an ID token of its own; and
a cost header on every completion, which the API writes on its usage row.
Offline: the classifier and the hook traced with the gateway image's own pins (Presidio 2.2.364, en_core_web_lg); the
token proxy's token, minted per audience. Live: make deploy-gateway, make smoke-gateway, and three requests - the
cost header on a completion, a PAN re-routed, and the PAN the smoke sends, which is not.

Build-time proof: the offline trace ran the kit's own classifier and hook under the real Presidio at the image's pins
(PRESIDIO_PY: a Python with requirements.txt's presidio pins and en_core_web_lg installed), gcp_id_token.py ran with
the metadata server stood in, and make smoke-gateway and the live cells ran against a stand-in gateway (lane181.py,
beside this file) that serves config.yaml's routes behind the kit's own hook. The panel is the hook's routing decision
and config.yaml's fallback chains, ported and compared with the kit's on every combination it offers.

    PRESIDIO_PY=/path/to/python python lessons/09-serving/9.1-gateway-routes/build.py
"""
import ast
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
from pathlib import Path

sys.dont_write_bytecode = True                     # the kit modules loaded below leave no __pycache__ in deploy/
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "9.1"
title = "<title>Lesson 9.1 Trace and authorize gateway routes - one door, a hook that re-routes, a token per backend, a cost per answer | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
GATEWAY = "https://documind-gateway-NUMBER.asia-south1.run.app"
LL = "services/litellm"
CFG, CLS, RTR, PROXY, TOK, SMOKE, GEN = (f"{LL}/config.yaml", f"{LL}/documind_classifier.py", f"{LL}/documind_router.py", f"{LL}/token_proxy.py",
                                        f"{LL}/gcp_id_token.py", "smoke/smoke_gateway.py", "services/rag-api/generator.py")
PRESIDIO_PY = os.environ.get("PRESIDIO_PY", "")
assert PRESIDIO_PY and Path(PRESIDIO_PY).exists(), "set PRESIDIO_PY to a Python with the gateway image's presidio pins and en_core_web_lg"

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.gr-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:0 10px;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,140px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.gr-out{margin:6px 0 0;font-size:12.5px;line-height:1.6;}
.gr-out .pass{color:var(--teal-dark);font-weight:600;}
.gr-out .stop{color:#9a3412;font-weight:600;}
.gr-out .mono{font-family:var(--mono);font-size:11.5px;white-space:pre-wrap;}
"""

setup = setup_section()


# ------------------------------------------------------------------ verbatim excerpts
def span(rel: str, start: str, last: str) -> int:
    lines = (KIT / rel).read_text(encoding="utf-8").split("\n")
    i = next(k for k, line in enumerate(lines) if line.startswith(start))
    return next(k for k in range(i, len(lines)) if lines[k].startswith(last)) - i + 1


EXCERPTS = {
    "door": ("Makefile - make deploy-gateway: behind IAM, and two accounts that may call it",
             block("Makefile", "	gcloud run deploy documind-gateway --source services/litellm", n=9)),
    "sensitive": ("services/litellm/config.yaml - the sensitive route: the self-hosted model, and no fallback",
                  block(CFG, "  # The pre-call hook's target for RESTRICTED text", n=10)),
    "fallbacks": ("services/litellm/config.yaml - where each route goes when its backend does not answer",
                  block(CFG, "  # Self-host cold, scaled to zero or out of quota", n=6)),
    "classify": ("services/litellm/documind_classifier.py - classify_tier(): a pattern, then Presidio's confirmation",
                 block(CLS, "def classify_tier(text: str) -> SensitivityTier:", n=span(CLS, "def classify_tier(", "    return SensitivityTier.PUBLIC"))),
    "hook": ("services/litellm/documind_router.py - the pre-call hook's decision",
             block(RTR, "        tier = classify_tier(text)", n=span(RTR, "        tier = classify_tier(text)", "        # else PUBLIC: keep original model selection"))),
    "proxy": ("services/litellm/token_proxy.py - the caller's token stays at the door; the proxy sends its own",
              block(PROXY, '    headers = {k: v for k, v in request.headers.items() if k.lower() not in HOP}', n=2)),
    "token": ("services/litellm/gcp_id_token.py - get_id_token(): one token per audience, refreshed five minutes early",
              block(TOK, "def get_id_token(audience: str | None = None) -> str:", n=span(TOK, "def get_id_token(", "        return token"))),
    "smokepan": ("smoke/smoke_gateway.py - the PAN check",
                 block(SMOKE, '    status, body, headers, secs = completion(token, "documind-general", "My PAN is ABCDE1234F.', n=7)),
    "cost": ("services/rag-api/generator.py - _gateway_call(): the cost header becomes the usage row's price",
             block(GEN, '    cost = r.headers.get("x-litellm-response-cost")           # the gateway prices the route it served', n=2)),
}
assert EXCERPTS["door"][1].rstrip().endswith('(the API and the UI\'s account may call it)"') and "--no-allow-unauthenticated" in EXCERPTS["door"][1]
assert "documind-sensitive" in EXCERPTS["sensitive"][1] and EXCERPTS["sensitive"][1].rstrip().endswith("output_cost_per_token: 0.0000205")
assert EXCERPTS["fallbacks"][1].rstrip().endswith('- documind-reasoning: ["documind-general"]') and "documind-sensitive" not in EXCERPTS["fallbacks"][1]
assert EXCERPTS["classify"][1].rstrip().endswith("return SensitivityTier.PUBLIC") and "if any(r.score >= 0.7 for r in results):" in EXCERPTS["classify"][1]
assert EXCERPTS["hook"][1].rstrip().endswith("# else PUBLIC: keep original model selection") and 'data["model"] = "documind-sensitive"' in EXCERPTS["hook"][1]
assert EXCERPTS["proxy"][1].rstrip().endswith('headers["Authorization"] = f"Bearer {get_id_token(base)}"')
assert EXCERPTS["token"][1].rstrip().endswith("return token") and "REFRESH_MARGIN_S" in EXCERPTS["token"][1]
assert EXCERPTS["smokepan"][1].rstrip().endswith("deploy or warm the SLM\")") and EXCERPTS["smokepan"][1].count('ok("a PAN is routed by the guardrail"') == 2
assert EXCERPTS["cost"][1].rstrip().endswith("return _GatewayReply(r.json(), float(cost) if cost else None, model)")
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (CFG, CLS, RTR, PROXY, TOK, SMOKE, GEN, "Makefile", "terraform/gateway.tf",
                                                          f"{LL}/Dockerfile", f"{LL}/requirements.txt", f"{LL}/entrypoint.sh", f"{LL}/dlp_audit.py")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
flat = lambda s: re.sub(r"\s+", " ", s)  # noqa: E731
PINS = re.findall(r"^(presidio-[a-z]+)==([\d.]+)$", src[f"{LL}/requirements.txt"], re.M)
assert PINS == [("presidio-analyzer", "2.2.364"), ("presidio-anonymizer", "2.2.364")] and "RUN python -m spacy download en_core_web_lg" in src[f"{LL}/Dockerfile"]
assert "FROM docker.litellm.ai/berriai/litellm:v1.80.5-stable" in src[f"{LL}/Dockerfile"]
assert "no master key (a master key would make every caller's ID token an invalid virtual key)" in flat(src[CFG])
assert "ROUTER_ENFORCE  ?= 1" in MK and 'enforce = os.environ.get("ROUTER_ENFORCE", "1") != "0"' in src[RTR]
assert "for sa in documind-api-sa documind-ui-sa; do" in MK and "--role=roles/run.invoker" in MK and "--min-instances 0 --max-instances 3" in MK
assert "SLM=https://documind-slm-$$NUMBER.$(SLM_REGION).run.app" in MK and "SLM_REGION ?= us-central1" in MK
assert 'api_base: http://127.0.0.1:8090/slm' in src[CFG] and "python /app/token_proxy.py &" in src[f"{LL}/entrypoint.sh"]
assert 'HOP = {"host", "authorization", "content-length", "connection", "transfer-encoding"}' in src[PROXY]
assert "REFRESH_MARGIN_S = 300" in src[TOK] and '_CACHE[audience] = {"token": token, "exp": time.time() + 3600}' in src[TOK]
assert 'cost = headers.get("x-litellm-response-cost") or headers.get("X-Litellm-Response-Cost")' in src[SMOKE]
assert "input_cost_per_token: 0.0000015" in src[CFG] and "output_cost_per_token: 0.0000075" in src[CFG]
assert "MODEL_BACKEND   ?= vertex" in MK and "those two services grant it run.invoker when they are deployed" in flat(src["terraform/gateway.tf"])
flatc = lambda s: flat(re.sub(r"\n\s*#\s*", " ", s))  # noqa: E731 - a comment's lines as one sentence
assert "Presidio lives HERE and only here (11.3): the decision \"may this text leave our perimeter\" is made once, at the gateway, where every route passes." in flatc(src[CFG])
assert "A cold GPU means a slow answer, not a leak." in src[CFG] and "the safe rollout for a classifier that moves traffic" in src[RTR]
assert "a pasted token expires at 3am on a path nobody is watching" in flat(src[CFG])
import yaml  # noqa: E402
_cfg = yaml.safe_load(src[CFG])
_groups = [m["model_name"] for m in _cfg["model_list"]]
_managed = [m["model_name"] for m in _cfg["model_list"] if m["litellm_params"]["model"].startswith("vertex_ai/")]
assert len(_groups) == 6 and _managed == ["documind-general", "documind-reasoning"], (_groups, _managed)
assert all(v[-1] == "documind-general" for d in _cfg["router_settings"]["fallbacks"] for v in d.values())
# the findings
# 1. the classifier's own test cases: a list nothing runs
assert "test_cases = [" in src[CLS] and "classify_tier(" not in src[CLS].split("test_cases = [", 1)[1] and "test_cases" not in "".join(
    (KIT / p).read_text(encoding="utf-8") for p in (RTR, SMOKE))
# 2. the smoke's PAN check passes whatever the gateway did (both branches call ok) - asserted on the excerpt above
# 3. the tag budgets are named, and nothing sends a tag
assert "tag_budget_config:" in src[CFG] and "tenant-acme:" in src[CFG] and "tenant-enterprise:" in src[CFG]
assert '"metadata": {"tenant": tenant_id or ""}' in src[GEN] and '"tags"' not in src[GEN]
# 4. dlp_audit.py is copied into the image and nothing calls it; the gateway's dlp.user role serves it
assert "COPY documind_classifier.py documind_router.py dlp_audit.py gcp_id_token.py token_proxy.py ./" in src[f"{LL}/Dockerfile"]
assert not any("dlp_audit" in (KIT / p).read_text(encoding="utf-8") for p in (RTR, CLS, PROXY, TOK, f"{LL}/entrypoint.sh", CFG))
assert 'role    = "roles/dlp.user"' in src["terraform/gateway.tf"]
# 5. the database is declared whether or not the gateway is deployed
assert "one shape, the database always declared" in flat(src["terraform/gateway.tf"]) and 'tier              = "db-f1-micro"' in src["terraform/gateway.tf"]
assert "DOWN_SERVICES_M11 = documind-gateway" in MK
# the masking masks every finding, whatever its score
assert "anonymized = self.anonymizer.anonymize(text=content, analyzer_results=results)" in src[RTR] and "score" not in src[RTR].split("def mask_pii", 1)[1].split("async def", 1)[0]

# ------------------------------------------------------------------ step 3: the hook, traced with the image's pins (offline)
T = Path(tempfile.mkdtemp(prefix="lesson181-"))
K2 = T / "kit"
for part in ("services/litellm", "smoke", "services/rag-api"):
    shutil.copytree(KIT / part, K2 / part, ignore=shutil.ignore_patterns("__pycache__"))
shutil.copy(KIT / "Makefile", K2 / "Makefile")
shutil.copy(HERE / "lane181.py", T / "lane181.py")
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "NUMBER": "NUMBER",
       "REGION": "asia-south1", "HOME": str(T), "USERPROFILE": str(T), "PYTHONPATH": str(T)}


def run(py: str, code: str, cwd: Path, env: dict | None = None) -> str:
    r = subprocess.run([py, "-"], input=code, cwd=str(cwd), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


ver = run(PRESIDIO_PY, "import importlib.metadata as m\nprint(m.version('presidio-analyzer'), m.version('presidio-anonymizer'), m.version('en_core_web_lg'))", T).split()
assert ver[:2] == ["2.2.364", "2.2.364"], ver
TRACE_PY = r'''import asyncio, sys, types
for name in ("litellm", "litellm.integrations", "litellm.integrations.custom_guardrail"):   # litellm is the image's, not this venv's:
    sys.modules[name] = types.ModuleType(name)                                              # the hook's base class, stood in
sys.modules["litellm.integrations.custom_guardrail"].CustomGuardrail = type("CustomGuardrail", (), {"__init__": lambda self, **kw: None})
import documind_classifier as dc
from documind_router import DocuMindRouter
print("Presidio's recognizers:", ", ".join(sorted(r.name.replace("Recognizer", "") for r in dc.get_analyzer().registry.recognizers)))
print("the classifier's own test cases, which nothing runs:")
for text, expected in dc.test_cases:
    print(f"  {text!r:32} expected {expected.name:12} got {dc.classify_tier(text).name}")
router = DocuMindRouter()
CONTEXT = ("Context:\n[Source 1] hr_policy_2026.md\nNP-03. A confirmed E3 serves a notice period of 60 days. "
           "Queries go to hr@acme.com.\n\nQuestion: What is the notice period for a confirmed E3?")
print("the hook, on four requests for documind-general:")
for text in ("What is the notice period for a confirmed E3?",
             "My PAN is ABCDE1234F. What is the notice period for a confirmed E3?",               # make smoke-gateway's own
             "My PAN is ABCDE1234F and I joined on 5 March 2026. What is my notice period?",
             CONTEXT):
    data = asyncio.run(router.async_pre_call_hook(None, None, {"model": "documind-general",
                                                               "messages": [{"role": "user", "content": text}]}, "completion"))
    print(f"  {data['metadata']['routing_tier']:12} -> {data['model']:18} {text.splitlines()[0]!r}")
print("and what the last one sends to Gemini:")
print("  " + data["messages"][0]["content"].replace("\n", "\n  "))'''
CELLS = {"venv": ('python -m venv ~/gw-venv && ~/gw-venv/bin/pip install -q $(grep \'^presidio\' services/litellm/requirements.txt)   # the gateway image\'s pins\n'
                  '~/gw-venv/bin/python -m spacy download en_core_web_lg > /dev/null && echo "en_core_web_lg installed: the image\'s model, 400 MB"'),
         "trace": "cd services/litellm && ~/gw-venv/bin/python - <<'PY'\n" + TRACE_PY + "\nPY\ncd ../.."}
OUT = {"venv": "en_core_web_lg installed: the image's model, 400 MB\n", "trace": run(PRESIDIO_PY, TRACE_PY, K2 / LL)}
TR = OUT["trace"]
assert TR.startswith("Presidio's recognizers: CreditCard, Crypto, Date, Email, Iban, Ip, MacAddress, MedicalLicense, Nhs, Phone, Spacy, Url, UsBank, UsItin, UsLicense, UsPassport, UsSsn\n"), TR[:300]
assert "'My Aadhaar is 2345-6789-0123'   expected RESTRICTED   got PUBLIC" in TR and "'SSN 123-45-6789'                expected RESTRICTED   got PUBLIC" in TR, TR
assert "'PAN ABCDE1234F'                 expected RESTRICTED   got PUBLIC" in TR and "'Email me at user@acme.com'      expected CONFIDENTIAL got CONFIDENTIAL" in TR, TR
assert "  PUBLIC       -> documind-general   'My PAN is ABCDE1234F. What is the notice period for a confirmed E3?'" in TR, TR
assert "  RESTRICTED   -> documind-sensitive 'My PAN is ABCDE1234F and I joined on 5 March 2026. What is my notice period?'" in TR, TR
assert "NP-03. A confirmed <US_DRIVER_LICENSE> serves a notice period of <DATE_TIME>. Queries go to <EMAIL_ADDRESS>." in TR and "[Source 1] hr_policy_<URL>" in TR, TR
N_RECOG = len(TR.split("\n", 1)[0].split(":", 1)[1].split(","))
N_FAIL = TR.count("expected RESTRICTED   got PUBLIC")

# ------------------------------------------------------------------ step 4: the token the proxy sends (offline)
KEYS_PY = r'''import ast, types
import google.oauth2.id_token
minted = []
google.oauth2.id_token.fetch_id_token = lambda request, audience: minted.append(audience) or f"<token {len(minted)}>"   # the metadata server, counted
import gcp_id_token as g
clock = [1_000_000.0]
g.time = types.SimpleNamespace(time=lambda: clock[0])                                  # a clock the cell can move
SLM, VLLM = "https://documind-slm-NUMBER.us-central1.run.app", "https://documind-vllm-NUMBER.us-central1.run.app/v1"
for label, audience, wait in (("the SLM, first call", SLM, 0), ("the SLM, a minute later", SLM, 60),
                              ("the SLM, 55 minutes in", SLM, 55 * 60 - 60), ("the vLLM engine", VLLM, 0)):
    clock[0] += wait
    print(f"{label:25} {g.get_id_token(audience)}   minted so far: {len(minted)}")
hop = ast.literal_eval(next(n.value for n in ast.parse(open("token_proxy.py", encoding="utf-8").read()).body
                            if isinstance(n, ast.Assign) and getattr(n.targets[0], "id", "") == "HOP"))
print("the proxy drops these request headers, then adds its own Authorization:", ", ".join(sorted(hop)))'''
CELLS["keys"] = "cd services/litellm && python - <<'PY'\n" + KEYS_PY + "\nPY\ncd ../.."
OUT["keys"] = run(sys.executable, KEYS_PY, K2 / LL)
KE = OUT["keys"]
assert "the SLM, first call       <token 1>   minted so far: 1\nthe SLM, a minute later   <token 1>   minted so far: 1\nthe SLM, 55 minutes in    <token 2>   minted so far: 2\nthe vLLM engine           <token 3>   minted so far: 3" in KE, KE
assert KE.rstrip().endswith("authorization, connection, content-length, host, transfer-encoding"), KE

# ------------------------------------------------------------------ steps 5 and 6: the gateway, deployed and called (the stand-in lane)
sock = socket.socket()
sock.bind(("127.0.0.1", 0))
PORT = sock.getsockname()[1]
sock.close()
LOCAL = f"http://127.0.0.1:{PORT}"
server = subprocess.Popen([PRESIDIO_PY, str(T / "lane181.py"), "serve", str(PORT), GATEWAY, str(K2 / LL)], cwd=str(T),
                          stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, env=ENV)
for _ in range(600):
    try:
        socket.create_connection(("127.0.0.1", PORT), timeout=1).close()
        break
    except OSError:
        assert server.poll() is None, server.stderr.read().decode()[-2000:]
        time.sleep(0.5)
CLIENT = "import lane181\nlane181.install_client()\n"
CENV = {"LANE181_GATEWAY": GATEWAY, "LANE181_LOCAL": LOCAL}
try:
    CELLS["deploy"] = 'make deploy-gateway PROJECT="$PROJECT"            # builds the image from services/litellm: the first build takes a while'
    OUT["deploy"] = "...\n>> gateway: https://documind-gateway-NUMBER.asia-south1.run.app (the API and the UI's account may call it)\n"
    CELLS["smoke"] = 'make smoke-gateway PROJECT="$PROJECT"'
    smoke = run(sys.executable, CLIENT + "import runpy, sys\nsys.argv = ['smoke_gateway.py']\ntry:\n    runpy.run_path('smoke/smoke_gateway.py', run_name='__main__')\n"
                "except SystemExit as e:\n    assert not e.code, e.code\n", K2,
                {**CENV, "DOCUMIND_GATEWAY_URL": GATEWAY, "DOCUMIND_IMPERSONATE_SA": f"documind-ui-sa@{PROJ}.iam.gserviceaccount.com"})
    OUT["smoke"] = re.sub(r" in \d+\.\ds", " in ...s", smoke)
    SM = OUT["smoke"]
    assert "[PASS] no token is refused at the door  HTTP 403" in SM and "[PASS] liveliness as the member's account  HTTP 200" in SM, SM
    assert "[PASS] a PAN is routed by the guardrail  served by 'gemini-3.6-flash'" in SM and "6 passed, 0 failed" in SM, SM
    COST_HDR = re.search(r"x-litellm-response-cost=([\d.e-]+)", SM).group(1)
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


g = rates["documind-general"]
print(f"documind-general is priced at {g['input'] * 1e6:.2f} and {g['output'] * 1e6:.2f} USD a million tokens, in and out (config.yaml)")
for label, text in (("no personal data", "What is the notice period for a confirmed E3?"),
                    ("a bare PAN", "My PAN is ABCDE1234F. What is the notice period for a confirmed E3?"),
                    ("a PAN and a date", "My PAN is ABCDE1234F and I joined on 5 March 2026. What is my notice period?")):
    status, j, cost = ask(text)
    if status == 200:
        u = j["usage"]
        print(f"  {label:17} HTTP 200  answered by {j['model']}; {u['prompt_tokens']} tokens in, {u['completion_tokens']} out; "
              f"x-litellm-response-cost {cost}")
    else:
        print(f"  {label:17} HTTP {status}  no answer: the route the hook chose has no backend yet, and no fallback")'''
    CELLS["route"] = "python - <<'PY'\n" + ROUTE_PY + "\nPY"
    OUT["route"] = run(sys.executable, CLIENT + ROUTE_PY, K2, CENV)
    RO = OUT["route"]
    assert "documind-general is priced at 1.50 and 7.50 USD a million tokens, in and out (config.yaml)" in RO, RO
    assert "  no personal data  HTTP 200  answered by gemini-3.6-flash" in RO and "  a bare PAN        HTTP 200  answered by gemini-3.6-flash" in RO, RO
    assert "  a PAN and a date  HTTP 500  no answer" in RO, RO
    m = re.search(r"no personal data  HTTP 200  answered by gemini-3.6-flash; (\d+) tokens in, (\d+) out; x-litellm-response-cost ([\d.e-]+)", RO)
    TIN, TOUT, COST = int(m.group(1)), int(m.group(2)), float(m.group(3))
    assert abs(COST - (TIN * 1.5e-6 + TOUT * 7.5e-6)) < 1e-12, (TIN, TOUT, COST)
    assert 0.005 < COST * 85 < 0.03, COST                                       # a paisa or two
finally:
    server.terminate()
    server.wait(timeout=30)

# ------------------------------------------------------------------ the panel: the hook's decision and config.yaml's chains, ported
PANEL_PY = r'''import asyncio, json, sys, types
for name in ("litellm", "litellm.integrations", "litellm.integrations.custom_guardrail"):
    sys.modules[name] = types.ModuleType(name)
sys.modules["litellm.integrations.custom_guardrail"].CustomGuardrail = type("CustomGuardrail", (), {"__init__": lambda self, **kw: None})
import documind_classifier as dc
import documind_router as dr
PRESETS = json.loads(sys.stdin.readline())
router = dr.DocuMindRouter()
out = {"presets": [], "decisions": []}
for label, text in PRESETS:
    res = dc.get_analyzer().analyze(text=text, language="en")
    layer1 = [n for n, p in dc.PATTERNS_RESTRICTED.items() if p.search(text)]
    conf = [n for n, p in dc.PATTERNS_CONFIDENTIAL.items() if p.search(text)]
    tier = dc.classify_tier(text).name
    data = asyncio.run(router.async_pre_call_hook(None, None, {"model": "documind-general", "messages": [{"role": "user", "content": text}]}, "c"))
    out["presets"].append({"label": label, "text": text, "tier": tier, "restricted": layer1, "confidential": conf,
                           "strong": sorted({(r.entity_type, round(r.score, 2)) for r in res if r.score >= 0.7}),
                           "sent": data["messages"][0]["content"]})
import os
masked_text = PRESETS[-1][1]
for tier in ("PUBLIC", "CONFIDENTIAL", "RESTRICTED"):
    for enforce in ("1", "0"):
        for model in ("documind-general", "documind-reasoning", "documind-slm", "documind-inference", "documind-sensitive"):
            os.environ["ROUTER_ENFORCE"] = enforce
            dr.classify_tier = lambda text, t=tier: dc.SensitivityTier[t]
            data = asyncio.run(router.async_pre_call_hook(None, None, {"model": model, "messages": [{"role": "user", "content": masked_text}]}, "c"))
            out["decisions"].append([tier, enforce, model, data["model"], data["messages"][0]["content"] != masked_text])
print(json.dumps(out))'''
PRESETS = [["no personal data", "What is the notice period for a confirmed E3?"],
           ["the smoke's bare PAN", "My PAN is ABCDE1234F. What is the notice period for a confirmed E3?"],
           ["a PAN and a date", "My PAN is ABCDE1234F and I joined on 5 March 2026. What is my notice period?"],
           ["an Aadhaar and a name", "My Aadhaar is 2345 6789 0123 and my name is Priya Sharma."],
           ["an email in the context", "Context:\n[Source 1] hr_policy_2026.md\nNP-03. A confirmed E3 serves a notice period of 60 days. "
                                       "Queries go to hr@acme.com.\n\nQuestion: What is the notice period for a confirmed E3?"]]
r = subprocess.run([PRESIDIO_PY, "-c", PANEL_PY], input=json.dumps(PRESETS) + "\n", cwd=str(K2 / LL), capture_output=True, text=True, encoding="utf-8", env=ENV)
assert r.returncode == 0, r.stderr[-2000:]
PANEL = json.loads(r.stdout)
assert [p["tier"] for p in PANEL["presets"]] == ["PUBLIC", "PUBLIC", "RESTRICTED", "RESTRICTED", "CONFIDENTIAL"], [p["tier"] for p in PANEL["presets"]]
shutil.rmtree(T, ignore_errors=True)
import yaml  # noqa: E402
CONFIG = yaml.safe_load(src[CFG])
GROUPS = {m["model_name"]: {"model": m["litellm_params"]["model"], "base": m["litellm_params"].get("api_base", ""),
                            "in": float(m["litellm_params"]["input_cost_per_token"]), "out": float(m["litellm_params"]["output_cost_per_token"])}
          for m in CONFIG["model_list"]}
FALLBACKS = {k: v for d in CONFIG["router_settings"]["fallbacks"] for k, v in d.items()}


def deployed(group: str, slm: bool) -> bool:
    """Which backends answer on the lane: Gemini always; the SLM once lesson 9.2 deploys it; the vLLM engine and GKE not in this chapter's lane."""
    base = GROUPS[group]["base"]
    return GROUPS[group]["model"].startswith("vertex_ai/") or (slm and base.endswith("/slm"))


def walk(route: str, slm: bool) -> list:
    chain = [route] + FALLBACKS.get(route, [])
    return [chain, next((g for g in chain if deployed(g, slm)), None)]


WALKS = [[route, slm, walk(route, slm)] for route in GROUPS for slm in (False, True)]
UI_JS = r"""var root = document.getElementById('gr'); if (!root) return;
  var PRESETS = __PRESETS__, GROUPS = __GROUPS__, FALLBACKS = __FALLBACKS__;
  function hook(tier, enforce, model){ if (tier === 'RESTRICTED') { return [enforce ? 'documind-sensitive' : model, false]; }
    if (tier === 'CONFIDENTIAL') { return [enforce ? 'documind-general' : model, enforce]; } return [model, false]; }
  function deployed(g, slm){ var b = GROUPS[g].base || ''; return GROUPS[g].model.indexOf('vertex_ai/') === 0 || (slm && b.slice(-4) === '/slm'); }
  function walk(route, slm){ var chain = [route].concat(FALLBACKS[route] || []), hit = null;
    for (var i = 0; i < chain.length; i++) { if (deployed(chain[i], slm)) { hit = chain[i]; break; } } return [chain, hit]; }
  window.__gr = {hook: hook, walk: walk};
  var $ = function(id){ return document.getElementById(id); };
  function line(out, cls, text){ var d = document.createElement('div'); if (cls) { d.className = cls; } d.textContent = text; out.appendChild(d); }
  function show(){ var p = PRESETS[Number($('gr-text').value)], model = $('gr-model').value, enforce = $('gr-enforce').value === '1', slm = $('gr-slm').value === '1';
    var cls = $('gr-class'), out = $('gr-route'); cls.textContent = ''; out.textContent = '';
    line(cls, 'mono', p.text);
    line(cls, '', 'The patterns: ' + (p.restricted.length ? 'RESTRICTED ' + p.restricted.join(', ') : 'no RESTRICTED pattern') + '; ' + (p.confidential.length ? 'CONFIDENTIAL ' + p.confidential.join(', ') : 'no CONFIDENTIAL pattern') + '.');
    line(cls, '', 'Presidio at 0.7 or above: ' + (p.strong.length ? p.strong.map(function(s){ return s[0] + ' ' + s[1]; }).join(', ') : 'nothing') + '.');
    line(cls, p.tier === 'PUBLIC' && p.restricted.length ? 'stop' : 'pass', 'The tier: ' + p.tier + (p.tier === 'PUBLIC' && p.restricted.length ? ' - a RESTRICTED pattern matched, and Presidio confirmed nothing, so it goes where it was asked.' : '.'));
    var h = hook(p.tier, enforce, model), w = walk(h[0], slm);
    line(out, '', 'Asked for ' + model + '; the hook sends it to ' + h[0] + (h[0] === model ? ' (unchanged).' : '.') + (!enforce && p.tier !== 'PUBLIC' ? ' ROUTER_ENFORCE=0 is shadow mode: logged, not moved.' : ''));
    if (h[1]) { line(out, 'stop', 'Masked first, so Gemini is sent:'); line(out, 'mono', p.sent); }
    line(out, '', 'The chain: ' + w[0].join(' \u2192 ') + '.');
    if (w[1]) { var g = GROUPS[w[1]]; line(out, w[1] === h[0] ? 'pass' : '', 'Answered by ' + w[1] + ' (' + g.model + '), at ' + (g['in'] * 1e6).toFixed(2) + ' and ' + (g.out * 1e6).toFixed(2) + ' USD a million tokens in and out: the cost header prices it.'); }
    else { line(out, 'stop', 'No backend in the chain is deployed, and ' + h[0] + ' has no fallback: an error, never Gemini.'); } }
  ['gr-text', 'gr-model', 'gr-enforce', 'gr-slm'].forEach(function(id){ $(id).addEventListener('change', show); });
  show();"""
UI_JS = (UI_JS.replace("__PRESETS__", json.dumps(PANEL["presets"], ensure_ascii=False)).replace("__GROUPS__", json.dumps(GROUPS))
         .replace("__FALLBACKS__", json.dumps(FALLBACKS)))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
PORT_JS = UI_JS.split("var $ = function(id)")[0].replace("var root = document.getElementById('gr'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var D = " + json.dumps(PANEL["decisions"]) + ", W = " + json.dumps(WALKS) + ";\n"
        "process.stdout.write(JSON.stringify({d: D.map(function(c){ return window.__gr.hook(c[0], c[1] === '1', c[2]); }),"
        " w: W.map(function(c){ return window.__gr.walk(c[0], c[1]); })}));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
JSR = json.loads(node.stdout)
for case, got in zip(PANEL["decisions"], JSR["d"]):
    assert got == case[3:], (case, got)
for case, got in zip(WALKS, JSR["w"]):
    assert got == case[2], (case, got)
N_CHECKED = len(PANEL["decisions"]) + len(WALKS)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "venv": "run in the operator shell, in the kit (once: a venv with the gateway image's Presidio and spaCy model)",
    "trace": "run in the operator shell, in the kit (the gateway's own classifier and hook; no network)",
    "keys": "run in the operator shell, in the kit (the token proxy's token, with the metadata server stood in; no network)",
    "deploy": "run in the operator shell, in the kit where make up ran (it reads the database URL from Terraform's state)",
    "smoke": "run in the operator shell, in the kit",
    "route": "run in the operator shell, in the kit (three short answers through the gateway)",
}
OUT_LABELS = {
    "venv": "(the install's own lines are sent to /dev/null)",
    "trace": "(this cell, run with the gateway image's pins: Presidio 2.2.364 and en_core_web_lg)",
    "keys": "(this cell, run on the kit's own gcp_id_token.py)",
    "deploy": "(gcloud's build and deploy lines are left out)",
    "smoke": "(the kit's own smoke, against a stand-in gateway that serves config.yaml's routes behind the kit's own hook, with the real Presidio; the self-hosted backend is absent, as it is until lesson 9.2)",
    "route": "(this cell, against the same stand-in: your token counts and cost differ)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
opts = lambda pairs, sel: "".join(f'<option value="{html.escape(str(v))}"{" selected" if v == sel else ""}>{html.escape(t)}</option>' for v, t in pairs)  # noqa: E731
STATS = {"N_CHECKED": str(N_CHECKED), "N_RECOG": str(N_RECOG), "N_FAIL": str(N_FAIL), "COST_HDR": COST_HDR, "TIN": str(TIN), "TOUT": str(TOUT),
         "COST": f"{COST:.10f}".rstrip("0"),
         "TEXT_OPTIONS": opts([(i, p["label"]) for i, p in enumerate(PANEL["presets"])], 1),
         "MODEL_OPTIONS": opts([(g, g + (" (the API's)" if g == "documind-general" else "")) for g in ("documind-general", "documind-reasoning", "documind-slm", "documind-inference", "documind-sensitive")], "documind-general"),
         "ENFORCE_OPTIONS": opts([("1", "1 (the lane's)"), ("0", "0 (shadow mode)")], "1"),
         "SLM_OPTIONS": opts([("0", "not deployed (this lesson)"), ("1", "deployed (lesson 9.2)")], "0")}

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
print(f"kit: the classifier and the hook under Presidio {ver[0]}, gcp_id_token.py, make smoke-gateway against the stand-in | "
      f"{N_FAIL} of 5 of the classifier's own cases fail | panel checked on {N_CHECKED} cases")
