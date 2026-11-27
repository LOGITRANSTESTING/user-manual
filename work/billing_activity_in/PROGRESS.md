# Billing Activity (IN) — progress

Separate manual + mapping documents holding only the IN functions (not merged into the main Billing Activity .gui).

## Scope
| Function | Manual | Mapping |
|---|---|---|
| Invoice Generation Single - (IN) › Cash Invoice | done (confirmed) | done |
| Invoice Generation Single - (IN) › Credit Invoice | done (confirmed) | done |
| Proforma Invoice Generation - Single | done | done |
| Proforma Invoice Generation - Batch (+ How to view Address / Charges) | done (awaiting review) | done |
| Proforma Invoice Query & Reversal (+ sub-functions) | done | done |
| E Invoice Operations › How to mark E - Invoice as Cancelled | done (awaiting review) | pending (Afsys to come) |
| E Invoice Operations › How to regenerate E - Invoice Request CSV | done (awaiting review) | pending (Afsys to come) |
| E Invoice Operations › other menu options (Cancel Request 24 hrs, Printing, Reversal within 24 hrs, Update Customer Details) | pending (UCD shots received) | pending |
| Credit Invoice - IT (Batch Function) | pending | pending |

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

## Proforma Invoice Query & Reversal
- How-tos: How to send Right Fax, How to reprint Proforma Invoice, How to cancel Proforma Invoice.
- Right Fax: Steps 1-3 (query+Search, results, Right Fax icon = first row icon marked, number placed below the cell). Success bar "Right Fax Generated Successfully" built (user request): bar + ✕ from Batch 04, text from the TR Print/Re-Print Right Fax shot (same font/size).
- All marked images must be `prep` → `mark` (house border); Batch images were re-done that way.

### Query & Reversal – Reprint
- Page `how_to_reprint_proforma_invoice.md` (Steps 1–3 + PDF result). Shots 01/02 reused from Right Fax as is; 03 = proforma PDF.
- Print icon marked (spec q_rp02: box 64,128,116,161, at 111,172). Inline icon `icon_reprint.png`.

### Query & Reversal – Cancel
- Page `how_to_cancel_proforma_invoice.md` (Steps 1–4 + success). 01/02 reused from Right Fax; 03 = confirmation alert (unmarked); 04 = Cancelled status + built bar "Proforma Invoice Reversed Successfully" (glyphs spliced from Batch 04 / Right Fax 03 bars; script /tmp/pf/cxbar.py).
- Cancel icon marked (spec q_cx02: box 117,128,168,161, at 163,172). Inline icon `icon_cancel_pf.png`.
- Right Fax 03: cleaned Grand Total remnant row above the bar.

### Mapping – Query & Reversal
- Parent `in_pf_query.md`; each sub-function on its own child page. Reprint: `in_pfq_reprint.md` (Afsys 01–06). Reversal: `in_pfq_reversal.md` (Afsys 01–05, ILIS cancel 01–04). Right Fax: `in_pfq_rightfax.md` (Afsys 01–05, ILIS rightfax 01–03).

## E Invoice Operations
- Screenshots: `screenshots/Billing Activity IN/05 E Invoice Operations/` (originals of edited shots in `raw/`). Spec `specs/ein_cx.json`, images `img/in_ein_cx_01..05`.
- Flow (mirrors main manual How to cancel E-Invoice): 1 side icon, 3 query pair (BL Number box unnumbered), 5 row menu Cancel Marking, 7 pop-up pair + Submit, success unmarked.
- 02 edited (user request): BL Number N651100284 typed (glyphs transplanted from the grid BL cell of raw/03).
- 03 edited (user request, match pop-up shot): Total Records 101 -> 1, rows 2+ cleared (menu + shadow kept), scrollbar thumb removed, Status Printed -> Prepared.
- 02: Invoice From/To Date cleared (empty date fields copied from 01 On Board From/To Date, same width).
- 03: Cancel Marking option given the blue hover fill (204,230,255) as in the main mapping menu shots (amlc_02, grq_cancel_ei_03).
- Inline: icon_e_invoice_query, btn_submit_ein (cropped), icon_row_menu (from main manual).
- Regenerate CSV (`specs/ein_rg.json`, `img/in_ein_rg_01..04`): 01/02 = same shots as Cancel Marking; 03 = `rg_03.png` (user shot: red box removed + tooltip over logo removed using the clean Cancel menu shot; option given blue fill); 04 success unmarked. Each menu option gets its own How to (user).
- Query shot 02 (both how-tos): number 3 circle starts 2 px below the Search button, overlapping the red box edge (`at` [1582,284], user); pair split into big box (no number) + tight Search box (kind line) because the pair rule ignores `at`.
