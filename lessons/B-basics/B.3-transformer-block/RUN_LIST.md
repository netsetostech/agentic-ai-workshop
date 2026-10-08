# Lesson B.3 run list

**None needed.** Every cell on the page is numpy or plain Python on the learner's laptop: no network, no account, no
Google Cloud project, and no `recorded()` output. `python pagekit/build.py B.3` runs each cell itself, and each expected
window is that run's stdout, so nothing on the page waits on the author's lane.

What the build proves on every run:

- each cell, run by the Basics interpreter (Python 3.12, numpy 2.5.3) exactly as the page shows it, prints its expected
  window, and the asserts in `build.py` pin every number the prose states;
- a guard wraps `numpy.round` during the build and refuses any printed number within 1e-5 of a rounding edge in its last
  digit, so a different processor, BLAS or numpy build cannot flip a printed digit (the guard changes no output: the build
  runs each cell without it too and compares);
- the explorer's JSON comes from the same code, and matches the weights tables steps 4 and 5 print;
- the kit tie's numbers come from the kit: the excerpts are verbatim (`check_lesson.py`), and the 22 chunks per embedding
  request come from running `indexer.py`'s own `batches()` on 2,000-character chunks.

Checked once by hand on 7 October 2026, not by the build: the eight cells, pasted through Git Bash exactly as the page
shows them, print their expected windows; and they print the same under numpy 2.4.6 (Python 3.12) and numpy 2.5.2
(Python 3.14).

The page states a few facts that are not computed. Their sources, read on 7 October 2026:

- Gemini 3 Pro's model card (storage.googleapis.com/deepmind-media/Model-Cards/Gemini-3-Pro-Model-Card.pdf): a "sparse
  mixture-of-experts (MoE)" transformer-based model, citing Vaswani et al. 2017; no layer count, width or head count.
- Vaswani et al. 2017, *Attention Is All You Need* (arXiv 1706.03762): LayerNorm(x + Sublayer(x)); d_model 512 and a
  feed-forward width of 2048; the variance d_k of a dot product; positional encodings added to the input embeddings.
- Radford et al. 2019 (GPT-2): layer normalization moved to the input of each sub-block, and one more after the final block.
- PyTorch's `torch.nn.LayerNorm`: `eps: float = 1e-5`, and the biased variance (divided by N), as the cells compute it.
- Touvron et al. 2023 (LLaMA, arXiv 2302.13971) and Gemma Team 2024 (arXiv 2403.08295): RMSNorm on each sub-layer's input.
