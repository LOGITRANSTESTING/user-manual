# ILISCyber manual workspace

- This workspace builds ILISCyber Dr.Explain user manuals and, when asked, mapping documents. Use the skill `iliscyber-drexplain-manual` for manuals, `iliscyber-mapping-document` only when a mapping document is requested, and `iliscyber-add-keywords` when an index/keywords is requested for a manual or a mapping document. Follow the skill and its reference files exactly; they are the user's house rules.
- All image and .gui work is done with `python tools/ilis.py` (keywords: `python scripts/add_keywords.py`) (see the skill's references/toolkit.md). Do not write new Python for images or .gui files; do not open .gui files (100+ MB).
- Reply in plain text only - no diagrams, tables of options or generated widgets unless asked.
- When the user shares a plan or an approach, engage with it as it stands. No corrections, cautions or refinements unless asked.
- Show a preview of every image you create or change, as soon as it exists (on github.com: commit it to output/previews/ and show it in your reply).
- On github.com the finished .gui goes in output/ in your pull request, so the user can download it.
- Ask before anything that cannot be undone; otherwise keep working through the function without asking for permission at each step.
