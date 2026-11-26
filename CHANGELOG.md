# Changelog

## Unreleased

- Complete fresh-install VM validation from base Debian 13 to a fully functional
  Cinnamon desktop, confirmed and accepted by the user on 2026-11-26.

- Match the lock-screen clock to the login/panel 12-hour time with AM/PM; verify
  both the shared clock preference and the separate lock-screen format.
- Keep Cinnamon's native account label above the lock-screen password box:
  preserve the full name, or initialize an empty account display name to the
  username so AccountsService cannot blank the label. This also matches login.
- Center native clock/date text and align the account name over the password
  field alone; guard package-layout changes and reapply after APT transactions.

- Offer a separately consented, GPU-validated native Debian proprietary NVIDIA
  fallback for older cards unsupported by the preferred open module.

- Restore normal adduser password and Full Name prompts for newly created accounts.
- Detect physical graphics adapters and offer native Intel/AMD firmware/Mesa or
  the authenticated NVIDIA open-module stack, with supported-GPU and Secure Boot checks.

- Own the native graphical-session lifecycle from LightDM around Debian Xsession;
  stop portal backends before X teardown and bind the Mint XApp unit to the session.
- Verify graphical-session activity and failed system/user units, which were not
  covered by the original accent-color-only portal check.

- Repair existing Gear Lever-generated Notepadqq menu suffixes, preserving launcher
  commands, icons, desktop actions and update configuration with an original backup.

- Fixed first-login Notepadqq discovery when Gear Lever adds a version/hash suffix
  to its display name; reruns reuse the installed AppImage and configure updates.

- Initial Debian 13 Cinnamon X11 provisioning implementation and staged lifecycle.
- Strict NetworkManager translation with reboot-boundary commit/recovery.
- Narrow Mint repository policy, actual APT candidate/solver tests and security audit.
- Preserved reference appearance, icon utility, optional Windows asset workflows.
- Official application repositories, native Gear Lever integration, latest initial
  Notepadqq release and main-default Nemo Grid Compensator integration.
- Windows exporter quick start, optional input directory and fresh-install checklist.

Clean-install acceptance and initial public release remain pending.
