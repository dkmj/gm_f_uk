# Klimatbudget Uppsala — Visualiseringsverktyg

Gapminder-inspirerat pedagogiskt verktyg för att visualisera och
förstå Uppsalas klimatbudget.

## Funktioner

- **Bubbeldiagram** — interaktiv D3.js-visualisering av utsläpp per sektor
- **Quiz** — testa uppfattningar om klimatdata i Gapminder-stil
- **Datakällor** — transparens kring var data kommer ifrån

## Kom igång

### Webbappen

Öppna `index.html` i en webbläsare, eller besök den publicerade
GitHub Pages-sidan.

### Uppdatera data

Kräver Python och uv:

    uv sync
    uv run scripts/fetch_scb.py
    uv run scripts/fetch_nvv.py

## Teknik

- HTML/CSS/JavaScript (ingen ramverk)
- D3.js v7 för visualisering
- Python för datapipeline
- GitHub Pages för hosting
