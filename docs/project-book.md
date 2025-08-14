# Project Book: Website AI Assistance (WAS) & Agentic Chatbot

Note on emphasis: This book focuses primarily on the Website AI Assistant (≈75%) and uses the Agentic Chatbot as a supporting helper (≤25%). Content is grounded in the current codebase, not legacy docs.

## Table of Contents

1. Introduction
2. Theoretical Background / Foundational Concepts
3. Current Existing Situation / State of the Art
4. Specification and Design (including development tools)
5. Scenarios (Use Cases / User Stories, System Processes)
6. Implementation and Results & Evaluation
7. Technical Details (models, data, methods)
8. Summary and Future Extensions
9. Bibliography / References
10. Appendices

## 1. Introduction

Purpose and motivation
- We’re building an inclusive website assistant so people can interact with any site in normal human language—text or voice—in their own language.
- The motivation is practical and human: many users struggle with education, language, technical literacy, or accessibility barriers, especially on essential services (government, healthcare, finance). We’ve seen these struggles first‑hand and designed the system to remove them.

What it does
- Users talk to the website via a chatbot widget (text or voice). They ask questions in their language; the assistant answers in the same language.
- Answers are grounded in the website’s own content using Retrieval‑Augmented Generation (RAG), reducing hallucinations and keeping responses accurate and up‑to‑date.
- Voice mode supports speech in/out for those who can’t (or prefer not to) type.
 - Summarization: users can paste a URL or raw text to get a concise summary in their own language.
 - Screenshot analysis: users can upload a page screenshot to extract and explain on‑screen content.

Who it helps
- Non‑technical users and people with lower educational backgrounds who need clear, direct answers.
- Users facing language barriers; the assistant mirrors the user’s language regardless of the site’s locale.
- People with accessibility needs (for example, motor impairments) who benefit from voice‑first interaction.
- Power users and developers on documentation‑heavy sites: the assistant pinpoints relevant passages, explains concepts, and accelerates onboarding and troubleshooting.

Why it helps website owners
- Reach more people by meeting them where they are—language, voice, and level of expertise.
- Reduce support load with accurate, self‑serve answers tied to your content.
- Provide a consistent, trustworthy experience; RAG answers are grounded in your site, not general web knowledge.

Two related applications in this repo
- Primary: Website AI Assistance (WAS), a multi‑tenant, code‑grounded RAG chatbot and embeddable widget.
- Secondary (demo): a voice‑first agentic shopping assistant that uses tool/function calling to search products, add to cart, and complete checkout. It’s not yet integrated into WAS; current demo flow is English‑only with a roadmap for multilingual voice.

Suggested images for this section:
- Widget answering a question on a sample site (text UI).
- Voice mode snippet (mic on, streaming transcript, spoken reply).
- Admin dashboard: create chatbot + add sources.

## 2. Theoretical Background

This section outlines the core concepts that underpin the two systems, aligned with how they are implemented in code.

### 2.1 Retrieval-Augmented Generation (RAG)

- Ingestion & Indexing: Source content (web pages, PDFs, DOCX, text) is parsed, cleaned, split into chunks, and stored. Each chunk is converted to a dense vector using Google’s Generative AI embeddings (google.genai, e.g., model “gemini-embedding-001”). The raw chunk texts are saved to Google Cloud Storage (GCS), and the vectors are upserted into Vertex AI Matching Engine. Vector IDs encode chatbot_id and source identity to enable strict per-chatbot isolation at query time.
- Retrieval: At query time, the user’s question is embedded via google.genai EmbedContent API and searched against the Matching Engine index using a namespace filter on chatbot_id (via aiplatform.matching_engine.Namespace). The top candidate chunk IDs are returned and their raw texts are fetched from GCS.
- Reranking: Retrieved chunks are optionally re-ranked by a RankingService to improve context ordering for the LLM.
- Generation: A prompt is constructed that includes instructions (knowledge adherence and strict “respond in the user’s language”), the chat history budgeted to a character limit, and the selected context sections. A Vertex AI GenerativeModel (Gemini family) generates the final answer with safety settings (harm categories and thresholds). Voice/image context can be included when enabled.

Why this matters: RAG keeps answers grounded in the site’s content, reduces hallucinations, and allows updates without retraining an LLM.

### 2.2 Agentic AI and Tool Use

The agentic helper uses an “LLM + tools” pattern. The LLM plans which tool to use, extracts parameters from the conversation, calls a tool (HTTP/API or Python function), observes the result, and synthesizes a final response.

Retail demo (separate from WAS, not yet integrated):
- Product catalog is created by the site owner and uploaded to Google Cloud Retail API; product vectors are served via Google’s Matching Engine.
- The user can operate the entire shopping flow by voice: search products, inspect details, add to cart, and proceed through checkout.
- Current status: English‑only demo; multilingual voice is on the roadmap so shoppers can browse and buy in their own language without typing or knowing the site’s locale.
- The agent calls well‑scoped tools: list_products, get_product, add_to_cart, remove_from_cart, view_cart, checkout, and optional image identification.

### 2.3 System Architecture Foundations

