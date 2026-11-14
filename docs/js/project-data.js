/**
 * ==============================================================================
 * Camada Centralizada de Dados do Projeto - Previsão de Produtividade Agrícola
 * ==============================================================================
 * 
 * Dados oficiais consolidados da Sprint 5 (Sorriso-MT, N=10 safras consolidadas:
 * 2015-2022 treino com 3 quebras severas, 2023-2024 teste cego com 2 safras normais).
 */

window.PROJECT_DATA = {
  // Metadados Gerais do Experimento
  metadata: {
    municipio: "Sorriso - MT",
    codigo_ibge: "5107925",
    cultura: "Soja em Grão",
    media_historica_kg_ha: 3477.0,
    limiar_quebra_kg_ha: 3400.0,
    amostra_total: 10,
    treino_anos: "2015 a 2022 (8 safras)",
    teste_anos: "2023 a 2024 (2 safras)",
    split_estrategia: "Temporal sem vazamento (80% treino antigo / 20% teste recente)",
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
    { modelo: "DummyClassifier", recallS3: 0.0, recallS4: 0.0, f1S3: 0.0, f1S4: 0.0, deltaRecall: "+0.00", status: "Inerte ao evento raro" },
    { modelo: "Persistência", recallS3: 0.0, recallS4: 0.0, f1S3: 0.0, f1S4: 0.0, deltaRecall: "+0.00", status: "Falha nas transições de quebra" },
    { modelo: "GaussianNB", recallS3: 0.67, recallS4: 1.00, f1S3: 0.57, f1S4: 0.86, deltaRecall: "+0.33", status: "Capturou Safra 2021 (Eliminou FN)" }
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
      nome: "Regressão Logística (L2, p=0.35)",
      familia: "Linear Probabilístico Calibrado",
      tipoBadge: "Co-Campeão Linear",
      recall: 1.0,
      precisao: 0.50,
      f1: 0.67,
      acuracia: 1.0,
      fnTreino: 0,
      fpTreino: 0,
      fnTeste: 0,
      fpTeste: 0,
      tempoTreinoMs: 5.33,
      tempoPredicaoMs: 3.87,
      riscoOverfitting: "Muito Baixo (penalidade L2)",
      interpretabilidade: "Alta (Pesos Lineares)",
      cenarioIdeal: "Calibração contínua de probabilidade em amostras pequenas",
      matrizConfusao: { tn: 2, fp: 0, fn: 0, tp: 0 }
    },
    decisionTree: {
      id: "decisionTree",
      nome: "Árvore de Decisão Rasa",
      familia: "Particionamento Binário",
      tipoBadge: "Melhor Modelo (Vencedor)",
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

  // Importância Relativa dos Atributos Preditores (Random Forest Ensemble + Correlação)
  featureImportance: [
    { feature: "deficit_hidrico_solo", nome: "Déficit Hídrico no Solo (Jan-Fev)", peso: 0.49, correlacao: "+0.90", unidade: "dias com GWETROOT < 0.70" },
    { feature: "dias_pico_calor", nome: "Picos de Calor Extremo (Jan-Fev)", peso: 0.18, correlacao: "+0.74", unidade: "dias com T2M_MAX >= 35°C" },
    { feature: "precipitacao_enchimento", nome: "Chuva no Enchimento de Grãos", peso: 0.18, correlacao: "-0.55", unidade: "milímetros acumulados (mm)" },
    { feature: "amplitude_termica", nome: "Amplitude Térmica Média", peso: 0.15, correlacao: "+0.41", unidade: "variação diária em °C" }
  ],

  // Função utilitária de simulação local da Árvore de Decisão
  preverRisco: function(deficit, picoCalor, precEnchimento, ampTermica) {
    let probabilidade = 0.05;
    let caminho = [];
    let alerta = false;

    caminho.push("Nó Raiz: Avaliando Déficit Hídrico no Solo em Jan-Fev (corte: 21,5 dias)...");
    if (deficit > 21.5) {
      caminho.push(`Déficit Hídrico (${deficit} dias) > 21,5 dias → Ramo de Estresse Hídrico`);
      if (picoCalor >= 2.5 || deficit >= 28.0) {
        caminho.push(`Pico de Calor (${picoCalor} dias) ou Déficit Crítico (${deficit} >= 28) → Nó Folha de Quebra (Gini = 0.0)`);
        probabilidade = 0.95;
        alerta = true;
      } else {
        caminho.push(`Calor moderado (${picoCalor} dias) e déficit intermediário → Nó Folha Limítrofe`);
        probabilidade = 0.45;
        alerta = false;
      }
    } else {
      caminho.push(`Déficit Hídrico (${deficit} dias) <= 21,5 dias → Solo com umidade adequada`);
      if (precEnchimento < 200.0 && ampTermica > 28.0) {
        caminho.push(`Chuva de enchimento baixa (${precEnchimento} mm) com amplitude alta → Alerta preventivo`);
        probabilidade = 0.52;
        alerta = true;
      } else {
        caminho.push(`Precipitação favorável (${precEnchimento} mm) → Nó Folha Safra Normal (Gini = 0.0)`);
        probabilidade = 0.05;
        alerta = false;
      }
    }

    return {
      alerta: alerta,
      probabilidade: probabilidade,
      caminho: caminho,
      modelo: "DecisionTreeClassifier (Parcimonioso - max_depth=2)"
    };
  }
};
