Role: You are a senior market data architect writing a concise, practitioner-grade overview of trading instrument reference data for front-office, risk, and post-trade engineers.

Deliverable:
- A 8–12 page Markdown document with tables + one Mermaid diagram.
- Tone: technical, neutral, precise. Short paragraphs and bullet points.
- Include inline citations in brackets, e.g., [Source: ESMA, 2025, FIRDS].
- End with a one-page glossary of identifiers.

Scope & structure (use these section headings):

1) Taxonomy & scope
- Define “listed/vanilla securities” (equities, funds, corporate/sovereign debt) vs. “derivatives” (ETD: futures/options; OTC: swaps, forwards).
- Distinguish “pricing securities” vs. “trading securities” datasets: evaluated pricing vs. executable/tradable symbology; valuation vs. order-routing fields. Tie to IFRS/ASC fair-value hierarchy.

2) Core reference fields (by asset class)
- Equity, fund, fixed income, ETD, OTC IRD/CRD/FX/CD: issuer, instrument, listing, venue, trading rules, settlement, clearing, regulatory flags.
- Static vs. dynamic attributes; lifecycle states (when-issued, active, suspended, delisted); corporate actions impacts on IDs (splits, spins, mergers).

3) Identifier hierarchy & governance (the heart of the doc)
- **Issuer-level (“who is who / who owns whom”)**: LEI (ISO 17442, Level1/Level2 parent relationships), SEC CIK (US filers).
- **Issue-level (global)**: ISIN (ISO 6166), CFI (ISO 10962), FISN (ISO 18774), FIGI (open symbology).
- **Issue+listing level**: for accounting and asset servicing e.g. tracking unique positions across cororate actions.
- **Listing / venue-level**: Tickers, RICs, Bloomberg tickers, SEDOL (LSEG), CUSIP/CINS (CGS), Market Identifier Code (MIC & Segment MIC, ISO 10383).
- **Derivative product-level**: 
  - ETD: exchange product codes (e.g., CME/Eurex/ICE), contract identifiers; options: OCC/OSI symbology; ISINs for ETD where assigned by NNA.
  - OTC: UPI (ISO 4914) + UTI (ISO 23897) for trade reporting; UTI ≠ instrument ID.
- **Regulatory datasets**: ESMA FIRDS/FITRS (EU), EMIR/UK EMIR reporting fields; mapping to ISIN/CFI/MIC.

4) Cross-identifier “symbology” crosswalks
- Present a normalized crosswalk table: {Issuer: LEI, CIK} → {Issue: ISIN, CFI, FISN, FIGI} → {Listing: MIC, local ticker, RIC, SEDOL, CUSIP/CINS} → {Derivatives: exchange code, OCC/OSI, ISIN (where applicable)} → {Reporting: UPI, UTI}.
- Note governance, scope, typical change drivers, licensing/access constraints.

5) “Pricing vs trading” data model
- Pricing: evaluated prices, curves, methodologies; IFRS 13 / ASC 820 level classification; pricing vendor IDs; close vs. executable.
- Trading: venue MIC/segment MIC, tick size, lot size, currency, trading calendar, LULD bands (US), clearing product codes; symbol normalization for OMS/EMS/SOR.

6) Common challenges & control patterns
- Cross-listing & DR/local line collisions; fungibility & ISIN re-use rules; symbol churn (ticker/SEDOL/CUSIP changes) vs. persistence of LEI/ISIN; exchange segment MIC vs. operating MIC.
- Golden-source strategy, symbology mapping/match rules, survivorship keys, CA-driven re-identification, audit trails.
- Quality controls: completeness, uniqueness, referential integrity, lineage; exception dashboards.

7) Worked mini-example (no PII)
- Pick one large-cap equity and one liquid future; show issuer→issue→listing→derivative mapping, with citations to GLEIF/SEC/exchange.

8) Implementation appendix
- Minimal canonical JSON for an instrument (issuer block, issue block, listing block, derivatives block); include keys, change events.
- Ingestion sources: regulatory (FIRDS), numbering agencies (ANNA/DSB), GLEIF; operational playbook for daily deltas.

Tables to include (mandatory):
- **Identifier dictionary** (columns: Layer, Standard/ID, Governing body, Scope, Example, Change frequency, Primary uses).
- **Trading vs Pricing fields** (columns: Domain, Field, Purpose, Source of truth, Usage (pre/post-trade)).
- **Corporate action impacts** (Action, Which IDs change?, Notes).

Diagram (mandatory):
- Mermaid diagram of identifier hierarchy and data lineage: LEI/CIK → ISIN/CFI/FISN/FIGI → (MIC, ticker, RIC, SEDOL, CUSIP) → Derivatives (Exchange Codes, OSI/ISIN) → Reporting (UPI, UTI).

Style & constraints:
- Keep it concise; prefer bullets; no vendor promotion; cite standards/regulators first.
- Where identifiers are proprietary (e.g., CUSIP, SEDOL, RIC), state access/licensing constraints briefly.
- Use accurate examples and validate via official sources listed below.

Authoritative sources to cite inside the document:
- LEI & relationships: GLEIF overview and Level 2 data pages [ISO 17442]. 
- ISIN: ISO 6166 + ANNA ISIN Guidelines (Dec 2023). 
- CFI & FISN: ISO 10962 / ISO 18774; ANNA/DSB references.
- MIC: ISO 10383 (SWIFT RA).
- UPI: ISO 4914; ANNA-DSB UPI service launch.
- UTI: ISO 23897; CPMI-IOSCO technical guidance; FSB governance note; UK EMIR technical standard.
- ESMA FIRDS / transparency: ESMA registers.
- OCC/OSI & OPRA references for options symbology.
- Exchange product code examples: CME/Eurex/ICE product pages.

Acceptance criteria:
- Every identifier introduced has: definition, layer, steward, scope, example, and change semantics.
- Clear distinction between “pricing securities” and “trading securities” datasets with IFRS/ASC fair-value linkage.
- One crosswalk table and one hierarchy diagram are present.
- All key claims are footnoted to the authoritative sources above.
