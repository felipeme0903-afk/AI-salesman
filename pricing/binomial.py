"""Arvore Binomial (Cox-Ross-Rubinstein) para opcoes europeias e americanas."""
from __future__ import annotations

import numpy as np


def binomial_price(
    S: float,
    K: float,
    T: float,
    r: float,
    sigma: float,
    n_steps: int = 200,
    option_type: str = "call",
    exercise: str = "european",
) -> float:
    """Precifica opcao por Arvore Binomial CRR.

    Parametros
    ----------
    exercise : 'european' ou 'american'.
    """
    if n_steps < 1:
        raise ValueError("n_steps deve ser >= 1.")
    if option_type not in ("call", "put"):
        raise ValueError("option_type deve ser 'call' ou 'put'.")
    if exercise not in ("european", "american"):
        raise ValueError("exercise deve ser 'european' ou 'american'.")

    dt = T / n_steps
    u = np.exp(sigma * np.sqrt(dt))
    d = 1.0 / u
    disc = np.exp(-r * dt)
    p = (np.exp(r * dt) - d) / (u - d)

    if not (0 < p < 1):
        # parametros incoerentes; ainda assim seguimos com p limitado
        p = float(np.clip(p, 1e-12, 1 - 1e-12))

    # precos no vencimento
    j = np.arange(n_steps + 1)
    ST = S * (u ** (n_steps - j)) * (d ** j)

    if option_type == "call":
        values = np.maximum(ST - K, 0.0)
    else:
        values = np.maximum(K - ST, 0.0)

    # retropropagacao
    for step in range(n_steps - 1, -1, -1):
        j = np.arange(step + 1)
        S_step = S * (u ** (step - j)) * (d ** j)
        cont = disc * (p * values[:-1] + (1 - p) * values[1:])
        if exercise == "american":
            if option_type == "call":
                exercise_val = np.maximum(S_step - K, 0.0)
            else:
                exercise_val = np.maximum(K - S_step, 0.0)
            values = np.maximum(cont, exercise_val)
        else:
            values = cont

    return float(values[0])
