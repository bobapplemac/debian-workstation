#!/usr/bin/env python3
"""Apply the reference settings through the real Cinnamon session bus."""
import sys
from gi.repository import Gio, GLib

def settings(schema, path=None):
    source=Gio.SettingsSchemaSource.get_default()
    definition=source.lookup(schema,True)
    if definition is None: raise ValueError(f'Missing GSettings schema: {schema}')
    return Gio.Settings.new_full(definition,None,path)

def set_values(schema, values, path=None):
    s=settings(schema,path)
    for key,value in values.items():
        if not s.get_property('settings-schema').has_key(key): raise ValueError(f'Unsupported settings key: {schema} {key}')
        variant=GLib.Variant(s.get_value(key).get_type_string(),value)
        if not s.set_value(key,variant): raise ValueError(f'Unable to set {schema} {key}')

def main(theme):
    set_values('org.cinnamon.desktop.interface',{'gtk-theme':'Mint-Y-Blue','icon-theme':'Mint-Y-Blue','cursor-theme':theme,'cursor-size':32})
    set_values('org.gnome.desktop.interface',{'cursor-theme':theme,'cursor-size':32})
    set_values('org.cinnamon.theme',{'name':'Mint-Y-Dark-Blue'})
    set_values('org.cinnamon.desktop.wm.preferences',{'button-layout':':minimize,maximize,close'})
    set_values('org.nemo.desktop',dict.fromkeys(['computer-icon-visible','home-icon-visible','trash-icon-visible','volumes-visible'],True))
    set_values('org.gnome.software',{'allow-updates':True,'download-updates':False,'download-updates-notify':True})
    profile=settings('org.gnome.Terminal.ProfilesList').get_string('default')
    set_values('org.gnome.Terminal.Legacy.Profile',{'use-theme-colors':False,'background-color':'#0C0C0C','foreground-color':'#CCCCCC'},
               f'/org/gnome/terminal/legacy/profiles:/:{profile}/')
    schema='org.cinnamon.desktop.keybindings'
    # Preserve other lock shortcuts while assigning the requested key.
    s=settings(schema+'.media-keys'); bindings=list(s.get_strv('screensaver'))
    for binding in ('<Super>l','<Control><Alt>l','XF86ScreenSaver'):
        if binding not in bindings: bindings.append(binding)
    set_values(schema+'.media-keys',{'screensaver':bindings})
    set_values(schema,{'looking-glass-keybinding':[]})
    s=settings(schema); ids=[i for i in s.get_strv('custom-list') if i!='__dummy__']
    def custom(identifier): return settings(schema+'.custom-keybinding',f'/org/cinnamon/desktop/keybindings/custom-keybindings/{identifier}/')
    identifier=next((i for i in ids if custom(i).get_string('command')=='gnome-system-monitor'),None)
    if identifier is None:
        n=0
        while f'custom{n}' in ids: n+=1
        identifier=f'custom{n}'; ids.append(identifier)
    set_values(schema+'.custom-keybinding',{'name':'System Monitor','command':'gnome-system-monitor','binding':['<Primary><Shift>Escape']},
               f'/org/cinnamon/desktop/keybindings/custom-keybindings/{identifier}/')
    set_values(schema,{'custom-list':ids+['__dummy__']})
    set_values(schema,{'custom-list':ids})
    Gio.Settings.sync()
    bus=Gio.bus_get_sync(Gio.BusType.SESSION,None)
    script='''(() => {
      const manager = imports.ui.appletManager;
      const clocks = manager.getRunningInstancesForUuid("calendar@cinnamon.org");
      if (!clocks.length) throw new Error("Calendar applet is not running; retry after Cinnamon starts");
      clocks.forEach(clock => {
        clock.settings.setValue("custom-format", "%-I:%M:%S %p%n%-m/%-d/%Y");
        clock.settings.setValue("use-custom-format", true);
        clock._onSettingsChanged();
      });
      manager.getRunningInstancesForUuid("grouped-window-list@cinnamon.org").forEach(a => {
        a.settings.setValue("group-apps", false); a.settings.setValue("title-display", 3);
      });
      return "Workstation panel preferences applied";
    })()'''
    result=bus.call_sync('org.Cinnamon','/org/Cinnamon','org.Cinnamon','Eval',GLib.Variant('(s)',(script,)),None,Gio.DBusCallFlags.NONE,30000,None).unpack()
    if not result[0]: raise ValueError(f'Cinnamon panel configuration failed: {result[1]}')
    print(result[1])

if __name__=='__main__':
    try: main(sys.argv[1])
    except (ValueError,GLib.Error) as e: sys.exit(str(e))
