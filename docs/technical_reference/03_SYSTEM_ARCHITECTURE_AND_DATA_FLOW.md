# System Architecture and Data Flow Specification

**Document Identifier:** SAD-CDSCO-001  
**Revision:** 3.1  
**Classification:** Full-Stack Architecture, Component Interconnection, and Data Flow Blueprint  
**Governing Standard:** Medical Devices Rules, 2017 (MDR 2017), Gazette of India  
**Verified Primary Source:** CDSCO Online System for Medical Devices (`cdscomdonline.gov.in`)  
**Status:** Approved for Implementation  

---

## 1. Executive Architectural Baseline and Scope

This specification establishes the full-stack system architecture and operational data flow model for the **CDSCO Medical Device Submission Dossier Builder**. 

The system automates the preparation, generation, verification, and assembly of complex regulatory dossiers submitted to India's Central Drugs Standard Control Organisation (CDSCO) via the online SUGAM / MD Online portal.

The architecture directly addresses five critical regulatory and engineering constraints:
1. **Decomposed Slot Topologies:** Tracking between 36 and 48 discrete upload slots per application (such as Form MD-14, MD-7, MD-8, MD-3, MD-4, MD-12, and MD-16).
2. **Dual Fulfillment Modality:** Allowing regulatory specialists to either upload an existing external document or generate statutory declarations directly in the system using guided questionnaires and templating engines.
3. **Multi-Chapter Technical Dossier Stitching:** Assembling modular Device Master Files (DMF) and Plant Master Files (PMF) with automated Table of Contents (TOC) injection, chapter divider bookmarks, and continuous Bates numbering.
4. **Strict 10MB Portal Threshold Enforcement:** Compressing, optimizing, and downsampling large compiled PDFs (150 DPI) to ensure final dossiers comply with portal file size ceilings without human intervention.
5. **Interactive Co-Pilot Portal Lodgment:** Bridging the gap between the offline builder and the live government portal by providing field-by-field clipboard transfer and slot-verified document handoffs.

---

## 2. Global System Topology and Component Interconnections

The system is structured as a decoupled, 3-tier architecture. To ensure complete visual clarity and immediate readability across all development tools and text editors, all architectural diagrams are provided as formatted structural schematics.

```text
========================================================================================================================
                                     CDSCO DOSSIER BUILDER - GLOBAL SYSTEM TOPOLOGY
========================================================================================================================

+----------------------------------------------------------------------------------------------------------------------+
| 1. FRONTEND CLIENT TIER (Next.js 14 App Router / React 18 / TypeScript)                                              |
|                                                                                                                      |
|  +--------------------+   +-----------------------+   +---------------------+   +----------------------------------+ |
|  |  Slot Navigator    |   |  Entity Workspace     |   | Dynamic Form Engine |   | Evidence Vault & Dropzone        | |
|  |  (36-48 Slots)     |-->|  Controller           |-->| (Zod + Hook Form)   |   | (Chunked Upload + PDF.js Viewer) | |
|  +--------------------+   +-----------------------+   +---------------------+   +----------------------------------+ |
|            |                         |                           |                               |                   |
|  +--------------------+   +-----------------------+   +---------------------+                    |                   |
|  | Assembly Console   |   | Validation Drawer     |   | SUGAM Co-Pilot      |                    |                   |
|  | (10MB Gauge+Bates) |   | (Blockers / Errors)   |   | (Portal Companion)  |                    |                   |
|  +--------------------+   +-----------------------+   +---------------------+                    |                   |
|            |                         |                           |                               |                   |
|  +-----------------------------------------------------------------------------------------------------------------+ |
|  | TanStack React Query v5 State Cache  |  Zustand UI Store  |  Axios / Fetch HTTP Client & Event Stream Listener  | |
+--+-----------------------------------------------------------------------------------------------------------------+-+
                                      |                                                ^
                   RESTful JSON APIs  |  Multipart Form Streams                        | Server-Sent Events / Polling
                                      v                                                |
+----------------------------------------------------------------------------------------------------------------------+
| 2. API GATEWAY & SECURITY LAYER (FastAPI Async ASGI Server / Python 3.11+)                                           |
|                                                                                                                      |
|  [ CORS & Security Headers ] ---> [ Bearer JWT Authentication ] ---> [ Pydantic v2 Request / Response Validation ]  |
|                                                                                                                      |
|  Routers:  /submissions  |  /slots  |  /evidence  |  /generator  |  /assembly  |  /validation  |  /sugam-guide       |
+----------------------------------------------------------------------------------------------------------------------+
                                      |
                                      v
+----------------------------------------------------------------------------------------------------------------------+
| 3. BACKEND DOMAIN SERVICES & SPECIALIZED COMPILATION ENGINES                                                         |
|                                                                                                                      |
|  +------------------------+  +----------------------+  +------------------------+  +-------------------------------+ |
|  | Definition & Blueprint |  | Rules & Predicate    |  | Document & Evidence    |  | Continuous Validation         | |
|  | Service                |  | Evaluation Engine    |  | Management Service     |  | Service                       | |
|  | (Loads 36-48 Schemas)  |  | (JSON DSL Context)   |  | (SHA-256 + Metadata)   |  | (Blockers / Expiry Rules)     | |
|  +------------------------+  +----------------------+  +------------------------+  +-------------------------------+ |
|               |                         |                          |                              |                  |
|  +--------------------------------------------------+  +-----------------------------------------------------------+ |
|  | ENGINE 1: Guided Form Generator Pipeline         |  | ENGINE 2: Master Dossier Assembly & 10MB Optimizer        | |
|  | - Jinja2 Template Pro-Forma Engine               |  | - PyMuPDF (fitz) Multi-Chapter Stitching                  | |
|  | - WeasyPrint CSS-to-PDF Print Engine             |  | - Dynamic Table of Contents (TOC) & Bookmark Generator    | |
|  | - docxtpl Official Word (.docx) Filler           |  | - Continuous Bates Page Numbering Stamper                 | |
|  |                                                  |  | - pikepdf / qpdf Stream Optimizer & 150 DPI Downsampler   | |
|  +--------------------------------------------------+  +-----------------------------------------------------------+ |
+----------------------------------------------------------------------------------------------------------------------+
                         |                                                     |
                         | Dispatches Heavy Jobs                               | Dispatches Heavy Jobs
                         v                                                     v
+----------------------------------------------------------------------------------------------------------------------+
| 4. ASYNCHRONOUS BACKGROUND TASK WORKER (FastAPI BackgroundTasks / Celery Worker Pipeline)                            |
|                                                                                                                      |
|  - High-Resolution HTML-to-PDF Statutory Rendering                                                                   |
|  - 300+ Page Master Dossier Stitching (Device Master File & Plant Master File)                                       |
|  - Automated Stream Recompression & 150 DPI Downsampling (10MB Ceiling Enforcement)                                  |
+----------------------------------------------------------------------------------------------------------------------+
                         |                                                     |
                         v                                                     v
+----------------------------------------------------+   +-------------------------------------------------------------+
| 5. PERSISTENCE ENGINE (PostgreSQL 15+)             |   | 6. BINARY STORAGE ENGINE (Local Disk or S3 / MinIO)          |
|                                                    |   |                                                             |
|  - Relational Core:                                |   |  storage/submissions/{submission_id}/                       |
|    * submissions (Master filing records)           |   |   ├── raw/        (Uploaded vendor test reports & certs)    |
|    * submission_entities (36-48 tracked slots)     |   |   ├── generated/  (Engine 1 pro-formas & declarations)      |
|    * evidence_documents & evidence_links (M:N)     |   |   ├── assembled/  (Compiled DMF/PMF & 10MB optimized PDFs)  |
|    * validation_issues (Categorized diagnostics)   |   |   └── export/     (Structured offline ZIP packages)         |
|  - GIN Indexed JSONB: Dynamic questionnaires       |   |                                                             |
+----------------------------------------------------+   +-------------------------------------------------------------+
```

