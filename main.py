# main.py (FINAL, CORRECTED INDENTATION)
import os
import pymongo
import time
from datetime import datetime
from eyecite import clean_text
from summarizer_logic import generate_structured_brief

def clean_html(html: str) -> str:
    """
    Use eyecite's cleaner to strip HTML tags and normalize whitespace.
    """
    return clean_text(html, ['html', 'all_whitespace'])

def main():
    """
    Main execution script for the backend summarization process.
    """
    # --- 1. Setup ---
    start_time = datetime.now()
    log_filename = f"run_log_{start_time.strftime('%Y%m%d_%H%M%S')}.txt"
    log_filepath = os.path.join("logs", log_filename)
    os.makedirs("logs", exist_ok=True)

    total_cost = 0.0
    decisions_processed = 0
    decisions_skipped = 0

    # Pricing constants
    TOKEN_THRESHOLD = 128000
    COST_PER_INPUT_TOKEN_LOW = 1.25 / 1_000_000
    COST_PER_OUTPUT_TOKEN_LOW = 5.00 / 1_000_000
    COST_PER_INPUT_TOKEN_HIGH = 2.50 / 1_000_000
    COST_PER_OUTPUT_TOKEN_HIGH = 10.00 / 1_000_000

    # --- 2. Configuration and DB Connection ---
    mongo_url = os.environ.get("MONGO_URL")
    gemini_api_key = os.environ.get("GEMINI_API_KEY")
    db_name = os.environ.get("MONGO_DB_NAME", "PublicDecisions")   
    collection_name = os.environ.get("MONGO_COLLECTION", "Documents") 

    if not mongo_url or not gemini_api_key:
        print("FATAL: MONGO_URL and GEMINI_API_KEY environment variables must be set.")
        return

    try:
        print("Connecting to MongoDB...")
        mongo_client = pymongo.MongoClient(mongo_url)
        db = mongo_client[db_name]
        decisions_collection = db[collection_name]
        print("Successfully connected to MongoDB.")
        count = decisions_collection.count_documents({})
        print(f"📊 Total records in '{collection_name}' collection: {count}")
        if count > 0:
            sample_doc = decisions_collection.find_one()
            print("🔍 Sample record before update:")
            print(sample_doc)

            # 👉 Add `is_summarized = False` to all docs that don’t already have it
            result = decisions_collection.update_many(
                {"is_summarized": {"$exists": False}},   # filter
                {"$set": {"is_summarized": False}}       # update
            )
            print(f"✅ Updated {result.modified_count} documents with 'is_summarized = False'")

            sample_after = decisions_collection.find_one()
            print("🔍 Sample record after update:")
            print(sample_after)
        else:
            print("⚠️ No records found in the 'users' collection.")
    except Exception as e:
        print(f"FATAL: Could not connect to MongoDB. Error: {e}")
        return

    # This outer try/finally ensures the summary report always runs
    try:
        # --- 3. The Main Processing Loop (NOW CORRECTLY INDENTED) ---
        while True:
            decision = decisions_collection.find_one({"is_summarized": False})
            if not decision:
                print("No new decisions to process. Script will exit.")
                break

            doc_id = decision['_id']
            print(f"Processing document ID: {doc_id}")
            
            try:
                raw_html = decision.get("html")
                if not raw_html:
                    raise ValueError("Document is missing the 'raw_html_text' field.")
                
                cleaned_text = clean_html(raw_html)
                
                # Criminal Case Filter
                normalized_start = cleaned_text.strip().lower()
                is_criminal_case = (
                    normalized_start.startswith("people v") or 
                    normalized_start.startswith("the people of the state of new york v")
                )

                if not is_criminal_case:
                    print(f"--> SKIPPING: Document {doc_id} is not a criminal case.")
                    decisions_collection.update_one(
                        {"_id": doc_id},
                        {"$set": {"is_summarized": True, "summary_status": "skipped_not_criminal", "summarized_at": time.time()}}
                    )
                    decisions_skipped += 1
                    continue
                
                # Run the AI Pipeline
                complete_summary_data, usage_metadata = generate_structured_brief(cleaned_text, gemini_api_key)

                if complete_summary_data:
                    # Cost calculation
                    run_cost = 0.0
                    if usage_metadata:
                        input_tokens = usage_metadata.get("prompt_token_count", 0)
                        output_tokens = usage_metadata.get("candidates_token_count", 0)
                        if input_tokens <= TOKEN_THRESHOLD:
                            run_cost = (input_tokens * COST_PER_INPUT_TOKEN_LOW) + (output_tokens * COST_PER_OUTPUT_TOKEN_LOW)
                        else:
                            run_cost = (input_tokens * COST_PER_INPUT_TOKEN_HIGH) + (output_tokens * COST_PER_OUTPUT_TOKEN_HIGH)
                        total_cost += run_cost
                    
                    # Update database on success
                    decisions_collection.update_one(
                        {"_id": doc_id},
                        {"$set": { "is_summarized": True, "summary_status": "success", "summarized_at": time.time(), "ai_generated_brief": complete_summary_data }}
                    )
                    print(f"--> SUCCESS: Summarized and saved document ID: {doc_id}")

                    with open(log_filepath, "a") as log_file:
                        log_file.write(f"{doc_id}\n")
                    
                    decisions_processed += 1
                else:
                    raise Exception("generate_structured_brief returned None or an error.")

            except Exception as e:
                print(f"ERROR processing document {doc_id}: {e}")
                if "API key not valid" in str(e):
                    print("FATAL: Invalid API Key. The script will now exit.")
                    break
                
                decisions_collection.update_one(
                    {"_id": doc_id},
                    {"$set": {"is_summarized": True, "summary_status": "failed", "error_message": str(e)}}
                )

    finally:
        # --- 4. Final Summary Report ---
        print("\n--- Run Summary ---")
        print(f"Decisions Summarized: {decisions_processed}")
        print(f"Decisions Skipped (Not Criminal): {decisions_skipped}")
        if decisions_processed > 0:
            average_cost = total_cost / decisions_processed
            print(f"Total Estimated Cost: ${total_cost:.6f}")
            print(f"Average Cost Per Decision: ${average_cost:.6f}")
        else:
            print("No new decisions were summarized in this run.")
        print(f"Log file saved to: {log_filepath}")
        print("-------------------\n")

if __name__ == "__main__":
    main()