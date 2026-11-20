"""NyayaSathi - Find Free Legal Help Page.

Directory of verified, official Government of India legal aid authorities,
consumer forums, and emergency resources.
"""

import streamlit as st

st.set_page_config(page_title="Find Free Legal Help - NyayaSathi", page_icon="🏛️", layout="wide")

st.title("🏛️ Find Free Legal Help & Official Portals")
st.markdown(
    "If your dispute involves complex litigation, high financial stakes, or you cannot afford a private lawyer, "
    "the Government of India provides **free legal aid**, dispute resolution mechanisms, and grievance portals."
)

st.divider()

# Grid of resources
col1, col2 = st.columns(2, gap="large")

with col1:
    st.markdown("### 1. NALSA & District Legal Services Authority (DLSA)")
    st.info(
        """
        **National Legal Services Authority (NALSA)**  
        Under Section 12 of the Legal Services Authorities Act, 1987, free legal aid is guaranteed to:
        - Women & Children
        - Industrial Workmen & Labourers
        - Scheduled Castes (SC) & Scheduled Tribes (ST)
        - Persons with annual income below State ceiling (typically ₹3,00,000/year)
        
        📞 **National Legal Aid Helpline**: `15100` (Toll-Free, 24/7, Pan-India)  
        🌐 **Official Website**: [nalsa.gov.in](https://nalsa.gov.in)  
        🏢 **How to apply**: Visit the Front Office of the DLSA located inside any District Court Complex in your city.
        """
    )

    st.markdown("### 2. Consumer Forum & e-Daakhil Portal")
    st.info(
        """
        **National Consumer Helpline (NCH)**  
        For consumer grievances, refund refusals, and deficient services:
        - 📞 **Helpline Number**: `1915` or SMS `8800001915`
        - 🌐 **Online Complaint Portal**: [consumerhelpline.gov.in](https://consumerhelpline.gov.in)
        
        **e-Daakhil (E-filing in Consumer Commissions)**  
        - 🌐 **Filing Portal**: [edaakhil.nic.in](https://edaakhil.nic.in)  
        - Enables online filing of consumer complaints before District, State, and National Commissions without visiting the court in person.
        """
    )

with col2:
    st.markdown("### 3. Labour Commissioners & SAMADHAN Portal")
    st.info(
        """
        **Ministry of Labour and Employment**  
        For unpaid wages, illegal termination, and gratuity claims:
        - 🌐 **SAMADHAN Portal**: [samadhan.labour.gov.in](https://samadhan.labour.gov.in) (Industrial dispute conciliation)
        - 🌐 **Chief Labour Commissioner (Central)**: [clc.gov.in](https://clc.gov.in)
        - 🏢 **State Labour Offices**: Approach your local State Labour Commissioner office for claims under Section 15 of the Payment of Wages Act, 1936.
        """
    )

    st.markdown("### 4. Emergency & Specialised Helplines")
    st.warning(
        """
        **Emergency Situations & Physical Threat:**
        - 🚨 **National Emergency Helpline**: `112` (Police, Fire, Ambulance)
        - 👩 **Women Helpline**: `181` (Domestic distress & harassment)
        - 🛡️ **National Commission for Women (NCW)**: `7827170170`
        - 👵 **Senior Citizen Helpline**: `14567`
        - 💻 **National Cyber Crime Reporting**: `1930` or [cybercrime.gov.in](https://cybercrime.gov.in)
        """
    )

st.divider()
st.caption(
    "Note: All URLs and helpline numbers listed on this page are verified official Government of India resources. "
    "NyayaSathi does not charge any fees or act as an intermediary for official legal aid filings."
)
