"use client";

import React, { useState, useRef, DragEvent, ChangeEvent } from "react";
import {
  UploadCloud,
  AlertTriangle,
  FileText,
  X,
  Loader2,
  CheckCircle2,
} from "lucide-react";
import { useUploadEvidence, useLinkEvidence } from "@/hooks/useEvidence";
import { SubmissionEntity } from "@/types/regulatory";

interface FileUploadDropzoneProps {
  submissionId: string;
  entity: SubmissionEntity;
  onUploadComplete?: () => void;
}

const MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024; // 10.0 MB CDSCO ceiling

export function FileUploadDropzone({
  submissionId,
  entity,
  onUploadComplete,
}: FileUploadDropzoneProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadEvidence = useUploadEvidence();
  const linkEvidence = useLinkEvidence();

  const [isDragOver, setIsDragOver] = useState(false);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [documentTitle, setDocumentTitle] = useState("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [uploadPhase, setUploadPhase] = useState<string>("");
  const [isSuccess, setIsSuccess] = useState(false);

  const isProcessing = uploadEvidence.isPending || linkEvidence.isPending;

  const validateAndSetFile = (file: File) => {
    setErrorMessage(null);
    setIsSuccess(false);

    // Validate size
    if (file.size > MAX_FILE_SIZE_BYTES) {
      const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
      setErrorMessage(
        `File size (${sizeMB} MB) exceeds maximum CDSCO portal limit of 10.0 MB.`
      );
      return;
    }

    if (file.size === 0) {
      setErrorMessage("Selected file is empty (0 bytes).");
      return;
    }

    // Validate extension
    const ext = "." + file.name.split(".").pop()?.toLowerCase();
    const validExts = [
      ".pdf",
      ".docx",
      ".jpg",
      ".jpeg",
      ".png",
      ".webp",
      ".tiff",
      ".tif",
      ".bmp",
    ];

    if (!validExts.includes(ext)) {
      setErrorMessage(
        `Unsupported format '${ext}'. Permitted formats: PDF (.pdf), Word (.docx), or Images (.jpg, .png).`
      );
      return;
    }

    setSelectedFile(file);
    // Default document title to entity slot title or filename stem
    const baseName = file.name.replace(/\.[^/.]+$/, "");
    setDocumentTitle(baseName || entity.slot_title);
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragOver(false);

    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      const file = e.dataTransfer.files[0];
      validateAndSetFile(file);
    }
  };

  const handleFileInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files.length > 0) {
      const file = e.target.files[0];
      validateAndSetFile(file);
    }
  };

  const handleUploadAndLink = async () => {
    if (!selectedFile) return;

    setErrorMessage(null);
    setIsSuccess(false);

    try {
      // Step 1: Uploading binary
      setUploadProgress(35);
      setUploadPhase("Uploading and verifying binary...");
      const uploadedDoc = await uploadEvidence.mutateAsync({
        submissionId,
        file: selectedFile,
        documentTitle: documentTitle.trim() || undefined,
      });

      // Step 2: PyMuPDF verification & conversion
      setUploadProgress(70);
      setUploadPhase("Running pre-flight inspection & checksums...");

      // Step 3: Link document to active slot entity
      setUploadProgress(90);
      setUploadPhase(`Associating with Slot ${entity.slot_id}...`);
      await linkEvidence.mutateAsync({
        submissionId,
        evidenceDocumentId: uploadedDoc.id,
        submissionEntityId: entity.id,
        dossierChapter: entity.chapter,
      });

      setUploadProgress(100);
      setUploadPhase("Document satisfied and cataloged!");
      setIsSuccess(true);
      setSelectedFile(null);
      setDocumentTitle("");
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }

      if (onUploadComplete) {
        onUploadComplete();
      }
    } catch (err: unknown) {
      console.error("Upload error:", err);
      const msg =
        err instanceof Error ? err.message : "Failed to upload and link evidence document.";
      setErrorMessage(msg);
      setUploadProgress(0);
      setUploadPhase("");
    }
  };

  const clearSelectedFile = () => {
    setSelectedFile(null);
    setDocumentTitle("");
    setErrorMessage(null);
    setIsSuccess(false);
    setUploadProgress(0);
    setUploadPhase("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <div className="space-y-4">
      {/* Hidden Native File Input */}
      <input
        ref={fileInputRef}
        type="file"
        accept=".pdf,.docx,.jpg,.jpeg,.png,.webp,.tiff,.tif,.bmp"
        onChange={handleFileInputChange}
        className="hidden"
      />

      {/* Dropzone Box */}
      {!selectedFile && !isProcessing && (
        <div
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onDrop={handleDrop}
          onClick={() => fileInputRef.current?.click()}
          className={`cursor-pointer rounded-2xl border-2 border-dashed p-8 text-center transition-all ${
            isDragOver
              ? "border-blue-600 bg-blue-50/60 ring-2 ring-blue-600/30"
              : "border-slate-300 bg-slate-50/50 hover:border-blue-400 hover:bg-slate-50"
          }`}
        >
          <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-blue-100/70 text-blue-600 mb-3">
            <UploadCloud className="h-6 w-6" />
          </div>

          <p className="text-sm font-semibold text-slate-800">
            Drag & drop statutory evidence file here, or{" "}
            <span className="text-blue-600 hover:underline">browse files</span>
          </p>

          <p className="mt-1.5 text-xs text-slate-500 max-w-sm mx-auto">
            Supports PDF (.pdf), Word (.docx), and Scanned Images (.jpg, .png).
            Maximum allowable CDSCO portal ceiling: <strong>10.0 MB</strong>.
          </p>
        </div>
      )}

      {/* Selected File Card & Confirmation */}
      {selectedFile && !isProcessing && (
        <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-xs space-y-4">
          <div className="flex items-start justify-between gap-3">
            <div className="flex items-center gap-3 min-w-0">
              <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-blue-100 text-blue-700">
                <FileText className="h-5 w-5" />
              </div>
              <div className="min-w-0">
                <p className="text-xs font-bold text-slate-900 truncate">{selectedFile.name}</p>
                <p className="text-[11px] text-slate-500 mt-0.5">
                  {(selectedFile.size / 1024).toFixed(1)} KB • Ready for upload & linking
                </p>
              </div>
            </div>

            <button
              type="button"
              onClick={clearSelectedFile}
              className="rounded-lg p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 transition-colors"
              title="Remove selected file"
            >
              <X className="h-4 w-4" />
            </button>
          </div>

          {/* Document Title Input */}
          <div>
            <label className="block text-xs font-bold uppercase tracking-wider text-slate-700 mb-1">
              Document Title in Statutory Vault
            </label>
            <input
              type="text"
              value={documentTitle}
              onChange={(e) => setDocumentTitle(e.target.value)}
              placeholder="e.g. ISO 13485:2016 Certified Quality Manual"
              className="w-full rounded-lg border border-slate-300 px-3.5 py-2 text-xs text-slate-900 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>

          {/* Action Buttons */}
          <div className="flex items-center justify-end gap-2 pt-2 border-t border-slate-100">
            <button
              type="button"
              onClick={clearSelectedFile}
              className="rounded-lg border border-slate-200 bg-white px-3.5 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50"
            >
              Cancel
            </button>
            <button
              type="button"
              onClick={handleUploadAndLink}
              className="inline-flex items-center gap-1.5 rounded-lg bg-blue-600 px-4 py-1.5 text-xs font-semibold text-white shadow-xs hover:bg-blue-700 transition-colors"
            >
              <UploadCloud className="h-3.5 w-3.5" />
              <span>Upload & Link to Slot {entity.slot_id}</span>
            </button>
          </div>
        </div>
      )}

      {/* Uploading Progress Indicator */}
      {isProcessing && (
        <div className="rounded-2xl border border-blue-200 bg-blue-50/50 p-6 shadow-xs space-y-3">
          <div className="flex items-center justify-between text-xs">
            <div className="flex items-center gap-2 font-semibold text-blue-900">
              <Loader2 className="h-4 w-4 animate-spin text-blue-600" />
              <span>{uploadPhase || "Processing..."}</span>
            </div>
            <span className="font-mono font-bold text-blue-800">{uploadProgress}%</span>
          </div>

          <div className="h-2 w-full overflow-hidden rounded-full bg-blue-200/70">
            <div
              className="h-full rounded-full bg-blue-600 transition-all duration-300 ease-out"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {/* Success Notification */}
      {isSuccess && (
        <div className="rounded-xl border border-emerald-200 bg-emerald-50 p-4 flex items-center justify-between">
          <div className="flex items-center gap-2.5 text-emerald-900">
            <CheckCircle2 className="h-5 w-5 text-emerald-600 shrink-0" />
            <div>
              <p className="text-xs font-bold">Evidence Document Successfully Linked!</p>
              <p className="text-[11px] text-emerald-700">
                Slot {entity.slot_id} is now satisfied and cataloged in the submission vault.
              </p>
            </div>
          </div>
          <button
            type="button"
            onClick={() => setIsSuccess(false)}
            className="text-xs font-semibold text-emerald-800 hover:underline ml-4 shrink-0"
          >
            Upload Another
          </button>
        </div>
      )}

      {/* Error Notification */}
      {errorMessage && (
        <div className="rounded-xl border border-red-200 bg-red-50 p-4 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 text-red-600 shrink-0 mt-0.5" />
          <div className="flex-1">
            <p className="text-xs font-bold text-red-900">Upload Rejected</p>
            <p className="text-[11px] text-red-700 mt-0.5 leading-relaxed">{errorMessage}</p>
          </div>
          <button
            type="button"
            onClick={() => setErrorMessage(null)}
            className="rounded p-1 text-red-400 hover:text-red-700"
          >
            <X className="h-4 w-4" />
          </button>
        </div>
      )}
    </div>
  );
}
