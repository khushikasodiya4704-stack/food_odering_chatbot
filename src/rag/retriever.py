"""
Retriever interface for RAG queries.
"""

from typing import List, Dict, Any, Optional
from src.rag.vector_store import MenuKnowledgeRAG


class MenuRetriever:
    def __init__(self):
        self.rag = MenuKnowledgeRAG.get_instance()

    def query(self, query: str, top_k: int = 4, category: Optional[str] = None) -> str:
        """
        Retrieves relevant knowledge passages and formats them as a clear markdown context string.
        """
        results = self.rag.search(query=query, top_k=top_k, category_filter=category)
        if not results:
            return "No matching menu items or policies found for this query."

        formatted_chunks = []
        for i, doc in enumerate(results, 1):
            formatted_chunks.append(f"--- Document [{i}] ({doc['category']}) ---\n{doc['content']}")

        return "\n\n".join(formatted_chunks)

    def get_full_menu_summary(self) -> str:
        """Returns concise categorized menu summary."""
        items_by_cat: Dict[str, List[str]] = {}
        for doc in self.rag.documents:
            if doc["type"] == "menu_item":
                meta = doc["metadata"]
                cat = meta["category"]
                if cat not in items_by_cat:
                    items_by_cat[cat] = []
                diet_str = f" [{', '.join(meta.get('dietary', []))}]" if meta.get("dietary") else ""
                items_by_cat[cat].append(f"- **{meta['name']}** (${meta['price']:.2f}){diet_str}: {meta['description']}")

        lines = ["# Restaurant Menu\n"]
        for cat, items in items_by_cat.items():
            lines.append(f"### {cat}")
            lines.extend(items)
            lines.append("")

        return "\n".join(lines)


# Singleton retriever instance
retriever = MenuRetriever()
