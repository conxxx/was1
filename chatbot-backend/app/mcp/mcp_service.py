# chatbot-backend/app/mcp/mcp_service.py
import uuid
import httpx # Using httpx for async HTTP requests
import mimetypes
from flask import current_app, g
from app.services.rag_service import RagService # Assuming RagService can be imported
from app.mcp.schema_formatter import SchemaFormatter
from app.models import Chatbot # To fetch client_id

class MCPService:
    """
    Service for handling MCP protocol requests and responses.
    """
    def __init__(self, rag_service: RagService, config=None, logger=None):
        self.rag_service = rag_service
        self.logger = logger or current_app.logger
        
        if config and 'MCP_CONFIG' in config:
            self.mcp_config = config['MCP_CONFIG']
        elif current_app:
            self.mcp_config = current_app.config.get('MCP_CONFIG', {})
        else:
            self.mcp_config = { # Fallback
                "MAX_HISTORY_LENGTH": 10 
            }
        
        self.schema_formatter = SchemaFormatter(config=self.mcp_config)

    def _fetch_image(self, image_url: str):
        """Fetches image data from a URL synchronously."""
        try:
            with httpx.Client() as client:
                response = client.get(image_url, timeout=10.0) # 10 second timeout
                response.raise_for_status() # Raise an exception for bad status codes
                image_bytes = response.read()
                content_type = response.headers.get("Content-Type")
                
                # Guess MIME type if not provided or too generic
                if not content_type or content_type == 'application/octet-stream':
                    guessed_type, _ = mimetypes.guess_type(image_url)
                    if guessed_type:
                        content_type = guessed_type
                    else: # Fallback if guess fails
                        content_type = 'application/octet-stream' 
                        self.logger.warning(f"Could not determine specific MIME type for {image_url}, using {content_type}.")
                
                return image_bytes, content_type
        except httpx.HTTPStatusError as e:
            self.logger.error(f"HTTP error fetching image {image_url}: {e.response.status_code} - {e.response.text}")
            raise ValueError(f"Failed to fetch image: HTTP {e.response.status_code}")
        except httpx.RequestError as e:
            self.logger.error(f"Request error fetching image {image_url}: {e}")
            raise ValueError(f"Failed to fetch image: {e}")
        except Exception as e:
            self.logger.error(f"Unexpected error fetching image {image_url}: {e}", exc_info=True)
            raise ValueError(f"Unexpected error fetching image: {e}")

    def process_ask(self, chatbot_id_from_token: int, query: str, context: dict = None):
        """
        Process an MCP 'ask' request.
        chatbot_id_from_token is the validated chatbot_id from the auth mechanism.
        """
        self.logger.info(f"MCPService: Processing 'ask' for chatbot_id: {chatbot_id_from_token}")
        conversation_id = context.get('conversation_id') if context else str(uuid.uuid4())

        try:
            # Fetch chatbot to get client_id (assuming g.chatbot is set by decorator)
            # If not using g, fetch directly: chatbot = Chatbot.query.get(chatbot_id_from_token)
            chatbot = getattr(g, 'chatbot', None) # Safely get from g
            if not chatbot or chatbot.id != chatbot_id_from_token: # Double check
                 chatbot = Chatbot.query.get(chatbot_id_from_token)
            
            if not chatbot:
                self.logger.error(f"MCPService 'ask': Chatbot {chatbot_id_from_token} not found.")
                return self.schema_formatter.format_error_response("Chatbot not found.", conversation_id, "CHATBOT_NOT_FOUND")

            client_id = chatbot.client_id
            
            history = []
            if context and 'history' in context:
                max_history = self.mcp_config.get('MAX_HISTORY_LENGTH', 10)
                history = context['history'][-max_history:]
            
            rag_response_data = self.rag_service.execute_pipeline(
                query=query,
                chatbot_id=chatbot_id_from_token,
                client_id=client_id,
                chat_history=history
            )
            
            if rag_response_data.get("error"):
                self.logger.error(f"MCPService 'ask': RAG pipeline error for chatbot {chatbot_id_from_token}: {rag_response_data['error']}")
                return self.schema_formatter.format_error_response(
                    rag_response_data['error'], 
                    conversation_id, 
                    rag_response_data.get("error_code", "RAG_ERROR")
                )

            return self.schema_formatter.format_success_response(rag_response_data, conversation_id)

        except Exception as e:
            self.logger.error(f"MCPService 'ask': Unexpected error for chatbot {chatbot_id_from_token}: {e}", exc_info=True)
            return self.schema_formatter.format_error_response(f"An internal error occurred: {str(e)}", conversation_id, "INTERNAL_MCP_SERVICE_ERROR")

    def process_image(self, chatbot_id_from_token: int, image_url: str, query: str):
        """
        Process an image with an optional query.
        """
        self.logger.info(f"MCPService: Processing 'image' for chatbot_id: {chatbot_id_from_token}, image_url: {image_url}")
        conversation_id = str(uuid.uuid4()) # New conversation for each image process call

        try:
            chatbot = getattr(g, 'chatbot', None)
            if not chatbot or chatbot.id != chatbot_id_from_token:
                 chatbot = Chatbot.query.get(chatbot_id_from_token)

            if not chatbot:
                self.logger.error(f"MCPService 'process_image': Chatbot {chatbot_id_from_token} not found.")
                return self.schema_formatter.format_error_response("Chatbot not found.", conversation_id, "CHATBOT_NOT_FOUND")
            
            if not chatbot.image_analysis_enabled:
                self.logger.warning(f"MCPService 'process_image': Image analysis disabled for chatbot {chatbot_id_from_token}.")
                return self.schema_formatter.format_error_response("Image analysis is not enabled for this chatbot.", conversation_id, "IMAGE_ANALYSIS_DISABLED")

            client_id = chatbot.client_id

            try:
                image_bytes, image_mime_type = self._fetch_image(image_url)
            except ValueError as fetch_err: # Catch specific error from _fetch_image
                self.logger.error(f"MCPService 'process_image': Failed to fetch image {image_url}: {fetch_err}")
                return self.schema_formatter.format_error_response(str(fetch_err), conversation_id, "IMAGE_FETCH_FAILED")

            rag_response_data = self.rag_service.execute_pipeline(
                query=query, # Optional query about the image
                chatbot_id=chatbot_id_from_token,
                client_id=client_id,
                image_data=image_bytes,
                image_mime_type=image_mime_type
                # No chat_history for image processing as per MCP spec
            )

            if rag_response_data.get("error"):
                self.logger.error(f"MCPService 'process_image': RAG pipeline error for chatbot {chatbot_id_from_token}: {rag_response_data['error']}")
                return self.schema_formatter.format_error_response(
                    rag_response_data['error'], 
                    conversation_id, 
                    rag_response_data.get("error_code", "RAG_ERROR")
                )

            return self.schema_formatter.format_success_response(rag_response_data, conversation_id)

        except Exception as e:
            self.logger.error(f"MCPService 'process_image': Unexpected error for chatbot {chatbot_id_from_token}: {e}", exc_info=True)
            return self.schema_formatter.format_error_response(f"An internal error occurred: {str(e)}", conversation_id, "INTERNAL_MCP_SERVICE_ERROR")
