# Cinnamon / LightDM portal lifecycle

## Observed failure and cause

On the first fresh Debian 13 Cinnamon X11 trial, the GTK portal worked during the
session, then entered failed state after logout. Opening a chooser later could
activate it again; that recovery did not prove that the next logout was correct.
The journal showed GTK portal, XApp portal and GNOME Terminal exiting with status
1 at the same logout boundary. The surviving portal frontend immediately tried to
activate XApp against the disappearing display, producing `Failed to initialize Gtk`.

Inspection on the actual VM established:

- GTK portal, portal frontend and GNOME Terminal already declare
  `PartOf=graphical-session.target` in their Debian units.
- `graphical-session.target` remained inactive during the active graphical login.
  Consequently its existing stop relationships could not cleanly shut these
  processes down before LightDM destroyed their X server.
- The installed Mint XApp backend unit did not declare that PartOf relationship.
- LightDM used Debian's `/etc/X11/Xsession` wrapper. Cinnamon did not provide an
  active systemd graphical-session lifecycle in this configuration.

The actionable root cause is missing graphical-session ownership/teardown, not
a chooser installation problem or a missing restart policy. No arbitrary status-1
exit is reclassified as success, and no periodic reset-failed/restart loop is added.

## Implementation

The desktop module installs a small executable LightDM session wrapper, a native
session target and a drop-in binding XApp to graphical-session.target. Distribution
binaries and unit files are not modified.

The wrapper runs as the authenticated regular user. It imports the display
environment into that user's existing D-Bus/systemd activation environment, then
starts `debian-workstation-cinnamon-session.target`. This target binds to the native
graphical-session.target, which refuses direct manual start and stops when unneeded.
The explicit session dependency is necessary to start and retain it correctly.

Debian's `/etc/X11/Xsession` still runs unchanged as the child, including its usual
environment, D-Bus and user hooks. When that child exits, the wrapper synchronously
stops both targets; the portal frontend and GTK/XApp backends stop via their native
PartOf relationships before the wrapper returns control to LightDM and X is torn
down. The session's exit status is retained. Session cancellation does not stop
the target because the session process has not exited. An already-active native
graphical target is left to its existing owner instead of being claimed/stopped.

The target is not enabled at user-manager boot: it belongs to the graphical login,
not to SSH sessions or lingering. No new long-running watcher or update daemon is
introduced. The initial supported profile has one graphical login per user;
simultaneous graphical sessions for the same user remain unsupported.

Before installing, `lightdm --show-config` is validated against the known Debian
wrapper or the already-managed wrapper. A custom wrapper causes an actionable
failure instead of being silently replaced. The effective configuration is checked
again afterward. LightDM's output is captured from stderr as well as stdout.

## Applying to an existing VM

Use the targeted system repair entry point from a complete updated checkout or
the persisted implementation:

```bash
sudo bash scripts/session/install.sh
```

The system installer does this automatically as part of the desktop module.
The targeted repair installs the wrapper, target, XApp drop-in and dedicated
LightDM fragment. It backs up changed privileged files through the common helper.
It does not restart LightDM, reboot, stop the current session or broadly reset
failed services.

For an existing installation, **reboot once after applying the repair**. LightDM
keeps the running daemon's configuration in memory: a mere logout/login before
that reboot still uses the old wrapper. This was confirmed in the actual daemon
log even though `lightdm --show-config` correctly displayed the new file on disk.
The initial installation's planned reboot already satisfies this requirement.

## Acceptance

After the initial reboot/login:

```bash
systemctl --user is-active graphical-session.target debian-workstation-cinnamon-session.target
systemctl --user --failed --no-pager
```

Both targets should be active, with no failed units. Use Gear Lever's chooser and
check the accent-color portal. Log out/in twice normally. Inspect the journal:
portal stop/start jobs should occur at the session boundaries, with no new status-1
exits, XApp GTK initialization errors, or stale processes retained from the old X
display. Check the wrapper still executes the normal Debian Xsession, that desktop
login works, and that setup does not repeat for unchanged implementation inputs.

The read-only verifier now checks the active graphical target and failed system
and user units, in addition to the portal response. A blue accent response alone
cannot certify every backend or logout behavior.

## Recovery

If login fails after applying this repair, use the VM console/SSH to move
`/etc/lightdm/lightdm.conf.d/91-debian-workstation-session.conf` out of the active
configuration directory, then reboot when safe. Debian's original session wrapper
becomes effective again. Retain logs (`~/.xsession-errors`, LightDM daemon log and
the user journal) for diagnosis. Restore the prior XApp drop-in from the privileged
backup if it replaced one; otherwise remove only this project's
`10-debian-workstation-session.conf`. No user data needs to be deleted.

## Primary references

- [systemd graphical-session ownership](https://www.freedesktop.org/software/systemd/man/latest/systemd.special.html#graphical-session.target)
- [LightDM session-wrapper configuration](https://github.com/canonical/lightdm/blob/main/data/lightdm.conf)
- [LightDM session-child execution and wait](https://github.com/canonical/lightdm/blob/main/src/session-child.c)
- [GTK portal shipped unit](https://github.com/flatpak/xdg-desktop-portal-gtk/blob/1.15.3/data/xdg-desktop-portal-gtk.service.in)

The native unit relationships and effective LightDM settings were also inspected
directly on the authorized fresh VM; package behavior may differ on other systems.
