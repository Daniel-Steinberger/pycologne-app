"""Tests fuer den Anstoss, dass es neue Inhalte gibt.

Der Endpunkt prueft die Signatur und beruehrt eine Datei, sonst nichts.
Genau das wird hier geprueft, inklusive der Faelle, in denen er nichts tun
darf: falsche Signatur, fehlende Signatur, kein Secret hinterlegt.
"""

import hashlib
import hmac
import os

import pytest

from pycgnweb.webapp import app

SECRET = b"nur-fuer-den-test"
BODY = b'{"ref": "refs/heads/live"}'


def signature(secret: bytes, body: bytes) -> str:
    """Signatur bilden, wie GitHub sie im Header mitschickt."""
    return "sha256=" + hmac.new(secret, body, hashlib.sha256).hexdigest()


@pytest.fixture
def paths(tmp_path, monkeypatch, template_root):
    """Secret- und Trigger-Datei in ein temporaeres Verzeichnis umbiegen."""
    secret_file = tmp_path / "webhook-secret"
    trigger_file = tmp_path / "content-refresh.trigger"
    secret_file.write_bytes(SECRET + b"\n")
    monkeypatch.setenv("PYCOLOGNE_WEBHOOK_SECRET_FILE", str(secret_file))
    monkeypatch.setenv("PYCOLOGNE_CONTENT_TRIGGER", str(trigger_file))
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = str(template_root)
    app.config["TESTING"] = True
    return secret_file, trigger_file


def post(client, body=BODY, header=None):
    """Anfrage absetzen, wie GitHub sie schickt."""
    headers = {"X-GitHub-Delivery": "test-delivery-1"}
    if header is not None:
        headers["X-Hub-Signature-256"] = header
    return client.post("/_content/refresh", data=body, headers=headers)


def test_valid_signature_touches_trigger(paths):
    """Mit gueltiger Signatur entsteht die Trigger-Datei."""
    _, trigger_file = paths
    assert not trigger_file.exists()
    response = post(app.test_client(), header=signature(SECRET, BODY))
    assert response.status_code == 202
    assert trigger_file.exists()
    # Die Delivery-ID landet in der Datei, damit sich ein einzelner
    # Anstoss bis zur Auslieferung zurueckverfolgen laesst.
    assert trigger_file.read_text(encoding="utf-8").strip() == "test-delivery-1"


def test_wrong_signature_is_rejected(paths):
    """Eine falsche Signatur loest nichts aus."""
    _, trigger_file = paths
    response = post(app.test_client(), header=signature(b"falsches-secret", BODY))
    assert response.status_code == 403
    assert not trigger_file.exists()


def test_signature_covers_the_body(paths):
    """Eine Signatur ueber einen anderen Rumpf zaehlt nicht."""
    _, trigger_file = paths
    response = post(app.test_client(), body=b'{"ref": "andere"}', header=signature(SECRET, BODY))
    assert response.status_code == 403
    assert not trigger_file.exists()


def test_missing_signature_is_rejected(paths):
    """Ohne Signatur-Header passiert nichts."""
    _, trigger_file = paths
    response = post(app.test_client())
    assert response.status_code == 403
    assert not trigger_file.exists()


def test_without_secret_the_hook_is_off(paths, tmp_path, monkeypatch):
    """Ohne hinterlegtes Secret ist der Endpunkt schlicht nicht eingerichtet.

    Das ist der Zustand auf einem frischen System und bei der lokalen
    Entwicklung. Er darf keinen Fehler werfen und vor allem nichts
    ausloesen.
    """
    _, trigger_file = paths
    monkeypatch.setenv("PYCOLOGNE_WEBHOOK_SECRET_FILE", str(tmp_path / "gibt-es-nicht"))
    response = post(app.test_client(), header=signature(SECRET, BODY))
    assert response.status_code == 503
    assert not trigger_file.exists()


def test_empty_secret_file_counts_as_unset(paths, monkeypatch):
    """Eine leere Secret-Datei darf nicht als gueltiges Secret durchgehen."""
    secret_file, trigger_file = paths
    secret_file.write_bytes(b"\n")
    response = post(app.test_client(), header=signature(b"", b""))
    assert response.status_code == 503
    assert not trigger_file.exists()


def test_get_is_not_allowed(paths):
    """Der Endpunkt nimmt nur POST an."""
    assert app.test_client().get("/_content/refresh").status_code == 405