---

## 3. Frontend Internal Architecture and Subsystem Interactions

The frontend is constructed using Next.js 14 (App Router) and React 18, strictly typed in TypeScript. It operates as an interactive, single-window workspace that eliminates multi-tab disorientation for regulatory specialists.

```text
========================================================================================================================
                                          FRONTEND CLIENT SUBSYSTEM TOPOLOGY
========================================================================================================================

+----------------------------------------------------------------------------------------------------------------------+
| VIEWPORT CONTAINER (Next.js 14 App Router / Tailwind CSS / Lucide Icons)                                              |
|                                                                                                                      |
|  LEFT PANE (30% Width)                         CENTER WORKSPACE PANE (70% Width)                                     |
|  +-----------------------------------------+   +-------------------------------------------------------------------+ |
|  | 36-48 SLOT CHECKLIST TREE               |   | ENTITY WORKSPACE CONTROLLER                                       | |
|  |                                         |   |                                                                   | |
|  | [Filters: Modality | Risk Class | IVD]  |   | [Active Slot Header: Slot 10.14 - Pre-Clinical Biocompatibility]  | |
|  |                                         |   |                                                                   | |
|  | - Slot 1.0  Covering Letter    [GREEN]  |   | [8-Point Regulatory Guidance Card]                                | |
|  | - Slot 2.0  TR6 Fee Challan    [GREEN]  |   |  - Statutory Reference: Rule 34 / Fourth Schedule Part II         | |
|  | - Slot 3.0  Form MD-14         [GREEN]  |   |  - Pro-Forma Standards: ISO 10993 Series Endpoints                | |
|  | - Slot 10.1 ISO 13485 Cert     [GREEN]  |   |  - Common Rejection Reasons: Missing Cytotoxicity or GLP seals    | |
|  | - Slot 10.11 Device Master File [AMBER]  |   |                                                                   | |
|  | - Slot 10.14 Biocompatibility  [BLUE]   |   | [DUAL FULFILLMENT CONTROLLER]                                     | |
|  |                                         |   |  ( * ) Option A: Upload Existing PDF                              | |
|  | [Live Readiness Meter: 32 / 36 Slots]   |   |  (   ) Option B: Generate Document via Guided Form                | |
|  +-----------------------------------------+   |                                                                   | |
|                        |                       |  [FILE DROPZONE & PDF.js PREVIEW]                                 | |
|                        | Selected Slot Event   |  Drop "ISO_10993_Biocompatibility_Report.pdf" here                | |
|                        v                       |  [View PDF in Embedded Modal]  [Extract Page Count: 48 Pages]     | |
|  +-----------------------------------------+   +-------------------------------------------------------------------+ |
|  | VALIDATION DRAWER (Slide-out Overlay)   |                                     |                                   |
|  |                                         |                                     | Auto-Save / Mutation Event        |
|  | - [BLOCKER] Slot 10.11 DMF Missing      |                                     v                                   |
|  | - [WARNING] Slot 10.3 ISO Expires Soon |   +-------------------------------------------------------------------+ |
|  |                                         |   | CLIENT STATE & DATA SYNCHRONIZATION                               | |
|  | [1-Click Jump to Fix Button]            |   | - TanStack React Query v5 (Server-side cache & auto-invalidation) | |
|  +-----------------------------------------+   | - React Hook Form + Zod (Form schema validation & dirty tracking) | |
|                                                | - Zustand (Active slot ID, drawer visibility, modal states)       | |
+------------------------------------------------+-------------------------------------------------------------------+--+
                                                                   |
                                                                   v
                                     [ Axios / Fetch HTTP Client with Bearer JWT Auth ]
```

### Detailed Frontend Subsystems

1. **Navigator & Slot Tree Subsystem:**
   * Reads the active submission tree containing 36 to 48 portal upload slots.
   * Renders color-coded status badges: `NOT_APPLICABLE` (muted gray), `MISSING` (alert amber), `IN_PROGRESS` (active blue), `SATISFIED` (success green), and `INVALID` (critical red).
   * Filters slots dynamically based on active filing modality (`FRESH`, `ENDORSEMENT`, `RETENTION`) and device classification.
2. **Entity Workspace Controller:**
   * Manages single-slot active view rendering.
   * Injects the standard 8-point regulatory guidance model:
     - Statutory Rule Reference (MDR 2017 specific clause).
     - Official CDSCO Checklist Description.
     - Regulatory Purpose and Legal Context.
     - Required Document Structure and Pro-Forma Standards.
     - Common Rejection Reasons and Query Triggers.
     - Acceptable Alternative Equivalencies.
     - Cross-Reference Verification Checkpoints.
     - Dual Fulfillment Action Controls.
