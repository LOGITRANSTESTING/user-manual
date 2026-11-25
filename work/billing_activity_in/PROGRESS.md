# Billing Activity (IN) — progress

Separate manual + mapping documents holding only the IN functions (not merged into the main Billing Activity .gui).

## Scope
| Function | Manual | Mapping |
|---|---|---|
| Invoice Generation Single - (IN) › Cash Invoice | done (confirmed) | done |
| Invoice Generation Single - (IN) › Credit Invoice | done (confirmed) | done |
| Proforma Invoice Generation - Single | done | done |
| Proforma Invoice Generation - Batch (+ How to view Address / Charges) | done (awaiting review) | pending (Afsys shots) |
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

## Proforma Invoice Generation - Single
- Steps 1-8 (Step 7 Customer Name, Step 8 Check List & Process), alert, then "Upon clicking Ok, the Proforma Invoice pdf is displayed".
- Broken glyphs (mojibake arrows/calendar/clock/refresh icons, alert title "â€‹") fixed: 01 query panel copied from Single Invoice 01 (offset -1,0, exact match); 02-04 arrows pasted from Single Invoice 03/04/05 (copy_from_neighbour_offset); 04 title re-centred. Originals in `raw/`.
- Afsys shots were blurry: unsharp mask tuned per image to the existing Afsys mapping images' edge strength (grad99 ~760); red boxes kept as given. Originals in `Afsys/raw/`.

## Proforma Invoice Generation - Batch
- Tree: Proforma Invoice Generation - Batch > How to generate Batch Proforma Invoice > How to view Address / How to view Charges (children of the How-to, per user).
- Steps 1-9: query+Search, select BLs, Billing Activity menu > Proforma Invoice, Invoice Date/Credit Customer/Due Date, Apply, success message, Check List & Process, result pop-up.
- Address: pin icon of the first row marked; Charges: money-bag icon of the first row marked (separate shots, boxes = whole icon cell so the number does not cover the icon).
- Glyph fixes (date pickers, ▼, refresh, success-bar ✕, pop-up close ✕ with hover glow removed, "â€‹" title prefix): /tmp scripts; donors = Proforma Single 01 (fixed), Single cash 03/04, Container Redelivery 02/3 (success ✕). Originals in `raw/` and `04 Address and Charges/raw/`.
