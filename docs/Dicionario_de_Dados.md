# Dicionario de Dados - Contrato de Variaveis

**Projeto:** Previsao de Risco de Baixa Produtividade Agricola (Soja)  
**Trilha:** C - Risco de baixa produtividade agricola  
**Equipe:** Grupo 3 (Joao Guilherme Cravo, Jean Carlos Silva de Almeida, Samuel Allan Nunes da Cunha)  
**Ultima atualizacao:** 21/09/2026  
**Versao:** v0.1 (Sprint 1)  

* **Unidade de analise:** 1 ano-safra de soja para o municipio de Piracicaba-SP.
* **N apos o merge (Sprint 1, bruto):** 10 safras consolidadas (2015 a 2024).
* **N apos a limpeza (Sprint 2, data/interim):** A preencher na Sprint 2
* **Split (Sprint 2):** A formalizar na Sprint 2

---

## 1. Fontes de dados

| Fonte | API / Endpoint | Cobertura temporal disponivel | Resolucao temporal | Medido ou modelado? | Limitacoes conhecidas |
|---|---|---|---|---|---|
| **NASA POWER** | https://power.larc.nasa.gov/api/temporal/daily/point | 1981 ate o presente | Diaria | Modelado | Estimativa por sensoriamento remoto e reanalise fisica (resolucao 0.5 grau). Utiliza codigo -999.0 como sentinela de ausencia de medicao. |
| **IBGE (PAM)** | Agregado 1612 (Lavouras Temporarias, Cultura 2713) | Historico anual | Anual (Safra) | Medido / Declaratorio | Dados municipais oficiais consolidados apos encerramento da colheita. A safra de 2025 ainda nao foi divulgada pelo orgao. |

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
| Safra 2025 do IBGE nao consolidada | Juncao via how='inner' com validate='1:1' | 1 ano (2025) | 10 safras | Retencao do intervalo completo 2015 a 2024 |

---

## 3. Variavel-alvo

| Campo | Descricao |
|---|---|
| **Nome da coluna** | quebra_safra |
| **Definicao da classe positiva** | 1 = Quebra de safra (baixa produtividade crítica). 0 = Safra normal ou superior. |
| **Limiar adotado e justificativa** | Rendimento estritamente inferior a 2.450 kg/ha. A media historica observada entre 2015 e 2024 e de aproximadamente 2.470 kg/ha. O limiar segrega as safras de menor desempenho (2.400 kg/ha) como classe positiva e safras com rendimentos de 2.500 e 3.000 kg/ha como classe negativa. |
| **Variavel de origem** | Coluna rendimento_kg_ha da tabela 1612 do IBGE PAM. |
| **Horizonte de previsao** | De 2 a 3 meses antes da colheita (durante o enchimento de graos). |
| **Distribuicao no dado bruto** | 8 safras com quebra/baixa produtividade (80%) contra 2 safras de rendimento superior (20%) no intervalo 2015 a 2024. |

---

## 4. Atributos derivados (Sprints 2 e 4)

A preencher nas Sprints 2 e 4 conforme criacao de atributos adicionais.

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

* **Tamanho amostral reduzido (N = 10):** A granularidade anual do IBGE gera uma base de 10 safras municipais, impondo a necessidade de algoritmos de baixa variancia e sem sobreajuste.
* **Dados climaticos de reanalise:** Os registros da NASA POWER originam-se de modelos atmosfericos globais e sensores orbitais, nao de estacao fisica meteorologica em solo no municipio.
* **Pendencia de safra:** O registro de 2025 da NASA POWER foi coletado, mas permanece desvinculado do merge ate a divulgacao oficial dos dados pelo IBGE.

---

## 7. Historico de alteracoes

| Versao | Sprint | Data | Modificacoes |
|---|---|---|---|
| v0.1 | Sprint 1 | 21/09/2026 | Levantamento inicial de variaveis brutas, correcao de filtro de variaveis, integracao em data/raw/integrado.csv, estabelecimento do limiar numerico formal (< 2.450 kg/ha) e definicao de colunas excluidas por vazamento. |
