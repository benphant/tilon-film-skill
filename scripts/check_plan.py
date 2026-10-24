#!/usr/bin/env python3
"""Offline plan checks; no provider calls, generation, credentials or media inspection."""
import argparse
import json
import math
import re
import sys
from pathlib import Path

DETAIL_FIELDS = ('scene', 'blocking', 'action', 'performance', 'camera', 'lighting',
                 'background', 'sound', 'transition', 'continuity')
TOLERANCE = 0.001


def number(value):
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        return math.isfinite(value)
    except OverflowError:
        return False


def text(value):
    return isinstance(value, str) and bool(value.strip())


def string_list(value):
    return isinstance(value, list) and all(text(item) for item in value)


def timeline(parts, duration, prefix, field, errors, detailed=False):
    if not isinstance(parts, list) or not parts:
        errors.append(f'{prefix}: {field} must be a non-empty list')
        return
    previous_end = 0.0
    for index, part in enumerate(parts):
        label = f'{prefix}: {field}[{index}]'
        if not isinstance(part, dict):
            errors.append(f'{label} must be an object')
            continue
        if detailed:
            for name in DETAIL_FIELDS:
                if not text(part.get(name)):
                    errors.append(f'{label}.{name} needs a non-empty description')
        start, stop = part.get('start'), part.get('end')
        if not number(start) or not number(stop) or not 0 <= start < stop <= duration:
            errors.append(f'{label} has invalid time range')
            continue
        if abs(start - previous_end) > TOLERANCE:
            errors.append(f'{label} has a gap, overlap or incorrect order')
        previous_end = stop
    if abs(previous_end - duration) > TOLERANCE:
        errors.append(f'{prefix}: {field} do not cover full duration')


def dialogue(lines, duration, chars, allow_overlap, prefix, errors, warnings):
    if not isinstance(lines, list):
        errors.append(f'{prefix}: dialogue must be a list')
        return
    intervals = []
    for index, line in enumerate(lines):
        label = f'{prefix}: dialogue[{index}]'
        if not isinstance(line, dict):
            errors.append(f'{label} must be an object')
            continue
        start, stop = line.get('start'), line.get('end')
        if not number(start) or not number(stop) or not 0 <= start < stop <= duration:
            errors.append(f'{label} outside duration or invalid')
            continue
        speaker = line.get('speaker')
        if not text(speaker) or (speaker not in chars and speaker != 'VO'):
            errors.append(f'{label} has unknown speaker')
        if not text(line.get('text')):
            errors.append(f'{label} needs text')
        intervals.append((start, stop))
    intervals.sort()
    if any(right[0] < left[1] for left, right in zip(intervals, intervals[1:])) and not allow_overlap:
        errors.append(f'{prefix}: overlapping dialogue without explicit allow_overlap')
    # Use union duration so intentional overlapping speech does not double-count time.
    merged = []
    for start, stop in intervals:
        if merged and start <= merged[-1][1]:
            merged[-1][1] = max(merged[-1][1], stop)
        else:
            merged.append([start, stop])
    if sum(stop - start for start, stop in merged) / duration > 0.85:
        warnings.append(f'{prefix}: dialogue occupies over 85%; review breathing/reaction time manually')


def check(plan):
    errors, warnings = [], []
    if not isinstance(plan, dict):
        return ['plan must be an object'], []
    version = plan.get('schema_version', 1)
    if type(version) is not int or version not in (1, 2):
        return ['schema_version must be 1 or 2'], []
    if version == 1:
        warnings.append('legacy v1 beats accepted; use v2 subshots to check detailed directing fields')
    stage = plan.get('stage')
    if stage not in ('script', 'preproduction', 'production', 'review'):
        errors.append('stage must be script, preproduction, production or review')
    if version == 2:
        audio = plan.get('audio')
        if not isinstance(audio, dict):
            errors.append('audio must declare boolean bgm and subtitles policies')
        else:
            for name in ('bgm', 'subtitles'):
                if not isinstance(audio.get(name), bool):
                    errors.append(f'audio.{name} must be boolean')
    shots = plan.get('shots')
    if not isinstance(shots, list) or not shots:
        return errors + ['shots must be a non-empty list'], warnings
    seen = set()
    for index, shot in enumerate(shots):
        prefix = f'shots[{index}]'
        if not isinstance(shot, dict):
            errors.append(f'{prefix}: must be an object')
            continue
        key = shot.get('id')
        if not text(key) or key in seen:
            errors.append(f'{prefix}: id must be non-empty and unique')
        else:
            seen.add(key)
            prefix = key
        duration = shot.get('duration')
        if not number(duration) or duration <= 0:
            errors.append(f'{prefix}: duration must be positive and finite')
            continue
        if 'node_duration' in shot:
            actual = shot['node_duration']
            if not number(actual) or actual <= 0 or abs(actual - duration) > TOLERANCE:
                errors.append(f'{prefix}: node_duration differs from scripted duration or is invalid')
        for name in ('ratio', 'node_ratio'):
            if name in shot and (not isinstance(shot[name], str) or not re.fullmatch(r'[1-9][0-9]*:[1-9][0-9]*', shot[name])):
                errors.append(f'{prefix}: {name} must be a positive integer ratio such as 16:9')
        if 'node_ratio' in shot and shot.get('ratio') != shot['node_ratio']:
            errors.append(f'{prefix}: node_ratio differs from scripted ratio or ratio is missing')
        if stage == 'preproduction' and shot.get('status') != 'draft':
            errors.append(f'{prefix}: preproduction shot must remain draft')
        fields = {}
        for name in ('characters', 'references', 'continuity_required'):
            value = shot.get(name, [])
            if not string_list(value):
                errors.append(f'{prefix}: {name} must be a list of non-empty strings')
                fields[name] = []
            else:
                fields[name] = value
        chars, refs, required = (fields[name] for name in ('characters', 'references', 'continuity_required'))
        for character in sorted(set(required) - set(chars)):
            errors.append(f'{prefix}: continuity_required contains unknown character {character}')
        if stage in ('preproduction', 'production', 'review'):
            for character in sorted(set(required) - set(refs)):
                errors.append(f'{prefix}: missing visual reference for continuity_required character {character}')
        field = 'subshots' if version == 2 else 'beats'
        timeline(shot.get(field), duration, prefix, field, errors, detailed=version == 2)
        overlap = shot.get('allow_overlap', False)
        if not isinstance(overlap, bool):
            errors.append(f'{prefix}: allow_overlap must be boolean')
            overlap = False
        dialogue(shot.get('dialogue', []), duration, chars, overlap, prefix, errors, warnings)
    return errors, warnings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('plan', type=Path)
    args = parser.parse_args()
    try:
        errors, warnings = check(json.loads(args.plan.read_text(encoding='utf-8')))
    except (OSError, ValueError) as exc:
        print(json.dumps({'errors': [str(exc)], 'warnings': []}, ensure_ascii=False))
        return 2
    print(json.dumps({'errors': errors, 'warnings': warnings, 'scope': 'offline structure only; no media or CLI binding inspection'}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
