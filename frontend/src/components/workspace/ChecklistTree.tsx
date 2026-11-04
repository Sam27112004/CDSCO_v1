"use client";

import React, { useState, useMemo } from "react";
import {
  CheckCircle2,
  AlertCircle,
  Search,
  ChevronDown,
  ChevronRight,
  Layers,
} from "lucide-react";
import { SubmissionEntity } from "@/types/regulatory";

interface ChecklistTreeProps {
  entities: SubmissionEntity[];
  activeSlotId: string | null;
  onSelectSlot: (slotId: string) => void;
}

const CATEGORY_NAMES: Record<string, string> = {
  ADMINISTRATIVE: "Administrative Documents",
  ADMINISTRATIVE_LEGAL: "Administrative & Legal Documents",
  LEGAL_ELIGIBILITY: "Legal & Corporate Eligibility",
  REGULATORY_APPROVALS: "Regulatory Free Sale & Global Approvals",
  QUALITY_CERTIFICATES: "Quality & Standards Certifications",
  PLANT_MASTER_FILE_APPENDIX_I: "Plant Master File (Appendix I)",
  TECHNICAL_DOSSIER_PMF: "Plant Master File (PMF)",
  DEVICE_MASTER_FILE_APPENDIX_II: "Device Master File (Appendix II)",
  TECHNICAL_DOSSIER_DMF: "Device Master File (DMF)",
  FIFTH_SCHEDULE_QMS: "Quality Management System (Fifth Schedule)",
  SUPPLEMENTARY: "Supplementary & Undertakings",
  SUPPLEMENTARY_REGULATORY: "Supplementary Regulatory Documents",
};

