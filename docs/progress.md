# Development record

## Older NVIDIA fallback

After the authorized account/graphics push (bf1dd9b), the user suggested an older
driver option for incompatible cards. The open stack remains preferred. Only an
actual GPU-compatibility rejection triggers fallback; metadata/other errors still
stop. The temporary vendor source/key/pins are restored before native Debian
driver, kernel and diagnostic candidate checks.

The native package's authenticated supported-gpus.json must support every NVIDIA
adapter without a legacybranch restriction. NVIDIA_LEGACY=ask offers a separately
consented proprietary kernel module; yes/no support explicit unattended permission
or skip. Absent Kepler/etc. branches are not imported. Selected driver families
are retained for reruns and mixed incompatible GPU sets stop. Secure Boot, headers
and module verification are shared, with flavor-specific license verification.

Actual signed APT/package tests passed for upstream 620.70.10-1 (RTX 5060 Ti 2d04,
kernelopen) and native Debian 550.163.01-2 (GTX 1080 1b80). Each empty-status
transaction resolved 394 packages without toolkit, wrong-module choice or removals.
No driver was installed. Final WSL regression: 47 passed of 53, six existing nmcli
cases skipped; ShellCheck passed. Physical boot/DKMS/enrollment validation remains
pending. Versions are observations, not holds.

## Native account prompts and optional physical graphics support

User-requested changes: new regular accounts now use normal interactive adduser
instead of suppressing GECOS and asking only for a password. This restores Full
Name and the standard optional fields. Existing accounts are preserved; chfn is
documented for correcting their display name. Interrupted native account setup has
a dedicated marker and resumes password/chfn prompts rather than silently leaving
an incomplete account. The older password-pending marker is still recognized.

A graphics module follows desktop/hypervisor setup and is individually runnable.
It inspects PCI display adapters, retains virtual drivers, and offers native
Intel/AMD firmware/Mesa or NVIDIA's modern open kernel modules. Default ask requires
real terminal consent; yes/no config supports explicit unattended choice or skip.

NVIDIA uses only its official Debian 13 signed source with a verified current key
fingerprint and exact driver/runtime allowlist; unrelated CUDA packages are blocked.
Current driver candidates are selected dynamically, not frozen. GPU support comes
from supported-gpus.json inside the exact APT-authenticated driver package, including
kernelopen and subsystem checks for every NVIDIA card. Unmanaged existing driver
stacks require migration review. Candidate and selected runtime versions must be
coherent; simulated removals/closed modules stop. Default kernel headers, DKMS
module license/version and Secure Boot MOK enrollment are checked. No forced reboot,
driver unload, generated Xorg layout, legacy-kernel fallback or Secure Boot disabling.

Real signed-repository tests verified the NVIDIA InRelease -> Packages.gz -> exact
driver package SHA256 chain. The production libapt validator and isolated empty-
status transaction resolve 394 package candidates with matching 620.70.10-1 driver
components, no CUDA toolkit, no closed kernel module and no removals. This observed
version is not a pin. The package manifest names PCI 10de:2d04 as RTX 5060 Ti with
kernelopen support. Debian's actual DKMS generate_mok interface was inspected.

Final Debian WSL suite: 50 tests discovered, 44 passed and six existing native
NetworkManager cases skipped because nmcli is absent there. The new graphics
cases, native APT fixtures, Notepadqq Linux integration and opt-in systemd fixture
passed. Python/Bash syntax and ShellCheck warning checks passed. The revised
interactive account wizard is delegated to native adduser and still awaits the
next fresh-install human acceptance run.

Physical RTX 5060 Ti boot, DKMS installation and Secure Boot enrollment remain
unvalidated and must be accepted on real hardware. No driver was installed on the
Windows host or WSL during these simulations. See graphics.md for trust/security,
recovery, source selection and exact verification commands.

## Portal lifecycle root cause and validated repair

Direct access to the authorized fresh VM confirmed that graphical-session.target
was inactive throughout Cinnamon X11 login, despite the GTK portal, frontend and
GNOME Terminal already being PartOf that target. The installed Mint XApp backend
lacked that relationship entirely. At logout, GTK/XApp/Terminal exited with status
1 when X disappeared; the still-running frontend tried to reactivate XApp before
the next display was ready and logged Failed to initialize Gtk.

The desktop installer now uses LightDM's session-wrapper mechanism around the
unchanged Debian /etc/X11/Xsession. A small native session target binds to and
retains graphical-session.target; the wrapper imports display activation variables,
starts the session target and synchronously stops both targets before returning
to LightDM. XApp receives a PartOf/After drop-in. Custom existing wrappers are
rejected. This preserves normal Xsession hooks and avoids watchers, restart loops,
reset-failed loops and reclassifying all status-1 exits as successful.

