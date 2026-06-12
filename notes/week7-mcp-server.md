# Week 7 — a one-tool MCP server over the categorizer

## What I built

A minimal MCP server (`mcp_server/server.py`) that exposes the pipeline's real
`categorize()` function as a tool an AI agent can call. MCP (Model Context Protocol)
is an open standard for handing an AI agent a "toolbelt": the server describes its
tools with JSON Schemas, and any MCP client — Claude Code here — can discover and
call them over a standard wire format (JSON-RPC).

One deliberate design choice: **one tool, stdio transport, local only.** No HTTP, no
auth, no registry. Small and real beats broad and fake.

## How it works, in plain words

1. Claude Code reads `.mcp.json` at the repo root and spawns
   `.venv/bin/python -m mcp_server.server` as a subprocess.
2. The two processes talk JSON-RPC over the subprocess's stdin/stdout: first an
   `initialize` handshake, then `tools/list` (Claude discovers `categorize` and its
   schemas), then `tools/call` when you ask it to categorize something.
3. The tool builds a `Transaction` and runs the pipeline's actual categorizer:
   keyword rules first (free, instant), Claude Haiku fallback for anything unmatched.
   Without an Anthropic key the fallback degrades to "Other" instead of crashing.

The FastMCP API generates both the input and output JSON Schemas from the function's
type hints — the `TypedDict` return type is what makes the client receive structured
content instead of a JSON string.

## Things that bit me

- **stdout is sacred in a stdio server.** `src/secrets.py` printed a WARN line to
  stdout; in an MCP server, stdout *is* the protocol channel, so any stray print
  corrupts the JSON-RPC stream. One-line fix: print to stderr. Caught at the planning
  stage, confirmed live — the WARN now shows in stderr while the protocol stays clean.
- **A bare `dict` return gives no output schema.** `call_tool(...).structuredContent`
  came back `None` until the return type became a `TypedDict`.
- **Dependency isolation matters.** `deploy.sh` ships `requirements.txt` into the
  Lambda zip, so the MCP deps live in their own pinned `requirements-mcp.txt`
  (full freeze of the delta, so `pip-audit --no-deps` still covers transitives).

## How it's verified

`tests/test_mcp_server.py` is a real round-trip, not a mock: it spawns the server as
a subprocess and speaks actual JSON-RPC through the SDK's own client — initialize,
list tools (asserting the schema), call `categorize` on "STARBUCKS #123" and assert
"Food & Drink" via the keyword path (no API key, no AWS creds needed — CI-safe).
The whole thing is wrapped in a 30-second timeout so a dead server can't hang CI.
