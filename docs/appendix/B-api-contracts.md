# Appendix B: API contracts (schemas)

Purpose: Minimal, copy-pasteable request/response examples derived from the backend.

Auth
- Most /api/chatbots/* routes that serve the widget use API key auth: Authorization: Bearer <api_key>

## B.1 Create chatbot
POST /api/chatbots
Body (JSON or multipart form fields):
{
  "client_id": "<string>",
  "name": "<string>",
  "useUrlSource": true,
  "sourceValueUrl": "https://example.com",
  "useSitemapSource": false,
  "sourceValueSitemap": "",
  "useFiles": false,
  "selected_urls": ["https://example.com/page1"],
  "widget_primary_color": "#0ea5e9",
  "widget_text_color": "#ffffff",
  "widget_welcome_message": "Hi!",
  "advanced_rag_enabled": false
}
Response 202:
{
  "message": "Chatbot creation initiated.",
  "chatbot_id": 123,
  "status": "Queued",
  "api_key": "<plaintext_api_key>",
  "embed_script": "<script ...>"
}

Errors:
- 400: { "error": "client_id is required" } (or missing/invalid fields)
- 404: { "error": "Invalid client_id" }
- 400: { "error": "Maximum chatbots (3) reached." }
- 500: { "error": "Failed configuration save or processing start" }

## B.2 Widget config (requires API key)
GET /api/chatbots/{chatbot_id}/widget-config
Headers: Authorization: Bearer <api_key>
Response 200 (excerpt):
{
  "chatbot_id": 123,
  "name": "StoreBot",
  "primary_color": "#0ea5e9",
  "welcome_message": "Hi!",
  "voice_enabled": false,
  "text_chat_enabled": true,
  "file_uploads_enabled": false,
  "feedback_thumbs_enabled": true,
  "detailed_feedback_enabled": false,
  "consent_message": null,
  "consent_required": false
}

Errors:
- 401: { "error": "Missing API key" }
- 404: { "error": "Chatbot not found" }
- 403: { "error": "Invalid or unauthorized API key" }

## B.3 Chat (text) — via RAG pipeline
POST /api/voice/chatbots/{chatbot_id}/interact (voice)
- For pure text chat, your frontend calls the RAG pipeline through non-voice route; in this repo, the concrete POST text endpoint is implemented for voice flow with STT/TTS. The RAG core contract is reflected in its output.
Form fields:
- audio: file (mp3/wav), language: "en"|"fr"|"ar"|... , session_id: "<string>"
Headers: Authorization: Bearer <api_key>
Response 200 (success):
{
  "text_response": "<assistant_answer>",
  "audio_response_base64": "<base64 or null>",
  "transcribed_input": "<stt_text>"
}
Errors:
- 400: { "error": "Missing 'language' form field." } (or session_id/audio issues)
- 403: { "error": "Voice interaction is not enabled for this chatbot." }
- 500: { "error": "An internal server error occurred during voice interaction." }

## B.4 Feedback
POST /api/messages/{message_id}/feedback
Headers: Authorization: Bearer <api_key>
Body:
{ "feedback_type": "positive" | "negative" }
Response 200:
{ "message": "Feedback recorded successfully" }
Errors:
- 400: { "error": "Missing 'feedback_type' in request body (expecting 'positive' or 'negative')" }
- 404: { "error": "Message not found" }
- 403: { "error": "Forbidden: Message does not belong to this chatbot" } or { "error": "Feedback is disabled for this chatbot" }

POST /api/feedback/detailed
Headers: Authorization: Bearer <api_key>
Body:
{ "message_id": 1, "feedback_text": "...", "session_id": "abc" }
Response 201:
{ "message": "Detailed feedback saved successfully" }
Errors:
- 400: { "error": "Missing JSON request body" } (or missing fields)
- 404: { "error": "Message not found" }
- 403: { "error": "Detailed feedback is disabled for this chatbot" }
- 409: { "error": "Detailed feedback already submitted for this message" }

## B.5 Sources management
POST /api/chatbots/{chatbot_id}/sources/files
- multipart/form-data with files[]
Response 202:
{ "message": "<n> file(s) added and ingestion started.", "task_id": "..." }
Errors:
- 400: { "error": "No files selected" } or { "error": "File type not allowed: ..." }
- 500: { "error": "Could not save file <name>" } or { "error": "Failed to add file sources" }

POST /api/chatbots/{chatbot_id}/sources/url
Body: { "url": "https://example.com/page" }
Response 202: { "message": "URL source added and ingestion started.", "task_id": "..." }
Errors:
- 400: { "error": "Missing 'url' in request body" }
- 500: { "error": "Failed to add URL source" }

DELETE /api/chatbots/{chatbot_id}/sources
Headers: Authorization: Bearer <api_key>
Body: { "source_identifier": "file://..." | "https://..." }
Response 202: { "message": "Source deletion process initiated", "task_id": "..." }
Errors:
- 400: { "error": "Request body must be JSON" } or { "error": "Missing or invalid 'source_identifier' in request body" }
- 500: { "error": "Failed to start source deletion process" }

## B.6 Discovery/crawl
POST /api/discover-links
Body: { "source_url": "https://example.com", "source_type": "url" | "sitemap" }
GET /api/discover-links/{task_id}
Responses:
- 200: { "task_id": "...", "status": "SUCCESS|FAILURE", "result": {...} | null }
- 202: { "task_id": "...", "status": "PENDING|STARTED|RETRY", "result": null }
- 200 (failure payload): { "task_id": "...", "status": "FAILURE", "result": { "error": "...", "traceback": "..." } }

POST /api/chatbots/{chatbot_id}/crawl/start
Body: { "start_url": "https://example.com" }
GET /api/chatbots/{chatbot_id}/crawl/status/{task_id}

## B.7 Status stream (SSE)
GET /api/chatbots/status-stream?clientId=<client_id>
Event data schema:
{ "chatbot_id": 123, "status": "Queued|Updating|...", "client_id": "<client_id>" }
Notes: Connection headers include Content-Type: text/event-stream; keep-alive; CORS: Access-Control-Allow-Origin: * (dev).
