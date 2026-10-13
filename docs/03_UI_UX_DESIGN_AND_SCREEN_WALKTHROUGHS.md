# UI/UX Design and Screen Walkthroughs

**Document Code:** UIX-CDSCO-001  
**Project Name:** CDSCO Medical Device Submission Dossier Builder  
**Classification:** Visual Interface Specifications and Wireframe Walkthroughs  
**Status:** Approved Baseline for Stakeholder Presentation  

---

## 1. Visual Layout Overview and Navigation Model

The platform uses a focused **3-Panel Regulatory Workspace** designed to keep regulatory context, active work, and validation feedback visible simultaneously without page reloads:

```text
+---------------------------------------------------------------------------------------------------------+
|  CDSCO Dossier Builder   |   Submissions   |   Profiles   |   Regulatory Explorer   |   User: RA Lead   |
+---------------------------------------------------------------------------------------------------------+
|  LEFT PANEL: HIERARCHY       |  CENTER PANEL: ENTITY WORKSPACE           |  RIGHT PANEL: READINESS      |
|                              |                                           |                              |
|  [>] Application Info        |  CURRENT ENTITY: Power of Attorney        |  SUBMISSION STATUS           |
|      - Applicant Details [v] |                                           |  Overall: IN PROGRESS        |
|      - Manufacturer [v]      |  [ 8-POINT REGULATORY GUIDANCE CARD ]     |                              |
|      - Legal Undertakings [!] |  - What is required?                      |  READINESS BREAKDOWN         |
|                              |  - Why CDSCO asks for it                  |  - Information: 8/8 Complete |
|  [v] Device Master File      |  - What to provide & How to format        |  - Documents:   14/16 Done   |
|      - 1.0 Executive Summary |  - Legal Citation: Rule 34(1)             |  - Traceability: 42/48 Mapped|
|      - 2.0 Specifications    |                                           |                              |
|      - 6.0 V&V Studies [!]   |  ACTION AREA:                             |  BLOCKING ISSUES (2)         |
|        - 6.3 Sterilization   |  [ Choose File to Upload ]                |  [!] Power of Attorney unset |
|                              |  Linked: POA_Foreign_Mfg_Apostilled.pdf   |  [!] Sterilization report    |
|  [>] Plant Master File       |                                           |                              |
|  [>] Essential Principles    |  STATUS: SATISFIED (Validated)            |  [ Open SUGAM Filing Guide ] |
+---------------------------------------------------------------------------------------------------------+
```

---

## 2. Screen 1: Submissions Dashboard

The main landing page allows regulatory managers to track all active filings, monitor progress across pathways, and immediately see blocked items:

```text
+---------------------------------------------------------------------------------------------------------+
| SUBMISSIONS DASHBOARD                                                       [ + New Submission Button ] |
| Track and prepare statutory CDSCO filings across all 7 core pathways                                    |
+---------------------------------------------------------------------------------------------------------+
| METRICS OVERVIEW:                                                                                       |
| [ Total Submissions: 8 ]   [ In Preparation: 5 ]   [ Ready to File: 2 ]   [ Action Required: 1 ]        |
+---------------------------------------------------------------------------------------------------------+
| ACTIVE APPLICATIONS TABLE:                                                                              |
|                                                                                                         |
| Tracking ID    Pathway   Device Family         Risk Class   Progress   Blockers   Status     Actions    |
| ------------------------------------------------------------------------------------------------------- |
| SUB-2026-001   MD-14     Orthopedic Pedicle    Class C      85%        1          Review     [ Open ]   |
| SUB-2026-002   MD-7      Cardiovascular Pump   Class C      100%       0          READY      [ Guide ]  |
| SUB-2026-003   MD-14     Cardiovascular Stent  Class D      60%        3          Draft      [ Open ]   |
| SUB-2026-004   MD-3      Surgical Sutures      Class B      100%       0          READY      [ Guide ]  |
| SUB-2026-005   MD-12     Prototype Bioreactor  Class C      40%        2          Draft      [ Open ]   |
+---------------------------------------------------------------------------------------------------------+
```

---

## 3. Screen 2: Pathway and Context Setup Wizard

When creating a new submission, the user selects their regulatory pathway first. The system immediately enforces **Smart Statutory Constraints** on the risk class selector to prevent impossible regulatory filings:

