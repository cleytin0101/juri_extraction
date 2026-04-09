import client from "./client";
import type { PautasResponse, ExtrairRequest, ExtrairResponse, ExtrairJobStatus } from "../types/pauta";

export async function fetchPautas(): Promise<PautasResponse> {
  const { data } = await client.get<PautasResponse>("/pautas");
  return data;
}

export async function extrairPauta(req: ExtrairRequest): Promise<ExtrairResponse> {
  const { data } = await client.post<ExtrairResponse>("/extrair", req);
  return data;
}

export async function fetchExtrairStatus(): Promise<ExtrairJobStatus[]> {
  const { data } = await client.get<ExtrairJobStatus[]>("/extrair/status");
  return data;
}
