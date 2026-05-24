<img src="custom_components/gbs_control/brand/icon.png" width="96" align="right" alt="GBS Control logo">

# GBS Control — Home Assistant integration

[![HACS Custom](https://img.shields.io/badge/HACS-Custom-41BDF5.svg)](https://github.com/hacs/integration)
[![Test](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/test.yml/badge.svg)](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/test.yml)
[![Lint](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/lint.yml/badge.svg)](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/lint.yml)
[![Validate](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/validate.yml/badge.svg)](https://github.com/hudsonbrendon/ha-gbs-control/actions/workflows/validate.yml)

Control and monitor a [GBS Control](https://github.com/ramapcsx2/gbs-control) video
upscaler (GBS-8200 / GBS-8220 running the ESP firmware) from Home Assistant.

State is read live from the device WebSocket and commands are sent over HTTP — no
cloud, fully local.

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
| Output preset | `sensor` | Current output preset / resolution indicator |
| Active slot | `sensor` | Currently active preset slot |
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
| Scaling RGBHV | External clock disabled | |

### Select

| Entity | Options |
|--------|---------|
| Output resolution | 1280x960 · 1280x720 · 720x480/768x576 · 1280x1024 · 1920x1080 · Downscale |

> The output-resolution select is write-mostly: its shown value reflects the last selection
> made from Home Assistant, not a device readback.

### Buttons

| Button | Button |
|--------|--------|
| Reboot | Restore defaults |
| Save custom preset | Load custom preset |
| Restore filters | Cycle scanline strength |
| Cycle SDRAM clock | Cycle frame-time-lock method |
| Vertical mask increase | Vertical mask decrease |

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

The device has no JSON API. State is read from a 6-byte status frame pushed on the device
WebSocket (port 81); commands are HTTP GET requests (`/uc?<char>`, `/sc?<char>`, `/slot/*`)
on port 80. The integration keeps a single persistent WebSocket connection and reconnects
automatically (the ESP8266 drops clients when its heap runs low).

## Caveats

- The ESP8266 prefers a single WebSocket client; keep one Home Assistant instance connected.
- The brand icon renders on **Home Assistant 2026.3+** (local custom-integration brands);
  older versions show a generic icon.
- The output-resolution select is write-mostly (see above).

## Credits

- Firmware and logo: the [GBS Control project](https://github.com/ramapcsx2/gbs-control) by ramapcsx2.
- This is an unofficial, community-maintained Home Assistant integration.
