import requests
import json
import time
from flask import current_app

# Configuration
CHATBOT_ID = "19"
API_KEY = "66uKW9wgZyYw9kxZKmD-l8FLk9cOoSNs8sn6me8GDQE" # Make sure this is the correct API key for backend authentication if needed
API_BASE_URL = "http://localhost:5001" # Assuming the backend runs locally on port 5001
OUTPUT_FILE = "rag_benchmark_results.json"

RETRIEVAL_EVAL_DATASET = [
    {
        "question_id": "BARTLEBY_02",
        "question": "When Bartleby declined tasks, what was his characteristic phrase?",
        "ground_truth_answer": "\"I would prefer not to.\"",
        "expected_chunk_texts": ["Imagine my surprise, nay, my consternation, when without moving from his privacy, Bartleby in a singularly mild, firm voice, replied, “I would prefer not to.”"],
        "key_phrases_for_hit": ["i would prefer not to"]
    },
    {
        "question_id": "BARTLEBY_06",
        "question": "What specific aspect of Nippers' desk caused him constant dissatisfaction?",
        "ground_truth_answer": "Its height; he could never adjust it to his satisfaction.",
        "expected_chunk_texts": ["Though of a very ingenious mechanical turn, Nippers could never get this table to suit him."],
        "key_phrases_for_hit": ["nippers", "table", "suit him", "height"]
    },
    {
        "question_id": "BARTLEBY_07",
        "question": "What was one of Ginger Nut's responsibilities involving providing refreshments for Turkey and Nippers?",
        "ground_truth_answer": "He acted as a purveyor of cakes (like ginger-nuts) and apples for them.",
        "expected_chunk_texts": ["Not the least among the employments of Ginger Nut, as well as one which he discharged with the most alacrity, was his duty as cake and apple purveyor for Turkey and Nippers."],
        "key_phrases_for_hit": ["ginger nut", "cake and apple purveyor", "turkey and nippers"]
    },
    {
        "question_id": "BARTLEBY_11",
        "question": "List at least three specific items the narrator found that served as evidence Bartleby was living in the office.",
        "ground_truth_answer": "Any three of: a blanket, a blacking box and brush, a tin basin with soap and a ragged towel, or crumbs of ginger-nuts and a morsel of cheese.",
        "expected_chunk_texts": ["Rolled away under his desk, I found a blanket; under the empty grate, a blacking box and brush; on a chair, a tin basin, with soap and a ragged towel; in a newspaper a few crumbs of ginger-nuts and a morsel of cheese."],
        "key_phrases_for_hit": ["blanket", "blacking box", "tin basin", "ginger-nuts", "morsel of cheese"]
    },
    {
        "question_id": "BARTLEBY_13",
        "question": "After Bartleby's persistent refusal to leave the original chambers, what was the narrator's ultimate strategy to separate himself from Bartleby?",
        "ground_truth_answer": "He moved his legal offices to a new location.",
        "expected_chunk_texts": ["Since he will not quit me, I must quit him. I will change my offices; I will move elsewhere; and give him fair notice, that if I find him on my new premises I will then proceed against him as a common trespasser."],
        "key_phrases_for_hit": ["change my offices", "move elsewhere"]
    },
    {
        "question_id": "BARTLEBY_19",
        "question": "What was the unconfirmed rumor regarding Bartleby's occupation prior to working for the narrator?",
        "ground_truth_answer": "That he had been a subordinate clerk in the Dead Letter Office at Washington.",
        "expected_chunk_texts": ["The report was this: that Bartleby had been a subordinate clerk in the Dead Letter Office at Washington, from which he had been suddenly removed by a change in the administration."],
        "key_phrases_for_hit": ["dead letter office", "subordinate clerk"]
    },
    {
        "question_id": "BARTLEBY_23",
        "question": "When asked his opinion on Bartleby's refusal to examine papers, what was Ginger Nut's assessment of Bartleby?",
        "ground_truth_answer": "Ginger Nut said, \"I think, sir, he’s a little luny.\"",
        "expected_chunk_texts": ["“I think, sir, he’s a little luny,” replied Ginger Nut with a grin."],
        "key_phrases_for_hit": ["little luny"]
    },
    {
        "question_id": "YW_28",
        "question": "What primary activity, crucial to the narrator's sense of self, does her husband John forbid until she \"is well again\"?",
        "ground_truth_answer": "Work, which for her specifically means writing.",
        "expected_chunk_texts": ["So I take phosphates or phosphites—whichever it is, and tonics, and journeys, and air, and exercise, and am absolutely forbidden to “work” until I am well again."],
        "key_phrases_for_hit": ["forbidden to work", "writing"]
    },
    {
        "question_id": "YW_32",
        "question": "Who is Jennie, and what is her explicit familial relationship to John as stated in the text?",
        "ground_truth_answer": "Jennie is John's sister.",
        "expected_chunk_texts": ["There comes John’s sister. Such a dear girl as she is, and so careful of me! I must not let her find me writing."],
        "key_phrases_for_hit": ["john’s sister"]
    },
    {
        "question_id": "YW_37",
        "question": "What specific feature of the windows in their room (the nursery) suggests its previous use for children?",
        "ground_truth_answer": "The windows are barred.",
        "expected_chunk_texts": ["It was nursery first and then playground and gymnasium, I should judge; for the windows are barred for little children, and there are rings and things in the walls."],
        "key_phrases_for_hit": ["windows are barred", "little children"]
    },
    {
        "question_id": "YW_38",
        "question": "Beyond its visual appearance, what distinct sensory characteristic of the wallpaper does the narrator describe, noting it becomes particularly strong in damp weather?",
        "ground_truth_answer": "Its peculiar and enduring smell, which she describes as a \"yellow smell.\"",
        "expected_chunk_texts": ["But there is something else about that paper—the smell! I noticed it the moment we came into the room, but with so much air and sun it was not bad. Now we have had a week of fog and rain, and whether the windows are open or not, the smell is here... In this damp weather it is awful."],
        "key_phrases_for_hit": ["smell", "yellow smell", "damp weather"]
    },
    {
        "question_id": "YW_42",
        "question": "What object does the narrator mention having hidden in the room to potentially restrain the woman from the wallpaper if she gets out and tries to escape?",
        "ground_truth_answer": "A rope.",
        "expected_chunk_texts": ["I’ve got a rope up here that even Jennie did not find. If that woman does get out, and tries to get away, I can tie her!"],
        "key_phrases_for_hit": ["rope", "tie her"]
    },
    {
        "question_id": "YW_45",
        "question": "What is John's immediate physical reaction when he sees his wife's state and the condition of the room on the final day?",
        "ground_truth_answer": "He faints.",
        "expected_chunk_texts": ["Now why should that man have fainted? But he did, and right across my path by the wall, so that I had to creep over him every time!"],
        "key_phrases_for_hit": ["man have fainted", "he did"]
    },
    {
        "question_id": "YW_47",
        "question": "When the narrator first voices her feeling that there is \"something queer\" about the house, how does John dismiss her concern?",
        "ground_truth_answer": "He attributes her feeling to a draught and shuts the window.",
        "expected_chunk_texts": ["I even said so to John one moonlight evening, but he said what I felt was a draught, and shut the window."],
        "key_phrases_for_hit": ["something queer", "draught", "shut the window"]
    },
    {
        "question_id": "YW_49",
        "question": "If the narrator's condition didn't improve, to which well-known physician of the era (known for his \"rest cure\") did John say he would send her?",
        "ground_truth_answer": "Weir Mitchell.",
        "expected_chunk_texts": ["John says if I don’t pick up faster he shall send me to Weir Mitchell in the fall."],
        "key_phrases_for_hit": ["weir mitchell"]
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

def get_raw_retrieved_texts(question_text, chatbot_id_str, session_id_str, use_advanced_rag_bool):
    """
    Calls the existing query_chatbot API and extracts the raw retrieved texts.
    """
    print(f"Getting raw retrieved texts for: '{question_text}' (Advanced: {use_advanced_rag_bool})")
    api_response = query_chatbot(question_text, session_id_str, use_advanced_rag=use_advanced_rag_bool)
    
    if api_response and "retrieved_raw_texts" in api_response and isinstance(api_response["retrieved_raw_texts"], list):
        return api_response["retrieved_raw_texts"]
    elif api_response:
        print(f"Warning: 'retrieved_raw_texts' not found or not a list in API response for '{question_text}'. Full response: {api_response}")
        return []
    else:
        return []

def run_retrieval_evaluation(dataset, chatbot_id_to_test, rag_mode_is_advanced, rag_mode_name):
    hit_count = 0
    mrr_score = 0.0
    
    # Make a mutable copy for total_queries if items are skipped
    queries_to_evaluate = [item for item in dataset if item.get("key_phrases_for_hit")]
    initial_total_queries = len(dataset)
    evaluated_queries_count = 0

    K = 10 # Using fixed K as in original script, not from current_app
    
    all_precisions_at_k = []
    all_recalls_at_k = []

    session_id = f"retrieval_eval_{rag_mode_name}_{int(time.time())}"

    for item_idx, item in enumerate(dataset): # Use enumerate for original index if needed
        question = item["question"]
        key_phrases = item.get("key_phrases_for_hit", [])

        if not key_phrases:
            print(f"WARNING: No key_phrases_for_hit defined for question_id: {item.get('question_id', 'N/A')} ('{question}'). Skipping this question for retrieval eval.")
            continue # Skip this item if no key phrases
        
        evaluated_queries_count += 1
        print(f"\nEvaluating retrieval for Q ({item.get('question_id', 'N/A')}): {question}")
        retrieved_chunk_texts_from_rag = get_raw_retrieved_texts(question, chatbot_id_to_test, session_id, rag_mode_is_advanced)
        
        if not retrieved_chunk_texts_from_rag:
            print(f"  No chunks retrieved by RAG for this question. Marking as Miss.")
        
        # The user's log already prints this in get_raw_retrieved_texts, but let's keep a summary here too.
        # The previous diff added a print for misses, this new logic has a more general print.
        # Let's adapt the user's suggested print for all cases.
        print(f"  Retrieved texts for this query (top {len(retrieved_chunk_texts_from_rag[:K])}):")
        for i_debug, retrieved_text_debug in enumerate(retrieved_chunk_texts_from_rag[:K]):
            print(f"    Chunk {i_debug+1}: {retrieved_text_debug[:150].replace(chr(13), ' ').replace(chr(10), ' ')}...") # Replace CR/LF for cleaner one-line print

        found_relevant_chunk_for_query = False # Has any chunk been found relevant for *this query*?
        rank_of_first_hit = 0 # Rank of the first chunk that was relevant for this query
        
        relevant_retrieved_chunks_count_for_precision = 0 # How many of the K retrieved chunks are relevant
        any_key_phrase_found_for_recall = False # For this query, was any of its key phrases found in top K?

        for i, retrieved_text_content in enumerate(retrieved_chunk_texts_from_rag[:K]):
            current_chunk_is_relevant_for_precision = False # Is *this specific retrieved chunk* relevant?
            for phrase in key_phrases:
                if phrase.lower() in retrieved_text_content.lower():
                    any_key_phrase_found_for_recall = True # Mark that at least one key phrase was found for the query's recall
                    current_chunk_is_relevant_for_precision = True # Mark this specific chunk as relevant for precision
                    
                    if not found_relevant_chunk_for_query: # This is the first time we're finding a relevant chunk for this query
                        rank_of_first_hit = i + 1
                        # hit_count and mrr_score are updated *after* iterating through all K chunks for this query,
                        # but based on this rank_of_first_hit.
                    print(f"  Relevant key phrase '{phrase}' FOUND in retrieved chunk {i+1}.")
                    break # Stop checking other key_phrases for *this* retrieved_text_content; it's already deemed relevant.
            
            if current_chunk_is_relevant_for_precision:
                relevant_retrieved_chunks_count_for_precision += 1
                if not found_relevant_chunk_for_query: # This ensures we log the first hit correctly
                     # Log that this specific chunk is the first one contributing to a "hit" for the query
                    print(f"    -> This chunk (Rank {i+1}) is the first relevant hit for this query.")
                    found_relevant_chunk_for_query = True # Mark that we've now found the first relevant chunk for this query.
        
        # After checking all K retrieved chunks for the current query:
        if found_relevant_chunk_for_query:
            hit_count += 1 # Query is a "hit" if at least one relevant chunk was found in top K
            mrr_score += (1 / rank_of_first_hit) # Add to MRR score
            print(f"  Hit! First relevant chunk for this query was at rank: {rank_of_first_hit}")
        else:
            print(f"  Miss! No predefined relevant key phrases found in top {K} retrieved for this query.")

        precision_at_k = relevant_retrieved_chunks_count_for_precision / K if K > 0 else 0
        all_precisions_at_k.append(precision_at_k)
        print(f"  Precision@{K} for this query: {precision_at_k:.2f} ({relevant_retrieved_chunks_count_for_precision}/{K})")
        
        recall_for_this_query = 1.0 if any_key_phrase_found_for_recall else 0.0
        all_recalls_at_k.append(recall_for_this_query)
        print(f"  Recall@{K} for this query (found any key phrase): {recall_for_this_query:.2f}")

    # Final calculations based on queries that were actually evaluated
    if evaluated_queries_count == 0:
        print("\nNo queries were evaluated (e.g., all lacked key_phrases_for_hit). Metrics cannot be calculated.")
        final_hit_rate = 0.0
        final_mrr = 0.0
        final_avg_precision_at_k = 0.0
        final_avg_recall_at_k = 0.0
    else:
        final_hit_rate = (hit_count / evaluated_queries_count) * 100
        final_mrr = mrr_score / evaluated_queries_count
        final_avg_precision_at_k = sum(all_precisions_at_k) / evaluated_queries_count
        final_avg_recall_at_k = sum(all_recalls_at_k) / evaluated_queries_count
    
    print(f"\n--- Retrieval Metrics Summary ({rag_mode_name} RAG) ---")
    print(f"Total Queries in Dataset: {initial_total_queries}")
    print(f"Queries Evaluated (with key_phrases): {evaluated_queries_count}")
    print(f"Hit Rate (at least one relevant chunk in top K): {final_hit_rate:.2f}%")
    print(f"Mean Reciprocal Rank (MRR): {final_mrr:.3f}")
    print(f"Average Precision@{K}: {final_avg_precision_at_k:.3f}")
    print(f"Average Recall@{K} (found any key aspect): {final_avg_recall_at_k:.3f}")

    return {
        "total_queries_in_dataset": initial_total_queries,
        "queries_evaluated": evaluated_queries_count,
        "hit_rate": final_hit_rate,
        "mrr": final_mrr,
        "avg_precision_at_k": final_avg_precision_at_k,
        "avg_recall_at_k": final_avg_recall_at_k,
        "k_value_for_metrics": K
    }

def run_benchmark(mode):
    """Runs the benchmark and saves the results."""
    all_run_results = {"end_to_end_qa": [], "retrieval_evaluation": {}}
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
        
        print(f"\n--- Starting RETRIEVAL EVALUATION for {rag_mode_name.upper()} RAG ---")
        retrieval_metrics = run_retrieval_evaluation(RETRIEVAL_EVAL_DATASET, CHATBOT_ID, rag_mode_is_advanced, rag_mode_name)
        all_run_results["retrieval_evaluation"][rag_mode_name] = retrieval_metrics

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(all_run_results, f, indent=4, ensure_ascii=False)

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
