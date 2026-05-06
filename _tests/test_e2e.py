"""End-to-End-Smoke-Tests mit Playwright.

Diese Tests sind mit `@pytest.mark.e2e` markiert und werden im Standard-
Pytest-Lauf deselektiert (siehe `addopts` in pyproject.toml). Im CI laufen
sie nach `playwright install --with-deps chromium` mit `pytest -m e2e`.
"""

import os
import threading

import pytest
from werkzeug.serving import make_server

from pycgnweb.webapp import app

pytestmark = pytest.mark.e2e


@pytest.fixture(scope="module")
def live_server():
    """Startet einen Live-WSGI-Server in einem Hintergrund-Thread."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = os.path.join(os.getcwd(), "templates")
    app.config["TESTING"] = True

    server = make_server("localhost", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    host, port = server.server_address
    try:
        yield f"http://{host}:{port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def test_startseite_laedt(page, live_server):
    """Die Startseite muss laden und 'PyCologne' enthalten."""
    page.goto(f"{live_server}/")
    assert "PyCologne" in page.content()


def test_termine_laedt(page, live_server):
    """Die Termine-Seite muss laden."""
    response = page.goto(f"{live_server}/events")
    assert response is not None
    assert response.status == 200
