import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";

export interface Profile {
  id: string;
  profile_type: "INDIAN_AGENT" | "FOREIGN_MANUFACTURER" | "MANUFACTURING_SITE" | "DOMESTIC_MANUFACTURER";
  name: string;
  data_payload: Record<string, unknown>;
  created_at: string;
}

export function useProfiles(profileType?: string) {
  return useQuery<Profile[], Error>({
    queryKey: ["profiles", profileType || "ALL"],
    queryFn: () => {
      const params = profileType ? { profile_type: profileType } : undefined;
      return apiClient.get<Profile[]>("/profiles", params);
    },
    staleTime: 1000 * 60 * 10, // 10 minutes cache
  });
}
