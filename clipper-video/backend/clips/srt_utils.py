import re
from typing import Any, Dict, List

from .utils import format_srt_time


_SRT_TIME_RE = re.compile(r"^(\d{2}):(\d{2}):(\d{2}),(\d{3})$")
_SRT_LINE_RE = re.compile(
    r"^\s*(\d{2}:\d{2}:\d{2},\d{3})\s*-->\s*(\d{2}:\d{2}:\d{2},\d{3})\s*$"
)
_HTML_TAG_RE = re.compile(r"<[^>]+>")
_SPACE_RE = re.compile(r"\s+")
_PUNCT_END_RE = re.compile(r"[.!?]$")
_PUNCT_ATTACH_RE = re.compile(r"^[,.;:!?%)\]\}]+$")
_CONTRACTION_RE = re.compile(r"^'(?:s|m|re|ve|d|ll|t)$", re.IGNORECASE)
_CLIP_CLEAR_CHAR = "\u200b"


def parse_srt_time(value: str) -> float:
    match = _SRT_TIME_RE.match((value or "").strip())
    if not match:
        raise ValueError("Invalid SRT time format")
    hours, minutes, seconds, ms = [int(part) for part in match.groups()]
    return hours * 3600 + minutes * 60 + seconds + (ms / 1000.0)


def _clean_caption_text(text: str) -> str:
    text = _HTML_TAG_RE.sub("", text or "")
    return _SPACE_RE.sub(" ", text).strip()


def _normalize_word(word: str) -> str:
    return _SPACE_RE.sub(" ", str(word or "")).strip()


def parse_srt(content: str) -> List[Dict[str, Any]]:
    if not content:
        return []

    blocks = re.split(r"\n\s*\n", content.strip())
    entries: List[Dict[str, Any]] = []

    for block in blocks:
        lines = [line.strip("\r") for line in block.splitlines() if line.strip()]
        if not lines:
            continue

        if lines[0].isdigit():
            lines = lines[1:]
            if not lines:
                continue

        time_match = _SRT_LINE_RE.match(lines[0].strip())
        if not time_match:
            continue

        try:
            start = parse_srt_time(time_match.group(1))
            end = parse_srt_time(time_match.group(2))
        except ValueError:
            continue

        if end <= start:
            continue

        text = _clean_caption_text(" ".join(lines[1:]))
        if not text:
            continue

        entries.append({"start": start, "end": end, "text": text})

    return entries


def trim_srt(content: str, clip_start: float, clip_end: float) -> List[Dict[str, Any]]:
    entries = parse_srt(content)
    trimmed: List[Dict[str, Any]] = []
    for entry in entries:
        start = float(entry["start"])
        end = float(entry["end"])
        if end <= clip_start or start >= clip_end:
            continue
        trimmed.append(
            {
                "start": max(start, clip_start) - clip_start,
                "end": min(end, clip_end) - clip_start,
                "text": _clean_caption_text(entry["text"]),
            }
        )
    return dedupe_entries(trimmed)


def normalize_text_for_compare(text: str) -> str:
    lowered = (text or "").lower().strip()
    collapsed = _SPACE_RE.sub(" ", lowered)
    return re.sub(r"[^\w\s]", "", collapsed)


def remove_rolling_duplicates(entries: List[Dict[str, Any]], max_gap: float = 0.35) -> List[Dict[str, Any]]:
    if not entries:
        return []

    ordered = sorted(entries, key=lambda item: (float(item["start"]), float(item["end"])))
    compacted: List[Dict[str, Any]] = []

    for index, current in enumerate(ordered):
        cur_text_norm = normalize_text_for_compare(current["text"])
        if not cur_text_norm:
            continue
        cur_word_count = len(cur_text_norm.split())

        if compacted:
            prev = compacted[-1]
            prev_text_norm = normalize_text_for_compare(prev["text"])
            cur_duration = float(current["end"]) - float(current["start"])
            if (
                cur_text_norm in prev_text_norm
                and float(current["start"]) <= float(prev["end"]) + max_gap
                and cur_duration <= 1.0
                and cur_word_count >= 2
            ):
                continue

        if index + 1 < len(ordered):
            next_entry = ordered[index + 1]
            next_text_norm = normalize_text_for_compare(next_entry["text"])
            if (
                cur_text_norm in next_text_norm
                and cur_text_norm != next_text_norm
                and float(next_entry["start"]) <= float(current["end"]) + max_gap
                and cur_word_count >= 2
            ):
                continue

        compacted.append(current)

    return compacted


def _normalize_word_for_overlap(word: str) -> str:
    compact = re.sub(r"[^\w]+", "", (word or "").lower())
    return compact.strip()


