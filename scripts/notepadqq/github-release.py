#!/usr/bin/env python3
"""Fetch latest stable Notepadqq with GitHub's asset digest; reject retagged bytes."""
import hashlib
import json
from pathlib import Path
import re
import sys
import urllib.parse
import urllib.request
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from files import write

def response(url):
    return urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'debian-workstation'}),timeout=60)

def main(target):
    with response('https://api.github.com/repos/notepadqq/notepadqq/releases/latest') as r:
        data=r.read(2*1024*1024+1)
    if len(data)>2*1024*1024: raise ValueError('Release metadata too large')
    release=json.loads(data)
    if release.get('prerelease') or release.get('draft'): raise ValueError('Latest release is not stable')
    matches=[a for a in release['assets'] if re.fullmatch(r'notepadqq-.*-linux-x86_64\.AppImage',a['name'])]
    if len(matches)!=1: raise ValueError('Expected one official x86_64 Notepadqq AppImage')
    asset=matches[0]; digest=asset.get('digest','')
    if not re.fullmatch(r'sha256:[0-9a-f]{64}',digest): raise ValueError('Upstream asset has no SHA256 digest; review upstream metadata before installing')
    url=asset['browser_download_url']
    if not url.startswith('https://github.com/notepadqq/notepadqq/releases/download/'):
        raise ValueError('Unexpected release download origin')
    receipts=Path.home()/'.local/state/debian-workstation/notepadqq-downloads.json'
    known=json.loads(receipts.read_text()) if receipts.exists() else {}
    if url in known and known[url]!=digest: raise ValueError('Upstream changed the checksum for an observed release URL; manual review required')
    sha=hashlib.sha256(); total=0
    with response(url) as source, Path(target).open('xb') as output:
        while chunk:=source.read(1024*1024):
            total+=len(chunk)
            if total>512*1024*1024: raise ValueError('AppImage exceeds 512 MiB')
            sha.update(chunk); output.write(chunk)
    if sha.hexdigest()!=digest.split(':')[1]: raise ValueError('Notepadqq checksum mismatch')
    known[url]=digest
    write(receipts,json.dumps(known,indent=2)+'\n',0o600)
    print(f'Verified latest stable Notepadqq {release["tag_name"]}: {digest}')

if __name__=='__main__':
    try: main(sys.argv[1])
    except (OSError,ValueError,KeyError) as e: sys.exit(str(e))
