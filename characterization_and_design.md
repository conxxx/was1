## 4. Characterization and Design

This section provides a detailed description of each project's specifications, the design of its components, and the specific development tools and technologies used in its implementation.

### 4.1 Website AI Assistant (WAS)

The WAS platform is designed as a comprehensive solution for creating, managing, and deploying content-aware RAG chatbots. It consists of two primary user-facing components: the Administrator Dashboard and the end-user Chatbot Widget.

#### 4.1.1 System Components and User Interaction

This section describes the platform from the perspective of its users. *Note: Screenshots will be added in the final document to visually demonstrate these components.*

*   **Administrator Dashboard (`chatbot-frontend`):**
    *   **Login:** Administrators begin by logging into a secure portal to access the main dashboard.
    *   **Dashboard Home:** Upon login, the user is presented with a central view of all their created chatbots, providing at-a-glance information and quick access to editing and testing functionalities.
    *   **Chatbot Creation:** Administrators can initiate a workflow to create a new chatbot, which involves specifying a name and initial configuration.
    *   **Chatbot Editor:** This is the core of the administrative experience. It is a multi-tabbed interface where users define the chatbot's knowledge base and behavior:
        *   **Data Sources:** A dedicated area for adding website URLs to be crawled, uploading PDF or DOCX files, or inputting raw text. The system provides feedback on the status of data ingestion for each source.
        *   **Customization:** A settings panel for controlling the visual appearance of the widget, including colors, launcher text, and position on the screen.
        *   **Model & Features:** A section to configure advanced features, such as toggling the Advanced RAG pipeline or enabling summarization.
    *   **Chat Interface:** A full-featured chat page within the dashboard allows administrators to test the chatbot's responses and behavior in real-time before deploying it to a live website.

*   **End-User Chatbot Widget (`chatbot-widget`):**
    *   **Launcher:** The chatbot appears on the host website as a simple, non-intrusive launcher button.
    *   **Chat Window:** Clicking the launcher opens the chat interface. The window includes a clear conversation history, an input field for typing messages, and a button to initiate voice input.
    *   **Interaction:** End-users can type or speak their questions. The chatbot's responses are displayed in the conversation log. For voice responses, integrated audio playback controls (play, pause, seek) appear alongside the message.
    *   **Source Links:** When appropriate, the chatbot provides links to the source web pages from which it derived its answer, allowing users to explore the topic in more detail.

#### 4.1.2 Project Specifications

The platform is specified to deliver the following key capabilities:

*   **Chatbot Management Dashboard:** A secure, user-friendly web interface where administrators can create multiple chatbots, configure their data sources, customize their appearance, and monitor their activity.
*   **Multi-Source Data Ingestion:** The system must be able to crawl and process information from various sources, including public website URLs, uploaded PDF documents, and DOCX files.
*   **Customizable Chatbot Widget:** A lightweight, embeddable web component that can be easily integrated into any third-party website. The widget's appearance (colors, position, etc.) must be customizable from the dashboard.
*   **Core RAG Functionality:** The chatbot must accurately answer user questions based on the ingested content, providing source attribution where applicable.
*   **Advanced Conversational Features:**
    *   **Voice Interaction:** Support for both speech-to-text (STT) for user input and text-to-speech (TTS) for audio responses.
    *   **Summarization:** A feature allowing the chatbot to summarize the ingested content or the conversation history.
    *   **Request Cancellation:** The ability for the end-user to cancel a long-running query.
*   **Optional Advanced RAG Pipeline:** An administrator-enabled feature to improve response quality through a multi-step process including query rephrasing, sub-question decomposition, and intelligent re-ranking of retrieved context.

#### 4.1.2 System Design

The WAS platform is designed as a three-tier system, ensuring a clear separation of concerns between its components.

*   **Backend Design (`chatbot-backend`):**
    *   The backend is designed around a **RESTful API** built with Flask. This API serves as the single point of communication for both the frontend dashboard and the embeddable widget.
    *   Business logic is encapsulated within modular **Services** (e.g., `RagService`, `IngestionService`, `VoiceService`), making the codebase easier to maintain and test.
    *   Long-running processes, particularly data ingestion, are handled **asynchronously** using a Celery task queue with a Redis message broker. This ensures the API remains responsive and can handle multiple ingestion requests concurrently without degrading performance.
    *   The RAG pipeline is designed to be extensible, with the `AdvancedRagService` providing a clear example of how more complex processing steps can be added.

