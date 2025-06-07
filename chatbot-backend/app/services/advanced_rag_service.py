# chatbot-backend/app/services/advanced_rag_service.py
import logging
import re
import time # Ensure time is imported
import json
from typing import List, Tuple, Any, Dict, TYPE_CHECKING
from flask import current_app
from collections import defaultdict # Add this import
from google.api_core.exceptions import GoogleAPICallError, RetryError, DeadlineExceeded # Added specific API errors
from sqlalchemy.exc import SQLAlchemyError # Added for DB error handling
from cachetools import LFUCache, TTLCache # Added for BM25 caching

# --- Service Dependencies ---
if TYPE_CHECKING:
    from .rag_service import RAGService
# Updated import to include VectorIdMapping
from app.models import Chatbot, db, VectorIdMapping # Ensure db is imported
from sqlalchemy.orm import Session # Added Session for type hinting if needed
from rank_bm25 import BM25Okapi # Added for Hybrid Search
from sentence_transformers import CrossEncoder # Added for re-ranking

# --- LLM Interaction ---
import vertexai
from vertexai.generative_models import GenerativeModel, GenerationConfig, Part
from google.cloud.aiplatform_v1.types import HarmCategory, SafetySetting

# Configure logging
logger = logging.getLogger(__name__)

# --- Default Safety Settings (used if not found in config) ---
DEFAULT_QUERY_REPHRASING_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: SafetySetting.HarmBlockThreshold.BLOCK_MEDIUM_AND_ABOVE,
}

DEFAULT_RELAXED_JSON_SAFETY_SETTINGS = {
    HarmCategory.HARM_CATEGORY_HARASSMENT: SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_HATE_SPEECH: SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: SafetySetting.HarmBlockThreshold.BLOCK_ONLY_HIGH,
}

bm25_cache = TTLCache(maxsize=100, ttl=3600)

