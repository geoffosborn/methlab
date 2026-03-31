# MethLab — Go-to-Market Strategy

## Executive Summary

MethLab is positioned as the **independent satellite verification layer for Australian coal mine methane reporting**. No existing product — commercial or open source — offers NGER-aligned, facility-level satellite methane monitoring for Australian coal mines. The regulatory environment is creating forced buyer demand: Method 1 estimation is being phased out, Method 2 is under review for systemic flaws, and the government has established an Expert Panel to integrate satellite-based measurement into NGER.

---

## Market Context

### The Regulatory Driver

The Climate Change Authority's second review of NGER legislation made 25 recommendations (all accepted by government), including:

- **Phase out Method 1** (state-average emission factors) for open-cut coal mine fugitive emissions "as a matter of urgency"
- **Review Method 2** sampling requirements and standards to ensure they are "fit for purpose"
- **Establish an Expert Panel** on atmospheric measurement of fugitive methane emissions

The Expert Panel — chaired by former Chief Scientist Dr Cathy Foley — is specifically advising on how satellite, airborne, and ground-based "top-down" measurement can be integrated into the NGER scheme and National Greenhouse Accounts.

### Regulatory Timeline

| Date | Event |
|------|-------|
| 2023 | CCA review of NGER legislation (25 recommendations) |
| Aug 2024 | Government response — accepted all recommendations |
| 1 Jul 2025 | Method 1 phase-out begins (Safeguard mines >10Mt) |
| Aug 2025 | Expert Panel webinar — satellite can capture ~90% of facility-level emissions |
| 1 Jul 2026 | ALL Safeguard Mechanism open-cut mines must use Method 2 or 3 |
| 31 Oct 2026 | First reports due under new rules (FY2025-26) |
| TBD (~2027-28) | Expert Panel final recommendations on satellite integration into NGER |

### Evidence of Systemic Underreporting

Multiple independent studies using satellite and airborne data consistently show massive discrepancies with operator-reported figures:

| Study | Finding |
|-------|---------|
| Sadavarte et al. 2021 (TROPOMI, Bowen Basin) | 6 QLD mines = 7% of national production but 55% of reported coal mining methane |
| UNSW airborne study 2025 (Hail Creek) | Emissions 3–8x higher than operator-reported annual average |
| Ember analysis (TROPOMI, 79% of AU black coal) | 40% more methane than officially reported; NSW at 2x state-reported levels |
| IEA revised estimate | Increased AU coal mine methane estimate by 59% after satellite evidence |
| IEEFA "Coalmine Methane Mirage" | Major NSW miners reported 80% lower methane after switching to Method 2 |

Notable: Adani's Carmichael mine earned 351,232 Safeguard Mechanism Credits worth $12.3M in FY2023-24 without undertaking any emissions reduction activities.

### Method 2 Flaws (IEEFA findings)

The method mines are being forced onto is itself deeply flawed:

- Artificially high gas detection thresholds
- Nitrogen contamination in test samples
- Insufficient sampling requirements
- Gas proportion variability of +/-50% making monthly sampling unrepresentative
- BMA mines (Peak Downs, Saraji, Caval Ridge) reported 96% below Method 1 — implausibly low
- BHP Mount Arthur reported 97% below Method 1; NSW EPA flagged nitrogen contamination

---

## Competitive Landscape

### No one owns this space

| Competitor | What they do | Why they don't compete |
|------------|-------------|----------------------|
| GHGSat ($179M raised, ~$20M rev) | Proprietary satellite constellation, 25m resolution | O&G focused, $200K+/facility, no NGER integration, no AU coal product |
| Kayrros ($84M raised, 80 customers) | TROPOMI-based global methane platform | European HQ, no AU presence, no coal-specific offering |
| Open Methane (Superpower Institute) | Continent-scale TROPOMI analysis | 10km resolution — advocacy tool, not facility-level compliance |
| Carbon Mapper | Free point-source detection via Tanager-1 satellite | US nonprofit, no AU coal coverage priority, non-commercial license |
| Ember Climate | Coal mine methane datasets and analysis (CC BY 4.0) | Think tank, not a monitoring service — potential partner |
| Orbio Earth (YC S23, $4M seed) | Sentinel-2 methane detection models | O&G for finance customers, non-commercial license, no AU presence |

