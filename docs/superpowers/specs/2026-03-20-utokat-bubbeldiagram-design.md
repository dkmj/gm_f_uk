# Utökat bubbeldiagram — dynamiska axlar, fler datakällor och animation

**Datum:** 2026-03-20
**Status:** Design godkänd
**Projekt:** gm_f_uk (Gapminder för Uppsala kommun)
**Baseras på:** `docs/superpowers/specs/2026-03-20-klimatbudget-visualiseringsverktyg-design.md`

## 1. Syfte

Utöka det befintliga bubbeldiagrammet med:
- Fler dimensioner från SCB (befolkning, fordon, energi, byggnader, kollektivtrafik, jordbruk)
- Användarval av vilka dimensioner som visas på X-axel, Y-axel och bubbelstorlek
- Gapminder-stil play/pause-animation genom åren

## 2. Datamodell

### 2.1 Gemensamt format

Alla dimensioner normaliseras till ett gemensamt format per klimatbudgetområde och år i en samlad fil `data/bubble_data.json`:

```json
{
  "metadata": {
    "generated": "2026-03-20",
    "dimensions": {
      "co2e_kton": {"label": "CO₂e-utsläpp (kton)", "unit": "kton", "description": "Territoriella växthusgasutsläpp"},
      "share_pct": {"label": "Andel av totala utsläpp (%)", "unit": "%", "description": "Sektorns andel av kommunens totala utsläpp"},
      "population": {"label": "Befolkning", "unit": "invånare", "description": "Uppsalas folkmängd"},
      "co2e_per_capita": {"label": "CO₂e per capita (ton)", "unit": "ton/invånare", "description": "Utsläpp per invånare"},
      "vehicles_total": {"label": "Antal fordon", "unit": "fordon", "description": "Personbilar i trafik i kommunen"},
      "vehicles_electric_pct": {"label": "Andel elbilar (%)", "unit": "%", "description": "Andel laddbara fordon av totala fordonsflottan"},
      "energy_gwh": {"label": "Energianvändning (GWh)", "unit": "GWh", "description": "Total energianvändning"},
      "building_area_m2": {"label": "Bostadsyta (tusen m²)", "unit": "tusen m²", "description": "Total bostadsyta i kommunen"},
      "new_construction_units": {"label": "Nybyggda lägenheter", "unit": "lägenheter", "description": "Färdigställda lägenheter per år"},
      "public_transport_trips": {"label": "Kollektivtrafikresor per invånare", "unit": "resor/invånare", "description": "Antal kollektivtrafikresor per invånare och år"},
      "agriculture_hectares": {"label": "Jordbruksmark (hektar)", "unit": "hektar", "description": "Åker- och betesmark i kommunen"}
    }
  },
  "data": [
    {
      "area": "Transport",
      "year": 2020,
      "co2e_kton": 285,
      "share_pct": 45.2,
      "population": 233839,
      "co2e_per_capita": 1.22,
      "vehicles_total": 98500,
      "vehicles_electric_pct": 8.2,
      "energy_gwh": 1250,
      "building_area_m2": null,
      "new_construction_units": null,
      "public_transport_trips": 142,
      "agriculture_hectares": null
    }
  ]
}
```

### 2.2 Dimensionskoppling till områden

Dimensioner som inte är relevanta för ett visst klimatbudgetområde sätts till `null`:

| Dimension | Transport | Energi | Bygg | Jord/skog | Konsumtion | Övriga |
|-----------|-----------|--------|------|-----------|------------|--------|
| co2e_kton | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| share_pct | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| population | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| co2e_per_capita | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |
| vehicles_total | ✓ | – | – | – | – | – |
| vehicles_electric_pct | ✓ | – | – | – | – | – |
| energy_gwh | – | ✓ | ✓ | – | – | – |
| building_area_m2 | – | – | ✓ | – | – | – |
| new_construction_units | – | – | ✓ | – | – | – |
| public_transport_trips | ✓ | – | – | – | – | – |
| agriculture_hectares | – | – | – | ✓ | – | – |

Axelväljaren visar bara dimensioner som har data för minst ett synligt (ej dolt via legendfilter) område.

### 2.3 Delade dimensioner

Befolkning och co2e_per_capita är kommungemensamma värden — samma siffra för alla områden. De fungerar som storlek- eller axelvärden men representerar inte sektorsspecifik data.

## 3. Komponentdesign

### 3.1 Layout — desktop (> 1024px)

