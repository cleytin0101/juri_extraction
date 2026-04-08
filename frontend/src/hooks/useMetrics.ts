import { useQuery } from "@tanstack/react-query";
import { fetchMetrics } from "../api/metrics";

export function useMetrics() {
  return useQuery({
    queryKey: ["metrics"],
    queryFn: fetchMetrics,
    refetchInterval: 30_000,
    staleTime: 15_000,
  });
}
