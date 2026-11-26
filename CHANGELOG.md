# Changelog

## Unreleased

### Added

- Fresh Debian 13 amd64 provisioning from a minimal console system to a curated
  Cinnamon X11 desktop, with a system phase and visible first-login continuation.
- Mint-Y Blue appearance, native application artwork, familiar shortcuts,
  individual taskbar buttons, a two-line panel clock and a dark terminal profile.
- NetworkManager translation and staged reboot-boundary commit/recovery for the
  supported ifupdown Ethernet/VLAN configurations.
- Automatic VMware/KVM/Hyper-V guest integration selection and optional physical
  Intel/AMD firmware/Mesa or NVIDIA drivers. The open NVIDIA module is preferred;
  compatible older cards can receive a separately consented Debian proprietary driver.
- Native software management through GNOME Software, Flatpak/Flathub and Gear
  Lever; latest-stable initial Notepadqq installation and official 1Password repositories.
- Windows PowerShell exporters runnable directly from main, an optional input/
  directory for their ZIPs, and nonfatal missing-font/cursor fallback.
- Signed repository allowlists, security-fallback policy, dependency/driver
  compatibility checks, read-only verification and documented recovery procedures.

### Changed

- Root-driven setup uses Debian's normal account password/Full Name questions;
  regular-user setup validates sudo access and selects that workstation account.
- Nemo Grid Compensator follows main by default; Notepadqq selects the latest
  stable GitHub release initially. Optional source revisions remain configurable.
- Group related helpers under scripts/ subdirectories and name the artwork tool
  mint-y-app-icons.py.
- Keep Cinnamon's native locker/settings, use 12-hour lock-screen time with AM/PM,
  center time/date and center the full name above the password field alone.
  An empty Full Name receives a username display-name fallback.
- Guard native presentation adaptations against upstream layout changes, retain
  backups and reapply them after APT package transactions.

### Fixed

- Bind graphical-session services to the actual LightDM/Cinnamon session lifetime
  so portal backends stop before X teardown and restart cleanly after login.
- Discover Gear Lever's generated Notepadqq version/hash names and repair its
  menu label while preserving launcher commands, icons, actions and update configuration.
- Verify failed system/user services in addition to the portal's accent-color response.
- Include shared libraries and install.sh in first-login completion signatures;
  ignore generated Python bytecode so cache files do not repeat setup.

### Validation and documentation

- Complete end-to-end fresh-install VMware validation, accepted by the user on
  2026-11-26, from base Debian 13 to a fully functional Cinnamon desktop.
- Confirm native lock-screen presentation visually and reproduce the accepted
  changes from pristine package sources with the production helper.
- Separate current status from historical development notes, correct archive
  defaults and rerun guidance, and document the supported fresh-install scope.
- Keep physical GPU/Secure Boot and additional hardware/network scenario checks
  separate from the completed VMware baseline. No alternate-locker experiments
  are part of this implementation.
