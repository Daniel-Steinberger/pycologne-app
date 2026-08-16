/* Flip-Kacheln: Code hinter der Kachel, s. docs/design.md.
 *
 * Progressive Enhancement: Ohne dieses Script ist der Griff ein Link auf
 * die Funktion im GitHub-Repo und die Rueckseite bleibt verborgen. Hier
 * wird der Link durch einen Umdreh-Knopf ersetzt und die 3D-Drehung
 * freigeschaltet (.flip--ready).
 *
 * Der Griff gehoert zur Vorderseite und dreht mit ihr weg, die Rueckseite
 * bringt ihren eigenen Schliessen-Knopf in der Terminal-Kopfzeile mit.
 * Die jeweils abgewandte Seite ist inert, damit Fokus und Screenreader
 * nicht hinter der Kachel landen; der Fokus wandert beim Drehen auf das
 * Bedienelement der neuen Seite. Escape dreht zurueck.
 */
(function () {
  "use strict";

  document.querySelectorAll(".flip").forEach(function (tile) {
    var link = tile.querySelector("[data-flip-toggle]");
    var front = tile.querySelector(".flip__face--front");
    var back = tile.querySelector(".flip__face--back");
    var close = tile.querySelector("[data-flip-close]");
    if (!link || !front || !back || !close) {
      return;
    }

    var button = document.createElement("button");
    button.type = "button";
    button.className = link.className;
    button.setAttribute("aria-label", link.getAttribute("aria-label") || "Quelltext zeigen");
    button.setAttribute("aria-expanded", "false");
    if (link.title) {
      button.title = link.title;
    }
    button.innerHTML = link.innerHTML;
    link.replaceWith(button);

    back.setAttribute("inert", "");
    tile.classList.add("flip--ready");

    function setFlipped(flipped) {
      tile.classList.toggle("is-flipped", flipped);
      button.setAttribute("aria-expanded", String(flipped));
      if (flipped) {
        front.setAttribute("inert", "");
        back.removeAttribute("inert");
        close.focus();
      } else {
        back.setAttribute("inert", "");
        front.removeAttribute("inert");
        button.focus();
      }
    }

    button.addEventListener("click", function () {
      setFlipped(true);
    });
    close.addEventListener("click", function () {
      setFlipped(false);
    });
    tile.addEventListener("keydown", function (event) {
      if (event.key === "Escape" && tile.classList.contains("is-flipped")) {
        setFlipped(false);
      }
    });
  });
}());
