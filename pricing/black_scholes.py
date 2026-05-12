"""Modelo de Black-Scholes para opcoes europeias."""
from __future__ import annotations

import numpy as np
from scipy.stats import norm


def _d1_d2(S: float, K: float, T: float, r: float, sigma: float):
    if T <= 0 or sigma <= 0:
        raise ValueError("T e sigma devem ser positivos.")
    sqrt_T = np.sqrt(T)
    d1 = (np.log(S / K) + (r + 0.5 * sigma ** 2) * T) / (sigma * sqrt_T)
    d2 = d1 - sigma * sqrt_T
    return d1, d2


def black_scholes_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
) -> float:
    """Calcula o preco de uma opcao europeia via Black-Scholes."""
    if T <= 0:
        intrinsic = max(S - K, 0.0) if option_type == "call" else max(K - S, 0.0)
        return float(intrinsic)
    if sigma <= 0:
        disc = np.exp(-r * T)
        if option_type == "call":
            return float(max(S - K * disc, 0.0))
        return float(max(K * disc - S, 0.0))

    d1, d2 = _d1_d2(S, K, T, r, sigma)
    disc = np.exp(-r * T)
    if option_type == "call":
        price = S * norm.cdf(d1) - K * disc * norm.cdf(d2)
    elif option_type == "put":
        price = K * disc * norm.cdf(-d2) - S * norm.cdf(-d1)
    else:
        raise ValueError("option_type deve ser 'call' ou 'put'.")
    return float(price)


def vega(S: float, K: float, T: float, r: float, sigma: float) -> float:
    """Vega no modelo de Black-Scholes (mesma formula para call e put)."""
    if T <= 0 or sigma <= 0:
        return 0.0
    d1, _ = _d1_d2(S, K, T, r, sigma)
    return float(S * np.sqrt(T) * norm.pdf(d1))


def black_scholes_greeks(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
) -> dict:
    """Retorna delta, gamma, vega, theta e rho."""
    if T <= 0 or sigma <= 0:
        return {"delta": 0.0, "gamma": 0.0, "vega": 0.0, "theta": 0.0, "rho": 0.0}

    d1, d2 = _d1_d2(S, K, T, r, sigma)
    disc = np.exp(-r * T)
    pdf_d1 = norm.pdf(d1)

    gamma = pdf_d1 / (S * sigma * np.sqrt(T))
    v = S * np.sqrt(T) * pdf_d1

    if option_type == "call":
        delta = norm.cdf(d1)
        theta = (-S * pdf_d1 * sigma / (2 * np.sqrt(T))
                 - r * K * disc * norm.cdf(d2))
        rho = K * T * disc * norm.cdf(d2)
    elif option_type == "put":
        delta = norm.cdf(d1) - 1.0
        theta = (-S * pdf_d1 * sigma / (2 * np.sqrt(T))
                 + r * K * disc * norm.cdf(-d2))
        rho = -K * T * disc * norm.cdf(-d2)
    else:
        raise ValueError("option_type deve ser 'call' ou 'put'.")

    return {
        "delta": float(delta),
        "gamma": float(gamma),
        "vega": float(v),
        "theta": float(theta),
        "rho": float(rho),
    }
