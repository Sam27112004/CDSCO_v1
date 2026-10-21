# Sequential Team Distribution, Phase Workflows, and Progress Tracking Specification

**Document Identifier:** TDW-CDSCO-001  
**Revision:** 1.0  
**Classification:** Engineering Management, Team Distribution, and Implementation Roadmap  
**Governing Standard:** Medical Devices Rules, 2017 (MDR 2017), Gazette of India  
**Verified Primary Source:** CDSCO Online System for Medical Devices (`cdscomdonline.gov.in`)  
**Status:** Approved for Implementation & Tracking  

---

## 1. Executive Summary and Sequential Strategy Rationale

This specification establishes the operational development workflow and team distribution roadmap for the **CDSCO Medical Device Submission Dossier Builder**.

Because this platform involves strict statutory dependencies—ranging from **36 to 48 discrete portal upload slots**, **dynamic template pro-forma compilers**, and **multi-chapter Master Dossier assembly** under a strict **10MB file size ceiling**—an ad-hoc or disorganized multi-team build introduces severe integration risks.

### Why Sequential Team Distribution is Recommended
Instead of having multiple teams build overlapping layers concurrently (which causes database schema divergence, merge conflicts, and integration delays), this project is distributed **sequentially across distinct phases**:

```text
========================================================================================================================
                                     SEQUENTIAL EXECUTION & DEPENDENCY PIPELINE
========================================================================================================================

  [ PHASE 1: TEAM 1 ]                [ PHASE 2: TEAM 2 ]                 [ PHASE 3: TEAM 3 ]
  Platform Core & Workspace          Document Engines & Assembly         Filing Co-Pilot & Production
  +---------------------------+      +---------------------------+       +---------------------------+
  | - PostgreSQL Relational   |      | - Engine 1: Guided Form   |       | - Continuous Validation   |
  |   & JSONB Schema Core     |      |   Generator (WeasyPrint)  |       |   Diagnostics Engine      |
  | - Storage Provider Abstr. |      | - Engine 2: PyMuPDF fitz  |       | - Interactive SUGAM       |
  | - 36-48 Slot Tree & Nav   | ===> |   Dossier Stitching       | ====> |   Filing Co-Pilot Modal   |
  | - Evidence Vault & Upload |      | - 10MB pikepdf Downsample |       | - Numbered ZIP Exporter   |
  | - 8-Point Guidance View   |      | - Assembly Console UI     |       | - S3 Production Storage   |
  | - PDF.js In-Browser Viewer|      | - Dual Fulfillment Toggle |       | - Docker Deployment & UAT |
  +---------------------------+      +---------------------------+       +---------------------------+
                |                                  |                                   |
                v                                  v                                   v
       [ HAND-OFF GATE 1 ]                [ HAND-OFF GATE 2 ]                 [ FINAL RELEASE GATE ]
       Fully working workspace;           Every slot fulfilled via            Production-ready system
       slots trackable and files          upload or in-app generation;        ready for live CDSCO
       uploadable.                        dossiers compile under 10MB.        portal submission.
```

1. **Deterministic Hand-Offs:** Each team inherits a fully tested, functional baseline. Team 2 never has to mock database tables; Team 3 never has to mock compiled dossiers.
2. **Clear Accountability:** Quality defects and boundary mismatches are eliminated because each phase must satisfy an explicit **Definition of Done (DoD)** before the next team takes over.
3. **Single Source of Truth:** This document serves as the live progress tracker. Teams check off items as they complete them and sign off on hand-off gates.

---

## 2. Master Progress Tracking Dashboard

This dashboard reflects the live engineering status of the project. Update the status column (`NOT STARTED`, `IN PROGRESS`, `COMPLETED`) as milestones advance.

