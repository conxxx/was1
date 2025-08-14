# 🤖Website Ai Assistance  RAG Chatbot Platform advanced Development Plan

*   **Project Members:**
    *   Eyasu Belay (Backend & Core Logic)
    *   Solomon Kasshun (Frontend & User Experience)
*   **Supervisor:** dr.gadi 
---

### **Detailed Task Breakdown & Timeline**

| Phase & Task | Sub-Task | Eyasu Belay (Backend) | Solomon Kasshun (Frontend) | Timeline |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1: Core Project Development (January 2025 – June 12, 2025)** |
| **1. Foundational Setup & User Auth** | 1a. Project & DB Init | Initialize Flask project, virtual environment, and `.gitignore`. Configure SQLAlchemy and initialize Flask-Migrate for database schema management. | - | Jan 1 - Jan 15 |
| | 1b. Core Models | Define `User` and `Chatbot` SQLAlchemy models in `models.py`, including relationships and constraints. Create initial migration script. | - | Jan 16 - Jan 25 |
| | 1c. Auth API Endpoints | Implement `/register` and `/login` endpoints in `auth_routes.py`. Add logic for creating users and verifying credentials. | - | Jan 26 - Feb 10 |
| | 1d. Security Implementation | Integrate `Flask-Bcrypt` for secure password hashing and verification. Set up `Flask-Login` for user session management. | - | Feb 11 - Feb 20 |
| | 1e. Frontend Project Init | Initialize React project with Vite. Set up folder structure for `pages`, `components`, `services`, and `hooks`. | Configure `react-router-dom` for client-side routing. Create basic layout components (e.g., `Navbar`, `Sidebar`). | Feb 21 - Mar 1 |
| | 1f. Frontend Auth Service | - | In `services/api.js`, create functions to call the backend's `/register` and `/login` endpoints using `axios`. | Mar 2 - Mar 8 |
| | 1g. Auth UI & Integration | - | Build the UI forms for Login and Registration. Implement state management for form inputs and handle API responses for success/failure. | Mar 9 - Mar 20 |
| **2. Data Ingestion & RAG MVP** | 2a. Async Worker Setup | Configure Celery and Redis to manage background tasks for data ingestion. | - | Mar 21 - Mar 31 |
| | 2b. Website Crawler Task | Implement a Celery task that takes a URL, fetches its content with `requests`, and parses the HTML with `BeautifulSoup4` to extract clean text. | - | Apr 1 - Apr 10 |
| | 2c. Text Processing | Develop a text processing module to chunk the extracted text into manageable segments using a library like `langchain-text-splitters`. | - | Apr 11 - Apr 18 |
| | 2d. Embedding & Vector Store | Implement logic in `RagService` to generate vector embeddings for text chunks using a `sentence-transformers` model. Set up an in-memory FAISS vector store. | - | Apr 19 - Apr 30 |
| | 2e. Core Query Logic | In `RagService`, implement the core retrieval logic (similarity search on the vector store) and the prompt engineering logic to combine context with the user query for the LLM. | - | May 1 - May 10 |
| | 2f. Ingestion & Query APIs | Create the API endpoint to trigger the website ingestion task. Create the `/query` API endpoint that uses the `RagService` to generate a response. | - | May 11 - May 18 |
| | 2g. Chatbot Management UI | - | Design and build the dashboard UI to list a user's chatbots and a form to create a new one. | May 19 - May 26 |
| | 2h. Data Source UI | - | Implement the UI for managing a chatbot's data sources, including a form to add a new website URL. Connect this to the ingestion API. | May 27 - June 5 |
| **3. Widget & Chat Interface** | 3a. Widget Core Logic | - | Develop the core JavaScript modules for the widget: `state.js` for managing state, `api.js` for backend communication, and `handlers.js` for event listeners. | June 6 - June 12 |
| **Phase 2: Finalization for Submission (June 13, 2025 – August 2025)** |
| **4. Refinement & Testing** | 4a. Widget UI Polish | - | Design and implement the widget's chat interface (CSS and HTML structure). Ensure it is responsive and user-friendly. | June 13 - June 20 |
| | 4b. Dashboard Chat Page | - | Build the full `ChatPage` in the dashboard, including message display, input form, and conversation history state. | June 21 - June 30 |
| | 4c. Backend Refactoring | Refactor backend services for better separation of concerns. Standardize API response formats and error handling. | - | July 1 - July 10 |
| | 4d. Frontend Refactoring | Refactor React components to improve reusability and performance. Optimize state management to prevent unnecessary re-renders. | - | July 11 - July 20 |
| | 4e. Backend Testing | Write `pytest` unit tests for all critical services (Auth, RAG) and integration tests for the main API endpoints. | - | July 21 - July 28 |
| | 4f. Frontend Testing | - | Write unit tests for key components (e.g., forms, chat display) using Jest and React Testing Library. | July 29 - Aug 5 |
| **5. Documentation & Submission** | 5a. API Documentation | Document all public API endpoints, including request/response formats. Consider using a tool like Swagger/OpenAPI. | - | Aug 6 - Aug 12 |
| | 5b. Project READMEs | Write a comprehensive `README.md` for the backend, detailing setup, environment variables, and how to run the server. | Write comprehensive `README.md` files for the frontend and widget, detailing setup, build process, and usage. | Aug 13 - Aug 20 |
| | 5c. Final E2E Testing | **(Together)** Perform a final, thorough end-to-end test of all user stories and features to catch any remaining issues. | **(Together)** Perform a final, thorough end-to-end test of all user stories and features to catch any remaining issues. | Aug 21 - Aug 25 |
| | 5d. Final Submission | **(Together)** Clean up the codebases, remove any unnecessary files or logs, create production builds, and package the project for final submission. | **(Together)** Clean up the codebases, remove any unnecessary files or logs, create production builds, and package the project for final submission. | Aug 26 - Aug 31 |