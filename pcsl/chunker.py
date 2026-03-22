import json
import numpy as np
import os
from typing import List, Dict, Any

# Optional AI dependencies
try:
    from sentence_transformers import SentenceTransformer
    HAS_TRANSFORMERS = True
except ImportError:
    HAS_TRANSFORMERS = False

MODEL_NAME = "all-MiniLM-L6-v2"
_model = None

def get_model():
    global _model
    if not HAS_TRANSFORMERS:
        raise ImportError("sentence-transformers not installed. Install requirements-ai.txt.")
    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)
    return _model

def flatten_context(ctx: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flatten nested context into searchable chunks."""
    chunks = []
    for namespace, data in ctx.items():
        if namespace == "pcsl_version" or namespace == "last_updated":
            continue
            
        if isinstance(data, dict):
            for k, v in data.items():
                chunks.append({
                    "text": f"{namespace}.{k}: {v}",
                    "namespace": namespace,
                    "key": k,
                    "value": v
                })
        elif isinstance(data, list):
            for item in data:
                chunks.append({
                    "text": f"{namespace}: {json.dumps(item)}",
                    "namespace": namespace,
                    "data": item
                })
    return chunks

def get_relevant_context(ctx: Dict[str, Any], query: str, top_k: int = 5) -> Dict[str, Any]:
    """Return only the context chunks most relevant to the query using cosine similarity."""
    if not HAS_TRANSFORMERS:
        return ctx # Fallback to full context
        
    chunks = flatten_context(ctx)
    if not chunks:
        return {}
        
    texts = [c["text"] for c in chunks]
    
    model = get_model()
    query_emb = model.encode([query])
    chunk_embs = model.encode(texts)
    
    # Compute cosine similarity
    scores = np.dot(chunk_embs, query_emb.T).flatten()
    top_indices = scores.argsort()[-top_k:][::-1]
    
    relevant = {}
    for i in top_indices:
        if scores[i] < 0.1: # Low relevance threshold
            continue
            
        chunk = chunks[i]
        ns = chunk["namespace"]
        
        if ns not in relevant:
            relevant[ns] = {} if "key" in chunk else []
            
        if "key" in chunk:
            relevant[ns][chunk["key"]] = chunk["value"]
        else:
            relevant[ns].append(chunk["data"])
            
    return relevant
