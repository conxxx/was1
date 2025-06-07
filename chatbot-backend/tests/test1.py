import requests
import json
import time

# Configuration
CHATBOT_ID = "19"
API_KEY = "66uKW9wgZyYw9kxZKmD-l8FLk9cOoSNs8sn6me8GDQE" # Make sure this is the correct API key for backend authentication if needed
API_BASE_URL = "http://localhost:5001" # Assuming the backend runs locally on port 5001
OUTPUT_FILE = "rag_benchmark_results.json"

QUESTIONS_ANSWERS = [
    {
        "question": "What was the narrator's primary legal role before becoming a Master in Chancery in \"Bartleby, the Scrivener\"?",
        "expected_answer": "He was a lawyer specializing as a conveyancer and title hunter."
    },
    {
        "question": "When Bartleby declined tasks, what was his characteristic phrase?",
        "expected_answer": "\"I would prefer not to.\""
    },
    {
        "question": "Excluding Bartleby, who were the narrator's three named clerks at the story's outset?",
        "expected_answer": "Turkey, Nippers, and Ginger Nut."
    },
    {
        "question": "On which famous New York street were the narrator's legal chambers located?",
        "expected_answer": "Wall-street (specifically No.—Wall-street)."
    },
    {
        "question": "Describe the significant negative changes in Turkey's work performance and behavior after his midday meal.",
        "expected_answer": "After his midday meal (around twelve o’clock), Turkey's face would blaze, his business capacities were disturbed, he became overly energetic, reckless, made blots, was noisy, and could be insolent or combative."
    },
    {
        "question": "What specific aspect of Nippers' desk caused him constant dissatisfaction?",
        "expected_answer": "Its height; he could never adjust it to his satisfaction."
    },
    {
        "question": "What was one of Ginger Nut's responsibilities involving providing refreshments for Turkey and Nippers?",
        "expected_answer": "He acted as a purveyor of cakes (like ginger-nuts) and apples for them."
    },
    {
        "question": "Describe Bartleby's work output during his initial period of employment.",
        "expected_answer": "He initially produced an extraordinary quantity of writing, working day and night as if famishing to copy."
    },
    {
        "question": "What was the very first task the narrator requested of Bartleby which prompted the reply, \"I would prefer not to\"?",
        "expected_answer": "To help examine a small paper by comparing a copy to the original."
    },
    {
        "question": "What did the narrator eventually deduce Bartleby had been doing in the office after encountering him there on a Sunday morning and later inspecting the premises?",
        "expected_answer": "The narrator deduced Bartleby had been living in the office—eating, dressing, and sleeping there."
    },
    {
        "question": "List at least three specific items the narrator found that served as evidence Bartleby was living in the office.",
        "expected_answer": "Any three of: a blanket, a blacking box and brush, a tin basin with soap and a ragged towel, or crumbs of ginger-nuts and a morsel of cheese."
    },
    {
        "question": "What definitive statement did Bartleby eventually make to the narrator about his willingness to continue copying?",
        "expected_answer": "He stated he had \"permanently given up copying.\""
    },
    {
        "question": "After Bartleby's persistent refusal to leave the original chambers, what was the narrator's ultimate strategy to separate himself from Bartleby?",
        "expected_answer": "He moved his legal offices to a new location."
    },
    {
        "question": "Who first alerted the narrator that Bartleby was still present at the old Wall-street chambers after the narrator had relocated his office?",
        "expected_answer": "A perturbed-looking stranger, who was a lawyer and the new tenant of the narrator's former chambers."
    },
    {
        "question": "What was the name of the prison (also called the Halls of Justice) where Bartleby was taken as a vagrant?",
        "expected_answer": "The Tombs."
    },
    {
        "question": "What did the narrator pay the \"grub-man,\" Mr. Cutlets, to do for Bartleby in the Tombs?",
        "expected_answer": "He paid him to provide Bartleby with good food, specifically the best dinner possible, and to treat him politely."
    },
    {
        "question": "What was Bartleby's complete stated reason for declining Mr. Cutlets' dinner invitation in prison?",
        "expected_answer": "\"I prefer not to dine to-day. It would disagree with me; I am unused to dinners.\""
    },
    {
        "question": "Describe Bartleby's physical state and condition when the narrator found him for the last time in the prison yard.",
        "expected_answer": "He was found lying strangely huddled at the base of a wall, his eyes open but unseeing; he was dead."
    },
    {
        "question": "What was the unconfirmed rumor regarding Bartleby's occupation prior to working for the narrator?",
        "expected_answer": "That he had been a subordinate clerk in the Dead Letter Office at Washington."
    },
    {
        "question": "Which two principal characteristics did the narrator claim the late John Jacob Astor recognized in him?",
        "expected_answer": "Prudence and method."
    },
    {
        "question": "Besides examining papers, list two examples of simple errands or tasks Bartleby refused to perform for the narrator.",
        "expected_answer": "He refused to go to the Post Office and refused to go to the next room to tell Nippers to come to the narrator."
    },
    {
        "question": "During an afternoon when Bartleby declined to check his copies, what did Turkey angrily threaten to do?",
        "expected_answer": "Turkey threatened to \"step behind his screen, and black his eyes for him!\""
    },
    {
        "question": "When asked his opinion on Bartleby's refusal to examine papers, what was Ginger Nut's assessment of Bartleby?",
        "expected_answer": "Ginger Nut said, \"I think, sir, he’s a little luny.\""
    },
    {
        "question": "Based on the narrator's observations of Ginger Nut's deliveries to Bartleby's \"hermitage,\" what food item did Bartleby appear to mainly eat?",
        "expected_answer": "Ginger-nuts."
    },
    {
        "question": "When the narrator, before moving offices, offered Bartleby money and told him to leave, what was Bartleby's physical reaction to the offered money?",
        "expected_answer": "He made no motion to take the money."
    },
    {
        "question": "What is the medical profession of John, the husband of the narrator in \"The Yellow Wallpaper\"?",
        "expected_answer": "He is a physician."
    },
    {
        "question": "What romanticized, albeit quickly dismissed, explanation does the narrator initially consider for why their summer rental, a colonial mansion, was let so cheaply?",
        "expected_answer": "She speculates it might be a haunted house."
    },
    {
        "question": "What primary activity, crucial to the narrator's sense of self, does her husband John forbid until she \"is well again\"?",
        "expected_answer": "Work, which for her specifically means writing."
    },
    {
        "question": "In which specific room of the colonial mansion, initially much to her displeasure, does John insist they stay?",
        "expected_answer": "The large nursery at the top of the house."
    },
    {
        "question": "Which particular decorative element in their room becomes the central object of the narrator's escalating fixation?",
        "expected_answer": "The yellow wallpaper."
    },
    {
        "question": "Quote some of the narrator's key descriptive terms for the color of the wallpaper, highlighting its unpleasantness.",
        "expected_answer": "Repellant, almost revolting; a smouldering, unclean yellow; dull yet lurid orange; sickly sulphur tint; hideous."
    },
    {
        "question": "Who is Jennie, and what is her explicit familial relationship to John as stated in the text?",
        "expected_answer": "Jennie is John's sister."
    },
    {
        "question": "As her obsession grows, what primary figure or figures does the narrator begin to perceive moving behind the front pattern of the wallpaper?",
        "expected_answer": "She perceives a woman (or sometimes many women) stooping, creeping, and shaking the pattern from behind."
    },
    {
        "question": "List at least three components of the \"rest cure\" or treatment regimen John (and her brother, also a physician) prescribe for the narrator's nervous condition.",
        "expected_answer": "Any three of: perfect rest, all the air possible, phosphates or phosphites, tonics, journeys, specific exercises, a regulated diet, and a strict prohibition on intellectual work (especially writing)."
    },
    {
        "question": "According to John's medical opinion, what is the most detrimental thing for a person with the narrator's \"temperament\" or \"nervous weakness\" to do?",
        "expected_answer": "To think about her condition or give way to fancies."
    },
    {
        "question": "What type of activity does the narrator personally and secretly believe would be beneficial for her recovery, contrary to John's orders?",
        "expected_answer": "Congenial work, with excitement and change (which for her includes writing)."
    },
    {
        "question": "What specific feature of the windows in their room (the nursery) suggests its previous use for children?",
        "expected_answer": "The windows are barred."
    },
    {
        "question": "Beyond its visual appearance, what distinct sensory characteristic of the wallpaper does the narrator describe, noting it becomes particularly strong in damp weather?",
        "expected_answer": "Its peculiar and enduring smell, which she describes as a \"yellow smell.\""
    },
    {
        "question": "What is the \"long, straight, even smooch\" the narrator observes on the wall near the mopboard, circling the room?",
        "expected_answer": "It's a mark as if something had been rubbed over and over along the wall, into which her shoulder later fits as she creeps."
    },
    {
        "question": "What does the narrator claim to have seen the woman from the wallpaper doing outside the room during the daytime?",
        "expected_answer": "She claims to have seen her (and other women) creeping in the garden, the lane, and under the trees."
    },
    {
        "question": "On the final day, when John is due to return, what reason does the narrator give herself for locking the nursery door and throwing the key away?",
        "expected_answer": "She wants to astonish John and does not want anyone to enter until he arrives."
    },
    {
        "question": "What object does the narrator mention having hidden in the room to potentially restrain the woman from the wallpaper if she gets out and tries to escape?",
        "expected_answer": "A rope."
    },
    {
        "question": "After failing to move the heavy, nailed-down bedstead, what does the narrator do to it in her frustration?",
        "expected_answer": "She bites off a little piece at one corner of the bedstead."
    },
    {
        "question": "When John finally breaks into the room, what triumphant declaration does the narrator make to him regarding her escape and the wallpaper?",
        "expected_answer": "\"I’ve got out at last... in spite of you and Jane [Jennie]! And I’ve pulled off most of the paper, so you can’t put me back!\""
    },
    {
        "question": "What is John's immediate physical reaction when he sees his wife's state and the condition of the room on the final day?",
        "expected_answer": "He faints."
    },
    {
        "question": "After John faints across her path by the wall, what does the narrator find herself compelled to do repeatedly?",
        "expected_answer": "She has to creep over his fainted body."
    },
    {
        "question": "When the narrator first voices her feeling that there is \"something queer\" about the house, how does John dismiss her concern?",
        "expected_answer": "He attributes her feeling to a draught and shuts the window."
    },
    {
        "question": "What sequence of fixations did John predict the narrator would develop if he were to change the yellow wallpaper?",
        "expected_answer": "He said she would then fixate on the heavy bedstead, then the barred windows, and then the gate at the head of the stairs."
    },
    {
        "question": "If the narrator's condition didn't improve, to which well-known physician of the era (known for his \"rest cure\") did John say he would send her?",
        "expected_answer": "Weir Mitchell."
    },
    {
        "question": "What specific actions by John and Jennie does the narrator observe that lead her to believe they are also being secretly affected by the wallpaper?",
        "expected_answer": "She has caught John looking at the paper multiple times, and she caught Jennie with her hand on the paper once."
    }
]

def query_chatbot(question_text, session_id, use_advanced_rag: bool):
    """Sends a question to the chatbot and returns the response."""
    endpoint = f"{API_BASE_URL}/api/chatbots/{CHATBOT_ID}/query"
    headers = {
        "Authorization": f"Bearer {API_KEY}", # This is likely for widget config, backend might use different auth
        "Content-Type": "application/json",
        "Accept": "application/json"
    }
    payload = {
        "query": question_text,
        "session_id": session_id, # The API expects a session_id
        "language": "en", # Assuming English for now
        "use_advanced_rag": use_advanced_rag
    }
    try:
        response = requests.post(endpoint, headers=headers, json=payload, timeout=60)
        response.raise_for_status()  # Raise an exception for bad status codes
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
                raw_response = api_response # Store the full response
                if 'answer' in api_response and api_response['answer'] is not None:
                    actual_answer = api_response['answer']
                elif 'response' in api_response and api_response['response'] is not None: # Fallback, though 'answer' is preferred
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
            # Optional: Add a small delay between requests if needed
            # time.sleep(1)

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