| Phase / Team | Primary Architectural Scope | Target Workload | Current Status | Gate Sign-Off |
| :--- | :--- | :--- | :--- | :--- |
| **Phase 1: Team 1** | Platform Core, Database Schema, 36–48 Slot Workspace, Evidence Vault | 4 to 5 Dev Days | NOT STARTED | [ ] Gate 1 Approved |
| **Phase 2: Team 2** | Engine 1 (Guided Form Generator), Engine 2 (Assembly & 10MB Downsampling) | 5 to 6 Dev Days | NOT STARTED | [ ] Gate 2 Approved |
| **Phase 3: Team 3** | Continuous Validation Engine, Interactive SUGAM Co-Pilot, ZIP Exporter, Production | 4 to 5 Dev Days | NOT STARTED | [ ] Final Release Approved |

---

## 3. Phase 1 (Team 1): Platform Core, Data Ingestion, and Workspace Shell

### 3.1 Team 1 Architectural Responsibility
Team 1 builds the operational foundation: the PostgreSQL persistence tier, the FastAPI gateway, the abstract storage provider, and the Next.js workspace that renders the 36 to 48 decomposed portal slots with the 8-point regulatory guidance model.

### 3.2 Team 1 Detailed Work Breakdown Structure (WBS)

```text
[ ] Task 1.1: Backend Project Scaffolding & Database Setup
    [ ] 1.1.1: Initialize Python 3.11+ FastAPI project with async SQLAlchemy 2.0 and Alembic.
    [ ] 1.1.2: Execute PostgreSQL 15+ DDL migrations for core tables:
               - application_definitions (JSONB schema blueprints)
               - submissions (master records, regulatory context JSONB)
               - submission_entities (36-48 tracked slots)
               - evidence_documents (file registry, SHA-256 hashes)
               - evidence_links (many-to-many slot and chapter mappings)
               - profiles (Applicant, Foreign Manufacturer, Manufacturing Sites)
    [ ] 1.1.3: Create GIN indexes on application_definitions.schema_payload and submissions.regulatory_context.

[ ] Task 1.2: Application Definition & Slot Blueprint Service
    [ ] 1.2.1: Author declarative JSON schema blueprints for Form MD-14 (36 discrete upload slots).
    [ ] 1.2.2: Author declarative JSON schema blueprints for Form MD-7 (48 discrete upload slots).
    [ ] 1.2.3: Build DefinitionService to load blueprints and resolve statutory slot hierarchies.
    [ ] 1.2.4: Build RulesEngine predicate evaluator to activate/deactivate slots based on:
               - Device Category (Medical Device vs IVD)
               - Risk Class (Class A, B, C, D)
               - Sterility (Sterile vs Non-Sterile)
               - Filing Modality (FRESH, ENDORSEMENT, RETENTION)

[ ] Task 1.3: Abstract Storage Provider Architecture
    [ ] 1.3.1: Define StorageProvider abstract base interface:
               - save_file(stream, path) -> str
               - get_file_stream(path) -> BinaryIO
               - delete_file(path) -> bool
               - get_file_url(path) -> str
    [ ] 1.3.2: Implement LocalStorageProvider writing to ./storage/submissions/{id}/...
    [ ] 1.3.3: Implement S3StorageProvider interface (boto3) for AWS S3, Cloudflare R2, or MinIO.
    [ ] 1.3.4: Implement SHA-256 cryptographic checksum calculation on all incoming streams.

[ ] Task 1.4: Evidence Ingestion & Document Service
    [ ] 1.4.1: Build POST /api/v1/submissions/{id}/evidence/upload endpoint (multipart/form-data).
    [ ] 1.4.2: Integrate PyMuPDF (fitz) to inspect uploaded PDFs: extract page count, byte size, PDF version.
    [ ] 1.4.3: Build POST /api/v1/submissions/{id}/evidence/link endpoint to associate files with slots.
    [ ] 1.4.4: Build GET /api/v1/evidence/{document_id}/stream with HTTP byte-range support.

[ ] Task 1.5: Frontend Workspace Shell (Next.js 14 / TypeScript)
    [ ] 1.5.1: Initialize Next.js 14 App Router project with Tailwind CSS and Lucide Icons.
    [ ] 1.5.2: Configure TanStack React Query v5 for server-side state synchronization.
    [ ] 1.5.3: Build Portfolio Dashboard view (/) showing active submissions and readiness progress.
    [ ] 1.5.4: Build Setup Wizard view (/submissions/new) capturing Pathway, Modality, Class, and Profiles.
    [ ] 1.5.5: Build Split-Screen Workspace (/submissions/[id]):
               - Left Pane: 36-48 Slot Checklist Tree with color-coded badges (Muted, Amber, Blue, Green, Red).
               - Center Pane: Entity Workspace Controller rendering 8-point regulatory guidance card.
    [ ] 1.5.6: Build FileUploadDropzone supporting drag-and-drop PDF uploads with upload progress indicator.
    [ ] 1.5.7: Integrate PDF.js viewer modal allowing in-browser document verification without downloading.
```

