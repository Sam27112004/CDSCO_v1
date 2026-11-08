"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ArrowLeft,
  ArrowRight,
  Building2,
  Sliders,
  Info,
  Check,
  Sparkles,
  AlertCircle,
  PenLine,
} from "lucide-react";
import { useCreateSubmission } from "@/hooks/useSubmissions";
import { useProfiles, useCreateProfile } from "@/hooks/useProfiles";
import {
  DeviceCategory,
  FilingModality,
  RiskClass,
} from "@/types/regulatory";

interface PathwayOption {
  code: string;
  title: string;
  description: string;
  authority: string;
  eligibleClasses: RiskClass[];
  isImport: boolean;
  slotsCount: number;
  isAvailable: boolean;
  statusNote?: string;
}

const PATHWAY_OPTIONS: PathwayOption[] = [
  {
    code: "MD-14",
    title: "Form MD-14: Commercial Import Licence",
    description: "Anchor statutory pathway for commercial import and distribution of foreign manufactured medical devices in India.",
    authority: "Central Licensing Authority (CDSCO HQ, New Delhi)",
    eligibleClasses: ["CLASS_A", "CLASS_B", "CLASS_C", "CLASS_D"],
    isImport: true,
    slotsCount: 36,
    isAvailable: true,
  },
  {
    code: "MD-7",
    title: "Form MD-7: Commercial Manufacturing Licence (Class C & D)",
    description: "Domestic manufacturing licence for medium-high to high risk medical devices.",
    authority: "Central Licensing Authority (CLA)",
    eligibleClasses: ["CLASS_C", "CLASS_D"],
    isImport: false,
    slotsCount: 48,
    isAvailable: true,
  },
  {
    code: "MD-8",
    title: "Form MD-8: Loan Licence to Manufacture (Class C & D)",
    description: "Statutory loan licence to manufacture on another licensed manufacturer's premises.",
    authority: "Central Licensing Authority (CLA)",
    eligibleClasses: ["CLASS_C", "CLASS_D"],
    isImport: false,
    slotsCount: 48,
    isAvailable: false,
    statusNote: "Work in Progress",
  },
  {
    code: "MD-3",
    title: "Form MD-3: Commercial Manufacturing Licence (Class A & B)",
    description: "Domestic manufacturing licence for low and low-medium risk medical devices under State Licensing Authority (SLA).",
    authority: "State Licensing Authority (SLA)",
    eligibleClasses: ["CLASS_A", "CLASS_B"],
    isImport: false,
    slotsCount: 32,
    isAvailable: false,
    statusNote: "Work in Progress",
  },
  {
    code: "MD-4",
    title: "Form MD-4: Loan Licence to Manufacture (Class A & B)",
    description: "State loan licence for Class A & B devices manufactured through contract facilities under State Licensing Authority (SLA).",
    authority: "State Licensing Authority (SLA)",
    eligibleClasses: ["CLASS_A", "CLASS_B"],
    isImport: false,
    slotsCount: 32,
    isAvailable: false,
    statusNote: "Work in Progress",
  },
];

