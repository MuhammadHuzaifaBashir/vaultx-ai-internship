"""
Step 2: Embed the chunks with Gemini and store them in a persisted
Chroma vector database.

Run 01_ingest_and_chunk.py first to produce index/chunks.json.

Uses Gemini's embedding model via task_type="retrieval_document" for
the stored chunks (this tells the model to optimize the embedding for
being *found*, which is a different objective than embedding a query).

The Chroma collection is persisted to disk in ../index/chroma_db, so it
survives a restart -- you don't need to re-embed every time you query.

NOTE: uses the newer `google-genai` SDK (the old `google.generativeai`
package is deprecated by Google as of 2026).
"""

import json
import os

import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "index")
CHUNKS_PATH = os.path.join(INDEX_DIR, "chunks.json")
CHROMA_DIR = os.path.join(INDEX_DIR, "chroma_db")
COLLECTION_NAME = "nimbusworks_docs"
EMBED_MODEL = "gemini-embedding-001"
BATCH_SIZE = 20  # keep small; Gemini's batch embed endpoint has limits


def embed_batch(client, texts):
    """Embed a batch of chunk texts as documents (for storage/retrieval)."""
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=texts,
        config=types.EmbedContentConfig(task_type="RETRIEVAL_DOCUMENT"),
    )
    return [e.values for e in result.embeddings]


def main():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit(
            "GEMINI_API_KEY not set. Check your .env file."
        )
    client = genai.Client(api_key=api_key)

    if not os.path.exists(CHUNKS_PATH):
        raise SystemExit("chunks.json not found. Run 01_ingest_and_chunk.py first.")

    with open(CHUNKS_PATH, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    # fresh build each run, so re-running this script is safe/idempotent
    try:
        chroma_client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = chroma_client.create_collection(COLLECTION_NAME)

    print(f"Embedding {len(chunks)} chunks in batches of {BATCH_SIZE}...")
    for i in range(0, len(chunks), BATCH_SIZE):
        batch = chunks[i : i + BATCH_SIZE]
        texts = [c["text"] for c in batch]
        embeddings = embed_batch(client, texts)

        collection.add(
            ids=[c["id"] for c in batch],
            embeddings=embeddings,
            documents=texts,
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  embedded {min(i + BATCH_SIZE, len(chunks))}/{len(chunks)}")

    print(f"\nIndex persisted to {CHROMA_DIR}")
    print(f"Collection '{COLLECTION_NAME}' contains {collection.count()} chunks.")


if __name__ == "__main__":
    main()
 
