"""generate_assets.py - Generate brand assets, multi-res .ico, banners, and diagrams for Typing Buddy."""
from pathlib import Path

from PIL import Image, ImageDraw

ASSETS_DIR = Path(__file__).resolve().parent.parent / "assets"
ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def draw_typing_buddy_badge(size: int, status_color: str = None) -> Image.Image:
    """Render the official Typing Buddy icon with optional status badge."""
    # Scale canvas up 4x for supersampling/antialiasing
    scale = 4
    canvas_size = size * scale
    im = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(im)

    pad = int(canvas_size * 0.08)
    radius = int(canvas_size * 0.22)
    box = [pad, pad, canvas_size - pad, canvas_size - pad]

    # Rounded base squircle: vibrant deep indigo/blue gradient simulated or crisp solid
    base_color = (37, 99, 235, 255)       # Primary royal blue (#2563eb)
    accent_dark = (30, 64, 175, 255)     # Deep contrast (#1e40af)
    draw.rounded_rectangle(box, radius=radius, fill=base_color, outline=accent_dark, width=int(canvas_size * 0.025))

    # Inner keyboard key cap subtle highlight
    inner_pad = int(canvas_size * 0.14)
    inner_rad = int(canvas_size * 0.16)
    inner_box = [inner_pad, inner_pad, canvas_size - inner_pad, canvas_size - inner_pad]
    inner_color = (59, 130, 246, 255)    # Lighter blue cap (#3b82f6)
    draw.rounded_rectangle(inner_box, radius=inner_rad, fill=inner_color)

    # Center typing cursor & friendly companion sparkle
    cx, cy = canvas_size // 2, canvas_size // 2

    # Draw vertical typing cursor bar
    bar_w = int(canvas_size * 0.09)
    bar_h = int(canvas_size * 0.44)
    bar_x = cx - int(canvas_size * 0.12)
    bar_y = cy - bar_h // 2
    draw.rounded_rectangle(
        [bar_x - bar_w // 2, bar_y, bar_x + bar_w // 2, bar_y + bar_h],
        radius=bar_w // 2,
        fill=(255, 255, 255, 255)
    )

    # Draw smart buddy companion sparkle (4-point star)
    sx = cx + int(canvas_size * 0.15)
    sy = cy - int(canvas_size * 0.02)
    r_outer = int(canvas_size * 0.18)
    r_inner = int(canvas_size * 0.05)

    star_points = [
        (sx, sy - r_outer),
        (sx + r_inner, sy - r_inner),
        (sx + r_outer, sy),
        (sx + r_inner, sy + r_inner),
        (sx, sy + r_outer),
        (sx - r_inner, sy + r_inner),
        (sx - r_outer, sy),
        (sx - r_inner, sy - r_inner),
    ]
    draw.polygon(star_points, fill=(251, 191, 36, 255))  # Gold sparkle (#fbbf24)

    # Optional status indicator badge (bottom right)
    if status_color:
        badge_r = int(canvas_size * 0.16)
        bx = canvas_size - pad - badge_r
        by = canvas_size - pad - badge_r
        # Outline circle in dark/transparent for separation
        draw.ellipse([bx - badge_r - scale * 3, by - badge_r - scale * 3,
                      bx + badge_r + scale * 3, by + badge_r + scale * 3],
                     fill=(15, 23, 42, 255))
        draw.ellipse([bx - badge_r, by - badge_r, bx + badge_r, by + badge_r], fill=status_color)

    # Downsample with high-quality Lanczos filtering
    return im.resize((size, size), Image.Resampling.LANCZOS)


def generate_ico():
    """Generate multi-resolution .ico containing 16, 24, 32, 48, 64, 128, 256."""
    sizes = [(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)]
    base_img = draw_typing_buddy_badge(256)
    ico_path = ASSETS_DIR / "typing-buddy.ico"
    base_img.save(ico_path, format="ICO", sizes=sizes)
    print(f"Generated {ico_path} with sizes: {sizes}")


def generate_logo():
    """Generate 512x512 logo.png and SVG."""
    logo = draw_typing_buddy_badge(512)
    logo_path = ASSETS_DIR / "logo.png"
    logo.save(logo_path, format="PNG")
    print(f"Generated {logo_path}")

    # Generate vector SVG equivalent
    svg_content = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" width="512" height="512">
  <defs>
    <linearGradient id="blueGrad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" stop-color="#3b82f6"/>
      <stop offset="100%" stop-color="#1d4ed8"/>
    </linearGradient>
    <linearGradient id="keyGrad" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" stop-color="#60a5fa"/>
      <stop offset="100%" stop-color="#2563eb"/>
    </linearGradient>
    <filter id="shadow" x="-10%" y="-10%" width="120%" height="120%">
      <feDropShadow dx="0" dy="16" stdDeviation="16" flood-color="#0f172a" flood-opacity="0.3"/>
    </filter>
  </defs>
  <!-- Base Squircle -->
  <rect x="40" y="40" width="432" height="432" rx="100" fill="url(#blueGrad)" filter="url(#shadow)" stroke="#1e40af" stroke-width="8"/>
  <!-- Key Cap Layer -->
  <rect x="72" y="72" width="368" height="368" rx="72" fill="url(#keyGrad)"/>
  <!-- Typing Cursor Bar -->
  <rect x="176" y="144" width="44" height="224" rx="22" fill="#ffffff"/>
  <!-- Sparkle (4-point star) -->
  <path d="M 336 172 Q 336 248 412 248 Q 336 248 336 324 Q 336 248 260 248 Q 336 248 336 172 Z" fill="#fbbf24"/>
</svg>"""
    svg_path = ASSETS_DIR / "logo.svg"
    svg_path.write_text(svg_content, encoding="utf-8")
    print(f"Generated {svg_path}")


def generate_banner():
    """Generate 1600x400 banner.png for README header."""
    w, h = 1600, 400
    im = Image.new("RGBA", (w, h), (15, 23, 42, 255))  # Slate 900 dark background
    draw = ImageDraw.Draw(im)

    # Accent decorative glow
    for r in range(180, 0, -20):
        alpha = int(25 * (1 - r / 180))
        draw.ellipse([80 - r, 200 - r, 80 + r, 200 + r], fill=(37, 99, 235, alpha))

    # Paste badge logo
    logo = draw_typing_buddy_badge(240)
    im.paste(logo, (80, 80), logo)

    # Text rendering (Typing Buddy title and tagline)
    title_x = 360
    title_y = 110
    draw.text((title_x, title_y), "Typing Buddy", fill=(255, 255, 255, 255), font_size=76)
    draw.text((title_x, title_y + 96), "Fast, offline, privacy-first typing assistant & autocomplete for Windows",
              fill=(148, 163, 184, 255), font_size=32)
    draw.text((title_x, title_y + 148), "100% Offline  •  Zero Telemetry  •  RAM-Only  •  Grammar & Word Packs",
              fill=(96, 165, 250, 255), font_size=24)

    banner_path = ASSETS_DIR / "banner.png"
    im.save(banner_path, format="PNG")
    print(f"Generated {banner_path}")


def generate_social_preview():
    """Generate 1280x640 social-preview.png for GitHub Open Graph preview card."""
    w, h = 1280, 640
    im = Image.new("RGBA", (w, h), (15, 23, 42, 255))
    draw = ImageDraw.Draw(im)

    # Decorative background border
    draw.rectangle([20, 20, w - 20, h - 20], outline=(30, 41, 59, 255), width=2)
    draw.rectangle([28, 28, w - 28, h - 28], outline=(59, 130, 246, 60), width=1)

    # Center logo
    logo = draw_typing_buddy_badge(280)
    logo_x = (w - 280) // 2
    logo_y = 90
    im.paste(logo, (logo_x, logo_y), logo)

    # Main title
    title_text = "Typing Buddy"
    draw.text((w // 2, 410), title_text, fill=(255, 255, 255, 255), font_size=64, anchor="mm")

    tagline = "The Offline, Privacy-First Typing Assistant for Windows"
    draw.text((w // 2, 475), tagline, fill=(148, 163, 184, 255), font_size=28, anchor="mm")

    pills = "100% Offline  •  Zero Network Code  •  RAM-Only Buffer  •  Free & Open Source"
    draw.text((w // 2, 535), pills, fill=(96, 165, 250, 255), font_size=22, anchor="mm")

    preview_path = ASSETS_DIR / "social-preview.png"
    im.save(preview_path, format="PNG")
    print(f"Generated {preview_path}")


def generate_tray_states():
    """Generate tray states illustration showing Green (Active), Orange (Auto-Paused), Grey (Paused)."""
    w, h = 800, 260
    im = Image.new("RGBA", (w, h), (15, 23, 42, 255))
    draw = ImageDraw.Draw(im)

    states = [
        ("Active", (34, 197, 94, 255), "🟢 Active & Suggesting", 120),
        ("Auto-Paused", (249, 115, 22, 255), "🟠 Password / Locked App", 400),
        ("Paused", (148, 163, 184, 255), "🔘 Manually Paused", 680),
    ]

    for label, color, desc, cx in states:
        icon = draw_typing_buddy_badge(96, status_color=color)
        im.paste(icon, (cx - 48, 40), icon)
        draw.text((cx, 160), label, fill=(255, 255, 255, 255), font_size=24, anchor="mm")
        draw.text((cx, 195), desc, fill=(148, 163, 184, 255), font_size=16, anchor="mm")

    states_path = ASSETS_DIR / "tray-states.png"
    im.save(states_path, format="PNG")
    print(f"Generated {states_path}")


def generate_how_it_works_svg():
    """Generate how-it-works.svg diagram showing zero-network offline data flow."""
    svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 360" width="960" height="360">
  <defs>
    <style>
      .bg { fill: #0f172a; rx: 16px; }
      .box { fill: #1e293b; stroke: #3b82f6; stroke-width: 2px; rx: 12px; }
      .title { fill: #f8fafc; font-family: Segoe UI, system-ui, sans-serif; font-size: 18px; font-weight: 600; text-anchor: middle; }
      .sub { fill: #94a3b8; font-family: Segoe UI, system-ui, sans-serif; font-size: 13px; text-anchor: middle; }
      .arrow { stroke: #60a5fa; stroke-width: 2.5px; fill: none; marker-end: url(#arrowhead); }
      .privacy-badge { fill: #22c55e; font-family: Segoe UI, sans-serif; font-size: 13px; font-weight: bold; }
    </style>
    <marker id="arrowhead" markerWidth="8" markerHeight="6" refX="7" refY="3" orient="auto">
      <polygon points="0 0, 8 3, 0 6" fill="#60a5fa" />
    </marker>
  </defs>

  <rect width="960" height="360" class="bg" />

  <!-- Header -->
  <text x="480" y="45" class="title" font-size="22">Typing Buddy Offline Architecture</text>
  <text x="480" y="72" class="sub" font-size="14">Strict local privacy — zero network calls, RAM-only rolling buffer, no text saved to disk</text>

  <!-- Step 1: User Keystrokes -->
  <rect x="50" y="120" width="180" height="130" class="box" />
  <text x="140" y="160" class="title">1. Keystrokes</text>
  <text x="140" y="188" class="sub">pynput Global Hook</text>
  <text x="140" y="210" class="sub">Non-blocking</text>
  <text x="140" y="230" class="sub">Auto-pauses on password</text>

  <!-- Arrow 1 -> 2 -->
  <path d="M 230 185 L 285 185" class="arrow" />

  <!-- Step 2: RAM-Only Buffer -->
  <rect x="290" y="120" width="180" height="130" class="box" />
  <text x="380" y="160" class="title">2. Volatile RAM</text>
  <text x="380" y="188" class="sub">TextTracker buffer</text>
  <text x="380" y="210" class="sub">Capped at 300 chars</text>
  <text x="380" y="230" class="sub">Wiped on click / pause</text>

  <!-- Arrow 2 -> 3 -->
  <path d="M 470 185 L 525 185" class="arrow" />

  <!-- Step 3: Offline Engines -->
  <rect x="530" y="120" width="180" height="130" class="box" />
  <text x="620" y="160" class="title">3. Offline Engines</text>
  <text x="620" y="188" class="sub">Word Packs (Trie cache)</text>
  <text x="620" y="210" class="sub">Fuzzy Spelling D-L</text>
  <text x="620" y="230" class="sub">Harper Grammar Linter</text>

  <!-- Arrow 3 -> 4 -->
  <path d="M 710 185 L 765 185" class="arrow" />

  <!-- Step 4: Floating Overlay -->
  <rect x="770" y="120" width="150" height="130" class="box" />
  <text x="845" y="160" class="title">4. Popup UI</text>
  <text x="845" y="188" class="sub">Floating Overlay</text>
  <text x="845" y="210" class="sub">Never steals focus</text>
  <text x="845" y="230" class="sub">Pick with F2/F3/Tab</text>

  <!-- Bottom Privacy Banner -->
  <rect x="180" y="290" width="600" height="40" rx="8" fill="#14532d" />
  <text x="480" y="315" text-anchor="middle" fill="#86efac" font-family="Segoe UI, sans-serif" font-size="14" font-weight="600">
    🔒 Verified: Zero Sockets • Zero HTTP Requests • Zero Keystroke Logs
  </text>
</svg>"""
    how_path = ASSETS_DIR / "how-it-works.svg"
    how_path.write_text(svg, encoding="utf-8")
    print(f"Generated {how_path}")


def main():
    print("Generating assets for Typing Buddy...")
    generate_logo()
    generate_ico()
    generate_banner()
    generate_social_preview()
    generate_tray_states()
    generate_how_it_works_svg()
    print("Assets generation complete.")


if __name__ == "__main__":
    main()