def trim_cross_cue_overlap(entries: List[Dict[str, Any]], min_overlap_words: int = 4) -> List[Dict[str, Any]]:
    if not entries:
        return []

    result = [dict(entries[0])]
    for current in entries[1:]:
        prev = result[-1]
        current_text = (current.get("text") or "").strip()
        prev_text = (prev.get("text") or "").strip()
        if not current_text:
            continue

        prev_words = prev_text.split()
        current_words = current_text.split()
        prev_norm = [_normalize_word_for_overlap(word) for word in prev_words]
        current_norm = [_normalize_word_for_overlap(word) for word in current_words]

        max_overlap = min(len(prev_norm), len(current_norm) - 1)
        overlap = 0
        for count in range(max_overlap, min_overlap_words - 1, -1):
            if prev_norm[-count:] == current_norm[:count]:
                overlap = count
                break

        if overlap > 0:
            remaining = current_words[overlap:]
            if not remaining:
                continue
            current = dict(current)
            current["text"] = " ".join(remaining).strip()

        result.append(current)

    return result


def normalize_entries(
    entries: List[Dict[str, Any]],
    min_gap: float = 0.12,
    max_duration: float = 2.8,
    min_duration: float = 0.42,
) -> List[Dict[str, Any]]:
    if not entries:
        return []

    ordered = sorted(entries, key=lambda item: (float(item["start"]), float(item["end"])))
    normalized: List[Dict[str, Any]] = []

    for index, entry in enumerate(ordered):
        text = _clean_caption_text(entry.get("text", ""))
        if not text:
            continue

        start = float(entry["start"])
        end = float(entry["end"])
        if end <= start:
            continue

        if normalized:
            prev_end = float(normalized[-1]["end"])
            if start < prev_end + min_gap:
                start = prev_end + min_gap

        end = min(end, start + max_duration)

        if index + 1 < len(ordered):
            next_start = float(ordered[index + 1]["start"])
            if next_start <= end:
                end = max(start, next_start - min_gap)

        if end - start < min_duration:
            end = start + min_duration

        normalized.append({"start": start, "end": end, "text": text})

    return normalized


def dedupe_entries(entries: List[Dict[str, Any]], gap_threshold: float = 0.08) -> List[Dict[str, Any]]:
    cleaned: List[Dict[str, Any]] = []
    for entry in entries:
        text = _clean_caption_text(entry.get("text", ""))
        if not text:
            continue
        start = float(entry["start"])
        end = float(entry["end"])
        if end <= start:
            continue

        if cleaned and cleaned[-1]["text"] == text and start <= cleaned[-1]["end"] + gap_threshold:
            cleaned[-1]["end"] = max(cleaned[-1]["end"], end)
            continue

        cleaned.append({"start": start, "end": end, "text": text})

    cleaned = remove_rolling_duplicates(cleaned)
    cleaned = trim_cross_cue_overlap(cleaned)
    return normalize_entries(cleaned)


def render_srt(entries: List[Dict[str, Any]]) -> str:
    lines: List[str] = []
    for idx, entry in enumerate(entries, start=1):
        lines.append(str(idx))
        lines.append(f"{format_srt_time(entry['start'])} --> {format_srt_time(entry['end'])}")
        lines.append(entry["text"])
        lines.append("")
    return "\n".join(lines).strip() + ("\n" if lines else "")


def write_trimmed_srt(source_path: str, output_path: str, clip_start: float, clip_end: float) -> int:
    with open(source_path, "r", encoding="utf-8") as file:
        content = file.read()
    trimmed = trim_srt(content, clip_start, clip_end)
    rendered = render_srt(trimmed)
    with open(output_path, "w", encoding="utf-8") as file:
        file.write(rendered)
    return len(trimmed)