- Client-Server: A decoupled frontend (React admin and an embeddable JS widget) communicates with a Flask backend via HTTP APIs secured per-chatbot with an API key (Bearer).
- Data & Infra: SQLAlchemy models back a relational DB (SQLite in dev), chunk texts live in GCS, vectors live in Vertex AI Matching Engine, and LLM/Embeddings are served via Vertex AI/Google GenAI SDKs. Long-running jobs (ingestion, cleanup) run in Celery workers. Redis backs Server-Sent Events (SSE) for status streaming.
- Multimodal/Voice: Optional STT→RAG→TTS endpoints enable voice experiences; image input can seed or refine a query.

Suggested diagrams for this section:
- RAG pipeline schematic (Ingestion → Index → Retrieve → Re-rank → Generate).
- Data placement map (DB vs GCS vs Matching Engine) with the vector ID/GCS path conventions.

## 3. Current Existing Situation / State of the Art

This section summarizes the competitive landscape . The focus is on how the Proposed WAS aligns with or differs from other solutions on key capabilities.


//////////////////////////////////////////////////////////////////////Image placeholder: insert your comparison matrix image here.

### Competitor snapshots (2–3 sentences each)

1) WebAssistants.ai — AI helpers for web apps and dashboards
- What it is: A plug-and-play JavaScript widget for adding AI assistants to existing web apps/dashboards with “one line of code,” offering customizable assistants, function calls, optional web search, and multilingual support.
- Comparison: Optimized for in-app assistance and data interpretation inside owned dashboards. Our WAS is grounded RAG over any website’s content with strict per-tenant isolation, voice mode, URL/text summarization, and screenshot analysis; agentic tool use exists as a separate demo, not the core default.

2) A‑Eye Web Chat Assistant (Chrome extension)
- What it is: A browser accessibility assistant that analyzes the current page/screenshot, summarizes content, and enables voice navigation; runs with local models (Gemini Nano, Ollama, LM Studio, vLLM) or cloud (Gemini, Mistral) for privacy/control.
- Comparison: Targets end‑users in their browser, not site owners; logic runs client‑side and is page‑contextual. WAS is a site‑embedded, multi‑tenant service that answers strictly from the site’s indexed knowledge with server‑side RAG, tenant controls, and an admin console.

3) Salesloft Drift — AI chat for pipeline and revenue orchestration
- What it is: Enterprise conversational marketing/sales chat that personalizes conversations, qualifies leads, deanonymizes visitors, routes to reps, and plugs into Salesloft’s revenue platform (Rhythm, Deals, Analytics, Forecast).
- Comparison: Focused on demand gen and sales orchestration (lead scoring, routing, attribution). WAS centers on accurate, multilingual, accessibility‑friendly help grounded in site content; it doesn’t deanonymize visitors or manage pipeline by default, and prioritizes content grounding and voice inclusivity over sales ops.

## 4. Specification & Design (אפיון ועיצוב)

### 4.1 System goals and functional requirements

WAS (primary):
- Multi-tenant chatbots per account; each chatbot has a unique API key and configuration.
- Sources: add website URLs and upload files (.txt, .pdf, .docx); ingestion is asynchronous.
- RAG chat: answer strictly from the provided content; enforce language matching to the user query; optional image-conditioned Q&A.
- Widget: embeddable script tag with customizable colors, avatar/logo, launcher text, typing indicator, start-open toggle, consent message (Authorization: Bearer <api_key> sent on widget calls).
- Admin: create/update/delete chatbots; manage sources; view ingestion status via SSE; regenerate API key.
- Feedback/history: thumbs and detailed feedback endpoint (if enabled); history persistence optional per chatbot with a retention policy.
- Voice: optional STT and TTS endpoints; VAD toggle.
 - Summarization: summarize a web page by URL or summarize pasted text; return the summary in the user’s language.
 - Screenshot analysis: accept an image of a page; extract text and elements to answer or summarize what’s on screen.

- Advanced RAG: feature flag per chatbot; standard mode is the default. Note: an experimental advanced RAG pipeline was less effective in our benchmarks for this deployment, so standard mode remains recommended.

Agentic chatbot (secondary):
- Use tool calls to perform product/cart tasks and simple checkout simulation.
- Optional image-identification tool to match products; optional external retail search.
- Keep scope focused; no broad autonomous actions beyond defined tools.

Non-functional:
- Isolation: per‑chatbot namespace filtering in vector search; see 4.6 for details on vector IDs and storage layout.
- Performance: background ingestion, concurrent GCS fetch, and reranking with prompt/history/context budgets; see 4.7 for targets and behavior.
- Safety & validation: LLM safety settings, strict knowledge adherence, file/input checks, and rate limiting; see 4.6 for the full model and controls.

### 4.2 High-level architecture

Components:
- Clients: React admin app; embeddable JS widget.
- Backend: Flask API with Blueprints; RagService (execute_pipeline, multimodal), Ingestion; Voice routes; SSE over Redis for status.
- Workers: Celery for ingestion, discovery/crawl, and deletion/cleanup tasks.
- Data & AI: SQLite (dev) via SQLAlchemy; GCS for chunk text; Vertex AI Matching Engine for vectors; google.genai for embeddings; Vertex AI GenerativeModel for LLM.

Recommended architecture diagram (insert here):

Note: The Discovery Engine reranker is optional and has a graceful fallback to the original retrieval order when unavailable or failing.

### 4.3 Agent tool specification (helper)

Scope: demo only; not integrated into the WAS RAG flow yet. Tool calls are constrained to declared endpoints/utilities; no autonomous browsing within WAS.

