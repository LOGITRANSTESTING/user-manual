# Billing Activity (IN) — progress

Separate manual + mapping documents holding only the IN functions (not merged into the main Billing Activity .gui).

## Scope
| Function | Manual | Mapping |
|---|---|---|
| Invoice Generation Single - (IN) › Cash Invoice | done (confirmed) | done |
| Invoice Generation Single - (IN) › Credit Invoice | done (confirmed) | done |
| Proforma Invoice Generation - Single | pending | pending |
| Proforma Invoice Generation - Batch | pending | pending |
| Proforma Invoice Query & Reversal (+ sub-functions) | pending | pending |

## Decisions (from user)
- One function at a time; user supplies ILISCyber then Afsys screenshots.
- Cash Invoice: no separate Customer Name step (populated by default). Step 9 = "The fields under the Cash Invoice Details are Autopopulated. The user should select Collection Bank as given below and click on [Process]." (unnumbered Collection Bank box).
- Credit Invoice: Step 1 reuses the Single Invoice side-icon shot. Step 9 = "All the fields in the Credit Invoice pop up will be autopopulated, click on [Check List]." Step 10 = Process.
- Mapping: Afsys images used as given (`>>`), ILISCyber = ilis_ov_01/02 then red-box-only copies from `mapping images/`.

## Layout
- Screenshots: `screenshots/Billing Activity IN/`
- Manual project: `work/billing_activity_in/` (specs/ = mark specs in original coords)
- Mapping project: `work/billing_activity_in_mapping/`
- Not built yet. Planned outputs: `output/Billing & Reporting - Billing Activity (IN).gui` and `output/Billing & Reporting - Billing Activity Mapping (IN).gui` (names to confirm).
