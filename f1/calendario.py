# -*- coding: utf-8 -*-
"""Orden de carreras, proxima fecha y panel visual del calendario."""

import re
from datetime import datetime, timezone
from typing import List, Tuple

from .config import CALENDARIO, FLAG_MAP

def get_orden_carreras() -> List[str]:
    orden = []
    for entry in CALENDARIO:
        nombre_raw = entry["Carrera"]
        if "<s>" in nombre_raw:
            continue
        nombre = re.sub(r'<[^>]+>', '', nombre_raw).strip().capitalize()
        if nombre not in orden:
            orden.append(nombre)
    return orden
def carreras_en_orden(available: List[str]) -> List[str]:
    orden_cal = get_orden_carreras()
    available_set = set(available)
    ordenadas = [c for c in orden_cal if c in available_set]
    for c in available:
        if c not in ordenadas:
            ordenadas.append(c)
    return ordenadas
def obtener_proxima_carrera() -> Tuple[str, str]:
    ahora = datetime.now(timezone.utc)
    for item in CALENDARIO:
        if item.get("FechaISO") is None:
            continue
        try:
            fecha = datetime.fromisoformat(item["FechaISO"])
            if fecha > ahora:
                return item["Carrera"], item["FechaISO"]
        except Exception:
            continue
    return "FIN DE TEMPORADA", ""
def generar_calendario_visual(proxima_iso: str) -> str:
    ahora_utc = datetime.now(timezone.utc)
    total_validas = sum(1 for e in CALENDARIO if e.get("FechaISO"))
    completadas = 0
    proxima_encontrada = False
    cal_cards = []

    STATUS_LABEL = {
        "past": "Completada", "next": "Próxima",
        "future": "Pendiente", "cancelled": "Cancelada"
    }
    STATUS_CLASS = {
        "past": "status-done", "next": "status-next",
        "future": "status-future", "cancelled": "status-cancel"
    }

    for entry in CALENDARIO:
        raw_nombre  = entry["Carrera"]
        raw_jornada = entry["Jornada"]
        is_cancelled = "<s>" in raw_nombre

        nombre_limpio  = re.sub(r'<[^>]+>', '', raw_nombre).strip()
        jornada_limpio = re.sub(r'<[^>]+>', '', raw_jornada).strip()
        fecha_limpio   = re.sub(r'<[^>]+>', '', entry["Fecha"]).strip()
        hora_arg_limpio = re.sub(r'<[^>]+>', '', entry["Hora Argentina"]).strip()

        nombre_key = nombre_limpio.capitalize()
        flag = FLAG_MAP.get(nombre_key, "🏁")
        if flag == "🏁":
            for k, v in FLAG_MAP.items():
                if k.lower() == nombre_limpio.lower():
                    flag = v
                    break

        iso = entry.get("FechaISO")

        if is_cancelled or iso is None:
            status = "cancelled"
        else:
            try:
                fecha_dt = datetime.fromisoformat(iso)
                if fecha_dt < ahora_utc:
                    status = "past"
                    completadas += 1
                elif not proxima_encontrada:
                    status = "next"
                    proxima_encontrada = True
                else:
                    status = "future"
            except Exception:
                status = "future"

        def td(s):
            return f"<s>{s}</s>" if is_cancelled else s

        pill = (f'<span class="status-pill {STATUS_CLASS[status]}">'
                f'<span class="dot"></span>{STATUS_LABEL[status]}</span>')

        cd_html = ""
        if status == "next":
            cd_html = (
                '<div class="cd-mini">'
                '<div class="cd-mini-label">Faltan</div>'
                '<div class="cd-mini-nums">'
                '<div class="cd-num" id="cdn-d">--</div>'
                '<span class="cd-sep">:</span>'
                '<div class="cd-num" id="cdn-h">--</div>'
                '<span class="cd-sep">:</span>'
                '<div class="cd-num" id="cdn-m">--</div>'
                '<span class="cd-sep">:</span>'
                '<div class="cd-num" id="cdn-s">--</div>'
                '</div>'
                '<div class="cd-unit-row" style="display:flex;gap:0;margin-top:3px;">'
                '<span class="cd-unit" style="min-width:30px;text-align:center;">días</span>'
                '<span class="cd-unit" style="min-width:14px;"></span>'
                '<span class="cd-unit" style="min-width:30px;text-align:center;">hrs</span>'
                '<span class="cd-unit" style="min-width:14px;"></span>'
                '<span class="cd-unit" style="min-width:30px;text-align:center;">min</span>'
                '<span class="cd-unit" style="min-width:14px;"></span>'
                '<span class="cd-unit" style="min-width:30px;text-align:center;">seg</span>'
                '</div>'
                '</div>'
            )

        card = (
            f'<div class="cal-card {status} reveal">'
            f'<span class="rnd-badge">{td(jornada_limpio)}</span>'
            f'<span class="cal-flag">{flag}</span>'
            f'<div class="cal-name">{td(nombre_limpio)}</div>'
            f'<div class="cal-date-row">{td(fecha_limpio)}</div>'
            f'<div class="cal-time-arg">ARG {td(hora_arg_limpio)}</div>'
            f'{pill}'
            f'{cd_html}'
            f'</div>'
        )
        cal_cards.append(card)

    pct = round(completadas / total_validas * 100) if total_validas > 0 else 0
    canceladas_n = sum(1 for e in CALENDARIO if "<s>" in e["Carrera"] or e.get("FechaISO") is None)

    return f"""
<div style="display:flex;gap:10px;margin-bottom:20px;flex-wrap:wrap;align-items:center;">
    <div class="section-label" style="margin:0;">Progreso de temporada:</div>
    <div style="flex:1;min-width:120px;max-width:340px;">
        <div class="cal-progress-bar">
            <div class="cal-progress-fill" style="width:{pct}%;"></div>
        </div>
    </div>
    <div style="font-size:.78rem;color:var(--muted);font-weight:600;">
        {completadas}/{total_validas} carreras · {canceladas_n} canceladas
    </div>
</div>
<div class="cal-grid">
{''.join(cal_cards)}
</div>"""
