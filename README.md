# Debian Workstation

Turn a minimal Debian 13 installation into a curated Cinnamon workstation:
Mint-Y Blue appearance, consistent window controls, familiar shortcuts and panel
behavior, balanced Nemo desktop icons, and native software management.

This provisions Debian; it does not create a distribution or installation ISO.
**Fresh-install VM validation complete.** The full workflow has been tested from
a base Debian 13 installation to a fully functional Cinnamon desktop. See the
[validation record](docs/validation.md) for scope and results.

## Quick start

Optional, on your licensed Windows PC, run these in **PowerShell** to export
cursor artwork and supplemental fonts. They execute the scripts directly from
this repository's `main` branch; no clone or release is needed:

```powershell
irm https://raw.githubusercontent.com/bobapplemac/debian-workstation/main/scripts/windows/Export-Windows-Cursors.ps1 | iex
irm https://raw.githubusercontent.com/bobapplemac/debian-workstation/main/scripts/windows/Export-Windows-Fonts.ps1 | iex
```

The outputs are `Windows-Cursors.zip` and `Windows-Fonts.zip` in your Windows
Downloads folder. Copy them into this repository's **`input/`** folder on Debian
before installing. Both are optional: missing files produce warnings, retain
native cursor/font support, and skip only the corresponding customizations.
Do not commit or redistribute these ZIPs or generated proprietary artwork.
Review the scripts first if preferred: open the linked raw URLs before running.

On a fresh **Debian 13 Trixie amd64** system, use a checkout or extracted source
archive (Git is optional):

```bash
cd debian-workstation
bash install.sh
```

Run as your regular user: the installer checks sudo access and uses that account.
Run as root: it asks for a regular workstation username and guides creation of a
new account and password. An existing regular account can also be selected.
New accounts use Debian's normal `adduser` questions, including Full Name, which
provides the login-screen display name. To add/correct it on an existing account,
run `sudo chfn "$USER"` as that regular user.
Root can use `--user USER` to select the account explicitly. Passwords are entered
through the terminal and never stored in project configuration.

Alternatively, from a console/SSH session with Bash, Python 3, CA certificates
and wget already installed:

```bash
wget -qO- https://raw.githubusercontent.com/bobapplemac/debian-workstation/main/install.sh | bash
```

For this remote method, optional archives are found in **`./input/` beneath the
directory you run the command from**. Use `--input-dir /absolute/path` to choose
another folder. A failed initial download can yield an empty successful Bash
pipeline: look for the installer's explicit completion message.

The installer downloads one resolved repository commit, validates its archive,
and runs the same implementation as the local method. No published release is
required. The `main` URLs serve the latest published commit; local uncommitted
changes are not included.

**Reboot when the system phase finishes**, then sign in normally to Cinnamon
using X11. A terminal opens to finish session-dependent configuration. Allow Gear
Lever's native background permission request when shown. The terminal displays
success or the error and continuation command. Reopen applications and log out
and back in once to reload libraries and panel styling. Nothing enables autologin
or forcibly restarts LightDM or Cinnamon.

## What is installed

- Debian's Cinnamon task with the R&D profile's explicit mail, office, chat and
  torrent exclusions; Firefox ESR and the remaining native task applications.
- Mint-Y-Blue GTK/icons, Mint-Y-Dark-Blue shell, original application artwork,
  tested GTK3/GTK4 window controls and symbolic glyphs.
- Adwaita/Papirus LightDM GTK greeter with Debian's default wallpaper.
- Native Cinnamon lock screen with 12-hour time, centered time/date and the full
  name (username fallback) centered above the password field. See [lock-screen setup](docs/lock-screen.md).
