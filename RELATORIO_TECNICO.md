# Relatório Técnico — Calculadora de Opções

**Curso:** Gestão de Riscos e Derivativos
**Data de entrega:** 12.05.2026
**Repositório:** https://github.com/felipeme0903-afk/AI-salesman

---

## 1. Objetivo

Este trabalho apresenta o desenvolvimento de uma **calculadora de opções financeiras** em formato de aplicativo web, construída em Python com o framework Streamlit. A calculadora precifica opções europeias, americanas e asiáticas por três métodos quantitativos (Black-Scholes, Monte Carlo e Árvore Binomial), calcula a volatilidade implícita a partir do preço de mercado (Newton-Raphson e Bisseção) e integra-se ao Yahoo Finance para obtenção de dados reais.

---

## 2. Arquitetura da Solução

O código foi organizado em módulos com responsabilidades bem separadas, facilitando teste e manutenção:

```
AI-salesman/
├── app.py                    # Interface Streamlit (6 abas)
├── requirements.txt          # Dependências
├── pricing/
│   ├── black_scholes.py      # Fórmula fechada + Gregas
│   ├── monte_carlo.py        # Simulação MGB (europeia + asiática)
│   ├── binomial.py           # Árvore CRR (europeia + americana)
│   └── implied_vol.py        # Vol. implícita (Newton-Raphson + Bisseção)
└── utils/
    └── data.py               # Yahoo Finance + volatilidade histórica
```

**Bibliotecas utilizadas:**

| Biblioteca | Uso |
|---|---|
| `numpy` | Vetorização de simulações e álgebra |
| `scipy.stats` | Função de distribuição normal (N(·), φ(·)) |
| `pandas` | Manipulação de séries históricas |
| `yfinance` | Coleta de preços do Yahoo Finance |
| `streamlit` | Interface web interativa |
| `plotly` | Gráficos interativos (payoff, trajetórias, distribuições) |

---

## 3. Modelos Implementados

### 3.1 Black-Scholes (`pricing/black_scholes.py`)

Preço de opção europeia:

- **Call:** C = S₀·N(d₁) − K·e⁻ʳᵀ·N(d₂)
- **Put:** P = K·e⁻ʳᵀ·N(−d₂) − S₀·N(−d₁)

com d₁ = [ln(S₀/K) + (r + σ²/2)T] / (σ√T) e d₂ = d₁ − σ√T.

Também são calculadas as **Gregas** (Delta, Gamma, Vega, Theta, Rho) para análise de sensibilidade:

- Vega = S₀·√T·φ(d₁) (usado no cálculo de volatilidade implícita)
- Gamma = φ(d₁) / (S₀·σ·√T)
- Theta e Rho conforme fórmulas clássicas

**Casos de borda tratados:** T ≤ 0 devolve o valor intrínseco; σ = 0 devolve o preço forward descontado.

### 3.2 Simulação de Monte Carlo (`pricing/monte_carlo.py`)

Modelo estocástico: **Movimento Geométrico Browniano** discretizado.

Sₜ₊Δₜ = Sₜ · exp[(r − σ²/2)Δt + σ√Δt · Z]

**Otimizações aplicadas:**
- **Antithetic variates** (variáveis antitéticas): reduzem variância ao parear cada choque Z com −Z
- Vetorização total via NumPy (sem loops Python nas trajetórias)
- Seed configurável para reprodutibilidade

**Estatísticas retornadas:**
- Preço estimado V̂₀ = e⁻ʳᵀ · média(payoffs)
- Erro padrão SE = e⁻ʳᵀ · σ(payoffs) / √M
- Intervalo de confiança 95%: V̂₀ ± 1.96·SE

**Para opções asiáticas** implementamos média aritmética (padrão do enunciado) e geométrica.

### 3.3 Árvore Binomial (`pricing/binomial.py`)

Modelo **Cox-Ross-Rubinstein (CRR)**:

- u = e^(σ√Δt), d = 1/u
- Probabilidade neutra ao risco: p = (e^(rΔt) − d) / (u − d)
- Valor por retropropagação: V = e⁻ʳΔᵗ · [p·Vᵤ + (1−p)·V_d]

**Para opções americanas** compara-se em cada nó o valor de continuidade com o valor de exercício imediato:

V = max(V_cont, V_exerc)

