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
| 4 | Direct Invoice - (CN), Print/Re-Print - (TR) (E - Invoice Generation removed - user decision) | Approved | Approved | Yes |
| 5 | Direct Invoice - (TW) / (HK) / (VN) | Approved (1 BUILT image flagged: VN Cash alert) | Approved | Yes |
| 6 | Tax Invoice Query (CN), Tax Invoice Generation (CN)/(VN), Debit Note (VN), Debit Note Query | Approved | Approved | Yes |
| 7 | Government Receipt (TW), Government Receipt Query (TW), Detention Invoice Generation (CN), Add/Modify Local Charge | Files received | - | No |
| 8 | Local Charge Calculation, Exchange Rate Revalidation, Cancel Shipment Collection, AR Un-Invoiced Query | Files received | - | No |

Outputs: `output/Billing & Reporting - Billing Activity.gui`, Mapping split by part group (user decision): `output/Billing & Reporting - Billing Activity Mapping 1 (Parts 1-3).gui`, `... Mapping 2 (Parts 4-6).gui`, later `... Mapping 3 (Parts 7-8).gui`. Previews: `output/previews/`.

## Projects
- Manual: `work/billing_activity/` (`outline.txt`, `pages/`, `img/`, `specs/`, `edits/`)
- Mapping: `work/billing_activity_mapping/` (Afsys images `img/afsys_*`, ILISCyber images `img/ilis_*` = copies of `work/billing_activity/mapping images/`)
- Rebuild: `.venv/bin/python tools/ilis.py --no-open gui build work/billing_activity --out "output/Billing & Reporting - Billing Activity.gui"` ; mapping: one outline per document -> `gui build work/billing_activity_mapping --outline outline_N.txt --out "output/Billing & Reporting - Billing Activity Mapping N (Parts x-y).gui"` (`outline_1.txt` = Parts 1-3, `outline_2.txt` = Parts 4-6; each starts with `pages/billing_activity.md`)
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
Part 2, 3 and 4 sources deleted after approval. Part 5: export uploads to `work/_src5/{unmarked,marked}`.
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

## Part 4 tree (approved; E-Invoice section named "E - Invoice Generation - (IN)")
```
Billing Activity Side Functions
  Direct Invoice - (CN)                          (CN user; side icon shot + Direct Invoice screen)
    How to generate Direct Cash Invoice          (side icon -> select charges -> Cash Invoice -> Cash Invoice pop-up -> Tax Invoice pop-up -> receipt alert)
    How to generate Direct Credit Invoice        (side icon -> select charges -> Credit Invoice -> pop-up -> Validate -> Process -> alert -> PDF)
  E - Invoice Generation - (IN)                  (IN user; side icon shot + E-Invoice Query screen)
    How to print E - Invoice                     (query -> row menu "Printing" -> success)
    How to mark E - Invoice as Cancelled         (query -> row menu "Cancel Marking" -> pop-up -> Submit -> status Cancel)
    (no How to for Update Customer Details - user decision; ILIS shots stop at the result list)
  Print/Re-Print - (TR)                          (TR user; side icon shot + Print/Re-Print screen)
    How to view Invoice                          (BL Number -> Search -> select -> View -> PDF)
    How to view Invoice Printing Details         (printing details icon -> pop-up)
    How to print Invoice                         (select all -> Print -> PDF)
    How to send Right Fax                        (select all -> Right Fax -> success)
```
Decisions: the 2nd source page "E - Invoice Generation - Printing" (Afsys "Reversal within 24 Hrs", ILIS = copy of Printing) is skipped. Update Customer Details: mapping page only. E-Invoice ILIS shots had no red marks in the marked file - boxes placed by us.
Part 4 sources exported to `work/_src4/{unmarked,marked}` (not committed). Flow sheets: `output/previews/p4_*_flow.png`.
- Part 4 mapping: tree follows the marked file (Print/Reprint, E - Invoice Generation, Direct Invoice - (CN)), source titles. Tiles: TR (same as Part 3), IN (`_tiles/in_*`), CN (`_tiles/cn_*`). Direct Invoice - (CN) parent = the 2 source images as given (`img/src_di_*`). Mapping-only specs: `ein`, `ein_ucd`, `pr`.
- Part 4 specs: `di_cash`, `di_credit`, `ein_print`, `ein_cancel`, `pr_view`, `pr_details`, `pr_print`, `pr_rightfax`; new inline icons icon_direct_invoice, btn_calculate, btn_add, btn_di_cash_invoice, btn_di_credit_invoice, icon_e_invoice_query, icon_print_reprint, btn_view, btn_print, btn_right_fax, icon_printing_details.
- E - Invoice Generation (IN) REMOVED from both documents (user decision, after Part 4 build). Do not add it back.

