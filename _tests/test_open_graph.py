"""Tests fuer die Vorschau in sozialen Netzen (Open Graph).

Facebook und X bauen ihre Link-Vorschau aus diesen Angaben und holen sie von
aussen. Alles darin muss deshalb eine absolute Adresse sein, ein relativer
Pfad ist dort wertlos.
"""

import os
import re

import pytest

from pycgnweb.webapp import app

from .conftest import NEWEST_NEWS


@pytest.fixture
def client(template_root):
    """Flask-Test-Client auf dem Inhaltsbestand der Tests."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = str(template_root)
    app.config["TESTING"] = True
    return app.test_client()


def _meta(page: str, prop: str) -> str | None:
    """Den Inhalt eines og-Meta-Tags aus der Seite ziehen."""
    match = re.search(rf'<meta property="{prop}" content="([^"]*)">', page)
    return match.group(1) if match else None


@pytest.mark.parametrize("path", ["/", "/about", "/events", "/news", "/contact"])
def test_every_page_carries_open_graph(client, path):
    """Jede Seite nennt Titel, Adresse und Bild."""
    page = client.get(path).get_data(as_text=True)
    assert _meta(page, "og:title")
    assert _meta(page, "og:url") == f"https://www.pycologne.de{path}"
    assert _meta(page, "og:image") == "https://www.pycologne.de/static/images/og-default.png"


def test_preview_image_is_a_raster_file(client):
    """Das Vorschaubild ist kein SVG, das rendert dort keine Vorschau."""
    page = client.get("/").get_data(as_text=True)
    image = _meta(page, "og:image") or ""
    assert image.endswith(".png")
    assert _meta(page, "og:image:width") == "1200"
    assert _meta(page, "og:image:height") == "630"


def test_default_title_comes_from_the_page_title(client):
    """Ohne eigene Angabe traegt die Vorschau den Seitentitel."""
    page = client.get("/news").get_data(as_text=True)
    assert _meta(page, "og:title") == "News, PyCologne"
    assert _meta(page, "og:type") == "website"


def test_news_entry_overrides_title_type_and_description(client):
    """Ein geteilter Eintrag zeigt sich selbst, nicht die ganze Seite."""
    page = client.get(f"/news/{NEWEST_NEWS}").get_data(as_text=True)
    assert _meta(page, "og:title") == "Facebook nach zehn Jahren"
    assert _meta(page, "og:type") == "article"
    description = _meta(page, "og:description") or ""
    assert description.startswith("Unsere alte Facebook-Seite lebt wieder")
    # Klartext, kein HTML: das Teaser-Markup darf hier nicht auftauchen.
    assert "<" not in description


def test_description_falls_back_to_the_site_description(client):
    """Seiten ohne eigene Beschreibung nehmen die der Webseite."""
    page = client.get("/about").get_data(as_text=True)
    assert _meta(page, "og:description") == (
        "PyCologne, die Python User Group Köln. Monatliche Treffen, "
        "Vorträge, Diskussionen rund um Python."
    )


def test_meta_description_and_open_graph_agree(client):
    """Beschreibung im Head und in der Vorschau kommen aus einer Quelle."""
    page = client.get("/").get_data(as_text=True)
    head = re.search(r'<meta name="description" content="([^"]*)">', page)
    assert head is not None
    assert head.group(1) == _meta(page, "og:description")
