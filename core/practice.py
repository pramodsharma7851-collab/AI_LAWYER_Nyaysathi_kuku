"""Practice Mode Engine for NyayaSathi.

Simulates realistic opposing party personas (Landlord, E-commerce Manager, HR/Employer)
with authentic excuses, enabling citizens to rehearse negotiations and get actionable
feedback on their argument strength and required evidence.
"""

import json
from typing import List, Optional, Tuple
from google import genai
from google.genai import types
from pydantic import BaseModel, Field

from core.config import config
from core.context import build_context
from core.models import CaseFacts, PracticeFeedback
from core.scope import ALLOWED_TOPICS, ScopeGate, scope_gate

PERSONA_PROMPTS = {
    "landlord": """You are playing the role of an obstinate, defensive Landlord in India.
Your tenant has moved out and is demanding their security deposit back.
You are making typical landlord excuses:
- "I had to repaint the entire flat because you left marks on the walls."
- "Deep cleaning cost me 15,000 rupees."
- "You did not give me full notice, so I forfeit the deposit."
- "If you want to go to court, go ahead, it takes 10 years in India."
Stay strictly in character. Be stubborn and skeptical, but do not use profanity.
DO NOT cite fake legal sections or fake court cases.
Respond in the language the user speaks to you (English, Hindi, or Hinglish).""",

    "ecommerce": """You are playing the role of a rigid Customer Support Escalation Manager for an Indian e-commerce platform.
The customer is demanding a refund for a defective product or deficient service.
Your typical corporate excuses:
- "Our return window is strictly 7 days, which has expired."
- "The product has physical damage caused by customer handling, not covered by warranty."
- "You need to take it to the brand's authorized service center yourself; our platform is only an intermediary."
- "Company policy does not allow cash refunds, only store credits."
Stay strictly in character. Be polite but bureaucratic and unyielding.
DO NOT cite fake legal sections or fake court cases.
Respond in the user's language.""",

    "employer": """You are playing the role of a defensive HR Manager / Startup Founder in India.
An ex-employee is demanding their unpaid final salary and severance.
Your typical corporate excuses:
- "You did not complete proper knowledge transfer / handover of company code and documents."
- "The company has client billing issues and cash flow constraints; everyone is waiting."
- "You violated the non-compete agreement by speaking to other companies."
- "We are deducting your notice period shortage from your final settlement."
Stay strictly in character. Defend the company's position stubbornly.
DO NOT cite fake legal sections or fake court cases.
Respond in the user's language.""",
}


