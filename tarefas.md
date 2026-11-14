# Quadro Consolidado de Tarefas Scrum (`tarefas.md`) - Sprints 1 a 5

**Projeto:** SojaRisco - Previsão de Quebra de Safra de Soja em Sorriso-MT (Trilha C)  
**Quadro Oficial no Trello:** [Trello - Projeto de Ciência de Dados](https://trello.com/invite/b/6a975ab20fa3094b426c0c68/ATTI02cea94da7f784bcf30e1e3d24341426A34F2CE2/📊-projeto-de-ciencia-de-dados)

| Sprint | ID Card | Tarefa / Entregável | Responsável | Status | Artefato no Repositório |
| :---: | :---: | :--- | :--- | :---: | :--- |
| **S1** | S1-01 | Definição do Canvas de Kickoff (8 perguntas) e RFC | João Guilherme | CONCLUÍDO | `README.md`, `docs/RFC.md` |
| **S1** | S1-02 | Coleta idempotente NASA POWER Daily e IBGE PAM 1612 | Samuel Allan | CONCLUÍDO | `notebooks/01_coleta_de_dados.ipynb`, `src/coleta_api.py` |
| **S1** | S1-03 | Dicionário de Dados v0.1 e governança Scrum S1 | Jean Carlos | CONCLUÍDO | `docs/Dicionario_de_Dados.md`, `docs/sprints/Sprint1_TrilhaC.md` |
| **S2** | S2-01 | Limpeza do sentinela `-999.0` e exclusão da safra 2025 | Jean Carlos | CONCLUÍDO | `notebooks/02_limpeza_split_temporal.ipynb` |
| **S2** | S2-02 | Definição do alvo binário (< 3.400 kg/ha) e Split Temporal | Samuel Allan | CONCLUÍDO | `notebooks/03_tratamento_estatistico_residual.ipynb`, `notebooks/04_alvo_e_features.ipynb` |
| **S2** | S2-03 | Auditoria contra vazamento temporal e Diário S2 | João Guilherme | CONCLUÍDO | `docs/sprints/Sprint2_TrilhaC.md` |
| **S3** | S3-01 | Análise Exploratória (EDA) e investigação da safra 2021 | João Guilherme | CONCLUÍDO | `notebooks/05_analise_exploratoria_eda.ipynb` |
| **S3** | S3-02 | Modelagem dos Baselines (`Dummy`, `Persistência`, `GaussianNB`) | Samuel Allan | CONCLUÍDO | `notebooks/06_modelagem_baselines.ipynb`, `notebooks/07_dummyclassifier_gaussiannb_pipeline.ipynb` |
| **S3** | S3-03 | Avaliação crítica de Falsos Negativos e Diário S3 | Jean Carlos | CONCLUÍDO | `docs/sprints/Sprint3_TrilhaC.md` |
| **S4** | S4-01 | Engenharia de Atributos na janela crítica (Jan-Fev) | João Guilherme | CONCLUÍDO | `notebooks/08_engenharia_features_selecao_parcimoniosa.ipynb`, `src/etl_processamento.py` |
| **S4** | S4-02 | Congelamento do `ColumnTransformer` e retreino dos Baselines | Jean Carlos | CONCLUÍDO | `notebooks/09_retreino_baselines_pipeline_congelado.ipynb`, `models/s4_preprocessor_congelado.joblib` |
| **S4** | S4-03 | Tabela de Lift (S3 vs S4) e revisão da Sprint 4 | Samuel Allan | CONCLUÍDO | `notebooks/10_tabela_lift_interpretacao_sprint_review.ipynb`, `docs/sprints/Sprint4_TrilhaC.md` |
| **S5** | S5-01 | Comparativo final (`DecisionTree`, `RandomForest`, `XGBoost`, `LogReg`) | Samuel Allan | CONCLUÍDO | `notebooks/11_modelagem_comparativa_novos_classificadores.ipynb`, `models/s5_comparativo_teste.csv` |
| **S5** | S5-02 | Calibração de limiar na validação temporal e custo de FN | Jean Carlos | CONCLUÍDO | `notebooks/12_calibracao_limiar_validacao_temporal.ipynb`, `models/limiar_congelado.json` |
| **S5** | S5-03 | Avaliação única no teste cego, serialização `joblib` e Model Card | Jean Carlos | CONCLUÍDO | `notebooks/13_avaliacao_teste_congelado_model_card.ipynb`, `models/pipeline_final.joblib`, `docs/Model_Card.md` |
| **S5** | S5-04 | Persistência relacional SQLite (3 tabelas) e Dashboard Streamlit | Samuel Allan | CONCLUÍDO | `src/database.py`, `data/monitoramento_safra.db`, `streamlit_app.py` |
| **S5** | S5-05 | Artigo técnico web (GitHub Pages), QR Code e Diário Final | João Guilherme | CONCLUÍDO | `docs/index.html`, `docs/js/project-data.js`, `docs/img/qrcode_artigo.png`, `DIARIO.md` |

