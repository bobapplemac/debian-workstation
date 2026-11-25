#!/usr/bin/python3
"""Use reviewed application artwork in the installed Mint-Y theme."""
import argparse
import configparser
import fcntl
from functools import lru_cache
import os
from pathlib import Path
import subprocess
import tempfile

from gi.repository import Gio, GLib

SYSTEM_ICONS = Path('/usr/share/icons')
MINT = SYSTEM_ICONS / 'Mint-Y'
HICOLOR = SYSTEM_ICONS / 'hicolor'
DATA = Path(GLib.get_user_data_dir())
LOCAL = DATA / 'icons' / MINT.name
STORE = DATA / 'mint-y-app-icons'
FORMATS = ('.png', '.svg', '.xpm')
# Desktop ID: (full-color icon name, desktop package, artwork package)
APPS = {
    'firefox-esr.desktop': ('firefox-esr', 'firefox-esr', 'firefox-esr'),
    'org.gnome.Calculator.desktop': ('org.gnome.Calculator', 'gnome-calculator', 'gnome-calculator'),
    'org.gnome.Evince.desktop': ('org.gnome.Evince', 'evince', 'evince'),
    'org.gnome.FileRoller.desktop': ('org.gnome.FileRoller', 'file-roller', 'file-roller'),
    'org.gnome.Gnote.desktop': ('org.gnome.Gnote', 'gnote', 'gnote'),
    'org.gnome.SoundRecorder.desktop': ('org.gnome.SoundRecorder', 'gnome-sound-recorder', 'gnome-sound-recorder'),
    'org.gnome.Totem.desktop': ('org.gnome.Totem', 'totem', 'totem-common'),
    'org.remmina.Remmina.desktop': ('org.remmina.Remmina', 'remmina', 'remmina-common'),
    'simple-scan.desktop': ('org.gnome.SimpleScan', 'simple-scan', 'simple-scan'),
}


@lru_cache
def metadata(theme):
    info = configparser.ConfigParser(interpolation=None)
    with (theme / 'index.theme').open(encoding='utf-8') as index:
        info.read_file(index)
    return info


def directories(theme):
    info = metadata(theme)
    for key in ('Directories', 'ScaledDirectories'):
        for name in info['Icon Theme'].get(key, '').split(','):
            name = name.strip()
            path = Path(name)
            if name and not path.is_absolute() and '..' not in path.parts:
                yield path, info[name]


def variants():
    return [MINT] + sorted(
        theme for theme in SYSTEM_ICONS.glob('Mint-Y-*')
        if (theme / 'index.theme').is_file()
        and MINT.name in metadata(theme)['Icon Theme'].get('Inherits', '').replace(' ', '').split(',')
    )


@lru_cache
def package_files(package):
    query = subprocess.run(['dpkg-query', '-L', package], capture_output=True, text=True)
    return {Path(line) for line in query.stdout.splitlines() if line.startswith('/')} if query.returncode == 0 else set()


def choose_artwork(artwork, pixels):
    def priority(item):
        size, path = item
        return (
            0 if size == pixels else 1 if size is None else 2,
            abs(size - pixels) if size is not None else 0,
            -(size or 0),
            FORMATS.index(path.suffix),
            path,
        )
    return min(artwork, key=priority)[1]


def discover():
    slots = {
        path: attrs.getint('Size') * attrs.getint('Scale', 1)
        for path, attrs in directories(MINT)
        if path.parts[0] == 'apps' and attrs.get('Type') == 'Fixed'
    }
    if not slots:
        raise ValueError('No fixed Mint-Y application slots found.')
    stock = variants()
    entries = {entry.get_id(): entry for entry in Gio.AppInfo.get_all()
               if isinstance(entry, Gio.DesktopAppInfo)}
    links = {}
    originals = {}
    for desktop_id, (name, desktop_package, artwork_package) in APPS.items():
        entry = entries.get(desktop_id)
        if entry is None:
            continue
        if (entry.get_nodisplay() or name.endswith('-symbolic') or entry.get_string('Icon') != name
                or Path(entry.get_filename()) not in package_files(desktop_package)):
            print(f'Skipping {desktop_id}: desktop entry does not match the reviewed package and icon.')
            continue
        filenames = [name + ext for ext in FORMATS]
        if not any((MINT / slot / filename).is_file() for slot in slots for filename in filenames):
            continue
        if any((theme / directory / filename).is_file()
               for theme in [*stock, HICOLOR] for directory, _ in directories(theme)
               if (theme == MINT and directory not in slots)
               or (theme != MINT and theme != HICOLOR)
               or (theme == HICOLOR and directory.name != 'apps')
               for filename in filenames):
            print(f'Skipping {desktop_id}: icon name is also used outside the shared app slots.')
            continue
        owned = package_files(artwork_package)
        artwork = []
        for directory, attrs in directories(HICOLOR):
            if directory.name != 'apps' or 'symbolic' in directory.parts:
                continue
            for filename in filenames:
                path = HICOLOR / directory / filename
                if path in owned and path.is_file() and path.resolve() in owned:
                    size = None if path.suffix == '.svg' else attrs.getint('Size') * attrs.getint('Scale', 1)
                    artwork.append((size, path))
        if not artwork:
            print(f'Skipping {desktop_id}: no package-owned full-color artwork found.')
            continue
        originals[desktop_id] = {path.resolve() for _, path in artwork}
        for slot, pixels in slots.items():
            source = choose_artwork(artwork, pixels)
            links[slot / (name + source.suffix)] = source
    return links, originals


