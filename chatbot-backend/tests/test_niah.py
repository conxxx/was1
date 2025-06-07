import requests
import time
import os
import json
import math

# --- Configuration ---
BASE_URL = "http://localhost:5001/api"  # Updated backend API URL
# CLIENT_ID will be fetched/created via login
NEEDLE_SENTENCE = "The most interesting discovery reported in the archives was a talking cat named Whiskers."
QUESTION_TO_ASK = "What was the most interesting discovery reported in the archives?"

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ORIGINAL_HAYSTACK_FILE_PATH = os.path.join(SCRIPT_DIR, "..", "..", "combined_haystack.txt") # Path relative to script location

TEMP_HAYSTACK_UPLOAD_FILENAME = "niah_temp_haystack.txt"
# Path where Flask app expects uploads. If UPLOAD_FOLDER is 'uploads' at chatbot-backend root:
TEMP_HAYSTACK_SAVE_PATH = os.path.join(SCRIPT_DIR, "..", "uploads", TEMP_HAYSTACK_UPLOAD_FILENAME) # Relative to script location

# Approximate lengths for splitting "The Yellow Wallpaper" and "Bartleby"
# YW: ~6000 words, Bartleby: ~14500 words. Total ~20500.
# YW is roughly 6000/20500 = ~29% of the total.
PERCENT_YELLOW_WALLPAPER = 0.29

# --- Helper Functions ---

def print_test_step(message):
    print(f"\n[NIAH TEST] {message}")

# Removed get_all_chatbots and cleanup_all_existing_chatbots as per new strategy

def get_or_create_test_client_id(test_case_id):
    # Generate a unique email for each test case to ensure a new user
    unique_email = f"niah_user_{test_case_id}_{int(time.time())}@example.com"
    print_test_step(f"Ensuring test client/user exists with unique email: {unique_email} for Test Case: {test_case_id}")
    url = f"{BASE_URL}/login"
    payload = {"email": unique_email}
    try:
        response = requests.post(url, json=payload, timeout=30)
        response.raise_for_status()
        data = response.json()
        client_id = data.get("client_id")
        if client_id:
            print_test_step(f"Obtained client_id: {client_id} for email {unique_email}")
            return client_id
        else:
            print_test_step(f"ERROR: Did not receive client_id from login endpoint for email {unique_email}. Response: {data}")
            return None
    except requests.exceptions.RequestException as e:
        print_test_step(f"ERROR: API request failed during login/client creation for email {unique_email}: {e}")
        return None

def create_chatbot(client_id, test_case_name):
    print_test_step(f"Creating chatbot: {test_case_name} for client_id: {client_id}")
    url = f"{BASE_URL}/chatbots"
    payload = {
        "client_id": client_id,
        "name": test_case_name,
        "advanced_rag_enabled": False,
        # Add other minimal required fields if any, otherwise defaults will be used
    }
    print_test_step(f"Sending chatbot creation payload: {json.dumps(payload)}")
    try:
        response = requests.post(url, json=payload, timeout=30)
        
        if response.status_code != 202 and response.status_code != 200: # 202 is for creation initiated
            print_test_step(f"ERROR: Chatbot creation failed with status {response.status_code}.")
            try:
                print_test_step(f"Server error response: {response.json()}")
            except json.JSONDecodeError:
                print_test_step(f"Server error response (not JSON): {response.text}")
            response.raise_for_status() # This will raise an exception for bad statuses

        data = response.json()
        chatbot_id = data.get("chatbot_id")
        api_key = data.get("api_key") # Get api_key directly from the response
        
        if chatbot_id and api_key:
            print_test_step(f"Chatbot created. ID: {chatbot_id}, API Key: {api_key[:10]}...") # Log partial key for verification
            return chatbot_id, api_key
        else:
            missing_fields = []
            if not chatbot_id: missing_fields.append("chatbot_id")
            if not api_key: missing_fields.append("api_key")
            print_test_step(f"ERROR: Failed to get required fields from chatbot creation response. Missing: {', '.join(missing_fields)}. Response: {data}")
            return None, None
    except requests.exceptions.RequestException as e:
        print_test_step(f"ERROR: API request failed during chatbot creation: {e}")
        return None, None

def get_story_split_points(lines):
    total_lines = len(lines)
    yw_end_line_approx = math.ceil(total_lines * PERCENT_YELLOW_WALLPAPER)
    # Ensure Bartleby starts after YW, even if YW is very short
    bartleby_start_line_approx = yw_end_line_approx 
    if bartleby_start_line_approx >= total_lines and total_lines > 0: # If YW takes all lines
        bartleby_start_line_approx = total_lines -1 # Bartleby starts at the last line (effectively empty)
        yw_end_line_approx = total_lines -1
    elif total_lines == 0:
        yw_end_line_approx = 0
        bartleby_start_line_approx = 0

    print_test_step(f"Approximate split: YW ends line {yw_end_line_approx}, Bartleby starts line {bartleby_start_line_approx} (out of {total_lines} total lines)")
    return yw_end_line_approx, bartleby_start_line_approx

