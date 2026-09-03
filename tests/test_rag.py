"""
Unit tests for RAG Vector Store, Ingestion, and Retriever.
"""

import pytest
from src.rag.vector_store import MenuKnowledgeRAG
from src.rag.retriever import MenuRetriever


def test_rag_knowledge_ingestion():
    rag = MenuKnowledgeRAG.get_instance()
    assert len(rag.documents) > 0

    # Ensure both menu items and restaurant policies are ingested
    types = {doc["type"] for doc in rag.documents}
    assert "menu_item" in types
    assert "policy" in types


def test_rag_vegan_search():
    retriever = MenuRetriever()
    results = retriever.query("vegan options", top_k=3)
    assert results is not None
    assert ("Beyond Plant Power Burger" in results or "Cauliflower" in results or "Vegan" in results)


def test_rag_policy_search():
    retriever = MenuRetriever()
    results = retriever.query("delivery hours policy and fees", top_k=2)
    assert results is not None
    assert ("Delivery" in results or "Hours" in results or "10:00 AM" in results)


def test_full_menu_summary():
    retriever = MenuRetriever()
    summary = retriever.get_full_menu_summary()
    assert "Burgers" in summary
    assert "Pizzas" in summary
    assert "Beverages" in summary
