# Donor rules and recipes (settled with the user on EMS - Depot Activity, Door Address Link)

Read this before clearing (unmarking) any marked screenshot. `image-logic.md` says what the tools do; this file says how to
choose where every hidden pixel comes from, in what order, and how to prove the result.

The user's words for the goal: an unmarked image must look seamless, and the work must be fast.

## 0. The method in one paragraph
Look at the marks first. If there are none, only the frame goes. If there are marks, list the DAMAGED
PARTS (not whole elements), find a swap for each part - same screen first - judge every candidate on the
untouched pixels around that part, copy only what the mark hid, then run the gate. Never trust the
`"seamless": true` of `unmark` on its own.

## 1. Speed rules
1. **Marks first.** Run `python tools/brs_judge.py marks SRC`. No marks -> `unmark SRC DST` with NO donors
   (under a second). Never pass `--donor-dir` to an unmarked image: preparing 30 donors costs ~45 s for nothing.
2. **Sort the whole function once:** `python tools/brs_judge.py scan screenshots/<function>`.
   It prints unmarked / twin / NO TWIN for every screenshot. Only the NO TWIN ones need part work.
   It takes about 1.5 s per screenshot (run it once per function). A screen with red logos and no marks
   (the EMS home screen) shows as NO TWIN: look at it, it needs only the frame removed. It tests same-size
   twins only; check a cropped strip against its full screenshot with `judge --dy`.
3. **Shortlist, never the whole folder.** Give `unmark`, `fill` and `judge` the 1-3 donors that fit, by name.
4. **Stop at the first exact fit** for a part. Open another donor only for a part that is still unresolved.
5. **Same screen before other screenshots.** A swap on the same screen needs no donor at all.

## 2. Marked elements versus screen elements
- **Marks (added by the manual, always removed):** the blue frame at the image edge; red rectangle
  outlines (3 px, pure red, no soft edge); white circles with a red ring and red number; red stubs.
- **The app's own (never removed):** red menu icons, red asterisks, red clear crosses and link icons (compact
  shapes, usually a lighter red, not touching a mark); blue buttons, bars, highlights, grid headers; hover
  highlights; tooltips; the white veil and the animation arrows on a success screen.
- A red icon INSIDE a red box is still the app's: it is compact and does not touch the line.
- **App leftovers of the mouse** (a hover tooltip over a record, a stray highlight) stay unless the user
  says to remove them. Ask once per image, with a crop. Example: the "40DC-DRY CARGO CONTAINER" tooltip
  on the Door Address Link screen was removed on the user's say; the arrows on the success screen stayed.

## 3. Judging a donor (per part, never per image)
Use `python tools/brs_judge.py judge MARKED --box x0,y0,x1,y1 --donors F...`.
1. **Judge on untouched pixels only:** the pixels of the part's box that lie outside the marks' footprint.
   A donor qualifies only when it agrees on ALL of them (`EXACT`).
2. **The donor must be clean at that spot.** A donor with its own mark there is rejected for that part
   (`DIRTY`), not for the whole image. Pixels under a donor's own marks are unknown - a donor that was
   "cleaned" by a tool is never a source there.
3. **State must match.** A hovered, focused, selected or disabled copy of an element fails on its edges
   (shadow, glow). Its face can still be used when the face matches exactly.
4. **Offsets differ per part.** Two parts of one mark can need different donors at different offsets
   (0, 2 and 3 px on one red box). Test per part; never assume a donor from the screen name.
5. **Keep parts tight.** Box = the mark plus a 1-3 px ring. A wide box fails on unrelated stray pixels.
   If the tool warns "fewer than 40 untouched px", widen by a pixel or two.
6. **Brightness gate.** A donor that matches on position but not on brightness is rejected, even if it is
   the same screen. Veiled (success message, 32% white) and dimmed (pop-up open) screens are separate donor
   groups from normal screens.
7. **Different captures.** Some screenshots of the same screen were captured in another session (other size,
   text drawn slightly differently). They cannot feed each other; the judge shows it as large differences.

## 4. Donor order (first that passes wins)
1. **Twin.** An unmarked screenshot of the same screen at the same moment (the page image of a function is
   usually the twin of Step "click the menu item"). Take every hidden pixel from it and stop.
2. **Cropped twin.** The marked image is a crop of another capture (a strip of the same screen): every
   untouched pixel agrees with a region of the donor. Take everything from it. A cropped twin of an image
   already in the manual adds nothing: drop it as a duplicate.
3. **Same-capture screenshot of another function.** Same position, only the highlighted item or one value
   differs (the menu screenshots of the Single Functions). Best donor for everything around the mark.