- Desktop Computer/Home/Trash/volume icons, manual modern grid through
  [Nemo Grid Compensator](https://github.com/bobapplemac/nemo-grid-compensator),
  Win+L, Ctrl+Shift+Esc, individual titled taskbar buttons, two-line US clock,
  dark GNOME Terminal colors.
- NetworkManager migration staged at reboot; VMware/KVM/Hyper-V guest integration
  selected automatically where supported.
- Physical GPU detection and optional native Intel/AMD firmware/Mesa or NVIDIA
  open kernel modules, with a separately consented compatible Debian proprietary
  fallback for older cards. See [graphics setup](docs/graphics.md),
  including the RTX 5060 Ti and Secure Boot prerequisites.
- GNOME Software, system Flathub and Gear Lever, update checks and notifications
  with manual application update installation.
- Optional latest stable Notepadqq AppImage, official 1Password desktop/CLI,
  Microsoft Core Fonts and user-supplied supplemental fonts/cursors.

Nemo Grid Compensator follows **`main` by default**, as requested. It is installed
through its own installer and initialization mechanism; its MIT-licensed source
is not copied into this repository. Its current supported layout is one monitor,
100% scaling, top-left work area, modern grid and Normal icon size.

## Baseline and prerequisites

The preferred starting point is
[debian-netinst-customizer](https://github.com/bobapplemac/debian-netinst-customizer).
It supplies a root-only console installation, ifupdown networking, Debian package
and security sources, sudo, SSH, Chrony, and basic guest tools. It explicitly
selects no unattended update policy. Workstation setup creates the desktop user
when needed and adds desktop features without redesigning that base.

Use a fresh Debian 13 amd64 installation. The console-to-Cinnamon X11 workflow
is validated on VMware. Wayland, other
desktops/distributions/architectures and arbitrary existing network configurations
are unsupported. Physical hardware and other hypervisors are not yet acceptance
validated. Internet access is required. If using a conventional minimal Debian
system, install `bash python3 ca-certificates curl wget sudo` first as root, provide
working Debian Trixie/security sources (including contrib for Core Fonts), and
grant your regular account sudo access before running as that account.

## Configuration and reruns

Copy `config.example.conf` to ignored `config.local.conf`, edit it, then run:

```bash
bash install.sh --config config.local.conf
bash install.sh --module desktop
bash /usr/local/lib/debian-workstation/install.sh --phase session \
  --config /usr/local/lib/debian-workstation/session.conf
```

Configuration is strict `KEY=value` data, with no quoting or shell expansion.
Options cover account creation, passwordless sudo (off by default), guest type,
`GRAPHICS_DRIVERS=ask|yes|no` (default ask),
`NVIDIA_LEGACY=ask|yes|no` (separate consent for a compatible older Debian driver),
Notepadqq, 1Password desktop/CLI, Core Fonts, optional archive paths, and
`NEMO_REF` (default `main`, or an explicit revision). `--module` accepts `base`,
`network`, `repositories`, `desktop`, `graphics`, `assets`, `applications`, or `all`.
System modules require their normal prerequisites; rerunning a module is intended
after an initial full installation. Reruns reapply the selected desktop defaults,
including native GSettings preferences. Unrelated settings are retained; edited
generated user assets stop with diagnostics rather than being discarded. Existing
KDE/other-desktop conversions are outside the supported fresh-install workflow.

Debian packages, signed external APT packages and Flatpaks receive ordinary
upstream updates. Notepadqq installs the latest stable release initially, verifies
GitHub's asset SHA256, and then uses Gear Lever for manual updates. Observed
release URL/digest pairs are retained to detect changed release artifacts.
The cursor converter remains pinned to the tested 1.6.0 artifact and checksum.
Changing `NEMO_REF` to a commit and installing workstation with `--ref COMMIT`
pins those source inputs; it does not freeze Debian or Flathub repositories.

## Inspect before execution

Download a full source archive from the repository's GitHub Code menu, inspect
the source, extract it, and run `bash install.sh` locally. To inspect only the
bootstrap first:

```bash
work=$(mktemp -d)
curl -fsSL https://raw.githubusercontent.com/bobapplemac/debian-workstation/main/install.sh -o "$work/install.sh"
less "$work/install.sh"
bash "$work/install.sh" --ref main
rm -r -- "$work"
```

Inspecting the bootstrap does not review code in the subsequently downloaded
archive. For a fixed revision, replace `main` in both the URL and `--ref` with
the same full commit. Downloaded temporary source is cleaned on normal exit,
errors and handled signals; persistent continuation lives under
`/usr/local/lib/debian-workstation`, not the temporary directory.

## Security and recovery

Read [the LMDE security policy](docs/security-policy.md) and
[network migration/recovery](docs/networking.md) before applying to a real machine.
The [session lifecycle notes](docs/session-lifecycle.md) explain native portal
shutdown and the one reboot needed when adding the repair to an existing install.
The Mint repository has an exact package allowlist. Debian security libadwaita
packages take precedence even when their versions sort lower than Mint's;
this can reduce accent integration and can require an explicit reviewed
downgrade. Package-inventory changes produce a review notice at graphical login.
There is no claim that Mint patch security equivalence can be inferred from
Debian advisory/version metadata. Existing unattended update mechanisms are kept.

Failed session setup: inspect `~/.local/state/debian-workstation/session.log`,
correct the error, then run:

```bash
bash /usr/local/lib/debian-workstation/scripts/first-login.sh --terminal
```

No reset/reinstall of the whole desktop is required. See
[acceptance procedure](docs/acceptance.md), [implementation decisions](docs/architecture.md),
[dependency inventory](docs/dependencies.md), [validation results](docs/validation.md),
and [development record](docs/progress.md).
Run `bash scripts/verify.sh` in the desktop session after installation.

The [screenshots directory](docs/screenshots/README.md) describes the real captures
to collect. VM acceptance is complete; sanitized screenshots are not yet committed.

## License

Project implementation: [0BSD](LICENSE), Copyright (c) 2026 Andrew J. Moore.
External software and optional proprietary artwork retain their own licenses;
see [third-party notices](docs/third-party-notices.md).
