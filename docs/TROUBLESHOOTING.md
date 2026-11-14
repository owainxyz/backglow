# Troubleshooting

## The app says "No monitor"

- Check DDC/CI is enabled in the monitor's on-screen menu.
- Check `i2c-dev` is loaded: `ls /dev/i2c-*` should list devices. If not, run `sudo modprobe i2c-dev`.
- Some docks, KVMs and adapters do not pass DDC/CI through. Connect the monitor directly to the GPU.
- `ddcutil detect` should list the monitor. If it does not, backglow cannot reach it either.

## The app says "No access"

Your user cannot open the GPU's i2c devices. Install the udev rule:

```sh
sudo cp 60-backglow.rules /etc/udev/rules.d/
sudo udevadm control --reload
sudo udevadm trigger
```

On NixOS, use the module from the flake, or add the rule to `services.udev.extraRules`.

The rule uses `TAG+="uaccess"`, which grants access to the user of the active local session. If you log in without a session manager that registers seats (for example a bare TTY login starting a compositor), replace `TAG+="uaccess"` with `OWNER="youruser", MODE="0600"`. Avoid `MODE="0666"`.

## The app says "No reply"

The monitor did not answer. Close other DDC tools (ddcutil, monitor control apps) and try again. Waking the monitor from standby can also help.

## A colour does not change

Some effects ignore some colours. On the AG276QKD2 the secondary colour cannot be set while the effect is Static. Pick the custom pattern before setting a custom colour; backglow does this for you.

## White looks blue or green

The LEDs are not colour calibrated. backglow applies a white balance correction tuned on an AG276QKD2. If yours looks different, open a monitor report with what you see.

## The window is blank

pywebview needs WebKitGTK 4.1. Install it from your distribution (`webkit2gtk4.1`, `libwebkit2gtk-4.1-0` or similar). On systems with GPU driver issues, try:

```sh
WEBKIT_DISABLE_DMABUF_RENDERER=1 backglow
```
