# CDSCO Medical Device Dossier Builder - Live Engineering Status

**Governing Rule:** [.agents/rules/implementation-workflow.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/.agents/rules/implementation-workflow.md)  
**Implementation Roadmap:** [06_TEAM_DISTRIBUTION_AND_SEQUENTIAL_WORKFLOW.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/06_TEAM_DISTRIBUTION_AND_SEQUENTIAL_WORKFLOW.md)  
**Verification Baseline:** [07_SYSTEM_VERIFICATION_AND_TEST_TRACEABILITY.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/07_SYSTEM_VERIFICATION_AND_TEST_TRACEABILITY.md)  

---

## Current Status Snapshot

* **Current Active Phase:** Phase 1 (Platform Core, Data Ingestion, and Workspace Shell)
* **Last Completed Sub-Task:** Task 1.1.2: Author and execute Alembic migrations for core PostgreSQL tables (2026-10-25 11:35 IST | Alembic revision `e0f736a11ec1`: create_core_tables)
* **Next Active Sub-Task:** **Task 1.1.3: Create GIN indexes on `application_definitions.schema_payload` and `submissions.regulatory_context`**

---

## Phase 1: Platform Core, Data Ingestion & Workspace Shell

### Task 1.1: Backend Project Scaffolding & Database Tier
- [x] **1.1.1:** Initialize Python 3.11+ FastAPI project structure with async SQLAlchemy 2.0, Pydantic v2, and Alembic configuration.
- [x] **1.1.2:** Author and execute Alembic migrations for core PostgreSQL tables:
  - `application_definitions`
  - `profiles`
  - `submissions`
  - `submission_entities`
  - `evidence_documents`
  - `evidence_links`
  - `validation_issues`
  - `background_jobs`
- [ ] **1.1.3:** Create GIN indexes on `application_definitions.schema_payload` and `submissions.regulatory_context`.

### Task 1.2: Application Definition & Slot Blueprint Service
- [ ] **1.2.1:** Author declarative JSON schema blueprint fixture for Form MD-14 (36 discrete upload slots).
- [ ] **1.2.2:** Author declarative JSON schema blueprint fixture for Form MD-7 (48 discrete upload slots).
- [ ] **1.2.3:** Build `DefinitionService` to load blueprints and resolve statutory slot hierarchies.
- [ ] **1.2.4:** Build `RulesEngine` predicate evaluator to activate/deactivate slots based on `regulatory_context`.

### Task 1.3: Abstract Storage Provider Architecture
- [ ] **1.3.1:** Define `StorageProvider` abstract base interface (`save_file`, `get_file_stream`, `delete_file`, `get_file_url`).
- [ ] **1.3.2:** Implement `LocalStorageProvider` writing to `./storage/submissions/{id}/...`.
- [ ] **1.3.3:** Implement `S3StorageProvider` interface (`boto3`) for AWS S3, Cloudflare R2, or MinIO.
- [ ] **1.3.4:** Implement SHA-256 cryptographic checksum calculation on all incoming file streams.

### Task 1.4: Evidence Ingestion & Document Service
- [ ] **1.4.1:** Build `POST /api/v1/submissions/{id}/evidence/upload` endpoint (multipart/form-data).
- [ ] **1.4.2:** Integrate PyMuPDF (`fitz`) to inspect uploaded PDFs: extract page count, byte size, PDF version.
- [ ] **1.4.3:** Build `POST /api/v1/submissions/{id}/evidence/link` endpoint to associate files with slots.
- [ ] **1.4.4:** Build `GET /api/v1/evidence/{document_id}/stream` with HTTP byte-range support.

### Task 1.5: Frontend Workspace Shell (Next.js 14 / TypeScript)
- [ ] **1.5.1:** Initialize Next.js 14 App Router project with Tailwind CSS and Lucide Icons.
- [ ] **1.5.2:** Configure TanStack React Query v5 for server-side state synchronization.
- [ ] **1.5.3:** Build Portfolio Dashboard view (`/`) showing active submissions and readiness progress.
- [ ] **1.5.4:** Build Setup Wizard view (`/submissions/new`) capturing Pathway, Modality, Class, and Profiles.
- [ ] **1.5.5:** Build Split-Screen Workspace (`/submissions/[id]`):
  - Left Pane: 36-48 Slot Checklist Tree with color-coded badges (Muted, Amber, Blue, Green, Red).
  - Center Pane: Entity Workspace Controller rendering 8-point regulatory guidance card.
- [ ] **1.5.6:** Build `FileUploadDropzone` supporting drag-and-drop PDF uploads with progress indicators.
- [ ] **1.5.7:** Integrate PDF.js viewer modal allowing in-browser document verification without downloading.

---

## Phase 2: Document Generation & Dossier Assembly (Engine 1 & 2)

