# -*- coding: utf-8 -*-
"""Sistema de logros: definicion de los badges y quien los desbloqueo."""

import pandas as pd
from typing import Dict, List

from .calendario import carreras_en_orden
from .paleta import color_participante, hex_a_rgba
from .scoring import calcular_historial_posiciones


BADGES = {
    "francotirador":  {
        "emoji": "🎯", "nombre": "Francotirador",       "nivel": "BRONCE",    "nivel_emoji": "🥉", "hex": "#E74C3C",
        "desc_corta":  "Acertar P1 exacto en 5 carreras distintas",
        "desc_larga":  "No tienen que ser seguidas. Pero acertar 5 ganadores en 22 carreras requiere leer bien hasta las fechas más impredecibles.",
        "criterio":    "Acertar la posición exacta del ganador (P1) en 5 o más carreras de la temporada.",
        "progreso_max": 5,
    },
    "racha_caliente": {
        "emoji": "🔥", "nombre": "Racha Caliente",       "nivel": "BRONCE",    "nivel_emoji": "🥉", "hex": "#E67E22",
        "desc_corta":  "Top-3 del grupo en 3 carreras consecutivas",
        "desc_larga":  "Sostener el nivel sin un solo tropiezo durante tres fechas seguidas. La consistencia a corto plazo tiene su recompensa.",
        "criterio":    "Terminar en el top-3 del ranking grupal en 3 carreras consecutivas.",
        "progreso_max": 3,
    },
    "hincha_franco":  {
        "emoji": "🇦🇷", "nombre": "Hincha de Franco",   "nivel": "BRONCE",    "nivel_emoji": "🥉", "hex": "#3498DB",
        "desc_corta":  "Posición exacta de Colapinto en 4 carreras",
        "desc_larga":  "Con su variabilidad de resultados, acertar 4 posiciones exactas de Franco Colapinto es una hazaña real.",
        "criterio":    "Acertar la posición exacta de Franco Colapinto en 4 o más carreras.",
        "progreso_max": 4,
    },
    "bomba_puntos":   {
        "emoji": "💣", "nombre": "Bomba de Puntos",      "nivel": "BRONCE",    "nivel_emoji": "🥉", "hex": "#C0392B",
        "desc_corta":  "Top-1 absoluto en puntaje en 4 carreras distintas",
        "desc_larga":  "Ganar una fecha es suerte. Ganar cuatro en la temporada es dominio real. Sin empates, techo absoluto del grupo.",
        "criterio":    "Ser el máximo anotador individual del grupo en 4 o más carreras distintas.",
        "progreso_max": 4,
    },
    "adivino":        {
        "emoji": "🔮", "nombre": "Adivino",              "nivel": "BRONCE",    "nivel_emoji": "🥉", "hex": "#9B59B6",
        "desc_corta":  "5+ aciertos exactos en una sola carrera",
        "desc_larga":  "Acertar la mitad exacta de las 10 posiciones predichas es estadísticamente raro con 20 pilotos en pista.",
        "criterio":    "Lograr 5 o más predicciones de posición exacta en una misma carrera.",
        "progreso_max": 5,
    },
    "muralla":        {
        "emoji": "🛡️", "nombre": "Muralla",              "nivel": "PLATA",     "nivel_emoji": "🥈", "hex": "#95A5A6",
        "desc_corta":  "Nunca terminar último en el ranking de ninguna carrera",
        "desc_larga":  "Con 10-12 jugadores, evitar el fondo absoluto durante toda la temporada es un logro de consistencia pura.",
        "criterio":    "No terminar nunca último en el ranking individual de ninguna carrera disputada.",
        "progreso_max": 22,
    },
    "remontada_epica":{
        "emoji": "📈", "nombre": "Remontada Épica",       "nivel": "PLATA",     "nivel_emoji": "🥈", "hex": "#27AE60",
        "desc_corta":  "De los últimos 3 del ranking a top-3 en 4 fechas",
        "desc_larga":  "La remontada tiene que ser profunda (desde el fondo) y sostenida (mantenerse 4 fechas consecutivas en el top).",
        "criterio":    "Pasar de los últimos 3 del ranking general a top-3 y sostenerlo 4 fechas seguidas.",
        "progreso_max": 1,
    },
    "estratega":      {
        "emoji": "🧠", "nombre": "Estratega",             "nivel": "PLATA",     "nivel_emoji": "🥈", "hex": "#16A085",
        "desc_corta":  "Top-5 completo exacto (P1-P5 en orden) en una carrera",
        "desc_larga":  "Cinco posiciones exactas de diez en una carrera de F1. Brutal. La probabilidad estadística es mínima.",
        "criterio":    "Acertar P1, P2, P3, P4 y P5 exactos en orden en una misma carrera.",
        "progreso_max": 1,
    },
    "consistente":    {
        "emoji": "⚙️", "nombre": "Consistente",           "nivel": "PLATA",     "nivel_emoji": "🥈", "hex": "#7F8C8D",
        "desc_corta":  "Top-50% del grupo en 17 de las 22 carreras",
        "desc_larga":  "Solo 5 fechas malas permitidas en toda la temporada. No hay margen para rachas negativas prolongadas.",
        "criterio":    "Terminar en el top-50% del grupo en al menos 17 de las 22 carreras.",
        "progreso_max": 17,
    },
    "apostador_nato": {
        "emoji": "🎰", "nombre": "Apostador Nato",         "nivel": "PLATA",     "nivel_emoji": "🥈", "hex": "#8E44AD",
        "desc_corta":  "Acierto exacto entre P7-P10 en 6 carreras distintas",
        "desc_larga":  "La zona del caos total. Acertar 6 posiciones exactas entre P7 y P10 a lo largo de la temporada es excepcional.",
        "criterio":    "Acertar una posición exacta entre P7 y P10 en 6 o más carreras distintas.",
        "progreso_max": 6,
    },
    "marea_alta":     {
        "emoji": "🌊", "nombre": "Marea Alta",             "nivel": "ORO",       "nivel_emoji": "🥇", "hex": "#2471A3",
        "desc_corta":  "Top-1 del grupo en 7 o más carreras individuales",
        "desc_larga":  "Una de cada tres carreras tiene que ser tuya. Ganar el ranking general y este badge a la vez es rarísimo.",
        "criterio":    "Ser el top-1 del grupo en el puntaje individual de 7 o más carreras.",
        "progreso_max": 7,
    },
    "arquitecto":     {
        "emoji": "🏗️", "nombre": "Arquitecto",             "nivel": "ORO",       "nivel_emoji": "🥇", "hex": "#D35400",
        "desc_corta":  "Mayor puntaje acumulado en predicciones P6-P10",
        "desc_larga":  "Premia el conocimiento profundo del pelotón medio, no solo adivinar a los favoritos de siempre.",
        "criterio":    "Tener el mayor puntaje acumulado del grupo en predicciones de P6 a P10.",
        "progreso_max": 1,
    },
    "oraculo":        {
        "emoji": "🌌", "nombre": "Oráculo",                "nivel": "LEGENDARIO","nivel_emoji": "💎", "hex": "#4A90E2",
        "desc_corta":  "Podio exacto (P1, P2 y P3) en 5 carreras distintas",
        "desc_larga":  "El podio exacto cinco veces. La probabilidad estadística de lograrlo en una sola carrera ya es ridículamente baja.",
        "criterio":    "Acertar el podio completo (P1, P2 y P3 en orden exacto) en 5 o más carreras.",
        "progreso_max": 5,
    },
    "perfeccionista": {
        "emoji": "💎", "nombre": "Perfeccionista",          "nivel": "LEGENDARIO","nivel_emoji": "💎", "hex": "#00BCD4",
        "desc_corta":  "7+ aciertos exactos en una sola carrera",
        "desc_larga":  "Casi imposible. Si alguien lo logra en alguna fecha, es el momento de la temporada. Estadísticamente brutal.",
        "criterio":    "Lograr 7 o más predicciones de posición exacta en una misma carrera.",
        "progreso_max": 7,
    },
    "rey_temporada":  {
        "emoji": "👑", "nombre": "Rey de la Temporada",    "nivel": "CAMPEÓN",   "nivel_emoji": "🏆", "hex": "#F39C12",
        "desc_corta":  "Primero en el ranking general al cierre de la temporada",
        "desc_larga":  "El logro más grande del torneo. Solo uno puede tenerlo por temporada. No hay nada por encima de este badge.",
        "criterio":    "Liderar el ranking general acumulado al cierre de la temporada.",
        "progreso_max": 1,
    },
}


