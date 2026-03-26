# ==============================================================================
# DASHBOARD DE CONFIABILIDAD OPERACIONAL — VERSIÓN RESPONSIVE V4
# Análisis de Impacto — Modernización del Estátor
# Unidad de Generación N.° 1 — Central Hidroeléctrica Playas — EPM
# Elaborado por Jaime Alonso Rúa Marín — Ingeniero Electronico
# ==============================================================================
# Elaboró base: Jaime Alonso Rúa Marín
# Optimización responsive: ChatGPT
# Área de Instrumentación, Control y Protección
# Empresas Públicas de Medellín E.S.P.
# ==============================================================================

import os
import io
import warnings
import numpy as np
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

warnings.filterwarnings("ignore")

# ==============================================================================
# CONFIGURACIÓN DE PÁGINA
# ==============================================================================
st.set_page_config(
    page_title="Dashboard Confiabilidad U1 — Central Playas EPM",
    layout="wide",
    page_icon="⚡",
    initial_sidebar_state="expanded"
)

# ==============================================================================
# PALETA BASE
# ==============================================================================
C_ANTES   = "#1565C0"
C_DESPUES = "#1B7A4E"
C_DELTA   = "#E65100"
C_ALERTA  = "#C00000"
C_MORADO  = "#6A1B9A"
C_GRIS    = "#666666"
C_NEGRO   = "#111111"

# ==============================================================================
# FUNCIONES DE TEMA
# ==============================================================================
def get_theme_config(theme_name: str):
    if theme_name == "Oscuro":
        return {
            "bg_main": "#0f1117",
            "bg_card": "#161b22",
            "bg_panel": "#161b22",
            "text_main": "#f0f3f6",
            "text_soft": "#b8c0cc",
            "header_grad_1": "#000000",
            "header_grad_2": "#111827",
            "header_grad_3": "#1f2937",
            "border_left": "#3a7d3a",
            "plot_bg": "#ffffff",
            "paper_bg": "#ffffff",
            "box_shadow": "0 4px 14px rgba(0,0,0,0.28)"
        }
    return {
        "bg_main": "#f6f8fb",
        "bg_card": "#ffffff",
        "bg_panel": "#ffffff",
        "text_main": "#111111",
        "text_soft": "#666666",
        "header_grad_1": "#000000",
        "header_grad_2": "#161616",
        "header_grad_3": "#2a2a2a",
        "border_left": "#3a7d3a",
        "plot_bg": "#ffffff",
        "paper_bg": "#ffffff",
        "box_shadow": "0 2px 12px rgba(0,0,0,0.07)"
    }

# ==============================================================================
# FUNCIONES AUXILIARES
# ==============================================================================
def fmt_temp(v):
    return f"{v:.1f}°C" if v is not None else "—"

def fmt_num(v):
    return f"{v:.1f}" if v is not None else "—"

def stats(data, col):
    if col not in data.columns:
        return None, None, None, None, None
    v = pd.to_numeric(data[col], errors="coerce").dropna()
    if len(v) == 0:
        return None, None, None, None, None
    return (
        round(float(v.mean()), 1),
        round(float(v.min()), 1),
        round(float(v.max()), 1),
        round(float(v.std()), 1),
        round(float(v.quantile(0.95)), 1),
    )

def clasificar_estado_temp(valor):
    if valor is None:
        return "Sin dato", "pill-warn"
    if valor < 75:
        return "Óptimo", "pill-ok"
    elif valor < 85:
        return "Normal", "pill-warn"
    return "Crítico", "pill-alert"

def clasificar_semaforo(delta):
    if delta is None:
        return "🟡 Sin base suficiente"
    if delta <= -10:
        return "🟢 Mejora robusta"
    if delta < 0:
        return "🟡 Mejora moderada"
    return "🔴 Deterioro / aumento térmico"

