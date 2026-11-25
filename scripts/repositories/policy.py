#!/usr/bin/env python3
"""Inspect libapt's real candidates; no home-grown Debian version comparator."""
import json
from pathlib import Path
import sys

ALLOW = set('mint-themes mint-x-icons mint-y-icons mint-cursor-themes libadwaita-1-0 gir1.2-adw-1 libadwaita-1-dev libadwaita-1-doc libadwaita-1-examples xdg-desktop-portal-xapp xapp-symbolic-icons'.split())
LIBRARY = set('libadwaita-1-0 gir1.2-adw-1 libadwaita-1-dev libadwaita-1-doc libadwaita-1-examples'.split())
STATE = Path('/var/lib/debian-workstation')

def main(action):
    import apt
    cache=apt.Cache()
    problems=[]; report=[]; fallback=False
    for pkg in cache:
        candidate=pkg.candidate
        if candidate and any(o.site=='fastly.linuxmint.io' for o in candidate.origins) and pkg.name not in ALLOW:
            problems.append(f'Unapproved Mint candidate: {pkg.name}')
        if pkg.name in ALLOW and candidate:
            print(pkg.name, 'installed='+str(pkg.installed.version if pkg.installed else None), 'candidate='+candidate.version,
                  'origins='+','.join(o.site+'/'+o.archive for o in candidate.origins))
        if pkg.name in LIBRARY and candidate:
            security=[v for v in pkg.versions if any(o.origin=='Debian' and o.codename=='trixie-security' for o in v.origins)]
            if security:
                # APT's candidate must actually be one of the security versions.
                if candidate.version not in {v.version for v in security}: problems.append(f'Debian security candidate masked for {pkg.name}')
                fallback=True
            if pkg.installed:
                debian=sorted({v.version for v in pkg.versions if any(o.origin=='Debian' for o in v.origins)})
                report.append({'package':pkg.name,'installed':pkg.installed.version,'candidate':candidate.version,'debian':debian})
    if problems: raise ValueError('; '.join(problems))
    if action=='security-fallback': return 0 if fallback else 1
    if action=='audit':
        STATE.mkdir(parents=True,exist_ok=True)
        status={'security_fallback':fallback,'packages':report,
                'notice':'Mint patch security equivalence is not established by Debian version ordering. Review Debian source updates and Mint changelogs.'}
        text=json.dumps(status,indent=2)+'\n'
        previous=STATE/'security-status.json'
        if previous.exists() and previous.read_text()!=text:
            print('SECURITY REVIEW: libadwaita package inventory changed; inspect /var/lib/debian-workstation/security-status.json',file=sys.stderr)
        temp=STATE/'security-status.tmp'; temp.write_text(text); temp.chmod(0o644); temp.replace(previous)
    return 0

if __name__=='__main__':
    try: sys.exit(main(sys.argv[1] if len(sys.argv)>1 else 'audit'))
    except (ValueError,OSError) as e: sys.exit(str(e))
