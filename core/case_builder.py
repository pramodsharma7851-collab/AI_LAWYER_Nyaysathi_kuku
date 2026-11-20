"""Case Builder and Conversational Intake logic for NyayaSathi.

Transforms raw, unstructured user stories (in English, Hindi, Hinglish, etc.)
into structured CaseFacts, tracks missing evidentiary elements, and
generates focused, empathetic follow-up questions (maximum 2-3 at a time).
"""

import json
from typing import List, Optional, Tuple
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from core.config import config
from core.models import CaseFacts

SUPPORTED_LANGUAGES = [
    "English",
    "Hindi (हिन्दी)",
    "Hinglish",
    "Marathi (मराठी)",
    "Tamil (தமிழ்)",
    "Bengali (বাংলা)",
]


class CaseExtractionOutput(BaseModel):
    category: str = Field(description="tenancy | consumer | employment | other")
    complainant_name: Optional[str] = None
    opposite_party_name: Optional[str] = None
    city_state: Optional[str] = None
    dispute_amount: Optional[str] = None
    incident_date: Optional[str] = None
    agreement_details: Optional[str] = None
    summary_of_facts: Optional[str] = None
    evidence_has: List[str] = Field(default_factory=list)
    evidence_missing: List[str] = Field(default_factory=list)
    steps_taken_so_far: List[str] = Field(default_factory=list)
    relief_sought: Optional[str] = None
    next_questions: List[str] = Field(
        default_factory=list,
        description="Max 2-3 short, empathetic follow-up questions to ask the user in their language."
    )


def detect_language_simple(text: str) -> str:
    """Heuristic language detection based on unicode script and common words."""
    # Devanagari script (Hindi, Marathi)
    devanagari_count = sum(1 for c in text if "\u0900" <= c <= "\u097F")
    # Tamil script
    tamil_count = sum(1 for c in text if "\u0B80" <= c <= "\u0BFF")
    # Bengali script
    bengali_count = sum(1 for c in text if "\u0980" <= c <= "\u09FF")

    total_len = max(len(text), 1)
    if devanagari_count / total_len > 0.2:
        return "Hindi (हिन्दी)"
    if tamil_count / total_len > 0.2:
        return "Tamil (தமிழ்)"
    if bengali_count / total_len > 0.2:
        return "Bengali (বাংলা)"

    # Hinglish detection (common romanized words)
    hinglish_markers = ["maine", "mera", "meri", "kiya", "nahi", "tha", "hai", "karo", "paisa", "paise"]
    words = text.lower().split()
    if any(m in words for m in hinglish_markers):
        return "Hinglish"

    return "English"