4. **Part swap on the same screen** (section 5).
5. **Part swap from another screenshot** that passes the judge for that part.
6. **Whole element from another screenshot** - only when the mark covers the element's icon or text.
7. **Letters from the letter library** (section 6) - only for letter pixels the mark really hid.
8. **Flip or recolour** (section 7) - only with the user's approval, only inside the marked area.
9. Still not exact: ask the user for an unmarked screenshot, naming the screen and the spot.

## 5. Part swaps (the main tool)
**Damage first.** For each mark, write down what it hides: cap (rounded end), edge strip, corner, border
line, separator, fill, text, icon, check box, grid behind.

- **Read the hidden rows/columns from untouched ones FIRST.** A border, scrollbar track, separator or grid
  line that runs through the mark is visible just above/below or left/right of it. Look there before
  assuming what is under the mark. (Assuming cost 113 wrong pixels on the Accept Release menu.)
- **Buttons.** Caps and edge strips come from ANY button of the same style and height on the screen - width
  and label do not matter (Edit's caps from Delete, Submit's from Cancel). The marked button keeps its own
  face. If the circle covers part of the icon/text, that piece alone comes from a clean copy of the same
  button elsewhere (its face is the same even when that copy is hovered).
- **Highlighted record marked in red.** Usually only the four edges are covered: take the edge strips from
  another highlighted record of the same size (same screen, then other screenshots); the text stays the
  marked record's own.
- **Grid cells / records.** Grids repeat exactly (records every 36 px, menu items every 32 px on Depot
  Activity). Split the hidden area BY CELL; each cell takes the same column of another record whose value
  is the same. A running number takes the hidden character from a record that has that character in that
  position. Cut copy boxes in the gap BETWEEN characters, never through one.
- **Menu item marked.** Shell = the highlighted item of another menu screenshot (same capture), moved by a
  multiple of the item pitch; separators above and below come with it. The marked item's own text is pasted
  back over it; every visible letter pixel is kept.
- **Lines of a big red box.** Each of the four lines is its own part; take each from whichever donor is
  exact for it, or from the same screen when the line runs over plain background.
- **Check boxes.** All check boxes in the manual share one size. A check box hidden by a circle or box is
  replaced whole by any unmarked check box of the right state (ticked/unticked/disabled) from anywhere in
  the manual. The state comes from what the step says the user did; if the step does not say, ask.
- **Plain areas** (white, pop-up background, one flat colour) may be copied from any plain patch of the same
  colour on the same screen.

## 6. Letters
- The letter library (`fonts/`, `python tools/ilis.py learn / write / fonts`) stores real letters as masks and
  writes them on any background. `menu_item` holds the function-menu letters (learned from "Cancel Release").
- Use it when a mark hid part of a letter and no clean copy of that letter on that background exists.
- Learn from a clean word of the SAME style on the same screen: `ilis.py learn SRC --box B --text "..." --font NAME`.
- Calibrate first: write a word over its own clean position and check it lands on itself (x was 1 px off on
  the first try). Then write the letter, and paste the marked text's visible pixels back over it, so only
  the truly hidden pixels come from the font. Result on "Change to Empty Return": 5 px, each off by 1 of 255.

## 7. Flip and recolour (user approval, marked area only)
`python tools/brs_img.py copy SRC DST --from-box B --to x,y [--donor D] --flip h|v|hv --recolor FROM:TO,... --marks MARKED.png`
- A flipped or recoloured piece is not a plain copy. The tool writes only `DST_proposal.png` (before | after)
  and changes nothing. Show the proposal to the user. Re-run with `--approved` ONLY after the user says yes
  to that piece.
- `--marks` is the original marked screenshot. The piece is placed only inside its marked area; every pixel
  outside the marks stays. The tool refuses to run without it.
- Several small pieces may be shown on one sheet and approved together.
- Use it for: a shape that exists only in another colour (No button -> Yes button), a corner that is visible
  only on the other side (glow corner, pop-up corner), a glow step read from the visible side.

## 8. Recipes (from the user, with the screen they were settled on)
- **Alert with Yes / No (Cancel Group).** No gives the size (same rectangle). Recolour No's background and
  outline to the blue of the marked Yes button, place at Yes's position: only the marked area takes it, so
  Yes keeps its own text. The 1 px ring touching the button is filled with the button's blue (the user's
  "fill with the blue" rule). Glow columns: the visible glow column beside it, recoloured one step (steps
  read from the top edge of the same glow). Corners under the circle: flip the visible opposite corner.
  Dimmed area beside/under the pop-up: same columns one record up/down (the dimmed grid repeats).
