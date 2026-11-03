# Session start, page tree and default pages (house rules - unchanged)

## 0. Session start (always)
1. Template: the toolkit already holds the house template (`assets/ILISCyber_Template.gui`: project settings, cover with logo/hub graphic/address, title placeholder `ILISCyber - Main Module - Sub Module`). If the user puts their own `ILISCyber_Template.gui` in `template/`, set `"template": "template/ILISCyber_Template.gui"` in project.json. House inline icons are in `assets/icons/` (select_all, single_select, batch_menu, record_menu); crop any other icon (e.g. print) from the user's screenshot.
2. Ask for the four overview screenshots together:
   - Main module screen (e.g. Billing & Reporting tile selected)
   - Sub module screen (e.g. Billing Activity tile selected)
   - Query screen of the sub module
   - Result grid screen of the sub module (queried, with records)
   If the tiles are not marked red, spot the selected tile yourself (darker blue / larger / raised with shadow) and draw a plain red box (4px, no number). Always keep the FIRST set of main/sub images; ignore later ones. Draw the tile box with `mark` (an unnumbered box: `{"box":[...],"n":null}`, coords on the original screenshot, , with `"width":4` for the 4px tile box).
3. Main/sub screens give the names. Cover title = `ILISCyber - <Main Module> - <Sub Module>`.
4. Before the user sends screenshots for any function, ASK which "How to" pages they want for it (e.g. query data, Reprint, Cancel, Revert Reversal Status, Right Fax, BL Query, Reverse BL Wise). They tell you which images belong to which page.
5. EXISTING MANUALS ARE TEXT SOURCES ONLY: when the user gives an existing/old manual (.gui), use it ONLY to gather each function's overview text, pre defined conditions, notes and the titles of its How to pages. NEVER use images from it (screenshots, menu shots, result shots, inline crops) unless the user places those images in the screenshots folder. If no screenshot is given for a page, ask for it; do not pull one from the old manual.
6. Build everything through the session as page files in `work/<manual>/` (see page-format.md). Generate ONE `.gui` file at the end (or when the user says "generate") with `gui build`. Do not hand over intermediate .gui files unless asked; image previews are always shown (rule: every edited image is previewed).

## 1. Page tree
```
ILISCyber - <Main> - <Sub>                (cover: copied from template, title replaced)
<Sub Module>                               (overview: description BLANK, then main, sub, query AND result grid screenshots - ALWAYS include the result grid)
  Content Section                          (DEFAULT page - see "Default pages")
    Query Parameters                       (DEFAULT page - fixed content, see "Default pages")
    Result Grid                            (DEFAULT page - fixed content, see "Default pages")
    <Sub> Group Functions                  (top menu; "This menu allows the user to perform functions on multiple records at a time.")
      <Function> -> How to ...
    <Sub> Single Functions                 (record menu; "This menu allows the user to perform functions on one record at a time.")
      <Function> -> How to ...
    <Sub> Side Functions                   (side icons; "These functions are accessed from the side icons given on the right side of the <Sub> screen.")
      <Function> -> How to ... (one per page requested)
```
### Default pages (always the same content; only swap names, records and fields)
**Content Section**
- `Content section is further divided into two sections.` (Calibri 11)
- Numbered list: 1. Query Parameters  2. Result Grid
- Bold heading `Query Parameters` + query screenshot (blue border); bold heading `Result Grid` + result grid screenshot.

**Query Parameters** (the user's own wording; use exactly as written, swap only records and fields)
1. `The query section can be expanded or collapsed by clicking on ` + [collapse icon] (the ^ arrow at the top right of the query panel, cropped inline at original size).
2. `The User can search <records> using the Query Parameters like <main query fields from the screen, e.g. Voyage, BL Number, Booking Number, Customer, Invoice Status and ETD From / To Date>.` If a query field has a red star, name it and add `(This is a mandatory query field)` after it.
3. Query screenshot (blue border, centred, unmarked).
4. One line per button actually on the screen, button cropped inline at original size:
   - [Search] ` Used to search the data based on the information entered in the query fields.`
   - [Reset] ` Used to clear the information entered in the query fields.`
   Leave out any button that isn't on the screen. If a button not listed here appears (e.g. Clear), ASK for its line.

**Result Grid**
1. `This screen shows the list of <records> that matches the information typed in the <Sub Module> Query Fields.`
2. Result grid screenshot (blue border, centred, unmarked).
3. Inline search box crop (search field + magnifier button) on its own line, then `Used to inline search a data from the queried data` (Calibri 11).
4. Icons: see rule below.

- Result Grid icons: if the grid has icons, ASK if they want an icon page. If "already created" / "not required" -> skip. If yes -> add page "Icons - to be filled" with the result grid screenshot and blank space.
- Function overview pages (new ones): description BLANK for the user, plain (unmarked) screenshot, topic status = `Waiting`. Never change overviews the user already confirmed.
- NO Trouble shooting pages: never add a "Trouble shooting" page to any function. When finishing a manual that already contains Trouble shooting pages, remove them all.
- "Pre defined conditions": ALWAYS add this bold-underlined 14pt heading on EVERY "How to" page, placed before the "Steps" heading, and leave it BLANK (needs SME input) unless the user gives the conditions or approves reusing them from an existing manual. Do not ask about it otherwise.
- Agent tags: agent-specific functions ALWAYS keep the agent tag in the page title, written exactly as it appears in the menu (same brackets, same spacing), e.g. "Free Letter[EG]", "Undo FROB[YMA]", "CSD Query[UK]", "EDI References [ES]", "Full Container Admission Process [TR]", "Debit Note (VN)", "Single Invoice (HK)". Never drop or reformat the tag.

## 4. Locking
Once the user confirms a page, it is FINAL. Do not change it unless they ask (a global rule they ask for, e.g. grey padding, may be applied everywhere - say which locked pages it touched).

