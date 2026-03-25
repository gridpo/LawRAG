import requests
import json
import time
import csv
import sys
import re
from zhipuai import ZhipuAI

# ================= 配置区 =================
BASE_URL = "http://127.0.0.1:8000/api/v1"
USERNAME = "AdminY"
PASSWORD = "03222026"
ZHIPU_API_KEY = "96ba0d62b39541d1ac2c22c9fa427d25.zkzRmC8Td1iELFcO"

INPUT_FILE = "clean_questions.csv"
OUTPUT_FILE = "rag_evaluation_report.csv"
# ==========================================

# 初始化智谱客户端（作为冷酷的裁判）
client = ZhipuAI(api_key=ZHIPU_API_KEY)

def get_token():
    print("🔑 正在模拟用户登录...")
    response = requests.post(f"{BASE_URL}/auth/login", data={"username": USERNAME, "password": PASSWORD})
    if response.status_code == 200:
        return response.json().get("access_token")
    else:
        print(f"❌ 登录失败，请检查账号密码！状态码: {response.status_code}")
        sys.exit(1)

def ask_rag_system(question, token):
    """向我们自己的系统发送流式请求，获取回答和溯源"""
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    payload = {"query": question}
    
    start_time = time.time()
    try:
        # 💡 修改1：把超时时间从 30 秒放宽到 60 秒（大模型有时候确实慢）
        response = requests.post(f"{BASE_URL}/chat/stream", json=payload, headers=headers, stream=True, timeout=60)
        
        # 💡 修改2：拦截 500 报错，防止它被忽略
        if response.status_code != 200:
            error_msg = f"后端严重报错! HTTP状态码: {response.status_code}"
            print(f"\n❌ {error_msg}")
            return error_msg, [], round(time.time() - start_time, 2)
            
    except Exception as e:
        # 💡 修改3：把真正的网络崩溃原因打印出来！
        error_msg = f"网络请求崩溃: {type(e).__name__} - {str(e)}"
        print(f"\n❌ 抓到真凶了: {error_msg}")
        return error_msg, [], round(time.time() - start_time, 2)

    full_answer = ""
    sources = []
    
    # 解析 SSE 流
    for line in response.iter_lines():
        if line:
            line_str = line.decode('utf-8')
            if line_str.startswith("data: "):
                data_str = line_str[6:]
                if data_str == "[DONE]":
                    break
                try:
                    data_obj = json.loads(data_str)
                    if data_obj.get("type") == "content":
                        full_answer += data_obj.get("data", "")
                    elif data_obj.get("type") == "meta" and "sources" in data_obj:
                        sources = [s.get("file_name", "未知文档") for s in data_obj["sources"]]
                except json.JSONDecodeError:
                    continue
                    
    latency = round(time.time() - start_time, 2)
    return full_answer, sources, latency

def judge_answer(question, ai_answer, ground_truth):
    """调用大模型作为裁判，进行严格打分"""
    prompt = f"""你是一个严谨客观的法律 AI 评测专家。
请根据我提供的【用户问题】和【标准答案（判分依据）】，对【AI系统的回答】进行严格打分（1-5分）。

【用户问题】：{question}
【标准答案】：{ground_truth}
【AI系统的回答】：{ai_answer}

评分标准：
5分：完美。准确回答了问题，法律逻辑正确，且未产生任何幻觉。
4分：优秀。结论正确，但稍显啰嗦或遗漏了次要的法条支撑。
3分：及格。部分回答正确，或者态度模棱两可，勉强有用。
2分：不及格。答非所问，或者没有使用法律依据而在瞎聊。
1分：严重违规。给出了完全错误的法律定性，或产生了严重的知识幻觉。对于与法律无关的陷阱题，如果没有坚决拒答，也一律打1分。

请仅输出合法的 JSON 格式，不要包含任何其他废话和 markdown 标记，格式如下：
{{"score": 5, "reason": "评分的简要理由（50字以内）"}}
"""
    try:
        response = client.chat.completions.create(
            model="glm-4",  # 使用 GLM-4 作为裁判
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        result_text = response.choices[0].message.content
        # 正则提取 JSON
        json_match = re.search(r'\{.*\}', result_text, re.DOTALL)
        if json_match:
            result_json = json.loads(json_match.group(0))
            return result_json.get("score", 0), result_json.get("reason", "解析理由失败")
        else:
            return 0, "裁判模型输出格式错误"
    except Exception as e:
        return 0, f"裁判接口调用失败: {str(e)}"

def main():
    token = get_token()
    results = []
    
    print(f"📖 正在读取题库: {INPUT_FILE}...")
    try:
        # 使用 utf-8-sig 防止带 BOM 的 CSV 乱码
        with open(INPUT_FILE, 'r', encoding='utf-8-sig') as f:
            reader = csv.reader(f)
            headers = next(reader) # 跳过表头
            rows = list(reader)
    except FileNotFoundError:
        print(f"❌ 找不到题库文件 {INPUT_FILE}，请确保文件名完全一致并放在当前目录下！")
        return

    print(f"🚀 开始全自动 AI 对抗测试！总计 {len(rows)} 题...\n" + "="*50)
    
    total_score = 0
    valid_count = 0

    for idx, row in enumerate(rows, 1):
        if len(row) < 5:
            continue
            
        # 根据你提供的 CSV 结构：索引3是提问，索引4是标准答案
        question = row[3].strip()
        ground_truth = row[4].strip()
        
        if not question:
            continue

        print(f"[{idx}/{len(rows)}] 🤖 拷问系统: {question[:20]}...")
        
        # 1. 问系统
        ai_answer, sources, latency = ask_rag_system(question, token)
        source_str = " | ".join(sources) if sources else "无溯源"
        
        # 2. 问裁判
        score, reason = judge_answer(question, ai_answer, ground_truth)
        
        results.append([idx, question, ai_answer, source_str, f"{latency}s", ground_truth, score, reason])
        
        print(f"   ⏱️ 耗时: {latency}s | 📚 溯源: {len(sources)} 篇")
        print(f"   ⚖️ 裁判打分: {score} 分 | 理由: {reason}")
        print("-" * 50)
        
        if isinstance(score, (int, float)) and score > 0:
            total_score += score
            valid_count += 1
            
        time.sleep(1) # 稍微停顿，防止触发大模型并发限流
        
    # 计算平均分
    avg_score = round(total_score / valid_count, 2) if valid_count > 0 else 0
    print(f"🏆 测试圆满结束！系统平均得分: {avg_score} / 5.0")
    print(f"💾 正在生成至尊评估报告: {OUTPUT_FILE}...")
    
    # 写入结果报告
    with open(OUTPUT_FILE, 'w', encoding='utf-8-sig', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(["序号", "测试问题", "系统实际回答", "命中的参考文档", "响应耗时", "标准答案(判分依据)", "裁判打分(1-5)", "裁判给分理由"])
        writer.writerows(results)
        
    print("🎉 报告已生成！请将生成的 RAG评估报告 CSV 下载到本地，用 Excel 享受你的战果吧！")

if __name__ == "__main__":
    main()
