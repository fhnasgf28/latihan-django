import json
from pathlib import Path

from .utils import run_command, escape_ffmpeg_path


def fetch_video_info(url):
    output = run_command(['yt-dlp', '-J', '--no-playlist', url])
    return json.loads(output)


def get_max_height(formats):
    heights = [fmt.get('height') for fmt in formats if fmt.get('height')]
    return max(heights) if heights else 0


def has_height(formats, min_height):
    return any((fmt.get('height') or 0) >= min_height for fmt in formats)


def build_format_selector(strict_1080, min_height_fallback):
    if strict_1080:
        return 'bv*[height>=1080][ext=mp4]+ba[ext=m4a]/bv*[height>=1080]+ba/b'
    return (
        'bv*[height>=1080][ext=mp4]+ba[ext=m4a]'
        '/bv*[height>=1080]+ba'
        f'/bv*[height>={min_height_fallback}]+ba/best'
    )


def download_video(url, work_dir, selector):
    work_dir = Path(work_dir)
    output_template = str(work_dir / 'source.%(ext)s')
    run_command([
        'yt-dlp',
        '-f', selector,
        '--merge-output-format', 'mp4',
        '--no-playlist',
        '-o', output_template,
        url,
    ])
    source_path = work_dir / 'source.mp4'
    if not source_path.exists():
        matches = list(work_dir.glob('source.*'))
        if matches:
            source_path = matches[0]
    if not source_path.exists():
        raise RuntimeError('Download video gagal: file output tidak ditemukan')
    return source_path


def download_subtitles(url, work_dir, langs):
    work_dir = Path(work_dir)
    lang_arg = ','.join(langs)
    output_template = str(work_dir / 'subs.%(ext)s')
    run_command([
        'yt-dlp',
        '--write-subs',
        '--write-auto-subs',
        '--sub-langs', lang_arg,
        '--convert-subs', 'srt',
        '--skip-download',
        '--no-playlist',
        '-o', output_template,
        url,
    ])
    return list(work_dir.glob('subs*.srt'))


def pick_subtitle_file(srt_files, langs):
    if not srt_files:
        return None
    lang_map = {}
    for file in srt_files:
        parts = file.name.split('.')
        if len(parts) >= 3:
            lang = parts[-2]
            lang_map.setdefault(lang, file)
    for lang in langs:
        if lang in lang_map:
            return lang_map[lang]
        for candidate, path in lang_map.items():
            if candidate.startswith(lang):
                return path
    return srt_files[0]


def split_video(source_path, ranges, work_dir, fast_copy=True):
    clips = []
    work_dir = Path(work_dir)
    for idx, (start, end) in enumerate(ranges, start=1):
        duration = max(0, end - start)
        clip_path = work_dir / f'clip_{idx:03d}.mp4'
        if fast_copy:
            try:
                run_command([
                    'ffmpeg',
                    '-y',
                    '-ss', str(start),
                    '-i', str(source_path),
                    '-t', str(duration),
                    '-c', 'copy',
                    '-movflags', '+faststart',
                    str(clip_path),
                ])
                clips.append(clip_path)
                continue
            except Exception:
                pass
        run_command([
            'ffmpeg',
            '-y',
            '-i', str(source_path),
            '-ss', str(start),
            '-t', str(duration),
            '-c:v', 'libx264',
            '-c:a', 'aac',
            '-movflags', '+faststart',
            str(clip_path),
        ])
        clips.append(clip_path)
    return clips


def burn_subtitles(clip_path, srt_path, output_path):
    subtitle_filter = f"subtitles='{escape_ffmpeg_path(srt_path)}'"
    run_command([
        'ffmpeg',
        '-y',
        '-i', str(clip_path),
        '-vf', subtitle_filter,
        '-c:a', 'copy',
        str(output_path),
    ])
