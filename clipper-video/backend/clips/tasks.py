import shutil
import re
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import Job
from .services import (
    fetch_video_info,
    probe_duration_seconds,
    get_max_height,
    has_height,
    build_format_selector,
    download_video,
    download_section,
    download_subtitles,
    pick_subtitle_file,
    split_video,
    burn_subtitles,
    convert_to_portrait,
    burn_subtitles_from_words,
)
from .srt_utils import write_trimmed_srt
from .utils import parse_timecode, parse_yt_dlp_progress
import json
from .stt import transcribe_to_srt_from_words, transcribe_to_word_tokens

MAX_DURATION_SECONDS = 2 * 60 * 60
MAX_CLIPS = 60
CLIP_OUTPUT_RE = re.compile(r"^clip_(\d{3})(?:_caption)?\.mp4$")


class JobCanceledError(Exception):
    pass


def update_job(job, **fields):
    # Prevent any stale worker process from overwriting canceled state.
    job.refresh_from_db(fields=['status', 'cancel_requested'])
    if (job.status == 'canceled' or job.cancel_requested) and fields.get('status') != 'canceled':
        raise JobCanceledError('Canceled by user')
    for key, value in fields.items():
        setattr(job, key, value)
    job.save(update_fields=list(fields.keys()) + ['updated_at'])


def ensure_not_canceled(job):
    job.refresh_from_db(fields=['cancel_requested', 'status'])
    if job.cancel_requested or job.status == 'canceled':
        raise JobCanceledError('Canceled by user')


def iter_output_clips(job_dir):
    """Yield (clip_idx, clip_path) for final clip outputs.

    Prefer *_caption.mp4 when both base and caption variants exist.
    """
    selected = {}
    for clip_path in sorted(job_dir.glob('clip_*.mp4')):
        match = CLIP_OUTPUT_RE.match(clip_path.name)
        if not match:
            continue
        clip_idx = int(match.group(1))
        previous = selected.get(clip_idx)
        if previous is None or clip_path.name.endswith('_caption.mp4'):
            selected[clip_idx] = clip_path

    for clip_idx in sorted(selected):
        yield clip_idx, selected[clip_idx]


@shared_task
def cleanup_old_jobs():
    """
    Delete job output folders older than JOB_RETENTION_DAYS.
    This only removes files under MEDIA_ROOT/jobs/<job_id>/.
    """
    retention_days = getattr(settings, 'JOB_RETENTION_DAYS', 2)
    cutoff = timezone.now() - timedelta(days=retention_days)
    old_jobs = Job.objects.filter(created_at__lt=cutoff)
    base_dir = Path(settings.MEDIA_ROOT) / 'jobs'
    deleted = 0
    for job in old_jobs:
        job_dir = base_dir / str(job.id)
        if job_dir.exists():
            shutil.rmtree(job_dir, ignore_errors=True)
            deleted += 1
    return deleted