### 3.3 Team 1 Hand-Off Gate 1 Verification Checklist
Before handing off the codebase to Team 2, the following verification tests must pass:

- [ ] Database migrations execute cleanly from scratch on a fresh PostgreSQL instance.
- [ ] Seed script successfully populates a test Form MD-14 submission with 36 discrete slots.
- [ ] User can create a new submission via `/submissions/new` and view the resolved 36-slot tree.
- [ ] User can drag and drop a real PDF into Slot 10.3 (ISO 13485 Certificate).
- [ ] Backend calculates correct SHA-256, page count, and byte size, storing file in `./storage/`.
- [ ] The slot status badge immediately updates from `MISSING` (Amber) to `SATISFIED` (Green).
- [ ] Clicking "Preview PDF" opens the embedded PDF.js modal and renders the document properly.
- [ ] OpenAPI documentation is accessible at `http://localhost:8000/docs`.

---

## 4. Phase 2 (Team 2): Specialized Document Engines & Dossier Assembly

### 4.1 Team 2 Architectural Responsibility
Team 2 inherits the functional workspace from Team 1 and builds the two specialized compilation engines:
1. **Engine 1:** Guided Statutory Form Generator (compiling dynamic questionnaires into official PDFs/DOCXs).
2. **Engine 2:** Master Dossier Assembly Engine (stitching multi-chapter Fourth Schedule DMF/PMF dossiers, injecting dynamic TOCs, stamping Bates numbers, and downsampling to &le; 10MB).

### 4.2 Team 2 Detailed Work Breakdown Structure (WBS)

