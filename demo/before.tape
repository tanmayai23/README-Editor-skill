# Scene 2: "BEFORE". A bad README and its F score. Deterministic: same output every run.
# Render from the demo/ folder:   vhs before.tape     → before.mp4 + before.gif
Output before.mp4
Output before.gif

Require python

Set Shell "pwsh"
Set FontFamily "JetBrains Mono, Cascadia Mono, Consolas, monospace"
Set FontSize 22
Set Width 1280
Set Height 720
Set Padding 36
Set Margin 0
Set WindowBar Colorful
Set BorderRadius 12
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms
Set CursorBlink false

# --- hidden setup: reset the sample app to its bad README, short prompt
Hide
Type "[Console]::OutputEncoding = [Text.Encoding]::UTF8; $PSStyle.OutputRendering = 'Ansi'; cd sample-app; Copy-Item README.before.md README.md -Force; function prompt { 'orbit-api ❯ ' }; function readme-score { python ../../readme-forge/scripts/score_readme.py @args --repo . --color | Select-Object -First 16 }; Clear-Host"
Enter
Sleep 500ms
Show

# --- the problem
Type "Get-Content README.md"
Sleep 300ms
Enter
Sleep 3s

# clear between the README and the score so nothing scrolls off-screen
Hide
Type "Clear-Host"
Enter
Show

Type "readme-score README.md"
Sleep 300ms
Enter
Sleep 5s
