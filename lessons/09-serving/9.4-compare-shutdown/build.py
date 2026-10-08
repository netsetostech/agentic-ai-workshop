"""Build lesson 9.4 from its three parts, the shared template, the 1.1 setup section and verbatim kit excerpts.

Compare actual backends and verify shutdown behavior. make compare asks the same golden questions of each backend through
the gateway (services/slm/compare_backends.py): one retrieval per question - the API's own answer, whose citations'
quotes become every backend's context - then each route answers, and the script prints four numbers a backend:
groundedness, citation precision, p95 latency and rupees per 1k queries, the small model's at a RATE. A row is labelled
and priced by the route it asked for; nothing reads which model answered. Then the lane is switched off (make off: four
floors to zero and the GKE workload removed) and proved off: min-instances is a floor, so the proof is Cloud Monitoring's
instance_count after the idle window.
Offline: the kit's own selftest; what a row reads and what it cannot see. Live: the comparison with a recorder beside it
(the route asked, the model that answered, the gateway's price), with the vLLM route included; make off; zero GPU
instances.

Build-time proof: the comparison cell ran the kit's own compare_backends.live(), summarise() and print_summary(), with
shared/documind_tools.retrieve(), against a stand-in lane (lane184.py, beside this file): an API whose citations are the
kit's own chunks, a gateway with config.yaml's rates in which the vLLM route falls back to the small model, and Cloud
Monitoring. make off's output is its recipes' own lines. The panel is the rate against the GPU's hour, ported and
compared with a Python version on every combination it offers.

    python lessons/09-serving/9.4-compare-shutdown/build.py
"""
import contextlib
import html
import io
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
from datetime import timedelta
from pathlib import Path

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
from pagekit import pagebuild as pb  # noqa: E402
from pagekit.pagebuild import KIT, block, filler, finish, setup_section, window  # noqa: E402,F401

LESSON = "9.4"
title = "<title>Lesson 9.4 Compare actual backends and verify shutdown behavior - one table, the model behind each row, a floor that is not a count, zero GPU instances | Netsetos</title>\n"
PROJ = "documind-ai-YOUR-ID"
REGION = "asia-south1"
GATEWAY = f"https://documind-gateway-NUMBER.{REGION}.run.app"
API = f"https://documind-api-NUMBER.{REGION}.run.app"
MON = "https://monitoring.googleapis.com"
CB, DT, CFG, ALERTS, OFFTF = ("services/slm/compare_backends.py", "shared/documind_tools.py", "services/litellm/config.yaml",
                              "terraform/alerts.tf", "terraform/off.tf")

EXTRA_CSS = """/* the embed never shows its own vertical scrollbar: the host sizes the frame from the height handshake, and if it does not, the content still scrolls by wheel and touch without a bar */
html,body{scrollbar-width:none;-ms-overflow-style:none;}
html::-webkit-scrollbar,body::-webkit-scrollbar{width:0;height:0;display:none;}
.ro{font-family:var(--mono);font-size:var(--chip-size);color:#fcd34d;border:1px dashed #475569;padding:3px 10px;border-radius:5px;white-space:nowrap;}
.rb-cols{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,210px),1fr));gap:0 10px;}
.pc-in{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,130px),1fr));gap:8px 12px;margin:6px 0;}
.pc-in label{font-size:var(--small-size);color:var(--navy);display:flex;flex-direction:column;gap:4px;min-width:0;}
.pc-in select{font:inherit;font-size:16px;padding:6px 8px;border:1px solid var(--border);border-radius:8px;background:var(--card);min-height:44px;max-width:100%;box-sizing:border-box;}
.pc-box{background:var(--card);border:1px solid var(--border);border-radius:10px;padding:8px 12px;margin:0 0 10px;font-size:12.5px;line-height:1.55;color:var(--slate);min-width:0;overflow-wrap:anywhere;}
.pc-box b.h{display:block;color:var(--navy);font-family:var(--mono);font-size:var(--kicker-size);letter-spacing:1px;text-transform:uppercase;margin:6px 0 4px;}
.rb-out{margin:6px 0 0;font-size:12.5px;line-height:1.6;}
.rb-out div{margin:0 0 4px;}
.rb-out .pass{color:var(--teal-dark);font-weight:600;}
.rb-out .stop{color:#9a3412;font-weight:600;}
"""

setup = setup_section()


# ------------------------------------------------------------------ verbatim excerpts
def span(rel: str, start: str, last: str) -> int:
    lines = (KIT / rel).read_text(encoding="utf-8").split("\n")
    i = next(k for k, line in enumerate(lines) if line.startswith(start))
    return next(k for k in range(i, len(lines)) if lines[k].startswith(last)) - i + 1


