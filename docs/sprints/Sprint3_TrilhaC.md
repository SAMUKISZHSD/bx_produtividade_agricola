# Diário de Sprint 3 — Ingestão robusta e primeira modelagem (baseline)
**Período:** 28/09/2026 a 04/10/2026
**Trilha:** C — Risco de baixa produtividade agrícola

**Equipe:**
**Scrum Master do Sprint:**
**Repositório GitHub:** (link)

> Kickoff e **coleta bruta**: Sprint 1. Limpeza, split por safra, EDA no treino tratado, alvo e features: Sprint 2. Esta sprint **não reabre** esses pontos: robustece a ingestão e treina o primeiro conjunto de baselines **no mesmo split da Sprint 2**.

### Contrato desta sprint

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | `data/interim/`, split por safra, alvo, features iniciais, dicionário v0.2 | Sprint 2 — **mesmo split e mesmas features** |
| **Entra** | `data/raw/` + `config/` | Sprint 1 (robustecer a coleta, sem apagar o bruto) |
| **Sai** | Ingestão idempotente + `requirements.txt` + N atualizado | Sprint 4–5 |
| **Sai** | `ColumnTransformer` inicial (`fit` só no treino) | Sprint 4 |
| **Sai** | Dummy + persistência + Naive Bayes, métricas por classe, leitura dos erros | Sprint 4 (**os erros motivam features novas**) |

**Não sai daqui:** modelo final complexo, limiar fino, model card.

- [ ] Confirmei que treino/teste são os da Sprint 2 e que as features são as da Sprint 2

---

## 1. Aprofundamento da ingestão (Pipeline CD)

- [ ] Período histórico de safras ampliado, ou período redefinido com justificativa. Se o recorte mudar: versionar o novo bruto em `data/raw/`, **reaplicar as regras de limpeza da Sprint 2** para gerar de novo o `interim`, e reaplicar o **mesmo critério** de split (safras antigas / recentes).
- [ ] Tratamento de erros revisado e robustecido (reexecução após falhas parciais)
- [ ] Coleta idempotente comprovada (reexecução não duplica registros)
- [ ] `data/raw/` intocado como origem; `data/interim/` = tabela limpa (Sprint 2); `data/processed/` = matriz já com features para o modelo (esta sprint em diante)
- [ ] `requirements.txt` (ou equivalente) com versões usadas na coleta
- [ ] N (municípios × safras) atualizado após qualquer recorte

**N atual (treino / teste):**
**Evidências (link do notebook/commit):**

## 2. Preparação para modelagem

- [ ] Mesmo split por safra/ano da Sprint 2 (treino em safras antigas, teste nas recentes — nunca aleatório)
- [ ] Um `Pipeline` sklearn: `ColumnTransformer` **e** o classificador no mesmo objeto; `fit` **somente no treino**
- [ ] Imputação residual / encoding / normalização dentro desse Pipeline
- [ ] `random_state` documentado onde o algoritmo for estocástico
- [ ] Ausência de vazamento reconfirmada (nada agregado após o fim da janela de previsão)
- [ ] Features da Sprint 2 incluídas no transformer

**Descrição da estratégia de split (safras de corte, N) e do ColumnTransformer:**

## 3. Modelagem baseline

- [ ] `DummyClassifier` (piso de **acurácia** da classe majoritária — não é piso de recall na classe rara)
- [ ] Baseline de **persistência** (classe da safra anterior daquele município — não o alvo futuro da safra prevista)
- [ ] Naive Bayes treinado e avaliado **no mesmo split e nas mesmas features**, no mesmo `Pipeline`
- [ ] Independência condicional do Naive Bayes discutida (variáveis climáticas do mesmo ciclo são correlatas; o modelo é baseline pedagógico)
- [ ] Recall, precisão, F1 e matriz de confusão **por classe** para os três; N pequeno se reporta também em **contagem** (ex.: 3 FN em 8 eventos)
- [ ] Interpretação ligada ao custo de falso negativo do RFC; se N de treino for pequeno, isso entra na leitura das métricas
- [ ] Ainda **sem** ajuste fino de limiar (Sprint 5)
- [ ] Sem SMOTE / oversampling aleatório (N pequeno + série/safra: inventa linhas que não existiram)

**Resultados (Dummy vs. persistência vs. Naive Bayes) e interpretação:**

**Evidências (link do notebook, métricas):**

## 4. Scrum

- [ ] Atualizações assíncronas semanais registradas
- [ ] Board refletindo o estado real da Sprint

## 5. Diário de bordo (retrospectiva individual)

| Integrante | O que fiz nesta Sprint | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| | | | |

---

## Rubrica de avaliação — Sprint 3 (nota de 0 a 4,0)

| Critério | Peso | O que caracteriza nota máxima | Nota atribuída | Observações |
|---|---|---|---|---|
| Aprofundamento da ingestão | 1,0 | Coleta robustecida, idempotência comprovada, `raw` / `interim` / `processed` distintos, N atualizado | | |
| Preparação (mesmo split + ColumnTransformer) | 0,5 | Split da Sprint 2 respeitado, transformações ajustadas só no treino, sem vazamento | | |
| Baselines (Dummy + persistência + Naive Bayes) com métricas interpretadas | 1,5 | Três baselines no mesmo split, métricas por classe, leitura compatível com o N amostral | | |
| Scrum + diário de bordo | 1,0 | Board e diário refletindo o processo real da Sprint | | |
| **Nota final da Sprint 3** | **4,0** | | **___ / 4,0** | |
