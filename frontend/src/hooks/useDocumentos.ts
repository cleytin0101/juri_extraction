import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { uploadDocumentos, enviarLote, fetchUploadHistorico } from "../api/documentos";
import type { LoteRequest } from "../types/documento";

export function useUploadDocumentos() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({ files, responsavel }: { files: File[]; responsavel: string }) =>
      uploadDocumentos(files, responsavel),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["metrics"] });
      queryClient.invalidateQueries({ queryKey: ["upload-historico"] });
    },
  });
}

export function useUploadHistorico(page = 1) {
  return useQuery({
    queryKey: ["upload-historico", page],
    queryFn: () => fetchUploadHistorico(page),
    staleTime: 30_000,
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
