"""Validate a sequential edit plan and create a new draft in a staging directory."""
import argparse
import json
import math
import os
from pathlib import Path


def number(value, label, minimum=0, integer=False):
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f'{label}: expected a finite number')
    if value < minimum or (integer and int(value) != value):
        raise ValueError(f'{label}: invalid value {value}')
    return value


def validate(plan, probe):
    for k in ('width', 'height', 'fps'):
        number(plan[k], k, 1, True)
    if not plan.get('clips'):
        raise ValueError('At least one clip is required')
    number(plan.get('original_volume_db', 0), 'original_volume_db', -120)
    duration = 0
    for i, clip in enumerate(plan['clips']):
        p = Path(clip['path'])
        if not p.is_absolute() or not p.is_file():
            raise ValueError(f'clips[{i}]: absolute existing local media path required')
        if clip.get('transition') or clip.get('start') is not None or clip.get('speed', 1) != 1 or clip.get('motion', 'none') != 'none':
            raise ValueError('This verified plan builder supports sequential clips at normal speed. Advanced effects require separate native verification.')
        if clip.get('gain_db') is not None:
            number(clip['gain_db'], 'gain_db', -120)
        if clip.get('volume_db') is not None:
            number(clip['volume_db'], 'volume_db', -120)
        info = probe(str(p))
        if info['kind'] == 'image':
            span = number(clip.get('duration_ms', 3000), 'duration_ms', 1, True)
            if not info['width'] or not info['height']:
                raise ValueError('Unreadable image: ' + str(p))
        else:
            if not info['width'] or not info['height'] or info['duration_ms'] <= 0:
                raise ValueError('Unreadable video or ffprobe unavailable: ' + str(p))
            start = number(clip.get('trim_in', 0), 'trim_in', 0, True)
            end = number(clip.get('trim_out', info['duration_ms']), 'trim_out', 1, True)
            if not start < end <= info['duration_ms']:
                raise ValueError('Video trim must be inside source duration')
            span = end - start
        duration += span
    for cap in plan.get('captions', []):
        start = number(cap['start'], 'caption.start', 0, True)
        end = number(cap['end'], 'caption.end', 1, True)
        if not cap.get('text') or not start < end <= duration:
            raise ValueError('Caption must have text and lie inside the video timeline')
        for axis in ('x', 'y'):
            if abs(number(cap.get(axis, 0), 'caption.'+axis, -1)) > 1:
                raise ValueError('Caption coordinates must be between -1 and 1')
        if number(cap.get('opacity', 1), 'caption.opacity') > 1:
            raise ValueError('Caption opacity must be between 0 and 1')
        number(cap.get('scale', .56), 'caption.scale', .01)
    for audio in plan.get('audio', []):
        p = Path(audio['path'])
        if not p.is_absolute() or not p.is_file():
            raise ValueError('Audio requires an absolute existing local path')
        info = probe(str(p))
        start = number(audio.get('start', 0), 'audio.start', 0, True)
        trim_in = number(audio.get('trim_in', 0), 'audio.trim_in', 0, True)
        trim_out = number(audio.get('trim_out', info['duration_ms']), 'audio.trim_out', 1, True)
        if not trim_in < trim_out <= info['duration_ms'] or start+trim_out-trim_in > duration:
            raise ValueError('Audio must fit source duration and video timeline; specify trim_out')
        number(audio.get('volume_db', 0), 'audio.volume_db', -120)
        for field in ('fade_in', 'fade_out'):
            if number(audio.get(field, 0), field, 0, True) > trim_out-trim_in:
                raise ValueError('Audio fade exceeds clip duration')
    return int(duration)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan')
    parser.add_argument('--output', required=True, help='Workspace staging directory, not live BCUT library')
    args = parser.parse_args()
    output = Path(args.output).resolve()
    marker = output / '.codex-bcut-staging'
    if output == (Path.home()/'Documents'/'Bcut Drafts').resolve():
        raise ValueError('Use a workspace staging directory; register separately')
    if output.exists() and any(output.iterdir()) and not marker.is_file():
        raise ValueError('Refusing a non-empty directory not created by this staging tool')
    os.environ['BCUT_DRAFT_ROOT'] = str(output)
    import bcut_draft as bd
    import edit_plan as ep
    plan = ep.load(args.plan)
    duration = validate(plan, bd.probe)
    output.mkdir(parents=True, exist_ok=True)
    marker.touch(exist_ok=True)
    guid = ep.to_bcut(plan)
    print(json.dumps({'guid': guid, 'name': plan['name'], 'duration_ms': duration,
                      'staged_root': str(output), 'folder': str(output/guid)}, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
