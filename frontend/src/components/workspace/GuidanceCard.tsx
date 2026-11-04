"use client";

import React from "react";
import {
  ShieldAlert,
  CheckSquare,
  BookOpen,
  Calendar,
  Building,
  ExternalLink,
  Info,
  Scale,
  Sparkles,
} from "lucide-react";
import { SubmissionEntity } from "@/types/regulatory";

interface GuidanceCardProps {
  entity: SubmissionEntity;
}

export function GuidanceCard({ entity }: GuidanceCardProps) {
  const guidance = entity.guidance;

  if (!guidance) {
    return (
      <div className="rounded-xl border border-slate-200 bg-white p-6 shadow-xs text-center text-slate-500">
        <Info className="h-6 w-6 mx-auto mb-2 text-slate-400" />
        <p className="text-xs">No specific regulatory guidance card mapped for slot {entity.slot_id}.</p>
      </div>
    );
  }

  const mandatoryInclusions = guidance.mandatory_inclusions || [];
  const criticalPitfalls = guidance.critical_pitfalls || [];

  return (
    <div className="rounded-2xl border border-slate-200 bg-white shadow-xs overflow-hidden">
      {/* Guidance Header */}
      <div className="border-b border-slate-100 bg-gradient-to-r from-blue-50/60 to-indigo-50/30 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-blue-700">
            <BookOpen className="h-4 w-4" />
            <span>8-Point Regulatory Guidance Card</span>
          </div>
          {guidance.official_citation && (
            <div className="flex items-center gap-1.5 rounded-full border border-blue-200 bg-white px-2.5 py-0.5 text-[11px] font-semibold text-blue-800 shadow-2xs">
              <Scale className="h-3 w-3 text-blue-600" />
              <span>{guidance.official_citation}</span>
            </div>
          )}
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* 1. What is required & 2. Why it is needed */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Point 1: What is Required */}
          <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-4">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
              1. What is Required?
            </span>
            <p className="text-xs text-slate-800 leading-relaxed font-medium">
              {guidance.what_it_is || "Statutory documentary evidence satisfying the compliance criteria for this slot."}
            </p>
          </div>

          {/* Point 2: Why it is Needed */}
          <div className="rounded-xl border border-slate-200/80 bg-slate-50/50 p-4">
            <span className="text-[11px] font-bold uppercase tracking-wider text-slate-500 block mb-1">
              2. Why is CDSCO Asking for It?
            </span>
            <p className="text-xs text-slate-700 leading-relaxed">
              {guidance.why_it_is_needed || "Mandated under the Medical Devices Rules, 2017 to demonstrate safety, performance, and regulatory standing."}
            </p>
          </div>
        </div>

        {/* 3. Who issues & 4. Validity & 5. Target SUGAM Portal */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
          {/* Point 3: Who issues */}
          <div className="rounded-lg border border-slate-200 p-3 bg-white">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <Building className="h-3.5 w-3.5 text-blue-600" />
              <span className="text-[10px] font-bold uppercase tracking-wider">3. Who Issues It?</span>
            </div>
            <p className="text-xs font-semibold text-slate-900 line-clamp-2">
              {guidance.who_issues || "Manufacturer / Statutory Authority"}
            </p>
          </div>

          {/* Point 4: Validity & Expiry */}
          <div className="rounded-lg border border-slate-200 p-3 bg-white">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <Calendar className="h-3.5 w-3.5 text-emerald-600" />
              <span className="text-[10px] font-bold uppercase tracking-wider">4. Statutory Tenure</span>
            </div>
            <p className="text-xs font-semibold text-slate-900 line-clamp-2">
              {guidance.validity_period || "Must be valid on date of submission"}
            </p>
          </div>

          {/* Point 5: Target SUGAM Location */}
          <div className="rounded-lg border border-slate-200 p-3 bg-white">
            <div className="flex items-center gap-1.5 text-slate-500 mb-1">
              <ExternalLink className="h-3.5 w-3.5 text-indigo-600" />
              <span className="text-[10px] font-bold uppercase tracking-wider">5. SUGAM Portal Tab</span>
            </div>
            <p className="text-xs font-semibold text-slate-900 line-clamp-2">
              {guidance.target_sugam_location || "Checklist / Part III Uploads"}
            </p>
          </div>
        </div>

        {/* Point 6: Mandatory Inclusions Checklist */}
        {mandatoryInclusions.length > 0 && (
          <div className="rounded-xl border border-slate-200 p-4.5 bg-white">
            <div className="flex items-center gap-1.5 text-slate-800 mb-3">
              <CheckSquare className="h-4 w-4 text-emerald-600" />
              <span className="text-xs font-bold uppercase tracking-wider">
                6. Mandatory Document Inclusions Checklist
              </span>
            </div>
            <ul className="space-y-2">
              {mandatoryInclusions.map((item, idx) => (
                <li key={idx} className="flex items-start gap-2.5 text-xs text-slate-700">
                  <div className="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded border border-slate-300 bg-slate-50">
                    <span className="text-[10px] font-bold text-slate-500">{idx + 1}</span>
                  </div>
                  <span className="leading-relaxed">{item}</span>
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Point 7: Critical Pitfalls & Common Deficiencies */}
        {criticalPitfalls.length > 0 && (
          <div className="rounded-xl border border-amber-200 bg-amber-50/60 p-4">
            <div className="flex items-center gap-2 text-amber-900 mb-2">
              <ShieldAlert className="h-4 w-4 text-amber-600" />
              <span className="text-xs font-bold uppercase tracking-wider">
                7. Critical Pitfalls & Query Triggers (Avoid Common CDSCO Deficiencies)
              </span>
            </div>
            <ul className="space-y-1.5 pl-6 list-disc text-xs text-amber-800">
              {criticalPitfalls.map((pitfall, idx) => (
                <li key={idx} className="leading-relaxed">
                  {pitfall}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Point 8: Statutory Pro-Forma Availability */}
        <div className="flex items-center justify-between rounded-lg border border-slate-200 bg-slate-50 px-4 py-3">
          <div className="flex items-center gap-2">
            <Sparkles className="h-4 w-4 text-blue-600" />
            <span className="text-xs font-semibold text-slate-800">
              8. Statutory Pro-Forma Template Available
            </span>
          </div>
          <span className={`text-xs font-bold px-2 py-0.5 rounded ${
            guidance.pro_forma_available
              ? "bg-emerald-100 text-emerald-800"
              : "bg-slate-200 text-slate-600"
          }`}>
            {guidance.pro_forma_available ? "In-App Form Supported" : "External Upload Only"}
          </span>
        </div>
      </div>
    </div>
  );
}