Examples based on the agent demo endpoints and utilities:
- list_products(): returns product summaries. Inputs: none | filters.
- get_product(product_id): returns product details. Inputs: product_id.
- add_to_cart(user_id, product_id, quantity): adds or updates an item. Inputs: user_id, product_id, quantity.
- remove_from_cart(user_id, product_id): removes item. Inputs: user_id, product_id.
- view_cart(user_id): returns cart items and totals. Inputs: user_id.
- checkout(user_id): simulates order creation; returns confirmation. Inputs: user_id.
- identify_image(image): classifies/identifies items in an image; may return candidate products. Inputs: base64 image or URL.

For each tool, the LLM is responsible for choosing the tool, extracting parameters from the conversation, and integrating tool outputs into its response.

### 4.4 Development tools & stack

- Backend: Python, Flask, SQLAlchemy, Alembic (migrations), Celery.
- Frontend: React SPA for admin; vanilla JS widget for embedding.
- Infra & AI: Google Cloud (Vertex AI GenerativeModel, Vertex AI Matching Engine), google-genai SDK for embeddings, Google Cloud Storage, Redis (SSE), SQLite (dev).
- Testing & Ops: Rate limiting, request validation, API-key auth per chatbot; logs and usage metrics via UsageLog.

Cross‑ref: For the full API endpoints and request/response schemas, see Appendix B.

///////////////////////////////////////////////////////////////////////////////////////////////////Suggested images for this section:
- Architecture diagram (above) exported as PNG for the book.
- Sequence diagram for ingestion and RAG.

### 4.5 UI/UX design philosophy

Admin dashboard (React):
- Prioritize clarity and control: one‑click chatbot creation; inline visibility into ingestion status via SSE; simple toggles for features (voice, image analysis, history retention, feedback).
- Safe defaults: strict knowledge adherence enabled by default; history disabled by default where privacy is required; conservative rate limits applied backend‑side.

- Error UX: surface backend validation messages (e.g., file type/size errors) and task statuses; provide copy‑paste embed snippet with chatbot_id and an auto‑injected API key placeholder.

Embeddable widget (vanilla JS):
- Minimal footprint: loads lazily, attaches to page corner, non‑intrusive by default; optional start‑open for proactive engagement.
- Conversational clarity: clear message bubbles, timestamps (optional), typing indicator, and consent message when required.
- Internationalization: answers strictly mirror the user’s query language; voice UI shows recording state and VAD behavior when enabled.
- Resilience: displays a friendly fallback message if the backend returns an error or the safety system blocks a reply.

Accessibility (inclusive by default):
- Keyboard navigation for all interactive elements; visible focus states.
- Screen‑reader labels for controls (open/close, mic start/stop, send) and ARIA live regions for streamed responses.
- High‑contrast theme compatibility and configurable font sizes; alt text for images and avatars.
- Voice‑only path for users who can’t type; captions/transcripts surfaced alongside TTS when available.

/////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////Suggested visuals: two lightweight wireframes—(1) admin “Create Chatbot” form with source inputs and toggles, (2) widget in closed and open states with branding.

### 4.6 Security model and data isolation

AuthN/AuthZ:
- Per‑chatbot API key required for widget endpoints; keys are securely hashed at rest (check_password_hash) and accepted via Authorization: Bearer <key>.
- Ownership checks on management endpoints using client_id; rate limits applied (e.g., login, create, update, widget‑config) via a limiter.
- Per‑chatbot API key is stored hashed and verified on each widget call via the Authorization: Bearer header.

Data isolation:
- Hard isolation at retrieval time using Vertex AI Matching Engine Namespace filtering by chatbot_id.
- Deterministic vector IDs encode chatbot and source: chatbot_{chatbot_id}_source_{hash}_chunk_{index}. GCS blob paths mirror this layout: chatbot_{id}/source_{hash}/{index}.txt.
- The RAG path validates the vector_id’s chatbot_{id} prefix before attempting any GCS fetch.

Input validation:
- File uploads restricted by extension and size for data sources; separate stricter limits for logo/.
- Image uploads validated for type; untrusted inputs are never executed.

Transport & CORS:
- CORS enabled for widget and admin usage; permissive defaults in dev; tighten allowed origins in production (permissive in dev; restrict in prod).

Safety:
- LLM safety settings block harassment, hate, explicit, and dangerous content; non‑STOP finish reasons are surfaced as user‑friendly messages.
- Knowledge adherence levels are configurable (strict/moderate/flexible) and enforced in prompt construction.

PII and consent:
- Voice privacy: audio is processed transiently for STT/TTS by default; no raw audio stored unless explicitly enabled in admin settings and disclosed to end users.

### 4.7 Operational characteristics and performance

SLOs (targets, adjustable):
- Chat response P50 < 2.5s, P95 < 6s for text‑only queries at moderate context sizes.
- Ingestion latency depends on site size; feedback streamed via SSE with states (Queued, Updating, Active, Pending Deletion, Empty) but relativly fast.

Throughput and concurrency:
- Celery workers handle ingestion/discovery/deletion tasks; concurrency sized to CPU and I/O; retrieval path supports concurrent GCS fetches and parallelizable neighbor searches. In standard mode a single query variant is used; advanced modes may add variants (experimental in this deployment and found less effective in benchmarks).

Retries and backoff:
- Background tasks use retries with backoff/jitter; transient GCP/HTTP errors do not block the API; partial results degrade gracefully.

Prompt/context budgets:
- Max history characters and context length are bounded; reranking reduces wasted tokens; token usage recorded in metadata when available.