3. **Dynamic Form Questionnaire Renderer:**
   * Dynamically renders input forms from declarative JSON schemas when Option B (Generate via Guided Form) is selected.
   * Manages conditional input visibility, input masks, and immediate client-side validation using React Hook Form and Zod schemas.
4. **Evidence Uploader and Embedded Viewer:**
   * Provides drag-and-drop file ingestion supporting PDF documents.
   * Validates MIME types and checks raw file size prior to upload.
   * Embeds PDF.js to allow immediate full-text viewing, zoom, and page navigation without downloading files locally.
5. **Dossier Assembly Console and 10MB Gauge:**
   * Configures compilation parameters for Master Dossiers (DMF and PMF).
   * Renders real-time file size meters with visual warnings as output nears the 10MB CDSCO portal threshold.
   * Exposes controls for Bates stamp prefix, starting index, stamp position, and TOC title formatting.
6. **Continuous Validation Inspector Drawer:**
   * Slide-out diagnostic panel displaying categorized issues: `BLOCKER`, `ERROR`, `WARNING`, and `INFO`.
   * Includes one-click navigation buttons that jump the active workspace focus directly to the violating slot.
7. **Interactive SUGAM Filing Co-Pilot:**
   * Step-by-step portal filing companion matching the exact tabs of the live CDSCO portal:
     - Tab 1: Application Form Details.
     - Tab 2: Regulatory Profile & Manufacturing Sites.
     - Tab 3: Device Master Details & Accessories.
     - Tab 4: Statutory Checklist Upload Slots (36 to 48 slots).
     - Tab 5: Fee Payment & TR6 Challan.
   * Provides single-click clipboard copying for formatted text values and verified download links for slot-specific PDF attachments.

---

## 4. Backend Internal Architecture and Processing Pipeline

The backend application is implemented in Python 3.11+ using the asynchronous FastAPI framework. It enforces a strict separation of concerns between HTTP handling, schema validation, domain business logic, document rendering, and persistence operations.

```text
========================================================================================================================
                                     BACKEND FASTAPI INTERNAL SERVICE ARCHITECTURE
========================================================================================================================

+----------------------------------------------------------------------------------------------------------------------+
| FASTAPI INGRESS & ROUTING LAYER                                                                                      |
|                                                                                                                      |
|  Routes:                                                                                                             |
|  - POST /api/v1/submissions                      (Initialize filing workspace & resolve 36-48 slots)                 |
|  - GET  /api/v1/submissions/{id}/workspace       (Fetch full slot tree, fulfillment status & validation counts)      |
|  - PATCH /api/v1/submissions/{id}/slots/{slot_id} (Update field values & toggle fulfillment mode)                     |
|  - POST /api/v1/submissions/{id}/slots/{id}/generate (Engine 1: Render Jinja2 / WeasyPrint statutory document)       |
|  - POST /api/v1/submissions/{id}/evidence/upload (Multi-part upload, SHA-256 computation, PyMuPDF inspection)        |
|  - POST /api/v1/submissions/{id}/evidence/link   (Link document to slot / DMF chapter)                               |
|  - POST /api/v1/submissions/{id}/dossiers/{type}/assemble (Engine 2: PyMuPDF stitching & pikepdf 10MB downsampling)   |
|  - GET  /api/v1/submissions/{id}/validation-report (Run multi-tier continuous validation audit)                      |
|  - GET  /api/v1/submissions/{id}/sugam-guide     (Generate tab-by-tab portal filing guide & clipboard payloads)      |
|  - POST /api/v1/submissions/{id}/export-handoff  (Build standardized numbered offline ZIP package)                   |
+----------------------------------------------------------------------------------------------------------------------+
                                      |
                                      v
+----------------------------------------------------------------------------------------------------------------------+
| SPECIALIZED DOMAIN SERVICE LAYER                                                                                     |
|                                                                                                                      |
|  +--------------------------------+  +--------------------------------+  +-----------------------------------------+ |
|  | Definition & Blueprint Service |  | Rules & Applicability Engine   |  | Document & Evidence Service             | |
|  | - Parses application schemas   |  | - Evaluates JSON-DSL rules     |  | - Manages local / S3 storage            | |
|  | - Maps 36-48 portal slots      |  | - Deactivates non-applicable   |  | - Computes cryptographic SHA-256 hashes | |
|  | - Sets mandatory requirements  |  | - Evaluates risk class rules   |  | - Extracts page count, size, text layer | |
|  +--------------------------------+  +--------------------------------+  +-----------------------------------------+ |
|                  |                                   |                                     |                         |
|  +--------------------------------+  +--------------------------------+  +-----------------------------------------+ |
|  | Continuous Validation Service  |  | SUGAM Handoff & ZIP Service    |  | Profiling & Signatory Service           | |
|  | - Validates mandatory slots    |  | - Formats portal tab values    |  | - Manages Authorized Indian Agent       | |
|  | - Checks document expiry       |  | - Generates numbered folders   |  | - Manages Foreign Manufacturer profiles | |
|  | - Flags missing DMF chapters   |  | - Streams offline ZIP archive  |  | - Manages Manufacturing Site addresses  | |
|  +--------------------------------+  +--------------------------------+  +-----------------------------------------+ |
+----------------------------------------------------------------------------------------------------------------------+
                                      |
                                      v
+----------------------------------------------------------------------------------------------------------------------+
| SPECIALIZED COMPILATION ENGINES (C-Native & Python Processing Pipelines)                                             |
|                                                                                                                      |
|  ENGINE 1: Guided Form Generator Pipeline             ENGINE 2: Master Dossier Assembly & 10MB Downsampler           |
|  +-------------------------------------------------+  +------------------------------------------------------------+ |
|  | Step 1: Ingest JSON questionnaire answers       |  | Step 1: Query ordered chapter documents (DMF / PMF)        | |
|  | Step 2: Inject into Jinja2 statutory template   |  | Step 2: Render dynamic Table of Contents (TOC) with links  | |
|  | Step 3: WeasyPrint compiles CSS & HTML to PDF   |  | Step 3: PyMuPDF (fitz) stitches chapters into master stream| |
|  | Step 4: Write to storage/.../generated/         |  | Step 4: PyMuPDF stamps continuous Bates numbers ("DMF-001")| |
|  | Step 5: Automatically link & satisfy slot       |  | Step 5: If > 10MB, pikepdf downsamples images to 150 DPI   | |
|  +-------------------------------------------------+  +------------------------------------------------------------+ |
+----------------------------------------------------------------------------------------------------------------------+
```

