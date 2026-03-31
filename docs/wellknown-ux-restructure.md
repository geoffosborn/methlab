# WellKnown UX Restructure: Narrative-Driven Navigation

**Date:** 2026-03-30
**Status:** Proposed
**Author:** Geoff Osborn / GeoSynergy

---

## Problem

WellKnown Explorer crams four distinct user workflows into one 7-tab interface:
- Well register / data catalogue
- Subsurface modelling & analysis
- Model visualisation
- Emissions monitoring & compliance

Different users (geologist, engineer, compliance officer) all navigate the same tabs, most of which are irrelevant to them. There's no narrative arc — a demo walks through disconnected data types rather than telling a story.

Production data — critical for material balance — is buried in charts rather than having its own prominence.

## Proposed Structure

Restructure around the **King (1993) material balance narrative**: "Where does the gas go?"

### Four sections, left-to-right

```
┌─────────────┐   ┌─────────────┐   ┌─────────────┐   ┌─────────────┐
│  RESERVOIR   │ → │ PRODUCTION  │ → │ MONITORING   │ → │  BALANCE    │
│              │   │             │   │              │   │             │
│ "What's in   │   │ "What are   │   │ "What can we │   │ "Does it    │
│  the ground?"│   │  you        │   │  see from    │   │  add up?"   │
│              │   │  capturing?"│   │  space?"     │   │             │
└─────────────┘   └─────────────┘   └─────────────┘   └─────────────┘
     OGIP              Drained          Fugitive         Closure error
    (1st bar)         (2nd bar)        (3rd bar)        (the punchline)
```

Each section feeds the next. The material balance waterfall is the visual thread — each section contributes a bar.

---

### 1. RESERVOIR — "What's in the ground?"

*The geological foundation. Sets the scene.*

**Content (from current Tabs 1-5):**
- Well register (browse, search, filter wells)
- Well documents and test data
- Seam properties / gas content scatter plots
- Voxel model viewer (3D gas-in-place)
- Sweet spots and strike direction
- WMS layer overlays

**Key metric:** OGIP (TJ) — Original Gas In Place from the reservoir model

**Sub-navigation:**
- Wells (register + documents)
- Seams (scatter + gas content)
- Model (voxel viewer + WMS)
- Analysis (sweet spots + strike)

---

### 2. PRODUCTION — "What are you capturing?"

*The operator's story. What they report and control.*

**Content (currently scattered/hidden):**
- Monthly/quarterly production curves
  - ROM coal tonnage
  - Gas drainage volumes (pre-drainage, goaf drainage)
  - Gas captured / flared / utilised
  - Gas sales
- Cumulative production over project life
- Production vs plan comparison
- Per-facility production breakdown

**Key metric:** Cumulative Drained (TJ) — gas removed from the reservoir

**Data sources:**
- CNPC import (Bowen Basin)
- Well test / production data from well register
- NGER production/drainage summary
- Manual entry (operator-provided)

**Note:** This section needs a data ingestion workflow — currently production data is patchy. Could support CSV upload, NGER data import, or API integration with mine planning systems.

---

### 3. MONITORING — "What can we see from space?"

*The independent verification. Satellite evidence.*

**Content (from current Tab 7, expanded):**
- Facility map with project AOI and satellite basemap
- Likely emitters list (prioritised by TROPOMI intensity)
- TROPOMI wind-rotated tear sheets per facility
  - Quarterly time series
  - Enhancement trends
- Sentinel-2 plume detections
  - Detection count, rates, confidence
  - Temporal distribution
- Carbon Mapper point sources (where available)
- Assessment status per facility (analysed / needs analysis)

**Key metric:** Estimated Annual Fugitive Emission (TJ) — satellite-derived

**Sub-navigation:**
- Overview (facility map + summary stats)
- TROPOMI (tear sheets + trends)
- Detections (S2 + Carbon Mapper)
- Assessment (likely emitters + action list)

---

### 4. BALANCE — "Does it add up?"

*The punchline. Where the story lands.*

