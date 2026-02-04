from pathlib import Path

from faster_whisper import WhisperModel

from .utils import run_command, format_srt_time
from .srt_utils import dedupe_entries

_MODEL_CACHE = {}


def get_whisper_model(model_size):
    if model_size not in _MODEL_CACHE:
        _MODEL_CACHE[model_size] = WhisperModel(model_size, device='cpu', compute_type='int8')
    return _MODEL_CACHE[model_size]


def extract_audio(input_path, output_path):
    run_command([
        'ffmpeg',
        '-y',
        '-i', str(input_path),
        '-ac', '1',
        '-ar', '16000',
        '-vn',
        str(output_path),
    ])
    return output_path


def transcribe_to_srt(input_path, output_srt, language='id', model_size='tiny'):
    model = get_whisper_model(model_size)
    segments, _ = model.transcribe(
        str(input_path),
        language=language,
        vad_filter=True,
    )
    entries = []
    for segment in segments:
        text = segment.text.strip()
        if not text:
            continue
        entries.append({
            'start': segment.start,
            'end': segment.end,
            'text': text,
        })
    entries = dedupe_entries(entries)

    lines = []
    for idx, entry in enumerate(entries, start=1):
        lines.append(str(idx))
        lines.append(f"{format_srt_time(entry['start'])} --> {format_srt_time(entry['end'])}")
        lines.append(entry['text'])
        lines.append('')

    output_srt = Path(output_srt)
    output_srt.write_text('\n'.join(lines).strip() + ('\n' if lines else ''), encoding='utf-8')
    return len(entries)
