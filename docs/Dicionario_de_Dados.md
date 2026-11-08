# Dicionario de Dados - Contrato de Variaveis

**Projeto:** Previsao de Risco de Baixa Produtividade Agricola (Soja)  
**Trilha:** C - Risco de baixa produtividade agricola  
**Equipe:** Grupo 3 (Joao Guilherme Cravo, Jean Carlos Silva de Almeida, Samuel Allan Nunes da Cunha)  
**Ultima atualizacao:** 31/10/2026  
**Versao:** v0.4 (Sprint 5)  

* **Unidade de analise:** 1 ano-safra de soja para o municipio de Sorriso-MT (Codigo IBGE 5107925).
* **N apos o merge (bruto):** 11 safras (2015 a 2025 integradas em `data/raw/integrado.csv`).
* **N apos a limpeza (`data/interim/limpo.csv`):** 10 safras consolidadas (2015 a 2024, safra 2025 descartada por estimativas estaticas nao consolidadas).
* **Split Temporal Congelado:** Treino: safras 2015 a 2022 (8 safras) | Teste: safras 2023 a 2024 (2 safras).
* **Dataset Processado Final (Sprint 4):** `data/processed/dados_modelo.csv` gerado com features selecionadas e validadas sem vazamento temporal.

---

## 1. Fontes de dados

| Fonte | API / Endpoint | Cobertura temporal disponivel | Resolucao temporal | Medido ou modelado? | Limitacoes conhecidas |
|---|---|---|---|---|---|
| **NASA POWER** | https://power.larc.nasa.gov/api/temporal/daily/point | 1981 ate o presente | Diaria | Modelado | Estimativa por sensoriamento remoto e reanalise fisica (resolucao 0.5 grau). Coordenadas centrais de Sorriso-MT (-12.5414, -55.7269). Utiliza codigo -999.0 como sentinela de ausencia de medicao. |
| **IBGE (PAM)** | Agregado 1612 (Lavouras Temporarias, Cultura 2713) | Historico anual | Anual (Safra) | Medido / Declaratorio | Dados municipais oficiais de Sorriso-MT (codigo 5107925) consolidados apos encerramento da colheita. A safra de 2025 ainda nao foi divulgada oficialmente pelo orgao. |

---

## 2. Variaveis brutas (coletadas na Sprint 1)

| Nome da coluna | Fonte | Tipo | Unidade | Descricao | Papel no projeto |
|---|---|---|---|---|---|
| `ano` | IBGE / NASA | Numerica discreta | Ano civil | Ano da safra correspondente | Chave de juncao temporal (merge) |
| `area_plantada_ha` | IBGE PAM (109) | Numerica continua | Hectares (ha) | Area destinada ao cultivo de soja | Excluida das features (anti-vazamento) |
| `area_colhida_ha` | IBGE PAM (216) | Numerica continua | Hectares (ha) | Area efetivamente colhida | Excluida das features (anti-vazamento) |
| `quantidade_produzida_t` | IBGE PAM (214) | Numerica continua | Toneladas (t) | Producao total municipal | Excluida das features (anti-vazamento) |
| `rendimento_kg_ha` | IBGE PAM (112) | Numerica continua | kg/ha | Produtividade media | Variavel geradora do alvo (`quebra_safra`) |
| `T2M` | NASA POWER | Numerica continua | °C | Temperatura media a 2 metros | Usada na Sprint 2 / Descartada na Sprint 4 por redundancia |
| `T2M_MAX` | NASA POWER | Numerica continua | °C | Temperatura maxima diaria | Base para calculo de amplitude termica |
| `T2M_MIN` | NASA POWER | Numerica continua | °C | Temperatura minima diaria | Base para calculo de amplitude termica |
| `PRECTOTCORR` | NASA POWER | Numerica continua | mm/dia | Precipitacao diaria corrigida | Base para acumulados pluviais |
| `RH2M` | NASA POWER | Numerica continua | % | Umidade relativa do ar a 2 metros | Feature climatica agregada |
| `GWETROOT` | NASA POWER | Numerica continua | Fracao (0 a 1) | Umidade do solo na zona radicular | Base para identificacao de deficit hidrico |

---

## 2.1 Log de limpeza e tratamento (Sprint 2, antes da EDA)

* **Sentinelas (-999.0):** Nao identificados nas coordenadas municipais de Sorriso-MT.
* **Valores nulos (NA):** Verificados e confirmados como zero em todas as colunas de 2015 a 2024 (`notebooks/03_tratamento_estatistico_residual.ipynb`).
* **Ano 2025:** Removido do dataset operacional (`data/interim/limpo.csv`) por conter rendimento preliminar identico e estatico.

---

## 3. Variavel-alvo

| Nome da coluna | Formula / Regra | Tipo | Descricao | Racional Tecnico e Agronomico |
|---|---|---|---|---|
| `quebra_safra` | `1 se rendimento_kg_ha < 3400 senao 0` | Binaria (0 ou 1) | Indicador de quebra severa de safra | Calibrado no RFC v0.3 com base na media historica de Sorriso-MT (~3.550 kg/ha). Treino: 3 quebras (2015, 2016, 2021) e 5 safras normais. Teste: 0 quebras (2023, 2024 normais). |

---

## 4. Atributos derivados de Engenharia de Features

### 4.1 Features Criadas na Sprint 4 (Focadas nos Erros da S3 e Janela Critica Jan-Fev)

