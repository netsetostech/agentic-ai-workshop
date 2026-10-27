#!/usr/bin/env python3
"""The Ralph loop's egress proxy (workshop lesson 10.10, RALPH_EGRESS=proxy): the only way out of the live agent's
container. An allowlisting forward proxy: it opens an HTTPS tunnel (HTTP CONNECT) to a host:port on its allowlist and
refuses every other request, so the agent's container reaches the model endpoint and nothing else.

    python3 -I -B -u commands/ralph/egress.py --allow aiplatform.googleapis.com:443 [--allow HOST:PORT ...]
                                              [--listen 0.0.0.0:3128]

WHERE IT RUNS. commands/ralph.py starts it for each live iteration (Egress, there): in a container of the ralph image
with this file mounted read-only, on docker's default bridge and on the iteration's own internal network (docker
network create --internal: no route out). The agent's container joins the internal network alone, with HTTPS_PROXY
naming this proxy, so a connection that does not come through here goes nowhere. The proxy holds no credential and
mounts nothing else, and it sees host:port, never what goes through a tunnel: that is TLS between the agent and the
endpoint.

THE RULES. One request a connection, its head read within HEAD_LIMIT bytes and HEAD_TIMEOUT_S seconds:
    CONNECT to a host:port on the allowlist         200, then bytes both ways until either side closes
    CONNECT to anything else (a host, a port, an IP)  403, and nothing is dialled
    any other method (GET http://..., a plain request)  403: the model endpoint is HTTPS, so nothing needs one
    not HTTP/1.x, a head over the limit, or too slow  400
    an allowed host:port that cannot be reached     502
The host is compared as the request writes it, in lower case and without a trailing dot, with the allowlist's exact
entries: no wildcard, no suffix match, no DNS answer consulted. The proxy resolves the name itself, so the agent's
container needs no DNS of its own.

THE LOG. One line a request on stdout, which docker logs keeps and commands/ralph.py copies into the run:
    egress: listening on 0.0.0.0:3128; allowed: aiplatform.googleapis.com:443
    allowed aiplatform.googleapis.com:443
    refused example.com:443: not on the allowlist
    refused GET example.com: only CONNECT tunnels, to an allowed host:port
    failed aiplatform.googleapis.com:443: TimeoutError: timed out
A plain request is logged by its method and host alone: a URL's path and query can carry a key, and the log never does.

The standard library only: the ralph image has Python 3.12 and nothing installed for it. commands/tests/
test_ralph_egress.py runs this proxy on loopback, with a stand-in upstream in place of the model endpoint.
"""
from __future__ import annotations

import argparse
import re
import select
import socket
import socketserver
import sys
import threading
import time
from urllib.parse import urlsplit

HEAD_LIMIT, HEAD_TIMEOUT_S, DIAL_TIMEOUT_S = 8192, 10.0, 10.0
IDLE_TIMEOUT_S = 900.0              # commands/ralph.py cuts an iteration at 900 s: no tunnel needs to idle longer
LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
HOST = re.compile(rf"^(?=.{{1,253}}$){LABEL}(?:\.{LABEL})+$")      # a dotted name, or an IPv4 address written out
PORT = re.compile(r"^[0-9]{1,5}$")
REASON = {200: "Connection established", 400: "Bad Request", 403: "Forbidden", 502: "Bad Gateway"}
_SAY = threading.Lock()


def say(line: str) -> None:
    """One log line on stdout, whole: the handler threads never interleave inside a line."""
    with _SAY:
        sys.stdout.write(line + "\n")
        sys.stdout.flush()


def printable(text: str, limit: int = 80) -> str:
    """Text the agent controls, as a log can hold it: printable ASCII on one line, cut at `limit`. A request's method
    and target hold no space (its line is split on spaces), so they stay one word."""
    clean = "".join(c if 31 < ord(c) < 127 else "?" for c in text)
    return clean[:limit] + ("..." if len(clean) > limit else "")


def target(text: str) -> str:
    """host:port as the proxy compares it - lower case, no trailing dot, a port from 1 to 65535 - or ValueError."""
    host, sep, port = text.lower().rpartition(":")
    host = host.rstrip(".")
    if not sep or not HOST.match(host) or not PORT.match(port) or not 0 < int(port) < 65536:
        raise ValueError(f"not host:port: {printable(text)}")
    return f"{host}:{int(port)}"


def host_of(where: str) -> str:
    """The host a plain request names (http://host/...), never its path or query; "a path" when it names none."""
    try:
        host = urlsplit(where).hostname
    except ValueError:
        host = None
    return printable(host, 64) if host else "a path"


def decide(line: str, allow: frozenset) -> tuple[int, str, str | None]:
    """One request line's fate: (status, the log line, the host:port to dial - None when nothing is dialled)."""
    parts = line.split(" ")
    if len(parts) != 3 or parts[2] not in ("HTTP/1.1", "HTTP/1.0"):
        return 400, "refused a request that is not HTTP/1.x", None
    method, where = parts[0], parts[1]
    if method != "CONNECT":
        words = f"refused {printable(method, 16)} {host_of(where)}: only CONNECT tunnels, to an allowed host:port"
        return 403, words, None
    try:
        want = target(where)
    except ValueError:
        return 403, f"refused {printable(where)}: not host:port", None
    if want not in allow:
        return 403, f"refused {want}: not on the allowlist", None
    return 200, f"allowed {want}", want


