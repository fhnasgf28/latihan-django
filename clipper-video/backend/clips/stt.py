import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

try:
    from faster_whisper import WhisperModel

    HAS_FASTER_WHISPER = True
except ImportError:
    WhisperModel = None
    HAS_FASTER_WHISPER = False

try:
    import stable_whisper

    HAS_STABLE_WHISPER = True
except ImportError:
    stable_whisper = None
    HAS_STABLE_WHISPER = False

from .utils import format_srt_time
from .srt_utils import dedupe_entries, export_word_srt_from_tokens, export_word_webvtt_from_tokens

_MODEL_CACHE: Dict[Tuple[str, str, str], Dict[str, Any]] = {}


def _pick_device() -> Tuple[str, str]:
    cuda_visible = (os.environ.get("CUDA_VISIBLE_DEVICES") or "").strip()
    has_cuda = bool(cuda_visible and cuda_visible != "-1")
    if has_cuda:
        return ("cuda", "float16")
    return ("cpu", "int8")


def get_whisper_model(model_size: str) -> Dict[str, Any]:
    device, compute_type = _pick_device()
    cache_key = (model_size, device, compute_type)
    if cache_key in _MODEL_CACHE:
        return _MODEL_CACHE[cache_key]

    if HAS_FASTER_WHISPER:
        try:
            model = WhisperModel(model_size, device=device, compute_type=compute_type)
            wrapper = {"backend": "faster", "model": model}
            _MODEL_CACHE[cache_key] = wrapper
            return wrapper
        except Exception:
            if device == "cuda":
                cpu_key = (model_size, "cpu", "int8")
                if cpu_key in _MODEL_CACHE:
                    return _MODEL_CACHE[cpu_key]
                model = WhisperModel(model_size, device="cpu", compute_type="int8")
                wrapper = {"backend": "faster", "model": model}
                _MODEL_CACHE[cpu_key] = wrapper
                return wrapper
            raise

    if HAS_STABLE_WHISPER:
        # Fallback backend if faster-whisper is unavailable.
        model = stable_whisper.load_model(model_size, device=device)
        wrapper = {"backend": "stable", "model": model}
        _MODEL_CACHE[cache_key] = wrapper
        return wrapper

    raise RuntimeError("Neither faster_whisper nor stable_whisper is installed")


def _clean_word(word: str) -> str:
    return " ".join(str(word or "").split()).strip()


def _fallback_words_from_segment(segment_text: str, seg_start: float, seg_end: float) -> List[Dict[str, Any]]:
    text = (segment_text or "").strip()
    if not text:
        return []
    pieces = text.split()
    if not pieces:
        return []

    seg_duration = max(0.001, float(seg_end) - float(seg_start))
    lengths = [max(1, len(piece)) for piece in pieces]
    total_len = sum(lengths)
    cursor = float(seg_start)
    words: List[Dict[str, Any]] = []

    for piece, piece_len in zip(pieces, lengths):
        duration = (piece_len / total_len) * seg_duration
        words.append(
            {
                "word": piece,
                "start": cursor,
                "end": cursor + duration,
                "confidence": 0.85,
            }
        )
        cursor += duration

    return words


def _collect_faster_whisper_words(segments: List[Any]) -> List[Dict[str, Any]]:
    words: List[Dict[str, Any]] = []
    for segment in segments:
        seg_start = float(getattr(segment, "start", 0.0))
        seg_end = float(getattr(segment, "end", seg_start))
        segment_words = getattr(segment, "words", None) or []

        if segment_words:
            for token in segment_words:
                raw_word = _clean_word(getattr(token, "word", ""))
                if not raw_word:
                    continue
                start = getattr(token, "start", None)
                end = getattr(token, "end", None)
                start = seg_start if start is None else float(start)
                end = seg_end if end is None else float(end)
                if end <= start:
                    continue
                words.append(
                    {
                        "word": raw_word,
                        "start": start,
                        "end": end,
                        "confidence": float(getattr(token, "probability", 1.0)),
                    }
                )
            continue

        words.extend(_fallback_words_from_segment(getattr(segment, "text", ""), seg_start, seg_end))

    return words


def _collect_stable_whisper_words(result: Any) -> List[Dict[str, Any]]:
    words: List[Dict[str, Any]] = []
    for segment in getattr(result, "segments", []) or []:
        seg_start = float(getattr(segment, "start", 0.0))
        seg_end = float(getattr(segment, "end", seg_start))
        segment_words = getattr(segment, "words", None) or []

        if segment_words:
            for token in segment_words:
                raw_word = _clean_word(getattr(token, "word", ""))
                if not raw_word:
                    continue
                start = getattr(token, "start", None)
                end = getattr(token, "end", None)
                start = seg_start if start is None else float(start)
                end = seg_end if end is None else float(end)
                if end <= start:
                    continue
                words.append(
                    {
                        "word": raw_word,
                        "start": start,
                        "end": end,
                        "confidence": float(getattr(token, "confidence", 1.0)),
                    }
                )
            continue

        words.extend(_fallback_words_from_segment(getattr(segment, "text", ""), seg_start, seg_end))

    return words


