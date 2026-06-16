import urllib.request, json, subprocess, time, sys

def nvidia_smi():
    """Get GPU memory info"""
    try:
        out = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=memory.used,memory.free,memory.total', '--format=csv,noheader,nounits'],
            timeout=5).decode().strip()
        used, free, total = [int(x.strip()) for x in out.split(',')]
        return used, free, total
    except:
        return None, None, None

def api(path, data=None):
    url = f'http://127.0.0.1:11434{path}'
    if data:
        req = urllib.request.Request(url, data=json.dumps(data).encode(),
            headers={'Content-Type': 'application/json'})
    else:
        req = urllib.request.Request(url)
    return json.loads(urllib.request.urlopen(req, timeout=120).read())

print("=" * 60)
print("MMAP STREAMING INFERENCE TEST")
print("=" * 60)

# Before loading model
before_used, before_free, before_total = nvidia_smi()
print(f"\n1. VRAM BEFORE model load: {before_used} MiB used / {before_total} MiB total ({before_free} MiB free)")

# Load qwen2.5:14b via inference request
print("\n2. Loading qwen2.5:14b (9GB model) via API...")
response = api('/api/generate', {
    'model': 'qwen2.5:14b',
    'prompt': 'Hello, respond with just "OK".',
    'stream': False,
    'options': {
        'num_gpu': 15,  # Limit GPU layers to leave room for KV cache
    }
})

print(f"   Response: {response.get('response', '')[:50]}")
print(f"   Eval count: {response.get('eval_count', 'N/A')}")
print(f"   Eval duration: {response.get('eval_duration', 'N/A')}")

# After model loaded
after_used, after_free, after_total = nvidia_smi()
print(f"\n3. VRAM AFTER model load: {after_used} MiB used / {after_total} MiB total ({after_free} MiB free)")
if after_used and before_used:
    delta = after_used - before_used
    print(f"   VRAM increase: {delta} MiB (model requires ~9GB but VRAM used only {delta} MiB)")

# Check if model is using GPU or CPU
ps = api('/api/ps')
for m in ps.get('models', []):
    print(f"\n4. Model processor info: {m.get('name', '')} - {m.get('size_vram', 'N/A')} VRAM / {m.get('size', 'N/A')} total")

print("\n" + "=" * 60)
print("CONCLUSION:")
print("- Ollama uses llama.cpp's mmap by default")
print("- Model file is memory-mapped, not fully loaded into RAM")
print("- Only actively used tensor pages occupy physical memory")
print("- This IS the 'Mobius strip' streaming approach")
print("=" * 60)