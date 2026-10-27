# Sahyadri Freight on DocuMind: the cost model

Dated 2026-11-18, at USD_INR = 85, with gemini-3.6-flash at $1.50 in and $7.50 out per million tokens. An answer
reads about 2,000 tokens and writes about 300: $0.00525, Rs 0.45. The figures are the canned fork's, not a lane's.

| Queries a month | Model | Retrieval and hosting | Total |
|---|---|---|---|
| 1k | Rs 446 ($5.25) | Rs 1,700 ($20.00) | Rs 2,146 ($25.25) |
| 10k | Rs 4,463 ($52.50) | Rs 2,550 ($30.00) | Rs 7,013 ($82.50) |
| 100k | Rs 44,625 ($525.00) | Rs 8,500 ($100.00) | Rs 53,125 ($625.00) |

## What breaks first at 10x

Not the bill: the per-minute request quota on the global endpoint, which the morning dispatch peak reaches first.
