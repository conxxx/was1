# Appendix F: Runbook and troubleshooting

Purpose: Quick fixes for common MVP issues.

## F.0 Quick triage flow (5 minutes)
- Scope: one chatbot or all? If all, suspect infra/env (Redis, DB, Vertex config). If one, suspect data/index for that chatbot.
- Reproduce once with timestamps; note chatbot_id, client_id, and any request_id from logs.
- Health checks:
	- Redis reachable (SSE): see console for "SSE Utils: Connected to Redis".
	- DB reachable: GET /api/chatbots?client_id=...
	- Vertex config sane: PROJECT_ID/REGION/INDEX_ENDPOINT_ID/DEPLOYED_INDEX_ID present in config.
- Recent changes: ingestion, config, or env vars changed? Roll back or reapply.

## F.1 Ingestion appears stuck
- Check Celery worker is running and Redis reachable.
- Look at chatbot status via SSE (/api/chatbots/status-stream?clientId=...).
- Verify uploads/ files exist and have allowed extensions.
- Confirm /api/chatbots (POST) returned 202 with a task id in logs; ingestion enqueues run_ingestion_task.
- For updates, PUT /api/chatbots/{id} sets status 'Update Queued' when files/URLs change; verify SSE event published.
- If files rejected: ensure allowed types (txt, pdf, docx, md as per routes) and sizes; check server logs for cleanup actions.
- If discovery/crawl: verify /api/discover-links returns a task_id and GET /api/discover-links/{task_id} moves from PENDING→SUCCESS.
- Recovery: retry ingestion with a single small source; check that new vector mappings appear in DB and total_chunks_indexed increases.

## F.2 SSE not receiving events
- Ensure Redis is running at Config.CELERY_BROKER_URL.
- Confirm app/sse_utils.py prints connection OK and channel name matches.
- Check browser EventSource network tab for stream connection.
- The stream filters by client_id; ensure your widget passes the same clientId used on publish.
- CORS: dev allows *; if hosted behind a proxy, ensure headers are preserved and connection is not buffered.
- If no events but publish logs show >0 subscribers, check for client-side JS errors.

## F.3 Retrieval returns no results
- Verify chatbot_id namespace matches the indexed data.
- Confirm RAG_TOP_K and M_FUSED_CHUNKS reasonable; try increasing.
- Check that ingestion actually upserted datapoints to the index.
- Matching Engine filter: Namespace(name="chatbot_id", allow_tokens=[str(chatbot_id)]) — wrong chatbot_id will yield 0 neighbors.
- Check DEPLOYED_INDEX_ID and endpoint exist and are correct in config; if multiple deployed indexes, ensure the right one is selected.
- If fetch from GCS fails: validate vector_id format and GCS path (chatbot_{id}/source_{hash}/{index}.txt) and bucket access.
- Reranker failure is non-fatal; pipeline falls back to original order — investigate RankingService only after retrieval is healthy.

## F.4 LLM response empty or blocked
- Look at generation metadata: finish_reason, safety ratings.
- Reduce temperature or increase max tokens if truncated.
- Ensure prompt language and user query language align.
- Non-STOP finish_reason:
	- SAFETY: content blocked — adjust user input or safety settings (only if appropriate); surface a helpful message.
	- MAX_TOKENS: increase GENERATION_MAX_TOKENS or ask follow-up.
	- RECITATION: model avoided potential copyrighted content — reframe query.
- Verify GOOGLE_GENAI_USE_VERTEXAI=True in env for Vertex routing.
- Check model names in config: EMBEDDING_MODEL_NAME and GENERATION_MODEL_NAME must be valid and available in region.

## F.5 Voice flow issues
- Validate language code is in the supported set.
- If TTS audio missing: check base64 encoding and Content-Type.
- For STT failures: check Google Cloud STT quotas and credentials.
- Endpoint requires: audio (file), language, session_id; missing fields return 400.
- If voice disabled for chatbot, API returns 403; enable in settings.
- If responses include Markdown, TTS strips it via remove_markdown — verify text is still sensible.

## F.6 Rate limits and 429s
- Flask-Limiter defaults are in config (DEFAULT_RATE_LIMIT etc.); hotspots: login, creation, discovery.
- Back off and retry with jitter; for background tasks, prefer queueing over tight loops.

## F.7 Common error signatures → likely root cause
- "ME client/deployed ID not initialized": INDEX_ENDPOINT_ID/DEPLOYED_INDEX_ID misconfigured or clients not initialized.
- "Failed to generate any embeddings": genai client not initialized or API/model config invalid; check GOOGLE_GEMINI_API_KEY and Vertex env.
- "Failed to fetch text content for ... sections": GCS path or bucket permissions issue; confirm blob exists.
- "Forbidden: Message does not belong to this chatbot": API key/auth mismatch across tenants.
- SSE stream connects but no messages: clientId mismatch or publish not called (no push_status_update).

## F.8 When to re-index / re‑ingest
- After changing chunking/cleaning logic or source content: re-ingest the affected source(s).
- After DEPLOYED_INDEX_ID/index endpoint changes: verify and, if needed, rebuild vectors and mappings.
- For one-off fixes, target a single chatbot_id to limit blast radius.
