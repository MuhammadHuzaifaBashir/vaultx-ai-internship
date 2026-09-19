"""
Step 1: Ingest a real corpus and chunk it.

Reads every .txt file in ../corpus, cleans whitespace, and splits each
document into overlapping chunks. Chunking choices are explained below.

CHUNKING STRATEGY (explain this in your runbook):
- Chunk size: ~700 characters (~120-150 tokens). Small enough that each
  chunk stays on one topic (these are short policy documents with clear
  numbered sections), large enough to keep enough context for the LLM
  to answer without needing to stitch many chunks together.
- Overlap: 100 characters. Prevents a fact from being split exactly at
  a chunk boundary and becoming unretrievable or ungrounded.
- We split on paragraph/section boundaries first (numbered sections in
  these docs), then fall back to a sliding window inside long sections.
  This keeps each chunk semantically coherent instead of cutting
  mid-sentence.
- Each chunk keeps metadata: source filename, doc_id parsed from the
  header, and a chunk index, so the RAG step can cite exactly where an
  answer came from.

Output: chunks.json in ../index/ (a list of {id, text, metadata}).
"""

import json
import os
import re

CORPUS_DIR = os.path.join(os.path.dirname(__file__), "..", "corpus")
INDEX_DIR = os.path.join(os.path.dirname(__file__), "..", "index")
CHUNK_SIZE = 700
CHUNK_OVERLAP = 100


def clean_text(text: str) -> str:
    text = text.replace("\r\n", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def extract_doc_id(text: str) -> str:
    match = re.search(r"Document ID:\s*(\S+)", text)
    return match.group(1) if match else "UNKNOWN"


def split_into_sections(text: str):
    """Split on numbered section headers like '1. Annual Leave'."""
    pattern = r"\n(?=\d+\.\s+[A-Z])"
    sections = re.split(pattern, text)
    return [s.strip() for s in sections if s.strip()]


def sliding_window(text: str, size: int, overlap: int):
    if len(text) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def chunk_document(text: str, filename: str, doc_id: str):
    sections = split_into_sections(text)
    chunks = []
    chunk_idx = 0
    for section in sections:
        # keep short sections whole, split long ones with overlap
        pieces = sliding_window(section, CHUNK_SIZE, CHUNK_OVERLAP)
        for piece in pieces:
            chunks.append({
                "id": f"{filename}::chunk{chunk_idx}",
                "text": piece,
                "metadata": {
                    "source": filename,
                    "doc_id": doc_id,
                    "chunk_index": chunk_idx,
                },
            })
            chunk_idx += 1
    return chunks


def main():
    os.makedirs(INDEX_DIR, exist_ok=True)
    all_chunks = []

    files = sorted(f for f in os.listdir(CORPUS_DIR) if f.endswith(".txt"))
    if not files:
        print(f"No .txt files found in {CORPUS_DIR}. Add your documents there.")
        return

    for filename in files:
        path = os.path.join(CORPUS_DIR, filename)
        with open(path, "r", encoding="utf-8") as f:
            raw = f.read()
        text = clean_text(raw)
        doc_id = extract_doc_id(text)
        chunks = chunk_document(text, filename, doc_id)
        all_chunks.extend(chunks)
        print(f"{filename} ({doc_id}): {len(chunks)} chunks")

    out_path = os.path.join(INDEX_DIR, "chunks.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(all_chunks, f, indent=2)

    print(f"\nTotal chunks: {len(all_chunks)}")
    print(f"Saved to {out_path}")


if __name__ == "__main__":
    main()
