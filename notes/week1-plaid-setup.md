# Week 1 — Plaid Setup Notes

## Key concepts

**Plaid amount convention** — opposite of your bank statement:
- Positive amount = money OUT (debit/expense)
- Negative amount = money IN (deposit/credit)
- When you see `amount: 11.74` that's $11.74 spent.

**Why Plaid instead of CSV?**
- BofA CSV export = manual download every time, messy raw descriptions
- Plaid = one-time OAuth link, then `transactions_get()` on demand, clean merchant names
- Plaid cleans "MOBILE PURCHASE 0325 MCDONALD'S F10061 MELBOURNE FL" → `name: "McDonald's"`

**Plaid environments**
- `sandbox` — fake data, no real bank connection, free
- `development` — real bank data, up to 100 Items free, needs BofA OAuth
- `production` — paid, for real apps

**Sandbox public token trick**
- Normally Plaid Link requires a browser UI (OAuth flow)
- In sandbox: `sandbox_public_token_create()` bypasses this — creates a token directly
- This is why our CLI script works without a browser in sandbox mode

**Access token flow**
1. `sandbox_public_token_create()` → `public_token` (one-time use, short-lived)
2. `item_public_token_exchange()` → `access_token` (long-lived, store this for Week 2)

## Gotchas learned

**`PRODUCT_NOT_READY` in sandbox** — after `sandbox_public_token_create`, transactions aren't generated instantly. Fix: call `transactions_refresh` first, then retry with a 5s sleep. Already handled in `ingest.py`.

**`plaid.Environment.Development` doesn't exist** in current SDK — only `Sandbox` and `Production`. When you're ready to link real BofA account, flip `PLAID_ENV=production` in `.env` (Plaid's "development" is just a legacy label; sandbox → production is the real path for personal use).

## Week 2 prep
- In Week 2 we store the `access_token` so we don't re-create the sandbox item each run
- DynamoDB table schema: `transaction_id` (partition key, String), all other fields as attributes
- Plaid `category` field is a list like `["Food and Drink", "Restaurants", "Fast Food"]`
  — Week 2 rule-based categorizer maps first element → our own category labels
