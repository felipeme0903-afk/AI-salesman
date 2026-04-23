import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta
import warnings
import re
warnings.filterwarnings('ignore')

# ══════════════════════════════════════════════════════════════
# CONFIGURAÇÃO
# ══════════════════════════════════════════════════════════════

SETORES_ACOES = {
    "1.Energia Elétrica":    ["AURE3.SA", "CMIG4.SA", "SBSP3.SA", "ENGI11.SA", "AXIA3.SA"],
    "2.Petróleo e Gás":      ["PETR4.SA", "GGRAIZ4.SA", "UGPA3.SA", "BRAV3.SA"],
    "3.Mineração/Siderurgia":["VALE3.SA", "GGBR4.SA", "USIM5.SA", "CSNA3.SA"],
    "4.Varejo e Consumo":    ["ABEV3.SA", "ASAI3.SA", "LREN3.SA", "MGLU3.SA"],
    "5.Construção":          ["CYRE3.SA", "MRVE3.SA", "JHSF3.SA", "MDNE3.SA"],
    "6.Telecom":             ["TIMS3.SA", "VIVT3.SA", "OIBR3.SA"],
    "7.Transportes":         ["RAIL3.SA", "JSLG3.SA", "MOVI3.SA", "VAMO3.SA"],
    "8.Saúde":               ["RDOR3.SA", "HAPV3.SA", "FLRY3.SA", "RADL3.SA"],
    "9.Educação":            ["CSED3.SA", "SEER3.SA", "ANIM3.SA", "YDUQ3.SA", "COGN3.SA"],
    "10.Empresas Estrangeiras": ["NVDC34.SA", "AAPL34.SA", "MSFT34.SA", "GOGL34.SA", "M1TA34.SA"],
}

MACRO = {
    "Índices":     ["^IXIC", "^GSPC", "^BVSP"],
    "Câmbio":      ["USDBRL=X", "EURBRL=X"],
    "Commodities": ["GC=F", "CL=F"],
    "Cripto":      ["BTC-USD"],
}

MACRO_NOMES = {
    "^IXIC": "Nasdaq", "^GSPC": "S&P 500", "^BVSP": "Ibovespa",
    "USDBRL=X": "USD/BRL", "EURBRL=X": "EUR/BRL",
    "GC=F": "Ouro (USD)", "CL=F": "Petróleo WTI", "BTC-USD": "Bitcoin",
}

BENCHMARK = "^BVSP"

# ══════════════════════════════════════════════════════════════
# DATAS FIXAS DE REFERÊNCIA
# ══════════════════════════════════════════════════════════════

def get_datas_fixas() -> dict:
    hoje = datetime.now()
    ano  = hoje.year
    return {
        'hoje':          hoje,
        'ini_ano_atual': datetime(ano,     1, 1),
        'ini_ano_ant':   datetime(ano - 1, 1, 1),
        'meio_ano_ant':  datetime(ano - 1, 7, 1),
    }

DATAS = get_datas_fixas()

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════

def safe_get(info: dict, key: str):
    val = info.get(key)
    return val if val not in (None, "N/A", "", 0) else np.nan

def to_pct(value):
    return round(value * 100, 2) if pd.notna(value) else np.nan

def nearest_price(serie: pd.Series, data: datetime) -> float:
    idx = serie.index.get_indexer([data], method='nearest')[0]
    return serie.iloc[idx]

def retorno_fixo(serie: pd.Series, data_ini: datetime, data_fim: datetime) -> float:
    p_ini = nearest_price(serie, data_ini)
    p_fim = nearest_price(serie, data_fim)
    if pd.isna(p_ini) or pd.isna(p_fim) or p_ini == 0:
        return np.nan
    return round(((p_fim / p_ini) - 1) * 100, 2)

def serie_ytd(serie: pd.Series) -> pd.Series:
    idx_ini = serie.index.get_indexer([DATAS['ini_ano_atual']], method='nearest')[0]
    return serie.iloc[idx_ini:]