### Consulting firms (channel partners, not competitors)

These firms advise on NGER compliance but have no satellite data capability:

- **Anthesis Group** — registered NGER auditors, former CER Audit Panel members
- **Earth Systems** — mine site NGER compliance services
- **Arche Energy** — Safeguard Mechanism advisory for coal mining
- **ERM, SLR Consulting, SRK Consulting** — broader environmental/mining consultancies

They need data inputs, not another consulting competitor. They are the channel to mine operators.

---

## Product Positioning

**MethLab = independent satellite verification for Australian coal mine methane reporting.**

Not a replacement for NGER Methods 2/3 (ground sampling), but the **top-down verification layer** that the Expert Panel is building the framework for. The product mines will need when the government mandates cross-checking bottom-up estimates against satellite observations.

### Competitive Moat

| Advantage | Detail |
|-----------|--------|
| NGER-native | Purpose-built for Australian regulatory context. No competitor offers this. |
| Dual-sensor | TROPOMI (broad screening) + Sentinel-2 (facility-level plume detection). Most competitors use one or the other. |
| Published methods | Varon IME and wind-rotated enhancement are peer-reviewed. No proprietary black box. |
| Price point | 5–10x cheaper than GHGSat. Free satellite data (Copernicus) means low marginal cost per facility. |
| Australian | Local company, local data, local regulatory expertise. Government procurement preference. |

---

## Business Opportunities

### 1. Compliance Monitoring SaaS — B2B to mine operators

**Value proposition:** "Your Method 2 numbers say 0.002 tCO2e/t. Satellite says 0.06. The CER will have satellite data soon — wouldn't you rather know first?"

**What we sell:**
- Per-facility monitoring dashboard (TROPOMI screening + Sentinel-2 plume detection)
- Monthly/quarterly reports comparing satellite-derived emissions vs NGER-reported figures
- NGER baseline breach alerts (early warning before CER audits)
- Trend analysis showing whether emissions track within Safeguard decline trajectory (4.9%/yr)

**Target market:** ~50–70 coal mines under the Safeguard Mechanism (>100,000 tCO2e/year). Initially target the top 20 emitters — highest exposure to Safeguard credit liabilities and regulatory scrutiny.

**Pricing:** $50–100K/facility/year. At 20 facilities = $1–2M ARR.

**Pricing justification:**
- ACCU purchase costs if baselines exceeded: $30–35/tCO2e
- One audit clawback dwarfs monitoring costs
- GHGSat charges significantly more with no NGER integration
- Insurance framing: know your real exposure before the regulator does

**Dollar case for a 5Mt/yr mine:**
- Reported emissions (Method 2, potentially understated): ~50,000 tCO2e
- Actual emissions (satellite-derived): ~150,000 tCO2e
- Safeguard baseline (2025-26): ~130,000 tCO2e, declining 4.9%/yr
- Exposure if CER audits using satellite data: 20,000+ tCO2e × $35/ACCU = **$700K+/yr**
- MethLab monitoring cost: **$75K/yr**

### 2. Verification-as-a-Service — B2B to consultancies and regulators

**Value proposition:** "Your clients are switching from Method 1 to Method 2. Here's independent satellite data to validate their numbers before the CER does."

**What we sell:**
- API access to facility-level satellite emissions estimates
- White-label reports for consulting firms to include in NGER audit submissions
- Bulk portfolio monitoring for firms managing 10+ mine clients
- Historical baseline analysis (satellite record vs reported NGER history)

**Target market:**
- Environmental consultancies (Anthesis, Earth Systems, Arche Energy, ERM, SLR)
- Clean Energy Regulator / DCCEEW (audit verification, policy evaluation)
- Financial institutions and insurers (ESG due diligence on coal assets)

**Pricing:** $20–40K/year per consultancy seat + per-facility query fees. Government contracts via procurement.

**Why this works:** Consulting firms are the existing channel to mine operators. Partnering avoids the hard sell to miners. They have client relationships; we have data they can't produce.

### 3. Expert Panel Alignment — strategic positioning

