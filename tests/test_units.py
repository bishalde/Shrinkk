from services import socials, themes
from utils.formatting import compact, flag
from utils.validators import is_safe_next, is_valid_alias, username_error


def test_username_rules():
    assert username_error("alice_01") is None
    assert username_error("ab") is not None
    assert username_error("Alice") is not None  # must already be normalized to lowercase
    assert username_error("dashboard") == "That username is reserved."
    assert username_error(".alice") is not None
    assert username_error("a..b") is not None


def test_alias_rejects_reserved_paths():
    assert is_valid_alias("launch-2026")
    assert not is_valid_alias("dashboard")
    assert not is_valid_alias("Login")
    assert not is_valid_alias("no spaces")


def test_safe_next_only_allows_local_paths():
    assert is_safe_next("/dashboard/links")
    assert not is_safe_next("https://evil.com")
    assert not is_safe_next("//evil.com")
    assert not is_safe_next("/\\evil.com")
    assert not is_safe_next("")


def test_theme_resolve_applies_overrides_with_contrast():
    look = themes.resolve({"theme": "classic", "bg": "#000000", "button_color": "#FFFFFF", "radius": "full"})
    assert "--bio-bg:#000000" in look["css"]
    assert "--bio-text:#FFFFFF" in look["css"]
    assert "--bio-btn-text:#101010" in look["css"]
    assert "--bio-radius:999px" in look["css"]


def test_theme_clean_drops_unknown_values():
    assert themes.clean({"theme": "nope", "bg": "red", "font": "comic"}) == {"theme": "classic"}


def test_socials_normalize_handles_and_urls():
    assert socials.to_url("instagram", "@alice") == "https://instagram.com/alice"
    assert socials.to_url("tiktok", "alice") == "https://tiktok.com/@alice"
    assert socials.to_url("website", "alice.dev") == "https://alice.dev"
    assert socials.to_url("email", "a@b.co") == "mailto:a@b.co"
    assert socials.to_url("email", "nope") is None
    cleaned, errors = socials.clean({"x": "@al", "github": "bad handle!"})
    assert cleaned == {"x": "@al"} and "github" in errors


def test_formatting():
    assert compact(999) == "999"
    assert compact(1500) == "1.5k"
    assert compact(2_000_000) == "2M"
    assert flag("US") == "🇺🇸"
    assert flag(None) == "🌐"
