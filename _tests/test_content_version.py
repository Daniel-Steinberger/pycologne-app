"""Tests fuer den Stand der Inhalte in der Fusszeile.

Die Inhalte liegen auf dem Server in einem Git-Checkout. Welcher Commit
gerade ausgeliefert wird, liest die Anwendung direkt aus dessen
Git-Verzeichnis, ohne Unterprozess. Hier wird beides geprueft: die
gelesenen Faelle und der Fall ohne Checkout, in dem die Fusszeile die
Angabe einfach weglaesst.
"""

import os
import shutil

import pytest

from pycgnweb.webapp import app, content_commit

COMMIT = "23400fcabcdef0123456789abcdef0123456789a"


@pytest.fixture
def client(template_root):
    """Flask-Test-Client auf dem Inhaltsbestand der Tests."""
    app.static_folder = os.path.join(os.getcwd(), "static")
    app.template_folder = str(template_root)
    app.config["TESTING"] = True
    return app.test_client()


@pytest.fixture
def git_dir(template_root):
    """Ein Git-Verzeichnis neben den Inhalten, nach dem Test wieder weg."""
    path = template_root / ".git"
    path.mkdir()
    try:
        yield path
    finally:
        shutil.rmtree(path)


def test_loose_ref_is_read(client, git_dir):
    """Der Normalfall: HEAD zeigt auf einen Branch, der als Datei vorliegt."""
    (git_dir / "HEAD").write_text("ref: refs/heads/live\n", encoding="utf-8")
    (git_dir / "refs" / "heads").mkdir(parents=True)
    (git_dir / "refs" / "heads" / "live").write_text(COMMIT + "\n", encoding="utf-8")

    assert content_commit() == COMMIT
    html = client.get("/").get_data(as_text=True)
    assert f"Inhalte {COMMIT[:7]}" in html
    assert f"pycologne-content/commit/{COMMIT}" in html


def test_packed_ref_is_read(client, git_dir):
    """Nach einem git gc liegt die Referenz nur noch in packed-refs."""
    (git_dir / "HEAD").write_text("ref: refs/heads/live\n", encoding="utf-8")
    (git_dir / "packed-refs").write_text(
        f"# pack-refs with: peeled fully-peeled sorted\n{COMMIT} refs/heads/live\n",
        encoding="utf-8",
    )

    assert content_commit() == COMMIT
    assert f"Inhalte {COMMIT[:7]}" in client.get("/").get_data(as_text=True)


def test_detached_head_is_read(client, git_dir):
    """Steht der Checkout auf einem Commit statt auf einem Branch."""
    (git_dir / "HEAD").write_text(COMMIT + "\n", encoding="utf-8")

    assert content_commit() == COMMIT
    assert f"Inhalte {COMMIT[:7]}" in client.get("/").get_data(as_text=True)


def test_dangling_ref_yields_nothing(client, git_dir):
    """Zeigt HEAD ins Leere, wird nichts behauptet."""
    (git_dir / "HEAD").write_text("ref: refs/heads/gibt-es-nicht\n", encoding="utf-8")

    assert content_commit() is None
    assert "Inhalte " not in client.get("/").get_data(as_text=True)


def test_without_checkout_the_footer_stays_quiet(client):
    """Ohne Git-Verzeichnis laesst die Fusszeile die Angabe weg.

    Das ist der Zustand bei der lokalen Entwicklung ohne Checkout und
    ueberall dort, wo die Inhalte anders hinkommen.
    """
    assert content_commit() is None
    html = client.get("/").get_data(as_text=True)
    assert "Inhalte " not in html
    # die uebrige Fusszeile steht weiterhin
    assert "Quellcode" in html