*   **Frontend Design (`chatbot-frontend`):**
    *   The frontend is a **Single-Page Application (SPA)** built with React. This provides a fluid and responsive user experience without requiring full page reloads.
    *   The application is structured using a **component-based architecture**, promoting reusability and maintainability. Key views include user authentication pages, a main dashboard for listing chatbots, and detailed pages for creating and editing individual chatbots.
    *   State management is handled within React using its native state and context APIs. Communication with the backend is performed via asynchronous HTTP requests using the Axios library.

*   **Widget Design (`chatbot-widget`):**
    *   The widget is designed as a **self-contained, dependency-free JavaScript module**. This is a critical design choice to ensure it is lightweight and does not conflict with the host website's existing JavaScript libraries.
    *   It maintains its own internal state (e.g., for conversation history, UI state) and communicates directly with the backend API's public-facing endpoints.
    *   To prevent security vulnerabilities, all HTML content rendered within the widget is sanitized using DOMPurify.

#### 4.1.3 Development Tools and Libraries

*   **Backend (`chatbot-backend`):**
    *   **Language:** Python
    *   **Web Framework:** Flask
    *   **Database & ORM:** SQLite, Flask-SQLAlchemy, Flask-Migrate
    *   **API & Web:** Flask-Cors, Flask-Login, Flask-Bcrypt, Flask-Limiter
    *   **Task Queue:** Celery, Redis
    *   **Cloud Integration (Google Cloud):** `google-generativeai`, `google-cloud-storage`, `google-cloud-speech`, `google-cloud-texttospeech`
    *   **NLP/RAG/Text Processing:** `beautifulsoup4`, `lxml`, `python-docx`, `pdfminer.six`, `sentence-transformers`, `tiktoken`

*   **Frontend (`chatbot-frontend`):**
    *   **Language/Framework:** JavaScript, React
    *   **Build Tool:** Vite
    *   **Styling:** Tailwind CSS
    *   **Routing:** `react-router-dom`
    *   **HTTP Client:** Axios
    *   **UI Components/Utils:** `react-colorful`, `react-icons`, `react-markdown`, `react-modal`

*   **Widget (`chatbot-widget`):**
    *   **Language:** JavaScript (ES6)
    *   **Build Tool:** Webpack
    *   **Markdown Processing:** `marked`
    *   **HTML Sanitization:** `dompurify`

### 4.2 Agentic Chatbot

This project was undertaken as a proof-of-concept to explore the capabilities of task-oriented, tool-using AI agents.

#### 4.2.1 Project Specifications

The agent is specified as a customer service assistant for a fictional retail company with the following capabilities:
*   **Conversational Interaction:** Engage in a natural, friendly conversation with the user.
*   **Personalization:** Access (mocked) customer data to greet users by name and reference their purchase history.
*   **Tool Use:** Interact with a set of defined tools to perform actions on behalf of the user.
*   **Task-Oriented Functions:**
    *   Provide product recommendations.
    *   Manage a shopping cart (add/remove items).
    *   Schedule appointments for services.
    *   Request manager approval for discounts.
*   **Multi-modal Input:** Be capable of receiving and interpreting video input to assist with tasks like plant identification.

#### 4.2.2 System Design

The agent's design is dictated by the **Google Agent Development Kit (ADK)**.
*   The core of the design is a **reasoning loop**. The LLM acts as the brain of the agent, receiving user input and deciding which, if any, of its available tools to call.
*   The tools themselves are simple Python functions that simulate interactions with external systems (e.g., a CRM, an inventory database, a scheduling system). In a production environment, these functions would be replaced with actual API calls to live services.
*   Session state is managed by the ADK framework to maintain context throughout a conversation, allowing for multi-turn interactions where the agent remembers previous parts of the dialogue.

#### 4.2.3 Development Tools and Libraries

*   **Core Framework:** Google Agent Development Kit (ADK)
*   **Language:** Python
*   **Dependency Management:** Poetry
*   **AI Model & Platform:** Google Gemini Pro, accessed via the Vertex AI platform.
