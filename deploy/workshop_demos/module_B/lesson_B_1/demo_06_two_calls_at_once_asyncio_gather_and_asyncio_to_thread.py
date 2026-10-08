"""Lesson B.1: Two calls at once: asyncio.gather and asyncio.to_thread

A call to the API, or to Gemini, is mostly waiting: the request goes out, the other side works, the answer comes back, and your program does nothing in between. Two calls made one after the other wait twice. asyncio lets one program wait on both at once. A function written async def is a coroutine; inside it, await marks each place where it waits; and the event loop that asyncio.run() starts runs another coroutine while one waits. asyncio.gather() runs several and returns their results as a list, in the order you passed them, not the order they finished. There is one catch, and the cell below is built to show it. The loop can switch only at an await, and urllib is synchronous: it never awaits, so while it waits it holds the whole thread, loop and all. asyncio.to_thread() is the way out. It runs an ordinary blocking function in a separate thread and gives the loop something to await, which is what Python's documentation says it is for. The cell's server takes half a second over every answer, a stand-in for a slow model, and notes whether a request arrived while another was still being served.

Run order inside this file:
1. Two calls at once: asyncio.gather and asyncio.to_thread (source window 24)

Prerequisites: demo_05_one_http_call_a_server_on_your_laptop_and_urllib.
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


def step_01_two_calls_at_once_asyncio_gather_and_async(session):
    """Run Two calls at once: asyncio.gather and asyncio.to_thread at this checkpoint.

    A call to the API, or to Gemini, is mostly waiting: the request goes out, the other side works, the answer comes back, and your program does nothing in between. Two calls made one after the other wait twice. asyncio lets one program wait on both at once. A function written async def is a coroutine; inside it, await marks each place where it waits; and the event loop that asyncio.run() starts runs another coroutine while one waits. asyncio.gather() runs several and returns their results as a list, in the order you passed them, not the order they finished. There is one catch, and the cell below is built to show it. The loop can switch only at an await, and urllib is synchronous: it never awaits, so while it waits it holds the whole thread, loop and all. asyncio.to_thread() is the way out. It runs an ordinary blocking function in a separate thread and gives the loop something to await, which is what Python's documentation says it is for. The cell's server takes half a second over every answer, a stand-in for a slow model, and notes whether a request arrived while another was still being served.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run on your laptop: the same kind of server, slowed down on purpose.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: one after the other            ['a', 'b']  about 2 waits, both in flight at once: False
    gather over blocking calls     ['a', 'b']  about 2 waits, both in flight at once: False
    gather over asyncio.to_thread  ['a', 'b']  about 1 wait, both in flight at once: True
    """
    import asyncio, json, threading, time, urllib.request, warnings
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    warnings.filterwarnings("ignore", category=UserWarning)
    
    WAIT = 0.5                                                 # every answer takes half a second: a stand-in for a slow model
    busy, overlap, lock = 0, [], threading.Lock()
    
    class Slow(BaseHTTPRequestHandler):
        """A stand-in server whose every answer takes the same fixed wait, to show calls overlapping or queueing.
        
        Example: See the instance constructed in this lesson step and inspect its state in the debugger.
        """
        def do_GET(self):
            """Answer a GET on this stand-in server the way the lesson's scenario needs: an answer, a delay or a failure.
            
            Example: self.do_GET() in the owning lesson/helper context
            """
            global busy
            with lock:
                busy += 1
                overlap.append(busy > 1)                       # was another request already being served?
            time.sleep(WAIT)
            with lock:
                busy -= 1
            data = json.dumps({"name": self.path.strip("/")}).encode()
            self.send_response(200)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
    
        def log_message(self, *args):
            """Silence the standard library server's per-request log lines, which would otherwise go to stderr.
            
            Example: self.log_message() in the owning lesson/helper context
            """
            pass
    
    server = ThreadingHTTPServer(("127.0.0.1", 0), Slow)       # a thread per request: it can serve two at once
    threading.Thread(target=server.serve_forever, daemon=True).start()
    API = f"http://127.0.0.1:{server.server_address[1]}"
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    
    def fetch(name):                                           # an ordinary call: it blocks until the answer is in
        """Make one blocking HTTP call to the stand-in server and return the name it answers with.
        
        Example: fetch(name)
        """
        with opener.open(f"{API}/{name}", timeout=10) as r:
            return json.loads(r.read())["name"]
    
    async def fetch_in_async_def(name):                        # async def, but the call inside still blocks the loop
        """The blocking call inside async def: it still blocks the event loop, which the timing shows.
        
        Example: fetch_in_async_def('a')
        """
        return fetch(name)
    
    async def gather_blocking():
        """Await two blocking calls with asyncio.gather; they run one after the other, each blocking the loop.
        
        Example: gather_blocking()
        """
        return await asyncio.gather(fetch_in_async_def("a"), fetch_in_async_def("b"))
    
    async def gather_threads():                                # each call in a thread of its own; the loop awaits both
        """Await two calls with asyncio.gather, each in its own thread through asyncio.to_thread, so they overlap.
        
        Example: gather_threads()
        """
        return await asyncio.gather(asyncio.to_thread(fetch, "a"), asyncio.to_thread(fetch, "b"))
    
    def timed(label, run):
        """Run one way of making the two calls and print how many fixed waits it took and whether they overlapped.
        
        Example: timed('one after the other', lambda: [fetch('a'), fetch('b')])
        """
        overlap.clear()
        t0 = time.perf_counter()
        names = run()
        waits = round((time.perf_counter() - t0) / WAIT)       # how many waits it took, rounded: not seconds
        print(f"{label:30} {names}  about {waits} wait{'s' if waits != 1 else ''}, both in flight at once: {any(overlap)}")
    
    timed("one after the other", lambda: [fetch("a"), fetch("b")])
    timed("gather over blocking calls", lambda: asyncio.run(gather_blocking()))
    timed("gather over asyncio.to_thread", lambda: asyncio.run(gather_threads()))
    server.shutdown()
    server.server_close()

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_24', step_01_two_calls_at_once_asyncio_gather_and_async),
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