class AdvancedRagProcessor:
    def __init__(self):
        logger.info("Initializing AdvancedRagProcessor and loading models...")
        start_time = time.time()
        self.rephrasing_llm = None
        self.final_llm = None
        self.cross_encoder = None
        self.cross_encoder_model_name = None

        try:
            rephrasing_model_name = current_app.config.get('QUERY_REPHRASING_MODEL_NAME', "gemini-2.5-flash-preview-04-17")
            final_response_model_name = current_app.config.get('FINAL_RESPONSE_MODEL_NAME', "gemini-2.5-flash-preview-04-17")

            self.rephrasing_llm = GenerativeModel(rephrasing_model_name)
            self.final_llm = GenerativeModel(final_response_model_name)
            logger.info(f"Using Rephrasing LLM: {rephrasing_model_name}")
            logger.info(f"Using Final Response LLM: {final_response_model_name}")

            self.cross_encoder_model_name = current_app.config.get('CROSS_ENCODER_MODEL_NAME', 'cross-encoder/ms-marco-MiniLM-L6-v2')
            cross_encoder_max_length = current_app.config.get('CROSS_ENCODER_MAX_LENGTH', 1000)
            self.cross_encoder = CrossEncoder(self.cross_encoder_model_name, max_length=cross_encoder_max_length)
            logger.info(f"Successfully loaded CrossEncoder model: {self.cross_encoder_model_name} with max_length={cross_encoder_max_length}")

            logger.info(f"All models initialized in {time.time() - start_time:.2f}s.")

        except Exception as e:
            logger.error(f"FATAL: Failed to initialize models in AdvancedRagProcessor: {e}", exc_info=True)
            if not self.rephrasing_llm: logger.error("Rephrasing LLM failed to initialize.")
            if not self.final_llm: logger.error("Final LLM failed to initialize.")
            if not self.cross_encoder: logger.error(f"CrossEncoder model '{self.cross_encoder_model_name or 'N/A'}' failed to initialize.")
            raise RuntimeError("Failed to initialize one or more core models for Advanced RAG.") from e

    def _estimate_token_count(self, text: str) -> int:
        if not self.rephrasing_llm:
            logger.warning("Rephrasing LLM not available for token counting. Falling back to approximation.")
            return len(text) // 4
        try:
            response = self.rephrasing_llm.count_tokens(contents=[text])
            if response and hasattr(response, 'total_tokens'):
                 logger.debug(f"Counted tokens for text (first 50 chars: '{text[:50]}...'): {response.total_tokens}")
                 return response.total_tokens
            else:
                 logger.warning(f"count_tokens response invalid: {response}. Falling back to approximation.")
                 return len(text) // 4
        except Exception as e:
            logger.error(f"Error calling count_tokens: {e}. Falling back to approximation.", exc_info=True)
            return len(text) // 4

    def _compress_context(self, context_string: str, target_token_limit: int, original_query: str) -> str:
        estimated_tokens = self._estimate_token_count(context_string)
        logger.info(f"Estimated tokens in context before compression: {estimated_tokens}")
        config_target_token_limit = current_app.config.get('CONTEXT_COMPRESSION_TARGET_TOKENS', 4000)

        if estimated_tokens <= config_target_token_limit:
            logger.info("Context is within token limit, no compression needed.")
            return context_string

        if not self.final_llm:
            logger.error("Compression LLM (final_llm) not initialized. Falling back to truncation.")
            fallback_chars = int(config_target_token_limit * current_app.config.get('CONTEXT_TRUNCATION_CHAR_MULTIPLIER', 5))
            return context_string[:fallback_chars]

        logger.info(f"Context exceeds limit ({estimated_tokens} > {config_target_token_limit}). Attempting compression...")
        start_time = time.time()
        prompt = f"""The following context has been retrieved to answer the query: "{original_query}"

Context:
---
{context_string}
---

The context is too long ({estimated_tokens} estimated tokens) and needs to be summarized to fit within approximately {config_target_token_limit} tokens.
Please summarize the context concisely, focusing *only* on the information most relevant to answering the original query: "{original_query}".
Preserve key details and source references (like "[Source X: ...]") if possible within the summary.
Output *only* the summarized context.
"""
        try:
            compression_temp = current_app.config.get('CONTEXT_COMPRESSION_TEMPERATURE', 0.3)
            compression_token_buffer = current_app.config.get('CONTEXT_COMPRESSION_TOKEN_BUFFER', 500)
            compression_max_tokens = config_target_token_limit + compression_token_buffer
            compression_safety_settings = current_app.config.get('FINAL_RESPONSE_SAFETY_SETTINGS', DEFAULT_QUERY_REPHRASING_SAFETY_SETTINGS)
            generation_config = GenerationConfig(temperature=compression_temp, max_output_tokens=compression_max_tokens)
            response = self.final_llm.generate_content(contents=[prompt], generation_config=generation_config, safety_settings=compression_safety_settings, stream=False)

            if response and response.candidates and response.candidates[0].content.parts:
                summarized_context = response.candidates[0].content.parts[0].text
                summarized_tokens = self._estimate_token_count(summarized_context)
                logger.info(f"Context compressed successfully in {time.time() - start_time:.2f}s. New estimated tokens: {summarized_tokens}")
                return summarized_context
            else:
                logger.warning(f"LLM response for context compression was empty or invalid. Falling back to truncation. Response: {response}")
                fallback_chars = int(config_target_token_limit * current_app.config.get('CONTEXT_TRUNCATION_CHAR_MULTIPLIER', 5))
                return context_string[:fallback_chars]
        except (GoogleAPICallError, RetryError, DeadlineExceeded) as e:
             logger.error(f"API Error during context compression LLM call: {e}", exc_info=True)
             fallback_chars = int(config_target_token_limit * current_app.config.get('CONTEXT_TRUNCATION_CHAR_MULTIPLIER', 5))
             return context_string[:fallback_chars]
        except Exception as e:
            logger.error(f"Unexpected error during context compression LLM call: {e}", exc_info=True)
            fallback_chars = int(config_target_token_limit * current_app.config.get('CONTEXT_TRUNCATION_CHAR_MULTIPLIER', 5))
            return context_string[:fallback_chars]

    def _format_context(self, chunks: List[Dict]) -> str:
        formatted_context = ""
        if not chunks: return "No context available."
        for i, chunk in enumerate(chunks):
            text = chunk.get('text', 'Missing text')
            metadata = chunk.get('metadata', {})
            source = metadata.get('source', 'Unknown source')
            source_str = str(source) if source is not None else 'Unknown source'
            formatted_context += f"[Source {i+1}: {source_str}]\n{text}\n---\n"
        return formatted_context.strip()

    def _generate_query_variations(self, original_query: str, chat_history: list) -> list[str]:
        start_time = time.time()
        logger.info(f"Generating query variations for: '{original_query[:100]}...'")
        if not self.rephrasing_llm:
            logger.error("Rephrasing LLM not initialized. Falling back to original query.")
            return [original_query]
        formatted_history = "\n".join([f"{turn['role']}: {turn['content']}" for turn in chat_history])
        prompt = f"""Given the following chat history and the latest user query, generate 3-5 diverse rephrasings or expansions of the original query. Focus on capturing different facets or underlying intents of the query, considering the conversation context. Output *only* the rephrased queries, each on a new line, without any preamble or numbering.
Include the original query itself in the output list.

Chat History:
---
{formatted_history}
---

Original Query: "{original_query}"

Rephrased Queries (including original):"""
        try:
            rephrasing_temp = current_app.config.get('QUERY_REPHRASING_TEMPERATURE', 0.7)
            rephrasing_max_tokens = current_app.config.get('QUERY_REPHRASING_MAX_TOKENS', 150)
            rephrasing_safety_settings = current_app.config.get('QUERY_REPHRASING_SAFETY_SETTINGS', DEFAULT_QUERY_REPHRASING_SAFETY_SETTINGS)
            generation_config = GenerationConfig(temperature=rephrasing_temp, max_output_tokens=rephrasing_max_tokens)
            response = self.rephrasing_llm.generate_content(contents=[prompt], generation_config=generation_config, safety_settings=rephrasing_safety_settings, stream=False)
            if response and response.candidates and response.candidates[0].content.parts:
                generated_text = response.candidates[0].content.parts[0].text
                variations = [q.strip() for q in generated_text.split('\n') if q.strip()]
                if original_query not in variations: variations.insert(0, original_query)
                logger.info(f"Generated {len(variations)} query variations in {time.time() - start_time:.2f}s.")
                return variations
            else:
                logger.warning(f"LLM response for query rephrasing was empty or invalid. Response: {response}")
                return [original_query]
        except (GoogleAPICallError, RetryError, DeadlineExceeded) as e:
             logger.error(f"API Error generating query variations: {e}", exc_info=True)
             return [original_query]
        except Exception as e:
            logger.error(f"Unexpected error generating query variations: {e}", exc_info=True)
            return [original_query]

    def _rerank_chunks(self, original_query: str, chunks: List[Dict]) -> List[Dict]:
        logger.info(f"Starting re-ranking for {len(chunks)} chunks...")
        start_time = time.time()
        if not chunks:
            logger.info("No chunks to re-rank.")
            return []
        if self.cross_encoder is None:
            model_name_for_warning = self.cross_encoder_model_name or 'default (config access failed or init failed)'
            logger.warning(f"CrossEncoder model '{model_name_for_warning}' not loaded/initialized. Skipping re-ranking.")
            return chunks
        try:
            model_input = [(original_query, chunk.get('text', '')) for chunk in chunks]
            scores = self.cross_encoder.predict(model_input, show_progress_bar=False)
            chunks_with_scores = list(zip(scores, chunks))
            sorted_chunks_with_scores = sorted(chunks_with_scores, key=lambda x: x[0], reverse=True)
            reranked_chunks = [chunk for score, chunk in sorted_chunks_with_scores]
            duration = time.time() - start_time
            logger.info(f"CrossEncoder re-ranking finished in {duration:.2f}s. Resulting chunks: {len(reranked_chunks)}")
            return reranked_chunks
        except Exception as e:
            logger.error(f"Error during CrossEncoder prediction/re-ranking: {e}", exc_info=True)
            return chunks

    def _clean_json_string(self, raw_string: str) -> str:
        if not isinstance(raw_string, str): return ""
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", raw_string, re.DOTALL | re.IGNORECASE)
        cleaned = match.group(1) if match else raw_string
        return cleaned.strip()

    def _call_llm_with_retry_and_parse_json(self, model: GenerativeModel, prompt: str, generation_config: GenerationConfig, safety_settings: dict, expected_keys: list = None, expected_types: dict = None, max_retries: int = None, retry_delay: int = None, fallback_value: Any = None) -> Any:
        config_max_retries = current_app.config.get('LLM_JSON_MAX_RETRIES', 2) if max_retries is None else max_retries
        config_retry_delay = current_app.config.get('LLM_JSON_RETRY_DELAY', 1) if retry_delay is None else retry_delay
        if not model:
             logger.error(f"LLM model provided to _call_llm_with_retry_and_parse_json is None. Cannot proceed.")
             return fallback_value
        attempts = 0
        last_exception = None
        while attempts <= config_max_retries:
            attempts += 1
            try:
                logger.debug(f"LLM JSON Call Attempt {attempts}/{config_max_retries + 1}")
                response = model.generate_content(contents=[prompt], generation_config=generation_config, safety_settings=safety_settings, stream=False)
                if not (response and response.candidates and response.candidates[0].content.parts):
                    logger.warning(f"LLM response was empty or invalid structure on attempt {attempts}. Response: {response}")
                    last_exception = ValueError("LLM response empty or invalid structure")
                    if attempts <= config_max_retries: time.sleep(config_retry_delay)
                    continue
                raw_text = response.candidates[0].content.parts[0].text
                cleaned_text = self._clean_json_string(raw_text)
                if not cleaned_text:
                     logger.warning(f"LLM response was empty after cleaning on attempt {attempts}. Raw: '{raw_text}'")
                     last_exception = ValueError("LLM response empty after cleaning")
                     if attempts <= config_max_retries: time.sleep(config_retry_delay)
                     continue
                try:
                    parsed_json = json.loads(cleaned_text)
                    if expected_keys and not all(key in parsed_json for key in expected_keys):
                        missing_keys = [k for k in expected_keys if k not in parsed_json]
                        logger.warning(f"Parsed JSON missing expected keys: {missing_keys} on attempt {attempts}. JSON: {parsed_json}")
                        last_exception = ValueError(f"Parsed JSON missing expected keys: {missing_keys}")
                        if attempts <= config_max_retries: time.sleep(config_retry_delay)
                        continue
                    if expected_types:
                        type_errors = [f"Key '{key}' expected type {expected_type}, got {type(parsed_json[key])}" for key, expected_type in expected_types.items() if key in parsed_json and not isinstance(parsed_json[key], expected_type)]
                        if type_errors:
                             logger.warning(f"Parsed JSON type validation failed: {type_errors} on attempt {attempts}. JSON: {parsed_json}")
                             last_exception = TypeError(f"Parsed JSON type validation failed: {'; '.join(type_errors)}")
                             if attempts <= config_max_retries: time.sleep(config_retry_delay)
                             continue
                    logger.debug(f"LLM JSON call successful on attempt {attempts}.")
                    return parsed_json
                except json.JSONDecodeError as e:
                    logger.warning(f"JSONDecodeError on attempt {attempts}: {e}. Cleaned text: '{cleaned_text}'")
                    last_exception = e
                    if attempts <= config_max_retries: time.sleep(config_retry_delay)
            except (GoogleAPICallError, RetryError, DeadlineExceeded) as e:
                logger.warning(f"API Error on LLM JSON call attempt {attempts}: {type(e).__name__} - {e}")
                last_exception = e
                if attempts <= config_max_retries:
                    logger.info(f"Retrying in {config_retry_delay}s...")
                    time.sleep(config_retry_delay)
            except Exception as e:
                logger.error(f"Unexpected error during LLM JSON call attempt {attempts}: {e}", exc_info=True)
                last_exception = e
                break
        logger.error(f"LLM JSON call failed after {attempts} attempts. Last exception: {last_exception}")
        return fallback_value

    def _decompose_query(self, original_query: str, chat_history: list) -> list[str]:
        start_time = time.time()
        logger.info("Decomposing query...")
        if not self.rephrasing_llm:
            logger.error("Decomposition LLM (rephrasing_llm) not initialized. Falling back to original query.")
            return [original_query]
        formatted_history = "\n".join([f"{turn['role']}: {turn['content']}" for turn in chat_history])
        prompt = f"""Analyze the 'Original Query' in the context of the 'Chat History'.
Break it down into one or more simpler, self-contained sub-questions that can be answered independently to fully address the original query.
If the original query is already simple and self-contained, just return the original query as a single item in the list.

Output the results as a JSON list of strings. Example: ["sub-question 1", "sub-question 2"] or ["original query"]

Chat History:
---
{formatted_history}
---

Original Query: "{original_query}"

JSON Output:"""
        decomp_temp = current_app.config.get('QUERY_DECOMPOSITION_TEMPERATURE', 0.7)
        decomp_max_tokens = current_app.config.get('QUERY_DECOMPOSITION_MAX_TOKENS', 150)
        decomp_safety_settings = current_app.config.get('RELAXED_JSON_SAFETY_SETTINGS', DEFAULT_RELAXED_JSON_SAFETY_SETTINGS)
        generation_config = GenerationConfig(temperature=decomp_temp, max_output_tokens=decomp_max_tokens, response_mime_type="application/json")
        parsed_result = self._call_llm_with_retry_and_parse_json(model=self.rephrasing_llm, prompt=prompt, generation_config=generation_config, safety_settings=decomp_safety_settings, fallback_value=None)
        if isinstance(parsed_result, list) and all(isinstance(q, str) for q in parsed_result) and parsed_result:
            logger.info(f"Decomposed query into {len(parsed_result)} sub-questions in {time.time() - start_time:.2f}s.")
            return parsed_result
        else:
            logger.warning(f"Decomposition failed or returned invalid structure after retries. Result: {parsed_result}. Falling back to original query.")
            return [original_query]

    def _recognize_intent_and_slots(self, query: str, chat_history: list) -> dict:
        start_time = time.time()
        logger.info("Recognizing intent and slots...")
        if not self.rephrasing_llm:
            logger.error("Intent/Slot LLM (rephrasing_llm) not initialized. Returning empty dict.")
            return {"intent": "error", "slots": {}}
        formatted_history = "\n".join([f"{turn['role']}: {turn['content']}" for turn in chat_history])
        prompt = f"""Analyze the 'Original Query' in the context of the 'Chat History'.
Identify the primary user intent (e.g., 'information_seeking', 'comparison', 'greeting', 'request_action', 'clarification', 'other').
Extract key named entities or slots relevant to the query (e.g., product names, features, locations, dates).

Output the results as a single JSON object with two keys: "intent" (string) and "slots" (object).
Example: {{"intent": "comparison", "slots": {{"product_a": "XYZ", "product_b": "ABC", "feature": "battery life"}}}}
If no specific slots are identified, return an empty object for "slots": {{"intent": "greeting", "slots": {{}}}}

Chat History:
---
{formatted_history}
---

Original Query: "{query}"

JSON Output:"""
        intent_temp = current_app.config.get('INTENT_SLOT_TEMPERATURE', 0.2)
        intent_max_tokens = current_app.config.get('INTENT_SLOT_MAX_TOKENS', 200)
        intent_safety_settings = current_app.config.get('RELAXED_JSON_SAFETY_SETTINGS', DEFAULT_RELAXED_JSON_SAFETY_SETTINGS)
        generation_config = GenerationConfig(temperature=intent_temp, max_output_tokens=intent_max_tokens, response_mime_type="application/json")
        expected_keys = ["intent", "slots"]
        expected_types = {"intent": str, "slots": dict}
        fallback = {"intent": "unknown", "slots": {}}
        parsed_result = self._call_llm_with_retry_and_parse_json(model=self.rephrasing_llm, prompt=prompt, generation_config=generation_config, safety_settings=intent_safety_settings, expected_keys=expected_keys, expected_types=expected_types, fallback_value=fallback)
        logger.info(f"Intent/Slot recognition finished in {time.time() - start_time:.2f}s. Result: {parsed_result}")
        return parsed_result

    def _analyze_retrieval_and_generate_followups(self, original_query: str, sub_questions: list, retrieved_chunks: List[Dict]) -> dict:
        start_time = time.time()
        logger.info("Analyzing retrieval sufficiency and generating follow-ups...")
        if not self.rephrasing_llm:
            logger.error("Analysis/Followup LLM (rephrasing_llm) not initialized. Returning default insufficient.")
            return {"sufficient": False, "follow_ups": []}
        context_preview = "\n---\n".join([chunk.get('text', '')[:200] + "..." for chunk in retrieved_chunks[:3]])
        sub_questions_str = "\n".join([f"- {q}" for q in sub_questions])
        prompt = f"""Given the original user query, the sub-questions derived from it, and a preview of the retrieved context, analyze if the context likely contains enough information to fully answer *all* the sub-questions.
Then, generate 1-3 potential follow-up questions the user might ask next, based on the original query and the provided context. If unsure, provide an empty list.

Original Query: "{original_query}"

Sub-questions derived:
{sub_questions_str}

Retrieved Context Preview:
---
{context_preview}
---

Analysis Task:
1. Sufficiency: Based *only* on the preview, is it likely the full retrieved context can answer *all* the sub-questions? Answer true or false.
2. Follow-up Questions: Generate 1-3 concise follow-up questions a user might ask next, related to the original query or the provided context. If unsure, provide an empty list.

Output the results as a single JSON object with two keys: "sufficient" (boolean) and "follow_ups" (list of strings).
Example: {{"sufficient": true, "follow_ups": ["What are the side effects?", "How does it compare to product Y?"]}}
"""
        followup_temp = current_app.config.get('FOLLOWUP_TEMPERATURE', 0.6)
        followup_max_tokens = current_app.config.get('FOLLOWUP_MAX_TOKENS', 300)
        followup_safety_settings = current_app.config.get('RELAXED_JSON_SAFETY_SETTINGS', DEFAULT_RELAXED_JSON_SAFETY_SETTINGS)
        generation_config = GenerationConfig(temperature=followup_temp, max_output_tokens=followup_max_tokens, response_mime_type="application/json")
        expected_keys = ["sufficient", "follow_ups"]
        expected_types = {"sufficient": bool, "follow_ups": list}
        fallback = {"sufficient": False, "follow_ups": []}
        parsed_result = self._call_llm_with_retry_and_parse_json(model=self.rephrasing_llm, prompt=prompt, generation_config=generation_config, safety_settings=followup_safety_settings, expected_keys=expected_keys, expected_types=expected_types, fallback_value=fallback)
        if not isinstance(parsed_result.get("follow_ups"), list) or not all(isinstance(q, str) for q in parsed_result.get("follow_ups", [])):
             logger.warning(f"Follow-up questions list is not valid: {parsed_result.get('follow_ups')}. Resetting to empty list.")
             parsed_result["follow_ups"] = []
        logger.info(f"Retrieval analysis/follow-up generation finished in {time.time() - start_time:.2f}s. Result: {parsed_result}")
        return parsed_result

