from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
import requests
import google.generativeai as genai
import json
genai.configure(api_key="your-gemini-api-key")


NPC_ID = "adam"  

with open("persona_config.json", "r", encoding="utf-8") as f:
    PERSONA_MAP = json.load(f)

# Ask user to choose NPC
print("\nAvailable NPCs:")
for npc in PERSONA_MAP:
    print(f"- {npc}")
NPC_ID = input("\nEnter NPC ID to talk to: ").strip().lower()
if NPC_ID not in PERSONA_MAP:
    print("Unknown NPC. Defaulting to adam.")
    NPC_ID = "adam"

class DialogueState(TypedDict):
    user_input: str
    context: str
    tool_result: str
    prompt: str
    gpt_output: str

# 1. InputNode
def receive_user_input(state: DialogueState) -> DialogueState:
    user_input = input("You: ")
    return {"user_input": user_input}

# 2. CheckContextNode
def fetch_context(state: DialogueState) -> DialogueState:
    try:
        r = requests.get(f"http://127.0.0.1:5000/get_context", params={"npc_id": NPC_ID})
        r.raise_for_status()
        ctx = r.json().get("context", [])
    except Exception as e:
        print(f"⚠️ Failed to fetch context: {e}")
        ctx = []

    context_text = "\n".join(f'{m["role"]}: {m["content"]}' for m in ctx)
    state["context"] = context_text
    return state


# 3. ToolDecisionNode 
def needs_tool(state: DialogueState) -> bool:
    keywords = ["what", "who", "when", "where", "genre", "define", "history"]
    return any(k in state["user_input"].lower() for k in keywords)



# 4. PromptAssemblyNode: Generate prompt according to NPC
def assemble_prompt(state: DialogueState) -> DialogueState:
    persona = PERSONA_MAP.get(NPC_ID, {}).get("system_prompt", f"You are {NPC_ID}, an RPG character.")
    tool_info = f"\n(Reference: {state['tool_result']})" if state.get("tool_result") else ""
    prompt = persona + "\n" + state["context"] + "\nUser: " + state["user_input"] + tool_info
    state["prompt"] = prompt
    return state

# 5. LLMNode: : Sends prompt to gemini API
def call_gemini(state: DialogueState) -> DialogueState:
    prompt = state["prompt"]

    try:
        model = genai.GenerativeModel(model_name="models/gemini-1.5-pro")
        response = model.generate_content(prompt)
        state["gpt_output"] = response.text.strip()
    except Exception as e:
        state["gpt_output"] = f"(Gemini error: {e})"

    return state


# 6. OutputNode
def output_and_update(state: DialogueState) -> DialogueState:

    for role in ["user", "assistant"]:
        payload = {
            "npc_id": NPC_ID,
            "role": role,
            "content": state["user_input"] if role == "user" else state["gpt_output"]
        }
        try:
            requests.post("http://127.0.0.1:5000/add_message", json=payload)
        except:
            print(f"(⚠️ Failed to update message: {role})")

    return state

# Call Tool
def call_tool(state: DialogueState) -> DialogueState:
    try:
        r = requests.post("http://127.0.0.1:5000/tool_call", json={"query": state["user_input"]})
        result = r.json().get("result", "")
    except Exception as e:
        result = f"(Tool call failed: {e})"
    state["tool_result"] = result
    return state


graph = StateGraph(DialogueState)

graph.add_node("Input", receive_user_input)
graph.add_node("CheckContext", fetch_context)
graph.add_node("ToolCall", call_tool)
graph.add_node("Prompt", assemble_prompt)
graph.add_node("LLM", call_gemini)
graph.add_node("Output", output_and_update)
graph.set_entry_point("Input")
graph.add_edge("Input", "CheckContext")
graph.add_conditional_edges(
    "CheckContext",
    needs_tool,
    {
        True: "ToolCall",
        False: "Prompt"
    }
)
graph.add_edge("ToolCall", "Prompt")
graph.add_edge("Prompt", "LLM")
graph.add_edge("LLM", "Output")
graph.add_edge("Output", END)

app = graph.compile()
app.invoke({})
