# Development record

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
