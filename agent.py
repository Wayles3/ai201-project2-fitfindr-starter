"""
agent.py

The FitFindr planning loop. Orchestrates the tools in response to a
natural language user query, passing state between them via a session dict.

Usage:
    from agent import run_agent
    from utils.data_loader import get_example_wardrobe

    result = run_agent(
        query="vintage graphic tee under $30, size M",
        wardrobe=get_example_wardrobe(),
    )
    print(result["fit_card"])
    print(result["error"])   # None on success
"""

import os
import re
import json
from dotenv import load_dotenv
from groq import Groq
from tools import search_listings, suggest_outfit, create_fit_card

load_dotenv()


# ── session state ─────────────────────────────────────────────────────────────

def _new_session(query: str, wardrobe: dict) -> dict:
    """
    Initialize and return a fresh session dict for one user interaction.
    """
    return {
        "query": query,              # original user query
        "parsed": {},                # extracted description / size / max_price
        "search_results": [],        # list of matching listing dicts
        "selected_item": None,       # top result, passed into suggest_outfit
        "wardrobe": wardrobe,        # user's wardrobe dict
        "outfit_suggestion": None,   # string returned by suggest_outfit
        "fit_card": None,            # string returned by create_fit_card
        "error": None,               # set if the interaction ended early
    }


# ── parameter parsing helper ──────────────────────────────────────────────────

def _parse_query(query: str) -> dict:
    """
    Extracts search filters (description, max_price, size) from a natural language query.
    Uses regex rules for fast extraction and falls back to LLM parsing if regex fails.
    """
    query_clean = query.strip()
    max_price = None
    size = None

    # 1. Extract Price (e.g. "under $30", "under 30", "<$30")
    price_match = re.search(r'(?:under|<|\$)\s*\$?(\d+(?:\.\d{1,2})?)', query_clean, re.IGNORECASE)
    if price_match:
        try:
            max_price = float(price_match.group(1))
        except ValueError:
            max_price = None

    # 2. Extract Size (e.g. "size M", "size Medium", "size 32", "size XL")
    size_match = re.search(r'\bsize\s+([a-zA-Z0-9]+)\b', query_clean, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).upper()

    # 3. Clean query string to derive description
    description = query_clean
    if price_match:
        description = re.sub(r'(?:under|<|\$)\s*\$?(\d+(?:\.\d{1,2})?)', '', description, flags=re.IGNORECASE)
    if size_match:
        description = re.sub(r'\bsize\s+[a-zA-Z0-9]+\b', '', description, flags=re.IGNORECASE)

    # Clean up excess noise words and extra spaces
    description = re.sub(r'\b(looking for|find me|a|an|in)\b', '', description, flags=re.IGNORECASE)
    description = " ".join(description.split()).strip(",. ")

    parsed = {
        "description": description or query_clean,
        "max_price": max_price,
        "size": size,
    }

    # 4. Fallback to LLM if regex failed to isolate a meaningful description
    if not parsed["description"] or len(parsed["description"]) < 2:
        api_key = os.getenv("GROQ_API_KEY")
        if api_key:
            try:
                client = Groq(api_key=api_key)
                prompt = (
                    f"Extract search parameters from this thrift query: '{query}'.\n"
                    f"Respond ONLY in valid raw JSON with keys: 'description', 'max_price', 'size'.\n"
                    f"Use null if missing."
                )
                response = client.chat.completions.create(
                    model="openai/gpt-oss-20b",
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=150,
                )
                raw_text = response.choices[0].message.content or ""
                # Attempt to parse json from response
                json_match = re.search(r'\{.*\}', raw_text, re.DOTALL)
                if json_match:
                    parsed_llm = json.loads(json_match.group(0))
                    parsed["description"] = parsed_llm.get("description") or query
                    parsed["max_price"] = parsed_llm.get("max_price")
                    parsed["size"] = parsed_llm.get("size")
            except Exception:
                pass

    return parsed


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Main agent entry point. Runs the FitFindr planning loop for a single
    user interaction and returns the completed session dict.
    """
    # Step 1: Initialize session
    session = _new_session(query, wardrobe)

    # Step 2: Parse query intent and extract metadata filters
    parsed_params = _parse_query(query)
    session["parsed"] = parsed_params

    # Step 3: Execute tool search_listings
    desc = parsed_params.get("description", query)
    max_price = parsed_params.get("max_price")
    size = parsed_params.get("size")

    try:
        results = search_listings(description=desc, size=size, max_price=max_price)
    except Exception as e:
        session["error"] = f"Error during search_listings execution: {str(e)}"
        return session

    session["search_results"] = results

    # Handle no-results early exit path
    if not results:
        session["error"] = f"No thrift listings found matching '{query}'."
        return session

    # Step 4: Select top matching item
    selected_item = results[0]
    session["selected_item"] = selected_item

    # Step 5: Execute tool suggest_outfit
   # Step 5: Execute tool suggest_outfit
    try:
        # Pass selected_item (dict), NOT a string like selected_item.get("title")
        outfit_text = suggest_outfit(new_item=selected_item, wardrobe=wardrobe)
        session["outfit_suggestion"] = outfit_text
    except Exception as e:
        session["error"] = f"Error during suggest_outfit execution: {str(e)}"
        return session

    # Step 6: Execute tool create_fit_card
    try:
        fit_card_res = create_fit_card(outfit=session["outfit_suggestion"], new_item=selected_item)
        session["fit_card"] = fit_card_res
    except Exception as e:
        session["error"] = f"Error during create_fit_card execution: {str(e)}"
        return session

    # Step 7: Return completed session state
    return session


# ── CLI test ──────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== Happy path: graphic tee ===\n")
    session = run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    )
    if session["error"]:
        print(f"Error: {session['error']}")
    else:
        print(f"Found: {session['selected_item']['title']}")
        print(f"\nOutfit: {session['outfit_suggestion']}")
        print(f"\nFit card: {session['fit_card']}")

    print("\n\n=== No-results path ===\n")
    session2 = run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    )
    print(f"Error message: {session2['error']}")