```text
[ ] Task 2.1: Engine 1 – Statutory Jinja2 Templates & Pro-Formas
    [ ] 2.1.1: Author official CDSCO Jinja2 HTML/CSS templates adhering to statutory margins:
               - covering_letter.html (Slot 1.0)
               - essential_principles_checklist.html (Slot 10.10)
               - declaration_of_conformity.html (Slot 10.8)
               - non_commercial_undertaking.html (Slot 10.13)
               - tr6_fee_challan_summary.html (Slot 2.0)
    [ ] 2.1.2: Author docxtpl Microsoft Word (.docx) templates for legal stamp-paper pro-formas:
               - power_of_attorney_proforma.docx (Slot 6.0)

[ ] Task 2.2: Engine 1 – Guided Form Questionnaire Pipeline
    [ ] 2.2.1: Build GeneratorService executing Jinja2 context merge and WeasyPrint headless PDF compilation.
    [ ] 2.2.2: Build POST /api/v1/submissions/{id}/slots/{slot_id}/generate endpoint:
               - Stores questionnaire JSONB payload into submission_entities.form_values.
               - Compiles PDF and saves to storage/submissions/{id}/generated/{uuid}.pdf.
               - Registers document in evidence_documents and creates link in evidence_links.
               - Automatically updates slot status to SATISFIED.
    [ ] 2.2.3: Build DynamicFormRenderer component in Next.js using React Hook Form and Zod schemas.
    [ ] 2.2.4: Implement Dual Fulfillment Toggle (Option A: Upload vs Option B: Generate) in UI:
               - Allows seamless switching between uploading an external file or using guided form.

[ ] Task 2.3: Engine 2 – Master Dossier Assembly & Bates Stamping (DMF & PMF)
    [ ] 2.3.1: Define Fourth Schedule statutory chapter sequence models:
               - Part II Device Master File (DMF: 14 chapters from 6.1 to 6.8)
               - Part III Plant Master File (PMF: 7 chapters from 1.0 to 7.0)
    [ ] 2.3.2: Build AssemblyService using PyMuPDF (fitz):
               - Queries evidence_links for all verified chapter attachments in order.
               - Dynamically compiles HTML Cover Page and Table of Contents (TOC) with hyperlinks.
               - Merges all chapter PDF streams into a unified master document.
               - Injects PDF hierarchical bookmarks matching Fourth Schedule chapters.
    [ ] 2.3.3: Implement Continuous Bates Page Numbering Stamper:
               - Configurable Bates prefix (e.g. "DMF-", "PMF-"), starting number, and font styling.
               - Coordinates: Centered at bottom margin (X: center, Y: height - 36 points).

[ ] Task 2.4: Engine 2 – Strict 10MB Portal Threshold Downsampling Loop
    [ ] 2.4.1: Implement size checking logic: If assembled PDF > 10.0 MB (10,485,760 bytes):
               - Execute pikepdf lossless stream recompression and deflate object tables.
    [ ] 2.4.2: If still > 10.0 MB:
               - Extract raster image streams, downsample to 150 DPI (sRGB color space) via PIL.
               - Re-pack PDF streams with optimized images.
    [ ] 2.4.3: Verify optimized PDF is &le; 10.0 MB; fail safely with actionable diagnostic if impossible.
    [ ] 2.4.4: Save final master dossier to storage/submissions/{id}/assembled/.

[ ] Task 2.5: Assembly Console UI & Asynchronous Job Status
    [ ] 2.5.1: Configure FastAPI BackgroundTasks / worker runner for non-blocking assembly execution.
    [ ] 2.5.2: Build POST /api/v1/submissions/{id}/dossiers/{type}/assemble returning 202 Accepted { job_id }.
    [ ] 2.5.3: Build GET /api/v1/jobs/{job_id} endpoint for polling assembly status and compression stats.
    [ ] 2.5.4: Build AssemblyCenter view in Next.js:
               - Chapter readiness tree showing which DMF/PMF chapters are satisfied.
               - Bates stamp configuration inputs.
               - Real-time 10MB Threshold Gauge with visual warning indicators.
               - 1-click compiled dossier download button.
```

### 4.3 Team 2 Hand-Off Gate 2 Verification Checklist
Before handing off the codebase to Team 3, the following verification tests must pass:

- [ ] Specialist can navigate to Slot 1.0 (Covering Letter), select "Generate via Guided Form", input values, and click "Generate Statutory Document".
- [ ] System compiles a valid PDF via WeasyPrint, stores it in `generated/`, and marks Slot 1.0 as `SATISFIED`.
- [ ] User can switch between Option A (Upload) and Option B (Generate) without data corruption.
- [ ] Specialist can navigate to Assembly Center, configure Bates prefix `DMF-`, and click "Assemble DMF".
- [ ] Background worker stitches 14 chapter PDFs, injects TOC, and applies continuous Bates stamps (`DMF-0001` to `DMF-0348`).
- [ ] If source files total 25MB+, the downsampler successfully compresses the final PDF to &le; 10.0 MB.
- [ ] The 10MB Threshold Gauge displays the final size in green and enables direct dossier download.


---

## 5. Phase 3 (Team 3): Regulatory Intelligence, SUGAM Co-Pilot, and Production

### 5.1 Team 3 Architectural Responsibility
Team 3 inherits the complete document and assembly platform. Team 3 builds the diagnostic validation engine, the live SUGAM portal filing co-pilot, the offline ZIP package exporter, and hardens the application for production deployment.

### 5.2 Team 3 Detailed Work Breakdown Structure (WBS)