def calc_rsi(serie: pd.Series, periodo: int = 14) -> float:
    delta = serie.diff()
    ganho = delta.clip(lower=0).ewm(com=periodo - 1, min_periods=periodo).mean()
    perda = (-delta.clip(upper=0)).ewm(com=periodo - 1, min_periods=periodo).mean()
    rs = ganho / perda
    return round((100 - 100 / (1 + rs)).iloc[-1], 1)

def calc_beta(ret_ativo: pd.Series, ret_bench: pd.Series) -> float:
    df = pd.concat([ret_ativo, ret_bench], axis=1).dropna()
    if len(df) < 20:
        return np.nan
    cov = np.cov(df.iloc[:, 0], df.iloc[:, 1])
    return round(cov[0, 1] / cov[1, 1], 2)

def baixar_precos(tickers: list, period: str = '2y') -> pd.DataFrame:
    dados = yf.download(tickers, period=period, auto_adjust=True,
                        threads=True, progress=False)['Close']
    if isinstance(dados, pd.Series):
        dados = dados.to_frame(name=tickers[0])
    for t in tickers:
        if t not in dados.columns:
            dados[t] = np.nan
    return dados.ffill()

def _ordem_setor(nome: str) -> int:
    """Extrai o número prefixo do setor para ordenação numérica (não alfabética)."""
    m = re.match(r'^(\d+)\.', nome)
    return int(m.group(1)) if m else 999

# ══════════════════════════════════════════════════════════════
# MÓDULO 1 — ANÁLISE TÉCNICA E DE RISCO
# ══════════════════════════════════════════════════════════════

def analisar_tecnico_risco(precos: pd.DataFrame, bench_retornos: pd.Series) -> pd.DataFrame:
    hoje_ts = precos.index[-1]
    registros = []

    bench_ytd = bench_retornos.loc[
        bench_retornos.index >= precos.index[
            precos.index.get_indexer([DATAS['ini_ano_atual']], method='nearest')[0]
        ]
    ] if len(bench_retornos) > 0 else pd.Series(dtype=float)

    for ticker in precos.columns:
        serie = precos[ticker].dropna()
        if len(serie) < 30:
            continue

        p_atual   = serie.iloc[-1]
        p_52w_max = serie.tail(252).max()
        p_52w_min = serie.tail(252).min()
        mm50      = serie.tail(50).mean()

        s_ytd     = serie_ytd(serie)
        ret_ytd   = s_ytd.pct_change().dropna()
        n_pregoes = len(ret_ytd)

        registros.append({
            'Ticker': ticker,
            'Preço (R$)':                          round(p_atual, 2),
            f'Ret YTD/{DATAS["ini_ano_atual"].year} (%)':
                retorno_fixo(serie, DATAS['ini_ano_atual'], hoje_ts),
            f'Ret H1/{DATAS["ini_ano_ant"].year} (%)':
                retorno_fixo(serie, DATAS['ini_ano_ant'], DATAS['meio_ano_ant']),
            f'Ret Jan{DATAS["ini_ano_ant"].year}→Hoje (%)':
                retorno_fixo(serie, DATAS['ini_ano_ant'], hoje_ts),
            f'Vol YTD ({n_pregoes}d) (%)':
                round(ret_ytd.std() * np.sqrt(n_pregoes) * 100, 2) if n_pregoes >= 5 else np.nan,
            'Beta (IBOV)':   calc_beta(ret_ytd, bench_ytd),
            'RSI(14)':        calc_rsi(serie),
            'vs Máx 52s (%)': round(((p_atual / p_52w_max) - 1) * 100, 2),
            'vs Mín 52s (%)': round(((p_atual / p_52w_min) - 1) * 100, 2),
            'vs MM50 (%)':    round(((p_atual / mm50) - 1) * 100, 2),
        })

    return pd.DataFrame(registros).set_index('Ticker')

# ══════════════════════════════════════════════════════════════
# MÓDULO 2 — ANÁLISE FUNDAMENTALISTA
# ══════════════════════════════════════════════════════════════

