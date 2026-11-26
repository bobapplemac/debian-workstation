# Fresh-install acceptance procedure

Status: **initial implementation ready for a controlled fresh-VM trial, not
release/production validated**. Do not reinstall the original R&D workstation.
Use a genuinely new disposable VMware VM and the console/server ISO created by
debian-netinst-customizer. Keep its VM console available during networking tests.
The disposable integration VM used in development already had the customized
desktop; its successful module/session tests do not satisfy this acceptance gate.

## Preparation

1. Build/install the companion's Debian 13 amd64 console profile. Record companion
   revision, ISO checksum, VM display/scaling, boot mode and whether VLAN was used.
2. Confirm working Internet/DNS, Debian Trixie/security sources and root access.
   The reference base creates root only. A regular account and sudo are also
   supported; in that case the installer chooses that logged-in regular account.
3. Transfer this workstation checkout/archive to the VM. Before publishing, use
   local files; main/raw URLs will not contain unpublished development code.
4. Optional: run the two main-branch Windows PowerShell exporters from the README
   and copy their ZIP outputs into `debian-workstation/input/`. Do not put them in
   a Git commit or public test log. For the first trial, also test missing ZIPs.

## Provision

```bash
cd debian-workstation
bash install.sh
```

From root, choose/create a regular workstation account and set its password via
the terminal. From a regular account, verify sudo authentication succeeds and the
same account is selected. Check the passwordless-sudo option is **off** by default.
For a new account, enter Full Name in the standard adduser questions and confirm
that name appears on the greeter. On physical GPU hardware, test the graphics offer
and explicit decline path; a virtual GPU should retain its existing guest driver.
See [graphics acceptance](graphics.md) for NVIDIA open-module, Secure Boot and
RTX 5060 Ti boot checks, which require real hardware.
On an older NVIDIA card, verify that a separate proprietary-driver offer appears
only when Debian's manifest supports it. Test decline, NVIDIA_LEGACY=no and
noninteractive behavior. Never accept an incompatible older driver for Blackwell
or a mixed GPU set supported by neither stack.

Record the explicit system-phase completion message and any diagnostics. Confirm
there was no forced reboot, autologin, desktop restart or live network disconnect.
Before reboot, inspect staged networking and repository policy:

```bash
sudo cat /var/lib/debian-workstation/network/plan.json
sudo ls -l /var/lib/debian-workstation/network
apt-cache policy libadwaita-1-0 gir1.2-adw-1 cinnamon muffin nemo libgtk-4-1 libxapp1
apt-get -s full-upgrade
```

Network staging is absent if the machine already uses NetworkManager. On a fresh
reference base it should exist. Avoid publishing the plan's real addresses/DNS.
Then reboot deliberately. Reconnect SSH and verify addresses, gateways, DNS/search
and routes match the original configuration. Check exactly one manager owns each
interface. Exercise DHCP, a separate static dual-stack trial, VLAN and multiple
interfaces if those are intended deployment profiles. Unsupported hooks/profiles
must stop before source modification; use documented console recovery if needed.

## First graphical login

Select Cinnamon X11 and log in normally. Confirm the continuation terminal opens,
uses the same desktop user and completes. A native Gear Lever permission dialog
may require your response. A denied permission should leave a visible error and
working retry command. Do not interpret a missing/closed terminal as success;
inspect `~/.local/state/debian-workstation/session.log` and completion marker.

Log out/in once afterward to reload all libraries/panel styling. The completed
continuation should not run again for an unchanged implementation. Then:

```bash
bash /usr/local/lib/debian-workstation/scripts/verify.sh
bash tests/run.sh
```

The verify command reports packages, APT policy/simulation, settings, icon artwork,
portal response, grid service, Gear Lever preference/autostart and optional native
cursor loading. A response from the accent-color portal is not a visual color
acceptance result; check the blue tuple approximately (0.04706, 0.45882, 0.87059)
and actual GTK4 controls separately. Policy fallback can legitimately change it.

