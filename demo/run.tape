# Scene 3–4: "THE RUN". A REAL Claude Code run of the skill on the sample app.
# Output differs a little each run (it's live AI). Speed it up 6–10× in the editor (see STORYBOARD.md).
# Needs: Claude Code installed and logged in, and the skill installed (~/.claude/skills/readme-forge).
# Render from the demo/ folder:   vhs run.tape     → run.mp4
Output run.mp4

Require claude

Set Shell "pwsh"
Set FontFamily "JetBrains Mono, Cascadia Mono, Consolas, monospace"
Set FontSize 20
Set Width 1280
Set Height 720
Set Padding 36
Set WindowBar Colorful
Set BorderRadius 12
Set Theme "Catppuccin Mocha"
Set TypingSpeed 55ms

Hide
Type "[Console]::OutputEncoding = [Text.Encoding]::UTF8; $PSStyle.OutputRendering = 'Ansi'; cd sample-app; Copy-Item README.before.md README.md -Force; function prompt { 'orbit-api ❯ ' }; Clear-Host"
Enter
Sleep 500ms
Show

# Interactive Claude Code session: this is what viewers recognise.
# Auto mode: Claude Code's built-in safety check approves routine steps, so the take runs unattended.
# (Recording by hand instead? Just type `claude` and approve prompts yourself.)
Type "claude --permission-mode auto"
Enter
Sleep 8s
# First launch in a folder shows a "trust this folder?" dialog whose DEFAULT is "No, exit".
# Down selects "Yes, I trust this folder", Enter confirms. (If the folder is already trusted,
# Down/Enter on an empty prompt do nothing.)
Down
Sleep 400ms
Enter
Sleep 4s

Type "/readme-forge improve my README. Don't ask questions, just do it."
Sleep 600ms
Enter

# Long enough for analysis + writing + scoring. Approve permission prompts if Claude Code asks:
# simplest is to start this tape in a session where you have already allowed Edit and Bash(python ...).
Sleep 180s

# Leave the session open on the final summary for a few seconds
Sleep 5s
