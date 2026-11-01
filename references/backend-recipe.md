# Admin Bridge — backend recipe

How to add the admin API to any backend. Checklist first, then notes per stack.

## Checklist
1. **Token middleware**: read `Authorization: Bearer <token>`, compare (constant-time) against the server secret. Reject with `403` JSON. Keep any existing session auth working in parallel.
2. **JSON endpoints**: implement the four routes from `api-contract.md` (`queue`, `log`, `moderate`, `publish`). Accept `application/json`; keep any existing form/redirect behavior for the browser panel untouched.
3. **Audit log**: every token action writes one row (`action`, `kind`, `target_id`, `via='api_token'`, timestamp).
4. **CORS**: answer `OPTIONS /api/admin/*` with `204` and permissive headers; the token is the security boundary.
5. **Secret install**: store the token as a server secret / env var (Cloudflare Pages secret, Fly secret, systemd env, etc.). Never commit it, never ship it to the client.
6. **Verify**: `GET /api/admin/queue` with the token → `200`; without → `403`; wrong token → `403`; preflight → `204`.

## Token setup (agent-run)
```bash
openssl rand -hex 32            # generate
# install as a server secret (platform-specific), then
install -m 600 <(echo -n "$TOKEN") ~/.config/admin-bridge/<site>.token
```
Agent keeps the `600` copy and uses `ADMIN_API_TOKEN_FILE`. Rotation = new token → update secret → redeploy/restart if the platform binds secrets at deploy time → replace the local copy.

## Stack notes
- **Cloudflare Pages/Workers**: put the secret with `wrangler pages secret put` (or the API); read it from the environment binding. Reference implementation: `~/workspace/skill-harbor-site/worker/api.js` (Bearer check + JSON admin routes + CORS, deployed on theskillharbor.com).
- **Express (Node)**: middleware reading `req.headers.authorization`; routes returning `res.json(...)`; `cors({ origin: '*' })` scoped to `/api/admin/*`.
- **Flask/Django**: a `before_request` / middleware check on the path prefix; `JsonResponse` views; log via the app's audit model.
- **Static + serverless functions** (Vercel/Netlify): one function per route or a catch-all `api/admin/[[...route]]`; secret from the dashboard env vars.

## What NOT to do
- Don't accept the token as a query param (it leaks into logs).
- Don't return the token, or whether a guess was "close", in error messages.
- Don't let the browser panel's session cookie become the API auth; keep the two mechanisms separate and log which one was used.

## Client User-Agent note
If the site sits behind Cloudflare, the default `Python-urllib/...` User-Agent can be blocked at the edge (error 1010) before the request reaches the API. `bin/admin_call.py` already sets its own UA (`AdminBridge/1.0 ...`); any custom client must do the same.
