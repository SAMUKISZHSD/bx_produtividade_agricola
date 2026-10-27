# Dicionario de Dados - Contrato de Variaveis

**Projeto:** Previsao de Risco de Baixa Produtividade Agricola (Soja)  
**Trilha:** C - Risco de baixa produtividade agricola  
**Equipe:** Grupo 3 (Joao Guilherme Cravo, Jean Carlos Silva de Almeida, Samuel Allan Nunes da Cunha)  
**Ultima atualizacao:** 11/10/2026  
**Versao:** v0.3 (Sprint 4)  

* **Unidade de analise:** 1 ano-safra de soja para o municipio de Sorriso-MT.
* **N apos o merge (bruto):** 11 safras (2015 a 2025 integradas em data/raw/integrado.csv).
* **N apos a limpeza (data/interim/limpo.csv):** 10 safras consolidadas (2015 a 2024, safra 2025 descartada por estimativas estaticas nao consolidadas).
* **Split Temporal:** Treino: safras 2015 a 2022 (8 safras) | Teste: safras 2023 a 2024 (2 safras).

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
| `area_colhida_ha` | IBGE PAM (216) | Numerica continua | Hectares (ha) | Area que foi efetivamente colhida | Excluida das features (anti-vazamento) |
| `quantidade_produzida_t` | IBGE PAM (214) | Numerica continua | Toneladas (t) | Volume colhido total | Excluida das features (anti-vazamento) |
| `rendimento_kg_ha` | IBGE PAM (112) | Numerica continua | kg/hectare | Produtividade media obtida no ciclo | Variavel-alvo: rotulagem da quebra |
| `PRECTOTCORR` | NASA POWER | Numerica continua | mm/dia | Precipitacao pluviometrica diaria | Feature preditora: balanco hidrico |
| `T2M` | NASA POWER | Numerica continua | graus C | Temperatura media diaria do ar | Feature preditora: acumulo termico |
| `T2M_MAX` | NASA POWER | Numerica continua | graus C | Temperatura maxima diaria | Feature preditora: estresse termico |
| `T2M_MIN` | NASA POWER | Numerica continua | graus C | Temperatura minima diaria | Feature preditora: frio limitante |
| `RH2M` | NASA POWER | Numerica continua | percentual | Umidade relativa do ar a 2 metros | Feature preditora: deficit de vapor |
| `GWETROOT` | NASA POWER | Numerica continua | 0 a 1 | Umidade do solo na zona das raizes | Feature preditora: seca no solo |

---

## 2.1 Log de limpeza e tratamento (Sprint 2, antes da EDA)

data/raw/ permanece preservado. O arquivo de integracao inicial e data/raw/integrado.csv.

| Problema identificado | Regra aplicada | Celulas afetadas | N depois | Observacoes |
|---|---|---|---|---|
| Sentinela -999.0 da NASA POWER | Substituido por valor nulo (pd.NA) antes da agregacao | Registros pontuais | 10 safras | Conforme especificacao tecnica da API |
| Safra 2025 do IBGE nao consolidada | Filtragem por ano <= 2024 em data/interim/limpo.csv | 1 ano (2025) | 10 safras | Retencao do intervalo completo consolidado 2015 a 2024 |

---

## 3. Variavel-alvo

| Campo | Descricao |
|---|---|
| **Nome da coluna** | quebra_safra |
| **Definicao da classe positiva** | 1 = Quebra de safra (baixa produtividade crítica). 0 = Safra normal ou superior. |
| **Limiar adotado e justificativa** | Rendimento estritamente inferior a 3.400 kg/ha. A media historica observada entre 2015 e 2024 em Sorriso-MT e de aproximadamente 3.477 kg/ha (desvio padrao ~293 kg/ha). O limiar segrega como quebra (classe positiva = 1) safras com perdas decorrentes de estresses agroclimaticos (2015 com 3.148 kg/ha, 2016 com 2.880 kg/ha e 2021 com 3.360 kg/ha) e safras com rendimentos superiores (3.480 a 3.870 kg/ha) como classe negativa (0). |
| **Variavel de origem** | Coluna rendimento_kg_ha da tabela 1612 do IBGE PAM. |
| **Horizonte de previsao** | De 2 a 3 meses antes da colheita (durante o enchimento de graos). |
| **Distribuicao no dado consolidado** | 3 safras com quebra (30%) contra 7 safras de produtividade normal ou superior (70%) no intervalo 2015 a 2024. |

