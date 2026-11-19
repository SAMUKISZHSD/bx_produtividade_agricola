# Model Card - Alerta de Risco de Quebra de Safra de Soja por Calor no Enchimento de Grãos

**Status:** protótipo experimental (não aprovado para decisão operacional)

## 1. Detalhes do modelo
- **Modelo:** regressão logística L2 (`C=1.0`, `class_weight="balanced"`) sobre uma única variável padronizada, `tmax_enchimento`.
- **Regra de alerta:** alerta se tmax_enchimento (média da tmax diária dez-fev) >= 28.34 °C (probabilidade ≥ 0.45).
- **Versão:** 1.0 (Sprint 5). Artefatos: `models/modelo_final.joblib` e `models/modelo_final_metadados.json`.
- **Desenvolvedores:** Grupo 3 (João Guilherme Cravo, Jean Carlos Silva de Almeida, Samuel Allan Nunes da Cunha).

## 2. Uso pretendido
- **Pergunta respondida:** "o enchimento de grãos desta safra (dez-fev) foi quente o bastante para indicar risco elevado de quebra?"
- **Local de uso:** Sorriso-MT (IBGE 5107925); o modelo foi treinado com a microrregião do Alto Teles Pires.
- **Momento:** março (após o fim do enchimento, antes da colheita). Serve para antecipar a gestão de caixa, a comercialização e a comunicação com o seguro. Não serve para manejo da lavoura, porque o enchimento já terminou.
- **Fora do escopo:**
  - quebras por **chuva em excesso ou doença** (por exemplo, 2004, 2006, 2014 e 2022), que o modelo não detecta;
  - outras culturas e regiões;
  - previsão do rendimento em kg/ha.

## 3. Dados
- **Unidade:** município × safra. Municípios: Ipiranga do Norte, Itanhangá, Lucas do Rio Verde, Nobres, Nova Mutum, Nova Ubiratã, Santa Rita do Trivelato, Sorriso, Tapurah.
- **Clima:** NASA POWER (diário). **Rendimento:** IBGE/PAM.
- **Alvo:** quebra = rendimento < 0,92 × tendência linear das até 10 safras anteriores do município (mínimo 5, só passado).
- **Treino:** safras 2001-2018, com 138 linhas e 24 quebras (17%). Quebras de Sorriso: 2002, 2003, 2006, 2016.
- **Teste:** safras 2019-2024, com 54 linhas e 12 quebras (22%). Quebras de Sorriso: 2021, 2024.
- **Seleção de features:** feita no 08 com validação deixando uma safra de fora. Nenhuma família de features passou da referência nula; só `tmax_enchimento` teve sinal.

## 4. Desempenho
| Conjunto | Recall | Precisão | % alertas | % real | Custo (5×FN+FP) | AUC |
|---|---|---|---|---|---|---|
| Validação (treino, uma safra de fora) | 0.71 | 0.28 | 44% | 17% | 79 | 0.65 (p95 nulo 0.60) |
| Teste 2019-2024 | 0.75 | 0.24 | 70% | 22% | 44 (nunca: 60; sempre: 42) | 0.73 (IC 90% 0.24-0.96) |
| Teste sem 2024 | 0.25 | 0.03 | 64% | 9% | 43 (nunca: 20; sempre: 41) | 0.34 |
| Teste, só Sorriso-MT | 1.00 | 0.50 | 67% | 33% | 2 (nunca: 10; sempre: 4) | - |

**Critério de aprovação:** custo menor que "nunca alertar" e que "alertar sempre", no teste e no teste sem 2024. Resultado: **não cumprido**.

