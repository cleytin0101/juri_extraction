"use client"

import { useState, useCallback, useMemo } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Textarea } from "@/components/ui/textarea"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import {
  Dialog,
  DialogContent,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Badge } from "@/components/ui/badge"
import {
  ChevronLeft, ChevronRight, Plus, Calendar, Clock, Grid3x3,
  List, Search, Filter, X, Building2, Gavel,
} from "lucide-react"
import { cn } from "@/lib/utils"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuCheckboxItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { format } from "date-fns"
import { ptBR } from "date-fns/locale"

// ─── Types ────────────────────────────────────────────────────────────────────

export interface LeadOption {
  id: string
  nome: string
  processo: string
  cnpj?: string
  valor_causa?: number | null
  data_audiencia?: string | null
  orgao_julgador?: string | null
  reclamante_nome?: string | null
  resumo_caso?: string | null
}

export interface Event {
  id: string
  title: string
  description?: string
  startTime: Date
  endTime: Date
  color: string
  category?: string
  tags?: string[]
  lead_id?: string
}

export interface EventManagerProps {
  events?: Event[]
  leads?: LeadOption[]
  onEventCreate?: (event: Omit<Event, "id">) => void
  onEventUpdate?: (id: string, event: Partial<Event>) => void
  onEventDelete?: (id: string) => void
  categories?: string[]
  colors?: { name: string; value: string; bg: string }[]
  defaultView?: "month" | "week" | "day" | "list"
  className?: string
  availableTags?: string[]
}

// ─── Formatação ───────────────────────────────────────────────────────────────

function fmtValor(v: number | null | undefined) {
  if (v == null) return "—"
  return new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" }).format(v)
}

function fmtData(d: string | null | undefined) {
  if (!d) return "—"
  try {
    return format(new Date(d), "dd/MM/yyyy HH:mm", { locale: ptBR })
  } catch {
    return d
  }
}

function fmtCnpj(cnpj: string | undefined) {
  if (!cnpj) return "—"
  const d = cnpj.replace(/\D/g, "")
  if (d.length !== 14) return cnpj
  return `${d.slice(0, 2)}.${d.slice(2, 5)}.${d.slice(5, 8)}/${d.slice(8, 12)}-${d.slice(12)}`
}

function fmtHora(date: Date) {
  return format(date, "HH:mm", { locale: ptBR })
}

// ─── Padrões ──────────────────────────────────────────────────────────────────

const defaultColors = [
  { name: "Azul",    value: "blue",   bg: "bg-blue-500" },
  { name: "Verde",   value: "green",  bg: "bg-green-500" },
  { name: "Roxo",    value: "purple", bg: "bg-purple-500" },
  { name: "Laranja", value: "orange", bg: "bg-orange-500" },
  { name: "Rosa",    value: "pink",   bg: "bg-pink-500" },
  { name: "Vermelho",value: "red",    bg: "bg-red-500" },
]

const DIAS_SEMANA_CURTO = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]
const DIAS_SEMANA_MIN   = ["D", "S", "T", "Q", "Q", "S", "S"]

// ─── Componente principal ─────────────────────────────────────────────────────

