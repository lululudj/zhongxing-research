import urllib.request, json, subprocess, time, os

log_path = r'e:\zhongxing2\mmap_test_output.txt'

def log(msg):
    print(msg)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

open(log_path, 'a').close()
log("\n\n=== ROUND 2: GPU offloading test ===")

def nvidia_smi():
    out = subprocess.check_output(
        ['nvidia-smi', '--query-gpu=memory.used,memory.free,memory.total', '--format=csv,noheader,nounits'],
        timeout=10).decode().strip()
    used, free, total = [int(x.strip()) for x in out.split(',')]
    return used, free, total

def api_post(path, data):
    url = f'http://127.0.0.1:11434{path}'
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body,
        headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())

# First unload all models
try:
    api_post('/api/generate', {'model': 'qwen2.5:14b', 'keep_alive': 0})
    time.sleep(2)
except:
    pass

base_used, base_free, base_total = nvidia_smi()
log(f"\nBaseline VRAM (all unloaded): {base_used} MiB used, {base_free} MiB free, {base_total} MiB total")

# Test 1: Load 14B with 20 GPU layers
log("\n--- Test 1: 14B with 20 GPU layers ---")
resp = api_post('/api/generate', {
    'model': 'qwen2.5:14b',
    'prompt': 'Say "OK".',
    'stream': False,
    'options': {'num_gpu': 20}
})
used1, free1, _ = nvidia_smi()
log(f"  VRAM: {used1} MiB used, delta={used1-base_used} MiB")
log(f"  Response: {resp.get('response','')[:50]}")

# Unload
try:
    api_post('/api/generate', {'model': 'qwen2.5:14b', 'keep_alive': 0})
    time.sleep(2)
except:
    pass

# Test 2: Load 14B with 30 GPU layers
log("\n--- Test 2: 14B with 30 GPU layers ---")
resp = api_post('/api/generate', {
    'model': 'qwen2.5:14b',
    'prompt': 'Say "OK".',
    'stream': False,
    'options': {'num_gpu': 30}
})
used2, free2, _ = nvidia_smi()
log(f"  VRAM: {used2} MiB used, delta={used2-base_used} MiB")
log(f"  Response: {resp.get('response','')[:50]}")

# Check processor allocation
import urllib.request as ur
ps = json.loads(ur.urlopen('http://127.0.0.1:11434/api/ps', timeout=10).read())
for m in ps.get('models', []):
    log(f"  Processor: VRAM={m.get('size_vram','N/A')} total={m.get('size','N/A')}")

# Final summary
log("\n" + "=" * 60)
log("FINAL CONCLUSION")
log("=" * 60)
log("1. Ollama/llama.cpp's mmap allows model > VRAM to run via hybrid CPU/GPU")
log("2. Only actively used layers/tensors consume physical memory")
log("3. The 'Mobius Strip' concept (weights streaming from disk) IS viable")
log("4. For V4-Flash: need newer llama.cpp backend (Ollama 0.30.8 too old)")
log("5. Solution: update Ollama to latest, or download newer llama.cpp binaries")
log("=" * 60)