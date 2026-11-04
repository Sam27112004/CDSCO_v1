import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import {
  Submission,
  DeviceCategory,
  FilingModality,
  RiskClass,
  RegulatoryContext,
} from "@/types/regulatory";

export interface CreateSubmissionInput {
  pathway_code: string;
  filing_modality: FilingModality;
  device_category: DeviceCategory;
  risk_class: RiskClass;
  device_family_name?: string;
  regulatory_context: RegulatoryContext;
  applicant_profile_id?: string;
  manufacturer_profile_id?: string;
  site_profile_id?: string;
}

export function useSubmissions() {
  return useQuery<Submission[], Error>({
    queryKey: ["submissions"],
    queryFn: () => apiClient.get<Submission[]>("/submissions"),
  });
}

export function useSubmission(submissionId?: string) {
  return useQuery<Submission, Error>({
    queryKey: ["submission", submissionId],
    queryFn: () => apiClient.get<Submission>(`/submissions/${submissionId}`),
    enabled: Boolean(submissionId),
  });
}

export function useCreateSubmission() {
  const queryClient = useQueryClient();

  return useMutation<Submission, Error, CreateSubmissionInput>({
    mutationFn: (newSubmission) =>
      apiClient.post<Submission>("/submissions", newSubmission),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submissions"] });
    },
  });
}

export function useDeleteSubmission() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, string>({
    mutationFn: (submissionId: string) =>
      apiClient.delete<void>(`/submissions/${submissionId}`),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["submissions"] });
    },
  });
}
