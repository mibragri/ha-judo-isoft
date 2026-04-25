# JUDO Water Treatment — Home Assistant Integration

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
[![HACS Custom](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://hacs.xyz/)
[![Validate](https://github.com/mibragri/ha-judo-isoft/actions/workflows/validate.yml/badge.svg)](https://github.com/mibragri/ha-judo-isoft/actions/workflows/validate.yml)

Home Assistant custom component for **JUDO water softeners** (i-soft, i-soft K, i-soft Pro, Softwell, …) over the **JUDO Connectivity Module** (P/N 2202271).

> **100% local — no cloud account, no `myjudo.eu` login.** The integration talks directly to the connectivity module's REST API on your LAN/Wi-Fi.

## Features

| Area | Entities |
|---|---|
| **Consumption** | Total water (m³), Soft water (m³), Daily consumption (L) |
| **Plant** | Salt level (g), Salt range (days), Target water hardness (°dH), Operating time |
| **Status** | Connected / connection lost (binary sensor) |
| **Actions** | Start regeneration (button) |
| **Switches** | Leakage protection, Vacation mode |
| **Diagnostic** | Installation date, device info (type, serial, software version) |

UI translations: **English** and **German**.

## How it works

- A single **`DataUpdateCoordinator`** fetches every value once per cycle; entities read from a shared in-memory snapshot.
- **API throttling**: the connectivity module silently drops back-to-back requests. The integration serializes calls and enforces an **11 s minimum gap** between them.
- **HTTP only**: firmware V2023+ permanently redirects HTTPS to the HTTP root.
- **Plausibility filters** for fields that ship junk on some models (e.g. installation date on i-soft K).

## Requirements

- Home Assistant **2025.1** or newer
- JUDO Connectivity Module (P/N 2202271) on your home network, reachable over HTTP
- Initial Wi-Fi/LAN setup of the module already done via the JUDO app or web UI (see below)

## Installation

### Option A — HACS (recommended)

1. HACS → three-dot menu → **Custom repositories**
2. Repository: `https://github.com/mibragri/ha-judo-isoft`, category: **Integration**
3. Install *JUDO Water Treatment*
4. **Restart** Home Assistant
5. *Settings → Devices & services → Add integration → JUDO*

### Option B — manual

1. Copy `custom_components/judo/` to `<config>/custom_components/judo/`
2. Restart Home Assistant
3. Add the integration via the UI

## Configuration

| Field | Default | Description |
|---|---|---|
| **IP address / hostname** | – | The connectivity module's address on your LAN |
| **Username** | `admin` | API user on the module |
| **Password** | `Connectivity` | Default password — **change this on the module itself!** |

If the module's IP changes (DHCP rotation), use the integration's **Reconfigure** option — no need to delete and re-add.

## Connectivity module first-time setup

If the module is brand new and not yet on your network:

1. Power up the module (LAN cable optional)
2. From a phone or laptop, join the open Wi-Fi **`Judo Connectivity`** (the module's hotspot)
3. Browse to `http://192.168.4.1`
4. Log in: `admin` / `Connectivity`
5. *Settings → enable Wi-Fi* → enter your home SSID + password → save
6. Optionally enable the portal at `myjudo.eu:8585` (for the JU-Control mobile app)
7. Replace the default `Connectivity` password
8. Reboot the module — it will join your LAN and pick up a DHCP address

## Known firmware quirks (V2023+)

- **HTTPS redirects to HTTP root.** The integration uses HTTP directly.
- **Rate limit**: requests less than ~10 s apart return empty bodies. The integration enforces an 11 s gap.
- **Installation date** (`/api/rest/0E00`) returns junk on some models (e.g. i-soft K). Values outside `[2000, now+1d]` are discarded → sensor stays `unknown`.
- **Salt level** (`/api/rest/5600`) is 4 bytes total: bytes 0–1 are weight in grams (big-endian), bytes 2–3 are remaining range in days (little-endian).
- **Operating time** (`/api/rest/2500`) and **installation date** (`/api/rest/0E00`) are **firmware-build counters**, not user-installation counters. Verified empirically: `operating_time` in days exactly equals the calendar-day delta between today and `installation_date`. The Judo device counts from firmware compile date (e.g. 2017-05-13 for V4.01), regardless of when you actually unboxed and wired it up. Don't expect these values to reflect time since you installed the unit — for that you need to track the install date yourself.
- **Write actions** (regeneration, leakage protection toggle, vacation mode) don't return a confirmed switch state. The integration caches the last requested state locally.

## Supported models

The integration should work with any device that uses the JUDO Connectivity Module:

- JUDO i-soft / i-soft K / i-soft TGA
- JUDO i-soft Pro / i-soft Pro SAFE+ / i-soft K SAFE+
- JUDO Softwell P / S / K / KS / C

Currently tested with **i-soft K** (firmware V2023+).

For other models, extend the device-type mapping in `const.py: DEVICE_TYPES` — pull requests welcome.

## Related projects

- [OStrama/judo_rest_api](https://github.com/OStrama/judo_rest_api) — Another HA integration with the most thorough register reverse-engineering. We cross-referenced our register layout and device-type table against this project. Key differences in our integration: working daily-statistics sensor, vacation-mode switch, more permissive plausibility checks for installation date.
- [iobroker.judoisoft (arteck)](https://github.com/arteck/iobroker.judoisoft) — ioBroker adapter with detailed data converter and register documentation.
- [iobroker forum script (Bert)](https://forum.iobroker.net/topic/78777/) — Community script with formulas confirmed by JUDO support.

## Contributing

Issues and pull requests welcome. Useful sources for further register exploration:

- [JUDO Connectivity Module manual](https://judo.eu/app/downloads/files/de/8000000/manuals/1702929_202301.pdf)
- The repos above
- KNX-User-Forum thread on [JUDO i-soft](https://knx-user-forum.de/forum/projektforen/edomi/1453632-lbs19002090-judo-i-soft-wasserenth%C3%A4rtungsanlage)

## License

[MIT](LICENSE)
