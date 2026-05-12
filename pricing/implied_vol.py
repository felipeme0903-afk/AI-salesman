"""Calculo de volatilidade implicita via Newton-Raphson e Bissecao."""
from __future__ import annotations

import numpy as np

from .black_scholes import black_scholes_price, vega


def _intrinsic_bounds(S: float, K: float, T: float, r: float, option_type: str):
    """Limites teoricos do preco de uma opcao europeia."""
    disc = np.exp(-r * T)
    if option_type == "call":
        lower = max(S - K * disc, 0.0)
        upper = S
    else:
        lower = max(K * disc - S, 0.0)
        upper = K * disc
    return lower, upper


def implied_vol_newton(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "call",
    sigma_init: float = 0.2,
    tol: float = 1e-6,
    max_iter: int = 100,
) -> dict:
    """Volatilidade implicita por Newton-Raphson."""
    lower, upper = _intrinsic_bounds(S, K, T, r, option_type)
    if market_price < lower - 1e-8 or market_price > upper + 1e-8:
        return {
            "sigma": float("nan"),
            "iterations": 0,
            "converged": False,
            "error": "Preco de mercado fora dos limites teoricos.",
        }

    sigma = max(sigma_init, 1e-4)
    for i in range(1, max_iter + 1):
        price = black_scholes_price(S, K, T, r, sigma, option_type)
        diff = price - market_price
        if abs(diff) < tol:
            return {
                "sigma": float(sigma),
                "iterations": i,
                "converged": True,
                "error": None,
            }
        v = vega(S, K, T, r, sigma)
        if v < 1e-10:
            break
        sigma -= diff / v
        if sigma <= 0:
            sigma = 1e-4

    return {
        "sigma": float(sigma),
        "iterations": max_iter,
        "converged": False,
        "error": "Nao convergiu (tente Bissecao).",
    }


def implied_vol_bisection(
    market_price: float,
    S: float,
    K: float,
    T: float,
    r: float,
    option_type: str = "call",
    sigma_low: float = 1e-4,
    sigma_high: float = 5.0,
    tol: float = 1e-6,
    max_iter: int = 200,
) -> dict:
    """Volatilidade implicita pelo metodo da Bissecao."""
    lower, upper = _intrinsic_bounds(S, K, T, r, option_type)
    if market_price < lower - 1e-8 or market_price > upper + 1e-8:
        return {
            "sigma": float("nan"),
            "iterations": 0,
            "converged": False,
            "error": "Preco de mercado fora dos limites teoricos.",
        }

    f_low = black_scholes_price(S, K, T, r, sigma_low, option_type) - market_price
    f_high = black_scholes_price(S, K, T, r, sigma_high, option_type) - market_price

    if f_low * f_high > 0:
        return {
            "sigma": float("nan"),
            "iterations": 0,
            "converged": False,
            "error": "Sem mudanca de sinal no intervalo inicial.",
        }

    a, b = sigma_low, sigma_high
    for i in range(1, max_iter + 1):
        mid = 0.5 * (a + b)
        f_mid = black_scholes_price(S, K, T, r, mid, option_type) - market_price
        if abs(f_mid) < tol or (b - a) / 2 < tol:
            return {
                "sigma": float(mid),
                "iterations": i,
                "converged": True,
                "error": None,
            }
        if f_low * f_mid < 0:
            b = mid
            f_high = f_mid
        else:
            a = mid
            f_low = f_mid

    return {
        "sigma": float(0.5 * (a + b)),
        "iterations": max_iter,
        "converged": False,
        "error": "Nao convergiu dentro do max_iter.",
    }