export function EventManager({
  events: initialEvents = [],
  leads = [],
  onEventCreate,
  onEventUpdate,
  onEventDelete,
  categories = ["Reunião", "Tarefa", "Lembrete", "Pessoal"],
  colors = defaultColors,
  defaultView = "month",
  className,
  availableTags = ["Importante", "Urgente", "Trabalho", "Pessoal", "Equipe", "Cliente"],
}: EventManagerProps) {
  const [events, setEvents] = useState<Event[]>(initialEvents)
  const [currentDate, setCurrentDate] = useState(new Date())
  const [view, setView] = useState<"month" | "week" | "day" | "list">(defaultView)
  const [selectedEvent, setSelectedEvent] = useState<Event | null>(null)
  const [isDialogOpen, setIsDialogOpen] = useState(false)
  const [isCreating, setIsCreating] = useState(false)
  const [draggedEvent, setDraggedEvent] = useState<Event | null>(null)
  const [newEvent, setNewEvent] = useState<Partial<Event>>({
    title: "", description: "", color: colors[0].value,
    category: categories[0], tags: [], lead_id: "",
  })

  const [searchQuery, setSearchQuery] = useState("")
  const [selectedColors, setSelectedColors] = useState<string[]>([])
  const [selectedTags, setSelectedTags] = useState<string[]>([])
  const [selectedCategories, setSelectedCategories] = useState<string[]>([])

  const filteredEvents = useMemo(() => {
    return events.filter((event) => {
      if (searchQuery) {
        const q = searchQuery.toLowerCase()
        const ok = event.title.toLowerCase().includes(q)
          || event.description?.toLowerCase().includes(q)
          || event.category?.toLowerCase().includes(q)
          || event.tags?.some(t => t.toLowerCase().includes(q))
        if (!ok) return false
      }
      if (selectedColors.length > 0 && !selectedColors.includes(event.color)) return false
      if (selectedTags.length > 0 && !event.tags?.some(t => selectedTags.includes(t))) return false
      if (selectedCategories.length > 0 && event.category && !selectedCategories.includes(event.category)) return false
      return true
    })
  }, [events, searchQuery, selectedColors, selectedTags, selectedCategories])

  const hasFilters = selectedColors.length > 0 || selectedTags.length > 0 || selectedCategories.length > 0

  const clearFilters = () => {
    setSelectedColors([])
    setSelectedTags([])
    setSelectedCategories([])
    setSearchQuery("")
  }

  const getColor = useCallback((v: string) => colors.find(c => c.value === v) || colors[0], [colors])

  const handleCreate = useCallback(() => {
    if (!newEvent.title || !newEvent.startTime || !newEvent.endTime) return
    const event: Event = {
      id: Math.random().toString(36).substr(2, 9),
      title: newEvent.title!,
      description: newEvent.description,
      startTime: newEvent.startTime!,
      endTime: newEvent.endTime!,
      color: newEvent.color || colors[0].value,
      category: newEvent.category,
      tags: newEvent.tags || [],
      lead_id: newEvent.lead_id || undefined,
    }
    setEvents(prev => [...prev, event])
    onEventCreate?.(event)
    setIsDialogOpen(false)
    setIsCreating(false)
    setNewEvent({ title: "", description: "", color: colors[0].value, category: categories[0], tags: [], lead_id: "" })
  }, [newEvent, colors, categories, onEventCreate])

  const handleUpdate = useCallback(() => {
    if (!selectedEvent) return
    setEvents(prev => prev.map(e => e.id === selectedEvent.id ? selectedEvent : e))
    onEventUpdate?.(selectedEvent.id, selectedEvent)
    setIsDialogOpen(false)
    setSelectedEvent(null)
  }, [selectedEvent, onEventUpdate])

  const handleDelete = useCallback((id: string) => {
    setEvents(prev => prev.filter(e => e.id !== id))
    onEventDelete?.(id)
    setIsDialogOpen(false)
    setSelectedEvent(null)
  }, [onEventDelete])

  const handleDragStart = useCallback((e: Event) => setDraggedEvent(e), [])
  const handleDragEnd   = useCallback(() => setDraggedEvent(null), [])

  const handleDrop = useCallback((date: Date, hour?: number) => {
    if (!draggedEvent) return
    const dur = draggedEvent.endTime.getTime() - draggedEvent.startTime.getTime()
    const start = new Date(date)
    if (hour !== undefined) start.setHours(hour, 0, 0, 0)
    const updated = { ...draggedEvent, startTime: start, endTime: new Date(start.getTime() + dur) }
    setEvents(prev => prev.map(e => e.id === draggedEvent.id ? updated : e))
    onEventUpdate?.(draggedEvent.id, updated)
    setDraggedEvent(null)
  }, [draggedEvent, onEventUpdate])

  const navigate = useCallback((dir: "prev" | "next") => {
    setCurrentDate(prev => {
      const d = new Date(prev)
      const delta = dir === "next" ? 1 : -1
      if (view === "month") d.setMonth(d.getMonth() + delta)
      else if (view === "week") d.setDate(d.getDate() + delta * 7)
      else d.setDate(d.getDate() + delta)
      return d
    })
  }, [view])

  const toggleTag = (tag: string, creating: boolean) => {
    if (creating) {
      setNewEvent(p => ({ ...p, tags: p.tags?.includes(tag) ? p.tags.filter(t => t !== tag) : [...(p.tags || []), tag] }))
    } else {
      setSelectedEvent(p => p ? { ...p, tags: p.tags?.includes(tag) ? p.tags.filter(t => t !== tag) : [...(p.tags || []), tag] } : null)
    }
  }

  const openEvent = (event: Event) => { setSelectedEvent(event); setIsCreating(false); setIsDialogOpen(true) }
  const openCreate = () => { setIsCreating(true); setIsDialogOpen(true) }

  // ─── título do cabeçalho ────────────────────────────────────────────────────
  const headerTitle = useMemo(() => {
    if (view === "month") return format(currentDate, "MMMM yyyy", { locale: ptBR })
    if (view === "week")  return `Semana de ${format(currentDate, "d 'de' MMMM", { locale: ptBR })}`
    if (view === "day")   return format(currentDate, "EEEE, d 'de' MMMM 'de' yyyy", { locale: ptBR })
    return "Todos os eventos"
  }, [view, currentDate])

  // ─── lead selecionado no modal ──────────────────────────────────────────────
  const eventLead = useMemo(() => {
    const lid = isCreating ? newEvent.lead_id : selectedEvent?.lead_id
    return lid ? leads.find(l => l.id === lid) : undefined
  }, [isCreating, newEvent.lead_id, selectedEvent?.lead_id, leads])

  // ─── classes de filtros comuns ──────────────────────────────────────────────
  const filterBtn = "gap-1.5 text-xs border-surface-600 bg-surface-800 hover:bg-surface-700 text-gray-300"
  const viewBtn   = (active: boolean) => cn(
    "flex items-center gap-1.5 px-3 py-1.5 rounded text-sm transition-colors",
    active ? "bg-accent-blue text-white" : "text-gray-400 hover:text-white hover:bg-surface-700"
  )

  return (
    <div className={cn("flex flex-col gap-4", className)}>

      {/* ─── Cabeçalho ──────────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
        <div className="flex items-center gap-3">
          <h2 className="text-xl font-semibold text-white capitalize">{headerTitle}</h2>
          <div className="flex items-center gap-1">
            <button
              onClick={() => navigate("prev")}
              className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-surface-700 transition-colors"
            >
              <ChevronLeft size={16} />
            </button>
            <button
              onClick={() => setCurrentDate(new Date())}
              className="px-2.5 py-1 rounded text-xs text-gray-400 hover:text-white border border-surface-600 hover:bg-surface-700 transition-colors"
            >
              Hoje
            </button>
            <button
              onClick={() => navigate("next")}
              className="p-1.5 rounded text-gray-400 hover:text-white hover:bg-surface-700 transition-colors"
            >
              <ChevronRight size={16} />
            </button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Seletor de view */}
          <div className="flex items-center gap-1 rounded-lg border border-surface-600 bg-surface-800 p-1">
            <button className={viewBtn(view === "month")} onClick={() => setView("month")}>
              <Calendar size={14} />Mês
            </button>
            <button className={viewBtn(view === "week")} onClick={() => setView("week")}>
              <Grid3x3 size={14} />Semana
            </button>
            <button className={viewBtn(view === "day")} onClick={() => setView("day")}>
              <Clock size={14} />Dia
            </button>
            <button className={viewBtn(view === "list")} onClick={() => setView("list")}>
              <List size={14} />Lista
            </button>
          </div>

          <button
            onClick={openCreate}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-accent-blue hover:bg-blue-600 text-white text-sm font-medium transition-colors"
          >
            <Plus size={15} />Novo Evento
          </button>
        </div>
      </div>

      {/* ─── Busca + Filtros ─────────────────────────────────────────────────── */}
      <div className="flex flex-col gap-2">
        <div className="relative">
          <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" />
          <input
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Pesquisar eventos..."
            className="w-full bg-surface-800 border border-surface-600 rounded-lg pl-9 pr-8 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent-blue transition-colors"
          />
          {searchQuery && (
            <button onClick={() => setSearchQuery("")} className="absolute right-2 top-1/2 -translate-y-1/2 text-gray-500 hover:text-white">
              <X size={14} />
            </button>
          )}
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <FilterDropdown label="Cores" count={selectedColors.length} className={filterBtn}>
            {colors.map(c => (
              <DropdownMenuCheckboxItem
                key={c.value}
                checked={selectedColors.includes(c.value)}
                onCheckedChange={v => setSelectedColors(p => v ? [...p, c.value] : p.filter(x => x !== c.value))}
              >
                <div className="flex items-center gap-2">
                  <div className={cn("h-3 w-3 rounded-full", c.bg)} />{c.name}
                </div>
              </DropdownMenuCheckboxItem>
            ))}
          </FilterDropdown>

          <FilterDropdown label="Tags" count={selectedTags.length} className={filterBtn}>
            {availableTags.map(t => (
              <DropdownMenuCheckboxItem
                key={t}
                checked={selectedTags.includes(t)}
                onCheckedChange={v => setSelectedTags(p => v ? [...p, t] : p.filter(x => x !== t))}
              >{t}</DropdownMenuCheckboxItem>
            ))}
          </FilterDropdown>

          <FilterDropdown label="Categorias" count={selectedCategories.length} className={filterBtn}>
            {categories.map(c => (
              <DropdownMenuCheckboxItem
                key={c}
                checked={selectedCategories.includes(c)}
                onCheckedChange={v => setSelectedCategories(p => v ? [...p, c] : p.filter(x => x !== c))}
              >{c}</DropdownMenuCheckboxItem>
            ))}
          </FilterDropdown>

          {hasFilters && (
            <button onClick={clearFilters} className="flex items-center gap-1 text-xs text-gray-400 hover:text-white transition-colors">
              <X size={13} />Limpar filtros
            </button>
          )}
        </div>

        {hasFilters && (
          <div className="flex flex-wrap items-center gap-1.5">
            <span className="text-xs text-gray-500">Filtros ativos:</span>
            {selectedColors.map(v => {
              const c = getColor(v)
              return (
                <span key={v} className="inline-flex items-center gap-1 text-xs bg-surface-700 border border-surface-600 text-gray-300 rounded-full px-2 py-0.5">
                  <div className={cn("h-2 w-2 rounded-full", c.bg)} />{c.name}
                  <button onClick={() => setSelectedColors(p => p.filter(x => x !== v))} className="ml-0.5 hover:text-white"><X size={11} /></button>
                </span>
              )
            })}
            {selectedTags.map(t => (
              <span key={t} className="inline-flex items-center gap-1 text-xs bg-surface-700 border border-surface-600 text-gray-300 rounded-full px-2 py-0.5">
                {t}<button onClick={() => setSelectedTags(p => p.filter(x => x !== t))} className="ml-0.5 hover:text-white"><X size={11} /></button>
              </span>
            ))}
            {selectedCategories.map(c => (
              <span key={c} className="inline-flex items-center gap-1 text-xs bg-surface-700 border border-surface-600 text-gray-300 rounded-full px-2 py-0.5">
                {c}<button onClick={() => setSelectedCategories(p => p.filter(x => x !== c))} className="ml-0.5 hover:text-white"><X size={11} /></button>
              </span>
            ))}
          </div>
        )}
      </div>

      {/* ─── Views ───────────────────────────────────────────────────────────── */}
      {view === "month" && (
        <MonthView currentDate={currentDate} events={filteredEvents}
          onEventClick={openEvent} onDragStart={handleDragStart}
          onDragEnd={handleDragEnd} onDrop={handleDrop} getColor={getColor} />
      )}
      {view === "week" && (
        <WeekView currentDate={currentDate} events={filteredEvents}
          onEventClick={openEvent} onDragStart={handleDragStart}
          onDragEnd={handleDragEnd} onDrop={handleDrop} getColor={getColor} />
      )}
      {view === "day" && (
        <DayView currentDate={currentDate} events={filteredEvents}
          onEventClick={openEvent} onDragStart={handleDragStart}
          onDragEnd={handleDragEnd} onDrop={handleDrop} getColor={getColor} />
      )}
      {view === "list" && (
        <ListView events={filteredEvents} onEventClick={openEvent} getColor={getColor} />
      )}

      {/* ─── Modal criar / editar ─────────────────────────────────────────── */}
      <Dialog open={isDialogOpen} onOpenChange={open => { setIsDialogOpen(open); if (!open) { setIsCreating(false); setSelectedEvent(null) } }}>
        <DialogContent className="bg-surface-800 border-surface-600 text-white max-w-md max-h-[90vh] overflow-y-auto p-0">
          {/* Cabeçalho do modal */}
          <DialogHeader className="px-5 py-4 border-b border-surface-600 bg-surface-700 rounded-t-lg">
            <DialogTitle className="text-base font-semibold text-white">
              {isCreating ? "Novo Evento" : "Detalhes do Evento"}
            </DialogTitle>
          </DialogHeader>

          <div className="px-5 py-4 space-y-4">
            {/* Título */}
            <div className="space-y-1.5">
              <Label className="text-xs text-gray-400 uppercase tracking-wide">Título</Label>
              <input
                value={isCreating ? (newEvent.title ?? "") : (selectedEvent?.title ?? "")}
                onChange={e => isCreating
                  ? setNewEvent(p => ({ ...p, title: e.target.value }))
                  : setSelectedEvent(p => p ? { ...p, title: e.target.value } : null)
                }
                placeholder="Nome do evento"
                className="w-full bg-surface-900 border border-surface-600 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent-blue"
              />
            </div>

            {/* Descrição */}
            <div className="space-y-1.5">
              <Label className="text-xs text-gray-400 uppercase tracking-wide">Descrição</Label>
              <textarea
                value={isCreating ? (newEvent.description ?? "") : (selectedEvent?.description ?? "")}
                onChange={e => isCreating
                  ? setNewEvent(p => ({ ...p, description: e.target.value }))
                  : setSelectedEvent(p => p ? { ...p, description: e.target.value } : null)
                }
                placeholder="Detalhes do evento..."
                rows={3}
                className="w-full bg-surface-900 border border-surface-600 rounded-lg px-3 py-2 text-sm text-gray-200 placeholder-gray-500 focus:outline-none focus:border-accent-blue resize-none"
              />
            </div>

            {/* Datas */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs text-gray-400 uppercase tracking-wide">Início</Label>
                <input
                  type="datetime-local"
                  value={toDatetimeLocal(isCreating ? newEvent.startTime : selectedEvent?.startTime)}
                  onChange={e => {
                    const d = new Date(e.target.value)
                    isCreating
                      ? setNewEvent(p => ({ ...p, startTime: d }))
                      : setSelectedEvent(p => p ? { ...p, startTime: d } : null)
                  }}
                  className="w-full bg-surface-900 border border-surface-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-accent-blue"
                />
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-gray-400 uppercase tracking-wide">Fim</Label>
                <input
                  type="datetime-local"
                  value={toDatetimeLocal(isCreating ? newEvent.endTime : selectedEvent?.endTime)}
                  onChange={e => {
                    const d = new Date(e.target.value)
                    isCreating
                      ? setNewEvent(p => ({ ...p, endTime: d }))
                      : setSelectedEvent(p => p ? { ...p, endTime: d } : null)
                  }}
                  className="w-full bg-surface-900 border border-surface-600 rounded-lg px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-accent-blue"
                />
              </div>
            </div>

            {/* Categoria + Cor */}
            <div className="grid grid-cols-2 gap-3">
              <div className="space-y-1.5">
                <Label className="text-xs text-gray-400 uppercase tracking-wide">Categoria</Label>
                <Select
                  value={isCreating ? newEvent.category : selectedEvent?.category}
                  onValueChange={v => isCreating
                    ? setNewEvent(p => ({ ...p, category: v }))
                    : setSelectedEvent(p => p ? { ...p, category: v } : null)
                  }
                >
                  <SelectTrigger className="bg-surface-900 border-surface-600 text-gray-200">
                    <SelectValue placeholder="Selecione..." />
                  </SelectTrigger>
                  <SelectContent className="bg-surface-800 border-surface-600">
                    {categories.map(c => <SelectItem key={c} value={c} className="text-gray-200 focus:bg-surface-700">{c}</SelectItem>)}
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-1.5">
                <Label className="text-xs text-gray-400 uppercase tracking-wide">Cor</Label>
                <Select
                  value={isCreating ? newEvent.color : selectedEvent?.color}
                  onValueChange={v => isCreating
                    ? setNewEvent(p => ({ ...p, color: v }))
                    : setSelectedEvent(p => p ? { ...p, color: v } : null)
                  }
                >
                  <SelectTrigger className="bg-surface-900 border-surface-600 text-gray-200">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent className="bg-surface-800 border-surface-600">
                    {colors.map(c => (
                      <SelectItem key={c.value} value={c.value} className="text-gray-200 focus:bg-surface-700">
                        <div className="flex items-center gap-2">
                          <div className={cn("h-3 w-3 rounded-full", c.bg)} />{c.name}
                        </div>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            </div>

            {/* Tags */}
            <div className="space-y-1.5">
              <Label className="text-xs text-gray-400 uppercase tracking-wide">Tags</Label>
              <div className="flex flex-wrap gap-1.5">
                {availableTags.map(tag => {
                  const sel = isCreating ? newEvent.tags?.includes(tag) : selectedEvent?.tags?.includes(tag)
                  return (
                    <button
                      key={tag}
                      onClick={() => toggleTag(tag, isCreating)}
                      className={cn(
                        "text-xs px-2.5 py-1 rounded-full border transition-colors",
                        sel
                          ? "bg-accent-blue border-blue-500 text-white"
                          : "bg-surface-900 border-surface-600 text-gray-400 hover:text-white hover:border-gray-400"
                      )}
                    >{tag}</button>
                  )
                })}
              </div>
            </div>

            {/* Lead associado */}
            {leads.length > 0 && (
              <div className="space-y-1.5">
                <Label className="text-xs text-gray-400 uppercase tracking-wide">Lead associado</Label>
                <Select
                  value={isCreating ? (newEvent.lead_id || "none") : (selectedEvent?.lead_id || "none")}
                  onValueChange={v => {
                    const val = v === "none" ? "" : v
                    isCreating
                      ? setNewEvent(p => ({ ...p, lead_id: val }))
                      : setSelectedEvent(p => p ? { ...p, lead_id: val } : null)
                  }}
                >
                  <SelectTrigger className="bg-surface-900 border-surface-600 text-gray-200">
                    <SelectValue placeholder="Selecionar lead..." />
                  </SelectTrigger>
                  <SelectContent className="bg-surface-800 border-surface-600 max-h-48">
                    <SelectItem value="none" className="text-gray-400 focus:bg-surface-700">Nenhum</SelectItem>
                    {leads.map(l => (
                      <SelectItem key={l.id} value={l.id} className="text-gray-200 focus:bg-surface-700">
                        <span className="font-medium">{l.nome}</span>
                        <span className="text-gray-400 ml-1 text-xs">— {l.processo}</span>
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
            )}

            {/* Card do lead (quando selecionado) */}
            {eventLead && (
              <div className="rounded-xl bg-surface-700 border border-surface-600 p-4 space-y-3">
                <div className="flex items-center gap-2">
                  <Building2 size={13} className="text-accent-blue" />
                  <p className="text-xs font-semibold text-accent-blue uppercase tracking-wide">Lead Associado</p>
                </div>
                <div>
                  <p className="font-medium text-white text-sm">{eventLead.nome}</p>
                  {eventLead.cnpj && <p className="text-xs text-gray-400 mt-0.5">CNPJ: {fmtCnpj(eventLead.cnpj)}</p>}
                </div>
                <div className="flex items-center gap-1.5">
                  <Gavel size={12} className="text-gray-500" />
                  <p className="text-xs text-gray-300">{eventLead.processo}</p>
                </div>
                <div className="grid grid-cols-2 gap-x-4 gap-y-1 text-xs">
                  {eventLead.reclamante_nome && (
                    <div>
                      <p className="text-gray-500">Reclamante</p>
                      <p className="text-gray-300">{eventLead.reclamante_nome}</p>
                    </div>
                  )}
                  {eventLead.orgao_julgador && (
                    <div>
                      <p className="text-gray-500">Órgão</p>
                      <p className="text-gray-300">{eventLead.orgao_julgador}</p>
                    </div>
                  )}
                  <div>
                    <p className="text-gray-500">Valor da causa</p>
                    <p className="text-gray-300">{fmtValor(eventLead.valor_causa)}</p>
                  </div>
                  {eventLead.data_audiencia && (
                    <div>
                      <p className="text-gray-500">Audiência</p>
                      <p className="text-gray-300">{fmtData(eventLead.data_audiencia)}</p>
                    </div>
                  )}
                </div>
                {eventLead.resumo_caso && (
                  <p className="text-xs text-gray-400 leading-relaxed border-t border-surface-600 pt-2">{eventLead.resumo_caso}</p>
                )}
              </div>
            )}
          </div>

          <DialogFooter className="px-5 py-3 border-t border-surface-600 flex items-center gap-2">
            {!isCreating && (
              <button
                onClick={() => selectedEvent && handleDelete(selectedEvent.id)}
                className="px-3 py-1.5 rounded-lg text-sm text-red-400 hover:bg-red-500/10 border border-red-500/30 transition-colors"
              >
                Excluir
              </button>
            )}
            <div className="flex-1" />
            <button
              onClick={() => { setIsDialogOpen(false); setIsCreating(false); setSelectedEvent(null) }}
              className="px-3 py-1.5 rounded-lg text-sm text-gray-400 hover:text-white border border-surface-600 hover:bg-surface-700 transition-colors"
            >
              Cancelar
            </button>
            <button
              onClick={isCreating ? handleCreate : handleUpdate}
              className="px-4 py-1.5 rounded-lg text-sm font-medium bg-accent-blue hover:bg-blue-600 text-white transition-colors"
            >
              {isCreating ? "Criar" : "Salvar"}
            </button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

// ─── Utilitário datetime-local ────────────────────────────────────────────────

function toDatetimeLocal(d: Date | undefined): string {
  if (!d) return ""
  const offset = d.getTimezoneOffset() * 60000
  return new Date(d.getTime() - offset).toISOString().slice(0, 16)
}

// ─── FilterDropdown helper ────────────────────────────────────────────────────

function FilterDropdown({ label, count, className, children }: {
  label: string
  count: number
  className?: string
  children: React.ReactNode
}) {
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="sm" className={className}>
          <Filter size={12} />{label}
          {count > 0 && (
            <span className="ml-1 bg-accent-blue text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">{count}</span>
          )}
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="start" className="bg-surface-800 border-surface-600 w-48">
        <DropdownMenuLabel className="text-gray-400 text-xs">Filtrar por {label.toLowerCase()}</DropdownMenuLabel>
        <DropdownMenuSeparator className="bg-surface-600" />
        {children}
      </DropdownMenuContent>
    </DropdownMenu>
  )
}

// ─── EventPill ────────────────────────────────────────────────────────────────

function EventPill({ event, onClick, onDragStart, onDragEnd, getColor, variant = "default" }: {
  event: Event
  onClick: (e: Event) => void
  onDragStart: (e: Event) => void
  onDragEnd: () => void
  getColor: (v: string) => { bg: string }
  variant?: "compact" | "default" | "detailed"
}) {
  const c = getColor(event.color)

  if (variant === "compact") {
    return (
      <div
        draggable
        onDragStart={() => onDragStart(event)}
        onDragEnd={onDragEnd}
        onClick={() => onClick(event)}
        className={cn("rounded px-1.5 py-0.5 text-[11px] font-medium cursor-pointer truncate text-white transition-opacity hover:opacity-80", c.bg)}
        title={event.title}
      >
        {event.title}
      </div>
    )
  }

  if (variant === "detailed") {
    return (
      <div
        draggable
        onDragStart={() => onDragStart(event)}
        onDragEnd={onDragEnd}
        onClick={() => onClick(event)}
        className={cn("rounded-lg p-2.5 cursor-pointer text-white transition-opacity hover:opacity-90", c.bg)}
      >
        <p className="font-medium text-sm">{event.title}</p>
        {event.description && <p className="text-xs opacity-80 mt-0.5 line-clamp-1">{event.description}</p>}
        <div className="flex items-center gap-1 mt-1 text-[11px] opacity-70">
          <Clock size={10} />{fmtHora(event.startTime)} – {fmtHora(event.endTime)}
        </div>
      </div>
    )
  }

  return (
    <div
      draggable
      onDragStart={() => onDragStart(event)}
      onDragEnd={onDragEnd}
      onClick={() => onClick(event)}
      className={cn("rounded px-2 py-0.5 text-xs font-medium cursor-pointer truncate text-white transition-opacity hover:opacity-80", c.bg)}
      title={event.title}
    >
      {event.title}
    </div>
  )
}

// ─── MonthView ────────────────────────────────────────────────────────────────

function MonthView({ currentDate, events, onEventClick, onDragStart, onDragEnd, onDrop, getColor }: {
  currentDate: Date
  events: Event[]
  onEventClick: (e: Event) => void
  onDragStart: (e: Event) => void
  onDragEnd: () => void
  onDrop: (date: Date) => void
  getColor: (v: string) => { bg: string }
}) {
  const firstDay = new Date(currentDate.getFullYear(), currentDate.getMonth(), 1)
  const startDate = new Date(firstDay)
  startDate.setDate(startDate.getDate() - startDate.getDay())

  const days: Date[] = []
  const cur = new Date(startDate)
  for (let i = 0; i < 42; i++) { days.push(new Date(cur)); cur.setDate(cur.getDate() + 1) }

  const eventsForDay = (d: Date) => events.filter(e => {
    const ed = new Date(e.startTime)
    return ed.getDate() === d.getDate() && ed.getMonth() === d.getMonth() && ed.getFullYear() === d.getFullYear()
  })

  return (
    <div className="rounded-xl border border-surface-600 overflow-hidden">
      {/* Dias da semana */}
      <div className="grid grid-cols-7 bg-surface-700 border-b border-surface-600">
        {DIAS_SEMANA_CURTO.map((d, i) => (
          <div key={i} className="py-2 text-center text-xs font-medium text-gray-400 border-r border-surface-600 last:border-r-0">
            <span className="hidden sm:inline">{d}</span>
            <span className="sm:hidden">{DIAS_SEMANA_MIN[i]}</span>
          </div>
        ))}
      </div>

      {/* Células */}
      <div className="grid grid-cols-7">
        {days.map((day, i) => {
          const dayEvents = eventsForDay(day)
          const isCurrentMonth = day.getMonth() === currentDate.getMonth()
          const isToday = day.toDateString() === new Date().toDateString()
          return (
            <div
              key={i}
              className={cn(
                "min-h-[80px] sm:min-h-[100px] border-b border-r border-surface-600 p-1.5 last:border-r-0 transition-colors",
                isCurrentMonth ? "bg-surface-800 hover:bg-surface-700/50" : "bg-surface-900/60",
              )}
              onDragOver={e => e.preventDefault()}
              onDrop={() => onDrop(day)}
            >
              <div className={cn(
                "mb-1 w-6 h-6 flex items-center justify-center rounded-full text-xs font-medium",
                isToday ? "bg-accent-blue text-white" : isCurrentMonth ? "text-gray-300" : "text-gray-600"
              )}>
                {day.getDate()}
              </div>
              <div className="space-y-0.5">
                {dayEvents.slice(0, 3).map(e => (
                  <EventPill key={e.id} event={e} onClick={onEventClick}
                    onDragStart={onDragStart} onDragEnd={onDragEnd}
                    getColor={getColor} variant="compact" />
                ))}
                {dayEvents.length > 3 && (
                  <p className="text-[10px] text-gray-500 pl-1">+{dayEvents.length - 3} mais</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </div>
  )
}

// ─── WeekView ─────────────────────────────────────────────────────────────────

function WeekView({ currentDate, events, onEventClick, onDragStart, onDragEnd, onDrop, getColor }: {
  currentDate: Date
  events: Event[]
  onEventClick: (e: Event) => void
  onDragStart: (e: Event) => void
  onDragEnd: () => void
  onDrop: (date: Date, hour: number) => void
  getColor: (v: string) => { bg: string }
}) {
  const startOfWeek = new Date(currentDate)
  startOfWeek.setDate(currentDate.getDate() - currentDate.getDay())

  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const d = new Date(startOfWeek)
    d.setDate(startOfWeek.getDate() + i)
    return d
  })

  const hours = Array.from({ length: 24 }, (_, i) => i)

  const eventsAt = (date: Date, hour: number) => events.filter(e => {
    const d = new Date(e.startTime)
    return d.getDate() === date.getDate() && d.getMonth() === date.getMonth()
      && d.getFullYear() === date.getFullYear() && d.getHours() === hour
  })

  return (
    <div className="rounded-xl border border-surface-600 overflow-auto">
      <div className="grid border-b border-surface-600 bg-surface-700" style={{ gridTemplateColumns: "56px repeat(7, 1fr)" }}>
        <div className="py-2 border-r border-surface-600" />
        {weekDays.map((d, i) => (
          <div key={i} className="py-2 text-center border-r border-surface-600 last:border-r-0">
            <p className="text-xs text-gray-400">{DIAS_SEMANA_CURTO[d.getDay()]}</p>
            <p className={cn("text-sm font-medium", d.toDateString() === new Date().toDateString() ? "text-accent-blue" : "text-gray-200")}>
              {d.getDate()}
            </p>
          </div>
        ))}
      </div>
      <div className="grid" style={{ gridTemplateColumns: "56px repeat(7, 1fr)" }}>
        {hours.map(hour => (
          <>
            <div key={`h-${hour}`} className="border-b border-r border-surface-600 p-1 text-[10px] text-gray-500 text-right pr-2 bg-surface-800">
              {hour.toString().padStart(2, "0")}h
            </div>
            {weekDays.map((day, di) => (
              <div
                key={`${hour}-${di}`}
                className="min-h-[48px] border-b border-r border-surface-600 last:border-r-0 p-0.5 bg-surface-800 hover:bg-surface-700/50 transition-colors"
                onDragOver={e => e.preventDefault()}
                onDrop={() => onDrop(day, hour)}
              >
                <div className="space-y-0.5">
                  {eventsAt(day, hour).map(e => (
                    <EventPill key={e.id} event={e} onClick={onEventClick}
                      onDragStart={onDragStart} onDragEnd={onDragEnd} getColor={getColor} />
                  ))}
                </div>
              </div>
            ))}
          </>
        ))}
      </div>
    </div>
  )
}

// ─── DayView ──────────────────────────────────────────────────────────────────

function DayView({ currentDate, events, onEventClick, onDragStart, onDragEnd, onDrop, getColor }: {
  currentDate: Date
  events: Event[]
  onEventClick: (e: Event) => void
  onDragStart: (e: Event) => void
  onDragEnd: () => void
  onDrop: (date: Date, hour: number) => void
  getColor: (v: string) => { bg: string }
}) {
  const hours = Array.from({ length: 24 }, (_, i) => i)
  const eventsAt = (hour: number) => events.filter(e => {
    const d = new Date(e.startTime)
    return d.getDate() === currentDate.getDate() && d.getMonth() === currentDate.getMonth()
      && d.getFullYear() === currentDate.getFullYear() && d.getHours() === hour
  })

  return (
    <div className="rounded-xl border border-surface-600 overflow-hidden">
      {hours.map(hour => (
        <div
          key={hour}
          className="flex border-b border-surface-600 last:border-b-0"
          onDragOver={e => e.preventDefault()}
          onDrop={() => onDrop(currentDate, hour)}
        >
          <div className="w-14 flex-shrink-0 border-r border-surface-600 py-2 px-2 text-xs text-gray-500 text-right bg-surface-800">
            {hour.toString().padStart(2, "0")}h
          </div>
          <div className="flex-1 min-h-[60px] p-1.5 bg-surface-800 hover:bg-surface-700/40 transition-colors space-y-1">
            {eventsAt(hour).map(e => (
              <EventPill key={e.id} event={e} onClick={onEventClick}
                onDragStart={onDragStart} onDragEnd={onDragEnd} getColor={getColor} variant="detailed" />
            ))}
          </div>
        </div>
      ))}
    </div>
  )
}

// ─── ListView ─────────────────────────────────────────────────────────────────

function ListView({ events, onEventClick, getColor }: {
  events: Event[]
  onEventClick: (e: Event) => void
  getColor: (v: string) => { bg: string }
}) {
  const sorted = [...events].sort((a, b) => a.startTime.getTime() - b.startTime.getTime())

  if (sorted.length === 0) {
    return (
      <div className="rounded-xl border border-surface-600 bg-surface-800 p-12 text-center">
        <p className="text-gray-500 text-sm">Nenhum evento encontrado</p>
      </div>
    )
  }

  const grouped: Record<string, Event[]> = {}
  sorted.forEach(e => {
    const key = e.startTime.toDateString()
    if (!grouped[key]) grouped[key] = []
    grouped[key].push(e)
  })

  return (
    <div className="space-y-4">
      {Object.entries(grouped).map(([key, dayEvents]) => (
        <div key={key}>
          <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2 capitalize">
            {format(new Date(key), "EEEE, d 'de' MMMM", { locale: ptBR })}
          </p>
          <div className="space-y-2">
            {dayEvents.map(e => {
              const c = getColor(e.color)
              return (
                <div
                  key={e.id}
                  onClick={() => onEventClick(e)}
                  className="flex items-start gap-3 bg-surface-800 border border-surface-600 rounded-xl px-4 py-3 cursor-pointer hover:bg-surface-700 transition-colors"
                >
                  <div className={cn("mt-1 h-3 w-3 rounded-full flex-shrink-0", c.bg)} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-2">
                      <p className="font-medium text-sm text-white truncate">{e.title}</p>
                      <span className="text-xs text-gray-400 whitespace-nowrap flex items-center gap-1">
                        <Clock size={11} />{fmtHora(e.startTime)} – {fmtHora(e.endTime)}
                      </span>
                    </div>
                    {e.description && <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{e.description}</p>}
                    {(e.category || (e.tags && e.tags.length > 0)) && (
                      <div className="flex flex-wrap gap-1 mt-1.5">
                        {e.category && <span className="text-[10px] px-2 py-0.5 rounded-full bg-surface-700 border border-surface-600 text-gray-300">{e.category}</span>}
                        {e.tags?.map(t => <span key={t} className="text-[10px] px-2 py-0.5 rounded-full border border-surface-600 text-gray-400">{t}</span>)}
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </div>
      ))}
    </div>
  )
}
