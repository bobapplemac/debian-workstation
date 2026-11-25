# LMDE integration and security-update policy

## Decision

The project uses the tested LMDE 7 Gigi theme/icon packages, patched libadwaita
and XApp portal. Only these package names are allowed from fastly.linuxmint.io:

```
mint-themes mint-x-icons mint-y-icons mint-cursor-themes
libadwaita-1-0 gir1.2-adw-1 libadwaita-1-dev libadwaita-1-doc libadwaita-1-examples
xdg-desktop-portal-xapp xapp-symbolic-icons
```

The signed repository uses an explicit keyring, verified against fingerprint
`302F0738F465C1535761F965A6616109451BBBF2`. All other Mint packages have priority
**-1**. The allowlist has priority **500**. Before changes are accepted, the
installer checks libapt's candidates for every package, simulates the selected
install and full-upgrade, and rejects removals. Failed repository validation
restores the prior source, preferences and key files. No package holds are used.

**Security fallback:** the five libadwaita binary packages from the signed Debian
`trixie-security` release have priority **1001**. This intentionally permits a
Debian security package to become the candidate even if its version sorts lower
than the Mint-patched package. It does not generally prefer Debian packages over
the intended Mint integration. In the absence of a security-repository version,
the tested Mint version remains the candidate when it sorts higher.

This is a conservative tradeoff: once a libadwaita package is present in Debian
security, that version remains preferred while published there, even if Mint
later incorporates the same fix. The project does not automatically infer patch
equivalence or remove the fallback to recover appearance. An explicit maintainer
review of source changes is needed before changing policy. Accent integration
can be reduced after falling back; a package inventory and desktop notice make
the change visible. Other Mint-only assets remain installed.

## Evidence and limitations

Public metadata inspected during development on 2026-11-25:

| Package/source | Debian Trixie | LMDE Gigi |
| --- | --- | --- |
| libadwaita-1 | 1.7.6-1~deb13u1 | 1.7.6+mint2+gigi |
| mint-themes | no native counterpart | 2.3.8 |
| mint-x-icons / mint-y-icons | no native counterpart | 1.7.5 / 1.9.1 |
| mint-cursor-themes | no native counterpart | 1.0.2 |
| xdg-desktop-portal-xapp | Debian candidate inspected on target | 1.1.3+gigi |
| xapp-symbolic-icons | Debian candidate inspected on target | 1.0.9 |

No libadwaita binary was present in the Debian security amd64 index inspected
that day. These are observations, not package locks. The Gigi development package
depends on **exact matching versions** of both GIR and the shared library.
Fallback/reversion must therefore consider the installed family together, not
downgrade only libadwaita-1-0 while retaining an incompatible -dev package.

Debian version comparison puts `1.7.6+mint2+gigi` above
`1.7.6-1~deb13u2`. Equal priority 500 would therefore mask that hypothetical
Debian security rebuild. APT regression tests exercise actual libapt candidates
and installation simulations in isolated synthetic indexes: normal Mint selection,
unapproved Mint package rejection, a lower-sorting security rebuild winning and
being proposed as a downgrade, and a higher security version winning. Separate
target tests inspect current real signed metadata and real dependency simulations.
Synthetic scenarios are not claims that those security releases exist.

LMDE uses Debian as its base while maintaining its own modified packages.
The review found no machine-readable promise mapping Debian security advisories
to every corresponding Mint-patched binary, nor a guaranteed patch delivery
deadline for this mixed Debian/Mint arrangement. Debian source advisory versions
and Mint version suffixes alone cannot establish that a Mint patch carries a
specific fix. No such guarantee is claimed. Maintainers must examine Debian
security tracker/source changelogs and Mint source changes for equivalence.

## Notifications and ordinary updates

`apt update` invokes a short local candidate audit. A daily timer audits the
current cached inventory as well. It does not independently fetch metadata;
normal Debian APT metadata refresh or an administrator's `apt update` supplies
fresh signed indexes. The audit writes a public, credential-free
`/var/lib/debian-workstation/security-status.json`, containing installed versions,
candidates and all published Debian versions for the installed library family.
Changes are logged. The next graphical login displays a native notification once
per changed inventory. This is a review prompt, not a vulnerability scanner.

Stock `apt upgrade` / `apt full-upgrade` consult the policy; no holds or Debian
security sources are removed. A security fallback may be a **downgrade** in dpkg
version ordering. Noninteractive `apt-get -y` ordinarily refuses a downgrade
without explicit authorization; the installer likewise stops rather than adding
a blanket --allow-downgrades. Administrators should inspect the simulation and
use the explicit reversion procedure below. An existing unattended-upgrades
installation retains its configuration and allowed origins. It might refuse a
downgrade or packages outside its origins; this project does not promise automatic
installation in that case. The audit makes the candidate discrepancy reviewable.
The reference base has no unattended update policy in the first place.

GNOME Software's manual-update preference and Gear Lever's background checking
are separate application choices. They do not disable an existing OS security
updater or silently enable unattended installation of Mint packages.

## Revert the library family to Debian

1. Run `sudo apt update` and inspect
   `apt-cache policy libadwaita-1-0 gir1.2-adw-1 libadwaita-1-dev` plus the audit.
2. Run `sudo bash scripts/repositories/revert.sh` from the checkout (or the
   corresponding persisted path). This pins only the libadwaita family to signed
   Debian releases, selects native versions for every installed family member,
   prints an exact-version simulation, rejects removals, then installs with
   narrowly scoped downgrade authorization. It retains the Mint themes and portal.
3. Log out/in to reload shared libraries. Check GTK4 appearance and portal accent
   behavior. Native libadwaita may not retain the reference accent integration.
4. Keep the generated native-family preference until a deliberate review decides
   to restore patched integration. Do not remove it merely to silence the notice.

To remove all Mint integration, first switch to native GTK/icon/shell themes,
remove Mint-only theme packages after reviewing dependencies, then disable the
project's Mint source. Do not delete the repository before arranging the coherent
native library-family transaction. Privileged repository backups are retained
under `/var/lib/debian-workstation/backups/` using the original absolute path
hierarchy. User/greeter text updates retain `.before-debian-workstation` backups
beside the original file. Backups are not active APT source/preference fragments.

## Primary sources

- [APT priority and downgrade rules](https://manpages.debian.org/trixie/apt/apt_preferences.5.en.html)
- [Debian package version format](https://manpages.debian.org/trixie/dpkg-dev/deb-version.5.en.html)
- [Debian security tracker: libadwaita-1](https://security-tracker.debian.org/tracker/source-package/libadwaita-1)
- [LMDE](https://www.linuxmint.com/download_lmde.php)
- [Mint libadwaita source](https://github.com/linuxmint/libadwaita)
- [Gigi package indexes](https://fastly.linuxmint.io/dists/gigi/)

The fallback policy and its limitations are project engineering decisions based
on package metadata and tests, not a claim of Debian/Mint endorsement.
