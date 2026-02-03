import os
import shutil
import tempfile

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import FileResponse


def _wrap_close(old_close, cleanup):
    def _close():
        try:
            old_close()
        finally:
            cleanup()
    return _close

@api_view(["POST"])
@permission_classes([AllowAny])
def youtube_download(request):
    url = (request.data.get("url") or "").strip()
    download_type = request.data.get("type", "video") # 'video' or 'audio'
    
    if not url:
        return Response({"detail": "url is required"}, status=400)

    try:
        from yt_dlp import YoutubeDL
    except ImportError:
        return Response({"detail": "yt-dlp belum terpasang."}, status=500)

    temp_dir = tempfile.mkdtemp(prefix="yt_")
    try:
        ydl_opts = {
            "outtmpl": os.path.join(temp_dir, "%(title).200s.%(ext)s"),
            "noplaylist": True,
            "restrictfilenames": True,
            "quiet": False,
            "no_warnings": False,
            "socket_timeout": 30,
            "fragment_retries": 10,
            "retries": 5,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            },
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"],
                }
            }
        }

        if download_type == "audio":
            ydl_opts.update({
                "format": "bestaudio/best",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }],
            })
        else:
            # Video: Prioritaskan MP4 single file agar cepat dan kompatibel
            ydl_opts["format"] = "best[ext=mp4]/best"
        
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            
            # Jika postprocessor audio jalan, ekstensi file berubah jadi .mp3
            if download_type == "audio":
                base, _ = os.path.splitext(file_path)
                mp3_path = base + ".mp3"
                if os.path.exists(mp3_path):
                    file_path = mp3_path

        if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
            files = os.listdir(temp_dir)
            if files:
                # Prioritaskan file mp3 jika mode audio
                if download_type == "audio":
                    mp3_files = [f for f in files if f.endswith('.mp3')]
                    if mp3_files:
                        files = mp3_files
                
                files.sort(key=lambda x: os.path.getsize(os.path.join(temp_dir, x)), reverse=True)
                file_path = os.path.join(temp_dir, files[0])
            else:
                raise FileNotFoundError("Gagal mengunduh file atau file kosong.")

        filename = os.path.basename(file_path)
        
        content_type = "application/octet-stream"
        if filename.lower().endswith(".mp4"):
            content_type = "video/mp4"
        elif filename.lower().endswith(".webm"):
            content_type = "video/webm"
        elif filename.lower().endswith(".mp3"):
            content_type = "audio/mpeg"

        response = FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename=filename,
        )
        response["Content-Type"] = content_type
        response["Access-Control-Expose-Headers"] = "Content-Disposition"

        def _cleanup():
            shutil.rmtree(temp_dir, ignore_errors=True)

        response.close = _wrap_close(response.close, _cleanup)
        return response

    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        return Response({"detail": str(exc)}, status=400)
