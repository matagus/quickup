Output screenshots/demo.gif

Set Shell zsh
Set FontSize 14
Set Width 1200
Set Height 600
Set Theme "Dracula"
Set WindowBar Colorful
Set Margin 20
Set MarginFill "#282a36"
Set BorderRadius 8
Set TypingSpeed 75ms
Set CursorBlink false

# ── Scene 1: Interactive mode ──────────────────────────────────────────────────
Type "quickup -i"
Enter
Wait+Screen /Select/
Sleep 500ms
# Navigate to desired project (Project #1 requires Down 3)
Down 3
Sleep 300ms
Enter
Wait+Screen /Select/
Sleep 5s

# ── Scene 2: Sprint command ────────────────────────────────────────────────────
Hide
Type "clear"
Enter
Show

Type `echo "    # quickup sprint  --  auto-detect current sprint"`
Enter
Sleep 1.5s

Hide
Type "clear"
Enter
Show

Type "quickup sprint"
Enter
Wait+Screen /Run again/
Sleep 8s

# ── Scene 3: Task details ──────────────────────────────────────────────────────
Hide
Type "clear"
Enter
Show

Type `echo "    # quickup task <id>  --  show task details"`
Enter
Sleep 1.5s

Hide
Type "clear"
Enter
Show

Type "quickup task 86b902nz4"
Enter
Wait+Screen /Status/
Sleep 8s

# ── Scene 4: Update task status ────────────────────────────────────────────────
Hide
Type "clear"
Enter
Show

Type `echo "    # quickup update <id> --status  --  update task status"`
Enter
Sleep 1.5s

Hide
Type "clear"
Enter
Show

Type `quickup update 86b902nz4 --status "in progress"`
Enter
Wait+Screen /→/
Sleep 8s

# ── Scene 5: Add a comment to same task ────────────────────────────────────────────────
Hide
Type "clear"
Enter
Show

Type `echo "    # quickup comment <id> --text  --  add a comment to a task"`
Enter
Sleep 1.5s

Hide
Type "clear"
Enter
Show

Type `quickup comment 86b902nz4 --text "I'm working on it"`
Enter
Wait+Screen /Comment Posted/
Sleep 8s

# ── Scene 6: Task details with comments ──────────────────────────────────────────────────────
Hide
Type "clear"
Enter
Show

Type `echo "    # quickup task <id> --comments  --  show task details with comments"`
Enter
Sleep 1.5s

Hide
Type "clear"
Enter
Show

Type "quickup task 86b902nz4 --comments"
Enter
Wait+Screen /Status/
Sleep 8s
