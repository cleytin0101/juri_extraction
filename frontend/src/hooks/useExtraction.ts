import { useEffect, useRef } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { extrairPauta, fetchPautas, fetchExtrairStatus } from "../api/pautas";
import type { ExtrairRequest, ExtrairJobStatus } from "../types/pauta";

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
  const qc = useQueryClient();
  const prevRef = useRef<ExtrairJobStatus[]>();

  const query = useQuery({
    queryKey: ["extrair-status"],
    queryFn: fetchExtrairStatus,
    // Poll every 3s while running, 30s when idle
    refetchInterval: (query) => {
      const data = query.state.data;
      if (data?.some((j) => j.status === "running")) return 3_000;
      return 30_000;
    },
  });

  // Auto-refresh leads + metrics quando um job passa de "running" para "done"
  useEffect(() => {
    const prev = prevRef.current;
    const curr = query.data;
    if (prev && curr) {
      const justFinished = curr.some(
        (job) =>
          job.status === "done" &&
          prev.find((p) => p.key === job.key)?.status === "running"
      );
      if (justFinished) {
        qc.invalidateQueries({ queryKey: ["leads"] });
        qc.invalidateQueries({ queryKey: ["metrics"] });
      }
    }
    prevRef.current = curr;
  }, [query.data, qc]);

  return query;
}
