"""Workshop lesson 2.5's rewrite stage on /v1/query: the question in the documents' words, searched before retrieval.

QUERY_REWRITE=off (config.py; the default) is no stage at all: search_query() returns the question and the vector the
handler already has, makes no call and writes nothing, so the answer, its stages and the usage row are what they were.
On, shared/query_rewrite.py asks QUERY_REWRITE_MODEL (gemini-3.1-flash-lite) on the generator's global client for the
question as a search query, and search_query() returns what retrieve() is to search: the rewrite and its own embedding,
or the question and its vector when the model gave the question back, when the rewrite dropped a code, a grade or a
figure (the literal guard), or when anything failed. The rewrite changes what is searched, never what is reranked or
answered: main.py hands rerank() and generate() req.query, and the answer cache keeps the question's own vector.
/v1/stream and /v1/passages do not call it.

On, the answer's stages say what happened: rewrite (rewritten | same | rejected | fallback), search_query (the text the
index was searched with) and rewrite_ms (the model call and the second embedding, inside retrieve_ms). Each call writes
one "query_rewrite" line: the outcome, tokens, cost and time, never the question. Its cost is on that line only - the
usage row's cost_usd and the month's budget counter do not count it.
"""
import json
import logging
import time

from config import settings
from generator import _client
from retriever import embed_query
from shared import query_rewrite

log = logging.getLogger("documind-api")


def search_query(question: str, qvec: list[float], stages: dict, tenant_id: str | None = None) -> tuple[str, list[float]]:
    """(the text retrieve() searches, its vector). Off: (question, qvec), with no call, no line and the stages untouched.
    On: the rewrite and its embedding when the guard kept it, else (question, qvec) - outcome fallback on any failure,
    the second embedding's included. Never raises."""
    if settings.query_rewrite != "on":
        return question, qvec
    t0 = time.perf_counter()
    got, q, vec = None, question, qvec
    try:
        got = query_rewrite.rewrite(_client, question, model=settings.query_rewrite_model)
        if got["outcome"] == "rewritten":
            q, vec = got["query"], embed_query(got["query"])
    except Exception as e:  # noqa: BLE001 - the question as asked is always a search
        got = {**(got or query_rewrite.result(question, settings.query_rewrite_model)),
               "query": question, "outcome": "fallback", "error": type(e).__name__}
        q, vec = question, qvec
    log.info(json.dumps(query_rewrite.row("query", tenant_id, got)))
    stages.update(rewrite=got["outcome"], search_query=q, rewrite_ms=int((time.perf_counter() - t0) * 1000))
    return q, vec
