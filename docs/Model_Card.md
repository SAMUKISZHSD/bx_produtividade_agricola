# Model Card - Alerta de Risco de Baixa Produtividade Agrícola (Soja em Sorriso-MT)

## 1. Detalhes do Modelo
- **Nome Oficial:** Árvore de Decisão Parcimoniosa para Previsão de Quebra de Safra (`DecisionTreeClassifier`) e Co-Campeão Probabilístico (`LogisticRegression` L2).
- **Versão:** 1.0 (Sprint 5 Consolidada - Outubro/Novembro 2026)
- **Família de Algoritmos:** Particionamento Binário Supervisionado (`DecisionTreeClassifier(criterion='gini', max_depth=2, class_weight='balanced', random_state=42)`), comparado contra `DummyClassifier`, `Persistência`, `GaussianNB`, `LogisticRegression`, `RandomForestClassifier` (Bagging) e `XGBClassifier` (Gradient Boosting).
- **Desenvolvedores:** Grupo 3 - Trilha C:
 - **João Guilherme Cravo** (RGM: 35880759) - *Scrum Master & Engenharia de Dados/Frontend*
 - **Jean Carlos Silva de Almeida** (RGM: 33783276) - *Pipelines Scikit-Learn, Split Temporal & Validação*
 - **Samuel Allan Nunes da Cunha** (RGM: 34524746) - *Modelagem Supervisionada, Banco SQLite & Dashboard Streamlit*
- **Pipeline Serializado:** `models/pipeline_final.joblib` e `models/modelo_final.joblib` (`ColumnTransformer` com `StandardScaler` + `DecisionTreeClassifier`).

## 2. Uso Pretendido e Escopo Operacional
- **Objetivo de Negócio:** Antecipar safras de soja com risco severo de quebra de produtividade (< 3.400 kg/ha) no município de Sorriso-MT até o fechamento de fevereiro (28/02), com 30 a 45 dias de antecedência em relação à consolidação da colheita.
- **Público-Alvo:** Produtores rurais, cooperativas agropecuárias, corretores de seguro agrícola e agentes de crédito rural.
- **Ação Engatilhada:** Acionamento de seguro rural, revisão de contratos futuros de entrega de grãos (hedge financeiro) e vistoria agronômica direcionada.
- **Fora do Escopo:** Não deve ser aplicado diretamente a outras culturas (milho, algodão) ou municípios fora do bioma de transição Cerrado-Amazônia sem recalibração do limiar histórico local.

## 3. Dados de Treinamento, Validação e Teste
- **Fontes Públicas Abertas:** NASA POWER Daily API (`PRECTOTCORR`, `T2M_MAX`, `T2M_MIN`, `GWETROOT`) e IBGE SIDRA PAM (Agregado 1612 - Soja em grão, Município `5107925` Sorriso-MT).
- **Amostra Consolidada ($N = 10$):** Safras de 2015 a 2024 (safra de 2025 excluída por ausência de fechamento oficial no IBGE).
 - **Partição de Treino (2015-2022, $N = 8$):** 3 quebras severas (2015, 2016 e 2021) e 5 safras normais (2017, 2018, 2019, 2020 e 2022).
 - **Partição de Teste Cego (2023-2024, $N = 2$):** 2 safras normais (3.580 kg/ha e 3.560 kg/ha).
- **4 Features Intra-Safra Congeladas (Bimestre Crítico Jan-Fev):**
  1. `deficit_hidrico_solo`: dias com umidade na zona radicular (`GWETROOT < 0.70`) em Jan-Fev.
  2. `dias_pico_calor`: dias com temperatura máxima (`T2M_MAX >= 35°C`) em Jan-Fev.
  3. `precipitacao_enchimento`: chuva acumulada (mm) em Jan-Fev.
  4. `amplitude_termica`: variação térmica extrema (°C) em Jan-Fev.

## 4. Desempenho Comparativo (Treino, Validação Temporal e Teste Congelado)

| Modelo | Recall (Treino) | F1 (Treino) | FN (Treino) | Recall (Val. 2019-22) | F1 (Val. 2019-22) | Acurácia (Teste 2023-24) | FP (Teste) | Treino (ms) | Inferência (ms) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `DummyClassifier` | 0.00 | 0.00 | 3 | 0.00 | 0.00 | 100% | 0 | 4.24 | 5.19 |
| `Persistência` ($y_{t-1}$) | 0.33 | 0.33 | 2 | 0.00 | 0.00 | 100% | 0 | 0.38 | 0.72 |
| `GaussianNB` | 1.00 | 1.00 | 0 | **1.00** | **0.67** | 100% | 0 | 4.25 | 4.07 |
| `LogisticRegression` (L2, $p=0.50$ / $p=0.35$) | 1.00 | 1.00 | 0 | 0.00 / **1.00** | 0.00 / **0.67** | 100% | 0 | 5.33 | 3.87 |
| **`DecisionTreeClassifier` (Campeã)** | **1.00** | **1.00** | **0** | **1.00** | **0.67** | **100%** | **0** | **4.33** | **4.72** |
| `RandomForestClassifier` (100 árvores) | 1.00 | 1.00 | 0 | 0.00 | 0.00 | 100% | 0 | 124.95 | 17.52 |
| `XGBClassifier` (50 árvores) | 1.00 | 1.00 | 0 | 0.00 | 0.00 | 100% | 0 | 16.07 | 7.40 |

### Justificativa Técnica da Escolha da Árvore de Decisão Rasa
- **Superação dos Ensembles em Amostra Decenal ($N=10$):** Na validação temporal expansiva para prever a quebra de 2021 (treinando apenas com 2015-2020, $N=6$), o `RandomForest` diluiu a probabilidade da quebra para `0.39` pela amostragem bootstrap em subconjuntos minúsculos, e o `XGBoost` sofreu com a regularização dos gradientes (`0.4545`), ambos falhando no corte padrão. A **Árvore de Decisão Rasa** isolou a regra biofísica exata no nó raiz (`deficit_hidrico_solo > 21,5 dias`), capturando 100% das quebras sem precisar de ajuste artificial de limiar.
- **Interpretabilidade Caixa-Branca:** Fornece uma regra auditável em campo pelos agrônomos e seguradoras.

## 5. Limitações, Riscos e Considerações Éticas
- **Tamanho Amostral ($N = 10$):** Restrito pela periodicidade anual da pesquisa oficial IBGE PAM.
- **Ausência de Quebras no Teste Recente (2023-2024):** Como 2023 e 2024 foram safras normais, o teste cego comprova **100% de Especificidade (zero falsos alarmes)**, enquanto a sensibilidade às quebras (Recall = 100%) é atestada na validação cruzada temporal expansiva.
- **Resolução Espacial da NASA POWER:** Grade de $0,5^\circ \times 0,5^\circ$ (~55 km), representando o comportamento médio municipal e não talhões isolados.