com V_exerc = max(S − K, 0) para call e max(K − S, 0) para put. Isso captura corretamente o **prêmio de exercício antecipado**, essencial em puts americanas.

**Implementação vetorizada:** cada passo da retropropagação usa slicing NumPy — a árvore de 500 passos roda em milissegundos.

### 3.4 Volatilidade Implícita (`pricing/implied_vol.py`)

Resolve numericamente f(σ) = C_BS(σ) − C_mercado = 0.

**Método de Newton-Raphson:**

σₙ₊₁ = σₙ − [C_BS(σₙ) − C_mercado] / Vega(σₙ)

- Rápido (tipicamente < 5 iterações para tol = 10⁻⁶)
- Pode falhar quando Vega ≈ 0 (opções muito ITM ou OTM, ou próximas do vencimento)
- Salvaguardas: limita σ > 0 e detecta divergência

**Método da Bisseção:**

Intervalo inicial [σ_min, σ_max] = [10⁻⁴, 5.0]; a cada iteração o intervalo é dividido pela metade. Sempre converge quando há mudança de sinal, ao custo de maior número de iterações (~20-30).

**Validação prévia:** ambos os métodos verificam se o preço de mercado está dentro dos **limites teóricos de arbitragem** antes de iterar:
- Call: max(S − K·e⁻ʳᵀ, 0) ≤ C ≤ S
- Put: max(K·e⁻ʳᵀ − S, 0) ≤ P ≤ K·e⁻ʳᵀ

---

## 4. Integração com Yahoo Finance

O módulo `utils/data.py` usa `yfinance` para baixar histórico de preços e calcular a volatilidade histórica:

r_t = ln(S_t / S_{t-1})
σ_anual = std(r_t) · √252

Tickers testados: PETR4.SA, VALE3.SA, ITUB4.SA, AAPL, MSFT, TSLA, ^BVSP, USDBRL=X.

---

## 5. Interface do Aplicativo

O app Streamlit está organizado em **6 abas**:

| Aba | Funcionalidade |
|---|---|
| **Preço** | Cálculo do preço pelo método escolhido + Gregas (BS) + comparação americana vs europeia |
| **Volatilidade Implícita** | Newton-Raphson e Bisseção, comparação lado a lado, smile ilustrativo |
| **Payoff** | Diagrama de payoff no vencimento + curva de P&L descontando o prêmio |
| **Monte Carlo** | Trajetórias simuladas + histograma do preço terminal |
| **Comparação** | Tabela consolidada com todos os métodos + sensibilidade preço × volatilidade |
| **Histórico** | Preços do Yahoo Finance + distribuição dos log-retornos + vol. histórica |

Todos os parâmetros são ajustáveis pela sidebar; o app recalcula reativamente.

---

## 6. Validação com os Exemplos do Enunciado

### Exemplo 1 — Call Europeia sobre PETR4
**Parâmetros:** S₀ = 38, K = 40, T = 0,5 ano, r = 10% a.a., σ = 30% a.a.

| Método | Preço |
|---|---|
| Black-Scholes | **3,1874** |
| Monte Carlo (50.000 sim.) | **3,1891** — IC 95% [3,1422; 3,2359] |
| Árvore Binomial (500 passos) | **3,1883** |

Os três métodos convergem para o mesmo preço — a diferença é inferior a 0,05%. Isso valida a implementação: em opções europeias sob as hipóteses de Black-Scholes, os três métodos precisam concordar.

### Exemplo 2 — Put Americana
**Parâmetros:** S₀ = 50, K = 55, T = 1 ano, r = 8% a.a., σ = 25% a.a.

| Método | Preço |
|---|---|
| Binomial (europeia — referência) | **5,4080** |
| Binomial (americana) | **6,3623** |
| **Prêmio de exercício antecipado** | **0,9543** |

O prêmio positivo (~17,6% acima da europeia) confirma o comportamento teórico esperado: para uma put americana ITM (S < K), o direito de exercer antes do vencimento tem valor econômico — o titular pode receber K − S imediatamente e reinvestir à taxa r. Esse efeito não existe em calls americanas sobre ativos sem dividendos, para as quais o preço iguala o da europeia.

### Exemplo 3 — Call Asiática
**Parâmetros:** S₀ = 38, K = 40, T = 0,5 ano, r = 10% a.a., σ = 30% a.a.

**Preço por Monte Carlo:** **1,4107** — IC 95% [1,3879; 1,4335]

