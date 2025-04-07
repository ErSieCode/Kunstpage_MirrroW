# Kunstpage_MirrroW

# Karl Ulinger - Interaktive Kunstgalerie Webseite

Dies ist eine moderne, interaktive Single-Page-Webanwendung zur Präsentation der Kunstwerke von Karl Ulinger. Die Seite wurde mit reinem HTML, CSS und JavaScript erstellt und nutzt eingebettete JSON-Daten zur dynamischen Anzeige der Kunstwerke und Blog-Einblicke.

![Screenshot der Galerie](link/zum/screenshot.png)  (später) <!-- WICHTIG: Füge hier einen Screenshot deiner Seite ein! -->

[Link zur Live-Demo]([deine-live-demo-url.hier](https://github.com/ErSieCode/Kunstpage_MirrroW/blob/main/Karl_Ulinger_Art.html))  (später) <!-- Optional: Füge hier einen Link zur gehosteten Version hinzu -->

## ✨ Features

*   **Dynamische Kunstgalerie:** Zeigt Kunstwerke aus einer integrierten Datenquelle an.
*   **Detaillierte Ansicht:** Klickbare Karten öffnen ein Modal (Lightbox) mit größerem Bild, Beschreibung, Metadaten und kuratorischem Text.
*   **Filterung:** Filtern der Werke nach Kategorien (z.B. Gemälde, Digital, Print, Großformat).
*   **Textsuche:** Volltextsuche über Titel, Beschreibung, Kategorie, Jahr, Technik und Maße.
*   **Ansichtsoptionen:** Wechsel zwischen Raster- und Listenansicht für die Galerie.
*   **Licht-/Dunkelmodus:** Umschaltbares Theme für unterschiedliche Vorlieben.
*   **Responsive Design:** Anpassung an verschiedene Bildschirmgrößen (Desktop, Tablet, Mobil).
*   **Aktuelles / Blog-Einblicke:** Zeigt die neuesten relevanten Einträge (basierend auf den bereitgestellten Daten) mit direkten Links zu den Blog-Posts. Fallback-Link zur Blog-Hauptseite, wenn keine Einträge gefunden werden.
*   **Direkte Verlinkung:** Links zu den Original-Blogspot-Quellen der Werke und Blog-Posts.
*   **Kontaktformular:** Integriertes (simuliertes) Kontaktformular.
*   **Lokaler Admin-Bereich (Optional):** Möglichkeit, neue Werke *nur lokal im Browser* für Testzwecke hinzuzufügen (Daten gehen beim Neuladen verloren).
*   **Reine Frontend-Lösung:** Läuft komplett im Browser ohne serverseitige Abhängigkeiten (außer für das Hosting der Datei selbst).

## 🚀 Benutzung / Setup

Da dies eine reine Frontend-Anwendung in einer einzigen HTML-Datei ist, ist die Benutzung sehr einfach:

1.  **Herunterladen oder Klonen:**
    *   Lade die `index.html` (oder wie auch immer du sie nennst) Datei herunter.
    *   Oder klone das Repository: `git clone https://github.com/dein-benutzername/dein-repo-name.git`
2.  **Öffnen im Browser:** Öffne die heruntergeladene HTML-Datei direkt in einem modernen Webbrowser (wie Chrome, Firefox, Edge, Safari). Doppelklicken auf die Datei sollte genügen.

Fertig! Die Galerie sollte nun mit den integrierten Daten angezeigt werden.

**Hosting (Optional):**

Wenn du die Seite online verfügbar machen möchtest, kannst du die HTML-Datei einfach bei einem statischen Hosting-Anbieter hochladen, wie z.B.:

*   [GitHub Pages](https://pages.github.com/)
*   [Netlify](https://www.netlify.com/)
*   [Vercel](https://vercel.com/)
*   oder jedem anderen Webspace, der HTML-Dateien hosten kann.

## 🛠️ Technologie-Stack

*   **HTML5:** Semantische Strukturierung des Inhalts.
*   **CSS3:** Styling und Layout (Flexbox, Grid, Custom Properties, Transitions, Farbverläufe).
*   **JavaScript (ES6+):**
    *   DOM-Manipulation zur dynamischen Erstellung der Galerie und Modals.
    *   Event Handling für Filter, Suche, Theme-Wechsel, Modals etc.
    *   Verarbeitung der eingebetteten JSON-Daten.
    *   Speicherung von Nutzerpräferenzen (Theme, Ansicht) im `localStorage`.
*   **Font Awesome:** Für Icons.

## ⚙️ Funktionsweise & Datenhandling

Diese Webseite ist als **Single-File-Anwendung** konzipiert. Der gesamte Code (HTML, CSS, JavaScript) befindet sich in einer Datei.

**Datenquelle:**

Die Kernfunktionalität (Anzeige der Kunstwerke und Blog-Einblicke) basiert **ausschließlich auf den JSON-Daten**, die direkt in die Variable `rawArtworkData` innerhalb des `<script>`-Blocks am Ende der HTML-Datei eingebettet sind.

**WICHTIG:** Die Anwendung **durchsucht nicht aktiv** die Blogspot-Seite in Echtzeit! Sie verlässt sich vollständig auf die bereitgestellten `rawArtworkData`.

**Datenverarbeitung:**

1.  Beim Laden der Seite liest die JavaScript-Funktion `createArtworksFromData` die `rawArtworkData`.
2.  Für jeden Eintrag im JSON wird ein internes `artwork`-Objekt erstellt, wobei versucht wird, die Daten zu bereinigen und sinnvolle Kategorien abzuleiten (z.B. "gemälde" aus "Acryl auf Leinwand", "großformat" basierend auf Dimensionen).
3.  Diese bereinigte Liste (`artworks` im Skript) wird dann von den Funktionen `renderGallery`, `createGalleryItem` und `openArtworkModal` verwendet, um die Galerie und die Detailansichten dynamisch im HTML zu erzeugen.
4.  Die Funktion `populateNewsSection` filtert ebenfalls `rawArtworkData`, um Einträge zu finden, die Blog-Posts ähneln (anhand von `Ursprungs_Post_Titel` und `Ursprungs_Post_Datum`), und zeigt die neuesten davon im News-Bereich an, wobei der Link auf die `Quell_URL` des jeweiligen Posts verweist. Wenn keine passenden Posts gefunden werden, wird ein Button zur Blog-Hauptseite angezeigt.

**Interaktivität:**

*   Event-Listener für Klicks (Filter, Buttons, Modal-Schließen) und Eingaben (Suche) steuern die Funktionalität.
*   Das Theme und die Galerieansicht (Grid/List) werden im `localStorage` des Browsers gespeichert, um die Präferenz des Nutzers beim erneuten Besuch beizubehalten.

## 🔧 Anpassung & Erweiterung

**1. Aktualisieren der Kunstwerke/Daten:**

Dies ist der wichtigste Punkt zur Pflege der Seite!

*   **Öffne** die HTML-Datei in einem Texteditor.
*   **Finde** die JavaScript-Variable `const rawArtworkData = [ ... ];` (ziemlich am Anfang des `<script>`-Blocks).
*   **Bearbeite** diese Liste:
    *   **Neue Werke:** Füge neue JavaScript-Objekte im gleichen Format hinzu. Stelle sicher, dass alle Felder (insbesondere `"Name des Werkes"`, `"Das ganze Bild als vollen roh link"`, `"Thumpnail des Bildes als link"`) korrekt ausgefüllt sind. Füge auch den `"Kuratorischer Beschreibungstext"` hinzu.
    *   **Daten korrigieren:** Ändere die Werte in den bestehenden Objekten, wenn z.B. das Jahr oder die Beschreibung falsch sind.
    *   **Entfernen:** Lösche Objekte aus dem Array, um Werke aus der Galerie zu entfernen.
*   **Speichere** die HTML-Datei.

**Struktur eines Datenobjekts:**

```javascript
{
    "Name des Werkes": "TITEL HIER",
    "Erscheinungsdatum": "JAHR ODER DATUM HIER", // z.B. "2023" oder "15. Mai 2023"
    "Kunstform": "TECHNIK HIER", // z.B. "Acryl auf Leinwand", "Digital", "Aquarell"
    "Formatgröße": "MASSE HIER", // z.B. "70x100cm", "DIN A4"
    "Beschreibung des Bildes": "BESCHREIBUNG HIER.",
    "Thumpnail des Bildes als link": "URL ZUM KLEINEN BILD HIER", // z.B. von Blogspot mit /s320/ oder /s400/ am Ende
    "Das ganze Bild als vollen roh link": "URL ZUM GROSSEN BILD HIER", // z.B. von Blogspot mit /s0/ am Ende
    "Quell_URL": "URL ZUM ORIGINAL-BLOGPOST ODER SEITE", // Wichtig für Verlinkung
    "Ursprungs_Post_Titel": "TITEL DES BLOGPOSTS (falls zutreffend)",
    "Ursprungs_Post_Datum": "DATUM/ZEIT DES POSTS (falls zutreffend)",
    "Kuratorischer Beschreibungstext": "AUSFÜHRLICHER TEXT ZUM WERK (optional)." // NEU
}
