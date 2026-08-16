# Design der PyCologne-Webseite

Stand: 2026-08-16. Zwei Teile: erst der Bestand, wie er in
`static/css/pycologne.css` und den Templates umgesetzt ist, danach das
Konzept "Code hinter den Kacheln". Das Konzept ist inzwischen
**umgesetzt** (Entscheidungen vom 16.08.2026: Variante A "Phosphor pur",
nur der Griff, alle vier Kandidaten sofort); Teil 2 dient damit als
Referenz der gebauten Lösung.

## Teil 1: Bestand, der "Adaptive Dev-Style"

### Grundidee

Die Seite soll aussehen wie das, was sie ist: die Webseite einer Python User
Group, gebaut von Leuten, die Code mögen. Daraus folgen die Leitplanken:

- **Farben von python.org**: Python-Blau (`#306998` hell, `#4584b6` dunkel)
  für Links und Primäraktionen, Python-Gelb (`#ffd43b`) als Akzent und
  Highlight. Der Dark-Mode nutzt ein weiches Navy (`#1a1d2e`) statt reinem
  Schwarz.
- **System-Fonts, keine Webfonts**: `ui-sans-serif`-Stack für Text,
  `ui-monospace`-Stack für alles Datenhafte. Termine, Datumsangaben,
  Eyebrows und Suchtreffer-Daten stehen bewusst in Mono, das ist das
  wiederkehrende "Dev"-Signal der Seite.
- **Kein Bootstrap, fast kein JavaScript**: Die Seite kam bis August 2026
  komplett ohne eigenes Script aus, Interaktivität lief über native
  HTML-Elemente (`<details>` für aufklappbare Jahrgänge). Seit den
  Flip-Kacheln gibt es genau ein Script, `static/js/flip.js`, als
  progressive enhancement (s. Teil 2). Daneben Leaflet auf der
  Anfahrtsseite.

### Token-System

Alle Gestaltungswerte sind Custom Properties in `:root`, organisiert in
`@layer reset, tokens, base, layout, components, utilities`. Die wichtigsten
Gruppen:

| Gruppe | Werte | Anmerkung |
|---|---|---|
| Farben | `--bg`, `--surface`, `--surface-alt`, `--text`, `--text-muted`, `--text-soft`, `--border`, `--border-strong`, `--accent`, `--primary`, `--code-bg` | jede Farbe als natives `light-dark()`-Paar |
| Typografie | `--fs-xs` bis `--fs-5xl` | ab `--fs-2xl` als `clamp()` fließend |
| Spacing | `--space-1` bis `--space-24` | 4-Punkt-Raster |
| Layout | `--container-max: 1180px`, `--content-max: 65ch`, `--gutter` | Lesetext bleibt bei 65 Zeichen |
| Form | `--radius-sm` bis `--radius-xl`, `--radius-pill` | Kacheln nutzen `--radius-xl` |
| Tiefe | `--shadow-sm/-md` | Schatten ebenfalls per `light-dark()`, dunkel kräftiger |

### Theming

`color-scheme: light dark` plus `light-dark()` für jeden Farbwert, es gibt
keine doppelten Regelblöcke pro Theme. Der Print-Stylesheet setzt
`color-scheme: only light`. Es gibt keinen Theme-Umschalter, die Seite folgt
dem System.

### Komponenten-Inventar

- **Kacheln** (`.tile`): der Grundbaustein der Startseite. Varianten:
  `--accent` (gelber Verlauf mit diagonaler Schraffur, Hero),
  `--saying` (gelbe Startkante, Zen-Zitat), `--code` (Code-Beistellkachel),
  `--map` (Leaflet).
- **Karten** (`.card`, `.card--accent`): das Pendant auf der Terminseite.
- **Listen** (`.upcoming-list`, `.past-link`): Terminvorschau und vergangene
  Treffen, Datum in Mono, Themen als Fließtext.
- **Archiv** (`.past-years`, `details.past-year`): Jahrgänge als native
  `<details>`, oberster Jahrgang offen.
- **Suche** (`.search-form`, `.search-results`): Treffer mit `<mark>` in
  Akzent-Gelb.
- **Prose** (`.prose`): gerenderte Markdown-Inhalte, begrenzt auf
  `--content-max`.
- **Fußzeile**: "Powered by"-Block mit Laufzeitversionen in Mono sowie der
  Commit des ausgelieferten Contents, verlinkt ins Content-Repo.

### Barrierefreiheit im Bestand

Skip-Link, `.sr-only`, sichtbarer Fokusring (`--ring-accent`), globales
`prefers-reduced-motion: reduce` im Reset (Animationen und Transitions auf
0.01ms), semantische Landmarken in `theme.html`.

### Code-Einblicke im Bestand (der Vorläufer des neuen Konzepts)

