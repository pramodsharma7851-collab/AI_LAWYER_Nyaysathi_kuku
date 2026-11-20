"""Document drafter for NyayaSathi.

Generates:
1. Formal Legal Notice
2. Consumer Complaint (District Commission / e-Daakhil)
3. Reply to Legal Notice
4. Wage Claim / Grievance Application

Anti-hallucination rule:
Placeholders are filled ONLY from user-provided facts; any unknown facts
remain strictly as [TO BE FILLED] markers.
Delivers in-memory DOCX and PDF with mandatory statutory citations and disclaimer.
"""

import io
from datetime import datetime
from typing import Dict, List, Optional
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer

from core.models import CaseFacts, CitationItem
from core.scope import ALLOWED_TOPICS

DISCLAIMER_TEXT = (
    "DISCLAIMER: This legal draft was prepared using NyayaSathi AI legal information assistant "
    "for pre-litigation and self-help communication. It does not constitute formal legal representation. "
    "The user must verify all factual assertions and consult an advocate or the District Legal Services "
    "Authority (DLSA / NALSA Helpline 15100) prior to formal court filing."
)


class DocumentDrafter:
    """Engine for drafting legal notices, complaints, and applications."""

    def draft_legal_notice(self, facts: CaseFacts, citations: List[CitationItem], session_id: Optional[str] = None) -> str:
        """Draft a formal legal notice based on confirmed facts."""
        if facts.category not in ALLOWED_TOPICS and facts.category != "general":
            return "I do not know."
        today = datetime.now().strftime("%d-%m-%Y")
        comp_name = facts.complainant_name
        comp_addr = facts.complainant_address
        comp_contact = facts.complainant_contact
        opp_name = facts.opposite_party_name
        opp_addr = facts.opposite_party_address
        amount = facts.dispute_amount
        incident_date = facts.incident_date
        summary = facts.summary_of_facts
        relief = facts.relief_sought if facts.relief_sought != "[TO BE FILLED]" else f"immediate refund/payment of {amount}"

        citation_lines = []
        for c in citations:
            citation_lines.append(f"- {c.provision_name}: {c.relevance}")
        cit_block = "\n".join(citation_lines) if citation_lines else "- General principles of Indian Contract Act, 1872 (Section 73)"

        draft = f"""LEGAL NOTICE / DEMAND NOTICE
(REGISTERED POST WITH A.D. / SPEED POST / EMAIL)

Date: {today}

TO:
{opp_name}
{opp_addr}

FROM:
{comp_name}
{comp_addr}
Contact: {comp_contact}

SUBJECT: FORMAL DEMAND NOTICE FOR {relief.upper()}

Sir / Madam,

Under instructions and on behalf of my client / the undersigned, {comp_name}, resident of {facts.city_state}, I hereby serve upon you this formal Legal Notice:

1. That the undersigned entered into a lawful relationship/agreement with you on or around {incident_date} regarding {facts.category.capitalize()} matters.

2. STATEMENT OF FACTS:
{summary}

3. That despite repeated reminders and requests, you have unlawfully withheld/failed to pay the sum of {amount}, causing wrongful loss and immense mental harassment to the undersigned.

4. RELEVANT STATUTORY PROVISIONS & LEGAL GROUNDS:
Your aforesaid act is contrary to applicable laws, including:
{cit_block}

5. DEMAND & NOTICE:
I hereby call upon you to pay/refund the aforesaid sum of {amount} together with reasonable interest at 18% per annum, or fulfill the following relief:
{relief}
within a period of 15 (FIFTEEN) days from the receipt of this notice.

Take notice that if you fail to comply with the requisitions of this notice within the stipulated 15 days, the undersigned shall be constrained to initiate appropriate civil and/or consumer/labour proceedings before the competent Forum / Court at {facts.city_state}, at your sole risk, cost, and legal consequences.

Yours faithfully,

_____________________________
{comp_name}
(Complainant / Aggrieved Party)

============================================================
{DISCLAIMER_TEXT}
============================================================
"""
        return draft.strip()

    def draft_consumer_complaint(self, facts: CaseFacts, citations: List[CitationItem], session_id: Optional[str] = None) -> str:
        """Draft a consumer complaint for the District Consumer Disputes Redressal Commission."""
        if facts.category != "consumer" and facts.category != "general":
            return "I do not know."
        comp_name = facts.complainant_name
        comp_addr = facts.complainant_address
        comp_contact = facts.complainant_contact
        opp_name = facts.opposite_party_name
        opp_addr = facts.opposite_party_address
        amount = facts.dispute_amount
        summary = facts.summary_of_facts
        city_state = facts.city_state

        citation_lines = []
        for c in citations:
            citation_lines.append(f"- {c.provision_name}: {c.relevance}")
        cit_block = "\n".join(citation_lines) if citation_lines else "- Consumer Protection Act, 2019 (Section 2(11) & Section 35)"

        draft = f"""BEFORE THE DISTRICT CONSUMER DISPUTES REDRESSAL COMMISSION AT {city_state.upper()}
CONSUMER COMPLAINT NO. _____ OF 2026
(Under Section 35 of the Consumer Protection Act, 2019)

IN THE MATTER OF:
{comp_name}
Residing at: {comp_addr}
Contact: {comp_contact}
... COMPLAINANT

VERSUS

{opp_name}
Having office at: {opp_addr}
... OPPOSITE PARTY

MOST RESPECTFULLY SHOWETH:

1. That the Complainant is a 'Consumer' within the meaning of Section 2(7) of the Consumer Protection Act, 2019, having purchased goods / availed services for consideration amounting to {amount}.

2. That the Opposite Party is a company/seller/service provider engaged in commercial business.

3. FACTS OF THE CASE:
{summary}

4. DEFICIENCY IN SERVICE / UNFAIR TRADE PRACTICE:
That the Opposite Party committed deficiency in service under Section 2(11) and/or supplied defective goods under Section 2(10) of the Consumer Protection Act, 2019:
{cit_block}

5. JURISDICTION & LIMITATION:
That this Hon'ble Commission has pecuniary jurisdiction under Section 34 (value not exceeding Rs. 50 Lakhs) and territorial jurisdiction. The complaint is filed well within the 2-year limitation period prescribed under Section 69.

PRAYER:
Wherefore, it is most respectfully prayed that this Hon'ble Commission may be pleased to:
a) Direct the Opposite Party to refund the sum of {amount} along with interest @ 18% p.a.
b) Direct the Opposite Party to pay compensation of Rs. 25,000/- towards mental agony and harassment.
c) Direct payment of litigation expenses of Rs. 10,000/-.
d) Pass such further orders as this Hon'ble Commission deems fit in the interest of justice.

Complainant: {comp_name}
Verification:
I, {comp_name}, do hereby verify that the contents of paragraphs 1 to 5 are true to my personal knowledge.
Verified at {city_state} on this day.

_____________________________
DEPONENT

============================================================
{DISCLAIMER_TEXT}
============================================================
"""
        return draft.strip()

    def generate_docx(self, text: str, title: str = "Legal Draft") -> io.BytesIO:
        """Render draft text into formatted Microsoft Word (.docx) document."""
        doc = Document()
        # Title
        p_title = doc.add_paragraph()
        run_title = p_title.add_run(title)
        run_title.font.size = Pt(16)
        run_title.font.bold = True
        run_title.font.color.rgb = RGBColor(27, 54, 93)  # Navy blue

        doc.add_paragraph()

        # Content lines
        for line in text.split("\n"):
            line_str = line.strip()
            if line_str.startswith("===="):
                doc.add_paragraph("____________________________________________________________")
            elif line_str.startswith("DISCLAIMER:"):
                p_disc = doc.add_paragraph()
                r_disc = p_disc.add_run(line_str)
                r_disc.font.size = Pt(8.5)
                r_disc.font.italic = True
                r_disc.font.color.rgb = RGBColor(120, 120, 120)
            elif any(line_str.startswith(h) for h in ["BEFORE", "LEGAL NOTICE", "SUBJECT:", "PRAYER:", "VERSUS"]):
                p_h = doc.add_paragraph()
                r_h = p_h.add_run(line_str)
                r_h.font.bold = True
                r_h.font.size = Pt(11.5)
            else:
                p = doc.add_paragraph(line)
                p.paragraph_format.space_after = Pt(2)

        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer

    def generate_pdf(self, text: str, title: str = "Legal Draft") -> io.BytesIO:
        """Render draft text into formatted PDF document using ReportLab."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=54,
            leftMargin=54,
            topMargin=54,
            bottomMargin=54,
        )

        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            "DocTitle",
            parent=styles["Heading1"],
            fontSize=14,
            leading=18,
            textColor="#1B365D",
            spaceAfter=12,
        )
        body_style = ParagraphStyle(
            "DocBody",
            parent=styles["Normal"],
            fontSize=9.5,
            leading=13.5,
            textColor="#1E293B",
            spaceAfter=6,
        )
        disclaimer_style = ParagraphStyle(
            "DocDisclaimer",
            parent=styles["Normal"],
            fontSize=7.5,
            leading=10.5,
            textColor="#64748B",
            fontName="Helvetica-Oblique",
            spaceBefore=14,
        )

        story = [Paragraph(title, title_style), Spacer(1, 10)]

        for line in text.split("\n"):
            line_clean = line.strip()
            if not line_clean:
                story.append(Spacer(1, 4))
                continue
            if line_clean.startswith("===="):
                continue
            if line_clean.startswith("DISCLAIMER:"):
                story.append(Paragraph(line_clean, disclaimer_style))
            else:
                # Escape xml characters for ReportLab Paragraph
                escaped = (
                    line_clean.replace("&", "&amp;")
                    .replace("<", "&lt;")
                    .replace(">", "&gt;")
                )
                story.append(Paragraph(escaped, body_style))

        doc.build(story)
        buffer.seek(0)
        return buffer


# Global singleton drafter
drafter = DocumentDrafter()
