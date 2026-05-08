# Git workflow rules

## Branch naming
`week<N>/<short-description>` — always off main, always pushed to remote.

Examples:
- `week2/dynamodb`
- `week3/lambda-schedule`
- `week4/llm-categorization`
- `fix/<what-broke>` for hotfixes

## Commits on a branch
Format: `<type>: <description>`

Types: `feat` / `fix` / `chore` / `docs`

Examples:
- `feat: write transactions to DynamoDB on ingest`
- `fix: handle empty transaction list from Plaid`
- `chore: update requirements.txt`
- `docs: add DynamoDB schema to README`

Keep commits small and focused — one logical change per commit.

## PR rules
- Title: `Week N: <what this week delivers>`
- Open PR as soon as branch is pushed (even if work in progress)
- Squash merge into main — keeps main history clean (one commit per week)
- Delete branch after merge

## What never happens
- No direct push to main (branch protection blocks it)
- No `git push --force` on shared branches
- No batch commits that mix unrelated changes
