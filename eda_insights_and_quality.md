# Task 2: Key Insights & Data Quality Assessment

**Project:** Forecasting Financial Inclusion in Ethiopia  
**Document:** EDA summary — at least 5 key insights with supporting evidence; data quality and limitations.

---

## 1. Key Insights (with supporting evidence)

### Insight 1: Account ownership growth has slowed sharply (2021–2024)

**Evidence:**  
- 2011→2014: +8 pp (14%→22%); 2014→2017: +13 pp (22%→35%); 2017→2021: +11 pp (35%→46%); 2021→2024: +3 pp (46%→49%).  
- Growth rate (pp per period) is lowest in the last interval despite the largest expansion in mobile money (Telebirr 2021, M-Pesa 2023, 65M+ registered accounts).

**Implication:** Findex “account ownership” (past-12-months use) is not tracking registered mobile money accounts one-for-one; structural or survey-timing effects matter.

---

### Insight 2: Gender gap in account ownership is large and only slightly narrowing

**Evidence:**  
- 2021: male 56%, female 36% → gap 20 pp (GEN_GAP_ACC).  
- 2024: gap 18 pp (from GEN_GAP_ACC series).  
- Female ownership remains well below national average (49% in 2024).

**Implication:** Women are a major untapped segment; digital ID (Fayda) and targeted policies could help (impact_links model Fayda → reduction in gender gap).

---

### Insight 3: Mobile money “account” penetration (Findex) is low relative to operator-reported users

**Evidence:**  
- Findex: mobile money account ~9.45% (2024).  
- Operator data: Telebirr ~54M users, M-Pesa ~10M+; adult population ~70M → implied “registered” penetration far above 9.45%.  
- Guide Sheet D: “Mobile money–only users are extremely rare (~0.5%)”; most adults with mobile money also have a bank account.

**Implication:** “Registered vs active” and “bank vs mobile money” definitions matter. Findex captures *use in past 12 months*; many registered users may not report as having a “mobile money account” or may be double-counted as bank + MM.

---

### Insight 4: Events align with inflection points in infrastructure and usage

**Evidence:**  
- Telebirr launch (May 2021): account ownership rises 35%→46% by 2021 survey; mobile money account rate 4.7% (2021)→9.45% (2024).  
- M-Pesa entry (Aug 2023): ACC_MM_ACCOUNT and usage indicators show second provider; impact_links attribute +5 pp to MM account rate (medium, 6-month lag).  
- P2P surpassing ATM (2024) and interoperability/Fayda events align with usage-focused impact_links (USG_DIGITAL_PAY, P2P count).

**Implication:** Event–impact modeling (impact_link) is consistent with narrative; lags and magnitudes are plausible for forecasting.

---

### Insight 5: Infrastructure and enablers correlate with access and usage

**Evidence:**  
- 4G coverage rises (e.g. 37%→71% in data); mobile penetration and Fayda enrollment grow.  
- Correlation analysis (EDA notebook): ACC_OWNERSHIP and USG_DIGITAL_PAY correlate with infrastructure indicators where overlapping years exist.  
- impact_links tie Safaricom entry → 4G (+15%), Fayda → ACC_OWNERSHIP (+10% pp, 24-month lag), NBE Interop → USG_DIGITAL_PAY (+5 pp).

**Implication:** Infrastructure and policy events are candidate leading indicators for Findex outcomes; useful for scenario and impact modeling.

---

### Insight 6: 2021–2024 slowdown is consistent with “saturation” and definition effects

**Evidence:**  
- Easiest-to-reach adults (urban, male, already banked) may have been included first; remaining unbanked are harder to reach (rural, female, informal).  
- Guide Sheet D: P2P dominance for commerce; “mobile money–only” very small; bank accounts relatively accessible. So Findex “account” may already capture many who added mobile money, and +3 pp reflects incremental newly “included” adults.  
- Survey timing: 2024 Findex may not fully reflect 2023–2024 M-Pesa and interoperability rollout.

**Implication:** Hypotheses for impact modeling: (1) lagged effect of M-Pesa/interop on 2025+ Findex; (2) diminishing returns without targeted rural/female interventions; (3) leading indicators (4G, Fayda, P2P volume) may lead Findex by 1–2 years.

---

## 2. Data Quality Assessment & Limitations

### Strengths

- **Unified schema:** One structure for observations, events, targets, impact_links; clear record_type and pillar.  
- **Source diversity:** Findex (survey), operators, NBE, regulator, research; reference_codes and guide (Sheet D) document Ethiopia-specific nuances.  
- **Confidence:** Most observations tagged high/medium; estimated/placeholders identified.  
- **Event–indicator links:** impact_link table gives testable relationships (direction, magnitude, lag, evidence_basis).

### Limitations

1. **Temporal sparsity**  
   - Findex points every 3 years (2011, 2014, 2017, 2021, 2024); no annual Findex.  
   - Many indicators (ATM density, branch density, agent density, smartphone penetration) have 0 or 1 observation (placeholders or single year).  
   - Limits trend and correlation precision.

2. **Disaggregation gaps**  
   - Location: only “national”; no urban/rural in dataset.  
   - Gender: available for ACC_OWNERSHIP in 2021 (and GEN_GAP_ACC 2021/2024); not for all indicators or all years.  
   - Limits analysis of geographic and gender drivers.

3. **Definition and denominator mismatches**  
   - Operator “registered users” vs Findex “used mobile money in past 12 months.”  
   - Different denominators (adults 15+ vs population) and “account” definition (bank and/or MM) affect comparability.  
   - Requires clear labeling when combining operator and Findex data.

4. **Placeholder and estimated values**  
   - Agent density, ATM/branch density, smartphone penetration, mobile internet: 0 or placeholder; confidence “estimated.”  
   - Enrichment (Task 1) added structure; values need to be filled from FAS, GSMA, ITU, NBE for production forecasting.

5. **Impact_link subjectivity**  
   - Magnitudes and lags (e.g. +15 pp Telebirr→ACC_OWNERSHIP, 12-month lag) are from literature/expert judgment, not estimated from Ethiopian time series.  
   - Good for scenario logic; should be validated or updated as new data arrives.

6. **Survey timing**  
   - Findex 2024 field period may not align with event dates (e.g. M-Pesa Aug 2023, interop 2025).  
   - Can create apparent “no effect” or “lagged effect” in raw comparisons.

### Recommendations

- Prioritize filling placeholders (agent density, ATM/branch, smartphone, mobile internet) from IMF FAS, GSMA, ITU, NBE.  
- Use impact_links for scenario design; consider Bayesian or sensitivity analysis on magnitudes/lags.  
- Treat “registered vs Findex MM account” explicitly in narrative and in any composite usage metric.  
- When Findex microdata or DHS/ESS become available, add urban/rural and gender disaggregation for key indicators.

---

*Supporting visualizations and detailed correlation/temporal coverage are in the EDA notebook: `notebooks/02_eda_task2.ipynb`.*
