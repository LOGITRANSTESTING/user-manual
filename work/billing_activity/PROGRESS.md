# Billing & Reporting - Billing Activity: progress (hand-over notes)

Source material arrives in 8 parts. Each part = 2 Dr.Explain mapping files:
- **unmarked** file -> its ILISCyber screenshots are the ones we mark (copied to `screenshots/Billing Activity/Part N/`).
- **marked** file -> reference only for each function's flow; its **Afsys** images (already red-boxed) are used as-is in the mapping document.
After a part is finished, its source documents (uploads + `work/_src`) are deleted; the manual and mapping projects keep growing.

## Status
| Part | Functions | Manual | Mapping | Sources deleted |
|---|---|---|---|---|
| 1 | Invoice Generation Single - (CN) / (TW) / (HK) | Drafted (7 How to pages + overview/default pages) - awaiting user review | Drafted | Yes |
| 2 | Invoice Generation Single - (VN), Invoice Generation - (TR) | tree plan proposed | - | No |
| 3-8 | - | waiting for files | - | - |

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

## Open points for Part 1
- Default pages use "BL/Booking Number records" (confirmed).
- Icons page added under Result Grid ("Icons - to be filled", result grid shot + blank space).
- Function overview pages: only the expanded side icon shot (01). Billing Activity overview: only main, sub, query shots (confirmed).
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
Part 2 sources exported to `work/_src2/{unmarked,marked}` (delete when Part 2 is done).
