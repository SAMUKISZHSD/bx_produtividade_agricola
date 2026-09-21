# RFC: Proposta de Projeto - Previsao de Risco de Baixa Produtividade Agricola (Soja)

| Campo | Valor |
|---|---|
| **Titulo** | Previsao de Risco de Baixa Produtividade Agricola para Soja em Piracicaba - SP |
| **Trilha** | C - Risco de baixa produtividade agricola |
| **Equipe** | Joao Guilherme Cravo (RGM 35880759), Jean Carlos Silva de Almeida (RGM 33783276), Samuel Allan Nunes da Cunha (RGM 34524746) |
| **Autores** | Grupo 3 - Trilha C |
| **Status** | Aprovado (Sprint 1) |
| **Data** | Setembro de 2026 |
| **Sprint de referencia** | 1 |

---

## 1. Resumo (TL;DR)

O projeto visa prever o risco de quebra de safra (baixa produtividade agricola em kg/ha) da cultura de soja em grao no municipio de Piracicaba - SP, cruzando variaveis agroclimaticas diarias da NASA POWER com dados historicos de producao do IBGE PAM. O modelo destina-se a orientar produtores rurais, cooperativas e seguradoras agricolas em decisoes preventivas de manejo e contratacao de seguro rural.

---

## 2. Contexto e motivacao

A soja representa uma das culturas de maior peso economico no agronegocio paulista. O rendimento da lavoura e dependente de fatores meteorologicos, sofrendo perdas expressivas quando ocorrem deficits hidricos ou picos de calor em fases fenologicas criticas, como floracao e enchimento de graos. A previsao antecipada da produtividade com meses de antecedencia subsidia medidas mitigadoras e planejamento financeiro, reduzindo a exposicao do produtor ao risco climatico.

---

## 3. Problema e evento a ser previsto

| Pergunta | Resposta |
|---|---|
| **Qual evento sera previsto?** | Ocorrencia de quebra de safra (rendimento medio por hectare abaixo do patamar historico aceitavel). |
| **Como e definida a classe positiva?** | Classe 1 (quebra de safra) definida por rendimento medio inferior a 2.450 kg/ha, com base na media historica municipal de 2.470 kg/ha. Classe 0 representa safras normais ou de alto rendimento (>= 2.450 kg/ha). |
| **Qual e o horizonte da previsao?** | Antecedencia de 2 a 3 meses em relacao ao encerramento da colheita (previsao realizada durante a fase de floracao e enchimento de vagens). |
| **Qual e a unidade de analise?** | Ano-safra de soja para o municipio de Piracicaba-SP (1 linha = 1 safra anual). |

---

## 4. Escopo

| Pergunta | Resposta |
|---|---|
| **Recorte geografico e cultura** | Soja em grao no municipio de Piracicaba - SP (Codigo IBGE: 3538709, Latitude: -22.7253, Longitude: -47.6492). |
| **Periodo historico considerado** | Safras de 2015 a 2024 consolidadas (10 safras integradas; safra de 2025 ainda nao finalizada no IBGE PAM). |
| **Dentro do escopo** | Ingestao de dados da NASA POWER e IBGE PAM, pipeline de pre-processamento sem vazamento temporal, integracao em data/raw/integrado.csv, avaliacao de modelos baseline e classificadores Supervisionados. |
| **Fora do escopo** | Previsao de precos de mercado, diagnostico de pragas biologicas, modelagem de outras culturas (milho, cana) ou expansao para outros municipios nesta etapa. |

**Nota sobre a amostra:** A integracao resulta em N = 10 safras anuais consolidadas. A dimensionalidade reduzida restringe o uso de arquiteturas de alta complexidade e exige modelos parcimoniosos com forte controle contra sobreajuste (overfitting).

---

## 5. Usuarios e decisao apoiada

* **Usuarios:** Produtores rurais, tecnicos de cooperativas agropecuarias e analistas de risco de credito rural.
* **Decisao apoiada:** Alertas precoces de quebra de safra apoiam:
  1. Contratacao antecipada de apolices de seguro agricola.
  2. Redefinicao de custos com adubacao de cobertura e irrigacao suplementar.
  3. Repactuacao preventiva de fluxo de caixa e creditos de insumos.

