import pytest
from tools import search_listings, suggest_outfit, create_fit_card

# --- search_listings Tests ---

def test_search_returns_results():
    results = search_listings("vintage graphic tee", size=None, max_price=50)
    assert isinstance(results, list)
    assert len(results) > 0

def test_search_empty_results():
    results = search_listings("designer ballgown", size="XXS", max_price=5)
    assert results == []  # Empty list, no exception raised

def test_search_price_filter():
    results = search_listings("jacket", size=None, max_price=10)
    assert isinstance(results, list)
    assert all(item["price"] <= 10 for item in results)

# --- suggest_outfit Tests ---

def test_suggest_outfit_happy_path():
    dummy_item = {"title": "Vintage Denim Jacket", "category": "outerwear", "style_tags": ["vintage", "streetwear"]}
    dummy_wardrobe = {"items": [{"title": "Black Graphic Tee", "category": "tops"}, {"title": "Cargo Pants", "category": "bottoms"}]}
    
    result = suggest_outfit(dummy_item, dummy_wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0

def test_suggest_outfit_empty_wardrobe():
    dummy_item = {"title": "Vintage Denim Jacket", "category": "outerwear", "style_tags": ["vintage"]}
    empty_wardrobe = {"items": []}
    
    result = suggest_outfit(dummy_item, empty_wardrobe)
    assert isinstance(result, str)
    assert len(result) > 0
    assert not result.startswith("Error:")

# --- create_fit_card Tests ---

def test_create_fit_card_happy_path():
    dummy_item = {"title": "Vintage Denim Jacket", "price": 25.0, "platform": "depop"}
    dummy_outfit = "Pair the denim jacket with a black graphic tee and cargo pants."
    
    result = create_fit_card(dummy_outfit, dummy_item)
    assert isinstance(result, str)
    assert len(result) > 0

def test_create_fit_card_empty_outfit():
    dummy_item = {"title": "Vintage Denim Jacket", "price": 25.0, "platform": "depop"}
    empty_outfit = ""
    
    result = create_fit_card(empty_outfit, dummy_item)
    assert isinstance(result, str)
    assert "Error:" in result or "Vintage Denim Jacket" in result