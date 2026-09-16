import json
import os
import re
from functools import lru_cache

from langchain_core.tools import tool
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from pymongo import MongoClient


@lru_cache(maxsize=1)
def _client():
    uri = os.getenv("MONGO_URI")
    if not uri:
        raise RuntimeError("MONGO_URI is not configured")
    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    client.admin.command("ping")
    return client


@lru_cache(maxsize=1)
def _collection():
    db_name = os.getenv("MONGO_DB", "khojindia")
    collection_name = os.getenv("MONGO_COLLECTION", "Sthan")
    return _client()[db_name][collection_name]


@lru_cache(maxsize=1)
def _embeddings():
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def database_status():
    try:
        collection = _collection()
        count = collection.estimated_document_count()
        return {
            "status": "ok",
            "database": os.getenv("MONGO_DB", "khojindia"),
            "collection": os.getenv("MONGO_COLLECTION", "Sthan"),
            "documents": count,
        }
    except Exception as exc:
        return {"status": "error", "message": str(exc)}


def _clean_doc(doc):
    return {
        "localName": doc.get("localName") or doc.get("name") or "Unknown",
        "district": doc.get("district", ""),
        "state": doc.get("state", ""),
        "description": doc.get("description", ""),
        "hashtags": doc.get("hashtags") or [],
        "mediaUrl": doc.get("mediaUrl", ""),
        "coins": doc.get("coins", 0),
        "similarity": round(float(doc.get("score", 0)), 4) if doc.get("score") is not None else None,
    }


def _vector_search(query: str):
    query_vector = _embeddings().embed_query(query)
    index_name = os.getenv("MONGO_VECTOR_INDEX", "vector_index")
    pipeline = [
        {
            "$vectorSearch": {
                "index": index_name,
                "path": "embedding",
                "queryVector": query_vector,
                "numCandidates": 50,
                "limit": 8,
            }
        },
        {
            "$project": {
                "_id": 0,
                "localName": 1,
                "name": 1,
                "district": 1,
                "state": 1,
                "description": 1,
                "hashtags": 1,
                "mediaUrl": 1,
                "coins": 1,
                "score": {"$meta": "vectorSearchScore"},
            }
        },
    ]
    return [_clean_doc(doc) for doc in _collection().aggregate(pipeline)]


def _lexical_search(query: str):
    stop_words = {
        "trip", "travel", "place", "places", "visit", "want", "need",
        "find", "show", "plan", "days", "day", "weekend", "india",
        "from", "near", "around", "some", "with", "for", "the", "and",
    }
    tokens = [
        token.lower()
        for token in re.findall(r"[A-Za-z]{3,}", query)
        if token.lower() not in stop_words
    ]

    docs = list(
        _collection().find(
            {},
            {
                "_id": 0,
                "localName": 1,
                "name": 1,
                "district": 1,
                "state": 1,
                "description": 1,
                "hashtags": 1,
                "mediaUrl": 1,
                "coins": 1,
            },
        ).sort("createdAt", -1).limit(200)
    )

    if not tokens:
        return [_clean_doc(doc) for doc in docs[:8]]

    ranked = []
    for doc in docs:
        searchable = " ".join([
            str(doc.get("localName", "")),
            str(doc.get("name", "")),
            str(doc.get("district", "")),
            str(doc.get("state", "")),
            str(doc.get("description", "")),
            " ".join(doc.get("hashtags") or []),
        ]).lower()
        score = sum(1 for token in tokens if token in searchable)
        if score:
            ranked.append((score, doc))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected = [doc for _, doc in ranked[:8]] or docs[:8]
    return [_clean_doc(doc) for doc in selected]


@tool
def search_hidden_gems(query: str) -> str:
    """Search the KhojIndia MongoDB dataset. Always call this before choosing a destination."""
    try:
        method = "vector"
        try:
            places = _vector_search(query)
        except Exception:
            method = "lexical-fallback"
            places = _lexical_search(query)

        return json.dumps({
            "found": bool(places),
            "retrieval": method,
            "count": len(places),
            "places": places,
            "rule": "The final destination must be selected only from this returned list.",
        })
    except Exception as exc:
        return json.dumps({
            "found": False,
            "retrieval": "failed",
            "count": 0,
            "places": [],
            "message": f"MongoDB retrieval failed: {exc}",
        })
