"""
MCP Integration Code Samples for RAG-based Chatbot Platform

This file contains sample code snippets to demonstrate how the MCP integration
would be implemented in the existing platform.
"""

# Sample 1: MCP Service Implementation

class MCPService:
    """Service for handling MCP protocol requests and responses."""
    
    def __init__(self, rag_service, config):
        """
        Initialize the MCP service.
        
        Args:
            rag_service: The existing RAG service for query processing
            config: Configuration parameters
        """
        self.rag_service = rag_service
        self.config = config
        
    async def process_ask(self, chatbot_id, query, api_key, context=None):
        """
        Process an MCP 'ask' request.
        
        Args:
            chatbot_id: ID of the target chatbot
            query: Natural language query from the agent
            api_key: API key for authentication
            context: Optional conversation context
            
        Returns:
            Schema.org formatted response
        """
        # Validate API key
        if not self._validate_api_key(chatbot_id, api_key):
            return self._create_error_response("Invalid API key")
        
        # Extract conversation history if provided
        history = []
        if context and 'history' in context:
            history = context['history'][-self.config['MCP_CONFIG']['MAX_HISTORY_LENGTH']:]
        
        # Process query through RAG pipeline
        rag_response = await self.rag_service.process_query(
            chatbot_id=chatbot_id,
            query=query,
            history=history
        )
        
        # Format response according to Schema.org
        formatted_response = self._format_schema_org_response(rag_response)
        
        # Return response with conversation ID
        conversation_id = context.get('conversation_id') if context else None
        return {
            "response": formatted_response,
            "conversation_id": conversation_id or self._generate_conversation_id()
        }
    
    async def process_image(self, chatbot_id, image_url, query, api_key):
        """
        Process an image with an optional query.
        
        Args:
            chatbot_id: ID of the target chatbot
            image_url: URL of the image to process
            query: Optional natural language query about the image
            api_key: API key for authentication
            
        Returns:
            Schema.org formatted response
        """
        # Validate API key
        if not self._validate_api_key(chatbot_id, api_key):
            return self._create_error_response("Invalid API key")
        
        # Download image (or use URL directly if from trusted source)
        image_data = await self._fetch_image(image_url)
        
        # Process image through multimodal model
        # Note: This assumes the RAG service has multimodal capabilities
        # or will need to be extended for this purpose
        rag_response = await self.rag_service.process_image_query(
            chatbot_id=chatbot_id,
            image_data=image_data,
            query=query
        )
        
        # Format response according to Schema.org
        formatted_response = self._format_schema_org_response(rag_response)
        
        return {
            "response": formatted_response,
            "conversation_id": self._generate_conversation_id()
        }
    
    def _validate_api_key(self, chatbot_id, api_key):
        """Validate the provided API key for the chatbot."""
        # Implementation would connect to your existing API key validation
        # For MVP, this could be a simple lookup in a database
        return True  # Simplified for example
    
    def _format_schema_org_response(self, rag_response):
        """
        Format RAG response according to Schema.org standards.
        
        Args:
            rag_response: Response from the RAG pipeline
            
        Returns:
            Schema.org formatted response object
        """
        # Basic Schema.org Answer format
        schema_response = {
            "@context": "https://schema.org",
            "@type": "Answer",
            "text": rag_response.get("response", "")
        }
        
        # Add citations if available
        if "source_documents" in rag_response and rag_response["source_documents"]:
            schema_response["citation"] = []
            for doc in rag_response["source_documents"]:
                citation = {
                    "@type": "WebPage",
                    "url": doc.get("url", ""),
                    "name": doc.get("title", "Source document")
                }
                schema_response["citation"].append(citation)
        
        return schema_response
    
    def _create_error_response(self, error_message):
        """Create an error response in Schema.org format."""
        return {
            "response": {
                "@context": "https://schema.org",
                "@type": "Answer",
                "text": f"Error: {error_message}"
            }
        }
    
    def _generate_conversation_id(self):
        """Generate a unique conversation ID."""
        import uuid
        return str(uuid.uuid4())
    
    async def _fetch_image(self, image_url):
        """Fetch image data from URL."""
        import aiohttp
        async with aiohttp.ClientSession() as session:
            async with session.get(image_url) as response:
                if response.status == 200:
                    return await response.read()
                else:
                    raise ValueError(f"Failed to fetch image: {response.status}")


# Sample 2: FastAPI Routes for MCP Endpoints

from fastapi import FastAPI, Depends, HTTPException, Body
from typing import Optional, Dict, List, Any

app = FastAPI()

# Dependency to get MCP service instance
async def get_mcp_service():
    # In a real implementation, this would be properly initialized
    # and possibly retrieved from a dependency injection container
    from config import Config
    from rag_service import RagService
    
    config = Config()
    rag_service = RagService(config)
    return MCPService(rag_service, config)

@app.post("/api/v1/mcp/ask")
async def mcp_ask(
    request: Dict[str, Any] = Body(...),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """MCP ask endpoint for agent-to-chatbot communication."""
    try:
        chatbot_id = request.get("chatbot_id")
        api_key = request.get("api_key")
        query = request.get("query")
        context = request.get("context")
        
        if not all([chatbot_id, api_key, query]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        response = await mcp_service.process_ask(
            chatbot_id=chatbot_id,
            query=query,
            api_key=api_key,
            context=context
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/mcp/process-image")
async def mcp_process_image(
    request: Dict[str, Any] = Body(...),
    mcp_service: MCPService = Depends(get_mcp_service)
):
    """MCP image processing endpoint."""
    try:
        chatbot_id = request.get("chatbot_id")
        api_key = request.get("api_key")
        image_url = request.get("image_url")
        query = request.get("query", "")
        
        if not all([chatbot_id, api_key, image_url]):
            raise HTTPException(status_code=400, detail="Missing required parameters")
        
        response = await mcp_service.process_image(
            chatbot_id=chatbot_id,
            image_url=image_url,
            query=query,
            api_key=api_key
        )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# Sample 3: Configuration Extension

"""
Add to existing config.py
"""

class Config:
    # Existing configuration...
    
    # MCP Configuration
    MCP_CONFIG = {
        "ENABLED": True,
        "SCHEMA_VERSION": "https://schema.org",
        "DEFAULT_RESPONSE_TYPE": "Answer",
        "MAX_HISTORY_LENGTH": 10,
        "ALLOWED_ORIGINS": ["*"],  # For MVP; restrict in production
        "RATE_LIMIT": {
            "ENABLED": True,
            "REQUESTS_PER_MINUTE": 60
        }
    }
