# CDSCO Medical Device Submission Dossier Builder

A high-assurance regulatory workspace for preparing, validating, and organizing complete CDSCO medical device applications and supporting technical dossiers (Device Master File, Plant Master File, Essential Principles) prior to submission on the CDSCO **SUGAM / MD-Portal** under the **Medical Device Rules (MDR) 2017**.

---

## Current Status: Phase 1 Complete (Platform Core, Ingestion & Workspace Shell)

All 7 core milestones of **Phase 1** are fully implemented, verified, and passing 144 automated tests:
1. **Scaffolding & Database Tier (Task 1.1):** Async SQLAlchemy 2.0, Alembic migrations, PostgreSQL 15, and GIN indexes.
2. **Statutory Slot Blueprints (Task 1.2):** Form MD-14 (Import, 36 slots) & Form MD-7 (Manufacturing, 48 slots) blueprints with dynamic DSL rules engine.
3. **Storage Architecture (Task 1.3):** Abstract `StorageProvider` (Local disk & AWS S3/MinIO) with streaming SHA-256 cryptographic verification.
4. **Evidence Ingestion Service (Task 1.4):** PyMuPDF (`fitz`) inspection, RFC 7233 byte-range streaming (`GET /api/v1/evidence/{id}/stream`), and automatic image (`.jpg`, `.png`, `.webp`) and Word (`.docx`) to PDF conversion (`DocumentConverter`).
5. **Next.js 14 Frontend Workspace (Task 1.5):**
   - **Portfolio Dashboard (`/`):** Submission tracking, readiness gauges, pathway filtering.
   - **Setup Wizard (`/submissions/new`):** 3-step setup with smart statutory licensing constraints (CLA strictly Class C/D; SLA strictly Class A/B).
   - **Split-Screen Workspace (`/submissions/[id]`):** 36-48 slot checklist tree, 8-point statutory guidance card, attached evidence management.
   - **File Upload Dropzone:** Drag-and-drop upload with 10.0 MB CDSCO portal ceiling enforcement and live progress animation.
   - **In-Browser PDF Viewer Modal:** Zero-dependency in-browser document verification via RFC 7233 byte-range streaming, SHA-256 hash copying, and fullscreen expansion.

---

## Quickstart Guide: How to Run the Project

You can run the entire platform with one single Docker command, or run the services locally.

### Option A: Run Everything via Docker Compose (Recommended)

Run one command from the project root:

```bash
docker compose up --build
```

This starts:
- **PostgreSQL 15 Database:** Unified container `cdsco-postgres` running on port `5433` (avoiding port `5432` conflicts with local Windows PostgreSQL instances).
- **FastAPI Backend:** Runs migrations automatically and exposes endpoints on `http://localhost:8000` (Interactive API Swagger Docs: `http://localhost:8000/docs`).
- **Next.js 14 Frontend:** Accessible in your browser at `http://localhost:3000`.

To stop the containers:
```bash
docker compose down
```

---

### Option B: Run Locally for Development

If you prefer running services directly on your host machine:

#### 1. Start the PostgreSQL Container
```bash
docker start cdsco-postgres
```
*(Runs PostgreSQL on port `5433` matching the default `.env` configuration).*

#### 2. Start the FastAPI Backend
```bash
# In terminal 1:
backend\.venv\Scripts\uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
- API Root: `http://127.0.0.1:8000/`
- Interactive OpenAPI Docs: `http://127.0.0.1:8000/docs`

#### 3. Start the Next.js Frontend
```bash
# In terminal 2:
npm --prefix frontend run dev
```
- Web Application: `http://localhost:3000`

---

## Step-by-Step Testing & User Acceptance Guide

Here is how you can interactively test everything built in Phase 1:

### 1. Test the Portfolio Dashboard (`http://localhost:3000`)
- Open `http://localhost:3000` in your browser.
- You will see the Portfolio Dashboard with aggregate statutory metrics:
  - Total active submissions
  - In Preparation vs Validation Blocked counts
  - Average readiness progress across applications
- The search bar lets you filter applications by tracking code, device family name, or pathway.
- Pathway filter pills allow filtering by Form MD-14, MD-7, MD-8, etc.

### 2. Test the Statutory Setup Wizard (`http://localhost:3000/submissions/new`)
- Click **"Initialize New Application"** in the top navigation or dashboard.
- **Step 1 (Pathway & Modality):**
  - Choose between Form MD-14 (Import) and Form MD-7 (Domestic Manufacturing).
  - Select filing modality: Fresh Application, Renewal, or Post-Approval Change.
- **Step 2 (Device Identity & Statutory Risk Class):**
  - Select Device Category: Medical Device vs IVD.
  - Enter the Device Family Name (e.g., `Cardiovascular Balloon Dilatation Catheter`).
  - **Verify Smart Statutory Constraints (TC-UR01-01):**
    - When Form MD-7 is selected (regulated by Central Licensing Authority / CLA), notice that **Class A and Class B are automatically disabled** with an explanatory statutory tooltip, because SLA regulates Class A & B.
    - Select **Class C** or **Class D**.
- **Step 3 (Organizational Profiles & Review):**
  - Select Applicant, Foreign Manufacturer, and Manufacturing Site profiles (seeded automatically from Indian statutory defaults).
  - Verify the live calculation of checklist slots (e.g., 36 slots for MD-14, 48 slots for MD-7).
  - Click **"Create Submission Workspace"**. The workspace initializes and opens automatically!

### 3. Test the Split-Screen Workspace (`http://localhost:3000/submissions/{id}`)
- **Left Pane (Statutory Checklist Tree):**
  - Browse 36 to 48 statutory slots organized by regulatory category (Administrative Documents, Technical Specifications, Quality Management, Performance Reports).
  - Filter slots by status: All, Missing (red), or Satisfied (green).
  - Search slots dynamically by title or slot number (e.g., `Covering Letter` or `10.1`).
