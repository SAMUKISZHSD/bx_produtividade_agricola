# Diário de Sprint 4 — Iteração de atributos, retreino do baseline e pipeline congelado
**Período:** 05/10/2026 a 11/10/2026
**Trilha:** C — Risco de baixa produtividade agrícola

**Equipe:**
**Scrum Master do Sprint:**
**Repositório GitHub:** (link)

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

- [ ] Confirmei o mesmo split da Sprint 2 e que as features “novas” não são as da Sprint 2 renomeadas

---

## 1. Engenharia de atributos iterada

- [ ] Atributos **novos** em relação à Sprint 2 (não são os mesmos com outro nome)
- [ ] Motivação ligada aos erros da Sprint 3 (ex.: safras de baixa produtividade não sinalizadas)
- [ ] Seleção/redução de atributos avaliada **só no treino** (não no teste nem no dataset inteiro) e justificada (compatível com o N de treino)
- [ ] Vazamento revisado em **todos** os atributos (antigos e novos); nada após o fim da janela de previsão
- [ ] Cada atributo novo descrito e justificado individualmente
- [ ] Dicionário (seção de derivados) atualizado

**Descrição dos atributos criados/selecionados e de quais erros da Sprint 3 eles atacam:**

## 2. Pipeline de preparação congelado

- [ ] Um `Pipeline` sklearn: `ColumnTransformer` **e** o classificador no mesmo objeto; lista de colunas **congelada** (a da seleção no treino)
- [ ] Estratégias de imputação, encoding e normalização justificadas (não só o default do sklearn)
- [ ] `fit` confirmado apenas no treino
- [ ] Este Pipeline/transformer é o que a Sprint 5 vai usar. Não “descongelar” na Sprint 5; se o PO pedir mudança aqui, retreinar de novo os três baselines antes de entregar.

**Descrição da preparação final:**

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

## 4. Sprint Review — checkpoint intermediário

**Incremento demonstrado ao PO (docente):**
**Feedback recebido:**

## 5. Scrum

- [ ] Atualizações assíncronas semanais registradas
- [ ] Board refletindo o backlog, em andamento e concluído

## 6. Diário de bordo (retrospectiva individual)

| Integrante | O que fiz nesta Sprint | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| | | | |

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