### Task 2.1: Engine 1 – Statutory Jinja2 Templates & Pro-Formas
- [ ] **2.1.1:** Author official CDSCO Jinja2 HTML/CSS templates adhering to statutory margins:
  - `covering_letter.html` (Slot 1.0)
  - `essential_principles_checklist.html` (Slot 10.10)
  - `declaration_of_conformity.html` (Slot 10.8)
  - `non_commercial_undertaking.html` (Slot 10.13)
  - `tr6_fee_challan_summary.html` (Slot 2.0)
- [ ] **2.1.2:** Author docxtpl Microsoft Word (`.docx`) template for legal stamp-paper pro-forma:
  - `power_of_attorney_proforma.docx` (Slot 4.0)

### Task 2.2: Engine 1 – Guided Form Questionnaire Pipeline
- [ ] **2.2.1:** Build `GeneratorService` executing Jinja2 context merge and WeasyPrint headless PDF compilation.
- [ ] **2.2.2:** Build `POST /api/v1/submissions/{id}/slots/{slot_id}/generate` endpoint.
- [ ] **2.2.3:** Build `DynamicFormRenderer` component in Next.js using React Hook Form and Zod schemas.
- [ ] **2.2.4:** Implement Dual Fulfillment Toggle (Option A: Upload vs Option B: Generate) in UI.

### Task 2.3: Engine 2 – Master Dossier Assembly & Bates Stamping (DMF & PMF)
- [ ] **2.3.1:** Define Fourth Schedule statutory chapter sequence models (DMF Part III and PMF Part II).
- [ ] **2.3.2:** Build `AssemblyService` using PyMuPDF (`fitz`):
  - Calculate Two-Pass page offsets.
  - Compile Cover Page & dynamic Table of Contents.
  - Sequential PDF merge.
  - Continuous Bates stamping (`{prefix}-{page:04d} | Page {page} of {total}`).
  - Hierarchical outline bookmark injection.

### Task 2.4: Engine 2 – Strict 10MB Portal Threshold Downsampling Loop
- [ ] **2.4.1:** Implement pikepdf lossless stream deflation and object table cleanup.
- [ ] **2.4.2:** Implement PIL raster image downsampling to 150 DPI JPEG (80% quality).
- [ ] **2.4.3:** Implement Tier 3 Split Strategy (Core Dossier $\le 5\text{MB}$ + discrete Annexures $\le 10\text{MB}$).

### Task 2.5: Assembly Console UI & Asynchronous Job Status
- [ ] **2.5.1:** Configure FastAPI `BackgroundTasks` / worker runner for non-blocking assembly execution.
- [ ] **2.5.2:** Build `POST /api/v1/submissions/{id}/dossiers/{type}/assemble` returning 202 Accepted `{ job_id }`.
- [ ] **2.5.3:** Build `GET /api/v1/jobs/{job_id}` endpoint for polling assembly status and compression stats.
- [ ] **2.5.4:** Build Assembly Center view in Next.js with chapter tree, Bates configuration, and 10MB Threshold Gauge.

---

## Phase 3: Regulatory Intelligence, SUGAM Co-Pilot & Production

### Task 3.1: Continuous Pre-Submission Validation Engine
- [ ] **3.1.1:** Build `ValidationService` evaluating multi-tier statutory rules (Blockers, Errors, Warnings, Info).
- [ ] **3.1.2:** Build `GET /api/v1/submissions/{id}/validation-report` endpoint.
- [ ] **3.1.3:** Wire automatic validation triggers on file upload, slot update, or link deletion.
- [ ] **3.1.4:** Update global submission state machine (`IN_PREPARATION`, `VALIDATION_BLOCKED`, `SUBMISSION_READY`).

### Task 3.2: Slide-Out Validation Diagnostics Drawer
- [ ] **3.2.1:** Build `ValidationDrawer` component in Next.js.
- [ ] **3.2.2:** Render issue cards grouped by severity with 1-click "Fix Issue" button.

### Task 3.3: Interactive SUGAM Live Portal Filing Co-Pilot
- [ ] **3.3.1:** Build `SugamGuideService` mapping satisfied entities to 5 CDSCO portal tabs.
- [ ] **3.3.2:** Build `GET /api/v1/submissions/{id}/sugam-guide` endpoint.
- [ ] **3.3.3:** Build `SugamGuideModal` in Next.js with 1-click copy and verified $\le 10\text{MB}$ downloads.

### Task 3.4: Standardized Offline ZIP Package Exporter
- [ ] **3.4.1:** Build `POST /api/v1/submissions/{id}/export-handoff` endpoint with numbered folders and `manifest.json`.
- [ ] **3.4.2:** Add "Export Complete ZIP Archive" button to topbar and dashboard.

### Task 3.5: Production Hardening & Dockerization
- [ ] **3.5.1:** Configure `S3StorageProvider` for production.
- [ ] **3.5.2:** Implement auto-save debouncing (500ms).
- [ ] **3.5.3:** Author multi-stage `Dockerfile.backend` and `Dockerfile.frontend`.
- [ ] **3.5.4:** Author `docker-compose.prod.yml` (PostgreSQL 15, Redis, Backend, Frontend).
- [ ] **3.5.5:** Execute full End-to-End User Acceptance Test (UAT).