```
┌──────────────────────────────────────────────────────────┐
│ Nav                                                       │
├──────────────────────────────────────────┬─────────────────┤
│                                          │ X-axel     [▼] │
│                                          │ Y-axel     [▼] │
│          Bubbeldiagram (~70%)            │ Storlek    [▼] │
│                                          │─────────────────│
│                                          │ ☑ Transport     │
│                                          │ ☑ Energi        │
│                                          │ ☑ Bygg          │
│                                          │ ☑ Jord/skog     │
│                                          │ ☑ Konsumtion    │
│                                          │ ☑ Övriga        │
├──────────────────────────────────────────┴─────────────────┤
│              ▶  2020  ━━━━━━━━━●━━━━━━                    │
└──────────────────────────────────────────────────────────────┘
```

### 3.2 Layout — mobil (< 1024px)

```
┌─────────────────────────┐
│ Nav (hamburger)          │
├─────────────────────────┤
│ X: [▼]  Y: [▼]  S: [▼] │
│ ● Tra ● Ene ● Byg ...  │
├─────────────────────────┤
│                          │
│    Bubbeldiagram (100%)  │
│                          │
├─────────────────────────┤
│  ▶  2020  ━━━━●━━━━     │
├─────────────────────────┤
│ [Detaljpanel vid tap]    │
└─────────────────────────┘
```

Dropdowns visas kompakt i fullbredd ovanför diagrammet. Legendfilter visas som korta etiketter med färgprickar.

### 3.3 Axelväljare

**Skaltyp:** Alla axlar använder `d3.scaleLinear()` — detta är en förändring från MVP:n som använde `d3.scaleBand()` med områdesnamn på X-axeln. Den nya versionen har numeriska värden på båda axlarna, precis som Gapminder.

Tre `<select>`-element:
- **X-axel** — alla numeriska dimensioner som har data
- **Y-axel** — alla numeriska dimensioner som har data
- **Storlek** — alla numeriska dimensioner + "Lika stor" (default)

**Dublettval:** Samma dimension får väljas på flera axlar (t.ex. X och Y båda satta till co2e_kton). Diagrammet visar då en diagonal linje — inte användbart men inte heller ett fel. Ingen validering behövs.

Standardvärden:
- X: co2e_kton
- Y: share_pct
- Storlek: population

När användaren byter dimension:
1. Axeletikett uppdateras
2. Skalor räknas om (domain baserat på all data över alla år och alla områden, inklusive dolda — detta håller skalorna stabila)
3. Bubblor animeras till nya positioner med D3 transition (500ms)
4. Bubblor vars valda dimension är `null` döljs tillfälligt

Dimensioner med `null` för alla synliga områden filtreras bort ur dropdown-listan.

### 3.4 Play/pause-animation

- **Knapp:** ▶ (play) / ⏸ (pause) placerad till vänster om slidern
- **Hastighet:** 1200ms per steg (800ms transition + 400ms paus)
- **Transitions:** D3 `.transition().duration(800)` för smooth rörelse, följt av 400ms statisk visning innan nästa steg
- **Beteende:**
  - Play: Stegar framåt från aktuellt år till sista året, sedan stoppar
  - Pause: Stoppar på aktuellt år
  - Slider-klick under play: Pausar automatiskt
  - Dropdown-byte under play: Pausar, uppdaterar, användaren kan trycka play igen
- **Årsvisning:** Stor siffra som uppdateras under animationen
- **Tillgänglighet:** Knappen har `aria-label` som uppdateras ("Spela animation" / "Pausa animation")

### 3.5 Tooltip och detaljpanel

Samma mönster som MVP:
- **Desktop:** Hover-tooltip med alla icke-null-dimensioner för bubblan
- **Mobil:** Tap → detaljpanel under diagrammet
- **Tangentbord:** Enter/Space visar detaljer

Tooltip visar nu fler rader — alla dimensioner som har värden för det området:
```
Transport (2020)
CO₂e: 285 kton
Andel: 45.2%
Fordon: 98 500
Elbilar: 8.2%
Kollektivtrafik: 142 resor/inv
```

### 3.6 Feltillstånd

- **Data kan inte laddas:** Visar "Data kunde inte laddas. Kontrollera att data/bubble_data.json finns." (Ersätter MVP:ns referens till nvv_kommun_co2.json.)
- **Inga synliga bubblor:** Om alla synliga områdens värden är `null` för valda axlar: "Ingen data tillgänglig för valda dimensioner. Prova att byta axel eller visa fler områden."
- **Bara ett år i data:** Play-knappen inaktiveras (disabled) med tooltip "Animering kräver data för flera år."

### 3.7 Datakällsprovenienshantering

Den nya `bubble_data.json` innehåller ett `sources`-fält i metadata som listar vilka källfiler som ingick:

