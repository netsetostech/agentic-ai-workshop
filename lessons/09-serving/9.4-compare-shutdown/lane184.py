"""The stand-in lane for lesson 9.4's build. Under it the kit's own code runs unchanged - compare_backends.live(),
summarise() and print_summary() with shared/documind_tools.retrieve() - and so do the page's cells.

What is stood in, and how:
  the API        POST /v1/query: the live revision's answer to a golden question. Its citations are the kit's own chunks
                 (shared/documind_corpus.chunk_document over evals/corpus), each quoting the line that holds one of the
                 row's must_contain phrases - which is what the comparison hands every backend as its context.
  the gateway    POST /v1/chat/completions, behind a token for its URL. documind-general is answered by gemini-3.6-flash;
                 documind-slm by the small model, cold on its first call; documind-inference by config.yaml's first
                 fallback, documind-slm, because no vLLM service is deployed (lesson 9.3). Usage and the cost header are
                 at config.yaml's rates for the route that served. The small model misses three rows the way lesson
                 9.2's stand-in did: a partial answer, a refusal, and half of a join.
  Monitoring     GET /v3/projects/P/timeSeries: instance_count per service, one point a minute, for the zero check.
  the clock      as in lane182: time.time stands still except by each stand-in's X-Stand-In-Seconds, so the latencies
                 the comparison records are the stand-in's, exactly; LANE184_EPOCH sets where it stands.
  gcloud         auth print-identity-token, auth print-access-token, projects describe.

    python lane184.py api PORT KIT_DIR          python lane184.py gateway PORT KIT_DIR          python lane184.py monitoring PORT
"""
import json
import os
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from datetime import datetime, timedelta, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

HOSTS = ("LANE184_API", "LANE184_GATEWAY", "LANE184_MONITORING")      # public URL=local URL, one variable each
MISS = {"lk-02": "partial", "lk-08": "refused", "jn-03": "half"}
T0 = datetime(2026, 9, 24, 10, 0, tzinfo=timezone.utc)                 # the comparison starts; the monitoring series hang off it


# ---- the client side
def install_client() -> None:
    import requests
    routes = [tuple(os.environ[k].split("=", 1)) for k in HOSTS if os.environ.get(k)]
    skew, epoch = [0.0], float(os.environ.get("LANE184_EPOCH", T0.timestamp()))

    def route(url: str) -> str:
        for public, local in routes:
            if url.startswith(public):
                return local + url[len(public):]
        return url

    real_post, real_open, real_run = requests.post, urllib.request.urlopen, subprocess.run

    def post(url, *a, **kw):
        r = real_post(route(url), *a, **kw)
        skew[0] += float(r.headers.get("X-Stand-In-Seconds") or 0)
        return r

    def urlopen(req, *a, **kw):
        if isinstance(req, urllib.request.Request):
            req.full_url = route(req.full_url)
        else:
            req = route(req)
        return real_open(req, *a, **kw)

    def run(cmd, *a, **kw):
        c = list(cmd) if isinstance(cmd, (list, tuple)) else []
        if c[:3] == ["gcloud", "auth", "print-identity-token"]:
            aud = next(x.split("=", 1)[1] for x in c if x.startswith("--audiences="))
            return subprocess.CompletedProcess(c, 0, f"tok:{aud}\n", "")
        if c[:3] == ["gcloud", "auth", "print-access-token"]:
            return subprocess.CompletedProcess(c, 0, "ya29.stand-in\n", "")
        if c[:3] == ["gcloud", "projects", "describe"]:
            return subprocess.CompletedProcess(c, 0, "NUMBER\n", "")
        return real_run(cmd, *a, **kw)
    requests.post, urllib.request.urlopen, subprocess.run = post, urlopen, run
    time.time = lambda: epoch + skew[0]


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def send(self, status: int, body, seconds: float = 0.0, headers: dict | None = None) -> None:
        raw = json.dumps(body).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("X-Stand-In-Seconds", f"{seconds:.3f}")
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.send_header("Content-Length", str(len(raw)))
        self.end_headers()
        self.wfile.write(raw)

    def body(self) -> dict:
        n = int(self.headers.get("Content-Length") or 0)
        return json.loads(self.rfile.read(n)) if n else {}


