"""Smoke-Tests fuer HTTP-Status aller Routen via Flask-Test-Client."""

import os

import pytest

from pycgnweb.webapp import app


@pytest.fixture
def client():
    """Flask-Test-Client mit Pfaden auf das Repo-Root konfiguriert."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = os.path.join(os.getcwd(), "templates")
    app.config["TESTING"] = True
    return app.test_client()


@pytest.mark.parametrize(
    "path",
    ["/", "/index", "/about", "/join", "/events", "/contact"],
)
def test_page_returns_ok(client, path):
    """Jede der oeffentlichen Routen muss HTTP 200 liefern."""
    response = client.get(path)
    assert response.status_code == 200


def test_unknown_url_returns_404(client):
    """Unbekannte URLs muessen 404 liefern."""
    response = client.get("/this-does-not-exist")
    assert response.status_code == 404