```text
+---------------------------------------------------------------------------------------------------------+
| STEP 1 OF 3: SELECT REGULATORY PATHWAY                                                                  |
| Choose the statutory application route under Medical Devices Rules, 2017:                               |
|                                                                                                         |
| (*) FORM MD-14: Commercial Import Licence (Anchor - Classes A, B, C, D - Central Authority)            |
| ( ) FORM MD-7:  Commercial Manufacturing Licence (Class C & D - Central Licensing Authority)           |
| ( ) FORM MD-8:  Loan Licence to Manufacture (Class C & D - Central Licensing Authority)                |
| ( ) FORM MD-3:  Commercial Manufacturing Licence (Class A & B - State Licensing Authority)             |
| ( ) FORM MD-4:  Loan Licence to Manufacture (Class A & B - State Licensing Authority)                  |
| ( ) FORM MD-12: Test & Evaluation Manufacturing Licence (All Classes)                                  |
| ( ) FORM MD-16: Test & Evaluation Import Licence (All Classes)                                         |
+---------------------------------------------------------------------------------------------------------+
| STEP 2 OF 3: BIND REUSABLE ORGANIZATIONAL PROFILES                                                      |
| Select pre-saved profiles to auto-populate administrative details:                                      |
|                                                                                                         |
| Authorized Indian Agent:   [ MedTech India Solutions Pvt Ltd        |v]  (Licence: MD-42-DL-2024)       |
| Foreign Manufacturer:      [ SpineCraft Medical GmbH (Germany)      |v]  (ISO 13485: Valid)         |
| Manufacturing Site:        [ Werk 2, Tuttlingen Site               |v]  (Cleanroom ISO Class 7)     |
+---------------------------------------------------------------------------------------------------------+
| STEP 3 OF 3: DEFINE REGULATORY CONTEXT (WITH SMART STATUTORY CONSTRAINTS)                               |
| Risk Class options are dynamically constrained by the selected pathway to guarantee regulatory validity: |
|                                                                                                         |
| [ Active Pathway: FORM MD-14 selected -> All 4 Risk Classes eligible for Import ]                       |
| Risk Classification:       ( ) Class A    ( ) Class B    (*) Class C    ( ) Class D                     |
|                                                                                                         |
| [ SMART CONSTRAINT BEHAVIOR EXAMPLES ]:                                                                 |
| - If user selects Form MD-7/8: [Class A: Disabled] [Class B: Disabled] (*) Class C   ( ) Class D       |
|   (Tooltip: 'Form MD-7 is strictly for Class C & D. For Class A or B, please select Form MD-3')         |
| - If user selects Form MD-3/4: (*) Class A   ( ) Class B   [Class C: Disabled] [Class D: Disabled]     |
|   (Tooltip: 'Form MD-3 is strictly for Class A & B. For Class C or D, please select Form MD-7')         |
|                                                                                                         |
| Product Category:          (*) Medical Device            ( ) In-Vitro Diagnostic (IVD)                  |
| Sterilization Status:      (*) Sterile                   ( ) Non-Sterile                                |
| Contains Software / AI:    ( ) Yes                       (*) No                                         |
+---------------------------------------------------------------------------------------------------------+
| DYNAMIC CHECKLIST SUMMARY:                                                                              |
| [ 42 Mandatory Requirements Activated ]  [ 6 Conditional Rules Applied ]  [ 14 Rules Not Applicable ]   |
|                                                                             [ Launch Workspace -> ]     |
+---------------------------------------------------------------------------------------------------------+
```

---

## 4. Screen 3: One-Entity Regulatory Workspace

When editing a specific requirement, the applicant sees the comprehensive **8-Point Guidance Card**. Non-experts can understand exactly what is required and why:

