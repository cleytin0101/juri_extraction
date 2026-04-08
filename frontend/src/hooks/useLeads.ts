import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { fetchLeads, updateLeadStatus, sendMensagem } from "../api/leads";
import type { LeadStatus } from "../types/lead";

export function useLeads(status?: string, page = 1, page_size = 20) {
  return useQuery({
    queryKey: ["leads", status, page, page_size],
    queryFn: () => fetchLeads({ status, page, page_size }),
    placeholderData: (prev) => prev,
    staleTime: 30_000,
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