def process_advanced_query(query: str, chat_history: list, chatbot_id: int, session_id: str, rag_service_instance: 'RAGService', image_data: bytes = None, image_mime_type: str = None):
    start_pipeline_time = time.time()
    current_logger = current_app.logger if current_app else logger
    current_logger.info(f"ADV_RAG: Starting advanced RAG pipeline for chatbot {chatbot_id}, session {session_id}. Query: '{query[:100]}...'")

    try:
        try:
            processor = AdvancedRagProcessor()
        except Exception as e:
            current_logger.error(f"ADV_RAG: Failed to instantiate AdvancedRagProcessor: {e}", exc_info=True)
            return ("Sorry, I encountered an internal error (Processor Init).", [], None, "Failed to initialize RAG processor.", 500, {})

        if not processor.rephrasing_llm or not processor.final_llm:
            current_logger.error("ADV_RAG: LLM models were not initialized correctly within AdvancedRagProcessor.")
            return ("Sorry, I encountered an internal error (LLM Init).", [], None, "Failed to initialize necessary LLM models.", 500, {})

        chatbot = db.session.get(Chatbot, chatbot_id)
        if not chatbot:
            current_logger.error(f"ADV_RAG: Chatbot with ID {chatbot_id} not found.")
            return ("Error: Chatbot configuration not found.", [], None, "Chatbot not found.", 404, {})

        current_logger.info("--- ADV_RAG Step 1: Query Understanding ---")
        intent_slots = processor._recognize_intent_and_slots(query, chat_history)
        current_logger.info(f"ADV_RAG Recognized Intent: {intent_slots.get('intent', 'N/A')}, Slots: {intent_slots.get('slots', {})}")
        sub_questions = processor._decompose_query(query, chat_history)
        current_logger.info(f"ADV_RAG Decomposed into Sub-questions: {sub_questions}")

        current_logger.info("--- ADV_RAG Step 2: Multi-Step Retrieval ---")
        # removed fetched_texts_dict initialization here as it was tied to BM25 only
        bm25 = None
        corpus_chunk_ids_for_bm25 = [] # Renamed to clarify its purpose
        cache_key = f"bm25_index_{chatbot_id}"

        if cache_key in bm25_cache:
            try:
                bm25, corpus_chunk_ids_for_bm25 = bm25_cache[cache_key]
                current_logger.info(f"ADV_RAG: BM25 index found in cache for chatbot {chatbot_id}. Using cached index with {len(corpus_chunk_ids_for_bm25)} documents.")
                # We don't need to pre-fetch texts for cached BM25 here if BM25Okapi doesn't require them for scoring.
                # Texts will be fetched on-demand for selected RRF chunks.
            except Exception as e:
                current_logger.error(f"ADV_RAG: Error retrieving BM25 from cache: {e}. Will attempt rebuild.", exc_info=True)
                bm25 = None; corpus_chunk_ids_for_bm25 = []
                if cache_key in bm25_cache: del bm25_cache[cache_key]
        
        if bm25 is None:
            current_logger.info(f"ADV_RAG: BM25 index not in cache for chatbot {chatbot_id}. Attempting to build...")
            try:
                # Fetch ALL vector IDs associated with the chatbot to build a comprehensive BM25 index
                all_chatbot_vector_ids = [m.vector_id for m in db.session.query(VectorIdMapping.vector_id).filter_by(chatbot_id=chatbot_id).all() if m.vector_id]
                
                if all_chatbot_vector_ids:
                    current_logger.info(f"ADV_RAG: Found {len(all_chatbot_vector_ids)} vector IDs for chatbot {chatbot_id} for BM25 index build.")
                    
                    # Fetch texts for these IDs to build the BM25 index
                    # This fetch_chunk_texts is for BM25 corpus creation, not for RRF results later.
                    bm25_corpus_texts_list, fetch_err = rag_service_instance.fetch_chunk_texts(all_chatbot_vector_ids, chatbot_id)
                    
                    if fetch_err:
                        current_logger.warning(f"ADV_RAG: Error fetching some texts for BM25 build: {fetch_err}")
                    
                    valid_texts_for_bm25 = []
                    valid_ids_for_bm25_corpus = []

                    if isinstance(bm25_corpus_texts_list, list) and len(bm25_corpus_texts_list) == len(all_chatbot_vector_ids):
                        for i, text_content in enumerate(bm25_corpus_texts_list):
                            if text_content: # Ensure text is not None or empty
                                valid_texts_for_bm25.append(text_content)
                                valid_ids_for_bm25_corpus.append(all_chatbot_vector_ids[i])
                            else:
                                current_logger.debug(f"ADV_RAG: Skipping vector ID {all_chatbot_vector_ids[i]} for BM25 due to empty text.")
                        
                        if valid_texts_for_bm25:
                            current_logger.info(f"ADV_RAG: Building BM25 index with {len(valid_texts_for_bm25)} documents.")
                            tokenized_corpus = [doc.split(" ") for doc in valid_texts_for_bm25]
                            bm25 = BM25Okapi(tokenized_corpus)
                            corpus_chunk_ids_for_bm25 = valid_ids_for_bm25_corpus # Store the IDs corresponding to the BM25 corpus order
                            current_logger.info(f"ADV_RAG: BM25 index built successfully. Caching...")
                            bm25_cache[cache_key] = (bm25, corpus_chunk_ids_for_bm25)
                        else:
                            current_logger.warning("ADV_RAG: No valid text found after filtering fetched texts for BM25 index build.")
                    else:
                        current_logger.warning(f"ADV_RAG: Mismatch or error fetching texts for BM25 build. Fetched count/type issue. Skipping BM25.")
                else:
                    current_logger.warning(f"ADV_RAG: No VectorIdMappings found for chatbot {chatbot_id}. Skipping BM25 build.")
            except Exception as e:
                current_logger.error(f"ADV_RAG: Error preparing BM25 index: {e}", exc_info=True)


        all_retrieved_chunk_ids_set = set() # Changed name for clarity
        all_retrieved_chunks_list = [] # Changed name for clarity
        analysis_result = {"sufficient": False, "follow_ups": []}
        max_retrieval_steps = current_app.config.get('MAX_RETRIEVAL_STEPS', 3)
        variation_processing_limit = current_app.config.get('VARIATION_PROCESSING_LIMIT', 10)
        processed_count = 0 # Moved initialization here

        for current_step in range(max_retrieval_steps):
            current_logger.info(f"--- ADV_RAG Starting Retrieval Step {current_step + 1}/{max_retrieval_steps} ---")
            queries_for_step = sub_questions if current_step == 0 else analysis_result.get("follow_ups", [])
            if not queries_for_step:
                current_logger.info(f"ADV_RAG Step {current_step + 1}: No follow-up questions generated or sub-questions available. Breaking loop.")
                break
            current_logger.info(f"ADV_RAG Step {current_step + 1}: Using {'initial sub-questions' if current_step == 0 else 'follow-up questions'}: {queries_for_step}")
            
            current_step_variations = []
            for q_idx, q_text in enumerate(queries_for_step):
                 if processed_count >= variation_processing_limit: break
                 current_step_variations.extend(processor._generate_query_variations(q_text, chat_history))
            current_step_variations = list(dict.fromkeys(current_step_variations)) # Deduplicate
            current_logger.info(f"ADV_RAG Step {current_step + 1}: Generated {len(current_step_variations)} unique variations.")

            current_step_candidate_chunk_ids = set() # IDs found in this step
            for i, current_variation in enumerate(current_step_variations):
                if processed_count >= variation_processing_limit:
                    current_logger.warning(f"ADV_RAG: Reached processing limit ({processed_count}). Skipping remaining variations for step {current_step + 1}.")
                    break
                current_logger.debug(f"ADV_RAG Step {current_step + 1}, Variation {i+1}/{len(current_step_variations)}: Processing '{current_variation[:100]}...'")
                
                vector_ranks = {}; bm25_ranks = {}
                try:
                    query_embeddings, emb_error = rag_service_instance.generate_multiple_embeddings([current_variation])
                    if emb_error or not query_embeddings:
                        current_logger.error(f"ADV_RAG: Failed to generate embedding for variation '{current_variation[:50]}...': {emb_error}")
                        processed_count += 1; continue
                    
                    neighbors_list, retrieval_error = rag_service_instance.retrieve_chunks_multi_query(query_embeddings=query_embeddings, chatbot_id=chatbot_id, client_id=session_id)
                    vector_results_raw = [] if retrieval_error else [{'id': neighbor_id} for neighbor_id in neighbors_list] # Assuming retrieve_chunks_multi_query returns list of IDs
                    if retrieval_error: current_logger.warning(f"ADV_RAG: Vector search failed for variation '{current_variation[:50]}...': {retrieval_error}")
                    
                    # Assuming retrieve_chunks_multi_query returns IDs already somewhat ranked or distances
                    # If it returns distances, sort by distance. If just IDs, rank by order.
                    # For simplicity, let's assume it's already implicitly ranked.
                    vector_ranks = {res['id']: r + 1 for r, res in enumerate(vector_results_raw) if 'id' in res}

                    if bm25 is not None and corpus_chunk_ids_for_bm25:
                        tokenized_variation = current_variation.split(" ")
                        if tokenized_variation:
                            doc_scores_all = bm25.get_scores(tokenized_variation)
                            # Map scores back to original vector_ids used to build BM25
                            scored_chunk_ids = [(corpus_chunk_ids_for_bm25[idx], doc_scores_all[idx]) for idx in range(len(doc_scores_all)) if doc_scores_all[idx] > 0 and idx < len(corpus_chunk_ids_for_bm25)]
                            bm25_results_ranked = sorted(scored_chunk_ids, key=lambda item: item[1], reverse=True)
                            bm25_ranks = {item[0]: r + 1 for r, item in enumerate(bm25_results_ranked)}
                    
                    rrf_scores = defaultdict(float)
                    all_ids_this_variation = set(vector_ranks.keys()) | set(bm25_ranks.keys())
                    rrf_k_val = current_app.config.get('RRF_K', 60)
                    for chunk_id_rrf in all_ids_this_variation: # Renamed chunk_id to chunk_id_rrf
                        score = 0.0
                        if chunk_id_rrf in vector_ranks: score += 1.0 / (rrf_k_val + vector_ranks[chunk_id_rrf])
                        if chunk_id_rrf in bm25_ranks: score += 1.0 / (rrf_k_val + bm25_ranks[chunk_id_rrf])
                        rrf_scores[chunk_id_rrf] = score
                    
                    rrf_sorted_chunk_ids_variation = sorted(all_ids_this_variation, key=lambda cid: rrf_scores[cid], reverse=True)
                    num_hybrid_chunks = current_app.config.get('NUM_HYBRID_CHUNKS_PER_VARIATION', 5)
                    top_rrf_chunk_ids_this_variation = rrf_sorted_chunk_ids_variation[:num_hybrid_chunks] # Renamed
                    current_step_candidate_chunk_ids.update(set(top_rrf_chunk_ids_this_variation))
                    processed_count += 1
                except Exception as e:
                    current_logger.error(f"ADV_RAG: Error during retrieval or RRF for variation '{current_variation[:50]}...': {e}", exc_info=True)
            
            if processed_count >= variation_processing_limit and current_step < max_retrieval_steps -1 :
                 current_logger.warning(f"ADV_RAG: Reached processing limit ({processed_count}) during step {current_step + 1}. Breaking retrieval loop.")
                 break

            # --- MODIFIED TEXT FETCHING LOGIC ---
            new_chunk_ids_to_fetch_texts_for = list(current_step_candidate_chunk_ids - all_retrieved_chunk_ids_set)
            current_logger.info(f"ADV_RAG Step {current_step + 1}: Identified {len(new_chunk_ids_to_fetch_texts_for)} new unique chunk IDs to fetch texts for.")
            
            if new_chunk_ids_to_fetch_texts_for:
                newly_fetched_chunks_this_step = [] # Renamed
                # Fetch texts for these specific IDs
                actual_fetched_texts_list, fetch_error = rag_service_instance.fetch_chunk_texts(new_chunk_ids_to_fetch_texts_for, chatbot_id)
                
                if fetch_error:
                    current_logger.error(f"ADV_RAG: Error fetching texts for new chunks in step {current_step + 1}: {fetch_error}")
                elif actual_fetched_texts_list and isinstance(actual_fetched_texts_list, list) and len(actual_fetched_texts_list) == len(new_chunk_ids_to_fetch_texts_for):
                    mappings = db.session.query(VectorIdMapping).filter(VectorIdMapping.vector_id.in_(new_chunk_ids_to_fetch_texts_for), VectorIdMapping.chatbot_id == chatbot_id).all()
                    mapping_dict = {m.vector_id: m for m in mappings}
                    
                    for i, chunk_id_fetch in enumerate(new_chunk_ids_to_fetch_texts_for): # Renamed chunk_id
                        mapping = mapping_dict.get(chunk_id_fetch)
                        chunk_text_content = actual_fetched_texts_list[i] # Assumes fetch_chunk_texts returns in order

                        if mapping and chunk_text_content: # Check if text_content is not None or empty
                            newly_fetched_chunks_this_step.append({
                                "id": chunk_id_fetch,
                                "text": chunk_text_content,
                                "metadata": {"source": mapping.source_identifier or 'Unknown source'}
                            })
                            all_retrieved_chunk_ids_set.add(chunk_id_fetch) # Add to master set *after* successful fetch
                        elif not chunk_text_content:
                            current_logger.warning(f"ADV_RAG: Fetched empty text for new chunk_id: {chunk_id_fetch}")
                        elif not mapping:
                            current_logger.warning(f"ADV_RAG: Could not find mapping for successfully fetched new chunk_id: {chunk_id_fetch} (text was '{str(chunk_text_content)[:50]}...')")
                
                    if newly_fetched_chunks_this_step:
                        all_retrieved_chunks_list.extend(newly_fetched_chunks_this_step)
                        current_logger.info(f"ADV_RAG Step {current_step + 1}: Accumulated {len(newly_fetched_chunks_this_step)} new chunks with text. Total unique with text: {len(all_retrieved_chunks_list)}")
                else:
                    current_logger.warning(f"ADV_RAG: Text fetch for new chunks returned unexpected result or count mismatch. Expected {len(new_chunk_ids_to_fetch_texts_for)}, got {len(actual_fetched_texts_list) if actual_fetched_texts_list else 'None'}")
            # --- END OF MODIFIED TEXT FETCHING LOGIC ---
            
            if not all_retrieved_chunks_list:
                current_logger.warning(f"ADV_RAG Step {current_step + 1}: No chunks with text accumulated, skipping analysis or breaking.")
                if current_step == 0: # If first step and no chunks, pointless to continue
                    current_logger.info("ADV_RAG: No chunks after first step, breaking retrieval.")
                    break
            else:
                # Deduplicate all_retrieved_chunks_list before analysis, though all_retrieved_chunk_ids_set should handle upstream logic
                # For safety, ensure no duplicate dicts if IDs somehow got duplicated before text fetch
                seen_ids_for_dedup = set()
                deduplicated_chunks_for_analysis = []
                for chunk_item in all_retrieved_chunks_list:
                    if chunk_item['id'] not in seen_ids_for_dedup:
                        deduplicated_chunks_for_analysis.append(chunk_item)
                        seen_ids_for_dedup.add(chunk_item['id'])
                
                analysis_result = processor._analyze_retrieval_and_generate_followups(query, sub_questions, deduplicated_chunks_for_analysis)
                current_logger.info(f"ADV_RAG Step {current_step + 1}: Analysis Result: {analysis_result}")
                if analysis_result.get("sufficient", False):
                    current_logger.info(f"ADV_RAG Step {current_step + 1}: Sufficient context found. Breaking loop.")
                    break
        
        current_logger.info(f"ADV_RAG: Multi-step retrieval finished. Total unique chunks with text: {len(all_retrieved_chunks_list)}")
        reranked_chunks = processor._rerank_chunks(query, all_retrieved_chunks_list) if all_retrieved_chunks_list else []
        current_logger.info(f"ADV_RAG: Chunks after final re-ranking: {len(reranked_chunks)}")
        
        num_final_chunks = current_app.config.get('NUM_FINAL_CONTEXT_CHUNKS', 5)
        final_context_chunks = reranked_chunks[:num_final_chunks]
        current_logger.info(f"ADV_RAG: Selected top {len(final_context_chunks)} chunks for final context.")
        formatted_context = processor._format_context(final_context_chunks)
        config_target_token_limit = current_app.config.get('CONTEXT_COMPRESSION_TARGET_TOKENS', 4000)
        compressed_context = processor._compress_context(formatted_context, config_target_token_limit, query)

        current_logger.info("--- ADV_RAG Step 5: Final Answer Synthesis ---")
        # ... (rest of the final answer synthesis code remains the same) ...
        final_answer = "Sorry, I couldn't generate a response based on the available information." # Default
        formatted_history = "\n".join([f"{turn['role']}: {turn['content']}" for turn in chat_history])
        base_prompt = chatbot.base_prompt or "You are a helpful assistant."
        final_prompt = f"""{base_prompt}

Chat History:
---
{formatted_history}
---

Context (potentially summarized for relevance and length):
---
{compressed_context}
---

User Query: "{query}"

Instructions: Based *only* on the provided context and chat history, answer the user's query. If the context does not contain the answer, state that clearly. Cite the source number (e.g., [Source 1], [Source 2]) where the information was found, if possible. Do not make up information.

Answer:"""
        try:
            final_temp = current_app.config.get('FINAL_RESPONSE_TEMPERATURE', 0.5)
            final_max_tokens = current_app.config.get('FINAL_RESPONSE_MAX_TOKENS', 1500)
            final_safety_settings = current_app.config.get('FINAL_RESPONSE_SAFETY_SETTINGS', DEFAULT_QUERY_REPHRASING_SAFETY_SETTINGS)
            generation_config = GenerationConfig(temperature=final_temp, max_output_tokens=final_max_tokens)
            llm_response = processor.final_llm.generate_content(contents=[final_prompt], generation_config=generation_config, safety_settings=final_safety_settings, stream=False)
            if llm_response and llm_response.candidates and llm_response.candidates[0].content.parts:
                response_text = llm_response.candidates[0].content.parts[0].text.strip()
                if response_text: final_answer = response_text; current_logger.info("ADV_RAG: Successfully generated final answer.")
                else: current_logger.warning("ADV_RAG: Final LLM response text was empty.")
            else:
                current_logger.warning(f"ADV_RAG: Final LLM response was empty or invalid. Response: {llm_response}")
                try:
                    if llm_response.prompt_feedback.block_reason: # Check if prompt_feedback exists
                        final_answer = f"Sorry, I couldn't generate a response due to safety filters ({llm_response.prompt_feedback.block_reason.name})."
                        current_logger.warning(f"ADV_RAG: Final response blocked. Reason: {llm_response.prompt_feedback.block_reason.name}")
                except AttributeError: # Handle cases where prompt_feedback might be None or not have block_reason
                    current_logger.warning(f"ADV_RAG: Could not determine block reason from LLM response: {llm_response}")
                except Exception as block_reason_e: # Catch other unexpected errors accessing block_reason
                    current_logger.error(f"ADV_RAG: Error accessing block_reason: {block_reason_e}", exc_info=True)

        except (GoogleAPICallError, RetryError, DeadlineExceeded) as e:
             current_logger.error(f"ADV_RAG: API Error during final answer synthesis: {e}", exc_info=True)
             final_answer = "Sorry, I encountered an API error while generating the final response."
        except Exception as e:
            current_logger.error(f"ADV_RAG: Error during final answer synthesis: {e}", exc_info=True)
            final_answer = "Sorry, I encountered an error while generating the final response."


        end_pipeline_time = time.time()
        duration = end_pipeline_time - start_pipeline_time
        current_logger.info(f"ADV_RAG: Advanced RAG pipeline finished in {duration:.2f}s.")
        
        # Prepare metadata for return
        final_metadata = {
            "follow_ups": analysis_result.get("follow_ups", []),
            "retrieved_raw_texts": [chunk.get('text', '') for chunk in all_retrieved_chunks_list]
        }
        
        result = {"answer": final_answer, "sources": final_context_chunks}
        return (result.get("answer", "Error: No answer generated."), result.get("sources", []), None, None, 200, final_metadata)

    except SQLAlchemyError as db_e: # Specific DB error
        current_logger.error(f"ADV_RAG: Database error for chatbot {chatbot_id}, session {session_id}: {db_e}", exc_info=True)
        return ("Sorry, a database error occurred.", [], None, "A database error occurred in the advanced RAG pipeline.", 500, {"internal_error_type": "DatabaseError"})
    except Exception as e:
        current_logger.error(f"ADV_RAG: Unhandled exception in process_advanced_query for chatbot {chatbot_id}, session {session_id}: {e}", exc_info=True)
        return ("Sorry, an unexpected error occurred while processing your request.", [], None, "An internal error occurred in the advanced RAG pipeline.", 500, {"internal_error_type": str(type(e).__name__)})
