# Appendix C: RAG configuration reference

Purpose: Quick reference for key parameters and isolation rules.

## C.1 Core parameters (from config.py)
- RAG_TOP_K: 10 (env: RAG_TOP_K)
- MAX_CONTEXT_CHARS: 9000 (env: MAX_CONTEXT_CHARS)
- GENERATION_MAX_TOKENS: 2048 (env: GENERATION_MAX_TOKENS)
- GENERATION_TEMPERATURE: 0.3 (env: GENERATION_TEMPERATURE)
- EMBEDDING_MODEL_NAME: gemini-embedding-001
- GENERATION_MODEL_NAME: gemini-2.5-flash-preview-04-17

## C.2 Retrieval & reranking
- Matching Engine filter: Namespace(name="chatbot_id", allow_tokens=[str(chatbot_id)])
- Fusion: min-distance across queries → top M (M_FUSED_CHUNKS, default 10)
- Reranker: RankingService.rank_documents(query, docs) → reordered context

## C.3 History and prompting
- History budget: MAX_HISTORY_CHARS (default 1500 in RagService)
- Prompt enforces: answer in user query language, knowledge adherence level

## C.4 Image handling
- If image provided and enabled: extract text first; resupply image to final LLM only when no context found or image-only query

## C.5 Isolation and mapping
- Vector IDs: chatbot_{chatbot_id}_source_{hash}_chunk_{index}
- GCS path: chatbot_{id}/source_{hash}/{index}.txt
- Mapping table: VectorIdMapping.vector_id → source_identifier (file:// or http(s)://)

## C.6 Environment variables (selected)
- PROJECT_ID, GOOGLE_CLOUD_PROJECT: default "roo-code-459017"
- REGION: default "us-central1"
- BUCKET_NAME: default "was-bucket4"
- INDEX_ENDPOINT_ID: default "7916908131475521536"
- DEPLOYED_INDEX_ID: default "deployed_1746727342706"
- GOOGLE_GENAI_USE_VERTEXAI: default False (must be True for Vertex routing)
- GENERATION_MAX_TOKENS: default 2048
- GENERATION_TEMPERATURE: default 0.3
- RAG_TOP_K: default 10
- MAX_CONTEXT_CHARS: default 9000
