import React from "react";
import { RiskClass, SubmissionStatus } from "@/types/regulatory";

interface RiskBadgeProps {
  riskClass: RiskClass | string;
}

export function RiskBadge({ riskClass }: RiskBadgeProps) {
  const normalized = riskClass.toUpperCase();

  switch (normalized) {
    case "CLASS_A":
      return (
        <span className="inline-flex items-center rounded-md bg-emerald-50 px-2 py-1 text-xs font-medium text-emerald-700 ring-1 ring-inset ring-emerald-600/20">
          Class A (Low)
        </span>
      );
    case "CLASS_B":
      return (
        <span className="inline-flex items-center rounded-md bg-blue-50 px-2 py-1 text-xs font-medium text-blue-700 ring-1 ring-inset ring-blue-700/10">
          Class B (Low-Mod)
        </span>
      );
    case "CLASS_C":
      return (
        <span className="inline-flex items-center rounded-md bg-amber-50 px-2 py-1 text-xs font-medium text-amber-800 ring-1 ring-inset ring-amber-600/20">
          Class C (Mod-High)
        </span>
      );
    case "CLASS_D":
      return (
        <span className="inline-flex items-center rounded-md bg-red-50 px-2 py-1 text-xs font-medium text-red-700 ring-1 ring-inset ring-red-600/20">
          Class D (High)
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center rounded-md bg-slate-100 px-2 py-1 text-xs font-medium text-slate-600">
          {riskClass}
        </span>
      );
  }
}

interface StatusBadgeProps {
  status: SubmissionStatus | string;
}

export function StatusBadge({ status }: StatusBadgeProps) {
  switch (status.toUpperCase()) {
    case "SUBMISSION_READY":
    case "APPROVED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-semibold text-emerald-700 border border-emerald-200">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-600" />
          Ready to File
        </span>
      );
    case "IN_REVIEW":
    case "IN_PROGRESS":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-semibold text-blue-700 border border-blue-200">
          <span className="h-1.5 w-1.5 rounded-full bg-blue-600" />
          In Review
        </span>
      );
    case "QUERIED":
    case "REJECTED":
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-semibold text-red-700 border border-red-200">
          <span className="h-1.5 w-1.5 rounded-full bg-red-600" />
          Action Required
        </span>
      );
    case "DRAFT":
    default:
      return (
        <span className="inline-flex items-center gap-1.5 rounded-full bg-slate-100 px-2.5 py-0.5 text-xs font-semibold text-slate-700 border border-slate-200">
          <span className="h-1.5 w-1.5 rounded-full bg-slate-400" />
          Draft
        </span>
      );
  }
}

interface PathwayBadgeProps {
  code: string;
}

export function PathwayBadge({ code }: PathwayBadgeProps) {
  return (
    <span className="inline-flex items-center rounded-md bg-slate-900 px-2.5 py-1 text-xs font-bold text-white shadow-xs">
      {code}
    </span>
  );
}
