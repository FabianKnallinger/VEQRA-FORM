"""Prueft die gebaute Weboberflaeche (Web-Build)."""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
WEB_DIST = REPO_ROOT / "web" / "dist"


def test_web_build_exists() -> None:
    assert (WEB_DIST / "index.html").is_file(), \
        "web/dist fehlt - bitte zuerst 'make web' ausführen"


def test_web_build_is_self_contained() -> None:
    index = (WEB_DIST / "index.html").read_text(encoding="utf-8")
    assert "VEQRA FORM" in index
    assert "/assets/" in index

    assets = list((WEB_DIST / "assets").glob("*.js"))
    assert assets, "Keine JavaScript-Assets im Web-Build"

    # Keine externen CDN-Verweise: die Oberflaeche laeuft vollstaendig lokal
    for pattern in ("http://cdn.", "https://cdn.", "unpkg.com", "jsdelivr.net"):
        assert pattern not in index


def test_no_api_keys_in_web_build() -> None:
    """Der Browser darf niemals einen API-Schluessel enthalten.

    Der Name der Umgebungsvariable darf im Hilfetext vorkommen;
    echte Schluesselwerte (sk-ant-...) duerfen nirgends auftauchen.
    """

    for path in WEB_DIST.rglob("*"):
        if path.is_file() and path.suffix in (".js", ".html", ".css"):
            content = path.read_text(encoding="utf-8", errors="replace")
            assert "sk-ant-" not in content
