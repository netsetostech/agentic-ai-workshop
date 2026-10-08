"""Lesson 7.6: An answer read aloud, and a question nobody hears

The first cell asks the town hall question as documind-ui-sa. It reads the answer aloud with the UI's own cached_tts, twice, and saves the audio as ~/answer.ogg. The text is the answer's first 1,500 characters, as the chat's toggle reads it. Play it: in Cloud Shell, cloudshell download ~/answer.ogg hands the file to your browser. That is the second proof: an answer read aloud. The second cell gives that audio to the UI's own transcribe, first where the UI runs it, then in eu. eu is a location Google lists chirp_3 in, for Hindi and English (India). The audio leaves India for that one call: a synthetic voice reading an answer about acme, whose policy is any (lesson 7.3). This is the function:

Run order inside this file:
1. Definition (source window 18)
2. Definition (source window 21)

Prerequisites: demo_05_the_upload_door.
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


# Original CLI workflow for step_01_definition.
COMMANDS_01 = """python -m pip install -q google-cloud-speech==2.40.0 google-cloud-texttospeech==2.37.0   # the UI image's two speech clients
python - <<'PY'
import hashlib, json, os, subprocess, sys, types, urllib.request
P = os.environ["PROJECT"]
os.environ.update(GOOGLE_CLOUD_PROJECT=P, TTS_CACHE_BUCKET=f"{P}-tts-cache", SPEECH_REGION="asia-south1")     # the UI's own settings
sys.modules["streamlit"] = types.ModuleType("streamlit")    # voice.py imports streamlit and never calls it
sys.path.insert(0, "services/frontend")
import voice                                                  # the UI's module, unchanged
API, UI = os.environ["API"], f"documind-ui-sa@{P}.iam.gserviceaccount.com"
Q = "In the FY2026 town hall, what did the CFO say happened to EMEA revenue?"
tok = subprocess.run(["gcloud", "auth", "print-identity-token", "--include-email", f"--audiences={API}", f"--impersonate-service-account={UI}"],
                     capture_output=True, text=True, check=True).stdout.strip()
req = urllib.request.Request(API + "/v1/query", data=json.dumps({"query": Q, "tenant_id": "acme"}).encode(),
                             headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
answer = json.load(urllib.request.urlopen(req, timeout=180))["answer"]
print("the answer:", answer)
text = answer[:1500]                                          # what chat.py reads aloud: the first 1,500 characters
key = hashlib.sha256(f"en-IN-Chirp3-HD-Kore|1.0|ogg|{text}".encode()).hexdigest()
blob = voice.TTS_CACHE_BUCKET.blob(f"tts/{key}.ogg")
for n in (1, 2):
    hit = blob.exists()
    audio = voice.cached_tts(text)
    print(f"read aloud {n}: {'a hit, read back from' if hit else 'a miss, synthesised by Chirp 3 HD and written to'} "
          f"gs://{P}-tts-cache/tts/{key[:12]}....ogg ({len(audio):,} bytes of Ogg Opus)")
path = os.path.expanduser("~/answer.ogg")
open(path, "wb").write(audio)
print("saved ~/answer.ogg: in Cloud Shell, cloudshell download ~/answer.ogg hands it to your browser to play")
PY

"""

def step_01_definition(session):
    """Run Definition at this checkpoint.

    The first cell asks the town hall question as documind-ui-sa. It reads the answer aloud with the UI's own cached_tts, twice, and saves the audio as ~/answer.ogg. The text is the answer's first 1,500 characters, as the chat's toggle reads it.

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (one answer, read aloud twice).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: the answer: The CFO said EMEA was the one region that shrank: revenue fell 5.2 per cent, from 96 crore to 91 crore, because two large renewals in Germany slipped into the first quarter of FY2027 [3].
    read aloud 1: a miss, synthesised by Chirp 3 HD and written to gs://documind-ai-YOUR-ID-tts-cache/tts/d28fac84987c....ogg (36,799 bytes of Ogg Opus)
    read aloud 2: a hit, read back from gs://documind-ai-YOUR-ID-tts-cache/tts/d28fac84987c....ogg (36,799 bytes of Ogg Opus)
    saved ~/answer.ogg: in Cloud Shell, cloudshell download ~/answer.ogg hands it to your browser to play
    """
    # Preserve the kit CLI's arguments, conditions and observation order.
    session.shell(COMMANDS_01)

def step_02_definition(session):
    """Run Definition at this checkpoint.

    Play it: in Cloud Shell, cloudshell download ~/answer.ogg hands the file to your browser. That is the second proof: an answer read aloud. The second cell gives that audio to the UI's own transcribe, first where the UI runs it, then in eu. eu is a location Google lists chirp_3 in, for Hindi and English (India). The audio leaves India for that one call: a synthetic voice reading an answer about acme, whose policy is any (lesson 7.3). This is the function:

    Args: session is the active lesson run, with validated settings and saved prerequisites.
    Operations: bash — run in the operator shell, in the kit (the answer's audio, transcribed twice).
    Returns: None; observations are printed or saved by the lesson code.
    Failures propagate to the session; inspect its failed attempt before continuing.

    Example: Run this file after its README prerequisites, or set a breakpoint in this function.
    Observe: transcribe() where the UI runs it, asia-south1: ''
    transcribe() in eu: 'The CFO said EMEA was the one region that shrank: revenue fell 5.2 per cent, from 96 crore to 91 crore, because two large renewals in Germany slipped into the first quarter of FY2027.'
    """
    import importlib, os, sys, types
    P = os.environ["PROJECT"]
    os.environ.update(GOOGLE_CLOUD_PROJECT=P, TTS_CACHE_BUCKET=f"{P}-tts-cache", SPEECH_REGION="asia-south1")     # the UI's own settings
    sys.modules["streamlit"] = types.ModuleType("streamlit")    # voice.py imports streamlit and never calls it
    sys.path.insert(0, "services/frontend")
    import voice                                                  # the UI's module, unchanged
    audio = open(os.path.expanduser("~/answer.ogg"), "rb").read()
    print(f"transcribe() where the UI runs it, asia-south1: {voice.transcribe(audio)!r}")
    os.environ["SPEECH_REGION"] = "eu"                          # the same function, pointed at a location Google lists chirp_3 in
    voice = importlib.reload(voice)
    print(f"transcribe() in eu: {voice.transcribe(audio)!r}")

def demonstrate(session):
    """Run this section in source order, saving each function's outcome.

    Example: main() opens the configured session and calls demonstrate(session).
    A failed step stops this sequence; inspect its evidence before an explicit retry.
    """
    run_steps(session, [
        ('source_18', step_01_definition),
        ('source_21', step_02_definition),
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
