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



> Who are you?
> what is an RPG game?
> who was the first king of the northern isles?

---

## Sample Transcript

See sample_dialogue.json.

> "User": "Hi, Nice to meet you. May I know something about you? Where is Baldur's Gate? Do you want to go to Baldur's Gate?",
> "Karlach": "BLOODY HELL, it's NICE to meet you too!  HAH!  *Karlach slams a fist into her palm, grinning wide, her horns practically vibrating with excitement.*  Name's Karlach, and I'm a BARBARIAN!  Though, maybe "barbarian" doesn't quite cover it.  See this? *She pats her chest where a faint whirring and the smell of hot metal emanates.*  Infernal engine. Keeps my blood boiling—literally! Makes me stronger, faster, HOTTER!  It's...complicated.  Let's just say I'm working on getting it fixed.  It's a bit...OVERENTHUSIASTIC, if you catch my drift.  Makes things a little TOO toasty sometimes.

> Baldur's Gate?  That's the goal!  The BIG ONE!  Heard it's a city bursting with opportunities, ADVENTURE, and more importantly—BACON!  Mountains of it!  Can you imagine?  Crispy, greasy, glorious BACON!  My mouth's watering just thinking about it.  And besides the bacon, I have...business there.  Need to find someone.  Someone who OWES me. Big time.  So yeah, Baldur's Gate!  I'm going there!  Wanna come?  It'll be a blast! Probably literally!  HAH!"



---

## Files

*mcp_server.py*: TCP/HTTP server with memory, summarization, and tool-call support

*mcp_client.py*: LangGraph dialogue flow, Gemini LLM integration

*offline_memory_job.py*: Periodical task. Re-score, rank and trim memory using Gemini for better long-term quality.

*persona_config.json*: Stores per-character system prompts for easy customization and extension.

*sample_dialogue.json*: Example dialogue

*README.md*

---

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

---

## Design Trade-offs

This section describes key trade-offs considered during development.
Each decision aims to balance speed, quality, simplicity, and extensibility.

### 1. Online vs. offline memory scoring
Online scoring uses keywords for latency performance.
Offline jobs use Gemini to update the score and improve accuracy.
This allows the system to stay responsive in real-time, while improving memory quality over time.

### 2. Token limit vs. keep history
To avoid model truncation, context is trimmed to a token budget. And all memory are ranked by score.
The design keeps important content while staying under token limitation.

### 3. Cold start handling
When a new character has no memory file, the system creates it automatically.
This prevents crashes and makes the first-time experience smooth.

## Future Plans
With more compute and real data, several improvements can be made in the future:

### 1. User-defined characters
Users can create new characters by writing a name and a short description.
The system will generate a persona and manage its memory automatically.
This supports open-ended, scalable role creation.

### 2. Embedding-based memory
Instead of using text to store memory, memory also can be encoded as embeddings.
This allows more precise similarity-based filtering and summarization.
It also enables character memory search and long-term personalization.

### 3. Dynamic tool selection
Instead of using keyword, we can use a light model to check if it need to use tools.

### 4. Safety model for content moderation
A safety model is a must for a online dialogue product. It will detect harmful, biased, or inappropriate content before the model responds.
