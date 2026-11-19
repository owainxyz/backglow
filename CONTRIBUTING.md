# Contributing to backglow

Thanks for your interest in improving backglow. Bug reports, monitor reports, and pull requests are all welcome.

## Ways to contribute

- **Report a bug** using the bug report template. Include your distribution, monitor model, and steps to reproduce.
- **Report a monitor.** If you have another AOC AGON monitor with Light FX, open a monitor report with the output of `backglow --status` and the monitor's DDC/CI capabilities string.
- **Suggest a feature** using the feature request template.
- **Send a pull request** for fixes, features, or documentation.

## Development setup

### With Nix

```sh
git clone https://github.com/owainxyz/backglow
cd backglow
nix build
./result/bin/backglow
```

### Without Nix

Install WebKitGTK 4.1 and PyGObject from your distribution, then:

```sh
git clone https://github.com/owainxyz/backglow
cd backglow
python -m venv --system-site-packages .venv
. .venv/bin/activate
pip install -e .
backglow
```

`--system-site-packages` lets the virtual environment use your distribution's PyGObject.

You also need `i2c-dev` loaded and the udev rule from [`60-backglow.rules`](60-backglow.rules) installed, or the app will report **No access**.

### Testing the UI headless

To test the UI under Xvfb:

```sh
Xvfb :99 -screen 0 1060x720x24 &
DISPLAY=:99 GDK_BACKEND=x11 WEBKIT_DISABLE_DMABUF_RENDERER=1 LIBGL_ALWAYS_SOFTWARE=1 ./result/bin/backglow
```

Unset `WAYLAND_DISPLAY` when doing this so the window does not open on a real desktop.

## Project layout

| Path                   | Purpose                                              |
|------------------------|------------------------------------------------------|
| `backglow/monitor.py`  | DDC/CI protocol, bus discovery, device access        |
| `backglow/app.py`      | Python API exposed to the UI, CLI entry point        |
| `backglow/web/`        | UI: `index.html`, `style.css`, `app.js`              |
| `flake.nix`            | Nix package and NixOS module                         |
| `60-backglow.rules`    | udev rule for unprivileged access                    |
| `docs/`                | Protocol reference and troubleshooting               |

## Code style

- camelCase for functions and variables, in both Python and JavaScript
- Keep code self-explanatory; avoid comments and docstrings
- Four-space indentation in Python, two spaces in JavaScript, HTML, CSS and Nix (see [`.editorconfig`](.editorconfig))
- No new runtime dependencies without discussion
- UI text is short and functional: labels and one or two word status messages, no explanatory copy
- The UI is monochrome (black and greys); do not introduce accent colours
- Follow the rules in the [rules below](#device-access-rules): only display buses, only Light FX codes, validate bridge input

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

## Testing

There is no automated test suite yet. Before opening a pull request:

1. Run `nix build` (or `pip install -e .`) and make sure the app starts.
2. If you changed `monitor.py`, run `backglow --status`, change the effect and colour from the CLI, and confirm the LEDs follow.
3. If you changed the UI, check both pages with and without a monitor reachable.

Please say in the pull request which monitor you tested on.

## Protocol changes

The codes were worked out from AOC's G-Menu and confirmed on hardware. If you add or change one:

- Document it in [`docs/PROTOCOL.md`](docs/PROTOCOL.md)
- Describe how you verified it on a real monitor
- Never send codes you have not verified; monitors expose factory and service functions on the same pages

## Commits and pull requests

- Keep pull requests focused on one change
- Write commit messages in the imperative mood, e.g. `Add effect speed`
- Update `CHANGELOG.md` under **Unreleased** for user-facing changes
- Update the README if you change behaviour, options, or installation steps

## Code of conduct

This project follows the [Code of Conduct](CODE_OF_CONDUCT.md). By participating you agree to uphold it.
