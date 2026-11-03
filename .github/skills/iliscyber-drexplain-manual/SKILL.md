---
name: iliscyber-drexplain-manual
description: Build ILISCyber Dr.Explain .gui user manuals from screenshots in the house format - How to pages, step wording, red box/number marking, image edits (alerts, pop-ups, success bars, changed values), 1250 px widths. Use for any ILISCyber user manual work.
---

# ILISCyber user manual builder (Dr.Explain house format)

The user writes ILISCyber help manuals in Dr.Explain. You turn their screenshots into a finished `.gui` that opens directly in Dr.Explain. Reply in plain text only (no diagrams or widgets). When the user shares a plan or approach, engage with it as it stands - no unrequested corrections or cautions.

## Golden rules for this workspace
1. **Never write image or .gui code yourself.** Every pixel and file operation is a command of `python tools/ilis.py` (full list: `references/toolkit.md`). If something truly cannot be made from the commands or recipes, tell the user what is missing; with their OK add a new recipe (preferred) or extend `tools/` - never a one-off script. Do not change `tools/` otherwise.
2. **Never open a .gui file** (they are 100+ MB). Use `gui info`, `gui page`, `gui export`.
3. **Screenshots are files** in `screenshots/<function>/`. Images pasted only into chat cannot be processed - ask the user to upload them there (on github.com: Add file > Upload files) (suggest names in step order: `01_menu.png`, `02_screen.png`, `03_alert.png`).
4. **Every edited or marked image is shown as a preview** right away so the user can correct it on the spot, before it goes into a page. In VS Code the toolkit opens it; when working on github.com (cloud agent), save the preview in `output/previews/`, commit it, and show it in your reply / pull request (`![](output/previews/x.png)`). Always run commands with `--no-open` there.
5. **Crop inline buttons/icons before marking**, always from the original unmarked screenshot (`crop` refuses marked images).
6. **Missing screenshots**: if a step's screenshot is missing, build it from a neighbouring or matching screenshot (same flow, same manual) with a recipe (`recipe list`) - e.g. an alert from the clean screen + another alert, a success bar, a changed grid value, a region from a neighbour shot. If nothing matchable exists, ask the user for that image and name the step it is for.
7. **Locate, don't guess**: get boxes with `find --text "..." [--button]`, `find --red`, `find --popup`, `find --lines`, `snap`; use `grid` only when nothing else works. Never estimate coordinates by eye and iterate.
8. Work in `work/<manual>/`; the finished manual goes to `output/<Main> - <Sub>.gui`.

## House rules (unchanged from the user's skill - read before writing)
- Session start, page tree, default pages, locking: `references/house-rules-pages.md`
- Step templates and closing lines (exact wording): `references/step-templates.md`
- Screenshot rules (border, grey padding, marking, circle placement, clearing, editing): `references/screenshots.md`
- How a page is written as a file and built: `references/page-format.md`

## Workflow per function
1. Ask which How to pages are needed. Never ask for a query screenshot; single functions start at the menu step. If an old manual is given, read its text with `gui info` / `gui page` (text only - never its images) and ask before reusing overview text, pre defined conditions, notes and page titles.
2. When the screenshots are in `screenshots/<function>/`: identify access type (top menu / record menu / side icon / combined) and screen type (direct result / pop-up / actual screen). Old manual images the user placed there with a new menu screenshot: list every mismatch first (references/screenshots.md).
3. Draft the steps from the templates; write record-level checkbox steps automatically; put every unknown (clicked items not in the template, editable grids, how the result is shown) as numbered questions. Questions about box placement are asked with option images (`mark` each option, then one `preview` sheet).
4. After the answers, per screenshot:
   - `crop` the inline buttons from the ORIGINAL screenshot (`crop SRC DST --text "Process"`),
   - `prep` (grey side crop + border + grey padding if dimmed; `--side` for side-function shots),
   - `mark` with a spec in ORIGINAL-screenshot coordinates (the sidecar converts them; numbers continue across screenshots),
   - look at the preview; fix and re-mark if anything covers text.
5. Write the page file (`references/page-format.md`) and add it to `outline.txt`. Pages the user confirmed are locked.
6. On "generate": `gui build work/<manual> --out "output/<Main> - <Sub>.gui"`, then report the tree it prints. No Trouble shooting pages anywhere (build skips them; `gui remove ... --match "trouble ?shooting"` removes them from an existing file).

## On demand
- Every image 1250 px wide in a finished .gui: `gui widths SRC "SRC_1250.gui"` - report the changed / already 1250 / smaller counts it prints.
- Clear a marked screenshot for reuse: `clear` (check the `_check.png` sheet; repair spots with `patch --donor` or ask).
- Edit text in a screenshot (record, value, message): recipes `change_value`, `alert_from_screen`, `popup_text`, `success_bar`, or `write --replace`. Letters come from the letter library (`fonts`); teach new ones with `learn` from any screenshot that shows them. If a letter is missing the tool draws it with Arial and says so - mention it with the preview.
- Mapping document requested: use the `iliscyber-mapping-document` skill instead.
