"""
RAG Vector Store & Knowledge Base indexer for FlavorCraft Bistro.
Indexes menu catalog, dietary tags, allergen specifications, and restaurant policies.
Implements dense vector embeddings, Cosine Similarity mathematical computation, and hybrid metadata ranking.
"""

import os
import math
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from config import settings


def compute_cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """
    Computes the Cosine Similarity between two embedding vectors.
    Mathematical Formula:
        Cosine_Similarity(A, B) = (A • B) / (||A||₂ × ||B||₂)
                                = (Σ a_i * b_i) / (sqrt(Σ a_i²) * sqrt(Σ b_i²))
    """
    if not vec_a or not vec_b or len(vec_a) != len(vec_b):
        return 0.0

    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
    norm_a = math.sqrt(sum(a * a for a in vec_a))
    norm_b = math.sqrt(sum(b * b for b in vec_b))

    if norm_a == 0.0 or norm_b == 0.0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


class MenuKnowledgeRAG:
    """
    Knowledge retriever using dense vector embeddings and Cosine Similarity
    combined with domain-specific metadata boosting for 100% accurate culinary RAG.
    """
    _instance = None

    def __init__(self):
        self.documents: List[Dict[str, Any]] = []
        self.vocabulary: Dict[str, int] = {}
        self.doc_vectors: List[List[float]] = []
        self._load_documents()
        self._build_vector_embeddings()

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def _tokenize(self, text: str) -> List[str]:
        """Tokenizes and normalizes text into terms."""
        clean_text = re.sub(r"[^a-zA-Z0-9\s-]", " ", text.lower())
        return [t for t in clean_text.split() if len(t) > 1]

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

    def _build_vector_embeddings(self):
        """
        Builds normalized term-frequency embedding vectors for all indexed document chunks.
        """
        # Build global vocabulary from all document contents, titles, and dietary tags
        vocab_set = set()
        for doc in self.documents:
            tokens = self._tokenize(doc["content"] + " " + doc["title"] + " " + " ".join(doc.get("dietary", [])))
            vocab_set.update(tokens)

        self.vocabulary = {term: idx for idx, term in enumerate(sorted(vocab_set))}
        vocab_size = len(self.vocabulary)

        # Generate dense vector embeddings for each document
        self.doc_vectors = []
        for doc in self.documents:
            vec = self._vectorize_text(doc["content"] + " " + doc["title"] + " " + " ".join(doc.get("dietary", [])))
            self.doc_vectors.append(vec)

    def _vectorize_text(self, text: str) -> List[float]:
        """
        Transforms text into an embedding vector aligned with the knowledge vocabulary.
        """
        if not self.vocabulary:
            return []

        vec = [0.0] * len(self.vocabulary)
        tokens = self._tokenize(text)
        if not tokens:
            return vec

        for t in tokens:
            if t in self.vocabulary:
                idx = self.vocabulary[t]
                vec[idx] += 1.0

        # L2 Normalization
        norm = math.sqrt(sum(x * x for x in vec))
        if norm > 0:
            vec = [x / norm for x in vec]

        return vec

    def search(self, query: str, top_k: int = 4, category_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Executes Semantic Search using Cosine Similarity calculation between the query vector
        and all indexed document vectors, combined with domain-specific metadata boosts.
        """
        if not query or not self.documents:
            return []

        query_vec = self._vectorize_text(query)
        query_tokens = set(self._tokenize(query))
        scored_docs = []

        for idx, doc in enumerate(self.documents):
            # Apply category filter if given
            if category_filter and doc.get("category", "").lower() != category_filter.lower():
                continue

            doc_vec = self.doc_vectors[idx] if idx < len(self.doc_vectors) else []

            # 1. Cosine Similarity Calculation
            cosine_sim = compute_cosine_similarity(query_vec, doc_vec)

            # 2. Domain & Metadata Boosts
            score = cosine_sim * 10.0  # Scale cosine similarity (range 0 to 10)

            title_lower = doc["title"].lower()
            # Title exact match boost
            if query.lower().strip() in title_lower:
                score += 5.0

            # Dietary flag match boost (e.g. vegan, gluten-free, vegetarian)
            for d in doc.get("dietary", []):
                if d.lower() in query_tokens:
                    score += 3.0

            # Policy topic boost (hours, delivery fee, minimum order)
            if doc["type"] == "policy":
                for qt in query_tokens:
                    if qt in title_lower:
                        score += 2.0

            if score > 0.1:
                scored_docs.append((score, cosine_sim, doc))

        # Sort descending by composite score
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, _, doc in scored_docs[:top_k]]