---

## 5. Persistence Layer: Database Schema and Storage Structure

The persistence layer combines structured relational models for identity, submissions, and document links with PostgreSQL `JSONB` columns for semi-structured portal slot values and regulatory context.

```text
========================================================================================================================
                                     DATABASE SCHEMA & ENTITY RELATIONSHIPS
========================================================================================================================

 [ APPLICATION_DEFINITIONS ]
   - id: UUID (PK)
   - code: VARCHAR(50) (e.g. 'MD-14', 'MD-7')
   - version: VARCHAR(50)
   - schema_payload: JSONB (Declarative 36-48 slot blueprints & applicability rules)
        |
        | 1:N
        v
 [ SUBMISSIONS ] <----------------------------------------+ [ PROFILES ]
   - id: UUID (PK)                                        |   - id: UUID (PK)
   - tracking_code: VARCHAR(100) (Unique)                 |   - profile_type: 'APPLICANT' | 'MANUFACTURER' | 'SITE'
   - filing_modality: 'FRESH' | 'ENDORSEMENT' | 'RETENTION' |   - name: VARCHAR(255)
   - device_category: 'MEDICAL_DEVICE' | 'IVD'            |   - data_payload: JSONB (Address, Signatory, Licenses)
   - risk_class: 'CLASS_A' | 'CLASS_B' | 'CLASS_C' | 'CLASS_D'
   - status: 'DRAFT' | 'IN_PREPARATION' | 'VALIDATION_BLOCKED' | 'SUBMISSION_READY'
   - regulatory_context: JSONB (Sterile, Predicate, Device details)
   - applicant_profile_id: UUID (FK) ---------------------+
   - manufacturer_profile_id: UUID (FK) ------------------+
   - site_profile_id: UUID (FK) --------------------------+
        |
        +-----------------------------------+-----------------------------------+
        | 1:N                               | 1:N                               | 1:N
        v                                   v                                   v
 [ SUBMISSION_ENTITIES ]             [ EVIDENCE_DOCUMENTS ]              [ VALIDATION_ISSUES ]
   - id: UUID (PK)                     - id: UUID (PK)                     - id: UUID (PK)
   - submission_id: UUID (FK)          - submission_id: UUID (FK)          - submission_id: UUID (FK)
   - slot_id: VARCHAR(50) (e.g. '10.1')- document_title: VARCHAR(255)      - severity: 'BLOCKER' | 'ERROR' |
   - slot_title: VARCHAR(255)          - original_filename: VARCHAR(255)               'WARNING' | 'INFO'
   - fulfillment_mode: 'UPLOAD'|'GEN'  - storage_path: VARCHAR(500)        - rule_code: VARCHAR(100)
   - status: 'NOT_APPLICABLE' |        - mime_type: VARCHAR(100)           - target_slot_id: VARCHAR(50)
             'MISSING' | 'IN_PROGRESS'|- file_size_bytes: BIGINT          - message: TEXT
             'SATISFIED' | 'INVALID'   - page_count: INTEGER               - fix_guidance: TEXT
   - form_values: JSONB                - extracted_metadata: JSONB
        |                                   |
        | 1:N                               | 1:N
        +-----------------+-----------------+
                          |
                          v
                   [ EVIDENCE_LINKS ]
                     - id: UUID (PK)
                     - submission_id: UUID (FK)
                     - submission_entity_id: UUID (FK)
                     - evidence_document_id: UUID (FK)
                     - dossier_chapter: VARCHAR(50) (e.g. 'DMF_6_2', 'PMF_5')
```

### Physical Binary Storage Directory Hierarchy

Uploaded documents, generated pro-formas, assembled master dossiers, and export archives are isolated by submission UUID on the physical storage tier:

```text
storage/
└── submissions/
    └── {submission_id}/
        ├── raw/
        │   ├── {evidence_id}_iso_13485_certificate.pdf
        │   ├── {evidence_id}_free_sale_certificate.pdf
        │   └── {evidence_id}_biocompatibility_report.pdf
        ├── generated/
        │   ├── {slot_id}_covering_letter_signed.pdf
        │   ├── {slot_id}_essential_principles_checklist.pdf
        │   └── {slot_id}_non_commercial_undertaking.pdf
        ├── assembled/
        │   ├── dmf_device_master_file_compiled.pdf
        │   ├── dmf_device_master_file_compiled_optimized.pdf
        │   ├── pmf_plant_master_file_compiled.pdf
        │   └── pmf_plant_master_file_compiled_optimized.pdf
        └── export/
            └── cdsco_md14_submission_package_{tracking_code}.zip
```

---

## 6. Component Interconnection Matrix and Data Contracts

The following matrix documents the exact technical link between each frontend UI component, its corresponding backend REST endpoint, the processing service invoked, and the persistence entity touched:

| Frontend UI Component | HTTP Route & Method | Backend Service | Database Table & Storage Action |
| :--- | :--- | :--- | :--- |
| **Setup Wizard** (`/submissions/new`) | `POST /api/v1/submissions` | `DefinitionService`, `RulesEngine` | Inserts into `submissions`; populates initial 36–48 records in `submission_entities`. |
| **Slot Navigator** (`SlotChecklistTree`) | `GET /api/v1/submissions/{id}/workspace` | `DefinitionService`, `ValService` | Queries `submissions`, `submission_entities`, and `validation_issues`. |
| **Workspace Controller** (`EntityDetailPane`) | `PATCH /api/v1/submissions/{id}/slots/{slot_id}` | `EntityController`, `RulesEngine` | Updates `form_values`, `fulfillment_mode`, and `status` in `submission_entities`. |
| **Dynamic Form Renderer** (`DynamicForm`) | `POST /api/v1/submissions/{id}/slots/{slot_id}/generate` | `GenEngine` (Engine 1: WeasyPrint) | Writes PDF to `storage/.../generated/`; creates record in `evidence_documents`; links in `evidence_links`; marks slot `SATISFIED`. |
| **File Dropzone** (`FileUploadDropzone`) | `POST /api/v1/submissions/{id}/evidence/upload` | `DocService` (SHA-256 & Fitz) | Writes file to `storage/.../raw/`; records metadata in `evidence_documents`. |
| **Evidence Linker** (`EvidenceLinkModal`) | `POST /api/v1/submissions/{id}/evidence/link` | `DocService`, `ValService` | Inserts into `evidence_links`; triggers continuous validation re-evaluation. |
| **PDF Viewer Modal** (`PdfPreviewModal`) | `GET /api/v1/evidence/{document_id}/stream` | `DocService` | Streams PDF binary chunk from `storage/` with byte-range support. |
| **Assembly Console** (`AssemblyCenter`) | `POST /api/v1/submissions/{id}/dossiers/{type}/assemble` | `AsmEngine` (Engine 2: Fitz & Pike) | Stitches PDFs, compresses to `storage/.../assembled/`; updates `evidence_links`; updates assembly status. |
| **Validation Drawer** (`ValidationDrawer`) | `GET /api/v1/submissions/{id}/validation-report` | `ValService` | Evaluates all active slots; updates records in `validation_issues`; returns categorized list. |
| **SUGAM Co-Pilot** (`SugamGuideModal`) | `GET /api/v1/submissions/{id}/sugam-guide` | `SugamService` | Reads verified slots and document paths; generates tab-by-tab portal filing guide. |
| **ZIP Exporter** (`ExportArchiveButton`) | `POST /api/v1/submissions/{id}/export-handoff` | `SugamService` | Zips all satisfied documents into structured folders in `storage/.../export/`; returns download link. |

