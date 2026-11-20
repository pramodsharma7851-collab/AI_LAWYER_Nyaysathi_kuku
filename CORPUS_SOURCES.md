# NyayaSathi Verified Legal Corpus Sources

This document details every statutory provision included in the NyayaSathi source-of-truth corpus (`/corpus`).
Every entry has been verified against official government gazettes, statutes on [India Code](https://www.indiacode.nic.in), or central ministry notifications.

## Anti-Hallucination Source Rules
1. **Public Domain Only**: Verbatim extracts are strictly sourced from official government publications and kept concise.
2. **Current Law Enforced**: The Indian Penal Code (IPC 1860) was repealed on July 1, 2024 by the Bharatiya Nyaya Sanhita (BNS 2023). Criminal defense advice is strictly out-of-scope; citing IPC as current law is forbidden.
3. **Labour Law Status**: Provisions are grounded in operative, in-force statutes (Payment of Wages Act 1936, Industrial Disputes Act 1947, Indian Contract Act 1872).
4. **State Tenancy Distinction**: The Model Tenancy Act 2021 is classified as `model_law` because tenancy is a state subject; state rent control acts are noted explicitly.
5. **Zero Case Law Without Verification**: As per system rules, default behavior does not cite unverified case law.

---

## 1. Consumer Protection Domain (`corpus/consumer.json`)
Governing Statute: **Consumer Protection Act, 2019 (Act No. 35 of 2019)**

| Corpus ID | Section | Title / Scope | Official Source URL | Status | Last Verified |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `CPA_2019_SEC_2_7` | Sec 2(7) | Definition of Consumer | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) | In Force | 2026-11-20 |
| `CPA_2019_SEC_2_10` | Sec 2(10) | Definition of Defect | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) | In Force | 2026-11-20 |
| `CPA_2019_SEC_2_11` | Sec 2(11) | Deficiency in Service | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) | In Force | 2026-11-20 |
| `CPA_2019_SEC_2_46` | Sec 2(46) | Unfair Contract | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) | In Force | 2026-11-20 |
| `CPA_2019_SEC_2_47` | Sec 2(47) | Unfair Trade Practice | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) | In Force | 2026-11-20 |
| `CPA_2019_SEC_34` | Sec 34 | District Commission Jurisdiction (up to ₹50L) | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) | In Force | 2026-11-20 |
| `CPA_2019_SEC_35` | Sec 35 | Manner of Making Complaint (e-Daakhil) | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) | In Force | 2026-11-20 |
| `CPA_2019_SEC_39` | Sec 39 | Findings & Reliefs (Refund, Replacement, Compensation) | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) | In Force | 2026-11-20 |
| `CPA_2019_SEC_69` | Sec 69 | 2-Year Limitation Period | [India Code](https://www.indiacode.nic.in/handle/123456789/15256) | In Force | 2026-11-20 |

---

## 2. Tenancy & Residential Rent Domain (`corpus/tenancy.json`)
Governing Statutes: **Transfer of Property Act, 1882** & **Model Tenancy Act, 2021**

| Corpus ID | Section | Title / Scope | Official Source URL | Status | Last Verified |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `TPA_1882_SEC_106` | Sec 106 | 15-day termination notice for month-to-month lease | [India Code](https://www.indiacode.nic.in/handle/123456789/2338) | In Force | 2026-11-20 |
| `TPA_1882_SEC_108_B` | Sec 108(b)-(c) | Lessor duty of quiet possession & non-interruption | [India Code](https://www.indiacode.nic.in/handle/123456789/2338) | In Force | 2026-11-20 |
| `TPA_1882_SEC_108_M` | Sec 108(m) | Lessee duty: Reasonable wear & tear protection | [India Code](https://www.indiacode.nic.in/handle/123456789/2338) | In Force | 2026-11-20 |
| `MTA_2021_SEC_11` | Sec 11 | Residential deposit capped at 2 months; refund on possession | [Ministry of Housing & Urban Affairs](https://mohua.gov.in) | Model Law | 2026-11-20 |
| `MTA_2021_SEC_20` | Sec 20 | Mandatory written agreement registered with Rent Authority | [MoHUA](https://mohua.gov.in) | Model Law | 2026-11-20 |
| `MTA_2021_SEC_21` | Sec 21 | Protection against wrongful/arbitrary eviction | [MoHUA](https://mohua.gov.in) | Model Law | 2026-11-20 |
| `STATE_RENT_CONTROL_PRINCIPLE` | State Rent Acts | State Rent Control Framework (Maharashtra, Delhi, Karnataka, etc.) | [India Code](https://www.indiacode.nic.in) | In Force | 2026-11-20 |

---

## 3. Employment & Wages Domain (`corpus/employment.json`)
Governing Statutes: **Payment of Wages Act, 1936**, **Industrial Disputes Act, 1947**, **Indian Contract Act, 1872**

| Corpus ID | Section | Title / Scope | Official Source URL | Status | Last Verified |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `PWA_1936_SEC_3` | Sec 3 | Employer responsibility for payment of wages | [India Code](https://www.indiacode.nic.in/handle/123456789/2361) | In Force | 2026-11-20 |
| `PWA_1936_SEC_5` | Sec 5 | FNF / settlement due by 2nd working day from termination | [India Code](https://www.indiacode.nic.in/handle/123456789/2361) | In Force | 2026-11-20 |
| `PWA_1936_SEC_7` | Sec 7 | Prohibition on unauthorized deductions from wages | [India Code](https://www.indiacode.nic.in/handle/123456789/2361) | In Force | 2026-11-20 |
| `PWA_1936_SEC_15` | Sec 15 | Wage claims before Labour Commissioner (compensation up to 10x) | [India Code](https://www.indiacode.nic.in/handle/123456789/2361) | In Force | 2026-11-20 |
| `IDA_1947_SEC_2A` | Sec 2A | Individual termination deemed an industrial dispute | [India Code](https://www.indiacode.nic.in/handle/123456789/15286) | In Force | 2026-11-20 |
| `IDA_1947_SEC_25F` | Sec 25F | 1 month notice / pay + 15 days severance per continuous year | [India Code](https://www.indiacode.nic.in/handle/123456789/15286) | In Force | 2026-11-20 |
| `ICA_1872_SEC_27` | Sec 27 | Restraint of trade void (non-compete post-employment unenforceable) | [India Code](https://www.indiacode.nic.in/handle/123456789/2187) | In Force | 2026-11-20 |

---

## 4. General Civil, Legal Aid & Constitutional Remedies (`corpus/general.json`)
Governing Statutes: **Indian Contract Act, 1872**, **Legal Services Authorities Act, 1987**, **Limitation Act, 1963**, **Bharatiya Nyaya Sanhita, 2023**

| Corpus ID | Section | Title / Scope | Official Source URL | Status | Last Verified |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `ICA_1872_SEC_73` | Sec 73 | Compensation for breach of contract (natural direct losses) | [India Code](https://www.indiacode.nic.in/handle/123456789/2187) | In Force | 2026-11-20 |
| `ICA_1872_SEC_74` | Sec 74 | Reasonable compensation where penalty is stipulated | [India Code](https://www.indiacode.nic.in/handle/123456789/2187) | In Force | 2026-11-20 |
| `LSAA_1987_SEC_12` | Sec 12 | Eligibility for Free Legal Aid (NALSA / DLSA / Helpline 15100) | [India Code](https://www.indiacode.nic.in/handle/123456789/1944) | In Force | 2026-11-20 |
| `LSAA_1987_SEC_19` | Sec 19 | Lok Adalat forum for amicable zero-fee settlement | [India Code](https://www.indiacode.nic.in/handle/123456789/1944) | In Force | 2026-11-20 |
| `LIMIT_1963_ART_113` | Art 113 | 3-year limitation period for civil claims / recovery | [India Code](https://www.indiacode.nic.in/handle/123456789/1566) | In Force | 2026-11-20 |
| `CRIMINAL_REFORM_NOTE_BNS` | BNS Notice | IPC 1860 repealed by BNS 2023 on 01-07-2024; Criminal advice out of scope | [India Code](https://www.indiacode.nic.in/handle/123456789/20262) | In Force | 2026-11-20 |
