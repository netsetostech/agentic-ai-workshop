"""The A2A peer of workshop lesson 10.6, as Vertex AI Agent Engine runs it (workshop lesson 10.9).

commands/managed_peer.py stages this file as the package documind_peer/__init__.py, beside the peer's own
services/agent/agent.py and requirements.txt copied byte for byte, and deploys the package with google-adk's own
deploy (`adk deploy agent_engine`). ADK's image runs `adk api_server`, which imports the package and serves the
`root_agent` it finds there. That is the peer's own agent - the object agent.py builds at import, the one its A2A app
serves on Cloud Run - with one setting changed here, never in the peer: where its model is called.

Why the model needs it. ADK's Agent Engine image sets GOOGLE_CLOUD_LOCATION to the instance's region (google-adk
2.8.0, cli/cli_deploy.py's Dockerfile template: ENV GOOGLE_CLOUD_LOCATION={gcp_region}); the platform reserves the
name, so the deploy cannot set it back; and Gemini 3.x is served only from location global. On Cloud Run the peer's
deploy sets GOOGLE_CLOUD_LOCATION=global (commands/lesson-8.4.sh). Here GlobalGemini, the subclass google-adk 2.8.0
documents for exactly this (models/google_llm.py, the Gemini class docstring), pins the client to global.

Two settings are not code here. The cap of 12 model calls a turn is ADK_MAX_LLM_CALLS in the deploy's environment
(RunConfig's default reads it, google-adk 2.8.0 agents/run_config.py). Message content stays out of the spans because
the deploy asks for telemetry (otel_to_cloud), and ADK's deploy then sets ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS=false.

One line goes to the runtime's log at import: the versions the image installed, and the location the platform set,
which make managed-peer-trace reads back. ADK's deploy appends google-cloud-aiplatform to the requirements without
a version, so the image is the only place the version it took is written down.
"""
from __future__ import annotations

import importlib.metadata
import json
import logging
import os
from functools import cached_property

from google.adk.models.google_llm import Gemini
from google.genai import Client

from . import agent as peer

log = logging.getLogger("documind.managed_peer")
VERSIONS = ("google-adk", "google-cloud-aiplatform", "a2a-sdk", "google-genai", "google-auth")


class GlobalGemini(Gemini):
    """Gemini on location global, whatever GOOGLE_CLOUD_LOCATION says."""

    @cached_property
    def api_client(self) -> Client:
        return Client(enterprise=True, location="global")


def _version(dist: str):
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return None


root_agent = peer.agent
root_agent.model = GlobalGemini(model=peer.MODEL)

log.info(json.dumps({"event": "managed_peer_up", "agent": root_agent.name, "model": peer.MODEL,
                     "model_location": "global", "GOOGLE_CLOUD_LOCATION": os.environ.get("GOOGLE_CLOUD_LOCATION"),
                     "ADK_MAX_LLM_CALLS": os.environ.get("ADK_MAX_LLM_CALLS"),
                     "ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS": os.environ.get("ADK_CAPTURE_MESSAGE_CONTENT_IN_SPANS"),
                     "versions": {d: _version(d) for d in VERSIONS}}, sort_keys=True))