Como esperado, a call asiática vale **menos** que a europeia equivalente (1,41 vs 3,19). Isso decorre da menor volatilidade da **média** dos preços em relação ao preço terminal — a média suaviza movimentos extremos, reduzindo o valor de opcionalidade. É exatamente por essa razão que opções asiáticas são atrativas em mercados de commodities: protegem contra manipulação de preço em uma única data.

### Volatilidade Implícita (verificação)
Alimentando o preço BS de 3,1874 (σ verdadeiro = 30%) de volta no solver:

| Método | σ recuperado | Iterações |
|---|---|---|
| Newton-Raphson | 30,0000% | 3 |
| Bisseção | 30,0000% | 23 |

Ambos recuperam o σ original com precisão de 10⁻⁶. Newton é ~7× mais rápido em número de iterações, mas Bisseção sempre converge — trade-off didático clássico.

---

## 7. Discussão das Perguntas do Enunciado

**1. Por que Black-Scholes é mais adequado para europeias?**
A dedução assume exercício apenas no vencimento (uma única variável aleatória Sₜ). Para americanas, seria preciso resolver um problema de parada ótima em cada instante, o que a fórmula fechada não faz.

**2. Por que americanas exigem análise de exercício antecipado?**
O titular tem o direito de exercer a qualquer momento. O preço correto é max(V_cont, V_exerc) em cada nó — ignorar isso subestima o preço quando há valor no exercício imediato (típico de puts ITM).

**3. Quando Monte Carlo é mais adequado?**
Para payoffs path-dependent (asiáticas, barreiras, lookback), múltiplos ativos (baskets), ou modelos onde não há fórmula fechada. É a única técnica genuinamente flexível.

**4. Por que opções asiáticas são úteis em commodities?**
Reduzem risco de manipulação e volatilidade pontual em uma única data de fixação. Também alinham o hedge com fluxo de caixa: exportadoras que recebem em várias parcelas preferem proteger a média do câmbio.

**5. Volatilidade implícita elevada significa o quê?**
Expectativa de mercado de grandes movimentos futuros — pode refletir eventos programados (resultados, decisões de juros), aumento de aversão a risco ou stress de liquidez.

**6. Vol histórica × implícita — diferença?**
Histórica olha para o passado (dados realizados); implícita olha para frente (extraída do preço da opção). O spread entre elas é usado por mesas para identificar volatilidade cara ou barata.

**7. Quando Newton-Raphson pode falhar?**
Quando Vega é próximo de zero (opções muito ITM/OTM ou próximas do vencimento), chute inicial ruim, ou preço de mercado fora dos limites teóricos.

**8. Por que Bisseção é mais robusta?**
Só exige mudança de sinal no intervalo; não depende da derivada. Converge sempre, mas linearmente (mais lento).

**9. Como aumento de volatilidade afeta calls e puts?**
Ambos ficam mais caros (Vega > 0). Maior σ aumenta a probabilidade de payoffs extremos favoráveis, e a assimetria do payoff faz o comprador se beneficiar sem risco simétrico.

**10. Uso em mesa de trading?**
Precificação para market-making, hedge dinâmico via Delta/Gamma, marcação a mercado, identificação de mispricings, construção de superfície de volatilidade para calibração de modelos mais avançados.

---

## 8. Limitações e Possíveis Extensões

**Limitações atuais:**
- Modelo assume dividendos = 0
- Volatilidade constante — não incorpora Heston, SABR ou modelos de saltos
- Smile de volatilidade na aba de VI é ilustrativo — para um smile real seria preciso ingerir preços de mercado por strike

**Extensões naturais:**
- Suporte a dividendos (contínuo q ou discretos)
- Least-Squares Monte Carlo (Longstaff-Schwartz) para americanas
- Redução de variância adicional (control variates com opção geométrica asiática)
- Ingestão de cadeia de opções real via `yf.Ticker.option_chain()` para construir superfície de vol

---

## 9. Conclusão

O aplicativo integra teoria de derivativos, matemática financeira, programação e simulação estocástica em uma ferramenta funcional. Os três exemplos do enunciado foram implementados e validados; os métodos apresentam concordância numérica esperada nos casos europeus e capturam corretamente o prêmio de exercício antecipado no caso americano. A ferramenta simula um pequeno "pricer" de mesa de derivativos e pode ser estendida para casos de mercado real com esforço incremental.
