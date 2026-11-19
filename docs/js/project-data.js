/**
 * ==============================================================================
 * Camada Centralizada de Dados do Projeto - Previsão de Produtividade Agrícola
 * ==============================================================================
 * 
 * Fonte atual: notebooks 08-13 e Model Card Sprint 5.
 * Unidade: municipio x safra; regioes do Alto Teles Pires.
 */

window.PROJECT_DATA = {
  // Metadados Gerais do Experimento
  metadata: {
    municipio: "Sorriso - MT",
    codigo_ibge: "5107925",
    cultura: "Soja em Grão",
    unidade: "municipio x safra",
    amostra_total: 192,
    municipios: 9,
    treino_anos: "2001 a 2018",
    teste_anos: "2019 a 2024",
    split_estrategia: "Temporal",
    feature: "tmax_enchimento",
    limiar_probabilidade: 0.45,
    limiar_celsius: 28.34,
    is_mock: false,
    tag_status: "Dados Oficiais Consolidados (Sprint 5)"
  },

  // Série Histórica Consolidada (10 Safras)
  historico: [
    { ano: 2015, split: "Treino", deficit_hidrico_solo: 47, dias_pico_calor: 0, amplitude_termica: 24.48, precipitacao_enchimento: 159.28, rendimento_real: 3148, quebra_real: 1, rotulo: "Quebra" },
    { ano: 2016, split: "Treino", deficit_hidrico_solo: 28, dias_pico_calor: 4, amplitude_termica: 23.79, precipitacao_enchimento: 257.40, rendimento_real: 2880, quebra_real: 1, rotulo: "Quebra" },
    { ano: 2017, split: "Treino", deficit_hidrico_solo: 0,  dias_pico_calor: 0, amplitude_termica: 27.62, precipitacao_enchimento: 425.38, rendimento_real: 3520, quebra_real: 0, rotulo: "Normal" },
    { ano: 2018, split: "Treino", deficit_hidrico_solo: 0,  dias_pico_calor: 0, amplitude_termica: 26.29, precipitacao_enchimento: 724.46, rendimento_real: 3870, quebra_real: 0, rotulo: "Normal" },
    { ano: 2019, split: "Treino (Val.)", deficit_hidrico_solo: 15, dias_pico_calor: 0, amplitude_termica: 25.44, precipitacao_enchimento: 382.11, rendimento_real: 3480, quebra_real: 0, rotulo: "Normal" },
    { ano: 2020, split: "Treino (Val.)", deficit_hidrico_solo: 15, dias_pico_calor: 0, amplitude_termica: 27.58, precipitacao_enchimento: 299.01, rendimento_real: 3490, quebra_real: 0, rotulo: "Normal" },
    { ano: 2021, split: "Treino (Val.)", deficit_hidrico_solo: 42, dias_pico_calor: 3, amplitude_termica: 28.69, precipitacao_enchimento: 418.57, rendimento_real: 3360, quebra_real: 1, rotulo: "Quebra" },
    { ano: 2022, split: "Treino (Val.)", deficit_hidrico_solo: 0,  dias_pico_calor: 0, amplitude_termica: 30.48, precipitacao_enchimento: 463.11, rendimento_real: 3610, quebra_real: 0, rotulo: "Normal" },
    { ano: 2023, split: "Teste Cego", deficit_hidrico_solo: 0,  dias_pico_calor: 0, amplitude_termica: 27.11, precipitacao_enchimento: 476.27, rendimento_real: 3580, quebra_real: 0, rotulo: "Normal" },
    { ano: 2024, split: "Teste Cego", deficit_hidrico_solo: 4,  dias_pico_calor: 0, amplitude_termica: 27.50, precipitacao_enchimento: 556.25, rendimento_real: 3560, quebra_real: 0, rotulo: "Normal" }
  ],

  // Tabela de Lift de Engenharia de Atributos (Sprint 3 -> Sprint 4)
  liftS3S4: [
    { modelo: "Seleção de famílias", recallS3: null, recallS4: 0.71, f1S3: null, f1S4: 0.40, deltaRecall: "Modelo atual", status: "Nenhuma família superou a referência nula; tmax_enchimento manteve sinal" }
  ],

  // Métricas Consolidadas dos Modelos (Sprint 5 Oficial)
  modelos: {
    dummy: {
      id: "dummy",
      nome: "DummyClassifier",
      familia: "Baseline Ingênuo",
      tipoBadge: "Piso de Acurácia",
      recall: 0.0,
      precisao: 0.0,
      f1: 0.0,
      acuracia: 1.0,
      fnTreino: 3,
      fpTreino: 0,
      fnTeste: 0,
      fpTeste: 0,
      tempoTreinoMs: 4.24,
      tempoPredicaoMs: 5.19,
      riscoOverfitting: "Inexistente",
      interpretabilidade: "Nula",
      cenarioIdeal: "Sanity check inicial do pipeline",
      matrizConfusao: { tn: 2, fp: 0, fn: 0, tp: 0 }
    },
    persistencia: {
      id: "persistencia",
      nome: "Persistência (y_{t-1})",
      familia: "Baseline Temporal",
      tipoBadge: "Regra Temporal",
      recall: 0.0,
      precisao: 0.0,
      f1: 0.0,
      acuracia: 1.0,
      fnTreino: 2,
      fpTreino: 2,
      fnTeste: 0,
      fpTeste: 0,
      tempoTreinoMs: 0.38,
      tempoPredicaoMs: 0.72,
      riscoOverfitting: "Inexistente",
      interpretabilidade: "Trivial",
      cenarioIdeal: "Séries com alta autocorrelação",
      matrizConfusao: { tn: 2, fp: 0, fn: 0, tp: 0 }
    },
    gaussianNb: {
      id: "gaussianNb",
      nome: "Gaussian Naive Bayes",
      familia: "Probabilístico Bayesiano",
      tipoBadge: "Baseline Estatístico",
      recall: 1.0,
      precisao: 0.50,
      f1: 0.67,
      acuracia: 1.0,
      fnTreino: 0,
      fpTreino: 0,
      fnTeste: 0,
      fpTeste: 0,
      tempoTreinoMs: 4.25,
      tempoPredicaoMs: 4.07,
      riscoOverfitting: "Baixo",
      interpretabilidade: "Média",
      cenarioIdeal: "Linha de base inicial sob premissa de independência",
      matrizConfusao: { tn: 2, fp: 0, fn: 0, tp: 0 }
    },
    logisticRegression: {
      id: "logisticRegression",
      nome: "Regressão Logística (L2, p=0.45)",
      familia: "Linear Probabilístico Calibrado",
      tipoBadge: "Modelo Campeão",
      recall: 0.75,
      precisao: 0.24,
      f1: 0.36,
      acuracia: null,
      fnTreino: 0,
      fpTreino: 0,
      fnTeste: 0,
      fpTeste: 0,
      tempoTreinoMs: 5.33,
      tempoPredicaoMs: 3.87,
      riscoOverfitting: "Muito Baixo (penalidade L2)",
      interpretabilidade: "Alta (Pesos Lineares)",
      cenarioIdeal: "Calibração contínua de probabilidade em amostras pequenas",
      matrizConfusao: { tn: 12, fp: 30, fn: 3, tp: 9 }
    },
    decisionTree: {
      id: "decisionTree",
      nome: "Árvore de Decisão (não campeã)",
      familia: "Particionamento Binário",
      tipoBadge: "Modelo histórico",
      recall: 1.0,
      precisao: 0.50,
      f1: 0.67,
      acuracia: 1.0,
      fnTreino: 0,
      fpTreino: 0,
      fnTeste: 0,
      fpTeste: 0,
      tempoTreinoMs: 4.33,
      tempoPredicaoMs: 4.72,
      riscoOverfitting: "Médio (controlado com max_depth=2)",
      interpretabilidade: "Máxima (Fluxograma Lógico Direto)",
      cenarioIdeal: "Decisões agronômicas auditáveis e N pequeno",
      matrizConfusao: { tn: 2, fp: 0, fn: 0, tp: 0 },
      hiperparametros: "criterion='gini', max_depth=2, class_weight='balanced', threshold=0.50"
    },
    randomForest: {
      id: "randomForest",
      nome: "Random Forest",
      familia: "Bagging (Bootstrap Aggregating)",
      tipoBadge: "Ensemble Paralelo",
      recall: 0.0,
      precisao: 0.0,
      f1: 0.0,
      acuracia: 1.0,
      fnTreino: 0,
      fpTreino: 0,
      fnTeste: 0,
      fpTeste: 0,
      tempoTreinoMs: 124.95,
      tempoPredicaoMs: 17.52,
      riscoOverfitting: "Diluição por bootstrap em N=6 (P(2021)=0.39)",
      interpretabilidade: "Média (Feature Importance agregada)",
      cenarioIdeal: "Bases tabulares médias/grandes com ruído",
      matrizConfusao: { tn: 2, fp: 0, fn: 0, tp: 0 },
      hiperparametros: "n_estimators=100, max_depth=2, class_weight='balanced'"
    },
    xgboost: {
      id: "xgboost",
      nome: "XGBoost",
      familia: "Gradient Boosting",
      tipoBadge: "Ensemble Sequencial",
      recall: 0.0,
      precisao: 0.0,
      f1: 0.0,
      acuracia: 1.0,
      fnTreino: 0,
      fpTreino: 0,
      fnTeste: 0,
      fpTeste: 0,
      tempoTreinoMs: 16.07,
      tempoPredicaoMs: 7.40,
      riscoOverfitting: "Alto em N reduzido (P(2021)=0.454 no backtest)",
      interpretabilidade: "Baixa (soma ponderada de árvores de resíduo)",
      cenarioIdeal: "Grandes volumes de dados complexos e heterogêneos",
      matrizConfusao: { tn: 2, fp: 0, fn: 0, tp: 0 },
      hiperparametros: "n_estimators=50, max_depth=2, learning_rate=0.1, scale_pos_weight=1.67"
    }
  },

  // Modelo final: uma feature padronizada
  featureImportance: [
    { feature: "tmax_enchimento", nome: "Temperatura máxima média no enchimento", peso: 1.0, correlacao: "AUC 0,73 no teste", unidade: "°C, média diária de dezembro a fevereiro" }
  ],

  // Simulação ilustrativa; o limiar oficial corresponde a 28,34 °C.
  preverRisco: function(tmaxEnchimento, picoCalor, precEnchimento, ampTermica) {
    const z = (tmaxEnchimento - 28.34) / 1.0;
    const probabilidade = 1 / (1 + Math.exp(-z));
    const alerta = tmaxEnchimento >= 28.34;
    const caminho = [
      `Entrada: tmax_enchimento = ${tmaxEnchimento} °C`,
      `Regra: alerta se ${tmaxEnchimento} >= 28,34 °C`,
      alerta ? "Resultado: alerta de risco por calor" : "Resultado: sem alerta pelo limiar atual"
    ];
    return {
      alerta: alerta,
      probabilidade: probabilidade,
      caminho: caminho,
      modelo: "LogisticRegression L2 (C=1.0, class_weight=balanced)"
    };
  }
};
