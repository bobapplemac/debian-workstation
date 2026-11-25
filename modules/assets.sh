#!/bin/bash
assets_main() (
    set -Eeuo pipefail
    work=$(mktemp -d /var/tmp/debian-workstation-assets.XXXXXX)
    cleanup_assets() {
        rm -rf -- "$work"
        if [[ ${stage:-} == /usr/share/icons/.dw-* && -d $stage ]]; then rm -rf -- "$stage"; fi
    }
    trap cleanup_assets EXIT
    trap 'exit 130' INT
    trap 'exit 143' HUP TERM
    # Untrusted proprietary formats are parsed and converted as the desktop user.
    chown "$DESKTOP_USER:" "$work"
    theme=Adwaita
    current=no
    if [[ -n $CURSOR_ARCHIVE ]]; then
        archive_sha=$(sha256sum "$CURSOR_ARCHIVE" | cut -d' ' -f1)
        current=yes
        for name in Windows-Aero-Light Windows-Black; do
            [[ -f /usr/share/icons/$name/.debian-workstation && $(cat "/usr/share/icons/$name/.debian-workstation") == "$archive_sha" ]] || current=no
        done
    fi
    if [[ $current == yes ]]; then
        log 'Cursor themes already match the input archive; skipping conversion and download.'
        theme=Windows-Aero-Light
        python3 "$DW_ROOT/scripts/cursors/native.py"
    elif [[ -n $CURSOR_ARCHIVE ]]; then
        for name in Windows-Aero-Light Windows-Black; do
            target=/usr/share/icons/$name
            [[ ! -L $target ]] || die "Refusing cursor theme symlink: $target"
            [[ ! -e $target || -f $target/.debian-workstation ]] || die "Existing unmanaged cursor theme: $target"
        done
        apt_install python3-pil libxcursor1 libfuse2t64
        install -o "$DESKTOP_USER" -m 0600 "$CURSOR_ARCHIVE" "$work/cursors.zip"
        as_user python3 "$DW_ROOT/scripts/safe-zip.py" "$work/cursors.zip" "$work/microsoft"
        download https://github.com/yuzujr/ani2xcursor/releases/download/v1.6.0/ani2xcursor-v1.6.0-linux-x86_64.AppImage "$work/converter"
        printf '%s  %s\n' 9ae4c9855061622e6007bf5f2d1f0713c56daf8451e239b843d00389b6235b6b "$work/converter" | sha256sum -c -
        chmod 0755 "$work/converter"
        as_user bash "$DW_ROOT/scripts/cursors/build.sh" "$DW_ROOT" "$work"
        for name in Windows-Aero-Light Windows-Black; do
            target=/usr/share/icons/$name
            [[ ! -L $target ]] || die "Refusing cursor theme symlink: $target"
            [[ ! -e $target || -f $target/.debian-workstation ]] || die "Existing unmanaged cursor theme: $target"
            # Retain previous managed theme until the replacement is fully built and validated.
            stage=$(mktemp -d "/usr/share/icons/.dw-$name.XXXXXX")
            cp -a "$work/themes/$name/." "$stage/"
            printf '%s\n' "$archive_sha" > "$stage/.debian-workstation"
            chown -hR root:root "$stage"
            chmod -R go-w "$stage"
            if [[ -d $target ]]; then
                previous=$(mktemp -d "/usr/share/icons/$name.previous.XXXXXX")
                mv -T "$target" "$previous"
            fi
            mv -T "$stage" "$target"
            stage=''
            update-alternatives --install /usr/share/icons/default/index.theme x-cursor-theme "$target/cursor.theme" 50
        done
        theme=Windows-Aero-Light
        update-alternatives --set x-cursor-theme /usr/share/icons/Windows-Aero-Light/cursor.theme
        python3 "$DW_ROOT/scripts/cursors/native.py"
        python3 "$DW_ROOT/scripts/cursors/thumbnails.py"
    elif [[ -f /usr/share/icons/Windows-Aero-Light/.debian-workstation ]]; then
        theme=Windows-Aero-Light
    else
        log 'Using native Adwaita cursors; Windows cursor archive was not supplied.'
    fi
    printf '%s\n' "$theme" > /var/lib/debian-workstation/cursor-theme
    python3 "$DW_ROOT/scripts/files.py" greeter "$theme"
    if [[ $INSTALL_CORE_FONTS == yes ]]; then
        # contrib is already part of the reference base. Do not rewrite its repositories.
        apt-cache show ttf-mscorefonts-installer >/dev/null 2>&1 || die 'Enable Debian trixie contrib to install Core Fonts, or set INSTALL_CORE_FONTS=no.'
        apt_install ttf-mscorefonts-installer fontconfig
    fi
    if [[ -n $FONT_ARCHIVE ]]; then
        install -o "$DESKTOP_USER" -m 0600 "$FONT_ARCHIVE" "$work/fonts.zip"
        as_user python3 "$DW_ROOT/scripts/safe-zip.py" "$work/fonts.zip" "$work/source"
        as_user mkdir -p "$work/fonts"
        as_user python3 "$DW_ROOT/scripts/fonts/select.py" "$work"
        install -d -m 0755 /usr/local/share/fonts/windows-supplemental
        while IFS= read -r -d '' font; do
            target=/usr/local/share/fonts/windows-supplemental/$(basename "$font")
            [[ ! -e $target ]] || cmp -s "$font" "$target" || die "Existing different supplemental font: $target"
            atomic_install "$font" "$target"
        done < <(find "$work/fonts" -maxdepth 1 -type f -print0)
        fc-cache -f
    fi
)
