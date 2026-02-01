# Data Enrichment Log — Task 1

**Project:** Forecasting Financial Inclusion in Ethiopia  
**Task:** Data Exploration and Enrichment  
**Collected by:** Selam Analytics (Task 1)  
**Collection date:** 2025-02-01  

This log documents every new record added to the unified dataset. All records follow the **unified schema** (same column set).  
- **record_type logic:** `observation` = measured value; `event` = policy/launch/milestone (no pillar); `impact_link` = event→indicator relationship (has `parent_id` = event’s `record_id`).  
- **Pillar handling:** Observations have `pillar` set (ACCESS, USAGE, etc.). Events have `pillar` empty. Impact_links have `pillar` set to the pillar of the **indicator** they affect (`related_indicator`).  
- **parent_id:** Only on `impact_link` rows; value is the `record_id` of the event that causes the effect. Links are verified by matching `impact_link.parent_id` to `event.record_id`.

---

## 1. New observations

For each observation: pillar, indicator, indicator_code, value_numeric, observation_date, source_name, source_url, confidence, original_text, collected_by, collection_date, notes.

| record_id | record_type | pillar | indicator | indicator_code | value_numeric | unit | observation_date | source_name | source_url | confidence | original_text | collected_by | collection_date | notes |
|-----------|-------------|--------|-----------|----------------|---------------|------|------------------|-------------|------------|------------|---------------|---------------|-----------------|-------|
| REC_ENR_001 | observation | ACCESS | Account Ownership Rate | ACC_OWNERSHIP | 14 | % | 2011-12-31 | Global Findex 2011 | https://www.worldbank.org/en/publication/globalfindex | high | Ethiopia account ownership 14% (2011). World Bank Global Findex Database. | Selam Analytics (Task 1) | 2025-02-01 | Baseline year (Findex); added for continuity. |
| REC_ENR_002_2021 | observation | USAGE | Digital Payment Adoption Rate | USG_DIGITAL_PAY | 18 | % | 2021-12-31 | Estimated from Findex/operator context | (none) | estimated | (estimated) | Selam Analytics (Task 1) | 2025-02-01 | Approximate pre–digital surge; no Findex point for 2021. |
| REC_ENR_002_2024 | observation | USAGE | Digital Payment Adoption Rate | USG_DIGITAL_PAY | 35 | % | 2024-12-31 | Global Findex | https://www.worldbank.org/en/publication/globalfindex | high | Made or received digital payment in past 12 months (%). | Selam Analytics (Task 1) | 2025-02-01 | Findex: made or received digital payment (past 12 months). |
| REC_ENR_003 | observation | USAGE | Agent Density (per 10k adults) | USG_AGENT_DENSITY | 0 | per 10k adults | 2024-12-31 | To be collected – FSD / NBE | (to be collected) | estimated | Placeholder. | Selam Analytics (Task 1) | 2025-02-01 | Direct correlation (Guide B). Fill from FSD or NBE when available. |
| REC_ENR_004 | observation | ACCESS | ATM Density (per 100k adults) | ACC_ATM_DENSITY | 0 | per 100k adults | 2024-12-31 | IMF FAS / NBE | (IMF FAS) | estimated | Placeholder. | Selam Analytics (Task 1) | 2025-02-01 | IMF Financial Access Survey; Ethiopia included. Placeholder. |
| REC_ENR_005 | observation | ACCESS | Bank Branch Density (per 100k adults) | ACC_BRANCH_DENSITY | 0 | per 100k adults | 2024-12-31 | IMF FAS / NBE | (IMF FAS) | estimated | Placeholder. | Selam Analytics (Task 1) | 2025-02-01 | Supply-side access; IMF FAS. Placeholder. |
| REC_ENR_006 | observation | ACCESS | Smartphone Penetration | ACC_SMARTPHONE_PEN | 0 | % | 2024-12-31 | To be collected – GSMA / ITU | (to be collected) | estimated | Placeholder. | Selam Analytics (Task 1) | 2025-02-01 | Indirect enabler (Guide C). Placeholder. |
| REC_ENR_007 | observation | ACCESS | Mobile Internet Usage (% adults) | ACC_MOBILE_INTERNET | 0 | % | 2024-12-31 | To be collected – ITU / GSMA | (to be collected) | estimated | Placeholder. | Selam Analytics (Task 1) | 2025-02-01 | Indirect; effective connectivity. Placeholder. |
| REC_ENR_008 | observation | USAGE | Used Account to Receive Wages | USG_WAGES | 15 | % | 2024-12-31 | Global Findex 2024 | https://www.worldbank.org/en/publication/globalfindex | high | Share of adults who used an account to receive wages in the past 12 months; Ethiopia ~15% (2024). | Selam Analytics (Task 1) | 2025-02-01 | Direct usage indicator; useful for forecasting digital payment adoption. |

---

## 2. New events

Events: **category** filled; **pillar** left empty (per schema). Required fields: source_url, original_text, confidence, collected_by, collection_date, notes.

