# Lerneffekte

Diese Datei enthält ausschließlich belegte, wiederverwendbare Hinweise zur Arbeit an diesem Kodi-Add-on. Sie steht unter `AGENTS.md`, `Projekt_Rules.md` und `.agent/router.md`.

## Eintragsformat

### YYYY-MM-DD – Kurzer Titel
- Werkzeug/Prozess: betroffener Ablauf.
- Beobachtung: nachweisbares Ergebnis.
- Ursache/Korrektur: falls bekannt.
- Künftig beachten: wiederverwendbare Konsequenz.

## Einträge

### 2026-10-21 – Kodi-Kompatibilität nicht aus dem Manifest allein ableiten
- Werkzeug/Prozess: Kompatibilitätsbewertung von Add-ons anhand `addon.xml` und Python-Code.
- Beobachtung: `xbmc.python` ABI 3.0.0 weist die Python-3-API-Anforderung aus, belegt aber allein keinen erfolgreichen Start oder vollständige Funktion in einer konkreten Kodi-Version.
- Künftig beachten: API-Kompatibilität anhand Kodi-Dokumentation einordnen und Laufzeitkompatibilität nur nach einem tatsächlichen Test in der Zielversion behaupten.