### 4.8 Data lifecycle and deletion

Ingestion:
- Sources (URLs/files) are parsed, chunked, embedded, and upserted; VectorIdMapping relates each vector to its origin.

Update:
- Re‑ingestion tasks run when sources change; stale vectors are identified and removed; chatbot status reflects progress via SSE.

Deletion:
- Per‑source deletion removes vectors from Matching Engine and mappings from DB; full chatbot deletion clears vectors/mappings, chat messages,  and usage logs; reset chatbot status to Empty.
- Per‑source deletion specifically maps vector_ids via VectorIdMapping, removes those datapoints in Matching Engine, then cleans up corresponding DB mappings.

Storage layout:
- GCS: chatbot_{id}/source_{hash}/{index}.txt; DB: Chatbot, User, ChatMessage, DetailedFeedback, UsageLog, VectorIdMapping.

### 4.9 Configuration and environment

Core configuration (env/app config):
- PROJECT_ID, REGION, BUCKET_NAME, INDEX_ENDPOINT_ID, DEPLOYED_INDEX_ID.
- EMBEDDING_MODEL_NAME (e.g., gemini‑embedding‑001), GENERATION_MODEL_NAME (e.g., gemini‑2.5‑flash‑preview‑04‑17), generation temperature and max tokens.
- RAG_TOP_K, M_FUSED_CHUNKS, MAX_CONTEXT_CHARS, MAX_HISTORY_CHARS.
- GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are set programmatically to align SDKs in workers; workers also require GOOGLE_GENAI_USE_VERTEXAI=True for google.genai to target Vertex AI.

Secrets:
- API keys are hashed at rest; GCP credentials provided via standard environment mechanisms; never commit secrets.

Environments:
- Dev: SQLite; permissive CORS; relaxed rate limits.
- Prod: Prefer managed Postgres (or Cloud SQL), restricted CORS, stricter limits, multiple Celery workers, and health probes.

### 4.10 Observability and telemetry

Structured logging:
- Each request receives a request_id; timings recorded per step (embeddings, retrieval, fetch, rerank, generation).

Usage logs:
- UsageLog stores action details (query, response snippets, sources, duration_ms, status_code, token counts when available, errors, request_id) for audits and quality analysis.

LLM metadata:
- Finish reason and safety_ratings are included in the response metadata when available from the model API.

### 4.11 Risks and mitigations

- Model refusals/safety blocks: present helpful fallbacks; allow thumbs/detailed feedback to learn failure modes.
- Hallucinations: strict knowledge adherence with explicit “say I don’t know” instruction; retrieved context only.
- Latency spikes: concurrent GCS fetch, reranking budget, background task isolation; cache warmups as optional enhancement.
- Quota limits: exponential backoff; degrade to fewer neighbors or smaller context when necessary.
- Data leakage: namespace filtering and vector ID validation ensure cross‑chatbot isolation; never mix contexts across tenants.
- Credential mishandling: store only hashed API keys; rotate via regenerate‑key endpoint.
- Reranker failures: if the reranker fails or is unavailable, the system preserves the original retrieval order as a fallback.


## 5. Scenarios (Use Cases, User Stories, System Processes)

### 5.1 User Stories — WAS (primary)

- As a potential customer, I want to ask the chatbot specific questions about a product’s features so I can make a decision without reading long pages.
- As a new user, I want to ask “How do I reset my password?” and get an instant, accurate answer based on the site’s docs.
- As a business owner, I want to add web pages and documents so the chatbot can answer common questions and reduce my support load.
- As a support manager, I want visibility into questions asked so I can improve site content.
 - As a non‑English speaker, I want answers in my language so I can understand without switching locales (the bot mirrors the query language).
 - As an admin, I want to regenerate the API key and copy the widget embed snippet to quickly deploy the chatbot.
 - As a privacy‑sensitive tenant, I want to disable history and enable a consent gate in the widget.
 - As an admin, I want to delete a specific source or the entire chatbot and see status updates via SSE.
 - As a mobile user, I want to upload an image with my question so the bot can use it to seed or refine retrieval.
 - As a user, I want to paste a URL and get a concise summary of that page in my language.
 - As a user, I want to paste raw text and get a concise summary in my language.
 - As a user, I want to upload a screenshot of a page and have the assistant analyze and explain the content.
 - As a user with motor impairments, I want to use voice mode end‑to‑end without typing so I can navigate and get answers hands‑free.
 - As a developer on a documentation‑heavy platform, I want the assistant to interpret complex docs and guide me to exact steps or APIs.

### 5.2 User Stories — Agentic helper (secondary)

- As a customer trying to buy, I want the agent to help with cart operations and checkout.
- As a user troubleshooting, I want guided multi-step instructions based on my responses.
 - As a shopper, I want to browse and complete checkout using voice‑only interaction.

### 5.3 System Process — Answering a question with WAS

1) Widget sends POST to the backend with chatbot_id and API key (Bearer) plus the user’s question history.
2) Backend (RagService.execute_pipeline):
    - Embeds the query via google.genai models.embed_content (task_type=RETRIEVAL_QUERY).
    - Searches Vertex AI Matching Engine for nearest neighbors, filtered by Namespace chatbot_id to isolate data.
    - Fetches the raw chunk texts from GCS using the vector ID → GCS path convention.
    - For advanced Reranks the texts via RankingService and maps vector IDs back to their source identifiers. If the reranker is disabled or unavailable, the system preserves the original retrieval order.
    - Builds a prompt with knowledge adherence and a strict “respond in the query’s language” rule, budgets chat history, and includes context sections.
    - Calls Gemini (Vertex AI GenerativeModel) with safety settings to generate the answer.
