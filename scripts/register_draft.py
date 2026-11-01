"""Register one prepared draft while BCUT is closed; preserve existing entries."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import uuid


def register(source, guid, destination, backup_dir):
    guid = str(uuid.UUID(guid)).upper()
    source, destination = Path(source).resolve(), Path(destination).resolve()
    folder, target = source / guid, destination / guid
    if source == destination or target.exists():
        raise ValueError('Destination must be new; existing drafts are never replaced.')
    if not (folder / '.dsh-created').is_file() or not list(folder.glob('*.bjson')):
        raise ValueError('Source is not a generated draft.')
    rows = list(csv.reader(io.StringIO(subprocess.check_output(
        ['tasklist', '/FI', 'IMAGENAME eq BCUT.exe', '/FO', 'CSV', '/NH'],
        text=True, errors='replace'))))
    if any(row and row[0].lower() == 'bcut.exe' for row in rows):
        raise RuntimeError('Close BCUT before registering, to prevent index overwrite.')
    entry = next(x for x in json.loads((source/'draftInfo.json').read_text(encoding='utf-8'))['draftInfos'] if x['id'] == guid)
    index = destination / 'draftInfo.json'
    original = index.read_bytes() if index.exists() else None
    data = json.loads(original) if original is not None else {'draftInfos': []}
    if any(x['id'] == guid for x in data['draftInfos']):
        raise ValueError('GUID already registered.')
    backup = Path(backup_dir).resolve() / ('before-' + guid)
    backup.mkdir(parents=True, exist_ok=False)
    if original is not None:
        (backup/'draftInfo.json').write_bytes(original)
    (backup/'registration.json').write_text(json.dumps({
        'guid': guid, 'destination': str(destination), 'old_count': len(data['draftInfos']),
        'index_sha256': hashlib.sha256(original or b'').hexdigest()
    }, indent=2), encoding='utf-8')
    destination.mkdir(parents=True, exist_ok=True)
    shutil.copytree(folder, target)
    current = index.read_bytes() if index.exists() else None
    if current != original:
        raise RuntimeError('Index changed concurrently. New folder retained, index untouched.')
    data['draftInfos'].append(entry)
    tmp = destination / ('draftInfo.codex-' + guid + '.tmp')
    with tmp.open('x', encoding='utf-8') as out:
        json.dump(data, out, ensure_ascii=False, indent=2)
    os.replace(tmp, index)
    check = json.loads(index.read_text(encoding='utf-8'))
    assert check['draftInfos'][:-1] == (json.loads(original)['draftInfos'] if original else [])
    print(json.dumps({'guid': guid, 'folder': str(target), 'backup': str(backup),
                      'draft_count': len(check['draftInfos'])}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--source', required=True)
    p.add_argument('--guid', required=True)
    p.add_argument('--destination', required=True)
    p.add_argument('--backup-dir', required=True)
    a = p.parse_args()
    register(a.source, a.guid, a.destination, a.backup_dir)
