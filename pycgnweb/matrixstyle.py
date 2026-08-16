"""Pygments-Stil fuer die Rueckseiten der Flip-Kacheln.

Phosphorgruen auf sattem Dunkelgruen, bewusst als Matrix-Anklang. Die
Palette ist in docs/design.md dokumentiert und absichtlich themenfest:
die Rueckseite sieht in hellem wie dunklem Theme gleich aus, das
Umdrehen der Kachel ist der Moduswechsel.
"""

from pygments.style import Style
from pygments.token import (
    Comment,
    Keyword,
    Name,
    Number,
    Operator,
    Punctuation,
    String,
    Token,
)


class MatrixStyle(Style):
    """Alle Farben aus der Phosphor-Palette, s. docs/design.md."""

    background_color = "#04120a"
    highlight_color = "#14402a"

    styles = {  # noqa: RUF012, Pygments erwartet hier ein Klassenattribut
        Token: "#a9f5c4",
        Comment: "italic #55a878",
        Keyword: "#00ff41",
        Operator: "#5fbf82",
        Operator.Word: "#00ff41",
        Punctuation: "#5fbf82",
        Name: "#a9f5c4",
        Name.Function: "#6dffa0",
        Name.Class: "#6dffa0",
        Name.Builtin: "#6dffa0",
        Name.Decorator: "#6dffa0",
        String: "#d2ffe0",
        String.Doc: "italic #d2ffe0",
        Number: "#6dffa0",
    }
