# One-Page Runbook — NimbusWorks Document RAG System

*(Convert this to PDF for submission — fill in the [bracketed] parts after you run it)*

## What it does
Answers employee questions (leave policy, IT security, onboarding, expenses,
remote work) using only NimbusWorks' internal documents, with citations to
the source chunk, and an honest refusal when the answer isn't in the docs.

## How it works
1. `01_ingest_and_chunk.py` — loads 5 policy docs, splits into ~40 chunks by
   section (700 chars, 100 char overlap).
2. `02_build_index.py` — embeds each chunk with Gemini
   (`gemini-embedding-001`) and stores it in a persisted Chroma DB.
3. `03_rag_query.py` — embeds the question, retrieves top-4 chunks, asks
   `gemini-2.5-flash` to answer using *only* those chunks with citations.
4. `app_api.py` — exposes `/ask` as an HTTP endpoint so n8n can call it.

## Triggers
- Manual: CLI (`python 03_rag_query.py "question"`)
- Automated: Slack message → n8n webhook → POST `/ask` → reply in Slack.
  [Insert your n8n workflow screenshot/JSON reference here.]

## Cost (approximate)
- Embeddings: ~40 chunks + [N] queries/day × gemini-embedding-001 pricing.
- Generation: ~[N] queries/day × gemini-2.5-flash pricing.
- [Insert your actual measured $/day or $/month once running.]

## How to fix it
| Symptom | Likely cause | Fix |
|---|---|---|
| `GEMINI_API_KEY not set` | `.env` missing/not loaded | copy `.env.example` to `.env`, add key |
| Every answer is NOT_FOUND | Index empty or stale | re-run `02_build_index.py` |
| Wrong/irrelevant sources cited | Chunk size too big, or `top_k` too low | lower `CHUNK_SIZE` in step 1, or raise `TOP_K` in step 3, re-index |
| API 429 errors | Rate limit / batch too large | lower `BATCH_SIZE` in `02_build_index.py` |
| n8n workflow gets no response | API not running / wrong port | confirm `uvicorn app_api:app` is running, check the port in the HTTP node |

## Guardrails in place
- System prompt forbids answering outside the retrieved context.
- Distance threshold: if the closest retrieved chunk is too far from the
  query embedding, we skip the LLM call entirely and return NOT_FOUND.
- Every answer includes source chunk IDs so a human can verify.
- Refusal string (`NOT_FOUND: ...`) is a fixed, greppable format so
  downstream automations (e.g. n8n) can branch on it.

## Evaluation results
[Paste summary from `eval_results.json` here, e.g.:
"15/15 answerable questions retrieved the correct source document;
3/3 unanswerable questions were correctly refused."]
