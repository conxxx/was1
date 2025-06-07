# chatbot-backend/app/api/mcp_routes.py
from flask import Blueprint, request, jsonify, current_app, g
from functools import wraps
from app.models import Chatbot
from app.services.rag_service import RagService # For type hinting and instantiation
from app.mcp.mcp_service import MCPService
from app import limiter # Assuming limiter is initialized in app/__init__.py

mcp_bp = Blueprint('mcp_api', __name__, url_prefix='/api/v1/mcp')

# --- Helper to get RagService instance ---
def get_rag_service_instance():
    if not hasattr(current_app, 'extensions') or 'rag_service' not in current_app.extensions:
        current_app.logger.info("Initializing RAG Service instance for MCP routes...")
        if not hasattr(current_app, 'extensions'):
            current_app.extensions = {}
        current_app.extensions['rag_service'] = RagService(current_app.logger)
    rag_instance = current_app.extensions.get('rag_service')
    if rag_instance is None:
        raise RuntimeError("RAG Service failed previous initialization or is not available.")
    return rag_instance

# --- API Key Authentication Decorator for MCP (reads from JSON body) ---
def require_mcp_api_key(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)

        data = request.get_json()
        if not data:
            return jsonify({"error": {"code": "INVALID_REQUEST", "message": "Request body must be JSON."}}), 400

        api_key = data.get('api_key')
        chatbot_id_str = data.get('chatbot_id')

        if not api_key:
            return jsonify({"error": {"code": "AUTH_MISSING_KEY", "message": "Missing API key in request body."}}), 401
        if not chatbot_id_str:
            return jsonify({"error": {"code": "AUTH_MISSING_CHATBOT_ID", "message": "Missing chatbot_id in request body."}}), 400

        try:
            chatbot_id = int(chatbot_id_str)
        except ValueError:
            return jsonify({"error": {"code": "INVALID_CHATBOT_ID", "message": "Invalid chatbot_id format."}}), 400

        chatbot = Chatbot.query.filter_by(id=chatbot_id).first()
        if not chatbot:
            return jsonify({"error": {"code": "CHATBOT_NOT_FOUND", "message": "Chatbot not found."}}), 404

        # Assuming api_key in Chatbot model is hashed.
        # The original require_api_key uses check_password_hash. We need to import it.
        from werkzeug.security import check_password_hash
        if not chatbot.api_key or not check_password_hash(chatbot.api_key, api_key):
            current_app.logger.warning(f"MCP: Invalid API key for chatbot {chatbot_id}.")
            return jsonify({"error": {"code": "AUTH_INVALID_KEY", "message": "Invalid or unauthorized API key."}}), 403
        
        # Store chatbot in g for use by the route and service
        g.chatbot = chatbot 
        # Store the validated chatbot_id from token (which is chatbot.id here)
        # This helps MCPService access it consistently if g.chatbot is not directly used there.
        g.chatbot_id_from_token = chatbot.id 

        return f(*args, **kwargs)
    return decorated_function

@mcp_bp.route('/ask', methods=['POST'])
@limiter.limit("60 per minute") # Example rate limit
@require_mcp_api_key
def mcp_ask_route():
    data = request.get_json()
    query = data.get('query')
    context = data.get('context') # Optional

    if not query:
        return jsonify({"error": {"code": "MISSING_QUERY", "message": "Missing 'query' in request body."}}), 400

    try:
        rag_service_instance = get_rag_service_instance()
        mcp_service = MCPService(rag_service=rag_service_instance, config=current_app.config, logger=current_app.logger)
        
        # g.chatbot_id_from_token is set by the decorator
        response = mcp_service.process_ask(
            chatbot_id_from_token=g.chatbot_id_from_token, 
            query=query, 
            context=context
        )
        # MCPService methods now return the full dict including "response" and "conversation_id"
        return jsonify(response), 200
    except RuntimeError as e: # Catch RAG service init error
        current_app.logger.error(f"MCP Ask Route: Runtime error - {str(e)}", exc_info=True)
        # MCPService's schema_formatter can be used even if MCPService instantiation failed partially
        # but it's safer to construct a simple error here if service itself is the issue.
        formatter = MCPService(None).schema_formatter # Temp formatter
        return jsonify(formatter.format_error_response(f"Service unavailable: {str(e)}", None, "SERVICE_UNAVAILABLE")), 503
    except Exception as e:
        current_app.logger.error(f"MCP Ask Route: Unexpected error - {str(e)}", exc_info=True)
        formatter = MCPService(None).schema_formatter
        return jsonify(formatter.format_error_response(f"An internal server error occurred: {str(e)}", None, "INTERNAL_SERVER_ERROR")), 500


@mcp_bp.route('/process-image', methods=['POST'])
@limiter.limit("30 per minute") # Example rate limit
@require_mcp_api_key
def mcp_process_image_route():
    data = request.get_json()
    image_url = data.get('image_url')
    query = data.get('query', "") # Query is optional for image processing

    if not image_url:
        return jsonify({"error": {"code": "MISSING_IMAGE_URL", "message": "Missing 'image_url' in request body."}}), 400

    try:
        rag_service_instance = get_rag_service_instance()
        mcp_service = MCPService(rag_service=rag_service_instance, config=current_app.config, logger=current_app.logger)
        
        # g.chatbot_id_from_token is set by the decorator
        response = mcp_service.process_image(
            chatbot_id_from_token=g.chatbot_id_from_token, 
            image_url=image_url, 
            query=query
        )
        return jsonify(response), 200
    except RuntimeError as e: # Catch RAG service init error
        current_app.logger.error(f"MCP Process Image Route: Runtime error - {str(e)}", exc_info=True)
        formatter = MCPService(None).schema_formatter
        return jsonify(formatter.format_error_response(f"Service unavailable: {str(e)}", None, "SERVICE_UNAVAILABLE")), 503
    except Exception as e:
        current_app.logger.error(f"MCP Process Image Route: Unexpected error - {str(e)}", exc_info=True)
        formatter = MCPService(None).schema_formatter
        return jsonify(formatter.format_error_response(f"An internal server error occurred: {str(e)}", None, "INTERNAL_SERVER_ERROR")), 500
