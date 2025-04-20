import json
import tiktoken
import time
import google.generativeai as genai

# 初始化 Gemini
genai.configure(api_key="AIza...")  # ← 替换成你的 key

# 初始化 tokenizer
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

def estimate_tokens(text):
    return len(encoding.encode(text)) + 2

def gemini_score(msg):
    prompt = f"""
                Rate the importance of the following message for remembering in an RPG dialogue history.
                Give a score from 1 (not important) to 10 (very important). Only return the number.

                Message:
                "{msg['content']}"
            """

    try:
        model = genai.GenerativeModel("models/gemini-1.5-pro")
        response = model.generate_content(prompt)
        score = float(response.text.strip())
        return min(max(score, 1), 10)
    except Exception as e:
        print(f"[Gemini error] {e}")
        return 5  # fallback default

def run_offline_memory_job():
    with open("conversation_history.json", "r") as f:
        history = json.load(f)

    enriched = []
    for msg in history:
        token = estimate_tokens(msg["content"])

        g_score = gemini_score(msg)

        enriched.append({
            "role": msg["role"],
            "content": msg["content"],
            "token": token,
            "score": g_score
        })
        time.sleep(0.5)  #  防止请求过快，避免被限流

    # 按分数降序，选前 N 条 or 控制总 token
    MAX_TOTAL_TOKENS = 3000
    enriched.sort(key=lambda x: -x["score"])

    selected = []
    total = 0
    for msg in enriched:
        if total + msg["token"] > MAX_TOTAL_TOKENS:
            break
        selected.append(msg)
        total += msg["token"]

    with open("memory_pool.json", "w", encoding="utf-8") as f:
        json.dump(selected, f, ensure_ascii=False, indent=2)

    print(f"✅ Done! Saved {len(selected)} messages into memory_pool.json")

if __name__ == "__main__":
    run_offline_memory_job()
