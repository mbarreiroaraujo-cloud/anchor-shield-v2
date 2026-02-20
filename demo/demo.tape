# anchor-shield-v2 — Terminal Demo
# Generates an animated GIF showing the semantic vulnerability scanner in action.
#
# Requirements: VHS (https://github.com/charmbracelet/vhs), ffmpeg
# Usage: vhs demo/demo.tape
#
# Regenerate: vhs demo/demo.tape

Output demo/anchor-shield-v2-demo.gif

Require python3

Set Shell "bash"
Set FontSize 20
Set Width 1200
Set Height 650
Set Theme "Dracula"
Set Padding 20
Set TypingSpeed 40ms
Set CursorBlink false

Type "python scripts/demo_scan.py examples/vulnerable-lending/programs/vulnerable-lending/src/lib.rs"
Sleep 500ms
Enter
Sleep 8s
Sleep 3s
