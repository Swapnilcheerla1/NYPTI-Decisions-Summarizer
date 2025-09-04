import json
from typing import Optional, List, Dict, Any, Tuple
from langchain_google_genai import ChatGoogleGenerativeAI

# Local imports
from models import LegalBrief, SourcedTakeaway, HoldingDetail, SourcedIssue, SourcedHolding
from prompts import (
    legal_brief_prompt, legal_brief_parser,
    sourcing_prompt, sourcing_parser,
    issues_sourcing_prompt, issues_sourcing_parser,
    holdings_sourcing_prompt, holdings_sourcing_parser
)

llm_instance = None

def get_llm_instance(api_key: str):
    """Initializes and returns a reusable LLM instance."""
    global llm_instance
    if llm_instance is None:
        llm_instance = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.1,
            google_api_key=api_key
        )
        print("Initialized Gemini 1.5 Pro client.")
    return llm_instance

# --- Helper functions are modified to return usage data ---

def _source_takeaways(takeaways: List[str], full_text: str, llm_instance) -> Tuple[Optional[List[SourcedTakeaway]], dict]:
    if not takeaways:
        return [], {}
    try:
        print(f"Sourcing quotes for {len(takeaways)} takeaways...")
        sourcing_chain = sourcing_prompt | llm_instance | sourcing_parser
        response_obj = sourcing_chain.invoke({ "full_text": full_text, "takeaways_json_list": json.dumps(takeaways) })
        usage = getattr(response_obj, 'response_metadata', {})
        print("Sourcing successful.")
        return response_obj.sourced_takeaways, usage
    except Exception as e:
        print(f"ERROR during quote sourcing: {e}")
        return None, {}

def _source_issues(issues: List[str], full_text: str, llm_instance) -> Tuple[Optional[List[SourcedIssue]], dict]:
    if not issues:
        return [], {}
    try:
        print(f"Sourcing quotes for {len(issues)} issues...")
        sourcing_chain = issues_sourcing_prompt | llm_instance | issues_sourcing_parser
        response_obj = sourcing_chain.invoke({ "full_text": full_text, "issues_json_list": json.dumps(issues) })
        usage = getattr(response_obj, 'response_metadata', {})
        print("Issue sourcing successful.")
        return response_obj.sourced_issues, usage
    except Exception as e:
        print(f"ERROR during issue sourcing: {e}")
        return None, {}

def _source_holdings(holdings: List[HoldingDetail], full_text: str, llm_instance) -> Tuple[Optional[List[SourcedHolding]], dict]:
    if not holdings:
        return [], {}
    try:
        print(f"Sourcing quotes for {len(holdings)} holdings...")
        holdings_as_dict = [h.model_dump() for h in holdings]
        sourcing_chain = holdings_sourcing_prompt | llm_instance | holdings_sourcing_parser
        response_obj = sourcing_chain.invoke({ "full_text": full_text, "holdings_json_list": json.dumps(holdings_as_dict) })
        usage = getattr(response_obj, 'response_metadata', {})
        print("Holding sourcing successful.")
        return response_obj.sourced_holdings, usage
    except Exception as e:
        print(f"ERROR during holding sourcing: {e}")
        return None, {}

# --- The main function, now corrected and with better cost tracking ---

def generate_structured_brief(full_text: str, api_key: str) -> Tuple[Optional[Dict[str, Any]], Dict[str, int]]:
    """
    Takes raw text, runs the full AI pipeline, and returns a tuple containing:
    1. The final structured data dictionary.
    2. A dictionary with the TOTAL token usage for all calls.
    """
    llm = get_llm_instance(api_key)
    
    total_usage = {"prompt_token_count": 0, "candidates_token_count": 0}

    def _accumulate_usage(usage: dict):
        total_usage["prompt_token_count"] += usage.get("prompt_token_count", 0)
        total_usage["candidates_token_count"] += usage.get("candidates_token_count", 0)

    # STEP 1: Generate the main brief (unsourced)
    print("Generating main legal brief...")
    brief_generation_chain = legal_brief_prompt | llm | legal_brief_parser
    response_obj = brief_generation_chain.invoke({"court_decision_full_text": full_text})
    
    unsourced_brief = response_obj
    brief_usage = getattr(response_obj, 'response_metadata', {})
    _accumulate_usage(brief_usage)

    if not unsourced_brief:
        print("ERROR: Main brief generation failed, returned None.")
        return None, total_usage
    
    # Update the format note using the court name that was already extracted
    court_name = unsourced_brief.brief_step_2_caption.court
    dynamic_format_note = f"This is an AI generated summary of a decision from {court_name}."
    unsourced_brief.brief_step_1_format_note = dynamic_format_note
    print(f"Updated format note: {dynamic_format_note}")
    
    # STEP 2: Source quotes and accumulate usage from each call
    sourced_facts, facts_usage = _source_takeaways(unsourced_brief.brief_step_3_key_facts_takeaways, full_text, llm)
    _accumulate_usage(facts_usage)
    
    sourced_rationale, rationale_usage = _source_takeaways(unsourced_brief.brief_step_7_rationale_takeaways, full_text, llm)
    _accumulate_usage(rationale_usage)
    
    sourced_issues, issues_usage = _source_issues(unsourced_brief.brief_step_5_issues_as_questions, full_text, llm)
    _accumulate_usage(issues_usage)
    
    sourced_holdings, holdings_usage = _source_holdings(unsourced_brief.brief_step_6_holdings_summary, full_text, llm)
    _accumulate_usage(holdings_usage)

    # STEP 3: Assemble the final, complete dictionary
    final_structured_data = {
        "main_brief": unsourced_brief.model_dump(),
        "sourced_facts": [sf.model_dump() for sf in sourced_facts] if sourced_facts else [],
        "sourced_rationale": [sr.model_dump() for sr in sourced_rationale] if sourced_rationale else [],
        "sourced_issues": [si.model_dump() for si in sourced_issues] if sourced_issues else [],
        "sourced_holdings": [sh.model_dump() for sh in sourced_holdings] if sourced_holdings else [],
    }

    return final_structured_data, total_usage