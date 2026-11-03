# Step templates (house rules - unchanged)

## 2. Step templates (copy the regular wording, swap names only; if a screen differs, TELL the user before writing)
All: heading "Steps " bold+underline 14pt. Each step `**Step N** : text` (only "Step N " bold). UI names bold inside double quotes, EXCEPT the side icon name in the side-icon step, which has NO quotes (write `(Single Invoice side icon)`, never `("Single Invoice" side icon)`). Buttons/icons appear as small cropped images inline ("click on [Search]"). Sub-menus: "A" >> "B". Screens are named by function/header, never by a record number shown in the tab ("Add/Modify Local Charge screen", not the BL number). Always use on-screen labels for field names.

**Query steps and query screenshots:** NEVER ask the user for a query screenshot. Write the query steps (`Enter the query fields ... click on [Search].` + `Upon clicking [Search], <records> ... are returned.`) and show a query screenshot ONLY when the user gives a query screenshot for that page. Otherwise the How to page starts directly at the access step and Step 1 is the menu / side icon step. Single functions (record menu) always start at the menu step. If a query screenshot is needed, the user will give it.

### A. Top menu (batch function)
```
(only when the user gave a query screenshot:)
Step 1 : Enter the query fields with desirable input for querying data and click on [Search].
Step 2 : Upon clicking [Search], <Record Type> with matching information are returned.
(then, numbered on from there:)
Step N : Either select all records available by clicking on [icon](select all checkbox) or select individual records by clicking on [icon](single select checkbox).
Step N+1 : The user should drag the cursor to the batch function menu icon [icon], click on it, and then select "<Function>" from the menu.
   (one screenshot for the selection and menu steps: selection = the end-to-end selection box (see "Record-level selection checkboxes"), menu step = the chosen menu item, with "Batch menu" >> "sub-item" boxing when it is in a sub-menu)
```
Then by what the next screenshot shows:
- Direct result (menu click goes straight to the result) -> no further step; closing line + result.
- Pop-up (dialog over dimmed screen) -> `Step N : Upon clicking "<Function>" the user is shown <Function> pop up screen.`
- Actual screen (new tab, no dimming) -> `Step N : Upon clicking "<Function>" User will be shown the <Function> screen.`
If the user did not select records (e.g. Copy From Master BL), drop the selection step and start from the menu.

### B. Record menu (single functions; one record, red ☰ in the row) - ALWAYS starts at the menu step
```
Step 1 : The user should drag the cursor to the record menu icon [icon] in the respective record, click on it, and then select "<Function>" from the menu.
   (screenshot: mark ONLY the chosen menu item, never the ☰ itself)
Step 2 : Upon clicking "<Function>" User will be shown the <Function> screen.   (pop-up variant as above)
```
Only if the user gives a query screenshot for the page, put the two query steps (enter query fields + Search, records returned) before the menu step and renumber.

### C. Side icon (no query on the main screen; query is inside the function screen)
```
Step 1 : Click on the [icon] (<Function> side icon) given on the right side of the <Sub Module> screen.
   (side icon marked 1; NO quotes around the function name)
Step 2 : Upon clicking [icon], User will be shown the <Function> screen.
Step 3 : Enter the query fields with desirable input for querying data and click on [Search].
   (query screen marked with the two-box / one-number rule - see "Query screens in How to pages"; only when the user gives that query screenshot)
Step 4 : Upon clicking [Search], <records> with matching information are returned.
```

### Combining templates
Some functions use two access paths in sequence (e.g. Revert Reversal Status: side icon screen, then a record menu inside it). Write template C Steps 1-4, then continue with template B's menu step as Step 5 (`The user should drag the cursor to the record menu icon [icon] in the respective record, click on it, and then select "<Function>" from the menu.`), then the screen/pop-up step, and keep numbering on from there.

### Any button that opens a pop-up or screen
Use the same wording as the menu steps, swapping the button in:
- Pop-up: `Step N : Upon clicking [button], the user is shown <Pop-up title> pop up screen.`
- Actual screen: `Step N : Upon clicking [button], User will be shown the <Screen name> screen.`

### Record-level selection checkboxes (applies EVERYWHERE)
Whenever a grid of records/rows has select checkboxes (a select-all checkbox in the header and a single-select checkbox per row) and they are ticked in the screenshot, ALWAYS write the selection step with the same pattern as template A, swapping only the record name:
```
Step N : Either select all <records> available by clicking on [icon](select all checkbox) or select individual <records> by clicking on [icon](single select checkbox).
```
- Applies to result grids AND grids inside function screens/pop-ups (e.g. the Charges grid in Single Invoice -> "charges").
- Do NOT ask about these; just write the step.
- Inline icons: if the checkboxes look like the house icons, use the house icons; if they look different (e.g. green ticks), crop them from the user's screenshot at original size.
- Marking: the selection box runs END TO END. Width: the full checkbox column, cell border to cell border (including the coloured status strip on record cards in the result grid). Height: from the top of the first ticked item (the header select-all cell if it is ticked, otherwise the first selected record) to the bottom of the last selected record row. The box never stops short at the checkbox itself. Number: middle of the box's left edge.
- This rule is ONLY for record-level select checkboxes. General checkboxes (options/flags such as Printing Required, XML Required) are NOT covered: treat them under the "clicked/ticked" rule below (ask whether default or user action).

