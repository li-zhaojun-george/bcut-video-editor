"""Check the public package for local media, personal paths and template residue."""
import argparse
import json
from pathlib import Path
import re
import subprocess


ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {'README.md', 'SKILL.md', 'LICENSE', 'requirements.txt', '.gitignore'}
SKIP_DIRS = {'.git', '__pycache__', '.venv', '.pytest_cache'}


def walk_values(value, trail=''):
    if isinstance(value, dict):
        for key, child in value.items():
            yield from walk_values(child, trail + '/' + key)
    elif isinstance(value, list):
        for i, child in enumerate(value):
            yield from walk_values(child, trail + '/' + str(i))
    else:
        yield trail, value


def check(root=ROOT):
    errors = []
    files = []
    for path in sorted(root.rglob('*')):
        relative = path.relative_to(root)
        if any(part in SKIP_DIRS for part in relative.parts) or not path.is_file():
            continue
        name = relative.as_posix()
        allowed = name in ROOT_FILES or any(relative.match(pattern) for pattern in (
            'scripts/*.py', 'scripts/templates/*.json', 'scripts/catalog/*.json',
            'references/*.md', 'agents/*.yaml', 'examples/*.json', 'tests/*.py',
            '.github/workflows/*.yml'))
        if not allowed:
            errors.append(f'{name}: unexpected distribution file')
            continue
        files.append(name)
        try:
            text = path.read_text(encoding='utf-8')
        except UnicodeError:
            errors.append(f'{name}: not a UTF-8 source/document file')
            continue
        # Match concrete Windows user profiles, allowing <user> documentation.
        if re.search(r'[A-Za-z]:[/\\]+Users[/\\]+(?!<|\$|%)[^/\\\s]+', text):
            errors.append(f'{name}: concrete Windows user profile path')
        if re.search(r'gh[pousr]_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}', text):
            errors.append(f'{name}: possible credential')
        if path.suffix != '.json':
            continue
        data = json.loads(text)
        if relative.parts[:2] != ('scripts', 'templates'):
            continue
        for key, value in walk_values(data):
            field = key.rsplit('/', 1)[-1]
            if field in ('idString', 'uid', 'importTime', 'recentlyUsedTime') and value:
                errors.append(f'{name}{key}: instance metadata must be empty')
            if isinstance(value, str) and re.match(r'^[A-Za-z]:[/\\]|^[/\\]{2}', value):
                errors.append(f'{name}{key}: absolute machine path in template')
            if field in ('sourcePath', 'originalFilePath', 'originSrcPath', 'coverPath', 'cover') and value:
                errors.append(f'{name}{key}: source/cache path must be empty')
        if path.name in ('caption.json', 'audio_clip.json', 'video_clip.json', 'image_clip.json', 'builtin_clip.json'):
            if any(data['assetInfo'].get(k) for k in ('content', 'displayName', 'realMaterialId', 'srcPath', 'customInfos')):
                errors.append(f'{name}: retained source asset metadata')
            if data.get('captionText') or data.get('markSet') or data.get('markInfoMap'):
                errors.append(f'{name}: retained captions or timeline markers')
    return files, errors


def check_history(root=ROOT):
    """Check reachable local Git history without echoing private addresses."""
    result = subprocess.run(['git', 'log', '--all', '--format=%H%x00%ae%x00%ce'],
                            cwd=root, capture_output=True, text=True, encoding='utf-8')
    if result.returncode:
        return ['Git history could not be read; use a repository checkout']
    errors = []
    for line in result.stdout.splitlines():
        commit, author, committer = line.split('\x00')
        if not author.endswith('@users.noreply.github.com') or not committer.endswith('@users.noreply.github.com'):
            errors.append(f'{commit[:12]}: author/committer must use GitHub noreply before publishing')
    return errors


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--git-history', action='store_true', help='Also check reachable commit author/committer addresses')
    args = parser.parse_args()
    files, errors = check()
    if args.git_history:
        errors.extend(check_history())
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f'PASS: {len(files)} distribution files; no local media or retained template instance data')
