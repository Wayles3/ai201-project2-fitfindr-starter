"""
tools.py

The three required FitFindr tools. Each tool is a standalone function that
can be called and tested independently before being wired into the agent loop.

Tools:
    search_listings(description, size, max_price)  → list[dict]
    suggest_outfit(new_item, wardrobe)              → str
    create_fit_card(outfit, new_item)               → str
"""
from __future__ import annotations
import re
import os
import json
from dotenv import load_dotenv
from groq import Groq
from utils.data_loader import load_listings


load_dotenv()

MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"


# ── Groq client ───────────────────────────────────────────────────────────────

def _get_groq_client() -> Groq:
    """Initialize and return a Groq client using GROQ_API_KEY from .env."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise ValueError("GROQ_API_KEY environment variable is missing.")
    return Groq(api_key=api_key)


# ── Tool 1: search_listings ───────────────────────────────────────────────────

def search_listings(
    description: str,
    size: str | None = None,
    max_price: float | None = None,
) -> list[dict]:
    """
    Search the mock listings dataset for items matching the description,
    optional size, and optional price ceiling.
    """
    # 1. Load all listings
    listings = load_listings()
    
    # Clean and tokenize query description
    query_tokens = set(re.findall(r'\b\w+\b', description.lower())) if description else set()
    
    scored_listings = []

    for item in listings:
        # 2. Filter by max_price (inclusive)
        if max_price is not None and float(item.get("price", 0)) > float(max_price):
            continue

        # Filter by size (case-insensitive substring match, e.g., "M" in "S/M")
        if size:
            item_size = (item.get("size") or "").upper()
            target_size = size.upper()
            if target_size not in item_size:
                continue

        # Safely extract string fields
        title = (item.get("title") or "").lower()
        desc = (item.get("description") or "").lower()
        category = (item.get("category") or "").lower()
        tags = [t.lower() for t in (item.get("style_tags") or []) if t]
        brand = (item.get("brand") or "").lower()

        # Tokenize fields
        title_tokens = set(re.findall(r'\b\w+\b', title))
        desc_tokens = set(re.findall(r'\b\w+\b', desc))
        category_tokens = set(re.findall(r'\b\w+\b', category))
        tag_tokens = set(re.findall(r'\b\w+\b', " ".join(tags)))
        brand_tokens = set(re.findall(r'\b\w+\b', brand))

        score = 0
        for token in query_tokens:
            if token in title_tokens:
                score += 3
            if token in category_tokens:
                score += 3
            if token in tag_tokens:
                score += 2
            if token in brand_tokens:
                score += 2
            if token in desc_tokens:
                score += 1

        if score > 0:
            scored_listings.append((score, item))

    scored_listings.sort(key=lambda x: x[0], reverse=True)
    return [item for _, item in scored_listings]


# ── Tool 2: suggest_outfit ────────────────────────────────────────────────────

def suggest_outfit(new_item: dict, wardrobe: dict) -> str:
    """
    Given a thrifted item and the user's wardrobe, suggest complete outfits.
    Handles empty wardrobe gracefully by providing general styling advice.
    """
    if not new_item or not isinstance(new_item, dict):
        return "Error: Valid thrift item required."

    items_list = wardrobe.get("items", []) if isinstance(wardrobe, dict) else []

    title = new_item.get("title", "Thrift Item")
    category = new_item.get("category", "Apparel")
    style_tags = ", ".join(new_item.get("style_tags", []))

    if not items_list:
        prompt = (
            f"The user has acquired a thrift item: {title} ({category}, style tags: {style_tags}). "
            f"The user's wardrobe is empty. Suggest 2-3 versatile ways to style this piece "
            f"as a standalone statement item using general fashion guidelines."
        )
    else:
        wardrobe_str = json.dumps(items_list, indent=2)
        prompt = (
            f"New thrift item: {title} ({category}, style tags: {style_tags}).\n"
            f"User's current wardrobe:\n{wardrobe_str}\n\n"
            f"Suggest a cohesive, stylish outfit ensemble combining the new item with 2-3 items from the wardrobe."
        )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are an expert personal fashion stylist."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=350,
        )
        content = response.choices[0].message.content
        return content.strip() if content else "Styling recommendation generation was empty."
    except Exception as e:
        return f"Styling unavailable: {str(e)}"


# ── Tool 3: create_fit_card ───────────────────────────────────────────────────

def create_fit_card(outfit: str, new_item: dict) -> str:
    """
    Generate a short, shareable outfit caption for the thrifted find using Groq LLM.
    Guards against empty outfit strings or missing item context.
    """
    if not outfit or not outfit.strip():
        return f"Error: Outfit details missing. Check out this find: {new_item.get('title', 'Thrift Item')} for ${new_item.get('price', 0.0)}!"

    if not new_item or not isinstance(new_item, dict):
        return "Error: Valid item details dictionary required."

    title = new_item.get("title") or "Thrifted Find"
    price = new_item.get("price", 0.0)
    platform = new_item.get("platform") or "Thrift Find"

    try:
        price_str = f"${float(price):.2f}"
    except (ValueError, TypeError):
        price_str = str(price)

    prompt = (
        f"Write a short, casual, authentic 2-4 sentence Instagram/TikTok OOTD caption.\n\n"
        f"Outfit Context: {outfit}\n"
        f"Thrifted Item: {title}\n"
        f"Price Paid: {price_str}\n"
        f"Platform Sourced From: {platform}\n\n"
        f"Style Requirements:\n"
        f"- Sound authentic and casual (like a real OOTD post).\n"
        f"- Naturally mention the item title ({title}), price ({price_str}), and platform ({platform}) exactly once each.\n"
        f"- Keep it strictly between 2 to 4 sentences."
    )

    try:
        client = _get_groq_client()
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "You are a trendy social media fashion influencer."},
                {"role": "user", "content": prompt}],
            temperature=0.8,
            max_tokens=350,
        )
        message = response.choices[0].message
        content = getattr(message, "content", None) or getattr(message, "reasoning_content", None)
        if content and content.strip():
            return content.strip()
        return f"**Item:** {title}\n**Price:** {price_str}\nJust scored this awesome find!"
    except Exception as e:
        return f"**Item:** {title}\n**Price:** {price_str}\nJust scored this awesome find! (API Error: {str(e)})"