Check `systemctl --user is-active graphical-session.target` during Cinnamon login.
Test two normal logout/login cycles after activating the lifecycle configuration
with the planned reboot. Confirm no portal backend exit failures or XApp GTK
initialization failures at either boundary. See [session lifecycle](session-lifecycle.md).

## Visual and interactive checks

- Lock with Win+L and check the clock uses 12-hour time with AM/PM (for example,
  11:42 PM), matching the login screen and desktop. Unlock, then repeat after
  logout/login to confirm the preference persists.
- Confirm the lock screen identifies the locked account above the password box
  by full name, or username if no full name was supplied, matching the login screen.
  The desktop module initializes an empty account display name to its username;
  it preserves any supplied full name. On a multi-user test system,
  switch users and lock each session to confirm each shows its own identity.
- Confirm time and date share the same horizontal center and the name is
  centered over the entry alone, excluding the two side buttons. Check normal
  unlocking and Cinnamon's native Screensaver settings. See [native lock screen](lock-screen.md)
  for guarded package-update behavior and recovery.

- LightDM: Debian default wallpaper, Adwaita/Papirus, intended clock/layout,
  regular-user selection, manual login and matching 32px cursor theme.
- GTK3, GTK4/libadwaita and Muffin: correct glyphs, 6px upper corners on ordinary
  windows, rectangular hover, red close hover/pressed and correct maximized/tiled
  geometry. Open GNOME Terminal and Sudoku. Verify visible blue accent controls.
- Original application artwork is restored while folder/system icons remain Mint.
- Computer, Home, Trash and mounted volumes appear. Arrange icons manually;
  change resolution and confirm logical rows/columns, spacing and margins persist.
  Use one monitor at 100% scaling for the initial supported grid baseline.
- Win+L locks. Ctrl+Shift+Esc opens System Monitor. Existing custom shortcuts remain.
- Taskbar has individual titled buttons. Clock displays seconds and US date on
  two lines. Terminal background/foreground are #0C0C0C/#CCCCCC.
- Without ZIPs: clear warnings, Adwaita cursors, native fonts, remaining setup
  succeeds. With ZIPs: both cursor themes, animation, aliases, thumbnails, greeter
  cursor and supplemental font metadata selection; Debian emoji/symbol fallback
  remains intact. No proprietary artwork appears in repository/status output.
- GNOME Software lists APT and Flatpak software. System Flathub and Gear Lever work.
  Gear Lever background preference matches native portal-created autostart.
  Notepadqq opens, is managed once and has GithubUpdater configured. Latest initial
  release selection and manual update checking work. 1Password desktop/CLI launch
  without provisioning credentials or accounts.
  The Notepadqq menu label must be exactly `Notepadqq`, without a version/hash
  suffix. Existing KEEP-mode entries are repaired during its installer step;
  the original launcher is retained at
  `~/.local/state/debian-workstation/backups/notepadqq/`.

## Rerun, failures and security checks

Rerun the installer with the same configuration/input. Expect no duplicate users,
repos, shortcuts, icon overlays or app entries; no unnecessary converter/AppImage
download; no forced session/network restart. Confirm optional selected applications
are omitted when disabled. Disabling an install option does not uninstall existing
applications or revoke a previously granted sudo rule; those require deliberate
administrator actions. Missing input on a later run retains previously managed
Windows themes when installed, rather than uninstalling them.

Check preservation with a harmless unrelated CSS rule, custom keybinding and INI
value. Edited project-owned assets must stop instead of discarding user edits.
Exercise interrupted/error session continuation and unchanged next-login behavior.
Test root account creation through the console and sudo authentication through a
real terminal, including an account lacking sudo permission.

Run the isolated native APT tests for lower/higher security-version scenarios and
the native nmcli/transaction tests. Inspect the real candidate audit and notification
after a changed package inventory. Validate a coherent native library-family
reversion on a disposable clone if needed; this can reduce Mint accent appearance.
Existing security-update configuration must remain unchanged.

Record observed versions, test results and real screenshots (with private details
removed) in a new validation entry. Only after a successful genuine fresh install
and required graphical checks should release preparation begin. No push/release
or publication is authorized by this acceptance procedure alone.