**Content (from current Tab 7, elevated to its own section):**
- Material balance waterfall: OGIP → Drained → Ventilated → Fugitive → Remaining
- Closure error percentage and interpretation
- NGER Reported vs Satellite Observed comparison
  - Gap ratio (e.g., 1.4× — satellite sees 40% more than reported)
  - Horizontal bar comparison
- NGER method assessment (Method 1/2/3 status)
- Safeguard Mechanism exposure
  - Baseline vs actual
  - Credits potentially at risk
  - Regulatory timeline (M1 phase-out → M2 deadline → Expert Panel)
- Depletion efficiency over time (capture rate, fugitive fraction)
- VAM configuration panel
- Export report button — generates the formal assessment document

**Key metric:** Closure Error (%) — the gap that tells the story

**Sub-navigation:**
- Waterfall (the centrepiece)
- Compliance (NGER gap + Safeguard)
- Trends (efficiency over time)
- Report (export)

---

## Demo Flow

Walk left-to-right through the four sections:

> **[Reservoir]** "24 coal mines in the Arrow Bowen project, sitting on deep metallurgical seams. High gas content — 8-12 m³/tonne. The reservoir model shows X TJ of gas in place."
>
> **[Production]** "Here's what's being captured — drainage wells pulling Y TJ per year. Some goes to gas sales, some flared. This is what the operators report to the CER."
>
> **[Monitoring]** "Now here's what the satellites see. TROPOMI shows persistent methane enhancement over these 5 facilities. Hail Creek — known superemitter per Ember research. Grosvenor reports 36% below baseline, but the satellite disagrees."
>
> **[Balance]** "When we close the material balance, there's a 40% gap. That gap represents Z TJ of unreported fugitive emissions. At current ACCU prices, that's $X million in Safeguard credits potentially incorrectly claimed. The Expert Panel is recommending satellite data be integrated into NGER by 2027-28. We're already doing it."

---

## Implementation Approach

### Phase 1: Navigation restructure (UI only)
- Replace 7-tab Explorer with 4-section navigation
- Move existing components into their new sections
- No backend changes — same data, same APIs
- Add section landing pages with summary cards

### Phase 2: Production section (new)
- Design production data model (monthly ROM, drainage, gas sales)
- Build production data entry / CSV import
- Production charts and per-facility breakdown
- Connect to material balance (currently uses placeholder data)

### Phase 3: Monitoring enhancements
- Likely Emitters API endpoint (from earlier plan)
- Assessment workflow (run TROPOMI analysis from UI)
- Multi-facility comparison view

### Phase 4: Balance section polish
- Standalone balance page with full waterfall
- Compliance scorecard
- Automated report generation (PDF)
- Safeguard credit risk calculator

---

## Current Tab → New Section Mapping

| Current Tab | Content | New Section |
|-------------|---------|-------------|
| Tab 1: Wells | Well register, documents | Reservoir → Wells |
| Tab 2: Seams | Seam scatter plots | Reservoir → Seams |
| Tab 3: Models | Voxel model viewer | Reservoir → Model |
| Tab 4: Sweet Spots | Sweet spot analysis | Reservoir → Analysis |
| Tab 5: Strike | Strike direction | Reservoir → Analysis |
| Tab 6: WMS | GeoServer layers | Reservoir → Model |
| Tab 7: Fugitive Methane | Everything emissions | Split across Monitoring + Balance |
| (hidden) | Production data | Production (new section) |

---

## References

- King, G.R. (1993). Material Balance Techniques for Coal-Seam and Devonian Shale Gas Reservoirs. SPE-20730.
- Saghafi, A. (2012). A Tier 3 method to estimate fugitive gas emissions from surface coal mining. Int. J. Coal Geology, 100, 14-25.
- Sadavarte et al. (2021). Methane emissions from superemitting coal mines in Australia quantified using TROPOMI satellite observations.
- CCA (2023). Review of the National Greenhouse and Energy Reporting legislation. 25 recommendations.
- Expert Panel on Atmospheric Measurement of Fugitive Methane Emissions (established 2024).
