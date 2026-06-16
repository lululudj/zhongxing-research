"""Debug V4-Flash CLI - write to file"""
import subprocess
import os
import sys
import time

CLI = r"E:\zhongxing2\llama-cpp-v4flash\build\bin\Release\llama-cli.exe"
MODEL = r"E:\models\v4-flash-download\deepseek-v4-flash-iq2xxs.gguf"
LOG = r"E:\zhongxing2\v4flash_debug.log"

cmd = [
    CLI,
    "-m", MODEL,
    "-p", "1+1=? answer in one word",
    "-n", "10",
    "-c", "1024",
    "--no-display-prompt",
    "--temp", "0",
    "-t", "4",
    "--log-disable",
]

start = time.time()
print(f"[{time.strftime('%H:%M:%S')}] Starting...", flush=True)

with open(LOG, 'w', encoding='utf-8', errors='replace') as logfile:
    proc = subprocess.Popen(
        cmd,
        stdout=logfile,
        stderr=subprocess.STDOUT,
        cwd=os.path.dirname(CLI),
        text=False,
    )
    proc.wait(timeout=900)

elapsed = time.time() - start
print(f"[{time.strftime('%H:%M:%S')}] Done in {elapsed:.0f}s, exit={proc.returncode}", flush=True)

# Read output
with open(LOG, 'r', encoding='utf-8', errors='replace') as f:
    content = f.read()
print(f"Output: {len(content)} bytes", flush=True)
print(f"--- LAST 2000 CHARS ---\n{content[-2000:]}", flush=True)