---

## 4. Atributos derivados (Sprints 2 e 4 - data/processed/dados_modelo.csv)

| Nome da coluna | Formula / Metodo | Tipo | Descricao | Razoabilidade Agronomica |
|---|---|---|---|---|
| `amplitude_termica` | `T2M_MAX - T2M_MIN` | Numerica continua (°C) | Amplitude termica media diária ao longo do ciclo | Grandes variacoes diarias elevam estresse osmotico e fisiologico na soja. |
| `precipitacao_por_temperatura` | `PRECTOTCORR / (T2M + 0.001)` | Numerica continua (mm/°C) | Indice de balanço de agua frente a evapotranspiracao | Quantifica a eficiencia da umidade sob regime de calor no Cerrado. |
| `GWET_x_PREC` | `GWETROOT * PRECTOTCORR` | Numerica continua | Interacao umidade do solo x volume precipitado | Identifica anos de precipitacao efetiva retida na zona radicular da cultura. |
| `deficit_hidrico_solo` | Contagem de dias em Jan-Fev com `GWETROOT < 0.70` | Numerica discreta (dias) | Frequencia de deficit hidrico na zona radicular na floracao/enchimento | Seca na raiz no enchimento aborta vagens e reduz drasticamente o peso de graos. |
| `dias_pico_calor` | Contagem de dias em Jan-Fev com `T2M_MAX >= 35.0` | Numerica discreta (dias) | Frequencia de calor extremo na fase reprodutiva da cultura | Temperaturas acima de 35°C causam esterilidade de polen e estresse osmotico agudo. |
| `veranico_max_dias` | Maior sequencia de dias consecutivos com chuva $< 1.0$ mm em Jan-Fev | Numerica discreta (dias) | Duracao do maior veranico no periodo reprodutivo | Estiagens prolongadas consecutivas rompem a capacidade de retencao do solo. |
| `precipitacao_enchimento` | Soma da precipitacao pluviometrica em Jan-Fev (mm) | Numerica continua (mm) | Volume pluviometrico acumulado no bimestre critico | Balanco hidrico efetivo disponivel durante a formacao da produtividade final. |

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

* **Tamanho amostral reduzido (N = 10):** A granularidade anual do IBGE gera uma base de 10 safras municipais consolidadas (2015 a 2024), impondo a necessidade de algoritmos de baixa variancia e sem sobreajuste.
* **Dados climaticos de reanalise:** Os registros da NASA POWER originam-se de modelos atmosfericos globais e sensores orbitais, nao de estacao fisica meteorologica em solo no municipio.
* **Pendencia de safra:** O registro de 2025 da NASA POWER e do IBGE foi filtrado em data/interim/ por consistir em estimativas estaticas nao consolidadas.

---

## 7. Historico de alteracoes

| Versao | Sprint | Data | Modificacoes |
|---|---|---|---|
| v0.1 | Sprint 1 | 21/09/2026 | Levantamento inicial de variaveis brutas, correcao de filtro de variaveis, integracao em data/raw/integrado.csv, estabelecimento do limiar numerico formal e definicao de colunas excluidas por vazamento. |
| v0.2 | Sprint 2 | 05/10/2026 | Re-arquitetura do dicionario de dados para Sorriso-MT 100% (Codigo IBGE 5107925), recalibracao formal do limiar para < 3.400 kg/ha, adicao dos atributos derivados de engenharia de features e formalizacao do split temporal. |
| v0.3 | Sprint 4 | 11/10/2026 | Inclusao dos atributos fenologicos derivados da NASA POWER (deficit_hidrico_solo, dias_pico_calor, veranico_max_dias e precipitacao_enchimento) focados nos erros de 2021, selecao parcimoniosa e congelamento do ColumnTransformer. |
