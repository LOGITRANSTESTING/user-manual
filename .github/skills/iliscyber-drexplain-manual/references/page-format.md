# Page files and building the .gui

A manual is a folder `work/<manual>/`:
```
work/import_activity/
  project.json        {"main": "Imports", "sub": "Import Activity"}   (+ "template": "template/ILISCyber_Template.gui" if the user gave one)
  outline.txt         page tree, 2 spaces per level, one page file per line
  pages/*.md          one file per page
  img/                marked screenshots and inline crops used by the pages
```

outline.txt (order = order in the manual):
```
pages/import_activity.md
  pages/content_section.md
    pages/query_parameters.md
    pages/result_grid.md
    pages/group_functions.md
      pages/status_change.md
        pages/how_to_process_bl_open.md
```

## Page file
```
---
title: How to Process BL Open
status: Waiting
---
## Steps
**Step 1** : The user should drag the cursor to the batch function menu icon {icon:batch_menu}, click on it, and then select "**Status Change**" from the menu.
![](../img/bl_open_01.png)
**Step 2** : Upon clicking "**Status Change**" User will be shown the Status Change screen.
**Step 3** : Click on {img:../img/btn_process.png}.
![](../img/bl_open_02.png)
If successfully processed, an alert is shown as given below and the "**BL Close**" is changed to "**Open**".
![](../img/bl_open_03.png)
```
Front matter: `title` (exact page title, agent tags exactly as in the menu), `status` (Not Started / Waiting / Completed - new function overview pages are Waiting).

One line = one paragraph. An empty line = an empty paragraph (spacing).

| Markup | Result |
|---|---|
| `## Steps` / `## Pre defined conditions` (PDC only when the user asks) | heading: Calibri 14, bold, underlined |
| `### Afsys` | bold Calibri 12 paragraph (sub-headings, mapping headings) |
| `**Step 3** : text` (or `Step 3 : text`) | "Step 3 " bold, ": text" normal |
| `**text**` | bold run (UI names: `"**Status Change**"` - quotes stay normal) |
| `{icon:batch_menu}` | house inline icon: select_all, single_select, batch_menu, record_menu |
| `{img:../img/btn_search.png}` | inline crop at original size |
| `![](../img/x.png)` alone on a line | centred full screenshot, width min(original, 1250) |
| `![w=900](../img/x.png)` | full screenshot at a set width |
| `>> text` | centred paragraph (e.g. `>> {img:...}` = centred picture at original size, as the Afsys shots in mapping documents) |
| `1. text` / `    1. text` | numbered list level 1 / level 2 |
| `@11 text` | Calibri 11 (the default pages' first lines; combine as `1. @11 Query Parameters`) |

Paths are relative to the page file. The page title (h1 Arial 16, house colour) and the blank line under it are added by the build.

## Commands
- `python tools/ilis.py gui build work/<manual> --out "output/<Main> - <Sub>.gui"` - builds, checks the XML parses, prints the tree. Trouble shooting pages are skipped.
- `python tools/ilis.py gui page <file.gui> --title "<title>" --out work/<manual>/pages` - an existing page as a page file + its images (text source for old manuals).
- `python tools/ilis.py gui export <file.gui> --out work/<manual>` - a whole existing .gui as a project. Pages you do not edit are rebuilt byte-for-byte from the original; pages you edit are rebuilt from the markup.
- `python tools/ilis.py gui info <file.gui> [--text 0] [--depth 2]` - tree with status, shot and icon counts.