@shared_task
def process_job(job_id):
    job = Job.objects.get(id=job_id)
    try:
        ensure_not_canceled(job)
        update_job(job, status='running', progress=5, message='Preparing')
        ensure_not_canceled(job)

        info = None
        duration = 0
        if job.source_type == 'youtube':
            update_job(job, message='Fetching video info')
            info = fetch_video_info(job.youtube_url)
            ensure_not_canceled(job)
            duration = info.get('duration') or 0
            if not duration:
                raise RuntimeError('Tidak bisa membaca durasi video')
        else:
            update_job(job, message='Probing local video')
            source_path = Path(settings.MEDIA_ROOT) / job.local_video_path
            if not source_path.exists():
                raise RuntimeError('Local video file tidak ditemukan')
            duration = probe_duration_seconds(source_path)
            ensure_not_canceled(job)
            if not duration:
                raise RuntimeError('Tidak bisa membaca durasi video (ffprobe)')
        if duration > MAX_DURATION_SECONDS:
            raise RuntimeError('Video lebih dari 2 jam. Silakan gunakan video yang lebih pendek.')

        if job.source_type == 'youtube':
            formats = info.get('formats') or []
            max_height = get_max_height(formats)
            if job.strict_1080 and not has_height(formats, 1080):
                raise RuntimeError(f'1080p tidak tersedia. Max height tersedia: {max_height}p')

        if job.mode == 'auto':
            # Pastikan interval_minutes tidak None sebelum dikalikan
            interval_minutes = job.interval_minutes
            if interval_minutes is None:
                # Fallback jika somehow null di database, default ke 3 menit
                interval_minutes = 3

            interval = interval_minutes * 60
            if interval < 60:
                raise RuntimeError('Interval minimal 1 menit')
            ranges = []
            start = 0
            while start < duration:
                end = min(start + interval, duration)
                ranges.append((start, end))
                start = end
        else:
            ranges = []
            for item in job.ranges or []:
                start = parse_timecode(item['start'])
                end = parse_timecode(item['end'])
                if start >= end:
                    raise RuntimeError('Range tidak valid: start harus lebih kecil dari end')
                if end > duration:
                    raise RuntimeError('Range melebihi durasi video')
                ranges.append((start, end))

        if len(ranges) > MAX_CLIPS:
            raise RuntimeError('Terlalu banyak clip. Maksimum 60 clip per job.')

        max_clips = max(0, job.max_clips or 0)
        if max_clips > 0:
            ranges = ranges[: max_clips]

        job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id)
        work_dir = job_dir / 'work'
        job_dir.mkdir(parents=True, exist_ok=True)
        work_dir.mkdir(parents=True, exist_ok=True)

        selector = build_format_selector(job.strict_1080, job.min_height_fallback)
        source_path = None
        if job.source_type == 'youtube':
            if not job.download_sections:
                last_reported = {'progress': 0}

                def handle_download_line(line):
                    ensure_not_canceled(job)
                    percent = parse_yt_dlp_progress(line)
                    if percent is None:
                        return
                    scaled = 5 + int((percent / 100) * 15)
                    if scaled > last_reported['progress']:
                        last_reported['progress'] = scaled
                        update_job(job, progress=scaled, message=f'Downloading video {percent:.1f}%')

                update_job(job, message='Downloading video 0%')
                source_path = download_video(job.youtube_url, work_dir, selector, on_line=handle_download_line)
                update_job(job, progress=20, message='Download complete')
            else:
                update_job(job, progress=20, message='Using download-sections (streaming)')
        else:
            # Local source: file already exists, skip download.
            source_path = Path(settings.MEDIA_ROOT) / job.local_video_path
            update_job(job, progress=20, message='Local video ready')

        update_job(job, progress=40, message='Processing clips (streaming)')

        subtitle_file = None
        per_clip_whisper = False
        wants_subtitles = job.burn_subtitles or job.auto_captions or job.generate_srt
        prefer_auto_asr = bool(job.auto_captions)

        if wants_subtitles and job.source_type == 'youtube' and not prefer_auto_asr:
            update_job(job, progress=60, message='Fetching subtitles')
            try:
                srt_files = download_subtitles(job.youtube_url, work_dir, job.subtitle_langs or ['id', 'en'])
                subtitle_file = pick_subtitle_file(srt_files, job.subtitle_langs or ['id', 'en'])
                if not subtitle_file:
                    update_job(job, message='No YouTube subtitles found')
            except Exception:
                update_job(job, message='No YouTube subtitles found')
        elif wants_subtitles and not prefer_auto_asr:
            update_job(job, progress=60, message='No YouTube subtitles for local source')

        if prefer_auto_asr:
            if (job.source_type == 'youtube' and job.download_sections) or max_clips <= 3:
                per_clip_whisper = True
                update_job(job, message='Auto captions per clip (word-level)')
            else:
                update_job(job, message='Auto captions full audio (word-level)')
                full_srt = work_dir / 'whisper_full.srt'
                transcribe_to_srt_from_words(
                    source_path,
                    full_srt,
                    language=job.auto_caption_lang,
                    model_size=job.whisper_model,
                    pause_threshold=0.35,
                    max_words_per_line=6,
                    max_chars=40,
                )
                ensure_not_canceled(job)
                subtitle_file = full_srt
        elif (job.burn_subtitles or job.generate_srt) and not subtitle_file:
            update_job(job, message='Subtitle/SRT diminta tapi subtitle sumber tidak tersedia')

        total = len(ranges)
        for idx, (start, end) in enumerate(ranges, start=1):
            ensure_not_canceled(job)
            if job.source_type == 'youtube' and job.download_sections:
                clip_path = download_section(job.youtube_url, work_dir, selector, start, end, idx)
            else:
                fast_copy = not job.burn_subtitles
                clip_paths = split_video(source_path, [(start, end)], work_dir, fast_copy=fast_copy)
                clip_path = clip_paths[0]

            output_srt = None
            count = 0
            if wants_subtitles:
                output_srt = job_dir / f'clip_{idx:03d}.srt'
                if per_clip_whisper:
                    count = transcribe_to_srt_from_words(
                        clip_path,
                        output_srt,
                        language=job.auto_caption_lang,
                        model_size=job.whisper_model,
                        pause_threshold=0.35,
                        max_words_per_line=6,
                        max_chars=40,
                    )
                    ensure_not_canceled(job)
                elif subtitle_file:
                    try:
                        count = write_trimmed_srt(subtitle_file, output_srt, start, end)
                    except Exception:
                        output_srt.write_text('', encoding='utf-8')
                        count = 0
                else:
                    output_srt.write_text('', encoding='utf-8')
                    count = 0

            if job.orientation == 'portrait':
                portrait_path = work_dir / f'clip_{idx:03d}_portrait.mp4'
                convert_to_portrait(clip_path, portrait_path)
                ensure_not_canceled(job)
                clip_path = portrait_path

            output_video = job_dir / f'clip_{idx:03d}_caption.mp4'

            if job.burn_subtitles and output_srt and count > 0:
                burn_subtitles(
                    clip_path,
                    output_srt,
                    output_video,
                    font_name=job.subtitle_font,
                    font_size=job.subtitle_size,
                )
            else:
                shutil.copyfile(clip_path, output_video)

            progress = 40 + int((idx / total) * 50) if total else 90
            update_job(job, progress=progress, message=f'Processing clip {idx}/{total}')

        update_job(job, status='done', progress=100, message='Done')
        try:
            produce_word_tokens.delay(str(job.id))
            # Burn word-level subtitles jika enabled
            if job.burn_word_level:
                burn_clips_with_word_subtitles.delay(str(job.id))
        except Exception:
            pass
        shutil.rmtree(work_dir, ignore_errors=True)
    except JobCanceledError:
        update_job(job, status='canceled', progress=100, message='Canceled by user', cancel_requested=True)
        try:
            work_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id) / 'work'
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
    except Exception as exc:
        update_job(job, status='failed', progress=100, error=str(exc), message='Failed')
        try:
            work_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id) / 'work'
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass


