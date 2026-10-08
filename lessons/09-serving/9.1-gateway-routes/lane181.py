"""The stand-in lane for lesson 9.1's build. Under it the kit's own code runs unchanged: smoke/smoke_gateway.py (make
smoke-gateway), the gateway's guardrail (services/litellm/documind_router.py and documind_classifier.py, with the real
Presidio at the gateway image's pins and the image's spaCy model), gcp_id_token.py, and the page's cells.

What is stood in, and how:
  The gateway    documind-gateway on Cloud Run, as a local HTTP server: IAM at the door (no token, or a token for another
                 audience: 403), LiteLLM's model groups and fallbacks read from the kit's own config.yaml, the kit's own
                 pre-call hook deciding each request's route, Gemini answering the managed routes, and the self-hosted
                 backend absent (lesson 9.2 deploys it): a route to it falls back where config.yaml says, and the
                 sensitive route, which has no fallback, fails. The cost header is the answer's tokens at config.yaml's
                 per-token rates for the route that answered.
  gcloud         auth print-identity-token: a token for the audience asked; urllib's calls to the gateway's URL reach
                 the local server.

    python lane181.py serve PORT GATEWAY_URL KIT_LITELLM_DIR     # the gateway, under a Python with the image's Presidio
"""
import json
import os
import subprocess
import sys
import threading
import types
import urllib.request

PUBLIC_ENV = "LANE181_GATEWAY"          # the gateway's public URL, as the page names it
LOCAL_ENV = "LANE181_LOCAL"             # where the stand-in listens


# ---- the client side: the cells and make smoke-gateway
def install_client() -> None:
    public, local = os.environ[PUBLIC_ENV].rstrip("/"), os.environ[LOCAL_ENV].rstrip("/")
    real_open, real_run = urllib.request.urlopen, subprocess.run

    def urlopen(req, *a, **kw):
        url = req.full_url if isinstance(req, urllib.request.Request) else req
        if url.startswith(public):
            if isinstance(req, urllib.request.Request):
                req.full_url = local + url[len(public):]
            else:
                req = local + url[len(public):]
        return real_open(req, *a, **kw)

    def run(cmd, *a, **kw):
        if isinstance(cmd, (list, tuple)) and list(cmd[:3]) == ["gcloud", "auth", "print-identity-token"]:
            aud = next(c.split("=", 1)[1] for c in cmd if c.startswith("--audiences="))
            return subprocess.CompletedProcess(list(cmd), 0, f"tok:{aud}\n", "")
        return real_run(cmd, *a, **kw)
    urllib.request.urlopen, subprocess.run = urlopen, run


# ---- the gateway
def _guardrail(kit_dir: str):
    """The kit's own pre-call hook, imported as the image imports it; litellm's base class stood in."""
    sys.path.insert(0, kit_dir)
    for name in ("litellm", "litellm.integrations", "litellm.integrations.custom_guardrail"):
        sys.modules[name] = types.ModuleType(name)
    sys.modules["litellm.integrations.custom_guardrail"].CustomGuardrail = type("CustomGuardrail", (), {"__init__": lambda self, **kw: None})
    from documind_router import DocuMindRouter
    return DocuMindRouter()


def serve(port: int, public: str, kit_dir: str) -> None:
    import asyncio
    import yaml
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    cfg = yaml.safe_load(open(os.path.join(kit_dir, "config.yaml"), encoding="utf-8"))
    groups = {m["model_name"]: m["litellm_params"] for m in cfg["model_list"]}
    fallbacks = {k: v for d in cfg["router_settings"]["fallbacks"] for k, v in d.items()}
    router = _guardrail(kit_dir)
    token = f"tok:{public.rstrip('/')}"

    def managed(group: str) -> bool:
        return groups[group]["model"].startswith("vertex_ai/")

    def chain(group: str) -> list:
        return [group] + fallbacks.get(group, [])

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *a):
            pass

        def _send(self, status, body, headers=None):
            raw = (json.dumps(body) if not isinstance(body, str) else body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json" if not isinstance(body, str) else "text/plain")
            for k, v in (headers or {}).items():
                self.send_header(k, v)
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        def _door(self) -> bool:
            if self.headers.get("Authorization") != f"Bearer {token}":
                self._send(403, "<html><body>Error: Forbidden. Your client does not have permission to get URL.</body></html>")
                return False
            return True

        def do_GET(self):
            if self._door():
                self._send(200, "\"I'm alive!\"")

        def do_POST(self):
            if not self._door():
                return
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length") or 0)))
            data = asyncio.run(router.async_pre_call_hook(None, None, body, "completion"))
            for group in chain(data["model"]):
                if not managed(group):
                    continue                                     # the self-hosted backend is not deployed (lesson 9.2)
                text = " ".join(m.get("content", "") for m in data["messages"] if isinstance(m.get("content"), str))
                if (data.get("response_format") or {}).get("type") == "json_object":
                    answer = '{"ok": true}'
                elif "single word OK" in text:
                    answer = "OK"
                else:
                    answer = "It depends on the grade: ask DocuMind, which answers from your tenant's documents."
                usage = {"prompt_tokens": max(1, len(text) // 4), "completion_tokens": max(1, len(answer) // 4)}
                usage["total_tokens"] = usage["prompt_tokens"] + usage["completion_tokens"]
                p = groups[group]
                cost = usage["prompt_tokens"] * float(p["input_cost_per_token"]) + usage["completion_tokens"] * float(p["output_cost_per_token"])
                reply = {"id": "chatcmpl-lesson181", "object": "chat.completion", "model": p["model"].split("/", 1)[1],
                         "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": answer}}],
                         "usage": usage}
                self._send(200, reply, {"x-litellm-response-cost": str(cost)})
                return
            self._send(500, {"error": {"message": f"no deployment of {data['model']} answered, and it has no fallback that did",
                                       "type": None, "param": None, "code": "500"}})

    ThreadingHTTPServer(("127.0.0.1", port), Handler).serve_forever()


if __name__ == "__main__" and len(sys.argv) > 1 and sys.argv[1] == "serve":
    serve(int(sys.argv[2]), sys.argv[3], sys.argv[4])
