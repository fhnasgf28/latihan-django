import json
import os
import shutil
import sys
import importlib.util
from pathlib import Path

from .utils import run_command, run_command_stream, escape_ffmpeg_path, format_timecode
from .reframe import compute_dominant_person_crop
from .srt_utils import render_ass_from_words
from tempfile import NamedTemporaryFile


def _get_yt_dlp_cmd():
    env_path = os.getenv('YT_DLP_PATH')
    if env_path:
        return [env_path]

    # Prefer module execution from the active Python env (e.g. pyenv virtualenv).
    if importlib.util.find_spec('yt_dlp') is not None:
        return [sys.executable, '-m', 'yt_dlp']

    binary = shutil.which('yt-dlp')
    if binary:
        return [binary]

    # Final fallback if PATH/module detection misses.
    return [sys.executable, '-m', 'yt_dlp']


def fetch_video_info(url):
    yt_dlp_cmd = _get_yt_dlp_cmd()
    try:
        # Add --no-check-certificate and --user-agent for better compatibility
        output = run_command([
            *yt_dlp_cmd,
            '-J', 
            '--no-playlist',
            '--no-check-certificate',
            '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            url,
        ])
        return json.loads(output)
    except Exception as e:
        # Try fallback without user-agent if first attempt fails
        try:
            output = run_command([
                *yt_dlp_cmd,
                '-J', 
                '--no-playlist',
                '--no-check-certificate',
                url,
            ])
            return json.loads(output)
        except Exception as e2:
            raise RuntimeError(f'Failed to fetch video info: {str(e2)}')


def probe_duration_seconds(video_path):
    output = run_command([
        'ffprobe',
        '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'json',
        str(video_path),
    ])
    data = json.loads(output)
    duration = data.get('format', {}).get('duration')
    if not duration:
        return 0
    try:
        return float(duration)
    except ValueError:
        return 0


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


def download_video(url, work_dir, selector, on_line=None):
    work_dir = Path(work_dir)
    output_template = str(work_dir / 'source.%(ext)s')
    yt_dlp_cmd = _get_yt_dlp_cmd()
    run_command_stream([
        *yt_dlp_cmd,
        '--newline',
        '--progress',
        '-f', selector,
        '--merge-output-format', 'mp4',
        '--no-playlist',
        '--no-check-certificate',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        '--embed-metadata',
        '--embed-chapters',
        '-o', output_template,
        url,
    ], on_line=on_line)
    source_path = work_dir / 'source.mp4'
    if not source_path.exists():
        matches = list(work_dir.glob('source.*'))
        if matches:
            source_path = matches[0]
    if not source_path.exists():
        raise RuntimeError('Download video gagal: file output tidak ditemukan')
    return source_path


def download_section(url, work_dir, selector, start, end, index):
    work_dir = Path(work_dir)
    output_template = str(work_dir / f'section_{index:03d}.%(ext)s')
    section = f"*{format_timecode(start)}-{format_timecode(end)}"
    yt_dlp_cmd = _get_yt_dlp_cmd()
    run_command([
        *yt_dlp_cmd,
        '--download-sections', section,
        '-f', selector,
        '--merge-output-format', 'mp4',
        '--no-playlist',
        '--no-check-certificate',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        '-o', output_template,
        url,
    ])
    section_path = work_dir / f'section_{index:03d}.mp4'
    if not section_path.exists():
        matches = list(work_dir.glob(f'section_{index:03d}.*'))
        if matches:
            section_path = matches[0]
    if not section_path.exists():
        raise RuntimeError('Download section gagal: file output tidak ditemukan')
    return section_path


def download_subtitles(url, work_dir, langs):
    work_dir = Path(work_dir)
    lang_arg = ','.join(langs)
    output_template = str(work_dir / 'subs.%(ext)s')
    yt_dlp_cmd = _get_yt_dlp_cmd()
    run_command([
        *yt_dlp_cmd,
        '--write-subs',
        '--write-auto-subs',
        '--sub-langs', lang_arg,
        '--convert-subs', 'srt',
        '--skip-download',
        '--no-playlist',
        '--no-check-certificate',
        '--user-agent', 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
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


def burn_subtitles(clip_path, srt_path, output_path, font_name='Arial', font_size=28):
    safe_font_name = (font_name or 'Arial').replace("'", '')
    safe_font_size = max(14, min(72, int(font_size or 28)))
    style = f"FontName={safe_font_name},FontSize={safe_font_size},Outline=1,Shadow=0,MarginV=28"
    subtitle_filter = f"subtitles='{escape_ffmpeg_path(srt_path)}':force_style='{style}'"
    run_command([
        'ffmpeg',
        '-y',
        '-i', str(clip_path),
        '-vf', subtitle_filter,
        '-c:a', 'copy',
        str(output_path),
    ])


def burn_subtitles_from_words(clip_path, words_json_path, output_path, font_name='Arial', font_size=28):
    """Create ASS from words JSON then burn into video using ffmpeg.

    words_json_path: path to JSON file with [{'word','start','end','speaker'?}, ...]
    """
    import json
    from pathlib import Path

    p = Path(words_json_path)
    if not p.exists():
        raise RuntimeError('Words JSON file not found')
    words = json.loads(p.read_text(encoding='utf-8'))
    ass_text = render_ass_from_words(words, font_name=font_name, font_size=font_size)
    # write to temp file
    with NamedTemporaryFile('w', suffix='.ass', delete=False, encoding='utf-8') as tmp:
        tmp.write(ass_text)
        tmp_path = tmp.name

    try:
        subtitle_filter = f"subtitles='{escape_ffmpeg_path(tmp_path)}'"
        run_command([
            'ffmpeg',
            '-y',
            '-i', str(clip_path),
            '-vf', subtitle_filter,
            '-c:a', 'copy',
            str(output_path),
        ])
    finally:
        try:
            Path(tmp_path).unlink()
        except Exception:
            pass


def convert_to_portrait(input_path, output_path):
    debug_reframe = os.getenv('REFRAME_DEBUG') == '1'
    crop = compute_dominant_person_crop(str(input_path), debug=debug_reframe)
    if crop:
        crop_x, crop_y, crop_w, crop_h = crop
        vf = f"crop={crop_w}:{crop_h}:{crop_x}:{crop_y},scale=1080:1920"
    else:
        vf = 'scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920'

    run_command([
        'ffmpeg',
        '-y',
        '-i', str(input_path),
        '-vf', vf,
        '-c:v', 'libx264',
        '-c:a', 'aac',
        '-movflags', '+faststart',
        str(output_path),
    ])