def prepare_haystack_for_ingestion(original_haystack_lines, needle_sentence, placement_strategy):
    print_test_step(f"Preparing haystack with needle. Strategy: {placement_strategy}")
    modified_lines = list(original_haystack_lines) # Make a copy
    total_lines = len(modified_lines)
    
    yw_end_line, bartleby_start_line = get_story_split_points(modified_lines)
    yw_lines_count = yw_end_line
    bartleby_lines_count = total_lines - bartleby_start_line

    insertion_point = 0

    if placement_strategy == "start_yw": # Test Case 1
        insertion_point = 0
    elif placement_strategy == "1/3_yw": # Test Case 2
        insertion_point = math.ceil(yw_lines_count * (1/3))
        if insertion_point >= yw_end_line and yw_end_line > 0 : insertion_point = yw_end_line -1 # ensure within YW
    elif placement_strategy == "end_yw": # Test Case 3
        insertion_point = yw_end_line - 2 if yw_end_line >=2 else 0 # A few lines before YW ends
    elif placement_strategy == "start_bartleby": # Test Case 4
        insertion_point = bartleby_start_line
    elif placement_strategy == "1/4_bartleby": # Test Case 5
        insertion_point = bartleby_start_line + math.ceil(bartleby_lines_count * 0.25)
    elif placement_strategy == "mid_bartleby": # Test Case 6
        insertion_point = bartleby_start_line + math.ceil(bartleby_lines_count * 0.5)
    elif placement_strategy == "3/4_bartleby": # Test Case 7
        insertion_point = bartleby_start_line + math.ceil(bartleby_lines_count * 0.75)
    elif placement_strategy == "end_bartleby": # Test Case 8
        insertion_point = total_lines - 2 if total_lines >=2 else total_lines # A few lines before end of Bartleby
    elif placement_strategy == "mid_combined": # Test Case 9
        insertion_point = math.ceil(total_lines * 0.5)
    elif placement_strategy == "end_combined": # Test Case 10
        insertion_point = total_lines # Insert as the very last line (append)
    
    # Ensure insertion_point is within bounds
    if insertion_point < 0: insertion_point = 0
    if insertion_point > total_lines: insertion_point = total_lines
    
    modified_lines.insert(insertion_point, needle_sentence)
    print_test_step(f"Needle inserted at line index {insertion_point} (0-based).")

    try:
        # Ensure the directory for TEMP_HAYSTACK_SAVE_PATH exists
        os.makedirs(os.path.dirname(TEMP_HAYSTACK_SAVE_PATH), exist_ok=True)
        with open(TEMP_HAYSTACK_SAVE_PATH, "w", encoding="utf-8") as f:
            f.write("\n".join(modified_lines))
        print_test_step(f"Modified haystack saved to {TEMP_HAYSTACK_SAVE_PATH}")
        return True
    except IOError as e:
        print_test_step(f"ERROR: Could not write temporary haystack file: {e}")
        return False

