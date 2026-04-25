# Judo Wasseraufbereitung — Home Assistant Integration

Custom component für Judo Connectivity-Module (i-soft, Softwell, i-soft Pro u.a.) über die lokale REST-API.

## Features

- **Lokale Polling-Integration** (kein Cloud-Account)
- DataUpdateCoordinator mit Throttling (~11 s zwischen API-Calls — die Firmware rate-limitet)
- Sensoren: Wunschwasserhärte, Salzvorrat, Gesamt-/Weichwassermenge, Betriebstage, Tagesverbrauch, Inbetriebnahmedatum
- Binary-Sensor: Verbunden/Verbindung verloren
- Button: Regeneration manuell starten
- Switches: Leckageschutz, Urlaubsmodus
- Übersetzungen Deutsch + Englisch
- Reconfigure-Flow für IP-Wechsel

## Installation

### HACS

1. HACS → Integrationen → drei Punkte oben rechts → *Eigene Repositories*
2. `https://github.com/mbraig/ha-judo-isoft` als Typ *Integration* hinzufügen
3. *Judo Wasseraufbereitung* installieren
4. Home Assistant neu starten
5. *Einstellungen → Geräte & Dienste → Integration hinzufügen → Judo*

### Manuell

1. Inhalt von `custom_components/judo/` nach `<config>/custom_components/judo/` kopieren
2. Home Assistant neu starten
3. Integration über UI hinzufügen

## Voraussetzungen

- Judo Connectivity-Modul (Art.-Nr. 2202271) im LAN/WLAN
- Standardpasswort `Connectivity` oder eigenes Passwort
- Firmware ab V2023 (HTTP-API)

## Bekannte Eigenheiten der Firmware

- Reagiert nur auf HTTP, HTTPS leitet auf HTTP-Root um
- Rate-Limit: ca. 10 s Pause zwischen API-Aufrufen, sonst kommen leere Antworten
- Web-UI und API teilen sich denselben Auth-Cache
- **Betriebszeit-Counter (`/api/rest/2500`)** liefert oft Werte, die nicht zur tatsächlichen Nutzungsdauer passen — vermutlich Werks-Vortest-Stunden oder ein anderer interner Zähler. Die Integration zeigt genau, was das Gerät meldet (Format "Tage, h, min"); Diskrepanz zur Realität bitte mit dem Geräte-Display vergleichen.
- **Inbetriebnahmedatum (`/api/rest/0E00`)** liefert auf einigen Modellen (z.B. i-soft K) keinen sinnvollen Unix-Timestamp. Werte vor 2000 oder in der Zukunft werden verworfen → Sensor bleibt `unknown`.
- **Salzstand (`/api/rest/5600`)** sind 4 Bytes, davon nur die ersten 2 das Gewicht in g (Big-Endian). Die hinteren 2 Bytes sind reserviert oder modellabhängig (Reichweite in Tagen?).

## Lizenz

[MIT](LICENSE)
