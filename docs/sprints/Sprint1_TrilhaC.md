# Diario de Sprint 1 - Kickoff e Coleta Bruta Integrada

**Periodo:** 17/08/2026 a 21/09/2026  
**Trilha:** C - Risco de baixa produtividade agricola  
**Equipe:** Grupo 3  
**Integrantes:**
* Joao Guilherme Cravo (RGM: 35880759)
* Jean Carlos Silva de Almeida (RGM: 33783276)
* Samuel Allan Nunes da Cunha (RGM: 34524746)

**Scrum Master do Sprint:** Joao Guilherme Cravo  
**Repositorio GitHub:** [SAMUKISZHSD/bx_produtividade_agricola](https://github.com/SAMUKISZHSD/bx_produtividade_agricola)  

---

### Contrato desta Sprint

| Fluxo | Artefato | Destino / Consumidor |
|---|---|---|
| **Entrada** | Enunciado da Trilha C e APIs publicas | Base do kickoff do projeto |
| **Saida** | RFC.md v0.2 (problema, cultura, Piracicaba, horizonte, limiar formal, custo FN/FP, N esperado) | Sprint 2 e Sprint 5 |
| **Saida** | Dicionario_de_Dados.md v0.1 (fontes, codigos IBGE, variaveis brutas e regras anti-vazamento) | Sprint 2 |
| **Saida** | data/raw/ (JSONs originais integros e integrado.csv com N = 10) | Sprint 2 consome este bruto |
| **Saida** | Notebook executado notebooks/01_coleta_de_dados.ipynb e este diario de bordo | Avaliacao docente |

---

## 1. Definicao do problema (Canvas de Kickoff)

| Pergunta | Resposta Oficial do Grupo |
|---|---|
| **Qual evento sera previsto?** | Risco de baixa produtividade agricola (quebra de safra) da lavoura de soja. |
| **Para qual cultura e quais municipios?** | Soja em grao, exclusivamente no municipio de Piracicaba - SP (Codigo IBGE: 3538709). |
| **Qual e a unidade de analise?** | 1 ano-safra de soja para o municipio (1 linha = 1 safra anual). |
| **Qual e o horizonte da previsao?** | Previsao com 2 a 3 meses de antecedencia em relacao ao encerramento da colheita (durante floracao e enchimento de graos). |
| **Quem usaria o alerta e qual decisao ele apoiaria?** | Produtores rurais e cooperativas agricolas de Piracicaba, subsidiando contratacao preventiva de seguro rural e manejo adaptativo. |
| **Como e definida a classe positiva?** | 1 = Quebra de safra (rendimento medio < 2.450 kg/ha, abaixo da media historica municipal de 2.470 kg/ha). 0 = Safra normal/alta (>= 2.450 kg/ha). |
| **Quais dados estarao disponiveis no momento real da previsao?** | Variaveis agroclimaticas da NASA POWER acumuladas ate o momento da decisao. Variaveis agricolas do IBGE (area, quantidade, rendimento) sao excluidas das features por serem apuradas apenas pos-colheita. |
| **Qual e o custo de um falso negativo e de um falso positivo?** | O Falso Negativo e mais gravoso (produtor nao adota seguro ou contingenciamento e tem perda severa); o Falso Positivo gera custo dispensavel de premio securitario. |
| **Quantos municipios e safras entram no recorte (N esperado)?** | 1 municipio (Piracicaba) x 10 safras consolidadas (2015 a 2024), resultando em N = 10 safras no merge. |
| **Justificativa da escolha da Trilha C:** | Relevancia socioeconomica da soja, disponibilidade de dados meteorologicos globais via NASA POWER e serie historica oficial do IBGE PAM. |

- [x] RFC preenchido a partir deste canvas com limiar formal numerico
- [x] Dicionario v0.1 com fontes, codigos IBGE, variaveis brutas e tabela anti-vazamento
- [x] Recorte com uma cultura (Soja) e N esperado declarado (10 safras consolidadas)

---

## 2. Documentacao das APIs e parametros

**Variaveis selecionadas (4 variaveis oficiais do IBGE, sem variaveis de percentual):**

| Variavel | API / Endpoint | Unidade | Justificativa Agronomica | Papel no Projeto |
|---|---|---|---|---|
| `rendimento_kg_ha` | IBGE PAM (112) | kg/ha | Produtividade media obtida por hectare | Alvo (Target) |
| `area_plantada_ha` | IBGE PAM (109) | ha | Area total cultivada | Excluida (anti-vazamento) |
| `area_colhida_ha` | IBGE PAM (216) | ha | Area de fato colhida | Excluida (anti-vazamento) |
| `quantidade_produzida_t` | IBGE PAM (214) | toneladas | Producao total em peso | Excluida (anti-vazamento) |
| `PRECTOTCORR` | NASA POWER Daily | mm/dia | Precipitacao pluviometrica diaria | Feature preditora |
| `T2M` | NASA POWER Daily | graus C | Temperatura media diaria do ar | Feature preditora |
| `T2M_MAX` | NASA POWER Daily | graus C | Temperatura maxima diaria | Feature preditora |
| `T2M_MIN` | NASA POWER Daily | graus C | Temperatura minima diaria | Feature preditora |
| `RH2M` | NASA POWER Daily | percentual | Umidade relativa do ar | Feature preditora |
| `GWETROOT` | NASA POWER Daily | 0 a 1 | Umidade do solo na regiao das raizes | Feature preditora |

- [x] Documentacao das duas APIs registrada com endpoints, limites e parametros
- [x] Metadados do agregado 1612 do IBGE consultados (/metadados) com codigos explicados (Classificacao 81, Cultura Soja 2713, Municipio 3538709)
- [x] Selecao com filtro exato (eliminando colunas de percentual)
- [x] Registro formal de que o IBGE possui safras consolidadas ate 2024 (2025 em aberto)

---

## 3. Coleta bruta e inspecao tecnica

- [x] Estrutura config centralizada no notebook com coordenadas, datas e localidade
- [x] Requisicoes HTTP com timeout (30 e 60 segundos), try/except requests.RequestException e raise_for_status()
- [x] Inspecao tecnica completa: status_code (200), url consultada, Content-Type, headers e estrutura das chaves JSON documentados para ambas as APIs
- [x] Respostas brutas originais salvas em data/raw/nasa_power_Piracicaba_SP_2015_2025.json e data/raw/ibge_pam_Piracicaba_SP_2015_2025.json sem modificacoes
- [x] requirements.txt atualizado com as dependencias do projeto

---

## 4. Integracao do bruto (Transformacao e Merge)

- [x] Datas da NASA convertidas via pd.to_datetime(..., format='%Y%m%d')
- [x] Indicador sentinela de falha da NASA (-999.0 e -999) identificado e substituido por pd.NA
- [x] Agregacao do clima diario por ano-safra (groupby('ano')) com operacoes justificadas (soma para chuva, media para temperaturas/umidade, maximo para pico termico, minimo para frio)
- [x] Tabela do IBGE estruturada com as 4 variaveis em formato colunar por ano
- [x] Juncao realizada via pd.merge(how='inner', validate='1:1'), assegurando integridade relacional sem duplicatas
- [x] N apos o merge registrado: 10 safras consolidadas (2015 a 2024)
- [x] Tabela integrada salva em data/raw/integrado.csv

---

## 5. Verificacao inicial de qualidade e variavel-alvo

- [x] Inspecao estrutural e estatistica via .info() e .describe()
- [x] Quantificacao de ausentes por coluna (df.isna().sum())
- [x] Verificacao de duplicatas completa (df.duplicated().sum() e na chave ano)
- [x] Validacao de regras de consistencia de dominio (rendimentos negativos, chuva negativa, umidade fora de 0-100% contados sem exclusao cega)
- [x] Visualizacao temporal com matplotlib plotando a serie de rendimento da soja com titulo, eixos e unidade
- [x] Variavel-alvo codificada com limiar formal (2.450 kg/ha), gerando a coluna quebra_safra (1 = quebra, 0 = normal)
- [x] Distribuicao das classes reportada via .value_counts() em contagem e percentual

---

## 6. Organizacao Scrum

* **Product Owner:** Jean Carlos Silva de Almeida
* **Scrum Master da Sprint 1:** Joao Guilherme Cravo  
* **Equipe de Desenvolvimento:** Samuel Allan Nunes da Cunha  

**User Stories do Backlog da Sprint 1:**
1. Como desenvolvedor, preciso requisitar os dados da NASA POWER via API diaria para dispor da serie historica agroclimatica de Piracicaba-SP (2015-2025).
2. Como desenvolvedor, preciso consultar a API de Dados Agregados do IBGE PAM para obter as metricas de produtividade e area de soja consolidadas.
3. Como cientista de dados, preciso agregar o clima por ano-safra e realizar a integracao (merge 1:1) com o IBGE, gerando o arquivo data/raw/integrado.csv para servir de base as etapas subsequentes.

**Quadro de Tarefas:** [SAMUKISZHSD/bx_produtividade_agricola - Projects](https://github.com/users/SAMUKISZHSD/projects/)

---

## 7. Diario de bordo (Retrospectiva individual)

| Integrante | Papel Scrum | Atividades Realizadas na Sprint | Dificuldades Tecnicas | Proximos Passos |
|---|---|---|---|---|
| **Joao Guilherme** | Scrum Master | Coordenacao das metas da sprint, organizacao do board e backlog, padronizacao do merge 1:1 e consolidacao do diario de bordo e da RFC. | Assegurar o fechamento do escopo em conformidade rigorosa com as rubricas de avaliacao da disciplina. | Facilitar a transicao para a Sprint 2, acompanhando os prazos de limpeza e split no board. |
| **Jean Carlos** | Product Owner | Definicao do escopo de negocio (soja em Piracicaba), priorizacao do custo de falso negativo, refinamento das user stories e aprovacao dos dados do IBGE PAM. | Calibrar o limiar historico de quebra de safra em conformidade com as perdas reais da cultura. | Validar os criterios de negocio da variavel-alvo e definir as prioridades analiticas da Sprint 2. |
| **Samuel Allan** | Equipe de Dev | Execucao tecnica das requisicoes as APIs, inspecao de headers HTTP, verificacao de qualidade (.info, .describe, checagens de dominio) e codificacao do alvo no notebook. | Tratamento de codigos sentinela (-999.0) da NASA e ajuste de filtro do IBGE para descartar variaveis de percentual. | Implementar os scripts de limpeza e transformacao para geracao da base interim na Sprint 2. |

---

## 8. Evidencias da entrega

* **Notebook executado:** [notebooks/01_coleta_de_dados.ipynb](notebooks/01_coleta_de_dados.ipynb)
* **Tabela integrada bruta:** [data/raw/integrado.csv](data/raw/integrado.csv)
* **JSONs preservados:** `data/raw/nasa_power_Piracicaba_SP_2015_2025.json` e `data/raw/ibge_pam_Piracicaba_SP_2015_2025.json`
* **RFC:** [docs/RFC.md](docs/RFC.md)
* **Dicionario de Dados:** [docs/Dicionario_de_Dados.md](docs/Dicionario_de_Dados.md)

---