```text
+---------------------------------------------------------------------------------------------------------+
| WORKSPACE: Form MD-14  >  Legal Undertakings  >  Power of Attorney (PoA)                                |
+---------------------------------------------------------------------------------------------------------+
| GUIDANCE FRAME:                                                                                         |
|                                                                                                         |
| 1. WHAT IS REQUIRED?                                                                                    |
|    A notarized and apostilled Power of Attorney executed by the foreign manufacturer authorizing the    |
|    Indian Authorized Agent to act on their behalf for regulatory and commercial distribution.           |
|                                                                                                         |
| 2. WHY IS IT REQUIRED?                                                                                  |
|    Mandated under MDR 2017 Rule 34 to establish statutory legal liability and representation in India. |
|                                                                                                         |
| 3. WHAT SHOULD BE PROVIDED?                                                                             |
|    A high-resolution color scan of the original apostilled Power of Attorney conforming to the        |
|    official format prescribed in Part I of the First Schedule.                                          |
|                                                                                                         |
| 4. HOW TO PROVIDE IT?                                                                                   |
|    Upload the complete PDF document (including the apostille seal page). Enter the document execution  |
|    date and expiration date in the metadata fields below.                                               |
|                                                                                                         |
| 5. REGULATORY CITATION                                                                                  |
|    MDR 2017: Rule 34(1) and Fourth Schedule Part I, Clause 1(a).                                        |
|                                                                                                         |
| 6. TARGET SUGAM LOCATION                                                                                |
|    SUGAM Portal Tab: "Applicant Information" -> Sub-Tab: "Legal Undertakings" -> Field: "Power of Atty"|
+---------------------------------------------------------------------------------------------------------+
| ACTION AREA: FULFILLMENT METHOD                                                                         |
|                                                                                                         |
| Choose How to Provide This Document:                                                                    |
|   (*) Option A: Upload Existing Document       ( ) Option B: Generate via Guided In-App Form            |
|                                                                                                         |
| [ When Option A (Upload) is active: ]                                                                   |
|   [ Drop PDF/Word file here or Click to Upload ]                                                        |
|   Current Attached File: POA_SpineCraft_India_Apostilled_2026.pdf (4.2 MB)                              |
|   Document Issue Date: [ 2026-01-15 ]      Expiration Date: [ 2029-01-14 ]                              |
|                                                                                                         |
| [ When Option B (Generate) is active: ]                                                                 |
|   [ Open Guided Form: Enter Signatory Details & Auto-Generate Statutory Draft (First Schedule) ]        |
|                                                                                                         |
| [ Save & Continue ]                                                 Current Entity Status: [ SATISFIED ]|
+---------------------------------------------------------------------------------------------------------+
```

---

## 5. Screen 4: Hierarchical Dossier Builder (Device Master File Explorer)

Rather than uploading one gigantic 300-page PDF, the applicant builds and verifies the **Device Master File (DMF)** section by section:

```text
+---------------------------------------------------------------------------------------------------------+
| DEVICE MASTER FILE (DMF) EXPLORER (Fourth Schedule Part III Standard)                                   |
+---------------------------------------------------------------------------------------------------------+
| SECTION TREE                                  COMPLETION    ATTACHED EVIDENCE              STATUS       |
| ------------------------------------------------------------------------------------------------------- |
| [v] 1.0 Executive Summary & Description                                                                 |
|     1.1 Device Overview & Principles of Op     100%         DMF_Sec_1_Overview.pdf         SATISFIED    |
|     1.2 Intended Use & Indications             100%         IFU_Pedicle_Screw_Rev3.pdf     SATISFIED    |
|     1.3 Predicate Comparison Table             100%         Predicate_Substantial_Eq.pdf   SATISFIED    |
|                                                                                                         |
| [v] 2.0 Product Specifications                                                                          |
|     2.1 Engineering Drawings & Dimensions      100%         Titanium_Screw_Drawings.pdf    SATISFIED    |
|     2.2 Raw Material Specifications            100%         Ti6Al4V_ELI_Mill_Cert.pdf      SATISFIED    |
|                                                                                                         |
| [v] 6.0 Design Verification & Validation                                                                |
|     6.1 Mechanical Bench Testing               100%         ASTM_F1797_Static_Fatigue.pdf  SATISFIED    |
|     6.2 Biocompatibility Evaluation            100%         ISO_10993_Summary_Report.pdf   SATISFIED    |
|     6.3 Sterilization Validation               [!] 0%       -- NO DOCUMENT ATTACHED --     MISSING [!]  |
|     6.4 Packaging & Shelf Life Testing         100%         Accelerated_Aging_5Yr.pdf      SATISFIED    |
|                                                                                                         |
| [>] 7.0 Clinical Evidence & Literature Review   100%         Clinical_Evaluation_Report.pdf SATISFIED    |
| [>] 8.0 Device Artwork, Labels & Packaging     100%         Blister_Outer_Artwork.pdf      SATISFIED    |
+---------------------------------------------------------------------------------------------------------+
| DMF SUMMARY: 11 of 12 Subsections Satisfied  |  1 Subsection Missing Evidence (6.3 Sterilization)       |
+---------------------------------------------------------------------------------------------------------+
```

