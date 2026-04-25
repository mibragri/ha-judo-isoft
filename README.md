# JUDO Wasseraufbereitung — Home Assistant Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Validate](https://github.com/mibragri/ha-judo-isoft/actions/workflows/validate.yml/badge.svg)](https://github.com/mibragri/ha-judo-isoft/actions/workflows/validate.yml)

Custom Component für Home Assistant zur lokalen Anbindung von **JUDO Wasseraufbereitungsanlagen** (i-soft, i-soft K, i-soft Pro, Softwell, …) über das **JUDO Connectivity-Modul** (Art.-Nr. 2202271).

> **Lokal — kein Cloud-Account, keine `myjudo.eu`-Anmeldung.** Die Integration spricht direkt das REST-API des Connectivity-Moduls im LAN/WLAN an.

## Features

| Bereich | Entitäten |
|---|---|
| **Verbrauch** | Gesamtwassermenge (m³), Weichwassermenge (m³), Tagesverbrauch (L) |
| **Anlage** | Salzvorrat (g), Wunschwasserhärte (°dH), Betriebszeit |
| **Status** | Verbindung verloren / OK (Binary-Sensor) |
| **Aktionen** | Regeneration starten (Button) |
| **Schalter** | Leckageschutz, Urlaubsmodus |
| **Diagnose** | Inbetriebnahmedatum, Geräteinfo (Typ, Seriennummer, SW-Version) |

Sprachen: **Deutsch** und **Englisch**.

## Wie es technisch funktioniert

- **Eine zentrale `DataUpdateCoordinator`-Instanz** holt alle Werte gebündelt; Entitäten lesen aus einem geteilten Datencontainer
- **API-Throttling**: das Connectivity-Modul reagiert auf zu schnelle Anfragen mit leeren Antworten. Die Integration serialisiert Calls und hält **mindestens 11 s Pause** zwischen Aufrufen
- **HTTP only**: die neue Firmware (V2023+) leitet HTTPS auf HTTP um
- **Plausibilitätschecks** für Felder, die je nach Modell Junk-Werte liefern (z. B. Inbetriebnahmedatum bei i-soft K)

## Voraussetzungen

- Home Assistant **2025.1** oder neuer
- JUDO Connectivity-Modul (2202271) im Heimnetz, erreichbar per HTTP
- Erstkonfiguration der Connectivity-Modul-Verbindung über die JUDO-App oder das Web-UI bereits abgeschlossen (siehe Abschnitt unten)

## Installation

### Variante A — HACS (empfohlen)

1. HACS öffnen → drei Punkte oben rechts → **Eigene Repositories**
2. Repository: `https://github.com/mibragri/ha-judo-isoft`, Kategorie: **Integration**
3. *Judo Wasseraufbereitung* installieren
4. Home Assistant **neu starten**
5. *Einstellungen → Geräte & Dienste → Integration hinzufügen → Judo*

### Variante B — manuell

1. Inhalt von `custom_components/judo/` nach `<config>/custom_components/judo/` kopieren
2. Home Assistant neu starten
3. Integration über UI hinzufügen

## Konfiguration

| Feld | Standard | Beschreibung |
|---|---|---|
| **IP-Adresse / Hostname** | – | IP des Connectivity-Moduls im LAN |
| **Benutzername** | `admin` | Anmelde-Benutzer am Modul |
| **Passwort** | `Connectivity` | Werkspasswort (sollte am Modul geändert werden!) |

Eine spätere IP-Änderung (DHCP-Wechsel) lässt sich über **Reconfigure** im Integrations-Menü erledigen, ohne neu hinzuzufügen.

## Connectivity-Modul Erstkonfiguration

Falls dein Modul noch nicht im Netz ist:

1. Modul anschließen (LAN-Kabel optional)
2. Smartphone/Laptop mit der WLAN-SSID **`Judo Connectivity`** verbinden (Hotspot des Moduls)
3. Browser → `http://192.168.4.1`
4. Login: `admin` / `Connectivity`
5. *Einstellungen → WLAN aktivieren* + Heimnetz-SSID + Passwort eintragen → speichern
6. Optional: Portal-Server `myjudo.eu` Port `8585` aktivieren (für JU-Control-App)
7. Werkspasswort durch eigenes ersetzen
8. Modul neu starten — bekommt jetzt eine IP per DHCP im Heimnetz

## Bekannte Eigenheiten der Firmware (V2023+)

- **HTTPS leitet auf HTTP-Root um.** Die Integration nutzt direkt HTTP.
- **Rate-Limit**: Bei Anfragen unter ~10 s Abstand kommt eine leere Antwort zurück. Die Integration throttled auf 11 s Mindestabstand.
- **Inbetriebnahmedatum (`/api/rest/0E00`)** liefert auf einigen Modellen (z. B. i-soft K) keinen plausiblen Unix-Timestamp. Die Integration verwirft Werte vor 2000 oder in der Zukunft → Sensor bleibt `unknown`.
- **Salzstand (`/api/rest/5600`)** sind 4 Bytes; nur die ersten 2 sind das Gewicht in g (Big-Endian). Die hinteren 2 Bytes sind reserviert oder modellabhängig (vermutlich Reichweite in Tagen — derzeit nicht ausgewertet).
- **Betriebszeit-Counter (`/api/rest/2500`)** liefert auf manchen Modellen Werte, die nicht zur tatsächlichen Nutzungsdauer passen — vermutlich werksinterne Test-Stunden vor Auslieferung. Die Integration zeigt das Format genau wie das Geräte-Display ("X Tage, Y h, Z min").
- **Schreib-Aktionen** (Regenerationsstart, Leckageschutz-Toggle, Urlaubsmodus) liefern keine Bestätigung des Schaltzustands über die API. Die Switches halten den letzten gewählten Zustand selbst.

## Unterstützte Modelle

Die Integration sollte mit allen Geräten funktionieren, die das Connectivity-Modul akzeptieren:

- JUDO i-soft / i-soft K / i-soft TGA
- JUDO i-soft Pro / i-soft Pro SAFE+ / i-soft K SAFE+
- JUDO Softwell P / S / K / KS / C

Getestet wurde aktuell mit **i-soft K** (Firmware V2023+).

Bei anderen Modellen kann das **Modell-Mapping** (Const-Datei `const.py: DEVICE_TYPES`) erweitert werden — Pull Requests willkommen.

## Mitwirken

Issues und Pull Requests sind willkommen. Beim Reverse-Engineering der API helfen folgende Quellen:

- [JUDO Connectivity-Modul Handbuch](https://judo.eu/app/downloads/files/de/8000000/manuals/1702929_202301.pdf)
- [iobroker.judoisoft (arteck)](https://github.com/arteck/iobroker.judoisoft) — Datenkonverter mit Register-Beschreibungen
- [iobroker Forum-Script (Bert)](https://forum.iobroker.net/topic/78777/) — von Judo bestätigte Formeln

## Lizenz

[MIT](LICENSE)
