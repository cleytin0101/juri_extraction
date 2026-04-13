import { Scale, Users, Calendar, DollarSign, Loader2, CheckCircle2, XCircle, TrendingUp, Search, Filter } from "lucide-react";
import { MetricCard } from "../components/metrics/MetricCard";
import { FunnelChart } from "../components/metrics/FunnelChart";
import { BarChart } from "../components/metrics/BarChart";
import { DonutChart } from "../components/metrics/DonutChart";
import { LeadTable } from "../components/leads/LeadTable";
import { useMetrics } from "../hooks/useMetrics";
import { useExtrairStatus } from "../hooks/useExtraction";
import type { ExtrairJobStatus } from "../types/pauta";
import { SparklesCore } from "@/components/ui/sparkles";

function fmtBRL(v: number) {
  if (v >= 1_000_000) return `R$ ${(v / 1_000_000).toFixed(1)}M`;
  if (v >= 1_000) return `R$ ${(v / 1_000).toFixed(0)}K`;
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}

function JobStatusIcon({ status }: { status: ExtrairJobStatus["status"] }) {
  if (status === "running") return <Loader2 size={14} className="animate-spin text-accent-blue" />;
  if (status === "done") return <CheckCircle2 size={14} className="text-accent-green" />;
  return <XCircle size={14} className="text-accent-red" />;
}

export function Dashboard() {
  const { data, isLoading } = useMetrics();
  const { data: jobs } = useExtrairStatus();

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
              <div className="text-xs text-slate-400">PJe TRT-7 — Dados atualizados em tempo real</div>
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
            label="Processos Hoje"
            value={isLoading ? "—" : data?.processos_hoje ?? 0}
            icon={<Calendar size={20} />}
            className="bg-surface-800/40 border-white/5 hover:border-indigo-500/50 transition-all duration-300"
          />
          <MetricCard
            label="Leads Capturados"
            value={isLoading ? "—" : data?.leads_capturados ?? 0}
            icon={<Users size={20} />}
            className="bg-surface-800/40 border-white/5 hover:border-indigo-500/50 transition-all duration-300"
          />
          <MetricCard
            label="Audiências Encontradas"
            value={isLoading ? "—" : data?.audiencias_encontradas ?? 0}
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

        {/* Extrações Recentes */}
        {jobs && jobs.length > 0 && (
          <div className="bg-surface-800/40 border border-white/5 rounded-2xl p-8 shadow-xl">
            <div className="flex items-center justify-between mb-6">
              <div>
                <h3 className="text-white font-bold text-lg">Extrações Recentes</h3>
                <p className="text-xs text-slate-500 mt-1">Status das últimas pautas processadas pelo agente</p>
              </div>
              <button className="text-xs font-semibold text-indigo-400 hover:text-indigo-300 transition-colors">Ver histórico completo</button>
            </div>
            
            <div className="space-y-3">
              {jobs.map((job) => (
                <div
                  key={job.key}
                  className="group flex items-center justify-between bg-white/5 hover:bg-white/10 border border-transparent hover:border-white/10 rounded-xl px-5 py-4 transition-all duration-200"
                >
                  <div className="flex items-center gap-4 min-w-0">
                    <div className={cn(
                      "p-2 rounded-lg",
                      job.status === "done" ? "bg-accent-green/10" : job.status === "running" ? "bg-accent-blue/10" : "bg-accent-red/10"
                    )}>
                      <JobStatusIcon status={job.status} />
                    </div>
                    <div>
                      <span className="text-sm font-medium text-white block truncate">{job.vara_nome || job.vara_id}</span>
                      <span className="text-xs text-slate-500 font-mono mt-0.5">{job.data}</span>
                    </div>
                  </div>
                  
                  <div className="flex items-center gap-6 shrink-0 ml-4 text-xs">
                    {job.status === "running" ? (
                      <div className="flex items-center gap-2">
                        <div className="h-1.5 w-24 bg-surface-700 rounded-full overflow-hidden">
                          <div className="h-full bg-accent-blue animate-progress w-2/3"></div>
                        </div>
                        <span className="text-accent-blue font-semibold animate-pulse">Em andamento...</span>
                      </div>
                    ) : job.status === "error" ? (
                      <span className="text-accent-red font-semibold bg-accent-red/10 px-2 py-1 rounded">Erro no processamento</span>
                    ) : (
                      <div className="flex items-center gap-6">
                        <div className="flex flex-col items-end">
                          <span className="text-white font-bold">{job.processos_encontrados}</span>
                          <span className="text-[10px] text-slate-500 uppercase tracking-tighter">Processos</span>
                        </div>
                        <div className="flex flex-col items-end">
                          <span className="text-white font-bold">{job.leads_criados}</span>
                          <span className="text-[10px] text-slate-500 uppercase tracking-tighter">Leads</span>
                        </div>
                        {job.processos_com_advogado > 0 && (
                          <div className="flex flex-col items-end">
                            <span className="text-red-400 font-bold">{job.processos_com_advogado}</span>
                            <span className="text-[10px] text-red-400/50 uppercase tracking-tighter">C/ Adv.</span>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

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
