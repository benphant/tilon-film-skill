#!/usr/bin/env python3
"""Offline structural checks. No provider calls, generation or credentials."""
import argparse
import json
import math
import sys
from pathlib import Path


def number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def check(plan):
    errors, warnings = [], []
    if not isinstance(plan, dict):
        return ['plan must be an object'], []
    stage = plan.get('stage')
    if stage not in ('script', 'preproduction', 'production', 'review'):
        errors.append('stage must be script, preproduction, production or review')
    shots = plan.get('shots')
    if not isinstance(shots, list) or not shots:
        return errors + ['shots must be a non-empty list'], warnings
    seen = set()
    for i, shot in enumerate(shots):
        prefix = f'shots[{i}]'
        if not isinstance(shot, dict):
            errors.append(f'{prefix}: must be an object')
            continue
        key = shot.get('id')
        if not isinstance(key, str) or not key or key in seen:
            errors.append(f'{prefix}: id must be non-empty and unique')
        else:
            seen.add(key)
            prefix = key
        duration = shot.get('duration')
        if not number(duration) or duration <= 0:
            errors.append(f'{prefix}: duration must be positive and finite')
            continue
        if 'node_duration' in shot and shot['node_duration'] != duration:
            errors.append(f'{prefix}: node_duration differs from scripted duration')
        if stage == 'preproduction' and shot.get('status') != 'draft':
            errors.append(f'{prefix}: preproduction shot must remain draft')
        chars = shot.get('characters', [])
        refs = shot.get('references', [])
        for label, value in [('characters', chars), ('references', refs)]:
            if not isinstance(value, list) or any(not isinstance(x, str) for x in value):
                errors.append(f'{prefix}: {label} must be a list of strings')
        if not isinstance(chars, list) or not isinstance(refs, list) or any(not isinstance(x, str) for x in chars + refs):
            continue
        if stage == 'preproduction':
            for char in set(chars) - set(refs):
                errors.append(f'{prefix}: missing visual reference for {char}')
        beats = shot.get('beats')
        if not isinstance(beats, list) or not beats:
            errors.append(f'{prefix}: beats must be a non-empty list')
            continue
        end = 0.0
        for j, beat in enumerate(beats):
            if not isinstance(beat, dict):
                errors.append(f'{prefix}: beat {j} must be an object')
                continue
            start, stop = beat.get('start'), beat.get('end')
            if not number(start) or not number(stop) or not 0 <= start < stop <= duration:
                errors.append(f'{prefix}: beat {j} has invalid time range')
                continue
            if abs(start - end) > 0.001:
                errors.append(f'{prefix}: beat {j} has a gap, overlap or incorrect order')
            end = stop
        if abs(end - duration) > 0.001:
            errors.append(f'{prefix}: beats do not cover full duration')
        lines = shot.get('dialogue', [])
        if not isinstance(lines, list):
            errors.append(f'{prefix}: dialogue must be a list')
            continue
        intervals = []
        for j, line in enumerate(lines):
            if not isinstance(line, dict):
                errors.append(f'{prefix}: dialogue {j} must be an object')
                continue
            start, stop = line.get('start'), line.get('end')
            if not number(start) or not number(stop) or not 0 <= start < stop <= duration:
                errors.append(f'{prefix}: dialogue {j} outside duration or invalid')
                continue
            speaker = line.get('speaker')
            if speaker not in chars and speaker != 'VO':
                errors.append(f'{prefix}: dialogue {j} has unknown speaker')
            if not isinstance(line.get('text'), str) or not line['text'].strip():
                errors.append(f'{prefix}: dialogue {j} needs text')
            intervals.append((start, stop))
        intervals.sort()
        if any(b[0] < a[1] for a, b in zip(intervals, intervals[1:])) and not shot.get('allow_overlap', False):
            errors.append(f'{prefix}: overlapping dialogue without explicit allow_overlap')
        if intervals and sum(b - a for a, b in intervals) / duration > 0.85:
            warnings.append(f'{prefix}: dialogue occupies over 85%; review breathing/reaction time manually')
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
    print(json.dumps({'errors': errors, 'warnings': warnings, 'scope': 'offline structure only; no media inspection'}, ensure_ascii=False, indent=2))
    return int(bool(errors))


if __name__ == '__main__':
    sys.exit(main())