Bis August 2026 zeigte die Seite an zwei Stellen echten Quelltext, beide
gespeist aus `inspect.getsource()`, gerendert mit Pygments, ein Style pro
Theme (`default` hell, `monokai` dunkel): ein `<details class="code-reveal">`
unter der Terminliste auf `/events` (`meeting_dates()`) und eine statische
Beistellkachel (`.tile--code`) auf `/about` (`get_saying()`). Zwei Stellen,
zwei verschiedene Mechaniken. Beide sind im Flip-Muster aus Teil 2
aufgegangen, die Theme-Pygments-Styles wurden dabei durch den einen
Matrix-Stil ersetzt.

## Teil 2: Konzept "Code hinter den Kacheln"

### Idee

Jede Kachel, deren Inhalt von einer Funktion erzeugt wird, bekommt einen
kleinen Griff (`</>`) in der Ecke. Ein Klick dreht die Kachel um. Auf der
Rückseite steht der Quelltext, der genau diesen Inhalt gerade berechnet hat,
gestaltet als Terminal in Phosphorgrün, als bewusster Matrix-Anklang.
Darunter eine REPL-Zeile mit dem live ausgewerteten Ergebnis der Funktion.

Drei Regeln halten das ehrlich:

1. **Der Griff erscheint nur, wo wirklich Code läuft.** Redaktionelle
   Kacheln (Hero, "Was wir bieten") bekommen keinen. Das `</>` ist eine
   Aussage, kein Ornament.
2. **Die Rückseite lügt nie.** Der Quelltext kommt zur Laufzeit per
   `inspect.getsource()` aus dem Modul, nie als gepflegte Kopie.
3. **Ohne JavaScript bleibt alles benutzbar.** Der Griff ist zunächst ein
   Link auf die Funktion im GitHub-Repo (mit Zeilenanker). Ein kleines
   Script (Größenordnung 30 Zeilen, das erste der Seite) wertet ihn
   progressiv zum Umdreh-Knopf auf.

### Kandidaten

| Kachel | Seite | Funktion | REPL-Zeile zeigt |
|---|---|---|---|
| Nächstes Treffen | Startseite, Termine | `events.meeting_dates()` | `next(meeting_dates())`, das echte Datum |
| Zen-Zitat | Startseite | `sayings.get_saying()` | das gerade geloste Tupel |
| Protokollsuche | Suche | `search.build_query()` | den FTS5-Ausdruck der laufenden Suche, serverseitig gerendert |
| Kalender-Abo | Termine | `webapp._ics_fold()` | keine, hier trägt der Code allein |

Bewusst ohne Griff: Hero und "Was wir bieten" (redaktioneller Text) sowie
die Fußzeile (zeigt bereits Versionen und Content-Commit).

### Rückseite: Palette "Phosphor"

Die Rückseite ist eine eigene, themenfeste Welt. Sie bleibt in hellem wie
dunklem Theme identisch, das Umdrehen ist der Moduswechsel:

| Token | Wert | Rolle |
|---|---|---|
| `--mx-bg` | `#04120a` | Grund |
| `--mx-panel` | `#071b0f` | Flächen |
| `--mx-bar` | `#061609` | Terminal-Kopfzeile |
| `--mx-border` | `#14402a` | Ränder |
| `--mx-text` | `#a9f5c4` | Code-Grundtext |
| `--mx-bright` | `#00ff41` | Schlüsselwörter, Prompt, Glühen |
| `--mx-func` | `#6dffa0` | Funktionsnamen, Zahlen |
| `--mx-string` | `#d2ffe0` | Strings |
| `--mx-comment` | `#55a878` | Kommentare, kursiv |
| `--mx-out` | `#eafff2` | REPL-Ausgabe |

Dazu: Scanlines als `repeating-linear-gradient` (3px-Raster, 4 bis 5 Prozent
Deckung), leichte Vignette, Glühen (`text-shadow`) nur auf Schlüsselwörtern
und Prompt, blinkender Block-Cursor in der REPL-Zeile. Syntax-Highlighting
über einen eigenen Pygments-Style "matrix" mit genau diesen Tokens.

Aufbau der Rückseite von oben nach unten: Terminal-Kopfzeile (Status-Punkt,
Modulpfad wie `pycgnweb/sayings.py`, Label "live"), scrollender Code-Bereich,
REPL-Fußzeile mit Prompt und Ergebnis.

### Interaktion

- **Griff statt ganzer Kachel**: Die Vorderseiten enthalten Links und
  Buttons ("Zum Event", "Mitmachen"). Eine komplett klickbare Kachel würde
  damit kollidieren, der Griff in der Ecke bleibt eindeutig. Der Griff
  gehört zur Vorderseite und **dreht mit ihr weg**; die Rückseite bringt
  ihren eigenen Schließen-Knopf (`×`) fest in der Terminal-Kopfzeile mit.
  Kein Element schwebt über beiden Seiten, das Drehen wirkt dadurch wie
  ein Stück. (Erste Fassung hatte einen feststehenden Griff mit
  Label-Wechsel, auf Daniels Feedback hin verworfen.) Als Tooltip trägt
  der Griff "Peek into the code", der Schließen-Knopf "Exit the Matrix";
  die `aria-label` bleiben deutsch und funktional (Quelltext
  zeigen/schließen).
