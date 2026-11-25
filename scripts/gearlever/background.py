#!/usr/bin/env python3
import configparser
import uuid
from pathlib import Path
from gi.repository import Gio, GLib

APP_ID = "it.mijorus.gearlever"
KEY = "fetch-updates-in-background"

# Request native autostart through the XDG Background Portal.
# Running inside the Flatpak associates the request with Gear Lever.

bus = Gio.bus_get_sync(Gio.BusType.SESSION, None)
loop = GLib.MainLoop()
result = {}

token = "gearlever_" + uuid.uuid4().hex

sender = bus.get_unique_name()[1:].replace(".", "_")

request_path = (
    "/org/freedesktop/portal/desktop/request/"
    + sender + "/" + token
)

def on_response(connection, sender_name, object_path,
                interface_name, signal_name, parameters,
                user_data):

    code, values = parameters.unpack()

    result["code"] = code
    result["values"] = values

    loop.quit()

subscription = bus.signal_subscribe(
    "org.freedesktop.portal.Desktop",
    "org.freedesktop.portal.Request",
    "Response",
    request_path,
    None,
    Gio.DBusSignalFlags.NONE,
    on_response,
    None,
)

options = {
    "handle_token": GLib.Variant("s", token),
    "reason": GLib.Variant(
        "s", "Gear Lever background updates fetch"
    ),
    "autostart": GLib.Variant("b", True),
    "background": GLib.Variant("b", True),
    "commandline": GLib.Variant(
        "as", ["gearlever", "--fetch-updates"]
    ),
}

handle = bus.call_sync(
    "org.freedesktop.portal.Desktop",
    "/org/freedesktop/portal/desktop",
    "org.freedesktop.portal.Background",
    "RequestBackground",
    GLib.Variant("(sa{sv})", ("", options)),
    GLib.VariantType.new("(o)"),
    Gio.DBusCallFlags.NONE,
    -1,
    None,
).unpack()[0]

if handle != request_path:
    raise RuntimeError(f"Unexpected portal request path: {handle}")

def on_timeout():
    loop.quit()
    return False

timeout = GLib.timeout_add_seconds(120, on_timeout)

loop.run()

bus.signal_unsubscribe(subscription)

if not result:
    raise RuntimeError("Background portal request timed out")

GLib.source_remove(timeout)

if (
    result["code"] != 0
    or not result["values"].get("background", False)
    or not result["values"].get("autostart", False)
):
    raise RuntimeError(
        f"Background autostart was not granted: {result}"
    )

# Update Gear Lever's internal configuration,
# preserving existing application and update-source settings.

path = Path(GLib.get_user_config_dir()) / "gearlever.conf"
path.parent.mkdir(parents=True, exist_ok=True)

config = configparser.ConfigParser(interpolation=None)
config.read(path)

config[config.default_section][KEY] = "yes"

with path.open("w") as file:
    config.write(file)

# Synchronize the actual GUI preference.

settings = Gio.Settings.new(APP_ID)

if not settings.set_boolean(KEY, True):
    raise RuntimeError("Unable to save Gear Lever preference")

Gio.Settings.sync()

print("Gear Lever background update checking enabled.")
print(f"Configuration: {path}")
print(f"Preference: {settings.get_boolean(KEY)}")
