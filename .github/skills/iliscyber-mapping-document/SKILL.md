---
name: iliscyber-mapping-document
description: Build an ILISCyber mapping document (Dr.Explain .gui) that maps each Afsys (old Forms) function to its ILISCyber screens. Use ONLY when the user asks for a mapping document.
---

# ILISCyber mapping document builder

Use only when the user asks for a mapping document. Everything else (manuals) uses `iliscyber-drexplain-manual`. Reply in plain text only; engage with the user's plan as it stands.

The same workspace rules apply as in the manual skill: no hand-written image/.gui code (only `python tools/ilis.py`), never open a .gui, screenshots are files in `screenshots/`, every edited image is previewed, ask for missing images naming the step. Commands: `../iliscyber-drexplain-manual/references/toolkit.md`; page files and build: `../iliscyber-drexplain-manual/references/page-format.md`.

## How a mapping document differs from a user manual (from the user's Import mapping document, Version 4)
- Purpose: shows, per function, how it was done in Afsys next to how it is done in ILISCyber. No instructions.
- Same tree skeleton as the manual (cover, `<Sub Module>`, Content Section > Query Parameters, Result Grid (Indicators, Sort By), Group / Single / Side Functions), but each function or sub-function is ONE page titled with the plain function name - no "How to" (e.g. "BL Open", not "How to Process BL Open"). A group (e.g. Status Change, Cargo Release) is a parent page with the functions as children. Agent tags exactly as in the menu.
- Every page body is only two bold Calibri 12 headings with screenshots under each:
  ```
  **Afsys**

  >> {img:../img/afsys_gm_01.png}
  >> {img:../img/afsys_gm_02.png}


  **ILISCyber**

  ![](../img/ilis_gm_01.png)
  ![](../img/ilis_gm_02.png)
  ```
- No overview description, no Pre defined conditions, no Steps, no inline button crops, no closing lines - including on the overview pages (Import Activity, Content Section, Query Parameters, Result Grid): headings and screenshots only.
- Afsys section: the old Forms screens (main workflow menu with the module boxed, the module screen with the function icon boxed, the function screen with entry + button boxed, the result message). Kept at ORIGINAL size as centred inline pictures (`>> {img:...}`); red boxes only, NO numbers, NO blue border. Screenshots come from the user.
- `NIL` under Afsys (a plain line) when the function did not exist in Afsys. Ask the user for each function whether there is an Afsys equivalent; do not guess.
- Under Afsys, short sub-headings when one function covers several Afsys screens (e.g. Access Type Change / Cross BL Access / Gate Port Access / Get BL Access), and the odd one-line note (e.g. "Transferred records are removed.", "After {img:...} is clicked, the screen will be closed without any success message.", "BOOK CLOSE to BOOK OPEN") - only when the user gives them.
- ILISCyber section: the same screenshots as the manual's How to pages but with red boxes only - no numbers, no blue border (`![](...)`, width 1250 through the image properties like the manual). Only the core flow: typically menu/selection shot, function screen with entries and the button boxed, result (alert / success bar / resultant grid), and the changed record if the status changes. Query screens and separate menu shots only when they are part of the flow. Selection box and menu item can be on one screenshot.
- Cover: same as the manual (`ILISCyber - <Main> - <Sub>` Help Manual cover from the template), unless the user says otherwise.
- Pages with an Afsys heading and nothing under it are allowed (Afsys shots still to come) - keep status Waiting.

## Workflow
1. Ask which functions/pages the mapping document needs and whether a finished manual exists for them.
2. ILISCyber shots from a finished manual: `gui page <manual.gui> --title "How to ..." --out work/<map>/from_manual`, pick the core-flow images, then `to-mapping SRC DST [--donor <unmarked shot of the same screen>]` for each (removes the border and the numbers, redraws the boxes whole). Check every `_check.png` sheet; smudged spots: `patch --donor` or ask the user. Show the converted images as one `preview` sheet.
   (Manual images are allowed here because they are the user's own manual for the same function; still never take Afsys images from anywhere but the user.)
   - If the sidecar donor is missing or points to a temporary file, first look in `screenshots/<function>/`: these are the originals used to mark the user manual. Match the actual screen, state and step, not just the filename; do not treat a missing temporary path as a missing screenshot or ask for a re-upload before checking there.
   - Prefer rebuilding from the matched original with `prep --no-border` and `mark` with `"n": null` when removing numbers leaves damage. Locate boxes on the original again if the old image was cropped; do not reuse bordered-image coordinates as raw coordinates. Preserve any intentional screenshot edits using the existing toolkit recipes.
   - Keep source paths and marking specifications persistent in the project (not `/tmp`). Preview the corrected images, and regenerate both the user manual and mapping document if their shared screenshots were corrected.
3. New ILISCyber screenshots: no inline crops; `prep SRC DST --no-border` (grey side crop only), then `mark` with unnumbered boxes only (`"n": null`), coordinates as found on the original screenshot.
4. Afsys screenshots: mark with unnumbered boxes on the original; no border.
5. Write one page file per function (format above), outline.txt, project.json (`{"main": ..., "sub": ..., "kind": "mapping"}`), then `gui build work/<map> --out "output/<Main> - <Sub> Mapping.gui"`.
