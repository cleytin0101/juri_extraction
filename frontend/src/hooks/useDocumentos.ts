import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { uploadDocumentosStreaming, enviarLote, fetchUploadHistorico } from "../api/documentos";
import type { DocumentoProcessado, LoteRequest } from "../types/documento";

const BATCH_SIZE = 1;

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
      for (let i = 0; i < files.length; i += BATCH_SIZE) {
        const batch = files.slice(i, i + BATCH_SIZE);
        await uploadDocumentosStreaming(batch, responsavel, onResult);
        if (i + BATCH_SIZE < files.length) {
          await new Promise(r => setTimeout(r, 1500));
        }
      }
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