def analisar_fundamentos(tickers: list) -> pd.DataFrame:
    registros = []
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            registros.append({
                'Ticker':          ticker,
                'P/L':             round(safe_get(info, 'trailingPE'), 1)
                                   if pd.notna(safe_get(info, 'trailingPE')) else np.nan,
                'P/VPA':           round(safe_get(info, 'priceToBook'), 2)
                                   if pd.notna(safe_get(info, 'priceToBook')) else np.nan,
                'EV/EBITDA':       round(safe_get(info, 'enterpriseToEbitda'), 1)
                                   if pd.notna(safe_get(info, 'enterpriseToEbitda')) else np.nan,
                'DY (%)':          to_pct(safe_get(info, 'dividendYield')),
                'ROE (%)':         to_pct(safe_get(info, 'returnOnEquity')),
                'Margem Liq (%)':  to_pct(safe_get(info, 'profitMargins')),
                'Dív/PL':          round(safe_get(info, 'debtToEquity') / 100, 2)
                                   if pd.notna(safe_get(info, 'debtToEquity')) else np.nan,
                'Mkt Cap (Bi R$)': round(safe_get(info, 'marketCap') / 1e9, 1)
                                   if pd.notna(safe_get(info, 'marketCap')) else np.nan,
            })
        except Exception:
            registros.append({'Ticker': ticker})
    return pd.DataFrame(registros).set_index('Ticker')

# ══════════════════════════════════════════════════════════════
# MÓDULO 3 — MACRO E REFERÊNCIAS
# ══════════════════════════════════════════════════════════════

def analisar_macro(macro_dict: dict, precos: pd.DataFrame) -> pd.DataFrame:
    hoje_ts = precos.index[-1]
    registros = []

    for grupo, tickers in macro_dict.items():
        for t in tickers:
            if t not in precos.columns:
                continue
            serie = precos[t].dropna()
            if len(serie) < 5:
                continue
            registros.append({
                'Grupo':  grupo,
                'Ativo':  MACRO_NOMES.get(t, t),
                'Último': round(serie.iloc[-1], 2),
                f'Ret YTD/{DATAS["ini_ano_atual"].year} (%)':
                    retorno_fixo(serie, DATAS['ini_ano_atual'], hoje_ts),
                f'Ret H1/{DATAS["ini_ano_ant"].year} (%)':
                    retorno_fixo(serie, DATAS['ini_ano_ant'], DATAS['meio_ano_ant']),
                f'Ret Jan{DATAS["ini_ano_ant"].year}→Hoje (%)':
                    retorno_fixo(serie, DATAS['ini_ano_ant'], hoje_ts),
            })

    return pd.DataFrame(registros).set_index(['Grupo', 'Ativo'])

# ══════════════════════════════════════════════════════════════
# MÓDULO 4 — RESUMO SETORIAL
# ══════════════════════════════════════════════════════════════

def resumo_setorial(df_tecnico: pd.DataFrame, df_fund: pd.DataFrame,
                    setores_dict: dict) -> pd.DataFrame:
    mapa_setor = {t: s for s, lista in setores_dict.items() for t in lista}
    df = df_tecnico.join(df_fund, how='left')
    df['Setor'] = df.index.map(mapa_setor)

    cols_num = [c for c in df.columns
                if c not in ('Setor', 'Preço (R$)', 'Mkt Cap (Bi R$)')]

    resumo = df.groupby('Setor')[cols_num].mean().round(2)

    col_ytd = next((c for c in resumo.columns if 'YTD' in c and 'Vol' not in c), None)
    if col_ytd:
        resumo = resumo.sort_values(col_ytd, ascending=False)

    return resumo

# ══════════════════════════════════════════════════════════════
# ORQUESTRADOR
# ══════════════════════════════════════════════════════════════

