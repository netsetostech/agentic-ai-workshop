"""Lesson 9.3: The vLLM service, read

Do it

Run order inside this file:
1. Do it (source window 10)

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


def step_01_the_vllm_service_read(session):
    """Run Do it at this checkpoint.

    Do it

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (reads the service's files; no network).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the image: FROM vllm/vllm-openai:v0.28.0, then python -m uvicorn main:app --host 0.0.0.0 --port 8080 --workers 1 --timeout-keep-alive 120
      weights in the image: none - no step fetches them, and the HF_TOKEN build-arg cloudbuild.yaml passes has no ARG to land in
      so the engine downloads google/gemma-3-4b-it when it starts, from Hugging Face
      the environment make deploy-vllm gives it: GOOGLE_CLOUD_PROJECT - no Hugging Face token
    the service: 1 nvidia-l4, 8 vCPU, 32Gi; 0 to 1 instance; 32 requests at a time; startup probe 120 s + 5 x 30 s = 270 s
    its door: every chat completion needs an X-API-Key header, hashed and looked up in Firestore (api_keys then tenants)
      what the gateway's token pro
    """
    import glob, os, re
    rd = lambda p: open(p, encoding="utf-8").read()
    dock, main, auth, logm, proxy, cfg, mk = (rd(p) for p in ("services/gemma-vllm/Dockerfile", "services/gemma-vllm/main.py",
        "services/gemma-vllm/auth.py", "services/gemma-vllm/logging_module.py", "services/litellm/token_proxy.py",
        "services/litellm/config.yaml", "Makefile"))
    base = re.search(r"^FROM (\S+)", dock, re.M).group(1)
    cmd = " ".join(re.findall(r'"([^"]+)"', re.search(r"CMD \[(.*?)\]", dock, re.S).group(1)))
    fetches = [l for l in dock.splitlines() if re.search(r"huggingface|hf_hub|snapshot_download|wget|curl", l, re.I)]
    model = re.search(r'os.getenv\("MODEL_NAME", "([^"]+)"\)', main).group(1)
    deploy = mk.split("\ndeploy-vllm:", 1)[1].split("\n\n", 1)[0]
    flag = dict(re.findall(r"--([a-z-]+) ([^\s-]\S*)", deploy))            # a flag and its value; a bare flag takes none
    d, f, p = (int(re.search(k + r"=(\d+)", deploy).group(1)) for k in ("initialDelaySeconds", "failureThreshold", "periodSeconds"))
    env_names = [e.split("=")[0] for e in flag["set-env-vars"].split(",")]
    print(f"the image: FROM {base}, then {cmd}")
    print("  weights in the image: " + ("a download step" if fetches else "none - no step fetches them")
          + ("" if re.search(r"^ARG HF_TOKEN", dock, re.M) else ", and the HF_TOKEN build-arg cloudbuild.yaml passes has no ARG to land in"))
    print(f"  so the engine downloads {model} when it starts, from Hugging Face")
    print(f"  the environment make deploy-vllm gives it: {', '.join(env_names)} - no Hugging Face token")
    print(f"the service: {flag['gpu']} {flag['gpu-type']}, {flag['cpu']} vCPU, {flag['memory']}; {flag['min-instances']} to {flag['max-instances']} instance; "
          f"{flag['concurrency']} requests at a time; startup probe {d} s + {f} x {p} s = {d + f * p} s")
    header = re.search(r'APIKeyHeader\(name="([^"]+)"\)', auth).group(1)
    cols = list(dict.fromkeys(re.findall(r'collection\("(\w+)"\)', auth)))
    print(f"its door: every chat completion needs an {header} header, hashed and looked up in Firestore ({' then '.join(cols)})")
    print(f"  what the gateway's token proxy sends: its own ID token as Authorization, and no {header}")
    writers = [n for n in glob.glob("**/*.py", recursive=True) if "gemma-vllm" not in n and 'collection("api_keys")' in rd(n)]
    print(f"  code elsewhere in the kit that writes an api_keys document: {len(writers) or 'none'}")
    grants = sum(rd(t).count("google_service_account.vllm.email") for t in glob.glob("terraform/*.tf")) - 1      # one is the output
    print(f"  roles Terraform grants documind-vllm-sa, the account it runs as: {grants or 'none'}")
    print("its request log: BigQuery table " + repr(re.search(r'BQ_TABLE = "([^"]+)"', logm).group(1)))
    route = cfg.split("- model_name: documind-inference", 1)[1].split("- model_name:", 1)[0]
    fall = re.search(r"- documind-inference: \[([^\]]*)\]", cfg).group(1).replace('"', "")
    api = re.search(r"api_base: (\S+)", route).group(1)
    print(f"the gateway's route to it: documind-inference, {api}, falling back to {fall}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_10', step_01_the_vllm_service_read),
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
