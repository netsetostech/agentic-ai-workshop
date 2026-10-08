"""Build lesson 9.3 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Inspect the vLLM service and the GKE alternative. Two more ways to serve the small model sit in the kit, both optional and
neither deployed by a lesson: vLLM on a Cloud Run L4 (services/gemma-vllm, make build-vllm deploy-vllm, the gateway's
documind-inference route), and vLLM on GKE Autopilot (gke/vllm-deployment.yaml, make gke-up, the documind-gke route) -
always on, billed by the node, and the only self-serve L4 in Mumbai. The lesson reads both and decides between them.
Offline: the vLLM service read from its files; the manifest read against the image it runs. Live (read-only): the lane's
cluster described, make gke-up's guard, the vLLM service and image looked for. Then the duty-cycle sum: when an always-on
pod beats an instance billed only while it lives.

Build-time proof: the three offline cells ran on the kit's own files. The live cell ran against gcloud stood in with what
make up leaves (lane183.py, beside this file: gke.tf's defaults, no vLLM service, no image). make gke-up's output is its
recipe's own message. The rates are Google's (Cloud Run, Compute Engine and GKE pricing, 24 September 2026), typed into
the cells and checked against the kit's gke/README.md where it prices the same lines. The panel is the duty-cycle sum,
ported and compared with a Python version on every combination it offers.

    python lessons/09-serving/9.3-vllm-gke/build.py
"""
import html
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "9.3"
title = "<title>Lesson 9.3 Inspect the vLLM service and the GKE alternative - an engine that batches, a pod that never sleeps, the manifest read, the duty-cycle sum | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
REGION = "asia-south1"
VL, GK = "services/gemma-vllm", "gke"
DOCK, CB, MAIN, AUTH, LOGM, MAN, README, PROXY, CFG, GKETF, OFFTF, ALERTS, GWTF, QUOTA, UNOWNED = (
    f"{VL}/Dockerfile", f"{VL}/cloudbuild.yaml", f"{VL}/main.py", f"{VL}/auth.py", f"{VL}/logging_module.py",
    f"{GK}/vllm-deployment.yaml", f"{GK}/README.md", "services/litellm/token_proxy.py", "services/litellm/config.yaml",
    "terraform/gke.tf", "terraform/off.tf", "terraform/alerts.tf", "terraform/gateway.tf", "services/slm/gpu_quota.py", "UNOWNED.md")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.dc-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:0 10px;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,130px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.dc-out{margin:6px 0 0;font-size:12.5px;line-height:1.6;}
.dc-out div{margin:0 0 4px;}
.dc-out .pass{color:var(--teal-dark);font-weight:600;}
.dc-out .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()


# ------------------------------------------------------------------ verbatim excerpts
def span(rel: str, start: str, last: str) -> int:
    lines = (KIT / rel).read_text(encoding="utf-8").split("\n")
    i = next(k for k, line in enumerate(lines) if line.startswith(start))
    return next(k for k in range(i, len(lines)) if lines[k].startswith(last)) - i + 1