def ingest_haystack(chatbot_id, api_key):
    print_test_step(f"Ingesting haystack for chatbot ID: {chatbot_id}")
    url = f"{BASE_URL}/chatbots/{chatbot_id}/sources/files"
    headers = {"Authorization": f"Bearer {api_key}"}
    try:
        with open(TEMP_HAYSTACK_SAVE_PATH, "rb") as f:
            files = {"files": (TEMP_HAYSTACK_UPLOAD_FILENAME, f, "text/plain")}
            response = requests.post(url, headers=headers, files=files, timeout=60)
        response.raise_for_status()
        print_test_step(f"Ingestion request successful. Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print_test_step(f"ERROR: API request failed during ingestion: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print_test_step(f"Error response content: {e.response.json()}")
            except json.JSONDecodeError:
                print_test_step(f"Error response content (not JSON): {e.response.text}")
        return False

def poll_chatbot_status(chatbot_id, client_id, timeout_seconds=1200, poll_interval=15): # Increased timeout to 20 minutes
    print_test_step(f"Polling status for chatbot ID: {chatbot_id} (Timeout: {timeout_seconds}s)")
    start_time = time.time()
    while time.time() - start_time < timeout_seconds:
        url = f"{BASE_URL}/chatbots/{chatbot_id}?client_id={client_id}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 404: # For deletion polling
                print_test_step("Chatbot not found (404), assuming deleted.")
                return "DELETED"
            response.raise_for_status()
            data = response.json()
            
            # Check primary status first
            current_status = data.get("status", "").lower()
            # Then check detailed index operation status
            index_op_status_dict = data.get("index_operation_status", {})
            index_op_state = index_op_status_dict.get("state", "").upper()
            index_op_progress = index_op_status_dict.get("progress", 0)

            print_test_step(f"Status: '{current_status}', Index Op State: '{index_op_state}', Progress: {index_op_progress}%")

            if index_op_state == "COMPLETED":
                print_test_step("Ingestion completed.")
                return "COMPLETED"
            if index_op_state == "FAILED":
                print_test_step("ERROR: Ingestion failed according to status.")
                return "FAILED"
            # Fallback for older status if index_operation_status is not detailed
            if current_status == "idle" and index_op_state not in ["RUNNING", "PENDING", "QUEUED"]: # Ensure it's truly idle
                 print_test_step("Chatbot is Idle, assuming ingestion complete.")
                 return "IDLE" # Treat as completed for ingestion

        except requests.exceptions.RequestException as e:
            print_test_step(f"Polling error: {e}. Retrying...")
        
        time.sleep(poll_interval)
    
    print_test_step("ERROR: Polling timed out.")
    return "TIMEOUT"

def query_the_chatbot(chatbot_id, api_key, question):
    print_test_step(f"Querying chatbot ID: {chatbot_id}")
    url = f"{BASE_URL}/chatbots/{chatbot_id}/query"
    headers = {"Authorization": f"Bearer {api_key}"}
    payload = {"query": question, "session_id": f"niah_test_session_{chatbot_id}"} # Unique session per test
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=120) # Increased timeout for query
        response.raise_for_status()
        data = response.json()
        answer = data.get("answer", "")
        print_test_step(f"Query successful. Answer received (first 100 chars): {answer[:100]}...")
        return answer
    except requests.exceptions.RequestException as e:
        print_test_step(f"ERROR: API request failed during query: {e}")
        if hasattr(e, 'response') and e.response is not None:
            try:
                print_test_step(f"Error response content: {e.response.json()}")
            except json.JSONDecodeError:
                print_test_step(f"Error response content (not JSON): {e.response.text}")
        return None

def evaluate_response(answer_text, needle):
    if answer_text is None:
        return False
    # Check for the core part of the needle as per user's instruction
    return "a talking cat named Whiskers" in answer_text or needle in answer_text

def delete_chatbot_cleanup(chatbot_id, client_id):
    print_test_step(f"Deleting chatbot ID: {chatbot_id}")
    url = f"{BASE_URL}/chatbots/{chatbot_id}?client_id={client_id}" # client_id as query param
    try:
        response = requests.delete(url, timeout=30)
        response.raise_for_status()
        print_test_step(f"Deletion request successful for chatbot {chatbot_id}. Response: {response.json()}")
        return True
    except requests.exceptions.RequestException as e:
        print_test_step(f"ERROR: API request failed during chatbot deletion: {e}")
        return False

def cleanup_temp_file():
    if os.path.exists(TEMP_HAYSTACK_SAVE_PATH):
        try:
            os.remove(TEMP_HAYSTACK_SAVE_PATH)
            print_test_step(f"Temporary haystack file {TEMP_HAYSTACK_SAVE_PATH} deleted.")
        except OSError as e:
            print_test_step(f"ERROR: Could not delete temporary haystack file: {e}")

# --- Test Cases Definition ---
TEST_CASES = [
    {"id": "TC1", "description": "Needle at the beginning of YW part.", "strategy": "start_yw"},
    {"id": "TC2", "description": "Needle about 1/3rd into YW part.", "strategy": "1/3_yw"},
    {"id": "TC3", "description": "Needle near the end of YW part.", "strategy": "end_yw"},
    {"id": "TC4", "description": "Needle at the beginning of Bartleby part.", "strategy": "start_bartleby"},
    {"id": "TC5", "description": "Needle about 1/4 into Bartleby part.", "strategy": "1/4_bartleby"},
    {"id": "TC6", "description": "Needle in the middle of Bartleby part.", "strategy": "mid_bartleby"},
    {"id": "TC7", "description": "Needle about 3/4 into Bartleby part.", "strategy": "3/4_bartleby"},
    {"id": "TC8", "description": "Needle near the end of Bartleby part.", "strategy": "end_bartleby"},
    {"id": "TC9", "description": "Needle roughly in the overall middle of combined file.", "strategy": "mid_combined"},
    {"id": "TC10", "description": "Needle at the very end of combined file.", "strategy": "end_combined"},
]

