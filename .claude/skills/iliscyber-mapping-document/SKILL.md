---
name: iliscyber-mapping-document
description: Build an ILISCyber mapping document (Dr.Explain .gui) that maps each Afsys (old Forms) function to its ILISCyber screens - one page per function with an Afsys and an ILISCyber section, red boxes only. Use ONLY when the user asks for a mapping document; ILISCyber user manuals are a different job.
---

# ILISCyber mapping document builder (Claude)

Use only when the user asks for a mapping document. Reply in plain text only (no diagrams, option tables or widgets unless asked). When the user shares a plan or approach, engage with it as it stands - no unrequested corrections, cautions or refinements. Ask before anything that cannot be undone; otherwise keep working through the function without asking permission at each step.

## Workspace rules (always)
1. **Never write image or .gui code yourself.** Every pixel and file operation is a command of `python tools/ilis.py` (`python tools/ilis.py -h`; full reference: `.github/skills/iliscyber-drexplain-manual/references/toolkit.md`). If something cannot be made from the commands or recipes, tell the user what is missing; with their OK add a recipe (preferred) or extend `tools/` - never a one-off script.
2. **Never open or read a .gui file** (100+ MB). Use `gui info`, `gui page`, `gui export`.
3. **Screenshots are files** in `screenshots/<function>/`, named in step order (`01_menu.png`, `02_screen.png`, ...). Images attached as files: copy them there, say which file each became. Images pasted only into chat cannot be processed - ask the user to save them as files.
4. **Preview every image you create or change** as soon as it exists (`preview` sheet, or show the PNG). Use `--no-open` when not in VS Code.
5. **Locate, don't guess**: get boxes with `find --text "..." [--button]`, `find --red`, `find --popup`, `find --lines`, `snap`; `grid` only as a last resort. Never estimate coordinates by eye.
6. Missing image: ask the user for it and name the step it is for. Never take Afsys images from anywhere but the user.
7. If the toolkit fails with a missing module and `pip install` is blocked: `python3 -m venv .venv && .venv/bin/pip install -r requirements.txt`, then run `.venv/bin/python tools/ilis.py ...`. Never commit `.venv/`.
8. Page file format and build: `.github/skills/iliscyber-drexplain-manual/references/page-format.md`.

## User's standing mapping rules (these override anything below)
- One page per function, titled with the plain function name.
- No overview pages: no Content Section, Query Parameters, Result Grid or Functions pages. The tree is the cover, then `<Sub Module>` (title only, empty body), then the function pages directly under it.
- The Afsys section starts from Import Documentation (the AFSYS+ Flow main menu).
- The ILISCyber section starts from the main module, then the sub module, then the function's query screen, then the function's core flow.
- The user's Afsys images already have their red boxes: use them as given (original size, no re-marking). Only add red boxes (no numbers) to an Afsys image that arrives without any.
- Leave out duplicate shots (e.g. a "Click on Process" shot when the previous shot already has Process boxed), and tell the user which one was left out.

## What a mapping document is (from the user's Import mapping document, Version 4)
- Shows, per function, how it was done in Afsys next to how it is done in ILISCyber. No instructions.
- Each function or sub-function is ONE page titled with the plain function name - no "How to" (e.g. "BL Open", not "How to Process BL Open"). A group (e.g. Status Change, Cargo Release) is a parent page with the functions as children. Agent tags exactly as in the menu.
- Every page body is only two bold Calibri 12 headings with screenshots under each:
  ```
  **Afsys**

  >> {img:../img/afsys_gm_01.png}
  >> {img:../img/afsys_gm_02.png}


  **ILISCyber**

  ![](../img/ilis_gm_01.png)
  ![](../img/ilis_gm_02.png)
  ```
- No overview description, no Pre defined conditions, no Steps, no inline button crops, no closing lines: headings and screenshots only.
- Afsys section: the old Forms screens (main workflow menu with the module boxed, module screen with the function icon boxed, function screen with entry + button boxed, result message). ORIGINAL size, centred inline pictures (`>> {img:...}`); red boxes only, NO numbers, NO blue border.
- `NIL` (a plain line) under Afsys when the function did not exist in Afsys. Ask the user for each function whether there is an Afsys equivalent; do not guess.
- Under Afsys, short sub-headings when one function covers several Afsys screens (e.g. Access Type Change / Cross BL Access / Gate Port Access / Get BL Access), and the odd one-line note (e.g. "Transferred records are removed.", "BOOK CLOSE to BOOK OPEN") - only when the user gives them.
- ILISCyber section: red boxes only - no numbers, no blue border (`![](...)`, width 1250 through the image properties). Only the core flow: menu/selection shot, function screen with entries and the button boxed, result (alert / success bar / resultant grid), and the changed record if the status changes. Selection box and menu item can be on one screenshot.
- Cover: `ILISCyber - <Main> - <Sub>` Help Manual cover from the template, unless the user says otherwise.
- A page with an Afsys heading and nothing under it is allowed (Afsys shots still to come) - keep its status Waiting.

## Workflow
1. Ask which functions/pages the mapping document needs, whether a finished manual exists for them, and (per function) whether there is an Afsys equivalent.
2. ILISCyber images - in this order:
   a. FIRST look in `work/<manual>/mapping images/`: the manual workflow saves a red-boxed, unnumbered, borderless copy of every marked image there. Use them directly (pick the core-flow ones).
   b. Missing there but a finished manual exists: `gui page <manual.gui> --title "How to ..." --out work/<map>/from_manual`, pick the core-flow images, then `to-mapping SRC DST [--donor <unmarked shot of the same screen>]` for each (removes border and numbers, redraws boxes whole). Check every `_check.png` sheet; fix smudges with `patch --donor` or ask the user. Show the converted images as one `preview` sheet.
      - If the donor is missing or points to a temporary file, look in `screenshots/<function>/` for the original first - match the actual screen, state and step, not just the filename. Do not ask for a re-upload before checking there.
      - When removing numbers leaves damage, rebuild from the matched original: `prep --no-border`, then `mark` with `"n": null`. Locate boxes on the original again (do not reuse bordered-image coordinates). Keep intentional screenshot edits using the existing recipes.
      - Keep source paths and marking specs in the project (not `/tmp`). If shared screenshots were corrected, regenerate both the user manual and the mapping document.
   c. New ILISCyber screenshots: no inline crops; `prep SRC DST --no-border` (grey side crop only), then `mark` with unnumbered boxes only (`"n": null`), coordinates from the original screenshot.
3. Afsys images: from the user only. Use as given if already boxed; otherwise `mark` unnumbered boxes on the original, no border, original size.
4. Preview every new or changed image.
5. Write one page file per function in `work/<map>/` (format above), `outline.txt`, and `project.json` (`{"main": ..., "sub": ..., "kind": "mapping"}`).
6. On "generate": `python tools/ilis.py gui build work/<map> --out "output/<Main> - <Sub> Mapping.gui"`, then report the tree it prints.
