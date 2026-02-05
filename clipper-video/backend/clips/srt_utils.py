import re
from .utils import format_srt_time


def parse_srt(content):
    lines = content.splitlines()
    entries = []
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if re.match(r'^\d+$', line):
            i += 1
            if i >= len(lines):
                break
            line = lines[i].strip()
        if '-->' not in line:
            i += 1
            continue
        start_str, end_str = [part.strip() for part in line.split('-->')]
        i += 1
        text_lines = []
        while i < len(lines) and lines[i].strip() != '':
            text_lines.append(lines[i])
            i += 1
        entries.append({
            'start': parse_srt_time(start_str),
            'end': parse_srt_time(end_str),
            'text': '\n'.join(text_lines).strip(),
        })
    return entries


def parse_srt_time(value):
    match = re.match(r'^(\d{2}):(\d{2}):(\d{2}),(\d{3})$', value)
    if not match:
        raise ValueError('Invalid SRT time format')
    hours, minutes, seconds, ms = [int(part) for part in match.groups()]
    return hours * 3600 + minutes * 60 + seconds + (ms / 1000.0)


def trim_srt(content, clip_start, clip_end):
    entries = parse_srt(content)
    trimmed = []
    for entry in entries:
        start = entry['start']
        end = entry['end']
        if end <= clip_start or start >= clip_end:
            continue
        new_start = max(start, clip_start) - clip_start
        new_end = min(end, clip_end) - clip_start
        trimmed.append({
            'start': new_start,
            'end': new_end,
            'text': entry['text'],
        })
    return dedupe_entries(trimmed)


def dedupe_entries(entries, gap_threshold=0.2):
    """
    1) Merge consecutive duplicate text (common with auto captions).
    2) Normalize timing to avoid 'previous caption' lingering/overlapping.
    """
    cleaned = []
    for entry in entries:
        text = entry['text'].strip()
        if not text:
            continue
        start = float(entry['start'])
        end = float(entry['end'])
        if end <= start:
            continue
        if cleaned and cleaned[-1]['text'] == text and start <= cleaned[-1]['end'] + gap_threshold:
            cleaned[-1]['end'] = max(cleaned[-1]['end'], end)
            continue
        cleaned.append({
            'start': start,
            'end': end,
            'text': text,
        })
    return normalize_entries(cleaned)


def normalize_entries(entries, min_gap=0.05, max_duration=4.5, min_duration=0.35):
    """
    Prevent overlapping cues and overly-long cues which cause old captions to
    remain visible while the next caption starts.
    """
    if not entries:
        return []
    entries = sorted(entries, key=lambda e: (e['start'], e['end']))
    normalized = []
    for idx, entry in enumerate(entries):
        start = float(entry['start'])
        end = float(entry['end'])
        text = entry['text'].strip()
        if not text:
            continue
        # If this starts before the previous ends, push it forward so captions never overlap.
        if normalized:
            prev_end = float(normalized[-1]['end'])
            if start < prev_end + min_gap:
                start = prev_end + min_gap

        # Cap duration so captions don't 'stick' too long.
        end = min(end, start + max_duration)

        # If next entry starts before this ends, clamp end to just before next start.
        if idx + 1 < len(entries):
            next_start = float(entries[idx + 1]['start'])
            if next_start <= end:
                end = max(start, next_start - min_gap)

        # Ensure a minimal on-screen time (otherwise some players behave oddly).
        if end - start < min_duration:
            end = start + min_duration

        normalized.append({'start': start, 'end': end, 'text': text})
    return normalized


def render_srt(entries):
    lines = []
    for idx, entry in enumerate(entries, start=1):
        lines.append(str(idx))
        lines.append(f"{format_srt_time(entry['start'])} --> {format_srt_time(entry['end'])}")
        lines.append(entry['text'])
        lines.append('')
    return '\n'.join(lines).strip() + ('\n' if lines else '')


def write_trimmed_srt(source_path, output_path, clip_start, clip_end):
    with open(source_path, 'r', encoding='utf-8') as file:
        content = file.read()
    trimmed = trim_srt(content, clip_start, clip_end)
    rendered = render_srt(trimmed)
    with open(output_path, 'w', encoding='utf-8') as file:
        file.write(rendered)
    return len(trimmed)