# --- Main Execution ---
if __name__ == "__main__":
    print_test_step("Starting NeedleInAHaystack Test Suite...")
    
    original_haystack_content_lines = []
    try:
        with open(ORIGINAL_HAYSTACK_FILE_PATH, "r", encoding="utf-8") as f:
            original_haystack_content_lines = f.read().splitlines()
        if not original_haystack_content_lines:
            print_test_step(f"ERROR: Original haystack file '{ORIGINAL_HAYSTACK_FILE_PATH}' is empty or could not be read properly.")
            exit(1)
        print_test_step(f"Successfully read {len(original_haystack_content_lines)} lines from original haystack.")
    except IOError as e:
        print_test_step(f"ERROR: Could not read original haystack file '{ORIGINAL_HAYSTACK_FILE_PATH}': {e}")
        exit(1)

    total_score = 0
    results_summary = []

    # Removed initial single client_id acquisition and global cleanup

    for test_case in TEST_CASES:
        print_test_step(f"--- Running Test Case: {test_case['id']} ({test_case['description']}) ---")
        
        # Create a new client_id for each test case
        print_test_step(f"Acquiring unique client_id for Test Case: {test_case['id']}...")
        current_test_client_id = get_or_create_test_client_id(test_case['id'])
        if not current_test_client_id:
            print_test_step(f"CRITICAL ERROR for TC {test_case['id']}: Could not obtain client_id. Skipping test case.")
            results_summary.append(f"{test_case['id']}: FAILED (Client ID creation failed)")
            continue
        print_test_step(f"Using client_id: {current_test_client_id} for Test Case: {test_case['id']}.")

        test_chatbot_id, test_api_key = None, None # Ensure they are reset for each test
        passed_this_case = False

        try:
            # 1. Create Chatbot using the current_test_client_id
            test_chatbot_id, test_api_key = create_chatbot(current_test_client_id, f"NIAH_Test_{test_case['id']}")
            if not test_chatbot_id or not test_api_key:
                results_summary.append(f"{test_case['id']}: FAILED (Chatbot creation failed)")
                continue

            # 2. Prepare Haystack
            if not prepare_haystack_for_ingestion(original_haystack_content_lines, NEEDLE_SENTENCE, test_case["strategy"]):
                results_summary.append(f"{test_case['id']}: FAILED (Haystack preparation failed)")
                continue # Skip to cleanup for this chatbot

            # 3. Ingest Data
            if not ingest_haystack(test_chatbot_id, test_api_key):
                results_summary.append(f"{test_case['id']}: FAILED (Ingestion request failed)")
                continue

            # 4. Wait for Ingestion (using current_test_client_id)
            ingestion_status = poll_chatbot_status(test_chatbot_id, current_test_client_id) # Timeout increased in function definition
            if ingestion_status not in ["COMPLETED", "IDLE"]: # IDLE is a fallback
                results_summary.append(f"{test_case['id']}: FAILED (Ingestion status: {ingestion_status})")
                continue
            
            # Add a small delay after ingestion completion, just in case indexing takes a moment more
            print_test_step("Waiting a few seconds post-ingestion before querying...")
            time.sleep(10)


            # 5. Query
            answer = query_the_chatbot(test_chatbot_id, test_api_key, QUESTION_TO_ASK)
            if answer is None:
                results_summary.append(f"{test_case['id']}: FAILED (Query failed or returned no answer)")
                continue

            # 6. Evaluate
            if evaluate_response(answer, NEEDLE_SENTENCE):
                total_score += 1
                passed_this_case = True
                results_summary.append(f"{test_case['id']}: PASSED")
                print_test_step(f"PASSED! Needle found in response: {answer}")
            else:
                results_summary.append(f"{test_case['id']}: FAILED (Needle not found in response)")
                print_test_step(f"FAILED. Needle NOT found. Response: {answer}")

        except Exception as e:
            print_test_step(f"UNEXPECTED ERROR during test case {test_case['id']}: {e}")
            results_summary.append(f"{test_case['id']}: FAILED (Unexpected error: {e})")
        
        finally:
            # 7. Cleanup (using current_test_client_id)
            if test_chatbot_id: # Only attempt delete if chatbot was created
                delete_chatbot_cleanup(test_chatbot_id, current_test_client_id)
                # Wait for deletion to avoid resource conflicts if backend processes async
                poll_chatbot_status(test_chatbot_id, current_test_client_id, timeout_seconds=120) # Poll for 404
            cleanup_temp_file()
            print_test_step(f"--- Finished Test Case: {test_case['id']} ---")

    print_test_step("\n--- NIAH Test Suite Finished ---")
    print_test_step("Results Summary:")
    for summary_line in results_summary:
        print_test_step(f"  {summary_line}")
    
    final_percentage = (total_score / len(TEST_CASES)) * 100 if TEST_CASES else 0
    print_test_step(f"\nTotal Score: {total_score} / {len(TEST_CASES)}")
    print_test_step(f"Percentage: {final_percentage:.2f}%")

    # Ensure final cleanup of temp file if loop was exited early
    cleanup_temp_file()
