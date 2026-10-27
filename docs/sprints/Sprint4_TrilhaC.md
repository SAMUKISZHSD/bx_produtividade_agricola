# Diário de Sprint 4 — Iteração de atributos, retreino do baseline e pipeline congelado
**Período:** 05/10/2026 a 11/10/2026  
**Trilha:** C — Risco de baixa produtividade agrícola  

**Equipe:** João Guilherme Cravo (RGM 35880759), Jean Carlos Silva de Almeida (RGM 33783276), Samuel Allan Nunes da Cunha (RGM 34524746)  
**Scrum Master do Sprint:** João Guilherme Cravo  
**Repositório GitHub:** [SAMUKISZHSD/bx_produtividade_agricola](https://github.com/SAMUKISZHSD/bx_produtividade_agricola)  

> Sprint 1: coleta bruta. Sprint 2: limpeza, split, alvo e features iniciais. Sprint 3: baselines. Esta sprint **evolui** as features a partir dos erros do baseline, **retreina Dummy + persistência + Naive Bayes no mesmo split** e congela o `ColumnTransformer` para a Sprint 5. Sem lift documentado, não há evolução — só colunas novas.
>
> Com N pequeno, preferir poucos atributos interpretáveis a dezenas de índices correlatos.

### Contrato desta sprint

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | Split da Sprint 2, features da Sprint 2, erros e métricas da Sprint 3 | Sprints 2 e 3 |
| **Entra** | `ColumnTransformer` inicial da Sprint 3 | Sprint 3 |
| **Sai** | Features **novas** (além das da Sprint 2), justificadas pelos erros da Sprint 3 e compatíveis com o N | Sprint 5 |
| **Sai** | `ColumnTransformer` **congelado** (`fit` só no treino) | Sprint 5 **é obrigada a usar este** |
| **Sai** | Dummy + persistência + NB **retreinados** + tabela de lift S3→S4 | Sprint 5 (piso do comparativo; **não colar métricas da Sprint 3**) |
| **Sai** | Dicionário v0.3 | Sprint 5 |

**Não sai daqui:** seleção do modelo final, limiar de decisão, model card.

- [x] Confirmei o mesmo split da Sprint 2 e que as features “novas” não são as da Sprint 2 renomeadas

---

## 1. Engenharia de atributos iterada

- [x] Atributos **novos** em relação à Sprint 2 (não são os mesmos com outro nome)
- [x] Motivação ligada aos erros da Sprint 3 (ex.: safras de baixa produtividade não sinalizadas)
- [x] Seleção/redução de atributos avaliada **só no treino** (não no teste nem no dataset inteiro) e justificada (compatível com o N de treino)
- [x] Vazamento revisado em **todos** os atributos (antigos e novos); nada após o fim da janela de previsão
- [x] Cada atributo novo descrito e justificado individualmente
- [x] Dicionário (seção de derivados) atualizado

**Descrição dos atributos criados/selecionados e de quais erros da Sprint 3 eles atacam:**

Na Sprint 3, os modelos receberam apenas atributos climáticos acumulados ou médios em escala anual. Esse desenho gerou uma falha preditiva crítica na **safra 2021**: apesar de ter registrado quebra severa de produtividade (3.360 kg/ha frente ao limiar de 3.400 kg/ha), seu volume pluviométrico anual foi de 1.634,39 mm (o 3º maior de todo o histórico decenal). Por conta disso, o `GaussianNB` classificou 2021 incorretamente como safra normal (Falso Negativo), além de incorrer em Falsos Positivos em 2019 e 2020.

Para corrigir essas distorções, investigamos os registros diários da NASA POWER (`data/raw/nasa_power_Sorriso_MT_2015_2025.json`) na janela fenológica determinante da cultura: o **bimestre de floração e enchimento de grãos (janeiro e fevereiro)** em Sorriso-MT. Foram criados 4 atributos inéditos no notebook [notebooks/08_engenharia_features_selecao_parcimoniosa.ipynb](../../notebooks/08_engenharia_features_selecao_parcimoniosa.ipynb):

1. `deficit_hidrico_solo` (dias com `GWETROOT < 0.70` em Jan-Fev): Identifica déficit na zona radicular na fase em que o abortamento de vagens e o enchimento de grãos são irreversíveis. Em 2021 foram 42 dias de solo seco (em 2015 foram 47; em safras normais, a contagem é próxima de zero). Correlação linear com o alvo no treino: **$r = +0.9027$**.
2. `dias_pico_calor` (dias com `T2M_MAX >= 35.0 °C` em Jan-Fev): Captura o estresse térmico pontual que inviabiliza o pólen e eleva o déficit de pressão de vapor. Em 2021 ocorreram 3 dias de pico e em 2016 ocorreram 4 dias (safras com quebra), enquanto safras normais registraram 0 dias. Correlação: **$r = +0.7354$**.
3. `veranico_max_dias` (maior sequência contínua de dias com chuva $< 1.0$ mm em Jan-Fev): Mensura o choque contínuo de estiagem intra-ciclo. Correlação: **$r = +0.5308$**.
4. `precipitacao_enchimento` (chuva acumulada em mm no bimestre Jan-Fev): Balanço hídrico intra-safra que substitui com muito mais precisão agronômica a chuva anual total. Correlação: **$r = -0.5545$**.

**Seleção Parcimoniosa no Treino ($N=8$):**  
Para evitar a maldição da dimensionalidade (*overfitting*) em amostra reduzida ($N_{train} = 8$), avaliamos a multicolinearidade entre todas as variáveis candidatas exclusivamente no bloco 2015–2022. Descartamos `PRECTOTCORR`, `GWETROOT` anual e `GWET_x_PREC` pela redundância mútua severa ($r > 0.93$). O subconjunto parcimonioso final selecionado contém 4 variáveis ortogonais e agronomicamente complementares:
- `deficit_hidrico_solo`
- `dias_pico_calor`
- `amplitude_termica` (mantida da Sprint 2)
- `precipitacao_enchimento`

**Prevenção de Vazamento Temporal:** Todas as variáveis fecham seu cômputo no último dia de fevereiro, com antecedência de 1 a 2 meses antes do encerramento das colheitas e muito antes da publicação oficial pelo IBGE PAM. O dataset consolidado foi salvo em [data/processed/dados_modelo.csv](../../data/processed/dados_modelo.csv) pronto para consumo nos Tópicos 3 e 5.

---

## 2. Pipeline de preparação congelado

- [ ] Um `Pipeline` sklearn: `ColumnTransformer` **e** o classificador no mesmo objeto; lista de colunas **congelada** (a da seleção no treino)
- [ ] Estratégias de imputação, encoding e normalização justificadas (não só o default do sklearn)
- [ ] `fit` confirmado apenas no treino
- [ ] Este Pipeline/transformer é o que a Sprint 5 vai usar. Não “descongelar” na Sprint 5; se o PO pedir mudança aqui, retreinar de novo os três baselines antes de entregar.

**Descrição da preparação final:**

---

## 3. Retreino do baseline e lift

- [ ] Dummy, persistência e Naive Bayes **retreinados** com as features desta sprint, **no mesmo split** da Sprint 2/3
- [ ] Métricas por classe (recall, precisão, F1, matriz) dos três, **depois** da iteração
- [ ] Tabela de delta em relação à Sprint 3 (pelo menos recall e F1 da classe positiva)
- [ ] Se não houve ganho: hipótese do porquê, e o que foi descartado

**Tabela de lift (classe positiva):**

| Modelo | Recall S3 | Recall S4 | F1 S3 | F1 S4 | Delta recall |
|---|---|---|---|---|---|
| Dummy | | | | | |
| Persistência | | | | | |
| Naive Bayes | | | | | |

**Interpretação do lift (ou da ausência de lift):**

---

## 4. Sprint Review — checkpoint intermediário

**Incremento demonstrado ao PO (docente):**
**Feedback recebido:**

---

## 5. Scrum

- [x] Atualizações assíncronas semanais registradas
- [x] Board refletindo o backlog, em andamento e concluído

* **Quadro Oficial no Trello:** [Quadro Trello - Projeto de Ciência de Dados](https://trello.com/invite/b/6a975ab20fa3094b426c0c68/ATTI02cea94da7f784bcf30e1e3d24341426A34F2CE2/📊-projeto-de-ciencia-de-dados)

---

## 6. Diário de bordo (retrospectiva individual)

| Integrante | O que fiz nesta Sprint | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| **João Guilherme Cravo** | • **TÓPICO 1 (Engenharia de Novas Features Focadas nos Erros da S3):** Extraí dos dados diários da NASA POWER as variáveis da janela fenológica crítica de Jan-Fev (`deficit_hidrico_solo`, `dias_pico_calor`, `veranico_max_dias` e `precipitacao_enchimento`), provando ausência de vazamento temporal.<br>• **TÓPICO 2 (Seleção Parcimoniosa Compatível com N=8):** Avaliei a matriz de correlação e multicolinearidade estritamente no bloco de treino (2015–2022), descartei redundâncias e fechei o vetor enxuto de 4 variáveis, atualizando a camada `data/processed/dados_modelo.csv` para os colegas utilizarem nos tópicos seguintes. | Definir os limiares agronômicos exatos de solo ($< 0.70$) e temperatura ($\ge 35^\circ C$) que fizessem sentido biológico para a soja do Cerrado sem sobreajustar a série. | Manter a documentação dos limites físicos das variáveis para fundamentar a defesa na Sprint 5. |
| **Jean Carlos Silva de Almeida** | | | |
| **Samuel Allan Nunes da Cunha** | | | |

---

## Rubrica de avaliação — Sprint 4 (nota de 0 a 4,0)

| Critério | Peso | O que caracteriza nota máxima | Nota atribuída | Observações |
|---|---|---|---|---|
| Engenharia de atributos iterada | 1,5 | Atributos novos, justificados pelos erros da Sprint 3, seleção compatível com o N, sem vazamento | | |
| Pipeline congelado | 0,5 | ColumnTransformer atualizado, `fit` só no treino, estratégias justificadas | | |
| Retreino do baseline e lift | 1,0 | Dummy/persistência/NB retreinados no mesmo split; delta de recall/F1 interpretado | | |
| Sprint Review / incremento demonstrado | 0,5 | Incremento real apresentado ao PO, com feedback registrado | | |
| Scrum + diário de bordo | 0,5 | Board atualizado semanalmente, diário reflexivo de todos os integrantes | | |
| **Nota final da Sprint 4** | **4,0** | | **___ / 4,0** | |
