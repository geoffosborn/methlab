"""Live API endpoint tests — run against localhost:8020."""

import json
import urllib.request
import sys

BASE = "http://localhost:8020"
PASS = 0
FAIL = 0


def test(name, method, path, body=None, headers=None, expect_status=200):
    global PASS, FAIL
    url = BASE + path
    h = headers or {}
    if body:
        h["Content-Type"] = "application/json"
        data = json.dumps(body).encode()
    else:
        data = None

    req = urllib.request.Request(url, data=data, headers=h, method=method)
    try:
        r = urllib.request.urlopen(req)
        status = r.status
        content = r.read().decode()
    except urllib.error.HTTPError as e:
        status = e.code
        content = e.read().decode()

    ok = status == expect_status
    if ok:
        PASS += 1
        print(f"  PASS  {name} ({status})")
    else:
        FAIL += 1
        print(f"  FAIL  {name} — expected {expect_status}, got {status}: {content[:200]}")
    return content if ok else None


# Health
test("Health check", "GET", "/health")

# Facilities
r = test("List facilities", "GET", "/facilities?limit=3")
if r:
    data = json.loads(r)
    assert data["total_count"] == 103, f"Expected 103, got {data['total_count']}"
    print(f"         -> {data['total_count']} total, returned {len(data['items'])} items")

test("Get facility by ID", "GET", "/facilities/1")
test("Get facility 404", "GET", "/facilities/9999", expect_status=404)
test("Facilities filter by state", "GET", "/facilities?state=QLD&limit=2")
test("Facilities filter by commodity", "GET", "/facilities?commodity=brown+coal&limit=5")

# TROPOMI
r = test("TROPOMI for facility", "GET", "/tropomi/facilities/1")
if r:
    data = json.loads(r)
    print(f"         -> {data.get('total_count', 'N/A')} observations")

test("TROPOMI rankings", "GET", "/tropomi/rankings")

# Sentinel-2
test("S2 detections recent", "GET", "/sentinel2/detections/recent")
test("S2 for facility", "GET", "/sentinel2/facilities/1")

# Alerts
test("Alerts list", "GET", "/alerts")
r = test("Alerts summary", "GET", "/alerts/summary")
if r:
    data = json.loads(r)
    print(f"         -> {data['total']} total, {data['unacknowledged']} unacked")

# Auth
# Try register — may already exist from previous run
r = test("Register user", "POST", "/auth/register",
         body={"email": "livetest2@methlab.io", "password": "pass123", "full_name": "Live Test"})
if r:
    token = json.loads(r)["access_token"]
    print(f"         -> token: {token[:20]}...")
else:
    # Already exists, login instead
    r_login = test("Login (fallback)", "POST", "/auth/login",
                   body={"email": "livetest@methlab.io", "password": "pass123"})
    if r_login:
        token = json.loads(r_login)["access_token"]
    else:
        token = None

if token:
    test("Auth /me", "GET", "/auth/me", headers={"Authorization": f"Bearer {token}"})
    test("Auth /facilities", "GET", "/auth/facilities", headers={"Authorization": f"Bearer {token}"})

r2 = test("Login", "POST", "/auth/login",
          body={"email": "livetest2@methlab.io", "password": "pass123"})
if r2:
    print(f"         -> login OK")

test("Login bad password", "POST", "/auth/login",
     body={"email": "livetest2@methlab.io", "password": "wrong"}, expect_status=401)

test("Auth /me no token", "GET", "/auth/me", expect_status=401)

# Reports (require query params)
test("Compliance report", "GET", "/reports/facilities/1/compliance?year=2025")
test("Export report (no data)", "GET", "/reports/facilities/1/export?start_date=2025-01-01&end_date=2025-12-31", expect_status=404)

# Summary
print(f"\n{'='*40}")
print(f"Results: {PASS} passed, {FAIL} failed out of {PASS+FAIL} tests")
sys.exit(1 if FAIL > 0 else 0)
