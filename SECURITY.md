# Security Policy

## Supported versions

Only the latest release receives fixes.

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a vulnerability

Please do not open a public issue for security problems.

Report vulnerabilities privately through GitHub: open the repository's **Security** tab and choose **Report a vulnerability**. Include:

- A description of the issue and its impact
- Steps to reproduce
- The version, distribution and install method you used

You can expect an initial response within a week. Once a fix is available it will be released and the report credited unless you ask otherwise.

## Security model

backglow runs locally as your user. It does not open network ports or make network requests, and it stores no files.

- **Bus restriction.** backglow only opens i2c buses whose adapter belongs to a PCI display device (class `0x03`). It never touches SMBus or other system i2c buses, where writes could reach RAM SPD EEPROMs or other hardware.
- **Device checks.** Device nodes are opened with `O_NOFOLLOW` and `O_CLOEXEC` and must be i2c character devices.
- **Monitor check.** DDC/CI commands are only sent to a bus whose EDID identifies an AOC monitor and which answers the Light FX query.
- **Command allowlist.** Only the nine Light FX codes (`F8 E1 60` to `68`) can be written, and every value is checked against the maximum the monitor reports.
- **Serialised access.** A lock in `$XDG_RUNTIME_DIR` stops the app and the CLI interleaving bus traffic.
- **UI isolation.** The interface is a local page inlined at launch under a strict Content Security Policy. Only the bundled script runs (by SHA-256 hash), and network, frames, workers and remote content are blocked. `unsafe-eval` is permitted because pywebview's JavaScript bridge requires it.
- **Minimal bridge.** Only the methods the UI needs are exposed to JavaScript, and each validates its arguments.

## udev rule

The bundled rule grants the active local session (`uaccess`) access to i2c buses under display adapters only:

```
SUBSYSTEM=="i2c-dev", KERNEL=="i2c-[0-9]*", SUBSYSTEMS=="pci", ATTRS{class}=="0x03*", TAG+="uaccess"
```

If your system does not support `uaccess`, prefer an owner-only rule over a world-writable one:

```
SUBSYSTEM=="i2c-dev", KERNEL=="i2c-[0-9]*", SUBSYSTEMS=="pci", ATTRS{class}=="0x03*", OWNER="youruser", MODE="0600"
```

Access to a monitor's DDC bus lets a user change any monitor setting, including input, brightness and factory functions. Do not grant it to accounts you do not trust.

## Scope

Areas of interest include:

- The udev rule and bus permissions
- Bus discovery and the display adapter check
- The bridge between the web UI and Python (`backglow/app.py`)
