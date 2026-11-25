# NetworkManager migration and recovery

The reference installer uses ifupdown. Its default is DHCP Ethernet; its VLAN
extension writes dotted names with a physical parent. Static netcfg configurations
can also be encountered after installer/manual selection. This project is a
strict translator for those configurations, not a general network framework.

Accepted input: loopback, `auto`/`allow-hotplug`, multiple Ethernet interfaces,
`inet dhcp/static/manual`, `inet6 auto/dhcp/static/manual`, static CIDR or IPv4
netmask, gateways, DNS nameservers/search, dotted VLAN IDs 1–4094 with an optional
matching `vlan-raw-device`, and simple `up`/`post-up ip route add PREFIX via GW
[metric N]` (including `ip -6 route add`). Native nmcli offline rendering validates
the resulting keyfiles before staging. MAC DHCPv4 client identity follows the
base installer to help retain existing leases.

Unknown stanza methods/options, arbitrary shell hooks, down hooks, policy routing,
multiple addresses per family, wireless/bond/bridge/VPN configuration, conflicting
existing NM profiles, unsafe includes and duplicate stanzas stop with diagnostics.
Translate such cases explicitly to NetworkManager first. No unsupported option
is silently discarded. Source files can include paths/globs within /etc/network;
symlink/recursive/outside includes are rejected. Include files remain intact.

1. Inspect all input before package installation. An existing NM connection bound
   to a migrated interface, or an unbound Ethernet/VLAN profile that may compete,
   stops migration. This intentionally requires manual reconciliation rather than
   guessing which profile to replace. Existing unrelated NM profiles are retained.
2. Install NetworkManager. Debian's ifupdown plugin must leave declared interfaces
   unmanaged; an existing `managed=true` setting is rejected. Render native
   `nmcli --offline connection add` keyfiles into root-only persistent staging.
3. Save source content hashes, exact original backups and staged profile hashes
   under `/var/lib/debian-workstation/network` (mode 0700). No live interface is
   brought down, deleted or activated. Enable a oneshot boot unit.
4. At the next planned reboot, before networking.service and NetworkManager start,
   verify that the source and staged profiles are unchanged. Copy the validated
   0600 profiles, then atomically replace the main interfaces file with loopback
   only. Its original include files remain on disk but are no longer referenced.
   NetworkManager now owns the migrated interfaces; ifupdown owns only loopback.
5. A transaction marker permits recovery if interrupted before completion. A
   failed commit restores the original main file and removes unchanged staged
   profiles. If an administrator has changed a profile mid-transaction, stop and
   use console recovery instead of overwriting it. Completed migration is not
   repeated on ordinary installer reruns; NM becomes authoritative.

SSH is retained throughout staging. The actual change is at reboot, where an SSH
disconnect is expected. Reconnect afterward. Keep a VMware console available;
neither offline validation nor a remembered DHCP client ID guarantees upstream
DHCP/DNS availability. Native rendering, transaction and recovery tests are not
equivalent to a live fresh-machine migration.

## Console recovery

If connectivity does not return after reboot:

```bash
sudo systemctl stop NetworkManager
sudo systemctl disable debian-workstation-network.service
sudo ls -l /var/lib/debian-workstation/network
sudo cat /var/lib/debian-workstation/network/plan.json
```

Restore the `backup-_etc_network_interfaces` file to `/etc/network/interfaces`.
Included source files were retained untouched; verify them against the backup
hashes and restore any deliberately changed include from its matching backup.
Remove only the `dw-INTERFACE.nmconnection` files listed in plan.json from
`/etc/NetworkManager/system-connections`, after checking that they are still the
project-generated files. Move aside the `committed`/`committing` markers and plan
for review. With the original ifupdown configuration restored, run:

```bash
sudo systemctl restart networking
ip address
ip route
getent hosts deb.debian.org
```

Inspect `journalctl -b -u debian-workstation-network -u NetworkManager -u networking`
and the interface's addressing/routes/DNS. Fix the unsupported/changed configuration,
then rerun the network module to restage. Do not start both owners for the same
interface. Do not run `ifdown` over the only SSH connection as a recovery experiment.

Reference: [native nmcli offline operations](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nmcli.html),
[keyfile format](https://networkmanager.pages.freedesktop.org/NetworkManager/NetworkManager/nm-settings-keyfile.html).
