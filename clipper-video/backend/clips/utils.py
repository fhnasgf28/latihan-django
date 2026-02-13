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


def run_command_stream(cmd, on_line=None, cwd=None):
    process = subprocess.Popen(
        cmd,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    output_lines = []
    callback_error = None
    try:
        if process.stdout:
            for line in process.stdout:
                output_lines.append(line)
                if on_line:
                    on_line(line)
    except Exception as exc:
        callback_error = exc
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            process.wait()
    return_code = process.wait()
    if callback_error:
        raise callback_error
    if return_code != 0:
        tail = ''.join(output_lines[-20:]).strip()
        raise RuntimeError(tail or 'Command failed')
    return ''.join(output_lines)


def parse_timecode(value):
    if not re.match(r'^\d{2}:\d{2}:\d{2}$', value):
        raise ValueError('Format waktu harus HH:MM:SS')
    hours, minutes, seconds = [int(part) for part in value.split(':')]
    return hours * 3600 + minutes * 60 + seconds


def format_timecode(seconds):
    total = int(seconds)
    hours = total // 3600
    remainder = total % 3600
    minutes = remainder // 60
    secs = remainder % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"


def parse_yt_dlp_progress(line):
    match = re.search(r'\\[download\\]\\s+(\\d+(?:\\.\\d+)?)%', line)
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


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
