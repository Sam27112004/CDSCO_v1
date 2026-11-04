import Link from "next/link";
import {
  FileText,
  Plus,
  CheckCircle2,
  AlertTriangle,
  FolderArchive,
  ArrowRight,
  Layers,
} from "lucide-react";

export default function HomePage() {
  return (
    <div className="mx-auto max-w-7xl px-4 py-8 sm:px-6 lg:px-8">
      {/* Top Banner */}
      <div className="mb-8 flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-slate-900 sm:text-3xl">
            Regulatory Submissions Portfolio
          </h1>
          <p className="mt-1 text-sm text-slate-600">
            Statutory dossier authoring, evidence cataloging, and pre-flight validation under MDR 2017.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <Link
            href="/submissions/new"
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-4 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-blue-600 transition-colors"
          >
            <Plus className="h-4 w-4" />
            New Submission
          </Link>
        </div>
      </div>

      {/* Metrics Row */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4 mb-8">
        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Active Filings
            </span>
            <Layers className="h-5 w-5 text-blue-600" />
          </div>
          <p className="mt-3 text-2xl font-bold text-slate-900">0</p>
          <p className="mt-1 text-xs text-slate-500">Across MD-14, MD-7, MD-8 pathways</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              In Preparation
            </span>
            <FileText className="h-5 w-5 text-amber-500" />
          </div>
          <p className="mt-3 text-2xl font-bold text-slate-900">0</p>
          <p className="mt-1 text-xs text-slate-500">Draft dossiers compiling evidence</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Pre-Flight Ready
            </span>
            <CheckCircle2 className="h-5 w-5 text-emerald-600" />
          </div>
          <p className="mt-3 text-2xl font-bold text-slate-900">0</p>
          <p className="mt-1 text-xs text-slate-500">All slots satisfied and verified</p>
        </div>

        <div className="rounded-xl border border-slate-200 bg-white p-5 shadow-sm">
          <div className="flex items-center justify-between">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">
              Action Required
            </span>
            <AlertTriangle className="h-5 w-5 text-red-500" />
          </div>
          <p className="mt-3 text-2xl font-bold text-slate-900">0</p>
          <p className="mt-1 text-xs text-slate-500">Blocking errors or expired certs</p>
        </div>
      </div>

      {/* Empty State / Quick Launch Card */}
      <div className="rounded-2xl border border-dashed border-slate-300 bg-white p-12 text-center shadow-sm">
        <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-full bg-blue-50 text-blue-600 mb-4">
          <FolderArchive className="h-7 w-7" />
        </div>
        <h3 className="text-lg font-semibold text-slate-900">No active submissions in workspace</h3>
        <p className="mt-2 text-sm text-slate-500 max-w-md mx-auto">
          Start a new statutory dossier by selecting your regulatory pathway (e.g. Form MD-14 for commercial import or Form MD-7 for domestic manufacturing).
        </p>
        <div className="mt-6">
          <Link
            href="/submissions/new"
            className="inline-flex items-center gap-2 rounded-lg bg-blue-600 px-5 py-2.5 text-sm font-semibold text-white shadow-sm hover:bg-blue-700 transition-colors"
          >
            Launch Setup Wizard
            <ArrowRight className="h-4 w-4" />
          </Link>
        </div>
      </div>
    </div>
  );
}
