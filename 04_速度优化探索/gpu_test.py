import urllib.request, json, time

print("Test 3B GPU...")
t0 = time.time()
d = json.dumps({"model": "qwen2.5:3b", "messages": [{"role": "user", "content": "OK"}], "stream": False}).encode()
r = urllib.request.urlopen(urllib.request.Request("http://127.0.0.1:11434/api/chat", data=d, headers={"Content-Type": "application/json"}), timeout=120)
elapsed = time.time() - t0
print(f"3B: {elapsed:.1f}s - {json.loads(r.read())['message']['content'][:100]}")

print("\nVRAM usage:")
r2 = urllib.request.urlopen("http://127.0.0.1:11434/api/ps", timeout=5)
ps = json.loads(r2.read())
for m in ps.get("models", []):
    vram = m.get("size_vram", 0)
    print(f"  {m['name']}: size_vram={vram/1e9:.1f}GB {'(GPU)' if vram > 0 else '(CPU)'}")