import client from "./client";
import type { LeadListResponse, LeadStatus } from "../types/lead";

export async function fetchLeads(params: {
  status?: string;
  page?: number;
  page_size?: number;
  valor_min?: number;
  valor_max?: number;
  data_audiencia_de?: string;
  data_audiencia_ate?: string;
}): Promise<LeadListResponse> {
  const { data } = await client.get<LeadListResponse>("/leads", { params });
  return data;
}

export async function updateLeadStatus(leadId: string, status: LeadStatus) {
  const { data } = await client.patch(`/leads/${leadId}/status`, { status });
  return data;
}

export async function sendMensagem(leadId: string, telefone?: string) {
  const { data } = await client.post(`/leads/${leadId}/mensagem`, {
    telefone_override: telefone || null,
  });
  return data;
}

export async function deleteLead(leadId: string): Promise<void> {
  await client.delete(`/leads/${leadId}`);
}
