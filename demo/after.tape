# Scene 6: "AFTER". The improved README scores an A. Deterministic.
# Uses README.live.md: the README Claude wrote live in run.tape (scored 95/100).
# If you'd rather show YOUR run.tape result, delete the Copy-Item line so it scores what Claude just wrote.
# Render from the demo/ folder:   vhs after.tape     → after.mp4 + after.gif
Output after.mp4
Output after.gif

Require python

Set Shell "pwsh"
Set FontFamily "JetBrains Mono, Cascadia Mono, Consolas, monospace"
Set FontSize 22
Set Width 1280
Set Height 720
Set Padding 36
Set WindowBar Colorful
Set BorderRadius 12
Set Theme "Catppuccin Mocha"
Set TypingSpeed 45ms
Set CursorBlink false

Hide
Type "[Console]::OutputEncoding = [Text.Encoding]::UTF8; $PSStyle.OutputRendering = 'Ansi'; cd sample-app; Copy-Item README.live.md README.md -Force; function prompt { 'orbit-api ❯ ' }; function readme-score { python ../../readme-forge/scripts/score_readme.py @args --repo . --color | Select-Object -First 11 }; Clear-Host"
Enter
Sleep 500ms
Show

Type "readme-score README.md"
Sleep 300ms
Enter
Sleep 5s

# reset so the sample app is ready for the next take
Hide
Type "Copy-Item README.before.md README.md -Force"
Enter
