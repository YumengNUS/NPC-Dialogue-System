# Multiple Characters Dialogue System

This project is a dialogue system for role-playing game (RPG) characters. Default character **Adam** is a centuries-old sage of the Northern Isles, and other example characters are from **Baldur's Gate 3**. 
Built using LangGraph, a custom memory server (MCP), and Google Gemini API.

---

##  Features

-  Support for multiple characters, each with independent memory and personality 
-  Memory-managed dialogue system (summarized + recent context)
-  Wikipedia tool integration (factual Q&A)
-  **Offline memory optimization and summarization**
-  Cold-start handling for first-time interactions
-  LangGraph 
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

### 5. Choose NPC and start the conversation

You will be asked to choose an NPC.
Then you can start the conversation.
Try to ask some questions like:


```bash
Who are you?
what is an RPG game?
who was the first king of the northern isles?
```

## Sample Transcript

See sample_dialogue.json.



## Files

mcp_server.py: TCP/HTTP server with memory, summarization, and tool-call support

mcp_client.py: LangGraph dialogue flow, Gemini LLM integration

offline_memory_job.py: Periodical task. Re-score, rank and trim memory using Gemini for better long-term quality.

persona_config.json: Stores per-character system prompts for easy customization and extension.

sample_dialogue.json: Example dialogue

README.md

## System Design Overview

### Memory Server

The most important design is **memory scoring**.
Online writes use fast keyword-based scoring for latency performance.
Offline jobs use Gemini to re-score for accuracy.
This enables automatic removal of less important messages when the token budget is exceeded.
It balances response time and memory quality under real constraints.


- Built with Flask, exposes HTTP APIs for memory and tool access

- Stores one memory file per character (memory_pool_{npc_id}.json)

- Supports message addition, token-aware context retrieval, reset, summarization, and Wikipedia lookup

- Stateless by design, easy to inspect and scale

### Dialogue Client

- Built with LangGraph to manage dialogue flow as a state machine

- Steps: input → context fetch → optional tool → prompt → Gemini call → output + memory update

- Easy to modify flow or add new modules without affecting others

### Multi-Character Support

- Each NPC has isolated memory and persona

- Users select NPC at runtime

- New characters can be added via JSON config without changing code
