## 2. Theoretical Background

The development of the Website AI Assistant (WAS) and the complementary Agentic Chatbot is grounded in a modern, robust client-server architecture and leverages several cutting-edge artificial intelligence paradigms. This section details the foundational theories upon which these systems are built.

### 2.1 Architectural Foundation

Both projects are built upon a client-server model, which separates the user-facing interface (client) from the data processing and business logic (server). This separation is critical for creating a scalable, maintainable, and secure application.

The **Website AI Assistant (WAS)** employs a sophisticated three-tier architecture, a proven software design pattern that separates the application into logical and physical computing tiers. This separation enhances scalability, maintainability, and flexibility by decoupling the user interface, business logic, and data storage layers.
1.  **Presentation Tier (Client):** This tier consists of two distinct clients—a web-based administrative dashboard and a lightweight, embeddable widget for end-users. It is responsible for rendering the user interface and capturing user input.
2.  **Logic Tier (Server/Backend):** This is the authoritative core of the system. It executes the business logic, handles data processing (such as website ingestion), manages asynchronous tasks, and orchestrates all interactions with AI models and other services.
3.  **Data Tier:** This tier includes both a traditional database for storing application state (like user and chatbot configurations) and a specialized vector database for storing the indexed knowledge required for the RAG process.

The **Agentic Chatbot** also follows a client-server model, but its architecture is conceptually defined by the principles of agent-based systems. The server-side logic encapsulates the agent's core reasoning loop, state management, and its ability to interact with a set of defined tools, representing a distinct architectural pattern focused on autonomous task execution.

### 2.2 Core AI Paradigm: Retrieval-Augmented Generation (RAG)

The central theory behind the WAS platform is **Retrieval-Augmented Generation (RAG)**. Traditional Large Language Models (LLMs) generate responses based solely on the vast, but static, data they were trained on. This can lead to outdated or generic answers. RAG enhances LLMs by connecting them to external, up-to-date knowledge sources.

The process works as follows:
1.  **Ingestion & Indexing:** Website content (HTML, PDFs, etc.) is collected, parsed, and broken down into smaller, manageable chunks of text. Each chunk is then converted into a numerical representation (a vector embedding) and stored in a specialized vector database. This index is optimized for fast and efficient similarity searches.
2.  **Retrieval:** When a user asks a question, the system first converts the query into a vector embedding. It then searches the vector database to find the text chunks that are most semantically similar to the user's query.
3.  **Augmentation & Generation:** The retrieved text chunks (the "context") are combined with the original user query into a detailed prompt. This augmented prompt is then sent to an LLM (like Google's Gemini). The model uses the provided context to generate a relevant, accurate, and factually grounded response, rather than relying only on its internal knowledge.

This RAG pipeline is the key to making the WAS chatbot a true expert on a specific website's content.

### 2.3 Core AI Paradigm: Agentic Models & Tool Use

The agentic chatbot project is built upon the theory of **tool-using agents**. This paradigm extends the capabilities of LLMs beyond text generation, turning them into reasoning engines that can interact with external systems to accomplish tasks.

The core concept involves providing the LLM with a set of "tools" (i.e., functions or APIs) and their descriptions. When a user makes a request, the LLM's reasoning capabilities are used to:
1.  **Deconstruct the Request:** Understand the user's intent and the steps required to fulfill it.
2.  **Select the Appropriate Tool:** Based on the descriptions, choose the correct tool or sequence of tools to execute.
3.  **Extract Parameters:** Identify and extract the necessary arguments for the chosen tool from the user's query.
4.  **Execute and Observe:** Call the tool and receive its output.
5.  **Synthesize a Response:** Formulate a human-readable response based on the outcome of the tool execution.

This approach allows the agent to perform actions in the real world, such as accessing a database, calling an external API, or modifying a user's state in a system, making it a powerful model for creating interactive, task-oriented assistants.
