"""Lesson 10.10: The live loop: Gemini CLI in a container, on a model-only key

DRY_RUN=1 prints the two docker run lines an iteration would run, and starts nothing: no Docker, image or key is needed. By default the agent's container can reach whatever the machine it runs on can reach. RALPH_EGRESS=proxy holds it to the model endpoint. Each iteration gets an internal network of its own, which has no route out, and a third container from the same image: commands/ralph/egress.py, an allowlisting forward proxy, on that network and on Docker's default bridge. The agent's container joins the internal network alone, with HTTPS_PROXY naming the proxy. The proxy opens a tunnel to aiplatform.googleapis.com:443 and refuses every other host, port and plain request without dialling it. A tool that ignores the proxy has no route at all, because the internal network has none. The network and the proxy are made before each iteration and removed after it, and the proxy's log, a line a request, is kept in the run's iterations/. The agent's line is the one above with two flags added, --network and HTTPS_PROXY. By default the agent's container can reach whatever the machine it runs on can reach. RALPH_EGRESS=proxy holds it to the model endpoint. Each iteration gets an internal network of its own, which has no route out, and a third container from the same image: commands/ralph/egress.py, an allowlisting forward proxy, on that network and on Docker's default bridge. The agent's container joins the internal network alone, with HTTPS_PROXY naming the proxy. The proxy opens a tunnel to aiplatform.googleapis.com:443 and refuses every other host, port and plain request without dialling it. A tool that ignores the proxy has no route at all, because the internal network has none. The network and the proxy are made before each iteration and removed after it, and the proxy's log, a line a request, is kept in the run's iterations/. The agent's line is the one above with two flags added, --network and HTTPS_PROXY. The kit's tests run the proxy on your machine's loopback, with a stand-in in place of the model endpoint, and the loop against a stub Docker. A live Docker is the author's check. make ralph-probe RALPH_EGRESS=proxy needs no key and makes no model call. From inside the agent's container it tries example.com and 169.254.169.254, the metadata server's address, directly, then example.com and the model endpoint through the proxy. It also prints whether example.com's name resolved there: whether a name lookup leaves the internal network is Docker's to decide, not the proxy's. Without the author's cap and key, the live loop does not start. It has no default spend, and it runs only on a model-only key, never on your gcloud login or Application Default Credentials.

Run order inside this file:
1. Do it: the two containers, printed (source window 62)
2. Do it: the egress proxy, printed (source window 64)
3. Do it: the egress proxy, printed (source window 66)
4. Do it: the live loop on your lane (source window 68)

Prerequisites: demo_07_the_reviewer_a_linter_first_then_gemini_on_your_lane.
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


# Original CLI workflow for step_01_the_two_containers_printed.
COMMANDS_01 = """make ralph DRY_RUN=1

"""

def step_01_the_two_containers_printed(session):
    """Run Do it: the two containers, printed at this checkpoint.

    DRY_RUN=1 prints the two docker run lines an iteration would run, and starts nothing: no Docker, image or key is needed.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the live loop's two containers, printed; nothing starts).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ralph --dry-run: the two containers an iteration runs, and nothing else; nothing is started
      the agent: docker run --rm --init --name ralph-<run>-01 --cap-drop ALL --security-opt no-new-privileges --read-only --tmpfs /tmp --memory 2g --pids-limit 256 --cpus 2 --user UID:GID --env-file <run>/agent.env --env RALPH_MODEL=gemini-3.6-flash --env HOME=/tmp --mount type=bind,source=<run>/workspace,target=/work --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph/PROMPT.md,target=/ralph/PROMPT.md,readonly --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph/settings.json,target=/etc/gemini-cli/settings.json,readonly --workdir /work documind-ralph ralph-iteration
        it
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

# Original CLI workflow for step_02_the_egress_proxy_printed.
COMMANDS_02 = """make ralph DRY_RUN=1 RALPH_EGRESS=proxy

"""

