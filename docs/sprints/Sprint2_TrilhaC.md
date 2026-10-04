# Diário de Sprint 2 — Limpeza, tratamento, EDA e engenharia de atributos
**Período:** 18/09/2026 a 27/09/2026
**Trilha definitiva do grupo:** C — Risco de baixa produtividade agrícola

**Equipe:**
**Scrum Master do Sprint:**
**Repositório GitHub:** (link)

> A aula pode usar a **Trilha A (chuva intensa)** só como exemplo de método. **A entrega é nos dados brutos da Trilha C coletados na Sprint 1** (`data/raw/`).
>
> Ordem obrigatória: **inspeção → limpeza e tratamento → split por safra → imputação estatística só no treino (se houver NA) → EDA no treino → alvo → features**. Não se faz EDA no bruto. Não há modelagem (baseline na Sprint 3).
>
> N = municípios × safras, **depois da limpeza**. N pequeno limita features e, depois, modelos.

### Contrato desta sprint

| | Artefato | Origem / destino |
|---|---|---|
| **Entra** | `data/raw/` + `config/` + N do merge (município × safra) | Sprint 1 — **não substituir por outra coleta sem versionar** |
| **Entra** | RFC v0.1 e dicionário v0.1 | Sprint 1 |
| **Sai** | `data/interim/` + log de limpeza (N antes/depois) | Sprint 3 em diante |
| **Sai** | Split por safra (corte, N treino/teste) | Sprints 3, 4 e 5 — **mesmo corte** |
| **Sai** | Alvo formal (limiar, horizonte, desbalanceamento no treino) | Sprints 3–5 |
| **Sai** | Features iniciais justificadas + dicionário v0.2 | Sprint 3 (transformer) e 4 (base para iterar) |

**Não sai daqui:** Dummy, persistência, Naive Bayes, F1, modelo escolhido.

- [ ] Confirmei que o notebook desta sprint lê o `data/raw` da Sprint 1

---

## 1. Limpeza e tratamento (antes da EDA)

`data/raw/` permanece intocado. A tabela tratada vai para `data/interim/`.

### 1.1 Inspeção (contar o sujo, ainda sem corrigir)

- [ ] Estatística descritiva das colunas numéricas
- [ ] Ausentes quantificados por coluna
- [ ] Duplicatas (linhas e por chave município × safra)
- [ ] Valores inválidos (produtividade negativa, safra incompleta) e sentinelas da API/IBGE

**Diagnóstico (números):**

### 1.2 Regras aplicadas

Não imputar com média/mediana/moda do dataset **inteiro**. Imputação estatística, se precisar, é a seção 3 (depois do split).

- [ ] Tipos e unidades padronizados
- [ ] Duplicatas tratadas com contagem
- [ ] Sentinelas / indicadores de ausência → `NaN` explícito
- [ ] Pares município-safra incompletos tratados com regra escrita (manter, excluir ou marcar)
- [ ] Inválidos de domínio tratados com regra escrita
- [ ] Log: o que foi feito, em quantas linhas/células, N depois
- [ ] Tabela salva em `data/interim/`
- [ ] Dicionário (log de limpeza) atualizado

| Problema encontrado | Regra aplicada | Linhas/células afetadas | N depois |
|---|---|---|---|
| | | | |

**N após a limpeza (município × safra):**
**Evidências (link do notebook/commit):**

## 2. Split temporal / por safra

Sobre a tabela **já limpa** (`data/interim/`).

- [ ] Treino = safras mais antigas; teste = mais recentes (sem embaralhar o tempo)
- [ ] Corte explícito; N treino e N teste
- [ ] Teste isolado: não usa para limiar, janelas nem parâmetros de imputação

**Corte (safras treino / teste):**
**Municípios:**
**N treino / N teste:**
**Justificativa:**

## 3. Tratamento estatístico residual (depois do split, antes da EDA)

Só NA que a limpeza de domínio não resolveu. Parâmetros saem **somente do treino**.

- [ ] Estratégia justificada (imputar agora / deixar NA para o `ColumnTransformer` da Sprint 3)
- [ ] Se imputar: regra ajustada no treino e aplicada ao teste

**Regra residual (ou “não há NA restantes”):**

## 4. Análise exploratória (EDA) — treino já tratado

- [ ] Estatística descritiva da variável de origem do alvo **no treino**
- [ ] Evolução por safra, histogramas, boxplots
- [ ] Correlação no treino
- [ ] Outliers discutidos (não só plotados)

> Desbalanceamento de **classes** só depois da seção 5 (quando o alvo existir). Nesta seção explora-se a variável de origem (produtividade bruta).

**Principais achados da EDA (treino):**

**Evidências (gráficos, link do notebook):**

## 5. Definição da variável-alvo

**Classe positiva (safra de risco / baixa produtividade):**
**Limiar e justificativa (treino, alinhada ao RFC):**
**Horizonte (o que já é conhecido no momento da decisão):**
**Desbalanceamento no treino:**

- [ ] Classe positiva sem ambiguidade, ligada ao custo de FN
- [ ] Desbalanceamento das classes quantificado **no treino**
- [ ] Seção do alvo no dicionário preenchida
- [ ] Colunas de construção do alvo na lista de exclusão (vazamento)

## 6. Engenharia de atributos (Feature Engineering)

- [ ] Agregações por ciclo/safra e defasagens (safra anterior) só com informação anterior ao fim da janela de previsão
- [ ] Cada feature seria calculável **no momento real da previsão** (mesmo horizonte do RFC; sem clima posterior à decisão)
- [ ] Código IBGE / município **não** entram como número; calendário (safra, mês) vale. Município como categoria só se todos os do teste existirem no treino — e mesmo assim justificar (risco de só memorizar o lugar)
- [ ] Variáveis de calendário agrícola quando pertinente
- [ ] Parâmetros definidos **no treino**, depois aplicados ao teste
- [ ] Nada agregado após o fim da janela de decisão da safra
- [ ] Cada atributo justificado um a um; dicionário atualizado

**Descrição e justificativa dos atributos:**

**Evidências (trecho de código, link do notebook):**

## 7. Scrum

- [ ] Atualizações semanais no board
- [ ] Board refletindo o estado real

**Link do board:**

## 8. Diário de bordo (retrospectiva individual)

| Integrante | O que fiz nesta Sprint | Dificuldades | O que pretendo manter/ajustar |
|---|---|---|---|
| | | | |

---

## Rubrica de avaliação — Sprint 2 (nota de 0 a 4,0)

| Critério | Peso | O que caracteriza nota máxima | Nota atribuída | Observações |
|---|---|---|---|---|
| Limpeza e tratamento | 1,0 | Inspeção numérica, regras explícitas, log com N, `interim` gerado, raw intocado, sem estatística global para imputar | | |
| Split por safra/ano | 0,5 | Corte explícito na tabela limpa; teste isolado; N depois da limpeza | | |
| EDA e variável-alvo | 1,0 | EDA no treino tratado; alvo formalizado no treino; dicionário atualizado | | |
| Engenharia de atributos | 1,0 | Agregações coerentes com a safra, sem vazamento, parâmetros no treino, atributos justificados um a um | | |
| Scrum + diário de bordo | 0,5 | Board com histórico; diário reflexivo de todos | | |
| **Nota final da Sprint 2** | **4,0** | | **___ / 4,0** | |
