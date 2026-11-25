# Dependency inventory and trust

The baseline companion was reviewed at
`8446f8dccd9e3da21f180bbc6fac22ebf0081d0b`. Its preseed creates only root,
permits root SSH password login, uses ifupdown, supplies Debian Trixie/update and
security sources (main/contrib/non-free-firmware, plus main-suite non-free),
Chrony, sudo, curl, SSH, cron, disk and monitoring utilities, basic VMware/KVM
guest tools, fstrim and a console login banner. It creates no swap and selects
no unattended updates. These are upstream conventions, not additional workstation
security-policy changes. The workstation does not rewrite SSH, timekeeping,
storage, partitioning, banner or existing unattended-update configuration.

| Dependency | Source / trust | Selection and failure behavior |
| --- | --- | --- |
| Debian desktop and system packages | Signed Debian Trixie/update/security repositories, existing distro keyring | Normal APT candidates; install simulations reject removals; explicit task exclusions in assets/exclusions.txt |
| Mint themes/icons/libadwaita/XApp | Signed Gigi repository at https://fastly.linuxmint.io | Exact name allowlist, verified key fingerprint, security fallback; see security-policy.md |
| Nemo Grid Compensator | https://github.com/bobapplemac/nemo-grid-compensator | **main by default**, optional NEMO_REF; its installer resolves its own single archive, checks dependencies and initializes through documented startup. No vendored copy. Inspected revision d4ac6b1e5b84b91a27b53c81de660931d3a73498, not a claim that every future main is tested |
| ani2xcursor | https://github.com/yuzujr/ani2xcursor/releases/tag/v1.6.0 | Tested amd64 AppImage, SHA256 9ae4c9855061622e6007bf5f2d1f0713c56daf8451e239b843d00389b6235b6b; executes as desktop user through FUSE, only when cursor ZIP supplied |
| Flatpak / Flathub / Gear Lever | Debian Flatpak; https://flathub.org/repo/flathub.flatpakrepo; it.mijorus.gearlever | System remote and app; Flatpak's native verification and normal updates, no forced commit freeze |
| Notepadqq | https://api.github.com/repos/notepadqq/notepadqq/releases/latest | Latest stable initial x86_64 AppImage; exactly one matching asset and GitHub SHA256 digest required; mismatch or changed previously seen release digest stops; subsequent manual updates through Gear Lever GithubUpdater |
| 1Password desktop and CLI | https://downloads.1password.com/linux/debian/amd64 | Official stable signed repository; key 3FEF9748469ADBE15DA7CA80AC2D62742012EA22; official debsig policy and package signatures verified before installing new versions; application-only package allowlist |
| Microsoft Core Fonts | Debian contrib ttf-mscorefonts-installer | Optional default-on package; follows package download/licensing workflow; requires contrib, does not bundle fonts |
| Supplemental Windows fonts/cursors | User-provided input ZIPs from scripts/windows exporters | Optional; safe bounded extraction, font-family metadata filtering, exact tested cursor mapping and validation; never redistribute |

The cursor checksum was originally a locally observed R&D checksum. During this
implementation it matched GitHub release API asset digest metadata as well. This
is corroboration from the official release host, not independent cryptographic
upstream attestation. HTTPS/repository account trust remains necessary. The latest
Notepadqq digest has the same hosting trust relationship; locally stored receipts
detect changed known artifacts, not a malicious upstream release account.

Gear Lever CLI/settings source was reviewed at
`a2917f2adafc78e0478e47d5843de9ede6c1aa3f`. Current CLI supports
`--integrate --yes`, `--list-installed --json`, `--set-update-source` and
`--list-updates`. The native background request is made **inside the Flatpak**
so the portal associates the application identity correctly. Its preference and
INI configuration are kept in sync; a permission rejection/time-out fails visibly,
and can be retried after the user permits it. No replacement update daemon is
introduced. Current 1Password packages create a deb822 1password.sources file;
the installer uses that same canonical path to avoid a duplicate legacy .list.

Windows ZIP filename/family inventories are not a license grant. Assets are
parsed as the desktop user; installation writes a separate local font directory
and dedicated generated cursor themes. Font emoji/symbol/asset families are
excluded. Native Adwaita cursors and Debian fonts remain sufficient without ZIPs.

Updating an immutable artifact pin requires reviewing the official release,
recording the new expected digest, testing converter behavior and updating the
documented observation. Do not silently accept a different digest. Updating main,
latest releases, signed package repositories and Flatpak remotes is intentionally
not bit-for-bit reproducible; use explicit source refs where offered and record
installed package/app versions for a particular deployment.

Primary integration documentation:
[1Password Linux install](https://support.1password.com/install-linux/),
[Gear Lever](https://github.com/mijorus/gearlever),
[ani2xcursor](https://github.com/yuzujr/ani2xcursor),
[Nemo installer](https://github.com/bobapplemac/nemo-grid-compensator/blob/main/docs/installation.md).
