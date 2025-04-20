from flask import Flask, request, jsonify
import json
import tiktoken
import os
import google.generativeai as genai


encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
genai.configure(api_key="your-gemini-api-key")
MAX_TOKENS = 3000
MEMORY_POOL_PATH = "memory_pool.json"
app = Flask(__name__)


def estimate_tokens(text):
    return len(encoding.encode(text)) + 2

# Use keyword to roughly calculate score
def keyword_score(msg):
    content = msg["content"].lower()
    trivial = ["ok", "sure", "bye", "yes", "hello", "thanks"]
    question_words = ["what", "why", "how", "where", "when"]

    if any(t in content for t in trivial):
        return 1
    elif any(q in content for q in question_words):
        return 5
    elif len(content) < 10:
        return 2
    return 3

# Get & Load & Save memory pool
def get_pool_path(npc_id):
    return f"memory_pool_{npc_id}.json"

def load_memory_pool(npc_id):
    path = f"memory_pool_{npc_id}.json"
    if not os.path.exists(path):
        with open(path, "w", encoding="utf-8") as f:
            json.dump([], f)
        return []
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def save_memory_pool(pool, npc_id):
    path = f"memory_pool_{npc_id}.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pool, f, ensure_ascii=False, indent=2)


# ADD_MESSAGE {role, content} – Append message.
@app.route("/add_message", methods=["POST"])
def add_message():
    print("start add message")
    data = request.json
    role = data.get("role")
    content = data.get("content")
    npc_id = data.get("npc_id", "adam")  # Default adam

    if role not in ["user", "assistant"] or not content:
        return jsonify({"error": "Invalid input"}), 400

    token = estimate_tokens(content)
    k_score = keyword_score({"content": content})

    pool = load_memory_pool(npc_id)
    pool.append({
        "role": role,
        "content": content,
        "token": token,
        "score": k_score
    })

    pool.sort(key=lambda x: -x["score"])
    total = 0
    selected = []
    for msg in pool:
        if total + msg["token"] > MAX_TOKENS:
            continue
        selected.append(msg)
        total += msg["token"]

    save_memory_pool(selected, npc_id)
    return jsonify({"message": f"Added to {npc_id}'s memory"}), 200


# GET_CONTEXT – Return summarized + recent messages within token limit.
@app.route("/get_context", methods=["GET"])
def get_context():
    npc_id = request.args.get("npc_id", "adam")

    try:
        pool = load_memory_pool(npc_id)
    except Exception as e:
        print(f"[WARN] Failed to load memory for {npc_id}: {e}")
        return jsonify({"context": [], "token_count": 0}), 200

    if not pool:
        print(f"[INFO] memory_pool_{npc_id}.json is empty.")
        return jsonify({"context": [], "token_count": 0}), 200

    total_tokens = 0
    selected = []

    pool.sort(key=lambda x: -x["score"])
    for msg in pool:
        if total_tokens + msg["token"] > MAX_TOKENS:
            break
        selected.append({
            "role": msg["role"],
            "content": msg["content"]
        })
        total_tokens += msg["token"]

    return jsonify({
        "context": selected,
        "token_count": total_tokens
    }), 200



# TOOL_CALL <query> – Search Wikipedia or any public data source and return top result (can use requests + parsing).
@app.route("/tool_call", methods=["POST"])
def tool_call():
    data = request.json
    query = data.get("query")

    if not query:
        return jsonify({"error": "Missing query"}), 400

    from urllib.parse import quote
    import requests

    try:
        search_term = quote(query)
        url = f"https://en.wikipedia.org/w/api.php?action=query&list=search&srsearch={search_term}&format=json"
        res = requests.get(url, timeout=5)
        results = res.json()

        hits = results.get("query", {}).get("search", [])
        if not hits:
            return jsonify({"result": "No results found"}), 200

        top = next((r for r in hits if len(r["snippet"]) > 50), hits[0])
        snippet = top["snippet"].replace("<span class=\"searchmatch\">", "").replace("</span>", "") + "..."

        return jsonify({
            "query": query,
            "result": snippet
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# SUMMARIZE_HISTORY – Condense old dialogue.
@app.route("/summarize_history", methods=["POST"])
def summarize_history():
    try:
        npc_id = request.args.get("npc_id", "adam")
        pool = load_memory_pool(npc_id)
        if not pool:
            return jsonify({"error": "Memory pool is empty."}), 400

        sorted_pool = sorted(pool, key=lambda x: -x["score"])
        total = 0
        selected = []
        for msg in sorted_pool:
            if total + msg["token"] > 3000:
                continue
            selected.append(msg)
            total += msg["token"]

        merged_text = "\n".join(f"{m['role']}: {m['content']}" for m in selected)

        model = genai.GenerativeModel("models/gemini-1.5-pro")
        prompt = f"""
                You are a memory summarizer for a long RPG dialogue history.
                Summarize the following conversation into one short system message that captures the key facts and events, for future prompt compression:

                {merged_text}
                """
        response = model.generate_content(prompt)
        summary = response.text.strip()

        pool.append({
            "role": "system",
            "content": summary,
            "token": estimate_tokens(summary),
            "score": 9.5  # High score
        })

        pool.sort(key=lambda x: -x["score"])
        final = []
        total = 0
        for m in pool:
            if total + m["token"] > MAX_TOKENS:
                continue
            final.append(m)
            total += m["token"]

        save_memory_pool(final, npc_id)
        return jsonify({"summary": summary}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500



# RESET – Clear conversation.
@app.route("/reset", methods=["POST"])
def reset():
    npc_id = request.args.get("npc_id", "adam")
    save_memory_pool([], npc_id)
    return jsonify({"message": f"{npc_id}'s memory cleared."}), 200



if __name__ == "__main__":
    app.run(port=5000)