def _word_tokens(words: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    tokens: List[Dict[str, Any]] = []
    for raw in words or []:
        word = _normalize_word(raw.get("word", ""))
        if not word:
            continue
        start = raw.get("start")
        end = raw.get("end")
        if start is None or end is None:
            continue
        start = float(start)
        end = float(end)
        if end <= start:
            continue
        tokens.append(
            {
                "word": word,
                "start": start,
                "end": end,
                "speaker": raw.get("speaker"),
                "confidence": float(raw.get("confidence", 1.0)),
            }
        )
    return sorted(tokens, key=lambda item: (item["start"], item["end"]))


def _join_token_words(buffer: List[Dict[str, Any]]) -> str:
    if not buffer:
        return ""

    chunks: List[str] = []
    for token in buffer:
        word = token["word"]
        if not chunks:
            chunks.append(word)
            continue
        if _PUNCT_ATTACH_RE.match(word) or _CONTRACTION_RE.match(word):
            chunks[-1] = f"{chunks[-1]}{word}"
        else:
            chunks.append(word)
    return _clean_caption_text(" ".join(chunks))


def _needs_break(
    buffer: List[Dict[str, Any]],
    next_token: Dict[str, Any],
    pause_threshold: float,
    max_words: int,
    max_chars: int,
) -> bool:
    if not buffer:
        return False

    if len(buffer) >= max_words:
        return True

    text = _join_token_words(buffer)
    if len(text) >= max_chars:
        return True

    if _PUNCT_END_RE.search(buffer[-1]["word"]):
        return True

    if not next_token:
        return True

    if buffer[-1].get("speaker") != next_token.get("speaker"):
        return True

    gap = float(next_token["start"]) - float(buffer[-1]["end"])
    return gap > pause_threshold


def words_to_cues(
    words: List[Dict[str, Any]],
    pause_threshold: float = 0.25,
    max_words: int = 8,
    max_chars: int = 40,
) -> List[Dict[str, Any]]:
    tokens = _word_tokens(words)
    if not tokens:
        return []

    cues: List[Dict[str, Any]] = []
    buffer: List[Dict[str, Any]] = []

    for index, token in enumerate(tokens):
        buffer.append(token)
        next_token = tokens[index + 1] if index + 1 < len(tokens) else None

        if not _needs_break(buffer, next_token, pause_threshold, max_words, max_chars):
            continue

        text = _join_token_words(buffer)
        if text:
            cues.append(
                {
                    "start": float(buffer[0]["start"]),
                    "end": float(buffer[-1]["end"]),
                    "text": text,
                    "speaker": buffer[0].get("speaker"),
                }
            )
        buffer = []

    return normalize_entries(cues, min_gap=0.05, max_duration=4.5, min_duration=0.2)


def align_speakers(words: List[Dict[str, Any]], diarization_segments: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not words or not diarization_segments:
        return words

    segments = sorted(diarization_segments, key=lambda item: float(item["start"]))
    out: List[Dict[str, Any]] = []
    segment_index = 0

    for token in words:
        start = float(token["start"])
        end = float(token["end"])
        mid = (start + end) / 2.0

        while segment_index + 1 < len(segments) and mid > float(segments[segment_index]["end"]):
            segment_index += 1

        speaker = None
        segment = segments[segment_index]
        if float(segment["start"]) <= mid <= float(segment["end"]):
            speaker = segment.get("speaker")

        merged = dict(token)
        merged["speaker"] = speaker
        out.append(merged)

    return out


def _format_webvtt_time(seconds: float) -> str:
    return format_srt_time(seconds).replace(",", ".")


def render_webvtt(entries: List[Dict[str, Any]]) -> str:
    lines = ["WEBVTT", ""]
    for entry in entries:
        lines.append(f"{_format_webvtt_time(entry['start'])} --> {_format_webvtt_time(entry['end'])}")
        text = entry["text"]
        speaker = entry.get("speaker")
        if speaker:
            text = f"[{speaker}] {text}"
        lines.append(text)
        lines.append("")
    return "\n".join(lines).strip() + "\n"


def export_word_srt(
    words: List[Dict[str, Any]],
    output_path: str,
    pause_threshold: float = 0.25,
    max_words: int = 8,
    max_chars: int = 40,
) -> int:
    cues = words_to_cues(words, pause_threshold=pause_threshold, max_words=max_words, max_chars=max_chars)
    for cue in cues:
        if cue.get("speaker"):
            cue["text"] = f"[{cue['speaker']}] {cue['text']}"
    rendered = render_srt(cues)
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(rendered)
    return len(cues)


def format_ass_time(seconds: float) -> str:
    total_ms = int(round(float(seconds) * 1000))
    hours = total_ms // 3600000
    remainder = total_ms % 3600000
    minutes = remainder // 60000
    remainder %= 60000
    secs = remainder // 1000
    centis = (remainder % 1000) // 10
    return f"{hours}:{minutes:02d}:{secs:02d}.{centis:02d}"


def render_ass_from_words(
    words: List[Dict[str, Any]],
    style_name: str = "Default",
    font_name: str = "Arial",
    font_size: int = 12,
    primary_color: str = "&H00FFFFFF",
) -> str:
    tokens = _word_tokens(words)
    safe_style = style_name or "Default"
    safe_font = (font_name or "Arial").replace(",", "").strip() or "Arial"
    safe_size = max(14, min(72, int(font_size or 28)))

    header = [
        "[Script Info]",
        "ScriptType: v4.00+",
        "PlayResX: 1280",
        "PlayResY: 720",
        "",
        "[V4+ Styles]",
        "Format: Name,Fontname,Fontsize,PrimaryColour,SecondaryColour,OutlineColour,BackColour,"
        "Bold,Italic,BorderStyle,Outline,Shadow,Alignment,MarginL,MarginR,MarginV,Encoding",
        f"Style: {safe_style},{safe_font},{safe_size},{primary_color},&H000000FF,&H00000000,&H00000000,"
        "0,0,1,2,0,2,20,20,28,1",
        "",
        "[Events]",
        "Format: Layer,Start,End,Style,Name,MarginL,MarginR,MarginV,Effect,Text",
    ]

    events: List[str] = []
    for token in tokens:
        start = format_ass_time(token["start"])
        end = format_ass_time(token["end"])
        text = token["word"]
        if token.get("speaker"):
            text = f"[{token['speaker']}] {text}"
        text = text.replace("\\", r"\\").replace("{", r"\{").replace("}", r"\}").replace("\n", r"\N")
        events.append(f"Dialogue: 0,{start},{end},{safe_style},,0000,0000,0000,,{text}")

    return "\n".join(header + events) + "\n"


def words_to_srt(
    words: List[Dict[str, Any]],
    pause_threshold: float = 0.3,
    max_words_per_line: int = 5,
    normalize: bool = True,
    max_chars: int = 40,
) -> str:
    cues = words_to_cues(
        words,
        pause_threshold=pause_threshold,
        max_words=max_words_per_line,
        max_chars=max_chars,
    )
    if normalize:
        cues = normalize_entries(cues, min_gap=0.05, max_duration=4.5, min_duration=0.2)
    return render_srt(cues)


def words_to_webvtt(
    words: List[Dict[str, Any]],
    pause_threshold: float = 0.3,
    max_words_per_line: int = 5,
    normalize: bool = True,
    max_chars: int = 40,
) -> str:
    cues = words_to_cues(
        words,
        pause_threshold=pause_threshold,
        max_words=max_words_per_line,
        max_chars=max_chars,
    )
    if normalize:
        cues = normalize_entries(cues, min_gap=0.05, max_duration=4.5, min_duration=0.2)
    return render_webvtt(cues)


def export_word_srt_from_tokens(
    words: List[Dict[str, Any]],
    output_path: str,
    pause_threshold: float = 0.3,
    max_words_per_line: int = 5,
    max_chars: int = 40,
) -> int:
    srt_text = words_to_srt(
        words,
        pause_threshold=pause_threshold,
        max_words_per_line=max_words_per_line,
        max_chars=max_chars,
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(srt_text)
    return len([line for line in srt_text.split("\n") if "-->" in line])


def export_word_webvtt_from_tokens(
    words: List[Dict[str, Any]],
    output_path: str,
    pause_threshold: float = 0.3,
    max_words_per_line: int = 5,
    max_chars: int = 40,
) -> int:
    vtt_text = words_to_webvtt(
        words,
        pause_threshold=pause_threshold,
        max_words_per_line=max_words_per_line,
        max_chars=max_chars,
    )
    with open(output_path, "w", encoding="utf-8") as handle:
        handle.write(vtt_text)
    return len([line for line in vtt_text.split("\n") if "-->" in line])


def filter_words_by_vad(
    words: List[Dict[str, Any]],
    vad_segments: List[Dict[str, Any]],
    min_overlap: float = 0.03,
) -> List[Dict[str, Any]]:
    if not vad_segments:
        return words

    segments = sorted(vad_segments, key=lambda item: float(item["start"]))
    kept: List[Dict[str, Any]] = []
    segment_index = 0

    for word in words:
        start = float(word["start"])
        end = float(word["end"])

        while segment_index + 1 < len(segments) and float(segments[segment_index]["end"]) < start:
            segment_index += 1

        overlap = 0.0
        for idx in (segment_index, segment_index + 1):
            if idx >= len(segments):
                continue
            seg_start = float(segments[idx]["start"])
            seg_end = float(segments[idx]["end"])
            overlap_start = max(start, seg_start)
            overlap_end = min(end, seg_end)
            if overlap_end > overlap_start:
                overlap = max(overlap, overlap_end - overlap_start)

        if overlap >= min_overlap:
            kept.append(word)

    return kept


def insert_clear_cues(
    entries: List[Dict[str, Any]],
    silence_threshold: float = 1.0,
    clear_duration: float = 0.05,
) -> List[Dict[str, Any]]:
    if not entries:
        return []

    out: List[Dict[str, Any]] = []
    for idx, entry in enumerate(entries):
        out.append(entry)
        if idx + 1 >= len(entries):
            continue
        next_start = float(entries[idx + 1]["start"])
        gap = next_start - float(entry["end"])
        if gap >= silence_threshold:
            start = float(entry["end"]) + 0.001
            out.append({"start": start, "end": start + clear_duration, "text": _CLIP_CLEAR_CHAR})
    return out
