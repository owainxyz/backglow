# Changelog

All notable changes to this project are documented here.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project follows [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-11-14

Initial public release.

### Added

- Light FX control for AOC AGON monitors over DDC/CI
- All effects the monitor reports, with the effect list chosen from the monitor's range
- Brightness: off, low, medium, strong
- Red, green, blue, rainbow and custom colour patterns, with presets and a secondary colour
- White balance correction for custom colours
- Colour wheel changes are sent once the wheel settles
- Writes run in the background and coalesce to the latest value
- `--status`, `--mode`, `--strength`, `--pattern`, `--colour` and `--colour2` command line options
- Monitor page with model, bus and access rule
- Nix flake, NixOS module (loads `i2c-dev`), udev rule and desktop entry

### Security

- Only i2c buses under PCI display adapters are opened; SMBus and other buses are never probed
- Device nodes are opened with `O_NOFOLLOW` and `O_CLOEXEC` and verified as i2c character devices
- DDC/CI is only sent to monitors whose EDID vendor is AOC and which answer the Light FX query
- Writes are limited to the Light FX codes and checked against the monitor's reported range
- Bus access is serialised across threads and processes
- Strict Content Security Policy for the UI; scripts allowed only by hash, no network access
- udev rule limited to display adapter i2c buses for the active session

[Unreleased]: https://github.com/owainxyz/backglow/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/owainxyz/backglow/releases/tag/v0.1.0