---

## 6. Screen 5: Evidence Vault and Relational Linking

Documents are managed in an Evidence Vault where a single uploaded file can satisfy multiple statutory requirements across the submission:

```text
+---------------------------------------------------------------------------------------------------------+
| EVIDENCE VAULT & TRACEABILITY MANAGER                                           [ + Upload New File ]   |
+---------------------------------------------------------------------------------------------------------+
| UPLOADED DOCUMENT                 TYPE            ISSUING BODY      EXPIRY DATE    LINKED SECTIONS      |
| ------------------------------------------------------------------------------------------------------- |
| ISO13485_TUV_SUD_2026.pdf         Certificate     TUV SUD Munich    2028-11-30     - Form MD-14 Item 7  |
|                                                                                    - PMF Section 3.0    |
|                                                                                    - EP Checklist Gen 3 |
|                                                                                                         |
| Free_Sale_Cert_Germany_BfArM.pdf  FSC             BfArM Bonn        2027-06-15     - Form MD-14 Item 5  |
|                                                                                    - DMF Section 1.4    |
|                                                                                                         |
| Biocompatibility_ISO10993.pdf     Test Report     NAMSA USA         N/A (Standard) - DMF Section 6.2    |
|                                                                                    - EP Checklist Bio 7 |
|                                                                                                         |
| Gamma_Sterilization_Valid.pdf     Validation      Steris Applied    2029-01-20     - DMF Section 6.3    |
|                                                                                    - EP Checklist Ster 8|
+---------------------------------------------------------------------------------------------------------+
| Traceability Summary: All 18 uploaded documents actively bound to 34 requirement nodes                  |
+---------------------------------------------------------------------------------------------------------+
```

---

## 7. Screen 6: Pre-Flight Validation and Gap Inspector

Before filing, the Validation Inspector performs a deep audit across four distinct checks:

```text
+---------------------------------------------------------------------------------------------------------+
| PRE-FLIGHT VALIDATION INSPECTOR                                              [ Re-Run Audit Now ]       |
| Submission: SUB-2026-001 (Form MD-14 Commercial Import)                                                 |
+---------------------------------------------------------------------------------------------------------+
| AUDIT RESULTS:   1 Blocking Error    |    1 Warning Advisory    |    0 Consistency Discrepancies        |
+---------------------------------------------------------------------------------------------------------+
| ISSUE LOG:                                                                                              |
|                                                                                                         |
| [ BLOCKING ERROR ]                                                                                      |
| Requirement: DMF Section 6.3 - Sterilization Validation Report                                          |
| Description: The device is designated as 'Sterile', but no validation report is linked to DMF 6.3.       |
| Fix:         Click here to attach 'Gamma_Sterilization_Valid.pdf' from Evidence Vault. [ Resolve Now ] |
|                                                                                                         |
| [ WARNING ADVISORY ]                                                                                    |
| Requirement: Free Sale Certificate (Germany)                                                            |
| Description: The attached FSC expires in 45 days. CDSCO evaluation typically takes 60-90 days.          |
| Recommendation: Consider requesting a renewed certificate to avoid mid-review queries.  [ Dismiss ]     |
+---------------------------------------------------------------------------------------------------------+
| [ Proceed to Interactive SUGAM Filing Guide -> ]                                                        |
+---------------------------------------------------------------------------------------------------------+
```

---

## 8. Screen 7: In-Application Interactive SUGAM Submission Guide (Primary Handoff)

This is the **core handoff feature**. Rather than abandoning the user with static files, the system acts as an interactive digital co-pilot that walks the user through filling the live government SUGAM portal step-by-step:

