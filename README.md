# Adam: The Wise NPC - Dialogue System

This project implements a dialogue engine for a role-playing game (RPG) NPC named **Adam**, a centuries-old sage of the Northern Isles. Built using LangGraph, a custom memory server (MCP), and Google Gemini API.

---

##  Features

-  Memory-managed dialogue system (summarized + recent context)
-  Wikipedia tool integration (factual Q&A)
-  Persona-driven natural responses
-  Powered by LangGraph (workflow routing)
-  Gemini integration (While the code that can call chatgpt is also retained)

---

##  How to Run

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2.Set your Gemini API Key

In mcp_client.py:

```bash
genai.configure(api_key="your-gemini-api-key")
```

### 3. Start the MCP server

```bash
python mcp_server.py
```

### 4. In another terminal, start the client

```bash
python mcp_client.py
```

### 5. Chat with Adam

Try to ask him some questions like:

```bash
what is an RPG game?
who was the first king of the northern isles?
```

## Sample Transcript

See sample_dialogue.json for a 6-turn conversation including a tool call.

## Files

mcp_server.py: TCP/HTTP server with memory, summarization, and tool-call support

mcp_client.py: LangGraph dialogue flow, Gemini LLM integration

sample_dialogue.json: Example 5+ turn interaction

README.md