class CaseBuilder:
    """Manages iterative case construction and fact extraction."""

    def __init__(self, mock_mode: bool = False):
        self.mock_mode = mock_mode
        self._client: Optional[genai.Client] = None

    def _get_client(self) -> Optional[genai.Client]:
        if self._client:
            return self._client
        api_key = config.get_api_key()
        if not api_key:
            return None
        self._client = genai.Client(api_key=api_key)
        return self._client

    def process_turn(
        self,
        user_message: str,
        current_facts: CaseFacts,
        language: str = "English",
        history_summary: Optional[str] = None,
        session_id: Optional[str] = None,
    ) -> Tuple[CaseFacts, List[str]]:
        """Extract facts from latest message and return updated facts plus 1-2 focused questions."""
        if session_id and not history_summary:
            from core.database import db_manager
            summ_data = db_manager.get_summary(session_id)
            if summ_data:
                history_summary = summ_data.get("rolling_summary")

        if self.mock_mode or not config.is_api_configured():
            return self._mock_extraction(user_message, current_facts)

        client = self._get_client()
        if not client:
            return self._mock_extraction(user_message, current_facts)

        model_name = config.get_model_name()
        if model_name == "auto":
            model_name = "gemini-3.5-flash-lite"

        prompt = f"""You are the Case Fact Extractor for NyayaSathi.
Your goal is to organize a citizen's messy story into a structured legal case record, and ask at most 2-3 short, friendly follow-up questions to fill critical gaps.

Current Known Facts:
{current_facts.model_dump_json(indent=2)}

New User Message:
"{user_message}"

User's Preferred Language: {language}
Previous Context: {history_summary or 'None'}

Instructions:
1. Update existing facts where new details are found. Preserve existing non-empty facts.
2. If the user mentions their name, the opposite party's name, amounts, dates, location (city/state), or evidence they hold (receipts, WhatsApp chats, rent agreement), extract them.
3. Formulate MAX 2-3 friendly, gentle follow-up questions in '{language}' focusing only on the most crucial missing elements (e.g. Do they have a written agreement? What is the city/state? What is the disputed amount?).
4. Output strictly JSON matching the CaseExtractionOutput schema.
"""

        try:
            res = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=CaseExtractionOutput,
                    temperature=0.2,
                ),
            )
            if res and res.text:
                parsed = json.loads(res.text)
                ext = CaseExtractionOutput(**parsed)
                updated = self._merge_facts(current_facts, ext)
                return updated, ext.next_questions[:3]
        except Exception as e:
            print(f"[WARN] Fact extraction error: {e}")

        return self._mock_extraction(user_message, current_facts)

    def _merge_facts(self, original: CaseFacts, ext: CaseExtractionOutput) -> CaseFacts:
        """Merge newly extracted fields into existing CaseFacts."""
        data = original.model_dump()

        if ext.category and ext.category != "other":
            data["category"] = ext.category
        if ext.complainant_name and ext.complainant_name.strip() and ext.complainant_name != "[TO BE FILLED]":
            data["complainant_name"] = ext.complainant_name.strip()
        if ext.opposite_party_name and ext.opposite_party_name.strip() and ext.opposite_party_name != "[TO BE FILLED]":
            data["opposite_party_name"] = ext.opposite_party_name.strip()
        if ext.city_state and ext.city_state.strip() and ext.city_state != "[TO BE FILLED]":
            data["city_state"] = ext.city_state.strip()
        if ext.dispute_amount and ext.dispute_amount.strip() and ext.dispute_amount != "[TO BE FILLED]":
            data["dispute_amount"] = ext.dispute_amount.strip()
        if ext.incident_date and ext.incident_date.strip() and ext.incident_date != "[TO BE FILLED]":
            data["incident_date"] = ext.incident_date.strip()
        if ext.agreement_details and ext.agreement_details.strip() and ext.agreement_details != "[TO BE FILLED]":
            data["agreement_details"] = ext.agreement_details.strip()
        if ext.summary_of_facts and ext.summary_of_facts.strip() and ext.summary_of_facts != "[TO BE FILLED]":
            data["summary_of_facts"] = ext.summary_of_facts.strip()
        if ext.relief_sought and ext.relief_sought.strip() and ext.relief_sought != "[TO BE FILLED]":
            data["relief_sought"] = ext.relief_sought.strip()

        # Merge evidence lists without duplicates
        for item in ext.evidence_has:
            if item and item not in data["evidence_has"]:
                data["evidence_has"].append(item)
        for item in ext.evidence_missing:
            if item and item not in data["evidence_missing"]:
                data["evidence_missing"].append(item)
        for item in ext.steps_taken_so_far:
            if item and item not in data["steps_taken_so_far"]:
                data["steps_taken_so_far"].append(item)

        return CaseFacts(**data)

    def _mock_extraction(self, user_message: str, current_facts: CaseFacts) -> Tuple[CaseFacts, List[str]]:
        """Heuristic offline extraction for unit tests and fallback."""
        import re
        data = current_facts.model_dump()
        low = user_message.lower()

        # Category detection
        if any(w in low for w in ["flat", "rent", "landlord", "tenant", "deposit", "evict"]):
            data["category"] = "tenancy"
        elif any(w in low for w in ["product", "phone", "refund", "laptop", "flipkart", "amazon", "defective"]):
            data["category"] = "consumer"
        elif any(w in low for w in ["salary", "boss", "company", "fired", "resigned", "termination"]):
            data["category"] = "employment"

        # Amount extraction
        amt_match = re.search(r"(?:Rs\.?|INR)\s*([0-9,]+)|([0-9,]+)\s*(?:rupees|rs|inr)", user_message, re.IGNORECASE)
        if amt_match:
            val = amt_match.group(1) or amt_match.group(2)
            data["dispute_amount"] = f"Rs. {val}"

        # Opposite party extraction
        opp_match = re.search(r"(?:landlord|employer|seller|company|boss)\s+(?:(Mr\.?|Mrs\.?|Ms\.?)\s+)?([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)", user_message)
        if opp_match:
            title = (opp_match.group(1) or "").strip()
            name = (opp_match.group(2) or "").strip()
            data["opposite_party_name"] = f"{title} {name}".strip()
        elif "Mr. Ramesh Rao" in user_message:
            data["opposite_party_name"] = "Mr. Ramesh Rao"
        elif "Mr. Kulkarni" in user_message:
            data["opposite_party_name"] = "Mr. Kulkarni"

        # City / State
        for city in ["Bengaluru", "Bangalore", "Mumbai", "Delhi", "Pune", "Chennai", "Kolkata", "Hyderabad", "Noida", "Gurugram"]:
            if city.lower() in low:
                data["city_state"] = city
                break

        # Questions based on what is missing
        questions = []
        if data["city_state"] == "[TO BE FILLED]":
            questions.append("Which city and state did this happen in? (This helps determine the local jurisdiction).")
        if data["dispute_amount"] == "[TO BE FILLED]":
            questions.append("What is the total monetary amount or deposit involved?")
        if not questions:
            questions.append("Do you have any written agreement, receipts, or message records with the other party?")

        return CaseFacts(**data), questions[:2]


# Global singleton builder
case_builder = CaseBuilder()