class PracticeEngine:
    """Manages roleplay turns and generates constructive argument critiques."""

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

    def play_opponent_turn(
        self,
        persona: str,
        user_argument: str,
        facts: CaseFacts,
        conversation_history: List[dict],
        language: str = "English",
        session_id: Optional[str] = None,
    ) -> str:
        """Simulate the opponent's counter-excuse with strict scope enforcement."""
        persona_domain = "tenancy" if persona == "landlord" else ("consumer" if persona == "ecommerce" else "employment")
        case_domain = facts.category if facts.category in ALLOWED_TOPICS else persona_domain

        # Scope Gate check
        gate = ScopeGate(mock_mode=self.mock_mode) if self.mock_mode else scope_gate
        scope_res = gate.classify(
            user_message=user_argument,
            ongoing_case_type=case_domain,
        )
        if scope_res.topic == "out_of_scope":
            fixed = gate.get_fixed_reply("out_of_scope", language=language, is_emergency=scope_res.is_emergency)
            return fixed or "I do not know."

        if self.mock_mode or not config.is_api_configured():
            return self._mock_opponent_reply(persona)

        client = self._get_client()
        if not client:
            return self._mock_opponent_reply(persona)

        model_name = config.get_model_name()
        if model_name == "auto":
            model_name = "gemini-3.5-flash-lite"

        system_prompt = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS["landlord"])

        context_prefix = ""
        if session_id:
            ctx = build_context(session_id=session_id, current_query=user_argument, domain=case_domain)
            context_prefix = f"Verified Case Context & History:\n{ctx.case_file_json}\nSummary: {ctx.rolling_summary}\n\n"

        history_lines = []
        for turn in conversation_history[-6:]:  # last 3 rounds
            history_lines.append(f"{turn['role'].upper()}: {turn['content']}")

        full_prompt = (
            f"{context_prefix}"
            f"Case Context:\n"
            f"- Disputed Amount: {facts.dispute_amount}\n"
            f"- Key Dates: {facts.incident_date}\n"
            f"- City/State: {facts.city_state}\n\n"
            f"Conversation History:\n"
            + "\n".join(history_lines)
            + f"\n\nUSER'S LATEST ARGUMENT:\n\"{user_argument}\"\n\n"
            f"Reply as the opponent persona in '{language}'. Keep reply under 3-4 sentences. Be realistic and challenging."
        )

        try:
            res = client.models.generate_content(
                model=model_name,
                contents=full_prompt,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    temperature=0.7,  # slightly higher for creative roleplay
                    max_output_tokens=250,
                ),
            )
            if res and res.text:
                return res.text.strip()
        except Exception as e:
            print(f"[WARN] Practice opponent turn failed: {e}")

        return self._mock_opponent_reply(persona)

    def evaluate_arguments(
        self,
        persona: str,
        user_arguments: List[str],
        facts: CaseFacts,
        language: str = "English",
    ) -> PracticeFeedback:
        """Analyze the user's rehearsal and provide actionable coaching."""
        if self.mock_mode or not config.is_api_configured():
            return self._mock_feedback(persona)

        client = self._get_client()
        if not client:
            return self._mock_feedback(persona)

        model_name = config.get_model_name()
        if model_name == "auto":
            model_name = "gemini-3.5-flash-lite"

        prompt = f"""You are a skilled Legal Negotiation Coach for ordinary citizens in India.
The citizen has been practicing their argument against a difficult {persona}.

Case Details:
- Disputed Amount: {facts.dispute_amount}
- Category: {facts.category}
- Facts: {facts.summary_of_facts}

The user's statements during rehearsal:
{json.dumps(user_arguments, indent=2)}

Task:
Provide a constructive critique in '{language}':
1. Evaluate how calm, factual, and assertive the user was.
2. Identify 2 key strengths of their argument.
3. Identify 2 potential pitfalls (e.g. getting emotional, making unprovable claims, lack of dates).
4. List the exact concrete evidence they MUST have ready (e.g. bank transfer statement, written move-in photos, chat exports).
5. Give a concise recommended counter-response that they can use in real life.

Output strictly JSON matching the PracticeFeedback schema.
"""

        try:
            res = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    response_schema=PracticeFeedback,
                    temperature=0.3,
                ),
            )
            if res and res.text:
                parsed = json.loads(res.text)
                return PracticeFeedback(**parsed)
        except Exception as e:
            print(f"[WARN] Feedback generation failed: {e}")

        return self._mock_feedback(persona)

    def _mock_opponent_reply(self, persona: str) -> str:
        if persona == "landlord":
            return "Look, I had to hire painters for 20,000 rupees and clean the kitchen. That's why I deducted the deposit. If you don't like it, you can do whatever you want."
        elif persona == "ecommerce":
            return "Sir, our return window is strictly 7 days from delivery. Today is day 12. As per policy, we cannot accept returns or refunds. Please contact the manufacturer."
        else:
            return "Our client has not released funds this quarter. Plus, you resigned abruptly without proper transition. The finance department has put your FNF settlement on hold."

    def _mock_feedback(self, persona: str) -> PracticeFeedback:
        return PracticeFeedback(
            user_argument_strength="Moderate. You made clear points but need stronger documentary evidence.",
            key_strengths=["Mentioned exact dates", "Polite and firm tone"],
            potential_pitfalls=["Avoid making emotional threats", "Do not agree to verbal compromises without written proof"],
            evidence_to_prepare=["Original agreement", "Bank transaction proof", "Handover inspection photos", "Email thread"],
            recommended_counter_response="I understand your position, but under our written agreement and standard statutory rules, deductions require itemized invoices. Please share the original bills, otherwise refund the deposit within 7 days.",
        )


# Global singleton practice engine
practice_engine = PracticeEngine()
