# Arbeitsablauf für dieses Kodi-Add-on

## 1. Bestand aufnehmen

- Branch, Arbeitsbaum und vorgemerkte Änderungen prüfen; nichts davon stillschweigend überschreiben.
- Relevante Dateien lesen: `addon.xml`, Python-Einstiegspunkte, Einstellungen, Übersetzungen, README und Changelog.
- Vorhandene Tests und Prüfskripte mit `rg --files` suchen. Nicht voraussetzen, dass ein Testsystem vorhanden ist.
- Bei Kodi- oder Piers-Fragen offizielle Kodi-Dokumentation bzw. die installierte Laufzeit verwenden und den Beleg nennen.

## 2. Änderung planen und umsetzen

- Kleinste Änderung wählen, die den beschriebenen Add-on-Vertrag erfüllt.
- Skin-Property-Namen, Einstellungs-IDs, Kodi-Add-on-API und Plattformunterschiede berücksichtigen.
- Keine nicht angeforderten Versionsnummern, Releases, Commits oder Pushes erzeugen.
- Dokumentation im selben Schritt aktualisieren, wenn sich Bedienung oder Verhalten ändert.

## 3. Prüfungen

- Relevante vorhandene Prüfungen zuerst lesen und ausführen.
- Python-Syntax kann mit `python -m py_compile default.py service.py` geprüft werden.
- `addon.xml` und `resources/settings.xml` müssen als XML parsebar sein.
- Kodi-Laufzeitverhalten ist nur geprüft, wenn es tatsächlich in der angegebenen Kodi-Version ausgeführt wurde. Syntax- und XML-Prüfungen ersetzen keinen Kodi-Test.
- Wenn Kodi lokal verfügbar ist, zuerst Version und ausführbaren Pfad ermitteln. Für einen vollständigen Test Add-on installieren, Einstellungen setzen, Script-Aufrufe ausführen, optionalen Dienst beobachten und Kodi-Log auf Fehler prüfen.
- Keine Prüfung als erfolgreich melden, wenn sie nicht ausgeführt wurde.

## 4. Abschluss

Kurz berichten:
- was geändert wurde und auf welchem Branch,
- welche Prüfungen tatsächlich liefen und mit welchem Ergebnis,
- was zur Laufzeit offen oder ungeprüft bleibt,
- relevante vorhandene Änderungen, die unangetastet blieben.

Kein agentischer Arbeitsmodus, Subagent, Review oder Plugin darf behauptet werden, wenn es nicht tatsächlich eingesetzt wurde.

## Branches und lokale Pakete

- `omega` und `piers` bleiben getrennte Entwicklungszweige.
- Für `script.skinhelper.ping` ist das lokale ZIP-Ziel branchabhängig: `omega` → `E:\Dokumente\kodiners repo multi\21`, `piers` → `E:\Dokumente\kodiners repo multi\22`.
- Die ZIP darf `AGENTS.md`, `Projekt_Rules.md`, `ML.md`, `CLAUDE.md` sowie versteckte Agenten-/Entwicklungsordner nicht enthalten.
- Ein `post-commit`-Hook baut das ZIP erst nach einem Commit. Ohne ausdrücklichen Commit-Auftrag keinen Commit dafür erstellen.
