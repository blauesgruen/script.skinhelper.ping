# Projektregeln

## Zweck und Aufbau

`script.skinhelper.ping` ist ein Kodi-Script-Add-on. `default.py` prüft bis zu zehn eingetragene Geräte per Ping, zeigt den Status an und kann Wake-on-LAN senden. `service.py` ist ein optionaler Kodi-Hintergrunddienst. `resources/settings.xml` enthält die Einstellungen; Übersetzungen liegen unter `resources/language/`.

Kodi-Skins lesen die Werte aus `Window(10000)`. Die Dokumentation der Skin-Integration steht in `README.md`.

## Kodi- und Python-Kompatibilität

- Die bestehende Add-on-Abhängigkeit `xbmc.python` ABI `3.0.0` ist die Kompatibilitätsbasis.
- Keine Kodi-API oder Python-Version als unterstützt ausgeben, ohne sie anhand des Codes oder eines passenden Kodi-Laufzeittests belegt zu haben.
- Kodi Omega und Piers verwenden die Python-3-Add-on-API. Das Add-on verlangt `xbmc.python` ABI `3.0.0`; konkrete Laufzeitkompatibilität ist jeweils durch Tests in der Zielversion zu belegen.
- Kodi stellt je Plattform unterschiedliche Betriebssysteme und Befehle bereit. Plattformabhängige Ping-Optionen müssen erhalten bleiben.
- Keine zusätzliche Python-Abhängigkeit einführen, wenn Standardbibliothek oder Kodi-API ausreichen.

## Schnittstellen, die stabil bleiben müssen

- Add-on-ID: `script.skinhelper.ping`.
- Einstellungsschlüssel: `name1`–`name10`, `ip1`–`ip10`, `mac1`–`mac10` und `service`.
- Skin-Property-Präfix: `SkinHelperPING`.
- Pro Gerät: `serverN` (`on`/`off` bei konfigurierter IP), `servernameN`, `ipN`, `macN`.
- Zusammenfassungen: `servercount`, `serveron`, `serveroff`.
- Script-Aufrufe: ohne Parameter für die Auswahlliste, `status` zur Statusaktualisierung, `wol1` bis `wol10` für Wake-on-LAN und `remove1` bis `remove10` für die Löschaktionen in den Geräteeinstellungen.

Änderungen an diesen Namen oder Aufrufverträgen können bestehende Skins brechen. Sie müssen deshalb gemeinsam mit README und Kompatibilitätsfolgen angepasst werden.

## Sicherheit und Robustheit

- Netzwerkadressen werden als Argumente an Prozesse übergeben; kein Shell-Aufruf mit interpolierten Einstellungen.
- Eingaben werden vor Wake-on-LAN geprüft. Ungültige Werte dürfen Kodi nicht zum Absturz bringen.
- Fehler wie fehlender Ping-Befehl, Zeitüberschreitung oder nicht erreichbare Geräte werden kontrolliert behandelt und passend protokolliert.
- Ein nicht konfiguriertes Gerät darf keinen alten Online-Status behalten.
- Der Hintergrunddienst muss `xbmc.Monitor` zum Beenden verwenden und darf nur im aktivierten Zustand periodisch prüfen.

## Dokumentation und Version

README dokumentiert Einrichtung, Skin-Properties, Script-Aufrufe und bekannte Laufzeitgrenzen. Änderungen an Verhalten oder Aufrufen werden dort nachvollziehbar nachgeführt. `changelog.txt` fasst umgesetzte Änderungen zusammen. Versionsnummern ändert ausschließlich die nutzende Person, sofern sie es nicht ausdrücklich anders beauftragt.

## Branch und ZIP-Veröffentlichung

- `master` ist die gemeinsame Entwicklungsbasis für Kodi Omega und Piers. Änderungen laufen über kurzlebige Feature-Branches und Pull Requests.
- Der lokale `post-commit`-Hook überspringt `master` und erstellt dort kein ZIP.
- Bei jedem Push nach `master` baut GitHub Actions die ZIP und veröffentlicht dieselbe Version in die Omega- und Piers-Feeds des BG-Repositories. Der Workflow benötigt das Repository-Secret `BG_REPOSITORY_TOKEN`.
- Das Paket enthält die zur Laufzeit benötigten Add-on-Dateien, nicht die Projektregeln `AGENTS.md`, `Projekt_Rules.md`, `ML.md` oder `CLAUDE.md`. Versteckte Verzeichnisse wie `.agent`, `.github` und `.idea` werden ebenfalls ausgelassen.
- Der Hook läuft nach einem Commit. Keine Commits nur zum Auslösen des Paketbaus erstellen; den Build bei Bedarf direkt ausführen.
