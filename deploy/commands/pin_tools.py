#!/usr/bin/env python3
"""make pin-tools: review the A2A peer's MCP tools and pin them, or check the pins against the server (lesson 10.8).

    python commands/pin_tools.py            [--url URL | --server-local] [--out services/agent/tool_pins.json]
    python commands/pin_tools.py --check    [--url URL | --server-local]      # make pin-tools CHECK=1

It lists the tools the peer would get - from a running MCP server at --url (the mcp 1.x streamable-HTTP client, as the
peer's ADK client lists them), or in process from the kit's own server with --server-local - and, for each, the
fingerprint services/agent/pins.py reads at run time (name, description, input schema). Without --check it writes
tool_pins.json: the reviewed fingerprint of every tool, with the description and schema a person signs off on, so the
git diff of a re-pin shows exactly what changed. With --check it compares the server's tools with the pinned set and
prints, then exits 1, for any tool added, removed or changed - the drill in the lesson edits one tool's description and
watches make pin-tools CHECK=1 fail. It makes no model call and reads no corpus: listing tools needs neither.

The peer only enforces the pins when TOOL_PINS=on (pins.py); this tool neither sets nor needs that switch.
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from pathlib import Path

KIT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(KIT / "services" / "agent"))
import pins  # noqa: E402  - the peer's own module: one fingerprint, read the same way here and at run time

DEFAULT_OUT = KIT / "services" / "agent" / "tool_pins.json"


def _tool_record(name: str, description, schema) -> dict:
    return {"fingerprint": pins.fingerprint(name, description, schema), "description": description or "",
            "input_schema": schema or {}}


async def _tools_from_url(url: str) -> list[tuple[str, str | None, dict | None]]:
    """The server's tools over the MCP wire, exactly as the peer's ADK client lists them."""
    from mcp import ClientSession
    from mcp.client.streamable_http import streamablehttp_client

    async with streamablehttp_client(url) as (read, write, _):
        async with ClientSession(read, write) as session:
            await session.initialize()
            listed = await session.list_tools()
    return [(t.name, t.description, t.inputSchema) for t in listed.tools]


def _tools_from_server_local() -> list[tuple[str, str | None, dict | None]]:
    """The kit's own MCP server's tools, listed in process (fastmcp) - offline, no HTTP, no credential."""
    sys.path.insert(0, str(KIT))
    from services.mcp import server

    async def _list():
        return [t.to_mcp_tool() for t in await server.mcp.list_tools()]

    return [(t.name, t.description, t.inputSchema) for t in asyncio.run(_list())]


def list_tools(url: str | None, server_local: bool) -> list[tuple[str, str | None, dict | None]]:
    if server_local or not url:
        return _tools_from_server_local()
    return asyncio.run(_tools_from_url(url))


def pinned(tools: list[tuple[str, str | None, dict | None]]) -> dict:
    """The tool_pins.json a review of `tools` would write: one entry per tool, names sorted."""
    return {"version": 1,
            "note": ("The A2A peer's reviewed MCP tools (workshop lesson 10.8). services/agent/pins.py keeps only a "
                     "tool whose name and fingerprint are here when TOOL_PINS=on. Re-pin with commands/pin_tools.py "
                     "(make pin-tools) after reviewing the diff; make pin-tools CHECK=1 fails on any drift."),
            "tools": {name: _tool_record(name, desc, schema) for name, desc, schema in sorted(tools)}}


def check(tools: list[tuple[str, str | None, dict | None]], pins_doc: dict) -> list[str]:
    """What has drifted between `tools` and the pinned set: tools added, removed, or changed since they were pinned."""
    have = {name: pins.fingerprint(name, desc, schema) for name, desc, schema in tools}
    want = {name: entry["fingerprint"] for name, entry in pins_doc.get("tools", {}).items()}
    problems = []
    for name in sorted(set(have) - set(want)):
        problems.append(f"added, never pinned: {name}")
    for name in sorted(set(want) - set(have)):
        problems.append(f"pinned but gone from the server: {name}")
    for name in sorted(set(have) & set(want)):
        if have[name] != want[name]:
            problems.append(f"changed since it was pinned: {name}")
    return problems


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n", 1)[0])
    ap.add_argument("--url", help="an MCP streamable-HTTP endpoint, e.g. http://localhost:8000/mcp")
    ap.add_argument("--server-local", action="store_true", help="list the kit's own server in process (offline)")
    ap.add_argument("--check", action="store_true", help="compare the server's tools with tool_pins.json and exit 1 on drift")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help="where to write the pins (default: services/agent/tool_pins.json)")
    args = ap.parse_args(argv)

    tools = list_tools(args.url, args.server_local)
    if args.check:
        try:
            pins_doc = json.loads(args.out.read_text(encoding="utf-8"))
        except FileNotFoundError:
            print(f"no pins to check: {args.out} does not exist (run make pin-tools first)", file=sys.stderr)
            return 1
        problems = check(tools, pins_doc)
        if problems:
            print(f"tool pins are out of date ({len(problems)}):")
            for p in problems:
                print(f"  - {p}")
            print("review the change, then re-pin with make pin-tools (no CHECK).")
            return 1
        print(f"tool pins are current: {len(tools)} tools, all pinned and unchanged.")
        return 0
    doc = pinned(tools)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:    # LF, whatever the operator's OS
        f.write(json.dumps(doc, indent=2, sort_keys=False) + "\n")
    print(f"pinned {len(doc['tools'])} tools to {args.out}: {', '.join(doc['tools'])}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
