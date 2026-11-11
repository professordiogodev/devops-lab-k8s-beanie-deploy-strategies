"""PROVIDED. Run inside the client pod:  python probe.py <seconds> <requests per second>
Calls http://menu:8001/healthz and counts the answers per version; failures are counted separately."""
import json, sys, time, urllib.request, collections
secs, rps = float(sys.argv[1]), float(sys.argv[2])
seen, fails, t_end = collections.Counter(), 0, time.time() + secs
while time.time() < t_end:
    try:
        v = json.load(urllib.request.urlopen("http://menu:8001/healthz", timeout=2))["version"]
        seen[v] += 1
    except Exception:
        fails += 1
    time.sleep(1 / rps)
print(json.dumps({"versions": dict(seen), "failures": fails}))
