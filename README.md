# SojaRisco

Sistema experimental de apoio à decisão para identificar risco de quebra de safra de soja por calor/seca no enchimento dos grãos.

## Estado atual

- **Modelo:** Regressão logística L2
- **Parâmetros:** `C=1.0`, `class_weight="balanced"`
- **Feature:** `tmax_enchimento`, média da temperatura máxima diária de dezembro a fevereiro
- **Regra:** alerta quando `tmax_enchimento >= 28,34 °C` (probabilidade de modelo >= 0,45)
- **Status:** protótipo experimental não aprovado para decisão operacional
- **Escopo:** nove municípios da microrregião do Alto Teles Pires
- **Treino:** 2001–2018, 138 linhas e 24 quebras
- **Teste:** 2019–2024, 54 linhas e 12 quebras

Esta probabilidade é um índice de risco: `class_weight="balanced"` infla as probabilidades e não representa a chance real de quebra.

## Desempenho no teste

| Conjunto | Recall | Precisão | % alertas | % reais | Custo (5x FN + FP) | AUC |
|---|---:|---:|---:|---:|---:|---:|
| 2019–2024 | 0,75 | 0,24 | 70% | 22% | 44 | 0,73 |
| Sem 2024 | 0,25 | 0,03 | 64% | 9% | 43 | 0,34 |
| Só Sorriso-MT | 1,00 | 0,50 | 67% | 33% | 2 | 1,00 |

O protótipo não passou no critério de aprovação: o custo no teste deve ser menor que os custos das regras "nunca alertar" e "alertar sempre". O teste completo teve custo 44, contra 60 e 42; sem 2024, teve 43, contra 20 e 41.

## Experimento multivariável

Foram testadas quatro variáveis adicionais — déficit hídrico, dias acima de 35 °C, chuva acumulada e veranico — junto com a temperatura máxima média. A nova LogReg de cinco sinais melhorou o custo do teste completo (32 vs. 44) e a AUC (0,778 vs. 0,728), mas teve custo pior na validação expansiva (61 vs. 25) e custo 31 sem 2024, acima do baseline "nunca alertar" (20). Portanto, **não foi promovida**; o artefato ativo continua com apenas `tmax_enchimento`. Resultados por safra estão no [Model Card](docs/Model_Card.md) e em `models/s6_*.csv`.

Também foram comparados nove classificadores nas cinco variáveis, com corte comum de 0,5 e ranking feito somente nas previsões walk-forward de treino. Extra Trees raso ficou em primeiro (custo OOF 39; AUC 0,721), mas no teste diagnóstico não melhorou o custo do modelo atual (44) e teve AUC menor (0,627 vs. 0,728). **Nenhuma substituição foi feita**; veja `src/comparacao_modelos_multivariaveis.py`, `models/s7_*.csv` e a seção 9 do [Model Card](docs/Model_Card.md).

## Definição da quebra

Para cada município, uma safra é positiva quando o rendimento fica abaixo de `0,92` vezes a tendência linear calculada somente com o passado, usando até 10 safras anteriores e um mínimo de 5 safras.

## Limitações

- São apenas 18 safras independentes no treino e 6 no teste; municípios compartilham clima por safra.
- O modelo cobre principalmente calor/seca no enchimento. Não detecta, por exemplo, quebra por excesso de chuva, doença ou outros eventos.
- O teste foi mais quente que o treino: média de 29,88 °C contra 28,46 °C. A deriva climática eleva a taxa de alertas.
- O sinal é sensível a poucas safras; em teste e validação há ampla incerteza.
- Não usar sozinho para negar crédito, seguro ou orientar manejo pós-colheita.

## Estrutura

- `notebooks/` - coleta, tratamento, seleção de features, modelagem e avaliação
- `notebooks/14_backtest_regressao_logistica.ipynb` - funcionamento do pipeline ativo, backtest expansivo, métricas e análise de erros
- `models/` - pipelines, limiar, metadados e resultados consolidados
- `data/processed/dados_modelo_s4.csv` - base municipal-safra usada pelo modelo
- `src/` - validação da base, cache da coleta e persistência SQLite
- `streamlit_app.py` - dashboard
- `docs/Model_Card.md` - documentação técnica completa
- `docs/Dicionario_de_Dados.md` - contrato dos dados
- `docs/RFC.md` - escopo e critérios

## Executar

```bash
python -m pip install -r requirements.txt
python src/database.py
streamlit run streamlit_app.py
```

## Reprodutibilidade

Os notebooks mais recentes são a fonte dos artefatos finais. Antes de trocar o modelo, limiar ou split, atualize o Model Card, os metadados e o aplicativo em conjunto.
