"""What a model call cost, priced where rag-api is not: the chat service's own model calls (workshop lesson 5.5).

rag-api prices its answers in services/rag-api/cost.py, from BigQuery's model_prices table with a fallback. The chat
service has no BigQuery role and needs no table: it prices each of its own calls at list price, from the same
fallback, here. commands/tests/test_chat_limits.py reads cost.py's FALLBACK and holds this table equal to it, so the
two cannot drift apart quietly; a price change is made in both. The cached tokens are part of tokens_in and are
billed at a tenth of the input rate, as cost.py bills them. The local profile (Ollama on a laptop) costs nothing.

Standard prices, USD per 1M tokens (input, output). The self-hosted gateway routes are a rate, not a price: see
cost.py's comment.
"""
from __future__ import annotations

import os

USD_INR = 85            # the course-wide rate, as in cost.py and shared/documind_tools.py
PROFILE = os.environ.get("DOCUMIND_PROFILE", "gcp")     # the same switch shared/profile.py reads
DEFAULT_MODEL = "gemini-3.6-flash"

PRICES = {"gemini-3.6-flash": (1.50, 7.50),
          "gemini-3.1-flash-lite": (0.25, 1.50),
          "gemini-3.1-pro-preview": (2.00, 12.00),
          "documind-general": (1.50, 7.50),
          "documind-reasoning": (2.00, 12.00),
          "documind-slm": (20.5, 20.5),
          "documind-inference": (20.5, 20.5),
          "documind-gke": (20.5, 20.5)}


def usd(model: str | None, tokens_in: int, tokens_out: int, cached_tokens: int = 0) -> float:
    """One call's cost in USD. An unknown model is priced as flash, as cost.py prices one. A tuned endpoint's
    path is unknown here too: cost.py bills it at its base model (RAG_MODEL_BASE, which only rag-api is given),
    this at flash."""
    if PROFILE == "local":
        return 0.0
    usd_in, usd_out = PRICES.get(model or DEFAULT_MODEL, PRICES[DEFAULT_MODEL])
    billable_in = max(tokens_in - cached_tokens, 0)
    return (billable_in * usd_in + cached_tokens * usd_in * 0.10 + tokens_out * usd_out) / 1_000_000


def inr(usd_amount: float) -> float:
    return usd_amount * USD_INR
