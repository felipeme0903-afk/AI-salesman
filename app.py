"""
Monitor de Equity — Dashboard Streamlit
Rodar: streamlit run app.py
"""
from datetime import datetime

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import analysis as an

# ══════════════════════════════════════════════════════════════
# PAGE CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="Monitor de Equity",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

CSS = """
<style>
    .block-container { padding-top: 1.5rem; padding-bottom: 1rem; }
    [data-testid="stMetricValue"] { font-size: 1.4rem; }
    [data-testid="stMetricDelta"] { font-size: 0.95rem; }
    .small-muted { color: #888; font-size: 0.85rem; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# CACHE
# ══════════════════════════════════════════════════════════════
@st.cache_data(ttl=300, show_spinner=False)
def carregar_tudo():
    return an.rodar_analise(an.SETORES_ACOES, an.MACRO, log=lambda *_: None)


# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.title("⚙️ Controles")

    if st.button("🔄 Atualizar agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    auto = st.toggle("Auto-refresh", value=False, help="Recarrega a página periodicamente")
    intervalo = st.select_slider(
        "Intervalo (min)",
        options=[1, 2, 5, 10, 15, 30],
        value=5,
        disabled=not auto,
    )
    if auto:
        st.markdown(
            f'<meta http-equiv="refresh" content="{intervalo * 60}">',
            unsafe_allow_html=True,
        )
        st.caption(f"⏱️ Recarregando a cada {intervalo} min")

    st.divider()
    st.subheader("Filtros")
    setores_disponiveis = sorted(an.SETORES_ACOES.keys(), key=an._ordem_setor)
    setores_selec = st.multiselect(
        "Setores",
        options=setores_disponiveis,
        default=setores_disponiveis,
    )

    st.divider()
    st.caption("Fonte: Yahoo Finance via `yfinance`")
    st.caption(f"Cache: 5 min • Benchmark: {an.BENCHMARK}")


# ══════════════════════════════════════════════════════════════
# CARREGAMENTO
# ══════════════════════════════════════════════════════════════
with st.spinner("Baixando dados do mercado..."):
    dados = carregar_tudo()

df_acoes     = dados['acoes']
df_setores   = dados['setores']
df_macro     = dados['macro']
precos_acoes = dados['precos_acoes']
precos_macro = dados['precos_macro']

ano_atual = an.DATAS['ini_ano_atual'].year
ano_ant   = an.DATAS['ini_ano_ant'].year


# ══════════════════════════════════════════════════════════════
# HEADER
# ══════════════════════════════════════════════════════════════
col_tit, col_ts = st.columns([3, 1])
with col_tit:
    st.title("📊 Monitor de Equity — Mercado BR")
with col_ts:
    st.markdown(
        f"<div style='text-align:right;margin-top:1.2rem;' class='small-muted'>"
        f"Atualizado: <b>{datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</b></div>",
        unsafe_allow_html=True,
    )


# ══════════════════════════════════════════════════════════════
# MACRO STRIP — Cards com último valor e variação do dia
# ══════════════════════════════════════════════════════════════
def variacao_diaria(serie: pd.Series) -> float:
    s = serie.dropna()
    if len(s) < 2:
        return np.nan
    return (s.iloc[-1] / s.iloc[-2] - 1) * 100

macro_ordem = ["^BVSP", "USDBRL=X", "^GSPC", "^IXIC", "CL=F", "GC=F", "BTC-USD"]
cards = [t for t in macro_ordem if t in precos_macro.columns]
cols = st.columns(len(cards))
for col, t in zip(cols, cards):
    serie = precos_macro[t].dropna()
    if serie.empty:
        continue
    valor = serie.iloc[-1]
    var   = variacao_diaria(serie)
    nome  = an.MACRO_NOMES.get(t, t)
    fmt   = f"{valor:,.2f}" if valor > 1 else f"{valor:,.4f}"
    col.metric(nome, fmt, f"{var:+.2f}%" if pd.notna(var) else None)

st.divider()


# ══════════════════════════════════════════════════════════════
# FORMATAÇÃO DE TABELAS
# ══════════════════════════════════════════════════════════════
def cor_pct(v):
    if pd.isna(v):
        return ""
    if v > 0:
        return "color: #16a34a; font-weight: 600;"
    if v < 0:
        return "color: #dc2626; font-weight: 600;"
    return ""

def cor_rsi(v):
    if pd.isna(v):
        return ""
    if v >= 70:
        return "background-color: #fee2e2; color: #991b1b;"
    if v <= 30:
        return "background-color: #dcfce7; color: #166534;"
    return ""

def estilizar(df: pd.DataFrame):
    cols_pct = [c for c in df.columns if "%" in c or c in ("Ret", "DY (%)")]
    cols_pct = [c for c in df.columns if "%" in c]
    sty = df.style.format(precision=2, na_rep="—")
    if cols_pct:
        sty = sty.map(cor_pct, subset=cols_pct)
    if "RSI(14)" in df.columns:
        sty = sty.map(cor_rsi, subset=["RSI(14)"])
    return sty


# ══════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════
tab1, tab2, tab3, tab4 = st.tabs(
    ["📈 Ativos", "🏭 Setores", "🌎 Macro", "📉 Gráficos"]
)

# ── TAB 1 · ATIVOS ────────────────────────────────────────────
with tab1:
    st.subheader("Análise por ativo")

    df_view = df_acoes.reset_index()
    df_view = df_view[df_view['Setor'].isin(setores_selec)]

    # Ordenação por coluna de retorno
    col_ytd = next((c for c in df_view.columns if "YTD" in c and "Vol" not in c), None)

    c1, c2, c3 = st.columns([2, 2, 6])
    ordenar_por = c1.selectbox(
        "Ordenar por",
        options=[c for c in df_view.columns if c not in ('Setor', 'Ticker')],
        index=[c for c in df_view.columns if c not in ('Setor', 'Ticker')].index(col_ytd)
              if col_ytd else 0,
    )
    ordem_desc = c2.toggle("Decrescente", value=True)
    df_view = df_view.sort_values(ordenar_por, ascending=not ordem_desc)

    st.dataframe(
        estilizar(df_view.set_index(['Setor', 'Ticker'])),
        use_container_width=True,
        height=600,
    )

    st.caption(
        f"YTD = {an.DATAS['ini_ano_atual'].strftime('%d/%m/%Y')} → hoje • "
        f"H1/{ano_ant} = {an.DATAS['ini_ano_ant'].strftime('%d/%m')}/{ano_ant} → "
        f"{an.DATAS['meio_ano_ant'].strftime('%d/%m')}/{ano_ant}"
    )

# ── TAB 2 · SETORES ───────────────────────────────────────────
with tab2:
    st.subheader("Resumo setorial (médias)")
    st.dataframe(estilizar(df_setores), use_container_width=True, height=450)

    col_ytd_s = next((c for c in df_setores.columns if "YTD" in c and "Vol" not in c), None)
    if col_ytd_s:
        st.subheader(f"Ranking · {col_ytd_s}")
        df_rank = df_setores[[col_ytd_s]].dropna().sort_values(col_ytd_s)
        fig = go.Figure(go.Bar(
            x=df_rank[col_ytd_s],
            y=df_rank.index,
            orientation='h',
            marker_color=['#dc2626' if v < 0 else '#16a34a' for v in df_rank[col_ytd_s]],
            text=[f"{v:+.2f}%" for v in df_rank[col_ytd_s]],
            textposition='outside',
        ))
        fig.update_layout(
            height=400, margin=dict(l=10, r=10, t=10, b=10),
            xaxis_title="%", yaxis_title=None,
            plot_bgcolor='rgba(0,0,0,0)',
        )
        st.plotly_chart(fig, use_container_width=True)

# ── TAB 3 · MACRO ─────────────────────────────────────────────
with tab3:
    st.subheader("Macro & referências globais")
    st.dataframe(estilizar(df_macro), use_container_width=True, height=400)

# ── TAB 4 · GRÁFICOS ──────────────────────────────────────────
with tab4:
    st.subheader("Gráfico histórico")

    tickers_filtrados = [
        t for s in setores_selec for t in an.SETORES_ACOES.get(s, [])
        if t in precos_acoes.columns
    ]
    tickers_macro = [t for t in precos_macro.columns]

    c1, c2 = st.columns([1, 1])
    fonte = c1.radio("Fonte", ["Ações", "Macro"], horizontal=True)
    if fonte == "Ações":
        opcoes = tickers_filtrados
        precos = precos_acoes
    else:
        opcoes = tickers_macro
        precos = precos_macro
        opcoes = [t for t in opcoes if t in precos.columns]

    if not opcoes:
        st.info("Nenhum ticker disponível para os filtros atuais.")
    else:
        ticker = c2.selectbox("Ativo", opcoes)
        periodo = st.radio(
            "Período",
            ["1M", "3M", "6M", "YTD", "1A", "2A"],
            horizontal=True, index=3,
        )

        serie = precos[ticker].dropna()
        hoje = serie.index[-1]
        mapa_per = {
            "1M":  serie.index >= hoje - pd.Timedelta(days=30),
            "3M":  serie.index >= hoje - pd.Timedelta(days=90),
            "6M":  serie.index >= hoje - pd.Timedelta(days=180),
            "YTD": serie.index >= pd.Timestamp(an.DATAS['ini_ano_atual']),
            "1A":  serie.index >= hoje - pd.Timedelta(days=365),
            "2A":  serie.index >= hoje - pd.Timedelta(days=730),
        }
        s_plot = serie[mapa_per[periodo]]
        mm50   = serie.rolling(50).mean()[mapa_per[periodo]]

        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=s_plot.index, y=s_plot.values,
            name=ticker, line=dict(color='#2563eb', width=2),
            fill='tozeroy', fillcolor='rgba(37,99,235,0.08)',
        ))
        fig.add_trace(go.Scatter(
            x=mm50.index, y=mm50.values,
            name='MM50', line=dict(color='#f59e0b', width=1.2, dash='dash'),
        ))
        fig.update_layout(
            height=500, margin=dict(l=10, r=10, t=30, b=10),
            hovermode='x unified',
            plot_bgcolor='rgba(0,0,0,0)',
            legend=dict(orientation='h', yanchor='bottom', y=1.02, x=0),
        )
        st.plotly_chart(fig, use_container_width=True)

        k1, k2, k3, k4 = st.columns(4)
        k1.metric("Último", f"{s_plot.iloc[-1]:,.2f}")
        k2.metric("Mín período", f"{s_plot.min():,.2f}")
        k3.metric("Máx período", f"{s_plot.max():,.2f}")
        ret_per = (s_plot.iloc[-1] / s_plot.iloc[0] - 1) * 100
        k4.metric("Retorno período", f"{ret_per:+.2f}%")