---

## 7. Detailed End-to-End Operational Execution Flows

### Flow 1: Workspace Initialization and Slot Blueprint Resolution

This flow executes when a specialist creates a new submission. It transforms statutory rules into an interactive checklist containing 36 to 48 discrete slots.

```text
[ Specialist Configures Submission ]
                 |
                 | 1. Selects Form MD-14, Class C, Medical Device, Modality FRESH
                 v
[ Next.js Setup Wizard View ]
                 |
                 | 2. POST /api/v1/submissions { definition_code: "MD-14", context: {...} }
                 v
[ FastAPI Router & Pydantic Validation ]
                 |
                 | 3. Resolves Blueprint & Evaluates Statutory Predicates
                 v
[ Definition & Rules Engine ]
                 |
                 | 4. SELECT schema_payload FROM application_definitions WHERE code = 'MD-14'
                 | 5. Evaluates Class C constraints (Activates Fourth Schedule Part II DMF)
                 | 6. Batch Inserts Submission Record + 36 Initial Slot Entities
                 v
[ PostgreSQL Persistence Layer ]
                 |
                 | 7. Transaction Committed: Returns Submission ID & Full Slot Blueprint
                 v
[ Next.js Navigator & Checklist Tree ]
                 |
                 | 8. Renders 36-Slot Interactive Checklist with Guidance Badges
                 v
[ Specialist Begins Preparation ]
```

#### Detailed Execution Steps for Flow 1

| Step | Action | Initiator | Target | Technical Payload & Operation |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Select Pathway & Context | Specialist | Setup Wizard | Selects Form `MD-14`, Modality `FRESH`, Device Category `MEDICAL_DEVICE`, Risk Class `CLASS_C`, Sterility `STERILE`. |
| **2** | Submit Initialization | Setup Wizard | FastAPI Router | `POST /api/v1/submissions` with JSON context body. |
| **3** | Schema Resolution | Definition Service | PostgreSQL | `SELECT schema_payload FROM application_definitions WHERE code = 'MD-14' AND is_active = TRUE`. |
| **4** | Rule Evaluation | Rules Engine | In-Memory Engine | Evaluates predicate conditions: activates 36 statutory slots; flags Part II DMF (Slot 10.11) and PMF (Slot 10.12) as mandatory. |
| **5** | State Persistence | Rules Engine | PostgreSQL | `INSERT INTO submissions` (status `IN_PREPARATION`); batch `INSERT INTO submission_entities` (36 rows with status `MISSING`). |
| **6** | Workspace Delivery | FastAPI Router | Frontend Client | `201 Created` with full slot hierarchy, readiness score `0/36`, and initial blocker list. |
| **7** | UI Initialization | Frontend Client | Specialist | TanStack Query stores workspace cache; UI renders 36 slots with color-coded status badges. |

---

### Flow 2: Dual Fulfillment Route A - Binary Evidence Ingestion and Linking

This flow executes when a specialist fulfills a slot using an externally created document (e.g., ISO 13485 Certificate, Free Sale Certificate, or Biocompatibility Test Report).

```text
[ Specialist Drags & Drops "ISO_13485_Certificate.pdf" onto Slot 10.3 ]
                 |
                 | 1. Client verifies MIME type (application/pdf) & file size (< 100MB)
                 v
[ Next.js Multi-Part File Dropzone ]
                 |
                 | 2. POST /api/v1/submissions/{id}/evidence/upload (multipart/form-data)
                 v
[ FastAPI Router & Document Service ]
                 |
                 | 3. Computes cryptographic SHA-256 hash for document audit integrity
                 | 4. Writes binary stream to storage/submissions/{id}/raw/{uuid}.pdf
                 | 5. PyMuPDF inspects file: Extracts page count, text layer, dimensions
                 v
[ PostgreSQL Persistence Layer ]
                 |
                 | 6. INSERT INTO evidence_documents (filename, storage_path, page_count, sha256)
                 | 7. INSERT INTO evidence_links (evidence_document_id, submission_entity_id)
                 | 8. UPDATE submission_entities SET status = 'SATISFIED' WHERE slot_id = '10.3'
                 v
[ Continuous Validation Engine ]
                 |
                 | 9. Incremental evaluation: Clears MISSING blocker for Slot 10.3
                 v
[ Frontend Client Workspace ]
                 |
                 | 10. Slot 10.3 Badge transitions from Amber (MISSING) to Green (SATISFIED)
                 | 11. PDF.js viewer loads document preview immediately
                 v
[ Specialist Verifies Document Preview ]
```

#### Detailed Execution Steps for Flow 2

| Step | Action | Initiator | Target | Technical Payload & Operation |
| :--- | :--- | :--- | :--- | :--- |
| **1** | File Selection | Specialist | File Dropzone | Drags external certified PDF onto designated slot card (e.g. Slot 10.3 ISO 13485). |
| **2** | Stream Ingestion | File Dropzone | FastAPI Router | `POST /api/v1/submissions/{id}/evidence/upload` sending binary stream with slot identifier. |
| **3** | Integrity Check & Storage | Document Service | Storage Tier | Computes SHA-256 hash; writes binary to `storage/submissions/{id}/raw/{uuid}.pdf`. |
| **4** | PDF Inspection | Document Service | PyMuPDF | Reads PDF header and page objects: extracts exact page count, byte size, PDF standard version. |
| **5** | Link Creation | Document Service | PostgreSQL | Inserts into `evidence_documents` and `evidence_links`; updates slot status to `SATISFIED`. |
| **6** | Validation Clearance | Validation Service | PostgreSQL | Deletes blocker from `validation_issues`; recalculates overall readiness score. |
| **7** | Reactive UI Update | Frontend Client | Specialist | TanStack Query updates slot state; status badge changes to green; embedded PDF preview is enabled. |