LightDM caches its running configuration. The first logout/login after installing
the repair still used the old wrapper (verified in lightdm.log), so one explicit
reboot was needed for the existing VM. After reboot, both native targets were
active. The user then performed two normal logout/login cycles and opened/cancelled
the chooser. SSH inspection confirmed clean stop/start jobs for every portal at
both boundaries, no failed user units, fresh portal processes, and the unchanged
expected blue accent tuple. The recurring lifecycle defect is resolved on this VM.

Validation: all 41 standard regression cases passed on the VM, including new
wrapper ordering, argument preservation, child-error cleanup, existing-owner and
custom-wrapper checks. An additional opt-in native systemd fixture passed using
unique runtime targets/services; it verifies RefuseManualStart/StopWhenUnneeded and
PartOf stop behavior without touching the real desktop targets. ShellCheck at
warning level and native systemd target syntax validation passed under Debian WSL.
See session-lifecycle.md for implementation, acceptance and recovery.

The final VM run passed all 42 cases together with DW_SYSTEMD_TESTS=1. The updated
installed workstation verifier reported zero failures. The updated implementation
and offline documentation were persisted, targeted installation was rerun without
configuration duplication, and the continuation completion signature was refreshed
by actually completing it in the live Cinnamon session. Temporary SSH test keys
were removed after validation. No remote push is implied by these local changes.

## Fresh VM verification after Notepadqq repairs

User-supplied fresh-VM output confirms plain Notepadqq name and GithubUpdater;
the user also confirms the menu regression is fixed. The existing verifier reports
zero failures: Debian/Cinnamon session, package/repository checks, no pending APT
transaction changes, artwork/glyphs, expected blue portal tuple, active grid service,
Gear Lever background preference/autostart, graphical target and 3,072 native
Windows XCursor loads. NetworkManager owns the connected migrated Ethernet
connection and DNS lookup succeeds. No failed system services were listed.

However, the separate user-service check lists xdg-desktop-portal-gtk.service as
failed. The successful accent-color response does not establish the health of all
portal backends. Service status/journal evidence is pending before diagnosing or
changing portal startup/configuration. The verifier now checks failed system and
user units explicitly, so this condition cannot yield an overall zero-failure
report. This verifier improvement is local until separately published. Visual and
interactive acceptance remains pending; no release-readiness claim.

Follow-up unit status shows the GTK portal active/running after a successful
restart. The journal records an earlier status-1 exit and subsequent successful
start, without an explanatory backend error. The current failure has recovered;
the cause remains unknown. No portal configuration change or failure-counter
reset is justified by this evidence. Next acceptance checks: no failed user units,
a real Flatpak file chooser, and stability after logout/login. Recurrence requires
broader session journal evidence around the exit.

## Fresh-install follow-up: successful continuation and menu-name repair

The user applied commit 01125e2 to the fresh VM and reported successful setup
completion. This establishes the real first-login continuation and retry path on
that VM; the remaining automated verifier and visual/interactive acceptance checks
are still pending. It does not establish release readiness.

The original KEEP-mode installation also left `Notepadqq (543d74)` in the menu.
The earlier fix prevented that mode for future integrations but deliberately reused
the existing AppImage, so it did not repair its label. The installer now repairs
the generated Name (including matching localized names) in the exact user desktop
entry reported by Gear Lever. It verifies X-AppImage-Name and TryExec first,
preserves comments/actions/commands/icons, backs up the original outside the
applications directory, and refuses custom names or unrelated entries. No AppImage
reinstall or update-source reset is needed for the standalone --repair-name mode.

Follow-up Windows validation: eight focused lookup/repair tests passed; two Linux
shell integration cases remain skipped on this host. The repair is idempotent in
file fixtures. Actual Cinnamon menu refresh and real launcher repair on the fresh
VM await the user's verification. The next push is explicitly user-authorized.

## Fresh-install feedback: Notepadqq discovery

The first user-run fresh Debian trial completed system provisioning, rebooted and
started the graphical continuation automatically. Appearance/artwork checks,
Nemo Grid Compensator initialization/startup and Gear Lever's background portal
preference succeeded. Notepadqq integration itself succeeded but the continuation
stopped: Gear Lever recorded `Notepadqq (543d74)` and our exact-name lookup missed
it. Earlier runtime validation reused an existing plain-name installation and did
not cover this fresh KEEP-mode name. Full acceptance remains incomplete.

The fix accepts a complete Notepadqq name with an optional generated parenthesized
suffix, rejects multiple matches and malformed inventory, and uses Gear Lever's
native --replace integration mode for new installs. An existing suffixed AppImage
is reused without downloading or integrating another copy. Focused tests cover
the reported inventory, ordinary/versioned names, malformed data, ambiguity, and
mocked fresh integration plus rerun through the actual shell installer.

