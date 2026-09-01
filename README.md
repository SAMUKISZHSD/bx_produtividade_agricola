# Previsão de Risco de Baixa Produtividade Agrícola

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Pandas](https://img.shields.io/badge/Pandas-2.0%2B-150458.svg?logo=pandas&logoColor=white)](https://pandas.pydata.org/)
[![Scikit-Learn](https://img.shields.io/badge/scikit--learn-1.3%2B-F7931E.svg?logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![NASA POWER API](https://img.shields.io/badge/Data_Source-NASA_POWER_API-red.svg)](https://power.larc.nasa.gov/)
[![IBGE PAM API](https://img.shields.io/badge/Data_Source-IBGE_PAM_1612-green.svg)](https://servicodados.ibge.gov.br/)

Projeto de Ciência de Dados e Inteligência Artificial voltado à previsão e alerta antecipado de **risco de baixa produtividade agrícola (quebra de safra)** para a cultura de **Soja em Grão** no município de **Piracicaba - SP** (safras 2015 a 2025).

---

##  1. Visão Geral do Problema de Negócio

As variações agroclimáticas (anomalias de precipitação, estresse térmico, déficit de umidade no solo) são os principais fatores de risco para a produtividade da lavoura de soja. 

* **Objetivo:** Construir um modelo preditivo capaz de sinalizar com antecedência se a safra agrícola terá rendimento abaixo do padrão histórico esperado.
* **Recorte Geográfico:** Piracicaba - SP (Código IBGE: `3538709` | Lat: `-22.7253`, Lon: `-47.6492`).
* **Recorte Temporal:** Safras de 2015 a 2025.
* **Unidade de Análise:** Ano-safra de soja (janela de desenvolvimento da cultura: Setembro do ano anterior a Abril/Agosto do ano de colheita).
---


##  2. Fontes de Dados e APIs

| Fonte | API / Endpoint | Resolução | Variáveis Utilizadas |
| :--- | :--- | :--- | :--- |
| **NASA POWER** | [Daily Point API](https://power.larc.nasa.gov/api/temporal/daily/point) | Diária | `PRECTOTCORR` (Precipitação mm), `T2M` (Temp. Média °C), `T2M_MAX`, `T2M_MIN`, `RH2M` (Umidade Relativa %), `GWETROOT` (Umidade do Solo na Raiz) |
| **IBGE (PAM)** | [Agregado 1612 - Lavouras Temporárias](https://servicodados.ibge.gov.br/api/v3/agregados/1612) | Anual (Safra) | *Rendimento médio da produção (kg/ha)*, *Área plantada (ha)*, *Área colhida (ha)*, *Quantidade produzida (t)* |

---

##  3. Como Instalar e Executar

### 3.1. Pré-requisitos
* Python 3.10 ou superior
* Gerenciador de pacotes `pip` ou `conda`

### 3.2. Configuração do Ambiente Virtual

```bash
# 1. Clone o repositório (se necessário)
git clone https://github.com/SAMUKISZHSD/bx_produtividade_agricola.git
cd bx_produtividade_agricola

# 2. Crie e ative um ambiente virtual
python3 -m venv .venv
source .venv/bin/activate  # No Linux/macOS
# .venv\Scripts\activate   # No Windows

# 3. Instale as dependências
pip install -r requirements.txt
```

---


## 👥 Equipe do Projeto

<div align="center">

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/jeanBR2O2O">
        <img src="https://github.com/jeanBR2O2O.png" width="100px;" alt="Jean Carlos"/><br>
        <b>Jean Carlos</b>
      </a>
      <br>
      Desenvolvedor
    </td>

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/jonnguii">
        <img src="https://github.com/jonnguii.png" width="100px;" alt="João Guilherme"/><br>
        <b>João Guilherme</b>
      </a>
      <br>
      Desenvolvedor
    </td>

<table>
  <tr>
    <td align="center">
      <a href="https://github.com/SAMUKISZHSD">
        <img src="https://github.com/SAMUKISZHSD.png" width="100px;" alt="Samuel"/><br>
        <b>Samuel</b>
      </a>
      <br>
      Desenvolvedor
    </td>
  </tr>
</table>

</div>
