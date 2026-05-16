import { useQuery } from "@tanstack/react-query"
import { fetchLeads } from "@/api/leads"
import { EventManager, type LeadOption } from "@/components/ui/event-manager"

export default function Agenda() {
  const { data } = useQuery({
    queryKey: ["leads-agenda"],
    queryFn: () => fetchLeads({ page_size: 200 }),
  })

  const leads: LeadOption[] = (data?.items ?? []).map(l => ({
    id: l.lead_id,
    nome: l.empresa_nome ?? "—",
    processo: l.numero_processo ?? "—",
    cnpj: l.empresa_cnpj ?? undefined,
    valor_causa: l.valor_causa,
    data_audiencia: l.data_audiencia ?? undefined,
    orgao_julgador: l.orgao_julgador ?? undefined,
    reclamante_nome: l.reclamante_nome ?? undefined,
    resumo_caso: l.resumo_caso ?? undefined,
  }))

  return (
    <div className="min-h-screen bg-surface-900 p-6">
      <EventManager
        leads={leads}
        defaultView="month"
        categories={["Reunião", "Tarefa", "Lembrete", "Pessoal"]}
        availableTags={["Importante", "Urgente", "Trabalho", "Pessoal", "Equipe", "Cliente"]}
        className="max-w-7xl mx-auto"
      />
    </div>
  )
}
