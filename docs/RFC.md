# RFC - Projeto SojaRisco

## Resumo

O projeto estima o risco de quebra de safra de soja por calor/seca no período de enchimento dos grãos. A implementação atual é regional, baseada em nove municípios do Alto Teles Pires, e não deve ser usada como decisão operacional isolada.

## Pergunta

O enchimento desta safra foi quente o suficiente para indicar risco elevado de quebra?

## Evento previsto

Quebra municipal-safra definida como rendimento inferior a 92% da tendência linear passada do próprio município.

## Unidade e horizonte

- Unidade: município × safra.
- Momento de alerta: março, após dezembro–fevereiro e antes da colheita.
- Não é previsão de manejo da lavoura, pois o período já terminou.
- Não é previsão de rendimento em kg/ha.

## Modelo atual

- Regressão logística L2.
- Feature única: `tmax_enchimento`.
- `C=1.0`, `class_weight="balanced"`.
- Alerta para probabilidade >= 0,45, equivalente a `tmax_enchimento >= 28,34 °C`.

## Dados

- Treino: 2001–2018, 138 linhas.
- Teste: 2019–2024, 54 linhas.
- NASA POWER para clima diário.
- IBGE/PAM para rendimento municipal.

## Validação

A seleção de features foi feita com validação deixando uma safra de fora no treino. O teste foi separado antes da escolha final e deve ser avaliado uma única vez.

## Custo dos erros

FN vale 5 vezes mais que FP na calibração do limiar. O limiar foi escolhido pela menor custo esperado na validação temporal, não pelo melhor desempenho do teste.

## Critério de aprovação

O custo deve ser menor que os custos das políticas “nunca alertar” e “alertar sempre”, no teste completo e no teste sem 2024. O modelo atual não atende a esse critério.

## Fora do escopo

Quebras por chuva excessiva, doenças, pragas, geadas ou outros mecanismos não cobertos por temperatura máxima. Outros municípios, culturas e predição absoluta de rendimento também estão fora do escopo.