NIVEL_CONFIG = {
    "BRONCE":    {"color": "#CD7F32", "bg": "rgba(205,127,50,0.08)",  "border": "rgba(205,127,50,0.25)",  "label": "🥉 BRONCE",    "order": 1},
    "PLATA":     {"color": "#C0C0C0", "bg": "rgba(192,192,192,0.08)", "border": "rgba(192,192,192,0.25)", "label": "🥈 PLATA",     "order": 2},
    "ORO":       {"color": "#FFD700", "bg": "rgba(255,215,0,0.08)",   "border": "rgba(255,215,0,0.3)",    "label": "🥇 ORO",       "order": 3},
    "LEGENDARIO":{"color": "#4A90E2", "bg": "rgba(74,144,226,0.08)",  "border": "rgba(74,144,226,0.3)",   "label": "💎 LEGENDARIO","order": 4},
    "CAMPEÓN":   {"color": "#F39C12", "bg": "rgba(243,156,18,0.08)",  "border": "rgba(243,156,18,0.3)",   "label": "🏆 CAMPEÓN",   "order": 5},
}


def calcular_pts_p6_p10(detalles_str: str) -> int:
    total = 0
    for line in detalles_str.split('<br>'):
        for pos in range(6, 11):
            if f'Exacto en P{pos}' in line:
                total += 10; break
            elif f'pred P{pos},' in line:
                if '+5' in line:   total += 5
                elif '+1' in line: total += 1
                break
    return total