- **Alert with Yes / No (Delete door address).** No's button for the size only; cut the Yes section from the
  marked screen and place it in.
- **CSV Load pop-up.** The Clear button gives the size; cut the Load button's contents from the marked
  screen and place them in. The "Select files" row: OPEN - ask the user (see section 10).
- **EQC Load pop-up.** Marked records: edges from the records below, centres cut from the marked records
  and pasted in (the text is not damaged). Submit: the Reset button above it gives the shell.
- **Form screen with Submit marked (Door Address Link, Link/Delink steps).** Submit = caps and edges from
  Cancel beside it + Submit's own face (from the unmarked Submit of the Edit how-to for the part under the
  circle). Big red box lines, each from its own exact donor. Check-box box: side lines from a donor, bottom
  line from the cell beside it.
- **Edit button marked.** Delete beside it is another width: caps/edges still come from it as parts; the
  icon piece under the circle comes from a clean Edit (Generate TOPS step 1).
- **Menu screenshot with a marked item** (two tested against their twins: 0 and 7 px difference).
  Everything around: a same-capture menu screenshot of another function, or the same screen (separators
  and white rows from the items below, grid behind the circle from the same columns of other records, border
  and track columns from untouched rows of the same menu).
- **Check boxes under a red box and circle (PR More Details, two ticked boxes).** Everything came from the
  same screen: the box lines, rounded record ends and cell line from the unmarked record below (records
  repeat every 36 px); the clipped corner of each ticked box from the other ticked box (upper's bottom-left
  from the lower, lower's top-left from the upper); white and the two separator lines between the records
  from the same rows one record down. When a check box is hidden completely, take a whole unmarked check
  box of the same state from anywhere in the manual.
- **Success message screen.** Frame only. The veil and the arrows are the app's and stay.
- **Group function menu + selected record marked (Empty Return Pre Advise).** Menu: the function's page
  image is a cropped twin of the top (exact on every untouched px; its "DIRTY" red is the app's ☰ icon).
  Record: the other Group functions' menu screenshots, but the GRID SCROLLS while the header, scroll arrow
  and track stay fixed. Measure the record border rows (`9dccfd`) and the header row in each screenshot
  first: records were at 361/397 here, 362/398 in Generate Truck Order, 364/400 in Generate Release Advise,
  header at 359 in all. So the record strips came from Truck Order at dy +1 and the scrollbar columns at dy 0.
  A hidden row band (a 3 px line that covers the record's top edge) is NOT pinned by the judge - the untouched
  rows around it agree at several offsets - so take the offset from the measured row pitch, then cross-check
  the result against a second donor at its own offset (9417 px rebuilt, only the scrollbar differed).
- **`copy` pastes the whole rectangle** even with `--marks` (only flip/recolour stay inside the marks). Over
  a record, copy thin strips that cover only the mark lines and the circle, never a box over text.

## 9. The gate (every image, before the frame is stripped)
`python tools/brs_judge.py gate MARKED.png REPAIRED.png [--twin UNMARKED.png]`
- changed OUTSIDE the marked area must be 0;
- mark lines left must be 0 (the app's own red in the marked area is listed separately - look at it);
- if a twin exists, use it as the answer key AFTER building, never as a shortcut for judging the method.
- `brs_img.py copy` boxes INCLUDE their last row and column. Off-by-one boxes leak; the gate catches it.
- The gate cannot see a wrong pixel INSIDE the marked area. So: always look at an enlarged crop of every
  repaired spot, and keep the order of copies in mind (a background patch pasted after a button wipes it).
Then strip the frame: `python tools/brs_img.py unmark REPAIRED.png work/<manual>/build/<name>.png` (no donors).

## 10. Open points (ask the user when they come up)
- "Select files" row of the CSV Load pop-up: no recipe yet.
- SETTLED: the one-pixel line touching a focused button is filled with the button's own colour. The user's
  test for such cases: if it cannot be seen with the image at 1250 px wide, it is fine - the manual shows
  the image at 1250 px. Do not ask about differences smaller than that.
- White-veil screens that also carry marks: a normal screenshot can serve them only after the same veil is
  applied; the tools cannot do that yet. None in Depot Activity needed it.

## 11. What the tools do NOT do on their own
`unmark` with donors does not follow sections 3-5: on a form screen it took Submit from a marked donor
(square corners) and, with better donors, reported "seamless" on a broken image. Until it is taught these
rules, build marked, twin-less images part by part with `judge` + `copy`, and prove them with `gate`.
