"""Simulacao de Monte Carlo para precificacao de opcoes."""
from __future__ import annotations

import numpy as np


def simulate_paths(
    S0: float,
    r: float,
    sigma: float,
    T: float,
    n_steps: int = 252,
    n_sims: int = 10000,
    seed: int | None = None,
    antithetic: bool = True,
) -> np.ndarray:
    """Simula trajetorias do preco do ativo via MGB.

    Retorna matriz (n_sims, n_steps + 1) com S0 na primeira coluna.
    """
    rng = np.random.default_rng(seed)
    dt = T / n_steps

    if antithetic:
        half = n_sims // 2
        Z_half = rng.standard_normal(size=(half, n_steps))
        Z = np.concatenate([Z_half, -Z_half], axis=0)
        if Z.shape[0] < n_sims:
            extra = rng.standard_normal(size=(n_sims - Z.shape[0], n_steps))
            Z = np.concatenate([Z, extra], axis=0)
    else:
        Z = rng.standard_normal(size=(n_sims, n_steps))

    drift = (r - 0.5 * sigma ** 2) * dt
    diffusion = sigma * np.sqrt(dt) * Z
    log_returns = drift + diffusion

    log_paths = np.cumsum(log_returns, axis=1)
    paths = S0 * np.exp(log_paths)
    paths = np.concatenate([np.full((n_sims, 1), S0), paths], axis=1)
    return paths


def monte_carlo_european(
    S0: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
    n_sims: int = 10000,
    seed: int | None = None,
    antithetic: bool = True,
) -> dict:
    """Preco de opcao europeia por Monte Carlo (apenas preco terminal)."""
    rng = np.random.default_rng(seed)
    if antithetic:
        half = n_sims // 2
        Z_half = rng.standard_normal(size=half)
        Z = np.concatenate([Z_half, -Z_half])
        if Z.size < n_sims:
            Z = np.concatenate([Z, rng.standard_normal(size=n_sims - Z.size)])
    else:
        Z = rng.standard_normal(size=n_sims)

    ST = S0 * np.exp((r - 0.5 * sigma ** 2) * T + sigma * np.sqrt(T) * Z)

    if option_type == "call":
        payoffs = np.maximum(ST - K, 0.0)
    elif option_type == "put":
        payoffs = np.maximum(K - ST, 0.0)
    else:
        raise ValueError("option_type deve ser 'call' ou 'put'.")

    disc = np.exp(-r * T)
    price = disc * payoffs.mean()
    se = disc * payoffs.std(ddof=1) / np.sqrt(n_sims)

    return {
        "price": float(price),
        "std_error": float(se),
        "ci_low": float(price - 1.96 * se),
        "ci_high": float(price + 1.96 * se),
        "terminal_prices": ST,
    }


def monte_carlo_asian(
    S0: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    option_type: str = "call",
    n_sims: int = 10000,
    n_steps: int = 252,
    seed: int | None = None,
    antithetic: bool = True,
    average_type: str = "arithmetic",
) -> dict:
    """Preco de opcao asiatica por Monte Carlo (media aritmetica ou geometrica)."""
    paths = simulate_paths(
        S0=S0, r=r, sigma=sigma, T=T,
        n_steps=n_steps, n_sims=n_sims,
        seed=seed, antithetic=antithetic,
    )
    # Media ao longo dos passos (sem incluir S0, conforme convencao usual).
    path_slice = paths[:, 1:]

    if average_type == "arithmetic":
        averages = path_slice.mean(axis=1)
    elif average_type == "geometric":
        averages = np.exp(np.log(path_slice).mean(axis=1))
    else:
        raise ValueError("average_type deve ser 'arithmetic' ou 'geometric'.")

    if option_type == "call":
        payoffs = np.maximum(averages - K, 0.0)
    elif option_type == "put":
        payoffs = np.maximum(K - averages, 0.0)
    else:
        raise ValueError("option_type deve ser 'call' ou 'put'.")

    disc = np.exp(-r * T)
    price = disc * payoffs.mean()
    se = disc * payoffs.std(ddof=1) / np.sqrt(n_sims)

    return {
        "price": float(price),
        "std_error": float(se),
        "ci_low": float(price - 1.96 * se),
        "ci_high": float(price + 1.96 * se),
        "paths": paths,
        "averages": averages,
    }
