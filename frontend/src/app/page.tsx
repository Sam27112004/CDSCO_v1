"use client";

import React, { useState } from "react";
import Link from "next/link";
import {
  FileText,
  Plus,
  CheckCircle2,
  AlertTriangle,
  FolderArchive,
  ArrowRight,
  Layers,
  Search,
  RefreshCw,
  Sparkles,
  Trash2,
} from "lucide-react";
import { useSubmissions, useDeleteSubmission } from "@/hooks/useSubmissions";
import {
  PathwayBadge,
  RiskBadge,
  StatusBadge,
} from "@/components/submissions/StatusBadge";
import { DeleteSubmissionModal } from "@/components/submissions/DeleteSubmissionModal";

export default function PortfolioDashboardPage() {
  const { data: submissions, isLoading, isError, error, refetch, isFetching } = useSubmissions();
  const deleteMutation = useDeleteSubmission();
  const [searchQuery, setSearchQuery] = useState("");
  const [pathwayFilter, setPathwayFilter] = useState("ALL");
  const [submissionToDelete, setSubmissionToDelete] = useState<{ id: string; tracking_code: string } | null>(null);

  const handleDeleteSubmission = async () => {
    if (!submissionToDelete) return;
    try {
      await deleteMutation.mutateAsync(submissionToDelete.id);
      setSubmissionToDelete(null);
    } catch (err) {
      console.error("Failed to delete submission:", err);
    }
  };

  const items = submissions || [];

  // Filtered submissions
  const filtered = items.filter((sub) => {
    const tracking = sub.tracking_code?.toLowerCase() || "";
    const family = (sub as unknown as { device_family_name?: string }).device_family_name?.toLowerCase() || "";
    const pathway = (sub as unknown as { pathway_code?: string }).pathway_code || "";

    const matchesSearch =
      tracking.includes(searchQuery.toLowerCase()) ||
      family.includes(searchQuery.toLowerCase());

    const matchesPathway =
      pathwayFilter === "ALL" || pathway.toUpperCase() === pathwayFilter.toUpperCase();

    return matchesSearch && matchesPathway;
  });

  // Calculate Metrics
  const totalCount = items.length;
  const inPrepCount = items.filter(
    (s) => s.status === "DRAFT" || s.status === "IN_REVIEW"
  ).length;
  const readyCount = items.filter(
    (s) => s.status === "SUBMISSION_READY" || (s as unknown as { progress_percent?: number }).progress_percent === 100
  ).length;
  const actionRequiredCount = items.filter(
    (s) =>
      ((s as unknown as { blockers_count?: number }).blockers_count || 0) > 0 ||
      s.status === "QUERIED"
  ).length;

  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Header */}
      <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-blue-600">
            <Sparkles className="h-4 w-4" />
            <span>CDSCO Statutory Portal Suite</span>
          </div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Submissions Dashboard
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Track, author, and inspect statutory CDSCO dossiers across all Medical Devices Rules, 2017 pathways.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-300 bg-white px-3 py-2 text-sm font-medium text-slate-700 shadow-xs hover:bg-slate-50 transition-colors disabled:opacity-50"
            title="Refresh submissions"
          >
            <RefreshCw className={`h-4 w-4 text-slate-500 ${isFetching ? "animate-spin" : ""}`} />
            <span className="hidden sm:inline">Refresh</span>
          </button>

          <Link
            href="/submissions/new"
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Submission
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Total Submissions
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-50 text-blue-600">
              <Layers className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">{isLoading ? "-" : totalCount}</p>
          <p className="mt-1 text-xs text-slate-500">Across MD-14, MD-7, MD-8 routes</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              In Preparation
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-amber-50 text-amber-600">
              <FileText className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">{isLoading ? "-" : inPrepCount}</p>
          <p className="mt-1 text-xs text-slate-500">Draft dossiers compiling evidence</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Ready to File
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-emerald-50 text-emerald-600">
              <CheckCircle2 className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">{isLoading ? "-" : readyCount}</p>
          <p className="mt-1 text-xs text-slate-500">100% slots satisfied & verified</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-xs">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Action Required
            </span>
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-red-50 text-red-600">
              <AlertTriangle className="h-4 w-4" />
            </div>
          </div>
          <p className="mt-2 text-2xl font-bold text-slate-900">{isLoading ? "-" : actionRequiredCount}</p>
          <p className="mt-1 text-xs text-slate-500">Active statutory blocking issues</p>
        </div>
      </div>

      {/* Filter and Search Bar */}
      <div className="mb-4 flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="relative flex-1 max-w-md">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by Tracking ID or Device Family..."
            className="w-full rounded-lg border border-slate-300 bg-white py-2 pl-9 pr-4 text-sm text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-xs font-medium text-slate-500">Pathway:</span>
          <select
            value={pathwayFilter}
            onChange={(e) => setPathwayFilter(e.target.value)}
            className="rounded-lg border border-slate-300 bg-white px-3 py-1.5 text-xs font-medium text-slate-700 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="ALL">All Pathways</option>
            <option value="MD-14">Form MD-14 (Import)</option>
            <option value="MD-7">Form MD-7 (Mfg C/D)</option>
            <option value="MD-8">Form MD-8 (Loan C/D)</option>
            <option value="MD-3">Form MD-3 (Mfg A/B)</option>
          </select>
        </div>
      </div>

      {/* Main Content Area */}
      {isLoading ? (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
          <div className="divide-y divide-slate-100 p-6 space-y-4">
            {[1, 2, 3].map((n) => (
              <div key={n} className="flex items-center justify-between pt-4 first:pt-0 animate-pulse">
                <div className="space-y-2">
                  <div className="h-4 w-40 rounded bg-slate-200" />
                  <div className="h-3 w-64 rounded bg-slate-100" />
                </div>
                <div className="h-6 w-20 rounded bg-slate-200" />
                <div className="h-8 w-24 rounded bg-slate-200" />
              </div>
            ))}
          </div>
        </div>
      ) : isError ? (
        <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
          <AlertTriangle className="mx-auto h-8 w-8 text-red-600 mb-2" />
          <h3 className="text-sm font-semibold text-red-900">Failed to load submissions</h3>
          <p className="mt-1 text-xs text-red-700 max-w-md mx-auto">
            {error?.message || "Could not connect to the CDSCO backend service."}
          </p>
          <button
            onClick={() => refetch()}
            className="mt-4 inline-flex items-center gap-1.5 rounded-md bg-red-600 px-3 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-red-700"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Retry
          </button>
        </div>
      ) : filtered.length === 0 ? (
        <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-xs">
          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-50 text-blue-600 mb-4">
            <FolderArchive className="h-7 w-7" />
          </div>
          <h3 className="text-lg font-semibold text-slate-900">
            {searchQuery || pathwayFilter !== "ALL"
              ? "No matching submissions found"
              : "No active submissions in workspace"}
          </h3>
          <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto">
            {searchQuery || pathwayFilter !== "ALL"
              ? "Try adjusting your search query or pathway filter."
              : "Start a new statutory dossier by selecting your regulatory pathway (e.g. Form MD-14 for commercial import or Form MD-7 for manufacturing)."}
          </p>
          {!(searchQuery || pathwayFilter !== "ALL") && (
            <div className="mt-6">
              <Link
                href="/submissions/new"
                className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-xs hover:bg-blue-700 transition-colors"
              >
                Launch Setup Wizard
                <ArrowRight className="h-4 w-4" />
              </Link>
            </div>
          )}
        </div>
      ) : (
        <div className="overflow-hidden rounded-xl border border-slate-200 bg-white shadow-xs">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-left text-sm">
              <thead className="bg-slate-50 text-xs font-semibold uppercase tracking-wider text-slate-500">
                <tr>
                  <th scope="col" className="px-6 py-3.5">Tracking ID & Device</th>
                  <th scope="col" className="px-4 py-3.5">Pathway</th>
                  <th scope="col" className="px-4 py-3.5">Risk Class</th>
                  <th scope="col" className="px-4 py-3.5 min-w-[180px]">Readiness Progress</th>
                  <th scope="col" className="px-4 py-3.5">Blockers</th>
                  <th scope="col" className="px-4 py-3.5">Status</th>
                  <th scope="col" className="px-6 py-3.5 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-200 bg-white">
                {filtered.map((sub) => {
                  const anySub = sub as unknown as {
                    pathway_code?: string;
                    device_family_name?: string;
                    progress_percent?: number;
                    total_slots?: number;
                    satisfied_slots?: number;
                    blockers_count?: number;
                  };

                  const pathway = anySub.pathway_code || "MD-14";
                  const deviceFamily = anySub.device_family_name || sub.device_category.replace("_", " ");
                  const progress = anySub.progress_percent ?? 0;
                  const satisfied = anySub.satisfied_slots ?? 0;
                  const total = anySub.total_slots ?? 0;
                  const blockers = anySub.blockers_count ?? 0;

                  return (
                    <tr
                      key={sub.id}
                      className="hover:bg-slate-50/80 transition-colors"
                    >
                      {/* Tracking ID & Device Family */}
                      <td className="px-6 py-4">
                        <Link
                          href={`/submissions/${sub.id}`}
                          className="font-semibold text-blue-600 hover:text-blue-800 hover:underline block"
                        >
                          {sub.tracking_code}
                        </Link>
                        <div className="mt-0.5 text-xs text-slate-500 font-medium">
                          {deviceFamily}
                        </div>
                      </td>

                      {/* Pathway */}
                      <td className="px-4 py-4 whitespace-nowrap">
                        <PathwayBadge code={pathway} />
                      </td>

                      {/* Risk Class */}
                      <td className="px-4 py-4 whitespace-nowrap">
                        <RiskBadge riskClass={sub.risk_class} />
                      </td>

                      {/* Progress Bar & Slots */}
                      <td className="px-4 py-4">
                        <div className="flex items-center justify-between text-xs font-semibold text-slate-700 mb-1">
                          <span>{progress}%</span>
                          <span className="text-slate-400 font-normal">
                            {satisfied}/{total} slots
                          </span>
                        </div>
                        <div className="h-2 w-full overflow-hidden rounded-full bg-slate-100">
                          <div
                            className={`h-full rounded-full transition-all duration-300 ${
                              progress === 100
                                ? "bg-emerald-500"
                                : progress > 50
                                ? "bg-blue-600"
                                : "bg-amber-500"
                            }`}
                            style={{ width: `${progress}%` }}
                          />
                        </div>
                      </td>

                      {/* Blockers */}
                      <td className="px-4 py-4 whitespace-nowrap">
                        {blockers > 0 ? (
                          <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2 py-0.5 text-xs font-semibold text-red-700 border border-red-200">
                            <AlertTriangle className="h-3 w-3" />
                            {blockers} {blockers === 1 ? "Blocker" : "Blockers"}
                          </span>
                        ) : (
                          <span className="inline-flex items-center gap-1 text-xs text-emerald-600 font-medium">
                            <CheckCircle2 className="h-3.5 w-3.5" />
                            Clean
                          </span>
                        )}
                      </td>

                      {/* Status */}
                      <td className="px-4 py-4 whitespace-nowrap">
                        <StatusBadge status={sub.status} />
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 whitespace-nowrap text-right">
                        <div className="flex items-center justify-end gap-2">
                          <Link
                            href={`/submissions/${sub.id}`}
                            className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 shadow-xs hover:bg-slate-100 hover:text-blue-600 transition-colors"
                          >
                            <span>Open</span>
                            <ArrowRight className="h-3.5 w-3.5" />
                          </Link>

                          <button
                            type="button"
                            onClick={(e) => {
                              e.stopPropagation();
                              setSubmissionToDelete({
                                id: sub.id,
                                tracking_code: sub.tracking_code,
                              });
                            }}
                            className="inline-flex items-center gap-1 rounded-lg border border-red-200 bg-red-50/50 px-2.5 py-1.5 text-xs font-semibold text-red-600 shadow-xs hover:bg-red-100 hover:text-red-700 transition-colors"
                            title={`Delete submission ${sub.tracking_code}`}
                          >
                            <Trash2 className="h-3.5 w-3.5" />
                            <span>Delete</span>
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Delete Confirmation Modal */}
      <DeleteSubmissionModal
        isOpen={Boolean(submissionToDelete)}
        onClose={() => setSubmissionToDelete(null)}
        onConfirm={handleDeleteSubmission}
        trackingCode={submissionToDelete?.tracking_code || ""}
        isDeleting={deleteMutation.isPending}
      />
    </div>
  );
}
