# Diário de Bordo Consolidado (Sprints 1 a 5) - Projeto SojaRisco (Trilha C)

**Disciplina:** Ciência de Dados e Aprendizado de Máquina (2026/2)  
**Trilha:** C - Risco de Baixa Produtividade Agrícola (Soja em Grão - Sorriso-MT, IBGE `5107925`)  
**Repositório:** [SAMUKISZHSD/bx_produtividade_agricola](https://github.com/SAMUKISZHSD/bx_produtividade_agricola)  
**Artigo Público:** [samukiszhsd.github.io/bx_produtividade_agricola](https://samukiszhsd.github.io/bx_produtividade_agricola/)

## Integrantes do Grupo
- **João Guilherme Cravo** (RGM: 35880759) - *Scrum Master (S1-S4), Engenharia de Dados Idempotente, SQLite & Artigo Técnico*
- **Jean Carlos Silva de Almeida** (RGM: 33783276) - *Pipelines Scikit-Learn, Split Temporal, Validação & Model Card*
- **Samuel Allan Nunes da Cunha** (RGM: 34524746) - *Scrum Master (S5), Modelagem Supervisionada (Árvores/Ensembles) & Dashboard Streamlit*

---

## Índice dos Diários Detalhados por Sprint
1. [Diário da Sprint 1 - Escopo, RFC, Coleta Bruta (NASA POWER + IBGE PAM)](docs/sprints/Sprint1_TrilhaC.md)
2. [Diário da Sprint 2 - Limpeza, Tratamento do Sentinela `-999.0` e Split Temporal Estrito](docs/sprints/Sprint2_TrilhaC.md)
3. [Diário da Sprint 3 - EDA, Descoberta da Armadilha de 2021 e Baselines Iniciais](docs/sprints/Sprint3_TrilhaC.md)
4. [Diário da Sprint 4 - Engenharia de Atributos Fenológicos (Jan-Fev), ColumnTransformer e Lift](docs/sprints/Sprint4_TrilhaC.md)
5. [Diário da Sprint 5 - Comparativo de Árvores/Ensembles, Calibração de Limiar, Model Card e SQLite](docs/sprints/Sprint5_TrilhaC.md)

---

## Retrospectiva Consolidada da Evolução do Projeto

### Sprint 1 (17/08 a 30/08/2026) - Kickoff, Escopo e Coleta
- **Entregas:** Canvas de Kickoff (8 perguntas), `docs/RFC.md`, coleta inicial via API da NASA POWER Daily e IBGE SIDRA PAM (Tabela 1612).
- **Decisão Crítica Registrada:** O grupo iniciou explorando Piracicaba-SP, mas identificou na auditoria dos dados brutos que a série de rendimento de soja apresentava valores repetidos/estáticos no IBGE PAM. Migramos o recorte oficial para **Sorriso-MT (IBGE 5107925)**, maior produtor nacional de soja, com série histórica dinâmica e 10 safras consolidadas (2015-2024).

### Sprint 2 (31/08 a 13/09/2026) - Limpeza e Partição Temporal
- **Entregas:** Tratamento do código sentinela `-999.0` da NASA POWER, exclusão da safra de 2025 (ainda não consolidada no IBGE PAM) e congelamento do **Split Temporal Estrito**:
 - **Treino:** 2015 a 2022 ($N = 8$ safras, sendo 3 quebras: 2015, 2016 e 2021).
 - **Teste Cego:** 2023 a 2024 ($N = 2$ safras normais).

### Sprint 3 (14/09 a 27/09/2026) - EDA e A Armadilha da Safra 2021
- **Entregas:** Análise exploratória (`05_analise_exploratoria_eda.ipynb`) e primeiros baselines (`DummyClassifier`, `Persistência`, `GaussianNB`).
- **Aprendizado Central:** Os modelos com chuva anual acumulada erraram a quebra severa de **2021** (Falso Negativo). A EDA provou o motivo: choveu `1.634 mm` no ano civil de 2021, mas a janela de enchimento de grãos (Jan-Fev) sofreu **42 dias de seca na raiz** (`GWETROOT < 0.70`) e **3 dias de calor extremo** ($\ge 35^\circ\text{C}$).

### Sprint 4 (28/09 a 11/10/2026) - Engenharia de Atributos (Jan-Fev) e Lift
- **Entregas:** Recorte estrito das variáveis no bimestre crítico de floração e enchimento (Janeiro e Fevereiro), eliminando qualquer vazamento de dados pós-fevereiro. Congelamento do `ColumnTransformer` (`models/s4_preprocessor_congelado.joblib`) com as 4 variáveis: `deficit_hidrico_solo`, `dias_pico_calor`, `precipitacao_enchimento` e `amplitude_termica`.
- **Resultado (Lift):** O `GaussianNB` saltou de Recall `0.67` para `1.00` ($\Delta = +0.33$), capturando a safra 2021 sem usar dados futuros.

### Sprint 5 (12/10 a 08/11/2026) - Árvores, Ensembles, Limiar, Dashboard e Artigo
- **Entregas:** Comparação completa de 7 modelos (`Dummy`, `Persistência`, `GaussianNB`, `LogisticRegression L2`, `DecisionTreeClassifier`, `RandomForestClassifier`, `XGBClassifier`), calibração de limiar pelo custo assimétrico do Falso Negativo (`models/limiar_congelado.json`), serialização final (`models/pipeline_final.joblib`), banco SQLite de 3 tabelas (`data/monitoramento_safra.db`), dashboard `streamlit_app.py` (WCAG 2.1 AA) e artigo web público (`docs/index.html`).
- **Conclusão Experimental:** Com $N=10$ safras, ensembles pesados (`RandomForest` e `XGBoost`) diluem a probabilidade da quebra de 2021 no backtest temporal (`0.39` e `0.454`), sofrendo Falso Negativo no corte padrão. A **Árvore de Decisão Rasa (`max_depth=2`)** foi a campeã entre as árvores (Recall = 100%, F1 = 0.67, Especificidade = 100% no teste, inferência em ~4,7 ms e regra 100% transparente para o produtor).

