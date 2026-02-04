import shutil
from pathlib import Path

from celery import shared_task
from django.conf import settings

from .models import Job
from .services import (
    fetch_video_info,
    get_max_height,
    has_height,
    build_format_selector,
    download_video,
    download_subtitles,
    pick_subtitle_file,
    split_video,
    burn_subtitles,
)
from .srt_utils import write_trimmed_srt
from .utils import parse_timecode

MAX_DURATION_SECONDS = 2 * 60 * 60
MAX_CLIPS = 60


def update_job(job, **fields):
    for key, value in fields.items():
        setattr(job, key, value)
    job.save(update_fields=list(fields.keys()) + ['updated_at'])


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

        job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id)
        work_dir = job_dir / 'work'
        job_dir.mkdir(parents=True, exist_ok=True)
        work_dir.mkdir(parents=True, exist_ok=True)

        update_job(job, progress=20, message='Downloading video')
        selector = build_format_selector(job.strict_1080, job.min_height_fallback)
        source_path = download_video(job.youtube_url, work_dir, selector)

        update_job(job, progress=40, message='Splitting video')
        clip_paths = split_video(source_path, ranges, work_dir)

        update_job(job, progress=60, message='Fetching subtitles')
        subtitle_file = None
        try:
            srt_files = download_subtitles(job.youtube_url, work_dir, job.subtitle_langs or ['id', 'en'])
            subtitle_file = pick_subtitle_file(srt_files, job.subtitle_langs or ['id', 'en'])
            if not subtitle_file:
                update_job(job, message='No subtitles available, proceeding without captions')
        except Exception:
            update_job(job, message='No subtitles available, proceeding without captions')

        update_job(job, progress=70, message='Trimming subtitles')
        subtitle_counts = []
        for idx, (start, end) in enumerate(ranges, start=1):
            output_srt = job_dir / f'clip_{idx:03d}.srt'
            if subtitle_file:
                try:
                    count = write_trimmed_srt(subtitle_file, output_srt, start, end)
                except Exception:
                    output_srt.write_text('', encoding='utf-8')
                    count = 0
            else:
                output_srt.write_text('', encoding='utf-8')
                count = 0
            subtitle_counts.append(count)

        update_job(job, progress=90, message='Burning subtitles')
        for idx, clip_path in enumerate(clip_paths, start=1):
            output_srt = job_dir / f'clip_{idx:03d}.srt'
            output_video = job_dir / f'clip_{idx:03d}_caption.mp4'
            if subtitle_counts[idx - 1] > 0:
                burn_subtitles(clip_path, output_srt, output_video)
            else:
                shutil.copyfile(clip_path, output_video)

        update_job(job, status='done', progress=100, message='Done')
        shutil.rmtree(work_dir, ignore_errors=True)
    except Exception as exc:
        update_job(job, status='failed', progress=100, error=str(exc), message='Failed')
        try:
            work_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id) / 'work'
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass
