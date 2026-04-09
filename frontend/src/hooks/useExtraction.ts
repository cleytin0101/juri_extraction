import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { extrairPauta, fetchPautas, fetchExtrairStatus } from "../api/pautas";
import type { ExtrairRequest } from "../types/pauta";

export function usePautas() {
  return useQuery({
    queryKey: ["pautas"],
    queryFn: fetchPautas,
    staleTime: 60_000,
  });
}

export function useExtraction() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (req: ExtrairRequest) => extrairPauta(req),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["metrics"] });
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["extrair-status"] });
    },
  });
}

export function useExtrairStatus() {
  return useQuery({
    queryKey: ["extrair-status"],
    queryFn: fetchExtrairStatus,
    // Poll every 5s while any job is running
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.some((j) => j.status === "running")) return 5_000;
      return 30_000;
    },
  });
}