---

### Flow 3: Dual Fulfillment Route B - In-App Guided Form Generation

This flow executes when a specialist selects Option B to generate a statutory document (such as a Covering Letter, Essential Principles Checklist, or Non-Commercial Undertaking) directly in the system.

```text
[ Specialist Selects "Generate via Guided Form" on Slot 1.0 (Covering Letter) ]
                 |
                 | 1. Dynamic Form Renderer displays guided inputs (Subject, Fees, Enclosures)
                 v
[ Next.js Dynamic Form View ]
                 |
                 | 2. Specialist fills statutory questionnaire & clicks "Generate Document"
                 | 3. POST /api/v1/submissions/{id}/slots/1.0/generate { template: "covering_letter", data: {...} }
                 v
[ FastAPI Router & Generator Service (Engine 1) ]
                 |
                 | 4. Saves answers into submission_entities.form_values (JSONB)
                 | 5. Jinja2 merges questionnaire values into official "covering_letter.html"
                 | 6. WeasyPrint compiles HTML and CSS into print-ready PDF binary
                 | 7. Writes compiled PDF to storage/submissions/{id}/generated/{uuid}.pdf
                 v
[ PostgreSQL Persistence Layer ]
                 |
                 | 8. INSERT INTO evidence_documents (title: "Covering Letter", storage_path, ...)
                 | 9. INSERT INTO evidence_links (document_id, entity_id, slot_id: '1.0')
                 | 10. UPDATE submission_entities SET status = 'SATISFIED', fulfillment_mode = 'GENERATE'
                 v
[ Frontend Client Workspace ]
                 |
                 | 11. Slot 1.0 Badge transitions to Green (SATISFIED)
                 | 12. PDF.js viewer immediately renders generated statutory Covering Letter
                 v
[ Specialist Reviews & Approves Generated Pro-Forma ]
```

#### Detailed Execution Steps for Flow 3

| Step | Action | Initiator | Target | Technical Payload & Operation |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Questionnaire Input | Specialist | Dynamic Form | Selects Option B; enters statutory values (Reference No, Payment Details, Signatory). |
| **2** | Generation Dispatch | Dynamic Form | FastAPI Router | `POST /api/v1/submissions/{id}/slots/{slot_id}/generate` with template key and questionnaire payload. |
| **3** | Answer Persistence | Generator Service | PostgreSQL | Updates `form_values` in `submission_entities` with JSONB payload. |
| **4** | Template Compilation | Generator Service | Jinja2 Engine | Injects field values into certified CDSCO pro-forma template (`covering_letter.html`). |
| **5** | PDF Compilation | Generator Service | WeasyPrint | Compiles HTML/CSS into statutory PDF with official legal margins and CDSCO header. |
| **6** | File Registration | Generator Service | Storage & DB | Saves PDF to `generated/`; inserts records into `evidence_documents` and `evidence_links`. |
| **7** | Preview Display | Frontend Client | Specialist | Slot status changes to `SATISFIED`; PDF.js renders document directly in viewport. |

---

### Flow 4: Master Dossier Assembly, Bates Stamping, and 10MB Downsampling

This flow executes when assembling modular chapters (Executive Summary, Device Description, Risk Management, Pre-Clinical Data, Clinical Evidence) into a single Device Master File (DMF) or Plant Master File (PMF).

```text
[ Specialist Clicks "Assemble Device Master File (DMF)" [Bates: "DMF-", Start: 1] ]
                 |
                 | 1. POST /api/v1/submissions/{id}/dossiers/DMF/assemble
                 v
[ FastAPI Router & Assembly Service (Engine 2) ]
                 |
                 | 2. Dispatches task to Background Worker; returns 202 Accepted { job_id }
                 v
[ Background Task Worker ]
                 |
                 | 3. SELECT * FROM evidence_links WHERE dossier_chapter LIKE 'DMF_%' ORDER BY order
                 | 4. Retrieves 14 individual chapter PDF files from storage tier
                 | 5. PyMuPDF renders dynamic Table of Contents (TOC) with clickable bookmarks
                 | 6. PyMuPDF stitches all 14 chapters into continuous master stream (348 Pages)
                 | 7. Stamps continuous Bates numbers ("DMF-0001" to "DMF-0348") at bottom center
                 | 8. Saves raw assembled PDF (Size: 28.4 MB)
                 v
[ 10MB Threshold Evaluation Loop ]
                 |
                 | 9. Evaluates: 28.4 MB > 10.0 MB CDSCO Portal Limit (Ceiling Exceeded)
                 | 10. pikepdf recompresses object streams & deflates internal tables
                 | 11. Downsamples embedded raster graphics to 150 DPI (sRGB color space)
                 | 12. Saves optimized PDF (Size: 7.8 MB <= 10.0 MB -> Threshold Passed)
                 v
[ PostgreSQL Persistence Layer ]
                 |
                 | 13. INSERT INTO evidence_documents (title: "Compiled DMF", size: 8178892)
                 | 14. UPDATE submission_entities SET status = 'SATISFIED' WHERE slot_id = '10.11'
                 | 15. UPDATE background_jobs SET status = 'COMPLETED', result_url = '...'
                 v
[ Frontend Assembly Console ]
                 |
                 | 16. Polling/SSE receives completion: Threshold Gauge shows Green (7.8 MB / 10 MB)
                 | 17. Enables 1-click download of compliant, Bates-stamped master dossier
                 v
[ Specialist Verifies Compiled Dossier ]
```

#### Detailed Execution Steps for Flow 4

