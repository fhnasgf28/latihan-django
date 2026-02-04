import re
import subprocess
from pathlib import Path


def run_command(cmd, cwd=None):
    result = subprocess.run(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip())
    return result.stdout


def parse_timecode(value):
    if not re.match(r'^\d{2}:\d{2}:\d{2}$', value):
        raise ValueError('Format waktu harus HH:MM:SS')
    hours, minutes, seconds = [int(part) for part in value.split(':')]
    return hours * 3600 + minutes * 60 + seconds


def format_srt_time(seconds):
    total_ms = int(round(seconds * 1000))
    hours = total_ms // 3600000
    remainder = total_ms % 3600000
    minutes = remainder // 60000
    remainder = remainder % 60000
    secs = remainder // 1000
    ms = remainder % 1000
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{ms:03d}"


def escape_ffmpeg_path(path):
    value = str(Path(path))
    value = value.replace('\\', '\\\\')
    value = value.replace(':', '\\:')
    value = value.replace("'", "\\'")
    return value