---

## 6. Dados e fontes

| Fonte | Endpoint / Identificador | Resolucao | Natureza dos Dados | Papel no Projeto |
|---|---|---|---|---|
| **NASA POWER** | api/temporal/daily/point (Comunidade AG) | Diaria | Modelado (Reanalise e satelite) | Features preditoras: PRECTOTCORR (chuva), T2M (temperatura media), T2M_MAX, T2M_MIN, RH2M (umidade ar) e GWETROOT (umidade solo). |
| **IBGE (PAM)** | Agregado 1612 (Classificacao 81, Cultura 2713) | Anual (Safra) | Medido / Declaratorio | Variavel-alvo: rendimento_kg_ha utilizado para rotulagem da classe positiva. Demais variaveis agricolas excluidas das features. |

Contrato de variaveis detalhado em: [Dicionario_de_Dados.md](docs/Dicionario_de_Dados.md)

---

## 7. Custo dos erros

| Tipo de Erro | Definicao no Contexto | Consequencia Pratica |
|---|---|---|
| **Falso Positivo (FP)** | O modelo indica quebra de safra, mas a colheita atinge nivel normal. | Custo financeiro nao essencial com o pagamento de premio de seguro rural. |
| **Falso Negativo (FN)** | O modelo indica safra normal, mas ocorre perda severa sem aviso. | Prejuizo severo ao produtor por falta de cobertura de seguro e descapitalizacao. |

**Metrica priorizada:** O Falso Negativo apresenta impacto operacional mais severo. Dessa forma, a calibracao dos modelos prioriza a metrica de Recall na classe positiva (quebra_safra = 1), assegurando que eventos de quebra sejam detectados com antecedencia.

---

## 8. Abordagem proposta

1. Ingestao automatizada das APIs (NASA POWER e IBGE PAM) com tratamento de erros HTTP e gravacao dos dados brutos em disco.
2. Agregacao temporal das variaveis meteorologicas diarias para o ciclo anual da cultura e integracao 1:1 com os dados do IBGE em data/raw/integrado.csv.
3. Inspecao de qualidade, verificacao de consistencia de dominio e analise exploratoria dos dados limpos.
4. Definicao de particao temporal de treino e teste sem embaralhamento temporal, respeitando a linha do tempo.
5. Construcao de pipeline scikit-learn unificado, garantindo fit exclusivo no conjunto de treino.
6. Avaliacao de baselines (Dummy, Persistencia e Naive Bayes) e selecao de modelos finais balizados pelo custo de falsos negativos.

---

## 9. Riscos e limitacoes

1. **Volume amostral reduzido (N = 10):** Limite imposto pela frequencia anual de divulgacao das safras pelo IBGE PAM.
2. **Defasagem da safra 2025:** O IBGE PAM consolida os dados apenas apos o encerramento do ano civil correspondente.
3. **Dados meteorologicos modelados:** Os dados da NASA POWER consistem em reanalise com resolucao de 0.5 grau, podendo apresentar variacoes pontuais em microclimas especificos.

---

## 10. Criterios de sucesso

* Execucao reprodutivel do pipeline de ingestao e integracao dos dados.
* Conformidade integral com diretrizes anti-vazamento de dados temporais.
* Maximizacao de Recall na classe positiva no conjunto de validacao e teste.
* Documentacao tecnica estruturada em conformidade com as rubricas da disciplina.

---

## 11. Historico de revisoes

| Versao | Data | Autor | Descricao da Modificacao |
|---|---|---|---|
| v0.1 | 31/08/2026 | Grupo 3 | Proposta inicial do projeto. |
| v0.2 | 21/09/2026 | Grupo 3 | Formalizacao do limiar numerico de quebra (< 2.450 kg/ha), atualizacao da amostra para 10 safras consolidadas (2015-2024), documentacao de ausencia da safra 2025 e detalhamento de criterios anti-vazamento. |
