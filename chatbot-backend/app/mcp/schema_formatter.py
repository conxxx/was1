# chatbot-backend/app/mcp/schema_formatter.py
import uuid
from flask import current_app

class SchemaFormatter:
    """
    Formats responses according to Schema.org standards for MCP.
    """

    def __init__(self, config=None):
        if config and 'MCP_CONFIG' in config:
            self.mcp_config = config['MCP_CONFIG']
        elif current_app:
            self.mcp_config = current_app.config.get('MCP_CONFIG', {})
        else:
            # Fallback if no config is available (e.g., testing outside app context)
            self.mcp_config = {
                "SCHEMA_VERSION": "https://schema.org",
                "DEFAULT_RESPONSE_TYPE": "Answer",
            }

    def format_success_response(self, rag_response_data, conversation_id=None):
        """
        Formats a successful RAG response into Schema.org format.

        Args:
            rag_response_data (dict): The dictionary returned by RagService.execute_pipeline.
                                      Expected keys: "answer", "sources" (optional).
            conversation_id (str, optional): The conversation ID.

        Returns:
            dict: The MCP formatted response.
        """
        schema_version = self.mcp_config.get("SCHEMA_VERSION", "https://schema.org")
        default_response_type = self.mcp_config.get("DEFAULT_RESPONSE_TYPE", "Answer")

        response_text = rag_response_data.get("answer", "No answer provided.")
        sources = rag_response_data.get("sources", [])

        schema_response_content = {
            "@context": schema_version,
            "@type": default_response_type,
            "text": response_text
        }

        if sources:
            schema_response_content["citation"] = []
            for src in sources:
                # Assuming sources from RagService are dicts with 'identifier' and 'type'
                # The sample code had 'url' and 'name'. We'll adapt.
                # 'identifier' could be a URL or a file name.
                citation_item = {
                    "@type": "WebPage" if src.get('type') == 'web' or str(src.get('identifier', '')).startswith('http') else "CreativeWork",
                    "name": src.get('identifier', "Source Document") # Use identifier as name for now
                }
                if str(src.get('identifier', '')).startswith('http'):
                    citation_item["url"] = src.get('identifier')
                
                schema_response_content["citation"].append(citation_item)
        
        return {
            "response": schema_response_content,
            "conversation_id": conversation_id or str(uuid.uuid4())
        }

    def format_error_response(self, error_message, conversation_id=None, error_code=None):
        """
        Creates an error response in Schema.org format.

        Args:
            error_message (str): The error message.
            conversation_id (str, optional): The conversation ID.
            error_code (str, optional): A specific error code.

        Returns:
            dict: The MCP formatted error response.
        """
        schema_version = self.mcp_config.get("SCHEMA_VERSION", "https://schema.org")
        default_response_type = self.mcp_config.get("DEFAULT_RESPONSE_TYPE", "Answer") # Errors are still "Answers"

        error_response_content = {
            "@context": schema_version,
            "@type": default_response_type, # Or potentially a more specific error type if MCP defines one
            "text": f"Error: {error_message}"
        }
        if error_code:
            error_response_content["errorDetails"] = {"code": error_code, "message": error_message}


        return {
            "response": error_response_content,
            "conversation_id": conversation_id or str(uuid.uuid4()) # Provide a conversation_id even for errors
        }

# Example usage (for testing purposes, can be removed):
if __name__ == '__main__':
    formatter = SchemaFormatter(config={"MCP_CONFIG": {"SCHEMA_VERSION": "https://schema.org", "DEFAULT_RESPONSE_TYPE": "Answer"}})
    
    # Test success
    sample_rag_success = {
        "answer": "This is the answer from RAG.",
        "sources": [
            {"type": "web", "identifier": "https://example.com/source1"},
            {"type": "file", "identifier": "file://document.pdf"}
        ]
    }
    mcp_success_response = formatter.format_success_response(sample_rag_success, "conv123")
    print("MCP Success Response:")
    import json
    print(json.dumps(mcp_success_response, indent=2))

    # Test error
    mcp_error_response = formatter.format_error_response("Something went wrong.", "conv123", "INTERNAL_ERROR")
    print("\nMCP Error Response:")
    print(json.dumps(mcp_error_response, indent=2))
    
    # Test success no sources
    sample_rag_no_source = {"answer": "This is an answer without sources."}
    mcp_no_source_response = formatter.format_success_response(sample_rag_no_source)
    print("\nMCP No Source Response:")
    print(json.dumps(mcp_no_source_response, indent=2))
