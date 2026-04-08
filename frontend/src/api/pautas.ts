import client from "./client";
import type { PautasResponse, ExtrairRequest, ExtrairResponse } from "../types/pauta";

export async function fetchPautas(): Promise<PautasResponse> {
  const { data } = await client.get<PautasResponse>("/pautas");
  return data;
}

export async function extrairPauta(req: ExtrairRequest): Promise<ExtrairResponse> {
  const { data } = await client.post<ExtrairResponse>("/extrair", req);
  return data;
}
