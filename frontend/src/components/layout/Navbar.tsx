"use client";

import React from "react";
import Link from "next/link";
import { Shield, FileText, PlusCircle } from "lucide-react";
import { useHealth } from "@/hooks/useHealth";

export function Navbar() {
  const { data: health, isLoading, isError } = useHealth();

  return (
    <header className="sticky top-0 z-50 w-full border-b border-slate-200 bg-white/95 backdrop-blur supports-[backdrop-filter]:bg-white/60">
      <div className="mx-auto flex h-14 max-w-7xl items-center justify-between px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-6">
          <Link href="/" className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-blue-600 text-white shadow-sm">
              <Shield className="h-5 w-5" />
            </div>
            <div>
              <span className="text-sm font-bold tracking-tight text-slate-900">
                CDSCO Dossier Builder
              </span>
              <span className="hidden text-xs text-slate-500 sm:inline ml-2 border-l border-slate-200 pl-2 font-medium">
                MDR 2017 Regulatory Suite
              </span>
            </div>
          </Link>

          <nav className="hidden md:flex items-center gap-1 text-sm font-medium text-slate-600">
            <Link
              href="/"
              className="flex items-center gap-1.5 rounded-md px-3 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            >
              <FileText className="h-4 w-4 text-slate-500" />
              Submissions
            </Link>
            <Link
              href="/submissions/new"
              className="flex items-center gap-1.5 rounded-md px-3 py-1.5 hover:bg-slate-100 hover:text-slate-900 transition-colors"
            >
              <PlusCircle className="h-4 w-4 text-slate-500" />
              New Filing
            </Link>
          </nav>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 rounded-full border border-slate-200 bg-slate-50 px-3 py-1 text-xs font-medium text-slate-700">
            {isLoading ? (
              <>
                <span className="flex h-2 w-2 rounded-full bg-amber-400 animate-pulse" />
                <span className="text-slate-500">Connecting...</span>
              </>
            ) : isError || health?.status !== "healthy" ? (
              <>
                <span className="flex h-2 w-2 rounded-full bg-red-500" />
                <span className="text-red-700">Service Degraded</span>
              </>
            ) : (
              <>
                <span className="flex h-2 w-2 rounded-full bg-emerald-500" />
                <span className="text-emerald-700">Gateway v{health.version}</span>
              </>
            )}
          </div>

          <div className="flex h-8 w-8 items-center justify-center rounded-full bg-slate-800 text-xs font-semibold text-white">
            RA
          </div>
        </div>
      </div>
    </header>
  );
}
