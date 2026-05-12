"""Calculadora de Opcoes - Streamlit App.

Implementa Black-Scholes, Monte Carlo, Arvore Binomial e Volatilidade
Implicita (Newton-Raphson e Bissecao), com integracao opcional ao
Yahoo Finance via yfinance.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from pricing import (
    binomial_price,
    black_scholes_greeks,
    black_scholes_price,
    implied_vol_bisection,
    implied_vol_newton,
    monte_carlo_asian,
    monte_carlo_european,
    simulate_paths,
)
from utils import fetch_history, get_spot_price, historical_volatility


st.set_page_config(
    page_title="Calculadora de Opcoes",
    page_icon="??",
    layout="wide",
)

st.title("Calculadora de Opcoes")
st.caption(
    "Black-Scholes - Monte Carlo - Arvore Binomial - Volatilidade Implicita"
)

# ---------------------------------------------------------------------------
# Sidebar - parametros de entrada
# ---------------------------------------------------------------------------
st.sidebar.header("Parametros")

TICKER_SUGESTOES = [
    "PETR4.SA", "VALE3.SA", "ITUB4.SA", "BBDC4.SA",
    "AAPL", "MSFT", "TSLA", "^BVSP", "USDBRL=X",
]

usar_yahoo = st.sidebar.checkbox("Usar dados do Yahoo Finance", value=False)

S0_default = 38.0
sigma_default = 0.30
hist_df: pd.DataFrame | None = None

ticker = st.sidebar.selectbox(
    "Ticker (Yahoo Finance)",
    options=TICKER_SUGESTOES,
    index=0,
)
periodo = st.sidebar.selectbox(
    "Periodo do historico",
    options=["3mo", "6mo", "1y", "2y", "5y"],
    index=2,
)

if usar_yahoo:
    try:
        with st.spinner(f"Baixando historico de {ticker}..."):
            hist_df = fetch_history(ticker, period=periodo)
            S0_default = get_spot_price(hist_df)
            sigma_default = historical_volatility(hist_df)
        st.sidebar.success(
            f"Spot: {S0_default:.2f} | Vol. hist.: {sigma_default*100:.2f}%"
        )
    except Exception as exc:  # noqa: BLE001
        st.sidebar.error(f"Falha ao buscar dados: {exc}")
        hist_df = None

tipo_opcao = st.sidebar.selectbox(
    "Tipo de opcao",
    options=["europeia", "americana", "asiatica"],
)
payoff = st.sidebar.selectbox("Payoff", options=["call", "put"])

metodos_disponiveis = ["Black-Scholes", "Monte Carlo", "Arvore Binomial"]
if tipo_opcao == "americana":
    metodos_disponiveis = ["Arvore Binomial"]
elif tipo_opcao == "asiatica":
    metodos_disponiveis = ["Monte Carlo"]

metodo = st.sidebar.selectbox("Metodo de precificacao", options=metodos_disponiveis)

S0 = st.sidebar.number_input("Preco atual do ativo (S0)", value=float(S0_default), min_value=0.01, step=0.01, format="%.4f")
K = st.sidebar.number_input("Preco de exercicio (K)", value=40.0, min_value=0.01, step=0.01, format="%.4f")
T = st.sidebar.number_input("Prazo ate o vencimento (anos)", value=0.5, min_value=0.0001, step=0.05, format="%.4f")
r = st.sidebar.number_input("Taxa livre de risco (% a.a.)", value=10.0, step=0.25, format="%.4f") / 100.0
sigma = st.sidebar.number_input("Volatilidade (% a.a.)", value=float(sigma_default * 100), min_value=0.01, step=0.5, format="%.4f") / 100.0

n_sims = st.sidebar.number_input("Numero de simulacoes (Monte Carlo)", value=20000, min_value=100, step=1000)
n_steps_mc = st.sidebar.number_input("Passos por trajetoria (Monte Carlo)", value=126, min_value=1, step=10)
n_steps_bin = st.sidebar.number_input("Passos da Arvore Binomial", value=200, min_value=1, step=10)
seed = st.sidebar.number_input("Seed (Monte Carlo)", value=42, step=1)

st.sidebar.markdown("---")
st.sidebar.subheader("Volatilidade Implicita")
preco_mercado = st.sidebar.number_input("Preco de mercado da opcao", value=0.0, min_value=0.0, step=0.01, format="%.4f")
metodo_vi = st.sidebar.selectbox("Metodo", options=["Newton-Raphson", "Bissecao"])

# ---------------------------------------------------------------------------
# Abas principais
# ---------------------------------------------------------------------------
abas = st.tabs([
    "Preco",
    "Volatilidade Implicita",
    "Payoff",
    "Monte Carlo",
    "Comparacao",
    "Historico",
])

# ---------------------------------------------------------------------------
# Aba: Preco
# ---------------------------------------------------------------------------
with abas[0]:
    st.subheader("Calculo do Preco")

    resultado_preco = None
    detalhes = {}

    try:
        if tipo_opcao == "europeia":
            if metodo == "Black-Scholes":
                resultado_preco = black_scholes_price(S0, K, T, r, sigma, payoff)
                greeks = black_scholes_greeks(S0, K, T, r, sigma, payoff)
                detalhes["greeks"] = greeks
            elif metodo == "Monte Carlo":
                mc = monte_carlo_european(
                    S0, K, T, r, sigma, payoff,
                    n_sims=int(n_sims), seed=int(seed),
                )
                resultado_preco = mc["price"]
                detalhes["mc"] = mc
            elif metodo == "Arvore Binomial":
                resultado_preco = binomial_price(
                    S0, K, T, r, sigma,
                    n_steps=int(n_steps_bin),
                    option_type=payoff,
                    exercise="european",
                )
        elif tipo_opcao == "americana":
            resultado_preco = binomial_price(
                S0, K, T, r, sigma,
                n_steps=int(n_steps_bin),
                option_type=payoff,
                exercise="american",
            )
            # comparacao com europeia para mostrar premio de exercicio antecipado
            preco_eu = binomial_price(
                S0, K, T, r, sigma,
                n_steps=int(n_steps_bin),
                option_type=payoff,
                exercise="european",
            )
            detalhes["preco_europeia"] = preco_eu
            detalhes["premio_exercicio"] = resultado_preco - preco_eu
        elif tipo_opcao == "asiatica":
            mc = monte_carlo_asian(
                S0, K, T, r, sigma, payoff,
                n_sims=int(n_sims), n_steps=int(n_steps_mc),
                seed=int(seed),
            )
            resultado_preco = mc["price"]
            detalhes["mc"] = mc
    except Exception as exc:  # noqa: BLE001
        st.error(f"Erro no calculo: {exc}")

    if resultado_preco is not None:
        col1, col2, col3 = st.columns(3)
        col1.metric(
            f"Preco ({tipo_opcao} {payoff})",
            f"R$ {resultado_preco:.4f}",
        )
        col2.metric("S0", f"{S0:.2f}")
        col3.metric("K", f"{K:.2f}")

        if "greeks" in detalhes:
            st.markdown("### Gregas (Black-Scholes)")
            greeks = detalhes["greeks"]
            gcols = st.columns(5)
            gcols[0].metric("Delta", f"{greeks['delta']:.4f}")
            gcols[1].metric("Gamma", f"{greeks['gamma']:.4f}")
            gcols[2].metric("Vega", f"{greeks['vega']:.4f}")
            gcols[3].metric("Theta", f"{greeks['theta']:.4f}")
            gcols[4].metric("Rho", f"{greeks['rho']:.4f}")

        if "mc" in detalhes:
            mc = detalhes["mc"]
            st.markdown("### Estatisticas da Simulacao")
            mcols = st.columns(3)
            mcols[0].metric("Erro padrao", f"{mc['std_error']:.6f}")
            mcols[1].metric("IC 95% inferior", f"{mc['ci_low']:.4f}")
            mcols[2].metric("IC 95% superior", f"{mc['ci_high']:.4f}")

        if tipo_opcao == "americana":
            st.markdown("### Valor do Exercicio Antecipado")
            ec1, ec2 = st.columns(2)
            ec1.metric("Preco europeia (comparacao)", f"{detalhes['preco_europeia']:.4f}")
            ec2.metric("Premio de exercicio antecipado", f"{detalhes['premio_exercicio']:.4f}")
            st.info(
                "Para puts americanas, o premio de exercicio antecipado costuma ser "
                "positivo quando o ativo cai significativamente abaixo do strike. "
                "Para calls americanas sem dividendos, o premio tende a zero."
            )

# ---------------------------------------------------------------------------
# Aba: Volatilidade Implicita
# ---------------------------------------------------------------------------
with abas[1]:
    st.subheader("Calculo da Volatilidade Implicita (Black-Scholes)")
    if preco_mercado <= 0:
        st.info("Informe um preco de mercado positivo na barra lateral.")
    else:
        if metodo_vi == "Newton-Raphson":
            resvi = implied_vol_newton(preco_mercado, S0, K, T, r, payoff)
        else:
            resvi = implied_vol_bisection(preco_mercado, S0, K, T, r, payoff)

        if resvi["error"]:
            st.error(resvi["error"])
        if not np.isnan(resvi["sigma"]):
            c1, c2, c3 = st.columns(3)
            c1.metric("Vol. implicita", f"{resvi['sigma']*100:.4f}%")
            c2.metric("Iteracoes", f"{resvi['iterations']}")
            c3.metric("Convergiu", "Sim" if resvi["converged"] else "Nao")

            # comparacao com volatilidade historica, se disponivel
            if usar_yahoo and hist_df is not None:
                vol_hist = historical_volatility(hist_df)
                st.markdown(
                    f"**Vol. historica ({periodo}):** {vol_hist*100:.2f}% | "
                    f"**Vol. implicita:** {resvi['sigma']*100:.2f}% | "
                    f"**Spread:** {(resvi['sigma']-vol_hist)*100:.2f} p.p."
                )

            # comparacao entre os dois metodos
            st.markdown("### Comparacao Newton-Raphson vs Bissecao")
            r_nr = implied_vol_newton(preco_mercado, S0, K, T, r, payoff)
            r_bs = implied_vol_bisection(preco_mercado, S0, K, T, r, payoff)
            tabela = pd.DataFrame(
                [
                    {"Metodo": "Newton-Raphson", "Sigma": r_nr["sigma"], "Iteracoes": r_nr["iterations"], "Convergiu": r_nr["converged"]},
                    {"Metodo": "Bissecao", "Sigma": r_bs["sigma"], "Iteracoes": r_bs["iterations"], "Convergiu": r_bs["converged"]},
                ]
            )
            st.dataframe(tabela, use_container_width=True)

            # smile de volatilidade aproximado (variando strike)
            st.markdown("### Smile de Volatilidade (Black-Scholes)")
            strikes = np.linspace(0.7 * S0, 1.3 * S0, 21)
            # como precisamos de precos de mercado para todos os strikes, geramos
            # um conjunto sintetico assumindo a vol. implicita encontrada como
            # ATM e adicionando um leve smile quadratico ilustrativo.
            base_sigma = resvi["sigma"]
            smile = base_sigma + 0.15 * base_sigma * ((strikes - S0) / S0) ** 2
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=strikes, y=smile * 100, mode="lines+markers", name="Vol. implicita (%)"))
            fig.update_layout(
                xaxis_title="Strike", yaxis_title="Vol. implicita (%)",
                title="Smile de volatilidade (ilustrativo)",
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption(
                "Smile gerado de forma ilustrativa. Para um smile real, e necessario "
                "alimentar precos de mercado para cada strike."
            )

# ---------------------------------------------------------------------------
# Aba: Payoff
# ---------------------------------------------------------------------------
with abas[2]:
    st.subheader("Diagrama de Payoff no Vencimento")
    ST = np.linspace(0.5 * S0, 1.5 * S0, 200)
    if payoff == "call":
        payoffs = np.maximum(ST - K, 0.0)
    else:
        payoffs = np.maximum(K - ST, 0.0)

    # tenta calcular um premio de referencia para a P&L
    try:
        if tipo_opcao == "americana":
            premio = binomial_price(S0, K, T, r, sigma, n_steps=int(n_steps_bin),
                                    option_type=payoff, exercise="american")
        elif tipo_opcao == "asiatica":
            premio = monte_carlo_asian(S0, K, T, r, sigma, payoff,
                                       n_sims=int(n_sims), n_steps=int(n_steps_mc),
                                       seed=int(seed))["price"]
        else:
            premio = black_scholes_price(S0, K, T, r, sigma, payoff)
    except Exception:  # noqa: BLE001
        premio = 0.0

    pnl = payoffs - premio

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ST, y=payoffs, mode="lines", name="Payoff no vencimento"))
    fig.add_trace(go.Scatter(x=ST, y=pnl, mode="lines", name=f"P&L (premio = {premio:.4f})"))
    fig.add_hline(y=0, line_dash="dot", line_color="gray")
    fig.add_vline(x=K, line_dash="dash", line_color="red", annotation_text=f"K = {K}")
    fig.update_layout(
        xaxis_title="Preco do ativo no vencimento (ST)",
        yaxis_title="Valor",
        title=f"{payoff.upper()} {tipo_opcao}",
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Aba: Monte Carlo
# ---------------------------------------------------------------------------
with abas[3]:
    st.subheader("Simulacao de Monte Carlo")
    n_show = st.slider("Trajetorias a exibir", min_value=10, max_value=200, value=50)
    paths = simulate_paths(
        S0=S0, r=r, sigma=sigma, T=T,
        n_steps=int(n_steps_mc),
        n_sims=max(int(n_show), 1000),
        seed=int(seed),
    )
    tempo = np.linspace(0, T, paths.shape[1])

    fig = go.Figure()
    for i in range(min(n_show, paths.shape[0])):
        fig.add_trace(
            go.Scatter(x=tempo, y=paths[i], mode="lines",
                       line=dict(width=1), showlegend=False, opacity=0.5)
        )
    fig.add_hline(y=K, line_dash="dash", line_color="red",
                  annotation_text=f"K = {K}")
    fig.update_layout(
        title="Trajetorias simuladas do preco",
        xaxis_title="Tempo (anos)", yaxis_title="Preco do ativo",
    )
    st.plotly_chart(fig, use_container_width=True)

    # distribuicao do preco terminal
    ST_dist = paths[:, -1]
    hist = go.Figure()
    hist.add_trace(go.Histogram(x=ST_dist, nbinsx=60, name="ST"))
    hist.add_vline(x=K, line_dash="dash", line_color="red",
                   annotation_text=f"K = {K}")
    hist.update_layout(
        title="Distribuicao do preco no vencimento",
        xaxis_title="ST", yaxis_title="Frequencia",
    )
    st.plotly_chart(hist, use_container_width=True)

# ---------------------------------------------------------------------------
# Aba: Comparacao entre Metodos
# ---------------------------------------------------------------------------
with abas[4]:
    st.subheader("Comparacao entre Metodos")
    linhas = []

    # Black-Scholes (europeia)
    try:
        bs = black_scholes_price(S0, K, T, r, sigma, payoff)
        linhas.append({"Metodo": "Black-Scholes (europeia)", "Preco": bs, "Obs": "Formula fechada"})
    except Exception as exc:  # noqa: BLE001
        linhas.append({"Metodo": "Black-Scholes (europeia)", "Preco": np.nan, "Obs": str(exc)})

    # Monte Carlo europeia
    try:
        mc_eu = monte_carlo_european(S0, K, T, r, sigma, payoff,
                                     n_sims=int(n_sims), seed=int(seed))
        linhas.append({
            "Metodo": "Monte Carlo (europeia)",
            "Preco": mc_eu["price"],
            "Obs": f"IC95% [{mc_eu['ci_low']:.4f}, {mc_eu['ci_high']:.4f}]",
        })
    except Exception as exc:  # noqa: BLE001
        linhas.append({"Metodo": "Monte Carlo (europeia)", "Preco": np.nan, "Obs": str(exc)})

    # Binomial europeia
    try:
        bin_eu = binomial_price(S0, K, T, r, sigma, n_steps=int(n_steps_bin),
                                option_type=payoff, exercise="european")
        linhas.append({
            "Metodo": "Arvore Binomial (europeia)", "Preco": bin_eu,
            "Obs": f"{int(n_steps_bin)} passos",
        })
    except Exception as exc:  # noqa: BLE001
        linhas.append({"Metodo": "Arvore Binomial (europeia)", "Preco": np.nan, "Obs": str(exc)})

    # Binomial americana
    try:
        bin_us = binomial_price(S0, K, T, r, sigma, n_steps=int(n_steps_bin),
                                option_type=payoff, exercise="american")
        linhas.append({
            "Metodo": "Arvore Binomial (americana)", "Preco": bin_us,
            "Obs": f"{int(n_steps_bin)} passos",
        })
    except Exception as exc:  # noqa: BLE001
        linhas.append({"Metodo": "Arvore Binomial (americana)", "Preco": np.nan, "Obs": str(exc)})

    # Monte Carlo asiatica
    try:
        mc_as = monte_carlo_asian(S0, K, T, r, sigma, payoff,
                                  n_sims=int(n_sims), n_steps=int(n_steps_mc),
                                  seed=int(seed))
        linhas.append({
            "Metodo": "Monte Carlo (asiatica aritmetica)", "Preco": mc_as["price"],
            "Obs": f"IC95% [{mc_as['ci_low']:.4f}, {mc_as['ci_high']:.4f}]",
        })
    except Exception as exc:  # noqa: BLE001
        linhas.append({"Metodo": "Monte Carlo (asiatica aritmetica)", "Preco": np.nan, "Obs": str(exc)})

    df_cmp = pd.DataFrame(linhas)
    st.dataframe(df_cmp, use_container_width=True)

    st.markdown("### Sensibilidade do preco a volatilidade")
    sigmas = np.linspace(max(0.01, sigma * 0.3), sigma * 2.0, 30)
    serie_bs = [black_scholes_price(S0, K, T, r, s, payoff) for s in sigmas]
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=sigmas * 100, y=serie_bs, mode="lines+markers",
                             name="Black-Scholes"))
    fig.update_layout(
        xaxis_title="Volatilidade (%)", yaxis_title="Preco da opcao",
        title="Preco vs Volatilidade",
    )
    st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Aba: Historico (Yahoo Finance)
# ---------------------------------------------------------------------------
with abas[5]:
    st.subheader("Dados Historicos do Ativo")
    if not usar_yahoo or hist_df is None:
        st.info("Ative 'Usar dados do Yahoo Finance' na barra lateral para visualizar.")
    else:
        st.markdown(f"**Ticker:** {ticker} | **Periodo:** {periodo}")
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist_df.index, y=hist_df["Close"],
                                 mode="lines", name="Close"))
        fig.update_layout(
            title=f"Precos historicos - {ticker}",
            xaxis_title="Data", yaxis_title="Preco",
        )
        st.plotly_chart(fig, use_container_width=True)

        log_returns = np.log(hist_df["Close"] / hist_df["Close"].shift(1)).dropna()
        vol_anual = historical_volatility(hist_df)

        c1, c2, c3 = st.columns(3)
        c1.metric("Spot", f"{get_spot_price(hist_df):.2f}")
        c2.metric("Vol. anualizada", f"{vol_anual*100:.2f}%")
        c3.metric("Observacoes", f"{len(hist_df)}")

        fig2 = go.Figure()
        fig2.add_trace(go.Histogram(x=log_returns, nbinsx=50, name="Log-retornos"))
        fig2.update_layout(
            title="Distribuicao dos retornos logaritmicos",
            xaxis_title="Log-retorno", yaxis_title="Frequencia",
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.dataframe(hist_df.tail(20), use_container_width=True)


st.markdown("---")
st.caption(
    "Curso de Gestao de Riscos e Derivativos - Calculadora de Opcoes "
    "(Black-Scholes, Monte Carlo, Arvore Binomial e Volatilidade Implicita)."
)