## 5. Limitações e cautelas
- **Poucas safras independentes:** são 18 no treino e 6 no teste. Os municípios de uma mesma safra compartilham o clima, então o tamanho efetivo da amostra é o número de safras.
- **O sinal vem de poucas safras:** sem 2016, a AUC de validação cai para 0,56; sem 2016 e 2013, cai para 0,49. **2015** foi quente sem quebra (contraexemplo).
- **Deriva climática:** o teste foi mais quente (29.88 °C contra 28.46 °C no treino). Com um limiar absoluto, o alerta dispara em 70% das linhas, e a maior parte são falsos alarmes em 2019 e 2020. Se o aquecimento continuar, o alerta tende a perder especificidade.
- **Probabilidade não calibrada:** índice de risco: class_weight='balanced' infla as probabilidades; não é a chance real de quebra. Comunicar como índice de risco por calor, não como "X% de chance".
- **Um só mecanismo:** cobre só calor/seca no enchimento. Um alerta negativo **não** significa safra segura.
- **Limiar incerto:** o IC 90% do bootstrap vai de 25.06 a 30.1 °C.

## 6. Fatores éticos e de negócio
- **Falso alarme versus quebra silenciosa:** o limiar foi escolhido com custo de quebra não detectada = 5 × falso alarme. Mudar essa razão para entre 4 e 8 mantém o limiar; com razão 3, ele iria para cerca de 28,7 °C.
- **Uso em crédito ou seguro:** não usar o alerta, sozinho, para negar crédito ou seguro. A taxa de falsos alarmes em anos quentes é alta.
- **Manutenção:** reavaliar a cada safra. Se a % de alertas ficar muito acima da % de quebras por várias safras, rever o limiar (por exemplo, um limiar relativo ao histórico do município) ou reajustar o modelo com as safras recentes.

## 7. Experimento multivariável (candidato, não implantado)

Foram comparadas versões usando sinais derivados dos dados diários NASA POWER: dias com déficit hídrico (`GWETROOT < 0,70`), dias com temperatura máxima de pelo menos 35 °C, precipitação acumulada no período e maior sequência sem chuva relevante (`PRECTOTCORR < 1 mm`). A nova regressão logística inclui também `tmax_enchimento` como quinta feature. O alvo regional e o teste temporal congelado (2019–2024) foram mantidos. A validação usou janelas expansivas, treinando apenas com safras anteriores; o limiar candidato (0,6547) foi escolhido com os resultados OOF do treino, sem usar o teste.

| Modelo | Custo validação expansiva (5×FN+FP) | Acurácia teste | Recall teste | Precisão teste | AUC teste | Custo teste | Custo teste sem 2024 |
|---|---:|---:|---:|---:|---:|---:|---:|
| Ativo: LogReg, `tmax_enchimento` | 25 | 40,7% | 75% | 23,7% | 0,728 | 44 | 43 |
| LogReg multivariável | 62 | 59,3% | 75% | 32,1% | 0,758 | 34 | 33 |
| GaussianNB multivariável | 63 | 70,4% | 75% | 40,9% | 0,710 | 28 | 27 |
| Árvore, profundidade 1 | 45 | 35,2% | 75% | 22,0% | 0,494 | 47 | 46 |
| Árvore, profundidade 2 | 52 | 57,4% | 50% | 26,1% | 0,542 | 47 | 36 |
| LogReg multivariável, incluindo Tmax (5 sinais) | 61 | 63,0% | 75% | 34,6% | 0,778 | 32 | 31 |

O candidato de cinco sinais melhora o teste completo em relação ao ativo (custo 32 vs. 44; AUC 0,778 vs. 0,728), mas não atende aos critérios para promoção: o custo na validação expansiva é 61, contra 25 do atual; sem 2024, o custo 31 ainda supera o baseline "nunca alertar" (20), e o recall permanece em 25%. A GaussianNB multivariável tem custo 28 no teste completo, porém custo 63 na validação e 27 sem 2024. A LogReg multivariável de quatro sinais também não supera o baseline sem 2024 (custo 33). O modelo ativo tampouco é aprovado para uso operacional: seu custo no teste completo (44) supera "alertar sempre" (42), e sem 2024 (43) supera ambos os baselines (20 e 41). Portanto, nenhum candidato multivariável foi promovido; os artefatos ativos e o dashboard continuam usando somente `tmax_enchimento`.