```text
+---------------------------------------------------------------------------------------------------------+
| IN-APPLICATION INTERACTIVE SUGAM FILING GUIDE (Form MD-14 Import Application)                           |
| Portal: cdscomdonline.gov.in / sugam.mohfw.gov.in                                [ Exit to Dashboard ]  |
+---------------------------------------------------------------------------------------------------------+
| FILING PROGRESS: [ Step 4 of 6: Document Uploads Tab ]  ( 65% Completed on Portal )                     |
| [v] 1. Portal Navigation   [v] 2. Applicant Details   [v] 3. Manufacturing Site   [*] 4. Document Upload|
+---------------------------------------------------------------------------------------------------------+
| STEP 4: DOCUMENT UPLOADS TAB GUIDE                                                                      |
| Instructions: Open Tab 'Technical Documents' on SUGAM. For each upload slot below, click               |
| 'Download File' and upload to the corresponding portal field. All files are verified < 10 MB.           |
|                                                                                                         |
| SUGAM Portal Field: "Power of Attorney (Rule 34)"                                                      |
| Prepared Document:  POA_SpineCraft_India_Apostilled_2026.pdf (4.2 MB)                                    |
| Portal Action:      [ Download This File ] -> Upload to Field #1               [x] Uploaded on Portal    |
|                                                                                                         |
| SUGAM Portal Field: "Free Sale Certificate (Country of Origin)"                                         |
| Prepared Document:  FSC_BfArM_Germany_Original.pdf (2.1 MB)                                              |
| Portal Action:      [ Download This File ] -> Upload to Field #2               [x] Uploaded on Portal    |
|                                                                                                         |
| SUGAM Portal Field: "Quality Management System Certificate (ISO 13485)"                                 |
| Prepared Document:  ISO13485_TUV_SUD_Certified.pdf (1.8 MB)                                              |
| Portal Action:      [ Download This File ] -> Upload to Field #3               [x] Uploaded on Portal    |
|                                                                                                         |
| SUGAM Portal Field: "Plant Master File (PMF as per Fourth Schedule)"                                    |
| Prepared Document:  PMF_Werk2_Tuttlingen_Compiled.pdf (7.8 MB)                                           |
| Portal Action:      [ Download This File ] -> Upload to Field #4               [ ] Pending Portal Upload |
|                                                                                                         |
| SUGAM Portal Field: "Device Master File (DMF as per Fourth Schedule)"                                    |
| Prepared Document:  DMF_OrthoSpine_System_Compiled.pdf (9.4 MB)                                          |
| Portal Action:      [ Download This File ] -> Upload to Field #5               [ ] Pending Portal Upload |
+---------------------------------------------------------------------------------------------------------+
| NAVIGATION:                                                                                             |
| [ <- Previous: Product Details Tab ]                     [ Mark Step Complete & Proceed: Fee Payment ->]|
+---------------------------------------------------------------------------------------------------------+
```

---

## 9. Screen 8: Optional Offline Archive & PDF Export Center

For legal record-keeping and corporate regulatory archives, the user can optionally download a complete compiled offline archive:

```text
+---------------------------------------------------------------------------------------------------------+
| OPTIONAL OFFLINE ARCHIVE & AUDIT EXPORT                                                                 |
| Generate offline permanent archives for legal retention and quality audits                             |
+---------------------------------------------------------------------------------------------------------+
| [ DOWNLOAD COMPLETE SUBMISSION ARCHIVE (ZIP) ]        [ DOWNLOAD PRINTABLE AUDIT SUMMARY (PDF) ]        |
+---------------------------------------------------------------------------------------------------------+
| COMPILED ARCHIVE STRUCTURE PREVIEW:                                                                     |
|                                                                                                         |
| MD14_MedTech_OrthoSpine_2026/                                                                           |
|   |-- 00_Executive_Summary_and_Audit_Checklist.pdf                                                      |
|   |-- 01_Covering_Letter_and_Device_Schedule.pdf                                                        |
|   |-- 02_BharatKosh_Fee_Receipt.pdf                                                                     |
|   |-- 03_Form_MD14_Signed_Application.pdf                                                               |
|   |-- 04_Power_of_Attorney_Apostilled.pdf                                                               |
|   |-- 05_Free_Sale_Certificate_Germany.pdf                                                              |
|   |-- 06_ISO13485_Quality_Certificate.pdf                                                               |
|   |-- 07_Plant_Master_File_Compiled.pdf                                                                 |
|   |-- 08_Device_Master_File_Compiled.pdf                                                                |
|   |-- 09_Essential_Principles_Checklist_Completed.pdf                                                   |
|   `-- 10_Product_Labels_and_IFU.pdf                                                                     |
+---------------------------------------------------------------------------------------------------------+
| ARCHIVE SUMMARY:                                                                                        |
| All prepared documents cleanly organized and numbered matching official CDSCO checklist order.          |
+---------------------------------------------------------------------------------------------------------+
```
