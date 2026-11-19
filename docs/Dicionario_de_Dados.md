# Dicionario de Dados

**Projeto:** SojaRisco  
**Versao:** 1.0 - Sprint 5  
**Fonte atual:** notebooks 08 a 13 e artefatos em `models/`

## Unidade e recorte

- Unidade: município × safra.
- Municípios: Ipiranga do Norte, Itanhangá, Lucas do Rio Verde, Nobres, Nova Mutum, Nova Ubiratã, Santa Rita do Trivelato, Sorriso e Tapurah.
- Cultura: soja em grão.
- Treino: safras 2001–2018, 138 linhas.
- Teste: safras 2019–2024, 54 linhas.
- Base processada: `data/processed/dados_modelo_s4.csv`.

## Fontes

| Fonte | Dado |
|---|---|
| NASA POWER | Clima diário; agregação por safra e município |
| IBGE/PAM | Rendimento municipal anual |

## Variáveis centrais

| Coluna | Tipo | Definição |
|---|---|---|
| `cod_municipio` | inteiro | Código IBGE do município |
| `municipio` | texto | Nome do município |
| `safra` | inteiro | Ano da safra |
| `rendimento_kg_ha` | número | Rendimento de soja usado apenas para construir o alvo |
| `tmax_enchimento` | número, °C | Média da temperatura máxima diária em dezembro–fevereiro |
| `quebra_safra` | inteiro 0/1 | Alvo positivo definido abaixo |
| `split` | texto | `treino` ou `teste` |

## Alvo

`quebra_safra = 1` quando o rendimento da safra é inferior a `0,92 × tendência_linear`.

A tendência é calculada para cada município com a série histórica anterior à safra, usando até 10 safras passadas e exigindo pelo menos 5 observações. Nenhuma safra futura entra no cálculo.

## Feature final

A seleção no notebook 08 avaliou famílias de features e escolheu somente `tmax_enchimento`. O pipeline congela uma única variável padronizada pelo `StandardScaler`.

## Artefatos

- `pipeline_final.joblib` - pipeline campeão
- `modelo_final_metadados.json` - metadados do modelo
- `limiar_congelado.json` - limiar de decisão
- `features_selecionadas.json` - lista oficial de features
- `s5_avaliacao_teste_final.csv` - avaliação final

## Exclusões

Produção, área plantada, área colhida e rendimento não devem entrar como preditores. O rendimento gera o alvo e poderia vazar diretamente a resposta.
