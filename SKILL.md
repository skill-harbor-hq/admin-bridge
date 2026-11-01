---
name: "admin-bridge"
description: "Run a website's back office from Muse: moderation queue, approve/reject, publish, and action log through a secure token-authenticated JSON admin API. Use when the user wants to administer their site in chat."
---

# Admin Bridge

## Purpose
Let the agent operate any website's admin side conversationally. The site exposes a small JSON admin API guarded by a Bearer token (server-side only); the agent calls it with `bin/admin_call.py`, the user just talks: "show the queue", "approve the Trade Bot submission", "publish it", "what did we do this week?".

One skill, any site: the API contract is standardized (`references/api-contract.md`), the backend recipe adapts to any stack (`references/backend-recipe.md`).

## Tooling
`bin/admin_call.py` — generic admin API client.

```
ADMIN_API_TOKEN_FILE=/path/to/token python3 bin/admin_call.py --base https://example.com queue
ADMIN_API_TOKEN_FILE=/path/to/token python3 bin/admin_call.py --base https://example.com log
ADMIN_API_TOKEN_FILE=/path/to/token python3 bin/admin_call.py --base https://example.com moderate submission <id> approved
# actions: submission/suggestion → approved|rejected ; report → handled|ignored
ADMIN_API_TOKEN_FILE=/path/to/token python3 bin/admin_call.py --base https://example.com publish <submission_id> name=... slug=... tagline=... category=... is_free=true
ADMIN_API_TOKEN_FILE=/path/to/token python3 bin/admin_call.py --base https://example.com raw GET /api/admin/queue
```

Token from `ADMIN_API_TOKEN` env var or `ADMIN_API_TOKEN_FILE` (a `600` file). The script never prints it.

## Auth
Each site has its own token, generated once by the agent and installed as a **server-side secret** (env var / platform secret store — never in client code, never in chat, never in a journal). The agent keeps a session-local `600` copy and reads it via `ADMIN_API_TOKEN_FILE`.

- Generate: `openssl rand -hex 32`
- Rotate on suspicion: new token → update the server secret → redeploy/restart if the platform binds secrets at deploy time → replace the local copy.
- A `401`/`403` is a question about the request before it is about the token: check the `Authorization: Bearer` header was attached and the path is under `/api/admin/`.

## Operating Rules
1. Use this skill when the user wants to administer their website from chat.
2. Setup (once per site): implement the endpoints per `references/backend-recipe.md`, generate + install the token, verify with a read-only `queue` call.
3. Read-only first: always `queue`/`log` before any destructive action; confirm destructive actions (reject, delete) with the user unless already authorized.
4. Never expose the token: not in chat, not in journals or memory, not in client-side code, not in artifacts.
5. Never invent identifiers: copy submission/product IDs exactly from `queue` output.
6. After setup, record the site's base URL and token-file location in the journal (never the token value) so future sessions can resume; if the local copy is gone, rotate per Auth.
