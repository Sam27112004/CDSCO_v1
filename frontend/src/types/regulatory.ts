/**
 * Regulatory domain models and statutory data structures
 * for CDSCO Medical Device Rules, 2017 (MDR 2017).
 */

export type FilingModality =
  | "FRESH"
  | "RENEWAL"
  | "POST_APPROVAL_CHANGE"
  | "ENDORSEMENT";

export type DeviceCategory = "MEDICAL_DEVICE" | "IVD";

export type RiskClass = "CLASS_A" | "CLASS_B" | "CLASS_C" | "CLASS_D";

export type SubmissionStatus =
  | "DRAFT"
  | "IN_REVIEW"
  | "SUBMISSION_READY"
  | "SUBMITTED"
  | "APPROVED"
  | "QUERIED"
  | "REJECTED";

export type FulfillmentMode = "UPLOAD" | "GENERATE" | "PROFILE_INHERIT";

export type SlotStatus = "EMPTY" | "IN_PROGRESS" | "SATISFIED" | "FLAGGED";

export type IssueSeverity = "BLOCKER" | "ERROR" | "WARNING" | "INFO";

export interface PageDimension {
  page_number: number;
  width: number;
  height: number;
  is_portrait: boolean;
}

export interface ExtractedMetadata {
  sha256?: string;
  pdf_version?: string;
  is_encrypted?: boolean;
  title?: string;
  author?: string;
  creator?: string;
  producer?: string;
  creation_date?: string;
  modification_date?: string;
  converted?: boolean;
  source_format?: string;
  page_dimensions?: PageDimension[];
  [key: string]: unknown;
}

export interface EvidenceDocument {
  id: string;
  submission_id: string;
  document_title: string;
  original_filename: string;
  storage_path: string;
  mime_type: string;
  file_size_bytes: number;
  page_count: number;
  extracted_metadata: ExtractedMetadata;
  uploaded_at: string;
}

export interface EvidenceLink {
  id: string;
  submission_id: string;
  evidence_document_id: string;
  submission_entity_id: string;
  dossier_chapter?: string;
  created_at: string;
  evidence_document?: EvidenceDocument;
}

export interface SubmissionEntity {
  id: string;
  submission_id: string;
  slot_id: string;
  slot_title: string;
  fulfillment_mode: FulfillmentMode;
  status: SlotStatus;
  form_values?: Record<string, unknown>;
  updated_at: string;
  evidence_links?: EvidenceLink[];
}

export interface RegulatoryContext {
  is_sterile?: boolean;
  is_measuring?: boolean;
  contains_software?: boolean;
  contains_medicinal_substance?: boolean;
  contains_animal_tissue?: boolean;
  [key: string]: unknown;
}

export interface Submission {
  id: string;
  application_definition_id: string;
  tracking_code: string;
  filing_modality: FilingModality;
  device_category: DeviceCategory;
  risk_class: RiskClass;
  status: SubmissionStatus;
  regulatory_context: RegulatoryContext;
  applicant_profile_id?: string;
  manufacturer_profile_id?: string;
  site_profile_id?: string;
  created_at: string;
  updated_at: string;
  entities?: SubmissionEntity[];
  evidence_documents?: EvidenceDocument[];
}

export interface ApplicationDefinition {
  id: string;
  pathway_code: string;
  title: string;
  version: string;
  description?: string;
  target_authority: string;
  legal_reference: string;
  is_active: boolean;
}

export interface ValidationIssue {
  id: string;
  submission_id: string;
  severity: IssueSeverity;
  rule_code: string;
  target_slot_id?: string;
  message: string;
  fix_guidance?: string;
  created_at: string;
}

export interface HealthResponse {
  status: "healthy" | "degraded";
  version: string;
  project_name: string;
  environment: string;
  database_connected: boolean;
}