EXCERPTS = {
    "compare": ("Makefile - make compare: the gateway, a token for it, and the API to retrieve from",
                block("Makefile", "compare: guard-project", n=span("Makefile", "compare: guard-project", "	  $(PY) services/slm/compare_backends.py --summary compare.csv"))),
    "row": ("services/slm/compare_backends.py - live(): one retrieval, then every backend, one row each",
            block(CB, "        got = documind_tools.retrieve(r[\"question\"]", n=span(CB, "        got = documind_tools.retrieve(r[\"question\"]", "                          \";\".join(cited_ids(draft, chunks))"))),
    "ask": ("services/slm/compare_backends.py - ask(): the route by name, the context from the citations' quotes",
            block(CB, "    context = \"\\n\".join(f\"[Source {i}]", n=5)),
    "retrieve": ("shared/documind_tools.py - retrieve(): the API's own answer, and what a failure becomes",
                 block(DT, "        resp = requests.post(f\"{RAG_API_URL}/v1/query\"", n=span(DT, "        resp = requests.post(f\"{RAG_API_URL}/v1/query\"", "                \"citations\": [], \"answerable\": False, \"confidence\": \"low\"}"))),
    "off": ("Makefile - make off: four floors to zero, the GKE workload removed, then the floors printed",
            block("Makefile", "# The four switches in one, then the lines that prove it.", n=8)),
    "alarm": ("terraform/alerts.tf - the one place the kit reads an instance count", block(ALERTS, "# Cost control (10 September 2026): a GPU service left warm.", n=5)),
}
assert EXCERPTS["compare"][1].rstrip().endswith("$(PY) services/slm/compare_backends.py --summary compare.csv") and "--backends $${BACKENDS:-documind-general,documind-slm}" in EXCERPTS["compare"][1]
assert EXCERPTS["row"][1].rstrip().endswith('";".join(cited_ids(draft, chunks)), ";".join(r.get("must_retrieve", []))])') and 'f"{cost_inr(backend, tok_in, tok_out):.4f}"' in EXCERPTS["row"][1]
assert EXCERPTS["ask"][1].rstrip().endswith('{"role": "user", "content": f"Context:\\n{context}\\n\\nQuestion: {question}"}]})') and '"model": backend' in EXCERPTS["ask"][1]
assert EXCERPTS["retrieve"][1].rstrip().endswith('"citations": [], "answerable": False, "confidence": "low"}') and "timeout=RAG_TIMEOUT_S" in EXCERPTS["retrieve"][1]
assert EXCERPTS["off"][1].rstrip().endswith("-$(MAKE) gke-down PROJECT=$(PROJECT)") and "-$(MAKE) slm-off PROJECT=$(PROJECT)" in EXCERPTS["off"][1]
assert EXCERPTS["alarm"][1].rstrip().endswith("that is the reminder, not a bug.") and "instance_count is a gauge of a service's container" in EXCERPTS["alarm"][1]
fill = filler(EXCERPTS, window)