## Part 5 tree (approved)
```
Billing Activity Side Functions
  Direct Invoice - (TW)                          (TW user; side icon shot + Direct Invoice screen)
    How to generate Direct Cash Invoice          (side icon -> Add charges -> Calculate -> Cash Invoice -> pop-up + Process -> alert (Invoice No. + Receipt) -> PDF)
    How to generate Direct Credit Invoice        (side icon -> Add charges -> Calculate -> Credit Invoice -> pop-up + Check List -> success -> Process -> alert -> PDF)
  Direct Invoice - (HK)                          (HK user)
    How to generate Direct Cash Invoice          (... Calculate -> Cash Invoice -> Charge Settlement Details pop-up (Default) + Submit -> Cash Invoice pop-up + Process -> receipt alert)
    How to generate Direct Credit Invoice        (... Credit Invoice -> pop-up + Check List -> success -> Process -> alert; no PDF)
  Direct Invoice - (VN)                          (VN user)
    How to generate Direct Cash Invoice          (... Calculate -> Cash Invoice -> pop-up + Process; NO result shot in source - open point)
    How to generate Direct Credit Invoice        (... Check List -> success -> Process -> alert -> Tax Invoice Generation tab: select, File Path, Generate -> success)
```
Part 5 sources were exported to `work/_src5/{unmarked,marked}` (deleted after approval). Flow sheets (marked file ILIS shots): `output/previews/p5_*_flow.png`. Unmarked VN Cash has one extra shot (charges calculated, before Cash Invoice): `p5_vn_cash_unmarked_tail.png`.
- Part 5 built (manual + Mapping 2). Specs: `specs/d{tw,hk,vn}_{cash,credit}.json`, `fo_d{tw,hk,vn}.json`; screenshots `screenshots/Billing Activity/Part 5/`.
- **BUILT image (user: build it, but flag it):** VN Cash result alert `img/dvn_cash_05_BUILT.png` (mapping: `ilis_dvn_cash_05_BUILT.png`). Source `edits/dvn_cash_05.png`: VN cash 03 screen + VN Credit alert as donor, title "Cash Invoice", text "System Generated Receipt Voucher Number:" / "SGN/DRCT/2026/000014" (placeholder number). Flag line in bold above it on the manual How to page and the mapping page. Replace with a real VN screenshot when available, then drop the `_BUILT` name and flag lines. Re-running `run.sh` on dvn_cash recreates `img/dvn_cash_05.png` - rename again.
- New recipe `recipes/popup_text_clean_screen.json` (popup_text without `clear_marks`, which erases the red side icons). New crop `img/btn_submit_settle.png` (HK Submit, paper-plane icon).
- HK Cash numbering: 7 = Default radio, 8 = Submit (Charge Settlement Details), 10 = Cash Invoice pop-up pair.
- New TW tiles: `mapping images/tw_main.png`, `tw_sub.png` (tile box only) -> `ilis_tw_main/sub.png`. HK/VN reuse existing tiles.
- Mapping 2 outline: `dtw`, `dhk`, `dvn` (+ `_cash`, `_credit`) after `di`. Afsys lines kept as in the marked file (TW last image is a plain `![]` line).
- Review sheets: `output/previews/p5_d*_{cash,credit}.png` (manual), `p5_map_d*_ilis.png` (mapping ILISCyber).