3) API returns the answer, sources, and metadata; the widget renders the response.

Notes:
- If image analysis is enabled and an image is provided, the system first extracts text/description from the image to seed the query.
- Errors/warnings and token usage are logged to the UsageLog table for telemetry; finish_reason and safety_ratings are included in metadata when provided by the model.
- If no relevant context is found (or knowledge adherence is strict and nothing qualifies), the assistant replies that it doesn’t know rather than guessing.
- Advanced RAG can be toggled per chatbot or per request (use_advanced_rag), but standard mode is the default. In this deployment, the experimental advanced pipeline underperformed vs. standard in benchmarks.

### 5.4 System Process — Voice interaction (optional)

1) Frontend sends audio to the voice endpoint; backend performs STT.
2) The recognized text flows through the same RAG pipeline as above.
3) The final text answer is converted to TTS and returned alongside the text.

/////////////////////////////////////////////////////////////////////////////////////////////////Suggested images/diagrams for this section:
- Sequence diagram of the RAG query path (Widget → API → Embeddings → Matching Engine → GCS → Rerank → Gemini → Widget).
- Short clip or screenshot of voice request/response.

## 6. Implementation and Results & Evaluation (מימוש; תוצאות והערכה)


### 6.1 Backend layout (selected)

- Flask API: routes, auth decorators, and service wiring live under the backend app. Notable units:
    - REST routes (login, chatbot CRUD, widget-config, ingestion/crawl triggers, feedback, SSE status stream).
    - API key guard for widget endpoints via a decorator that reads Authorization: Bearer <key> and checks the hashed key.
    - A singleton accessor for the RAG service to reuse initialized clients (Vertex AI, google.genai, GCS, Redis, DB session).
    - SSE utilities publish status updates to Redis on a channel like "chatbot-status-updates", including chatbot_id and client_id for client-side filtering.
- RAG service: orchestrates embed → retrieve → fetch → //rerank → prompt → generate, plus multimodal and cleanup helpers.
- Celery workers: execute ingestion, discovery/crawl, and deletion tasks; report progress that the API exposes via SSE.
- Storage: chunk texts in GCS; vectors in Vertex AI Matching Engine; relational data via SQLAlchemy (SQLite in dev).

### 6.2 RAG pipeline internals

- Entry point: RagService.execute_pipeline(request). Responsibilities:
    - Generate embeddings for the user query (google.genai EmbedContent, task_type=RETRIEVAL_QUERY).
    - Retrieve neighbors from Matching Engine using Namespace filtering on chatbot_id for strict isolation.
    - Fetch raw chunk texts from GCS via the vector_id → blob path convention, after validating the vector_id prefix matches the chatbot_{id} namespace.
    - //Rerank with RankingService (Discovery Engine semantic-ranker-default-004) to compact the context window and improve ordering; on error/unavailability, preserve the original retrieval order.
    - Construct the prompt: include knowledge adherence level, strict “answer in the user’s language,” trimmed history (by char budget), and selected context.
    - Call Vertex AI GenerativeModel (Gemini) with safety settings; capture finish reason and safety blocks.
    - Return answer text, sources, and timing/usage metadata.
- Supporting methods (indicative): generate_multiple_embeddings, retrieve_chunks_multi_query, fetch_chunk_texts, construct_prompt, generate_response, multimodal_query.

Implementation notes:
- Vector IDs encode chatbot and source identity (chatbot_{chatbot_id}_source_{hash}_chunk_{index}); GCS paths mirror this, enabling direct fetch without extra DB lookups.
- History and context are bounded by MAX_HISTORY_CHARS and MAX_CONTEXT_CHARS to control latency and cost.
- UsageLog rows capture timings, token usage (when available), status codes, and errors keyed by a request_id.
 - Multimodal path: image-derived text may seed/refine the query; the original image is sent to the model only if no suitable textual context is found.


### 6.3 Ingestion, update, and deletion

- Ingestion tasks (Celery):
    - Accept URLs/files, parse and chunk content, embed chunks, upsert vectors to Matching Engine, and persist VectorIdMapping entries.
    - Emit progress states (Queued → Updating → Active) that the UI reads via SSE.
- Update: on content change, re‑ingest and remove stale vectors/mappings.
- Deletion:
    - Per‑source: remove vectors from Matching Engine and delete corresponding VectorIdMapping rows.
    - Full chatbot cleanup: remove vectors/mappings, chat messages, detailed feedback, and usage logs; reset chatbot status to Empty.

### 6.4 API surface (high level)

- Auth/session: login for admins; per‑chatbot API key for widget calls. For full request/response schemas, see Appendix B.
- Chatbot management: create/update/delete chatbot, manage sources, regenerate API key. Endpoint details are cataloged in Appendix B.
- Widget config: returns branding and feature toggles authorized by the chatbot API key (Appendix B).
- Feedback: thumbs and optional detailed feedback endpoints (Appendix B for payloads).
- Crawl/ingestion triggers: start discovery and ingestion jobs (async). See Appendix B for examples.
- Status: SSE endpoint streams chatbot status updates (Appendix B has the SSE event schema).
 - Voice: STT/TTS endpoints (see Appendix B for audio formats, payloads, and language codes).
 - Summarization: endpoints for summarize-by-URL and summarize-by-text (Appendix B for request/response and size limits).
 - Screenshot analysis: endpoint for image upload and analysis (Appendix B for image types, size limits, and OCR notes).

