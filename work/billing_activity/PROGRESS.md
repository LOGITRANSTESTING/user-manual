# Billing & Reporting - Billing Activity: progress (hand-over notes)

Source material arrives in 8 parts. Each part = 2 Dr.Explain mapping files:
- **unmarked** file -> its ILISCyber screenshots are the ones we mark (copied to `screenshots/Billing Activity/Part N/`).
- **marked** file -> reference only for each function's flow; its **Afsys** images (already red-boxed) are used as-is in the mapping document.
After a part is finished, its source documents (uploads + `work/_src`) are deleted; the manual and mapping projects keep growing.

## Status
| Part | Functions | Manual | Mapping | Sources deleted |
|---|---|---|---|---|
| 1 | Invoice Generation Single - (CN) / (TW) / (HK) | Approved | Approved | Yes |
| 2 | Invoice Generation Single - (VN), Invoice Generation - (TR) | Approved | Approved | Yes |
| 3 | Invoice Query (+ Reprint, Cancel, Revert Reversal Status, Right Fax, BL Query, Reverse BL Wise) | Approved | Approved | Yes |
| 4-8 | - | waiting for files | - | - |

Outputs: `output/Billing & Reporting - Billing Activity.gui`, `output/Billing & Reporting - Billing Activity Mapping.gui`. Previews: `output/previews/`.

## Projects
- Manual: `work/billing_activity/` (`outline.txt`, `pages/`, `img/`, `specs/`, `edits/`)
- Mapping: `work/billing_activity_mapping/` (Afsys images `img/afsys_*`, ILISCyber images `img/ilis_*` = copies of `work/billing_activity/mapping images/`)
- Rebuild: `.venv/bin/python tools/ilis.py --no-open gui build work/billing_activity --out "output/Billing & Reporting - Billing Activity.gui"` (same for `_mapping` -> `... Mapping.gui`)
- Re-mark a page: `work/billing_activity/specs/run.sh specs/<prefix>.json "<screenshot dir>" <prefix> 01` (dir in `specs/<prefix>.dir.json`; `edits/<prefix>_NN.png` overrides the source shot). Writes the numbered manual image to `img/` and the unnumbered, borderless copy to `mapping images/`.

## User-approved rules (keep for all parts)
- Function tag (CN), (TW), (HK); How to titles "How to generate Cash Invoice" / "Credit Invoice" / "Credit /Tax Invoice".
- Step 1 side icon: box Single Invoice tooltip+icon (prep `--side`), no box on the Billing Activity Search.
- Step 5: ONE box over Settlement Type + Charge Type ("Select the required Settlement Type and Charge Type."). HK also includes Inv Charges ("Select the required Settlement Type, Charge Type and Inv Charges.").
- Open drop-downs are removed (recipe `recipes/copy_from_dimmed_neighbour.json`, dimmed donor factor 0.6).
- Toolbar buttons (Cash/Credit Invoice etc.): red box TIGHT on the button, number circle top right (`"pos":"topright"`).
- Pop-up pair boxes must stay inside the pop-up. Success messages are never marked.
- "Enter the details as given below and click on [btn]." is used for pop-ups (incl. Tax Invoice).
- Credit flow: Check List (step 9) -> "If successfully validated, a success message is shown as given below." -> Step 10 Click on [Process] -> alert (+ "and pdf is displayed" + PDF only for CN).
- Missing validated/Process shots may be built with `recipes/success_bar.json` (bar colour on this screen 223,242,191). CN Credit /Tax image 05 is built this way ("Credit Invoice Validated Successfully") - approved.
- Duplicate Process shots are left out (HK Credit original 06 left out - approved).
- When asking the user a question, ALWAYS show the flow (preview sheet of the related images).
- Mapping: cover -> Billing Activity (empty) -> Invoice Generation Single - (XX) (empty) -> "Single Invoice - <X> Invoice" pages; Afsys = user's marked images as given; ILISCyber = main tile, sub tile, then the How to images (red boxes only).
- Mapping ILISCyber order (user rule, every page): Billing & Reporting tile -> Billing Activity tile -> side icon shot (Single Invoice boxed; batch functions: query/batch menu) -> the screen -> remaining steps. Use the tiles of the same country user (CN/TW/HK: `ov_01/02`; VN/TR: `_tiles/`). Preview: `output/previews/mapping_ilis_order.png`.

