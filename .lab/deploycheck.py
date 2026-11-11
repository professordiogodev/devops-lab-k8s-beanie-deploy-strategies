#!/usr/bin/env python3
import json, os, subprocess, sys, time
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
os.chdir(ROOT)
NS = "beanie-deploy"
passed = failed = 0
IMG = open(".image").read().strip()
PROBE = open("common/probe.py").read()


def check(desc, ok, hint=""):
    global passed, failed
    if ok:
        passed += 1; print("PASS  " + desc, flush=True)
    else:
        failed += 1; print("FAIL  " + desc + (("   -> " + hint) if hint else ""), flush=True)


def k(*a, timeout=180, inp=None):
    r = subprocess.run(("kubectl",) + a, capture_output=True, text=True, timeout=timeout, input=inp)
    return r.returncode, r.stdout, r.stderr


def kj(*a):
    rc, out, _ = k(*a, "-o", "json")
    try:
        return json.loads(out) if rc == 0 else None
    except Exception:
        return None


def wait_for(fn, secs, step=3):
    end = time.time() + secs
    while time.time() < end:
        try:
            if fn():
                return True
        except Exception:
            pass
        time.sleep(step)
    return False


def finish():
    print()
    print(("ALL CHECKS PASSED (%d/%d)" % (passed, passed)) if failed == 0 else ("%d check(s) failed, %d passed" % (failed, passed)))
    sys.exit(1 if failed else 0)


