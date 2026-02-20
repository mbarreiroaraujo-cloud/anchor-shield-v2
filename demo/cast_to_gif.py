#!/usr/bin/env python3
"""Convert an asciinema .cast file to an animated GIF.

Uses pyte for terminal emulation and Pillow for image rendering.
Produces a Dracula-themed GIF suitable for README display.

Usage:
    python demo/cast_to_gif.py demo/recording.cast demo/anchor-shield-v2-demo.gif
"""

import json
import sys
from pathlib import Path

import pyte
from PIL import Image, ImageDraw, ImageFont

# ── Dracula theme ──
BG_COLOR = (40, 42, 54)       # #282a36
FG_COLOR = (248, 248, 242)    # #f8f8f2

# Standard ANSI colors (Dracula palette)
COLORS_16 = {
    "black":         (33, 34, 44),
    "red":           (255, 85, 85),
    "green":         (80, 250, 123),
    "brown":         (241, 250, 140),
    "blue":          (189, 147, 249),
    "magenta":       (255, 121, 198),
    "cyan":          (139, 233, 253),
    "white":         (248, 248, 242),
    "default":       (248, 248, 242),
    # Bright variants
    "brightblack":   (98, 114, 164),
    "brightred":     (255, 110, 110),
    "brightgreen":   (105, 255, 148),
    "brightyellow":  (255, 255, 165),
    "brightblue":    (214, 172, 255),
    "brightmagenta": (255, 146, 223),
    "brightcyan":    (164, 255, 255),
    "brightwhite":   (255, 255, 255),
}

# Font settings
FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
BOLD_FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"
FONT_SIZE = 17
PADDING = 24


def color_for(name, default=FG_COLOR):
    """Resolve a pyte color name to an RGB tuple."""
    if not name or name == "default":
        return default
    name_lower = str(name).lower().replace(" ", "").replace("-", "")
    if name_lower in COLORS_16:
        return COLORS_16[name_lower]
    # Handle numeric index (256-color)
    try:
        idx = int(name)
        if 0 <= idx <= 7:
            keys = list(COLORS_16.keys())[:8]
            return COLORS_16[keys[idx]]
        if 8 <= idx <= 15:
            keys = list(COLORS_16.keys())[8:16]
            return COLORS_16[keys[idx - 8]]
        # 216-color cube (indices 16-231)
        if 16 <= idx <= 231:
            idx -= 16
            r = (idx // 36) * 51
            g = ((idx % 36) // 6) * 51
            b = (idx % 6) * 51
            return (r, g, b)
        # Grayscale (232-255)
        if 232 <= idx <= 255:
            v = 8 + (idx - 232) * 10
            return (v, v, v)
    except (ValueError, TypeError):
        pass
    return default


def render_frame(screen, font, bold_font, char_w, char_h, img_w, img_h):
    """Render pyte screen to a Pillow Image."""
    img = Image.new("RGB", (img_w, img_h), BG_COLOR)
    draw = ImageDraw.Draw(img)

    for row in range(screen.lines):
        for col in range(screen.columns):
            char = screen.buffer[row][col]
            if char.data == " " and char.bg == "default":
                continue

            x = PADDING + col * char_w
            y = PADDING + row * char_h

            # Background
            if char.bg and char.bg != "default":
                bg = color_for(char.bg, BG_COLOR)
                draw.rectangle([x, y, x + char_w, y + char_h], fill=bg)

            # Foreground
            if char.data and char.data != " ":
                fg = color_for(char.fg, FG_COLOR)
                if char.bold:
                    fg = brighten(fg)
                f = bold_font if char.bold else font
                draw.text((x, y), char.data, fill=fg, font=f)

    return img


def brighten(color):
    """Make a color brighter (for bold text)."""
    return tuple(min(255, int(c * 1.2)) for c in color)


def frames_are_equal(f1, f2):
    """Fast comparison of two PIL images."""
    if f1.size != f2.size:
        return False
    return f1.tobytes() == f2.tobytes()


def main():
    if len(sys.argv) < 3:
        print("Usage: python cast_to_gif.py <input.cast> <output.gif>")
        sys.exit(1)

    cast_path = Path(sys.argv[1])
    out_path = Path(sys.argv[2])

    # Load cast file
    with open(cast_path) as f:
        lines = f.readlines()

    header = json.loads(lines[0])
    cols = header.get("width", 100)
    rows = header.get("height", 30)

    events = []
    for line in lines[1:]:
        ev = json.loads(line)
        if ev[1] == "o":
            events.append((float(ev[0]), ev[2]))

    # Setup pyte terminal emulator
    screen = pyte.Screen(cols, rows)
    stream = pyte.Stream(screen)

    # Setup font
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)
    bold_font = ImageFont.truetype(BOLD_FONT_PATH, FONT_SIZE)

    # Measure character dimensions
    bbox = font.getbbox("M")
    char_w = bbox[2] - bbox[0]
    char_h = int(FONT_SIZE * 1.45)

    img_w = PADDING * 2 + cols * char_w
    img_h = PADDING * 2 + rows * char_h

    print(f"Terminal: {cols}x{rows}, Image: {img_w}x{img_h}")
    print(f"Events: {len(events)}, Duration: {events[-1][0]:.1f}s")

    # Process events and capture frames at ~8 FPS
    frame_interval = 0.125  # seconds per frame
    frames = []
    durations = []

    current_time = 0.0
    event_idx = 0
    total_time = events[-1][0] + 1.0  # Add 1s pause at end

    while current_time <= total_time:
        # Feed all events up to current_time
        while event_idx < len(events) and events[event_idx][0] <= current_time:
            stream.feed(events[event_idx][1])
            event_idx += 1

        # Render frame
        frame = render_frame(screen, font, bold_font, char_w, char_h, img_w, img_h)

        # Deduplicate: if same as last frame, extend duration
        if frames and frames_are_equal(frames[-1], frame):
            durations[-1] += int(frame_interval * 1000)
        else:
            frames.append(frame)
            durations.append(int(frame_interval * 1000))

        current_time += frame_interval

    # Add extra pause at the end to let readers see the final output
    if durations:
        durations[-1] += 3000  # 3s extra pause at end

    print(f"Frames: {len(frames)}, unique after dedup")

    # Save GIF
    if len(frames) > 1:
        frames[0].save(
            str(out_path),
            save_all=True,
            append_images=frames[1:],
            duration=durations,
            loop=0,
            optimize=True,
        )
    elif frames:
        frames[0].save(str(out_path))

    size_kb = out_path.stat().st_size / 1024
    print(f"Saved: {out_path} ({size_kb:.0f} KB)")


if __name__ == "__main__":
    main()
