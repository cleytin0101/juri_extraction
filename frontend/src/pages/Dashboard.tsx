import { Scale, Users, Calendar, DollarSign } from "lucide-react";
import { MetricCard } from "../components/metrics/MetricCard";
import { FunnelChart } from "../components/metrics/FunnelChart";
import { BarChart } from "../components/metrics/BarChart";
import { DonutChart } from "../components/metrics/DonutChart";
import { LeadTable } from "../components/leads/LeadTable";
import { useMetrics } from "../hooks/useMetrics";

function fmtBRL(v: number) {
  if (v >= 1_000_000) return `R$ ${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `R$ ${(v / 1_000).toFixed(0)}K`;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}

export function Dashboard() {
  const { data, isLoading } = useMetrics();

  return (
    <div className="min-h-screen bg-surface-900 text-white">
      {/* Top bar */}
      <div className="border-b border-surface-600 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Scale size={22} className="text-accent-blue" />
          <div>
            <div className="font-bold text-white">Agente Dashboard</div>
            <div className="text-xs text-gray-500">PJe TRT-7 — Leads Jurídicos</div>
          </div>
        </div>
        <div className="flex items-center gap-2 text-xs text-gray-500">
          <span className="w-2 h-2 rounded-full bg-accent-green animate-pulse" />
          Atualiza a cada 30s
        </div>
      </div>

      <div className="p-6 space-y-6">
        {/* Métricas principais */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            label="Processos Hoje"
            value={isLoading ? "—" : data?.processos_hoje ?? 0}
            icon={<Calendar size={16} />}
          />
          <MetricCard
            label="Leads Capturados"
            value={isLoading ? "—" : data?.leads_capturados ?? 0}
            icon={<Users size={16} />}
          />
          <MetricCard
            label="Audiências Encontradas"
            value={isLoading ? "—" : data?.audiencias_encontradas ?? 0}
            icon={<Scale size={16} />}
          />
          <MetricCard
            label="Valor Total em Jogo"
            value={isLoading ? "—" : fmtBRL(data?.valor_total ?? 0)}
            icon={<DollarSign size={16} />}
          />
        </div>

        {/* Funil + gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
          <div className="lg:col-span-1">
            <FunnelChart steps={data?.funnel ?? []} />
          </div>
          <div className="lg:col-span-1">
            <BarChart data={data?.audiencias_por_dia ?? []} />
          </div>
          <div className="lg:col-span-1">
            <DonutChart data={data?.tipos_audiencia ?? []} />
          </div>
        </div>

        {/* Tabela de leads */}
        <LeadTable />
      </div>
    </div>
  );
}