def read_head(sock: socket.socket, timeout_s: float) -> tuple[bytes, bytes] | None:
    """The request head, to its blank line, and whatever came after it; None when it is over HEAD_LIMIT bytes, is not
    all there within timeout_s seconds, or the client hangs up first."""
    data, deadline = b"", time.monotonic() + timeout_s
    while b"\r\n\r\n" not in data:
        left = deadline - time.monotonic()
        if len(data) > HEAD_LIMIT or left <= 0:
            return None
        sock.settimeout(left)
        try:
            chunk = sock.recv(4096)
        except OSError:                          # socket.timeout is one
            return None
        if not chunk:
            return None
        data += chunk
    head, _, rest = data.partition(b"\r\n\r\n")
    return (head, rest) if len(head) <= HEAD_LIMIT else None


def reply(sock: socket.socket, status: int, words: str) -> None:
    """A refusal the client can read, then the connection closes."""
    body = f"egress: {words}\n".encode("ascii", "replace")
    head = (f"HTTP/1.1 {status} {REASON[status]}\r\nContent-Type: text/plain\r\nContent-Length: {len(body)}\r\n"
            "Connection: close\r\n\r\n")
    try:
        sock.sendall(head.encode("ascii") + body)
    except OSError:
        pass


def relay(a: socket.socket, b: socket.socket, idle_s: float) -> None:
    """Bytes both ways until either side closes, or nothing moves for idle_s seconds."""
    peer = {a: b, b: a}
    for s in peer:
        s.settimeout(None)
    while True:
        ready, _, _ = select.select([a, b], [], [], idle_s)
        if not ready:
            return
        for s in ready:
            try:
                data = s.recv(65536)
                if not data:
                    return
                peer[s].sendall(data)
            except OSError:
                return


def dial(want: str) -> socket.socket:
    """The upstream connection for an allowed host:port: the proxy's own name lookup, then TCP."""
    host, _, port = want.rpartition(":")
    return socket.create_connection((host, int(port)), DIAL_TIMEOUT_S)


class Handler(socketserver.BaseRequestHandler):
    """One client connection: its head read, the rules applied, then a tunnel or a refusal."""

    def handle(self) -> None:
        srv, client = self.server, self.request
        got = read_head(client, srv.head_timeout_s)
        client.settimeout(DIAL_TIMEOUT_S)                 # for the reply: the head's deadline may be all but spent
        if got is None:
            words = f"refused a request head over {HEAD_LIMIT} bytes, or not sent in {srv.head_timeout_s:g} s"
            srv.log(words)
            reply(client, 400, words)
            return
        head, rest = got
        status, words, want = decide(head.split(b"\r\n", 1)[0].decode("latin-1"), srv.allow)
        if want is None:
            srv.log(words)
            reply(client, status, words)
            return
        try:
            upstream = srv.dial(want)
        except OSError as e:
            srv.log(f"failed {want}: {type(e).__name__}: {printable(str(e), 120)}")
            reply(client, 502, f"{want} could not be reached")
            return
        with upstream:
            srv.log(words)
            client.sendall(b"HTTP/1.1 200 Connection established\r\n\r\n")
            if rest:
                upstream.sendall(rest)
            relay(client, upstream, srv.idle_timeout_s)


class Proxy(socketserver.ThreadingTCPServer):
    """The proxy on `listen`: `allow` the host:port entries it tunnels to; `dial` opens an allowed upstream (a test
    hands in its own, so nothing leaves the machine); `log` takes each line."""

    daemon_threads = True

    def __init__(self, listen: tuple[str, int], allow, dial=dial, log=say, head_timeout_s: float = HEAD_TIMEOUT_S,
                 idle_timeout_s: float = IDLE_TIMEOUT_S):
        self.allow = frozenset(target(a) for a in allow)
        if not self.allow:
            raise ValueError("no host:port allowed: give --allow host:port")
        self.dial, self.log = dial, log
        self.head_timeout_s, self.idle_timeout_s = head_timeout_s, idle_timeout_s
        super().__init__(listen, Handler)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="The Ralph loop's egress proxy (workshop lesson 10.10): HTTPS tunnels to "
                                             "the allowlist's host:port entries, and nothing else.")
    ap.add_argument("--allow", action="append", required=True, metavar="HOST:PORT",
                    help="a host:port it opens tunnels to (repeat for another); exact, no wildcard")
    ap.add_argument("--listen", default="0.0.0.0:3128", metavar="ADDRESS:PORT", help="where it listens (0.0.0.0:3128)")
    a = ap.parse_args(argv)
    address, _, port = a.listen.rpartition(":")
    try:
        server = Proxy((address, int(port)), a.allow)
    except (ValueError, OSError) as e:
        print(f"egress: {e}", file=sys.stderr)
        return 2
    say(f"egress: listening on {address}:{server.server_address[1]}; allowed: {', '.join(sorted(server.allow))}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
