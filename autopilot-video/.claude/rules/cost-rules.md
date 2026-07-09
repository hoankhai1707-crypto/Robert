# Cost Rules

## Daily Cost Limit

**DAILY_COST_LIMIT_USD = 5.00**

(Adjust here and in `.env` — both must match. Scripts read `DAILY_COST_LIMIT_USD` from
the environment and fall back to 5.00.)

Before any Claude API call, a script must read today's `./logs/costs_YYYY-MM-DD.json`
and exit(2) without calling if `total_usd >= DAILY_COST_LIMIT_USD`.

## Model Pricing (per 1K tokens, USD)

| Model | Input /1K | Output /1K | Input /1M | Output /1M |
|---|---|---|---|---|
| `claude-fable-5`   | $0.0100 | $0.0500 | $10.00 | $50.00 |
| `claude-sonnet-4-6`| $0.0030 | $0.0150 | $3.00  | $15.00 |
| `claude-haiku-4-5` | $0.0010 | $0.0050 | $1.00  | $5.00  |

Cost formula (identical for every model):

```
input_cost  = (usage.input_tokens  / 1000) * INPUT_PRICE_PER_1K
output_cost = (usage.output_tokens / 1000) * OUTPUT_PRICE_PER_1K
total       = input_cost + output_cost
```

## Cost Log Format — `./logs/costs_YYYY-MM-DD.json`

```json
{
  "date": "YYYY-MM-DD",
  "total_usd": 0.0,
  "entries": [
    {
      "ts": "ISO-8601",
      "script": "niche_selector",
      "model": "claude-fable-5",
      "input_tokens": 0,
      "output_tokens": 0,
      "cost_usd": 0.0
    }
  ]
}
```

The log is updated atomically (write temp file, rename) immediately after each API call
returns. `total_usd` is the running sum of `entries[].cost_usd`.

## Budget Allocation Guidance

- Fable 5: max 1 call per pipeline run (niche selection only).
- Sonnet 4.6: max 3 calls per run (one per script), max_tokens 1500 each.
- Haiku 4.5: unrestricted within the daily limit (utility tasks).
- Non-Claude costs (Pexels, Graph API) are free-tier and not tracked in the cost log.