def calcular_badges(all_rankings: pd.DataFrame, all_dfs: List[pd.DataFrame],
                    ranking_acumulado: pd.DataFrame) -> Dict[str, List[Dict]]:
    if all_rankings.empty or ranking_acumulado.empty:
        return {}

    df_all = pd.concat(all_dfs) if all_dfs else pd.DataFrame()
    historial  = calcular_historial_posiciones(all_rankings)
    carreras   = carreras_en_orden(all_rankings['Carrera'].unique().tolist())
    n_part     = ranking_acumulado.shape[0]
    n_disp     = len(carreras)

    per_race_pos: Dict[str, Dict[str, int]] = {}
    for _, row in all_rankings.iterrows():
        em = row['Participante']
        per_race_pos.setdefault(em, {})[row['Carrera']] = int(row['Posición'])

    n_part_per_race: Dict[str, int] = {
        c: int(all_rankings[all_rankings['Carrera'] == c]['Participante'].nunique())
        for c in carreras
    }

    cumul_pos: Dict[str, Dict[str, int]] = {}
    if not historial.empty:
        for _, row in historial.iterrows():
            em = row['Participante']
            cumul_pos.setdefault(em, {})[row['Carrera']] = int(row['Posición'])

    top1_per_race: Dict[str, List[str]] = {}
    for c in carreras:
        sub = all_rankings[all_rankings['Carrera'] == c]
        if not sub.empty:
            mx = sub['Puntos'].max()
            top1_per_race[c] = sub[sub['Puntos'] == mx]['Participante'].tolist()

    arch_pts: Dict[str, int] = {
        em: sum(
            calcular_pts_p6_p10(str(r['Detalles']))
            for _, r in df_all[df_all['Participante'] == em].iterrows()
        )
        for em in ranking_acumulado['Participante']
    } if not df_all.empty else {}
    max_arch = max(arch_pts.values(), default=0)

    def exactos_en_fila(det: str) -> int:
        return sum(1 for d in str(det).split('<br>') if 'Exacto en P' in d)

    badges_resultado: Dict[str, List[Dict]] = {}

    for _, acum_row in ranking_acumulado.iterrows():
        participante    = acum_row['Participante']
        pos_gral = int(acum_row['Posición'])
        badges: List[Dict] = []

        part_df = df_all[df_all['Participante'] == participante] \
                  if not df_all.empty else pd.DataFrame()
        my_rp   = per_race_pos.get(participante, {})
        my_cp   = cumul_pos.get(participante, {})

        # 🎯 FRANCOTIRADOR
        p1_ok = sum(1 for _, r in part_df.iterrows() if 'Exacto en P1' in str(r['Detalles']))
        if p1_ok >= 5:
            badges.append({**BADGES["francotirador"],
                "desc": (f"{BADGES['francotirador']['nivel_emoji']} BRONCE · "
                         f"Acertaste el ganador exacto en {p1_ok} carreras. "
                         f"Criterio: 5+ aciertos de P1 en la temporada.")})

        # 🔥 RACHA CALIENTE
        consec = max_consec = 0
        for c in carreras:
            p = my_rp.get(c)
            if p is not None and p <= 3:
                consec += 1; max_consec = max(max_consec, consec)
            else:
                consec = 0
        if max_consec >= 3:
            badges.append({**BADGES["racha_caliente"],
                "desc": (f"{BADGES['racha_caliente']['nivel_emoji']} BRONCE · "
                         f"Quedaste en el top-3 del grupo {max_consec} carreras seguidas. "
                         f"Criterio: 3+ fechas consecutivas en el podio grupal.")})

        # 🇦🇷 HINCHA DE FRANCO
        cola_ok = sum(1 for _, r in part_df.iterrows() if 'Colapinto: EXACTO' in str(r['Detalles']))
        if cola_ok >= 4:
            badges.append({**BADGES["hincha_franco"],
                "desc": (f"{BADGES['hincha_franco']['nivel_emoji']} BRONCE · "
                         f"Acertaste la posición exacta de Franco Colapinto en {cola_ok} carreras. "
                         f"Criterio: 4+ aciertos exactos.")})

        # 💣 BOMBA DE PUNTOS
        bomba_n = sum(1 for c in carreras if participante in top1_per_race.get(c, []))
        if bomba_n >= 4:
            badges.append({**BADGES["bomba_puntos"],
                "desc": (f"{BADGES['bomba_puntos']['nivel_emoji']} BRONCE · "
                         f"Fuiste el máximo anotador del grupo en {bomba_n} carreras distintas. "
                         f"Criterio: 4+ victorias de fecha.")})

        # 🔮 ADIVINO
        adivino_max = adivino_carrera = 0
        for _, r in part_df.iterrows():
            ex = exactos_en_fila(r['Detalles'])
            if ex > adivino_max:
                adivino_max = ex; adivino_carrera = r['Carrera']
        if adivino_max >= 5:
            badges.append({**BADGES["adivino"],
                "desc": (f"{BADGES['adivino']['nivel_emoji']} BRONCE · "
                         f"Lograste {adivino_max} predicciones exactas en {adivino_carrera}. "
                         f"Criterio: 5+ aciertos exactos en una carrera (sobre 10).")})

        # 🛡️ MURALLA
        muralla = all(
            my_rp.get(c, 1) < n_part_per_race.get(c, n_part)
            for c in carreras
        ) and n_disp > 0
        if muralla:
            badges.append({**BADGES["muralla"],
                "desc": (f"{BADGES['muralla']['nivel_emoji']} PLATA · "
                         f"Nunca terminaste en el último lugar del ranking en ninguna "
                         f"de las {n_disp} carreras disputadas.")})

        # 📈 REMONTADA ÉPICA
        remontada_epica = False
        if len(carreras) >= 5:
            for i in range(len(carreras) - 4):
                pos_t = my_cp.get(carreras[i])
                if pos_t is None or pos_t < (n_part - 2):
                    continue
                siguientes = [my_cp.get(carreras[i + j + 1]) for j in range(4)]
                if all(p is not None and p <= 3 for p in siguientes):
                    remontada_epica = True; break
        if remontada_epica:
            badges.append({**BADGES["remontada_epica"],
                "desc": (f"{BADGES['remontada_epica']['nivel_emoji']} PLATA · "
                         f"Pasaste de estar en los últimos 3 del ranking general a top-3 y "
                         f"lo sostuviste 4 carreras seguidas.")})

        # 🧠 ESTRATEGA
        estratega_carrera = None
        for _, r in part_df.iterrows():
            if all(f'Exacto en P{p}' in str(r['Detalles']) for p in range(1, 6)):
                estratega_carrera = r['Carrera']; break
        if estratega_carrera:
            badges.append({**BADGES["estratega"],
                "desc": (f"{BADGES['estratega']['nivel_emoji']} PLATA · "
                         f"Acertaste P1, P2, P3, P4 y P5 exactos en orden en {estratega_carrera}. "
                         f"Cinco posiciones exactas de una. Brutal.")})

        # ⚙️ CONSISTENTE
        umbral_50 = n_part / 2
        top50_n = sum(1 for c in carreras if (my_rp.get(c) or 999) <= umbral_50)
        if top50_n >= 17:
            badges.append({**BADGES["consistente"],
                "desc": (f"{BADGES['consistente']['nivel_emoji']} PLATA · "
                         f"Terminaste en el top-50% del grupo en {top50_n} de las {n_disp} "
                         f"carreras disputadas. Criterio: 17+ fechas en la mitad superior.")})

        # 🎰 APOSTADOR NATO
        apuesta_carreras = set()
        for _, r in part_df.iterrows():
            det = str(r['Detalles'])
            if any(f'Exacto en P{p}' in det for p in range(7, 11)):
                apuesta_carreras.add(r['Carrera'])
        if len(apuesta_carreras) >= 6:
            badges.append({**BADGES["apostador_nato"],
                "desc": (f"{BADGES['apostador_nato']['nivel_emoji']} PLATA · "
                         f"Acertaste una posición exacta entre P7 y P10 en "
                         f"{len(apuesta_carreras)} carreras distintas. "
                         f"Criterio: 6+ carreras. La zona del caos total.")})

        # 🌊 MAREA ALTA
        marea_n = sum(1 for c in carreras if participante in top1_per_race.get(c, []))
        if marea_n >= 7:
            badges.append({**BADGES["marea_alta"],
                "desc": (f"{BADGES['marea_alta']['nivel_emoji']} ORO · "
                         f"Fuiste el top-1 del grupo en {marea_n} carreras individuales. "
                         f"Criterio: 7+ victorias de fecha.")})

        # 🏗️ ARQUITECTO (se comparte en empate)
        if max_arch > 0 and arch_pts.get(participante, 0) == max_arch:
            badges.append({**BADGES["arquitecto"],
                "desc": (f"{BADGES['arquitecto']['nivel_emoji']} ORO · "
                         f"Mayor puntaje del grupo en predicciones de P6 a P10: "
                         f"{arch_pts.get(participante,0)} pts.")})

        # 🌌 ORÁCULO
        oraculo_n = sum(
            1 for _, r in part_df.iterrows()
            if all(f'Exacto en P{p}' in str(r['Detalles']) for p in range(1, 4))
        )
        if oraculo_n >= 5:
            badges.append({**BADGES["oraculo"],
                "desc": (f"{BADGES['oraculo']['nivel_emoji']} LEGENDARIO · "
                         f"Acertaste el podio completo (P1, P2 y P3 exactos en orden) en "
                         f"{oraculo_n} carreras. Criterio: 5+ carreras.")})

        # 💎 PERFECCIONISTA
        perf_max = perf_carrera = 0
        for _, r in part_df.iterrows():
            ex = exactos_en_fila(r['Detalles'])
            if ex > perf_max:
                perf_max = ex; perf_carrera = r['Carrera']
        if perf_max >= 7:
            badges.append({**BADGES["perfeccionista"],
                "desc": (f"{BADGES['perfeccionista']['nivel_emoji']} LEGENDARIO · "
                         f"Lograste {perf_max} predicciones exactas en {perf_carrera}. "
                         f"Criterio: 7+ aciertos exactos en una carrera.")})

        # 👑 REY DE LA TEMPORADA
        if pos_gral == 1:
            badges.append({**BADGES["rey_temporada"],
                "desc": (f"{BADGES['rey_temporada']['nivel_emoji']} CAMPEÓN · "
                         f"Líder del ranking general acumulado. "
                         f"El logro más grande del torneo. Solo uno puede tenerlo.")})

        badges_resultado[participante] = badges

    return badges_resultado


