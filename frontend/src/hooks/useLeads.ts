import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchLeads, updateLeadStatus, sendMensagem, deleteLead } from "../api/leads";
import { enviarLote } from "../api/documentos";
import type { LeadStatus } from "../types/lead";

export function useLeads(
  status?: string,
  page = 1,
  page_size = 20,
  valor_min?: number,
  valor_max?: number,
  data_audiencia_de?: string,
  data_audiencia_ate?: string,
) {
  return useQuery({
    queryKey: ["leads", status, page, page_size, valor_min, valor_max, data_audiencia_de, data_audiencia_ate],
    queryFn: () => fetchLeads({ status, page, page_size, valor_min, valor_max, data_audiencia_de, data_audiencia_ate }),
    placeholderData: (prev) => prev,
    staleTime: 30_000,
  });
}

export function useSendLote() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (leadIds: string[]) => enviarLote({ lead_ids: leadIds }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    },
  });
}

export function useUpdateLeadStatus() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ leadId, status }: { leadId: string; status: LeadStatus }) =>
      updateLeadStatus(leadId, status),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    },
  });
}

export function useSendMensagem() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ leadId, telefone }: { leadId: string; telefone?: string }) =>
      sendMensagem(leadId, telefone),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    },
  });
}

export function useDeleteLead() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (leadId: string) => deleteLead(leadId),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["metrics"] });
    },
  });
}
