"""
Unit tests for Custom Agent Tools and Fallback Agent.
"""

import pytest
from src.agent.tools import (
    place_food_order,
    get_order_status,
    cancel_food_order,
    search_restaurant_knowledge,
    get_full_restaurant_menu,
)
from src.agent.chatbot_agent import FallbackAgent
from src.database.connection import init_db
from src.database.seed_data import seed_database


@pytest.fixture(scope="module", autouse=True)
def setup_all():
    init_db()
    seed_database()


def test_custom_tool_place_food_order():
    payload = {
        "customer_name": "Test Agent User",
        "customer_phone": "555-4321",
        "delivery_address": "500 Automation Blvd",
        "items": [
            {"item_name": "Smoky BBQ Bacon Burger", "quantity": 1, "special_instructions": "Extra BBQ"},
            {"item_name": "Fresh Mint Limeade", "quantity": 2, "special_instructions": "Less ice"},
        ],
        "special_notes": "Call upon arrival",
    }

    result = place_food_order.invoke(payload)
    assert "Order Successfully Placed" in result
    assert "Smoky BBQ Bacon Burger" in result
    assert "Fresh Mint Limeade" in result
    assert "Order Tracking Code" in result


def test_custom_tool_get_status():
    result = get_order_status.invoke({"order_code": "ORD-SEED-1001"})
    assert ("Order Status" in result or "ORD-SEED-1001" in result)


def test_custom_tool_rag_search():
    result = search_restaurant_knowledge.invoke({"query": "nut allergy hazelnut"})
    assert result is not None
    assert ("Hazelnut" in result or "Cold Brew" in result or "Allergens" in result)


def test_fallback_agent_flow():
    agent = FallbackAgent()
    
    # Menu inquiry
    res1 = agent.invoke({"input": "What is on the menu?"})
    assert "menu" in res1["output"].lower()

    # RAG inquiry
    res2 = agent.invoke({"input": "What are your delivery hours and vegan burgers?"})
    assert len(res2["output"]) > 20
