# Diário de Sprint 5 — Modelagem completa, limiar de decisão e seleção
**Período:** 12/10/2026 a 25/10/2026
**Trilha:** C — Risco de baixa produtividade agrícola

**Equipe:**
**Scrum Master do Sprint:**
**Repositório GitHub:** (link)

> Split da Sprint 2 e `ColumnTransformer` **congelado na Sprint 4**. No comparativo, Dummy, persistência e Naive Bayes são os da Sprint 4 (mesmo pipeline). Pode **reproduzir** esses números no notebook desta sprint; **não** colar métricas da Sprint 3 (features antigas). Classificadores novos treinam neste pipeline, na mesma partição de teste.
>
> Se N de treino for pequeno, justificar a escolha de modelo: linear / Naive Bayes podem ser mais honestos que Random Forest ou XGBoost.

### Contrato desta sprint

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | Split da Sprint 2 | Sprint 2 — **não mudar o teste** |
| **Entra** | Features finais + `ColumnTransformer` congelado + baselines retreinados (lift) | Sprint 4 |
| **Entra** | RFC (custo de FN), dicionário v0.3 e N depois da limpeza | Sprints 1, 2 e 4 |
| **Sai** | Comparativo no pipeline final (baselines S4 + ≥2 modelos novos, mesma partição) | Entrega final |
| **Sai** | Limiar de decisão justificado pelo RFC | Entrega final |
| **Sai** | Modelo escolhido + caderno de experimentos + model card + dicionário v0.4 + `joblib` do Pipeline em `models/` | Entrega final / mostra |

**Não há sprint seguinte.** Dashboard, se houver, é extra e lê estes artefatos — não gera outro split.

- [ ] Confirmei transformer da Sprint 4, split da Sprint 2 e que nenhuma métrica da Sprint 3 entrou no quadro

---

## 1. Revisão do split e da preparação

- [ ] Mesmo split por safra/ano da Sprint 2 (treino em safras antigas, teste nas recentes)
- [ ] `Pipeline`/`ColumnTransformer` da Sprint 4, `fit` só no treino
- [ ] Vazamento reconfirmado com os atributos finais (nada após o fim da janela de previsão)
- [ ] N treino/teste reafirmado; complexidade dos modelos compatível com a amostra

**Safras de corte, N treino/teste e resumo do transformer:**

## 2. Comparativo no pipeline final

- [ ] Dummy, persistência e Naive Bayes **do pipeline da Sprint 4** no quadro (reproduzidos aqui; não usar números da Sprint 3)
- [ ] No mínimo **dois** classificadores adicionais, com justificativa compatível com o N
- [ ] Todos avaliados na **mesma** partição de teste
- [ ] Hiperparâmetros documentados; se houver busca, ela usa só o treino (ou validação temporal dentro do treino) — nunca o teste
- [ ] `class_weight="balanced"` (ou equivalente) é lícito; SMOTE / oversampling aleatório continua proibido
- [ ] Independência do Naive Bayes continua tratada como hipótese pedagógica

**Modelos no comparativo (3 baselines da Sprint 4 + ≥2 novos):**
1. Dummy
2. Persistência
3. Naive Bayes
4. (novo)
5. (novo)

## 3. Avaliação, limiar e custo do falso negativo

- [ ] Recall, precisão, F1 e matriz de confusão por classe para todos, no `predict` padrão **e** no limiar escolhido
- [ ] Recorte de **validação temporal no fim do treino** (safras finais do treino, ou `TimeSeriesSplit` só no treino)
- [ ] Tabela ou curva de limiar na **validação**; o melhor ponto pelo custo de FN do RFC é congelado
- [ ] Teste medido **uma vez** com esse limiar — não escolher o corte olhando o teste
- [ ] Acurácia alta com recall baixo na classe positiva tratada como falha, se ocorrer
- [ ] FN/FP também em **contagem** (ex.: 3 FN em 8 eventos), não só em percentual

**Caderno de experimentos (validação e teste):**

| ID | Modelo | Features (S2/S4) | Limiar | Recall val. | Recall teste | Precisão teste | F1 teste |
|---|---|---|---|---|---|---|---|
| | Dummy | | | | | | |
| | Persistência | | | | | | |
| | Naive Bayes | | | | | | |
| | | | | | | | |
| | | | | | | | |

Anotar `random_state` na coluna ID ou numa nota abaixo. Persistência não tem limiar probabilístico — deixar “—” e avaliar só a classe persistida.

**Limiar escolhido (na validação) e justificativa:**

## 4. Seleção do modelo, análise de erros e model card mínimo

- [ ] Modelo final selecionado com justificativa (métrica da classe positiva + limiar + complexidade vs. N). **Não** escolher por acurácia. Se Dummy ou persistência ganharem no teste, **eles são o modelo final**.
- [ ] Análise qualitativa de erros concretos (município/safra, não só “erra mais na positiva”)
- [ ] Model card mínimo preenchido abaixo
- [ ] `joblib` (ou equivalente) do **Pipeline inteiro** em `models/` (pré-processamento + classificador + limiar documentado)
- [ ] Dicionário conferido (features finais = as do modelo escolhido)

**Modelo final e justificativa:**

**Principais erros analisados (FN/FP relevantes):**

### Model card mínimo

| Campo | Conteúdo |
|---|---|
| Problema / classe positiva | |
| Unidade de análise e horizonte | |
| Split (safras treino / teste) e N | |
| Features (link do dicionário) | |
| Algoritmo, hiperparâmetros, `random_state` e limiar (origem: validação) | |
| Métrica principal no teste (classe positiva) | |
| O que o modelo **não** faz / limitações (incluir N, se pequeno) | |
| Como reproduzir (`requirements.txt` + notebook/script) | |

## 5. Integração com Banco de Dados (opcional)

- [ ] Ponto de integração avaliado com a disciplina de Banco de Dados (clima, produtividade e previsões)
- [ ] Situação atual da integração (em andamento / não viabilizada / concluída)

## 6. Scrum e diário de bordo

- [ ] Board atualizado
- [ ] Diário de bordo individual preenchido

| Integrante | O que fiz nesta Sprint | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| | | | |

---

## Rubrica de avaliação — Sprint 5 (nota de 0 a 4,0)

| Critério | Peso | O que caracteriza nota máxima | Nota atribuída | Observações |
|---|---|---|---|---|
| Revisão do split e da preparação | 0,5 | Split da Sprint 2 e transformer da Sprint 4, vazamento reconfirmado, N explícito | | |
| Comparativo no pipeline final | 1,0 | Baselines retreinados + ≥2 modelos novos compatíveis com o N, mesma partição | | |
| Avaliação, limiar e custo de FN | 1,0 | Métricas por classe + limiar escolhido **na validação** ligado ao RFC; teste uma vez; FN/FP em contagem | | |
| Seleção, erros e model card | 1,0 | Justificativa clara (inclui N; métrica da positiva, não acurácia), casos concretos, model card, `joblib` do Pipeline; baseline vencedor é aceito | | |
| Scrum + diário de bordo (e integração opcional com BD) | 0,5 | Board e diário refletindo o processo real da Sprint | | |
| **Nota final da Sprint 5** | **4,0** | | **___ / 4,0** | |
