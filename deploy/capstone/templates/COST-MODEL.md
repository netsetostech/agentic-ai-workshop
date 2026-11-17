# {{YOUR COMPANY}} on DocuMind: the cost model

<!--
The capstone's component 6 (lesson 11.8). Copy this file to your fork's root as COST-MODEL.md, replace every
placeholder in double curly braces, braces included, and delete these comments.

make capstone-check reads: the three volumes, 1k, 10k and 100k queries a month; three amounts or more in rupees (Rs,
INR or the rupee sign, then a figure) and three or more in dollars ($ or USD, then a figure), a pair for each volume;
a date, because prices move; and the rate, USD_INR = 85, on one line. The defence reads the rest, on dimension 3: what
one answer costs, split by the model, retrieval and hosting, and what breaks first at ten times the traffic, which is
a named limit and not the bill multiplied by ten. The kit's prices are in shared/prices.py, and lessons 8.3, 11.5 and
11.6 read your lane's. commands/tests/capstone_fork/COST-MODEL.md is one filled in, for a made-up company.
-->

Dated {{YYYY-MM-DD}}, at USD_INR = 85, with {{MODEL}} at USD {{PRICE}} in and USD {{PRICE}} out per million tokens.
An answer reads about {{TOKENS}} tokens and writes about {{TOKENS}}: USD {{COST}}, Rs {{COST}}.

| Queries a month | Model | Retrieval and hosting | Total |
|---|---|---|---|
| 1k | Rs {{AMOUNT}} (USD {{AMOUNT}}) | Rs {{AMOUNT}} (USD {{AMOUNT}}) | Rs {{AMOUNT}} (USD {{AMOUNT}}) |
| 10k | Rs {{AMOUNT}} (USD {{AMOUNT}}) | Rs {{AMOUNT}} (USD {{AMOUNT}}) | Rs {{AMOUNT}} (USD {{AMOUNT}}) |
| 100k | Rs {{AMOUNT}} (USD {{AMOUNT}}) | Rs {{AMOUNT}} (USD {{AMOUNT}}) | Rs {{AMOUNT}} (USD {{AMOUNT}}) |

## What breaks first at 10x

{{The first limit ten times today's traffic reaches, by name and number, and what you would do about it.}}
