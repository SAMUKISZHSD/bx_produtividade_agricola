# Inscrição na Mostra de Tecnologia (Prazo: 30/10) & Roteiro do Pitch (09/11)

**Projeto:** SojaRisco: Alerta de Quebra  
**Trilha:** C — Risco de Baixa Produtividade Agrícola (Soja em Sorriso - MT)  
**Equipe:** 
- João Guilherme Cravo (RGM 35880759)
- Jean Carlos Silva de Almeida (RGM 33783276)
- Samuel Allan Nunes da Cunha (RGM 34524746)

---

## 📋 Itens Oficiais para Formulário de Inscrição (30/10)

Copie e cole diretamente nos campos do formulário da turma:

### 1. Logo do Projeto (Arquivo PNG 500x500 px)
- **Nome do arquivo:** `logo_sojarisco.png`
- **Caminho no repositório:** `docs/mostra/logo_sojarisco.png` (também espelhado em `docs/img/logo_sojarisco.png`)
- **Resolução exata:** 500 x 500 pixels, PNG.

### 2. Nome do Projeto (Máximo 30 caracteres)
```text
SojaRisco: Alerta de Quebra
```
*(Contagem: 27 caracteres — dentro do limite de 30)*

### 3. Descritivo do Projeto (Máximo 200 caracteres)
```text
Sistema de IA agroclimática para predição antecipada de risco de quebra de safra de soja em Sorriso-MT com árvores de decisão, apoiando produtores e cooperativas na mitigação preventiva de perdas.
```
*(Contagem: 196 caracteres — dentro do limite de 200)*

### 4. Tags das Tecnologias Envolvidas
```text
Python, Machine Learning, Scikit-Learn, Árvores de Decisão, Random Forest, XGBoost, NASA POWER API, IBGE PAM, Streamlit, AgroTech, Engenharia de Dados, Sorriso-MT
```

---

## 🎬 Roteiro do Vídeo Pitch de 90 Segundos (Entrega de 09/11)

*Instrução: Gravar em vídeo de até 1m30s, postar no YouTube como "Não Listado" e inserir a URL no README.md e no artigo técnico.*

| Bloco de Tempo | Cena / Visual | Falas e Argumentação Chave |
|---|---|---|
| **00:00 - 00:15** (15s)<br>*O Gancho e a Dor* | Apresentador + Imagem aérea de lavoura de soja em Sorriso-MT | *"Sorriso, Mato Grosso: a capital nacional do agro. Mas mesmo com tecnologia de ponta, uma estiagem silenciosa na raiz durante o enchimento de grãos pode destruir safras inteiras. Em 2021, o município teve chuva anual recorde, mas a produtividade desabou. Como antecipar essa quebra a tempo?"* |
| **00:15 - 00:35** (20s)<br>*A Solução e os Dados* | Gravação de tela: Pipeline de 4 Camadas (NASA POWER + IBGE PAM) | *"Criamos o SojaRisco. Construímos um pipeline robusto e idempotente integrando medições orbitais da NASA POWER com dados oficiais do IBGE PAM. Em vez de olhar só a chuva anual, monitoramos a raiz em janeiro e fevereiro: déficit hídrico e picos térmicos acima de 35 graus."* |
| **00:35 - 00:60** (25s)<br>*O Experimento e o Vencedor* | Gráficos do Artigo: Matriz de Confusão e Árvore de Decisão | *"Comparamos Baselines, Random Forest, XGBoost e Árvore de Decisão em partição temporal estrita. Como o Falso Negativo é catastrófico para quem financia a lavoura, o foco é 100% no Recall. A Árvore de Decisão superou modelos complexos por ser imune ao sobreajuste em amostras decenais e por entregar regras claras e auditáveis para o agrônomo."* |
| **00:60 - 00:75** (15s)<br>*O Dashboard Vivo* | Tela do Streamlit App: Inferência ao Vivo (Aba 1) e Persistência SQLite (Aba 2) | *"Nosso protótipo vivo no Streamlit Community Cloud simula cenários em menos de 1 milissegundo, conecta com a API da NASA em tempo real e armazena todas as previsões e logs em banco relacional contínuo."* |
| **00:75 - 00:90** (15s)<br>*Fechamento e Chamada* | Tela final com QR Code do Artigo e link do GitHub | *"SojaRisco transforma dados públicos de satélite em decisões preventivas de seguro rural e manejo. Acesse nosso artigo interativo e teste o dashboard pelo QR Code na tela. Obrigado!"* |

---

## 📱 Links e Artefatos da Mostra

- **Artigo Técnico Publicado:** [https://samukiszhsd.github.io/bx_produtividade_agricola/](https://samukiszhsd.github.io/bx_produtividade_agricola/)
- **Dashboard Streamlit:** [streamlit_app.py](../../streamlit_app.py)
- **Repositório GitHub:** [https://github.com/SAMUKISZHSD/bx_produtividade_agricola](https://github.com/SAMUKISZHSD/bx_produtividade_agricola)
- **QR Code do Artigo:** [docs/mostra/qrcode_artigo.png](qrcode_artigo.png)
