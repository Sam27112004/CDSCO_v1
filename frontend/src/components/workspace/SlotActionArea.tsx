"use client";

import React from "react";
import {
  FileText,
  UploadCloud,
  FileCheck2,
  Trash2,
  AlertCircle,
} from "lucide-react";
import { SubmissionEntity } from "@/types/regulatory";
import { useUnlinkEvidence } from "@/hooks/useEvidence";

interface SlotActionAreaProps {
  submissionId: string;
  entity: SubmissionEntity;
}

export function SlotActionArea({
  submissionId,
  entity,
}: SlotActionAreaProps) {
  const unlinkEvidence = useUnlinkEvidence();
  const links = entity.evidence_links || [];
  const hasDocuments = links.length > 0;

  const handleUnlink = async (linkId: string) => {
    if (confirm("Are you sure you want to detach this document from this slot?")) {
      try {
        await unlinkEvidence.mutateAsync({
          submissionId,
          linkId,
        });
      } catch (err) {
        console.error("Failed to detach evidence link:", err);
      }
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-5">
      {/* Action Header */}
      <div className="flex items-center justify-between border-b border-slate-100 pb-4">
        <div>
          <h3 className="text-sm font-bold text-slate-900">
            Evidence Fulfillment & Document Association
          </h3>
          <p className="text-xs text-slate-500 mt-0.5">
            Satisfy this statutory requirement by attaching verified PDF, Word (.docx), or scanned image files.
          </p>
        </div>

        <div className="flex items-center gap-1.5">
          <span className="text-xs font-semibold text-slate-500">Status:</span>
          {hasDocuments ? (
            <span className="inline-flex items-center gap-1 rounded-full bg-emerald-50 px-2.5 py-0.5 text-xs font-bold text-emerald-700 border border-emerald-200">
              <FileCheck2 className="h-3.5 w-3.5" />
              Satisfied ({links.length} {links.length === 1 ? "file" : "files"})
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 rounded-full bg-red-50 px-2.5 py-0.5 text-xs font-bold text-red-700 border border-red-200">
              <AlertCircle className="h-3.5 w-3.5" />
              Missing Evidence
            </span>
          )}
        </div>
      </div>

      {/* Attached Documents List */}
      {hasDocuments ? (
        <div className="space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-600 block">
            Attached Documents in Vault
          </span>
          <div className="space-y-2">
            {links.map((link) => {
              const doc = link.evidence_document;
              const title = link.document_title || doc?.document_title || "Statutory Evidence";
              const filename = link.original_filename || doc?.original_filename || "document.pdf";
              const sizeKB = doc?.file_size_bytes ? Math.round(doc.file_size_bytes / 1024) : 0;
              const pages = doc?.page_count || 1;

              return (
                <div
                  key={link.id}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                >
                  <div className="flex items-center gap-3 min-w-0">
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-900 truncate">{title}</p>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                        <span className="font-mono text-slate-600 truncate">{filename}</span>
                        <span>•</span>
                        <span>{sizeKB} KB</span>
                        <span>•</span>
                        <span>{pages} {pages === 1 ? "page" : "pages"}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0 ml-4">
                    <button
                      type="button"
                      onClick={() => handleUnlink(link.id)}
                      disabled={unlinkEvidence.isPending}
                      className="rounded-lg p-1.5 text-slate-400 hover:text-red-600 hover:bg-red-50 transition-colors"
                      title="Detach document from slot"
                    >
                      <Trash2 className="h-4 w-4" />
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      ) : (
        /* Empty Slot Action Prompt */
        <div className="rounded-xl border border-dashed border-slate-300 bg-slate-50/50 p-6 text-center">
          <UploadCloud className="mx-auto h-8 w-8 text-slate-400 mb-2" />
          <h4 className="text-xs font-bold text-slate-800">
            No document attached to slot {entity.slot_id}
          </h4>
          <p className="text-xs text-slate-500 mt-1 max-w-sm mx-auto">
            Upload a compliant PDF, Word document, or high-resolution image scan satisfying this statutory requirement.
          </p>
        </div>
      )}
    </div>
  );
}
