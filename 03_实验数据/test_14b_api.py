import urllib.request, json, time
body = json.dumps({
    "model": "qwen2.5:14b",
    "messages": [{"role": "user", "content": "回复OK即可"}],
    "stream": False,
    "options": {"num_gpu": 15}
}).encode("utf-8")
print("Sending 14B request...", flush=True)
start = time.time()
try:
    req = urllib.request.Request("http://localhost:11434/api/chat", data=body, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=300) as r:
        data = json.loads(r.read())
        print(f"Response ({time.time()-start:.1f}s): {data['message']['content'][:100]}")
except Exception as e:
    print(f"Error ({time.time()-start:.1f}s): {e}")