### Two-box / one-number rule (query screens AND pop-ups in How to pages)
Used in exactly two places: (1) every query screen shown in a How to page, where the filled query fields are shown and Search is clicked (the main case), and (2) every pop-up where details are entered and then a button is clicked. It is NOT used on other full-screen steps.
- Marking: TWO boxes and ONE number, placed where the two boxes meet and touching both. Neither box carries its own number.
  - Query screens (as in the Import Documentation manual, e.g. How to Container Based Query, Land Lock Access Type Change): Box 1 = one big box around the WHOLE query panel - the filled query fields AND the Search/Reset buttons together. Box 2 = the Search button. The single numbered circle sits centred under Search, on Box 1's bottom line, touching the Search box (in the narrow gap between the Search box's bottom edge and Box 1's bottom line). Same layout whether the buttons share the fields' row or sit on a row under them.
  - Pop-ups: Box 1 = one big box around the whole entry area (all sections with entered fields, e.g. Cash Invoice Details + Bank/Cheque Details together), NOT the button. Box 2 = the button (Process / Ok / Submit / Save ...). The single numbered circle sits IN THE GAP BETWEEN the two boxes (horizontally centred on the button, vertically between the big box's bottom edge and the button's top edge, touching both), linking them. Extra unnumbered boxes may sit inside Box 1 to point at the entered field (e.g. Cross Recipient) when the user asks.
  - If the user asks to separate the entry and the button (e.g. a pop-up with a selection step before the entry), write two steps (`Enter the <field> as given below.` / `Click on [button].`) and mark each with its own numbered box.

**Query screens in How to pages** - keep the template wording (`Enter the query fields with desirable input for querying data and click on [Search].`) and mark with the two-box / one-number rule: big box around the whole query panel (filled fields + Search/Reset buttons), Search boxed, step number centred under Search on the big box's bottom line. Applies to every How to query screenshot the user gives. The default Query Parameters page stays unmarked.

**Pop-ups** - entering details and clicking the pop-up's button is ONE step, never two (unless the user asks to separate them):
```
Step N : Enter the details as given below and click on [button].
```
- Remarks-only pop-ups follow this same rule.
- If the pop-up has NO entry (button only), use the normal `Click on [button].` step.

### Function-specific steps (full screens other than query screens)
- More than 2 fields to fill -> "Enter all the required details as shown below." + ONE big rectangle around all fields with the number.
- 1-2 mandatory fields -> "Enter the data in <Label 1> and <Label 2> fields. These fields are mandatory." Mark with ONE numbered box around those fields; the button pressed next gets the next number.
- Red star = mandatory/editable. Greyed field = display only (never tell user to enter it).
- Grids: no light-blue underline under column headers = auto-populated (say so, e.g. "...and the invoice details are auto populated in the Details section."). Light-blue lines = possibly editable -> ASK.
- Drop-down choice: box the field (no number) + box the chosen option WITH the number. If both cannot be boxed cleanly, box only the chosen option with the number.
- Settlement Type: whenever a Settlement Type step is marked, the wording is always `Select the required Settlement Type.` (never name the chosen value).
- Anything clicked/ticked in a screenshot that the template does not cover (extra checkbox, toggle, opened drop-down) -> ASK why it was clicked and what to write. Never skip or guess. If the user says it is a default, write no step for it.
- If the user wants Settlement Type-like steps kept even when the drop-down is not open, keep them (ask, don't assume).

### Closing line
Pick the verb from the LAST button clicked: Process -> "processed", Submit -> "submitted", Save -> "saved", Send -> "sent" (even if the alert text says otherwise). If Process opens a follow-up pop-up (e.g. Tax Invoice) and that pop-up's Ok completes the action, still use "processed". Pick the object from the final screenshot: green bar = "a success message", Code/Description/Solution grid = "a Resultant grid", Alert box = "an alert".
- `If successfully <verb>, <a success message / a Resultant grid / an alert> is shown as given below.`
- With generated number + PDF: `If successfully processed, an alert with the System Generated <Receipt Voucher / Invoice> Number is shown as given below and pdf is displayed.` then alert screenshot, then PDF screenshot (blue border) LAST.
- Status change: `... is shown as given below and the "Status" is changed to "Prepared".`
- Validation step (Check List): `If successfully validated, a success message is shown as given below.` then the next step; one screenshot may show the success bar and the next button marked.
- Query-only page: `If data is available, the queried data is displayed as given below.`
- Reprint: `On clicking [print icon], the invoice pdf is displayed as given below.` + PDF.
- Follow-up view (e.g. charge details): `The added local charge can be viewed in the charge details as shown below.`
When you don't know how the result is shown, ASK. Ignore duplicate/redundant screenshots (confirm).