| Step | Action | Initiator | Target | Technical Payload & Operation |
| :--- | :--- | :--- | :--- | :--- |
| **1** | Request Assembly | Specialist | Assembly Console | Selects dossier type (`DMF`), specifies Bates stamp configuration, clicks Assemble. |
| **2** | Job Dispatch | Assembly Console | FastAPI Router | `POST /api/v1/submissions/{id}/dossiers/DMF/assemble`; receives `202 Accepted` with job ID. |
| **3** | Chapter Query | Background Worker | PostgreSQL | Queries `evidence_links` to fetch verified chapter documents sorted in statutory sequence. |
| **4** | PDF Merging & TOC | Background Worker | PyMuPDF (`fitz`) | Compiles dynamic TOC with page bookmarks; stitches all chapter PDFs into a single document. |
| **5** | Bates Numbering | Background Worker | PyMuPDF (`fitz`) | Iterates across all pages; stamps sequential Bates identifiers at designated margin coordinates. |
| **6** | Size Evaluation | Background Worker | Engine 2 Logic | Checks compiled file size against the strict 10MB CDSCO upload limit. |
| **7** | Stream Downsampling | Background Worker | pikepdf / PIL | Recompresses internal streams; resamples embedded color images to 150 DPI to ensure size &le; 10MB. |
| **8** | Status Broadcast | Background Worker | Frontend Client | Registers dossier in database; updates job status; progress gauge displays passing size (7.8 MB). |

---

### Flow 5: Real-Time Pre-Submission Validation Loop

This flow ensures continuous, automated verification across statutory completeness, technical evidence coverage, document expiry, and portal file size rules.

```text
[ Trigger: Document Uploaded, Slot Updated, or Manual "Run Audit" Click ]
                 |
                 | 1. Evaluator retrieves active submission context, 36-48 slots, links, and documents
                 v
+----------------------------------------------------------------------------------------------------+
| CONTINUOUS MULTI-TIER VALIDATION AUDIT ENGINE                                                      |
|                                                                                                    |
|  TIER 1: Mandatory Completeness Checker                                                            |
|  - Queries submission_entities: Are all active mandatory slots marked SATISFIED?                   |
|                                                                                                    |
|  TIER 2: Document Expiry & Authenticity Checker                                                    |
|  - Inspects ISO 13485 & FSC certificates: Expiration date < Current Date? (Flags ERROR)            |
|  - Expiration date within 90 days? (Flags WARNING)                                                 |
|                                                                                                    |
|  TIER 3: Technical Fourth Schedule Coverage Checker                                                |
|  - Inspects Device Master File: Are all required chapters (6.1 to 6.8) present? (Flags BLOCKER)    |
|                                                                                                    |
|  TIER 4: CDSCO Portal 10MB Size Checker                                                            |
|  - Inspects all linked attachments: Does any individual file exceed 10.0 MB? (Flags BLOCKER)       |
|                                                                                                    |
|  TIER 5: Profiling & Statutory Cross-Reference Checker                                             |
|  - Validates Power of Attorney signatories against Indian Agent Profile (Flags ERROR)              |
+----------------------------------------------------------------------------------------------------+
                 |
                 | 2. Persists categorized issues in PostgreSQL (validation_issues table)
                 | 3. Computes global readiness metrics (e.g. 34 of 36 Slots Satisfied, 0 Blockers)
                 v
[ Global Submission Status Transition ]
                 |
                 | - If BLOCKER count > 0: status = 'VALIDATION_BLOCKED'
                 | - If BLOCKER count == 0 and 100% slots satisfied: status = 'SUBMISSION_READY'
                 v
[ Reactive Frontend Update ]
                 |
                 | 4. Validation Drawer updates issue cards with 1-click remediation buttons
                 | 5. Topbar readiness bar updates; "Open SUGAM Co-Pilot" button enables
                 v
[ Specialist Resolves Issues or Proceeds to Lodgment ]
```

#### Validation Issue Classification Hierarchy

| Severity Level | Enforcement Policy | System Behavior | Example Regulatory Trigger |
| :--- | :--- | :--- | :--- |
| **BLOCKER** | Hard Stop | Prevents dossier assembly and disables the live SUGAM filing guide. | Mandatory Slot 10.11 (DMF) is missing; or an attachment exceeds 10MB. |
| **ERROR** | Statutory Non-Compliance | Flags imminent CDSCO rejection risk; requires explicit specialist confirmation. | ISO 13485 Certificate has passed its validity expiration date. |
| **WARNING** | High-Risk Ambiguity | Highlights potential deficiency that could trigger a CDSCO inquiry query. | Free Sale Certificate expires within 60 days of planned submission. |
| **INFO** | Best-Practice Advisory | Informational guidance to optimize submission quality. | High-resolution test graphs detected; recommendation to run 150 DPI downsampling. |

---

### Flow 6: Live SUGAM Portal Co-Pilot and Offline ZIP Packaging

This flow bridges the prepared workspace with the live CDSCO online portal (`cdscomdonline.gov.in`).

```text
[ Specialist Opens "Interactive SUGAM Filing Co-Pilot" View ]
                 |
                 | 1. GET /api/v1/submissions/{id}/sugam-guide
                 v
[ FastAPI Router & SUGAM Service ]
                 |
                 | 2. Reads verified slots and document storage paths from database
                 | 3. Structures data to mirror the 5 official CDSCO portal tabs
                 v
[ Next.js Split-Screen Co-Pilot Interface ]
                 |
                 | Side-by-Side View: Co-Pilot Guide on Left | Live SUGAM Portal on Right
                 |
                 | Tab 1: Form Details      ---> Specialist clicks "Copy", pastes into portal
                 | Tab 2: Profile & Sites   ---> Specialist clicks "Copy", pastes into portal
                 | Tab 3: Device Details    ---> Specialist clicks "Copy", pastes into portal
                 | Tab 4: Checklist Uploads ---> Specialist clicks "Download Slot PDF"
                 |                               (Delivers pre-verified, optimized file &le; 10MB)
                 | Tab 5: Fee Payment       ---> Specialist copies TR6 Challan reference
                 v
[ Optional Offline Archival Package ]
                 |
                 | 4. Specialist clicks "Export Standard Offline ZIP Package"
                 | 5. POST /api/v1/submissions/{id}/export-handoff
                 v
[ SUGAM Packaging Service ]
                 |
                 | 6. Builds numbered directory tree (e.g. "01_Covering_Letter/", "10_11_DMF/")
                 | 7. Writes manifest.json and packages archive into storage/.../export/
                 v
[ Specialist Downloads Complete Verified Submission Archive ]
```

---

## 8. Lifecycle State Machines and Concurrency Control

