#!/usr/bin/env python3
"""Generic admin API client for the Admin Bridge pattern.

Usage:
    admin_call.py --base https://example.com queue
    admin_call.py --base https://example.com log
    admin_call.py --base https://example.com moderate <kind> <id> <action>
      (submission/suggestion: approved|rejected; report: handled|ignored)
    admin_call.py --base https://example.com publish <submission_id> [k=v ...]
    admin_call.py --base https://example.com raw <METHOD> <PATH> [JSON_BODY]

Auth: ADMIN_API_TOKEN env var, or ADMIN_API_TOKEN_FILE pointing to a
600 file containing the token. The token is never printed.
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.request


def get_token():
    t = os.environ.get("ADMIN_API_TOKEN")
    if t and t.strip():
        return t.strip()
    p = os.environ.get("ADMIN_API_TOKEN_FILE")
    if p:
        with open(p) as f:
            return f.read().strip()
    sys.exit("error: set ADMIN_API_TOKEN or ADMIN_API_TOKEN_FILE")


def call(base, method, path, body=None):
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        base.rstrip("/") + path, data=data, method=method.upper())
    req.add_header("Authorization", "Bearer " + get_token())
    # Some WAFs (e.g. Cloudflare Browser Integrity Check) block the
    # default "Python-urllib/..." UA; identify the client honestly.
    req.add_header("User-Agent", "AdminBridge/1.0 (Muse agent; admin API client)")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, json.loads(r.read().decode() or "null")
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode()[:500]
        except Exception:
            detail = ""
        return e.code, {"http_error": e.code, "detail": detail}
    except Exception as e:
        return 0, {"transport_error": "%s: %s" % (type(e).__name__, e)}


def main():
    ap = argparse.ArgumentParser(description="Admin Bridge generic client")
    ap.add_argument("--base", required=True, help="Site base URL")
    ap.add_argument("action",
                    choices=["queue", "log", "moderate", "publish", "raw"])
    ap.add_argument("args", nargs="*")
    a = ap.parse_args()

    if a.action == "queue":
        status, body = call(a.base, "GET", "/api/admin/queue")
    elif a.action == "log":
        status, body = call(a.base, "GET", "/api/admin/log")
    elif a.action == "moderate":
        if len(a.args) != 3:
            sys.exit("usage: moderate <kind> <id> <approve|reject>")
        kind, item_id, action = a.args
        status, body = call(a.base, "POST", "/api/admin/moderate",
                            {"kind": kind, "id": item_id, "action": action})
    elif a.action == "publish":
        if not a.args:
            sys.exit("usage: publish <submission_id> [k=v ...]")
        body = {"submission_id": a.args[0]}
        for kv in a.args[1:]:
            if "=" not in kv:
                sys.exit("publish args must be k=v, got: %r" % kv)
            k, v = kv.split("=", 1)
            body[k] = v
        status, body = call(a.base, "POST", "/api/admin/publish", body)
    elif a.action == "raw":
        if len(a.args) < 2:
            sys.exit("usage: raw <METHOD> <PATH> [JSON_BODY]")
        method, path = a.args[0], a.args[1]
        body = json.loads(a.args[2]) if len(a.args) > 2 else None
        status, body = call(a.base, method, path, body)

    print(status)
    print(json.dumps(body, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
