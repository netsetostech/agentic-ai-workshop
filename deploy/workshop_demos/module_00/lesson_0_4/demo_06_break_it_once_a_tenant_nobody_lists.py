"""Lesson 0.4: Break it once: a tenant nobody lists

The same smoke without DOCUMIND_TENANT: one check fails, and you follow it to the code that printed it and the code that refused. Run the smoke again without the tenant, which the Makefile's header example leaves out too. Keep the URL and the project, so the smoke still has an identity to ask with. env -u makes sure no DOCUMIND_TENANT survives from an earlier shell, and the last command prints make's own exit status. Find why. The question named a tenant because smoke.py always sends one: DOCUMIND_TENANT, and without it, tenant-smoke. Its own docstring predicted this failure: Check the roster. Which tenants is documind-ui-sa on? make roster decides, through one function in commands/lane.py, and its dry run prints the plan without touching Firestore: Check the roster. Which tenants is documind-ui-sa on? make roster decides, through one function in commands/lane.py, and its dry run prints the plan without touching Firestore: The UI's account is on acme, zeta and globex, and no line names tenant-smoke. The plan is what make roster wrote in lesson 0.3. To see the rosters as they are now, read them from Firestore with the kit's own module:

Run order inside this file:
1. Break it once: a tenant nobody lists (source window 23)
2. Break it once: a tenant nobody lists (source window 29)
3. Break it once: a tenant nobody lists (source window 31)

Prerequisites: demo_05_make_smoke_one_line_per_check.
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


# Original CLI workflow for step_01_break_it_once_a_tenant_nobody_lists.
COMMANDS_01 = """# on purpose: no DOCUMIND_TENANT, which the Makefile's header example leaves out too
env -u DOCUMIND_TENANT make smoke DOCUMIND_API_URL="$API" DOCUMIND_PROJECT="$PROJECT"; echo "exit status: $?"

"""

def step_01_break_it_once_a_tenant_nobody_lists(session):
    """Run Break it once: a tenant nobody lists at this checkpoint.

    The same smoke without DOCUMIND_TENANT: one check fails, and you follow it to the code that printed it and the code that refused. Run the smoke again without the tenant, which the Makefile's header example leaves out too. Keep the URL and the project, so the smoke still has an identity to ask with. env -u makes sure no DOCUMIND_TENANT survives from an earlier shell, and the last command prints make's own exit status.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same smoke without a tenant: one check fails, on purpose).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/smoke_broken.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_break_it_once_a_tenant_nobody_lists.
COMMANDS_02 = """python commands/lane.py --project "$PROJECT" roster --tenant acme --members "$ME" --dry-run     # prints the plan, writes nothing

"""

def step_02_break_it_once_a_tenant_nobody_lists(session):
    """Run Break it once: a tenant nobody lists at this checkpoint.

    Find why. The question named a tenant because smoke.py always sends one: DOCUMIND_TENANT, and without it, tenant-smoke. Its own docstring predicted this failure: Check the roster. Which tenants is documind-ui-sa on? make roster decides, through one function in commands/lane.py, and its dry run prints the plan without touching Firestore:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (no network: the dry run prints and returns).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: would put you@your-company.com on acme
    would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
    would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
    would put documind-ui-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
    would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
    would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
    would put documind-mcp-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on globex
    would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on acme
    would put documind-chat-sa@documind-ai-YOUR-ID.iam.gserviceaccount.com on zeta
    would put documind-chat-sa@documin
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_break_it_once_a_tenant_nobody_lists.
COMMANDS_03 = """for t in tenant-smoke acme; do echo "== $t"; GOOGLE_CLOUD_PROJECT="$PROJECT" python -m shared.tenancy list "$t"; done

"""

def step_03_break_it_once_a_tenant_nobody_lists(session):
    """Run Break it once: a tenant nobody lists at this checkpoint.

    Check the roster. Which tenants is documind-ui-sa on? make roster decides, through one function in commands/lane.py, and its dry run prints the plan without touching Firestore: The UI's account is on acme, zeta and globex, and no line names tenant-smoke. The plan is what make roster wrote in lesson 0.3. To see the rosters as they are now, read them from Firestore with the kit's own module:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (two Firestore reads; writes nothing).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/roster_read.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_23', step_01_break_it_once_a_tenant_nobody_lists),
        ('source_29', step_02_break_it_once_a_tenant_nobody_lists),
        ('source_31', step_03_break_it_once_a_tenant_nobody_lists),
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
