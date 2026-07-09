"""
英语陪聊机器人 - 后端原型
技术栈: Flask + DeepSeek API
"""

import os
import sys
import json
from flask import Flask, request, jsonify, send_from_directory
import requests

app = Flask(__name__, static_folder=".")

# ============================================================
# 配置区 - 你的 DeepSeek API Key
# ============================================================
DEEPSEEK_API_KEY = os.environ.get("DEEPSEEK_API_KEY", "sk-67f8047b368f43a8badd25ba559f435c")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"


@app.route("/")
def index():
    """返回前端页面"""
    return send_from_directory(".", "index.html")


@app.route("/api/chat", methods=["POST"])
def chat():
    """接收中文文字 -> DeepSeek 翻译+回复"""
    data = request.get_json()
    user_text = data.get("text", "").strip()
    if not user_text:
        return jsonify({"error": "请输入文字"}), 400

    print(f"[用户中文]: {user_text}")

    prompt = f"""你是一个英语口语陪练助手。用户说了一句中文，请做三件事：

1. 将用户的中文翻译成自然、地道的英文
2. 用英文以英语老师的身份回复用户，回复要自然友好
3. 将你的英文回复翻译成中文

请严格按照以下 JSON 格式回复（不要加 markdown 包裹）：
{{"translation": "用户中文的英文翻译", "reply": "你的英文回复", "reply_cn": "英文回复的中文翻译"}}

用户说的是: {user_text}"""

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }

    payload = {
        "model": "deepseek-chat",
        "messages": [
            {"role": "system", "content": "你是一个英语口语陪练助手。你始终输出 JSON 格式。"},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "max_tokens": 500
    }

    try:
        resp = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=15)
        print(f"[DeepSeek 状态]: {resp.status_code}")
        resp.raise_for_status()
        result = resp.json()

        content = result["choices"][0]["message"]["content"].strip()
        print(f"[DeepSeek 原始]: {content}")

        # 清理可能的 markdown 包裹
        if content.startswith("```"):
            lines = content.split("\n")
            content = "\n".join(lines[1:-1]) if len(lines) > 2 else lines[-1]
        content = content.strip()

        parsed = json.loads(content)

        return jsonify({
            "translation": parsed.get("translation", ""),
            "reply": parsed.get("reply", ""),
            "reply_cn": parsed.get("reply_cn", "")
        })

    except json.JSONDecodeError as e:
        return jsonify({
            "translation": "(解析出错)",
            "reply": content,
            "reply_cn": ""
        }), 200
    except Exception as e:
        print(f"[错误]: {e}")
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    key_display = DEEPSEEK_API_KEY
    if key_display.startswith("sk-") and len(key_display) > 12:
        key_display = key_display[:8] + "..." + key_display[-4:]

    print("=" * 50)
    print("  English Buddy - 英语陪聊机器人")
    print(f"  DeepSeek Key: {key_display}")
    print("  打开浏览器: http://localhost:5000")
    print("  按 Ctrl+C 停止")
    print("=" * 50)
    app.run(host="0.0.0.0", port=5000, debug=False)