| Nome da coluna | Formula / Metodo | Tipo | Descricao | Justificativa Agronomica e Erro Atacado | Status na Selecao Final S4 |
|---|---|---|---|---|---|
| `deficit_hidrico_solo` | Contagem de dias em Jan-Fev com `GWETROOT < 0.70` | Numerica discreta (dias) | Dias sob deficit hidrico no solo durante floracao e enchimento de graos | Ataca o Falso Negativo de 2021 (onde choveu no ano mas faltou agua na raiz em Jan-Fev por 42 dias). $r = +0.9027$ com quebra. | **Selecionada (Ativa no Pipeline Congelado)** |
| `dias_pico_calor` | Contagem de dias em Jan-Fev com `T2M_MAX >= 35.0 °C` | Numerica discreta (dias) | Dias com temperatura extrema na floracao | Calor excessivo causa abortamento floral e chochamento de vagens. $r = +0.7354$ com quebra. | **Selecionada (Ativa no Pipeline Congelado)** |
| `precipitacao_enchimento` | Soma de `PRECTOTCORR` em Jan-Fev | Numerica continua (mm) | Volume total precipitado no bimestre de enchimento | Captura a escassez real intra-safra ($r = -0.5545$). Em 2015 choveu apenas 159 mm no periodo. | **Selecionada (Ativa no Pipeline Congelado)** |
| `veranico_max_dias` | Max dias consecutivos com chuva $< 1.0$ mm em Jan-Fev | Numerica discreta (dias) | Maior periodo seco continuo na janela reprodutiva | Mede estresse continuado. $r = +0.53$. | Descartada no corte parcimonioso (redundante com deficit hidrico) |

### 4.2 Features Herdadas da Sprint 2

| Nome da coluna | Formula / Metodo | Tipo | Descricao | Justificativa e Risco Documentado | Status na Selecao Final S4 |
|---|---|---|---|---|---|
| `amplitude_termica` | `T2M_MAX - T2M_MIN` anual | Numerica continua (°C) | Diferenca entre temperatura maxima e minima anual | Oscilacao termica do ciclo. $r = -0.42$. **Ressalva de Vazamento:** $T_{min}$ ocorre em Julho e $T_{max}$ em Setembro/Outubro (fora da janela Jan-Fev). Mantida por parcimonia, com sensibilidade testada. | **Selecionada (Ativa no Pipeline Congelado)** |
| `precipitacao_por_temperatura` | `PRECTOTCORR / (T2M + 0.001)` | Numerica continua (mm/°C) | Balanco hidrico anual aproximado | Redundante com `precipitacao_enchimento` e colinear a acumulados. | Descartada por parcimonia ($N=8$) |
| `GWET_x_PREC` | `GWETROOT * PRECTOTCORR` | Numerica continua | Interacao umidade e chuva anual | Multicolinearidade severa com `PRECTOTCORR` anual ($r = 0.996$). Mascarou estresse de 2021. | Descartada por colinearidade |

---

## 5. Variaveis excluidas das features (Prevencao de Vazamento de Dados)

| Nome da coluna | Motivo de Exclusao das Features Preditoras |
|---|---|
| `rendimento_kg_ha` | Variavel geradora do alvo preditivo. Mantê-la como preditora causaria vazamento direto da resposta. |
| `quantidade_produzida_t` | Dado apurado pelo IBGE somente apos a pesagem e consolidacao do termino da safra. |
| `area_colhida_ha` | Informacao decorrente do processo de colheita, indisponivel durante o ciclo vegetativo. |
| `area_plantada_ha` | Variavel declaratoria anual do IBGE, excluida para evitar interferencia pos-evento. |

---

## 6. Observacoes gerais e limitacoes

* **Tamanho amostral reduzido no treino ($N_{train} = 8$):** A granularidade anual do IBGE impoe restricao severa de graus de liberdade. O pipeline final congela rigorosamente 4 variaveis (`deficit_hidrico_solo`, `dias_pico_calor`, `precipitacao_enchimento`, `amplitude_termica`) padronizadas via `StandardScaler`, com `fit` exclusivo no bloco de treino (2015–2022).
* **Ausencia de eventos de quebra no teste ($N_{test} = 2$):** As safras de 2023 e 2024 apresentaram produtividades plenas (> 3.400 kg/ha). O teste oficial afere especificidade (taxa de falso positivo = 0), mas o lift da classe positiva (`quebra_safra=1`) so pode ser diagnosticado via backtest temporal no treino.
* **Janela temporal anti-vazamento:** As novas features climáticas da Sprint 4 fecham estritamente no ultimo dia de fevereiro, com antecedencia minima de 30 a 60 dias da colheita oficial.

---

## 7. Historico de alteracoes

| Versao | Sprint | Data | Modificacoes |
|---|---|---|---|
| v0.1 | Sprint 1 | 21/09/2026 | Levantamento inicial de variaveis brutas, correcao de filtro de variaveis, integracao em data/raw/integrado.csv, estabelecimento do limiar numerico formal e definicao de colunas excluidas por vazamento. |
| v0.2 | Sprint 2 | 05/10/2026 | Re-arquitetura do dicionario de dados para Sorriso-MT 100% (Codigo IBGE 5107925), recalibracao formal do limiar para < 3.400 kg/ha, adicao dos atributos derivados de engenharia de features e formalizacao do split temporal. |
| v0.3 | Sprint 4 | 31/10/2026 | Inclusao das features da janela critica Jan-Fev (`deficit_hidrico_solo`, `dias_pico_calor`, `precipitacao_enchimento`, `veranico_max_dias`), descarte justificado de atributos anuais colineares, congelamento do contrato de 4 features para a Sprint 5 e documentacao do risco de vazamento em `amplitude_termica`. |
| v0.4 | Sprint 5 | 08/11/2026 | Selecao e congelamento do modelo campeao (Logistic Regression L2 com class_weight balanced), calibracao do limiar otimo de decisao (p = 0.35) balizado pelo custo de FN do RFC, geracao do Model Card e persistencia do banco SQLite (data/monitoramento_safra.db). |
