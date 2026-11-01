# Admin Bridge — API contract (generic)

The standard contract any site implements so the `admin-bridge` skill can run its back office. Framework-agnostic; adapt field names to the site, keep the shapes.

## Authentication

- Header: `Authorization: Bearer <ADMIN_API_TOKEN>`
- Token compared in constant time against a server-side secret. No token → `403`.
- Existing session/cookie admin auth keeps working alongside; token actions are logged with `via='api_token'`.

## Endpoints

### `GET /api/admin/queue`
Returns everything awaiting moderation.
```json
{
  "pending":     [ {"id": 12, "kind": "submission", "title": "...", "created_at": "..."} ],
  "approved":    [ ... ],
  "reports":     [ {"id": 3, "kind": "report", "reason": "...", "target": "..."} ],
  "suggestions": [ {"id": 7, "kind": "suggestion", "text": "..."} ]
}
```
`200` on success. Empty arrays when there is nothing to do.

### `GET /api/admin/log`
Audit trail of admin actions, newest first.
```json
{ "entries": [ {"id": 1, "action": "approved", "kind": "submission",
                "target_id": 12, "via": "api_token", "created_at": "..."} ] }
```

### `POST /api/admin/moderate`
Body: `{ "kind": "submission|report|suggestion", "id": <id>, "action": "<valid action for the kind>" }`
Valid actions per kind: `submission` → `approved` / `rejected`; `suggestion` → `approved` / `rejected`; `report` → `handled` / `ignored`.
- `approved` on a submission → status becomes `approved` (visible in the queue's `approved` list, ready to publish).
- `rejected` → status becomes `rejected`.
- Response: `{ "ok": true }` or `{ "error": "..." }` with `4xx` (`bad_params` when the action is not valid for the kind).

### `POST /api/admin/publish`
Turns an approved submission into live content. Body carries the submission id plus the fields the site needs, e.g.:
```json
{ "submission_id": 12, "name": "Quest Board", "slug": "quest-board",
  "tagline": "...", "category": "productivity", "is_free": true }
```
Response: `{ "ok": true, "slug": "quest-board" }`.

### CORS
`OPTIONS /api/admin/*` → `204` with `Access-Control-Allow-Origin: *`,
`Access-Control-Allow-Headers: Authorization, Content-Type`,
`Access-Control-Allow-Methods: GET, POST, OPTIONS`.
Security rests on the Bearer token, not on the origin.

## Conventions
- All responses are JSON; errors use `{ "error": "..." }`.
- Every state-changing action writes one row to the audit log (who/what/when/how).
- IDs are opaque to the agent: copy them exactly from `queue` output, never invent them.