```json
"metadata": {
  "generated": "2026-03-20",
  "sources": ["nvv_kommun_co2.json", "scb_dimensions.json"],
  "dimensions": { ... }
}
```

Detaljerad proveniensinfo finns kvar i `data/sources.json` — admin-vyn refererar dit.

### 3.8 Bakåtkompatibilitet

Den nya `bubble-chart.js` läser **enbart** `data/bubble_data.json`. Den gamla filen `data/nvv_kommun_co2.json` behålls (används av merge-skriptet som input) men bubbeldiagrammet refererar inte längre till den direkt.

## 4. Datapipeline

### 4.1 Nya skript

| Skript | Ansvar |
|--------|--------|
| `scripts/fetch_scb_dimensions.py` | Hämta alla nya dimensioner från SCB PxWeb API |
| `scripts/merge_bubble_data.py` | Slå ihop NVV + SCB + beräknade dimensioner → `data/bubble_data.json` |

### 4.2 SCB-tabeller att hämta

| Dimension | SCB-tabell | Tabell-ID (ungefärligt) |
|-----------|-----------|------------------------|
| Befolkning | Folkmängd per kommun | BE0101 |
| Fordonsflotta | Personbilar i trafik per drivmedel och kommun | TK1001 |
| Energianvändning | Kommunal energibalans | EN0203 |
| Byggnadsbestånd | Bostadsbestånd per uppvärmningssätt | BO0104 |
| Nybyggnation | Färdigställda lägenheter | BO0101 |
| Kollektivtrafik | Kollektivtrafikresor per kommun | TK0601 |
| Jordbruksmark | Åkerareal per kommun | JO0104 |

Exakta tabell-ID:n verifieras vid implementation genom SCB:s API-navigering.

### 4.3 Beräknade dimensioner

- `co2e_per_capita` = totala kommunala utsläpp (summa co2e_kton alla sektorer) × 1000 / population. Beräknas per år i merge-skriptet. Samma värde sätts på alla områden (kommungemensam dimension).

### 4.4 Årsintervall och saknad data

Alla dimensioner ska hämtas för åren **2015–2024** (samma som NVV-data). Om en SCB-dimension saknar data för vissa år:
- Merge-skriptet sätter `null` för de åren
- Bubblor med `null`-värden på vald axel döljs för det året
- Inga interpoleringar eller uppskattningar görs

### 4.5 Befintliga skript

`fetch_nvv.py`, `fetch_scb.py`, `fetch_klimatkollen.py` och `convert_excel.py` ändras inte. Merge-skriptet läser deras output-filer.

## 5. Filändringar

| Fil | Åtgärd |
|-----|--------|
| `scripts/fetch_scb_dimensions.py` | Ny — hämtar dimensioner från SCB |
| `scripts/merge_bubble_data.py` | Ny — sammanfogar data till bubble_data.json |
| `data/bubble_data.json` | Ny — samlad datafil för bubbeldiagrammet |
| `js/bubble-chart.js` | Skrivs om — dynamiska axlar, animation, sidopanel |
| `bubble.html` | Uppdateras — sidopanel-layout, play-kontroller |
| `js/admin.js` | Uppdateras — visa nya datakällor |
| `data/sources.json` | Uppdateras — nya SCB-källor |
| `tests/test_fetch_scb_dimensions.py` | Ny — tester för SCB-dimensionshämtning |
| `tests/test_merge_bubble_data.py` | Ny — tester för datasammanfogning |

## 6. Avgränsningar

| Inkluderat | Exkluderat (framtida) |
|------------|----------------------|
| Axelväljare (X, Y, storlek) | Datasetsväxlare (flera dataset) |
| Play/pause-animation | Trails/spår under animation |
| 7 nya SCB-dimensioner | Avfallsdata (kräver manuell hämtning) |
| Sidopanel (desktop) / dropdowns (mobil) | Klickbara axeletiketter (C-layout) |
| Tooltip med alla dimensioner | Jämförelse med andra kommuner |
| Dynamisk filtrering av tomma dimensioner | Logaritmiska skalor |

## 7. Tillgänglighet

Samma WCAG 2.1 AA-krav som MVP, plus:
- Dropdowns har `<label>`-element
- Play-knapp har uppdaterande `aria-label`
- Animationen respekterar `prefers-reduced-motion` (hoppar direkt istället för att animera)
- Sidopanelens checkboxar har korrekta `aria-checked`-attribut
- Tangentbordsgenvägar: Mellanslag på play-knappen togglar play/pause, piltangenter vänster/höger stegar ett år bakåt/framåt när slidern har fokus
