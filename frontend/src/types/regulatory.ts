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

export interface SlotGuidance {
  what_it_is?: string;
  why_it_is_needed?: string;
  official_citation?: string;
  who_issues?: string;
  validity_period?: string;
  target_sugam_location?: string;
  mandatory_inclusions?: string[];
  critical_pitfalls?: string[];
  pro_forma_available?: boolean;
}

export interface EvidenceLink {
  id: string;
  submission_id: string;
  evidence_document_id: string;
  submission_entity_id: string;
  dossier_chapter?: string;
  created_at: string;
  document_title?: string;
  original_filename?: string;
  file_size_bytes?: number;
  page_count?: number;
  extracted_metadata?: ExtractedMetadata;
  evidence_document?: EvidenceDocument;
}

export interface SubmissionEntity {
  id: string;
  submission_id: string;
  slot_id: string;
  slot_title: string;
  fulfillment_mode: FulfillmentMode;
  status: SlotStatus;
  category?: string;
  chapter?: string;
  is_mandatory?: boolean;
  guidance?: SlotGuidance;
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
  portal_fields?: CDSCOApplicationFields;
  [key: string]: unknown;
}

export interface ModelVariant {
  model_number: string;
  model_name: string;
  dimension_spec: string;
  pack_size: string;
  accessories_included?: string;
}

export interface CDSCOApplicationFields {
  // Application & Treasury
  filing_modality?: string;
  bharatkosh_challan_no?: string;
  payment_date?: string;
  fee_amount_inr?: number;
  bank_reference_no?: string;

  // Legal Representation (Import MD-14)
  indian_agent_name?: string;
  wholesale_licence_no?: string;
  wholesale_licence_validity?: string;
  poa_execution_date?: string;
  foreign_mfr_name?: string;
  foreign_mfr_country?: string;
  foreign_site_address?: string;

  // Domestic Premises (MD-7 & MD-3)
  domestic_mfr_name?: string;
  mfg_premises_address?: string;
  cleanroom_area_sqm?: number;
  production_incharge_name?: string;
  qa_incharge_name?: string;
  inhouse_lab_available?: boolean;

  // Core Device Identity
  generic_name?: string;
  brand_name?: string;
  intended_use?: string;
  intended_patient_population?: string;
  anatomical_site?: string;
  material_of_construction?: string;
  shelf_life_months?: number;
  storage_temperature_min?: number;
  storage_temperature_max?: number;
  storage_conditions_text?: string;
  is_single_use?: boolean;
  reuse_cycles_max?: number;

  // Model Variant Matrix
  model_variants?: ModelVariant[];

  // Technology Predicates (Conditional)
  is_sterile?: boolean;
  sterilization_method?: string;
  sterility_assurance_level?: string;
  sterilization_facility_address?: string;
  packaging_barrier_system?: string;

  contains_software?: boolean;
  software_version?: string;
  software_safety_class?: string;
  target_operating_system?: string;
  cloud_hosted?: boolean;
  cybersecurity_standard_applied?: string;

  contains_medicinal_substance?: boolean;
  drug_inn_name?: string;
  drug_pharmacopoeial_grade?: string;
  drug_quantity_per_device?: string;
  drug_intended_action?: string;
  drug_source_manufacturer?: string;

  contains_animal_tissue?: boolean;
  animal_species?: string;
  tissue_type_harvested?: string;
  tse_bse_risk_category?: string;
  geographical_origin_country?: string;
  viral_inactivation_method?: string;

  // Modality Predicate: IVD
  target_analyte?: string;
  ivd_test_principle?: string;
  specimen_matrix?: string[];
  calibrator_traceability?: string;
  open_vial_stability_days?: number;
  compatible_instruments?: string;
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