### 6.5 Authentication, authorization, and rate limiting

- API key flow: Authorization: Bearer <key> is required for widget endpoints; the backend verifies against a hashed key stored with the chatbot.
- Ownership checks: management endpoints validate client_id ownership.
- Rate limits: applied on sensitive endpoints (e.g., login, create/update, widget‑config, chat) to protect resources.

### 6.6 Data model snapshot (concise)

- Chatbot: id, client_id, api_key_hash, name, config (branding/toggles), status.
- VectorIdMapping: id, chatbot_id, vector_id, source_identifier, created_at.
- ChatMessage: id, chatbot_id, role (user/assistant), content, created_at; optional lang.
- DetailedFeedback: id, chatbot_id, message_id, rating, free‑text feedback, created_at.
- UsageLog: id, chatbot_id, action, request_id, duration_ms, status_code, token counts (if available), error, source_ids.
- User/Admin: basic auth fields and ownership over chatbots.

Note: The ER diagram in the Design chapter reflects these entities and their relations (see Section 4.2 and Appendix E).

### 6.7 Error handling and observability

- Structured logs include request_id and per‑step timings (embeddings, retrieval, fetch, rerank, generation).
- Safety and refusal cases return user‑friendly messages; details are logged but not exposed to end users.
- Telemetry is persisted to UsageLog for audits and quality analysis.

### 6.8 Configuration and clients

- For the full list of env vars and defaults, see Design Section 4.9. Notes:
    - Cloud SDK alignment: GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION set programmatically where needed (including workers).
    - Clients are initialized once in the RAG service (Vertex AI, google.genai, GCS) and reused across requests when possible.
    - Workers ensure GOOGLE_GENAI_USE_VERTEXAI=True so google.genai routes via Vertex AI.

### 6.9 Frontend integration

- Widget: sends chat requests with chatbot_id and Bearer API key; renders answer, sources, and handles safety/fallback messages; honors branding toggles.
- Admin SPA: manages chatbots/sources, starts ingestion, consumes SSE for status, and shows embed snippets and validation errors.

### 6.10 Agentic helper (brief)

- Note: The agentic retail demo is currently English‑only and separate from the WAS RAG chatbot. Roadmap: full multilingual voice support and optional integration points into WAS.

- Pattern: LLM + tools. The model chooses a tool, extracts parameters, calls it, observes results, and composes a reply.
- Implemented tools (indicative): list_products, get_product, add_to_cart, remove_from_cart, view_cart, checkout, identify_image.
- Guardrails: scope limited to declared tools; no autonomous actions beyond user‑initiated flows.

### 6.11 Results & Evaluation (תוצאות והערכה)

#### 6.11.1 Needle‑in‑a‑Haystack Retrieval

- Corpus: ~150 pages, with a single “needle” sentence embedded once.
- Queries: 10 natural‑language variants designed to elicit that specific sentence.
- Result: 10/10 successful retrievals (100%).
- Mode: standard RAG (advanced disabled for this run); reranker enabled.
- Why it matters: This stresses end‑to‑end recall under our current pipeline (chunking ≈800/80, per‑chatbot namespace isolation, retrieval → rerank). Consistent 100% indicates that top‑K retrieval plus reranking reliably surfaces the exact passage when the knowledge exists.
- Notes and risks:
    - Keep an eye on synonym and paraphrase drift; consider periodic adversarial rephrasings.
    - If corpus size grows substantially, revisit RAG_TOP_K and reranker budget to preserve recall without inflating latency.

#### 6.11.2 Standard Q&A (Specialized Domain)

- Set: 50 curated, domain‑specific questions (mix of single‑hop and light multi‑hop).
- Evaluation: Automatic semantic similarity grading by Gemini 2.5 Pro against expected answers.
- Result: ≈96% accuracy.
- Mode: standard RAG (advanced disabled for this run); reranker enabled; knowledge adherence set to strict.
- Interpretation: Most misses were near‑misses or phrasing‑granularity issues rather than outright wrong facts. Tightening the knowledge‑adherence prompt and enabling short clarification follow‑ups can reduce these cases.

#### 6.11.3 Reading these results

- Automatic graders are directional. For edge cases (ambiguous or list‑style answers), include human spot checks.
- Reported numbers use standard RAG; the experimental advanced pipeline underperformed in this deployment and was not used for these results.
- Reranker was enabled; if unavailable, the system preserves the original retrieval order as a fallback.
- Reproducibility tips: fix retrieval parameters (RAG_TOP_K, reranker on/off), keep context/history budgets constant, and re‑use the same seed/config when supported; record finish_reason and safety_ratings for runs to spot safety/refusal patterns.

#### 6.11.4 Next steps (lightweight)

- Automate a small regression suite (subset of the 50 Q&A + 2–3 haystack prompts) and log accuracy per commit.
- Track retrieval hit rate and answer accuracy over time in UsageLog; plot trends alongside P50/P95 latency.
- Expand with multilingual prompts to validate “answer in the user’s language.”
- Periodically re‑sweep RAG_TOP_K and reranker settings as the corpus grows.
- Track finish_reason distribution (STOP vs non‑STOP) and safety_ratings to monitor refusal/block rates.

