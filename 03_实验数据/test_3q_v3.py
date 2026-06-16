"""3题测试 - 修复版：single-turn + UTF-8编码"""
import subprocess, time, os

CLI = r"E:\zhongxing2\llama-cpp-v4flash\build\bin\Release\llama-cli.exe"
MODEL = r"E:\models\v4-flash-download\deepseek-v4-flash-iq2xxs.gguf"
RESULT = r"E:\zhongxing2\test_3q_final.txt"

QUESTIONS = [
    "1+1等于几？请直接回答数字。",
    "中国的首都是哪里？请用一个词回答。",
    "水的化学式是什么？请直接回答。",
]

with open(RESULT, "w", encoding="utf-8") as f:
    f.write("众星3题测试 - V4-Flash IQ2_XXS\n")
    f.write(f"时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")

for i, q in enumerate(QUESTIONS, 1):
    outfile = rf"E:\zhongxing2\q{i}_output.txt"
    if os.path.exists(outfile):
        os.remove(outfile)
    
    print(f"第{i}题开始: {q}")
    start = time.time()
    
    # 关键修复：--single-turn 让llama-cli生成完自动退出
    # 用 echo 管道输入确保进程结束
    cmd = f'echo off | {CLI} -m "{MODEL}" -p "{q}" -n 30 -c 1024 -t 4 --no-display-prompt --log-disable --temp 0.7 --single-turn > "{outfile}" 2>&1'
    proc = subprocess.Popen(cmd, shell=True, cwd=os.path.dirname(CLI))
    proc.wait(timeout=900)
    elapsed = time.time() - start
    
    # 读取输出（UTF-8）
    try:
        with open(outfile, "r", encoding="utf-8", errors="replace") as f:
            output = f.read()
    except:
        try:
            with open(outfile, "r", encoding="gbk", errors="replace") as f:
                output = f.read()
        except:
            output = "(无法读取输出)"
    
    # 提取速度信息
    speed_info = ""
    for line in output.split('\n'):
        if 't/s' in line.lower():
            speed_info = line.strip()
    
    # 提取回答
    lines = output.split('\n')
    in_response = False
    answer_lines = []
    for line in lines:
        s = line.strip()
        if 'Start thinking' in s:
            in_response = True
            continue
        if in_response:
            if 'available commands' in s.lower() or 't/s' in s.lower():
                break
            if s and not s.startswith('[') and not s.startswith('>'):
                answer_lines.append(s)
    
    answer = ' '.join(answer_lines) if answer_lines else "(空输出)"
    
    result_line = f"第{i}题: {q}\n回答: {answer}\n速度: {speed_info}\n耗时: {elapsed:.1f}秒\n\n"
    print(result_line)
    
    with open(RESULT, "a", encoding="utf-8") as f:
        f.write(result_line)

with open(RESULT, "a", encoding="utf-8") as f:
    f.write("测试完成\n")

print("全部完成！结果在 test_3q_final.txt")
