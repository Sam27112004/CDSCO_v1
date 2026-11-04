"use client";

import React, { useState } from "react";
import {
  FileText,
  Save,
  CheckCircle2,
  AlertCircle,
  Plus,
  Trash2,
  ExternalLink,
  Sparkles,
  Loader2,
  Building,
  Cpu,
  Layers,
  FlaskConical,
  Activity,
} from "lucide-react";
import {
  Submission,
  DeviceCategory,
  CDSCOApplicationFields,
  ModelVariant,
} from "@/types/regulatory";
import { useUpdateSubmission } from "@/hooks/useSubmissions";

interface PortalFieldsTabProps {
  submission: Submission;
  pathwayCode: string;
  deviceCategory: DeviceCategory;
  onNavigateToSlot?: (slotId: string) => void;
}

export function PortalFieldsTab({
  submission,
  pathwayCode,
  deviceCategory,
  onNavigateToSlot,
}: PortalFieldsTabProps) {
  const updateMutation = useUpdateSubmission();
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);

  // Initialize fields from regulatory_context.portal_fields or fallback
  const initialPortalFields: CDSCOApplicationFields =
    (submission.regulatory_context?.portal_fields as CDSCOApplicationFields) || {};

  const [formData, setFormData] = useState<CDSCOApplicationFields>({
    // Application & Treasury
    filing_modality:
      initialPortalFields.filing_modality || submission.filing_modality || "FRESH",
    bharatkosh_challan_no: initialPortalFields.bharatkosh_challan_no || "",
    payment_date: initialPortalFields.payment_date || "",
    fee_amount_inr: initialPortalFields.fee_amount_inr || 0,
    bank_reference_no: initialPortalFields.bank_reference_no || "",

    // Legal Representation (MD-14 Import)
    indian_agent_name: initialPortalFields.indian_agent_name || "",
    wholesale_licence_no: initialPortalFields.wholesale_licence_no || "",
    wholesale_licence_validity: initialPortalFields.wholesale_licence_validity || "",
    poa_execution_date: initialPortalFields.poa_execution_date || "",
    foreign_mfr_name: initialPortalFields.foreign_mfr_name || "",
    foreign_mfr_country: initialPortalFields.foreign_mfr_country || "USA",
    foreign_site_address: initialPortalFields.foreign_site_address || "",

    // Domestic Premises (MD-7 & MD-3)
    domestic_mfr_name: initialPortalFields.domestic_mfr_name || "",
    mfg_premises_address: initialPortalFields.mfg_premises_address || "",
    cleanroom_area_sqm: initialPortalFields.cleanroom_area_sqm || 0,
    production_incharge_name: initialPortalFields.production_incharge_name || "",
    qa_incharge_name: initialPortalFields.qa_incharge_name || "",
    inhouse_lab_available: initialPortalFields.inhouse_lab_available ?? true,

    // Core Device Identity
    generic_name:
      initialPortalFields.generic_name ||
      (submission.regulatory_context?.device_family_name as string) ||
      "",
    brand_name: initialPortalFields.brand_name || "",
    intended_use: initialPortalFields.intended_use || "",
    intended_patient_population:
      initialPortalFields.intended_patient_population || "Adult patients",
    anatomical_site: initialPortalFields.anatomical_site || "",
    material_of_construction: initialPortalFields.material_of_construction || "",
    shelf_life_months: initialPortalFields.shelf_life_months || 36,
    storage_temperature_min: initialPortalFields.storage_temperature_min || 15,
    storage_temperature_max: initialPortalFields.storage_temperature_max || 30,
    storage_conditions_text:
      initialPortalFields.storage_conditions_text || "Store in cool, dry place. Protect from moisture.",
    is_single_use: initialPortalFields.is_single_use ?? true,
    reuse_cycles_max: initialPortalFields.reuse_cycles_max || 0,

    // Model Variant Matrix
    model_variants:
      initialPortalFields.model_variants && initialPortalFields.model_variants.length > 0
        ? initialPortalFields.model_variants
        : [
            {
              model_number: "MD-01-A",
              model_name: "Standard Model",
              dimension_spec: "10mm x 150mm",
              pack_size: "1 Unit per Box",
              accessories_included: "None",
            },
          ],

    // Technology Predicates
    is_sterile:
      initialPortalFields.is_sterile ??
      Boolean(submission.regulatory_context?.is_sterile),
    sterilization_method:
      initialPortalFields.sterilization_method || "ETHYLENE_OXIDE",
    sterility_assurance_level:
      initialPortalFields.sterility_assurance_level || "10^-6",
    sterilization_facility_address:
      initialPortalFields.sterilization_facility_address || "",
    packaging_barrier_system:
      initialPortalFields.packaging_barrier_system || "Tyvek Pouch with Heat-Sealed Polyethylene Barrier",

    contains_software:
      initialPortalFields.contains_software ??
      Boolean(submission.regulatory_context?.contains_software),
    software_version: initialPortalFields.software_version || "v1.0.0",
    software_safety_class:
      initialPortalFields.software_safety_class || "CLASS_B",
    target_operating_system:
      initialPortalFields.target_operating_system || "Embedded Microcontroller / Windows 11",
    cloud_hosted: initialPortalFields.cloud_hosted ?? false,
    cybersecurity_standard_applied:
      initialPortalFields.cybersecurity_standard_applied || "IEC 81001-5-1 / UL 2900",

    contains_medicinal_substance:
      initialPortalFields.contains_medicinal_substance ??
      Boolean(submission.regulatory_context?.contains_medicinal_substance),
    drug_inn_name: initialPortalFields.drug_inn_name || "",
    drug_pharmacopoeial_grade:
      initialPortalFields.drug_pharmacopoeial_grade || "IP",
    drug_quantity_per_device:
      initialPortalFields.drug_quantity_per_device || "",
    drug_intended_action: initialPortalFields.drug_intended_action || "",
    drug_source_manufacturer:
      initialPortalFields.drug_source_manufacturer || "",

    contains_animal_tissue:
      initialPortalFields.contains_animal_tissue ??
      Boolean(submission.regulatory_context?.contains_animal_tissue),
    animal_species: initialPortalFields.animal_species || "BOVINE",
    tissue_type_harvested: initialPortalFields.tissue_type_harvested || "",
    tse_bse_risk_category:
      initialPortalFields.tse_bse_risk_category || "CATEGORY_C_NO_DETECTABLE_INFECTIVITY",
    geographical_origin_country:
      initialPortalFields.geographical_origin_country || "Australia",
    viral_inactivation_method:
      initialPortalFields.viral_inactivation_method || "",

    // IVD Specifics
    target_analyte: initialPortalFields.target_analyte || "",
    ivd_test_principle:
      initialPortalFields.ivd_test_principle || "RAPID_LATERAL_FLOW",
    specimen_matrix: initialPortalFields.specimen_matrix || ["SERUM", "PLASMA"],
    calibrator_traceability: initialPortalFields.calibrator_traceability || "",
    open_vial_stability_days: initialPortalFields.open_vial_stability_days || 30,
    compatible_instruments: initialPortalFields.compatible_instruments || "",
  });

  const isImport = pathwayCode === "MD-14";
  const isIVD = deviceCategory === "IVD";

  // Form field change handler
  const handleFieldChange = (key: keyof CDSCOApplicationFields, value: unknown) => {
    setFormData((prev) => ({
      ...prev,
      [key]: value,
    }));
    setSaveSuccess(false);
    setSaveError(null);
  };

  // Model Matrix Handlers
  const handleAddVariant = () => {
    const newVariant: ModelVariant = {
      model_number: `MOD-${(formData.model_variants?.length || 0) + 1}`,
      model_name: "Variant",
      dimension_spec: "",
      pack_size: "1 Unit",
      accessories_included: "",
    };
    setFormData((prev) => ({
      ...prev,
      model_variants: [...(prev.model_variants || []), newVariant],
    }));
  };

  const handleRemoveVariant = (index: number) => {
    setFormData((prev) => ({
      ...prev,
      model_variants: (prev.model_variants || []).filter((_, i) => i !== index),
    }));
  };

  const handleVariantChange = (
    index: number,
    field: keyof ModelVariant,
    value: string
  ) => {
    const updated = [...(formData.model_variants || [])];
    updated[index] = { ...updated[index], [field]: value };
    setFormData((prev) => ({
      ...prev,
      model_variants: updated,
    }));
  };

  // Submit handler
  const handleSaveAllFields = async () => {
    try {
      setSaveError(null);
      await updateMutation.mutateAsync({
        id: submission.id,
        device_family_name: formData.brand_name || formData.generic_name,
        regulatory_context: {
          is_sterile: formData.is_sterile,
          contains_software: formData.contains_software,
          contains_medicinal_substance: formData.contains_medicinal_substance,
          contains_animal_tissue: formData.contains_animal_tissue,
          portal_fields: formData,
        },
      });
      setSaveSuccess(true);
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Failed to save portal fields";
      setSaveError(msg);
    }
  };

  return (
    <div className="space-y-8 pb-16">
      {/* Top Banner / Actions */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 rounded-xl border border-blue-200 bg-white p-5 shadow-xs">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-600">
            <Sparkles className="h-4 w-4" />
            <span>CDSCO Online Portal Web-Form Fields</span>
          </div>
          <h2 className="text-lg font-bold text-slate-900 mt-1">
            Application Particulars & Statutory Specifications
          </h2>
          <p className="text-xs text-slate-500 mt-0.5">
            These structured data inputs map directly to the textboxes on the CDSCO MD-Online / SUGAM portal.
            Each field group connects to an official document slot in your checklist.
          </p>
        </div>

        <div className="flex items-center gap-3 shrink-0">
          {saveSuccess && (
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-emerald-600">
              <CheckCircle2 className="h-4 w-4" />
              Fields Saved
            </span>
          )}
          {saveError && (
            <span className="inline-flex items-center gap-1.5 text-xs font-semibold text-red-600">
              <AlertCircle className="h-4 w-4" />
              {saveError}
            </span>
          )}
          <button
            type="button"
            onClick={handleSaveAllFields}
            disabled={updateMutation.isPending}
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-xs font-bold text-white shadow-xs hover:bg-blue-700 disabled:opacity-60 transition-colors"
          >
            {updateMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Saving to Database...</span>
              </>
            ) : (
              <>
                <Save className="h-4 w-4" />
                <span>Save Application Fields</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* SECTION 1: APPLICATION PARTICULARS & BHARATKOSH TREASURY */}
      <section className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="border-b border-slate-100 bg-slate-50/70 px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <FileText className="h-4 w-4 text-blue-600" />
              Section 1: Application Particulars & Treasury Verification
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Government fee payment verification through NTRP Bharatkosh portal.
            </p>
          </div>

          {/* Connected Statutory Requirement Card */}
          <div className="flex items-center gap-2 rounded-lg border border-blue-200 bg-blue-50/80 px-3 py-1.5 text-xs">
            <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1.5 py-0.5 rounded">
              Slot 2.0
            </span>
            <span className="text-blue-900 font-medium">Fee Challan (Second Schedule)</span>
            {onNavigateToSlot && (
              <button
                type="button"
                onClick={() => onNavigateToSlot("2.0")}
                className="text-blue-600 hover:text-blue-800 ml-1 inline-flex items-center gap-0.5 font-semibold text-[11px]"
                title="View Connected Document Slot"
              >
                <span>View Slot</span>
                <ExternalLink className="h-3 w-3" />
              </button>
            )}
          </div>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Filing Modality <span className="text-red-500">*</span>
            </label>
            <select
              value={formData.filing_modality}
              onChange={(e) => handleFieldChange("filing_modality", e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            >
              <option value="FRESH">Fresh Application</option>
              <option value="ENDORSEMENT">Endorsement / Model Addition</option>
              <option value="RETENTION">Retention / Licence Renewal</option>
              <option value="POST_APPROVAL_CHANGE">Post-Approval Change</option>
            </select>
            <p className="text-[11px] text-slate-400 mt-1">Must match Covering Letter pro-forma.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Bharatkosh Challan Number <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.bharatkosh_challan_no || ""}
              onChange={(e) => handleFieldChange("bharatkosh_challan_no", e.target.value)}
              placeholder="e.g. 0411260001234"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
            />
            <p className="text-[11px] text-slate-400 mt-1">NTRP transaction ID printed on receipt.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Payment Date <span className="text-red-500">*</span>
            </label>
            <input
              type="date"
              value={formData.payment_date || ""}
              onChange={(e) => handleFieldChange("payment_date", e.target.value)}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Date funds debited via Bharatkosh.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Statutory Fee Amount (INR) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={formData.fee_amount_inr || 0}
              onChange={(e) => handleFieldChange("fee_amount_inr", Number(e.target.value))}
              placeholder="e.g. 150000"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Statutory fee per Second Schedule.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Bank Reference / UTR Number <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.bank_reference_no || ""}
              onChange={(e) => handleFieldChange("bank_reference_no", e.target.value)}
              placeholder="e.g. SBIN00012345678"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
            />
            <p className="text-[11px] text-slate-400 mt-1">Bank gateway confirmation reference.</p>
          </div>
        </div>
      </section>

      {/* SECTION 2: LEGAL ENTITY & MANUFACTURING SITE DETAILS */}
      <section className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="border-b border-slate-100 bg-slate-50/70 px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Building className="h-4 w-4 text-blue-600" />
              Section 2: Legal Entity & Manufacturing Site Details
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              {isImport
                ? "Authorized Indian Agent and Foreign Manufacturer particulars under Rule 34."
                : "Domestic manufacturing site and approved technical staff under Rule 20 & 26."}
            </p>
          </div>

          {/* Connected Statutory Cards */}
          <div className="flex flex-wrap items-center gap-2">
            {isImport ? (
              <>
                <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-xs">
                  <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1 rounded">Slot 4.0</span>
                  <span className="text-blue-900 font-medium text-[11px]">Power of Attorney</span>
                </div>
                <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-xs">
                  <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1 rounded">Slot 5.0</span>
                  <span className="text-blue-900 font-medium text-[11px]">Wholesale Licence</span>
                </div>
                <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-xs">
                  <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1 rounded">Slot 9.0</span>
                  <span className="text-blue-900 font-medium text-[11px]">ISO 13485 QMS</span>
                </div>
              </>
            ) : (
              <>
                <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-xs">
                  <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1 rounded">Slot 6.2</span>
                  <span className="text-blue-900 font-medium text-[11px]">Personnel Organogram</span>
                </div>
                <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-xs">
                  <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1 rounded">Slot 6.4</span>
                  <span className="text-blue-900 font-medium text-[11px]">Premises Layout</span>
                </div>
              </>
            )}
          </div>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 text-xs">
          {isImport ? (
            <>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Authorized Indian Agent Legal Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.indian_agent_name || ""}
                  onChange={(e) => handleFieldChange("indian_agent_name", e.target.value)}
                  placeholder="e.g. Apex Healthcare Private Limited"
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Must match Form 20B/21B wholesale licence.</p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Wholesale Drug Licence Number <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.wholesale_licence_no || ""}
                  onChange={(e) => handleFieldChange("wholesale_licence_no", e.target.value)}
                  placeholder="e.g. MH-MZ2-123456 / Form 20B"
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                />
                <p className="text-[11px] text-slate-400 mt-1">Form 20B, 21B, or MD-42 registration.</p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Licence Validity / Retention Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={formData.wholesale_licence_validity || ""}
                  onChange={(e) => handleFieldChange("wholesale_licence_validity", e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Must be active for $\ge 6$ months.</p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Power of Attorney Execution Date <span className="text-red-500">*</span>
                </label>
                <input
                  type="date"
                  value={formData.poa_execution_date || ""}
                  onChange={(e) => handleFieldChange("poa_execution_date", e.target.value)}
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Notarized & apostilled execution date.</p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Legal Foreign Manufacturer Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.foreign_mfr_name || ""}
                  onChange={(e) => handleFieldChange("foreign_mfr_name", e.target.value)}
                  placeholder="e.g. Medtronic Inc. / Boston Scientific Corp."
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Must match Free Sale Certificate & ISO 13485.</p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Country of Legal Manufacturer <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.foreign_mfr_country || ""}
                  onChange={(e) => handleFieldChange("foreign_mfr_country", e.target.value)}
                  placeholder="e.g. United States, Germany, Japan"
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Issuing country of Origin FSC.</p>
              </div>

              <div className="md:col-span-2 lg:col-span-3">
                <label className="block font-semibold text-slate-700 mb-1">
                  Actual Manufacturing Site Physical Address <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={2}
                  value={formData.foreign_site_address || ""}
                  onChange={(e) => handleFieldChange("foreign_site_address", e.target.value)}
                  placeholder="Full street address, city, state, postal code, and country of the factory where device is manufactured."
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Must match ISO 13485 certificate scope address verbatim.</p>
              </div>
            </>
          ) : (
            <>
              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Domestic Manufacturing Entity Name <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.domestic_mfr_name || ""}
                  onChange={(e) => handleFieldChange("domestic_mfr_name", e.target.value)}
                  placeholder="e.g. Hindustan Meditech Devices Ltd."
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Registered domestic corporate entity.</p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Total Certified Cleanroom Area (sq m) <span className="text-red-500">*</span>
                </label>
                <input
                  type="number"
                  value={formData.cleanroom_area_sqm || 0}
                  onChange={(e) => handleFieldChange("cleanroom_area_sqm", Number(e.target.value))}
                  placeholder="e.g. 250"
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">ISO Class 7 / Class 8 validated area.</p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Production In-Charge (Rule 26) <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.production_incharge_name || ""}
                  onChange={(e) => handleFieldChange("production_incharge_name", e.target.value)}
                  placeholder="e.g. Dr. Rajesh Sharma, B.Pharm, 8 yrs exp"
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Approved qualified production personnel.</p>
              </div>

              <div>
                <label className="block font-semibold text-slate-700 mb-1">
                  Quality Assurance In-Charge (Rule 26) <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  value={formData.qa_incharge_name || ""}
                  onChange={(e) => handleFieldChange("qa_incharge_name", e.target.value)}
                  placeholder="e.g. Anjali Nair, M.Sc Microbiology"
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Independent QA head per MDR 2017.</p>
              </div>

              <div className="md:col-span-2">
                <label className="block font-semibold text-slate-700 mb-1">
                  Manufacturing Facility Physical Address <span className="text-red-500">*</span>
                </label>
                <textarea
                  rows={2}
                  value={formData.mfg_premises_address || ""}
                  onChange={(e) => handleFieldChange("mfg_premises_address", e.target.value)}
                  placeholder="Plot number, industrial estate, city, district, state, pin code."
                  className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                />
                <p className="text-[11px] text-slate-400 mt-1">Must match registered industrial land lease.</p>
              </div>
            </>
          )}
        </div>
      </section>

      {/* SECTION 3: CORE DEVICE IDENTITY & SPECIFICATIONS */}
      <section className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="border-b border-slate-100 bg-slate-50/70 px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Layers className="h-4 w-4 text-blue-600" />
              Section 3: Core Device Identity & Physical Specifications
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Statutory clinical indications, patient contact materials, shelf life, and storage requirements.
            </p>
          </div>

          {/* Connected Statutory Cards */}
          <div className="flex flex-wrap items-center gap-2">
            <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-xs">
              <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1 rounded">Slot 1.0</span>
              <span className="text-blue-900 font-medium text-[11px]">Covering Letter</span>
            </div>
            <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-xs">
              <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1 rounded">Slot 10.1</span>
              <span className="text-blue-900 font-medium text-[11px]">Executive Summary</span>
            </div>
            <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-xs">
              <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1 rounded">Slot 10.6.2</span>
              <span className="text-blue-900 font-medium text-[11px]">ISO 10993 Biocompatibility</span>
            </div>
          </div>
        </div>

        <div className="p-6 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5 text-xs">
          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Generic / Common Device Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.generic_name || ""}
              onChange={(e) => handleFieldChange("generic_name", e.target.value)}
              placeholder="e.g. Coronary Drug-Eluting Stent"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Official CDSCO classified device nomenclature.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Brand / Proprietary Trade Name <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.brand_name || ""}
              onChange={(e) => handleFieldChange("brand_name", e.target.value)}
              placeholder="e.g. Xience Sierra / Promus Premier"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 font-semibold"
            />
            <p className="text-[11px] text-slate-400 mt-1">Commercial name on product carton artwork.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Claimed Shelf Life (Months) <span className="text-red-500">*</span>
            </label>
            <input
              type="number"
              value={formData.shelf_life_months || 36}
              onChange={(e) => handleFieldChange("shelf_life_months", Number(e.target.value))}
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Substantiated by Slot 10.6.7 stability data.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Target Patient Population <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.intended_patient_population || ""}
              onChange={(e) => handleFieldChange("intended_patient_population", e.target.value)}
              placeholder="e.g. Adult patients $\ge 18$ years"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Adult, pediatric, neonatal, or geriatric.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Target Anatomical Site / Tissue <span className="text-red-500">*</span>
            </label>
            <input
              type="text"
              value={formData.anatomical_site || ""}
              onChange={(e) => handleFieldChange("anatomical_site", e.target.value)}
              placeholder="e.g. Native coronary arteries, femoral bone"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Anatomical application site.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Temperature Range (°C) <span className="text-red-500">*</span>
            </label>
            <div className="flex items-center gap-2">
              <input
                type="number"
                value={formData.storage_temperature_min || 0}
                onChange={(e) => handleFieldChange("storage_temperature_min", Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-xs text-slate-800 text-center"
              />
              <span className="text-slate-400 font-bold">to</span>
              <input
                type="number"
                value={formData.storage_temperature_max || 30}
                onChange={(e) => handleFieldChange("storage_temperature_max", Number(e.target.value))}
                className="w-full rounded-lg border border-slate-300 bg-white px-2.5 py-2 text-xs text-slate-800 text-center"
              />
              <span className="text-slate-500 font-medium">°C</span>
            </div>
            <p className="text-[11px] text-slate-400 mt-1">Matches packaging label markings.</p>
          </div>

          <div className="md:col-span-2">
            <label className="block font-semibold text-slate-700 mb-1">
              Statutory Intended Use Statement <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={2}
              value={formData.intended_use || ""}
              onChange={(e) => handleFieldChange("intended_use", e.target.value)}
              placeholder="Detailed statutory clinical intended use as stated in the Instructions for Use (IFU)."
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Must align verbatim with Slot 10.4 IFU booklet.</p>
          </div>

          <div>
            <label className="block font-semibold text-slate-700 mb-1">
              Material of Construction (MOC) <span className="text-red-500">*</span>
            </label>
            <textarea
              rows={2}
              value={formData.material_of_construction || ""}
              onChange={(e) => handleFieldChange("material_of_construction", e.target.value)}
              placeholder="e.g. Cobalt Chromium L605, PVDF-HFP Polymer, Titanium Ti-6Al-4V ELI"
              className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-800 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
            <p className="text-[11px] text-slate-400 mt-1">Must correspond to ISO 10993 in Slot 10.6.2.</p>
          </div>
        </div>
      </section>

      {/* SECTION 4: MODEL MATRIX / VARIANT TABLE */}
      <section className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="border-b border-slate-100 bg-slate-50/70 px-6 py-4 flex flex-col md:flex-row md:items-center md:justify-between gap-3">
          <div>
            <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
              <Cpu className="h-4 w-4 text-blue-600" />
              Section 4: Model Matrix & Product Variant Table
            </h3>
            <p className="text-xs text-slate-500 mt-0.5">
              Every model and catalogue number listed here must appear in the Free Sale Certificate and Covering Letter.
            </p>
          </div>

          <div className="flex items-center gap-3">
            <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50/80 px-2.5 py-1 text-xs">
              <span className="font-mono font-bold text-blue-700 bg-blue-100 px-1 rounded">Slot 7.0</span>
              <span className="text-blue-900 font-medium text-[11px]">Free Sale Certificate</span>
            </div>

            <button
              type="button"
              onClick={handleAddVariant}
              className="inline-flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-3 py-1.5 text-xs font-semibold text-blue-700 hover:bg-blue-100 transition-colors"
            >
              <Plus className="h-3.5 w-3.5" />
              <span>Add Model Variant</span>
            </button>
          </div>
        </div>

        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-slate-200 text-left text-xs">
            <thead className="bg-slate-50 text-[11px] font-semibold uppercase tracking-wider text-slate-500">
              <tr>
                <th scope="col" className="px-4 py-3">Model / Cat No.</th>
                <th scope="col" className="px-4 py-3">Variant Name</th>
                <th scope="col" className="px-4 py-3">Dimensional Specs</th>
                <th scope="col" className="px-4 py-3">Pack Size</th>
                <th scope="col" className="px-4 py-3">Accessories</th>
                <th scope="col" className="px-4 py-3 text-right">Action</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 bg-white">
              {(formData.model_variants || []).map((variant, idx) => (
                <tr key={idx} className="hover:bg-slate-50/60 transition-colors">
                  <td className="px-4 py-2.5">
                    <input
                      type="text"
                      value={variant.model_number}
                      onChange={(e) => handleVariantChange(idx, "model_number", e.target.value)}
                      placeholder="e.g. MOD-101"
                      className="w-full rounded border border-slate-300 px-2 py-1 text-xs font-mono"
                    />
                  </td>
                  <td className="px-4 py-2.5">
                    <input
                      type="text"
                      value={variant.model_name}
                      onChange={(e) => handleVariantChange(idx, "model_name", e.target.value)}
                      placeholder="e.g. Standard 2.5mm"
                      className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="px-4 py-2.5">
                    <input
                      type="text"
                      value={variant.dimension_spec}
                      onChange={(e) => handleVariantChange(idx, "dimension_spec", e.target.value)}
                      placeholder="e.g. 2.5mm x 18mm"
                      className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="px-4 py-2.5">
                    <input
                      type="text"
                      value={variant.pack_size}
                      onChange={(e) => handleVariantChange(idx, "pack_size", e.target.value)}
                      placeholder="e.g. 1 Unit / Box"
                      className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="px-4 py-2.5">
                    <input
                      type="text"
                      value={variant.accessories_included || ""}
                      onChange={(e) => handleVariantChange(idx, "accessories_included", e.target.value)}
                      placeholder="e.g. Guidewire, Dilator"
                      className="w-full rounded border border-slate-300 px-2 py-1 text-xs"
                    />
                  </td>
                  <td className="px-4 py-2.5 text-right">
                    <button
                      type="button"
                      onClick={() => handleRemoveVariant(idx)}
                      disabled={(formData.model_variants?.length || 0) <= 1}
                      className="text-slate-400 hover:text-red-600 disabled:opacity-30 p-1"
                      title="Remove variant"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* SECTION 5: DYNAMIC TECHNOLOGY & MODALITY PREDICATES */}
      <section className="rounded-xl border border-slate-200 bg-white shadow-xs overflow-hidden">
        <div className="border-b border-slate-100 bg-slate-50/70 px-6 py-4">
          <h3 className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Activity className="h-4 w-4 text-blue-600" />
            Section 5: Dynamic Technology & Statutory Predicates
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Conditional field groups that dynamically appear based on product characteristics (Sterile, Software, Drug, Tissue, IVD).
          </p>
        </div>

        <div className="p-6 space-y-6">
          {/* 5.1 STERILITY PREDICATE */}
          <div className="rounded-xl border border-slate-200 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="toggle-sterile"
                  checked={formData.is_sterile}
                  onChange={(e) => handleFieldChange("is_sterile", e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="toggle-sterile" className="text-xs font-bold text-slate-900 cursor-pointer">
                  Device is Supplied Sterile (`is_sterile: true`)
                </label>
              </div>

              {formData.is_sterile && (
                <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs text-blue-800">
                  <span className="font-mono font-bold text-blue-700">Slot 10.6.3</span>
                  <span className="text-[11px]">Sterilization Validation (ISO 11135 / 11137)</span>
                </div>
              )}
            </div>

            {formData.is_sterile && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 text-xs border-t border-slate-100">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Sterilization Method</label>
                  <select
                    value={formData.sterilization_method}
                    onChange={(e) => handleFieldChange("sterilization_method", e.target.value)}
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs bg-white"
                  >
                    <option value="ETHYLENE_OXIDE">Ethylene Oxide (EO Gas - ISO 11135)</option>
                    <option value="GAMMA_IRRADIATION">Gamma Irradiation (Cobalt-60 - ISO 11137)</option>
                    <option value="ELECTRON_BEAM">Electron Beam (E-Beam - ISO 11137)</option>
                    <option value="STEAM_AUTOCLAVE">Moist Heat / Steam (ISO 17665)</option>
                    <option value="ASEPTIC_PROCESSING">Aseptic Processing (ISO 13408)</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Sterility Assurance Level (SAL)</label>
                  <input
                    type="text"
                    value={formData.sterility_assurance_level || "10^-6"}
                    onChange={(e) => handleFieldChange("sterility_assurance_level", e.target.value)}
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs font-mono"
                  />
                  <p className="text-[11px] text-slate-400 mt-0.5">Statutory standard: $10^{-6}$ SAL.</p>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Sterile Barrier Packaging System</label>
                  <input
                    type="text"
                    value={formData.packaging_barrier_system || ""}
                    onChange={(e) => handleFieldChange("packaging_barrier_system", e.target.value)}
                    placeholder="e.g. Tyvek / Mylar heat-sealed pouch"
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs"
                  />
                </div>
              </div>
            )}
          </div>

          {/* 5.2 SOFTWARE / SAMD PREDICATE */}
          <div className="rounded-xl border border-slate-200 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="toggle-software"
                  checked={formData.contains_software}
                  onChange={(e) => handleFieldChange("contains_software", e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="toggle-software" className="text-xs font-bold text-slate-900 cursor-pointer">
                  Contains Embedded Software, Firmware, or SaMD (`contains_software: true`)
                </label>
              </div>

              {formData.contains_software && (
                <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs text-blue-800">
                  <span className="font-mono font-bold text-blue-700">Slot 10.6.4</span>
                  <span className="text-[11px]">Software Lifecycle (IEC 62304)</span>
                </div>
              )}
            </div>

            {formData.contains_software && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 text-xs border-t border-slate-100">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Software Build Version</label>
                  <input
                    type="text"
                    value={formData.software_version || ""}
                    onChange={(e) => handleFieldChange("software_version", e.target.value)}
                    placeholder="e.g. v2.4.1 (Build 108)"
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs font-mono"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">IEC 62304 Safety Classification</label>
                  <select
                    value={formData.software_safety_class}
                    onChange={(e) => handleFieldChange("software_safety_class", e.target.value)}
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs bg-white"
                  >
                    <option value="CLASS_A">Class A: No injury or damage to health possible</option>
                    <option value="CLASS_B">Class B: Non-serious injury possible</option>
                    <option value="CLASS_C">Class C: Death or serious injury possible</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Cybersecurity Standard</label>
                  <input
                    type="text"
                    value={formData.cybersecurity_standard_applied || ""}
                    onChange={(e) => handleFieldChange("cybersecurity_standard_applied", e.target.value)}
                    placeholder="e.g. IEC 81001-5-1 / UL 2900"
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs"
                  />
                </div>
              </div>
            )}
          </div>

          {/* 5.3 MEDICINAL SUBSTANCE / DRUG-DEVICE COMBINATION */}
          <div className="rounded-xl border border-slate-200 p-4 space-y-3">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="toggle-drug"
                  checked={formData.contains_medicinal_substance}
                  onChange={(e) => handleFieldChange("contains_medicinal_substance", e.target.checked)}
                  className="h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="toggle-drug" className="text-xs font-bold text-slate-900 cursor-pointer">
                  Incorporates Medicinal Substance / Drug Component (`contains_medicinal_substance: true`)
                </label>
              </div>

              {formData.contains_medicinal_substance && (
                <div className="flex items-center gap-1.5 rounded-lg border border-blue-200 bg-blue-50 px-2 py-0.5 text-xs text-blue-800">
                  <span className="font-mono font-bold text-blue-700">Slot 10.6.6</span>
                  <span className="text-[11px]">Medicinal Substance Dossier</span>
                </div>
              )}
            </div>

            {formData.contains_medicinal_substance && (
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 text-xs border-t border-slate-100">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Active Drug INN Name</label>
                  <input
                    type="text"
                    value={formData.drug_inn_name || ""}
                    onChange={(e) => handleFieldChange("drug_inn_name", e.target.value)}
                    placeholder="e.g. Everolimus / Paclitaxel"
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Pharmacopoeial Standard</label>
                  <select
                    value={formData.drug_pharmacopoeial_grade}
                    onChange={(e) => handleFieldChange("drug_pharmacopoeial_grade", e.target.value)}
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs bg-white"
                  >
                    <option value="IP">Indian Pharmacopoeia (IP)</option>
                    <option value="USP">United States Pharmacopeia (USP)</option>
                    <option value="EP">European Pharmacopoeia (EP)</option>
                    <option value="BP">British Pharmacopoeia (BP)</option>
                    <option value="IN_HOUSE">In-House Quality Specification</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Quantity per Unit</label>
                  <input
                    type="text"
                    value={formData.drug_quantity_per_device || ""}
                    onChange={(e) => handleFieldChange("drug_quantity_per_device", e.target.value)}
                    placeholder="e.g. 100 µg / stent"
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs"
                  />
                </div>
              </div>
            )}
          </div>

          {/* 5.4 IN VITRO DIAGNOSTIC (IVD) SECTION */}
          {isIVD && (
            <div className="rounded-xl border border-purple-200 bg-purple-50/20 p-4 space-y-3">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <FlaskConical className="h-4 w-4 text-purple-600" />
                  <span className="text-xs font-bold text-slate-900">
                    In Vitro Diagnostic (IVD) Specific Parameters (Fourth Schedule Appendix III)
                  </span>
                </div>

                <div className="flex items-center gap-1.5 rounded-lg border border-purple-200 bg-purple-50 px-2 py-0.5 text-xs text-purple-800">
                  <span className="font-mono font-bold text-purple-700">Slot 8.5</span>
                  <span className="text-[11px]">Analytical Performance Dossier</span>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2 text-xs border-t border-purple-100">
                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Target Analyte / Biomarker</label>
                  <input
                    type="text"
                    value={formData.target_analyte || ""}
                    onChange={(e) => handleFieldChange("target_analyte", e.target.value)}
                    placeholder="e.g. Hepatitis B Surface Antigen (HBsAg)"
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs"
                  />
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Methodology / Assay Principle</label>
                  <select
                    value={formData.ivd_test_principle}
                    onChange={(e) => handleFieldChange("ivd_test_principle", e.target.value)}
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs bg-white"
                  >
                    <option value="RAPID_LATERAL_FLOW">Rapid Lateral Flow Immunochromatography</option>
                    <option value="ELISA">Enzyme-Linked Immunosorbent Assay (ELISA)</option>
                    <option value="CLIA">Chemiluminescent Immunoassay (CLIA)</option>
                    <option value="REAL_TIME_RT_PCR">Real-Time RT-PCR / Nucleic Acid Testing</option>
                    <option value="FLOW_CYTOMETRY">Flow Cytometry</option>
                  </select>
                </div>

                <div>
                  <label className="block font-semibold text-slate-700 mb-1">Open-Vial / Working Stability</label>
                  <input
                    type="number"
                    value={formData.open_vial_stability_days || 30}
                    onChange={(e) => handleFieldChange("open_vial_stability_days", Number(e.target.value))}
                    className="w-full rounded border border-slate-300 px-3 py-1.5 text-xs"
                  />
                  <p className="text-[11px] text-slate-400 mt-0.5">Validated working days after opening.</p>
                </div>
              </div>
            </div>
          )}
        </div>
      </section>
    </div>
  );
}
