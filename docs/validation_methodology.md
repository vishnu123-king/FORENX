# Known-Answer Validation Methodology

## 1. Mathematical Metrics
- **Precision:**
  $$\text{Precision} = \frac{\text{Correctly Matched Extracted Events}}{\text{Total Extracted Events in Evaluation Scope}}$$
  *Safe division: If total extracted events is 0, Precision is reported as `N/A`.*

- **Recall:**
  $$\text{Recall} = \frac{\text{Correctly Matched Expected Events}}{\text{Total Expected Events in Ground-Truth Scope}}$$
  *Safe division: If total expected events is 0, Recall is reported as `N/A`.*

## 2. Matching Rules
Events are mapped by composite key:
`lower(browser_family) + '|' + lower(event_type) + '|' + strip_lower(url)`

## 3. Discrepancy Classification
- **Matched Records:** Candidate matching key with timestamp within $\pm 2.0$ seconds tolerance.
- **Missing Records:** In ground truth manifest, but absent in extracted database.
- **Unexpected Records:** Extracted by parser, but absent in expected ground truth manifest.
- **Field Mismatches:** Key matched, but page title or timestamp deviates beyond acceptable tolerance.
