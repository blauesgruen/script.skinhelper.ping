# Projektanweisungen

Diese Regeln gelten für `script.skinhelper.ping`, ein Kodi-Add-on zur Erreichbarkeitsanzeige und zum Aufwecken von bis zu fünf Netzwerkgeräten.

## Vorrang

1. `AGENTS.md`
2. `Projekt_Rules.md`
3. `.agent/router.md`
4. `ML.md` als nachrangige Sammlung belegter, wiederverwendbarer Hinweise

## Arbeitsweise

- Vor Änderungen den betroffenen Python-Code, `addon.xml`, Einstellungen, Übersetzungen und die Skin-Properties prüfen.
- Fehlende Fakten nicht erraten. Annahmen und ungeprüfte Laufzeitbedingungen klar benennen.
- Änderungen klein halten und die vorhandenen Kodi-APIs sowie die Python-Standardbibliothek wiederverwenden.
- Verhalten oder Bedienung im selben Schritt in `README.md` und bei Bedarf in `changelog.txt` dokumentieren.
- Projektgespräche und neue Dokumentation sind auf Deutsch. Vorhandene deutsche und englische Add-on-Texte werden bei Änderungen konsistent gepflegt.
- Die Add-on-Version wird nur auf ausdrückliche Anweisung geändert.
- Commit und Push erfolgen nur auf ausdrückliche Anweisung.
- Vor einem Commit den aktiven `core.hooksPath` prüfen: auf diesem Entwicklungsrechner erstellt ein global konfigurierter `post-commit`-Hook ein Add-on-ZIP.
- Für `script.skinhelper.ping` bestimmt der Branch das lokale ZIP-Ziel: `omega` nach `E:\Dokumente\kodiners repo multi\21`, `piers` nach `E:\Dokumente\kodiners repo multi\22`.
- Add-on-ZIPs enthalten keine Projektregeln (`AGENTS.md`, `Projekt_Rules.md`, `ML.md`, `CLAUDE.md`) und keine versteckten Agenten-/Entwicklungsordner.
- Ein ZIP nicht durch einen Commit erzeugen, wenn kein Commit beauftragt wurde. Den Paketbau bei Bedarf direkt mit dem Build-Skript ausführen.

## Arbeitsmodus

Vor jeder Analyse oder Änderung `.agent/router.md` anwenden. Ohne besondere Vorgabe den kleinsten passenden Prüfpfad nutzen. Rollen oder zusätzliche Agenten sind nur bei tatsächlichem Mehrwert einzusetzen.
