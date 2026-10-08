"""The stand-in lane for lesson 9.2's build. Under it the kit's own code runs unchanged: smoke/smoke_slm.py (make
smoke-slm), evals/run_eval.py for the scoped gate on the candidate, the gateway's hook (under the real Presidio at the
image's pins, as lesson 9.1's build runs it), and the page's cells.

What is stood in, and how:
  documind-slm   Ollama on a Cloud Run L4, as a local HTTP server: /api/tags, /api/generate and the OpenAI-compatible
                 /v1/chat/completions, behind IAM (a token for its URL, from an invoker). It starts cold: the first request
                 waits for an instance (LANE182_START seconds) and the first generation for the model to load into the
                 GPU (LANE182_LOAD seconds); after that it is warm until /_standin/idle makes it cold again.
  the gateway    lesson 9.1's stand-in, now with the self-hosted backend deployed: config.yaml's routes behind the kit's
                 own hook, the self-hosted routes forwarded to the SLM stand-in, the cost header at config.yaml's rates.
  the candidate  the API revision tagged candidate, with MODEL_BACKEND=gateway and GENERATOR_MODEL=documind-slm: each
                 golden question answered the way the scenario below says, by the small model through the gateway.
  the clock      each stand-in says how long its answer took (X-Stand-In-Seconds); the client's time.time stands still
                 except by that much, so the kit's own timers print the waits, exactly, without the build waiting for them.
  gcloud         auth print-identity-token, and run services describe for the SLM's label and image.

    python lane182.py slm PORT URL                          # the SLM
    python lane182.py gateway PORT URL KIT_LITELLM_DIR SLM   # the gateway, under a Python with the image's Presidio
    python lane182.py candidate PORT URL KIT_EVALS_DIR       # the candidate
"""
import json
import os
import subprocess
import sys
import threading
import time
import types
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOSTS = ("LANE182_SLM", "LANE182_GATEWAY", "LANE182_CAND")      # public URL=local URL, one variable each


# ---- the client side: the cells, make smoke-slm, the gate
def install_client() -> None:
    routes = [tuple(os.environ[k].split("=", 1)) for k in HOSTS if os.environ.get(k)]
    real_open, real_run, real_time = urllib.request.urlopen, subprocess.run, time.time
    skew = [0.0]

    def urlopen(req, *a, **kw):
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        for public, local in routes:
            if url.startswith(public):
                if isinstance(req, urllib.request.Request):
                    req.full_url = local + url[len(public):]
                else:
                    req = local + url[len(public):]
        try:
            r = real_open(req, *a, **kw)
        except urllib.error.HTTPError as e:
            skew[0] += float(e.headers.get("X-Stand-In-Seconds") or 0)
            raise
        skew[0] += float(r.headers.get("X-Stand-In-Seconds") or 0)
        return r

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and list(cmd[:3]) == ["gcloud", "auth", "print-identity-token"]:
            aud = next(c.split("=", 1)[1] for c in cmd if c.startswith("--audiences="))
            return subprocess.CompletedProcess(list(cmd), 0, f"tok:{aud}\n", "")
        if isinstance(cmd, (list, tuple)) and list(cmd[:4]) == ["gcloud", "run", "services", "describe"] and cmd[4] == "documind-slm":
            project = cmd[cmd.index("--project") + 1]
            return subprocess.CompletedProcess(list(cmd), 0, f"stock\tus-central1-docker.pkg.dev/{project}/cloud-run-source-deploy/documind-slm@sha256:DIGEST\n", "")
        return real_run(cmd, *a, **kw)
    t0 = real_time()
    urllib.request.urlopen, subprocess.run, time.time = urlopen, run, lambda: t0 + skew[0]


class _Handler(BaseHTTPRequestHandler):
    public = ""
    invokers = ()

    def log_message(self, *a):
        pass

    def send(self, status, body, seconds=0.0, headers=None):
        raw = (json.dumps(body) if not isinstance(body, str) else body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json" if not isinstance(body, str) else "text/html")
        self.send_header("X-Stand-In-Seconds", f"{seconds:.1f}")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def door(self) -> bool:
        if self.headers.get("Authorization") != f"Bearer tok:{self.public}":
            self.send(403, "<html><body>Error: Forbidden. Your client does not have permission to get URL.</body></html>")
            return False
        return True

    def body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n)) if n else {}


