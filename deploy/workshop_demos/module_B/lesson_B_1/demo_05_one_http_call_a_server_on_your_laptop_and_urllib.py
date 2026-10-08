"""Lesson B.1: One HTTP call: a server on your laptop, and urllib

An HTTP request is a method (GET to read, POST to send something), a URL, a set of headers and, for a POST, a body. The response is a status code, its own headers and a body. Everything else is one of those: the ID token is a header, the question is the body. 127.0.0.1 is the loopback address, your own machine, and a server bound to it can be called only from that machine, so nothing in this step leaves your laptop. The cell below starts a stand-in API in a background thread, with http.server from the standard library and three routes: GET /health; POST /v1/query, which refuses a request that has no bearer token; and a 404 for anything else. Then it calls the server four times with urllib.request, the way the kit's smoke test calls the real API: health, a question with a token (the eval gate's request body for row lk-01), the same question with no token, and a path that does not exist. The server keeps its own log, so you see each call from both ends.

Run order inside this file:
1. One HTTP call: a server on your laptop, and urllib (source window 18)

Prerequisites: demo_04_files_and_json_pathlib_json_and_a_jsonl_file.
Use the existing rag-shell-venv interpreter; Run or Debug this file.
The functions below contain the lesson examples in source order. Helpers
supply configuration, authentication, state and CLI execution. See README.md
for expected observations, effects and the next file; GUIDE.md retains prose.
Example: open this file at the matching HTML heading, Run once, then inspect
the observations below before continuing to the next numbered section.
A successful process is not proof that a live result matched the sample.

"""
from workshop_helpers.session import DemoSession
from workshop_helpers.steps import manual_checkpoint, run_steps

# REPEAT replays the whole file; use only after reviewing its effects.
REPEAT = False
# A failed function may have partial effects. Inspect its saved attempt first.
RETRY_FAILED_STEP = False


def step_01_one_http_call_a_server_on_your_laptop_and(session):
    """Run One HTTP call: a server on your laptop, and urllib at this checkpoint.

    An HTTP request is a method (GET to read, POST to send something), a URL, a set of headers and, for a POST, a body. The response is a status code, its own headers and a body. Everything else is one of those: the ID token is a header, the question is the body. 127.0.0.1 is the loopback address, your own machine, and a server bound to it can be called only from that machine, so nothing in this step leaves your laptop. The cell below starts a stand-in API in a background thread, with http.server from the standard library and three routes: GET /health; POST /v1/query, which refuses a request that has no bearer token; and a 404 for anything else. Then it calls the server four times with urllib.request, the way the kit's smoke test calls the real API: health, a question with a token (the eval gate's request body for row lk-01), the same question with no token, and a path that does not exist. The server keeps its own log, so you see each call from both ends.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop: a server on 127.0.0.1, stopped at the end; nothing leaves the machine.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: GET  /health           -> 200 {"status": "ok"}
    POST /v1/query   token -> 200 {"received": {"query": "What is the per-trip cap on domestic travel reimbursement?", "tenant_id": "acme", "top_k": 6}, "content_type": "application/json"}
    POST /v1/query         -> 401 {"detail": "no bearer token"}
    GET  /v1/missing       -> 404 {"detail": "no route GET /v1/missing"}
    the server's log: GET /health 200 | POST /v1/query 200 | POST /v1/query 401 | GET /v1/missing 404
    """
    import json, threading, urllib.error, urllib.request, warnings
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    warnings.filterwarnings("ignore", category=UserWarning)
    
    seen = []                                                  # the server's own log: what arrived, and its answer
    
    class Api(BaseHTTPRequestHandler):                         # a stand-in API: three routes, JSON in and out
        """A stand-in API on 127.0.0.1 with JSON routes, so an HTTP call can be made with no account and no network.
        
        Example: See the instance constructed in this lesson step and inspect its state in the debugger.
        """
        def reply(self, status, body):
            """Send this status and JSON body as the response, and note the request in the server's own log.
            
            Example: self.reply(404, {'detail': f'no route GET {self.path}'})
            """
            seen.append(f"{self.command} {self.path} {status}")
            data = json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    
        def do_GET(self):
            """Answer a GET on this stand-in server the way the lesson's scenario needs: an answer, a delay or a failure.
            
            Example: self.do_GET() in the owning lesson/helper context
            """
            if self.path == "/health":
                return self.reply(200, {"status": "ok"})
            self.reply(404, {"detail": f"no route GET {self.path}"})
    
        def do_POST(self):
            """Answer a POST: read the body, refuse a missing bearer token with 401, echo the JSON it received with 200.
            
            Example: self.do_POST() in the owning lesson/helper context
            """
            raw = self.rfile.read(int(self.headers.get("Content-Length", 0)))   # read the body first, always
            if self.path != "/v1/query":
                return self.reply(404, {"detail": f"no route POST {self.path}"})
            if not self.headers.get("Authorization", "").startswith("Bearer "):
                return self.reply(401, {"detail": "no bearer token"})
            self.reply(200, {"received": json.loads(raw), "content_type": self.headers["Content-Type"]})
    
        def log_message(self, *args):                          # quiet: by default every request is logged to stderr
            """Silence the standard library server's per-request log lines, which would otherwise go to stderr.
            
            Example: self.log_message() in the owning lesson/helper context
            """
            pass
    
    server = ThreadingHTTPServer(("127.0.0.1", 0), Api)        # 127.0.0.1: this laptop only; port 0: any free port
    threading.Thread(target=server.serve_forever, daemon=True).start()
    API = f"http://127.0.0.1:{server.server_address[1]}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))   # no proxy, even if your shell names one
    
    def call(method, path, token=None, body=None):             # the shape of the kit's smoke/smoke.py call()
        """Perform the current transport request and expose its actual response for the lesson comparison.
        
        Example: call(method, path, token, body)
        """
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(API + path, data=data, method=method)
        if token:
            req.add_header("Authorization", f"Bearer {token}")
        if body is not None:
            req.add_header("Content-Type", "application/json")
        try:
            with opener.open(req, timeout=10) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:                    # a 4xx or 5xx: an exception that carries the status and the body
            return e.code, json.loads(e.read())
    
    question = {"query": "What is the per-trip cap on domestic travel reimbursement?", "tenant_id": "acme", "top_k": 6}
    for method, path, token, body in (("GET", "/health", None, None),
                                      ("POST", "/v1/query", "stand-in-token", question),
                                      ("POST", "/v1/query", None, question),
                                      ("GET", "/v1/missing", None, None)):
        status, answer = call(method, path, token, body)
        print(f"{method:4} {path:11} {'token' if token else '     '} -> {status} {json.dumps(answer)}")
    server.shutdown()
    server.server_close()
    print("the server's log:", " | ".join(seen))

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_one_http_call_a_server_on_your_laptop_and),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=False, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