## Open points for Part 1
- Default pages use "BL/Booking Number records" (confirmed).
- Icons page added under Result Grid ("Icons - to be filled", result grid shot + blank space).
- Function overview pages: expanded side icon shot (01) + the Single Invoice screen after clicking it (02; CN uses edits/cn_credittax_03 with drop-down removed). Billing Activity overview: only main, sub, query shots (confirmed).
- After user confirms Part 1: delete Part 1 sources (uploads + `work/_src`), then wait for Part 2.

## Part 2 tree (approved)
```
Content Section
  Billing Activity Group Functions          (new; "This menu allows the user to perform functions on multiple records at a time.")
    Batch Invoice - (TR)
      How to generate Batch Credit Invoice  (batch menu -> Credit Invoice -> details + Apply -> Check List & Process)
  Billing Activity Side Functions
    Invoice Generation Single - (VN)
      How to generate Cash Invoice          (ends with Tax Invoice Generation tab: Generate, select, File Path, Process)
      How to generate Credit Invoice        (Check List/Process, then Tax Invoice Generation)
    Invoice Generation Single - (TR)
      How to generate Credit Invoice
```
Part 2 and 3 sources deleted after approval. Part 4: export uploads to `work/_src4/{unmarked,marked}`.
- Part 2 mapping: tree follows the marked file (Invoice Generation Single - (VN) -> Cash/Credit; Invoice Generation - (TR) -> Single Invoice - Credit Invoice, Batch Invoice - Credit Invoice). Afsys lines kept exactly as given (incl. two images on one line). ILISCyber tiles: `screenshots/Billing Activity/Part 2/_tiles/{vn,tr}_{main,sub}.png`, boxes at the same positions as Part 1 `ov_01/ov_02`. Note: unmarked .gui image numbering differs from the marked one - match by similarity.
- Overview pages: VN 02 = `edits/vn_cash_03.png` (drop-down removed); TR 02 = TR Credit shot 03; Batch Invoice - (TR) = batch menu shot (Batch 02) + Credit Invoice screen (Batch 03).
- TR Single Step 5 adds: "VAT Grouping can be selected if needed." (no box) - user decision.

## Part 3 tree (approved; user tags: Revert Reversal Status (TR), Reverse BL Wise (HK))
```
Billing Activity Side Functions
  Invoice Query                               (side icon shot + Invoice Query screen)
    How to query Invoice by Invoice Number    (side icon -> Invoice Number -> Search -> records + Details)
    How to query Invoice by BL Number         (BL Query)
    How to reprint Invoice                    (print icon -> PDF)
    How to cancel Invoice                     (cancel icon -> Reversal Date/Reason -> Submit -> alert -> PDF -> status Cancelled)
    How to revert Reversal Status - (TR)       (row menu -> Revert Reversal Status -> pop-up -> Submit -> success -> status Prepared)
    How to send Right Fax                     (row menu -> Right Fax -> recipients -> Submit -> success)
    How to reverse Invoice BL Wise - (HK)      ( row menu -> Reverse BL Wise -> select BL, Reversal Reason -> Process -> Yes -> alert)
```
Part 3 sources exported to `work/_src3/{unmarked,marked}` (not committed). Flow sheets: `output/previews/p3_*_flow.png`.
- Part 3 mapping: parent "Invoice Query" + 6 children (source titles), except user titles "Invoice Query - Revert Reversal Status (TR)" and "Invoice Query - Reverse BL Wise (HK)". ILISCyber tiles: TR (`_tiles/tr_*`), HK for Reverse BL Wise (`_tiles/hk_*`). Right Fax has no Afsys section in source.
- Part 3 specs: `specs/iq_*.json`; inline icons icon_invoice_query, icon_print, icon_cancel, icon_row_menu, btn_submit, btn_yes.