export function ChecklistTree({
  entities,
  activeSlotId,
  onSelectSlot,
}: ChecklistTreeProps) {
  const [search, setSearch] = useState("");
  const [statusFilter, setStatusFilter] = useState<"ALL" | "SATISFIED" | "MISSING">("ALL");
  const [collapsedCategories, setCollapsedCategories] = useState<Record<string, boolean>>({});

  // Filter entities
  const filteredEntities = useMemo(() => {
    return entities.filter((e) => {
      const matchesSearch =
        e.slot_id.toLowerCase().includes(search.toLowerCase()) ||
        e.slot_title.toLowerCase().includes(search.toLowerCase());

      const isSatisfied = e.status === "SATISFIED" || (e.evidence_links && e.evidence_links.length > 0);
      const matchesStatus =
        statusFilter === "ALL"
          ? true
          : statusFilter === "SATISFIED"
          ? isSatisfied
          : !isSatisfied;

      return matchesSearch && matchesStatus;
    });
  }, [entities, search, statusFilter]);

  // Group by category
  const groupedCategories = useMemo(() => {
    const groups: Record<string, SubmissionEntity[]> = {};
    for (const entity of filteredEntities) {
      const cat = entity.category || "ADMINISTRATIVE";
      if (!groups[cat]) {
        groups[cat] = [];
      }
      groups[cat].push(entity);
    }
    return groups;
  }, [filteredEntities]);

  const toggleCategory = (cat: string) => {
    setCollapsedCategories((prev) => ({
      ...prev,
      [cat]: !prev[cat],
    }));
  };

  return (
    <div className="flex h-full flex-col bg-white border-r border-slate-200">
      {/* Header and Filter */}
      <div className="p-4 border-b border-slate-200 bg-slate-50/50 space-y-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Layers className="h-4 w-4 text-blue-600" />
            <span className="text-xs font-bold uppercase tracking-wider text-slate-800">
              Statutory Checklist Tree
            </span>
          </div>
          <span className="text-xs font-medium text-slate-500">
            {entities.length} Slots
          </span>
        </div>

        {/* Search Input */}
        <div className="relative">
          <Search className="pointer-events-none absolute left-2.5 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-slate-400" />
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Filter requirements (e.g. 4.0, sterilization)..."
            className="w-full rounded-md border border-slate-300 bg-white py-1.5 pl-8 pr-3 text-xs text-slate-900 placeholder:text-slate-400 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          />
        </div>

        {/* Status Filter Buttons */}
        <div className="flex items-center gap-1.5 pt-1">
          <button
            type="button"
            onClick={() => setStatusFilter("ALL")}
            className={`rounded px-2 py-0.5 text-[11px] font-semibold transition-colors ${
              statusFilter === "ALL"
                ? "bg-slate-800 text-white"
                : "bg-slate-200/70 text-slate-600 hover:bg-slate-300/70"
            }`}
          >
            All
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter("MISSING")}
            className={`rounded px-2 py-0.5 text-[11px] font-semibold transition-colors ${
              statusFilter === "MISSING"
                ? "bg-red-600 text-white"
                : "bg-red-50 text-red-700 hover:bg-red-100"
            }`}
          >
            Missing Evidence
          </button>
          <button
            type="button"
            onClick={() => setStatusFilter("SATISFIED")}
            className={`rounded px-2 py-0.5 text-[11px] font-semibold transition-colors ${
              statusFilter === "SATISFIED"
                ? "bg-emerald-600 text-white"
                : "bg-emerald-50 text-emerald-700 hover:bg-emerald-100"
            }`}
          >
            Satisfied
          </button>
        </div>
      </div>

      {/* Tree View Scroll Area */}
      <div className="flex-1 overflow-y-auto divide-y divide-slate-100 p-2 space-y-2">
        {Object.entries(groupedCategories).map(([categoryKey, catEntities]) => {
          const isCollapsed = Boolean(collapsedCategories[categoryKey]);
          const categoryTitle = CATEGORY_NAMES[categoryKey] || categoryKey.replace(/_/g, " ");

          const catSatisfied = catEntities.filter(
            (e) => e.status === "SATISFIED" || (e.evidence_links && e.evidence_links.length > 0)
          ).length;

          return (
            <div key={categoryKey} className="pt-2 first:pt-0">
              {/* Category Header */}
              <button
                type="button"
                onClick={() => toggleCategory(categoryKey)}
                className="flex w-full items-center justify-between px-2 py-1.5 text-left rounded-md hover:bg-slate-100/70 transition-colors"
              >
                <div className="flex items-center gap-1.5 min-w-0">
                  {isCollapsed ? (
                    <ChevronRight className="h-3.5 w-3.5 text-slate-400 shrink-0" />
                  ) : (
                    <ChevronDown className="h-3.5 w-3.5 text-slate-500 shrink-0" />
                  )}
                  <span className="text-xs font-bold text-slate-800 truncate">
                    {categoryTitle}
                  </span>
                </div>
                <span className="text-[10px] font-medium text-slate-400 shrink-0 ml-2">
                  {catSatisfied}/{catEntities.length}
                </span>
              </button>

              {/* Slot Items */}
              {!isCollapsed && (
                <div className="mt-1 space-y-0.5 pl-2">
                  {catEntities.map((entity) => {
                    const isSelected = activeSlotId === entity.slot_id;
                    const isSatisfied =
                      entity.status === "SATISFIED" ||
                      (entity.evidence_links && entity.evidence_links.length > 0);

                    return (
                      <button
                        key={entity.id}
                        type="button"
                        onClick={() => onSelectSlot(entity.slot_id)}
                        className={`group flex w-full items-start gap-2.5 rounded-lg px-2.5 py-2 text-left transition-all ${
                          isSelected
                            ? "bg-blue-50 text-blue-900 font-medium ring-1 ring-blue-600/30"
                            : "hover:bg-slate-100 text-slate-700"
                        }`}
                      >
                        {/* Status Icon Indicator */}
                        <div className="mt-0.5 shrink-0">
                          {isSatisfied ? (
                            <CheckCircle2 className="h-3.5 w-3.5 text-emerald-600" />
                          ) : entity.is_mandatory !== false ? (
                            <AlertCircle className="h-3.5 w-3.5 text-red-500" />
                          ) : (
                            <span className="h-3.5 w-3.5 rounded-full border border-slate-300 inline-block" />
                          )}
                        </div>

                        {/* Slot ID & Title */}
                        <div className="min-w-0 flex-1">
                          <div className="flex items-center gap-1.5">
                            <span className="font-mono text-[11px] font-bold text-slate-900">
                              {entity.slot_id}
                            </span>
                            {isSatisfied && (
                              <span className="rounded bg-emerald-100 px-1 py-0.2 text-[9px] font-bold text-emerald-800">
                                SATISFIED
                              </span>
                            )}
                            {!isSatisfied && entity.is_mandatory !== false && (
                              <span className="rounded bg-red-100 px-1 py-0.2 text-[9px] font-bold text-red-700">
                                MISSING
                              </span>
                            )}
                          </div>
                          <p className="text-[11px] text-slate-600 line-clamp-1 leading-snug mt-0.5">
                            {entity.slot_title}
                          </p>
                        </div>
                      </button>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