def _to_srt_from_segment_entries(entries: List[Dict[str, Any]], output_srt: str) -> int:
    entries = dedupe_entries(entries)
    lines: List[str] = []
    for index, entry in enumerate(entries, start=1):
        lines.append(str(index))
        lines.append(f"{format_srt_time(entry['start'])} --> {format_srt_time(entry['end'])}")
        lines.append(entry["text"])
        lines.append("")
    Path(output_srt).write_text("\n".join(lines).strip() + ("\n" if lines else ""), encoding="utf-8")
    return len(entries)


def transcribe_to_word_tokens(input_path: str, language: str = "id", model_size: str = "tiny") -> List[Dict[str, Any]]:
    engine = get_whisper_model(model_size)
    backend = engine["backend"]
    model = engine["model"]

    if backend == "faster":
        segments_iter, _ = model.transcribe(
            str(input_path),
            language=(language or None),
            beam_size=5,
            word_timestamps=True,
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 500},
            condition_on_previous_text=False,
        )
        segments = list(segments_iter)
        words = _collect_faster_whisper_words(segments)
    else:
        result = model.transcribe(
            str(input_path),
            language=(language or None),
            vad=True,
            regroup=True,
            suppress_silence=True,
            word_timestamps=True,
        )
        words = _collect_stable_whisper_words(result)

    cleaned: List[Dict[str, Any]] = []
    for token in words:
        word = _clean_word(token.get("word", ""))
        if not word:
            continue
        start = float(token["start"])
        end = float(token["end"])
        if end <= start:
            continue
        cleaned.append(
            {
                "word": word,
                "start": start,
                "end": end,
                "confidence": float(token.get("confidence", 1.0)),
            }
        )

    return sorted(cleaned, key=lambda item: (item["start"], item["end"]))


def transcribe_to_srt(input_path: str, output_srt: str, language: str = "id", model_size: str = "tiny") -> int:
    words = transcribe_to_word_tokens(input_path, language=language, model_size=model_size)
    if words:
        return export_word_srt_from_tokens(
            words,
            output_srt,
            pause_threshold=0.35,
            max_words_per_line=6,
            max_chars=40,
        )

    engine = get_whisper_model(model_size)
    backend = engine["backend"]
    model = engine["model"]

    if backend == "faster":
        segments_iter, _ = model.transcribe(
            str(input_path),
            language=(language or None),
            beam_size=5,
            vad_filter=True,
            condition_on_previous_text=False,
            word_timestamps=False,
        )
        entries = []
        for segment in segments_iter:
            text = (getattr(segment, "text", "") or "").strip()
            if not text:
                continue
            entries.append(
                {
                    "start": float(getattr(segment, "start", 0.0)),
                    "end": float(getattr(segment, "end", 0.0)),
                    "text": text,
                }
            )
        return _to_srt_from_segment_entries(entries, output_srt)

    result = model.transcribe(
        str(input_path),
        language=(language or None),
        vad=True,
        regroup=True,
        suppress_silence=True,
    )
    entries = []
    for segment in getattr(result, "segments", []) or []:
        text = (getattr(segment, "text", "") or "").strip()
        if not text:
            continue
        entries.append(
            {
                "start": float(getattr(segment, "start", 0.0)),
                "end": float(getattr(segment, "end", 0.0)),
                "text": text,
            }
        )
    return _to_srt_from_segment_entries(entries, output_srt)


def transcribe_to_srt_from_words(
    input_path: str,
    output_srt: str,
    language: str = "id",
    model_size: str = "tiny",
    pause_threshold: float = 0.3,
    max_words_per_line: int = 5,
    max_chars: int = 40,
) -> int:
    words = transcribe_to_word_tokens(input_path, language=language, model_size=model_size)
    return export_word_srt_from_tokens(
        words,
        output_srt,
        pause_threshold=pause_threshold,
        max_words_per_line=max_words_per_line,
        max_chars=max_chars,
    )


def transcribe_to_webvtt_from_words(
    input_path: str,
    output_vtt: str,
    language: str = "id",
    model_size: str = "tiny",
    pause_threshold: float = 0.3,
    max_words_per_line: int = 5,
    max_chars: int = 40,
) -> int:
    words = transcribe_to_word_tokens(input_path, language=language, model_size=model_size)
    return export_word_webvtt_from_tokens(
        words,
        output_vtt,
        pause_threshold=pause_threshold,
        max_words_per_line=max_words_per_line,
        max_chars=max_chars,
    )