# ------------------------------------------------------------------ the kit's facts the page states
src = {p: (KIT / p).read_text(encoding="utf-8") for p in (CB, DT, CFG, ALERTS, OFFTF, "Makefile")}
MK = src["Makefile"] + "".join(p.read_text(encoding="utf-8") for p in sorted((KIT / "mk").glob("*.mk")))
flat = lambda s: re.sub(r"\s+", " ", s)  # noqa: E731
flatc = lambda s: flat(re.sub(r"\n\s*#\s*", " ", s))  # noqa: E731
recipe = lambda name: MK[MK.index(f"\n{name}: guard-project\n") + 1:].split("\n\n", 1)[0]  # noqa: E731
COMPARE, OFF = recipe("compare"), recipe("off")
assert "the same golden rows, retrieval once through the one retrieve(), every backend answering from the same context through the gateway." in flatc(MK)
assert "The four numbers, and the SLM's rupees are a RATE." in flatc(MK) and "--rows $${ROWS:-20}" in COMPARE
assert "The four switches in one, then the lines that prove it." in flatc(MK) and "so a forgotten GPU costs an evening, not a month" in flatc(MK)
assert "the only variable between rows is the model" in flatc(src[CB]) and "Cost per token for documind-slm is a RATE, not a price" in flatc(src[CB])
assert "At Rs 86,904/month and ~50M tokens/month that is ~Rs 0.0017 per token, either direction. A RATE, not a price: idle time is the variable." in flatc(src[CB])
assert "p95 latency (ms) the number a dashboard alerts on, not the mean" in flat(src[CB]) and "Rs per 1k queries mean cost x 1000" in flat(src[CB])
# finding 1: a row is the route asked, priced by the script; the reply's model and the gateway's cost header are never read
ASK = src[CB].split("def ask(", 1)[1].split("\ndef ", 1)[0]
assert 'body.get("model")' not in src[CB] and 'body["model"]' not in src[CB] and "x-litellm-response-cost" not in src[CB].lower()
assert "def cost_inr(model: str, tok_in: int, tok_out: int) -> float:\n    pin, pout = PRICES.get(model, PRICES[\"documind-general\"])" in src[CB]
# finding 2: the context is the API's own answer's quotes
assert 'context = "\\n".join(f"[Source {i}] {c.get(\'quote\') or c.get(\'text\', \'\')}"' in ASK
assert 'resp = requests.post(f"{RAG_API_URL}/v1/query", json=payload, headers=headers,' in src[DT] and '"citations": [{k: c[k] for k in CITATION_KEYS if k in c}' in src[DT]
# finding 3: 20 s, then an empty context and a warning
assert 'RAG_TIMEOUT_S = float(os.environ.get("RAG_TIMEOUT_S", "20"))' in src[DT] and 'logger.warning("retrieve failed: %s", exc)' in src[DT]
assert "RAG_TIMEOUT_S" not in COMPARE
# finding 4: the vLLM route has no price in the script
PRICES = {k: (float(a), float(b)) for k, a, b in re.findall(r'"(documind-[a-z]+)": \(([\d.]+), ([\d.]+)\)', src[CB])}
assert set(PRICES) == {"documind-general", "documind-slm", "documind-gke"} and PRICES["documind-slm"] == (20.5, 20.5), PRICES
assert "model: hosted_vllm/google/gemma-3-4b-it\n      api_base: http://127.0.0.1:8090/vllm/v1" in src[CFG] and "input_cost_per_token: 0.0000068" in src[CFG]
assert '    - documind-inference: ["documind-slm", "documind-general"]' in src[CFG]
# finding 5: p95 on 20 rows is the second-slowest
P95 = "        p95 = lat[max(0, int(round(0.95 * len(lat))) - 1)] if lat else 0"
assert P95 in src[CB] and max(0, int(round(0.95 * 20)) - 1) == 18
# finding 7: the table never scores a refusal - groundedness leaves them out, and make compare's 20 rows are all answerable
GOLD = [json.loads(line) for line in (KIT / "evals/golden.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
assert all(r["answerable"] for r in GOLD[:20]) and not all(r["answerable"] for r in GOLD)
SUMMARISE = src[CB].split("def summarise(", 1)[1].split("\ndef ", 1)[0]
assert 'grounded = [int(r["grounded"]) for r in answerable]' in SUMMARISE and "refus" not in SUMMARISE.split('out[backend] = {', 1)[1]
# finding 6: make off prints floors; nothing but the two-hour alarm reads an instance count
assert "get('autoscaling.knative.dev/minScale','0')" in OFF and 'echo "$$s: min-instances $$f"; done' in OFF
READERS = [p for p in pb.kit_runtime_files("*") if p.is_file() and p.suffix in (".py", ".sh", ".mk", ".tf", ".yaml", ".yml") and "container/instance_count" in p.read_text(encoding="utf-8", errors="ignore")]
assert [p.name for p in READERS] == ["alerts.tf"], READERS
assert 'duration        = "7200s"' in src[ALERTS] and 'for_each     = toset(["documind-slm", "documind-vllm"])' in src[ALERTS]
assert "sets min-instances 0 on documind-slm, documind-vllm, documind-gateway and documind-ui wherever a floor is above zero" in flatc(src[OFFTF])
assert "--min-instances 0 --quiet" in recipe("slm-off") and "--max-instances 1 --min-instances 0" in recipe("deploy-slm")

# ------------------------------------------------------------------ step 3: the table's maths, read (offline)
T = Path(tempfile.mkdtemp(prefix="lesson184-"))
K2 = T / "kit"
for part in ("services/slm", "services/litellm", "shared", "evals", "smoke", "mk", "terraform"):
    shutil.copytree(KIT / part, K2 / part, ignore=shutil.ignore_patterns("__pycache__"))
shutil.copy(KIT / "Makefile", K2 / "Makefile")
shutil.copy(HERE / "lane184.py", T / "lane184.py")
ENV = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1", "PYTHONDONTWRITEBYTECODE": "1", "PROJECT": PROJ, "NUMBER": "NUMBER",
       "REGION": REGION, "HOME": str(T), "USERPROFILE": str(T), "PYTHONPATH": str(T)}


def run(code: str, env: dict | None = None, args: list | None = None) -> str:
    cmd = [sys.executable] + (args or ["-"])
    r = subprocess.run(cmd, input=code, cwd=str(K2), capture_output=True, text=True, encoding="utf-8", env={**ENV, **(env or {})})
    assert r.returncode == 0 and not r.stderr.strip(), (r.returncode, r.stdout[-1500:], r.stderr[-3000:])
    return r.stdout


CELLS = {"selftest": "python services/slm/compare_backends.py --selftest"}
OUT = {"selftest": run("", args=["services/slm/compare_backends.py", "--selftest"])}
ST = OUT["selftest"]
assert ST.rstrip().endswith("selftest OK - groundedness excludes refusal rows, precision is per cited chunk, p95 is the 95th latency, Rs/1k is mean cost x 1000"), ST
assert "documind-slm          3         1.000           0.500     3100        1951.33" in ST, ST
READ_PY = r'''import re
rd = lambda p: open(p, encoding="utf-8").read()
cb, dt, cfg, mk = rd("services/slm/compare_backends.py"), rd("shared/documind_tools.py"), rd("services/litellm/config.yaml"), rd("Makefile")
ask = cb.split("def ask(", 1)[1].split("\ndef ", 1)[0]
backends = re.search(r"BACKENDS:-([\w,-]+)\}", mk).group(1)
print(f"a row asks the gateway for a route by name: {backends.replace(',', ', ')} (make compare's default)")
print("  its context: the citations' quotes of the API's own answer - retrieve() posts to "
      + re.search(r'requests\.post\(f"\{RAG_API_URL\}(/v1/\w+)"', dt).group(1))
wait = re.search(r'"RAG_TIMEOUT_S", "(\d+)"', dt).group(1)
print(f"  if that answer takes more than {wait} s, the row's context is empty, and only the log says so")
reads = [k for k in ("model", "x-litellm-response-cost") if f'"{k}")' in ask or f'["{k}"]' in ask]
print("from the gateway's reply a row keeps the answer and the token counts, and reads "
      + (", ".join(reads) if reads else "neither the model that answered nor x-litellm-response-cost"))
prices = {k: (float(a), float(b)) for k, a, b in re.findall(r'"(documind-[a-z]+)": \(([\d.]+), ([\d.]+)\)', cb)}
rates, group = {}, None
for line in cfg.splitlines():
    m = re.match(r"  - model_name: (\S+)", line)
    group = m.group(1) if m else group
    m = re.match(r"\s+(input|output)_cost_per_token: ([\d.]+)", line)
    if m:
        rates.setdefault(group, {})[m.group(1)] = float(m.group(2)) * 1e6
print("its price is the script's own, by the route asked (USD a million tokens, in / out):")
for route, r in rates.items():
    pin, pout = prices.get(route, prices["documind-general"])
    note = "" if route in prices else "  <- no entry: documind-general's"
    print(f"  {route:19} table {pin:5.2f} / {pout:5.2f}   config.yaml {r['input']:5.2f} / {r['output']:5.2f}{note}")
n = 20
print(f"p95 on {n} rows is sorted row {max(0, int(round(0.95 * n)) - 1) + 1} of {n}: the slowest row never shows")'''
CELLS["read"] = "python - <<'PY'\n" + READ_PY + "\nPY"
OUT["read"] = run(READ_PY)
RD = OUT["read"]
assert RD.startswith("a row asks the gateway for a route by name: documind-general, documind-slm (make compare's default)\n"), RD
assert "retrieve() posts to /v1/query" in RD and "more than 20 s, the row's context is empty" in RD, RD
assert "reads neither the model that answered nor x-litellm-response-cost" in RD, RD
assert "  documind-inference  table  1.50 /  7.50   config.yaml  6.80 /  6.80  <- no entry: documind-general's" in RD, RD
assert "  documind-reasoning  table  1.50 /  7.50   config.yaml  2.00 / 12.00  <- no entry: documind-general's" in RD, RD
assert "  documind-slm        table 20.50 / 20.50   config.yaml 20.50 / 20.50\n" in RD and RD.rstrip().endswith("p95 on 20 rows is sorted row 19 of 20: the slowest row never shows"), RD


# ------------------------------------------------------------------ steps 4 and 6: the stand-in lane
def free_port() -> int:
    s = socket.socket()
    s.bind(("127.0.0.1", 0))
    port = s.getsockname()[1]
    s.close()
    return port


P_API, P_GW, P_MON = free_port(), free_port(), free_port()
LANE = {"LANE184_API": f"{API}=http://127.0.0.1:{P_API}", "LANE184_GATEWAY": f"{GATEWAY}=http://127.0.0.1:{P_GW}",
        "LANE184_MONITORING": f"{MON}=http://127.0.0.1:{P_MON}"}
servers = [subprocess.Popen([sys.executable, str(T / "lane184.py"), kind, str(port)] + extra, cwd=str(T), stdout=subprocess.DEVNULL,
                            stderr=subprocess.PIPE, env=ENV)
           for kind, port, extra in (("api", P_API, [str(K2)]), ("gateway", P_GW, [str(K2)]), ("monitoring", P_MON, []))]
for port, proc in zip((P_API, P_GW, P_MON), servers):
    for _ in range(600):
        try:
            socket.create_connection(("127.0.0.1", port), timeout=1).close()
            break
        except OSError:
            assert proc.poll() is None, proc.stderr.read().decode()[-2000:]
            time.sleep(0.5)
sys.path.insert(0, str(T))
import lane184  # noqa: E402
CLIENT = ("import os, lane184\nlane184.install_client()\n"
          f"os.environ['RAG_API_URL'] = '{API}'                     # what the cell sets too; the module reads it once, at import\n"
          "import shared.documind_tools as _dt\n"
          "_dt._id_token = lambda audience: 'tok:' + audience          # google-auth's impersonation, stood in\n")
try:
    # ---- step 4: the comparison, with a recorder beside it
    COMPARE_PY = r'''import collections, contextlib, csv, os, subprocess, sys
P, R = os.environ["PROJECT"], os.environ["REGION"]
N = subprocess.run(["gcloud", "projects", "describe", P, "--format=value(projectNumber)"], capture_output=True, text=True, check=True).stdout.strip()
GW, API, UI = f"https://documind-gateway-{N}.{R}.run.app", f"https://documind-api-{N}.{R}.run.app", f"documind-ui-sa@{P}.iam.gserviceaccount.com"
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--impersonate-service-account={UI}", f"--audiences={GW}"],
                     capture_output=True, text=True, check=True).stdout.strip()
os.environ.update(LITELLM_URL=GW, LITELLM_ID_TOKEN=tok, RAG_API_URL=API, DOCUMIND_IMPERSONATE_SA=UI, GOOGLE_CLOUD_PROJECT=P)   # make compare's
sys.path.insert(0, "services/slm")
import requests
import compare_backends as cb
seen, post = [], requests.post                    # what the table does not keep: the model that answered, and the gateway's price


def recorded(url, **kw):
    r = post(url, **kw)
    if url.endswith("/v1/chat/completions"):
        seen.append((kw["json"]["model"], r.json().get("model"), float(r.headers.get("x-litellm-response-cost") or 0)))
    return r


requests.post = recorded
BACKENDS = "documind-general,documind-slm,documind-inference"
args = type("Args", (), {"golden": "evals/golden.jsonl", "rows": 20, "backends": BACKENDS})
with open("compare.csv", "w", newline="", encoding="utf-8") as f, contextlib.redirect_stdout(f):
    cb.live(args)                                 # make compare's own pass, row for row
rows = list(csv.DictReader(open("compare.csv", encoding="utf-8")))
cb.print_summary(cb.summarise(rows))
print("\nwhat answered each route - the gateway's reply, which the table does not keep:")
for (asked, served), n in sorted(collections.Counter((a, s) for a, s, _ in seen).items(), key=lambda x: BACKENDS.index(x[0][0])):
    print(f"  {asked:19} {served:26} {n:>3} rows")
print("the rupees for these rows, the gateway's price against the table's:")
for b in BACKENDS.split(","):
    gw, tb = sum(c for a, _, c in seen if a == b) * cb.USD_INR, sum(float(r["cost_inr"]) for r in rows if r["backend"] == b)
    print(f"  {b:19} Rs {gw:6.2f}   Rs {tb:6.2f}")
slm = sorted(int(r["latency_ms"]) for r in rows if r["backend"] == "documind-slm")
print(f"the slowest documind-slm row: {slm[-1] / 1000:.1f} s; the p95 the table prints is row {int(round(0.95 * len(slm)))} of {len(slm)}, "
      f"{slm[int(round(0.95 * len(slm))) - 1] / 1000:.1f} s")'''
    CELLS["compare"] = "python - <<'PY'\n" + COMPARE_PY + "\nPY"
    OUT["compare"] = run(CLIENT + COMPARE_PY, LANE)
    CO = OUT["compare"]
    SUM = {m.group(1): m.groups()[1:] for m in re.finditer(r"^(documind-[a-z]+)\s+(\d+)\s+([\d.]+)\s+([\d.]+)\s+(\d+)\s+([\d.]+)$", CO, re.M)}
    assert list(SUM) == ["documind-general", "documind-slm", "documind-inference"], CO
    assert SUM["documind-general"][:3] == ("20", "1.000", "1.000") and SUM["documind-slm"][:3] == ("20", "0.850", "1.000"), SUM
    assert SUM["documind-inference"][:3] == ("20", "0.850", "1.000"), SUM
    assert "  documind-general    gemini-3.6-flash            20 rows" in CO and "  documind-slm        ollama_chat/documind-slm    20 rows" in CO, CO
    assert "  documind-inference  ollama_chat/documind-slm    20 rows" in CO, CO
    RS = {m.group(1): (float(m.group(2)), float(m.group(3))) for m in re.finditer(r"^  (documind-[a-z]+)\s+Rs\s+([\d.]+)\s+Rs\s+([\d.]+)$", CO, re.M)}
    assert abs(RS["documind-general"][0] - RS["documind-general"][1]) < 0.02 and abs(RS["documind-slm"][0] - RS["documind-slm"][1]) < 0.02, RS
    assert RS["documind-inference"][0] > 5 * RS["documind-inference"][1], RS          # the gateway charged the SLM's rate; the table, Gemini's
    m = re.search(r"the slowest documind-slm row: ([\d.]+) s; the p95 the table prints is row 19 of 20, ([\d.]+) s", CO)
    assert m and float(m.group(1)) > 50 and float(m.group(2)) < 5, CO
    COLD_ROW, P95_ROW = m.group(1), m.group(2)
    assert SUM["documind-slm"][3] == str(int(float(P95_ROW) * 1000)), (SUM, P95_ROW)
    RATE_1K = {k: float(v[4]) for k, v in SUM.items()}

    # ---- step 5: make off (its recipes' own lines)
    CELLS["off"] = 'make off PROJECT="$PROJECT"'
    ECHOES = [re.search(r'@echo "([^"]+)"', recipe(t)).group(1) for t in ("slm-off", "gateway-off", "gke-down")]
    assert ECHOES == ["documind-slm scaled to zero", "documind-gateway scaled to zero",
                      "vLLM workload removed; the cluster and any Standard lab node remain (gke.tf) - make down removes them"], ECHOES
    FLOORS = {"documind-slm": "0", "documind-vllm": "absent", "documind-gateway": "0", "documind-ui": "0"}
    assert "for s in documind-slm documind-vllm documind-gateway documind-ui; do" in OFF and "|| echo absent);" in OFF
    OUT["off"] = ("...\n" + ECHOES[0] + "\n...\n" + ECHOES[1] + "\n...\n" + ECHOES[2] + "\n"
                  + "".join(f"{s}: min-instances {f}\n" for s, f in FLOORS.items()))

    # ---- step 6: zero GPU instances, read from Cloud Monitoring after the idle window
    ZERO_PY = r'''import json, os, subprocess, time, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone
P = os.environ["PROJECT"]
tok = subprocess.run(["gcloud", "auth", "print-access-token"], capture_output=True, text=True, check=True).stdout.strip()
now = datetime.fromtimestamp(time.time(), timezone.utc).replace(second=0, microsecond=0)
iso = lambda t: t.strftime("%Y-%m-%dT%H:%M:%SZ")
q = urllib.parse.urlencode({"filter": 'metric.type="run.googleapis.com/container/instance_count" AND resource.type="cloud_run_revision"',
                            "interval.startTime": iso(now - timedelta(minutes=45)), "interval.endTime": iso(now),
                            "aggregation.alignmentPeriod": "60s", "aggregation.perSeriesAligner": "ALIGN_MAX",
                            "aggregation.crossSeriesReducer": "REDUCE_SUM", "aggregation.groupByFields": "resource.label.service_name"})
req = urllib.request.Request(f"https://monitoring.googleapis.com/v3/projects/{P}/timeSeries?{q}", headers={"Authorization": f"Bearer {tok}"})
last = {}
for s in json.load(urllib.request.urlopen(req, timeout=60)).get("timeSeries", []):
    up = [p["interval"]["endTime"] for p in s.get("points", []) if int(p["value"].get("int64Value", 0)) > 0]
    last[s["resource"]["labels"]["service_name"]] = max(up) if up else None
GPU = ("documind-slm", "documind-vllm")
print(f"instance_count per service, {iso(now - timedelta(minutes=45))[11:16]} to {iso(now)[11:16]} UTC, one point a minute (Cloud Monitoring):")
for name in GPU + ("documind-gateway", "documind-ui"):
    t = last.get(name)
    what = f"last instance at {t[11:16]} UTC" if t else "no instance in the window"
    print(f"  {name:17} " + (f"{what:28}  a GPU service" if name in GPU else what))
fresh = iso(now - timedelta(minutes=3))           # a sample shows up to 120 s after it is taken
still = [n for n in GPU if last.get(n) and last[n] >= fresh]
print("GPU services with an instance in the last 3 minutes: " + (", ".join(still) if still else "none - zero GPU instances"))'''
    CELLS["zero"] = "python - <<'PY'\n" + ZERO_PY + "\nPY"
    OUT["zero"] = run(CLIENT + ZERO_PY, {**LANE, "LANE184_EPOCH": str((lane184.T0 + timedelta(minutes=25)).timestamp())})
    ZO = OUT["zero"]
    assert ZO.startswith("instance_count per service, 09:40 to 10:25 UTC, one point a minute (Cloud Monitoring):\n"), ZO
    assert "  documind-slm      last instance at 10:13 UTC    a GPU service" in ZO and "  documind-vllm     no instance in the window     a GPU service" in ZO, ZO
    assert "  documind-gateway  last instance at 10:09 UTC\n" in ZO and ZO.rstrip().endswith("GPU services with an instance in the last 3 minutes: none - zero GPU instances"), ZO
finally:
    for proc in servers:
        proc.terminate()
        proc.wait(timeout=30)
shutil.rmtree(T, ignore_errors=True)

# ------------------------------------------------------------------ the panel: the table's rate against the GPU's hour
RATE, GEM_IN, GEM_OUT, HOUR, INR, TAIL = 20.5e-6, 1.5e-6, 7.5e-6, 0.0001867 * 3600 + 8 * 0.000018 * 3600 + 32 * 0.000002 * 3600, 85, 10 / 60
assert abs(HOUR - 1.42092) < 1e-9 and PRICES["documind-slm"][0] * 1e-6 == RATE and PRICES["documind-general"] == (GEM_IN * 1e6, GEM_OUT * 1e6)


def bill(qpd: int, tin: int, tout: int, window: int, days: int) -> list:
    """Per 1k questions, in rupees: the table's small-model rate, the GPU's hour spread over the questions, and Gemini."""
    qs = qpd * days
    hours = min(24, window + TAIL) * days                  # the instance lives through the traffic, and idles once a day after it
    return [(tin + tout) * RATE * INR * 1000, hours * HOUR * INR / qs * 1000, (tin * GEM_IN + tout * GEM_OUT) * INR * 1000,
            (tin + tout) * qs, hours]


QPD, TIN, TOUT, WIN, DAYS = [100, 1000, 10000, 50000], [500, 1000, 2000], [60, 200], [10, 24], [22, 30]
CASES = [[q, i, o, w, d, bill(q, i, o, w, d)] for q in QPD for i in TIN for o in TOUT for w in WIN for d in DAYS]
assert any(c[5][1] > c[5][0] for c in CASES) and any(c[5][1] < c[5][0] for c in CASES)      # the rate errs both ways
UI_JS = r"""var root = document.getElementById('rb'); if (!root) return;
  var RATE = __RATE__, GEM_IN = __GIN__, GEM_OUT = __GOUT__, HOUR = __HOUR__, INR = 85, TAIL = __TAIL__;
  function bill(qpd, tin, tout, win, days){ var qs = qpd * days, hours = Math.min(24, win + TAIL) * days;
    return [(tin + tout) * RATE * INR * 1000, hours * HOUR * INR / qs * 1000, (tin * GEM_IN + tout * GEM_OUT) * INR * 1000, (tin + tout) * qs, hours]; }
  window.__rb = {bill: bill};
  var $ = function(id){ return document.getElementById(id); };
  function line(out, cls, text){ var d = document.createElement('div'); if (cls) { d.className = cls; } d.textContent = text; out.appendChild(d); }
  function rs(x){ return 'Rs ' + (x < 100 ? x.toFixed(2) : Math.round(x).toLocaleString('en-IN')); }
  function show(){ var q = Number($('rb-q').value), tin = Number($('rb-in').value), tout = Number($('rb-out').value), win = Number($('rb-win').value), days = Number($('rb-days').value);
    var r = bill(q, tin, tout, win, days), a = $('rb-table'), b = $('rb-bill'), g = $('rb-gem'); a.textContent = ''; b.textContent = ''; g.textContent = '';
    line(a, '', (tin + tout).toLocaleString('en-IN') + ' tokens a question, at the script\'s 20.50 USD a million, in and out.');
    line(a, 'pass', rs(r[0]) + ' per 1,000 questions.');
    var mt = r[3] / 1e6;
    line(a, '', 'The kit derived that rate from Rs 86,904 a month over about 50 million tokens; this pattern is ' + (mt < 100 ? mt.toFixed(1) : Math.round(mt).toLocaleString('en-IN')) + ' million a month.');
    line(b, '', 'One L4 instance lives ' + (win === 24 ? 'all day' : win + ' hours a day, plus up to 10 idle minutes') + ', on ' + days + ' days: ' + Math.round(r[4]) + ' hours at $' + HOUR.toFixed(4) + '.');
    line(b, 'pass', rs(r[1]) + ' per 1,000 questions.');
    var ratio = r[1] / r[0];
    line(b, ratio > 1 ? 'stop' : '', ratio > 1 ? 'The table understates the bill ' + ratio.toFixed(1) + ' times: the idle GPU is paid for, and no row counts it.' : 'The table overstates the bill ' + (1 / ratio).toFixed(1) + ' times: more tokens go through each GPU hour than the rate assumed.');
    line(g, '', 'The same tokens at documind-general\'s 1.50 in and 7.50 out.');
    line(g, 'pass', rs(r[2]) + ' per 1,000 questions.');
    line(g, '', r[2] < r[1] ? 'Cheaper than the small model\'s real bill by ' + (r[1] / r[2]).toFixed(1) + ' times.' : 'Dearer than the small model\'s real bill: at this volume the GPU pays for itself.'); }
  ['rb-q', 'rb-in', 'rb-out', 'rb-win', 'rb-days'].forEach(function(id){ $(id).addEventListener('change', show); });
  show();"""
UI_JS = (UI_JS.replace("__RATE__", repr(RATE)).replace("__GIN__", repr(GEM_IN)).replace("__GOUT__", repr(GEM_OUT)).replace("__HOUR__", repr(HOUR))
         .replace("__TAIL__", repr(TAIL)))
squeeze = lambda code: "\n".join(line.strip() for line in code.splitlines() if line.strip())  # noqa: E731
JS = "<script>\n(function(){\n'use strict';\n" + squeeze(UI_JS).replace("</", "<\\/") + "\n})();\n</script>\n"
assert "<div" not in JS
PORT_JS = UI_JS.split("var $ = function(id)")[0].replace("var root = document.getElementById('rb'); if (!root) return;", "")
NODE = ("var window = {}, document = {};\n(new Function('window', 'document', " + json.dumps(PORT_JS) + "))(window, document);\n"
        "var C = " + json.dumps([c[:5] for c in CASES]) + ";\n"
        "process.stdout.write(JSON.stringify(C.map(function(c){ return window.__rb.bill(c[0], c[1], c[2], c[3], c[4]); })));\n")
node = subprocess.run(["node", "-"], input=NODE, capture_output=True, text=True, encoding="utf-8")
assert node.returncode == 0, node.stderr[-800:]
for case, got in zip(CASES, json.loads(node.stdout)):
    assert all(abs(x - y) <= 1e-9 * max(1, abs(y)) for x, y in zip(got, case[5])), (case, got)
N_CHECKED = len(CASES)


def bash_window(label: str, code: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>bash &mdash; ' + label + '</span><button class="cp" type="button">copy</button></div>'
            '<pre tabindex="0">' + html.escape(code, quote=False) + "</pre></div>\n")


def out_window(label: str, text: str) -> str:
    return ('<div class="cw"><div class="ch-bar"><span>expected ' + label + '</span><span class="ro">read only</span></div>'
            '<pre tabindex="0">' + html.escape(text.rstrip("\n"), quote=False) + "</pre></div>\n")


CELL_LABELS = {
    "selftest": "run in the operator shell, in the kit (the script's own check of its maths; no network)",
    "read": "run in the operator shell, in the kit (reads the script, the tools module and config.yaml; no network)",
    "compare": "run in the operator shell, in the kit (20 questions to the API, then to three routes; the GPU wakes; about five minutes)",
    "off": "run in the operator shell, in the kit, when the comparison is done",
    "zero": "run in the operator shell, at least 10 minutes after make off (reads Cloud Monitoring; changes nothing)",
}
OUT_LABELS = {
    "selftest": "(the kit's own selftest)",
    "read": "(this cell, run on the kit's own files)",
    "compare": "(the kit's own compare_backends.py, against a stand-in API, gateway and small model: your numbers, times and rupees are your lane's)",
    "off": "(the kit's own lines; the gcloud, kubectl and make lines between them are left out, vllm-off's error among them: no documind-vllm service, and make ignores it)",
    "zero": "(this cell, against a stand-in Cloud Monitoring: your times are your lane's)",
}
WIN = {f"CELL_{k.upper()}": bash_window(CELL_LABELS[k], v) for k, v in CELLS.items()}
WIN.update({f"OUT_{k.upper()}": out_window(OUT_LABELS[k], v) for k, v in OUT.items()})
opts = lambda pairs, sel: "".join(f'<option value="{html.escape(str(v))}"{" selected" if v == sel else ""}>{html.escape(t)}</option>' for v, t in pairs)  # noqa: E731
STATS = {"N_CHECKED": str(N_CHECKED), "COLD_ROW": COLD_ROW, "P95_ROW": P95_ROW, "HOUR_INR": f"{HOUR * INR:.2f}",
         "RATE_GEN": f"{RATE_1K['documind-general']:.2f}", "RATE_SLM": f"{RATE_1K['documind-slm']:.2f}", "RATE_INF": f"{RATE_1K['documind-inference']:.2f}",
         "GW_INF": f"{RS['documind-inference'][0]:.2f}", "TB_INF": f"{RS['documind-inference'][1]:.2f}",
         "Q_OPTIONS": opts([(q, f"{q:,} a day") for q in QPD], 1000),
         "IN_OPTIONS": opts([(i, f"{i:,} in") for i in TIN], 1000),
         "OUT_OPTIONS": opts([(o, f"{o} out") for o in TOUT], 60),
         "WIN_OPTIONS": opts([(10, "10 hours a day"), (24, "round the clock")], 10),
         "DAYS_OPTIONS": opts([(22, "22 (working days)"), (30, "30 (every day)")], 22)}

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
print(f"kit: compare_backends.py --selftest, live(), summarise() and print_summary() against the stand-in | the vLLM route answered by "
      f"the small model, priced at Gemini's rates | zero GPU instances read from a stand-in Monitoring | panel checked on {N_CHECKED} cases")
