# Project Book: Website AI Assistant (WAS) & Agentic Chatbot — Remaining Sections

Note: Target emphasis ~75% on WAS (RAG chatbot) and ≤25% on the Agentic Chatbot helper.

## 3. Current State and Other Existing Solutions

3.1 Current State of Information Access on Websites
- TODO: Describe pain points (manual search, static FAQs, limited discovery).
- TODO: Briefly position WAS against current site search and FAQ widgets.

3.2 Related Work and Solutions
- TODO: Compare with: classic keyword search, FAQ bots, vendor RAG products.
- TODO: Pros/cons vs. WAS (multi-source ingestion, vector search, voice, widget API key, GCS/ME scale).

3.3 Rationale for Building WAS
- TODO: Why custom stack (Vertex AI ME + GCS + Celery + Flask + React widget) vs. off-the-shelf.

[Optional diagram] Competitive landscape chart. Place here.

## 4. Characterization, Specification, and Design

4.1 Functional Requirements (WAS)
- TODO: Chatbot creation, data ingestion (URLs/files), re-ingestion, deletion.
- TODO: RAG answering with citations, voice STT/TTS, widget config, SSE status.

4.2 Non-Functional Requirements
- TODO: Scalability (Celery workers), latency targets, observability, safety settings, privacy.

4.3 System Design Overview (WAS)
- TODO: 3-tier diagram (Frontend widget/admin, Flask API, storage/index).
- TODO: Data flow: Ingestion -> GCS -> Embeddings -> Matching Engine -> RAG -> Response.

4.4 Data Model and Indexing
- TODO: Vector ID scheme, ME namespace filtering by chatbot_id, GCS path layout.

4.5 Agentic Chatbot (Helper) Scope
- TODO: Bounded scope, available tools/APIs, SQLite store, image identification tool.

[Diagram] High-level architecture of WAS. Place here.

## 6. Implementation

6.1 Backend Services (WAS)
- TODO: Flask blueprints, key endpoints (create/update/delete chatbot, widget-config, voice, discovery/ingestion).
- TODO: Celery ingestion tasks, retries, chunking, embeddings, ME upsert.
- TODO: RAG pipeline (construct_prompt, find_neighbors, reranking, LLM generation).

6.2 Frontend/Admin and Widget
- TODO: React admin surfaces; embeddable widget parameters and API key.

6.3 Agentic Chatbot
- TODO: Flask API, SQLite DB, image identification, retail search, cart operations.

6.4 Security and Safety
- TODO: API key validation, rate limits, model safety settings.

[Sequence diagram] WAS query flow. Place here.

## 7. Technical Specifications

7.1 Models and APIs
- TODO: Embeddings model, generation model, STT/TTS services.

7.2 Data and Indexing Parameters
- TODO: Chunk sizes, overlaps, RAG_TOP_K, reranking.

7.3 Environments and Configuration
- TODO: Required env vars, GCP resources, local dev.

7.4 Benchmarks and Results
- TODO: Latency, retrieval quality, multilingual behavior.

[Table] Configuration parameters and defaults. Place here.

## 8. Summary and Future Extensions

8.1 Summary
- TODO: Summarize delivered capabilities and impact.

8.2 Future Work
- TODO: Scheduling tool for agent, analytics, feedback loop for reranking, multi-tenant hardening, UI polish.

## 9. Bibliography
- TODO: Add citations (RAG papers, Vertex AI docs, LangChain splitters, STT/TTS docs).

## 10. Appendices

A. API Reference (selected endpoints)
- TODO: Include request/response examples.

B. Deployment Notes
- TODO: GCP setup steps, environment variables, local dev tips.

C. Diagrams
- TODO: Final versions of all diagrams and captions.
