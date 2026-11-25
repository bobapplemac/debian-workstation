# Initial implementation validation — 2026-11-25

Environment: Windows development host with Python and Git Bash; an explicitly
authorized disposable Debian 13 amd64 VMware VM with an existing customized
Cinnamon X11 desktop. No connection credentials, private addresses, proprietary
ZIPs or generated Windows artwork are stored in this report/repository.

| Check | Result / scope |
| --- | --- |
| Python syntax, Bash syntax | Passed |
| ShellCheck warning severity | Passed for installer, modules, libraries and shell helpers |
| Automated regression suite | 24 tests passed on Debian; Windows skips APT/nmcli-specific cases |
| Remote bootstrap safety | Exact embedded code exercised with mocked HTTPS responses, valid fixed commit, invalid inventory/link/traversal/duplicate/root cases and truncated gzip footer |
| Real current APT candidates | Narrow Mint allowlist accepted; unrelated Mint candidates rejected by libapt audit |
| Hypothetical security releases | Actual isolated APT candidate/solver tests; lower-sorting and newer Debian security versions win; no package holds |
| Curated desktop from empty package state | Real-index simulation selects 1,644 packages; all requested desktop packages present; all 40 exclusions absent |
| Network native rendering | nmcli --offline accepts DHCP, MAC DHCP identity, static dual-stack VLAN, DNS/search and route properties; auto/hotplug intent preserved |
| Network transaction fixtures | Repeated stage/commit, changed-source refusal and simulated power-loss recovery passed without touching live NICs |
| Integrated system installation | Completed on existing disposable desktop, then completed again on rerun |
| Account lifecycle | Root username/new account/password walkthrough passed; ordinary temporary account's password-based sudo elevation passed; existing passwordless-sudo account path passed |
| Missing optional ZIPs | Warned and continued using native cursor fallback during initial system test; later supplied asset workflow tested separately |
| Cursor ZIP workflow | Two themes; 17 real cursor files per theme; all 16 sizes; expected Aero animation/static Black frames; structural checks passed |
| Native XCursor load | 3,072 loads, zero failures; high-quality thumbnails generated |
| Supplemental fonts | 57 files selected by family metadata; symbol/emoji exclusions retained |
| Actual Cinnamon session module | Completed settings, live panel operations, original artwork/glyph verification, native portal request and grid-service startup |
| Continuation wrapper | Completed and recorded success against the already active graphical session; a fresh-login autostart transition was not performed |
| Final workstation verify | Zero failures in the actual desktop environment |
| Latest stable Notepadqq downloader | Metadata/asset digest retrieval and download verification passed; current upstream latest observed as v2.1.1, not hardcoded in installer |
| Gear Lever | Native CLI options confirmed; existing Notepadqq integration/update source checked; background preference/portal autostart verified |
| 1Password | Official fingerprint/policy and both downloaded package signatures verified; subsequent rerun skipped unchanged packages; canonical deb822 source used |
| Native-library reversion | Coherent exact-version GIR/library transaction simulated; two downgrades, no removals; no actual fallback imposed |
| Existing session continuity | Installer did not forcibly restart LightDM or Cinnamon or reboot the machine |

Runtime tests found and corrected a PyGObject schema-property mistake, a
passwordless-sudo validation nuance, Linux source line endings after Windows
editing, and the vendor-generated 1Password deb822 source duplication issue.

**Not yet performed:** a genuinely fresh console-to-desktop installation, live
ifupdown ownership transfer at a reboot, automatic continuation across first
graphical login, denied-portal retry through an actual permission dialog, and
the visual/interactive acceptance checklist. Current hardware/other hypervisors,
multi-monitor, HiDPI and Wayland compatibility are not claimed. Main/latest inputs
can change after this report. This is preparation for controlled acceptance, not
production/release certification.
