#!/usr/bin/env python3
"""gmi_queue: tiny unofficial command-line client for the GMI Cloud request-queue API (video/image/audio models).
Not affiliated with GMI Cloud. Uses only the Python standard library.

  gmi_queue.py models [filter]                       list model ids
  gmi_queue.py info <model>                          price info + model description
  gmi_queue.py submit <model> <payload.json> [--yes] [--out file]
        prints the estimated cost and REFUSES to spend unless --yes is given
  gmi_queue.py poll <request_id> [--out file]        wait for a request and download the result

API key: env GMI_API_KEY, else ~/.config/gmi/key, else ./.secrets/gmi.key (never printed).
Payload URLs (images, audio) must be public HTTP(S) URLs."""
import json, os, sys, time, urllib.request, urllib.error
BASE = os.environ.get("GMI_QUEUE_BASE", "https://console.gmicloud.ai/api/v1/ie/requestqueue/apikey")

def load_key():
    if os.environ.get("GMI_API_KEY"): return os.environ["GMI_API_KEY"].strip()
    for p in (os.path.expanduser("~/.config/gmi/key"), os.path.join(os.getcwd(), ".secrets", "gmi.key")):
        if os.path.exists(p): return open(p).read().strip()
    sys.exit("no API key: set GMI_API_KEY or put it in ~/.config/gmi/key")

def call(method, path, body=None):
    req = urllib.request.Request(BASE + path, method=method, data=None if body is None else json.dumps(body).encode(),
        headers={"Authorization": "Bearer " + load_key(), "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r: return json.load(r)
    except urllib.error.HTTPError as e: sys.exit(f"HTTP {e.code}: {e.read().decode()[:400]}")

# Approximate USD per second for the Wan 3.0 tiers (the list price field only shows the top tier). Check the live price before big runs.
WAN_RATES = {"480p": 0.05, "720p": 0.10, "1080p": 0.20}
def est_cost(model, payload):
    info = call("GET", "/models/" + model); p = info.get("price_info", {})
    dur = payload.get("duration", 5); price = p.get("price", 0) / 1e6; ch = p.get("price_chart") or {}; res = str(payload.get("resolution", "")).lower()
    if ch.get("rates") and res in ch["rates"]: price = ch["rates"][res] / 1e6
    if model.startswith("wan3.0"): price = WAN_RATES.get(res, 0.20)
    return price * (dur if p.get("unit") == "second" else 1), p

def result_url(r):
    """first downloadable url of a finished request: video_url, or media_urls[0].url (Wan and others)"""
    o = r.get("outcome") or r
    if o.get("video_url"): return o["video_url"]
    for m in o.get("media_urls") or []:
        if isinstance(m, dict) and m.get("url"): return m["url"]
        if isinstance(m, str): return m
    return None

def download(url, out): urllib.request.urlretrieve(url, out); print("saved", out)
def poll(rid, out=None, every=8):
    while True:
        r = call("GET", "/requests/" + rid); st = r.get("status"); print(st, flush=True)
        if st in ("success", "failed", "cancelled"):
            print(json.dumps(r.get("outcome", r), ensure_ascii=False)[:800]); u = result_url(r)
            if out and u: download(u, out)
            elif out and st == "success": print("no downloadable url found in the result")
            return r
        time.sleep(every)

def main(a):
    if not a or a[0] in ("-h", "--help"): sys.exit(__doc__)
    if a[0] == "models":
        ids = call("GET", "/models")["model_ids"]; f = a[1].lower() if len(a) > 1 else ""
        print("\n".join(i for i in sorted(ids) if f in i.lower()))
    elif a[0] == "info":
        d = call("GET", "/models/" + a[1]); print(json.dumps(d.get("price_info")), "\n", d.get("detailed_description", "")[:3000])
    elif a[0] == "submit":
        model, pf = a[1], a[2]; payload = json.load(open(pf)); out = a[a.index("--out") + 1] if "--out" in a else None
        cost, _ = est_cost(model, payload); print(f"estimated cost: ${cost:.2f}")
        if "--yes" not in a: sys.exit("not submitted (add --yes to spend)")
        r = call("POST", "/requests", {"model": model, "payload": payload}); rid = r.get("request_id"); print("request_id", rid); poll(rid, out)
    elif a[0] == "poll": poll(a[1], a[a.index("--out") + 1] if "--out" in a else None)
    else: sys.exit(__doc__)
if __name__ == "__main__": main(sys.argv[1:])
