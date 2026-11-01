<img src="custom_components/gbs_control/brand/icon.png" width="96" align="right" alt="GBS Control logo">

# GBS Control — Home Assistant integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Test](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/test.yml/badge.svg)](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/test.yml)
[![Lint](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/lint.yml/badge.svg)](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/lint.yml)
[![Validate](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/validate.yml/badge.svg)](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/validate.yml)

Control and monitor a [GBS Control](https://github.com/ramapcsx2/gbs-control) video
upscaler (GBS-8200 / GBS-8220 running the ESP firmware) from Home Assistant.

State is read live from the device WebSocket and commands are sent over HTTP — no
cloud, fully local. Everything below was verified against the gbs-control firmware
source and a live device (see *How it works*).

## Installation (HACS)

[![Open your Home Assistant instance and open this repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=hudsonbrendon&repository=ha-gbs-control&category=integration)

1. Add this repository as a custom repository in HACS (category: Integration) — or use the button above.
2. Install **GBS Control** and restart Home Assistant.
3. The device is usually **auto-discovered** (mDNS `gbscontrol.local`). Otherwise:
   Settings → Devices & Services → Add Integration → **GBS Control**.
4. Enter the host (default `gbscontrol.local`, or the IP, e.g. `192.168.31.251`).

You can later change the host without removing the integration via **Configure** (reconfigure flow).

<!-- Optional: add a short screen recording of the HACS install at assets/install.gif and uncomment:
![Installing GBS Control via HACS](assets/install.gif)
-->

## Entities

### Sensors

| Entity | Platform | Description |
|--------|----------|-------------|
| Output preset | `sensor` | Loaded output preset (1280x960 … Pass-through / Custom); attributes carry the real resolution of a custom preset |
| Input format | `sensor` | Detected source: NTSC 480i, PAL 576i, 480p/576p, 720p, 1080i/p, VGA, RGBHV … |
| Active slot | `sensor` | Currently active preset slot |
| Source field rate / Output frame rate | `sensor` | Hz, printed by the firmware when frame-time lock runs |
| Brightness, Contrast, Pb/U gain, Pr/V gain, ADC gain, Scanline strength | `sensor` | Register values, updated whenever the device prints them (seeded at connect) |
| Frame-time-lock method, Wi-Fi network, IP address | `sensor` (diagnostic) | Device settings read from the firmware output and `/wifi/status` |
| Signal | `binary_sensor` | Whether a video source is detected |
| Connectivity | `binary_sensor` | Whether the device WebSocket is connected (stays available when offline) |

### Switches

Each maps to a device option. Commands are **toggles**, so a switch only sends a command
when the requested state differs from the reported state (and does nothing while the state
is still unknown).

| Switch | Switch | Switch |
|--------|--------|--------|
| Scanlines | Line filter | Peaking |
| Auto gain | Frame time lock | Force PAL to 60Hz |
| 6-tap filter | Full height | Component output |
| Match preset to source | Motion-adaptive deinterlace | ADC calibration |
| Scaling RGBHV | External clock disabled | Step response |

### Selects

| Entity | Options |
|--------|---------|
| Output resolution | 1280x960 · 1280x720 · 720x480/768x576 · 1280x1024 · 1920x1080 · Downscale · Pass-through |
| Preset slot | Your device's saved slot names (read from the device); switches the active slot |

> The output-resolution select reads back from the device status frame (and from the
> firmware's "preset applied" message for custom presets). The preset-slot select only
> appears when the device has named slots; its names are read at setup (use the
> `gbs_control.refresh` action after editing slots).

### Buttons

Every momentary command of the web UI is a button. Picture and geometry buttons are
enabled by default; developer-tab toggles without readback are disabled by default
(enable them from the entity settings).

| Group | Buttons |
|-------|---------|
| System | Reboot · Restore defaults · Save/Load custom preset · Restore filters · Print options · Reconnect Wi-Fi · Enable OTA updates |
| Picture | Brightness ± · Contrast ± · Pb/U gain ± · Pr/V gain ± · Reset colour defaults · Print colour registers · ADC gain ± · Cycle scanline strength · Cycle SDRAM clock · Cycle frame-time-lock method |
| Geometry | Shift picture left/right/up/down · Scale horizontal ± · Scale vertical ± · Horizontal/Vertical mask ± · Memory shift · HSync shift |
| Sync / developer | HTotal ± · Resync HTotal · Snap to 60/50Hz · Reset sync processor · Reset chip · Cycle oversampling · Invert sync · PLL divider · SOG level · Print video timings · Toggle freeze capture / ADC filter / IF auto offset / debug view / sync watcher |

## Services

The firmware has more single-character commands than there are entities. These services
expose the rest. All target a device via `device_id`.

### `gbs_control.send_command`

Send any raw command. `path` is `uc` (user/web command) or `sc` (low-level serial); the
`command` is a single character.

```yaml
action: gbs_control.send_command
data:
  device_id: <your GBS Control device>
  command: "7"   # toggle scanlines
  path: uc
```

### `gbs_control.refresh`

Reloads the saved slots and asks the device to print its options and colour registers
(re-seeds the readback sensors). Takes only `device_id`.

### `gbs_control.set_slot` / `save_slot` / `remove_slot`

Work with the device's preset slots.

```yaml
# Switch to a saved slot (slot id is a single character, as used by the device)
action: gbs_control.set_slot
data:
  device_id: <your GBS Control device>
  slot: "0"
---
# Save the current settings to a slot
action: gbs_control.save_slot
data:
  device_id: <your GBS Control device>
  index: 0
  name: "SNES 720p"
---
# Remove the currently active slot
action: gbs_control.remove_slot
data:
  device_id: <your GBS Control device>
```

## Languages

UI text (config flow, services, entity names) is translated to:
**English (en)**, **Español (es)**, **Português - Brasil (pt-BR)**, **Deutsch (de)**,
**Français (fr)**, **Italiano (it)** and **Nederlands (nl)**.

## How it works

The device has almost no JSON API. State comes from two things pushed on the device
WebSocket (port 81): a 6-byte status frame about once a second (preset, slot, option
flags) and the firmware's serial output, which is mirrored to the WebSocket one fragment
per `print()` call. The integration reassembles those fragments into lines and parses the
ones it knows (`preset applied: …`, `Format change: …`, `no signal`, `source Hz: …`,
`Brightness++ : …`, the option/colour-register dumps, …). Commands are HTTP GET requests
(`/uc?<char>`, `/sc?<char>`, `/slot/*`) on port 80; `/wifi/status` and `/spiffs/dir` are the
only JSON endpoints. The integration keeps a single persistent WebSocket connection and
reconnects automatically (the ESP8266 drops *all* clients when its free heap drops below
20 KB).

## Caveats

- The ESP8266 prefers a single WebSocket client; keep one Home Assistant instance connected.
- The brand icon renders on **Home Assistant 2026.3+** (local custom-integration brands);
  older versions show a generic icon.
- The firmware's "Print Info" developer stream (`/sc?i`) is deliberately not exposed: it
  floods the WebSocket until the ESP8266 runs out of heap and disconnects every client.
- Brightness/contrast/gain sensors only update when the device prints them (step buttons,
  "Print colour registers", or at connect), not continuously.

## Credits

- Firmware and logo: the [GBS Control project](https://github.com/ramapcsx2/gbs-control) by ramapcsx2.
- This is an unofficial, community-maintained Home Assistant integration.
