import client from "./client";
import type { LeadListResponse, LeadStatus } from "../types/lead";

export async function fetchLeads(params: {
  status?: string;
  page?: number;
  page_size?: number;
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
