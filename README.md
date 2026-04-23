# AI-salesman · Monitor de Equity

Dashboard para acompanhar em tempo real ações brasileiras, resumo setorial e indicadores macro (índices globais, câmbio, commodities e cripto), com análise técnica, de risco e fundamentalista.

## Estrutura

- `analysis.py` — módulo de análise (download, técnico/risco, fundamentos, macro, resumo setorial). Pode ser executado direto no terminal.
- `app.py` — dashboard Streamlit que consome `analysis.py`.
- `requirements.txt` — dependências.

## Instalação

```bash
pip install -r requirements.txt
```

## Uso

### Modo dashboard (interface gráfica)

```bash
streamlit run app.py
```

Abre no navegador em `http://localhost:8501`. Tem:

- Cards macro no topo (Ibov, USD/BRL, S&P, Nasdaq, Petróleo, Ouro, BTC)
- Filtro por setor na sidebar
- Botão de atualização manual + auto-refresh opcional (1–30 min)
- Abas: **Ativos** (tabela colorida, ordenável) • **Setores** (ranking) • **Macro** • **Gráficos** (histórico com MM50)

### Modo terminal (relatório em texto)

```bash
python analysis.py
```

## Configuração

Edite os dicionários `SETORES_ACOES` e `MACRO` no topo de `analysis.py` para adicionar/remover ativos.

Dados: Yahoo Finance via [`yfinance`](https://pypi.org/project/yfinance/). Cache do dashboard: 5 min.
