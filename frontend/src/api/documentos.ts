import client from "./client";
import type { DocumentoProcessado, LoteRequest, LoteResult, UploadBatch, UploadHistoricoResponse } from "../types/documento";

export async function uploadDocumentos(files: File[], responsavel: string): Promise<DocumentoProcessado[]> {
  const form = new FormData();
  for (const file of files) {
    form.append("files", file);
  }
  form.append("responsavel", responsavel);
  const { data } = await client.post<DocumentoProcessado[]>("/documentos/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    timeout: 600_000,
  });
  return data;
}

export async function enviarLote(payload: LoteRequest): Promise<LoteResult> {
  const { data } = await client.post<LoteResult>("/leads/mensagem/lote", payload);
  return data;
}

export async function fetchUploadHistorico(page = 1): Promise<UploadHistoricoResponse> {
  const { data } = await client.get<UploadHistoricoResponse>("/documentos/uploads", { params: { page, page_size: 20 } });
  return data;
}
