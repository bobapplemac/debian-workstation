# Architecture and baseline decisions

The formal installer is authoritative. `docs/history/` preserves anonymized R&D
notes for engineering context, not a second supported executable playbook.

Discovery read all five supplied files in full. The main and separate cursor
workflows agree in mappings, conversion, sizes, aliases, structural checks,
native loading and thumbnail generation. The separate cursor notes directly
edit the greeter cursor entry; the final main notes configure the complete
Adwaita/Papirus greeter afterward. The implementation uses that final appearance.
No missing CSS, SVG or supporting source artifact was found.

Order: base preparation -> validate/stage networking -> narrowly allowlisted
repositories -> curated desktop packages -> optional artwork/greeter -> software
repositories/Flatpak -> durable first-login continuation -> read-only verification.
The first four modules are system operations. Session preferences use the actual
logged-in Cinnamon user's GSettings/D-Bus. No fake root D-Bus session is used.
Offline dconf databases could set simple preferences, but do not configure live
applets, portal permissions, GTK icon verification or grid initialization; keeping
those operations in one visible continuation is simpler and avoids bus ownership
mistakes. No automatic login, forced reboot or display-manager restart occurs.

LightDM's authenticated X11 session is wrapped around the unchanged Debian Xsession
to own the native systemd graphical-session lifecycle. This stops GUI services
before X display teardown and fixes portal failures across logout/login. See
[session lifecycle](session-lifecycle.md) for the observed cause, native target
dependency, XApp drop-in, compatibility checks and recovery procedure.

`install.sh` is the local/remote entry. A remote bootstrap resolves its requested
ref once to a full commit, downloads one archive, validates every member (no
links/special files/traversal/duplicates; bounded compressed/expanded size),
extracts to a private temporary directory, then invokes that revision's local
installer. A recursion guard prevents another bootstrap. Fixed source revisions
are optional; dynamic external APT/Flatpak sources intentionally remain updatable.

Public Markdown documentation and the license are persisted with the implementation,
including offline network recovery instructions. Historical notes, local configuration,
proprietary inputs and screenshot binaries are excluded from that snapshot.

`lib/` holds the small runner and shared shell functions. `modules/` contains
coarse provisioning units. `scripts/` groups cursor, font, desktop, network,
repository, Notepadqq, Gear Lever and Windows helpers. Shared configuration,
safe ZIP extraction and file-update routines remain at its root. Substantial CSS
and SVG assets are extracted unchanged from the main playbook. The artwork utility
is named `mint-y-app-icons.py`, including its installed command.

Account behavior: an ordinary user's run checks sudo and selects that account;
root is guided through choosing/creating a regular account. Passwordless sudo is
explicitly opt-in. No account name, host address, private DNS workaround or
credential from development is part of the implementation.

Updates preserve unrelated INI keys, CSS, Xresources and custom shortcut IDs.
Dedicated user assets have content-hash ownership records and refuse conflicting
unmanaged content or later user edits. Changed files receive first-change backups.
Theme/application artwork is not written into distribution-owned binaries or
themes: local icon overlays are used. Rerun the session module after relevant
theme/application updates to refresh artwork slot discovery; existing symlinks
already reference package artwork paths, so there is no dedicated icon watcher.

User-requested changes from the original specification: Nemo Grid Compensator
tracks main by default; Notepadqq initially uses the latest stable GitHub release;
input/ is the default optional ZIP location; grouped helper folders and the
artwork helper's .py extension improve clarity. Optional fixed Nemo revisions
remain possible. Historical observed package versions are not package holds.