def step_02_the_egress_proxy_printed(session):
    """Run Do it: the egress proxy, printed at this checkpoint.

    By default the agent's container can reach whatever the machine it runs on can reach. RALPH_EGRESS=proxy holds it to the model endpoint. Each iteration gets an internal network of its own, which has no route out, and a third container from the same image: commands/ralph/egress.py, an allowlisting forward proxy, on that network and on Docker's default bridge. The agent's container joins the internal network alone, with HTTPS_PROXY naming the proxy. The proxy opens a tunnel to aiplatform.googleapis.com:443 and refuses every other host, port and plain request without dialling it. A tool that ignores the proxy has no route at all, because the internal network has none. The network and the proxy are made before each iteration and removed after it, and the proxy's log, a line a request, is kept in the run's iterations/. The agent's line is the one above with two flags added, --network and HTTPS_PROXY.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the same, behind the egress proxy; nothing starts).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ralph --dry-run: an iteration's network and three containers, the proxy, the agent and the oracle, and nothing else; nothing is started
      first, RALPH_EGRESS=proxy: the agent's internal network, and the proxy that opens a tunnel to aiplatform.googleapis.com:443 alone:
        docker network create --internal ralph-<run>-01-net
        docker run -d --name ralph-<run>-01-egress --network bridge --read-only --cap-drop ALL --security-opt no-new-privileges --memory 256m --pids-limit 128 --user UID:GID --mount type=bind,source=/home/you/deploy_module_rag/commands/ralph/egress.py,target=/egress/egress.py,readonly documind-ralph python3 -I -B -u /egress/egress.py --listen 0.0.0.0:3128 --allow aiplatform.go
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_02)

# Original CLI workflow for step_03_the_egress_proxy_printed.
COMMANDS_03 = """make ralph-image                            # Gemini CLI at the kit's pin (mk/coding.mk); once a Cloud Shell session
make ralph-probe RALPH_EGRESS=proxy         # no key, no model call: Rs 0

"""

def step_03_the_egress_proxy_printed(session):
    """Run Do it: the egress proxy, printed at this checkpoint.

    By default the agent's container can reach whatever the machine it runs on can reach. RALPH_EGRESS=proxy holds it to the model endpoint. Each iteration gets an internal network of its own, which has no route out, and a third container from the same image: commands/ralph/egress.py, an allowlisting forward proxy, on that network and on Docker's default bridge. The agent's container joins the internal network alone, with HTTPS_PROXY naming the proxy. The proxy opens a tunnel to aiplatform.googleapis.com:443 and refuses every other host, port and plain request without dialling it. A tool that ignores the proxy has no route at all, because the internal network has none. The network and the proxy are made before each iteration and removed after it, and the proxy's log, a line a request, is kept in the run's iterations/. The agent's line is the one above with two flags added, --network and HTTPS_PROXY. The kit's tests run the proxy on your machine's loopback, with a stand-in in place of the model endpoint, and the loop against a stub Docker. A live Docker is the author's check. make ralph-probe RALPH_EGRESS=proxy needs no key and makes no model call. From inside the agent's container it tries example.com and 169.254.169.254, the metadata server's address, directly, then example.com and the model endpoint through the proxy. It also prints whether example.com's name resolved there: whether a name lookup leaves the internal network is Docker's to decide, not the proxy's.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — the author's run, in Cloud Shell (batch 4): the egress proxy on a live docker.
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: [awaiting the author's run: data/isolation.txt]
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_03)

# Original CLI workflow for step_04_the_live_loop_on_your_lane.
COMMANDS_04 = """set +e +o pipefail   # as the page runs it: its expected output shows a command here failing, as the cell means it to
make ralph                        # live, with no cap
make ralph RALPH_BUDGET_INR=30    # live, with a cap and no key
true   # that failure is the cell's answer: compare the output with the page's expected window


"""

def step_04_the_live_loop_on_your_lane(session):
    """Run Do it: the live loop on your lane at this checkpoint.

    Without the author's cap and key, the live loop does not start. It has no default spend, and it runs only on a model-only key, never on your gcloud login or Application Default Credentials.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the live loop without the author's cap or key).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: ERROR: the live loop has no default spend: give it RALPH_BUDGET_INR=<cap>, set from a dry run (make ralph RALPH_MAX_ITERS=1 RALPH_BUDGET_INR=<a small cap> reads one iteration's rupees)
    make: *** [mk/coding.mk:33: ralph] Error 2
    ERROR: RALPH_API_KEY is not set: the live loop runs only on a model-only credential the author creates for the run and deletes after it, never on your gcloud login or ADC
    make: *** [mk/coding.mk:33: ralph] Error 2
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_04)

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_62', step_01_the_two_containers_printed),
        ('source_64', step_02_the_egress_proxy_printed),
        ('source_66', step_03_the_egress_proxy_printed),
        ('source_68', step_04_the_live_loop_on_your_lane),
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
