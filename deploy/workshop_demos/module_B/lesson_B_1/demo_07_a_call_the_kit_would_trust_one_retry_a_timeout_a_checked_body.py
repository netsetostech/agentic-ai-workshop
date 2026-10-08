"""Lesson B.1: A call the kit would trust: one retry, a timeout, a checked body

Three ways a real service lets a caller down, and the kit's rule for each, run against a server that misbehaves on purpose. The call in step 5 assumed the server answers, answers once and answers well. A real service can be briefly overloaded, can hang, or can answer 200 with an empty body. The kit's eval gate has a rule for each: give every call a timeout; retry a 5xx, a timeout or a transport error once, after a pause, and never a 4xx; and count a 200 as a failed request until its body has the right shape. The last two date from 12 September 2026, the day its docstring says the gate "learned to fail". The cell below gives a stand-in server three routes that misbehave on purpose and calls each one under those rules.

Run order inside this file:
1. A call the kit would trust: one retry, a timeout, a checked body (source window 30)

Prerequisites: demo_06_two_calls_at_once_asyncio_gather_and_asyncio_to_thread.
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


def step_01_a_call_the_kit_would_trust_one_retry_a_tim(session):
    """Run A call the kit would trust: one retry, a timeout, a checked body at this checkpoint.

    Three ways a real service lets a caller down, and the kit's rule for each, run against a server that misbehaves on purpose. The call in step 5 assumed the server answers, answers once and answers well. A real service can be briefly overloaded, can hang, or can answer 200 with an empty body. The kit's eval gate has a rule for each: give every call a timeout; retry a 5xx, a timeout or a transport error once, after a pause, and never a 4xx; and count a 200 as a failed request until its body has the right shape. The last two date from 12 September 2026, the day its docstring says the gate "learned to fail". The cell below gives a stand-in server three routes that misbehave on purpose and calls each one under those rules.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop: a server that misbehaves on purpose.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: /flaky -> 200 {"answer": "", "citations": [], "answerable": false, "confidence": "low"} | asked 2 times | an answer: True
    /hang  -> 0 {"error": "TimeoutError"} | asked 2 times | an answer: False
    /empty -> 200 {} | asked 1 time | an answer: False
    """
    import json, threading, time, urllib.error, urllib.request, warnings
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    warnings.filterwarnings("ignore", category=UserWarning)
    
    hits, release = {}, threading.Event()
    
    class Unreliable(BaseHTTPRequestHandler):                  # three ways a real service lets a caller down
        """A stand-in server that fails the three ways real services do: a 503 blip, a hang and an empty 200.
        
        Example: See the instance constructed in this lesson step and inspect its state in the debugger.
        """
        def send_json(self, status, body):
            """Send this status with a JSON body and its length.
            
            Example: self.send_json(200, {})
            """
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
            hits[self.path] = hits.get(self.path, 0) + 1
            if self.path == "/flaky":                          # a blip: a 503 the first time, an answer the second
                if hits["/flaky"] == 1:
                    return self.send_json(503, {"detail": "overloaded, try again"})
                return self.send_json(200, {"answer": "", "citations": [], "answerable": False, "confidence": "low"})
            if self.path == "/hang":                           # takes the request and never answers
                release.wait(10)
                return
            self.send_json(200, {})                            # /empty: a 200 with nothing in it
    
        def log_message(self, *args):
            """Silence the standard library server's per-request log lines, which would otherwise go to stderr.
            
            Example: self.log_message() in the owning lesson/helper context
            """
            pass
    
    server = ThreadingHTTPServer(("127.0.0.1", 0), Unreliable)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    API = f"http://127.0.0.1:{server.server_address[1]}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    
    def get(path, timeout):
        """Make one GET with a timeout and return (status, body); a timeout or a refused connection gives status 0.
        
        Example: get(path, timeout)
        """
        try:
            with opener.open(API + path, timeout=timeout) as r:
                return r.status, json.loads(r.read())
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read())
        except Exception as e:                                 # a timeout or a refused connection: no status at all
            return 0, {"error": type(e).__name__}
    
    def ask(path, timeout=0.5, retries=1):                     # the kit's rule: retry a 5xx or no answer once, after a pause
        """Send this example request to the selected API and return its response for the following comparison.
        
        Example: ask(path)
        """
        status, body = get(path, timeout)
        for _ in range(retries):
            if status == 200 or 400 <= status < 500:
                break
            time.sleep(0.2)                                    # run_eval.py pauses two seconds; a fifth of a second here
            status, body = get(path, timeout)
        return status, body
    
    def well_formed(body):                                     # the kit's shape check, cut down to its four fields
        """Check that an answer has the four fields of the kit's answer shape, each with the right type.
        
        Example: well_formed(body)
        """
        return (isinstance(body.get("answer"), str) and isinstance(body.get("citations"), list)
                and isinstance(body.get("answerable"), bool) and body.get("confidence") in ("high", "medium", "low"))
    
    for path in ("/flaky", "/hang", "/empty"):
        status, body = ask(path)
        n = hits[path]
        print(f"{path:6} -> {status} {json.dumps(body)} | asked {n} time{'s' if n > 1 else ''} | an answer: {status == 200 and well_formed(body)}")
    release.set()
    server.shutdown()
    server.server_close()

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_30', step_01_a_call_the_kit_would_trust_one_retry_a_tim),
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
