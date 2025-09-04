# models.py
from pydantic import BaseModel, Field
from typing import List, Optional

class CaptionDetails(BaseModel):
    case_name: str = Field(description="The full case name, People v. Smith, for example.")
    court: str = Field(description="The name of the court that authored and decided this opinion (e.g., 'Court of Appeals', 'Supreme Court, Appellate Division, Second Department').")
    year_decided: int = Field(description="The year the case was officially decided. Extract the numerical year.")
    ny_slip_op_citation: Optional[str] = Field(None, description="The New York Slip Opinion citation, if present (e.g., '2024 NY Slip Op 03379'). Should be null if not found.")
    official_reporter_citation: Optional[str] = Field(None, description="The official reporter citation, if present (e.g., '42 NY3d 668'). This is often found in brackets next to the NY Slip Op citation. Should be null if not found.")

class HoldingDetail(BaseModel):
    issue_question: str = Field(description="The specific issue/question this holding addresses.")
    answer: str = Field(description="The court's direct answer (e.g., 'Yes', 'No', 'Affirmed').")
    legal_principle: str = Field(description="The concise legal principle or rule the court relied on for this holding.")

class OpinionSummary(BaseModel):
    opinion_type: str = Field(description="Type of opinion (e.g., 'Dissenting', 'Concurring').")
    author_judge: Optional[str] = Field(None, description="Name of the judge who wrote this opinion, if identifiable.")
    summary_of_analysis: List[str] = Field(
        description="A list of brief takeaway points summarizing the main arguments or alternative analysis of this opinion."
    )

class SourcedTakeaway(BaseModel):
    takeaway: str = Field(description="The original concise takeaway point, summary, or fact that was provided as input.")
    supporting_quote: str = Field(description="An EXACT, VERBATIM quote from the court decision text that directly supports the provided takeaway. If no quote is found, this should state that.")

class SourcedTakeawaysList(BaseModel):
    sourced_takeaways: List[SourcedTakeaway] = Field(description="A list of takeaways, each with its supporting quote.")

class SourcedIssue(BaseModel):
    issue_question: str = Field(description="The original issue/question that was provided as input.")
    supporting_quote: str = Field(description="An EXACT, VERBATIM quote from the court decision text that frames or directly states this issue. If no quote is found, this should state that.")

class SourcedIssuesList(BaseModel):
    sourced_issues: List[SourcedIssue] = Field(description="A list of issues, each with its supporting quote.")

class SourcedHolding(BaseModel):
    issue_question: str = Field(description="The specific issue/question this holding addresses, copied from the input.")
    answer: str = Field(description="The court's direct answer (e.g., 'Yes', 'No', 'Affirmed'), copied from the input.")
    legal_principle: str = Field(description="The concise legal principle or rule, copied from the input.")
    supporting_quote: str = Field(description="An EXACT, VERBATIM quote from the court decision text that directly supports the legal_principle.")

class SourcedHoldingsList(BaseModel):
    sourced_holdings: List[SourcedHolding] = Field(description="A list of holdings, each with its supporting quote for the legal principle.")

class LegalBrief(BaseModel):
    brief_step_1_format_note: str = Field(description="Note about the format being used.")
    brief_step_2_caption: CaptionDetails = Field(description="Case caption details (name, court, year, citation).")
    brief_step_3_key_facts_takeaways: List[str] = Field(
        description="A list of concise, bullet-point style key legally relevant facts. Each string in the list should be a distinct factual takeaway."
    )
    brief_step_4_procedural_history: str = Field(
        description="A concise narrative of the procedural history from trial court to the current court."
    )
    brief_step_5_issues_as_questions: List[str] = Field(
        description="A list of specific legal and/or factual questions the court had to decide, phrased concisely as questions."
    )
    brief_step_6_holdings_summary: List[HoldingDetail] = Field(
        description="A list of holdings, each concisely answering an issue and stating the core legal principle."
    )
    brief_step_7_rationale_takeaways: List[str] = Field(
        description="A list of key takeaway points summarizing the court's main reasoning. Each string should be a distinct point from the rationale."
    )
    brief_step_8_disposition: str = Field(
        description="The final disposition of the case (e.g., Affirmed, Reversed, Remanded), stated succinctly."
    )
    brief_step_9_other_opinions_summary: Optional[List[OpinionSummary]] = Field(
        None,
        description="Brief summaries of any concurring or dissenting opinions. Null if none."
    )