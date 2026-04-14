from fastapi import APIRouter
from datetime import date, datetime, timedelta, timezone
from ..database import get_supabase
from ..models.metrics import DashboardMetrics, FunnelStep, DayCount, TipoCount

router = APIRouter(prefix="/api/metrics", tags=["metrics"])

DIAS_PT = ["Dom", "Seg", "Ter", "Qua", "Qui", "Sex", "Sáb"]

STATUS_FUNNEL = [
    ("audiencias_encontradas", "Audiências encontradas", "#4f8ef7"),
    ("enviado", "Processos enviados", "#22c55e"),
    ("telefones", "Telefones encontrados", "#f59e0b"),
    ("mensagens", "Mensagens enviadas", "#a855f7"),
    ("respondido", "Responderam", "#ef4444"),
]

TIPO_COLORS = {
    "instrucao": "#4f8ef7",
    "una": "#22c55e",
    "conciliacao": "#f59e0b",
    "outra": "#6b7280",
}


@router.get("", response_model=DashboardMetrics)
def get_metrics():
    sb = get_supabase()
    today = date.today().isoformat()

    # Processos hoje
    proc_hoje = (
        sb.table("processos")
        .select("id", count="exact")
        .gte("data_audiencia", f"{today}T00:00:00")
        .lte("data_audiencia", f"{today}T23:59:59")
        .execute()
    )
    processos_hoje = proc_hoje.count or 0

    # Leads totais capturados
    leads_total = sb.table("leads").select("id", count="exact").execute()
    leads_capturados = leads_total.count or 0

    # Audiências encontradas total
    aud_total = sb.table("processos").select("id", count="exact").execute()
    audiencias_encontradas = aud_total.count or 0

    # Valor total em jogo
    valor_result = sb.table("processos").select("valor_causa").execute()
    valor_total = sum(
        (r.get("valor_causa") or 0) for r in (valor_result.data or [])
    )

    # Funil de conversão
    # audiências → com telefone → enviados → respondidos → convertidos
    tel_result = (
        sb.table("empresas")
        .select("telefones")
        .not_.is_("telefones", "null")
        .execute()
    )
    telefones_count = sum(1 for r in (tel_result.data or []) if r.get("telefones"))

    enviados = (
        sb.table("leads")
        .select("id", count="exact")
        .in_("status", ["enviado", "respondido", "convertido"])
        .execute()
    )
    enviados_count = enviados.count or 0

    respondidos = (
        sb.table("leads")
        .select("id", count="exact")
        .in_("status", ["respondido", "convertido"])
        .execute()
    )
    respondidos_count = respondidos.count or 0

    funnel = [
        FunnelStep(label="Audiências encontradas", count=audiencias_encontradas, color="#4f8ef7"),
        FunnelStep(label="Processos enviados", count=enviados_count, color="#22c55e"),
        FunnelStep(label="Telefones encontrados", count=telefones_count, color="#f59e0b"),
        FunnelStep(label="Mensagens enviadas", count=enviados_count, color="#a855f7"),
        FunnelStep(label="Responderam", count=respondidos_count, color="#ef4444"),
    ]

    # Audiências por dia da semana (últimos 7 dias)
    week_ago = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    procs_week = (
        sb.table("processos")
        .select("data_audiencia, numero_processo")
        .gte("data_audiencia", week_ago)
        .execute()
    )
    day_counts: dict[int, dict] = {i: {"multiplas": 0, "unica": 0} for i in range(7)}
    from collections import Counter
    day_proc_count: Counter = Counter()
    for p in (procs_week.data or []):
        dt_str = p.get("data_audiencia", "")
        try:
            dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            day_proc_count[dt.weekday()] += 1
        except Exception:
            pass

    for weekday, count in day_proc_count.items():
        if count > 1:
            day_counts[weekday]["multiplas"] = count
        else:
            day_counts[weekday]["unica"] = count

    # weekday() retorna 0=Mon..6=Sun; mapear para Dom=0..Sab=6
    audiencias_por_dia = []
    for i in range(7):
        # 0=Dom,1=Seg,...,6=Sáb → weekday: 6=Dom,0=Seg,...,5=Sáb
        weekday = (i - 1) % 7  # Dom corresponde a weekday 6
        counts = day_counts.get(weekday, {"multiplas": 0, "unica": 0})
        audiencias_por_dia.append(DayCount(
            dia=DIAS_PT[i],
            multiplas=counts["multiplas"],
            unica=counts["unica"],
        ))

    # Tipos de audiência
    tipos_result = sb.table("processos").select("tipo_audiencia").execute()
    tipo_counter: Counter = Counter()
    for p in (tipos_result.data or []):
        tipo_counter[p.get("tipo_audiencia", "outra")] += 1

    tipo_labels = {
        "instrucao": "Instrução",
        "una": "Una",
        "conciliacao": "Conciliação",
        "outra": "Outra",
    }
    tipos_audiencia = [
        TipoCount(
            tipo=tipo_labels.get(tipo, tipo),
            count=count,
            color=TIPO_COLORS.get(tipo, "#6b7280"),
        )
        for tipo, count in tipo_counter.items()
        if count > 0
    ]

    return DashboardMetrics(
        processos_hoje=processos_hoje,
        leads_capturados=leads_capturados,
        audiencias_encontradas=audiencias_encontradas,
        valor_total=valor_total,
        funnel=funnel,
        audiencias_por_dia=audiencias_por_dia,
        tipos_audiencia=tipos_audiencia,
    )