Local follow-up validation on the Windows Python 3.9 host: 31 tests discovered,
20 passed and 11 Linux-dependent cases skipped; Bash syntax and git diff checks
passed. Five new lookup cases passed, including the reported fresh-install name.
The two new shell integration cases require Linux and have not run in this
follow-up environment. This result does not supersede the earlier Debian test
record or establish that the fresh VM's continuation now finishes.

## Scope and current boundary

Build the supplied Debian 13 amd64 Cinnamon X11 reference experience as a small
Bash/Python provisioning project, keeping the companion ISO builder and grid
utility independent. Stop for a genuinely fresh VMware acceptance trial, then
address reported defects before release preparation. Do not push/publish without
the user's approval. All supplied reference files were read in full.

Current implementation includes the complete system/session modules, optional
ZIP processing, native appearance assets and icon utility, strict networking,
repository policy and security review, remote/local bootstrap, user walkthrough,
verification and acceptance documents. The formal installer is authoritative.

User steering incorporated: root account creation walkthrough; regular-user sudo
elevation with that user as primary account; Nemo main by default; latest stable
initial Notepadqq release; input/ default ZIPs with nonfatal absence warnings;
main-branch irm/iex exporter quick start; .py artwork helper and grouped scripts.

## Evidence obtained on 2026-11-25

- Windows Python portable tests, Linux shell syntax and Python compilation.
- 24 automated tests passed on an authorized disposable Debian 13 amd64 VM:
  configuration rejection, archive validation, file preservation/ownership,
  actual isolated APT priorities/solver, exact embedded bootstrap extraction,
  native nmcli DHCP/static dual-stack VLAN rendering, stage/commit idempotence,
  changed-source rejection and simulated interrupted-transaction recovery.
- ShellCheck at warning severity passed after addressing reported issues.
- Full system provisioning ran successfully on the disposable **existing** desktop.
- Session provisioning ran successfully against its actual active Cinnamon X11
  session: settings, panel configuration, artwork/glyph verification, grid helper
  startup, Gear Lever native background request and Notepadqq update-source setup.
- Optional supplied cursor/font ZIP workflows ran on that VM. Generated cursors
  passed structural and native loading checks and received thumbnails; 57
  supplemental font files were selected by metadata. No proprietary assets were
  copied back into the public repository.
- Real current Debian/Mint package metadata and install/full-upgrade simulations
  were inspected. Official AppImage asset digests corroborated the R&D values.
- Existing desktop test uncovered/fixed PyGObject schema-property access and
  passwordless-sudo verification behavior. Current 1Password packages generate a
  deb822 source, so the implementation uses that canonical path to avoid duplicates.
- The complete installer rerun completed, skipping unchanged cursor conversion
  and already-current 1Password downloads. The continuation wrapper completed
  against the real active desktop; workstation verification reported zero failures,
  including 3,072 native XCursor loads.
- Empty-status simulation with real APT indexes selected 1,644 packages, included
  every requested desktop package and omitted all 40 exclusions.
- Root's interactive regular-user creation/password walkthrough and that ordinary
  account's password-based sudo elevation succeeded with a temporary account.
- Latest stable Notepadqq metadata/download verification passed. Coherent native
  library-family reversion was simulated with no removals.

These checks do not constitute a genuinely fresh install, live ifupdown-to-NM
reboot migration, or user visual/interactive acceptance. No release-readiness claim.

## Remaining acceptance work

Follow docs/acceptance.md on a genuinely fresh reference console VM. Recheck account
creation/password prompts, sudo denial/authentication, first-login autostart and
completion across a real login transition, live networking after reboot, missing
ZIP fallback on a clean profile, visual appearance and desktop interaction. Test
other network profiles only when needed for deployment. Dynamic main/latest
upstreams may change after the inspected revisions; record actual versions.

During development a separate disposable VM was authorized for unrestricted tests.
Connection details and temporary SSH test keys are kept outside tracked project
records. Its pre-existing repository/theme configurations were backed up locally
on that VM for integration tests. The original customized reference workstation
was not reinstalled. See the final validation record for the last rerun results.

## Historical input locations

| Supplied file | Formal/historical destination |
| --- | --- |
| reference/playbook-notes.txt | docs/history/playbook-notes.txt (username anonymized) |
| reference/workstation-cursor-playbook.txt | docs/history/workstation-cursor-playbook.txt (username anonymized) |
| reference/mint-y-app-icons | scripts/desktop/mint-y-app-icons.py |
| reference/Export-Windows-Cursors.ps1 | scripts/windows/Export-Windows-Cursors.ps1 |
| reference/Export-Windows-Fonts.ps1 | scripts/windows/Export-Windows-Fonts.ps1 |
