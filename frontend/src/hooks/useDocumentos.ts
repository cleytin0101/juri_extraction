import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { uploadDocumentosStreaming, enviarLote, fetchUploadHistorico } from "../api/documentos";
import type { DocumentoProcessado, LoteRequest } from "../types/documento";

export function useUploadDocumentos() {
  const queryClient = useQueryClient();
  const [isPending, setIsPending] = useState(false);
  const [isError, setIsError] = useState(false);

  const mutateAsync = async ({
    files,
    responsavel,
    onResult,
  }: {
    files: File[];
    responsavel: string;
    onResult: (doc: DocumentoProcessado) => void;
  }) => {
    setIsPending(true);
    setIsError(false);
    try {
      await uploadDocumentosStreaming(files, responsavel, onResult);
      queryClient.invalidateQueries({ queryKey: ["leads"] });
      queryClient.invalidateQueries({ queryKey: ["metrics"] });
      queryClient.invalidateQueries({ queryKey: ["upload-historico"] });
    } catch (e) {
      setIsError(true);
      throw e;
    } finally {
      setIsPending(false);
    }
  };

  return { mutateAsync, isPending, isError };
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
