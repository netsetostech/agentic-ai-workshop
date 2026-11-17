# Sahyadri Freight on DocuMind: the architecture

A canned capstone fork for commands/tests/test_capstone_check.py: a made-up logistics company's corpus on the kit's
lane, written to pass `make capstone-check`. Dated 2026-11-18.

## The request path

A dispatcher signs in to documind-ui through IAP and asks a question on the Chat page. documind-ui calls documind-api
with its own identity token; documind-api checks the sahyadri roster, retrieves from the kit's Vector Search index
filtered by tenant, reranks, and answers with gemini-3.6-flash on the global endpoint, citing the manual's clauses.

## The lane on top of the core

Chat: documind-chat answers follow-up questions, with the conversation kept by its checkpointer.

## Rejected options

- GKE Autopilot for the API: our duty cycle is about 4%, so Cloud Run's per-request billing costs less; above roughly
  74% we would move.
- A second vector database (Pinecone): it would hold tenant text outside asia-south1, which our customers' contracts
  forbid.
- Fine-tuning before prompting: the golden set showed no gap that the prompt and the reranker could not close, and a
  tuned model would need judging again after every corpus change.

## What would change our mind

A p95 above 3 s for a week at ten times today's traffic, or a duty cycle above 74%.
