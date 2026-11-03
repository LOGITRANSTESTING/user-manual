# Toolkit: `python tools/ilis.py <command>`

All commands work on files. Previews open in VS Code automatically (add `--no-open` before the command to skip). Coordinates are `x0,y0,x1,y1` in pixels.

## Finding things (use these instead of guessing coordinates)
| Command | Returns |
|---|---|
| `find SRC --text "Process" [--button] [--region B]` | boxes of a word/phrase (OCR; `--button` = the whole button/menu item around it) |
| `find SRC --red` | existing red boxes |
| `find SRC --popup` | the pop-up/alert box in a dimmed screenshot |
| `find SRC --lines B` | text blocks inside a box (top to bottom) |
| `find SRC --color 233,246,210` | largest area of that colour (e.g. success bar) |
| `find SRC --crop piece.png` | where a crop appears |
| `snap SRC --box B` | a rough box tightened to the UI element (+3 px) |
| `grid SRC DST` | coordinate grid overlay, last resort for reading positions |

`find --text` needs Tesseract OCR (README). Without it: `find --crop`, `snap` on a rough box, or `grid`.

## Preparing and marking
- `crop SRC DST --text "Search"` or `--box B [--snap]` - inline button/icon crop at original size. Only from the original screenshot (marked images are refused).
- `prep SRC DST [--side]` - crops grey side areas (not with `--side`), adds the blue border, grey padding when the shot is dimmed. Writes `DST.json` (crop/border offsets).
- `mark SRC DST --spec SPEC` - SRC is the prepped image; SPEC is a JSON file or JSON text; coordinates are on the ORIGINAL screenshot (converted through the sidecar; `--coords bordered` if you measured on the bordered image):
```json
[
 {"box": [1401, 52, 1495, 81], "n": 6},
 {"box": [15, 377, 48, 443], "n": 5, "kind": "tall"},
 {"box": [96, 103, 170, 125], "n": 4, "pos": "bottomleft"},
 {"box": [210, 140, 420, 170], "n": null},
 {"box": [40, 30, 300, 60], "n": null, "width": 4},
 {"pair": {"big": [10, 60, 1500, 160], "btn": [1400, 120, 1470, 150]}, "n": 2, "type": "query"},
 {"pair": {"big": [20, 80, 600, 300], "btn": [280, 320, 340, 345]}, "n": 9, "type": "popup"}
]
```
  `kind` (button / tall / line) is guessed from the box size when left out; the circle goes to the first free spot in the house order (references/screenshots.md); `pos` forces a spot (left, right, bottomleft, bottomright, topleft, topright). Buttons are padded on the left automatically so the circle clears the icon/text. The command prints where each number went.
- `clear SRC DST` - removes border, old boxes, numbers and stubs; writes `DST_check.png` (before/after of each old number spot).
- `patch SRC DST --donor D --box B` - rebuilds a smudged spot from a similar unmarked screenshot (only when the match is reliable).

## Building missing / changed images
Blocks (used by recipes, some also as commands): `clear_marks`, `strip_border`, `dim`/`undim` (the app's pop-up dimming, measured 0.549), `copy_popup` (pop-up from a dimmed donor, aligned on the screen), `copy_region` (a region or a colour area from a donor; `align: auto` same screen, `bottom` same distance from the bottom, `none` + `offset`), `text_blocks`, `learn`, `replace_text` (erase the old text, write the new one at the same left edge/centre and baseline), `write`, `erase`, `paste`, `mark`, `border`, `save`.

Saved recipes (`recipe list`):
| Recipe | Use |
|---|---|
| `alert_from_screen` | clean screen + a dimmed alert from another shot + new message -> the alert over this screen |
| `popup_text` | same, also a new pop-up title |
| `success_bar` | green success bar from another shot with a new message |
| `change_value` | change a value on screen (grid cell, field, status) |
| `copy_from_neighbour` | bring a region from a neighbouring shot of the same screen |

Run: `python tools/ilis.py recipe run recipes/alert_from_screen.json --set screen=... --set donor=... --set "donor_message=..." --set "message=..." --set out=work/<manual>/img/x.png`
It prints what it found (pop-up box, text blocks, learned letters, any letter drawn with Arial) and shows a preview. A request that fits no recipe: copy the closest recipe to `recipes/<new_name>.json`, change the steps (same blocks), run it, and keep it for next time.

## Letter library (`fonts/`)
Real letters cut from the user's screenshots, one set per place in the app: `popup_message`, `popup_title` (bold, white on blue), `success_bar` (bold), `grid_cell`; add others as needed (`grid_header`, `field_value`, `menu_item`, `tab_title` ...). Never mix places in one font.
- `fonts` lists what each set has.
- `learn SRC --box B --text "exact text" --font grid_cell [--bold]` teaches letters from a text line you can read on a screenshot (box from `find --text`). Learn from any screenshot of the same place in the app before writing words that need new letters.
- `replace_text` in recipes learns the old text automatically (`old_text`).
- `write SRC DST --font F --text T --replace B [--old-text T] [--align center]` - one-off text change.
Letters not in the set are drawn with Arial at the matched size and reported; teach them and run again if the preview shows a difference.

## Other
- `preview A.png B.png --out sheet.png [--labels "A|B"]` - one sheet to show options or a set of images.
- `to-mapping SRC DST [--donor D]` - mapping-document style (see the mapping skill).
- `gui info | page | export | build | widths | remove` - references/page-format.md.
