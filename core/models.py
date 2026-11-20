"""Data models and Pydantic schemas for NyayaSathi.

Defines schemas for:
- Legal Corpus entries
- Case builder facts
- Structured LLM output (Hard Gate)
- Legal document generation
- Practice mode personas & feedback
"""

from enum import Enum
from typing import Any, List, Optional
from pydantic import BaseModel, Field


class LegalStatus(str, Enum):
    IN_FORCE = "in_force"
    SUPERSEDED = "superseded"
    UNCERTAIN = "uncertain"
    MODEL_LAW = "model_law"


class CorpusEntry(BaseModel):
    id: str = Field(description="Unique identifier e.g. CPA_2019_SEC_2_7")
    act_name: str = Field(description="Full legal name of the Act or Code")
    year: int = Field(description="Year of enactment")
    section_number: str = Field(description="Section, Rule, or Article number")
    title: str = Field(description="Title or subject of the provision")
    summary: str = Field(description="Plain-language summary of the provision")
    verbatim_extract: str = Field(description="Short public domain extract from the official gazette/code")
    official_source_url: str = Field(description="Official URL on indiacode.nic.in, egazette, etc.")
    last_verified: str = Field(description="ISO date when verified")
    status: LegalStatus = Field(description="Current in-force legal status")
    domain: str = Field(description="tenancy | consumer | employment | general")
    keywords: List[str] = Field(default_factory=list, description="Keywords for retrieval matching")


class ConfidenceLevel(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CitationItem(BaseModel):
    corpus_id: str = Field(description="Must match exact corpus ID from the provided AUTHORITY block")
    provision_name: str = Field(description="Act name and section number")
    relevance: str = Field(description="Brief explanation of how this applies to the user's issue")


class LegalOption(BaseModel):
    title: str = Field(description="Short title of the option e.g. 'Issue Legal Notice'")
    description: str = Field(description="Plain language explanation of the step")
    pros: List[str] = Field(default_factory=list)
    cons: List[str] = Field(default_factory=list)
    estimated_timeframe: str = Field(default="Varies")
    forum: Optional[str] = Field(default=None, description="Official grievance portal or forum name")


class StructuredLegalAdvice(BaseModel):
    summary: str = Field(description="Plain language summary of the user's situation and legal standing")
    facts_extracted: List[str] = Field(default_factory=list, description="Key factual points extracted from user story")
    options: List[LegalOption] = Field(default_factory=list, description="Actionable paths forward")
    citations: List[CitationItem] = Field(default_factory=list, description="Grounding citations strictly from AUTHORITY")
    confidence: ConfidenceLevel = Field(description="Assessment confidence based on verified law")
    needs_lawyer: bool = Field(description="True if situation requires an advocate or exceeds self-help")
    lawyer_reason: Optional[str] = Field(default=None, description="Explanation if advocate/DLSA is advised")
    missing_info: List[str] = Field(default_factory=list, description="Critical facts needed before action can be taken")


class CaseFacts(BaseModel):
    category: str = Field(default="general", description="tenancy | consumer | employment | other")
    complainant_name: str = Field(default="[TO BE FILLED]")
    complainant_contact: str = Field(default="[TO BE FILLED]")
    complainant_address: str = Field(default="[TO BE FILLED]")
    opposite_party_name: str = Field(default="[TO BE FILLED]")
    opposite_party_address: str = Field(default="[TO BE FILLED]")
    city_state: str = Field(default="[TO BE FILLED]")
    dispute_amount: str = Field(default="[TO BE FILLED]")
    incident_date: str = Field(default="[TO BE FILLED]")
    agreement_details: str = Field(default="[TO BE FILLED]")
    summary_of_facts: str = Field(default="[TO BE FILLED]")
    evidence_has: List[str] = Field(default_factory=list)
    evidence_missing: List[str] = Field(default_factory=list)
    steps_taken_so_far: List[str] = Field(default_factory=list)
    relief_sought: str = Field(default="[TO BE FILLED]")
    is_confirmed: bool = Field(default=False)


class PracticeFeedback(BaseModel):
    user_argument_strength: str = Field(description="Critique of user argument")
    key_strengths: List[str] = Field(default_factory=list)
    potential_pitfalls: List[str] = Field(default_factory=list)
    evidence_to_prepare: List[str] = Field(default_factory=list)
    recommended_counter_response: str = Field(description="Suggested rebuttal or calm response")
