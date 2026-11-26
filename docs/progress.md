# Project status

## Accepted baseline

Fresh-install VM validation is complete as of 2026-11-26. The user rebuilt a
Debian 13 amd64 VM from the base installation and accepted the resulting fully
functional Cinnamon X11 desktop. See [validation](validation.md) and the
[repeatable acceptance procedure](acceptance.md).

The supported workflow is a fresh installation. Existing KDE/other-desktop
conversions are handled separately. Physical GPU boot/Secure Boot, other
hypervisors and additional hardware/network profiles retain their documented
validation scope; they are not blockers for the accepted VMware baseline.

The product uses Cinnamon's native screensaver and authentication, with the
verified clock/name presentation fixes. No alternate-locker experiments are
shipped. Main/default external sources remain updatable as documented in
[dependencies](dependencies.md).

## Current maintenance

Use [the changelog](../CHANGELOG.md) for maintained capabilities and fixes.
Native lock-screen adaptations are guarded and reapplied after APT transactions.
The first-login completion marker tracks implementation inputs, including shared
libraries and the entry point, while ignoring generated Python bytecode.

Sanitized screenshots have not yet been committed; the accepted result was
checked on the VM and in user-supplied captures. See [screenshots](screenshots/README.md).

## Historical record

The detailed development chronology is preserved in the repository's
[historical development record](https://github.com/bobapplemac/debian-workstation/blob/main/docs/history/development-record.md).
Earlier validation observations are in
[historical validation notes](https://github.com/bobapplemac/debian-workstation/blob/main/docs/history/validation-notes.md).
These archives are excluded from the installed offline documentation snapshot.