def _golden(kit: str) -> list:
    return [json.loads(line) for line in open(os.path.join(kit, "evals", "golden.jsonl"), encoding="utf-8") if line.strip()]


# ---- the API: /v1/query, with the kit's own chunks as citations
def quote_around(text: str, phrase: str) -> str:
    """The words a citation would quote for a phrase: from the sentence it sits in, at most 500 characters, verbatim."""
    i = text.lower().index(phrase.lower())
    start = max(0, i - 200)
    cut = max(text.rfind(". ", start, i), text.rfind("\n", start, i))
    start = cut + 1 if cut != -1 else start
    return text[start:start + 500].strip()


def citations_for(row: dict, chunks: list) -> list:
    """A citation for each of the row's phrases, from the chunk the golden set expects when it holds the phrase; a
    phrase already inside an earlier quote adds nothing, as one citation carries one quote."""
    anchors = row.get("must_retrieve", [])
    out = []
    for phrase in row.get("must_contain", []):
        if any(phrase.lower() in o["quote"].lower() for o in out):
            continue
        pool = ([c for c in chunks if any(a in c["chunk_id"] for a in anchors) and phrase.lower() in c["text"].lower()]
                or [c for c in chunks if phrase.lower() in c["text"].lower()])
        if pool:
            c = pool[0]
            out.append({"chunk_id": c["chunk_id"], "source_uri": c["source_uri"], "page": 1, "quote": quote_around(c["text"], phrase),
                        "score": 0.82, "kind": "text"})
    return out


def serve_api(port: int, kit: str) -> None:
    sys.path.insert(0, kit)
    from shared import documind_corpus as dc
    chunks = {t: [c for d in dc.load_documents(t, os.path.join(kit, "evals"), "documind-ai-YOUR-ID") for c in dc.chunk_document(d, t)]
              for t in ("acme", "globex", "zeta")}
    rows = {(r["question"], r["tenant"]): r for r in _golden(kit)}

    class H(_Handler):
        def do_POST(self):
            if not (self.headers.get("Authorization") or "").startswith("Bearer tok:"):
                return self.send(403, {"detail": "no token"})
            b = self.body()
            row = rows.get((b.get("query"), b.get("tenant_id")))
            cites = citations_for(row, chunks[row["tenant"]]) if row and row["answerable"] else []
            self.send(200, {"answer": " and ".join(row["must_contain"]) + " [1]." if cites else "The documents do not say.",
                            "citations": cites, "answerable": bool(cites), "confidence": "high" if cites else "low"}, 2.1)
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