As safras difíceis continuam relevantes: 2021 e 2022 têm poucos exemplos positivos, enquanto 2024 concentra oito quebras no conjunto de teste. A melhora agregada obtida incluindo 2024 não demonstra generalização para novas safras. Consulte `models/s6_comparacao_multivariavel.csv` e `models/s6_metricas_por_safra.csv` para as métricas completas e os erros por safra.

## 8. Backtest do modelo ativo

O notebook [`14_backtest_regressao_logistica.ipynb`](../notebooks/14_backtest_regressao_logistica.ipynb) mostra a função sigmoide do artefato ativo, refaz o ajuste em janelas expansivas usando somente safras anteriores (mínimo de oito) e analisa o teste congelado 2019–2024, incluindo gráficos e identificação de falsos positivos/negativos. No backtest histórico, os parâmetros do classificador são refeitos por origem; o limiar de 0,45 é mantido congelado. Como esse limiar foi selecionado usando validação do período de treino como um todo, o backtest é diagnóstico e não uma avaliação de política totalmente aninhada. O teste 2019–2024 segue como a avaliação temporal principal, sem ajuste com seus resultados.

## 9. Comparação de outros classificadores nas cinco variáveis

Foi feita uma comparação temporal de nove algoritmos, todos com `tmax_enchimento`, déficit hídrico, dias acima de 35 °C, precipitação acumulada e maior veranico. Para comparar os candidatos sem ajustar corte nos mesmos resultados usados para pontuar, todos usaram limiar fixo 0,50. A seleção foi ordenada por custo OOF expansivo (5×FN+FP), depois AUC e recall. As 88 previsões OOF cobrem safras de validação 2009–2018; o teste 2019–2024 foi calculado apenas como diagnóstico e não participou do ranking.

| Ranking OOF | Candidato | Custo OOF | AUC OOF | Recall OOF | Precisão OOF | Custo teste diagnóstico | AUC teste diagnóstico | Custo sem 2024 |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | Extra Trees raso | 39 | 0,721 | 76,9% | 29,4% | 44 | 0,627 | 43 |
| 2 | Random Forest raso | 47 | 0,683 | 61,5% | 26,7% | 44 | 0,605 | 43 |
| 3 | Árvore, profundidade 2 | 54 | 0,472 | 61,5% | 21,6% | 44 | 0,699 | 43 |
| 4 | Árvore, profundidade 1 | 56 | 0,683 | 84,6% | 19,3% | 44 | 0,530 | 43 |
| 5 | SVC RBF balanceado | 65 | 0,277 | 0% | 0% | 60 | 0,325 | 20 |
| 6 | LDA | 68 | 0,374 | 0% | 0% | 27 | 0,778 | 26 |
| 7 | GaussianNB | 68 | 0,350 | 7,7% | 11,1% | 31 | 0,700 | 30 |
| 8 | KNN (k=7) | 69 | 0,557 | 0% | 0% | 39 | 0,604 | 33 |
| 9 | LogReg L2 balanceada | 70 | 0,402 | 30,8% | 13,8% | 44 | 0,778 | 43 |

O melhor candidato **dentro deste protocolo** é Extra Trees raso, mas isso não basta para substituir o atual: no teste diagnóstico teve o mesmo custo e a mesma matriz binária do modelo ativo, AUC inferior (0,627 vs. 0,728), e custo 43 sem 2024. O limiar do modelo ativo é o oficial 0,45, enquanto os candidatos usam 0,50; logo, o custo OOF 39 vs. 57 não é uma comparação perfeitamente isolada do algoritmo. Ainda assim, o ranking entre os nove candidatos é justo sob o corte comum. Nenhuma escolha baseada nos números do teste é válida aqui: houve avaliação de múltiplas alternativas e há somente seis safras de teste, com 2024 concentrando oito quebras. **Nenhum modelo novo foi promovido; `pipeline_final.joblib`, o limiar e o dashboard permanecem inalterados.**

O código e as saídas reproduzíveis estão em `src/comparacao_modelos_multivariaveis.py` e `models/s7_*.csv`. Os resultados por safra e as previsões OOF permitem inspecionar quais anos movem o ranking.
