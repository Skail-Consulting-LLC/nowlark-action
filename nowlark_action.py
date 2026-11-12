"""The Nowlark GitHub Action: send, or ask and wait for the answer. Python 3 standard library only."""
import json
import os
import sys
import time
import urllib.error
import urllib.request

NAMED = ("approve_deny", "yes_no", "approve_deny_later", "yes_no_later")
env = os.environ.get
base = (env("NL_BASE") or "https://nowlark.com").rstrip("/")


def api(method, path, body=None):
    req = urllib.request.Request(base + path, method=method, data=json.dumps(body).encode() if body else None,
                                 headers={"X-Nowlark-Key": env("NOWLARK_API_KEY", ""), "Content-Type": "application/json",
                                          "User-Agent": "nowlark-github-action/1"})
    try:
        with urllib.request.urlopen(req, timeout=20) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        fail("Nowlark refused it (HTTP %d): %s" % (e.code, e.read().decode()[:300]))
    except (urllib.error.URLError, OSError) as e:
        return None if method == "GET" else fail("Could not reach %s: %s" % (base, e))


def fail(msg):
    print("::error title=Nowlark::" + msg)
    sys.exit(1)


def output(name, value):
    with open(env("GITHUB_OUTPUT"), "a") as f:
        f.write("%s<<NOWLARK_EOF\n%s\nNOWLARK_EOF\n" % (name, value))


if not env("NOWLARK_API_KEY"):
    fail("api-key is empty. Pass it from a secret: api-key: ${{ secrets.NOWLARK_API_KEY }}")
try:
    priority = int(env("NL_PRIORITY") or 0)
    wait = int(env("NL_WAIT") or 900)
except ValueError:
    fail("priority and wait are whole numbers")
payload = {"source": env("NL_SOURCE") or "GitHub", "title": env("NL_TITLE"), "priority": priority, "url": env("NL_URL")}
if env("NL_BODY"):
    payload["body"] = env("NL_BODY")
ask = (env("NL_ASK") or "").strip()
if ask:
    payload["replies"] = ask if ask in NAMED else [p.strip() for p in ask.split(",") if p.strip()]
    # The question closes on the phone when this step stops waiting, so a late tap can never approve a dead job.
    payload["reply_within"] = max(10, min(wait, 604800))
sent = api("POST", "/v1/notify", payload)
nid = sent.get("id")
output("id", nid or "")
if not ask:
    print("Sent %s." % nid)
    sys.exit(0)

print("Asked: %s (id %s). Waiting up to %ds for the answer." % (payload["title"], nid, wait))
end = time.time() + wait
while time.time() < end:
    r = api("GET", "/v1/receipts/%s" % nid) or {}
    state = r.get("reply_state")
    if state == "answered":
        answer = r.get("reply") or ""
        output("answer", answer)
        who = (" by " + r["replied_by"]) if r.get("replied_by") else ""
        print("Answered%s: %s" % (who, answer))
        allowed = [a.strip().lower() for a in (env("NL_PASS_ON") or "").split(",") if a.strip()]
        if allowed and answer.lower() not in allowed:
            fail("The answer was %s, not %s." % (answer, env("NL_PASS_ON")))
        sys.exit(0)
    if state == "expired":
        fail("Nobody answered before the question closed.")
    time.sleep(10)
fail("No answer within %ds." % wait)
