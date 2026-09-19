"""
Step 5: Expose the RAG system as an HTTP endpoint so n8n/Make can call it.

Run with:
    uvicorn app_api:app --host 0.0.0.0 --port 8000

Then in n8n: add an HTTP Request node, POST to http://<your-host>:8000/ask
with JSON body {"question": "..."}. Wire that after a Slack "message
received" trigger, and feed the response's "answer" field into a Slack
"send message" node. That's your "RAG connected to a live workflow"
deliverable -- export the n8n workflow as JSON and screenshot a real run.
"""

import os
import sys

from fastapi import FastAPI
from pydantic import BaseModel

sys.path.insert(0, os.path.dirname(__file__))
from importlib import import_module

rag_query = import_module("03_rag_query")

app = FastAPI(title="NimbusWorks RAG API")


class Question(BaseModel):
    question: str
    top_k: int = 4


@app.post("/ask")
def ask(payload: Question):
    result = rag_query.answer_question(payload.question, top_k=payload.top_k)
    return result


@app.get("/health")
def health():
    return {"status": "ok"}
