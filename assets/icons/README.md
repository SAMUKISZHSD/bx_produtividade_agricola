# SojaRisco — acervo de assets SVG

Ícones vetoriais para substituir emojis no dashboard Streamlit.

## Paleta
- Verde-floresta `#153D2B`
- Verde principal `#2E7D32`
- Verde claro `#81C784`
- Fundo `#F4F6F2`
- Destaque solar `#F9A825`

## Arquivos
dashboard, soybean, field, weather, rain, sun, drought, thermometer,
shield, alert, brain, history, database, chart_line, chart_bar,
calendar, location, settings, info, water, refresh e sojarisco_logo.

## Uso
Coloque os SVGs em `assets/icons/` e use:
```python
from pathlib import Path
import streamlit as st

ASSETS = Path(__file__).parent / "assets" / "icons"
st.image(str(ASSETS / "sojarisco_logo.svg"), width=240)
st.image(str(ASSETS / "weather.svg"), width=36)
```
Os SVGs são vetoriais e podem ser redimensionados sem perder qualidade.