### Regulatory Entity Slot State Machine

Tracks each of the 36 to 48 individual portal upload slots throughout the application lifecycle:

```text
                  +----------------------------------------------+
                  |               INITIAL STATE                  |
                  +----------------------------------------------+
                                  |              |
     Evaluated FALSE by Rules     |              | Evaluated TRUE by Rules
                                  v              v
               +--------------------+          +--------------------+
               |   NOT_APPLICABLE   |          |      MISSING       |
               +--------------------+          +--------------------+
                        |         ^              |            ^
  Predicate Deactivated |         | Context      | Partial    | Draft
                        |         | Activated    | Data Saved | Cleared
                        v         |              v            |
               +--------------------+          +--------------------+
               |      MISSING       |          |    IN_PROGRESS     |
               +--------------------+          +--------------------+
                                  |              |
                                  | Linked Valid | Upload / Generation
                                  | Document     | Complete
                                  v              v
                              +--------------------+
                              |     SATISFIED      |<-----------------+
                              +--------------------+                  |
                               |        |        ^                    |
             Certificate Expired|        | Linked | Remediation       | Change
             or Validation Error|        | File   | Completed         | Confirmed
                               v        | Changed|                    |
                        +-----------+   v        +--------------------+
                        |  INVALID  |   |        |    NEEDS_REVIEW    |
                        +-----------+   +------->+--------------------+
```

### Global Submission Dossier State Machine

Tracks the top-level submission master record across authoring, validation, and live filing:

```text
       +--------------------------------------------------------------+
       |                           DRAFT                              |
       +--------------------------------------------------------------+
                                      |
                                      | Regulatory Context Initialized
                                      v
       +--------------------------------------------------------------+
       |                       IN_PREPARATION                         |<---+
       +--------------------------------------------------------------+    |
                |                                            ^             |
                | Blocker or Error                           | Issues      | Specialist
                | Detected                                   | Remediated  | Reopens
                v                                            |             |
       +--------------------------------------------------------------+    |
       |                     VALIDATION_BLOCKED                       |    |
       +--------------------------------------------------------------+    |
                                                                           |
                | 100% Mandatory Slots SATISFIED                           |
                | Zero BLOCKER Diagnostics                                 |
                v                                                          |
       +--------------------------------------------------------------+    |
       |                      SUBMISSION_READY                        |----+
       +--------------------------------------------------------------+
                                      |
                                      | Specialist Launches SUGAM Co-Pilot
                                      v
       +--------------------------------------------------------------+
       |                         GUIDE_ACTIVE                         |
       +--------------------------------------------------------------+
                                      |
                                      | Lodged on CDSCO Portal with Reference No
                                      v
       +--------------------------------------------------------------+
       |                       SUBMISSION_FILED                       |
       +--------------------------------------------------------------+
```

### Dossier Assembly Job State Machine

Manages asynchronous PDF compilation, Bates numbering, and pikepdf downsampling operations:

```text
       +--------------------------------------------------------------+
       |                           QUEUED                             |<---+
       +--------------------------------------------------------------+    |
                                      |                                    |
                                      | Worker Dequeues Task               |
                                      v                                    |
       +--------------------------------------------------------------+    | Retry
       |                         PROCESSING                           |    | After
       |  (Stitching Chapters, Injecting TOC, Stamping Bates Numbers) |    | Fixing
       +--------------------------------------------------------------+    | Corrupt
                |                                            |             | File
                | Processing Error                           | Size > 10MB |
                | (Corrupt Source PDF)                       |             |
                v                                            v             |
       +------------------+                   +-----------------------+    |
       |      FAILED      |                   |       OPTIMIZING      |----+
       +------------------+                   | (pikepdf 150 DPI Down)|
                ^                             +-----------------------+
                |                                    |
                | Cannot Compress &le; 10MB          | Size &le; 10.0 MB
                +------------------------------------+
                                                     |
                                                     v
                                      +-------------------------------+
                                      |             READY             |
                                      | (Compliant Compiled Dossier)  |
                                      +-------------------------------+
```

---

## 9. Data Protection, Concurrency, and Memory Safety

1. **Database Transaction Isolation and Concurrency:**
   * PostgreSQL transactions are executed at the `READ COMMITTED` isolation level to prevent dirty reads.
   * Optimistic locking via updated timestamp checks prevents race conditions when multiple regulatory specialists edit different slots simultaneously.
   * Foreign keys utilize `ON DELETE CASCADE` on child entities (`submission_entities`, `evidence_links`, `validation_issues`) to prevent orphaned records upon submission deletion.
2. **Memory-Safe PDF Stream Processing:**
   * Large PDF files are processed as streams rather than buffered entirely in RAM.
   * PyMuPDF (`fitz`) handles document merging at native C-speeds with minimal memory footprint.
   * pikepdf processes PDF page streams sequentially, avoiding Out-Of-Memory (OOM) conditions even when stitching multi-hundred-page technical dossiers.
3. **Audit Trails and Document Integrity:**
   * Every ingested evidence document is assigned an immutable SHA-256 cryptographic hash at upload time.
   * Any change to an underlying document triggers automatic invalidation and recalculation of related `evidence_links` and validation diagnostics.
4. **Transport and Access Security:**
   * All network communication between the frontend client and FastAPI gateway is encrypted via TLS 1.3.
   * Role-Based Access Control (RBAC) separates authoring privileges from final QA sign-off and filing authority.

---

## 10. Cross-Reference Index

* For statutory definitions, CDSCO portal upload slot mappings, and Fourth Schedule DMF/PMF hierarchies, refer to [05_REGULATORY_FORMS_AND_DOSSIER_MATRIX.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/05_REGULATORY_FORMS_AND_DOSSIER_MATRIX.md).
* For complete PostgreSQL DDL schemas, Pydantic data models, and the 5-module implementation Work Breakdown Structure (WBS), refer to [04_ENGINEERING_AND_DATA_MODEL_SPEC.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/04_ENGINEERING_AND_DATA_MODEL_SPEC.md).
* For detailed logic governing the 35 statutory documents and guided form generation engines, refer to [05_DOCUMENT_ENGINES_AND_FULFILLMENT_LOGIC.md](file:///c:/Users/Sam/Documents/MyData/Projects/CDSCO_new/docs/technical_reference/05_DOCUMENT_ENGINES_AND_FULFILLMENT_LOGIC.md).
