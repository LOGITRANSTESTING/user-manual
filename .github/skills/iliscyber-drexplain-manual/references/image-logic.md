# Image logic: seamless, unmarked screenshots (shared with the BRS workspace)

Used when a marked screenshot (an old manual image, or one with red boxes/numbers) is cleared for reuse,
and when something is edited out of a screen. Tools: `python tools/brs_img.py` (unmark, fill, rank,
remove-rows, copy, sheet) and `python tools/brs_judge.py` (measurement only). Same tools and rules as the
BRS repository - keep the two in sync.

## The rule
- Every cleared image must look like an untouched screenshot of the app. Accept nothing less than 100%.
- An image is used only when `unmark` reports `"seamless": true`, or every unresolved box has since been fixed exactly.
- Never invent text, values or icons.

## Never remove the app's elements
- **Only the manual's additions go:** the frame, red marks, circles, stubs, and blue boxes the user confirmed.
- **Everything that belongs to the app stays:** panels, lines, buttons, asterisks, icons, grid lines, highlights.
- **How the tool enforces it:**
  - Every pixel outside the marks' footprint is compared with the screenshot and put back if it differs (`guard_restored_px`).
  - A frame is removed only when it closes on all four sides.
  - Red leftovers are removed only when they are line-shaped or tiny pieces touching a removed mark. Compact red shapes, such as asterisks and icons, stay.
  - Blue is removed only for boxes the user confirmed (`--blue-box`).

## What unmark removes
- **The manual's blue frame:** the house 21/17 px border, or the older style (shadow, thin blue line, inner shadow).
- **Mark leftovers:** red boxes, numbered circles, stubs, and short box segments a circle cut off.
- **Drawn blue boxes:** only those the user confirmed, given as `--blue-box x0,y0,x1,y1`. `--blue` just lists candidates.

The app's own red (asterisks, icons) and blue (bars, buttons, lines) stay. Only red pieces touching a removed mark are removed.

## How every covered spot is repaired (in this order)
1. **Similar element, copied whole.** Every button, input box, drop-down and check box is collected into an element library. The sources are:
   - the same screen (away from the marks);
   - every neighbouring screenshot in `--donor-dir` / `--donors`;
   - the manual's inline step crops (`--inline` / `--donor-dir`).

   A damaged element is replaced by a library element only where that element matches every pixel the mark left visible (border, fill, text and icons, mean difference ≤ 2.5). Only the hidden pixels are taken from it. Examples: an empty Carrier box from the empty Customs box, a Cancel button from the same Cancel button on the next screenshot, a check box from any check box of the same state.
2. **Element rebuild (same style, same screen).** A button, input box or drop-down hit by a mark is redrawn from an undamaged element of the same style and height on the same screen. Examples: the Container box from the Gross Weight box, a button from the button next to it.
   - **Hidden edges come from the layout:**
     - elements in the same row share top and bottom;
     - elements in the same form column share left and right, so they have the same width;
     - a button's hidden end comes from the reference button's content padding.
   - **What is kept:** every pixel the mark did not touch is kept from the screenshot. Only the end caps and plain fill are drawn.
   - **When it refuses:** if the mark covered any text or icon inside the element, or the drawn style does not match the element's visible border.
   - **Which reference wins:** the most similar element (same height and style, closest width) is tried first, and the first one that passes every check is used.
3. **Inline step crops (perfect fit only).** The manual's small crops (Submit, Process, check boxes, icons) are tried at every position over the spot. This step also runs inside step 1.
   - A crop is placed only where it matches every surrounding undamaged pixel it covers: mean difference ≤ 2.5 and 99% of pixels within 24.
   - Only the damaged pixels are taken from it.
   - A crop from another zoom level never fits, so it is never used.
4. **Neighbour screenshots of the same screen, then the same screen elsewhere.** The ring of pixels around the spot is matched, including the pop-up dimming scale. The donor must also agree with every undamaged pixel inside the spot. Only the damaged pixels are copied.
5. **Row/column continuation.** This is accepted only when every repaired pixel continues an unbroken line or plain background on both sides. A line carrying colour wins over plain background, so panel and grid lines run unbroken.
6. **Anything else is `unresolved`.** It is not seamless until it is fixed below.

## Fixing an unresolved box
- **`fill SRC DST --box B --donors ... [--self]`**
  - Copies the same area from a neighbouring screenshot where it is clean.
  - Use it as well to edit something OUT of a screen: a stale value, an open pop-up, a hover highlight, a row selection, a tooltip.
  - Find the best donors first with `rank SRC --donor-dir DIR`.
  - Keep the box tight.
- **`copy SRC DST --from-box B --to x,y [--donor D]`**
  - An exact copy of a known identical piece: a field edge from the field directly below (same x), a grid cell from the row above, a button end from an identical button.
  - Read the coordinates with `python tools/ilis.py grid SRC DST`.
- **`python tools/ilis.py patch SRC DST --donor D --box B`**: the house single-spot patch.
- **Check every fix.** Show its `_check.png` at full size and look at the seam. If it is not invisible, undo it.
- **Still not exact:** ask the user for an unmarked screenshot of that screen, naming the screen and the spot (for example "the left end of the Submit button on the Accept Release screen"). The originals in `screenshots/<function>/` are the best source.

## Removing grid rows
`remove-rows SRC DST --box x0,y0,x1,y1 --until Y`
- The band is the full width of the grid rows to delete.
- Y is the bottom of the grid body, above the scrollbar.
- The rows below move up, and the freed band becomes empty grid.

## Debugging
Set `BRS_DEBUG=1` to see why an element was not rebuilt. The number printed is the rule that refused it.

## Choosing donors
How to choose where each hidden pixel comes from (twin, part swaps, letters, flip/recolour, recipes) is in
`donor-rules.md`. The repair order above is what `unmark` tries by itself; for a marked screenshot with no
twin, follow `donor-rules.md` with `brs_judge.py judge` and `brs_img.py copy`, then `brs_judge.py gate`.

## Flip and recolour
`copy SRC DST --from-box B --to x,y [--donor D] --flip h|v|hv --recolor FROM:TO[,FROM:TO] --marks MARKED.png [--approved]`
- Without `--approved` it writes only `DST_proposal.png` (before | after). Show it to the user.
- With `--approved` (after the user's yes) it places the piece, only inside the marked area of MARKED.png.
- Copy boxes include their last row and column.

## Measurement tool
`python tools/brs_judge.py marks | scan | judge | gate` never changes an image. See its `-h`.
