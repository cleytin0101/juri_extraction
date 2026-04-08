import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { extrairPauta, fetchPautas } from "../api/pautas";
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
    },
  });
}