def rodar_analise(setores_acoes: dict, macro_dict: dict, log=print):
    todos_acoes = [t for lista in setores_acoes.values() for t in lista]
    todos_macro  = [t for lista in macro_dict.values() for t in lista]

    log("[ 1/4 ] Baixando preços de ações (2 anos)...")
    precos_acoes = baixar_precos(todos_acoes, period='2y')

    log("[ 2/4 ] Baixando preços macro (2 anos)...")
    precos_macro = baixar_precos(todos_macro, period='2y')

    bench_serie = precos_macro[BENCHMARK].dropna() if BENCHMARK in precos_macro.columns else None
    bench_ret   = bench_serie.pct_change().dropna() if bench_serie is not None else pd.Series(dtype=float)

    log("[ 3/4 ] Calculando indicadores técnicos e de risco...")
    df_tecnico = analisar_tecnico_risco(precos_acoes, bench_ret)

    log("[ 4/4 ] Coletando fundamentos...")
    df_fund = analisar_fundamentos(todos_acoes)

    mapa_setor = {t: s for s, lista in setores_acoes.items() for t in lista}

    df_full = df_tecnico.join(df_fund, how='left')
    df_full['Setor'] = df_full.index.map(mapa_setor)
    df_full = df_full.reset_index().rename(columns={'index': 'Ticker'})

    # ── Ordenação numérica pelo prefixo do setor (1, 2 ... 10) ──
    df_full['_ord'] = df_full['Setor'].map(_ordem_setor)
    df_full = df_full.sort_values(['_ord', 'Ticker']).drop(columns='_ord')
    df_full = df_full.set_index(['Setor', 'Ticker'])

    df_setores = resumo_setorial(df_tecnico, df_fund, setores_acoes)
    df_macro   = analisar_macro(macro_dict, precos_macro)

    return {
        'acoes':        df_full,
        'setores':      df_setores,
        'macro':        df_macro,
        'precos_acoes': precos_acoes,
        'precos_macro': precos_macro,
    }

# ══════════════════════════════════════════════════════════════
# EXECUÇÃO CLI (modo terminal — continua funcionando)
# ══════════════════════════════════════════════════════════════

def _print_relatorio():
    resultado   = rodar_analise(SETORES_ACOES, MACRO)
    df_acoes    = resultado['acoes']
    df_setores  = resultado['setores']
    df_macro    = resultado['macro']

    ano_atual = DATAS['ini_ano_atual'].year
    ano_ant   = DATAS['ini_ano_ant'].year
    SEP       = "═" * 140
    hoje_str  = datetime.now().strftime("%d/%m/%Y %H:%M")

    print(f"\n{' RELATÓRIO DE EQUITY — MERCADO BRASILEIRO ':═^140}")
    print(f"{'Gerado em: ' + hoje_str:^140}")
    print(f"\n  Datas de referência:")
    print(f"    YTD         : {DATAS['ini_ano_atual'].strftime('%d/%m/%Y')} → hoje")
    print(f"    H1/{ano_ant}   : {DATAS['ini_ano_ant'].strftime('%d/%m/%Y')} → {DATAS['meio_ano_ant'].strftime('%d/%m/%Y')}")
    print(f"    Jan{ano_ant}→Hoje : {DATAS['ini_ano_ant'].strftime('%d/%m/%Y')} → hoje")

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 220)
    pd.set_option('display.float_format', '{:.2f}'.format)

    print(f"\n{SEP}")
    print(f"{'TABELA 1 · ANÁLISE POR ATIVO':^140}")
    print(SEP)
    print(df_acoes.to_string())

    print(f"\n\n{SEP}")
    print(f"{'TABELA 2 · RESUMO SETORIAL (médias — ordenado por Ret YTD)':^140}")
    print(SEP)
    print(df_setores.to_string())

    print(f"\n\n{SEP}")
    print(f"{'TABELA 3 · MACROECONOMIA & REFERÊNCIAS GLOBAIS':^140}")
    print(SEP)
    print(df_macro.to_string())
    print(f"\n{'═' * 140}\n")


if __name__ == "__main__":
    _print_relatorio()
