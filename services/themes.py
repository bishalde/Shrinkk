"""Bio-page appearance: preset themes plus per-user overrides, resolved to CSS variables.

The dashboard's live preview mirrors `resolve()` in static/js/bio-editor.js; keep them in sync.
"""
from utils.validators import is_hex_color

PRESETS = {
    "classic": {
        "name": "Classic Blue",
        "style": "fill",
        "radius": "md",
        "font": "sans",
        "vars": {
            "--bio-bg": "linear-gradient(180deg,#EEF3FF 0%,#FFFFFF 70%)",
            "--bio-text": "#101010",
            "--bio-muted": "#5B6270",
            "--bio-btn-bg": "#1662FF",
            "--bio-btn-text": "#FFFFFF",
        },
    },
    "midnight": {
        "name": "Midnight",
        "style": "soft",
        "radius": "md",
        "font": "sans",
        "vars": {
            "--bio-bg": "radial-gradient(120% 80% at 50% 0%,#1D2B53 0%,#0B0F19 60%)",
            "--bio-text": "#F5F7FF",
            "--bio-muted": "#A3ACC2",
            "--bio-btn-bg": "#7EA6FF",
            "--bio-btn-text": "#0B0F19",
        },
    },
    "minimal": {
        "name": "Minimal",
        "style": "outline",
        "radius": "full",
        "font": "sans",
        "vars": {
            "--bio-bg": "#FFFFFF",
            "--bio-text": "#101010",
            "--bio-muted": "#6B6B6B",
            "--bio-btn-bg": "#101010",
            "--bio-btn-text": "#FFFFFF",
        },
    },
    "sunset": {
        "name": "Sunset",
        "style": "fill",
        "radius": "lg",
        "font": "grotesk",
        "vars": {
            "--bio-bg": "linear-gradient(160deg,#FF8A5B 0%,#FF3D7F 55%,#7B2FF7 100%)",
            "--bio-text": "#FFFFFF",
            "--bio-muted": "rgba(255,255,255,.8)",
            "--bio-btn-bg": "#FFFFFF",
            "--bio-btn-text": "#1F1235",
        },
    },
    "forest": {
        "name": "Forest",
        "style": "fill",
        "radius": "sm",
        "font": "serif",
        "vars": {
            "--bio-bg": "#0F2E24",
            "--bio-text": "#EEF5F0",
            "--bio-muted": "#A8C3B4",
            "--bio-btn-bg": "#D9F99D",
            "--bio-btn-text": "#0F2E24",
        },
    },
    "mono": {
        "name": "Mono",
        "style": "shadow",
        "radius": "none",
        "font": "mono",
        "vars": {
            "--bio-bg": "#F5F5F5",
            "--bio-text": "#101010",
            "--bio-muted": "#555555",
            "--bio-btn-bg": "#FFFFFF",
            "--bio-btn-text": "#101010",
        },
    },
}

BUTTON_STYLES = {"fill": "Filled", "outline": "Outline", "soft": "Soft", "shadow": "Hard shadow"}
RADII = {"none": "0px", "sm": "8px", "md": "14px", "lg": "20px", "full": "999px"}
FONTS = {
    "sans": {"name": "Sans", "family": "-apple-system,BlinkMacSystemFont,'Inter',system-ui,sans-serif", "google": "Inter:wght@400;500;600;700"},
    "grotesk": {"name": "Grotesk", "family": "'Space Grotesk',system-ui,sans-serif", "google": "Space+Grotesk:wght@400;500;600;700"},
    "serif": {"name": "Serif", "family": "'Fraunces',Georgia,serif", "google": "Fraunces:opsz,wght@9..144,400;9..144,600;9..144,700"},
    "mono": {"name": "Mono", "family": "'JetBrains Mono',ui-monospace,monospace", "google": "JetBrains+Mono:wght@400;500;700"},
}
DEFAULT_THEME = "classic"


def contrast_text(hex_color):
    """Near-black or white, whichever reads better on `hex_color`."""
    r, g, b = (int(hex_color[i:i + 2], 16) for i in (1, 3, 5))
    return "#101010" if (r * 299 + g * 587 + b * 114) / 1000 >= 150 else "#FFFFFF"


def clean(raw):
    """Validate an appearance payload from the editor, dropping anything unknown."""
    raw = raw or {}
    out = {"theme": raw.get("theme") if raw.get("theme") in PRESETS else DEFAULT_THEME}
    for key in ("bg", "button_color"):
        if is_hex_color(raw.get(key)):
            out[key] = raw[key].upper()
    if raw.get("button_style") in BUTTON_STYLES:
        out["button_style"] = raw["button_style"]
    if raw.get("radius") in RADII:
        out["radius"] = raw["radius"]
    if raw.get("font") in FONTS:
        out["font"] = raw["font"]
    return out


def resolve(appearance):
    """Turn a stored appearance into {style, font, css (inline style string), google font}."""
    appearance = clean(appearance)
    preset = PRESETS[appearance["theme"]]
    css_vars = dict(preset["vars"])

    if "bg" in appearance:
        text = contrast_text(appearance["bg"])
        css_vars["--bio-bg"] = appearance["bg"]
        css_vars["--bio-text"] = text
        css_vars["--bio-muted"] = "rgba(16,16,16,.65)" if text == "#101010" else "rgba(255,255,255,.75)"
    if "button_color" in appearance:
        css_vars["--bio-btn-bg"] = appearance["button_color"]
        css_vars["--bio-btn-text"] = contrast_text(appearance["button_color"])

    font_key = appearance.get("font", preset["font"])
    css_vars["--bio-radius"] = RADII[appearance.get("radius", preset["radius"])]
    css_vars["--bio-font"] = FONTS[font_key]["family"]

    return {
        "style": appearance.get("button_style", preset["style"]),
        "font": font_key,
        "google_font": FONTS[font_key]["google"],
        "css": ";".join(f"{k}:{v}" for k, v in css_vars.items()),
    }


def editor_config():
    """Static theme data the live preview needs to mirror `resolve()` in the browser."""
    return {
        "presets": PRESETS,
        "radii": RADII,
        "fonts": {k: {"name": v["name"], "family": v["family"]} for k, v in FONTS.items()},
        "button_styles": BUTTON_STYLES,
    }
