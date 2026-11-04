"use client";

import React, { useState, useMemo } from "react";
import Link from "next/link";
import { useParams, useRouter } from "next/navigation";
import {
  ArrowLeft,
  RefreshCw,
  ShieldCheck,
  AlertTriangle,
  ChevronRight,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useSubmission, useDeleteSubmission } from "@/hooks/useSubmissions";
import { ChecklistTree } from "@/components/workspace/ChecklistTree";
import { GuidanceCard } from "@/components/workspace/GuidanceCard";
import { SlotActionArea } from "@/components/workspace/SlotActionArea";
import {
  PathwayBadge,
  RiskBadge,
  StatusBadge,
} from "@/components/submissions/StatusBadge";
import { DeleteSubmissionModal } from "@/components/submissions/DeleteSubmissionModal";

export default function SubmissionWorkspacePage() {
  const router = useRouter();
  const params = useParams();
  const submissionId = String(params?.id || "");
  const { data: submission, isLoading, isError, error, refetch, isFetching } = useSubmission(submissionId);
  const deleteMutation = useDeleteSubmission();

  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);

  const handleDeleteSubmission = async () => {
    try {
      await deleteMutation.mutateAsync(submissionId);
      setIsDeleteModalOpen(false);
      router.push("/");
    } catch (err) {
      console.error("Failed to delete submission:", err);
    }
  };

  const entities = useMemo(() => submission?.entities || [], [submission]);

  // Selected slot state
  const [activeSlotId, setActiveSlotId] = useState<string | null>(null);

  // Default to first slot if none selected
  const activeEntity = useMemo(() => {
    if (!entities.length) return null;
    if (activeSlotId) {
      const found = entities.find((e) => e.slot_id === activeSlotId);
      if (found) return found;
    }
    return entities[0];
  }, [entities, activeSlotId]);

  // Calculate live stats
  const totalSlots = entities.length;
  const satisfiedSlots = entities.filter(
    (e) => e.status === "SATISFIED" || (e.evidence_links && e.evidence_links.length > 0)
  ).length;
  const missingSlots = totalSlots - satisfiedSlots;
  const progressPercent = totalSlots > 0 ? Math.round((satisfiedSlots / totalSlots) * 100) : 0;

  if (isLoading) {
    return (
      <div className="flex h-[calc(100vh-3.5rem)] items-center justify-center bg-slate-50">
        <div className="text-center space-y-3">
          <RefreshCw className="h-8 w-8 animate-spin text-blue-600 mx-auto" />
          <h3 className="text-sm font-semibold text-slate-800">Loading statutory submission workspace...</h3>
          <p className="text-xs text-slate-500">Resolving 36-48 checklist slots and regulatory blueprints</p>
        </div>
      </div>
    );
  }

  if (isError || !submission) {
    return (
      <div className="mx-auto max-w-2xl px-4 py-16 text-center">
        <div className="rounded-2xl border border-red-200 bg-red-50 p-8 shadow-xs">
          <AlertTriangle className="h-10 w-10 text-red-600 mx-auto mb-3" />
          <h2 className="text-base font-bold text-red-900">Failed to load submission workspace</h2>
          <p className="mt-1 text-xs text-red-700">
            {error?.message || `Submission '${submissionId}' could not be retrieved from the server.`}
          </p>
          <div className="mt-6 flex justify-center gap-3">
            <Link
              href="/"
              className="rounded-lg border border-slate-300 bg-white px-4 py-2 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-50"
            >
              Back to Dashboard
            </Link>
            <button
              onClick={() => refetch()}
              className="rounded-lg bg-red-600 px-4 py-2 text-xs font-semibold text-white shadow-xs hover:bg-red-700"
            >
              Retry
            </button>
          </div>
        </div>
      </div>
    );
  }

  const anySub = submission as unknown as {
    pathway_code?: string;
    pathway_title?: string;
    device_family_name?: string;
  };
  const pathwayCode = anySub.pathway_code || "MD-14";
  const deviceFamily = anySub.device_family_name || submission.device_category.replace("_", " ");

  return (
    <div className="flex flex-col h-[calc(100vh-3.5rem)] overflow-hidden bg-slate-100">
      {/* Top Workspace Bar */}
      <header className="shrink-0 border-b border-slate-200 bg-white px-4 py-2.5 shadow-2xs">
        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-3">
          {/* Breadcrumbs and Title */}
          <div className="flex items-center gap-3 min-w-0">
            <Link
              href="/"
              className="rounded-lg border border-slate-200 p-1.5 text-slate-500 hover:text-slate-800 hover:bg-slate-50 transition-colors shrink-0"
              title="Return to Portfolio Dashboard"
            >
              <ArrowLeft className="h-4 w-4" />
            </Link>

            <div className="min-w-0">
              <div className="flex items-center gap-2">
                <span className="font-mono text-sm font-bold text-slate-900">
                  {submission.tracking_code}
                </span>
                <PathwayBadge code={pathwayCode} />
                <RiskBadge riskClass={submission.risk_class} />
                <StatusBadge status={submission.status} />
              </div>
              <p className="text-xs text-slate-500 font-medium truncate mt-0.5">
                {deviceFamily} • {submission.filing_modality} Modality
              </p>
            </div>
          </div>

          {/* Readiness Gauge & Quick Stats */}
          <div className="flex items-center gap-5 shrink-0">
            <div className="flex items-center gap-3">
              <div className="text-right">
                <div className="text-xs font-bold text-slate-900">
                  {progressPercent}% Complete
                </div>
                <div className="text-[11px] text-slate-500">
                  {satisfiedSlots}/{totalSlots} slots satisfied
                </div>
              </div>
              <div className="h-2 w-28 overflow-hidden rounded-full bg-slate-200">
                <div
                  className={`h-full rounded-full transition-all duration-300 ${
                    progressPercent === 100
                      ? "bg-emerald-500"
                      : progressPercent > 50
                      ? "bg-blue-600"
                      : "bg-amber-500"
                  }`}
                  style={{ width: `${progressPercent}%` }}
                />
              </div>
            </div>

            <button
              onClick={() => refetch()}
              disabled={isFetching}
              className="rounded-md border border-slate-200 p-1.5 text-slate-500 hover:bg-slate-50 transition-colors"
              title="Refresh submission data"
            >
              <RefreshCw className={`h-3.5 w-3.5 ${isFetching ? "animate-spin" : ""}`} />
            </button>

            <button
              type="button"
              onClick={() => setIsDeleteModalOpen(true)}
              className="inline-flex items-center gap-1.5 rounded-lg border border-red-200 bg-red-50/50 px-2.5 py-1.5 text-xs font-semibold text-red-600 shadow-xs hover:bg-red-100 hover:text-red-700 transition-colors"
              title="Delete statutory submission workspace"
            >
              <Trash2 className="h-3.5 w-3.5" />
              <span>Delete</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main 3-Panel Split Workspace */}
      <div className="flex flex-1 overflow-hidden">
        {/* LEFT PANE: 36-48 Slot Checklist Tree */}
        <aside className="w-80 lg:w-96 shrink-0 h-full overflow-hidden">
          <ChecklistTree
            entities={entities}
            activeSlotId={activeEntity?.slot_id || null}
            onSelectSlot={(slotId) => setActiveSlotId(slotId)}
          />
        </aside>

        {/* CENTER PANE: Entity Workspace Controller */}
        <main className="flex-1 overflow-y-auto p-6 space-y-6">
          {activeEntity ? (
            <>
              {/* Slot Header Banner */}
              <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs">
                <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-400">
                  <span>Slot {activeEntity.slot_id}</span>
                  <ChevronRight className="h-3 w-3" />
                  <span>{activeEntity.category?.replace(/_/g, " ") || "Statutory Document"}</span>
                </div>
                <h2 className="text-lg font-bold text-slate-900 mt-1">
                  {activeEntity.slot_title}
                </h2>
                <div className="mt-2 flex flex-wrap items-center gap-2 text-xs">
                  <span className="rounded bg-slate-100 px-2 py-0.5 font-semibold text-slate-700">
                    Fulfillment: {activeEntity.fulfillment_mode}
                  </span>
                  <span className={`rounded px-2 py-0.5 font-semibold ${
                    activeEntity.status === "SATISFIED" || (activeEntity.evidence_links && activeEntity.evidence_links.length > 0)
                      ? "bg-emerald-100 text-emerald-800"
                      : "bg-red-100 text-red-700"
                  }`}>
                    {activeEntity.status === "SATISFIED" || (activeEntity.evidence_links && activeEntity.evidence_links.length > 0)
                      ? "SATISFIED (Evidence Attached)"
                      : "MISSING (Action Required)"}
                  </span>
                  {activeEntity.chapter && (
                    <span className="rounded bg-blue-50 px-2 py-0.5 font-medium text-blue-700">
                      Chapter: {activeEntity.chapter}
                    </span>
                  )}
                </div>
              </div>

              {/* 8-Point Regulatory Guidance Card */}
              <GuidanceCard entity={activeEntity} />

              {/* Slot Action Area (Attached Files & Upload) */}
              <SlotActionArea
                submissionId={submissionId}
                entity={activeEntity}
              />
            </>
          ) : (
            <div className="flex h-full items-center justify-center text-center p-12 text-slate-400">
              Select a slot from the checklist tree on the left.
            </div>
          )}
        </main>

        {/* RIGHT PANE: Submission Readiness Drawer */}
        <aside className="hidden xl:block w-72 shrink-0 border-l border-slate-200 bg-white p-5 overflow-y-auto space-y-5">
          <div>
            <div className="flex items-center gap-2 text-xs font-bold uppercase tracking-wider text-slate-700">
              <ShieldCheck className="h-4 w-4 text-blue-600" />
              <span>Readiness Breakdown</span>
            </div>
            <p className="text-[11px] text-slate-500 mt-0.5">
              Statutory pre-submission audit
            </p>
          </div>

          {/* Metrics summary */}
          <div className="space-y-2.5">
            <div className="flex items-center justify-between rounded-lg border border-slate-100 bg-slate-50/50 p-2.5 text-xs">
              <span className="text-slate-600 font-medium">Mandatory Slots</span>
              <span className="font-bold text-slate-900">{totalSlots}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-emerald-100 bg-emerald-50/40 p-2.5 text-xs">
              <span className="text-emerald-800 font-medium">Satisfied & Attached</span>
              <span className="font-bold text-emerald-800">{satisfiedSlots}</span>
            </div>
            <div className="flex items-center justify-between rounded-lg border border-red-100 bg-red-50/40 p-2.5 text-xs">
              <span className="text-red-800 font-medium">Missing Evidence</span>
              <span className="font-bold text-red-800">{missingSlots}</span>
            </div>
          </div>

          {/* Statutory Guidance Tip */}
          <div className="rounded-xl border border-blue-200 bg-blue-50/50 p-3.5 text-xs text-blue-900 space-y-1.5">
            <div className="flex items-center gap-1.5 font-bold">
              <Sparkles className="h-3.5 w-3.5 text-blue-600" />
              <span>Next Step in Flow</span>
            </div>
            <p className="text-[11px] text-blue-800 leading-relaxed">
              Attach compliant PDF, Word, or image evidence to each missing slot before running the 10MB master dossier assembly compiler.
            </p>
          </div>
        </aside>
      </div>

      {/* Delete Confirmation Modal */}
      <DeleteSubmissionModal
        isOpen={isDeleteModalOpen}
        onClose={() => setIsDeleteModalOpen(false)}
        onConfirm={handleDeleteSubmission}
        trackingCode={submission.tracking_code}
        isDeleting={deleteMutation.isPending}
      />
    </div>
  );
}
