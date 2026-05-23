# GBS Control — Home Assistant integration

Control and monitor a [GBS Control](https://github.com/ramapcsx2/gbs-control) video
upscaler (GBS-8200 / GBS-8220 with the ESP firmware) from Home Assistant.

## What you get

- **Sensors:** output preset, active slot (live, pushed over the device WebSocket).
- **Switches:** scanlines, line filter, peaking, auto gain, frame time lock, force PAL→60Hz,
  6-tap filter, full height, component output, match preset to source, motion-adaptive
  deinterlace, ADC calibration, scaling RGBHV, external clock disabled.
- **Select:** output resolution (1280x960, 1280x720, 720x480/768x576, 1280x1024, 1920x1080, Downscale).
- **Buttons:** reboot, restore defaults, save custom preset, load custom preset, restore filters.

## How it works

The device has no JSON API. State is read from a 6-byte status frame pushed on the
device WebSocket (port 81). Commands are HTTP GET requests (`/uc?<char>`, `/sc?<char>`)
on port 80. Because the device commands are toggles, switches only send a command when
the requested state differs from the reported state.

## Installation (HACS)

1. Add this repository as a custom repository in HACS (category: Integration).
2. Install "GBS Control" and restart Home Assistant.
3. Settings → Devices & Services → Add Integration → GBS Control.
4. Enter the host (default `gbscontrol.local`, or the IP, e.g. `192.168.31.251`).

## Caveats

- The ESP8266 prefers a single WebSocket client; keep one HA instance connected.
- The output-resolution select is write-mostly; its shown value reflects the last
  selection made from Home Assistant, not a device readback.
