import { api } from "./client";
import type { DocumentoProcessado, LoteRequest, LoteResult } from "../types/documento";

export async function uploadDocumentos(files: File[]): Promise<DocumentoProcessado[]> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  const { data } = await api.post<DocumentoProcessado[]>("/api/documentos/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 120_000,
  });
  return data;
}

export async function enviarLote(payload: LoteRequest): Promise<LoteResult> {
  const { data } = await api.post<LoteResult>("/api/leads/mensagem/lote", payload);
  return data;
}
