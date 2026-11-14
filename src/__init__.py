"""Módulo da Arquitetura de 4 Camadas do Projeto SojaRisco (Trilha C).

Camada 1 (CD): Coleta e Ingestão Idempotente (NASA POWER Daily + IBGE PAM 1612)
Camada 2 (AD): Engenharia de Atributos Agronômicos (Jan-Fev) e Split Temporal
Camada 3 (ML): Pipeline Scikit-Learn (ColumnTransformer + Classificadores)
Camada 4 (PROD): Persistência Relacional SQLite (3 tabelas encadeadas) e Dashboard
"""