- **Flip**: 3D-Rotation um die Y-Achse, etwa 650ms,
  `cubic-bezier(.25,.7,.3,1)`, `backface-visibility: hidden`. Die
  Vorderseite bestimmt die Höhe, die Rückseite liegt absolut darüber und
  scrollt intern.
- **Barrierefreiheit**: Der Griff ist ein `<button aria-pressed>` mit
  `aria-label`. Bei `prefers-reduced-motion: reduce` wird hart umgeschaltet
  statt gedreht (der globale Reset erledigt das bereits), der Cursor blinkt
  dann nicht. Kontraste der Grüntöne gegen `--mx-bg` sind auf AA zu prüfen,
  kritisch ist nur der Kommentarton.
- **Ohne JS**: Der Griff ist ein `<a>` auf
  `https://github.com/Daniel-Steinberger/pycologne-app/blob/main/<datei>#L<zeile>`,
  das Script ersetzt ihn beim Laden durch den Button.

### Stilvarianten

- **A, Phosphor pur**: nur Scanlines, Glühen, Cursor. Ruhig, der Code trägt.
- **B, Digital Rain**: zusätzlich fallender Zeichenregen als `<canvas>`
  hinter dem Code, Deckung um 17 Prozent, läuft nur bei umgedrehter Kachel
  und pausiert bei `prefers-reduced-motion`.

**Entschieden (16.08.2026): Variante A**, überall. Der Regen aus Variante B
wurde nicht gebaut.

### Umsetzungsplan

1. **Fundament**: Pygments-Style "matrix", CSS-Komponente `.tile-flip` in
   `pycologne.css`, das 30-Zeilen-Script (Griff-Links aufwerten,
   `aria-pressed` pflegen).
2. **Backend-Register**: `inject_code_reveal` wird zu einem kleinen Register
   verallgemeinert (Kachel-Kennung, Funktion, Beschriftung, GitHub-Link),
   ein Context-Processor liefert alle Rückseiten fertig gerendert. Erste
   Kacheln: Zen-Zitat und Nächstes Treffen auf der Startseite.
3. **Ausweitung**: Termin-Kachel auf `/events`, Suchseite (REPL-Zeile zeigt
   den FTS5-Ausdruck der laufenden Suche), Kalender-Abo. Die beiden
   Bestandsmechaniken (`details.code-reveal` auf `/events`, statische
   `.tile--code` auf `/about`) gehen im neuen Muster auf.
4. **Feinschliff**: Fokusführung beim Umdrehen, AA-Kontrastprüfung,
   Höhenverhalten auf schmalen Screens, danach gegebenenfalls der Regen.

Jeder Schritt ist einzeln deploybar, nichts davon ändert Inhalte oder
Routen.

### Umsetzung (16.08.2026)

Alle vier Schritte wurden in einem Zug gebaut, die drei offenen Fragen hat
Daniel entschieden: Variante A (Phosphor pur), nur der Griff, alle vier
Kandidaten sofort. Die Bausteine im Repo:

- `pycgnweb/matrixstyle.py`: der Pygments-Stil mit der Phosphor-Palette.
- `pycgnweb/webapp.py`: `get_code_reveals()` als Register (Kennung zu
  Modulpfad, GitHub-Link mit Zeilenanker, gehighlightetem Quelltext),
  lazy beim ersten Request gebaut. Die REPL-Werte kommen aus den Routen
  als `repr()` genau der Werte, die auch die Vorderseite zeigt.
- `templates/flip.html`: Macros `terminal` (Matrix-Terminal, auch statisch
  nutzbar wie auf `/about`), `back` (Terminal als Rückseite) und `chip`
  (der Griff als Link, No-JS-Fallback).
- `static/js/flip.js`: ersetzt den Link durch einen Umdreh-Knopf
  (`aria-expanded`), schaltet `.flip--ready` frei und setzt die jeweils
  abgewandte Seite `inert`, damit Fokus und Screenreader nicht hinter der
  Kachel landen. Beim Drehen wandert der Fokus auf das Bedienelement der
  neuen Seite, Escape dreht zurück.
- `static/css/pycologne.css`: Matrix-Tokens im Token-Layer, Komponenten
  `.flip` und `.mx` im Components-Layer. Die alten Blöcke `.code-reveal`
  und `.tile--code .highlight` sind entfernt.
- `_tests/test_flip.py`: Register, alle vier Seiten, No-JS-Fallback, und
  dass Kacheln ohne Code keinen Griff bekommen.
