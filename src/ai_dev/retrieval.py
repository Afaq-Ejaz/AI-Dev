"""
Phase 2 — First-Principles Semantic Retrieval

This module handles:
1. Loading the knowledge base from kb.json
2. Generating embeddings via Google GenAI
3. Cosine similarity from scratch using NumPy
4. Retrieving the best-matching policy for a given query
"""

import json
import os
import numpy as np
from pathlib import Path
from google import genai
from dotenv import load_dotenv

load_dotenv()

# ── Google GenAI Client ──────────────────────────────────────────────
client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
EMBEDDING_MODEL = "text-embedding-004"


# ── Load Knowledge Base ──────────────────────────────────────────────
def load_kb(path: str | None = None) -> list[dict]:
    """Load policies from kb.json and return as a list of dicts."""
    if path is None:
        path = Path(__file__).parent / "kb.json"
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data["policies"]


# ── Generate Embeddings ──────────────────────────────────────────────
def generate_embedding(text: str) -> np.ndarray:
    """Turn a single string into a vector (array of numbers) using Google GenAI."""
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
    )
    return np.array(response.embeddings[0].values)


def generate_kb_embeddings(policies: list[dict]) -> list[np.ndarray]:
    """Generate an embedding for each policy's content field."""
    embeddings = []
    for policy in policies:
        text = f"{policy['title']}: {policy['content']}"
        emb = generate_embedding(text)
        embeddings.append(emb)
    return embeddings


# ── Cosine Similarity (from scratch) ────────────────────────────────
def cosine_similarity(vec_a: np.ndarray, vec_b: np.ndarray) -> float:
    """
    Calculate cosine similarity between two vectors using NumPy.
    
    Formula: cos(θ) = (A · B) / (||A|| * ||B||)
    
    - dot product:  sum of element-wise multiplication
    - norm:         square root of sum of squares (length of vector)
    - result:       1.0 = identical, 0.0 = unrelated, -1.0 = opposite
    """
    dot_product = np.dot(vec_a, vec_b)
    norm_a = np.linalg.norm(vec_a)
    norm_b = np.linalg.norm(vec_b)

    if norm_a == 0 or norm_b == 0:
        return 0.0

    return float(dot_product / (norm_a * norm_b))


# ── Retrieval ────────────────────────────────────────────────────────
def retrieve_top_match(
    query: str,
    policies: list[dict],
    kb_embeddings: list[np.ndarray],
) -> tuple[dict, float]:
    """
    Given a user query, find the most relevant policy from the KB.
    
    Returns: (best_matching_policy, similarity_score)
    """
    query_embedding = generate_embedding(query)

    best_score = -1.0
    best_policy = policies[0]

    for i, kb_emb in enumerate(kb_embeddings):
        score = cosine_similarity(query_embedding, kb_emb)
        if score > best_score:
            best_score = score
            best_policy = policies[i]

    return best_policy, best_score


def retrieve_top_k(
    query: str,
    policies: list[dict],
    kb_embeddings: list[np.ndarray],
    k: int = 3,
) -> list[tuple[dict, float]]:
    """
    Return the top-K most relevant policies ranked by similarity.
    
    Useful for debugging — see what else the system considered.
    """
    query_embedding = generate_embedding(query)

    scored = []
    for i, kb_emb in enumerate(kb_embeddings):
        score = cosine_similarity(query_embedding, kb_emb)
        scored.append((policies[i], score))

    scored.sort(key=lambda x: x[1], reverse=True)
    return scored[:k]


# ── Quick Test ───────────────────────────────────────────────────────
if __name__ == "__main__":
    print("Loading knowledge base...")
    policies = load_kb()
    print(f"Loaded {len(policies)} policies.\n")

    print("Generating embeddings for all policies...")
    kb_embeddings = generate_kb_embeddings(policies)
    print(f"Generated {len(kb_embeddings)} embeddings.")
    print(f"Each embedding has {len(kb_embeddings[0])} dimensions.\n")

    # Test queries — each should match a specific policy
    test_queries = [
        "I got charged twice for my subscription",
        "I can't log in to my account",
        "How do I export my data?",
        "The app keeps crashing on my phone",
        "I want to delete my account permanently",
        "I want to speak to a manager right now",
        "I want a refund for my last order",
        "When will my package arrive?",
    ]

    print("=" * 60)
    print("RETRIEVAL ACCURACY TEST")
    print("=" * 60)

    for query in test_queries:
        policy, score = retrieve_top_match(query, policies, kb_embeddings)
        print(f"\nQuery:   \"{query}\"")
        print(f"Match:   {policy['title']}")
        print(f"Score:   {score:.4f}")
        print(f"Category: {policy['category']}")
        print("-" * 60)
