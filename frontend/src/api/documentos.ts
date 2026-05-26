import client from "./client";
import type { DocumentoProcessado, LoteRequest, LoteResult, UploadHistoricoResponse } from "../types/documento";

const API_BASE = import.meta.env.VITE_API_URL
  ? `${import.meta.env.VITE_API_URL}/api`
  : "/api";

export async function uploadDocumentosStreaming(
  files: File[],
  responsavel: string,
  onResult: (doc: DocumentoProcessado) => void
): Promise<void> {
  const form = new FormData();
  for (const file of files) {
    const safeName = file.name
      .normalize("NFD")
      .replace(/[̀-ͯ]/g, "")
      .replace(/[^\w.\- ]/g, "_");
    form.append("files", file, safeName);
  }
  form.append("responsavel", responsavel);

  const response = await fetch(`${API_BASE}/documentos/upload`, {
    method: "POST",
    body: form,
  });

  if (!response.ok) {
    const filename = files[0]?.name ?? "documento.pdf";
    onResult({
      filename,
      status: "erro",
      erro_msg: `Erro ao enviar arquivo (HTTP ${response.status})`,
      numero_processo: null,
      empresa_nome: null,
      empresa_cnpj: null,
      reclamante_nome: null,
      telefone: null,
      telefone_fonte: null,
      valor_causa: null,
      resumo_caso: null,
      tem_advogado: false,
      lead_id: null,
    } as DocumentoProcessado);
    return;
  }

  const reader = response.body!.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n");
    buffer = lines.pop() ?? "";
    for (const line of lines) {
      if (!line.startsWith("data: ")) continue;
      const payload = line.slice(6).trim();
      if (payload === "[DONE]") return;
      try {
        onResult(JSON.parse(payload) as DocumentoProcessado);
      } catch {
        // ignora linhas malformadas
      }
    }
  }
}

export async function enviarLote(payload: LoteRequest): Promise<LoteResult> {
  const { data } = await client.post<LoteResult>("/leads/mensagem/lote", payload);
  return data;
}

export async function fetchUploadHistorico(page = 1): Promise<UploadHistoricoResponse> {
  const { data } = await client.get<UploadHistoricoResponse>("/documentos/uploads", { params: { page, page_size: 20 } });
  return data;
}
