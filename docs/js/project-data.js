/**
 * ==============================================================================
 * Camada Centralizada de Dados do Projeto - SojaRisco
 * ==============================================================================
 *
 * Fonte oficial: data/processed/dados_modelo_s4.csv, models/limiar_congelado.json,
 * models/modelo_final_metadados.json, models/s5_avaliacao_teste_final.csv,
 * models/s5_comparativo_teste.csv, models/s5_comparativo_validacao.csv,
 * models/s7_comparacao_modelos.csv e docs/Model_Card.md.
 * Unidade: municipio x safra (9 municípios do Alto Teles Pires - MT).
 */

window.PROJECT_DATA = {
  // Metadados Gerais do Experimento
  metadata: {
    municipio: "Alto Teles Pires - MT (9 municípios)",
    municipioReferencia: "Sorriso - MT",
    codigo_ibge: "5107925",
    cultura: "Soja em Grão",
    unidade: "municipio x safra",
    amostra_total: 192,
    treino_linhas: 138,
    teste_linhas: 54,
    municipios: 9,
    treino_anos: "2001 a 2018",
    teste_anos: "2019 a 2024",
    split_estrategia: "Temporal",
    feature: "tmax_enchimento",
    limiar_probabilidade: 0.45,
    limiar_celsius: 28.34,
    deriva_climatica: {
      media_treino_c: 28.46,
      media_teste_c: 29.88
    },
    is_mock: false,
    aprovado: false,
    status: "protótipo experimental (não aprovado para decisão operacional)",
    tag_status: "Protótipo experimental — não aprovado para decisão operacional (Sprints 5–7)"
  },

  // Série Histórica Oficial de Sorriso - MT (24 safras, 2001-2024, fonte: dados_modelo_s4.csv)
  historico: [
    { ano: 2001, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.64, chuva_enchimento: 677.44, dias_calor_enchimento: 0, veranico_enchimento: 3, gwet_enchimento: 0.772, amplitude_termica: 23.90, quebra_real: 0, rotulo: "Normal" },
    { ano: 2002, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.67, chuva_enchimento: 860.11, dias_calor_enchimento: 0, veranico_enchimento: 1, gwet_enchimento: 0.816, amplitude_termica: 21.24, quebra_real: 1, rotulo: "Quebra" },
    { ano: 2003, municipio: "Sorriso", split: "Treino", tmax_enchimento: 28.49, chuva_enchimento: 798.08, dias_calor_enchimento: 2, veranico_enchimento: 6, gwet_enchimento: 0.779, amplitude_termica: 20.09, quebra_real: 1, rotulo: "Quebra" },
    { ano: 2004, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.41, chuva_enchimento: 936.03, dias_calor_enchimento: 0, veranico_enchimento: 2, gwet_enchimento: 0.844, amplitude_termica: 22.79, quebra_real: 0, rotulo: "Normal" },
    { ano: 2005, municipio: "Sorriso", split: "Treino", tmax_enchimento: 28.16, chuva_enchimento: 801.17, dias_calor_enchimento: 0, veranico_enchimento: 5, gwet_enchimento: 0.804, amplitude_termica: 22.92, quebra_real: 0, rotulo: "Normal" },
    { ano: 2006, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.58, chuva_enchimento: 931.89, dias_calor_enchimento: 0, veranico_enchimento: 4, gwet_enchimento: 0.829, amplitude_termica: 21.85, quebra_real: 1, rotulo: "Quebra" },
    { ano: 2007, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.94, chuva_enchimento: 1160.04, dias_calor_enchimento: 0, veranico_enchimento: 2, gwet_enchimento: 0.861, amplitude_termica: 22.37, quebra_real: 0, rotulo: "Normal" },
    { ano: 2008, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.49, chuva_enchimento: 974.84, dias_calor_enchimento: 0, veranico_enchimento: 4, gwet_enchimento: 0.847, amplitude_termica: 20.50, quebra_real: 0, rotulo: "Normal" },
    { ano: 2009, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.63, chuva_enchimento: 755.17, dias_calor_enchimento: 0, veranico_enchimento: 5, gwet_enchimento: 0.825, amplitude_termica: 21.32, quebra_real: 0, rotulo: "Normal" },
    { ano: 2010, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.80, chuva_enchimento: 858.45, dias_calor_enchimento: 0, veranico_enchimento: 4, gwet_enchimento: 0.808, amplitude_termica: 21.00, quebra_real: 0, rotulo: "Normal" },
    { ano: 2011, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.21, chuva_enchimento: 861.63, dias_calor_enchimento: 0, veranico_enchimento: 2, gwet_enchimento: 0.812, amplitude_termica: 23.23, quebra_real: 0, rotulo: "Normal" },
    { ano: 2012, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.60, chuva_enchimento: 791.67, dias_calor_enchimento: 0, veranico_enchimento: 4, gwet_enchimento: 0.785, amplitude_termica: 21.32, quebra_real: 0, rotulo: "Normal" },
    { ano: 2013, municipio: "Sorriso", split: "Treino", tmax_enchimento: 29.08, chuva_enchimento: 646.93, dias_calor_enchimento: 0, veranico_enchimento: 4, gwet_enchimento: 0.720, amplitude_termica: 21.95, quebra_real: 0, rotulo: "Normal" },
    { ano: 2014, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.42, chuva_enchimento: 593.39, dias_calor_enchimento: 0, veranico_enchimento: 3, gwet_enchimento: 0.763, amplitude_termica: 21.02, quebra_real: 0, rotulo: "Normal" },
    { ano: 2015, municipio: "Sorriso", split: "Treino", tmax_enchimento: 29.52, chuva_enchimento: 429.70, dias_calor_enchimento: 0, veranico_enchimento: 7, gwet_enchimento: 0.699, amplitude_termica: 21.45, quebra_real: 0, rotulo: "Normal" },
    { ano: 2016, municipio: "Sorriso", split: "Treino", tmax_enchimento: 31.69, chuva_enchimento: 408.16, dias_calor_enchimento: 14, veranico_enchimento: 7, gwet_enchimento: 0.682, amplitude_termica: 26.01, quebra_real: 1, rotulo: "Quebra" },
    { ano: 2017, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.85, chuva_enchimento: 654.19, dias_calor_enchimento: 0, veranico_enchimento: 3, gwet_enchimento: 0.759, amplitude_termica: 20.52, quebra_real: 0, rotulo: "Normal" },
    { ano: 2018, municipio: "Sorriso", split: "Treino", tmax_enchimento: 27.68, chuva_enchimento: 973.30, dias_calor_enchimento: 0, veranico_enchimento: 5, gwet_enchimento: 0.835, amplitude_termica: 22.51, quebra_real: 0, rotulo: "Normal" },
    { ano: 2019, municipio: "Sorriso", split: "Teste Temporal", tmax_enchimento: 29.04, chuva_enchimento: 547.61, dias_calor_enchimento: 0, veranico_enchimento: 7, gwet_enchimento: 0.719, amplitude_termica: 22.28, quebra_real: 0, rotulo: "Normal" },
    { ano: 2020, municipio: "Sorriso", split: "Teste Temporal", tmax_enchimento: 29.62, chuva_enchimento: 501.20, dias_calor_enchimento: 0, veranico_enchimento: 2, gwet_enchimento: 0.703, amplitude_termica: 21.17, quebra_real: 0, rotulo: "Normal" },
    { ano: 2021, municipio: "Sorriso", split: "Teste Temporal", tmax_enchimento: 31.42, chuva_enchimento: 546.79, dias_calor_enchimento: 9, veranico_enchimento: 5, gwet_enchimento: 0.676, amplitude_termica: 22.81, quebra_real: 1, rotulo: "Quebra" },
    { ano: 2022, municipio: "Sorriso", split: "Teste Temporal", tmax_enchimento: 27.53, chuva_enchimento: 823.55, dias_calor_enchimento: 0, veranico_enchimento: 5, gwet_enchimento: 0.836, amplitude_termica: 22.13, quebra_real: 0, rotulo: "Normal" },
    { ano: 2023, municipio: "Sorriso", split: "Teste Temporal", tmax_enchimento: 27.54, chuva_enchimento: 757.79, dias_calor_enchimento: 0, veranico_enchimento: 1, gwet_enchimento: 0.794, amplitude_termica: 23.33, quebra_real: 0, rotulo: "Normal" },
    { ano: 2024, municipio: "Sorriso", split: "Teste Temporal", tmax_enchimento: 31.19, chuva_enchimento: 692.67, dias_calor_enchimento: 18, veranico_enchimento: 5, gwet_enchimento: 0.717, amplitude_termica: 20.64, quebra_real: 1, rotulo: "Quebra" }
  ],

  // Tabela de Lift de Engenharia de Atributos (Sprint 3 -> Sprint 4 no teste, N=54)
  liftS3S4: [
    {
      modelo: "LogReg (tmax_enchimento)",
      recallS3: 0.75,
      recallS4: 0.75,
      f1S3: 0.419,
      f1S4: 0.367,
      aucS3: 0.764,
      aucS4: 0.728,
      deltaRecall: 0.0,
      status: "Nenhuma família multivariável superou o p95 nulo no treino; tmax_enchimento manteve sinal (AUC val=0,648 > p95=0,603)"
    },
    {
      modelo: "GaussianNB (tmax_enchimento)",
      recallS3: 0.75,
      recallS4: 0.75,
      f1S3: 0.439,
      f1S4: 0.529,
      aucS3: 0.714,
      aucS4: 0.728,
      deltaRecall: 0.0,
      status: "Sem sinal estatístico na validação do treino (AUC val=0,378 < p95=0,485)"
    }
  ],

  // Métricas Consolidadas dos Modelos no Teste Temporal (2019-2024, N=54, 9 municípios)
  // Fontes: models/s5_avaliacao_teste_final.csv, models/s5_comparativo_teste.csv e models/s7_comparacao_modelos.csv
  modelos: {
    dummy: {
      id: "dummy",
      nome: "DummyClassifier (Nunca alertar)",
      familia: "Baseline Ingênuo",
      tipoBadge: "Baseline de Referência",
      recall: 0.0,
      precisao: 0.0,
      f1: 0.0,
      acuracia: 0.778,
      auc: 0.5,
      custo: 60,
      fnTreino: 24,
      fpTreino: 0,
      fnTeste: 12,
      fpTeste: 0,
      riscoOverfitting: "Inexistente",
      interpretabilidade: "Nula",
      cenarioIdeal: "Piso de acurácia e referência de custo sem alertas (60)",
      matrizConfusao: { tn: 42, fp: 0, fn: 12, tp: 0 }
    },
    persistencia: {
      id: "persistencia",
      nome: "Persistência (y_{t-1})",
      familia: "Baseline Temporal",
      tipoBadge: "Regra Temporal",
      recall: 0.0,
      precisao: 0.0,
      f1: 0.0,
      acuracia: 0.704,
      auc: null,
      custo: 64,
      fnTreino: 18,
      fpTreino: 20,
      fnTeste: 12,
      fpTeste: 4,
      riscoOverfitting: "Inexistente",
      interpretabilidade: "Trivial",
      cenarioIdeal: "Referência de persistência entre safras consecutivas",
      matrizConfusao: { tn: 38, fp: 4, fn: 12, tp: 0 }
    },
    gaussianNb: {
      id: "gaussianNb",
      nome: "Gaussian Naive Bayes (tmax_enchimento)",
      familia: "Probabilístico Bayesiano",
      tipoBadge: "Comparativo Sprint 5",
      recall: 0.75,
      precisao: 0.409,
      f1: 0.529,
      acuracia: 0.704,
      auc: 0.728,
      custo: 28,
      fnTreino: 24,
      fpTreino: 3,
      fnTeste: 3,
      fpTeste: 13,
      riscoOverfitting: "Baixo",
      interpretabilidade: "Média",
      cenarioIdeal: "Sem sinal acima da referência nula na validação do treino (AUC=0,378)",
      matrizConfusao: { tn: 29, fp: 13, fn: 3, tp: 9 }
    },
    logisticRegression: {
      id: "logisticRegression",
      nome: "Regressão Logística L2 (C=1.0, p=0.45)",
      familia: "Linear (índice de risco não calibrado)",
      tipoBadge: "Modelo Ativo (Protótipo Experimental)",
      recall: 0.75,
      precisao: 0.237,
      f1: 0.360,
      acuracia: 0.407,
      auc: 0.728,
      custo: 44,
      fnTreino: 7,
      fpTreino: 44,
      fnTeste: 3,
      fpTeste: 29,
      riscoOverfitting: "Baixo (1 feature, penalidade L2)",
      interpretabilidade: "Alta (corte térmico equivalente >= 28,34 °C)",
      cenarioIdeal: "Índice experimental de risco térmico; não aprovado para decisão operacional (custo 44 > 'alertar sempre' 42)",
      matrizConfusao: { tn: 13, fp: 29, fn: 3, tp: 9 },
      recortesTeste: {
        todos: { n: 54, tn: 13, fp: 29, fn: 3, tp: 9, recall: 0.75, precisao: 0.237, f1: 0.360, acuracia: 0.407, auc: 0.728, custo: 44 },
        sem2024: { n: 45, tn: 13, fp: 28, fn: 3, tp: 1, recall: 0.25, precisao: 0.034, f1: 0.061, acuracia: 0.311, auc: 0.341, custo: 43 },
        sorrisoMt: { n: 6, tn: 2, fp: 2, fn: 0, tp: 2, recall: 1.0, precisao: 0.5, f1: 0.667, acuracia: 0.667, auc: 1.0, custo: 2 }
      },
      backtestExpansivoOOF: { n: 88, tn: 28, fp: 47, fn: 2, tp: 11, acuracia: 0.443, recall: 0.846, precisao: 0.190, f1: 0.310, auc: 0.775, custo: 57 }
    },
    decisionTree: {
      id: "decisionTree",
      nome: "Árvore de Decisão (prof. 2, tmax_enchimento)",
      familia: "Particionamento Binário",
      tipoBadge: "Comparativo Sprint 5",
      recall: 0.75,
      precisao: 0.231,
      f1: 0.353,
      acuracia: 0.389,
      auc: 0.679,
      custo: 45,
      fnTreino: 15,
      fpTreino: 38,
      fnTeste: 3,
      fpTeste: 30,
      riscoOverfitting: "Médio (AUC val=0,402)",
      interpretabilidade: "Alta (regras de corte em temperatura)",
      cenarioIdeal: "Sem sinal estatístico na validação do treino",
      matrizConfusao: { tn: 12, fp: 30, fn: 3, tp: 9 },
      hiperparametros: "max_depth=2, class_weight='balanced'"
    },
    extraTrees: {
      id: "extraTrees",
      nome: "Extra Trees (rasa, 5 sinais, limiar=0.50)",
      familia: "Ensemble de Árvores",
      tipoBadge: "Candidato S7 (Ranking OOF #1 — não promovido)",
      recall: 0.75,
      precisao: 0.237,
      f1: 0.360,
      acuracia: 0.407,
      auc: 0.627,
      custo: 44,
      fnTreino: 3,
      fpTreino: 24,
      fnTeste: 3,
      fpTeste: 29,
      riscoOverfitting: "Moderado em poucas safras (custo teste sem 2024 = 43)",
      interpretabilidade: "Média",
      cenarioIdeal: "Melhor candidato na validação OOF (custo 39, AUC 0,721), mas mesmo custo 44 e AUC menor no teste diagnóstico",
      matrizConfusao: { tn: 13, fp: 29, fn: 3, tp: 9 },
      validacaoOOF: { n: 88, tn: 51, fp: 24, fn: 3, tp: 10, acuracia: 0.693, recall: 0.769, precisao: 0.294, f1: 0.426, auc: 0.721, custo: 39 },
      hiperparametros: "n_estimators=200, max_depth=2, min_samples_leaf=9, class_weight='balanced', threshold=0.50"
    },
    randomForest: {
      id: "randomForest",
      nome: "Random Forest (rasa, 5 sinais, limiar=0.50)",
      familia: "Bagging de Árvores",
      tipoBadge: "Candidato S7 (Ranking OOF #2 — não promovido)",
      recall: 0.75,
      precisao: 0.237,
      f1: 0.360,
      acuracia: 0.407,
      auc: 0.605,
      custo: 44,
      fnTreino: 5,
      fpTreino: 22,
      fnTeste: 3,
      fpTeste: 29,
      riscoOverfitting: "Moderado em poucas safras",
      interpretabilidade: "Média",
      cenarioIdeal: "Candidato exploratório multivariável não promovido",
      matrizConfusao: { tn: 13, fp: 29, fn: 3, tp: 9 },
      validacaoOOF: { n: 88, tn: 53, fp: 22, fn: 5, tp: 8, acuracia: 0.693, recall: 0.615, precisao: 0.267, f1: 0.372, auc: 0.683, custo: 47 },
      hiperparametros: "n_estimators=200, max_depth=2, min_samples_leaf=9, class_weight='balanced_subsample', threshold=0.50"
    },
    arvoreProf2Multi: {
      id: "arvoreProf2Multi",
      nome: "Árvore de Decisão (prof. 2, 5 sinais, limiar=0.50)",
      familia: "Particionamento Binário",
      tipoBadge: "Candidato S7 (Ranking OOF #3)",
      recall: 0.75,
      precisao: 0.237,
      f1: 0.360,
      acuracia: 0.407,
      auc: 0.699,
      custo: 44,
      fnTreino: 5,
      fpTreino: 29,
      fnTeste: 3,
      fpTeste: 29,
      matrizConfusao: { tn: 13, fp: 29, fn: 3, tp: 9 },
      validacaoOOF: { n: 88, tn: 46, fp: 29, fn: 5, tp: 8, acuracia: 0.614, recall: 0.615, precisao: 0.216, f1: 0.320, auc: 0.472, custo: 54 }
    },
    arvoreProf1Multi: {
      id: "arvoreProf1Multi",
      nome: "Árvore de Decisão (prof. 1, 5 sinais, limiar=0.50)",
      familia: "Particionamento Binário",
      tipoBadge: "Candidato S7 (Ranking OOF #4)",
      recall: 0.75,
      precisao: 0.237,
      f1: 0.360,
      acuracia: 0.407,
      auc: 0.530,
      custo: 44,
      fnTreino: 2,
      fpTreino: 46,
      fnTeste: 3,
      fpTeste: 29,
      matrizConfusao: { tn: 13, fp: 29, fn: 3, tp: 9 },
      validacaoOOF: { n: 88, tn: 29, fp: 46, fn: 2, tp: 11, acuracia: 0.455, recall: 0.846, precisao: 0.193, f1: 0.314, auc: 0.683, custo: 56 }
    },
    svcRbf: {
      id: "svcRbf",
      nome: "SVC RBF balanceado (5 sinais, limiar=0.50)",
      familia: "Máquina de Vetores de Suporte",
      tipoBadge: "Candidato S7 (Ranking OOF #5)",
      recall: 0.0,
      precisao: 0.0,
      f1: 0.0,
      acuracia: 0.778,
      auc: 0.325,
      custo: 60,
      fnTreino: 13,
      fpTreino: 0,
      fnTeste: 12,
      fpTeste: 0,
      matrizConfusao: { tn: 42, fp: 0, fn: 12, tp: 0 },
      validacaoOOF: { n: 88, tn: 75, fp: 0, fn: 13, tp: 0, acuracia: 0.852, recall: 0.0, precisao: 0.0, f1: 0.0, auc: 0.277, custo: 65 }
    },
    lda: {
      id: "lda",
      nome: "LDA (5 sinais, limiar=0.50)",
      familia: "Análise Discriminante Linear",
      tipoBadge: "Candidato S7 (Ranking OOF #6)",
      recall: 0.75,
      precisao: 0.429,
      f1: 0.545,
      acuracia: 0.722,
      auc: 0.778,
      custo: 27,
      fnTreino: 13,
      fpTreino: 3,
      fnTeste: 3,
      fpTeste: 12,
      matrizConfusao: { tn: 30, fp: 12, fn: 3, tp: 9 },
      validacaoOOF: { n: 88, tn: 72, fp: 3, fn: 13, tp: 0, acuracia: 0.818, recall: 0.0, precisao: 0.0, f1: 0.0, auc: 0.374, custo: 68 }
    },
    gaussianNbMulti: {
      id: "gaussianNbMulti",
      nome: "GaussianNB (5 sinais, limiar=0.50)",
      familia: "Probabilístico Bayesiano",
      tipoBadge: "Candidato S7 (Ranking OOF #7)",
      recall: 0.75,
      precisao: 0.360,
      f1: 0.486,
      acuracia: 0.648,
      auc: 0.700,
      custo: 31,
      fnTreino: 12,
      fpTreino: 8,
      fnTeste: 3,
      fpTeste: 16,
      matrizConfusao: { tn: 26, fp: 16, fn: 3, tp: 9 },
      validacaoOOF: { n: 88, tn: 67, fp: 8, fn: 12, tp: 1, acuracia: 0.773, recall: 0.077, precisao: 0.111, f1: 0.091, auc: 0.350, custo: 68 }
    },
    knn: {
      id: "knn",
      nome: "KNN (k=7, 5 sinais, limiar=0.50)",
      familia: "Baseado em Vizinhos",
      tipoBadge: "Candidato S7 (Ranking OOF #8)",
      recall: 0.583,
      precisao: 0.333,
      f1: 0.424,
      acuracia: 0.648,
      auc: 0.604,
      custo: 39,
      fnTreino: 13,
      fpTreino: 4,
      fnTeste: 5,
      fpTeste: 14,
      matrizConfusao: { tn: 28, fp: 14, fn: 5, tp: 7 },
      validacaoOOF: { n: 88, tn: 71, fp: 4, fn: 13, tp: 0, acuracia: 0.807, recall: 0.0, precisao: 0.0, f1: 0.0, auc: 0.557, custo: 69 }
    },
    logRegMulti: {
      id: "logRegMulti",
      nome: "LogReg L2 balanceada (5 sinais, limiar=0.50)",
      familia: "Linear",
      tipoBadge: "Candidato S7 (Ranking OOF #9)",
      recall: 0.75,
      precisao: 0.237,
      f1: 0.360,
      acuracia: 0.407,
      auc: 0.778,
      custo: 44,
      fnTreino: 9,
      fpTreino: 25,
      fnTeste: 3,
      fpTeste: 29,
      matrizConfusao: { tn: 13, fp: 29, fn: 3, tp: 9 },
      validacaoOOF: { n: 88, tn: 50, fp: 25, fn: 9, tp: 4, acuracia: 0.614, recall: 0.308, precisao: 0.138, f1: 0.190, auc: 0.402, custo: 70 }
    }
  },

  // Modelo ativo: única variável padronizada
  featureImportance: [
    { feature: "tmax_enchimento", nome: "Temperatura máxima média no enchimento", peso: 1.0, correlacao: "AUC 0,728 no teste", unidade: "°C, média diária de dezembro a fevereiro" }
  ],

  /**
   * Calcula o índice de risco do pipeline oficial (models/pipeline_final.joblib):
   * StandardScaler + LogisticRegression(C=1.0, class_weight="balanced") em tmax_enchimento.
   *
   * IMPORTANTE: A saída é um índice de risco não calibrado (class_weight="balanced" infla os valores),
   * NÃO uma probabilidade real de quebra. Corte congelado: índice >= 0,45 (tmax >= 28,34 °C).
   */
  preverRisco: function(tmaxEnchimento) {
    const tmax = Number(tmaxEnchimento);
    const meanTreino = 28.458829183698764;
    const stdTreino = 1.040458233262264;
    const coef = 0.6333948141;
    const intercept = -0.1304474707;
    const z = coef * ((tmax - meanTreino) / stdTreino) + intercept;
    const indiceRisco = 1 / (1 + Math.exp(-z));
    const alerta = indiceRisco >= 0.45;
    const caminho = [
      `Entrada: tmax_enchimento = ${tmax.toFixed(2)} °C`,
      `Padronização (treino 2001–2018): (${tmax.toFixed(2)} - ${meanTreino.toFixed(2)}) / ${stdTreino.toFixed(2)}`,
      `Índice de risco (não calibrado): ${(indiceRisco * 100).toFixed(1)}% (limiar: 45,0% ≈ 28,34 °C)`,
      alerta ? "Resultado: ALERTA de risco por calor" : "Resultado: sem alerta térmico pelo limiar atual"
    ];
    return {
      alerta: alerta,
      indiceRisco: indiceRisco,
      probabilidade: indiceRisco,
      limiar: 0.45,
      limiarCelsius: 28.34,
      naoCalibrado: true,
      nota: "Índice de risco por calor (class_weight='balanced' infla as probabilidades; não é a chance real de quebra).",
      caminho: caminho,
      modelo: "LogisticRegression L2 (C=1.0, class_weight=balanced)"
    };
  }
};