Not a product — a positioning play. The Expert Panel's recommendations will define what "acceptable" satellite-based verification looks like for NGER. Being aligned with their methodology gives regulatory credibility.

**Actions:**
- Submit to public consultation processes the Expert Panel opens
- Publish methodology documentation showing alignment with published literature (Varon IME for S2, wind-rotated enhancement for TROPOMI — both already in MethLab)
- Engage with panel members' institutions (UNSW — A/Prof Bryce Kelly; FEnEx CRC — Prof Eric May)
- Position MethLab as an implementation of whatever the panel recommends

**Why it matters:** When the government mandates satellite verification (~2027–2028), the provider whose methodology aligns with the Expert Panel's framework wins the market by default.

---

## Go-to-Market Sequence

### Phase 1: Build Credibility (Now → Q3 2026)

- Complete backend pipeline (TROPOMI + S2 processing for AU coal mines)
- Produce verification reports for 5–10 high-profile mines using public satellite data
- Publish findings (blog/whitepaper) showing discrepancies — following Ember/IEEFA's lead
- Approach Ember for data partnership (their CC BY 4.0 mine database + our monitoring)
- Engage with Expert Panel process

### Phase 2: First Revenue (Q3 2026 → Q1 2027)

- Target 2–3 environmental consultancies as channel partners (Anthesis, Earth Systems)
- Offer pilot monitoring packages at reduced rate to 5 mine operators
- Align with Expert Panel methodology as recommendations emerge
- Leverage first Method 2/3 reporting deadline (31 Oct 2026) as demand driver

### Phase 3: Scale (2027+)

- Full SaaS product launch
- API platform for consultancy integration
- Expand to oil & gas facilities under Safeguard Mechanism
- Position for government procurement as satellite verification becomes mandated

---

## Key Risks and Mitigations

| Risk | Mitigation |
|------|-----------|
| Satellite resolution limits (TROPOMI ~7km, S2 ~20m SWIR) | Position as screening + verification, not primary measurement. Complement ground methods. |
| Expert Panel recommends airborne over satellite | Support multi-modal approach. Satellite = continuous/cheap baseline; airborne = periodic calibration. |
| GHGSat enters AU coal market | They'd price at $200K+/facility. Compete on price, NGER integration, and local expertise. |
| Mine operators resist transparency | Regulatory hammer is coming regardless. Sell "know before the CER knows" not "be transparent." |
| Method 2 gaming continues | The bigger the gap between reported and satellite-observed, the more valuable independent verification becomes. |

---

## Key References

### Expert Panel
- DCCEEW page: https://www.dcceew.gov.au/climate-change/emissions-reporting/national-greenhouse-energy-reporting-scheme/expert-panel-atmospheric-measurement-fugitive-methane-emissions-au
- Terms of Reference: https://www.dcceew.gov.au/about/news/expert-panel-fugitive-methane-emissions-tor

### CCA Review & Government Response
- Government response (PDF): https://www.dcceew.gov.au/sites/default/files/documents/government-response-cca-nger-review.pdf

### Underreporting Studies
- Sadavarte et al. 2021 (TROPOMI, Bowen Basin): https://pmc.ncbi.nlm.nih.gov/articles/PMC8698155/
- UNSW Hail Creek airborne study: https://pubs.acs.org/doi/10.1021/acs.estlett.4c01063
- Ember analysis: https://ember-energy.org/latest-insights/tackling-australias-coal-mine-methane-problem/
- IEEFA "Coalmine Methane Mirage": https://ieefa.org/resources/australias-coalmine-methane-mirage-urgent-need-accurate-emissions-reporting

### Other Resources
- UNEP-IMEO AU study ($5.5M AUD): https://www.unep.org/news-and-stories/press-release/unep-australia-announce-landmark-study-improve-understanding-coal
- Open Methane: https://openmethane.org/
- Superpower Institute Roadmap: https://www.superpowerinstitute.com.au/work/national-emissions-monitoring-roadmap
- Ember CMM Data Tracker: https://ember-energy.org/data/coal-mine-methane-data-tracker/
- Carbon Mapper API: https://api.carbonmapper.org/api/v1/docs
- CER Coal Mining Guideline: https://cer.gov.au/document/estimating-emissions-and-energy-coal-mining-guideline
