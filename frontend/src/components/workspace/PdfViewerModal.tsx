"use client";

import React, { useState, useEffect } from "react";
import {
  X,
  ExternalLink,
  Download,
  Maximize2,
  Minimize2,
  Copy,
  Check,
  Loader2,
  ShieldCheck,
  FileText,
} from "lucide-react";

export interface PdfViewerModalProps {
  isOpen: boolean;
  onClose: () => void;
  documentId: string;
  documentTitle: string;
  originalFilename?: string;
  fileSizeBytes?: number;
  pageCount?: number;
  sha256?: string;
  slotId?: string;
}

export function PdfViewerModal({
  isOpen,
  onClose,
  documentId,
  documentTitle,
  originalFilename,
  fileSizeBytes,
  pageCount,
  sha256,
  slotId,
}: PdfViewerModalProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);
  const [isLoadingStream, setIsLoadingStream] = useState(true);
  const [hasCopiedHash, setHasCopiedHash] = useState(false);

  // Lock body scroll and listen for Escape key
  useEffect(() => {
    if (!isOpen) return;

    setIsLoadingStream(true);
    setHasCopiedHash(false);

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    const originalOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    return () => {
      window.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = originalOverflow;
    };
  }, [isOpen, onClose, documentId]);

  if (!isOpen) return null;

  const streamUrl = `/api/v1/evidence/${documentId}/stream`;

  const copySha256 = () => {
    if (!sha256) return;
    navigator.clipboard.writeText(sha256);
    setHasCopiedHash(true);
    setTimeout(() => setHasCopiedHash(false), 2000);
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes || bytes <= 0) return "Unknown size";
    if (bytes >= 1024 * 1024) {
      return `${(bytes / (1024 * 1024)).toFixed(2)} MB`;
    }
    return `${Math.round(bytes / 1024)} KB`;
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-2 sm:p-4 md:p-6 bg-slate-950/70 backdrop-blur-xs"
      onClick={(e) => {
        if (e.target === e.currentTarget) onClose();
      }}
    >
      <div
        className={`relative flex flex-col bg-white shadow-2xl border border-slate-200 transition-all duration-200 overflow-hidden ${
          isFullscreen
            ? "fixed inset-0 w-screen h-screen rounded-none z-50"
            : "w-full max-w-6xl h-[90vh] rounded-2xl"
        }`}
      >
        {/* Top Verification Header */}
        <header className="shrink-0 flex items-center justify-between border-b border-slate-200 bg-slate-50/90 px-4 sm:px-6 py-3">
          {/* Document and Statutory Identity */}
          <div className="flex items-center gap-3 min-w-0 pr-4">
            <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-blue-100 text-blue-700">
              <FileText className="h-5 w-5" />
            </div>

            <div className="min-w-0">
              <div className="flex items-center gap-2 flex-wrap">
                {slotId && (
                  <span className="rounded-md bg-blue-600 px-2 py-0.5 text-[11px] font-bold text-white uppercase tracking-wider">
                    Slot {slotId}
                  </span>
                )}
                <h2 className="text-sm font-bold text-slate-900 truncate max-w-md">
                  {documentTitle}
                </h2>
                <span className="inline-flex items-center gap-1 rounded-full bg-emerald-100 px-2 py-0.5 text-[11px] font-semibold text-emerald-800">
                  <ShieldCheck className="h-3 w-3" />
                  Pre-flight Verified
                </span>
              </div>

              {/* Document Meta Row */}
              <div className="flex items-center gap-2.5 text-[11px] text-slate-500 mt-1 flex-wrap">
                <span className="font-mono text-slate-700 truncate max-w-[180px]">
                  {originalFilename || "document.pdf"}
                </span>
                <span>•</span>
                <span>{formatFileSize(fileSizeBytes)}</span>
                <span>•</span>
                <span>
                  {pageCount || 1} {pageCount === 1 ? "page" : "pages"}
                </span>

                {sha256 && (
                  <>
                    <span>•</span>
                    <button
                      type="button"
                      onClick={copySha256}
                      className="inline-flex items-center gap-1 font-mono text-[10px] bg-slate-200/80 hover:bg-slate-200 text-slate-700 px-2 py-0.5 rounded transition-colors"
                      title={`Full SHA-256: ${sha256} (Click to copy)`}
                    >
                      <span>SHA-256: {sha256.substring(0, 8)}...</span>
                      {hasCopiedHash ? (
                        <Check className="h-3 w-3 text-emerald-600" />
                      ) : (
                        <Copy className="h-3 w-3 text-slate-500" />
                      )}
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>

          {/* Quick Action Buttons */}
          <div className="flex items-center gap-1.5 shrink-0">
            {/* Fullscreen Toggle */}
            <button
              type="button"
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="rounded-lg p-2 text-slate-500 hover:text-slate-800 hover:bg-slate-200/60 transition-colors"
              title={isFullscreen ? "Exit Fullscreen" : "Fullscreen"}
            >
              {isFullscreen ? (
                <Minimize2 className="h-4 w-4" />
              ) : (
                <Maximize2 className="h-4 w-4" />
              )}
            </button>

            {/* Open in New Window */}
            <a
              href={streamUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="rounded-lg p-2 text-slate-500 hover:text-blue-600 hover:bg-slate-200/60 transition-colors"
              title="Open stream in dedicated browser window"
            >
              <ExternalLink className="h-4 w-4" />
            </a>

            {/* Direct Download */}
            <a
              href={streamUrl}
              download={originalFilename || "statutory_document.pdf"}
              className="rounded-lg p-2 text-slate-500 hover:text-blue-600 hover:bg-slate-200/60 transition-colors"
              title="Download statutory PDF"
            >
              <Download className="h-4 w-4" />
            </a>

            <div className="h-5 w-px bg-slate-300 mx-1" />

            {/* Close Button */}
            <button
              type="button"
              onClick={onClose}
              className="rounded-lg p-2 text-slate-500 hover:text-red-600 hover:bg-red-50 transition-colors"
              title="Close viewer (Esc)"
            >
              <X className="h-5 w-5" />
            </button>
          </div>
        </header>

        {/* Viewer Viewport Container */}
        <div className="relative flex-1 w-full h-full bg-slate-100 overflow-hidden">
          {/* Loading Indicator */}
          {isLoadingStream && (
            <div className="absolute inset-0 z-10 flex flex-col items-center justify-center bg-slate-100/90 gap-3">
              <Loader2 className="h-8 w-8 animate-spin text-blue-600" />
              <div className="text-center">
                <p className="text-xs font-semibold text-slate-800">
                  Streaming statutory PDF document...
                </p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  RFC 7233 byte-range acceleration active
                </p>
              </div>
            </div>
          )}

          {/* Embedded PDF Stream */}
          <iframe
            src={`${streamUrl}#toolbar=1&navpanes=1&view=FitH`}
            onLoad={() => setIsLoadingStream(false)}
            className="w-full h-full border-0"
            title={`PDF Viewer - ${documentTitle}`}
          />
        </div>

        {/* Bottom Verification Footer */}
        <footer className="shrink-0 flex items-center justify-between border-t border-slate-200 bg-white px-4 py-2 text-[11px] text-slate-500">
          <div className="flex items-center gap-2">
            <span className="h-2 w-2 rounded-full bg-emerald-500" />
            <span>Vault Stream: Online (HTTP 206 Partial Content Supported)</span>
          </div>

          <div className="flex items-center gap-3">
            <span>Press <kbd className="rounded border border-slate-300 bg-slate-100 px-1.5 py-0.5 font-mono text-[10px]">Esc</kbd> to exit</span>
            <span>•</span>
            <a
              href={streamUrl}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 hover:underline font-medium"
            >
              Open raw stream
            </a>
          </div>
        </footer>
      </div>
    </div>
  );
}
