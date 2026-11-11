---
name: iliscyber-add-keywords
description: Add the Dr.Explain index (keywords) to ILISCyber .gui user manuals and mapping documents. Use when the user asks for keywords, an index or a keyword tree for one or more .gui files.
argument-hint: <file.gui> [more .gui files]
---

# Add the Dr.Explain index (keywords)

Add the index/keywords to the Dr.Explain files the user names (if none were named, ask which .gui files). Works for both user manuals and mapping documents. Reply in plain text only.

For each file:

1. Decide if it is a user manual or a mapping document (file name contains "Mapping" or "mapping" = mapping document; otherwise user manual).
2. Run the script, writing the result next to the original with the same name plus `_keywords`:
   - User manual: `python scripts/add_keywords.py "<file>" "<file without .gui>_keywords.gui"`
   - Mapping: `python scripts/add_keywords.py "<file>" "<file without .gui>_keywords.gui" --mapping`
   (`python tools/ilis.py gui keywords SRC DST [--mapping]` does the same.)
3. Never edit the original file. Never open a .gui file.

House rules the script applies (do not change them unless asked):
- Keyword tree mirrors the topic tree; keyword name = topic title exactly as written (keep agent tags like [YMA], [EG]).
- Each topic is linked to its own keyword only, with its full path.
- Cover page gets no keyword.
- User manuals: no keywords for "How to ...", "Accessing ...", "Invoicing via ..." pages or anything under them, nor for "BL Modification - Tabs" / "... - Functionalities" pages.
- Mapping documents: every page gets a keyword, except the Tabs / Functionalities pages.
- Existing keywords are replaced.

When done, reply in plain text with the keyword tree printed by the script for each file, and point out:
- function names that differ between a manual and its mapping (if both were given),
- pages present in one file but not the other.
Do not rename anything to make them match unless asked.

On github.com (cloud agent): commit the `_keywords.gui` files in your pull request so the user can download them.
