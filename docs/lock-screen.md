# Native Cinnamon lock screen

The installer keeps Cinnamon's native screensaver, password authentication,
shortcuts and Settings controls. LightDM remains the login/user-switching greeter.
No alternate locker, authentication handoff, D-Bus adapter or visual-screensaver
daemon is installed.

Session setup selects 12-hour time with AM/PM through Cinnamon's own interface
and screensaver settings. These preferences remain editable in Cinnamon Settings.
The desktop module preserves a supplied full name. If the account's Full Name
field is empty, it initializes that display name to the username: otherwise
AccountsService can replace Cinnamon's native username fallback with a blank
label. The native label appears above the password field, not beneath the clock.
Changing the full name later through account settings updates the native display.

Two small presentation adaptations are applied to the installed package source:

- `clock.py`: center each line of the combined time/date label.
- `unlock.py`: offset the name label using the actual width of the adjacent
  button group so it centers over the password field alone. No fixed pixel
  offset is used, and the native entry, focus and authentication handlers remain.

`scripts/desktop/lock-screen.py` checks both native constructors before preparing
changes, preserves unrelated source, and recognizes already-applied changes.
`install-lock-screen.sh` installs them atomically using the shared file helper.
Original files are backed up once under
`/var/lib/debian-workstation/backups/usr/share/cinnamon-screensaver/`.
No running locker or display manager is stopped; a later locker process loads
the changes. Log out and back in after provisioning to reload presentation.

An APT `DPkg::Post-Invoke` hook reapplies the same guarded adaptations after
package transactions. It reads the newly installed package files rather than
keeping an old screensaver copy. If a future layout is unrecognized, the hook
warns and leaves the new package source in place; the package upgrade can finish.
The workstation verifier detects missing/changed adaptations for administrator
review. Direct `dpkg -i` transactions bypass APT hooks; rerun the desktop module
after those if necessary.

To remove only the source adaptations, remove the APT hook first, then reinstall
the package so the hook does not immediately reapply them:

```bash
sudo rm /etc/apt/apt.conf.d/99debian-workstation-lock-screen
sudo apt-get install --reinstall cinnamon-screensaver
```

This does not change the clock preferences or account display name; those remain
normal native settings. Rerunning workstation desktop provisioning reapplies its
defaults and presentation adaptations.

VM validation confirmed normal native locking/unlocking, AM/PM time, centered
time/date and the name centered over the entry alone. Offscreen allocation checks
covered short/full names, one/two buttons, and long/short date labels. Package
layout guards, idempotence and source preservation are covered by regression tests.
