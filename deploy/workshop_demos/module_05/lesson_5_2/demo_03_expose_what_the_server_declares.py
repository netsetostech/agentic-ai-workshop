"""Lesson 5.2: Expose: what the server declares

Do it: fastmcp Do it: what the server declares

Run order inside this file:
1. Do it: fastmcp (source window 7)
2. Do it: what the server declares (source window 9)

Prerequisites: setup_prepare.
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


# Original CLI workflow for step_01_fastmcp.
COMMANDS_01 = """python -m pip install -q "fastmcp==3.4.7" "uvicorn==0.52.4"   # the MCP image's pins, in the operator venv
python -c 'import fastmcp; print("fastmcp", fastmcp.__version__)'

"""

def step_01_fastmcp(session):
    """Run Do it: fastmcp at this checkpoint.

    Do it: fastmcp

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (fastmcp in the operator venv).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: fastmcp 3.4.7
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_what_the_server_declares(session):
    """Run Do it: what the server declares at this checkpoint.

    Do it: what the server declares

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the server imported and listed in memory; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: server DocuMind, protocol 2025-11-25
    instructions: DocuMind answers questions about a tenant's documents with citations. Use `ret...
    retrieve: Retrieve grounded passages from DocuMind's corpus, with the...
       query            string          required            The question, in natural...
       doc_type         string          default 'all'       policy, contract, invoice,...
       top_k            integer         default 5           How many passages to return...
       tenant           string or null  default None        Only if you belong to several...
    list_documents: What is in the caller's corpus: one row per uploaded document,...
       status           string          default 'indexed'   indexed, p
    """
    import asyncio, logging, sys, textwrap, warnings
    warnings.filterwarnings("ignore")
    sys.path.insert(0, ".")
    import services.mcp.server as server               # the kit's server, imported, not run
    logging.disable(logging.WARNING)                   # its INFO lines; step 6 reads them from a running server
    from fastmcp import Client
    async def main():
        """Run this cell's asynchronous MCP operation and print its returned tool declarations or evidence.
        
        Example: main()
        """
        async with Client(server.mcp) as c:            # in memory: no HTTP and no identity, and listing needs neither
            info = c.initialize_result
            print(f"server {info.serverInfo.name}, protocol {info.protocolVersion}")
            print(f"instructions: {info.instructions[:78]}...")
            for t in await c.list_tools():
                s = t.inputSchema
                print(f"{t.name}: {textwrap.shorten(t.description.splitlines()[0], 66, placeholder='...')}")
                for p, spec in s["properties"].items():
                    kind = spec.get("type") or " or ".join(a["type"] for a in spec.get("anyOf", []))
                    need = "required" if p in s.get("required", []) else f"default {spec.get('default')!r}"
                    print(f"   {p:16} {kind:14}  {need:19} {textwrap.shorten(spec.get('description', ''), 32, placeholder='...')}")
    asyncio.run(main())

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_7', step_01_fastmcp),
        ('source_9', step_02_what_the_server_declares),
    ], retry_failed=RETRY_FAILED_STEP, cleanup=False, finalize=False)


def main():
    """Open the lesson session and run this section.

    Example: use Run/Debug on this file with the rag-shell-venv interpreter.
    Project settings and completed prerequisites come from the shared setup.
    """
    with DemoSession(__file__, live=True, repeat=REPEAT) as session:
        demonstrate(session)


if __name__ == "__main__":
    main()
