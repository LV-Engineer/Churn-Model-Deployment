Experiment Log

Log checks, measurements and decisions for deployment and monitoring.

| # | Check | Setup | Result | Notes |
| --- | --- | --- | --- | --- |
| 1 | Drift check without a shift | `POST /monitoring/drift`: reference from the database against the same data exported as CSV; alert rule: drifted share >= 0.3 or drift in `tenure_months`, `monthly_charges`, `contract` | 0 of 18 columns drifted (share 0), `alert: false` | Checks that the rule does not raise an alert on unchanged data. Same data against itself, so zero drift is expected; it is not a test on a separate sample |
| 2 | Drift check with a simulated shift | `app/monitoring/simulate.py`, strength 1.0: monthly charges +30%, tenure -40%, 30% of customers moved to month-to-month, 20% to fiber optic; then `POST /monitoring/drift` | 3 of 18 columns drifted (share 0.167): `tenure_months`, `contract`, `monthly_charges`; `alert: true` | The alert comes from the key-feature rule, the share is below the 0.3 threshold. `internet_service` was shifted on purpose but not flagged: this shift is too small for the test Evidently uses for that column. Simulated shift on one dataset, not real production drift |
| 3 | | | | |
| 4 | | | | |
| 5 | | | | |
| 6 | | | | |
| 7 | | | | |
| 8 | | | | |

# Conclusions

[What worked, what broke, what to improve]