## 7. Technical Details (פירוט טכני)

### 7.1 Data handling and preparation (RAG)

- Inputs: URLs, and uploaded files (.txt, .pdf, .docx). HTML is cleaned to text; files parsed via pdfminer/docx.
- Chunking: RecursiveCharacterTextSplitter size ≈ 800 chars with ≈ 80 overlap.
- Storage and mapping: Raw chunk texts are stored in GCS; deterministic vector IDs encode chatbot and source identity (chatbot_{chatbot_id}_source_{hash}_chunk_{index}). A VectorIdMapping row relates vector_id → source_identifier.

See Appendix C for the full storage layout and mapping conventions.

### 7.2 Model configuration & prompting

- Embeddings: google.genai models.embed_content with model EMBEDDING_MODEL_NAME; RETRIEVAL_QUERY for queries, RETRIEVAL_DOCUMENT for ingestion.
- Retrieval: Vertex AI Matching Engine with Namespace filtering by chatbot_id; top-K and fused chunk counts as configured.
- Reranking: Discovery Engine semantic-ranker-default-004 via RankingService; preserves reranked order; falls back to original retrieval order if unavailable.
- Prompt rules: knowledge adherence level and “respond in the user’s language.” History and context are budgeted by character limits.
- Generation: Vertex AI GenerativeModel with temperature and max tokens; safety settings enforced.
- Multimodal: optional image text extraction; resend of original image only when no suitable textual context is found.

Language and speech configuration:
- Language detection: lightweight LID used to set the target language; falls back to user hint or site default.
- Response language: prompts enforce “answer in the user’s language”; deterministic unless overridden by tenant policy.
- Speech settings: STT/TTS model, sample rate, and encoding configured per environment; see Appendix B/C for current values.

Summarization and screenshot analysis specifics:
- Summarization: concise instruction template; length budget configurable; language mirrors detected or hinted user language.
- URL mode: fetch → HTML clean → main‑content extraction → summarize.
- Paste mode: summarize raw text directly.
- Screenshot mode: OCR first; optional image captioning if OCR is sparse; extracted text seeds RAG or direct summarization.

See Appendix C for parameter names and defaults.

### 7.3 References

- API endpoints and schemas: Appendix B.
- RAG parameters, storage layout, rate limits, and environment details: Appendix C.
 - Architecture context: Section 4.2. Implementation internals: Section 6.

## 8. Summary and Future Extensions (סיכום והרחבות עתידיות)

### 8.1 Summary

Website AI Assistance (WAS) delivers a multi‑tenant, code‑grounded RAG chatbot with strict per‑chatbot isolation, robust ingestion, reranking, and safety controls. The system integrates with Vertex AI (LLMs + Matching Engine), stores chunk text in GCS, and exposes a clean API + widget. Recent evaluations indicate strong quality: 100% retrieval on a needle‑in‑a‑haystack test (10/10) and ≈96% accuracy on a 50‑question specialized Q&A set, with safety blocks negligible and STOP finishes typical. This establishes a solid baseline for moving beyond Q&A into task assistance.

Operational note: The experimental advanced RAG pipeline underperformed for this deployment; standard RAG remains the default and recommended mode. The Discovery Engine reranker is optional and, if unavailable, the system preserves the original retrieval order as a fallback.

### 8.2 Future extensions (high‑impact ideas)

One‑page roadmap (summary):
- Agentic integration into WAS: unify RAG + tools in a single session; per‑tenant toggles, quotas, and tool‑call audit logs.
- On‑page actions: safe form filling and guided overlays; limited browser automation via a sandbox (allow‑lists, rate limits, redaction, approvals).
- Personalization (opt‑in): consented user profiles; lightweight IdP/CRM connectors; segment‑aware retrieval and ABAC on sources.
- Retrieval quality: hybrid search (dense+BM25), metadata filters, dynamic chunking; cross‑lingual rerankers; targeted multi‑hop planning.
- Knowledge freshness: change detection, incremental re‑index, and automatic re‑ingestion for updated URLs.
- Evaluation & governance: continuous eval (gold + adversarial), grounding/citation checks, HITL for sensitive tools; policy controls for PII, consent, and retention.
- Voice & multimodal: streaming STT with barge‑in, faster TTS; image‑grounded Q&A/visual search; doc summarization with table/list extraction.
- Platform & cost: deep tracing and SLO dashboards; embedding cache, adaptive top‑K and reranker budgets; autoscaling workers; regional residency and CMEK.
- Analytics & content ops: question taxonomy and gap analysis; admin insights on failed intents, safety blocks, latency, and tool success.
- Phasing: Phase 1 (agent toggles + form‑fill POC + approvals UI), Phase 2 (sandboxed automation + hybrid retrieval + dashboards), Phase 3 (broader tool library + advanced personalization + mature governance).


## 9. Bibliography (ביבליוגרפיה)

Style: Numeric references [1], [2], … with full URLs (and DOI where available). Use [n] for in‑text citations at first mention of a method/component.