EXCERPTS = {
    "deployvllm": ("Makefile - make deploy-vllm: the engine on one L4, 32 requests at a time",
                   block("Makefile", "deploy-vllm: guard-project", n=span("Makefile", "deploy-vllm: guard-project", "	  --startup-probe httpGet.path=/health"))),
    "dockerfile": ("services/gemma-vllm/Dockerfile - the image make build-vllm builds", block(DOCK, "FROM vllm/vllm-openai:v0.28.0", n=19)),
    "engine": ("services/gemma-vllm/main.py - the engine loads the model before the server answers",
               block(MAIN, "    engine_args = AsyncEngineArgs(", n=span(MAIN, "    engine_args = AsyncEngineArgs(", "    app.state.engine = AsyncLLMEngine"))),
    "door": ("services/gemma-vllm/auth.py - the service's own door: a tenant's API key, looked up in Firestore",
             block(AUTH, "async def get_tenant(api_key: str = Security(api_key_header)) -> dict:", n=6)),
    "pod": ("gke/vllm-deployment.yaml - the container the Deployment runs",
            block(MAN, "      containers:", n=span(MAN, "      containers:", "              value: \"1\""))),
    "service": ("gke/vllm-deployment.yaml - the Service in front of it", block(MAN, "kind: Service", n=span(MAN, "kind: Service", "      targetPort: 8080"))),
    "gkeup": ("Makefile - make gke-up: the mode checked first", block("Makefile", "gke-up: guard-project", n=5)),
    "gkeroute": ("services/litellm/config.yaml - the gateway's route to the GKE pod", block(CFG, "  - model_name: documind-gke", n=8)),
}
assert EXCERPTS["deployvllm"][1].rstrip().endswith("periodSeconds=30 --quiet") and "--concurrency 32" in EXCERPTS["deployvllm"][1]
assert EXCERPTS["dockerfile"][1].rstrip().endswith('"--workers", "1", "--timeout-keep-alive", "120"]') and "ENTRYPOINT []" in EXCERPTS["dockerfile"][1]
assert EXCERPTS["engine"][1].rstrip().endswith("app.state.engine = AsyncLLMEngine.from_engine_args(engine_args)") and "gpu_memory_utilization=0.90" in EXCERPTS["engine"][1]
assert EXCERPTS["door"][1].rstrip().endswith('raise HTTPException(status_code=401, detail="Invalid API key")') and 'collection("api_keys")' in EXCERPTS["door"][1]
assert EXCERPTS["pod"][1].rstrip().endswith('value: "1"') and "image: ${IMAGE}" in EXCERPTS["pod"][1] and "- --model=google/gemma-3-4b-it" in EXCERPTS["pod"][1]
assert EXCERPTS["service"][1].rstrip().endswith("targetPort: 8080") and "ClusterIP on purpose." in EXCERPTS["service"][1] and "type:" not in EXCERPTS["service"][1]
assert EXCERPTS["gkeup"][1].rstrip().endswith("kubectl apply -f -") and "STOP: the Standard CPU lab cannot run the L4 GPU lesson." in EXCERPTS["gkeup"][1]
assert EXCERPTS["gkeroute"][1].rstrip().endswith("output_cost_per_token: 0.0000205") and "api_base: os.environ/GKE_VLLM_URL" in EXCERPTS["gkeroute"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (DOCK, CB, MAIN, AUTH, LOGM, MAN, README, PROXY, CFG, GKETF, OFFTF, ALERTS, GWTF, QUOTA, UNOWNED,
                                                          "Makefile", "README.md")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
flat = lambda s: re.sub(r"\s+", " ", s)  # noqa: E731
flatc = lambda s: flat(re.sub(r"\n\s*#\s*", " ", s))  # noqa: E731
def recipe(name: str) -> str:
    """Read a target and its recipe, allowing additional current prerequisites.

    Example: ``recipe('deploy-gateway')`` includes its ``tf-backend`` prerequisite.
    Keep checking the project guard without assuming it is the only dependency.
    """
    match = re.search(rf"^{re.escape(name)}: [^\n]*\bguard-project\b[^\n]*$", MK, re.M)
    assert match, f"missing guarded target: {name}"
    return MK[match.start():].split("\n\n", 1)[0]
DEPLOY_VLLM, DEPLOY_GW, GKEUP, GKEDOWN, OFF = (recipe(n) for n in ("deploy-vllm", "deploy-gateway", "gke-up", "gke-down", "off"))
# the vLLM service
assert "a 13 GB image with the Gemma weights baked (a Hugging Face token with Gemma access in the hf-token secret; 20 to 30 minutes on E2_HIGHCPU_32)" in flatc(MK)
assert "Optional (D3)." in flatc(MK) and "machineType: E2_HIGHCPU_32" in src[CB] and "--build-arg HF_TOKEN=$$HF_TOKEN_SECRET" in src[CB]
assert "ARG " not in src[DOCK] and not re.search(r"huggingface|hf_hub|snapshot_download|wget|curl", src[DOCK], re.I)       # finding 1
assert "--set-env-vars GOOGLE_CLOUD_PROJECT=$(PROJECT) " in DEPLOY_VLLM and "HF_TOKEN" not in DEPLOY_VLLM and "--no-cpu-throttling --cpu-boost" in DEPLOY_VLLM
assert "--max-instances 1 --min-instances 0 --concurrency 32 --timeout 600" in DEPLOY_VLLM and "for sa in documind-gateway-sa documind-ui-sa; do" in DEPLOY_VLLM
assert "initialDelaySeconds=120,failureThreshold=5,timeoutSeconds=10,periodSeconds=30" in DEPLOY_VLLM
assert 'MODEL_NAME = os.getenv("MODEL_NAME", "google/gemma-3-4b-it")' in src[MAIN] and "max_model_len=8192," in src[MAIN]
assert '"--workers", "1"' in src[DOCK] and "# --workers 1 MANDATORY - GPU memory not shareable across processes" in src[DOCK]
assert "with the gemma-3-4b-it weights downloaded at build time - which is what makes HF_HUB_OFFLINE below correct instead of fatal." in flatc(src[MAN])
assert "The manifest runs the image lesson 11.1 builds (weights baked)." in flatc(src[README])
# the door, and who could open it (finding 2)
assert 'api_key_header = APIKeyHeader(name="X-API-Key")' in src[AUTH] and 'collection("tenants")' in src[AUTH]
assert 'HOP = {"host", "authorization", "content-length", "connection", "transfer-encoding"}' in src[PROXY] and "x-api-key" not in src[PROXY].lower()
assert "api_key: unused" in src[CFG].split("- model_name: documind-inference", 1)[1].split("- model_name:", 1)[0]
WRITERS = [p for p in pb.kit_runtime_files("*.py") if "gemma-vllm" not in p.parts and "__pycache__" not in p.parts and 'collection("api_keys")' in p.read_text(encoding="utf-8", errors="ignore")]
assert WRITERS == [], WRITERS
TF = "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "terraform").glob("*.tf")))
assert TF.count("google_service_account.vllm.email") == 1 and 'output "vllm_sa" { value = google_service_account.vllm.email }' in TF       # no role anywhere
assert "11.1 / 11.2's vLLM engine runs as its own account: it serves a model and needs nothing else." in flatc(src[GWTF])
assert 'BQ_TABLE = "project.dataset.inference_logs"' in src[LOGM]
# the manifest (finding 3)
DEP, SVC = src[MAN].split("\n---\n", 1)
assert "command:" not in DEP and re.findall(r"^\s+- (--\S+)$", DEP, re.M)[:2] == ["--model=google/gemma-3-4b-it", "--dtype=bfloat16"]
assert 'name: HF_HUB_OFFLINE\n              value: "1"' in DEP and "replicas: 1" in DEP and "cloud.google.com/gke-accelerator: nvidia-l4" in DEP
assert 'cpu: "6"' in DEP and "memory: 24Gi" in DEP and 'nvidia.com/gpu: "1"' in DEP and "failureThreshold: 60\n            periodSeconds: 10" in DEP
assert "Autopilot rounds up to g2-standard-12 and you silently pay for a bigger node." in flatc(DEP)
assert "IMAGE=$(IMAGE_REPO)/gemma-vllm:latest envsubst < gke/vllm-deployment.yaml | kubectl apply -f -" in GKEUP
assert "IMAGE_REPO = $(REGION)-docker.pkg.dev/$(PROJECT)/documind" in MK
# the documind-gke route (finding 4)
assert not any("GKE_VLLM_URL" in p.read_text(encoding="utf-8", errors="ignore") for p in pb.kit_runtime_files("*") if p.is_file() and p.suffix in (".py", ".tf", ".sh", ".mk", ".yaml", ".yml") and p.name != "config.yaml")
assert "GKE_VLLM_URL" not in MK and "vpc-connector" not in DEPLOY_GW and "--network" not in DEPLOY_GW and "--vpc-egress" not in DEPLOY_GW
assert "Reached through the ClusterIP 11.5's manifest exposes (GKE_VLLM_URL; the cluster sits on the lane's VPC, gke.tf)" in flatc(src[CFG])
assert '    - documind-gke: ["documind-inference", "documind-general"]' in src[CFG] and '    - documind-inference: ["documind-slm", "documind-general"]' in src[CFG]
assert "input_cost_per_token: 0.0000068" in src[CFG]
# the cluster (finding 5)
assert 'variable "gke_autopilot" {\n  type        = bool\n  default     = false' in src[GKETF] and "location   = var.region" in src[GKETF]
assert 'machine_type    = "e2-standard-2" # 2 vCPU, 8 GB RAM; no GPU' in src[GKETF] and 'disk_size_gb    = 30' in src[GKETF] and 'disk_type       = "pd-standard"' in src[GKETF]
assert 'gke_lab_zone = coalesce(var.gke_node_zone, "${var.region}-a")' in src[GKETF] and "node_count     = 1" in src[GKETF]
assert "network    = google_compute_network.vpc.id" in src[GKETF] and "subnetwork = google_compute_subnetwork.subnet.id" in src[GKETF]
assert "The regional control-plane fee and the Standard CPU node continue while provisioned." in flat(src["README.md"])
assert "the GKE lab cluster," in MK.split("ONE SHAPE", 1)[1][:400]
assert 'echo "STOP: the Standard CPU lab cannot run the L4 GPU lesson. Set gke_autopilot=true in Terraform, review cluster replacement and quota, and apply before make gke-up." >&2; exit 1' in GKEUP
assert '@echo "vLLM workload removed; the cluster and any Standard lab node remain (gke.tf) - make down removes them"' in GKEDOWN
# the cost controls (finding 6) and the night job's role (finding 7)
assert 'ap.add_argument("--service", default="run.googleapis.com")' in src[QUOTA] and "--region $(SLM_REGION)" in recipe("gpu-cap")
assert 'for_each     = toset(["documind-slm", "documind-vllm"])' in src[ALERTS] and 'resource.type=\\"cloud_run_revision\\"' in src[ALERTS]
assert "for pair in documind-slm:$SLM_REGION documind-vllm:$SLM_REGION documind-gateway:$REGION documind-ui:$REGION; do" in src[OFFTF]
assert 'echo "documind-autopilot: Terraform\'s since 15 September 2026 (gke.tf) - make gke-down removes the vLLM workload, make down the cluster"' in src[OFFTF]
assert 'role    = "roles/container.clusterAdmin"' in src[OFFTF] and src[OFFTF].count("gcloud container") == 0
assert "-$(MAKE) gke-down PROJECT=$(PROJECT)" in OFF
# the docs behind the code (finding 8)
assert "- **No VPC attachment.** `gke.tf` sets neither `network` nor `subnetwork`" in src[README]
assert "| Autopilot cluster fee (after the free-tier credit) | $0.10 |" in src[README]
assert "| g2-standard-8 (8 vCPU, 32 GiB, 1× L4) | $0.853624 |" in src[README] and "| Autopilot L4 GPU premium | $0.067 / GPU-hr |" in src[README]
assert "| Autopilot vCPU premium | $0.003 × 8 |" in src[README] and "| Autopilot memory premium | $0.00035 × 32 |" in src[README]
assert "**$1.0558/hr → $771/month → ₹65,514/month**" in src[README] and "GKE wins above roughly **74%**" in flat(src[README])
assert "| `terraform/gke.tf` + `gke/` | **11.5** | v2.0 | Autopilot, GPU requested per pod. `vllm-deployment.yaml` pins `vllm/vllm-openai:v0.28.0`, matching 11.1/11.2. |" in src[UNOWNED]

# ------------------------------------------------------------------ Google's rates (24 September 2026) and what they make
RUN_S = 0.0001867 + 8 * 0.000018 + 32 * 0.000002           # Cloud Run, us-central1: L4 without zonal redundancy, 8 vCPU, 32 GiB, USD a second
RUN_H = RUN_S * 3600
NODE = {"us-central1": 0.853624312, "asia-south1": 0.888583031}                          # g2-standard-8 (1 L4, 8 vCPU, 32 GiB), USD an hour
PREM = {"us-central1": [0.067, 0.003, 0.00035], "asia-south1": [0.0804737, 0.0036033, 0.00042]}   # Autopilot accelerator premiums: L4, vCPU, GiB
E2 = {"us-central1": 0.06701142, "asia-south1": 0.08048436}                              # e2-standard-2, USD an hour
FEE, HOURS, INR, IDLE = 0.10, 730, 85, 10
GKE_H = {r: NODE[r] + PREM[r][0] + 8 * PREM[r][1] + 32 * PREM[r][2] for r in NODE}
assert abs(RUN_H - 1.42092) < 1e-9 and abs(GKE_H["us-central1"] - 0.955824312) < 1e-9 and abs(GKE_H["us-central1"] + FEE - 1.0558) < 1e-4
assert round((GKE_H["us-central1"] + FEE) * HOURS) == 771 and abs((GKE_H["us-central1"] + FEE) / RUN_H - 0.743) < 0.001       # the README's own sum
LAB_H = FEE + E2[REGION]

# ------------------------------------------------------------------ steps 3 and 4: the service and the manifest, read (offline)
T = Path(tempfile.mkdtemp(prefix="lesson183-"))
K2 = T / "kit"
for part in ("services/gemma-vllm", "services/litellm", "gke", "terraform", "services/slm", "services/rag-api", "commands", "evals", "smoke", "mk"):
    shutil.copytree(KIT / part, K2 / part, ignore=shutil.ignore_patterns("__pycache__"))
shutil.copy(KIT / "Makefile", K2 / "Makefile")
shutil.copy(HERE / "lane183.py", T / "lane183.py")
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "NUMBER": "NUMBER",
       "REGION": REGION, "HOME": str(T), "USERPROFILE": str(T), "PYTHONPATH": str(T)}


