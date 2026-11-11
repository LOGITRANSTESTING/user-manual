# ILISCyber manual workspace (GitHub Copilot)

Builds ILISCyber Dr.Explain user manuals and mapping documents with GitHub Copilot, in the house format. Copilot follows the skills in `.github/skills/`. The work itself (cropping, borders, boxes and numbers, alerts, pop-ups, success bars, changed values, building the .gui) is done by the ready-made toolkit in `tools/`, so the results do not depend on Copilot writing code.

## One-time setup (Windows)
1. Install Python 3.10 or newer from python.org and tick "Add Python to PATH".
2. Open a terminal in this folder and run `pip install -r requirements.txt`.
3. Recommended: install Tesseract OCR (the UB Mannheim Windows installer, default folder). The toolkit finds it automatically and uses it to locate buttons and text by name (`find --text`). Without it, Copilot falls back to slower ways of finding positions.
4. In VS Code, open this folder (File > Open Folder) and click "Trust" when asked. Open Copilot Chat, choose **Agent** mode, and pick a **Claude** model (Sonnet or Opus) in the model picker.
5. Check that everything works: `python tools/ilis.py fonts` should list the letter sets.

`.vscode/settings.json` lets Copilot run `python tools/ilis.py ...` without asking each time. If VS Code still asks, click "Always allow" for that command.

## Folders
- `screenshots/<function>/` - your screenshots, saved as files, named in step order (`01_menu.png`, `02_screen.png`, `03_alert.png`). Images pasted only into chat cannot be edited by the tools.
- `template/` - put your own `ILISCyber_Template.gui` here if you want it used instead of the built-in one, and any old manuals used for text.
- `work/` - pages and images in progress (one folder per manual).
- `output/` - finished `.gui` files.
- `fonts/` - the letter library cut from your screenshots, used for edited text. It grows as you work.
- `recipes/` - saved image-building recipes (alert, pop-up text, success bar, changed value, copy from a neighbour shot).
- `assets/` - house template and house inline icons.

## Using it
- Manual: in Copilot Chat, type `/iliscyber-drexplain-manual` (or just ask for the manual) and follow the usual session start.
- Mapping document: ask for a mapping document. Copilot then uses `/iliscyber-mapping-document`.
- Every image Copilot builds or marks opens as a preview in VS Code. Say what to change there and then.
- To finish, say "generate". The `.gui` file appears in `output/`.
- Index (keywords): type `/iliscyber-add-keywords` followed by one or more `.gui` files (user manuals and/or mapping documents). A copy named `<file>_keywords.gui` is written next to each original; the original is not changed.

## Quick tool reference
`python tools/ilis.py -h` lists every command. The full reference is in `.github/skills/iliscyber-drexplain-manual/references/toolkit.md`.
