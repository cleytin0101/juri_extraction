import { useMutation, useQueryClient } from "@tanstack/react-query";
import { uploadDocumentos, enviarLote } from "../api/documentos";
import type { LoteRequest } from "../types/documento";

export function useUploadDocumentos() {
  return useMutation({
    mutationFn: (files: File[]) => uploadDocumentos(files),
  });
}

export function useEnviarLote() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (payload: LoteRequest) => enviarLote(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["metrics"] });
    },
  });
}
