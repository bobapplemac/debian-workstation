# Validation record

## Fresh-install VM acceptance complete — 2026-11-26

The user rebuilt the test VM from a base Debian 13 amd64 installation, ran the
installer through to a fully functional Cinnamon X11 desktop, and explicitly
accepted end-to-end VM validation as complete. The accepted implementation
includes e134a31's native lock-screen fixes; 89378a6 changed only the README,
and 3c39b2c recorded the acceptance status.

Earlier fresh-VM feedback verified system provisioning, the planned reboot,
graphical first-login continuation, Notepadqq discovery/menu repair, desktop
behavior and portal lifecycle. The final rebuilt-VM confirmation accepts the
integrated workflow, rather than only rerunning modules on the development desktop.

## Evidence

| Area | Recorded result |
| --- | --- |
| Base Debian to configured desktop | Completed and accepted by the user on a rebuilt VMware VM |
| First-login continuation | Completed successfully; unchanged subsequent logins do not repeat setup |
| Portal lifecycle | Reboot and two logout/login cycles verified native target/service behavior; no failed user services; real Flatpak file chooser worked |
| Notepadqq | Plain menu name, retained AppImage/update configuration and successful launch confirmed |
| Native lock screen | AM/PM time, centered time/date and account name centered over the field alone visually confirmed; native unlock/settings retained |
| Production lock-screen helper | Pristine Debian 6.4.0-1 sources transformed into byte-identical accepted files; root reapplication left contents unchanged |
| Appearance and assets | Native artwork/glyph checks and verifier passed; earlier supplied-cursor run verified 3,072 native XCursor loads |
| Networking | Fresh-VM migrated Ethernet connection and DNS worked after reboot |
| Package policy | Isolated libapt candidate/security-fallback tests and removal checks passed |
| NVIDIA metadata/dependencies | Signed repository/package manifests support the tested open RTX 5060 Ti and Debian proprietary GTX 1080 fixtures; no physical driver installation claimed |

The native Cinnamon lock screen is the accepted implementation. Alternate-locker
experiments were discarded and are not included in the installer.

## Automated checks

The 2026-11-26 repository audit passed all 61 tests under Debian 13 WSL, with
the opt-in isolated systemd fixture and offline NetworkManager checks enabled;
none were skipped. NetworkManager test dependencies were extracted locally
without installing or starting a networking service. ShellCheck and Bash/Python
syntax checks passed. Relative documentation links and example configuration
defaults were also checked.

Coverage includes lock-screen layout drift rejection, idempotence, source
preservation and warning behavior that lets package upgrades finish. New
continuation tests confirm that library/entry-point changes repeat setup while
generated Python bytecode does not.

## Separate scenario/hardware validation

Physical NVIDIA/Intel/AMD driver installation and display boot, Secure Boot
enrollment, other hypervisors, multi-monitor/HiDPI and additional network profiles
are not established by the VMware acceptance. Wayland and existing desktop
conversion are outside the supported baseline. See [graphics](graphics.md),
[networking](networking.md), and [acceptance](acceptance.md).

Inspected dependency versions are dated observations, not package holds or a
claim that future upstream main/latest inputs have already been tested. No
versioned release tag was created by the validation record.

## Historical observations

Earlier checkpoint notes, including the original failures and intermediate
pending statuses, are preserved in the repository's
[historical validation notes](https://github.com/bobapplemac/debian-workstation/blob/main/docs/history/validation-notes.md)
and [development record](https://github.com/bobapplemac/debian-workstation/blob/main/docs/history/development-record.md).
Historical archives are excluded from the installed offline documentation.