| record_id | record_type | category | pillar | indicator | observation_date | source_name | source_url | confidence | original_text | collected_by | collection_date | notes |
|-----------|-------------|----------|--------|-----------|------------------|-------------|------------|------------|---------------|---------------|-----------------|-------|
| EVT_ENR_001 | event | regulation | (empty) | NBE Interoperability Directive | 2024-06-01 | NBE | https://nbe.gov.et | high | National Bank of Ethiopia directive on interoperability of mobile money and payment systems. | Selam Analytics (Task 1) | 2025-02-01 | Enables cross-platform P2P and merchant payments; supports Usage forecasting. |

---

## 3. New impact_links

Impact_links: **parent_id** = event’s record_id; **pillar** = pillar of the indicator affected; **related_indicator**, **impact_direction**, **impact_magnitude**, **lag_months**, **evidence_basis** filled. Required documentation fields included.

| record_id | record_type | parent_id | pillar | related_indicator | relationship_type | impact_direction | impact_magnitude | impact_estimate | lag_months | evidence_basis | source_url | original_text | collected_by | collection_date | notes |
|-----------|-------------|-----------|--------|-------------------|--------------------|------------------|------------------|-----------------|------------|----------------|------------|---------------|---------------|-----------------|-------|
| IMP_ENR_001 | impact_link | EVT_ENR_001 | USAGE | USG_DIGITAL_PAY | direct | increase | medium | 5 | 12 | literature | (N/A) | (N/A) | Selam Analytics (Task 1) | 2025-02-01 | Interoperability typically raises digital payment usage (Tanzania, India). |
| IMP_ENR_002 | impact_link | EVT_0004 | USAGE | USG_DIGITAL_PAY | enabling | increase | low | 3 | 24 | literature | (N/A) | (N/A) | Selam Analytics (Task 1) | 2025-02-01 | Fayda (digital ID) enables account opening and payments; indirect effect on usage. |

**parent_id link check:** IMP_ENR_001.parent_id = EVT_ENR_001 (new event). IMP_ENR_002.parent_id = EVT_0004 (existing event: Fayda Digital ID Program Rollout).

---

## 4. Verification of enrichment impact

Verification is implemented in code so the enrichment impact is auditable:

- **Temporal coverage:** Before enrichment, ACC_OWNERSHIP has no 2011 point; after, it has 2011. USG_DIGITAL_PAY has no 2021/2024 in raw; after, it has both. See `verify_enrichment_impact()` in `src/data/enrichment.py` and `scripts/verify_enrichment.py`.
- **Indicator expansion:** New indicator_codes added by enrichment: ACC_OWNERSHIP (extra year 2011), USG_DIGITAL_PAY (new), USG_AGENT_DENSITY, ACC_ATM_DENSITY, ACC_BRANCH_DENSITY, ACC_SMARTPHONE_PEN, ACC_MOBILE_INTERNET, USG_WAGES.
- **Event expansion:** One new event EVT_ENR_001; impact_links reference it (IMP_ENR_001) and existing EVT_0004 (IMP_ENR_002).

Run: `python scripts/verify_enrichment.py` to print before/after counts and coverage.

---

## 5. Explicit construction (unified schema)

All new records are built in `src/data/enrichment.py` with the same column set. Pillar and record_type are set as follows.

### Observations

- **record_type:** `"observation"`. **pillar:** Set to the pillar of the indicator (e.g. `"ACCESS"`, `"USAGE"`).
- Built via `_row(...)` which returns a dict with `record_type="observation"`, plus `pillar`, `indicator`, `indicator_code`, `value_numeric`, `observation_date`, `source_name`, `source_url`, `confidence`, `original_text`, `collected_by`, `collection_date`, `notes`.
- Example (2011 baseline):

```python
_row(
    "REC_ENR_001",
    "ACCESS",           # pillar required for observations
    "Account Ownership Rate",
    "ACC_OWNERSHIP",
    14.0, "%", "2011-12-31",
    source_name="Global Findex 2011",
    source_url="https://www.worldbank.org/en/publication/globalfindex",
    confidence="high",
    original_text="Ethiopia account ownership 14% (2011)...",
    notes="Baseline year (Findex); added for continuity.",
)
```

### Events

- **record_type:** `"event"`. **pillar:** Left empty (`None`); events are not assigned to a pillar.
- Built in `_enrichment_events()` as a list of dicts with `record_type="event"`, `category` set (e.g. `"regulation"`), `pillar=None`, plus source and documentation fields.
- Example: `record_id="EVT_ENR_001"`, `category="regulation"`, `pillar=None`, `indicator="NBE Interoperability Directive"`.

### Impact_links

- **record_type:** `"impact_link"`. **parent_id:** Set to the event’s `record_id` (e.g. `"EVT_ENR_001"`). **pillar:** Set to the pillar of the *indicator* affected (`related_indicator`), e.g. `USG_DIGITAL_PAY` → `pillar="USAGE"`.
- Built in `_enrichment_impact_links()`; each row has `parent_id`, `pillar`, `related_indicator`, `impact_direction`, `impact_magnitude`, `impact_estimate`, `lag_months`, `evidence_basis`.
- Example: `record_id="IMP_ENR_001"`, `parent_id="EVT_ENR_001"` (links to event), `pillar="USAGE"`, `related_indicator="USG_DIGITAL_PAY"`.

**parent_id link:** Formed by setting `impact_link["parent_id"] = event["record_id"]`. Verification ensures every `impact_link.parent_id` appears in `event.record_id` (see `verify_enrichment_impact()` and `scripts/verify_enrichment.py`).