### 9.1 Academic and methods
1. Vaswani, A., Shazeer, N., Parmar, N., et al. "Attention Is All You Need." NeurIPS, 2017. https://arxiv.org/abs/1706.03762
2. Lewis, P., Perez, E., Piktus, A., et al. "Retrieval‑Augmented Generation for Knowledge‑Intensive NLP." NeurIPS, 2020. https://arxiv.org/abs/2005.11401
3. Yao, S., Zhao, J., Yu, D., et al. "ReAct: Synergizing Reasoning and Acting in Language Models." 2022. https://arxiv.org/abs/2210.03629
4. Li, M., Ma, X., Shen, D., et al. "SELF‑INSTRUCT: Aligning Language Models with Self‑Generated Instructions." 2023. https://arxiv.org/abs/2212.10560
5. Liu, J., Xu, W., Xie, S., et al. "Reranking for Retrieval‑Augmented Generation: A Survey." 2024. https://arxiv.org/abs/2402.11026

### 9.2 Cloud and model documentation
6. Google Cloud. "Generative AI on Vertex AI — Overview." https://cloud.google.com/vertex-ai/docs/generative-ai/learn/overview (accessed: 2025‑08‑10)
7. Google Cloud. "Vertex AI Matching Engine — Overview." https://cloud.google.com/vertex-ai/docs/matching-engine/overview (accessed: 2025‑08‑10)
8. Google for Developers. "Text embeddings API (gemini‑embedding‑001)." https://ai.google.dev/docs/embeddings_api (accessed: 2025‑08‑10)
9. Google Cloud. "Reranking for Vertex AI Search and Conversation." https://cloud.google.com/generative-ai-app-builder/docs/reranking (accessed: 2025‑08‑10)

### 9.3 Frameworks and libraries
10. Flask Documentation. "Flask." https://flask.palletsprojects.com/ (accessed: 2025‑08‑10)
11. SQLAlchemy Documentation. "SQLAlchemy." https://docs.sqlalchemy.org/ (accessed: 2025‑08‑10)
12. Celery Project. "Celery: Distributed Task Queue." https://docs.celeryq.dev/en/stable/ (accessed: 2025‑08‑10)
13. Redis. "Redis Documentation." https://redis.io/docs/ (accessed: 2025‑08‑10)
14. Beautiful Soup Documentation. "bs4." https://www.crummy.com/software/BeautifulSoup/bs4/doc/ (accessed: 2025‑08‑10)
15. MDN Web Docs. "Server‑Sent Events (EventSource)." https://developer.mozilla.org/docs/Web/API/Server-sent_events (accessed: 2025‑08‑10)

### 9.4 Datasets and benchmarks
16. Internal. "Needle‑in‑a‑Haystack test corpus and results (10/10)." Project artifact; see repository root: combined_haystack.txt (accessed: 2025‑08‑10)
17. Internal. "Specialized 50‑question Q&A set and Gemini‑graded results (≈96%)." Project artifact; stored with maintainers (accessed: 2025‑08‑10)

### 9.5 High‑quality articles (optional)
18. (Placeholder) Production RAG patterns on GCP/Vertex AI. Add final link if used.

Note: Compliance/accessibility references intentionally omitted for MVP scope per project guidelines.

### 9.6 Additional frameworks and tools (used in code)
19. LangChain. "Documentation." https://python.langchain.com/docs/ (accessed: 2025‑08‑10)
20. pdfminer.six. "Documentation." https://pdfminersix.readthedocs.io/ (accessed: 2025‑08‑10)
21. python‑docx. "Documentation." https://python-docx.readthedocs.io/ (accessed: 2025‑08‑10)
22. Pillow. "Pillow (PIL Fork) Documentation." https://pillow.readthedocs.io/ (accessed: 2025‑08‑10)
23. Alembic. "Alembic Documentation." https://alembic.sqlalchemy.org/ (accessed: 2025‑08‑10)

### 9.7 Competitor sources
24. WebAssistants.ai — Product site. https://webassistants.ai (accessed: 2025‑08‑11)
25. A‑Eye Web Chat Assistant — Chrome Web Store listing. https://chromewebstore.google.com/detail/a-eye-web-chat-assistant/cdjignhknhdkldbjijipaaamodpfjflp (accessed: 2025‑08‑11)
26. Salesloft Drift — Platform page. https://www.salesloft.com/platform/drift (accessed: 2025‑08‑11)

## 10. Appendices (נספחים)

Purpose: Provide implementation‑level details without bloating main chapters. No dependency/version dump per request.

### A. Prompting and templates
- See ./appendix/A-prompts-and-templates.md for the current system prompt, history preface, image prompts, and notes (supports 4.3, 4.5, 6.2).

### B. API contracts (schemas)
- See ./appendix/B-api-contracts.md for minimal request/response examples covering creation, widget config, voice interact, feedback, sources, discovery/crawl, and SSE schema (supports 4.1–4.2, 6.4).

### C. RAG configuration reference
- See ./appendix/C-rag-configuration.md for RAG/LLM parameters, retrieval filters, reranking, history budgets, and mapping conventions (supports 4.4, 4.9, 7.1–7.2, 6.2).

### D. Evaluation artifacts (internal)
- See ./appendix/D-evaluation-artifacts.md for the haystack recipe and 50‑QA set notes (supports 6.11.1–6.11.4).

### E. Architecture diagrams and data flows
- See ./appendix/E-architecture-diagrams.md for diagram links and captions (supports 4.2). Place exported images under ./images.

### F. Runbook and troubleshooting
- See ./appendix/F-runbook-troubleshooting.md for quick fixes to common MVP issues (supports 4.7, 4.10, 6.7).