def run(code: str, env: dict | None = None) -> str:
    r = subprocess.run([sys.executable, "-"], input=code, cwd=str(K2), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


VLLM_PY = r'''import glob, os, re
rd = lambda p: open(p, encoding="utf-8").read()
dock, main, auth, logm, proxy, cfg, mk = (rd(p) for p in ("services/gemma-vllm/Dockerfile", "services/gemma-vllm/main.py",
    "services/gemma-vllm/auth.py", "services/gemma-vllm/logging_module.py", "services/litellm/token_proxy.py",
    "services/litellm/config.yaml", "Makefile"))
base = re.search(r"^FROM (\S+)", dock, re.M).group(1)
cmd = " ".join(re.findall(r'"([^"]+)"', re.search(r"CMD \[(.*?)\]", dock, re.S).group(1)))
fetches = [l for l in dock.splitlines() if re.search(r"huggingface|hf_hub|snapshot_download|wget|curl", l, re.I)]
model = re.search(r'os.getenv\("MODEL_NAME", "([^"]+)"\)', main).group(1)
deploy = mk.split("\ndeploy-vllm:", 1)[1].split("\n\n", 1)[0]
flag = dict(re.findall(r"--([a-z-]+) ([^\s-]\S*)", deploy))            # a flag and its value; a bare flag takes none
d, f, p = (int(re.search(k + r"=(\d+)", deploy).group(1)) for k in ("initialDelaySeconds", "failureThreshold", "periodSeconds"))
env_names = [e.split("=")[0] for e in flag["set-env-vars"].split(",")]
print(f"the image: FROM {base}, then {cmd}")
print("  weights in the image: " + ("a download step" if fetches else "none - no step fetches them")
      + ("" if re.search(r"^ARG HF_TOKEN", dock, re.M) else ", and the HF_TOKEN build-arg cloudbuild.yaml passes has no ARG to land in"))
print(f"  so the engine downloads {model} when it starts, from Hugging Face")
print(f"  the environment make deploy-vllm gives it: {', '.join(env_names)} - no Hugging Face token")
print(f"the service: {flag['gpu']} {flag['gpu-type']}, {flag['cpu']} vCPU, {flag['memory']}; {flag['min-instances']} to {flag['max-instances']} instance; "
      f"{flag['concurrency']} requests at a time; startup probe {d} s + {f} x {p} s = {d + f * p} s")
header = re.search(r'APIKeyHeader\(name="([^"]+)"\)', auth).group(1)
cols = list(dict.fromkeys(re.findall(r'collection\("(\w+)"\)', auth)))
print(f"its door: every chat completion needs an {header} header, hashed and looked up in Firestore ({' then '.join(cols)})")
print(f"  what the gateway's token proxy sends: its own ID token as Authorization, and no {header}")
writers = [n for n in glob.glob("**/*.py", recursive=True) if "gemma-vllm" not in n and 'collection("api_keys")' in rd(n)]
print(f"  code elsewhere in the kit that writes an api_keys document: {len(writers) or 'none'}")
grants = sum(rd(t).count("google_service_account.vllm.email") for t in glob.glob("terraform/*.tf")) - 1      # one is the output
print(f"  roles Terraform grants documind-vllm-sa, the account it runs as: {grants or 'none'}")
print("its request log: BigQuery table " + repr(re.search(r'BQ_TABLE = "([^"]+)"', logm).group(1)))
route = cfg.split("- model_name: documind-inference", 1)[1].split("- model_name:", 1)[0]
fall = re.search(r"- documind-inference: \[([^\]]*)\]", cfg).group(1).replace('"', "")
api = re.search(r"api_base: (\S+)", route).group(1)
print(f"the gateway's route to it: documind-inference, {api}, falling back to {fall}")'''
CELLS = {"vllm": "python3 - <<'PY'\n" + VLLM_PY + "\nPY"}
OUT = {"vllm": run(VLLM_PY)}
VO = OUT["vllm"]
assert VO.startswith("the image: FROM vllm/vllm-openai:v0.28.0, then python -m uvicorn main:app --host 0.0.0.0 --port 8080 --workers 1 --timeout-keep-alive 120\n"), VO
assert "  weights in the image: none - no step fetches them, and the HF_TOKEN build-arg cloudbuild.yaml passes has no ARG to land in" in VO, VO
assert "  so the engine downloads google/gemma-3-4b-it when it starts, from Hugging Face" in VO and "gives it: GOOGLE_CLOUD_PROJECT - no Hugging Face token" in VO, VO
assert "the service: 1 nvidia-l4, 8 vCPU, 32Gi; 0 to 1 instance; 32 requests at a time; startup probe 120 s + 5 x 30 s = 270 s" in VO, VO
assert "its door: every chat completion needs an X-API-Key header, hashed and looked up in Firestore (api_keys then tenants)" in VO, VO
assert "writes an api_keys document: none" in VO and "the account it runs as: none" in VO and "its request log: BigQuery table 'project.dataset.inference_logs'" in VO, VO
assert "the gateway's route to it: documind-inference, http://127.0.0.1:8090/vllm/v1, falling back to documind-slm, documind-general" in VO, VO

MANIFEST_PY = r'''import os, re
rd = lambda p: open(p, encoding="utf-8").read()
man, dock, main, mk = rd("gke/vllm-deployment.yaml"), rd("services/gemma-vllm/Dockerfile"), rd("services/gemma-vllm/main.py"), rd("Makefile")
dep, svc = man.split("\n---\n", 1)
val = lambda doc, key: re.search(r"^\s*" + re.escape(key) + r":\s*(.+)$", doc, re.M).group(1).strip().strip('"')
args = re.findall(r"^\s+- (--\S+)$", dep, re.M)
env = dict(re.findall(r'- name: (\S+)\n\s+value: "?([^"\n]+)"?', dep))
sel = re.search(r"nodeSelector:\n\s+(\S+): (\S+)", dep).groups()
repo = re.search(r"^IMAGE_REPO = (\S+)", mk, re.M).group(1)
repo = repo.replace("$(REGION)", os.environ["REGION"]).replace("$(PROJECT)", os.environ["PROJECT"])
sp = dep.split("startupProbe:", 1)[1].split("readinessProbe:", 1)[0]
path = re.search(r"path: ([^,\s]+)", sp).group(1)
fails, period = (int(re.search(k + r": (\d+)", sp).group(1)) for k in ("failureThreshold", "periodSeconds"))
print(f"Deployment {val(dep, 'name')}: {val(dep, 'replicas')} replica, and no autoscaler")
print(f"  its node: nodeSelector {sel[0]}={sel[1]}, so Autopilot provisions an L4 node for the pod")
print(f"  image: {val(dep, 'image')}, which make gke-up fills in: {repo}/gemma-vllm:latest")
print(f"  limits: {val(dep, 'nvidia.com/gpu')} GPU, {val(dep, 'cpu')} vCPU, {val(dep, 'memory')} (requests default to the limits)")
print("  env: " + ", ".join(f"{k}={v}" for k, v in env.items()))
print(f"  startup probe: GET {path} every {period} s, {fails} failures allowed: {fails * period} s to load")
print("  args: " + " ".join(args))
kind = re.search(r"^\s*type: (\S+)", svc, re.M)
ports = re.search(r"port: (\d+)\n\s+targetPort: (\d+)", svc).groups()
print(f"Service {val(svc, 'name')}: {kind.group(1) if kind else 'ClusterIP (no type named, so the default)'}, port {ports[0]} to {ports[1]}: "
      "no address outside the cluster")
entry = re.search(r"^ENTRYPOINT (.+)$", dock, re.M).group(1).strip()
cmd = " ".join(re.findall(r'"([^"]+)"', re.search(r"CMD \[(.*?)\]", dock, re.S).group(1)))
print(f"the image it runs: ENTRYPOINT {entry}, CMD {cmd}")
if entry == "[]" and args and not re.search(r"^\s+command:", dep, re.M):
    print(f"  the manifest sets args and no command, and the ENTRYPOINT is empty: the container runs {args[0]!r} as its program")
reads = sorted(set(re.findall(r'os.getenv\("([A-Z_]+)"', main)))
print(f"  main.py takes its model from the environment ({', '.join(reads)}), and reads none of those args")
print(f"  the image holds no weights (step 3), and HF_HUB_OFFLINE={env['HF_HUB_OFFLINE']} forbids the download")
print("verdict: as written, this pod cannot start")'''
CELLS["manifest"] = "python3 - <<'PY'\n" + MANIFEST_PY + "\nPY"
OUT["manifest"] = run(MANIFEST_PY)
MO = OUT["manifest"]
assert MO.startswith("Deployment documind-vllm: 1 replica, and no autoscaler\n  its node: nodeSelector cloud.google.com/gke-accelerator=nvidia-l4"), MO
assert "  image: ${IMAGE}, which make gke-up fills in: asia-south1-docker.pkg.dev/documind-ai-YOUR-ID/documind/gemma-vllm:latest" in MO, MO
assert "  limits: 1 GPU, 6 vCPU, 24Gi (requests default to the limits)\n  env: HF_HUB_OFFLINE=1\n  startup probe: GET /health every 10 s, 60 failures allowed: 600 s to load" in MO, MO
assert "  args: --model=google/gemma-3-4b-it --dtype=bfloat16 --gpu-memory-utilization=0.90 --max-model-len=4096 --port=8080" in MO, MO
assert "Service documind-vllm: ClusterIP (no type named, so the default), port 80 to 8080: no address outside the cluster" in MO, MO
assert "the container runs '--model=google/gemma-3-4b-it' as its program" in MO and "main.py takes its model from the environment (MODEL_NAME)" in MO, MO
assert MO.rstrip().endswith("verdict: as written, this pod cannot start"), MO

# ------------------------------------------------------------------ step 5: the lane's cluster, inspected (live, read-only)
CLUSTER_PY = r'''import json, os, subprocess
P, R = os.environ["PROJECT"], os.environ["REGION"]


def gc(*args):
    r = subprocess.run(["gcloud", *args, "--project", P, "--format=json"], capture_output=True, text=True)
    return json.loads(r.stdout) if r.returncode == 0 else None


c = gc("container", "clusters", "describe", "documind-autopilot", "--region", R)
auto = (c.get("autopilot") or {}).get("enabled", False)
plane = "regional" if c["location"] == R else "zonal"
print(f"documind-autopilot: {'AUTOPILOT' if auto else 'STANDARD'}, a {plane} control plane in {c['location']}, on {c['network']}, {c['status']}")
for pool in c.get("nodePools", []):
    cfg = pool["config"]
    print(f"  node pool {pool['name']}: {pool['initialNodeCount']} x {cfg['machineType']} in {', '.join(pool['locations'])}, "
          f"{cfg['diskSizeGb']} GB {cfg['diskType']}, GPU: {cfg.get('accelerators') or 'none'}")
E2 = {"us-central1": 0.06701142, "asia-south1": 0.08048436}       # e2-standard-2, USD an hour (Compute Engine pricing, 24 September 2026)
if not auto and plane == "regional" and R in E2:
    hour = 0.10 + E2[R] * c["currentNodeCount"]
    print(f"  what it bills while it exists: $0.10 an hour for the control plane (the free tier covers only zonal and Autopilot "
          f"clusters) + ${E2[R] * c['currentNodeCount']:.4f} for the node = ${hour:.4f} an hour, Rs {hour * 85:.2f}; "
          f"Rs {hour * 85 * 730:,.0f} for a 730-hour month, plus the disk")
v = gc("run", "services", "describe", "documind-vllm", "--region", "us-central1")
print("documind-vllm on Cloud Run (us-central1): " + ("deployed" if v else "not deployed"))
images = gc("artifacts", "docker", "images", "list", f"{R}-docker.pkg.dev/{P}/documind/gemma-vllm")
print(f"the gemma-vllm image in {R}-docker.pkg.dev/{P}/documind: " + (f"{len(images)} version(s)" if images else "not built"))'''
CELLS["cluster"] = "python3 - <<'PY'\n" + CLUSTER_PY + "\nPY"
OUT["cluster"] = run("import lane183\nlane183.install_client()\n" + CLUSTER_PY)
CO = OUT["cluster"]
assert CO.startswith("documind-autopilot: STANDARD, a regional control plane in asia-south1, on documind-vpc, RUNNING\n"), CO
assert "  node pool documind-lab: 1 x e2-standard-2 in asia-south1-a, 30 GB pd-standard, GPU: none" in CO, CO
assert "+ $0.0805 for the node = $0.1805 an hour, Rs 15.34; Rs 11,199 for a 730-hour month, plus the disk" in CO, CO
assert "documind-vllm on Cloud Run (us-central1): not deployed" in CO and f"the gemma-vllm image in asia-south1-docker.pkg.dev/{PROJ}/documind: not built" in CO, CO
CELLS["gkeup"] = 'make gke-up PROJECT="$PROJECT"            # read-only on a Standard lab: it checks the mode and stops'
MKLINES = src["Makefile"].split("\n")
GKEUP_LINE = next(k for k, line in enumerate(MKLINES) if line.startswith("\t@MODE=$$(gcloud container clusters describe documind-autopilot")) + 1
STOP = re.search(r'echo "(STOP: [^"]+)"', GKEUP).group(1)
OUT["gkeup"] = f"{STOP}\nmake: *** [Makefile:{GKEUP_LINE}: gke-up] Error 1\n"

# ------------------------------------------------------------------ step 6: the duty-cycle sum
DUTY_PY = r'''import os
BURSTS, MINUTES, DAYS = (int(os.environ.get(k, d)) for k, d in (("BURSTS", 8), ("MINUTES", 30), ("DAYS", 22)))
IDLE, HOURS, INR = 10, 730, 85                    # Cloud Run keeps an idle GPU instance up to 10 minutes; a month; rupees a dollar
RUN = (0.0001867 + 8 * 0.000018 + 32 * 0.000002) * 3600     # Cloud Run, us-central1: L4, 8 vCPU, 32 GiB, USD an hour
GKE = {"us-central1": (0.853624312, 0.067, 0.003, 0.00035),   # g2-standard-8, then Autopilot's L4, vCPU and GiB premiums, USD an hour
       "asia-south1": (0.888583031, 0.0804737, 0.0036033, 0.00042)}
gap = 24 * 60 / BURSTS - MINUTES
lives = min(24 * 60, BURSTS * (MINUTES + min(IDLE, max(gap, 0))))    # minutes a day an instance is up, and billed
hours = lives / 60 * DAYS
print(f"your pattern: {BURSTS} bursts a day of {MINUTES} minutes, on {DAYS} days a month")
print(f"Cloud Run, on demand: each burst, then up to {IDLE} idle minutes - an instance lives {lives:.0f} minutes a day")
print(f"  the duty-cycle sum: {lives:.0f} min x {DAYS} days = {hours:.1f} hours of {HOURS} ({hours / HOURS:.1%}) x ${RUN:.4f} = "
      f"${hours * RUN:,.2f}, Rs {hours * RUN * INR:,.0f} a month")
print(f"GKE Autopilot, always on, for all {HOURS} hours:")
least = None
for region, (node, l4, vcpu, gib) in GKE.items():
    hour = node + l4 + 8 * vcpu + 32 * gib
    month, fee_month = hour * HOURS * INR, (hour + 0.10) * HOURS * INR
    least = min(least or month, month)
    print(f"  {region:12} ${hour:.4f} an hour (node {node:.4f} + L4 {l4:.4f} + 8 vCPU {8 * vcpu:.4f} + 32 GiB {32 * gib:.4f}): "
          f"Rs {month:,.0f}; with the $0.10 cluster fee, Rs {fee_month:,.0f}")
    print(f"  {'':12} cheaper than Cloud Run above {hour / RUN:.1%} of the month ({(hour + 0.10) / RUN:.1%} with the fee)")
print(f"at {hours / HOURS:.1%}: " + (f"Cloud Run is cheaper - Rs {hours * RUN * INR:,.0f} against Rs {least:,.0f} for the cheapest GKE line"
      if hours * RUN * INR < least else "GKE is cheaper: an instance that lives this long is a pod that never sleeps"))'''
CELLS["duty"] = "BURSTS=8 MINUTES=30 DAYS=22 python3 - <<'PY'      # your own pattern: change the three numbers\n" + DUTY_PY + "\nPY"
OUT["duty"] = run(DUTY_PY, {"BURSTS": "8", "MINUTES": "30", "DAYS": "22"})
DO = OUT["duty"]
assert "an instance lives 320 minutes a day" in DO and "the duty-cycle sum: 320 min x 22 days = 117.3 hours of 730 (16.1%) x $1.4209 = $166.72, Rs 14,171 a month" in DO, DO
assert "  us-central1  $0.9558 an hour (node 0.8536 + L4 0.0670 + 8 vCPU 0.0240 + 32 GiB 0.0112): Rs 59,309; with the $0.10 cluster fee, Rs 65,514" in DO, DO
assert "cheaper than Cloud Run above 67.3% of the month (74.3% with the fee)" in DO and "cheaper than Cloud Run above 71.2% of the month (78.2% with the fee)" in DO, DO
assert "  asia-south1  $1.0113 an hour" in DO and "Rs 62,753; with the $0.10 cluster fee, Rs 68,958" in DO, DO
assert DO.rstrip().endswith("at 16.1%: Cloud Run is cheaper - Rs 14,171 against Rs 59,309 for the cheapest GKE line"), DO
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ the panel: the duty-cycle sum, ported
def duty(bursts: int, minutes: int, days: int, region: str, fee: float) -> list:
    gap = 24 * 60 / bursts - minutes
    lives = min(24 * 60, bursts * (minutes + min(IDLE, max(gap, 0))))
    hours = lives / 60 * days
    gke = NODE[region] + PREM[region][0] + 8 * PREM[region][1] + 32 * PREM[region][2] + fee
    return [lives, hours * RUN_H, gke * HOURS, hours / HOURS, gke / RUN_H]


BURSTS_OPT, MIN_OPT, DAYS_OPT, FEES = [1, 2, 4, 8, 16, 24, 48], [5, 15, 30, 60, 120], [22, 30], [0, FEE]
CASES = [[b, m, d, r, f, duty(b, m, d, r, f)] for b in BURSTS_OPT for m in MIN_OPT for d in DAYS_OPT for r in NODE for f in FEES]
assert duty(8, 30, 22, "us-central1", 0)[0] == 320 and duty(48, 60, 30, "asia-south1", FEE)[0] == 1440
assert any(c[5][1] > c[5][2] for c in CASES) and any(c[5][1] < c[5][2] for c in CASES)          # both verdicts occur
UI_JS = r"""var root = document.getElementById('dc'); if (!root) return;
  var RUN_H = __RUN__, NODE = __NODE__, PREM = __PREM__, IDLE = __IDLE__, HOURS = __HOURS__, INR = 85, FEE = __FEE__;
  function duty(bursts, minutes, days, region, fee){ var gap = 24 * 60 / bursts - minutes;
    var lives = Math.min(24 * 60, bursts * (minutes + Math.min(IDLE, Math.max(gap, 0)))), hours = lives / 60 * days;
    var gke = NODE[region] + PREM[region][0] + 8 * PREM[region][1] + 32 * PREM[region][2] + fee;
    return [lives, hours * RUN_H, gke * HOURS, hours / HOURS, gke / RUN_H]; }
  window.__dc = {duty: duty};
  var $ = function(id){ return document.getElementById(id); };
  function line(out, cls, text){ var d = document.createElement('div'); if (cls) { d.className = cls; } d.textContent = text; out.appendChild(d); }
  function rs(usd){ return 'Rs ' + Math.round(usd * INR).toLocaleString('en-IN'); }
  function pct(x){ return (x * 100).toFixed(1) + '%'; }
  function show(){ var b = Number($('dc-bursts').value), m = Number($('dc-minutes').value), d = Number($('dc-days').value), region = $('dc-region').value, fee = Number($('dc-fee').value);
    var r = duty(b, m, d, region, fee), gap = 24 * 60 / b - m, tail = Math.min(IDLE, Math.max(gap, 0));
    var a = $('dc-run'), g = $('dc-gke'), v = $('dc-sum'); a.textContent = ''; g.textContent = ''; v.textContent = '';
    line(a, '', b + ' burst' + (b > 1 ? 's' : '') + ' a day of ' + m + ' minutes, each followed by ' + (tail === IDLE ? 'up to ' + IDLE + ' idle minutes' : (tail > 0 ? tail.toFixed(0) + ' idle minutes before the next' : 'no idle gap: the next burst is already due')) + '.');
    line(a, '', 'An instance lives ' + Math.round(r[0]) + ' minutes a day' + (r[0] >= 1440 ? ': all day' : '') + ', on ' + d + ' days: ' + (r[0] / 60 * d).toFixed(1) + ' hours a month.');
    line(a, 'pass', 'The duty cycle: ' + pct(r[3]) + ' of ' + HOURS + ' hours, at $' + RUN_H.toFixed(4) + ' an hour: ' + rs(r[1]) + ' a month.');
    line(g, '', 'A g2-standard-8 node with one L4 in ' + region + ', billed whole: $' + NODE[region].toFixed(4) + ', plus Autopilot\'s premiums: L4 $' + PREM[region][0].toFixed(4) + ', 8 vCPU $' + (8 * PREM[region][1]).toFixed(4) + ', 32 GiB $' + (32 * PREM[region][2]).toFixed(4) + (fee ? ', and the $0.10 cluster fee.' : '. The free tier pays the cluster fee.'));
    line(g, '', 'Always on: $' + (r[2] / HOURS).toFixed(4) + ' an hour for all ' + HOURS + ' hours, the model in the GPU at 3 a.m. too, and no cold start.');
    line(g, 'pass', rs(r[2]) + ' a month.');
    var cheaper = r[1] < r[2];
    line(v, cheaper ? 'pass' : 'stop', (cheaper ? 'Cloud Run is cheaper, by ' : 'GKE is cheaper, by ') + rs(Math.abs(r[2] - r[1])) + ' a month.');
    line(v, '', 'GKE wins above ' + pct(r[4]) + ' of the month: an instance alive about ' + (r[4] * 24).toFixed(1) + ' hours of every 24.');
    line(v, '', region === 'asia-south1' ? 'In Mumbai only GKE is self-serve: Cloud Run\'s L4 there is by invitation, so this line compares a pod in Mumbai with an instance in Iowa.' : 'Both in us-central1: the same region, the same L4.'); }
  ['dc-bursts', 'dc-minutes', 'dc-days', 'dc-region', 'dc-fee'].forEach(function(id){ $(id).addEventListener('change', show); });
  show();"""
UI_JS = (UI_JS.replace("__RUN__", repr(RUN_H)).replace("__NODE__", json.dumps(NODE)).replace("__PREM__", json.dumps(PREM))
         .replace("__IDLE__", str(IDLE)).replace("__HOURS__", str(HOURS)).replace("__FEE__", repr(FEE)))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
PORT_JS = UI_JS.split("var $ = function(id)")[0].replace("var root = document.getElementById('dc'); if (!root) return;", "")
NODE_JS = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
           "var C = " + json.dumps([c[:5] for c in CASES]) + ";\n"
           "process.stdout.write(JSON.stringify(C.map(function(c){ return window.__dc.duty(c[0], c[1], c[2], c[3], c[4]); })));\n")