- **Center Pane (Guidance Card & Fulfillment Area):**
  - Clicking any slot in the left pane updates the center pane immediately.
  - Read the **8-Point Regulatory Guidance Card**:
    1. What the document is
    2. Why CDSCO requires it
    3. Official MDR 2017 citation / rule
    4. Issuing authority
    5. Validity period & expiration criteria
    6. Target SUGAM portal upload tab
    7. Mandatory checklist inclusions
    8. Critical pitfalls & common rejection triggers

### 4. Test Evidence Upload & Format Converter (Task 1.4.5 & 1.5.6)
- In the center pane under **Evidence Fulfillment**:
  - Test client-side validation: try selecting or dragging a file larger than 10.0 MB. It immediately displays a red rejection notice without network transmission.
  - Drag and drop or browse for a valid file:
    - **Standard PDF file (`.pdf`)**
    - **Word document (`.docx`)**
    - **Scanned image (`.jpg`, `.png`, `.webp`)**
  - Enter an optional custom document title or keep the default.
  - Click **"Upload & Link to Slot"**.
  - Watch the live 4-stage progress animation:
    1. Binary upload (35%)
    2. Ingestion conversion & PyMuPDF pre-flight checks (70%)
    3. Slot association (90%)
    4. Cataloged in vault & status updated (100%)
  - Notice that Word and image files are automatically converted to standardized PDFs in-memory!
  - The slot status immediately changes to **SATISFIED** (green badge) in both the header and the left-hand checklist tree!

### 5. Test In-Browser PDF.js Viewer Modal (Task 1.4.4 & 1.5.7)
- In the **Attached Documents in Vault** list, click the **"Verify"** button with the eye icon on any document row (or click the row directly).
- The **In-Browser PDF Viewer Modal** opens:
  - The PDF document streams directly from the backend using RFC 7233 HTTP 206 Partial Content byte ranges without downloading to your hard drive.
  - In the modal header:
    - Slot ID badge and Document Title.
    - Verified File Size and Page Count.
    - **SHA-256 Cryptographic Checksum Pill:** Click the copy button to copy the SHA-256 fingerprint to your clipboard.
  - Click the **Fullscreen** button to expand the viewer to full screen.
  - Press the **Esc** key (or click the close button `X`) to smoothly dismiss the modal.

---

## Automated Backend Regression Suite

To execute all 144 unit, integration, and API tests:

```bash
backend\.venv\Scripts\pytest
```

To run tests with code coverage analysis:
```bash
backend\.venv\Scripts\pytest --cov=app --cov-report=term-missing
```

*Current Test Baseline:* **144 tests passing in ~5 seconds with 80% total codebase coverage.**

---

## Complete Documentation Index

All business rationale, user requirements, UI/UX screen mockups, and technical specifications are organized in the `docs/` directory:

### Product Requirements & Presentation Suite
* **[01. Project Concept and Vision](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/01_PROJECT_CONCEPT_AND_VISION.md)**: Executive pitch, core pain points in CDSCO filings, platform solution, and business value.
* **[02. User Requirements and Capabilities](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/02_USER_REQUIREMENTS_AND_CAPABILITIES.md)**: User personas, Jobs-to-be-Done, and core capabilities in plain business language.
* **[03. UI/UX Design and Screen Walkthroughs](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/03_UI_UX_DESIGN_AND_SCREEN_WALKTHROUGHS.md)**: Visual screen wireframes for Dashboard, Setup Wizard, Entity Workspace, Evidence Vault, and SUGAM Handoff Center.
* **[04. Conceptual System Design](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/04_CONCEPTUAL_SYSTEM_DESIGN.md)**: Application structure, core data components, conditional checklist filtering, and pre-submission checks.
* **[05. Regulatory Forms and Technical Dossier Matrix](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/05_REGULATORY_FORMS_AND_DOSSIER_MATRIX.md)**: Comparative matrix across all seven MDR 2017 application streams and Fourth Schedule DMF/PMF hierarchies.

### Technical Specifications Suite
* **[01. Project Charter & Scope](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/01_PROJECT_CHARTER_AND_SCOPE.md)**: Statutory standards, jurisdiction boundaries, and milestone schedule.
* **[02. User Requirements Specification (URS)](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/02_USER_REQUIREMENTS_SPECIFICATION_URS.md)**: Formal engineering requirements (UR-01 through UR-09) prioritized by MoSCoW criteria.
* **[03. System Architecture & Data Flow](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/03_SYSTEM_ARCHITECTURE_AND_DATA_FLOW.md)**: Multi-engine architecture, operational sequences, and entity state machines.
* **[04. Engineering & Data Model Spec](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/04_ENGINEERING_AND_DATA_MODEL_SPEC.md)**: Relational schemas, DSL rules engine, RESTful API endpoints, and validation severities.
* **[05. Document Engines & Dual Fulfillment Logic](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/05_DOCUMENT_ENGINES_AND_FULFILLMENT_LOGIC.md)**: Cross-form document landscape, engine applicability, guided questionnaire processing, and multi-file dossier assembly under 10MB.
* **[06. Team Distribution & Sequential Workflow](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/06_TEAM_DISTRIBUTION_AND_SEQUENTIAL_WORKFLOW.md)**: Granular WBS checklists, acceptance gates, and live progress tracking dashboard.
* **[07. System Verification & Test Traceability Matrix](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/07_SYSTEM_VERIFICATION_AND_TEST_TRACEABILITY.md)**: Complete RTM mapping every requirement to automated unit, integration, and E2E test suites.
* **[Live Engineering Status](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/project-status.md)**: Live task tracker showing completion status of every phase and sub-task.
