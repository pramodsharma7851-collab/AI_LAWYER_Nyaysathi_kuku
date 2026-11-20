# Known Limitations & Explicit System Boundaries

NyayaSathi is an AI legal information assistant designed to empower citizens, but it operates with explicit, designed boundaries:

1. **Strict Three-Topic Scope Restriction**:
   - NyayaSathi is strictly confined to three civil dispute domains:
     1. **Tenancy**: Residential rent, deposit recovery, eviction.
     2. **Consumer Protection**: Product defects, deficiency in services, refunds.
     3. **Employment**: Unpaid salary, wrongful termination, full & final settlement.
   - All other legal domains (Family/Divorce, Criminal defense, Corporate/Taxation, Motor Vehicle/Traffic, Property Titles/Inheritance, Constitutional/PIL) are deliberately **out of scope**.
   - Out-of-scope queries deterministically return *"I do not know."* without invoking the generative model.

2. **Context Budget & Rolling Summarization**:
   - To preserve latency and avoid exceeding model context limits, conversations exceeding the 12,000-character budget (~3,000 tokens) are automatically compressed: older turns are summarized into a structured rolling narrative, while the most recent 20 turns are retained verbatim. Highly specific phrasing from early messages will be captured in summary rather than exact words.

3. **Session Lifetime & Browser Query Parameters**:
   - The user session is tracked via a UUID in `st.query_params['session_id']` and saved in the SQLite/PostgreSQL database. If a user deletes browser history, navigates away without the URL query parameter, or clicks "Delete my data", prior state cannot be recovered.

4. **Not a Licensed Attorney**: NyayaSathi provides legal information and self-help document drafts, not formal legal advice or attorney representation. Users with complex litigation or court dates are directed to qualified counsel or District Legal Services Authorities (DLSA / NALSA Helpline 15100).

5. **State Tenancy Variations**: While the corpus provides general principles and citations from the Transfer of Property Act 1882 and the Model Tenancy Act 2021, tenancy procedures vary significantly between states (e.g. Maharashtra Rent Control Act, Delhi Rent Control Act). NyayaSathi explicitly flags this dependency.

6. **Labour Code Transition**: Indian labour laws are in transition between legacy statutes (Payment of Wages Act 1936, Industrial Disputes Act 1947, Shops and Establishments Acts) and the new Labour Codes (Code on Wages 2019). The corpus tracks in-force operational sections and notes pending rules.

7. **Court Filing & Appearance**: The tool drafts notices and complaint templates; it does not automate electronic court docketing or provide legal representation.

8. **Voice Recognition**: Streamlit web audio depends on browser permissions and microphone hardware. In environments where browser audio recording is restricted or noisy, the text chat is the primary and most accurate interface.
