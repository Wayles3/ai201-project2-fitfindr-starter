# FitFindr — Starter Kit

This starter kit contains everything you need to begin Project 2.

## What's Included

```
ai201-project2-fitfindr-starter/
├── data/
│   ├── listings.json          # 40 mock secondhand listings
│   └── wardrobe_schema.json   # Wardrobe format + example wardrobe
├── utils/
│   └── data_loader.py         # Helper functions for  
├── tools.py                   # Hardened tool definitions
├── app.py                     # Gradio UI interface & agent loop
├── planning.md                #System architecture & design spec
├──requirements.txt           # Python dependencies
└── README.md                  # Complete project documentation
```

## Setup

**macOS / Linux:**
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

**Windows:**
```bash
python -m venv .venv
source .venv/Scripts/activate
pip install -r requirements.txt
```

Set your Groq API key in a `.env` file (get a free key at [console.groq.com](https://console.groq.com)):
```
GROQ_API_KEY=your_key_here
```

## The Mock Listings Dataset

`data/listings.json` contains 40 mock secondhand listings across categories (tops, bottoms, outerwear, shoes, accessories) and styles (vintage, y2k, grunge, cottagecore, streetwear, and more).

Each listing has: `id`, `title`, `description`, `category`, `style_tags`, `size`, `condition`, `price`, `colors`, `brand`, and `platform`.

Load it with:
```python
from utils.data_loader import load_listings
listings = load_listings()
```

## The Wardrobe Schema

`data/wardrobe_schema.json` defines the format your agent uses to represent a user's existing wardrobe. It includes:

- `schema`: field definitions for a wardrobe item
- `example_wardrobe`: a sample wardrobe with 10 items you can use for testing
- `empty_wardrobe`: a starting template for a new user

Load an example wardrobe with:
```python
from utils.data_loader import get_example_wardrobe
wardrobe = get_example_wardrobe()
```

## Tool Inventory

Your README submission must document each tool's name, inputs, and return value. **These must exactly match your actual function signatures in `tools.py`.** Your documented interfaces will be checked against your actual function signatures in `tools.py` — if the parameter count or types contradict what's in the code, you may not receive full credit for that tool.

---
1. search_listings
Inputs: description (str), size (str | None = None), max_price (float | None = None)
Output: list[dict]
Purpose: Searches and scores mock secondhand listings using token matching across title, category, brand, and style tags, filtered by size and maximum price ceiling.
2. suggest_outfit
Inputs: new_item (dict), wardrobe (dict)
Output: str
Purpose: Generates cohesive outfit pairings using the user's wardrobe. If the wardrobe is empty, it falls back gracefully to general staple styling recommendations.
3. create_fit_card
Inputs: outfit (str), new_item (dict)
Output: str
Purpose: Synthesizes the outfit details, item title, price, and sourcing platform into an authentic 2-4 sentence social media caption.

## Interaction Walkthrough

<!-- Walk through a complete interaction step by step: natural language query → each tool call (and why) → final fit card.
     Walk through this carefully — it's how graders follow your agent's reasoning without a live demo.
     Use a specific example — do not leave this as a template. -->

**User query:**Find me a vintage graphic tee under $50 and style an outfit for me.

**Step 1 — Tool called:**search_listings
- Tool: 
- Input: description="vintage graphic tee", size=None, max_price=50.0
- Why this tool: To locate available thrift items matching the user's style preference and budget constraint.
- Output: [{'id': 'item_001', 'title': 'Vintage Graphic Tee', 'category': 'Tops', 'price': 25.0, ...}]

**Step 2 — Tool called:**suggest_outfit
- Tool:
- Input: new_item={'title': 'Vintage Graphic Tee', 'category': 'Tops', ...}, wardrobe={'items': [...]}
- Why this tool: To pair the thrifted find with existing user clothing pieces.
- Output: "Pair the Vintage Graphic Tee with your high-waisted beige chinos and white sneakers for a balanced smart-casual look."

**Step 3 — Tool called:**create_fit_card
- Tool:
- Input: outfit="Pair the Vintage Graphic Tee with...", new_item={'title': 'Vintage Graphic Tee', 'price': 25.0, 'platform': 'Thrift Find'}
- Why this tool: To format the complete outfit into a short OOTD caption.
- Output: "Just snagged this Vintage Graphic Tee for $25.00 on Thrift Find! Styled it with my go-to beige chinos and white sneakers for an effortless weekend fit. #OOTD"

**Final output to user:**

I found a great thrift match and styled a complete outfit for you!
Found Item: Vintage Graphic Tee — $25.00 (Thrift Find)
Outfit Suggestion: Pair the Vintage Graphic Tee with your high-waisted beige chinos and white sneakers for a balanced smart-casual look.
Fit Card Caption: "Just snagged this Vintage Graphic Tee for $25.00 on Thrift Find! Styled it with my go-to beige chinos and white sneakers for an effortless weekend fit. #OOTD"

## Error Handling and Fail Points

<!-- For each tool, describe the specific failure mode and what your agent does in response.
     This maps to the error handling section of the rubric (F5-C1). -->

| Tool | Failure mode | Agent response |
|------|-------------|----------------|
| `search_listings` |No listings match criteria or description is empty | Returns [] cleanly instead of raising NoneType or index errors.|

| `suggest_outfit` |User wardrobe is empty ({"items": []}) |Bypasses wardrobe matching and returns 2-3 versatile staple pairing ideas. |
| `create_fit_card` |outfit string is empty or missing |Returns a structured fallback caption containing the item title, price, and platform |

---

## Spec Reflection

<!-- Answer both questions with at least 2–3 sentences each. -->

**One way planning.md helped during implementation:**
Defining data flow early made it easy for me to structure state passing between suggest_outfit and create_fit_card without schema mismatches.
**One divergence from your spec, and why:**
Switched MODEL_NAME to qwen/qwen3.8-27b after encountering 413 Entity Too Large and 404 Model Not Found errors on compound model endpoints.
---


AI Usage section
(ChatGPT / Groq LLMs / Gemini/ Claude) was utilized during the development of FitFindr for the following specific tasks:
1. Tool Interface Hardening & Error Handling (tools.py)
AI Input: Error logs involving NoneType exceptions during empty search queries and KeyError exceptions when parsing user wardrobe payloads.
AI Contribution: Suggested defensive checking patterns and default return structures (e.g., returning empty lists [] instead of raising runtime errors).
Human Integration & Override: Refactored token-matching scoring logic to handle partial string matching across title, brand, and style_tags while preserving exact type signatures.
2. API Payload Optimization & Model Selection
AI Input: Groq API error logs (413 Request Entity Too Large and 404 Model Not Found).
AI Contribution: Identified that passing full JSON database dumps exceeded context window token limits and recommended string truncation.
Human Integration & Override: Selected qwen/qwen3.8-27b as the primary model and implemented string slicing (wardrobe_text[:400]) and max_tokens=300 caps to stay within rate limits.
3. UI Component Wiring (app.py)
AI Input: UI layout requirements for displaying tool outputs in separate Gradio panels.
AI Contribution: Generated initial Gradio layout structure using gr.Row() and gr.Textbox().
Human Integration & Override: Wrote the primary handle_query() execution loop to sequence tool execution state, update state keys, and return structured outputs directly to UI components.

## Where to Start

1. **Read `planning.md` and fill it out before writing any code.**
2. Verify the data loads correctly by running `python utils/data_loader.py`.
3. Build and test each tool individually before connecting them through your planning loop.

Your implementation files go in this same directory. There's no required file structure for your agent code — organize it however makes sense for your design.

## Demo Video
Watch the 2-minute FitFindr agent walkthrough here:
[FitFindr Demo Video](https://youtu.be/nhqiJGz6aIM)