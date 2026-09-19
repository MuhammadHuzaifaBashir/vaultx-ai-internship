"""
Step 3: Ask questions against the indexed corpus.

Retrieves the top-k most relevant chunks for a question, then asks
Gemini to answer USING ONLY those chunks, with citations back to the
source chunk IDs. If the answer isn't supported by the retrieved
chunks, the model is instructed to say so rather than guess.

Usage:
    python 03_rag_query.py "How many days of sick leave do I get?"

Can also be imported and used as a function (see answer_question()) --
this is what 04_evaluate.py and app_api.py both call.

NOTE: uses the newer `google-genai` SDK (the old `google.generativeai`
package is deprecated by Google as of 2026).

Includes retry logic on the generation call: transient errors (e.g.
503 "model overloaded") are retried with backoff instead of crashing
the whole run, per the Week 03 error-handling requirement.
"""

import json
import os
import sys
import time

import chromadb
from google import genai
from google.genai import types
from dotenv import load_dotenv

load_dotenv()

INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "index")
CHROMA_DIR = os.path.join(INDEX_DIR, "chroma_db")
COLLECTION_NAME = "nimbusworks_docs"
EMBED_MODEL = "gemini-embedding-001"
GEN_MODEL = "gemini-3.6-flash"
TOP_K = 4

SYSTEM_PROMPT = """You are a grounded question-answering assistant for NimbusWorks Inc.

Rules:
1. Answer ONLY using the information in the provided context chunks. Do not use outside knowledge, even if you know the answer.
2. Every factual claim in your answer must be traceable to a specific chunk. After each claim, cite the chunk id(s) it came from in square brackets, e.g. [hr_leave_policy.txt::chunk1].
3. If the context does not contain enough information to answer the question, respond exactly with: "NOT_FOUND: The documents don't contain enough information to answer this question." Do not guess or fill gaps with plausible-sounding information.
4. Be concise. Do not repeat the question back.
"""


def _client():
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY not set. Check your .env file.")
    return genai.Client(api_key=api_key)


def embed_query(client, text: str):
    result = client.models.embed_content(
        model=EMBED_MODEL,
        contents=[text],
        config=types.EmbedContentConfig(task_type="RETRIEVAL_QUERY"),
    )
    return result.embeddings[0].values


def retrieve(client, question: str, top_k: int = TOP_K):
    chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
    collection = chroma_client.get_collection(COLLECTION_NAME)
    query_embedding = embed_query(client, question)
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
    )
    chunks = []
    for i in range(len(results["ids"][0])):
        chunks.append({
            "id": results["ids"][0][i],
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })
    return chunks


def build_context(chunks):
    parts = []
    for c in chunks:
        parts.append(f"[{c['id']}] (source: {c['metadata']['source']})\n{c['text']}")
    return "\n\n---\n\n".join(parts)


def generate_answer(client, question: str, chunks, max_retries: int = 3):
    context = build_context(chunks)
    prompt = f"Context chunks:\n\n{context}\n\nQuestion: {question}"

    last_error = None
    for attempt in range(1, max_retries + 1):
        try:
            response = client.models.generate_content(
                model=GEN_MODEL,
                contents=prompt,
                config=types.GenerateContentConfig(system_instruction=SYSTEM_PROMPT),
            )
            return response.text.strip()
        except Exception as e:
            last_error = e
            print(f"  [retry {attempt}/{max_retries}] generation failed: {e}")
            if attempt < max_retries:
                time.sleep(2 * attempt)  # backoff: 2s, then 4s

    # all retries exhausted -- fail gracefully instead of crashing the whole run
    return f"NOT_FOUND: Generation failed after {max_retries} attempts ({last_error})."


def answer_question(question: str, top_k: int = TOP_K):
    """Main entry point used by CLI, eval script, and the API."""
    client = _client()
    chunks = retrieve(client, question, top_k=top_k)

    # basic guardrail: if nothing is even remotely close, don't bother
    # calling the LLM -- refuse immediately.
    if not chunks or min(c["distance"] for c in chunks) > 0.8:
        return {
            "question": question,
            "answer": "NOT_FOUND: The documents don't contain enough information to answer this question.",
            "sources": [],
            "grounded": False,
        }

    answer = generate_answer(client, question, chunks)
    is_not_found = answer.startswith("NOT_FOUND")

    return {
        "question": question,
        "answer": answer,
        "sources": [] if is_not_found else [
            {"id": c["id"], "source": c["metadata"]["source"]} for c in chunks
        ],
        "grounded": not is_not_found,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print('Usage: python 03_rag_query.py "your question here"')
        sys.exit(1)

    question = " ".join(sys.argv[1:])
    result = answer_question(question)
    print(json.dumps(result, indent=2))