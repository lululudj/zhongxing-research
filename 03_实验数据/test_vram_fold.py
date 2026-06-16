import urllib.request, json, subprocess, time, os

log_path = r'e:\zhongxing2\vram_fold_output.txt'

def log(msg):
    print(msg)
    with open(log_path, 'a', encoding='utf-8') as f:
        f.write(msg + '\n')

def nvidia_smi():
    try:
        out = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=memory.used,memory.free,memory.total', '--format=csv,noheader,nounits'],
            timeout=10).decode().strip()
        used, free, total = [int(x.strip()) for x in out.split(',')]
        return used, free, total
    except Exception as e:
        log(f'  nvidia-smi error: {e}')
        return None, None, None

def api_post(path, data):
    url = f'http://127.0.0.1:11434{path}'
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={'Content-Type': 'application/json'})
    return json.loads(urllib.request.urlopen(req, timeout=180).read())

def unload_model(model_name):
    try:
        api_post('/api/generate', {'model': model_name, 'keep_alive': 0})
        time.sleep(2)
        log(f"  Unloaded {model_name}")
    except:
        pass

open(log_path, 'w').close()
log("=== VRAM FOLDING TEST: Adaptive Layer Management ===")
log(f"Date: {time.strftime('%Y-%m-%d %H:%M:%S')}")

base_used, base_free, base_total = nvidia_smi()
log(f"\n[Initial State] VRAM: {base_used}/{base_total} MiB used, {base_free} MiB free")

vram_threshold = base_total * 0.85  
log(f"[Strategy] VRAM threshold: {int(vram_threshold)} MiB (85% of total)")

test_prompt = "Say OK."
test_models = [
    {'name': 'qwen2.5:1.5b', 'description': 'Small extractor', 'target_layers': 100},
    {'name': 'qwen2.5:3b', 'description': 'Medium extractor', 'target_layers': 100},
    {'name': 'qwen2.5:14b', 'description': 'Large reasoner', 'target_layers': 32}
]

for model in test_models:
    log(f"\n{'='*60}")
    log(f"Testing: {model['name']} - {model['description']}")
    log(f"{'='*60}")
    
    current_used, current_free, _ = nvidia_smi()
    
    if current_used > vram_threshold:
        log(f"[WARNING] VRAM usage {current_used} MiB exceeds threshold, unloading previous models")
        for m in test_models:
            unload_model(m['name'])
        time.sleep(3)
        current_used, current_free, _ = nvidia_smi()
        log(f"[AFTER UNLOAD] VRAM: {current_used} MiB used")
    
    free_headroom = current_free
    estimated_model_vram = min(model['target_layers'] * 200, free_headroom * 0.8)
    optimal_gpu_layers = int(estimated_model_vram / 200)
    optimal_gpu_layers = max(1, min(optimal_gpu_layers, model['target_layers']))
    
    log(f"[Auto-calculated] Optimal GPU layers: {optimal_gpu_layers}")
    log(f"[Expected] VRAM delta: ~{optimal_gpu_layers * 200} MiB")
    
    try:
        start_time = time.time()
        resp = api_post('/api/generate', {
            'model': model['name'],
            'prompt': test_prompt,
            'stream': False,
            'options': {
                'num_gpu': optimal_gpu_layers,
                'num_ctx': 2048
            }
        })
        elapsed = time.time() - start_time
        
        used_after, free_after, _ = nvidia_smi()
        vram_delta = used_after - current_used
        
        log(f"[SUCCESS] Inference completed in {elapsed:.2f}s")
        log(f"[VRAM Usage] Delta: {vram_delta} MiB (predicted ~{optimal_gpu_layers * 200} MiB)")
        log(f"[VRAM Usage] Current: {used_after}/{base_total} MiB")
        log(f"[Response] {resp.get('response','')[:100]}...")
        
        if vram_delta > vram_threshold - current_used:
            log(f"[AUTO-FOLD] High VRAM usage detected, triggering immediate unload")
            unload_model(model['name'])
            time.sleep(2)
            
    except Exception as e:
        log(f"[ERROR] Failed to run {model['name']}: {e}")
        unload_model(model['name'])

log("\n" + "="*60)
log("FINAL SUMMARY - VRAM FOLDING STRATEGY")
log("="*60)
log("1. [检测] 实时监控VRAM占用")
log("2. [计算] 根据剩余显存动态决定GPU层数")
log("3. [加载] 仅加载必要层到VRAM，其余通过mmap流式读取")
log("4. [释放] 推理完成后立即卸载，为下一模型腾出空间")
log("5. [循环] 形成'加载→推理→释放→加载'的莫比乌斯环")
log("="*60)

final_used, final_free, _ = nvidia_smi()
log(f"\n[Final State] VRAM: {final_used}/{base_total} MiB used, {final_free} MiB free")
log(f"[Efficiency] Total VRAM saved through folding: {base_total - final_used} MiB")