# ---- the gateway: three routes, config.yaml's rates, the vLLM route's fallback
def serve_gateway(port: int, kit: str) -> None:
    rows: dict = {}
    for r in _golden(kit):
        rows.setdefault(r["question"], r)          # the first: the isolation rows ask acme's questions again, as another tenant
    rates, group = {}, None
    for line in open(os.path.join(kit, "services", "litellm", "config.yaml"), encoding="utf-8"):
        m = re.match(r"  - model_name: (\S+)", line)
        group = m.group(1) if m else group
        m = re.match(r"\s+(input|output)_cost_per_token: ([\d.]+)", line)
        if m:
            rates.setdefault(group, {})[m.group(1)] = float(m.group(2))
    state = {"slm_warm": False}

    class H(_Handler):
        def do_POST(self):
            if not (self.headers.get("Authorization") or "").startswith("Bearer tok:"):
                return self.send(403, {"error": "no token"})
            b = self.body()
            system, user = b["messages"][0]["content"], b["messages"][1]["content"]
            row = rows[user.rsplit("\n\nQuestion: ", 1)[1]]
            sources = re.findall(r"^\[Source (\d+)\] (.*)$", user, re.M)
            asked = b["model"]
            served_route = "documind-slm" if asked == "documind-inference" else asked      # no vLLM service: its first fallback
            small = served_route == "documind-slm"
            seed = sum(map(ord, row["id"]))
            seconds = (2.2 + seed % 10 / 10) if small else (1.1 + seed % 5 / 10)
            if small and not state["slm_warm"]:
                seconds += 41.4 + 11.4                                                       # lesson 9.2's cold start
                state["slm_warm"] = True
            if asked == "documind-inference":
                seconds += 0.3                                                               # the dead vLLM route, tried first
            outcome = MISS.get(row["id"], "ok") if small else "ok"
            context = user.split("Context:\n", 1)[1].rsplit("\n\nQuestion: ", 1)[0].lower()
            mc = [m for m in row["must_contain"] if m.lower() in context]            # a model can state only what it was given
            if not sources or not mc or outcome == "refused":
                draft = {"answer": "The context does not say.", "citations": [], "answerable": False}
            else:
                said = {"partial": ["every June"], "half": mc[:1]}.get(outcome, mc)
                draft = {"answer": "; ".join(said) + ".", "citations": [{"source": int(n), "quote": q[:120]} for n, q in sources],
                         "answerable": True}
            content = json.dumps(draft)
            usage = {"prompt_tokens": len(system + user) // 4, "completion_tokens": max(1, len(content) // 4)}
            r = rates[served_route]
            cost = usage["prompt_tokens"] * r["input"] + usage["completion_tokens"] * r["output"]
            self.send(200, {"model": "ollama_chat/documind-slm" if small else "gemini-3.6-flash",
                            "choices": [{"index": 0, "finish_reason": "stop", "message": {"role": "assistant", "content": content}}],
                            "usage": {**usage, "total_tokens": usage["prompt_tokens"] + usage["completion_tokens"]}},
                      seconds, {"x-litellm-response-cost": repr(cost)})
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


# ---- Cloud Monitoring: instance_count per service, one point a minute
SERIES = {"documind-slm": (0, 13), "documind-gateway": (0, 9)}      # minutes after T0 with an instance: the comparison, then idle


def serve_monitoring(port: int) -> None:
    class H(_Handler):
        def do_GET(self):
            if not (self.headers.get("Authorization") or "").startswith("Bearer "):
                return self.send(401, {"error": "no token"})
            q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
            assert 'metric.type="run.googleapis.com/container/instance_count"' in q["filter"][0], q
            assert q["aggregation.groupByFields"] == ["resource.label.service_name"] and q["aggregation.crossSeriesReducer"] == ["REDUCE_SUM"], q
            start = datetime.fromisoformat(q["interval.startTime"][0].replace("Z", "+00:00"))
            end = datetime.fromisoformat(q["interval.endTime"][0].replace("Z", "+00:00"))
            out = []
            for name, (a, b) in SERIES.items():
                pts = [T0 + timedelta(minutes=m) for m in range(a, b + 1)]
                pts = [t for t in pts if start <= t <= end]
                out.append({"metric": {"type": "run.googleapis.com/container/instance_count"},
                            "resource": {"type": "cloud_run_revision", "labels": {"service_name": name}},
                            "points": [{"interval": {"startTime": t.strftime("%Y-%m-%dT%H:%M:%SZ"), "endTime": t.strftime("%Y-%m-%dT%H:%M:%SZ")},
                                        "value": {"int64Value": "1"}} for t in reversed(pts)]})
            self.send(200, {"timeSeries": out, "unit": "1"})
    ThreadingHTTPServer(("127.0.0.1", port), H).serve_forever()


if __name__ == "__main__" and len(sys.argv) > 1:
    kind, port = sys.argv[1], int(sys.argv[2])
    {"api": lambda: serve_api(port, sys.argv[3]), "gateway": lambda: serve_gateway(port, sys.argv[3]),
     "monitoring": lambda: serve_monitoring(port)}[kind]()
