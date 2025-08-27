# prompts.py (REVISED AND FIXED)

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from models import (
    CaptionDetails, LegalBrief, SourcedTakeawaysList,
    SourcedIssuesList, SourcedHoldingsList
)

# --- Parsers ---
# We still need the parsers to validate the final output, but we will NOT use their format instructions in the prompts.
caption_parser = PydanticOutputParser(pydantic_object=CaptionDetails)
legal_brief_parser = PydanticOutputParser(pydantic_object=LegalBrief)
sourcing_parser = PydanticOutputParser(pydantic_object=SourcedTakeawaysList)
issues_sourcing_parser = PydanticOutputParser(pydantic_object=SourcedIssuesList)
holdings_sourcing_parser = PydanticOutputParser(pydantic_object=SourcedHoldingsList)


# --- NEW, MORE DIRECT PROMPT TEMPLATES ---

# 1. Caption Extraction Prompt (REVISED)
caption_extraction_prompt_template_text = """You are a specialized legal assistant AI. Your only task is to extract caption information from the start of the provided court decision.

--- BEGIN DOCUMENT SNIPPET ---
{document_snippet_for_caption}
--- END DOCUMENT SNIPPET ---

Your response MUST be a single, valid JSON object and nothing else. Do not add explanations or markdown. Use these exact keys:
- "case_name" (string)
- "court" (string)
- "year_decided" (integer)
- "ny_slip_op_citation" (string or null)
- "official_reporter_citation" (string or null)
"""
caption_extraction_prompt = ChatPromptTemplate.from_template(template=caption_extraction_prompt_template_text)


# 2. Legal Brief Generation Prompt (REVISED)
# In prompts.py

legal_brief_prompt_template_text = """You are a highly skilled AI legal analyst. Read the following court decision and generate a comprehensive legal brief based on the 9 steps outlined below.

--- BEGIN COURT DECISION TEXT ---
{court_decision_full_text}
--- END COURT DECISION TEXT ---

Your entire output MUST be a single, valid JSON object. Do not include any other text, explanations, or markdown formatting. The JSON object must contain keys corresponding to these 9 steps:
1.  `brief_step_1_format_note`: (string) A note about the format.
2.  `brief_step_2_caption`: (JSON object) An object with keys `case_name`, `court`, `year_decided`, `ny_slip_op_citation`, and `official_reporter_citation`.
3.  `brief_step_3_key_facts_takeaways`: (list of strings) A list of key facts.
4.  `brief_step_4_procedural_history`: (string) A narrative of the case history.
5.  `brief_step_5_issues_as_questions`: (list of strings) A list of the legal questions.
6.  `brief_step_6_holdings_summary`: (list of JSON objects) Each object must have keys `issue_question`, `answer`, and `legal_principle`.
7.  `brief_step_7_rationale_takeaways`: (list of strings) A list of key points from the court's reasoning.
8.  `brief_step_8_disposition`: (string) The final outcome (e.g., "Affirmed").
9.  `brief_step_9_other_opinions_summary`: (list of JSON objects or null) If present, provide a list of summaries for any concurring or dissenting opinions.
    - Each summary object MUST contain the keys `opinion_type`, `author_judge`, and `summary_of_analysis`.
    - The value for `summary_of_analysis` MUST be a list of strings.
    - If no other opinions exist, this entire field MUST be `null`.
"""
legal_brief_prompt = ChatPromptTemplate.from_template(template=legal_brief_prompt_template_text)


# 3. Quote Sourcing Prompt (Facts/Rationale) (REVISED)
sourcing_prompt_template_text = """You are an AI assistant for legal research. Your task is to find a single, verbatim supporting quote from the full court decision for each takeaway point provided.

--- FULL COURT DECISION TEXT ---
{full_text}
--- END FULL COURT DECISION TEXT ---

--- TAKEAWAY POINTS LIST (in JSON format) ---
{takeaways_json_list}
--- END TAKEAWAY POINTS LIST ---

Respond with ONLY a single valid JSON object. It must contain one key: `sourced_takeaways`. The value should be a list of objects, where each object has two keys: `takeaway` (the original takeaway) and `supporting_quote` (the verbatim quote from the text). If no quote is found, use the string "No direct supporting quote found in the text." for the quote.
"""
sourcing_prompt = ChatPromptTemplate.from_template(template=sourcing_prompt_template_text)


# 4. Issues Sourcing Prompt (REVISED)
issues_sourcing_prompt_template_text = """You are an AI assistant for legal research. Your task is to find a single, verbatim supporting quote from the full court decision for each legal issue provided.

--- FULL COURT DECISION TEXT ---
{full_text}
--- END FULL COURT DECISION TEXT ---

--- ISSUES LIST (in JSON format) ---
{issues_json_list}
--- END ISSUES LIST ---

Respond with ONLY a single valid JSON object. It must contain one key: `sourced_issues`. The value should be a list of objects, where each object has two keys: `issue_question` (the original issue) and `supporting_quote` (the verbatim quote from the text that frames the issue). If no quote is found, use "No direct supporting quote found in the text." for the quote.
"""
issues_sourcing_prompt = ChatPromptTemplate.from_template(template=issues_sourcing_prompt_template_text)


# 5. Holdings Sourcing Prompt (REVISED)
holdings_sourcing_prompt_template_text = """You are an AI assistant for legal research. Your task is to find a single, verbatim supporting quote from the full court decision for the `legal_principle` of each holding provided.

--- FULL COURT DECISION TEXT ---
{full_text}
--- END FULL COURT DECISION TEXT ---

--- HOLDINGS LIST (in JSON format) ---
{holdings_json_list}
--- END HOLDINGS LIST ---

Respond with ONLY a single valid JSON object. It must contain one key: `sourced_holdings`. The value should be a list of objects. Each object must contain all the original holding keys (`issue_question`, `answer`, `legal_principle`) plus one new key: `supporting_quote` (the verbatim quote from the text that supports the legal principle). If no quote is found, use "No direct supporting quote found in the text." for the quote.
"""
holdings_sourcing_prompt = ChatPromptTemplate.from_template(template=holdings_sourcing_prompt_template_text)

print("Prompts and parsers initialized with DIRECT instructions.")