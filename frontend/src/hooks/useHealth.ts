import { useQuery } from "@tanstack/react-query";
import { apiClient } from "@/lib/api-client";
import { HealthResponse } from "@/types/regulatory";

export function useHealth() {
  return useQuery<HealthResponse, Error>({
    queryKey: ["health"],
    queryFn: () => apiClient.get<HealthResponse>("/health"),
    refetchInterval: 30000, // Polling check every 30s
    retry: 2,
  });
}