def probe_start(secs, rps):
    p = subprocess.Popen(["kubectl", "exec", "-i", "-n", NS, "deploy/client", "--", "python", "-", str(secs), str(rps)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    p.stdin.write(PROBE)      # feed the script NOW and close stdin: `python -` starts running at end-of-file
    p.stdin.close()
    return p, None


def probe_result(p_pair):
    p, _ = p_pair
    out, err = p.stdout.read(), p.stderr.read()
    p.wait(timeout=180)
    try:
        return json.loads(out.strip().split("\n")[-1])
    except Exception:
        return {"versions": {}, "failures": -1, "raw": (out + err)[-200:]}


def probe(secs, rps):
    pp = probe_start(secs, rps)
    return probe_result(pp)


def ready(name, n):
    return (kj("get", "deployment", name, "-n", NS) or {}).get("status", {}).get("readyReplicas", 0) >= n


def clean():
    k("delete", "deployment,service", "-n", NS, "-l", "app=menu", "--ignore-not-found", "--wait=true", timeout=120)
    for d in ("menu", "menu-blue", "menu-green", "menu-stable", "menu-canary"):
        k("delete", "deployment", d, "-n", NS, "--ignore-not-found", "--wait=true")
    k("delete", "service", "menu", "-n", NS, "--ignore-not-found")
    time.sleep(3)


print("kubectl context: " + k("config", "current-context")[1].strip())
check("the client pod is running in the namespace %s (run ./setup.sh)" % NS, wait_for(lambda: ready("client", 1), 90))
if not ready("client", 1):
    finish()
clean()

print("== Strategy 1: rolling update ==")
rc, out, err = k("apply", "-f", "rolling/menu.yaml")
check("rolling/menu.yaml applies", rc == 0, err[-200:])
if rc == 0:
    d = kj("get", "deployment", "menu", "-n", NS) or {}
    sp = d.get("spec", {})
    ru = sp.get("strategy", {}).get("rollingUpdate", {})
    c = sp.get("template", {}).get("spec", {}).get("containers", [{}])[0]
    env = {e["name"]: e.get("value") for e in c.get("env", [])}
    check("4 replicas, image from .image, APP_VERSION 1.0.0, a readiness probe on /readyz", sp.get("replicas") == 4 and c.get("image") == IMG and env.get("APP_VERSION") == "1.0.0" and (c.get("readinessProbe", {}).get("httpGet", {}) or {}).get("path") == "/readyz")
    check("strategy RollingUpdate with maxUnavailable 0 and maxSurge of at least 1", sp.get("strategy", {}).get("type") == "RollingUpdate" and str(ru.get("maxUnavailable")) in ("0", "0%") and str(ru.get("maxSurge")) not in ("0", "0%", "None"))
    check("all four pods become Ready", wait_for(lambda: ready("menu", 4), 150))
    pp = probe_start(50, 6)
    time.sleep(6)
    k("set", "env", "deployment/menu", "APP_VERSION=2.0.0", "-n", NS)
    k("rollout", "status", "deployment/menu", "-n", NS, "--timeout=120s", timeout=140)
    r = probe_result(pp)
    check("during the rollout NOT ONE request failed (%d failures)" % r["failures"], r["failures"] == 0, "a pod is removed from the Service's endpoints a moment AFTER it is told to stop: give it a preStop sleep so it keeps serving until every node knows. " + str(r))
    check("the client saw both versions while it ran: %s" % r["versions"], {"1.0.0", "2.0.0"} <= set(r["versions"]))
    k("rollout", "undo", "deployment/menu", "-n", NS)
    k("rollout", "status", "deployment/menu", "-n", NS, "--timeout=120s", timeout=140)
    r = probe(8, 6)
    check("rollout undo brought version 1.0.0 back, with no failures: %s" % r["versions"], set(r["versions"]) == {"1.0.0"} and r["failures"] == 0)
clean()

print("== Strategy 2: blue/green ==")
rc, out, err = k("apply", "-f", "bluegreen/")
check("bluegreen/ applies", rc == 0, err[-200:])
if rc == 0:
    check("both colours run at the same time (3 + 3 Ready)", wait_for(lambda: ready("menu-blue", 3) and ready("menu-green", 3), 150))
    svc = kj("get", "service", "menu", "-n", NS) or {}
    check("the Service selects app=menu AND track=blue", svc.get("spec", {}).get("selector") == {"app": "menu", "track": "blue"}, str(svc.get("spec", {}).get("selector")))
    r = probe(8, 6)
    check("all traffic goes to blue, version 1.0.0: %s" % r["versions"], set(r["versions"]) == {"1.0.0"} and r["failures"] == 0)
    pp = probe_start(16, 6)
    time.sleep(6)
    k("patch", "service", "menu", "-n", NS, "-p", '{"spec":{"selector":{"app":"menu","track":"green"}}}')
    r = probe_result(pp)
    check("switching the selector to green dropped no request (%d failures) and the client saw 1.0.0 then 2.0.0: %s" % (r["failures"], r["versions"]), r["failures"] == 0 and {"1.0.0", "2.0.0"} <= set(r["versions"]))
    time.sleep(2)
    r = probe(8, 6)
    check("after the switch only green answers: %s" % r["versions"], set(r["versions"]) == {"2.0.0"} and r["failures"] == 0)
    k("patch", "service", "menu", "-n", NS, "-p", '{"spec":{"selector":{"app":"menu","track":"blue"}}}')
    time.sleep(2)
    r = probe(8, 6)
    check("switching back (the rollback) is just as instant: %s" % r["versions"], set(r["versions"]) == {"1.0.0"} and r["failures"] == 0)
clean()

print("== Strategy 3: canary ==")
rc, out, err = k("apply", "-f", "canary/")
check("canary/ applies", rc == 0, err[-200:])
if rc == 0:
    check("9 stable pods and 1 canary pod are Ready", wait_for(lambda: ready("menu-stable", 9) and ready("menu-canary", 1), 200))
    svc = kj("get", "service", "menu", "-n", NS) or {}
    check("the Service selects app=menu only (it must not know about the version)", svc.get("spec", {}).get("selector") == {"app": "menu"}, str(svc.get("spec", {}).get("selector")))
    r = probe(45, 6)
    tot = sum(r["versions"].values()) or 1
    share = r["versions"].get("2.0.0", 0) / tot * 100
    check("about one request in ten reaches version 2.0.0: %.0f%% of %d requests (accepted: 3%% to 22%%), no failures" % (share, tot), 3 <= share <= 22 and r["failures"] == 0, str(r))
    k("scale", "deployment/menu-canary", "-n", NS, "--replicas=0")
    wait_for(lambda: not (kj("get", "pods", "-n", NS, "-l", "app=menu") or {}).get("items") or all(p["metadata"].get("deletionTimestamp") is None for p in (kj("get", "pods", "-n", NS, "-l", "app=menu") or {}).get("items", []) if "canary" in p["metadata"]["name"]) and not [p for p in (kj("get", "pods", "-n", NS, "-l", "app=menu") or {}).get("items", []) if "canary" in p["metadata"]["name"]], 90)
    time.sleep(4)
    r = probe(10, 6)
    check("aborting the canary (scale to 0) removes version 2.0.0 completely: %s" % r["versions"], "2.0.0" not in r["versions"] and r["failures"] == 0)
clean()
finish()
