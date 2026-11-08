# Model Card — Alerta de Risco de Baixa Produtividade Agrícola (Soja)

## 1. Detalhes do Modelo
- **Nome:** Classificador Logístico Regularizado L2 para Previsão de Quebra de Safra
- **Versão:** 1.0
- **Tipo:** Modelo linear probabilístico supervisionado (`LogisticRegression` com penalidade L2, $C=1.0$ e `class_weight=balanced`)
- **Data de Treinamento:** Outubro/2026
- **Desenvolvedores:** Grupo 3 (Jean Carlos Silva de Almeida, João Guilherme Cravo, Samuel Allan Nunes da Cunha)
- **Pipeline Pré-processador:** `ColumnTransformer` congelado na Sprint 4 (`StandardScaler` nas 4 variáveis intra-safra)

## 2. Uso Pretendido e Escopo
- **Aplicação Principal:** Apoiar cooperativas agropecuárias, corretores de seguro rural e produtores de Sorriso-MT na tomada de decisão preventiva até 28 de fevereiro.
- **Decisão Apoiada:** Contratação antecipada de seguros, ajuste de pulverização/adubação suplementar e gestão de caixa.
- **Fora do Escopo:** Não deve ser extrapolado para outros biomas/culturas (ex.: milho, algodão) sem retreino e recalibração agronômica local.

## 3. Dados de Treinamento e Teste
- **Recorte Geográfico:** Sorriso - MT (Código IBGE 5107925).
- **Dados de Treino:** 8 safras anuais consolidadas (2015 a 2022), com 3 eventos de quebra (< 3.400 kg/ha) e 5 safras normais.
- **Dados de Teste:** 2 safras anuais consolidadas (2023 a 2024), ambas normais.
- **Features Utilizadas:** `deficit_hidrico_solo` (dias com solo seco em Jan-Fev), `dias_pico_calor` (dias com Tmax >= 35°C em Jan-Fev), `precipitacao_enchimento` (chuva em Jan-Fev) e `amplitude_termica`.

## 4. Métricas e Desempenho
- **Limiar de Decisão Calibrado:** $p = 0.35$ (ajustado para priorizar o Falso Negativo, de alto custo ao produtor).
- **Recall na Validação Temporal:** 100% (1 de 1 evento de quebra detectado na safra de 2021).
- **F1-Score na Validação:** 0,67.
- **Desempenho no Teste Oficial (2023–2024):** 100% de acurácia, com 0 falsos alarmes (Especificidade = 100%).

## 5. Limitações e Fatores Éticos/Negócio
- **Tamanho Amostral Restrito ($N=10$):** O reduzido número de safras municipais impõe cautela contra sobreajuste e exige modelos parcimoniosos.
- **Alarme Falso vs Quebra Silenciosa:** O limiar calibrado (0.35) aceita uma taxa moderada de falsos alarmes para garantir que nenhuma quebra de safra passe desapercebida.
