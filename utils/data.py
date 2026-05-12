"""Utilitarios para coleta de dados do Yahoo Finance."""
from __future__ import annotations

import numpy as np
import pandas as pd


def fetch_history(ticker: str, period: str = "1y", interval: str = "1d") -> pd.DataFrame:
    """Baixa historico de precos do Yahoo Finance via yfinance."""
    import yfinance as yf

    df = yf.download(
        ticker,
        period=period,
        interval=interval,
        auto_adjust=True,
        progress=False,
    )
    if df is None or df.empty:
        raise ValueError(f"Sem dados retornados para o ticker '{ticker}'.")

    # Trata colunas multiindex (caso o yfinance devolva nesse formato).
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    df = df.dropna()
    return df


def get_spot_price(history: pd.DataFrame) -> float:
    """Retorna o ultimo preco de fechamento."""
    if "Close" not in history.columns:
        raise ValueError("DataFrame nao contem coluna 'Close'.")
    return float(history["Close"].iloc[-1])


def historical_volatility(
    history: pd.DataFrame,
    window: int | None = None,
    annualization: int = 252,
) -> float:
    """Volatilidade historica anualizada com retornos logaritmicos."""
    if "Close" not in history.columns:
        raise ValueError("DataFrame nao contem coluna 'Close'.")

    closes = history["Close"].astype(float)
    log_returns = np.log(closes / closes.shift(1)).dropna()
    if window is not None and window > 0:
        log_returns = log_returns.tail(window)

    if len(log_returns) < 2:
        raise ValueError("Dados insuficientes para calcular volatilidade.")

    return float(log_returns.std(ddof=1) * np.sqrt(annualization))
