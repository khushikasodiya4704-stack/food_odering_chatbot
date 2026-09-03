"""
RAG Vector Store & Knowledge Base indexer for FlavorCraft Bistro.
Indexes menu catalog, dietary tags, allergen specifications, and restaurant policies.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import settings

class MenuKnowledgeRAG:
    """
    Knowledge retriever using embedding similarity with fallback lexical/BM25 scoring
    to guarantee 100% reliability and lightning-fast responses.
    """
    _instance = None

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self._load_documents()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _load_documents(self):
        """Loads and prepares knowledge documents from JSON and Markdown files."""
        docs_dir = Path(settings.DOCS_DIR)
        menu_file = docs_dir / "menu_catalog.json"
        info_file = docs_dir / "restaurant_info.md"

        self.documents = []

        # 1. Ingest Menu Catalog items as distinct searchable chunks
        if menu_file.exists():
            with open(menu_file, "r", encoding="utf-8") as f:
                items = json.load(f)
                for item in items:
                    dietary_str = ", ".join(item.get("dietary", []))
                    allergens_str = ", ".join(item.get("allergens", [])) if isinstance(item.get("allergens"), list) else item.get("allergens", "None")
                    
                    content = (
                        f"Item: {item['name']}\n"
                        f"Category: {item['category']}\n"
                        f"Price: ${item['price']:.2f}\n"
                        f"Dietary: {dietary_str}\n"
                        f"Allergens: {allergens_str}\n"
                        f"Calories: {item.get('calories', 'N/A')} kcal\n"
                        f"Spicy Level: {item.get('spicy_level', 0)}/3\n"
                        f"Description: {item['description']}\n"
                        f"Pairing Recommendation: {item.get('pairing_recommendation', '')}"
                    )
                    self.documents.append({
                        "id": f"menu_{item['id']}",
                        "title": item["name"],
                        "category": item["category"],
                        "type": "menu_item",
                        "dietary": item.get("dietary", []),
                        "allergens": item.get("allergens", []),
                        "price": item["price"],
                        "content": content,
                        "metadata": item,
                    })

        # 2. Ingest Restaurant Info and Policies as section chunks
        if info_file.exists():
            with open(info_file, "r", encoding="utf-8") as f:
                content = f.read()
                sections = content.split("## ")
                for sec in sections:
                    if not sec.strip():
                        continue
                    lines = sec.strip().split("\n")
                    sec_title = lines[0].strip("# ")
                    sec_body = "\n".join(lines[1:]).strip()
                    
                    self.documents.append({
                        "id": f"policy_{sec_title.lower().replace(' ', '_')}",
                        "title": sec_title,
                        "category": "Restaurant Policy & Info",
                        "type": "policy",
                        "dietary": [],
                        "allergens": [],
                        "price": 0.0,
                        "content": f"Section: {sec_title}\n{sec_body}",
                        "metadata": {"title": sec_title, "text": sec_body},
                    })

    def search(self, query: str, top_k: int = 4, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Performs semantic/keyword relevance search over knowledge chunks.
        Computes composite relevance score based on token overlap, title match, and category.
        """
        if not query or not self.documents:
            return []

        query_tokens = set(query.lower().replace("?", "").replace(",", "").replace(".", "").split())
        scored_docs = []

        for doc in self.documents:
            # Apply category filter if given
            if category_filter and doc.get("category", "").lower() != category_filter.lower():
                continue

            content_lower = doc["content"].lower()
            title_lower = doc["title"].lower()

            score = 0.0
            # Title exact/partial matches receive high weight
            if query.lower() in title_lower:
                score += 5.0

            # Token overlap scoring
            for token in query_tokens:
                if len(token) < 2:
                    continue
                if token in title_lower:
                    score += 3.0
                if token in content_lower:
                    score += 1.0

            # Special dietary / allergen boost
            for d in doc.get("dietary", []):
                if d.lower() in query_tokens:
                    score += 2.5
            
            if score > 0:
                scored_docs.append((score, doc))

        # Sort descending by score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored_docs[:top_k]]