def link_target(path):
    return Path(os.readlink(path)) if path.is_symlink() else None


def sync(links):
    # Each managed overlay link points to its corresponding path in STORE.
    # This identifies ownership even after a source package is removed.
    if any(path.is_symlink() for path in (STORE, STORE / 'apps', LOCAL, LOCAL / 'apps')):
        raise ValueError('Expected real directories for the artwork store and theme overlay.')
    STORE.mkdir(parents=True, exist_ok=True)
    with (STORE / '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        current = {p.relative_to(LOCAL) for p in (LOCAL / 'apps').glob('*/*')
                   if not p.parent.is_symlink() and link_target(p) == STORE / p.relative_to(LOCAL)}
        for relative in links:
            dest = LOCAL / relative
            stored = STORE / relative
            if dest.parent.is_symlink() or any(p.is_symlink() for p in (stored.parent, stored.parent.parent)):
                raise ValueError(f'Expected real directories for {relative}')
            for extension in FORMATS:
                other = dest.with_suffix(extension)
                if os.path.lexists(other) and other.relative_to(LOCAL) not in current:
                    raise ValueError(f'Existing unmanaged icon: {other}')
            if stored.exists() and not stored.is_symlink():
                raise ValueError(f'Existing non-link in the artwork store: {stored}')
        changed = False
        for relative, source in sorted(links.items()):
            stored = STORE / relative
            if link_target(stored) != source:
                stored.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(dir=stored.parent) as staging:
                    replacement = Path(staging) / 'link'
                    replacement.symlink_to(source)
                    replacement.replace(stored)
                changed = True
            if relative not in current:
                dest = LOCAL / relative
                dest.parent.mkdir(parents=True, exist_ok=True)
                dest.symlink_to(stored)
                changed = True
        stale = current - links.keys()
        for relative in sorted(stale):
            (LOCAL / relative).unlink()
        for stored in (STORE / 'apps').glob('*/*'):
            if not stored.parent.is_symlink() and stored.is_symlink() and stored.relative_to(STORE) not in links:
                stored.unlink()
        if changed or stale:
            os.utime(LOCAL)
        return changed or bool(stale)


def verify(links, originals):
    import gi
    gi.require_version('Gtk', '3.0')
    from gi.repository import Gtk

    if not Gtk.init_check()[0]:
        raise ValueError('GTK verification needs access to the Cinnamon display.')
    if not originals:
        raise ValueError('No eligible applications to verify.')
    for relative, source in links.items():
        overlay = LOCAL / relative
        if link_target(overlay) != STORE / relative or overlay.resolve() != source.resolve():
            raise ValueError(f'Overlay differs from the desired link: {overlay}')

    samples = [(size, scale) for scale in (1, 2)
               for size in (16, 22, 24, 32, 48, 64, 96, 128, 256)]
    stock_icons = ('folder', 'drive-harddisk', 'text-x-generic', 'folder-remote',
                   'document-open', 'network-wireless-signal-excellent-symbolic',
                   'preferences-system', 'blueman')
    controls = ('window-close', 'window-minimize', 'window-maximize', 'window-restore')

    def filename(info):
        return Path(info.get_filename()) if info and info.get_filename() else None

    for variant in variants():
        live = Gtk.IconTheme.new()
        live.set_custom_theme(variant.name)
        stock = Gtk.IconTheme.new()
        stock.set_search_path([path for path in live.get_search_path()
                               if not Path(path).is_relative_to(Path.home())
                               and Path(path) != DATA / 'icons'])
        stock.set_custom_theme(variant.name)
        for size, scale in samples:
            for desktop_id, owned in originals.items():
                icon = Gio.DesktopAppInfo.new(desktop_id).get_icon()
                info = live.lookup_by_gicon_for_scale(icon, size, scale, 0)
                path = filename(info)
                if not path or not path.is_relative_to(LOCAL) or path.resolve() not in owned:
                    raise ValueError(f'{variant.name} {desktop_id} {size}@{scale}: got {path}')
                info.load_icon()
            for name in stock_icons:
                before = filename(stock.lookup_icon_for_scale(name, size, scale, 0))
                after = filename(live.lookup_icon_for_scale(name, size, scale, 0))
                if not before or before != after:
                    raise ValueError(f'{variant.name} {name} {size}@{scale}: {before} -> {after}')
            for stem in controls:
                name = stem + '-symbolic'
                path = filename(live.lookup_icon_for_scale(name, size, scale, 0))
                if path != LOCAL / 'actions' / 'symbolic' / (name + '.svg'):
                    raise ValueError(f'{variant.name} {name} {size}@{scale}: got {path}')
        print(f'{variant.name}: {len(originals)} apps and 12 protected icons passed at {len(samples)} size/scale pairs.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('apply', 'verify', 'remove'))
    args = parser.parse_args()
    if os.geteuid() == 0:
        parser.error('Run as the desktop user.')
    try:
        if args.action == 'remove':
            print('Removed managed app overrides.' if sync({}) else 'No managed app overrides.')
            return
        links, originals = discover()
        if args.action == 'verify':
            verify(links, originals)
        else:
            changed = sync(links)
            print(f'{"Applied" if changed else "Already current"}: {len(links)} links for {len(originals)} applications.')
        for desktop_id in originals:
            print(f'  {desktop_id}')
    except (OSError, ValueError, GLib.Error) as error:
        parser.exit(1, f'{parser.prog}: {error}\n')


if __name__ == '__main__':
    main()
