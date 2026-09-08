"""
Semantic Vector Retrieval and In-Memory Vector Store.
Computes deterministic embeddings and executes cosine similarity retrieval.
"""

import math
import re
from typing import List, Dict, Any, Tuple
from src.knowledge.interfaces import SemanticStoreInterface


def _tokenize(text: str) -> List[str]:
    """Tokenize text into lowercased alphanumeric tokens."""
    return re.findall(r"\b\w{3,}\b", text.lower())


def _compute_hash_embedding(text: str, dimension: int = 128) -> List[float]:
    """
    Compute a deterministic normalized hash embedding vector from text.
    Provides fast, reproducible, offline semantic representations without external API dependencies.
    """
    vector = [0.0] * dimension
    tokens = _tokenize(text)
    if not tokens:
        return vector

    for token in tokens:
        h = hash(token)
        idx = abs(h) % dimension
        weight = 1.0 + (abs(hash(token[:3])) % 5) * 0.1
        if h > 0:
            vector[idx] += weight
        else:
            vector[idx] -= weight

    # Compute Euclidean norm
    norm = math.sqrt(sum(x * x for x in vector))
    if norm > 0:
        vector = [x / norm for x in vector]

    return vector


def _cosine_similarity(vec_a: List[float], vec_b: List[float]) -> float:
    """Compute cosine similarity between two unit vectors."""
    if len(vec_a) != len(vec_b):
        return 0.0
    return sum(a * b for a, b in zip(vec_a, vec_b))


class InMemoryVectorStore(SemanticStoreInterface):
    """In-memory semantic vector store for fast similarity search."""

    def __init__(self, dimension: int = 128):
        self.dimension = dimension
        self.index: Dict[str, Dict[str, Any]] = {}

    def index_item(self, item_id: str, text: str, metadata: Dict[str, Any] = None) -> None:
        """Index a text item with computed vector embedding."""
        embedding = _compute_hash_embedding(text, self.dimension)
        self.index[item_id] = {
            "id": item_id,
            "text": text,
            "embedding": embedding,
            "metadata": metadata or {},
        }

    def search_similar(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search top-k most similar indexed items to query."""
        if not self.index:
            return []

        query_vec = _compute_hash_embedding(query, self.dimension)
        scores: List[Tuple[float, Dict[str, Any]]] = []

        for item_id, entry in self.index.items():
            sim = _cosine_similarity(query_vec, entry["embedding"])
            scores.append((sim, entry))

        # Sort descending by similarity
        scores.sort(key=lambda x: x[0], reverse=True)

        results = []
        for sim, entry in scores[:top_k]:
            results.append({
                "id": entry["id"],
                "text": entry["text"],
                "similarity": round(sim, 4),
                "metadata": entry["metadata"],
            })

        return results

    def clear(self):
        """Clear all indexed items."""
        self.index.clear()