# ---- documind-slm
def serve_slm(port: int, public: str) -> None:
    start, load = float(os.environ.get("LANE182_START", "41.3")), float(os.environ.get("LANE182_LOAD", "11.4"))
    state = {"up": os.environ.get("LANE182_WARM") == "1", "loaded": False}   # after a deploy: the probe started an instance
    lock = threading.Lock()

    def wait(generates: bool) -> float:
        with lock:
            s = 0.0 if state["up"] else start
            state["up"] = True
            if generates:
                s += (0.0 if state["loaded"] else load) + 0.6
                state["loaded"] = True
            else:
                s += 0.1
            return s

    class H(_Handler):
        pass
    H.public = public

    def do_GET(self):
        if self.path == "/_standin/idle":
            state.update(up=False, loaded=False)
            return self.send(200, {"idle": True})
        if not self.door():
            return
        s = wait(False)
        self.send(200, {"models": [{"name": "documind-slm:latest", "model": "documind-slm:latest", "size": 3338801315,
                                    "details": {"family": "gemma3", "parameter_size": "4.3B", "quantization_level": "Q4_K_M"}}]}, s)

    def do_POST(self):
        if not self.door():
            return
        b, s = self.body(), wait(True)
        if self.path == "/api/generate":
            return self.send(200, {"model": b.get("model"), "response": "OK", "done": True}, s)
        if self.path in ("/v1/chat/completions", "/api/chat"):
            text = " ".join(m.get("content", "") for m in b.get("messages", []))
            asked = [m.get("content", "") for m in b.get("messages", []) if m.get("role") == "user"][-1:]
            answer = ANSWERS.get(asked[0].strip() if asked else "", "OK")
            usage = {"prompt_tokens": max(1, len(text) // 4), "completion_tokens": max(1, len(answer) // 4)}
            return self.send(200, {"model": "documind-slm", "choices": [{"index": 0, "finish_reason": "stop",
                                   "message": {"role": "assistant", "content": answer}}], "usage": usage}, s)
        self.send(404, {"error": "not found"})
    H.do_GET, H.do_POST = do_GET, do_POST
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


# What the small model says to the questions the page asks it directly (through the gateway)
ANSWERS = {"My PAN is ABCDE1234F and I joined on 5 March 2026. What is my notice period?": "Your notice period depends on your grade and confirmation status; the documents you "
                                        "shared do not say which applies to you."}


# ---- the gateway (lesson 9.1's stand-in, the self-hosted backend deployed)
def serve_gateway(port: int, public: str, kit_dir: str, slm_local: str) -> None:
    import asyncio
    import yaml
    sys.path.insert(0, kit_dir)
    for name in ("litellm", "litellm.integrations", "litellm.integrations.custom_guardrail"):
        sys.modules[name] = types.ModuleType(name)
    sys.modules["litellm.integrations.custom_guardrail"].CustomGuardrail = type("CustomGuardrail", (), {"__init__": lambda self, **kw: None})
    from documind_router import DocuMindRouter
    from documind_classifier import classify_tier
    router = DocuMindRouter()
    classify_tier("PAN ABCDE1234F")                          # loads Presidio now, not inside the first timed request
    cfg = yaml.safe_load(open(os.path.join(kit_dir, "config.yaml"), encoding="utf-8"))
    groups = {m["model_name"]: m["litellm_params"] for m in cfg["model_list"]}
    fallbacks = {k: v for d in cfg["router_settings"]["fallbacks"] for k, v in d.items()}
    slm_public = os.environ["LANE182_SLM"].split("=", 1)[0]

    class H(_Handler):
        pass
    H.public = public

    def do_POST(self):
        if not self.door():
            return
        data = asyncio.run(router.async_pre_call_hook(None, None, self.body(), "completion"))
        for group in [data["model"]] + fallbacks.get(data["model"], []):
            p = groups[group]
            if p["model"].startswith("vertex_ai/"):
                answer, served, s = '{"ok": true}' if (data.get("response_format") or {}).get("type") == "json_object" else "OK", p["model"].split("/", 1)[1], 1.2
                text = " ".join(m.get("content", "") for m in data["messages"] if isinstance(m.get("content"), str))
                usage = {"prompt_tokens": max(1, len(text) // 4), "completion_tokens": max(1, len(answer) // 4)}
            elif str(p.get("api_base", "")).endswith("/slm"):
                req = urllib.request.Request(f"{slm_local}/v1/chat/completions", data=json.dumps({"model": "documind-slm", "messages": data["messages"]}).encode(),
                                             method="POST", headers={"Content-Type": "application/json", "Authorization": f"Bearer tok:{slm_public}"})
                with urllib.request.urlopen(req, timeout=300) as r:                   # the token proxy, with the gateway's own token
                    j, s = json.loads(r.read()), float(r.headers.get("X-Stand-In-Seconds") or 0)
                answer, served, usage = j["choices"][0]["message"]["content"], "ollama_chat/documind-slm", j["usage"]
            else:
                continue
            cost = usage["prompt_tokens"] * float(p["input_cost_per_token"]) + usage["completion_tokens"] * float(p["output_cost_per_token"])
            return self.send(200, {"model": served, "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": answer}}],
                                   "usage": {**usage, "total_tokens": usage["prompt_tokens"] + usage["completion_tokens"]}}, s,
                             {"x-litellm-response-cost": str(cost)})
        self.send(500, {"error": {"message": f"no deployment of {data['model']} answered", "code": "500"}})
    H.do_POST = do_POST
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


# ---- the candidate: the small model's answers to the golden rows, through the gateway and the API's grammar
MISS = {"lk-02": "partial", "lk-08": "refused"}
PARTIAL = {"lk-02": "Form 16 is issued every June [1]."}
TEXT = {"lk-06": "A confirmed E3 serves a notice period of 60 days [1]."}


def reply(row: dict) -> dict:
    mc, t = row.get("must_contain", []), row["tenant"]
    outcome = MISS.get(row["id"], "ok")
    cite = {"chunk_id": f"{t}:{row['id']}#0", "source_uri": f"gs://lesson/{t}/doc.md", "quote": mc[0] if mc else "lesson",
            "kind": row.get("must_cite_kind") or "text"}
    if not row["answerable"] or outcome == "refused":
        answer, cites, ok = "The documents do not say.", [], False
    elif outcome == "partial":
        answer, cites, ok = PARTIAL[row["id"]], [cite], True
    else:
        answer, cites, ok = TEXT.get(row["id"]) or " and ".join(mc) + " [1].", [cite], True
    return {"answer": answer, "citations": cites, "answerable": ok, "confidence": "high" if ok else "low",
            "model": "documind-slm", "backend": "gateway", "cache_hit": "none",           # the route it asked for (generate())
            "cost_usd": round(1900 * 0.0000205 + 40 * 0.0000205, 6), "tokens_in": 1900, "tokens_out": 40, "latency_ms": 2400,
            "stages": {"retrieve_ms": 400, "rerank_ms": 200, "generate_ms": 1700, "pool": 12}}


def serve_candidate(port: int, public: str, evals_dir: str) -> None:
    sys.path.insert(0, evals_dir)
    import run_eval
    golden = run_eval.load_golden()

    class H(_Handler):
        pass
    H.public = os.environ["LANE182_AUD"]                      # the API checks every token against its canonical URL

    def do_GET(self):
        if not self.door():
            return
        self.send(200, {"sources": []})                        # GET /v1/sources: the ledger's current versions

    def do_POST(self):
        b = self.body()
        if self.headers.get("x-user-email", "").startswith("outsider@"):
            return self.send(403, {"detail": "not a member of this tenant"})
        if not self.door():
            return
        row = next(r for r in golden if r["question"] == b["query"] and r["tenant"] == b["tenant_id"])
        self.send(200, reply(row), 2.4)
    H.do_GET, H.do_POST = do_GET, do_POST
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


if __name__ == "__main__" and len(sys.argv) > 1:
    kind, port, url = sys.argv[1], int(sys.argv[2]), sys.argv[3]
    {"slm": lambda: serve_slm(port, url), "gateway": lambda: serve_gateway(port, url, sys.argv[4], sys.argv[5]),
     "candidate": lambda: serve_candidate(port, url, sys.argv[4])}[kind]()