## Sources for Parts 6-8
Uploaded by the user as GitHub pre-release assets (chat/web upload too large): releases `part6-sources`, `part7-sources`, `part8-sources` on this repo. Downloaded with `gh release download` to `/root/.copilot/uploads/partN` and exported to `work/_srcN/{unmarked,marked}` (not committed). Delete each release + export after that part is approved.

## Part 6 tree (approved)
```
Billing Activity Group Functions
  Debit Note - (VN)                              (row checkbox -> Billing Activity menu: Debit Note (VN))
    How to generate Debit Note                   (BL No + ETA -> Search -> select -> Debit Note (VN) -> select -> Process -> alert)
Billing Activity Side Functions
  Tax Invoice Query - (CN)                       (side icon shot + Tax Invoice Query screen)
    How to query Tax Invoice                     (dates -> Search -> view icon -> details -> view icon -> Charge Details pop-up)
    How to reverse Receipt and Tax Invoice       (... view -> menu: Receipt and Tax Invoice Reversal -> Yes -> Reason + Submit -> alert)
    How to cancel Tax Invoice                    (... view -> menu: Cancel Tax Invoice -> Yes -> Reason + Submit -> alert)
  Tax Invoice Generation - (CN)
    How to generate Tax Invoice                  (Credit Customer, Settlement Amount, Received From, Settlement Type -> Search -> select -> Submit -> Tax Invoice pop-up OK -> alert -> PDF)
  Tax Invoice Generation - (VN)
    How to generate Tax Invoice                  (dates -> Search -> Generate radio -> select -> Process -> success bar)
    How to view/print Tax Invoice                (dates -> Search -> View/Print/Regenerate radio -> select -> View/Print -> success bar)
  Debit Note Query - (VN)                        (VN user; source title has no tag)
    How to reprint Debit Note                    (dates -> Search -> print icon -> loading -> PDF)
    How to cancel Debit Note                     (dates -> Search -> cancel icon -> Yes -> record removed)
```
Flow sheets: `output/previews/p6_*_flow.png`. Debit Note Query - Reprint / Cancel have no Afsys section in the source (mapping: ILISCyber only).
- Part 6 built (manual + Mapping 2). Specs: `specs/{dn_gen,tiq_query,tiq_rev,tiq_cancel,tig_cn,tvn_gen,tvn_print,dnq_reprint,dnq_cancel}.json` + `fo_{dn,tiq,tig_cn,tig_vn,dnq}.json`; screenshots `screenshots/Billing Activity/Part 6/`. No built images.
- New inline crops: icon_tax_invoice_query, icon_tax_invoice_generation (CN and VN identical), icon_debit_note_query, icon_view_doc, btn_process_tig, btn_process_dn, btn_submit_reason, btn_yes_alert, btn_yes_dn, btn_view_print. Reused: btn_search, btn_search_q, btn_submit, btn_ok_tax, icon_print, icon_cancel, chk_single, chk_select_all.
- Manual: Debit Note - (VN) under Group Functions (after Batch Invoice - (TR)); the rest appended to Side Functions after Print/Re-Print - (TR). Tax invoice tab menu written as {icon:batch_menu}.
- Mapping 2: source titles/tree kept (`tiq`, `tiq_rev`, `tiq_cancel`, `tig_vn`, `tig_vn_print`, `tig_cn`, `dn_vn`, `dnq_reprint`, `dnq_cancel`); tiles CN (`ilis_cn_*`) / VN (`ilis_vn_*`). Debit Note Query pages: ILISCyber only.
- Review sheets: `output/previews/p6_<prefix>.png`, `p6_fo.png`, `p6_map_*_ilis.png`.