```text
[ ] Task 3.1: Continuous Pre-Submission Validation Engine
    [ ] 3.1.1: Build ValidationService evaluating multi-tier statutory rules across active submission state:
               - TIER 1 (BLOCKER): Are any mandatory active slots still MISSING or INVALID?
               - TIER 2 (ERROR): Has any linked ISO 13485 or FSC certificate passed its expiry date?
               - TIER 3 (BLOCKER): Are all Fourth Schedule chapters present in compiled DMF/PMF?
               - TIER 4 (BLOCKER): Does any individual upload attachment exceed 10.0 MB?
               - TIER 5 (WARNING): Does any certificate expire within 90 days of planned lodgment?
               - TIER 6 (INFO): Are image downsampling opportunities detected?
    [ ] 3.1.2: Build GET /api/v1/submissions/{id}/validation-report returning issues by severity.
    [ ] 3.1.3: Wire automatic validation triggers: runs on file upload, slot update, or link deletion.
    [ ] 3.1.4: Update global submission status state machine:
               - Transitions to VALIDATION_BLOCKED if BLOCKER count > 0.
               - Transitions to SUBMISSION_READY if BLOCKER count == 0 and 100% mandatory slots satisfied.

[ ] Task 3.2: Slide-Out Validation Diagnostics Drawer
    [ ] 3.2.1: Build ValidationDrawer component in Next.js accessible from persistent topbar badge.
    [ ] 3.2.2: Render issue cards grouped by severity (BLOCKER, ERROR, WARNING, INFO).
    [ ] 3.2.3: Include 1-click "Fix Issue" button on each card that immediately jumps focus to violating slot.

[ ] Task 3.3: Interactive SUGAM Live Portal Filing Co-Pilot
    [ ] 3.3.1: Build SugamGuideService mapping satisfied entities to exact CDSCO online portal tabs:
               - Tab 1: Application Form Details (Form MD-14 reference, dates, applicant name).
               - Tab 2: Regulatory Profiles (Foreign manufacturer, manufacturing site addresses).
               - Tab 3: Device Master Details (Intended use, brand names, model numbers, shelf life).
               - Tab 4: Statutory Checklist Upload Slots (36 to 48 slots).
               - Tab 5: Fee Payment & TR6 Challan reference details.
    [ ] 3.3.2: Build GET /api/v1/submissions/{id}/sugam-guide returning formatted portal payloads.
    [ ] 3.3.3: Build SugamGuideModal in Next.js providing split-screen side-by-side filing companion:
               - 1-click clipboard copy buttons for formatted text inputs.
               - 1-click verified download buttons for pre-checked slot PDF attachments (&le; 10MB).
               - Checkbox tracking: "Mark slot uploaded on CDSCO portal".

[ ] Task 3.4: Standardized Offline ZIP Package Exporter
    [ ] 3.4.1: Build POST /api/v1/submissions/{id}/export-handoff endpoint:
               - Creates structured directory hierarchy matching CDSCO slot codes:
                 01_Covering_Letter/
                 02_TR6_Challan/
                 ...
                 10_11_Device_Master_File/
                 10_12_Plant_Master_File/
               - Generates manifest.json containing metadata, SHA-256 checksums, and filing date.
               - Streams compressed .zip archive to client.
    [ ] 3.4.2: Add "Export Complete ZIP Archive" button to topbar and dashboard.

[ ] Task 3.5: Production Hardening, Storage Configuration & Dockerization
    [ ] 3.5.1: Configure S3StorageProvider for production using AWS S3, Cloudflare R2, or MinIO.
    [ ] 3.5.2: Implement auto-save keystroke debouncing (500ms) to ensure zero data loss on user logout.
    [ ] 3.5.3: Author production multi-stage Dockerfiles:
               - Dockerfile.frontend (Next.js standalone build)
               - Dockerfile.backend (Uvicorn + FastAPI with PyMuPDF and WeasyPrint dependencies)
    [ ] 3.5.4: Author docker-compose.prod.yml with PostgreSQL 15, Redis, Backend, and Frontend containers.
    [ ] 3.5.5: Conduct end-to-end user acceptance testing (UAT) simulating full Form MD-14 filing workflow.
```

### 5.3 Team 3 Hand-Off Gate 3 (Production Go-Live) Verification Checklist
Before declaring the system ready for production launch, the following acceptance criteria must pass:

