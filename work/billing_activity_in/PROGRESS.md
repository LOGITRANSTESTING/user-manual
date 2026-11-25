# Billing Activity (IN) — progress

Separate manual + mapping documents holding only the IN functions (not merged into the main Billing Activity .gui).

## Scope
| Function | Manual | Mapping |
|---|---|---|
| Invoice Generation Single - (IN) › Cash Invoice | done (confirmed) | done |
| Invoice Generation Single - (IN) › Credit Invoice | done (confirmed) | done |
| Proforma Invoice Generation - Single | done | done |
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

## Proforma Invoice Generation - Single
- Steps 1-8 (Step 7 Customer Name, Step 8 Check List & Process), alert, then "Upon clicking Ok, the Proforma Invoice pdf is displayed".
- Broken glyphs (mojibake arrows/calendar/clock/refresh icons, alert title "â€‹") fixed: 01 query panel copied from Single Invoice 01 (offset -1,0, exact match); 02-04 arrows pasted from Single Invoice 03/04/05 (copy_from_neighbour_offset); 04 title re-centred. Originals in `raw/`.
- Afsys shots were blurry: unsharp mask tuned per image to the existing Afsys mapping images' edge strength (grad99 ~760); red boxes kept as given. Originals in `Afsys/raw/`.
