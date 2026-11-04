"use client";

import React, { useState } from "react";
import {
  FileText,
  FileCheck2,
  Trash2,
  AlertCircle,
  Eye,
} from "lucide-react";
import { SubmissionEntity, EvidenceLink } from "@/types/regulatory";
import { useUnlinkEvidence } from "@/hooks/useEvidence";
import { FileUploadDropzone } from "./FileUploadDropzone";
import { PdfViewerModal } from "./PdfViewerModal";

interface SlotActionAreaProps {
  submissionId: string;
  entity: SubmissionEntity;
  onPreviewDocument?: (documentId: string) => void;
}

export function SlotActionArea({
  submissionId,
  entity,
  onPreviewDocument,
}: SlotActionAreaProps) {
  const unlinkEvidence = useUnlinkEvidence();
  const [previewLink, setPreviewLink] = useState<EvidenceLink | null>(null);

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

  const handleOpenPreview = (link: EvidenceLink) => {
    setPreviewLink(link);
    if (onPreviewDocument) {
      onPreviewDocument(link.evidence_document_id);
    }
  };

  return (
    <div className="rounded-2xl border border-slate-200 bg-white p-6 shadow-xs space-y-6">
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
      {hasDocuments && (
        <div className="space-y-3">
          <span className="text-xs font-bold uppercase tracking-wider text-slate-600 block">
            Attached Documents in Vault ({links.length})
          </span>
          <div className="space-y-2">
            {links.map((link) => {
              const doc = link.evidence_document;
              const title = link.document_title || doc?.document_title || "Statutory Evidence";
              const filename = link.original_filename || doc?.original_filename || "document.pdf";
              const sizeBytes = link.file_size_bytes || doc?.file_size_bytes || 0;
              const sizeKB = sizeBytes > 0 ? Math.round(sizeBytes / 1024) : 0;
              const pages = link.page_count || doc?.page_count || 1;

              return (
                <div
                  key={link.id}
                  className="flex items-center justify-between p-3.5 rounded-xl border border-slate-200 bg-slate-50/50 hover:bg-slate-50 transition-colors"
                >
                  <div
                    onClick={() => handleOpenPreview(link)}
                    className="flex items-center gap-3 min-w-0 cursor-pointer flex-1 mr-3 group"
                    title="Click to preview and verify document in browser"
                  >
                    <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-700 group-hover:bg-blue-600 group-hover:text-white transition-colors">
                      <FileText className="h-5 w-5" />
                    </div>
                    <div className="min-w-0">
                      <p className="text-xs font-bold text-slate-900 truncate group-hover:text-blue-600 transition-colors">
                        {title}
                      </p>
                      <div className="flex items-center gap-2 text-[11px] text-slate-500 mt-0.5">
                        <span className="font-mono text-slate-600 truncate">{filename}</span>
                        <span>•</span>
                        <span>{sizeKB} KB</span>
                        <span>•</span>
                        <span>{pages} {pages === 1 ? "page" : "pages"}</span>
                      </div>
                    </div>
                  </div>

                  <div className="flex items-center gap-2 shrink-0">
                    <button
                      type="button"
                      onClick={() => handleOpenPreview(link)}
                      className="inline-flex items-center gap-1.5 rounded-lg border border-slate-200 bg-white px-2.5 py-1.5 text-xs font-semibold text-slate-700 hover:border-blue-300 hover:bg-blue-50/60 hover:text-blue-700 transition-colors shadow-2xs"
                      title="Verify document in browser without downloading"
                    >
                      <Eye className="h-3.5 w-3.5" />
                      <span>Verify</span>
                    </button>

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
      )}

      {/* File Upload & Ingestion Dropzone */}
      <div className="space-y-2 pt-2 border-t border-slate-100">
        <span className="text-xs font-bold uppercase tracking-wider text-slate-600 block">
          {hasDocuments ? "Attach Additional Statutory File" : "Upload Statutory Evidence File"}
        </span>
        <FileUploadDropzone
          submissionId={submissionId}
          entity={entity}
        />
      </div>

      {/* In-Browser PDF.js Viewer Modal */}
      {previewLink && (
        <PdfViewerModal
          isOpen={!!previewLink}
          onClose={() => setPreviewLink(null)}
          documentId={previewLink.evidence_document_id}
          documentTitle={
            previewLink.document_title ||
            previewLink.evidence_document?.document_title ||
            "Statutory Evidence"
          }
          originalFilename={
            previewLink.original_filename ||
            previewLink.evidence_document?.original_filename
          }
          fileSizeBytes={
            previewLink.file_size_bytes ||
            previewLink.evidence_document?.file_size_bytes
          }
          pageCount={
            previewLink.page_count ||
            previewLink.evidence_document?.page_count
          }
          sha256={
            (previewLink.extracted_metadata?.sha256 as string) ||
            (previewLink.evidence_document?.extracted_metadata?.sha256 as string)
          }
          slotId={entity.slot_id}
        />
      )}
    </div>
  );
}