- [ ] System detects an expired ISO 13485 certificate and raises an `ERROR` flag in the Validation Drawer.
- [ ] 1-click "Fix Issue" button scrolls the workspace directly to the violating slot.
- [ ] Adding a valid certificate clears the diagnostic and updates submission status to `SUBMISSION_READY`.
- [ ] Launching the SUGAM Co-Pilot displays side-by-side filing guidance matching all 5 portal tabs.
- [ ] Clicking "Copy" copies exact formatted text to the OS clipboard.
- [ ] Clicking "Download" delivers the verified, Bates-stamped, &le; 10MB attachment.
- [ ] Clicking "Export ZIP" downloads a complete, numbered archive with `manifest.json`.
- [ ] User logging out mid-questionnaire loses zero data; logging back in restores exact state.
- [ ] Production Docker containers start cleanly via `docker compose -f docker-compose.prod.yml up`.

---

## 6. Alternative 2-Team Sequential Distribution Model

If the project is executed by **two teams** instead of three, the work is partitioned into two equal, self-contained milestones:

```text
========================================================================================================================
                                     2-TEAM ALTERNATIVE SEQUENTIAL WORKFLOW
========================================================================================================================

  [ TEAM A: PLATFORM & DOCUMENT GENERATION ] ────────(Milestone Hand-off)────────► [ TEAM B: COMPILATION & FILING ]
  
  Scope: Tasks 1.1 through 2.2                                                      Scope: Tasks 2.3 through 3.5
  - PostgreSQL & JSONB Data Model                                                   - Engine 2: PyMuPDF Stitching & Bates
  - 36-48 Slot Tree & Navigation                                                    - pikepdf 10MB Stream Downsampler
  - Evidence Vault & PDF.js Viewer                                                  - Assembly Console UI
  - 8-Point Guidance Model                                                          - Continuous Validation Diagnostics
  - Engine 1: Jinja2 + WeasyPrint Generators                                        - Interactive SUGAM Co-Pilot
  - Dual Fulfillment Toggle (Upload vs Generate)                                    - Offline ZIP Package Exporter
                                                                                    - S3 Storage & Docker Production
  
  Hand-off Baseline:                                                                Final Release:
  A running portal where users can manage 36-48                                     A complete production regulatory
  slots and generate all statutory pro-formas.                                      platform with live portal guidance.
```

---

## 7. Hand-off Protocols and Development Rules

To ensure seamless transitions between teams, all contributors must observe these four rules:

1. **No Breaking Schema Changes Without Migration Scripts:**
   * Any change to database tables must be delivered via an Alembic migration script (`alembic upgrade head`). Never alter columns manually.
2. **API-First Contracts:**
   * All endpoints, payload formats, and status codes must strictly match the specifications in [04_ENGINEERING_AND_DATA_MODEL_SPEC.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/04_ENGINEERING_AND_DATA_MODEL_SPEC.md).
3. **Automated Seed Data Requirement:**
   * The departing team must provide working database seeds (`python scripts/seed_db.py`) so the incoming team can spin up a fully populated test environment in under 60 seconds.
4. **Active Documentation Updates:**
   * Whenever a team finishes a feature, they must update the corresponding checkboxes in this tracking specification to reflect the current state of the repository.

---

## 8. Cross-Reference Index

* For architectural schematics and end-to-end data flows, refer to [03_SYSTEM_ARCHITECTURE_AND_DATA_FLOW.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/03_SYSTEM_ARCHITECTURE_AND_DATA_FLOW.md).
* For complete PostgreSQL DDL schemas, Pydantic models, and RESTful route tables, refer to [04_ENGINEERING_AND_DATA_MODEL_SPEC.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/04_ENGINEERING_AND_DATA_MODEL_SPEC.md).
* For detailed logic governing the 35 statutory documents and guided form generation templates, refer to [05_DOCUMENT_ENGINES_AND_FULFILLMENT_LOGIC.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/05_DOCUMENT_ENGINES_AND_FULFILLMENT_LOGIC.md).
* For statutory definitions, CDSCO portal upload slot mappings, and Fourth Schedule DMF/PMF hierarchies, refer to [05_REGULATORY_FORMS_AND_DOSSIER_MATRIX.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/05_REGULATORY_FORMS_AND_DOSSIER_MATRIX.md).
