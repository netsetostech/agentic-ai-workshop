"""Pin the A2A peer's MCP tools to a reviewed set, so a changed or unknown tool never reaches the model (lesson 10.8).

Off unless TOOL_PINS=on on documind-agent. agent.py then gives build_agent's McpToolset a tool_filter from here, and
only a tool whose name AND fingerprint are in tool_pins.json reaches the peer's model; any other is dropped before the
first call and logged tool_unpinned. Off, the toolset gets no filter and every tool the server lists is used, as before.

Why a peer that already trusts its MCP server still pins its tools: the server is another team's (lesson 10.6), and its
tool list can change under the peer - a new tool, or a tool whose DESCRIPTION is rewritten to address the model (a
tool-description injection, or a swap after the tool was first trusted). The description and the input schema are what
the model reads to decide when and how to call a tool, so a changed description is, to the model, a changed tool. The
fingerprint is a sha256 over the tool's name, description and input schema - exactly what the model is shown - so any
of those changing unpins the tool until a person reviews the change and re-pins it (commands/pin_tools.py, make
pin-tools). The pin is not a signature: it proves the tool is the one a person read, not who wrote it.

tool_pins.json sits beside this file (the image copies services/agent/ whole) and holds the reviewed fingerprint of
each pinned tool, with the description and schema a person signed off on. commands/pin_tools.py writes and checks it
against the server's own tool list. Like agent.py, this file imports nothing from the kit: the fingerprint is read
from the tool object ADK hands the filter, by duck typing, so the peer carries no shared code.
"""
from __future__ import annotations

import hashlib
import json
import logging
import os
from pathlib import Path

log = logging.getLogger("documind.agent.pins")

TOOL_PINS = os.environ.get("TOOL_PINS", "off")                       # on -> filter; anything else -> every tool passes
PINS_FILE = Path(os.environ.get("TOOL_PINS_FILE", "") or Path(__file__).with_name("tool_pins.json"))


def fingerprint(name: str, description, input_schema) -> str:
    """A stable sha256 over what the model is shown of a tool: its name, its description and its input schema."""
    blob = json.dumps({"name": name or "", "description": description or "", "inputSchema": input_schema or {}},
                      sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


def tool_parts(tool) -> tuple[str, str | None, dict | None]:
    """(name, description, input schema) of a tool, however it is given: an ADK McpTool (its raw MCP tool behind
    raw_mcp_tool/_mcp_tool), a raw MCP tool, or a plain tool with name and description."""
    raw = getattr(tool, "raw_mcp_tool", None) or getattr(tool, "_mcp_tool", None) or tool
    schema = getattr(raw, "inputSchema", None)
    if schema is None:
        schema = getattr(raw, "input_schema", None)
    return getattr(raw, "name", "") or "", getattr(raw, "description", None), schema


def fingerprint_of(tool) -> str:
    name, description, schema = tool_parts(tool)
    return fingerprint(name, description, schema)


def load(path: Path | str = PINS_FILE) -> dict:
    """name -> reviewed fingerprint, from tool_pins.json; empty when the file is missing."""
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
    except FileNotFoundError:
        return {}
    return {name: entry["fingerprint"] for name, entry in data.get("tools", {}).items()}


def unpinned_reason(tool, pins: dict) -> str | None:
    """Why `tool` is not pinned, or None when it is pinned and unchanged."""
    name, _, _ = tool_parts(tool)
    if name not in pins:
        return "not in tool_pins.json"
    if fingerprint_of(tool) != pins[name]:
        return "fingerprint changed since it was pinned"
    return None


def tool_filter():
    """McpToolset's tool_filter: None when TOOL_PINS is not on, so every tool the server lists passes, as before; else a
    predicate that keeps only the pinned, unchanged tools and logs tool_unpinned for each one it drops. The pins are
    read once, here, as build_agent builds the toolset."""
    if TOOL_PINS != "on":
        return None
    pins = load()
    if not pins:
        log.info(json.dumps({"event": "tool_unpinned", "tool": None,
                             "reason": "TOOL_PINS=on but tool_pins.json is empty or missing - every tool is dropped"}))

    def keep(tool, readonly_context=None) -> bool:
        reason = unpinned_reason(tool, pins)
        if reason is None:
            return True
        name, _, _ = tool_parts(tool)
        log.info(json.dumps({"event": "tool_unpinned", "tool": name, "reason": reason}))
        return False

    return keep
