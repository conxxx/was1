## 5. Scenarios

This section outlines typical user stories and system processes, illustrating how users interact with the platform and how the system responds to those interactions.

### 5.1 Website AI Assistant (WAS) Scenarios

#### 5.1.1 User Story: Administrator Creates and Deploys a New Chatbot

**Actor:** A website administrator.

**Goal:** To create a new chatbot, train it on the company's public FAQ page, customize its appearance, and deploy it to the website.

**Process:**

1.  **Login:** The administrator navigates to the WAS platform's web dashboard and logs in with their credentials.
2.  **Create Chatbot:** From the main dashboard, the administrator clicks "Create New Chatbot." They give the chatbot a name, "Company FAQ Bot," and save it.
3.  **Add Data Source:** The administrator navigates to the "Data Sources" tab for the new chatbot. They select the "URL" option and paste the web address of their company's FAQ page (e.g., `https://mycompany.com/faq`).
4.  **System Ingestion Process:**
    *   The backend receives the request and queues an asynchronous ingestion task using Celery.
    *   A web crawling worker fetches the HTML content from the provided URL.
    *   The system parses the HTML, extracts the main textual content, and cleans it.
    *   The cleaned text is segmented into smaller, semantically meaningful chunks.
    *   Each chunk is passed to a text embedding model, which converts it into a vector.
    *   These vectors are stored and indexed in a specialized vector database, associated with the "Company FAQ Bot."
    *   The dashboard updates to show the FAQ page as a successfully ingested data source.
5.  **Customize Appearance:** The administrator goes to the "Customization" tab. They change the widget's primary color to match their company's branding and update the "Launcher Text" to say "Ask us anything!"
6.  **Test the Chatbot:** The administrator uses the built-in chat interface in the dashboard to test the chatbot. They ask, "What are your business hours?" The system retrieves the relevant context from the ingested FAQ page and generates an accurate answer.
7.  **Deploy to Website:** Satisfied with the result, the administrator copies the provided JavaScript snippet and embeds it into their website's HTML. The "Company FAQ Bot" launcher now appears on their live site, ready to assist visitors.

#### 5.1.2 User Story: End-User Asks a Question via Voice

**Actor:** A visitor on the company's website.

**Goal:** To find out the company's return policy without having to search the website manually.

**Process:**

1.  **Initiate Interaction:** The visitor sees the "Ask us anything!" launcher on the website and clicks it, opening the chat widget.
2.  **Start Voice Input:** The visitor clicks the microphone icon in the chat widget. The browser prompts for microphone access, which the user grants.
3.  **Ask Question:** The visitor speaks their question: "What is your return policy?"
4.  **System Voice-to-Text Process:**
    *   The widget's JavaScript captures the audio stream.
    *   The audio data is sent to the WAS backend's speech-to-text endpoint.
    *   The backend uses a cloud-based STT service (e.g., Google Cloud Speech-to-Text) to transcribe the audio into the text "What is your return policy?".
    *   The transcribed text is returned to the widget and displayed in the chat window.
5.  **System RAG Process:**
    *   The backend receives the transcribed query.
    *   The RAG service converts the query into a vector and searches the vector database for the most relevant text chunks from the ingested company documents.
    *   The top-matching chunks, which contain details about the return policy, are retrieved.
    *   These chunks are combined with the user's query into a prompt for the LLM.
    *   The LLM generates a concise answer summarizing the return policy based on the provided context.
6.  **Receive Answer:** The generated text answer is displayed in the chat widget. Because the user initiated the query with voice, the system also sends the text to a TTS service to generate an audio version of the response.
7.  **Audio Playback:** The audio response is streamed back to the widget, which automatically plays it for the user. The user sees the text answer and hears the spoken response simultaneously.

### 5.2 Agentic Chatbot Scenario

#### 5.2.1 User Story: Customer Modifies an Order and Schedules a Service

**Actor:** A returning customer of a home and garden store.

**Goal:** To get advice on a recent purchase, modify their current shopping cart, and schedule a planting service.

**Process:**

1.  **Initiate Conversation:** The customer starts a conversation with the agent. The system recognizes the customer as "Alex" based on their (mocked) logged-in state.
2.  **Agent Greeting & Context:** The agent greets the customer by name and acknowledges items already in their shopping cart, demonstrating awareness of the user's state.
3.  **Customer Inquiry:** The customer explains they are unsure if they have the right soil for a plant they recently purchased.
4.  **Agent Tool Use (Video Identification):**
    *   The agent recognizes the ambiguity and determines it needs more information.
    *   **Tool Selected:** `send_call_companion_link`
    *   The agent calls the tool to send a secure video link to the customer's phone.
    *   The customer uses the link to show the plant to the agent. The agent (simulating multimodal input) identifies the plant.
5.  **Agent Tool Use (Recommendation & Cart Modification):**
    *   Based on the plant identification, the agent determines a better soil is available.
    *   **Tool Selected:** `get_product_recommendations`
    *   The agent recommends the appropriate soil and a suitable fertilizer.
    *   The customer agrees to the change.
    *   **Tool Selected:** `modify_cart`
    *   The agent calls the tool to remove the incorrect soil from the cart and add the recommended soil and fertilizer.
6.  **Agent Tool Use (Upselling & Scheduling):**
    *   The agent suggests a professional planting service for the new items.
    *   The customer expresses interest and asks for available times.
    *   **Tool Selected:** `get_available_planting_times`
    *   The agent retrieves and presents a list of open appointment slots.
    *   The customer chooses a time.
    *   **Tool Selected:** `schedule_planting_service`
    *   The agent books the appointment and confirms the details with the customer.
