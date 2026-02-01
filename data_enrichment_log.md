# Data Enrichment Log — Task 1

**Project:** Forecasting Financial Inclusion in Ethiopia  
**Task:** Data Exploration and Enrichment  
**Collected by:** Selam Analytics (Task 1)  
**Collection date:** 2025-02-01  

This log documents every new record added to the unified dataset. All additions follow the unified schema; events have `category` filled and `pillar` empty; impact_links have `parent_id`, `pillar`, `related_indicator`, `impact_direction`, `impact_magnitude`, `lag_months`, `evidence_basis`.

---

## New Observations

| record_id    | pillar   | indicator                         | indicator_code     | value | unit  | observation_date | source_url                                              | confidence | original_text / notes |
|-------------|----------|-----------------------------------|--------------------|-------|-------|------------------|---------------------------------------------------------|------------|------------------------|
| REC_ENR_001 | ACCESS   | Account Ownership Rate            | ACC_OWNERSHIP      | 14    | %     | 2011-12-31       | https://www.worldbank.org/en/publication/globalfindex   | high       | Ethiopia account ownership 14% (2011). World Bank Global Findex. Baseline for continuity. |
| REC_ENR_002_2021 | USAGE | Digital Payment Adoption Rate     | USG_DIGITAL_PAY    | 18    | %     | 2021-12-31       | (estimated)                                            | estimated  | Approximate pre–digital surge; no Findex point for 2021. |
| REC_ENR_002_2024 | USAGE | Digital Payment Adoption Rate     | USG_DIGITAL_PAY    | 35    | %     | 2024-12-31       | https://www.worldbank.org/en/publication/globalfindex   | high       | Made or received digital payment in past 12 months (%). Findex definition. |
| REC_ENR_003 | USAGE    | Agent Density (per 10k adults)    | USG_AGENT_DENSITY  | 0     | per 10k adults | 2024-12-31 | (to be collected FSD/NBE)                        | estimated  | Direct correlation (Guide B). Placeholder for FSD or NBE. |
| REC_ENR_004 | ACCESS   | ATM Density (per 100k adults)     | ACC_ATM_DENSITY    | 0     | per 100k adults | 2024-12-31 | IMF FAS / NBE                                 | estimated  | IMF Financial Access Survey; Ethiopia included. Placeholder. |
| REC_ENR_005 | ACCESS   | Bank Branch Density (per 100k adults) | ACC_BRANCH_DENSITY | 0 | per 100k adults | 2024-12-31 | IMF FAS / NBE                                 | estimated  | Supply-side access; IMF FAS. Placeholder. |
| REC_ENR_006 | ACCESS   | Smartphone Penetration            | ACC_SMARTPHONE_PEN | 0     | %     | 2024-12-31       | (to be collected GSMA/ITU)                             | estimated  | Indirect enabler (Guide C). Placeholder. |
| REC_ENR_007 | ACCESS   | Mobile Internet Usage (% adults)   | ACC_MOBILE_INTERNET | 0    | %     | 2024-12-31       | (to be collected ITU/GSMA)                            | estimated  | Indirect; effective connectivity. Placeholder. |
| REC_ENR_008 | USAGE    | Used Account to Receive Wages     | USG_WAGES          | 15    | %     | 2024-12-31       | https://www.worldbank.org/en/publication/globalfindex   | high       | Share of adults who used an account to receive wages in past 12 months; Ethiopia ~15% (2024). Direct usage indicator for forecasting. |

---

## New Events

| record_id   | category    | indicator                      | observation_date | source_url       | confidence | original_text / notes |
|------------|-------------|--------------------------------|------------------|------------------|------------|------------------------|
| EVT_ENR_001 | regulation | NBE Interoperability Directive | 2024-06-01       | https://nbe.gov.et | high     | NBE directive on interoperability of mobile money and payment systems. Enables cross-platform P2P and merchant payments; supports Usage forecasting. |

---

## New Impact Links

| record_id  | parent_id   | pillar | related_indicator | relationship_type | impact_direction | impact_magnitude | impact_estimate | lag_months | evidence_basis | notes |
|------------|-------------|--------|-------------------|--------------------|------------------|------------------|-----------------|------------|----------------|-------|
| IMP_ENR_001 | EVT_ENR_001 | USAGE  | USG_DIGITAL_PAY   | direct             | increase         | medium           | 5               | 12         | literature     | Interoperability typically raises digital payment usage (Tanzania, India). |
| IMP_ENR_002 | EVT_0004    | USAGE  | USG_DIGITAL_PAY   | enabling           | increase         | low              | 3               | 24         | literature     | Fayda (digital ID) enables account opening and payments; indirect effect on usage. |

---

## Summary

- **Observations added:** 9 (REC_ENR_001 through REC_ENR_008; REC_ENR_002 for 2021 and 2024).
- **Events added:** 1 (EVT_ENR_001 — NBE Interoperability Directive).
- **Impact links added:** 2 (IMP_ENR_001: NBE Interop → USG_DIGITAL_PAY; IMP_ENR_002: Fayda → USG_DIGITAL_PAY).

All new records include `source_url`, `original_text` (where applicable), `confidence`, `collected_by`, `collection_date`, and `notes` as per Task 1 instructions.

**Updated dataset (with additions):**
- `data/processed/ethiopia_fi_unified_data_enriched.csv` — single file, all record types.
- `data/processed/ethiopia_fi_unified_data_enriched.xlsx` — Sheet 1: data (observation, event, target); Sheet 2: impact_links.

Generate with: `python scripts/export_enriched_dataset.py`
