# AGENTS.md

Guidance for coding agents working in this repository.

## Overview

backglow is a Linux app that controls the Light FX rear lighting on AOC AGON monitors over DDC/CI. Python talks to the monitor through `/dev/i2c-*` and exposes an API to a web UI rendered by pywebview (WebKitGTK).

## Layout

- `backglow/monitor.py`: protocol and device access. `displayBus`, `buses`, `find`, `read`, `write`, `setColour`, `transact`, `busLock`.
- `backglow/app.py`: `Api` class (public methods are callable from JS as `window.pywebview.api.*`), background writer thread, `gui`, `cli`, `main`.
- `backglow/web/`: `index.html`, `style.css`, `app.js`. These are inlined into one HTML string at launch by `page()` in `app.py`.
- `flake.nix`: package (`packages.default`) and NixOS module (`nixosModules.default`).
- `60-backglow.rules`: udev rule.

## Build and run

```sh
nix build
./result/bin/backglow
./result/bin/backglow --status
```

Without a display, test the UI under Xvfb:

```sh
Xvfb :99 -screen 0 1060x720x24 &
DISPLAY=:99 GDK_BACKEND=x11 WEBKIT_DISABLE_DMABUF_RENDERER=1 LIBGL_ALWAYS_SOFTWARE=1 ./result/bin/backglow
```

Unset `WAYLAND_DISPLAY` when doing this so the window does not open on a real desktop.

## Conventions

- camelCase names in Python and JavaScript
- No comments or docstrings
- UI copy is minimal: labels and one or two word statuses
- UI is monochrome (black and greys), dark only; no coloured accents or status dots
- Keep the CLI working without the GUI dependencies being imported

## Protocol rules

Read [`docs/PROTOCOL.md`](docs/PROTOCOL.md) before touching `monitor.py`.

- Only send codes on page `F8 E1` in the range `60` to `68`. Never add writes to other VCP codes, factory reset codes, or anything that was not observed on hardware.
- Validate every value against the maximum the monitor reports before writing.
- Keep at least 80 ms between writes; faster writes are silently dropped.
- Writes go through the `Api` writer thread, which coalesces to the latest value per field. Do not block the JS bridge on i2c.

## Device access rules

- Only open i2c buses that `displayBus()` accepts: the adapter must sit under a PCI display-class device (`0x03xxxx`). Never probe SMBus or other i2c buses; writing to address `0x50` on SMBus can reach RAM SPD EEPROMs.
- Open device nodes with `O_NOFOLLOW` and `O_CLOEXEC`, and check they are i2c character devices (major 89).
- All bus traffic goes through `busLock()`, which serialises threads and processes.
- Only talk DDC/CI to a bus whose EDID vendor is `AOC` and which answers the Light FX effect query.

## UI to Python bridge

- Every public method on `Api` is callable from JavaScript. Prefix internal helpers with `_` and validate every argument.
- Colour values cross the bridge as `#rrggbb` strings only.
- Errors from the writer thread are pushed to `window.onWriteError`.

## Security rules

- Keep the Content Security Policy in `page()` strict. Do not add `unsafe-inline` to `script-src`, inline event handler attributes, or any network source.
- Render strings with `textContent`, never `innerHTML`.
- The app makes no network requests and opens no ports. Keep it that way.

## Before finishing a change

- `nix build` succeeds
- The app starts and every page renders with and without a monitor
- `backglow --status` works
- `CHANGELOG.md` is updated under **Unreleased** for user-facing changes
