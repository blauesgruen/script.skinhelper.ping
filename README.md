# Skinhelper PING

Skinhelper PING ist ein Kodi-Addon für Kodi 19 und neuer, einschließlich Kodi 22 „Piers“. Es überwacht bis zu fünf Geräte im Netzwerk per Ping und stellt Status, Namen, IP- und MAC-Adressen als Properties im Home-Fenster (`Window(10000)`) bereit. Außerdem kann es Geräte per Wake-on-LAN starten.

Eine Skin-Integration ist nötig, wenn der Status im Skin angezeigt werden soll. Alternativ lässt sich der Status im Add-on-Menü ansehen. Der optionale Hintergrunddienst ist standardmäßig ausgeschaltet und aktualisiert die Werte bei Aktivierung alle zehn Sekunden.

## Einrichtung

Trage in den Add-on-Einstellungen je Gerät Name, IP-Adresse und MAC-Adresse ein. Für eine Statusprüfung wird eine IP-Adresse benötigt; zum Aufwecken per Wake-on-LAN eine gültige MAC-Adresse. Aktuell können bis zu fünf Geräte konfiguriert werden.

Mit **Netzwerksuche** kannst Du ein lokales IPv4-Netz durchsuchen. Bei mehreren Netzwerkadaptern wählst Du den passenden aus. Nach dem Scan wählst Du ein Gerät, kannst den vorgeschlagenen Namen bearbeiten und bestätigst den freien Geräteplatz. Der Scan ist auf 4096 IP-Adressen pro Durchlauf begrenzt und kann abgebrochen werden. IP- und MAC-Adressen werden aus erreichbaren Geräten und der lokalen Nachbartabelle ermittelt; Gerätenamen werden nach Möglichkeit per Reverse-DNS vorgeschlagen. Nicht jedes Gerät beantwortet Ping oder stellt seine MAC-Adresse bereit. In diesem Fall kannst Du die Werte weiterhin manuell eintragen.

## Aufruf aus einem Skin

Status aktualisieren:

```xml
<onclick>RunScript(script.skinhelper.ping,status)</onclick>
```

Gerät 1 bis 5 per Wake-on-LAN wecken:

```xml
<onclick>RunScript(script.skinhelper.ping,wol1)</onclick>
```

Ersetze `wol1` durch `wol2` bis `wol5` für die weiteren Geräte. Ohne Parameter öffnet das Add-on eine Auswahlliste mit den konfigurierten Geräten.

## Skin-Properties

Die Werte sind über `Window(Home).Property(...)` verfügbar:

- `SkinHelperPING.server1` bis `server5`: `on` oder `off` für konfigurierte Geräte
- `SkinHelperPING.servername1` bis `servername5`: Anzeigename
- `SkinHelperPING.ip1` bis `ip5`: IP-Adresse
- `SkinHelperPING.mac1` bis `mac5`: MAC-Adresse
- `SkinHelperPING.servercount`: Anzahl konfigurierter Geräte
- `SkinHelperPING.serveron`: Anzahl erreichbarer Geräte
- `SkinHelperPING.serveroff`: Anzahl nicht erreichbarer Geräte

Beispiel für eine Anzeige im Skin:

```xml
<label>$INFO[Window(Home).Property(SkinHelperPING.serveron)]</label>
```

Der Hintergrunddienst wird in den Add-on-Einstellungen unter „Start Addon as Service“ aktiviert.

## Kodi-Kompatibilität

Das Add-on verwendet die Kodi-Python-API ABI 3.0.0 (`xbmc.python` 3.0.0), die von Kodi 19 eingeführt wurde und für Kodi 22 Piers abwärtskompatibel ist. Der Code verwendet Python-3-Standardbibliotheken und Kodi-APIs, die in Piers weiterhin vorhanden sind. Eine Laufzeitprüfung auf Kodi 22 ist in diesem Repository nicht enthalten.

---

# Skinhelper PING (English)

A Kodi add-on for Kodi 19 and later, including Kodi 22 “Piers”. It pings up to five configured network hosts and publishes their status, names, IP addresses, and MAC addresses as properties on the home window (`Window(10000)`). It can also wake devices with Wake-on-LAN.

Skin integration is required to display status in a skin. The add-on menu can also show the current status. The optional background service is disabled by default and refreshes the values every ten seconds when enabled.

Use **Network scan** in the add-on settings to search a local IPv4 network. If multiple network adapters are available, select the relevant one. After scanning, select a device, edit its suggested name, and confirm the free device slot. Each scan is limited to 4096 IP addresses and can be canceled. IP and MAC addresses are collected from responding devices and the local neighbor table; names are suggested through reverse DNS when available. Some devices do not answer ping or expose a MAC address. You can always enter device details manually.