def kpi_card(title, value, subtitle="", border="#3a7d3a"):
    st.markdown(f"""
    <div class="kpi-card" style="border-top:5px solid {border};">
        <div class="kpi-title">{title}</div>
        <div class="kpi-value">{value}</div>
        <div class="kpi-sub">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)

def insight_box(title, body, border="#1565C0"):
    st.markdown(f"""
    <div class="panel-box" style="border-left:5px solid {border};">
        <div class="panel-title">{title}</div>
        <div style="font-size:13px; color:#333; line-height:1.5;">{body}</div>
    </div>
    """, unsafe_allow_html=True)

def safe_mean(df, col):
    if col not in df.columns:
        return None
    s = pd.to_numeric(df[col], errors="coerce").dropna()
    if s.empty:
        return None
    return round(float(s.mean()), 1)

def build_conclusiones_subsistemas(df_antes, df_despues):
    conclusiones = []

    a_dev, _, _, _, _ = stats(df_antes, "Temp_Dev_Prom") if not df_antes.empty else (None,)*5
    d_dev, _, _, _, _ = stats(df_despues, "Temp_Dev_Prom") if not df_despues.empty else (None,)*5
    if a_dev is not None and d_dev is not None:
        delta = round(d_dev - a_dev, 1)
        if delta <= -10:
            txt = "Mejora térmica robusta posterior a la modernización."
        elif delta < 0:
            txt = "Mejora térmica moderada en el devanado."
        else:
            txt = "Incremento térmico posterior; requiere revisión."
        conclusiones.append({"Subsistema": "Estátor y Devanado", "Delta (°C)": delta, "Conclusión": txt})

    a_ci, _, _, _, _ = stats(df_antes, "Temp_Metal_CojInf_Seg4_C") if not df_antes.empty else (None,)*5
    d_ci, _, _, _, _ = stats(df_despues, "Temp_Metal_CojInf_Seg4_C") if not df_despues.empty else (None,)*5
    if a_ci is not None and d_ci is not None:
        delta = round(d_ci - a_ci, 1)
        if delta > 3:
            txt = "Incremento relevante en cojinete inferior; seguimiento prioritario."
        elif delta > 0:
            txt = "Leve aumento térmico en cojinetes."
        else:
            txt = "Comportamiento térmico controlado en cojinetes."
        conclusiones.append({"Subsistema": "Cojinetes", "Delta (°C)": delta, "Conclusión": txt})

    a_pres = safe_mean(df_antes, "Pres_Agua_SistRefrig_bar") if not df_antes.empty else None
    d_pres = safe_mean(df_despues, "Pres_Agua_SistRefrig_bar") if not df_despues.empty else None
    if a_pres is not None and d_pres is not None:
        delta = round(d_pres - a_pres, 1)
        if delta < -0.2:
            txt = "Disminución en presión de refrigeración; revisar condición hidráulica."
        elif delta > 0.2:
            txt = "Presión de refrigeración superior respecto al período ANTES."
        else:
            txt = "Presión de refrigeración estable."
        conclusiones.append({"Subsistema": "Sistema de Refrigeración", "Delta (°C)": delta, "Conclusión": txt})

    return pd.DataFrame(conclusiones)

def to_excel_bytes(df_dict):
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet_name, df_sheet in df_dict.items():
            df_sheet.to_excel(writer, index=False, sheet_name=sheet_name[:31])
    output.seek(0)
    return output.getvalue()

# ==============================================================================
# CARGA DE DATOS
# ==============================================================================
@st.cache_data
def cargar_datos():
    ruta = os.path.join(os.path.dirname(os.path.abspath(__file__)), "DATA/U1_dashboard_data.csv")
    df = pd.read_csv(ruta, parse_dates=["Fecha_Hora"])

    columnas_numericas = [
        "Voltaje_BC_kV",
        "Temp_Metal_CojTurbina_C",
        "Temp_Dev_EstatorA3_C",
        "Temp_Dev_EstatorB2_C",
        "Temp_Dev_EstatorC1_C",
        "Temp_Nucleo_Estator2_C",
        "Temp_Metal_CojSup_Seg07_C",
        "Temp_Metal_CojInf_Seg4_C",
        "Temp_Metal_CojEmp_Seg3_C",
        "Potencia_Activa_MW",
        "Temp_Aceite_Transf",
        "Pres_Agua_SistRefrig_bar"
    ]

    for c in columnas_numericas:
        if c in df.columns:
            df[c] = pd.to_numeric(df[c], errors="coerce")

    df = df.dropna(subset=["Periodo"])

    meses_es = {
        1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
        5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
        9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
    }

    df["Mes_Num"] = df["Fecha_Hora"].dt.to_period("M").astype(str)
    df["Mes_Label"] = df["Fecha_Hora"].apply(lambda x: f"{meses_es[x.month]} {x.year}")
    df["Año"] = df["Fecha_Hora"].dt.year

    if {"Temp_Dev_EstatorA3_C", "Temp_Dev_EstatorB2_C", "Temp_Dev_EstatorC1_C"}.issubset(df.columns):
        df["Temp_Dev_Prom"] = df[
            ["Temp_Dev_EstatorA3_C", "Temp_Dev_EstatorB2_C", "Temp_Dev_EstatorC1_C"]
        ].mean(axis=1)
    else:
        df["Temp_Dev_Prom"] = np.nan

    orden = sorted(df["Mes_Num"].dropna().unique())
    df["Mes_Orden"] = pd.Categorical(df["Mes_Num"], categories=orden, ordered=True)

    return df

df = cargar_datos()
mes_map = df.drop_duplicates("Mes_Num").set_index("Mes_Num")["Mes_Label"].to_dict()

# ==============================================================================
# SIDEBAR — CONFIGURACIÓN GENERAL
# ==============================================================================
with st.sidebar:
    st.markdown("### 🎚️ Filtros Interactivos")
    st.markdown("---")

    tema_visual = st.selectbox("Tema visual", ["Claro", "Oscuro"], index=0)
    modo_movil = st.toggle("Modo móvil", value=False, help="Actívelo si abre el dashboard desde celular o si desea una vista más compacta.")
    theme_cfg = get_theme_config(tema_visual)

    mostrar_logo = True
    ruta_logo = r"IMG/Imagen1.jpg"

    st.markdown("---")
    st.markdown("**Período de análisis**")
    periodo_sel = st.radio("", ["ANTES", "DESPUÉS", "AMBOS"], index=2, horizontal=not modo_movil)

    st.markdown("---")
    st.markdown("**Meses disponibles**")
    meses_ordenados = sorted(df["Mes_Num"].dropna().unique())
    meses_labels_all = [mes_map[m] for m in meses_ordenados]
    meses_sel_labels = st.multiselect(
        "Seleccione meses:",
        options=meses_labels_all,
        default=meses_labels_all[:4] if modo_movil else meses_labels_all
    )
    meses_sel = [m for m, l in zip(meses_ordenados, meses_labels_all) if l in meses_sel_labels]

    st.markdown("---")
    st.markdown("**Filtro de operación**")
    pot_min = st.slider("Potencia activa mínima (MW):", min_value=0, max_value=70, value=48)

    st.markdown("---")
    st.markdown("**Subsistema a analizar**")
    subsistema = st.selectbox(
        "",
        [
            "Todos los subsistemas",
            "Estátor y Devanado",
            "Cojinetes",
            "Sistema de Refrigeración"
        ]
    )

    st.markdown("---")
    st.markdown("**📅 Comparación mes a mes**")
    st.caption("Compare un mes ANTES vs un mes DESPUÉS")

    meses_antes_df = (
        df[df["Periodo"] == "ANTES"][["Mes_Num", "Mes_Label"]]
        .drop_duplicates()
        .sort_values("Mes_Num")
    )

    meses_desp_df = (
        df[df["Periodo"] == "DESPUÉS"][["Mes_Num", "Mes_Label"]]
        .drop_duplicates()
        .sort_values("Mes_Num")
    )

    opciones_antes = dict(zip(meses_antes_df["Mes_Label"], meses_antes_df["Mes_Num"]))
    opciones_desp  = dict(zip(meses_desp_df["Mes_Label"], meses_desp_df["Mes_Num"]))

    mes_comp_antes_label = st.selectbox("Mes ANTES:", list(opciones_antes.keys()), key="mc_a")
    mes_comp_desp_label  = st.selectbox("Mes DESPUÉS:", list(opciones_desp.keys()), key="mc_d")

    mes_comp_antes = opciones_antes[mes_comp_antes_label]
    mes_comp_desp  = opciones_desp[mes_comp_desp_label]

    activar_comp = st.checkbox("✅ Activar comparación mes a mes", value=False)

# ==============================================================================
# CSS DINÁMICO SEGÚN TEMA / RESPONSIVE
# ==============================================================================
font_header = "18px" if modo_movil else "24px"
font_sub = "12px" if modo_movil else "14px"
logo_max = "220px" if modo_movil else "100%"
section_font = "12px" if modo_movil else "13px"
kpi_value_font = "22px" if modo_movil else "28px"
kpi_title_font = "11px" if modo_movil else "12px"

st.markdown(f"""
<style>
    .main {{
        background-color: {theme_cfg["bg_main"]};
    }}

    .header-banner {{
        background: linear-gradient(135deg, {theme_cfg["header_grad_1"]} 0%, {theme_cfg["header_grad_2"]} 45%, {theme_cfg["header_grad_3"]} 100%);
        padding: {"16px 18px" if modo_movil else "24px 32px"};
        border-radius: 14px;
        margin-bottom: 18px;
        border-left: 6px solid {theme_cfg["border_left"]};
        box-shadow: {theme_cfg["box_shadow"]};
    }}

    .header-title {{
        color:#ffffff;
        font-size:{font_header};
        font-weight:800;
        margin:0;
        font-family:Arial,sans-serif;
        line-height:1.35;
    }}

    .header-sub {{
        color:#c5ced8;
        font-size:{font_sub};
        margin:4px 0 0 0;
        font-family:Arial,sans-serif;
        line-height:1.45;
    }}

    .epm-badge {{
        background-color:#3a7d3a;
        color:white;
        padding:5px 14px;
        border-radius:20px;
        font-size:12px;
        font-weight:bold;
        display:inline-block;
    }}

    .seccion-titulo {{
        background:#000000;
        color:white;
        padding:9px 16px;
        border-radius:8px;
        font-size:{section_font};
        font-weight:bold;
        margin:16px 0 10px 0;
        border-left:5px solid #3a7d3a;
        letter-spacing:0.2px;
    }}

    .box-exito {{
        background:#E8F5E9;
        border-left:5px solid #1B7A4E;
        padding:12px 16px;
        border-radius:0 8px 8px 0;
        margin:8px 0;
        font-size:13px;
        color:#222;
    }}

    .box-alerta {{
        background:#FFEBEE;
        border-left:5px solid #C00000;
        padding:12px 16px;
        border-radius:0 8px 8px 0;
        margin:8px 0;
        font-size:13px;
        color:#222;
    }}

    .box-info {{
        background:#E8F4FD;
        border-left:5px solid #1565C0;
        padding:12px 16px;
        border-radius:0 8px 8px 0;
        margin:8px 0;
        font-size:13px;
        color:#222;
    }}

    .kpi-card {{
        background: {theme_cfg["bg_card"]};
        border-radius: 14px;
        padding: {"14px 14px" if modo_movil else "18px 18px"};
        box-shadow: {theme_cfg["box_shadow"]};
        border-top: 5px solid #3a7d3a;
        min-height: {"105px" if modo_movil else "122px"};
        margin-bottom: 10px;
    }}

    .kpi-title {{
        color: {theme_cfg["text_soft"]};
        font-size: {kpi_title_font};
        font-weight: 700;
        margin-bottom: 8px;
        text-transform: uppercase;
        letter-spacing: 0.4px;
    }}

    .kpi-value {{
        color: {theme_cfg["text_main"]};
        font-size: {kpi_value_font};
        font-weight: 800;
        line-height: 1.08;
        margin-bottom: 6px;
    }}

    .kpi-sub {{
        color: {theme_cfg["text_soft"]};
        font-size: {"11px" if modo_movil else "12px"};
        line-height: 1.35;
    }}

    .panel-box {{
        background: {theme_cfg["bg_panel"]};
        border-radius: 12px;
        padding: 16px 18px;
        box-shadow: {theme_cfg["box_shadow"]};
        border-left: 5px solid #1565C0;
        margin: 8px 0 14px 0;
    }}

    .panel-title {{
        font-size: 14px;
        font-weight: 800;
        color: {theme_cfg["text_main"]};
        margin-bottom: 8px;
    }}

    .pill-ok {{
        display:inline-block;
        background:#E8F5E9;
        color:#1B7A4E;
        padding:4px 10px;
        border-radius:30px;
        font-size:11px;
        font-weight:700;
    }}

    .pill-warn {{
        display:inline-block;
        background:#FFF3E0;
        color:#E65100;
        padding:4px 10px;
        border-radius:30px;
        font-size:11px;
        font-weight:700;
    }}

    .pill-alert {{
        display:inline-block;
        background:#FFEBEE;
        color:#C00000;
        padding:4px 10px;
        border-radius:30px;
        font-size:11px;
        font-weight:700;
    }}

    img {{
        max-width:{logo_max};
        height:auto;
    }}

    footer {{ visibility:hidden; }}
    #MainMenu {{ visibility:hidden; }}

    @media (max-width: 768px) {{
        .header-banner {{
            padding: 14px 14px !important;
        }}
        .header-title {{
            font-size: 17px !important;
        }}
        .header-sub {{
            font-size: 11px !important;
        }}
        .kpi-value {{
            font-size: 21px !important;
        }}
        .kpi-title {{
            font-size: 10px !important;
        }}
        .kpi-sub {{
            font-size: 10px !important;
        }}
    }}
</style>
""", unsafe_allow_html=True)

# ==============================================================================
# ENCABEZADO
# ==============================================================================
if modo_movil:
    st.markdown("""
    <div class="header-banner">
        <div>
            <p class="header-title">⚡ Dashboard de Confiabilidad Operacional — V3 Ejecutiva</p>
            <p class="header-sub">Análisis de Impacto — Modernización del Estátor | Unidad de Generación N.° 1</p>
            <p class="header-sub">Central Hidroeléctrica Playas | Área de Instrumentación, Control y Protección</p>
            <div style="margin-top:10px;">
                <span class="epm-badge">EPM</span>
            </div>
            <p class="header-sub" style="margin-top:10px;">SCADA histórico validado</p>
            <p class="header-sub">Mayo 2024 – Enero 2026</p>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if mostrar_logo and os.path.exists(ruta_logo):
        st.image(ruta_logo, width=180)
else:
    col_header_1, col_header_2 = st.columns([8, 2])

    with col_header_1:
        st.markdown("""
        <div class="header-banner">
            <div style="display:flex;justify-content:space-between;align-items:center;gap:20px;">
                <div>
                    <p class="header-title">⚡ Dashboard de Confiabilidad Operacional — V3 Ejecutiva</p>
                    <p class="header-sub">Análisis de Impacto — Modernización del Estátor | Unidad de Generación N.° 1</p>
                    <p class="header-sub">Central Hidroeléctrica Playas | Área de Instrumentación, Control y Protección</p>
                </div>
                <div style="text-align:right;">
                    <span class="epm-badge">EPM</span><br>
                    <span style="color:#c5ced8;font-size:11px;">SCADA histórico validado</span><br>
                    <span style="color:#c5ced8;font-size:11px;">Mayo 2024 – Enero 2026</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    with col_header_2:
        if mostrar_logo and os.path.exists(ruta_logo):
            st.image(ruta_logo, use_container_width=True)

# ==============================================================================
# APLICAR FILTROS
# ==============================================================================
df_f = df.copy()
df_f = df_f[df_f["Potencia_Activa_MW"] >= pot_min]

if meses_sel:
    df_f = df_f[df_f["Mes_Num"].isin(meses_sel)]

if periodo_sel == "ANTES":
    df_f = df_f[df_f["Periodo"] == "ANTES"]
elif periodo_sel == "DESPUÉS":
    df_f = df_f[df_f["Periodo"] == "DESPUÉS"]

if df_f.empty:
    st.warning("⚠️ Sin datos con los filtros seleccionados.")
    st.stop()

df_antes = df_f[df_f["Periodo"] == "ANTES"].copy()
df_despues = df_f[df_f["Periodo"] == "DESPUÉS"].copy()

# ==============================================================================
# TABS DINÁMICOS
# ==============================================================================
tabs_config = [("📊 Resumen Ejecutivo", "tab1")]

if subsistema in ["Todos los subsistemas", "Estátor y Devanado"]:
    tabs_config.append(("🌡️ Estátor y Devanado", "tab2"))

if subsistema in ["Todos los subsistemas", "Cojinetes"]:
    tabs_config.append(("⚙️ Cojinetes", "tab3"))

if subsistema in ["Todos los subsistemas", "Sistema de Refrigeración"]:
    tabs_config.append(("💧 Refrigeración y Aceite", "tab4"))

tabs_config.append(("📋 Datos y Estadísticas", "tab5"))

tabs = st.tabs([t[0] for t in tabs_config])
tabs_dict = {name: tab for (_, name), tab in zip(tabs_config, tabs)}

# ==============================================================================
# TAB 1 — RESUMEN EJECUTIVO
# ==============================================================================
with tabs_dict["tab1"]:
    st.markdown('<div class="seccion-titulo">📈 RESUMEN EJECUTIVO PREMIUM</div>', unsafe_allow_html=True)

    a_avg, _, a_max, a_std, _ = stats(df_antes, "Temp_Dev_Prom") if not df_antes.empty else (None, None, None, None, None)
    d_avg, _, d_max, d_std, _ = stats(df_despues, "Temp_Dev_Prom") if not df_despues.empty else (None, None, None, None, None)

    coj_inf_a, _, _, _, _ = stats(df_antes, "Temp_Metal_CojInf_Seg4_C") if not df_antes.empty else (None, None, None, None, None)
    coj_inf_d, _, _, _, _ = stats(df_despues, "Temp_Metal_CojInf_Seg4_C") if not df_despues.empty else (None, None, None, None, None)

    delta_dev = round(d_avg - a_avg, 1) if a_avg is not None and d_avg is not None else None
    delta_max = round(d_max - a_max, 1) if a_max is not None and d_max is not None else None
    delta_std = round(d_std - a_std, 1) if a_std is not None and d_std is not None else None
    estado_txt, estado_cls = clasificar_estado_temp(d_avg)
    semaforo_global = clasificar_semaforo(delta_dev)

    if modo_movil:
        row1 = st.columns(2)
        with row1[0]:
            kpi_card("Temperatura devanado actual", fmt_temp(d_avg), "Promedio filtrado del período DESPUÉS", "#1B7A4E")
        with row1[1]:
            subt = f"ANTES {fmt_temp(a_avg)} → DESPUÉS {fmt_temp(d_avg)}" if delta_dev is not None else "Sin base comparativa"
            kpi_card("Delta térmico global", f"{delta_dev:+.1f}°C" if delta_dev is not None else "—", subt, "#1565C0")

        row2 = st.columns(2)
        with row2[0]:
            subt = f"Máximo ANTES {fmt_temp(a_max)} / Máximo DESPUÉS {fmt_temp(d_max)}" if delta_max is not None else "Sin base comparativa"
            kpi_card("Cambio en máximos", f"{delta_max:+.1f}°C" if delta_max is not None else "—", subt, "#E65100")
        with row2[1]:
            subt = f"σ ANTES ±{fmt_num(a_std)} / σ DESPUÉS ±{fmt_num(d_std)}" if delta_std is not None else "Sin base comparativa"
            kpi_card("Estabilidad térmica", f"±{fmt_num(d_std)}°C" if d_std is not None else "—", subt, "#6A1B9A")

        st.markdown(f"""
        <div class="kpi-card" style="border-top:5px solid #C00000;">
            <div class="kpi-title">Condición operacional</div>
            <div class="kpi-value" style="font-size:24px;">{estado_txt}</div>
            <div class="{estado_cls}" style="margin-top:8px;">Evaluación automática</div>
            <div class="kpi-sub" style="margin-top:8px;">{semaforo_global}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            kpi_card("Temperatura devanado actual", fmt_temp(d_avg), "Promedio filtrado del período DESPUÉS", "#1B7A4E")
        with c2:
            subt = f"ANTES {fmt_temp(a_avg)} → DESPUÉS {fmt_temp(d_avg)}" if delta_dev is not None else "Sin base comparativa"
            kpi_card("Delta térmico global", f"{delta_dev:+.1f}°C" if delta_dev is not None else "—", subt, "#1565C0")
        with c3:
            subt = f"Máximo ANTES {fmt_temp(a_max)} / Máximo DESPUÉS {fmt_temp(d_max)}" if delta_max is not None else "Sin base comparativa"
            kpi_card("Cambio en máximos", f"{delta_max:+.1f}°C" if delta_max is not None else "—", subt, "#E65100")
        with c4:
            subt = f"σ ANTES ±{fmt_num(a_std)} / σ DESPUÉS ±{fmt_num(d_std)}" if delta_std is not None else "Sin base comparativa"
            kpi_card("Estabilidad térmica", f"±{fmt_num(d_std)}°C" if d_std is not None else "—", subt, "#6A1B9A")
        with c5:
            st.markdown(f"""
            <div class="kpi-card" style="border-top:5px solid #C00000;">
                <div class="kpi-title">Condición operacional</div>
                <div class="kpi-value" style="font-size:24px;">{estado_txt}</div>
                <div class="{estado_cls}" style="margin-top:8px;">Evaluación automática</div>
                <div class="kpi-sub" style="margin-top:8px;">{semaforo_global}</div>
            </div>
            """, unsafe_allow_html=True)

    st.markdown("---")

    if modo_movil:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("📊 Registros ANTES", f"{len(df_antes):,}")
            st.metric("📊 Total Registros", f"{len(df_f):,}")
        with c2:
            st.metric("📊 Registros DESPUÉS", f"{len(df_despues):,}")
            st.metric("⚙️ Potencia mínima", f"{pot_min} MW")
    else:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric("📊 Registros ANTES", f"{len(df_antes):,}")
        with c2:
            st.metric("📊 Registros DESPUÉS", f"{len(df_despues):,}")
        with c3:
            st.metric("📊 Total Registros", f"{len(df_f):,}")
        with c4:
            st.metric("⚙️ Potencia mínima aplicada", f"{pot_min} MW")

    st.markdown('<div class="seccion-titulo">🧠 INTERPRETACIÓN AUTOMÁTICA</div>', unsafe_allow_html=True)

    if modo_movil:
        if delta_dev is not None:
            if delta_dev <= -10:
                insight_box(
                    "Hallazgo principal",
                    "La modernización del estátor muestra una <b>mejora térmica robusta</b>, con reducción sostenida en la temperatura promedio del devanado bajo condiciones comparables de carga.",
                    "#1B7A4E"
                )
            elif delta_dev < 0:
                insight_box(
                    "Hallazgo principal",
                    "Se observa una <b>mejora térmica moderada</b> posterior a la intervención. El efecto es favorable, aunque menos contundente.",
                    "#1565C0"
                )
            else:
                insight_box(
                    "Hallazgo principal",
                    "Se observa un <b>incremento térmico</b> posterior al cambio. Conviene revisar comparabilidad operativa, ventilación y comportamiento del sistema de enfriamiento.",
                    "#C00000"
                )

        if coj_inf_a is not None and coj_inf_d is not None:
            delta_coj_inf = round(coj_inf_d - coj_inf_a, 1)
            if delta_coj_inf > 3:
                insight_box(
                    "Punto de atención",
                    f"El cojinete inferior presenta una variación de <b>{delta_coj_inf:+.1f}°C</b> respecto al período ANTES. Este subsistema merece seguimiento específico en lubricación, flujo de refrigeración y tendencia mensual.",
                    "#C00000"
                )
            else:
                insight_box(
                    "Punto de atención",
                    "No se detecta un incremento severo en el cojinete inferior dentro del filtro actual. El comportamiento luce controlado bajo las condiciones seleccionadas.",
                    "#E65100"
                )
    else:
        col_i1, col_i2 = st.columns(2)

        with col_i1:
            if delta_dev is not None:
                if delta_dev <= -10:
                    insight_box(
                        "Hallazgo principal",
                        "La modernización del estátor muestra una <b>mejora térmica robusta</b>, con reducción sostenida en la temperatura promedio del devanado bajo condiciones comparables de carga.",
                        "#1B7A4E"
                    )
                elif delta_dev < 0:
                    insight_box(
                        "Hallazgo principal",
                        "Se observa una <b>mejora térmica moderada</b> posterior a la intervención. El efecto es favorable, aunque menos contundente.",
                        "#1565C0"
                    )
                else:
                    insight_box(
                        "Hallazgo principal",
                        "Se observa un <b>incremento térmico</b> posterior al cambio. Conviene revisar comparabilidad operativa, ventilación y comportamiento del sistema de enfriamiento.",
                        "#C00000"
                    )

        with col_i2:
            if coj_inf_a is not None and coj_inf_d is not None:
                delta_coj_inf = round(coj_inf_d - coj_inf_a, 1)
                if delta_coj_inf > 3:
                    insight_box(
                        "Punto de atención",
                        f"El cojinete inferior presenta una variación de <b>{delta_coj_inf:+.1f}°C</b> respecto al período ANTES. Este subsistema merece seguimiento específico en lubricación, flujo de refrigeración y tendencia mensual.",
                        "#C00000"
                    )
                else:
                    insight_box(
                        "Punto de atención",
                        "No se detecta un incremento severo en el cojinete inferior dentro del filtro actual. El comportamiento luce controlado bajo las condiciones seleccionadas.",
                        "#E65100"
                    )

    st.markdown('<div class="seccion-titulo">📌 CONCLUSIONES AUTOMÁTICAS POR SUBSISTEMA</div>', unsafe_allow_html=True)
    df_conclusiones = build_conclusiones_subsistemas(df_antes, df_despues)
    if not df_conclusiones.empty:
        st.dataframe(df_conclusiones, use_container_width=True, hide_index=True)

    st.markdown('<div class="seccion-titulo">📈 TENDENCIA HISTÓRICA MENSUAL — TEMPERATURA DEVANADO PROMEDIO</div>', unsafe_allow_html=True)

    df_men = (
        df_f.groupby(["Mes_Num", "Mes_Label", "Periodo"])
        .agg(Dev_Prom=("Temp_Dev_Prom", "mean"))
        .reset_index()
        .sort_values("Mes_Num")
    )
    df_men["Dev_Prom"] = df_men["Dev_Prom"].round(1)

    fig = go.Figure()
    for p, c, nom in [("ANTES", C_ANTES, "Devanado ANTES"), ("DESPUÉS", C_DESPUES, "Devanado DESPUÉS")]:
        d = df_men[df_men["Periodo"] == p]
        if not d.empty:
            fig.add_trace(go.Bar(
                x=d["Mes_Label"],
                y=d["Dev_Prom"],
                name=nom,
                marker_color=c,
                hovertemplate="Mes: %{x}<br>Temperatura: %{y:.1f}°C<extra></extra>"
            ))

    fig.add_hline(y=80, line_dash="dash", line_color=C_ALERTA, annotation_text="Umbral 80°C", annotation_position="top right")

    if a_avg is not None:
        fig.add_hline(y=a_avg, line_dash="dot", line_color=C_ANTES, annotation_text=f"Prom ANTES: {a_avg}°C")
    if d_avg is not None:
        fig.add_hline(y=d_avg, line_dash="dot", line_color=C_DESPUES, annotation_text=f"Prom DESPUÉS: {d_avg}°C")

    fig.update_layout(
        title="Temperatura promedio mensual del devanado del estátor",
        xaxis_title="Mes",
        yaxis=dict(title="Temperatura (°C)", range=[50, 105]),
        legend=dict(orientation="h", y=1.12),
        plot_bgcolor=theme_cfg["plot_bg"],
        paper_bgcolor=theme_cfg["paper_bg"],
        height=420,
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True)

    with st.expander("🔥 Ver matriz térmica mensual", expanded=not modo_movil):
        st.markdown('<div class="seccion-titulo">🔥 MATRIZ TÉRMICA MENSUAL</div>', unsafe_allow_html=True)

        heat_vars = {
            "Dev A3": "Temp_Dev_EstatorA3_C",
            "Dev B2": "Temp_Dev_EstatorB2_C",
            "Dev C1": "Temp_Dev_EstatorC1_C",
            "Núcleo": "Temp_Nucleo_Estator2_C",
            "Coj. Sup.": "Temp_Metal_CojSup_Seg07_C",
            "Coj. Inf.": "Temp_Metal_CojInf_Seg4_C",
            "Coj. Turb.": "Temp_Metal_CojTurbina_C",
            "Coj. Emp.": "Temp_Metal_CojEmp_Seg3_C"
        }

        heat_rows = []
        for nom, col in heat_vars.items():
            if col in df_f.columns:
                tmp = (
                    df_f.groupby(["Mes_Num", "Mes_Label"])[col]
                    .mean()
                    .reset_index()
                    .rename(columns={col: "Valor"})
                    .sort_values("Mes_Num")
                )
                tmp["Variable"] = nom
                heat_rows.append(tmp)

        if heat_rows:
            df_heat = pd.concat(heat_rows, ignore_index=True)
            meses_orden_heat = (
                df_heat[["Mes_Num", "Mes_Label"]]
                .drop_duplicates()
                .sort_values("Mes_Num")["Mes_Label"]
                .tolist()
            )
            heat_pivot = df_heat.pivot(index="Variable", columns="Mes_Label", values="Valor")
            heat_pivot = heat_pivot.reindex(columns=meses_orden_heat)

            fig_heat = go.Figure(data=go.Heatmap(
                z=heat_pivot.values,
                x=list(heat_pivot.columns),
                y=list(heat_pivot.index),
                colorscale="RdYlGn_r",
                colorbar=dict(title="°C"),
                hovertemplate="Variable: %{y}<br>Mes: %{x}<br>Temp: %{z:.1f}°C<extra></extra>"
            ))
            fig_heat.update_layout(
                title="Mapa térmico mensual de variables críticas",
                plot_bgcolor=theme_cfg["plot_bg"],
                paper_bgcolor=theme_cfg["paper_bg"],
                height=430
            )
            st.plotly_chart(fig_heat, use_container_width=True)

    with st.expander("📋 Ver resumen comparativo por variable", expanded=not modo_movil):
        st.markdown('<div class="seccion-titulo">📋 RESUMEN COMPARATIVO POR VARIABLE</div>', unsafe_allow_html=True)

        vars_res = [
            ("Temp_Nucleo_Estator2_C",   "Núcleo Estátor (°C)"),
            ("Temp_Dev_EstatorA3_C",     "Devanado Fase A3 (°C)"),
            ("Temp_Dev_EstatorB2_C",     "Devanado Fase B2 (°C)"),
            ("Temp_Dev_EstatorC1_C",     "Devanado Fase C1 (°C)"),
            ("Temp_Metal_CojSup_Seg07_C","Metal Coj. Superior (°C)"),
            ("Temp_Metal_CojInf_Seg4_C", "Metal Coj. Inferior (°C)"),
            ("Temp_Metal_CojTurbina_C",  "Metal Coj. Turbina (°C)"),
            ("Temp_Metal_CojEmp_Seg3_C", "Metal Coj. Empuje (°C)"),
            ("Potencia_Activa_MW",       "Potencia Activa (MW)"),
        ]

        rows = []
        for cv, nom in vars_res:
            aa, _, am, _, ap = stats(df_antes, cv) if not df_antes.empty else (None, None, None, None, None)
            da, _, dm, _, dp = stats(df_despues, cv) if not df_despues.empty else (None, None, None, None, None)

            if aa is not None and da is not None:
                dlt = round(da - aa, 1)
                pct = round((dlt / aa) * 100, 1) if aa != 0 else 0
                rows.append({
                    "Variable": nom,
                    "Prom ANTES": aa,
                    "Máx ANTES": am,
                    "P95 ANTES": ap,
                    "Prom DESPUÉS": da,
                    "Máx DESPUÉS": dm,
                    "P95 DESPUÉS": dp,
                    "Δ Prom": dlt,
                    "Mejora %": pct
                })

        df_res = pd.DataFrame(rows) if rows else pd.DataFrame()

        if not df_res.empty:
            fmt = {
                "Prom ANTES": "{:.1f}",
                "Máx ANTES": "{:.1f}",
                "P95 ANTES": "{:.1f}",
                "Prom DESPUÉS": "{:.1f}",
                "Máx DESPUÉS": "{:.1f}",
                "P95 DESPUÉS": "{:.1f}",
                "Δ Prom": "{:.1f}",
                "Mejora %": "{:.1f}"
            }

            def color_delta(val):
                try:
                    v = float(val)
                    if v < -1:
                        return "background-color:#E8F5E9;color:#1B7A4E;font-weight:bold"
                    elif v > 1:
                        return "background-color:#FFEBEE;color:#C00000;font-weight:bold"
                except:
                    pass
                return ""

            st.dataframe(
                df_res.style.format(fmt).applymap(color_delta, subset=["Δ Prom", "Mejora %"]),
                use_container_width=True,
                hide_index=True,
                height=380
            )
        else:
            df_res = pd.DataFrame()

    with st.expander("🏆 Ver ranking de impacto térmico", expanded=not modo_movil):
        st.markdown('<div class="seccion-titulo">🏆 RANKING DE IMPACTO TÉRMICO</div>', unsafe_allow_html=True)

        ranking = []
        for cv, nom in [
            ("Temp_Nucleo_Estator2_C",   "Núcleo Estátor (°C)"),
            ("Temp_Dev_EstatorA3_C",     "Devanado Fase A3 (°C)"),
            ("Temp_Dev_EstatorB2_C",     "Devanado Fase B2 (°C)"),
            ("Temp_Dev_EstatorC1_C",     "Devanado Fase C1 (°C)"),
            ("Temp_Metal_CojSup_Seg07_C","Metal Coj. Superior (°C)"),
            ("Temp_Metal_CojInf_Seg4_C", "Metal Coj. Inferior (°C)"),
            ("Temp_Metal_CojTurbina_C",  "Metal Coj. Turbina (°C)"),
            ("Temp_Metal_CojEmp_Seg3_C", "Metal Coj. Empuje (°C)"),
            ("Potencia_Activa_MW",       "Potencia Activa (MW)")
        ]:
            aa, _, _, _, _ = stats(df_antes, cv) if not df_antes.empty else (None, None, None, None, None)
            da, _, _, _, _ = stats(df_despues, cv) if not df_despues.empty else (None, None, None, None, None)
            if aa is not None and da is not None:
                ranking.append({"Variable": nom, "Delta": round(da - aa, 1)})

        df_rank = pd.DataFrame(ranking).sort_values("Delta", ascending=True) if ranking else pd.DataFrame()

        if not df_rank.empty:
            fig_rank = px.bar(
                df_rank,
                x="Delta",
                y="Variable",
                orientation="h",
                text="Delta",
                title="Variación térmica por variable (DESPUÉS − ANTES)"
            )
            fig_rank.update_traces(
                texttemplate="%{text:+.1f}°C",
                textposition="outside",
                marker_color=[
                    "#1B7A4E" if v < -1 else "#C00000" if v > 1 else "#E65100"
                    for v in df_rank["Delta"]
                ],
                hovertemplate="Variable: %{y}<br>Delta: %{x:+.1f}°C<extra></extra>"
            )
            fig_rank.add_vline(x=0, line_dash="dash", line_color="black")
            fig_rank.update_layout(
                plot_bgcolor=theme_cfg["plot_bg"],
                paper_bgcolor=theme_cfg["paper_bg"],
                xaxis_title="Delta térmico (°C)",
                yaxis_title="",
                height=430
            )
            st.plotly_chart(fig_rank, use_container_width=True)

    if activar_comp:
        st.markdown("---")
        st.markdown(
            f'<div class="seccion-titulo">📅 COMPARACIÓN MES A MES — {mes_comp_antes_label} vs {mes_comp_desp_label}</div>',
            unsafe_allow_html=True
        )

        df_ma = df[
            (df["Periodo"] == "ANTES") &
            (df["Mes_Num"] == mes_comp_antes) &
            (df["Potencia_Activa_MW"] >= pot_min)
        ].copy()

        df_md = df[
            (df["Periodo"] == "DESPUÉS") &
            (df["Mes_Num"] == mes_comp_desp) &
            (df["Potencia_Activa_MW"] >= pot_min)
        ].copy()

        if df_ma.empty or df_md.empty:
            st.warning(f"Sin datos para los meses seleccionados con potencia ≥ {pot_min} MW.")
        else:
            df_ma["Temp_Dev_Prom"] = df_ma[["Temp_Dev_EstatorA3_C", "Temp_Dev_EstatorB2_C", "Temp_Dev_EstatorC1_C"]].mean(axis=1)
            df_md["Temp_Dev_Prom"] = df_md[["Temp_Dev_EstatorA3_C", "Temp_Dev_EstatorB2_C", "Temp_Dev_EstatorC1_C"]].mean(axis=1)

            kpi_v = [
                ("Temp_Dev_Prom", "Devanado Prom."),
                ("Temp_Nucleo_Estator2_C", "Núcleo"),
                ("Temp_Metal_CojSup_Seg07_C", "Coj. Superior"),
                ("Temp_Metal_CojInf_Seg4_C", "Coj. Inferior")
            ]

            if modo_movil:
                row1 = st.columns(2)
                row2 = st.columns(2)
                all_cols = [row1[0], row1[1], row2[0], row2[1]]
                for cw, (cv, nom) in zip(all_cols, kpi_v):
                    va = safe_mean(df_ma, cv)
                    vd = safe_mean(df_md, cv)
                    with cw:
                        if va is not None and vd is not None:
                            d = round(vd - va, 1)
                            st.metric(nom, f"{vd:.1f}°C", delta=f"{d:+.1f}°C")
                        else:
                            st.metric(nom, "—")
            else:
                c1, c2, c3, c4 = st.columns(4)
                for cw, (cv, nom) in zip([c1, c2, c3, c4], kpi_v):
                    va = safe_mean(df_ma, cv)
                    vd = safe_mean(df_md, cv)
                    with cw:
                        if va is not None and vd is not None:
                            d = round(vd - va, 1)
                            st.metric(nom, f"{vd:.1f}°C", delta=f"{d:+.1f}°C  (era {va:.1f}°C)", delta_color="inverse")
                        else:
                            st.metric(nom, "—")

            gv = [
                ("Temp_Dev_EstatorA3_C", "Dev. A3"),
                ("Temp_Dev_EstatorB2_C", "Dev. B2"),
                ("Temp_Dev_EstatorC1_C", "Dev. C1"),
                ("Temp_Nucleo_Estator2_C", "Núcleo"),
                ("Temp_Metal_CojSup_Seg07_C", "Coj. Sup."),
                ("Temp_Metal_CojInf_Seg4_C", "Coj. Inf."),
                ("Temp_Metal_CojTurbina_C", "Coj. Turb."),
                ("Temp_Metal_CojEmp_Seg3_C", "Coj. Emp.")
            ]

            noms = [v[1] for v in gv]
            v_ant = [safe_mean(df_ma, v[0]) if safe_mean(df_ma, v[0]) is not None else 0 for v in gv]
            v_des = [safe_mean(df_md, v[0]) if safe_mean(df_md, v[0]) is not None else 0 for v in gv]
            delts = [round(d - a, 1) for a, d in zip(v_ant, v_des)]

            st.markdown("#### 🔍 Juicio técnico automático")
            delta_global = round(float(np.mean(delts)), 1) if len(delts) > 0 else None

            if delta_global is not None:
                if delta_global <= -5:
                    st.markdown("""
                    <div class="box-exito">
                    <strong>Conclusión comparativa:</strong> el mes DESPUÉS presenta una reducción térmica clara frente al mes ANTES seleccionado.
                    </div>
                    """, unsafe_allow_html=True)
                elif delta_global < 0:
                    st.markdown("""
                    <div class="box-info">
                    <strong>Conclusión comparativa:</strong> el mes DESPUÉS muestra una mejora leve, pero consistente.
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown("""
                    <div class="box-alerta">
                    <strong>Conclusión comparativa:</strong> el mes DESPUÉS presenta incremento térmico global respecto al mes ANTES.
                    </div>
                    """, unsafe_allow_html=True)

            fig_c = go.Figure()
            fig_c.add_trace(go.Bar(
                name=f"ANTES — {mes_comp_antes_label}",
                x=noms, y=v_ant,
                marker_color=C_ANTES,
                text=[f"{v:.1f}°C" for v in v_ant],
                textposition="outside"
            ))
            fig_c.add_trace(go.Bar(
                name=f"DESPUÉS — {mes_comp_desp_label}",
                x=noms, y=v_des,
                marker_color=C_DESPUES,
                text=[f"{v:.1f}°C" for v in v_des],
                textposition="outside"
            ))
            fig_c.add_trace(go.Scatter(
                name="Delta (°C)",
                x=noms, y=delts,
                mode="lines+markers+text",
                line=dict(color=C_DELTA, width=2.5, dash="dot"),
                marker=dict(size=8, symbol="diamond"),
                text=[f"{d:+.1f}°C" for d in delts],
                textposition="top center",
                yaxis="y2"
            ))

            fig_c.update_layout(
                title=f"Comparación — {mes_comp_antes_label} (ANTES) vs {mes_comp_desp_label} (DESPUÉS)",
                xaxis_title="Variable",
                yaxis=dict(title="Temperatura (°C)", range=[40, 110]),
                yaxis2=dict(title="Delta (°C)", overlaying="y", side="right", range=[-35, 15], showgrid=False),
                barmode="group",
                plot_bgcolor=theme_cfg["plot_bg"],
                paper_bgcolor=theme_cfg["paper_bg"],
                legend=dict(orientation="h", y=1.15),
                height=460
            )
            st.plotly_chart(fig_c, use_container_width=True)

            df_tc = pd.DataFrame({
                "Variable": noms,
                f"ANTES {mes_comp_antes_label}": v_ant,
                f"DESPUÉS {mes_comp_desp_label}": v_des,
                "Delta (°C)": delts,
                "Mejora %": [f"{(d / a * 100):+.1f}%" if a else "—" for a, d in zip(v_ant, delts)]
            })

            fmt_tc = {
                f"ANTES {mes_comp_antes_label}": "{:.1f}",
                f"DESPUÉS {mes_comp_desp_label}": "{:.1f}",
                "Delta (°C)": "{:.1f}",
            }

            def cc(val):
                try:
                    v = float(val)
                    if v < -1:
                        return "background-color:#E8F5E9;color:#1B7A4E;font-weight:bold"
                    elif v > 1:
                        return "background-color:#FFEBEE;color:#C00000;font-weight:bold"
                except:
                    pass
                return ""

            st.dataframe(
                df_tc.style.format(fmt_tc).applymap(cc, subset=["Delta (°C)"]),
                use_container_width=True,
                hide_index=True
            )

    st.markdown('<div class="seccion-titulo">⬇️ EXPORTACIÓN</div>', unsafe_allow_html=True)

    export_resumen = df_res.copy() if 'df_res' in locals() and not df_res.empty else pd.DataFrame()
    export_conclusiones = df_conclusiones.copy() if not df_conclusiones.empty else pd.DataFrame()
    export_datos = df_f.copy()

    excel_bytes = to_excel_bytes({
        "Resumen_Comparativo": export_resumen if not export_resumen.empty else pd.DataFrame({"Info": ["Sin datos"]}),
        "Conclusiones": export_conclusiones if not export_conclusiones.empty else pd.DataFrame({"Info": ["Sin datos"]}),
        "Datos_Filtrados": export_datos
    })

    if modo_movil:
        st.download_button(
            "📥 Descargar Excel completo",
            data=excel_bytes,
            file_name="dashboard_confiabilidad_u1_v4.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
        csv_bytes = export_resumen.to_csv(index=False).encode("utf-8") if not export_resumen.empty else b""
        st.download_button(
            "📥 Descargar resumen CSV",
            data=csv_bytes,
            file_name="resumen_comparativo_u1.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        col_exp1, col_exp2 = st.columns(2)
        with col_exp1:
            st.download_button(
                "📥 Descargar Excel completo",
                data=excel_bytes,
                file_name="dashboard_confiabilidad_u1_v4.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        with col_exp2:
            csv_bytes = export_resumen.to_csv(index=False).encode("utf-8") if not export_resumen.empty else b""
            st.download_button(
                "📥 Descargar resumen comparativo CSV",
                data=csv_bytes,
                file_name="resumen_comparativo_u1.csv",
                mime="text/csv"
            )

# ==============================================================================
# TAB 2 — ESTÁTOR Y DEVANADO
# ==============================================================================
if "tab2" in tabs_dict:
    with tabs_dict["tab2"]:
        st.markdown('<div class="seccion-titulo">🌡️ ESTÁTOR Y DEVANADO DEL GENERADOR</div>', unsafe_allow_html=True)

        if modo_movil:
            st.markdown("#### Distribución por fase")
            rows_b = []
            for cf, nf in [
                ("Temp_Dev_EstatorA3_C", "Fase A3"),
                ("Temp_Dev_EstatorB2_C", "Fase B2"),
                ("Temp_Dev_EstatorC1_C", "Fase C1")
            ]:
                if cf in df_antes.columns:
                    for v in df_antes[cf].dropna():
                        rows_b.append({"Fase": nf, "Temp": round(v, 1), "Período": "ANTES"})
                if cf in df_despues.columns:
                    for v in df_despues[cf].dropna():
                        rows_b.append({"Fase": nf, "Temp": round(v, 1), "Período": "DESPUÉS"})

            if rows_b:
                fig_b = px.box(
                    pd.DataFrame(rows_b),
                    x="Fase",
                    y="Temp",
                    color="Período",
                    color_discrete_map={"ANTES": C_ANTES, "DESPUÉS": C_DESPUES},
                    title="Distribución de temperatura por fase",
                    labels={"Temp": "Temperatura (°C)"}
                )
                fig_b.add_hline(y=80, line_dash="dash", line_color=C_ALERTA, annotation_text="Umbral 80°C")
                fig_b.update_layout(
                    plot_bgcolor=theme_cfg["plot_bg"],
                    paper_bgcolor=theme_cfg["paper_bg"],
                    legend=dict(orientation="h", y=1.12),
                    height=390
                )
                st.plotly_chart(fig_b, use_container_width=True)

            st.markdown("#### Núcleo — Tendencia mensual")
            df_nuc = (
                df_f.groupby(["Mes_Num", "Mes_Label", "Periodo"])
                .agg(Nucleo=("Temp_Nucleo_Estator2_C", "mean"))
                .reset_index()
                .sort_values("Mes_Num")
            )
            df_nuc["Nucleo"] = df_nuc["Nucleo"].round(1)

            fig_n = go.Figure()
            for p, c in [("ANTES", C_ANTES), ("DESPUÉS", C_DESPUES)]:
                d = df_nuc[df_nuc["Periodo"] == p]
                if not d.empty:
                    fig_n.add_trace(go.Scatter(
                        x=d["Mes_Label"], y=d["Nucleo"],
                        mode="lines+markers+text",
                        name=f"Núcleo {p}",
                        line=dict(color=c, width=3),
                        marker=dict(size=8),
                        text=d["Nucleo"],
                        textposition="top center"
                    ))
            fig_n.add_hline(y=85, line_dash="dash", line_color=C_ALERTA, annotation_text="Umbral 85°C")
            fig_n.update_layout(
                title="Temperatura mensual del núcleo del estátor",
                xaxis_title="Mes",
                yaxis=dict(title="Temperatura (°C)", range=[55, 100]),
                plot_bgcolor=theme_cfg["plot_bg"],
                paper_bgcolor=theme_cfg["paper_bg"],
                legend=dict(orientation="h", y=1.12),
                height=390
            )
            st.plotly_chart(fig_n, use_container_width=True)

        else:
            c1, c2 = st.columns(2)

            with c1:
                st.markdown("#### Distribución por fase")
                rows_b = []
                for cf, nf in [
                    ("Temp_Dev_EstatorA3_C", "Fase A3"),
                    ("Temp_Dev_EstatorB2_C", "Fase B2"),
                    ("Temp_Dev_EstatorC1_C", "Fase C1")
                ]:
                    if cf in df_antes.columns:
                        for v in df_antes[cf].dropna():
                            rows_b.append({"Fase": nf, "Temp": round(v, 1), "Período": "ANTES"})
                    if cf in df_despues.columns:
                        for v in df_despues[cf].dropna():
                            rows_b.append({"Fase": nf, "Temp": round(v, 1), "Período": "DESPUÉS"})

                if rows_b:
                    fig_b = px.box(
                        pd.DataFrame(rows_b),
                        x="Fase",
                        y="Temp",
                        color="Período",
                        color_discrete_map={"ANTES": C_ANTES, "DESPUÉS": C_DESPUES},
                        title="Distribución de temperatura por fase",
                        labels={"Temp": "Temperatura (°C)"}
                    )
                    fig_b.add_hline(y=80, line_dash="dash", line_color=C_ALERTA, annotation_text="Umbral 80°C")
                    fig_b.update_layout(
                        plot_bgcolor=theme_cfg["plot_bg"],
                        paper_bgcolor=theme_cfg["paper_bg"],
                        legend=dict(orientation="h", y=1.12),
                        height=390
                    )
                    st.plotly_chart(fig_b, use_container_width=True)

            with c2:
                st.markdown("#### Núcleo — Tendencia mensual")
                df_nuc = (
                    df_f.groupby(["Mes_Num", "Mes_Label", "Periodo"])
                    .agg(Nucleo=("Temp_Nucleo_Estator2_C", "mean"))
                    .reset_index()
                    .sort_values("Mes_Num")
                )
                df_nuc["Nucleo"] = df_nuc["Nucleo"].round(1)

                fig_n = go.Figure()
                for p, c in [("ANTES", C_ANTES), ("DESPUÉS", C_DESPUES)]:
                    d = df_nuc[df_nuc["Periodo"] == p]
                    if not d.empty:
                        fig_n.add_trace(go.Scatter(
                            x=d["Mes_Label"], y=d["Nucleo"],
                            mode="lines+markers+text",
                            name=f"Núcleo {p}",
                            line=dict(color=c, width=3),
                            marker=dict(size=8),
                            text=d["Nucleo"],
                            textposition="top center"
                        ))
                fig_n.add_hline(y=85, line_dash="dash", line_color=C_ALERTA, annotation_text="Umbral 85°C")
                fig_n.update_layout(
                    title="Temperatura mensual del núcleo del estátor",
                    xaxis_title="Mes",
                    yaxis=dict(title="Temperatura (°C)", range=[55, 100]),
                    plot_bgcolor=theme_cfg["plot_bg"],
                    paper_bgcolor=theme_cfg["paper_bg"],
                    legend=dict(orientation="h", y=1.12),
                    height=390
                )
                st.plotly_chart(fig_n, use_container_width=True)

# ==============================================================================
# TAB 3 — COJINETES
# ==============================================================================
if "tab3" in tabs_dict:
    with tabs_dict["tab3"]:
        st.markdown('<div class="seccion-titulo">⚙️ COJINETES DEL GENERADOR</div>', unsafe_allow_html=True)

        df_coj = (
            df_f.groupby(["Mes_Num", "Mes_Label", "Periodo"])
            .agg(
                Sup=("Temp_Metal_CojSup_Seg07_C", "mean"),
                Inf=("Temp_Metal_CojInf_Seg4_C", "mean"),
                Turb=("Temp_Metal_CojTurbina_C", "mean"),
                Emp=("Temp_Metal_CojEmp_Seg3_C", "mean")
            )
            .reset_index()
            .sort_values("Mes_Num")
        )
        for c in ["Sup", "Inf", "Turb", "Emp"]:
            df_coj[c] = df_coj[c].round(1)

        fig_cj = go.Figure()
        for cv, nom, col in [
            ("Sup", "Coj. Superior", "#1565C0"),
            ("Inf", "Coj. Inferior", "#C00000"),
            ("Turb", "Coj. Turbina", "#888888"),
            ("Emp", "Coj. Empuje", "#BA7517")
        ]:
            fig_cj.add_trace(go.Scatter(
                x=df_coj["Mes_Label"], y=df_coj[cv],
                mode="lines+markers",
                name=nom,
                line=dict(color=col, width=2.5),
                marker=dict(size=6),
                hovertemplate="Mes: %{x}<br>Temp: %{y:.1f}°C<extra></extra>"
            ))

        fig_cj.update_layout(
            title="Temperatura metal de cojinetes",
            xaxis_title="Mes",
            yaxis=dict(title="Temperatura (°C)", range=[30, 90]),
            plot_bgcolor=theme_cfg["plot_bg"],
            paper_bgcolor=theme_cfg["paper_bg"],
            legend=dict(orientation="h", y=1.12),
            height=410
        )
        st.plotly_chart(fig_cj, use_container_width=True)

# ==============================================================================
# TAB 4 — REFRIGERACIÓN Y ACEITE
# ==============================================================================
if "tab4" in tabs_dict:
    with tabs_dict["tab4"]:
        st.markdown('<div class="seccion-titulo">💧 SISTEMA DE REFRIGERACIÓN Y ACEITE</div>', unsafe_allow_html=True)

        df_ref = (
            df_f.groupby(["Mes_Num", "Mes_Label", "Periodo"])
            .agg(
                AceiteTF=("Temp_Aceite_Transf", "mean"),
                PresRef=("Pres_Agua_SistRefrig_bar", "mean")
            )
            .reset_index()
            .sort_values("Mes_Num")
        )
        for c in ["AceiteTF", "PresRef"]:
            df_ref[c] = df_ref[c].round(1)

        if modo_movil:
            st.markdown("#### Temperatura de aceite del transformador")
            fig_a = go.Figure()
            for p, c in [("ANTES", C_ANTES), ("DESPUÉS", C_DESPUES)]:
                d = df_ref[df_ref["Periodo"] == p]
                if not d.empty:
                    fig_a.add_trace(go.Scatter(
                        x=d["Mes_Label"], y=d["AceiteTF"],
                        mode="lines+markers",
                        name=f"Aceite {p}",
                        line=dict(color=c, width=2.5),
                        marker=dict(size=7),
                        hovertemplate="Mes: %{x}<br>Temp: %{y:.1f}°C<extra></extra>"
                    ))
            fig_a.update_layout(
                title="Temperatura de aceite del transformador",
                xaxis_title="Mes",
                yaxis_title="Temperatura (°C)",
                plot_bgcolor=theme_cfg["plot_bg"],
                paper_bgcolor=theme_cfg["paper_bg"],
                legend=dict(orientation="h", y=1.12),
                height=370
            )
            st.plotly_chart(fig_a, use_container_width=True)

            st.markdown("#### Presión de agua del sistema de refrigeración")
            fig_p = go.Figure()
            for p, c in [("ANTES", C_ANTES), ("DESPUÉS", C_DESPUES)]:
                d = df_ref[df_ref["Periodo"] == p]
                if not d.empty:
                    fig_p.add_trace(go.Scatter(
                        x=d["Mes_Label"], y=d["PresRef"],
                        mode="lines+markers",
                        name=f"Presión {p}",
                        line=dict(color=c, width=2.5),
                        marker=dict(size=7),
                        hovertemplate="Mes: %{x}<br>Presión: %{y:.1f} bar<extra></extra>"
                    ))
            fig_p.update_layout(
                title="Presión de agua del sistema de refrigeración",
                xaxis_title="Mes",
                yaxis=dict(title="Presión (bar)", range=[2.5, 4.5]),
                plot_bgcolor=theme_cfg["plot_bg"],
                paper_bgcolor=theme_cfg["paper_bg"],
                legend=dict(orientation="h", y=1.12),
                height=370
            )
            st.plotly_chart(fig_p, use_container_width=True)
        else:
            c1, c2 = st.columns(2)

            with c1:
                fig_a = go.Figure()
                for p, c in [("ANTES", C_ANTES), ("DESPUÉS", C_DESPUES)]:
                    d = df_ref[df_ref["Periodo"] == p]
                    if not d.empty:
                        fig_a.add_trace(go.Scatter(
                            x=d["Mes_Label"], y=d["AceiteTF"],
                            mode="lines+markers",
                            name=f"Aceite {p}",
                            line=dict(color=c, width=2.5),
                            marker=dict(size=7),
                            hovertemplate="Mes: %{x}<br>Temp: %{y:.1f}°C<extra></extra>"
                        ))
                fig_a.update_layout(
                    title="Temperatura de aceite del transformador",
                    xaxis_title="Mes",
                    yaxis_title="Temperatura (°C)",
                    plot_bgcolor=theme_cfg["plot_bg"],
                    paper_bgcolor=theme_cfg["paper_bg"],
                    legend=dict(orientation="h", y=1.12),
                    height=370
                )
                st.plotly_chart(fig_a, use_container_width=True)

            with c2:
                fig_p = go.Figure()
                for p, c in [("ANTES", C_ANTES), ("DESPUÉS", C_DESPUES)]:
                    d = df_ref[df_ref["Periodo"] == p]
                    if not d.empty:
                        fig_p.add_trace(go.Scatter(
                            x=d["Mes_Label"], y=d["PresRef"],
                            mode="lines+markers",
                            name=f"Presión {p}",
                            line=dict(color=c, width=2.5),
                            marker=dict(size=7),
                            hovertemplate="Mes: %{x}<br>Presión: %{y:.1f} bar<extra></extra>"
                        ))
                fig_p.update_layout(
                    title="Presión de agua del sistema de refrigeración",
                    xaxis_title="Mes",
                    yaxis=dict(title="Presión (bar)", range=[2.5, 4.5]),
                    plot_bgcolor=theme_cfg["plot_bg"],
                    paper_bgcolor=theme_cfg["paper_bg"],
                    legend=dict(orientation="h", y=1.12),
                    height=370
                )
                st.plotly_chart(fig_p, use_container_width=True)

# ==============================================================================
# TAB 5 — DATOS Y ESTADÍSTICAS
# ==============================================================================
with tabs_dict["tab5"]:
    st.markdown('<div class="seccion-titulo">📋 ESTADÍSTICAS DESCRIPTIVAS</div>', unsafe_allow_html=True)

    cols_show = [
        "Temp_Nucleo_Estator2_C",
        "Temp_Dev_EstatorA3_C",
        "Temp_Dev_EstatorB2_C",
        "Temp_Dev_EstatorC1_C",
        "Temp_Metal_CojSup_Seg07_C",
        "Temp_Metal_CojInf_Seg4_C",
        "Temp_Metal_CojTurbina_C",
        "Temp_Metal_CojEmp_Seg3_C",
        "Potencia_Activa_MW"
    ]

    if modo_movil:
        with st.expander("##### PERÍODO ANTES", expanded=False):
            if not df_antes.empty:
                st.dataframe(df_antes[cols_show].describe().round(1), use_container_width=True, height=300)
            else:
                st.info("Sin datos ANTES.")
        with st.expander("##### PERÍODO DESPUÉS", expanded=False):
            if not df_despues.empty:
                st.dataframe(df_despues[cols_show].describe().round(1), use_container_width=True, height=300)
            else:
                st.info("Sin datos DESPUÉS.")
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("##### PERÍODO ANTES")
            if not df_antes.empty:
                st.dataframe(df_antes[cols_show].describe().round(1), use_container_width=True, height=300)
            else:
                st.info("Sin datos ANTES.")
        with c2:
            st.markdown("##### PERÍODO DESPUÉS")
            if not df_despues.empty:
                st.dataframe(df_despues[cols_show].describe().round(1), use_container_width=True, height=300)
            else:
                st.info("Sin datos DESPUÉS.")

    st.markdown("---")
    st.markdown('<div class="seccion-titulo">🗂️ DATOS CRUDOS FILTRADOS</div>', unsafe_allow_html=True)

    if st.checkbox("Mostrar datos crudos", value=False):
        cols_t = [
            "Fecha_Hora", "Periodo", "Mes_Label", "Potencia_Activa_MW",
            "Temp_Nucleo_Estator2_C", "Temp_Dev_EstatorA3_C", "Temp_Dev_EstatorB2_C",
            "Temp_Dev_EstatorC1_C", "Temp_Metal_CojSup_Seg07_C", "Temp_Metal_CojInf_Seg4_C",
            "Temp_Metal_CojTurbina_C", "Temp_Metal_CojEmp_Seg3_C"
        ]
        cols_t = [c for c in cols_t if c in df_f.columns]
        df_show = df_f[cols_t].copy()

        for c in cols_t[3:]:
            if c in df_show.columns:
                df_show[c] = pd.to_numeric(df_show[c], errors="coerce").round(1)

        st.dataframe(df_show.reset_index(drop=True), use_container_width=True, height=420)
        st.caption(f"Total registros filtrados: {len(df_f):,}")

    with st.expander("📖 Ver glosario técnico", expanded=not modo_movil):
        st.markdown('<div class="seccion-titulo">📖 GLOSARIO TÉCNICO</div>', unsafe_allow_html=True)

        glos = pd.DataFrame({
            "Término": [
                "P95 (Percentil 95)",
                "Desv. Estándar (σ)",
                "Delta (Δ)",
                "Potencia Activa",
                "ANTES",
                "DESPUÉS",
                "Devanado",
                "Núcleo Estátor",
                "Cojinete"
            ],
            "Definición": [
                "Temperatura superada solo el 5% del tiempo; indicador de condición sostenida real.",
                "Medida de variabilidad; menor σ implica mayor estabilidad térmica.",
                "Diferencia DESPUÉS - ANTES; valor negativo suele indicar mejora térmica.",
                "Energía eléctrica activa generada en MW; referencia de condición de carga.",
                "Período previo a la modernización del estátor.",
                "Período posterior a la modernización del estátor.",
                "Bobinado de cobre del generador donde se induce la corriente eléctrica.",
                "Parte fija del generador que concentra el flujo magnético.",
                "Elemento de soporte y guía del eje rotante, dependiente de adecuada lubricación."
            ]
        })
        st.dataframe(glos, use_container_width=True, hide_index=True, height=340)

# ==============================================================================
# PIE DE PÁGINA
# ==============================================================================
st.markdown("---")
st.markdown(f"""
<div style="text-align:center;color:{theme_cfg["text_soft"]};font-size:{'10px' if modo_movil else '12px'};padding:10px;">
    <b>Dashboard de Confiabilidad Operacional — Modernización Estátor U1 — V4 Responsive</b><br>
    Elaboro jaime alonso Rua M - ingeniero electronico | Central Hidroeléctrica Playas — EPM<br>
    Datos: Histórico SCADA validado | Mayo 2024 – Enero 2026
</div>
""", unsafe_allow_html=True)