def generar_logros_panel_html(badges_por_participante: dict) -> str:
    ganadores_por_badge: dict = {k: [] for k in BADGES}
    for participante, badges in badges_por_participante.items():
        nombre = participante
        for b in badges:
            for key, meta in BADGES.items():
                if meta["nombre"] == b["nombre"]:
                    ganadores_por_badge[key].append(nombre)
                    break

    ranking_badges = sorted(
        [(participante, len(badges)) for participante, badges in badges_por_participante.items()],
        key=lambda x: -x[1]
    )

    total_badges_posibles = len(BADGES)

    lideres_rows = ""
    for i, (nombre, n) in enumerate(ranking_badges):
        color = color_participante(nombre)
        pct = round(n / total_badges_posibles * 100)
        bar_width = max(4, pct)
        lideres_rows += f"""
        <div class="logros-lider-row">
            <div class="logros-lider-left">
                <span class="logros-lider-pos" style="color:{color};">#{i+1}</span>
                <span class="logros-lider-nombre" style="color:{color};">{nombre}</span>
            </div>
            <div class="logros-lider-bar-wrap">
                <div class="logros-lider-bar-fill" style="width:{bar_width}%;background:{color};"></div>
            </div>
            <div class="logros-lider-right">
                <span class="logros-lider-count">{n}</span>
                <span class="logros-lider-total">/{total_badges_posibles}</span>
            </div>
        </div>"""

    niveles_html = ""
    for nivel_key in ["BRONCE","PLATA","ORO","LEGENDARIO","CAMPEÓN"]:
        nc = NIVEL_CONFIG[nivel_key]
        badges_del_nivel = {k: v for k, v in BADGES.items() if v["nivel"] == nivel_key}

        cards_html = ""
        for badge_key, meta in badges_del_nivel.items():
            ganadores = ganadores_por_badge.get(badge_key, [])
            desbloqueado = len(ganadores) > 0
            hex_color = meta["hex"]

            bg_card   = hex_a_rgba(hex_color, 0.07 if desbloqueado else 0.03)
            border_c  = hex_a_rgba(hex_color, 0.35 if desbloqueado else 0.12)
            emoji_bg  = hex_a_rgba(hex_color, 0.15 if desbloqueado else 0.06)
            text_col  = hex_color if desbloqueado else "#444444"
            name_col  = "#FFFFFF" if desbloqueado else "#555555"
            desc_col  = "#AAAAAA" if desbloqueado else "#444444"
            long_col  = "#888888" if desbloqueado else "#333333"
            lock_icon = "" if desbloqueado else '<span class="badge-lock">🔒</span>'

            ganadores_html = ""
            if ganadores:
                ganadores_html = '<div class="badge-ganadores">'
                for g in ganadores:
                    ganadores_html += f'<span class="badge-ganador-chip">{g}</span>'
                ganadores_html += '</div>'
            else:
                ganadores_html = '<div class="badge-ganadores"><span class="badge-nadie">Sin desbloquear aún</span></div>'

            cards_html += f"""
            <div class="logro-card {'logro-desbloqueado' if desbloqueado else 'logro-bloqueado'}"
                 style="background:{bg_card};border:1px solid {border_c};">
                {lock_icon}
                <div class="logro-emoji-wrap" style="background:{emoji_bg};border:1px solid {border_c};">
                    <span class="logro-emoji">{meta['emoji']}</span>
                </div>
                <div class="logro-content">
                    <div class="logro-nombre" style="color:{name_col};">{meta['nombre']}</div>
                    <div class="logro-desc-corta" style="color:{text_col};">{meta['desc_corta']}</div>
                    <div class="logro-desc-larga" style="color:{long_col};">{meta['desc_larga']}</div>
                    {ganadores_html}
                </div>
            </div>"""

        niveles_html += f"""
        <div class="logros-nivel-block">
            <div class="logros-nivel-header" style="border-left:3px solid {nc['color']};">
                <span class="logros-nivel-label" style="color:{nc['color']};">{nc['label']}</span>
                <span class="logros-nivel-sub">
                    {sum(1 for k in badges_del_nivel if ganadores_por_badge.get(k))} / {len(badges_del_nivel)} desbloqueados
                </span>
            </div>
            <div class="logros-cards-grid">
                {cards_html}
            </div>
        </div>"""

    total_otorgados = sum(len(v) for v in ganadores_por_badge.values())
    total_unicos    = sum(1 for v in ganadores_por_badge.values() if v)

    leyenda_niveles = "".join(f'''<div class="logros-leyenda-row">
        <span class="logros-leyenda-dot" style="background:{NIVEL_CONFIG[n]["color"]};box-shadow:0 0 8px {NIVEL_CONFIG[n]["color"]}44;"></span>
        <span class="logros-leyenda-label" style="color:{NIVEL_CONFIG[n]["color"]};">{NIVEL_CONFIG[n]["label"]}</span>
    </div>''' for n in ["BRONCE","PLATA","ORO","LEGENDARIO","CAMPEÓN"])

    return f"""
<div id="panel-logros" class="tab-panel">
    <div class="logros-hero">
        <div class="logros-hero-bg"></div>
        <div class="logros-hero-content">
            <div class="logros-eyebrow">Sistema de Logros</div>
            <h2 class="logros-title">HAL<span>L OF</span><br>FAME</h2>
            <p class="logros-subtitle">15 badges · 5 niveles · 22 carreras · Solo los mejores los desbloquean</p>
            <div class="logros-hero-stats">
                <div class="logros-hero-stat">
                    <span class="logros-hero-num">{total_otorgados}</span>
                    <span class="logros-hero-desc">Badges otorgados</span>
                </div>
                <div class="logros-hero-divider"></div>
                <div class="logros-hero-stat">
                    <span class="logros-hero-num">{total_unicos}</span>
                    <span class="logros-hero-desc">Badges desbloqueados</span>
                </div>
                <div class="logros-hero-divider"></div>
                <div class="logros-hero-stat">
                    <span class="logros-hero-num">{total_badges_posibles}</span>
                    <span class="logros-hero-desc">Total disponibles</span>
                </div>
            </div>
        </div>
    </div>

    <div class="logros-main-grid">
        <div class="logros-sidebar">
            <div class="logros-sidebar-inner">
                <div class="logros-sidebar-title">🏆 Ranking de Logros</div>
                <div class="logros-sidebar-sub">Quién tiene más badges desbloqueados</div>
                <div class="logros-lideres-list">
                    {lideres_rows}
                </div>
                <div class="logros-leyenda">
                    <div class="logros-sidebar-title" style="margin-top:0;">Niveles de dificultad</div>
                    {leyenda_niveles}
                </div>
            </div>
        </div>
        <div class="logros-catalogo">
            {niveles_html}
        </div>
    </div>
</div>"""