@shared_task
def produce_word_tokens(job_id):
    """Generate per-word timestamps from per-clip media using ASR.

    Uses transcribe_to_word_tokens which attempts stable-ts or falls back to
    faster-whisper with approximate word timing.
    """
    job = Job.objects.get(id=job_id)
    job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id)
    if not job_dir.exists():
        return 0
    produced = 0
    for clip_idx, clip_path in iter_output_clips(job_dir):
        clip_key = f'clip_{clip_idx:03d}'
        try:
            words = transcribe_to_word_tokens(
                clip_path,
                language=job.auto_caption_lang or 'id',
                model_size=job.whisper_model or 'tiny'
            )
        except Exception:
            continue

        # Round and write to JSON
        words_rounded = [
            {
                'word': w['word'],
                'start': round(float(w['start']), 3),
                'end': round(float(w['end']), 3),
                'confidence': round(float(w.get('confidence', 1.0)), 3),
            }
            for w in words
        ]
        out_path = job_dir / f'{clip_key}_words.json'
        out_path.write_text(json.dumps(words_rounded, ensure_ascii=False), encoding='utf-8')
        produced += 1
    return produced


@shared_task
def burn_clips_with_word_subtitles(job_id):
    """Burn word-level subtitles to all clips in a job.
    
    Reads clip_*.mp4 and clip_*_words.json, burns to clip_*_word_burned.mp4
    """
    job = Job.objects.get(id=job_id)
    job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id)
    if not job_dir.exists():
        return 0

    burned = 0
    for clip_idx, clip_path in iter_output_clips(job_dir):
        clip_key = f'clip_{clip_idx:03d}'
        words_json = job_dir / f'{clip_key}_words.json'
        if not words_json.exists():
            continue

        try:
            output_path = clip_path.with_name(f'{clip_path.stem}_word_burned.mp4')
            burn_subtitles_from_words(
                clip_path=str(clip_path),
                words_json_path=str(words_json),
                output_path=str(output_path),
                font_name=job.subtitle_font or 'Arial',
                font_size=job.subtitle_size or 28
            )
            burned += 1
            clip_path.unlink(missing_ok=True)
            output_path.replace(clip_path)
        except Exception as e:
            import logging
            logging.error(f"Failed to burn clip {clip_key}: {str(e)}")
            continue

    return burned
