import { Scale, Users, FileText, DollarSign, TrendingUp, Search, Filter } from "lucide-react";
import { MetricCard } from "../components/metrics/MetricCard";
import { FunnelChart } from "../components/metrics/FunnelChart";
import { BarChart } from "../components/metrics/BarChart";
import { DonutChart } from "../components/metrics/DonutChart";
import { LeadTable } from "../components/leads/LeadTable";
import { useMetrics } from "../hooks/useMetrics";
import { SparklesCore } from "@/components/ui/sparkles";

function fmtBRL(v: number) {
  if (v >= 1_000_000) return `R$ ${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `R$ ${(v / 1_000).toFixed(0)}K`;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}

export function Dashboard() {
  const { data, isLoading } = useMetrics();

  return (
    <div className="min-h-screen bg-[#020617] text-white selection:bg-indigo-500/30">
      {/* Hero Section with Sparkles */}
      <div className="relative h-[25rem] w-full bg-slate-950 flex flex-col items-center justify-center overflow-hidden border-b border-surface-600/50">
        <div className="w-full absolute inset-0 h-full">
          <SparklesCore
            id="tsparticlesfullpage"
            background="transparent"
            minSize={0.6}
            maxSize={1.4}
            particleDensity={100}
            className="w-full h-full"
            particleColor="#FFFFFF"
            speed={1}
          />
        </div>
        
        <div className="relative z-20 flex flex-col items-center">
          <h1 className="md:text-7xl text-5xl lg:text-8xl font-bold text-center text-white tracking-tighter">
            CD PJE
          </h1>
          <div className="w-[40rem] h-2 relative">
            {/* Gradients */}
            <div className="absolute inset-x-20 top-0 bg-gradient-to-r from-transparent via-indigo-500 to-transparent h-[2px] w-3/4 blur-sm" />
            <div className="absolute inset-x-20 top-0 bg-gradient-to-r from-transparent via-indigo-500 to-transparent h-px w-3/4" />
            <div className="absolute inset-x-60 top-0 bg-gradient-to-r from-transparent via-sky-500 to-transparent h-[5px] w-1/4 blur-sm" />
            <div className="absolute inset-x-60 top-0 bg-gradient-to-r from-transparent via-sky-500 to-transparent h-px w-1/4" />
          </div>
          <p className="mt-4 text-slate-400 text-sm md:text-base font-medium tracking-wide uppercase">
            Inteligência de Extração e Análise Jurídica
          </p>
        </div>

        {/* Radial Gradient to prevent sharp edges */}
        <div className="absolute inset-0 w-full h-full bg-slate-950 [mask-image:radial-gradient(50%_50%_at_50%_50%,transparent_0%,#020617_100%)] pointer-events-none"></div>
      </div>

      <div className="max-w-7xl mx-auto p-6 lg:p-10 space-y-10 relative -mt-10 z-30">
        {/* Status bar floating */}
        <div className="flex items-center justify-between bg-surface-800/80 backdrop-blur-md border border-white/5 rounded-2xl px-6 py-4 shadow-2xl">
          <div className="flex items-center gap-4">
            <div className="p-2 bg-accent-blue/10 rounded-lg">
              <TrendingUp size={20} className="text-accent-blue" />
            </div>
            <div>
              <div className="text-sm font-semibold text-white">Visão Geral do Sistema</div>
              <div className="text-xs text-slate-400">Leads gerados via upload de documentos — Dados em tempo real</div>
            </div>
          </div>
          <div className="flex items-center gap-2 text-xs font-medium text-accent-green bg-accent-green/10 px-3 py-1 rounded-full border border-accent-green/20">
            <span className="w-1.5 h-1.5 rounded-full bg-accent-green animate-pulse" />
            Sistema Online
          </div>
        </div>

        {/* Métricas principais */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            label="Processos Cadastrados"
            value={isLoading ? "—" : data?.audiencias_encontradas ?? 0}
            icon={<FileText size={20} />}
            className="bg-surface-800/40 border-white/5 hover:border-indigo-500/50 transition-all duration-300"
          />
          <MetricCard
            label="Leads Capturados"
            value={isLoading ? "—" : data?.leads_capturados ?? 0}
            icon={<Users size={20} />}
            className="bg-surface-800/40 border-white/5 hover:border-indigo-500/50 transition-all duration-300"
          />
          <MetricCard
            label="Mensagens Enviadas"
            value={isLoading ? "—" : (data?.funnel?.find(f => f.label === "Mensagens enviadas")?.value ?? 0)}
            icon={<Scale size={20} />}
            className="bg-surface-800/40 border-white/5 hover:border-indigo-500/50 transition-all duration-300"
          />
          <MetricCard
            label="Valor Total em Jogo"
            value={isLoading ? "—" : fmtBRL(data?.valor_total ?? 0)}
            icon={<DollarSign size={20} />}
            className="bg-surface-800/40 border-white/5 hover:border-indigo-500/50 transition-all duration-300"
          />
        </div>

        {/* Funil + gráficos */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-1 bg-surface-800/40 border border-white/5 rounded-2xl p-6 shadow-xl">
             <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-lg">Funil de Conversão</h3>
                <Filter size={16} className="text-slate-500" />
             </div>
            <FunnelChart steps={data?.funnel ?? []} />
          </div>
          <div className="lg:col-span-1 bg-surface-800/40 border border-white/5 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-lg">Audiências diárias</h3>
                <TrendingUp size={16} className="text-slate-500" />
             </div>
            <BarChart data={data?.audiencias_por_dia ?? []} />
          </div>
          <div className="lg:col-span-1 bg-surface-800/40 border border-white/5 rounded-2xl p-6 shadow-xl">
            <div className="flex items-center justify-between mb-6">
                <h3 className="font-bold text-lg">Distribuição</h3>
                <Search size={16} className="text-slate-500" />
             </div>
            <DonutChart data={data?.tipos_audiencia ?? []} />
          </div>
        </div>

        {/* Tabela de leads */}
        <div className="bg-surface-800/40 border border-white/5 rounded-2xl p-8 shadow-xl">
           <div className="mb-6 flex items-center justify-between">
              <div>
                <h3 className="text-white font-bold text-lg">Base de Leads</h3>
                <p className="text-xs text-slate-500 mt-1">Listagem detalhada de potenciais clientes extraídos</p>
              </div>
           </div>
           <LeadTable />
        </div>
      </div>
    </div>
  );
}
