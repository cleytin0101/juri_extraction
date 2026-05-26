import { useRef, useState, useCallback } from "react";
import {
  Upload, FileText, CheckCircle2, XCircle, AlertTriangle,
  Send, Loader2, Phone, Building2, Hash, DollarSign, User,
  History, ChevronDown, ChevronRight,
} from "lucide-react";
import { useUploadDocumentos, useEnviarLote, useUploadHistorico } from "../hooks/useDocumentos";
import type { DocumentoProcessado, UploadBatch } from "../types/documento";
import { cn } from "@/lib/utils";

function fmtBRL(v: number | null) {
  if (v == null) return "—";
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v);
}

function fmtCNPJ(cnpj: string | null) {
  if (!cnpj) return "—";
  const d = cnpj.replace(/\D/g, "");
  if (d.length !== 14) return cnpj;
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`;
}

function StatusBadge({ status }: { status: DocumentoProcessado["status"] }) {
  const map = {
    criado: { label: "Lead criado", color: "bg-accent-green/10 text-accent-green border-accent-green/20" },
    ja_existe: { label: "Já existia", color: "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" },
    tem_advogado: { label: "Tem advogado", color: "bg-slate-500/10 text-slate-400 border-slate-500/20" },
    erro: { label: "Erro", color: "bg-accent-red/10 text-accent-red border-accent-red/20" },
  };
  const { label, color } = map[status];
  return (
    <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium border", color)}>
      {label}
    </span>
  );
}

function DropZone({ onFiles }: { onFiles: (files: File[]) => void }) {
  const [dragging, setDragging] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragging(false);
      const pdfs = Array.from(e.dataTransfer.files).filter(
        (f) => f.type === "application/pdf" || f.name.endsWith(".pdf")
      );
      if (pdfs.length) onFiles(pdfs);
    },
    [onFiles]
  );

  return (
    <div
      onDragOver={(e) => { e.preventDefault(); setDragging(true); }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
      onClick={() => inputRef.current?.click()}
      className={cn(
        "flex flex-col items-center justify-center gap-4 border-2 border-dashed rounded-2xl p-12 cursor-pointer transition-all duration-200",
        dragging
          ? "border-indigo-500 bg-indigo-500/10"
          : "border-white/10 bg-white/[0.02] hover:border-white/20 hover:bg-white/5"
      )}
    >
      <div className="p-4 bg-indigo-500/10 rounded-full">
        <Upload size={32} className="text-indigo-400" />
      </div>
      <div className="text-center">
        <p className="text-white font-semibold">Arraste os PDFs aqui ou clique para selecionar</p>
        <p className="text-slate-500 text-sm mt-1">Somente arquivos PDF do PJe — múltiplos arquivos suportados</p>
      </div>
      <input
        ref={inputRef}
        type="file"
        accept=".pdf,application/pdf"
        multiple
        className="hidden"
        onChange={(e) => {
          const files = Array.from(e.target.files || []);
          if (files.length) onFiles(files);
          e.target.value = "";
        }}
      />
    </div>
  );
}

const RESPONSAVEIS = ["Fernanda", "Vinícius", "Diego", "Cleyton"] as const;

const RESPONSAVEL_COLORS: Record<string, string> = {
  Fernanda: "bg-purple-500/20 text-purple-300 border-purple-500/30",
  "Vinícius": "bg-blue-500/20 text-blue-300 border-blue-500/30",
  Diego: "bg-amber-500/20 text-amber-300 border-amber-500/30",
  Cleyton: "bg-green-500/20 text-green-300 border-green-500/30",
};

function fmtDateTime(iso: string) {
  return new Intl.DateTimeFormat("pt-BR", {
    day: "2-digit", month: "2-digit", year: "numeric",
    hour: "2-digit", minute: "2-digit",
  }).format(new Date(iso));
}

function BatchItem({ batch }: { batch: UploadBatch }) {
  const [expanded, setExpanded] = useState(false);
  return (
    <div className="border border-white/5 rounded-xl overflow-hidden">
      <button
        onClick={() => setExpanded((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-3 hover:bg-white/[0.02] transition-colors"
      >
        <div className="flex items-center gap-4 text-sm">
          {expanded ? <ChevronDown size={14} className="text-slate-500" /> : <ChevronRight size={14} className="text-slate-500" />}
          <span className="text-slate-400 font-mono text-xs">{fmtDateTime(batch.created_at)}</span>
          {batch.responsavel && (
            <span className={cn("px-2 py-0.5 rounded-full text-xs font-medium border", RESPONSAVEL_COLORS[batch.responsavel] ?? "bg-white/5 text-slate-300 border-white/10")}>
              {batch.responsavel}
            </span>
          )}
          <span className="text-white font-medium">{batch.total_arquivos} arquivo{batch.total_arquivos !== 1 ? "s" : ""}</span>
          <span className="text-accent-green text-xs">{batch.criados} criados</span>
          {batch.ja_existentes > 0 && <span className="text-yellow-400 text-xs">{batch.ja_existentes} já existiam</span>}
          {batch.com_advogado > 0 && <span className="text-slate-500 text-xs">{batch.com_advogado} com advogado</span>}
          {batch.erros > 0 && <span className="text-accent-red text-xs">{batch.erros} erros</span>}
        </div>
      </button>
      {expanded && (
        <div className="border-t border-white/5 divide-y divide-white/5">
          {batch.arquivos.map((arq, i) => (
            <div key={i} className="flex items-center gap-3 px-5 py-2 text-xs">
              <FileText size={12} className="text-slate-600 shrink-0" />
              <span className="text-slate-400 truncate flex-1" title={arq.filename}>{arq.filename}</span>
              {arq.empresa_nome && <span className="text-slate-300 truncate max-w-[180px]">{arq.empresa_nome}</span>}
              {arq.numero_processo && <span className="text-slate-600 font-mono hidden lg:block">{arq.numero_processo}</span>}
              <span className={cn(
                "px-2 py-0.5 rounded-full border font-medium shrink-0",
                arq.status === "criado" ? "bg-accent-green/10 text-accent-green border-accent-green/20" :
                arq.status === "ja_existe" ? "bg-yellow-500/10 text-yellow-400 border-yellow-500/20" :
                arq.status === "tem_advogado" ? "bg-slate-500/10 text-slate-400 border-slate-500/20" :
                "bg-accent-red/10 text-accent-red border-accent-red/20"
              )}>
                {arq.status === "criado" ? "Criado" : arq.status === "ja_existe" ? "Já existia" : arq.status === "tem_advogado" ? "Com advogado" : "Erro"}
              </span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function HistoricoPanel() {
  const [page, setPage] = useState(1);
  const { data, isLoading } = useUploadHistorico(page);
  const total = data?.total ?? 0;
  const pageSize = data?.page_size ?? 20;
  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  if (isLoading) {
    return (
      <div className="flex items-center gap-3 py-12 justify-center text-slate-500">
        <Loader2 size={18} className="animate-spin" />
        <span className="text-sm">Carregando histórico...</span>
      </div>
    );
  }

  if (!data?.items?.length) {
    return (
      <div className="text-center py-12 text-slate-600">
        <History size={48} className="mx-auto mb-4 opacity-30" />
        <p className="text-sm">Nenhum upload registrado ainda.</p>
      </div>
    );
  }

  return (
    <div className="space-y-2">
      {data.items.map((batch) => (
        <BatchItem key={batch.id} batch={batch} />
      ))}
      {totalPages > 1 && (
        <div className="flex items-center justify-between pt-2 text-xs text-slate-500">
          <span>{total} batches · página {page} de {totalPages}</span>
          <div className="flex gap-2">
            <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1} className="px-2 py-1 rounded bg-surface-700 disabled:opacity-30">Anterior</button>
            <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages} className="px-2 py-1 rounded bg-surface-700 disabled:opacity-30">Próxima</button>
          </div>
        </div>
      )}
    </div>
  );
}

export function UploadPanel() {
  const [aba, setAba] = useState<"upload" | "historico">("upload");
  const [resultados, setResultados] = useState<DocumentoProcessado[]>([]);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [responsavel, setResponsavel] = useState<string>("");
  const [semResponsavelAviso, setSemResponsavelAviso] = useState(false);
  const [totalFiles, setTotalFiles] = useState(0);

  const upload = useUploadDocumentos();
  const enviarLote = useEnviarLote();

  const handleFiles = async (files: File[]) => {
    if (!responsavel) {
      setSemResponsavelAviso(true);
      return;
    }
    setSemResponsavelAviso(false);
    setResultados([]);
    setSelectedIds(new Set());
    setTotalFiles(files.length);
    await upload.mutateAsync({
      files,
      responsavel,
      onResult: (doc) => {
        setResultados((prev) => {
          const idx = prev.findIndex(r => r.filename === doc.filename && r.status === "erro");
          if (idx >= 0) {
            const next = [...prev];
            next[idx] = doc;
            return next;
          }
          return [...prev, doc];
        });
        if (doc.status === "criado" && doc.lead_id && doc.telefone) {
          setSelectedIds((prev) => new Set([...prev, doc.lead_id!]));
        }
      },
    });
  };

  const toggleSelect = (id: string) => {
    setSelectedIds((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const handleEnviarLote = async () => {
    if (!selectedIds.size) return;
    await enviarLote.mutateAsync({ lead_ids: Array.from(selectedIds) });
    setSelectedIds(new Set());
  };

  const leadsCriados = resultados.filter((r) => r.status === "criado" && r.lead_id);
  const comTelefone = leadsCriados.filter((r) => r.telefone);

  return (
    <div className="min-h-screen bg-[#020617] text-white">
      <div className="max-w-6xl mx-auto p-6 lg:p-10 space-y-8">
        {/* Header */}
        <div className="flex items-start justify-between">
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Upload de Documentos</h1>
            <p className="text-slate-400 mt-2 text-sm">
              Faça upload dos PDFs dos processos. O sistema extrai empresa, CNPJ, valor da causa
              e busca o telefone automaticamente via CNPJ.ws.
            </p>
          </div>
          <div className="flex gap-1 bg-surface-800 rounded-lg p-1 border border-white/5 shrink-0 mt-1">
            <button
              onClick={() => setAba("upload")}
              className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors", aba === "upload" ? "bg-surface-700 text-white" : "text-slate-400 hover:text-white")}
            >
              <Upload size={14} /> Upload
            </button>
            <button
              onClick={() => setAba("historico")}
              className={cn("flex items-center gap-1.5 px-3 py-1.5 rounded text-sm font-medium transition-colors", aba === "historico" ? "bg-surface-700 text-white" : "text-slate-400 hover:text-white")}
            >
              <History size={14} /> Histórico
            </button>
          </div>
        </div>

        {/* Aba Histórico */}
        {aba === "historico" && <HistoricoPanel />}

        {/* Aba Upload */}
        {aba === "upload" && <>

        {/* Seletor de responsável */}
        <div className="space-y-2">
          <p className="text-sm text-slate-400 font-medium">Quem está fazendo o upload?</p>
          <div className="flex flex-wrap gap-2">
            {RESPONSAVEIS.map((nome) => (
              <button
                key={nome}
                onClick={() => { setResponsavel(nome); setSemResponsavelAviso(false); }}
                className={cn(
                  "px-4 py-2 rounded-lg text-sm font-medium border transition-all",
                  responsavel === nome
                    ? RESPONSAVEL_COLORS[nome]
                    : "bg-white/[0.03] text-slate-400 border-white/10 hover:border-white/20 hover:text-white"
                )}
              >
                {nome}
              </button>
            ))}
          </div>
          {semResponsavelAviso && (
            <p className="text-xs text-amber-400 flex items-center gap-1">
              <AlertTriangle size={12} /> Selecione quem está fazendo o upload antes de enviar os arquivos.
            </p>
          )}
        </div>

        {/* Drop zone */}
        <DropZone onFiles={handleFiles} />

        {/* Loading state */}
        {upload.isPending && (
          <div className="flex items-center gap-3 bg-surface-800/60 border border-white/5 rounded-xl px-6 py-4">
            <Loader2 size={20} className="animate-spin text-indigo-400 shrink-0" />
            <span className="text-sm text-slate-300">
              Processando... {resultados.length} de {totalFiles}
            </span>
          </div>
        )}

        {/* Resultados */}
        {resultados.length > 0 && (
          <div className="space-y-4">
            {/* Resumo + botão lote */}
            <div className="flex items-center justify-between bg-surface-800/40 border border-white/5 rounded-xl px-6 py-4">
              <div className="flex gap-6 text-sm">
                <span className="text-accent-green font-semibold">{leadsCriados.length} leads criados</span>
                <span className="text-yellow-400">{resultados.filter((r) => r.status === "ja_existe").length} já existiam</span>
                <span className="text-slate-500">{resultados.filter((r) => r.status === "tem_advogado").length} com advogado</span>
                {resultados.filter((r) => r.status === "erro").length > 0 && (
                  <span className="text-accent-red">{resultados.filter((r) => r.status === "erro").length} erros</span>
                )}
              </div>
              <button
                onClick={handleEnviarLote}
                disabled={selectedIds.size === 0 || enviarLote.isPending || upload.isPending}
                className={cn(
                  "flex items-center gap-2 px-4 py-2 rounded-lg text-sm font-medium transition-all",
                  selectedIds.size > 0 && !enviarLote.isPending
                    ? "bg-indigo-600 hover:bg-indigo-500 text-white"
                    : "bg-surface-700 text-slate-500 cursor-not-allowed"
                )}
              >
                {enviarLote.isPending ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <Send size={15} />
                )}
                Enviar {selectedIds.size > 0 ? `(${selectedIds.size})` : "selecionados"} via WhatsApp
              </button>
            </div>

            {/* Resultado do envio em lote */}
            {enviarLote.isSuccess && enviarLote.data && (
              <div className="flex items-center gap-3 bg-accent-green/10 border border-accent-green/20 rounded-xl px-6 py-4 text-sm">
                <CheckCircle2 size={18} className="text-accent-green shrink-0" />
                <span className="text-accent-green font-medium">
                  {enviarLote.data.enviados} mensagens enviadas
                  {enviarLote.data.sem_telefone > 0 && ` · ${enviarLote.data.sem_telefone} sem telefone`}
                  {enviarLote.data.erros > 0 && ` · ${enviarLote.data.erros} erros`}
                </span>
              </div>
            )}

            {/* Tabela de resultados */}
            <div className="bg-surface-800/40 border border-white/5 rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-white/5 text-xs text-slate-500 uppercase tracking-wider">
                      <th className="px-4 py-3 text-left w-8">
                        <input
                          type="checkbox"
                          className="rounded"
                          checked={selectedIds.size === comTelefone.length && comTelefone.length > 0}
                          onChange={(e) => {
                            if (e.target.checked) {
                              setSelectedIds(new Set(comTelefone.map((r) => r.lead_id!)));
                            } else {
                              setSelectedIds(new Set());
                            }
                          }}
                        />
                      </th>
                      <th className="px-4 py-3 text-left">Arquivo</th>
                      <th className="px-4 py-3 text-left">Empresa</th>
                      <th className="px-4 py-3 text-left">CNPJ</th>
                      <th className="px-4 py-3 text-left">Reclamante</th>
                      <th className="px-4 py-3 text-left">Telefone</th>
                      <th className="px-4 py-3 text-right">Valor</th>
                      <th className="px-4 py-3 text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-white/5">
                    {resultados.map((doc, i) => {
                      const canSelect = doc.status === "criado" && !!doc.lead_id && !!doc.telefone;
                      const isSelected = doc.lead_id ? selectedIds.has(doc.lead_id) : false;
                      return (
                        <tr
                          key={i}
                          className={cn(
                            "transition-colors",
                            canSelect ? "hover:bg-white/[0.03] cursor-pointer" : "opacity-60"
                          )}
                          onClick={() => canSelect && doc.lead_id && toggleSelect(doc.lead_id)}
                        >
                          <td className="px-4 py-3">
                            {canSelect && (
                              <input
                                type="checkbox"
                                className="rounded"
                                checked={isSelected}
                                onChange={() => {}}
                                onClick={(e) => e.stopPropagation()}
                              />
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-2">
                              <FileText size={14} className="text-slate-500 shrink-0" />
                              <span className="text-slate-300 truncate max-w-[160px]" title={doc.filename}>
                                {doc.filename}
                              </span>
                            </div>
                            {doc.numero_processo && (
                              <div className="text-xs text-slate-600 mt-0.5 font-mono">
                                {doc.numero_processo}
                              </div>
                            )}
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1.5">
                              <Building2 size={12} className="text-slate-600 shrink-0" />
                              <span className="text-white font-medium truncate max-w-[180px]" title={doc.empresa_nome || ""}>
                                {doc.empresa_nome || <span className="text-slate-600">—</span>}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3 font-mono text-xs text-slate-400">
                            <div className="flex items-center gap-1">
                              <Hash size={11} className="text-slate-600" />
                              {fmtCNPJ(doc.empresa_cnpj)}
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            <div className="flex items-center gap-1.5">
                              <User size={12} className="text-slate-600 shrink-0" />
                              <span className="text-slate-300 truncate max-w-[140px]">
                                {doc.reclamante_nome || <span className="text-slate-600">—</span>}
                              </span>
                            </div>
                          </td>
                          <td className="px-4 py-3">
                            {doc.telefone ? (
                              <div className="flex items-center gap-1.5">
                                <Phone size={12} className="text-accent-green shrink-0" />
                                <span className="text-accent-green font-mono text-xs">{doc.telefone}</span>
                                {doc.telefone_fonte === "cnpj_ws" && (
                                  <span className="text-[10px] text-slate-600 bg-slate-800 px-1 rounded">CNPJ.ws</span>
                                )}
                              </div>
                            ) : (
                              <span className="text-slate-600 text-xs">Sem telefone</span>
                            )}
                          </td>
                          <td className="px-4 py-3 text-right">
                            <div className="flex items-center justify-end gap-1">
                              <DollarSign size={12} className="text-slate-600" />
                              <span className="text-white font-medium">{fmtBRL(doc.valor_causa)}</span>
                            </div>
                          </td>
                          <td className="px-4 py-3 text-center">
                            {doc.status === "erro" ? (
                              <div className="flex flex-col items-center gap-1">
                                <StatusBadge status={doc.status} />
                                {doc.erro_msg && (
                                  <span className="text-[10px] text-accent-red max-w-[140px] truncate" title={doc.erro_msg}>
                                    {doc.erro_msg}
                                  </span>
                                )}
                              </div>
                            ) : (
                              <StatusBadge status={doc.status} />
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Aviso sobre leads sem telefone */}
            {leadsCriados.filter((r) => !r.telefone).length > 0 && (
              <div className="flex items-start gap-3 bg-yellow-500/5 border border-yellow-500/20 rounded-xl px-5 py-4 text-sm">
                <AlertTriangle size={16} className="text-yellow-400 mt-0.5 shrink-0" />
                <div>
                  <span className="text-yellow-300 font-medium">
                    {leadsCriados.filter((r) => !r.telefone).length} lead(s) sem telefone
                  </span>
                  <p className="text-slate-500 text-xs mt-0.5">
                    CNPJ não encontrado na base do CNPJ.ws ou empresa sem telefone cadastrado.
                    Você pode adicionar manualmente no dashboard.
                  </p>
                </div>
              </div>
            )}
          </div>
        )}

        {/* Estado vazio */}
        {!upload.isPending && resultados.length === 0 && !upload.isError && (
          <div className="text-center py-12 text-slate-600">
            <FileText size={48} className="mx-auto mb-4 opacity-30" />
            <p>Nenhum documento processado ainda.</p>
          </div>
        )}

        {/* Erro geral */}
        {upload.isError && (
          <div className="flex items-center gap-3 bg-accent-red/10 border border-accent-red/20 rounded-xl px-6 py-4">
            <XCircle size={18} className="text-accent-red shrink-0" />
            <span className="text-accent-red text-sm">
              Erro ao enviar documentos. Verifique se o backend está online.
            </span>
          </div>
        )}
        </>}
      </div>
    </div>
  );
}
