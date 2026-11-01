# Admin Bridge

Run your website's back office from chat. Free, offered by the founder of Skill Harbor.

Your Muse shows the moderation queue, approves or rejects submissions, publishes new listings, and keeps an action log, all through a secure token-protected API you add to your site in an afternoon.

## Files

- `SKILL.md` — the skill definition
- `bin/admin_call.py` — generic admin API client (queue, log, moderate, publish, raw)
- `references/api-contract.md` — the standard admin API contract: 4 endpoints, Bearer auth
- `references/backend-recipe.md` — backend setup recipe and security checklist

## Install

Copy the install prompt from the Skill Harbor listing for Admin Bridge and paste it into your Muse chat. Your Muse fetches this repository, installs the skill, and walks you through setup.

## Setup, in short

1. Add the 4 admin API endpoints to your site (queue, log, moderate, publish), following `references/backend-recipe.md`.
2. Generate a secure admin token and store it as a server secret. Never put it in chat, in client code, or in a journal.
3. Verify with a read-only queue check.

## Security

Each site has its own token. A `401`/`403` is a question about the request before it is about the token: check the `Authorization: Bearer` header and that the path is under `/api/admin/`. Rotate the token on suspicion: new token, update the server secret, redeploy if needed.