export default function SetupWizardPage() {
  const router = useRouter();
  const createSubmission = useCreateSubmission();
  const createProfile = useCreateProfile();
  const { data: profiles } = useProfiles();

  // Wizard Step (1, 2, 3)
  const [currentStep, setCurrentStep] = useState<1 | 2 | 3>(1);

  // Form State
  const [selectedPathway, setSelectedPathway] = useState<string>("MD-14");
  const [modality, setModality] = useState<FilingModality>("FRESH");
  const [deviceFamilyName, setDeviceFamilyName] = useState<string>("");
  const [deviceTitleError, setDeviceTitleError] = useState<boolean>(false);
  const [deviceCategory, setDeviceCategory] = useState<DeviceCategory>("MEDICAL_DEVICE");
  const [riskClass, setRiskClass] = useState<RiskClass>("CLASS_C");

  // Profile Binding Mode: Select Saved vs Enter Manually
  const [profileMode, setProfileMode] = useState<"SAVED" | "MANUAL">("SAVED");

  // Organizational Profiles State (Saved IDs)
  const [agentProfileId, setAgentProfileId] = useState<string>("");
  const [mfgProfileId, setMfgProfileId] = useState<string>("");
  const [siteProfileId, setSiteProfileId] = useState<string>("");

  // Manual Profile Filling State
  const [manualAgentName, setManualAgentName] = useState<string>("");
  const [manualAgentLicence, setManualAgentLicence] = useState<string>("");
  const [manualMfgName, setManualMfgName] = useState<string>("");
  const [manualMfgCountry, setManualMfgCountry] = useState<string>("United States");
  const [manualSiteAddress, setManualSiteAddress] = useState<string>("");
  const [saveAsProfile, setSaveAsProfile] = useState<boolean>(true);

  const [submissionError, setSubmissionError] = useState<string | null>(null);

  // Regulatory Context Predicates
  const [isSterile, setIsSterile] = useState<boolean>(true);
  const [containsSoftware, setContainsSoftware] = useState<boolean>(false);
  const [containsDrug, setContainsDrug] = useState<boolean>(false);
  const [containsAnimalTissue, setContainsAnimalTissue] = useState<boolean>(false);

  // Active pathway object
  const activePathway = useMemo(
    () => PATHWAY_OPTIONS.find((p) => p.code === selectedPathway) || PATHWAY_OPTIONS[0],
    [selectedPathway]
  );

  // Filter profiles by type
  const agentProfiles = useMemo(
    () => profiles?.filter((p) => p.profile_type === "INDIAN_AGENT") || [],
    [profiles]
  );
  const foreignMfgProfiles = useMemo(
    () => profiles?.filter((p) => p.profile_type === "FOREIGN_MANUFACTURER") || [],
    [profiles]
  );
  const domesticMfgProfiles = useMemo(
    () => profiles?.filter((p) => p.profile_type === "DOMESTIC_MANUFACTURER") || [],
    [profiles]
  );
  const siteProfiles = useMemo(
    () => profiles?.filter((p) => p.profile_type === "MANUFACTURING_SITE") || [],
    [profiles]
  );

  // Auto-select verified default profiles whenever profiles load or pathway changes
  React.useEffect(() => {
    if (activePathway.isImport) {
      if (agentProfiles.length > 0 && (!agentProfileId || !agentProfiles.some((p) => p.id === agentProfileId))) {
        setAgentProfileId(agentProfiles[0].id);
      }
      if (foreignMfgProfiles.length > 0 && (!mfgProfileId || !foreignMfgProfiles.some((p) => p.id === mfgProfileId))) {
        setMfgProfileId(foreignMfgProfiles[0].id);
      }
    } else {
      if (domesticMfgProfiles.length > 0 && (!mfgProfileId || !domesticMfgProfiles.some((p) => p.id === mfgProfileId))) {
        setMfgProfileId(domesticMfgProfiles[0].id);
      }
    }
    if (siteProfiles.length > 0 && (!siteProfileId || !siteProfiles.some((p) => p.id === siteProfileId))) {
      setSiteProfileId(siteProfiles[0].id);
    }
  }, [
    activePathway.isImport,
    agentProfiles,
    foreignMfgProfiles,
    domesticMfgProfiles,
    siteProfiles,
    agentProfileId,
    mfgProfileId,
    siteProfileId,
  ]);

  // Handle pathway change with Smart Statutory Constraints (TC-UR01-01)
  const handlePathwaySelect = (pathway: PathwayOption) => {
    if (!pathway.isAvailable) {
      return;
    }
    setSubmissionError(null);
    setSelectedPathway(pathway.code);

    // Enforce valid risk class
    if (!pathway.eligibleClasses.includes(riskClass)) {
      setRiskClass(pathway.eligibleClasses[0]);
    }
  };

  // Submit Handler
  const handleLaunchWorkspace = async () => {
    setSubmissionError(null);

    // Validate Device Family Title
    if (!deviceFamilyName.trim()) {
      setDeviceTitleError(true);
      setCurrentStep(1);
      setSubmissionError("Device Family Title is required to establish statutory product identity.");
      return;
    }

    try {
      let resolvedApplicantId: string | undefined = profileMode === "SAVED" ? (agentProfileId || undefined) : undefined;
      let resolvedMfgId: string | undefined = profileMode === "SAVED" ? (mfgProfileId || undefined) : undefined;
      let resolvedSiteId: string | undefined = profileMode === "SAVED" ? (siteProfileId || undefined) : undefined;

      // If user filled manual details and opted to save them into organizational directory
      if (profileMode === "MANUAL" && saveAsProfile) {
        if (activePathway.isImport) {
          if (manualAgentName.trim()) {
            try {
              const agent = await createProfile.mutateAsync({
                profile_type: "INDIAN_AGENT",
                name: manualAgentName.trim(),
                data_payload: {
                  wholesale_licence: manualAgentLicence.trim() || undefined,
                },
              });
              resolvedApplicantId = agent.id;
            } catch (err) {
              console.warn("Could not save manual agent profile:", err);
            }
          }

          if (manualMfgName.trim()) {
            try {
              const mfg = await createProfile.mutateAsync({
                profile_type: "FOREIGN_MANUFACTURER",
                name: manualMfgName.trim(),
                data_payload: {
                  country: manualMfgCountry.trim() || undefined,
                  address: manualSiteAddress.trim() || undefined,
                },
              });
              resolvedMfgId = mfg.id;
            } catch (err) {
              console.warn("Could not save manual manufacturer profile:", err);
            }
          }
        } else {
          if (manualMfgName.trim()) {
            try {
              const mfg = await createProfile.mutateAsync({
                profile_type: "DOMESTIC_MANUFACTURER",
                name: manualMfgName.trim(),
                data_payload: {
                  address: manualSiteAddress.trim() || undefined,
                },
              });
              resolvedMfgId = mfg.id;
            } catch (err) {
              console.warn("Could not save manual domestic manufacturer profile:", err);
            }
          }
        }

        if (manualSiteAddress.trim()) {
          try {
            const site = await createProfile.mutateAsync({
              profile_type: "MANUFACTURING_SITE",
              name: `${manualMfgName.trim() || "Manufacturing"} Facility`,
              data_payload: {
                address: manualSiteAddress.trim(),
                country: activePathway.isImport ? manualMfgCountry.trim() : "India",
              },
            });
            resolvedSiteId = site.id;
          } catch (err) {
            console.warn("Could not save manual site profile:", err);
          }
        }
      }

      const manualPortalFields =
        profileMode === "MANUAL"
          ? {
              indian_agent_name: manualAgentName.trim() || undefined,
              wholesale_licence_no: manualAgentLicence.trim() || undefined,
              foreign_mfr_name: manualMfgName.trim() || undefined,
              foreign_mfr_country: manualMfgCountry.trim() || undefined,
              foreign_site_address: manualSiteAddress.trim() || undefined,
              domestic_mfr_name: manualMfgName.trim() || undefined,
              mfg_premises_address: manualSiteAddress.trim() || undefined,
            }
          : {};

      const payload = {
        pathway_code: selectedPathway,
        filing_modality: modality,
        device_category: deviceCategory,
        risk_class: riskClass,
        device_family_name: deviceFamilyName.trim(),
        regulatory_context: {
          device_family_name: deviceFamilyName.trim(),
          is_sterile: isSterile,
          contains_software: containsSoftware,
          contains_medicinal_substance: containsDrug,
          contains_animal_tissue: containsAnimalTissue,
          portal_fields: manualPortalFields,
        },
        applicant_profile_id: resolvedApplicantId,
        manufacturer_profile_id: resolvedMfgId,
        site_profile_id: resolvedSiteId,
      };

      const result = await createSubmission.mutateAsync(payload);
      router.push(`/submissions/${result.id}`);
    } catch (err: unknown) {
      console.error("Failed to initialize submission workspace:", err);
      const msg = err instanceof Error ? err.message : "Failed to initialize submission workspace.";
      setSubmissionError(msg);
    }
  };

  return (
    <div className="mx-auto max-w-5xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Breadcrumb */}
      <div className="mb-6">
        <Link
          href="/"
          className="inline-flex items-center gap-1.5 text-xs font-medium text-slate-500 hover:text-slate-800 transition-colors"
        >
          <ArrowLeft className="h-3.5 w-3.5" />
          <span>Back to Submissions Dashboard</span>
        </Link>
      </div>

      {/* Stepper Wizard Header */}
      <div className="mb-8 rounded-2xl border border-slate-200 bg-white p-6 shadow-xs">
        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-slate-100 pb-5">
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-600">
              <Sparkles className="h-3.5 w-3.5" />
              <span>Statutory Setup Wizard</span>
            </div>
            <h1 className="text-xl font-bold tracking-tight text-slate-900 sm:text-2xl mt-0.5">
              Initialize New Regulatory Filing
            </h1>
            <p className="mt-1 text-xs text-slate-500">
              Configure statutory route, bind legal entities, and set dynamic applicability predicates per MDR 2017.
            </p>
          </div>

          <div className="text-right">
            <span className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              Step {currentStep} of 3
            </span>
          </div>
        </div>

        {/* Visual Progress Steps */}
        <div className="mt-6 grid grid-cols-3 gap-2">
          {/* Step 1 */}
          <button
            onClick={() => setCurrentStep(1)}
            className={`flex items-center gap-2.5 rounded-lg p-2.5 text-left transition-colors ${
              currentStep === 1
                ? "bg-blue-50 text-blue-900 ring-1 ring-blue-600/30"
                : currentStep > 1
                ? "bg-emerald-50/50 text-emerald-900 hover:bg-slate-50"
                : "text-slate-400"
            }`}
          >
            <div
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-bold ${
                currentStep === 1
                  ? "bg-blue-600 text-white"
                  : currentStep > 1
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-100 text-slate-500"
              }`}
            >
              {currentStep > 1 ? <Check className="h-4 w-4" /> : "1"}
            </div>
            <div className="hidden sm:block min-w-0">
              <div className="text-xs font-semibold truncate">Pathway & Modality</div>
              <div className="text-[10px] text-slate-500 truncate">{selectedPathway} ({modality})</div>
            </div>
          </button>

          {/* Step 2 */}
          <button
            onClick={() => setCurrentStep(2)}
            className={`flex items-center gap-2.5 rounded-lg p-2.5 text-left transition-colors ${
              currentStep === 2
                ? "bg-blue-50 text-blue-900 ring-1 ring-blue-600/30"
                : currentStep > 2
                ? "bg-emerald-50/50 text-emerald-900 hover:bg-slate-50"
                : "text-slate-400"
            }`}
          >
            <div
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-bold ${
                currentStep === 2
                  ? "bg-blue-600 text-white"
                  : currentStep > 2
                  ? "bg-emerald-600 text-white"
                  : "bg-slate-100 text-slate-500"
              }`}
            >
              {currentStep > 2 ? <Check className="h-4 w-4" /> : "2"}
            </div>
            <div className="hidden sm:block min-w-0">
              <div className="text-xs font-semibold truncate">Legal Profiles</div>
              <div className="text-[10px] text-slate-500 truncate">Agent & Mfg Sites</div>
            </div>
          </button>

          {/* Step 3 */}
          <button
            onClick={() => setCurrentStep(3)}
            className={`flex items-center gap-2.5 rounded-lg p-2.5 text-left transition-colors ${
              currentStep === 3
                ? "bg-blue-50 text-blue-900 ring-1 ring-blue-600/30"
                : "text-slate-400"
            }`}
          >
            <div
              className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-md text-xs font-bold ${
                currentStep === 3
                  ? "bg-blue-600 text-white"
                  : "bg-slate-100 text-slate-500"
              }`}
            >
              3
            </div>
            <div className="hidden sm:block min-w-0">
              <div className="text-xs font-semibold truncate">Context & Constraints</div>
              <div className="text-[10px] text-slate-500 truncate">Risk & Applicability</div>
            </div>
          </button>
        </div>
      </div>

      {/* STEP 1: Select Regulatory Pathway & Modality */}
      {currentStep === 1 && (
        <div className="space-y-6">
          {/* Device Family Input */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
            <label className="block text-sm font-semibold text-slate-900">
              Device Family Title <span className="text-red-500">*</span>
            </label>
            <p className="mt-0.5 text-xs text-slate-500">
              Enter the statutory medical device name as approved on the Foreign Free Sale Certificate or Quality Manual. This is required to establish statutory product identity under MDR 2017.
            </p>
            <input
              type="text"
              value={deviceFamilyName}
              onChange={(e) => {
                setDeviceFamilyName(e.target.value);
                if (e.target.value.trim()) setDeviceTitleError(false);
              }}
              placeholder="e.g. Orthopedic Pedicle Screw Spinal Fixation System"
              className={`mt-3 w-full rounded-lg border px-3.5 py-2.5 text-sm text-slate-900 placeholder:text-slate-400 focus:outline-none focus:ring-1 ${
                deviceTitleError
                  ? "border-red-500 focus:border-red-500 focus:ring-red-500 bg-red-50/30"
                  : "border-slate-300 focus:border-blue-500 focus:ring-blue-500"
              }`}
            />
            {deviceTitleError && (
              <p className="mt-2 text-xs font-semibold text-red-600 flex items-center gap-1.5">
                <AlertCircle className="h-4 w-4" />
                <span>Device Family Title is required to establish statutory product identity.</span>
              </p>
            )}
          </div>

          {/* Filing Modality Selector */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
            <label className="block text-sm font-semibold text-slate-900 mb-1">
              Filing Modality (Statutory Application Nature)
            </label>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 mt-3">
              {[
                { id: "FRESH", title: "Fresh Application", desc: "First-time licence application in India" },
                { id: "RENEWAL", title: "Licence Renewal", desc: "Statutory 5-year validity extension" },
                { id: "POST_APPROVAL_CHANGE", title: "Post-Approval Change", desc: "Major or minor variation filing" },
                { id: "ENDORSEMENT", title: "Endorsement", desc: "Additional model or site inclusion" },
              ].map((m) => (
                <button
                  key={m.id}
                  type="button"
                  onClick={() => setModality(m.id as FilingModality)}
                  className={`flex flex-col text-left p-3.5 rounded-lg border transition-all ${
                    modality === m.id
                      ? "border-blue-600 bg-blue-50/50 ring-1 ring-blue-600"
                      : "border-slate-200 bg-white hover:border-slate-300"
                  }`}
                >
                  <span className="text-xs font-bold text-slate-900">{m.title}</span>
                  <span className="text-[11px] text-slate-500 mt-1">{m.desc}</span>
                </button>
              ))}
            </div>
          </div>

          {/* Pathway Selection */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
            <div className="flex items-center justify-between mb-3">
              <div>
                <label className="block text-sm font-semibold text-slate-900">
                  Select Statutory Regulatory Route
                </label>
                <p className="mt-0.5 text-xs text-slate-500">
                  Select statutory application route under Indian Medical Devices Rules, 2017.
                </p>
              </div>
            </div>

            <div className="space-y-3 mt-4">
              {PATHWAY_OPTIONS.map((pathway) => {
                const isSelected = selectedPathway === pathway.code;
                const isAvailable = pathway.isAvailable;

                return (
                  <div
                    key={pathway.code}
                    onClick={() => {
                      if (isAvailable) {
                        handlePathwaySelect(pathway);
                      }
                    }}
                    className={`rounded-xl border p-4.5 transition-all ${
                      !isAvailable
                        ? "cursor-not-allowed border-slate-200 bg-slate-50/70 opacity-60"
                        : isSelected
                        ? "cursor-pointer border-blue-600 bg-blue-50/40 ring-1 ring-blue-600"
                        : "cursor-pointer border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50"
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex items-start gap-3">
                        <div
                          className={`mt-0.5 flex h-5 w-5 shrink-0 items-center justify-center rounded-full border ${
                            !isAvailable
                              ? "border-slate-300 bg-slate-200 text-slate-400"
                              : isSelected
                              ? "border-blue-600 bg-blue-600 text-white"
                              : "border-slate-300 bg-white"
                          }`}
                        >
                          {isSelected && <div className="h-2 w-2 rounded-full bg-white" />}
                        </div>
                        <div>
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`text-sm font-bold ${isAvailable ? "text-slate-900" : "text-slate-600"}`}>
                              {pathway.title}
                            </span>
                            <span className="rounded-md bg-slate-100 px-2 py-0.5 text-[10px] font-semibold text-slate-600">
                              {pathway.slotsCount} Checklist Slots
                            </span>
                            {!isAvailable && (
                              <span className="inline-flex items-center rounded-full bg-slate-100 px-2 py-0.5 text-[10px] font-medium text-slate-600 border border-slate-200">
                                Work in Progress
                              </span>
                            )}
                          </div>
                          <p className="mt-1 text-xs text-slate-600 leading-relaxed">
                            {pathway.description}
                          </p>
                          <div className="mt-2 flex items-center gap-2 text-[11px] text-slate-500">
                            <span className="font-semibold text-slate-700">Authority:</span>
                            <span>{pathway.authority}</span>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Step 1 Actions */}
          <div className="flex justify-end gap-3 pt-4">
            <button
              type="button"
              onClick={() => {
                if (!deviceFamilyName.trim()) {
                  setDeviceTitleError(true);
                  return;
                }
                setDeviceTitleError(false);
                setCurrentStep(2);
              }}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 transition-colors"
            >
              <span>Continue to Legal Profiles</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 2: Bind Reusable Organizational Profiles OR Enter Manually */}
      {currentStep === 2 && (
        <div className="space-y-6">
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
            <div className="flex items-center gap-2 mb-1">
              <Building2 className="h-5 w-5 text-blue-600" />
              <h2 className="text-base font-bold text-slate-900">
                Legal Entity & Manufacturing Site Identification
              </h2>
            </div>
            <p className="text-xs text-slate-500 mb-6">
              Choose whether to select pre-saved verified organization profiles or fill in legal entity and plant details directly for this filing.
            </p>

            {/* Profile Selection Mode Toggle */}
            <div className="flex rounded-lg bg-slate-100 p-1 mb-6 max-w-md border border-slate-200">
              <button
                type="button"
                onClick={() => setProfileMode("SAVED")}
                className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition-all ${
                  profileMode === "SAVED"
                    ? "bg-white text-blue-700 shadow-xs ring-1 ring-slate-200"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                Select Saved Profiles (Default)
              </button>
              <button
                type="button"
                onClick={() => setProfileMode("MANUAL")}
                className={`flex-1 rounded-md py-1.5 text-xs font-semibold transition-all ${
                  profileMode === "MANUAL"
                    ? "bg-white text-blue-700 shadow-xs ring-1 ring-slate-200"
                    : "text-slate-500 hover:text-slate-900"
                }`}
              >
                Fill In Details Manually
              </button>
            </div>

            {profileMode === "SAVED" ? (
              /* SAVED PROFILES DROPDOWN MODE */
              activePathway.isImport ? (
                <div className="space-y-5">
                  {/* 1. Authorized Indian Agent */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                        Authorized Indian Agent (Under MDR 2017 Rule 34) <span className="text-red-500">*</span>
                      </label>
                      <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        Saved Enterprise Profile
                      </span>
                    </div>
                    <select
                      value={agentProfileId}
                      onChange={(e) => setAgentProfileId(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      {agentProfiles.length === 0 ? (
                        <option value="">No registered Indian Agent profiles found</option>
                      ) : (
                        agentProfiles.map((p) => {
                          const lic = (p.data_payload?.licence_number as string) || (p.data_payload?.wholesale_licence as string) || "Valid";
                          return (
                            <option key={p.id} value={p.id}>
                              {p.name} (Licence: {lic})
                            </option>
                          );
                        })
                      )}
                    </select>
                    <p className="mt-1 text-[11px] text-slate-500">
                      Must hold valid Wholesale Drug Licence (Form 20B/21B) or Medical Device Registration (Form MD-42).
                    </p>
                  </div>

                  {/* 2. Foreign Manufacturer */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                        Foreign Manufacturer (Legal Manufacturer) <span className="text-red-500">*</span>
                      </label>
                      <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        Saved Enterprise Profile
                      </span>
                    </div>
                    <select
                      value={mfgProfileId}
                      onChange={(e) => setMfgProfileId(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      {foreignMfgProfiles.length === 0 ? (
                        <option value="">No registered Foreign Manufacturer profiles found</option>
                      ) : (
                        foreignMfgProfiles.map((p) => {
                          const country = (p.data_payload?.country as string) || "Foreign";
                          return (
                            <option key={p.id} value={p.id}>
                              {p.name} ({country})
                            </option>
                          );
                        })
                      )}
                    </select>
                    <p className="mt-1 text-[11px] text-slate-500">
                      Corporate manufacturer as named on the Foreign Free Sale Certificate.
                    </p>
                  </div>

                  {/* 3. Manufacturing Site */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                        Primary Manufacturing Site <span className="text-red-500">*</span>
                      </label>
                      <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        Saved Enterprise Profile
                      </span>
                    </div>
                    <select
                      value={siteProfileId}
                      onChange={(e) => setSiteProfileId(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      {siteProfiles.length === 0 ? (
                        <option value="">No registered Manufacturing Site profiles found</option>
                      ) : (
                        siteProfiles.map((p) => {
                          const cleanroom = (p.data_payload?.cleanroom_classification as string) || "Certified Cleanroom";
                          return (
                            <option key={p.id} value={p.id}>
                              {p.name} ({cleanroom})
                            </option>
                          );
                        })
                      )}
                    </select>
                    <p className="mt-1 text-[11px] text-slate-500">
                      Physical production plant matching ISO 13485 accredited scope.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-5">
                  {/* Domestic Manufacturer */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                        Domestic Indian Manufacturer <span className="text-red-500">*</span>
                      </label>
                      <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        Saved Enterprise Profile
                      </span>
                    </div>
                    <select
                      value={mfgProfileId}
                      onChange={(e) => setMfgProfileId(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      {domesticMfgProfiles.length === 0 ? (
                        <option value="">No registered Domestic Manufacturer profiles found</option>
                      ) : (
                        domesticMfgProfiles.map((p) => {
                          const lic = (p.data_payload?.licence_number as string) || "Active";
                          return (
                            <option key={p.id} value={p.id}>
                              {p.name} (Licence: {lic})
                            </option>
                          );
                        })
                      )}
                    </select>
                  </div>

                  {/* Manufacturing Site */}
                  <div>
                    <div className="flex items-center justify-between mb-1.5">
                      <label className="block text-xs font-bold uppercase tracking-wider text-slate-700">
                        Licensed Manufacturing Plant / Site <span className="text-red-500">*</span>
                      </label>
                      <span className="text-[11px] font-semibold text-blue-600 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                        Saved Enterprise Profile
                      </span>
                    </div>
                    <select
                      value={siteProfileId}
                      onChange={(e) => setSiteProfileId(e.target.value)}
                      className="w-full rounded-lg border border-slate-300 bg-white px-3.5 py-2.5 text-sm text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                    >
                      {siteProfiles.length === 0 ? (
                        <option value="">No registered Manufacturing Site profiles found</option>
                      ) : (
                        siteProfiles.map((p) => (
                          <option key={p.id} value={p.id}>
                            {p.name}
                          </option>
                        ))
                      )}
                    </select>
                  </div>
                </div>
              )
            ) : (
              /* MANUAL FILLING / DIRECT TEXT ENTRY MODE */
              <div className="space-y-5 rounded-xl border border-slate-200 bg-slate-50/50 p-5">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-700">
                  <PenLine className="h-4 w-4" />
                  <span>Direct Text Entry for Filing Entities</span>
                </div>

                {activePathway.isImport ? (
                  <div className="space-y-4 text-xs">
                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Authorized Indian Agent Legal Name
                      </label>
                      <input
                        type="text"
                        value={manualAgentName}
                        onChange={(e) => setManualAgentName(e.target.value)}
                        placeholder="e.g. MedTech India Solutions Pvt Ltd"
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">
                          Wholesale Licence Number (Form 20B/21B or MD-42)
                        </label>
                        <input
                          type="text"
                          value={manualAgentLicence}
                          onChange={(e) => setManualAgentLicence(e.target.value)}
                          placeholder="e.g. DL-20B/21B-4491"
                          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 font-mono"
                        />
                      </div>
                      <div>
                        <label className="block font-semibold text-slate-700 mb-1">
                          Country of Legal Manufacturer
                        </label>
                        <input
                          type="text"
                          value={manualMfgCountry}
                          onChange={(e) => setManualMfgCountry(e.target.value)}
                          placeholder="e.g. Germany, USA, Japan"
                          className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Foreign Legal Manufacturer Name
                      </label>
                      <input
                        type="text"
                        value={manualMfgName}
                        onChange={(e) => setManualMfgName(e.target.value)}
                        placeholder="e.g. SpineCraft Medical GmbH"
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Actual Manufacturing Facility Physical Address
                      </label>
                      <textarea
                        rows={2}
                        value={manualSiteAddress}
                        onChange={(e) => setManualSiteAddress(e.target.value)}
                        placeholder="Full factory street address, city, state, postal code, and country."
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                ) : (
                  <div className="space-y-4 text-xs">
                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Domestic Manufacturing Entity Name
                      </label>
                      <input
                        type="text"
                        value={manualMfgName}
                        onChange={(e) => setManualMfgName(e.target.value)}
                        placeholder="e.g. Apex BioMedical Devices India Ltd"
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>

                    <div>
                      <label className="block font-semibold text-slate-700 mb-1">
                        Manufacturing Facility Physical Premises Address
                      </label>
                      <textarea
                        rows={2}
                        value={manualSiteAddress}
                        onChange={(e) => setManualSiteAddress(e.target.value)}
                        placeholder="Plot number, industrial estate, city, district, state, pin code."
                        className="w-full rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}

                {/* Save to Organization Profiles Directory Option */}
                <div className="flex items-start gap-2.5 pt-3 border-t border-slate-200 mt-4 bg-white/70 p-3 rounded-lg border border-slate-200">
                  <input
                    type="checkbox"
                    id="saveAsProfile"
                    checked={saveAsProfile}
                    onChange={(e) => setSaveAsProfile(e.target.checked)}
                    className="mt-0.5 h-4 w-4 rounded border-slate-300 text-blue-600 focus:ring-blue-500"
                  />
                  <label htmlFor="saveAsProfile" className="text-xs text-slate-700 cursor-pointer">
                    <span className="font-semibold text-slate-900">Save entered entities into organization directory</span>
                    <p className="text-[11px] text-slate-500 mt-0.5">
                      Automatically registers these entities in your saved profiles so you can quickly re-select them in future submissions without re-typing.
                    </p>
                  </label>
                </div>
              </div>
            )}
          </div>

          {/* Step 2 Actions */}
          <div className="flex justify-between items-center pt-4">
            <button
              type="button"
              onClick={() => setCurrentStep(1)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition-colors"
            >
              <ArrowLeft className="h-4 w-4" />
              <span>Back</span>
            </button>

            <button
              type="button"
              onClick={() => setCurrentStep(3)}
              className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 transition-colors"
            >
              <span>Continue to Context & Rules</span>
              <ArrowRight className="h-4 w-4" />
            </button>
          </div>
        </div>
      )}

      {/* STEP 3: Define Regulatory Context (with Smart Statutory Constraints) */}
      {currentStep === 3 && (
        <div className="space-y-6">
          {/* Statutory Risk Classification Card */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs">
            <div className="flex items-center justify-between mb-1">
              <label className="block text-sm font-semibold text-slate-900">
                Statutory Risk Classification (First Schedule, MDR 2017)
              </label>
              <span className="rounded-md bg-blue-50 px-2 py-0.5 text-[11px] font-semibold text-blue-700">
                {activePathway.code} Constraint Active
              </span>
            </div>
            <p className="text-xs text-slate-500 mb-4">
              Risk class options are dynamically constrained by the selected pathway to guarantee regulatory validity.
            </p>

            {/* Smart Constraint Warning Banners (TC-UR01-01) */}
            {(selectedPathway === "MD-7" || selectedPathway === "MD-8") && (
              <div className="mb-4 flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900">
                <Info className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Smart Statutory Rule:</span> Form {selectedPathway} is strictly for{" "}
                  <strong>Class C & Class D</strong> medical devices under Central Licensing Authority. Class A and B are disabled.
                </div>
              </div>
            )}

            {(selectedPathway === "MD-3" || selectedPathway === "MD-4") && (
              <div className="mb-4 flex items-start gap-2.5 rounded-lg border border-amber-200 bg-amber-50/70 p-3 text-xs text-amber-900">
                <Info className="h-4 w-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Smart Statutory Rule:</span> Form {selectedPathway} is strictly for{" "}
                  <strong>Class A & Class B</strong> medical devices under State Licensing Authority. Class C and D are disabled.
                </div>
              </div>
            )}

            {/* Risk Class Radio Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
              {[
                { id: "CLASS_A", name: "Class A", title: "Low Risk", desc: "Surgical dressings, thermometers, tongue depressors" },
                { id: "CLASS_B", name: "Class B", title: "Low-Moderate Risk", desc: "Hypodermic needles, suction pumps, blood pressure monitors" },
                { id: "CLASS_C", name: "Class C", title: "Moderate-High Risk", desc: "Pedicle screws, hemodialysis machines, ventilators" },
                { id: "CLASS_D", name: "Class D", title: "High Risk", desc: "Coronary stents, implantable pacemakers, heart valves" },
              ].map((rc) => {
                const isEligible = activePathway.eligibleClasses.includes(rc.id as RiskClass);
                const isSelected = riskClass === rc.id;

                return (
                  <button
                    key={rc.id}
                    type="button"
                    disabled={!isEligible}
                    onClick={() => isEligible && setRiskClass(rc.id as RiskClass)}
                    className={`flex flex-col text-left p-4 rounded-xl border transition-all ${
                      !isEligible
                        ? "opacity-40 cursor-not-allowed bg-slate-50 border-slate-200"
                        : isSelected
                        ? "border-blue-600 bg-blue-50/50 ring-1 ring-blue-600"
                        : "border-slate-200 bg-white hover:border-slate-300 hover:bg-slate-50/50"
                    }`}
                  >
                    <div className="flex items-center justify-between w-full">
                      <span className="text-xs font-bold text-slate-900">{rc.name}</span>
                      <span className={`text-[10px] font-semibold px-1.5 py-0.5 rounded ${
                        rc.id === "CLASS_D" ? "bg-red-100 text-red-700" :
                        rc.id === "CLASS_C" ? "bg-amber-100 text-amber-800" :
                        rc.id === "CLASS_B" ? "bg-blue-100 text-blue-700" :
                        "bg-emerald-100 text-emerald-700"
                      }`}>
                        {rc.title}
                      </span>
                    </div>
                    <span className="text-[11px] text-slate-500 mt-2 leading-relaxed">
                      {rc.desc}
                    </span>
                    {!isEligible && (
                      <span className="mt-2 text-[10px] text-red-600 font-semibold">
                        Not eligible under {selectedPathway}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>
          </div>

          {/* Dynamic Applicability Predicates (TC-UR01-02) */}
          <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs space-y-5">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Sliders className="h-5 w-5 text-blue-600" />
                <h2 className="text-base font-bold text-slate-900">
                  Dynamic Statutory Applicability Predicates
                </h2>
              </div>
              <p className="text-xs text-slate-500">
                Evaluating regulatory rules dynamically activates or deactivates statutory slots in the checklist.
              </p>
            </div>

            {/* Product Category Toggle */}
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between p-3.5 rounded-lg border border-slate-200 bg-slate-50/50 gap-3">
              <div>
                <span className="text-xs font-bold text-slate-900 block">Product Category</span>
                <span className="text-[11px] text-slate-500">
                  Select whether the product is a standard Medical Device or In-Vitro Diagnostic (IVD).
                </span>
              </div>
              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setDeviceCategory("MEDICAL_DEVICE")}
                  className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                    deviceCategory === "MEDICAL_DEVICE"
                      ? "bg-blue-600 text-white shadow-xs"
                      : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  Medical Device
                </button>
                <button
                  type="button"
                  onClick={() => setDeviceCategory("IVD")}
                  className={`rounded-md px-3 py-1.5 text-xs font-semibold transition-colors ${
                    deviceCategory === "IVD"
                      ? "bg-blue-600 text-white shadow-xs"
                      : "bg-white text-slate-700 border border-slate-200 hover:bg-slate-100"
                  }`}
                >
                  In-Vitro Diagnostic (IVD)
                </button>
              </div>
            </div>

            {/* Predicate Toggles */}
            <div className="space-y-3">
              {/* Sterile Status */}
              <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-white">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">Sterilization Status</span>
                    {isSterile && (
                      <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">
                        Activates ISO 11135/11137 (Slot 6.3)
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Is this device supplied sterile or required to be sterilized prior to use?
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setIsSterile(!isSterile)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    isSterile ? "bg-blue-600" : "bg-slate-200"
                  }`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                      isSterile ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {/* Software / AI */}
              <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-white">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">Software / Embedded Firmware / AI</span>
                    {containsSoftware && (
                      <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">
                        Activates IEC 62304 & Cybersecurity
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Does the device contain software, programmable logic, firmware, or AI algorithms?
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setContainsSoftware(!containsSoftware)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    containsSoftware ? "bg-blue-600" : "bg-slate-200"
                  }`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                      containsSoftware ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {/* Medicinal Substance */}
              <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-white">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">Drug-Device Combination Product</span>
                    {containsDrug && (
                      <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">
                        Activates Pharmacology Evaluation
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Does the device incorporate an integral medicinal or active pharmaceutical substance?
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setContainsDrug(!containsDrug)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    containsDrug ? "bg-blue-600" : "bg-slate-200"
                  }`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                      containsDrug ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>

              {/* Animal Tissue */}
              <div className="flex items-center justify-between p-3.5 rounded-lg border border-slate-200 bg-white">
                <div>
                  <div className="flex items-center gap-2">
                    <span className="text-xs font-bold text-slate-900">Animal Origin Material</span>
                    {containsAnimalTissue && (
                      <span className="rounded bg-blue-50 px-1.5 py-0.5 text-[10px] font-semibold text-blue-700">
                        Activates ISO 22442 TSE/BSE Assessment
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-slate-500 mt-0.5">
                    Does the device incorporate non-viable animal tissues, bovine derivatives, or cellular products?
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => setContainsAnimalTissue(!containsAnimalTissue)}
                  className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none ${
                    containsAnimalTissue ? "bg-blue-600" : "bg-slate-200"
                  }`}
                >
                  <span
                    className={`inline-block h-5 w-5 transform rounded-full bg-white shadow-sm ring-0 transition duration-200 ease-in-out ${
                      containsAnimalTissue ? "translate-x-5" : "translate-x-0"
                    }`}
                  />
                </button>
              </div>
            </div>
          </div>

          {/* Submission Error Alert */}
          {submissionError && (
            <div className="rounded-xl border border-red-200 bg-red-50 p-4 text-xs text-red-900 flex items-start gap-2.5">
              <Info className="h-4 w-4 text-red-600 shrink-0 mt-0.5" />
              <div>
                <p className="font-bold">Failed to Initialize Application</p>
                <p className="mt-0.5 text-red-700">{submissionError}</p>
              </div>
            </div>
          )}

          {/* Dynamic Summary Card & Launch Action */}
          <div className="rounded-2xl border border-blue-200 bg-gradient-to-br from-blue-50/50 to-indigo-50/30 p-6 shadow-xs">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider text-blue-700">
                  Ready to Compile Statutory Dossier Workspace
                </span>
                <div className="text-sm font-semibold text-slate-900 mt-1">
                  {activePathway.title} • {riskClass.replace("_", " ")}
                </div>
                <div className="flex flex-wrap items-center gap-2 mt-2">
                  <span className="inline-flex items-center rounded-md bg-white border border-slate-200 px-2 py-1 text-xs font-medium text-slate-700 shadow-2xs">
                    {activePathway.slotsCount} Statutory Slots
                  </span>
                  {isSterile && (
                    <span className="inline-flex items-center rounded-md bg-blue-100 text-blue-800 px-2 py-1 text-xs font-medium">
                      + Sterilization Report
                    </span>
                  )}
                  {containsSoftware && (
                    <span className="inline-flex items-center rounded-md bg-indigo-100 text-indigo-800 px-2 py-1 text-xs font-medium">
                      + Software Validation
                    </span>
                  )}
                </div>
              </div>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  onClick={() => setCurrentStep(2)}
                  className="rounded-lg border border-slate-200 bg-white px-4 py-2.5 text-sm font-semibold text-slate-700 shadow-xs hover:bg-slate-50 transition-colors"
                >
                  Back
                </button>
                <button
                  type="button"
                  disabled={createSubmission.isPending}
                  onClick={handleLaunchWorkspace}
                  className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-6 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 transition-colors disabled:opacity-50"
                >
                  <span>{createSubmission.isPending ? "Generating Workspace..." : "Launch Workspace"}</span>
                  <ArrowRight className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
