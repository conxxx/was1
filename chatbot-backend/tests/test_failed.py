import requests
import json
import time

# Configuration
CHATBOT_ID = "19"
API_KEY = "66uKW9wgZyYw9kxZKmD-l8FLk9cOoSNs8sn6me8GDQE" # Make sure this is the correct API key for backend authentication if needed
API_BASE_URL = "http://localhost:5001" # Assuming the backend runs locally on port 5001
OUTPUT_FILE = "rag_failed_questions_results.json"

QUESTIONS_ANSWERS = [
    {
        "question": "When Bartleby first refused to examine his own completed copies, what was Turkey's immediate, vocally expressed reaction when the narrator sought his opinion?",
        "expected_answer": "He angrily roared a threat to step behind Bartleby's screen and black his eyes."
    },
    {
        "question": "In reflecting on Bartleby's profound isolation and nature before the narrator decided to give him formal notice to leave, what striking metaphor did the narrator use to describe Bartleby?",
        "expected_answer": "He described Bartleby as \"A bit of wreck in the mid Atlantic.\""
    },
    {
        "question": "After moving offices, the narrator was informed Bartleby was \"haunting the building generally.\" What specific places was Bartleby reported to be occupying?",
        "expected_answer": "Sitting upon the banisters of the stairs by day and sleeping in the entry by night."
    },
    {
        "question": "The narrator considers it \"fortunate Mary is so good with the baby.\" What personal reason, stemming from her own condition, does she give that makes Mary's competence particularly relieving for her?",
        "expected_answer": "It is particularly fortunate for her because she herself cannot be with the baby, as doing so makes her excessively nervous."
    },
    {
        "question": "What is Jennie's opinion (which the narrator believes) about what made the narrator sick?",
        "expected_answer": "The narrator verily believes Jennie thinks it is the writing which made her sick."
    },
    {
        "question": "Why does the narrator say she doesn't want to leave the house \"until I have found it out\"?",
        "expected_answer": "She wants to find out about the woman/pattern in the wallpaper."
    },
    {
        "question": "What does the narrator intend to do, \"little by little,\" regarding the wallpaper patterns?",
        "expected_answer": "She means to try to get the top pattern off from the under one."
    },
    {
        "question": "When the narrator is creeping on the final day, what is her stated reason for not wanting to go outside?",
        "expected_answer": "Because outside you have to creep on the ground, and everything is green instead of yellow, whereas in the room she can creep smoothly."
    }
]

def query_chatbot(question_text, session_id, use_advanced_rag: bool):
    """Sends a question to the chatbot and returns the response."""
    endpoint = f"{API_BASE_URL}/api/chatbots/{CHATBOT_ID}/query"
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "query": question_text,
        "session_id": session_id,
        "language": "en",
        "use_advanced_rag": use_advanced_rag
    }
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error querying chatbot for question '{question_text}': {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print(f"Response content: {e.response.json()}")
            except json.JSONDecodeError:
                print(f"Response content (not JSON): {e.response.text}")
        return None

def run_benchmark(mode):
    """Runs the benchmark and saves the results."""
    results = []
    session_id_standard = f"benchmark_session_standard_{int(time.time())}"
    session_id_advanced = f"benchmark_session_advanced_{int(time.time())}"

    modes_to_run = []
    if mode == "standard":
        modes_to_run = [False]
    elif mode == "advanced":
        modes_to_run = [True]
    elif mode == "both":
        modes_to_run = [False, True]

    for rag_mode_is_advanced in modes_to_run:
        if rag_mode_is_advanced:
            rag_mode_name = "advanced"
            session_id = session_id_advanced
        else:
            rag_mode_name = "standard"
            session_id = session_id_standard
        
        print(f"\n--- Starting benchmark for {rag_mode_name.upper()} RAG with session ID: {session_id} ---")

        for i, qa_pair in enumerate(QUESTIONS_ANSWERS):
            question = qa_pair["question"]
            expected_answer = qa_pair["expected_answer"]
            print(f"Asking question {i+1}/{len(QUESTIONS_ANSWERS)} ({rag_mode_name} RAG): {question}")

            api_response = query_chatbot(question, session_id, use_advanced_rag=rag_mode_is_advanced)
            actual_answer = None
            raw_response = None

            if api_response:
                raw_response = api_response
                if 'answer' in api_response and api_response['answer'] is not None:
                    actual_answer = api_response['answer']
                elif 'response' in api_response and api_response['response'] is not None:
                    actual_answer = api_response['response']
                else:
                    actual_answer = "Error: No 'answer' or 'response' field in API response"
                    print(f"Warning: No 'answer' or 'response' field in API response for question: {question} ({rag_mode_name} RAG)")
                    print(f"Full API response: {api_response}")
            else:
                actual_answer = "Error: Failed to get response from API"

            results.append({
                "question_id": i + 1,
                "rag_mode": rag_mode_name,
                "question": question,
                "expected_answer": expected_answer,
                "actual_answer": actual_answer,
                "raw_response": raw_response,
                "session_id": session_id
            })
            print(f"  Expected: {expected_answer}")
            print(f"  Actual ({rag_mode_name}):   {actual_answer}")
            time.sleep(1)

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)

    print(f"\nBenchmark complete. Results saved to {OUTPUT_FILE}")

if __name__ == "__main__":
    while True:
        print("\nSelect RAG mode to test:")
        print("1. Standard RAG")
        print("2. Advanced RAG")
        print("3. Both Standard and Advanced RAG")
        choice = input("Enter your choice (1, 2, or 3): ")

        if choice == '1':
            selected_mode = "standard"
            break
        elif choice == '2':
            selected_mode = "advanced"
            break
        elif choice == '3':
            selected_mode = "both"
            break
        else:
            print("Invalid choice. Please enter 1, 2, or 3.")
    
    run_benchmark(selected_mode)
