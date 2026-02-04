import shutil
from pathlib import Path

from celery import shared_task
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

from .models import Job
from .services import (
    fetch_video_info,
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
)
from .srt_utils import write_trimmed_srt
from .utils import parse_timecode, parse_yt_dlp_progress
from .stt import extract_audio, transcribe_to_srt

MAX_DURATION_SECONDS = 2 * 60 * 60
MAX_CLIPS = 60


def update_job(job, **fields):
    for key, value in fields.items():
        setattr(job, key, value)
    job.save(update_fields=list(fields.keys()) + ['updated_at'])


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
        update_job(job, status='running', progress=5, message='Fetching video info')
        info = fetch_video_info(job.youtube_url)
        duration = info.get('duration')
        if not duration:
            raise RuntimeError('Tidak bisa membaca durasi video')
        if duration > MAX_DURATION_SECONDS:
            raise RuntimeError('Video lebih dari 2 jam. Silakan gunakan video yang lebih pendek.')

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
        if not job.download_sections:
            last_reported = {'progress': 0}

            def handle_download_line(line):
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

        update_job(job, progress=40, message='Processing clips (streaming)')

        subtitle_file = None
        per_clip_whisper = False
        wants_subtitles = job.burn_subtitles or job.auto_captions
        if wants_subtitles:
            update_job(job, progress=60, message='Fetching subtitles')
            try:
                srt_files = download_subtitles(job.youtube_url, work_dir, job.subtitle_langs or ['id', 'en'])
                subtitle_file = pick_subtitle_file(srt_files, job.subtitle_langs or ['id', 'en'])
                if not subtitle_file:
                    update_job(job, message='No YouTube subtitles, checking auto captions')
            except Exception:
                update_job(job, message='No YouTube subtitles, checking auto captions')

        if not subtitle_file and job.auto_captions:
            if job.download_sections or max_clips <= 3:
                per_clip_whisper = True
                update_job(job, message='Auto captions per clip (Whisper)')
            else:
                update_job(job, message='Auto captions (Whisper)')
                audio_path = work_dir / 'whisper_full.wav'
                extract_audio(source_path, audio_path)
                full_srt = work_dir / 'whisper_full.srt'
                transcribe_to_srt(
                    audio_path,
                    full_srt,
                    language=job.auto_caption_lang,
                    model_size=job.whisper_model,
                )
                subtitle_file = full_srt

        total = len(ranges)
        for idx, (start, end) in enumerate(ranges, start=1):
            if job.download_sections:
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
                    audio_path = work_dir / f'clip_{idx:03d}.wav'
                    extract_audio(clip_path, audio_path)
                    count = transcribe_to_srt(
                        audio_path,
                        output_srt,
                        language=job.auto_caption_lang,
                        model_size=job.whisper_model,
                    )
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
                clip_path = portrait_path

            output_video = job_dir / f'clip_{idx:03d}_caption.mp4'

            if job.burn_subtitles and output_srt and count > 0:
                burn_subtitles(clip_path, output_srt, output_video)
            else:
                shutil.copyfile(clip_path, output_video)

            progress = 40 + int((idx / total) * 50) if total else 90
            update_job(job, progress=progress, message=f'Processing clip {idx}/{total}')

        update_job(job, status='done', progress=100, message='Done')
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception as exc:
        update_job(job, status='failed', progress=100, error=str(exc), message='Failed')
        try:
            work_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id) / 'work'
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
