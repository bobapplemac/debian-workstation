> Historical development record. Pending statuses and temporary instructions
> describe earlier implementation stages. For current acceptance, see
> [the validation record](../validation.md). Use the main README for setup.

# Validation record

## Fresh-install VM acceptance complete — 2026-11-26

The user rebuilt the test VM from a base Debian 13 installation, ran the installer
through to a fully functional Cinnamon desktop, and confirmed that everything
looked good. The user has explicitly accepted end-to-end VM validation as complete.
This validates the fresh-install workflow, rather than only rerunning modules on
the original development desktop. The accepted source includes the native
lock-screen fixes in e134a31; 89378a6 adds the subsequent README-only adjustment.

Earlier fresh-VM feedback established successful system provisioning, reboot and
first-login continuation, Notepadqq repair, desktop behavior and portal lifecycle.
The final rebuilt-VM confirmation accepts the resulting integrated workflow.
The most recent automated suite recorded 53 passes and six NetworkManager-dependent
skips, with ShellCheck and APT hook syntax checks passing.

Physical GPU installation/boot, Secure Boot enrollment and additional hardware or
network profiles retain their separately documented validation status. VM acceptance
does not assert those scenarios were tested. No release tag is created by this record.

The sections below preserve earlier development checkpoints and the evidence
available at those stages; their pending-work statements are historical.

## Native Cinnamon lock-screen follow-up — 2026-11-26

The test VM retained native Cinnamon locking and settings. The user visually
confirmed AM/PM time, time/date centering, and a name centered over the password
field alone, excluding the two buttons. Empty account-name metadata was given a
username display-name fallback, and normal native unlocking was confirmed.
The alternate-locker experiments are excluded from the installer.

The production helper transformed pristine Debian 6.4.0-1 clock/unlock sources
into byte-identical copies of the visually accepted VM files. Its root installer
recognized both already-applied changes without altering contents or restarting
the locker. Preflight/source preservation, drift rejection, symlink rejection,
idempotence and APT-hook warning behavior are covered by regression checks.
Final suite: 53 passed, six NetworkManager-dependent skips (59 total), including
the opt-in native systemd lifecycle test. ShellCheck and APT hook syntax passed.

These checks initially validated the targeted changes on the existing VM. The
subsequent complete fresh-install acceptance is recorded above.

## Separately validated older NVIDIA branch

Signed APT and authenticated package-manifest tests passed for both driver paths:
upstream open 620.70.10-1 supports RTX 5060 Ti; native Debian 550.163.01-2 supports
GTX 1080. Each resolves 394 packages from empty status without toolkit, wrong
kernel module or removals. Native fallback requires separate consent and cannot
substitute an incompatible driver for Blackwell. Regression: 47 passed, six
nmcli-dependent skips (53 total); ShellCheck passed. No physical driver install
or boot has been performed.

## Account setup and graphics follow-up

New-account setup now delegates directly to native interactive adduser, retaining
Full Name and the usual optional account fields; supplied GECOS names are preserved.
Syntax checks cover this change; the revised native account wizard still requires
confirmation on the next fresh install.

New graphics fixtures cover sysfs display-class detection, virtual GPU/native
firmware choices, the RTX 5060 Ti kernelopen flag, legacy/mixed-card rejection,
subsystem restrictions, trusted/correct candidate selection and mixed runtime
version/removal refusal. The live opt-in APT test authenticated current Debian and
NVIDIA repository indexes, ran the production libapt validator and resolved the
complete open driver stack from empty dpkg state: 394 packages, no toolkit, closed
kernel-module package or removals. The signed metadata/artifact checksum chain was
also verified. NVIDIA driver 620.70.10-1 was observed, not pinned.

Final regression run under Debian 13 WSL: 44 passed, six nmcli-dependent cases
skipped (50 total), with the opt-in native systemd fixture enabled. ShellCheck at
warning level and Bash/Python syntax checks passed. No host driver installation
or physical-account database change was used for this follow-up validation.

These are dependency/support checks, not GPU runtime validation. No physical
NVIDIA DKMS installation, Secure Boot enrollment or RTX 5060 Ti X11 boot has been
tested yet. NVIDIA/Intel/AMD physical-hardware acceptance remains pending.

## Portal lifecycle repair: direct fresh-VM verification

Root cause confirmed on the fresh VM: no active graphical-session.target during
Cinnamon/LightDM X11, plus missing XApp PartOf linkage. A native session target,
LightDM wrapper around Debian's unchanged Xsession and XApp drop-in correct the
startup/shutdown lifecycle. LightDM needed one reboot to load its new wrapper.

After reboot the graphical targets were active and all portals succeeded. The user
then completed two normal logout/login cycles and exercised the Gear Lever chooser.
Direct SSH inspection of the complete journal showed clean portal stops before
graphical target teardown and fresh successful starts after each login. No failed
user units remained and the portal's expected blue accent tuple was retained.
No blanket exit-status success override or automatic reset-failed was used.

All 41 standard tests passed on the actual VM; the additional isolated native
systemd lifecycle fixture also passed. ShellCheck warning checks and systemd target
syntax validation passed in Debian 13 WSL. Earlier Windows-only skip limitations
for Notepadqq shell integration are now covered by actual Linux runs. These
results resolve this logout/login defect, while remaining visual/interactive
acceptance checks still apply.

Final direct run: 42 tests passed with the native systemd fixture enabled; the
updated installed verifier reported zero failures, including graphical-session
activity, failed system/user-unit checks, original artwork, portal accent response
and 3,072 cursor loads. Updated source/docs were persisted on the VM, the targeted
repair reran successfully, and the continuation completed for the new implementation
signature. Temporary SSH test authorization was removed afterward.

## Subsequent user-run fresh VM results

The fresh console installation reached graphical first-login continuation, then
completed after the Notepadqq discovery fix. The subsequent menu repair was
confirmed by the user and Gear Lever JSON shows plain Notepadqq with GithubUpdater.
The deployed verifier reported zero failures, including the expected blue accent
tuple and 3,072 native cursor loads. The migrated NetworkManager connection is
connected and DNS resolves. The system failed-unit list is empty.

A separate failed-user-unit listing revealed xdg-desktop-portal-gtk.service failed;
the earlier verifier did not inspect failed units. The local verifier now includes
both failed-unit checks. Diagnosis awaits the unit status/journal; do not treat the
old zero-failure result as complete portal/backend acceptance. Visual and
interactive checks are not yet confirmed.

Follow-up user output shows the GTK portal active/running after a successful
restart. Its journal contains an earlier status-1 exit but no diagnostic cause.
Record this as a recovered failure with unexplained cause, rather than a persistent
backend failure or a proven startup race. Flatpak file chooser and next-login
stability checks remain outstanding.

## Earlier development environment validation

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
