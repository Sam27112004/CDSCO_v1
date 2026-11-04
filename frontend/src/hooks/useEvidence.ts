import { useMutation, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { EvidenceDocument, EvidenceLink } from "@/types/regulatory";

export interface UploadEvidenceParams {
  submissionId: string;
  file: File;
  documentTitle?: string;
}

export interface LinkEvidenceParams {
  submissionId: string;
  evidenceDocumentId: string;
  submissionEntityId: string;
  dossierChapter?: string;
}

export interface UnlinkEvidenceParams {
  submissionId: string;
  linkId: string;
}

export function useUploadEvidence() {
  const queryClient = useQueryClient();

  return useMutation<EvidenceDocument, Error, UploadEvidenceParams>({
    mutationFn: async ({ submissionId, file, documentTitle }) => {
      const formData = new FormData();
      formData.append("file", file);
      if (documentTitle) {
        formData.append("document_title", documentTitle);
      }
      return apiClient.upload<EvidenceDocument>(
        `/submissions/${submissionId}/evidence/upload`,
        formData
      );
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["submission", variables.submissionId],
      });
      queryClient.invalidateQueries({
        queryKey: ["evidence", variables.submissionId],
      });
    },
  });
}

export function useLinkEvidence() {
  const queryClient = useQueryClient();

  return useMutation<EvidenceLink, Error, LinkEvidenceParams>({
    mutationFn: async ({
      submissionId,
      evidenceDocumentId,
      submissionEntityId,
      dossierChapter,
    }) => {
      return apiClient.post<EvidenceLink>(
        `/submissions/${submissionId}/evidence/link`,
        {
          evidence_document_id: evidenceDocumentId,
          submission_entity_id: submissionEntityId,
          dossier_chapter: dossierChapter,
        }
      );
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["submission", variables.submissionId],
      });
    },
  });
}

export function useUnlinkEvidence() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, UnlinkEvidenceParams>({
    mutationFn: async ({ submissionId, linkId }) => {
      return apiClient.delete<void>(
        `/submissions/${submissionId}/evidence/links/${linkId}`
      );
    },
    onSuccess: (_, variables) => {
      queryClient.invalidateQueries({
        queryKey: ["submission", variables.submissionId],
      });
    },
  });
}