node = subprocess.run(["node", "-"], input=NODE_JS, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
for case, got in zip(CASES, json.loads(node.stdout)):
    assert all(abs(x - y) < 1e-9 for x, y in zip(got, case[5])), (case, got)
N_CHECKED = len(CASES)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "vllm": "run in the operator shell, in the kit (reads the service's files; no network)",
    "manifest": "run in the operator shell, in the kit (reads the manifest and the image it runs; no network)",
    "cluster": "run in the operator shell, in the kit (read-only: describes the lane's cluster, looks for the vLLM service and image)",
    "gkeup": "run in the operator shell, in the kit (it stops before changing anything on a Standard lab)",
    "duty": "run in the operator shell (arithmetic only; no network)",
}
OUT_LABELS = {
    "vllm": "(this cell, run on the kit's own files)",
    "manifest": "(this cell, run on the kit's own files)",
    "cluster": "(this cell, against gcloud stood in with what make up leaves: gke.tf's defaults, no vLLM service, no image; your region's node price may differ)",
    "gkeup": "(the recipe's own message on a Standard lab)",
    "duty": "(this cell, with the pattern above: 8 bursts of 30 minutes on 22 days)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
opts = lambda pairs, sel: "".join(f'<option value="{html.escape(str(v))}"{" selected" if v == sel else ""}>{html.escape(t)}</option>' for v, t in pairs)  # noqa: E731
X = {r: GKE_H[r] / RUN_H for r in NODE}
XF = {r: (GKE_H[r] + FEE) / RUN_H for r in NODE}
STATS = {"N_CHECKED": str(N_CHECKED), "RUN_H": f"{RUN_H:.4f}", "RUN_INR": f"{RUN_H * INR:.2f}",
         "GKE_US": f"{GKE_H['us-central1']:.4f}", "GKE_IN": f"{GKE_H['asia-south1']:.4f}",
         "X_US": f"{X['us-central1']:.1%}", "XF_US": f"{XF['us-central1']:.1%}", "X_IN": f"{X['asia-south1']:.1%}", "XF_IN": f"{XF['asia-south1']:.1%}",
         "LAB_H": f"{LAB_H:.4f}", "LAB_INR_H": f"{LAB_H * INR:.2f}", "LAB_MONTH": f"{LAB_H * INR * HOURS:,.0f}",
         "GKE_US_MONTH": f"{GKE_H['us-central1'] * HOURS * INR:,.0f}", "GKE_IN_MONTH": f"{GKE_H['asia-south1'] * HOURS * INR:,.0f}",
         "BURSTS_OPTIONS": opts([(b, f"{b} a day") for b in BURSTS_OPT], 8),
         "MINUTES_OPTIONS": opts([(m, f"{m} minutes") for m in MIN_OPT], 30),
         "DAYS_OPTIONS": opts([(22, "22 (working days)"), (30, "30 (every day)")], 22),
         "REGION_OPTIONS": opts([("us-central1", "us-central1 (Iowa)"), ("asia-south1", "asia-south1 (Mumbai)")], "asia-south1"),
         "FEE_OPTIONS": opts([(0, "paid by the free tier"), (FEE, "$0.10 an hour")], 0)}
assert (STATS["X_US"], STATS["XF_US"], STATS["X_IN"], STATS["XF_IN"]) == ("67.3%", "74.3%", "71.2%", "78.2%"), STATS
assert STATS["LAB_MONTH"] == "11,199" and STATS["RUN_INR"] == "120.78"

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
print(f"kit: the vLLM service and the manifest read from the kit's files, the lane's cluster against gcloud stood in | "
      f"GKE wins above {STATS['X_US']} to {STATS['XF_IN']} | panel checked on {N_CHECKED} cases")
