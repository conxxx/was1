# MCP Integration Architecture for RAG-based Chatbot Platform

## Overview

This document outlines the architecture for integrating Machine Conversation Protocol (MCP) capabilities into the existing RAG-based chatbot platform. This integration will enable other AI agents to interact with chatbots created on the platform using the MCP protocol, similar to Microsoft's NLWeb implementation.

## Current Architecture Summary

The platform currently uses Google Cloud components:
- **Vertex AI** for embedding generation and response generation
- **Vertex AI Matching Engine** for vector similarity search
- **Google Cloud Storage (GCS)** for storing document chunks
- **Frontend** for chatbot creation and management

## MCP Integration Architecture

### 1. Core Components

#### 1.1 MCP Endpoint Service
- **Purpose**: Serve as the entry point for agent-to-chatbot communication via MCP protocol
- **Implementation**: New Python service that handles MCP requests and interfaces with existing RAG pipeline
- **Location**: Backend service deployed alongside existing RagService

#### 1.2 Schema.org Response Formatter
- **Purpose**: Format RAG responses according to Schema.org standards for MCP compatibility
- **Implementation**: Response transformation layer that converts RAG outputs to structured Schema.org JSON
- **Location**: Part of the MCP Endpoint Service

#### 1.3 Agent Authentication Layer (for future expansion)
- **Purpose**: Simple authentication mechanism for MVP, expandable for production
- **Implementation**: API key validation (reusing existing chatbot API keys)
- **Location**: Middleware in the MCP Endpoint Service

### 2. Integration Points

#### 2.1 RAG Pipeline Integration
```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│                 │     │                 │     │                 │
│  MCP Request    │────▶│  Existing RAG   │────▶│ Schema.org      │
│  Handler        │     │  Pipeline       │     │ Formatter       │
│                 │     │                 │     │                 │
└─────────────────┘     └─────────────────┘     └─────────────────┘
        │                                               │
        │                                               │
        ▼                                               ▼
┌─────────────────┐                           ┌─────────────────┐
│                 │                           │                 │
│  Agent          │◀──────────────────────────│  MCP Response   │
│  (External)     │                           │                 │
│                 │                           │                 │
└─────────────────┘                           └─────────────────┘
```

#### 2.2 Data Flow
1. External agent sends query to MCP endpoint (`/api/v1/mcp/ask`)
2. MCP service authenticates request using chatbot API key
3. Query is processed through existing RAG pipeline:
   - Query embedding generation
   - Vector search for relevant chunks
   - Chunk retrieval from GCS
   - Prompt construction
4. RAG response is transformed into Schema.org format
5. Formatted response is returned to the agent

### 3. API Design

#### 3.1 MCP Endpoint
```
POST /api/v1/mcp/ask
```

**Request:**
```json
{
  "chatbot_id": "string",
  "api_key": "string",
  "query": "string",
  "context": {
    "conversation_id": "string",
    "history": [
      {
        "role": "user|assistant",
        "content": "string"
      }
    ]
  }
}
```

**Response:**
```json
{
  "response": {
    "@context": "https://schema.org",
    "@type": "Answer",
    "text": "string",
    "citation": [
      {
        "@type": "WebPage",
        "url": "string",
        "name": "string"
      }
    ]
  },
  "conversation_id": "string"
}
```

#### 3.2 Image Support Extension
For MVP, image support will be implemented as a separate endpoint:

```
POST /api/v1/mcp/process-image
```

**Request:**
```json
{
  "chatbot_id": "string",
  "api_key": "string",
  "image_url": "string",
  "query": "string"
}
```

**Response:**
```json
{
  "response": {
    "@context": "https://schema.org",
    "@type": "Answer",
    "text": "string"
  }
}
```

### 4. Implementation Components

#### 4.1 Backend (Python)
- **mcp_service.py**: Main service handling MCP protocol requests
- **schema_formatter.py**: Transforms RAG responses to Schema.org format
- **mcp_router.py**: FastAPI/Flask routes for MCP endpoints

#### 4.2 Integration with Existing Code
- Add MCP endpoints to existing API service
- Reuse RagService for query processing
- Extend configuration to include MCP-specific settings

#### 4.3 Configuration
```python
# Add to existing config.py
MCP_CONFIG = {
    "ENABLED": True,
    "SCHEMA_VERSION": "https://schema.org",
    "DEFAULT_RESPONSE_TYPE": "Answer",
    "MAX_HISTORY_LENGTH": 10
}
```

### 5. Deployment Considerations

#### 5.1 Google Cloud Deployment
- Deploy as part of existing backend services
- No additional infrastructure required for MVP
- Ensure proper API routing and authentication

#### 5.2 Scaling Considerations
- MCP endpoints should be stateless for horizontal scaling
- Leverage existing Google Cloud infrastructure for scaling

### 6. Testing Strategy

#### 6.1 Unit Tests
- Test MCP request handling
- Test Schema.org response formatting
- Test integration with RAG pipeline

#### 6.2 Integration Tests
- End-to-end tests with sample agent requests
- Verify correct response format and content

#### 6.3 Test Agents
- Create simple test agents to validate MCP interaction
- Test both text and image processing capabilities
