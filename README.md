# Calculadora de Opcoes

Aplicativo Streamlit para precificacao de opcoes (europeias, americanas e
asiaticas) por Black-Scholes, Monte Carlo e Arvore Binomial, com calculo de
volatilidade implicita (Newton-Raphson e Bissecao) e integracao com o
Yahoo Finance via `yfinance`.

## Como executar

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Estrutura

- `app.py` - aplicativo Streamlit (UI completa)
- `pricing/` - modelos de precificacao
  - `black_scholes.py` - Black-Scholes (preco e gregas)
  - `monte_carlo.py` - Monte Carlo (europeia e asiatica)
  - `binomial.py` - Arvore Binomial CRR (europeia e americana)
  - `implied_vol.py` - Volatilidade implicita (Newton-Raphson e Bissecao)
- `utils/data.py` - integracao com Yahoo Finance e volatilidade historica