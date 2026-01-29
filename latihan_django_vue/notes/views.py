import os
import shutil
import tempfile

from rest_framework import viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.http import FileResponse

from .models import Note
from .serializers import NoteSerializer

class NoteViewSet(viewsets.ModelViewSet):
    queryset = Note.objects.all().order_by("-updated_at")
    serializer_class = NoteSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        archived = self.request.query_params.get("archived")
        if archived is not None:
            val = archived.lower() in ("1", "true", "yes")
            qs = qs.filter(is_archived = val)

#         search title / body
        q = (self.request.query_params.get("q") or "").strip()
        if q:
            qs = qs.filter(title__icontains=q) | qs.filter(body__icontains=q)
        return qs

    @action(detail=True, methods=["post"])
    def archive(self, request, pk=None):
        note = self.get_object()
        note.is_archived = True
        note.save(update_fields=["is_archived", "update_at"])
        return Response(self.get_serializer(note).data)

    @action(detail=True, methods=["post"])
    def unarchive(self, request, pk=None):
        note = self.get_object()
        note.is_archived = False
        note.save(update_fields=["is_archived", "update_at"])
        return Response(self.get_serializer(note).data)


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
    if not url:
        return Response({"detail": "url is required"}, status=400)

    try:
        from yt_dlp import YoutubeDL
        from yt_dlp.utils import sanitize_filename
    except ModuleNotFoundError:
        return Response(
            {"detail": "yt-dlp belum terpasang. Jalankan: pip install yt-dlp"},
            status=500,
        )

    temp_dir = tempfile.mkdtemp(prefix="yt_")
    try:
        ydl_opts = {
            "outtmpl": os.path.join(temp_dir, "%(title).200s.%(ext)s"),
            "format": "best",  # Gunakan format terbaik tanpa memfilter by extension
            "quiet": False,
            "no_warnings": False,
            "noplaylist": True,
            "restrictfilenames": True,
            "socket_timeout": 30,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            },
            "fragment_retries": 10,  # Retry fragments yang gagal
            "retries": 5,  # Retry keseluruhan
            "skip_unavailable_fragments": True,  # Skip fragment yang tidak bisa diakses
            "extractor_args": {
                "youtube": {
                    "player_client": ["web"],  # Gunakan web player
                    "player_skip": ["js"],  # Skip JavaScript player
                }
            },
            "postprocessors": [
                {
                    "key": "FFmpegVideoConvertor",
                    "preferedformat": "mp4"
                }
            ],
        }
        with YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        if not os.path.exists(file_path):
            raise FileNotFoundError("File hasil download tidak ditemukan. Coba gunakan link YouTube yang valid.")

        base_name = sanitize_filename(info.get("title") or "video", restricted=True)
        ext = info.get("ext") or "mp4"
        download_name = f"{base_name}.{ext}"

        response = FileResponse(
            open(file_path, "rb"),
            as_attachment=True,
            filename=download_name,
        )
        response["Content-Type"] = "video/mp4"

        def _cleanup():
            shutil.rmtree(temp_dir, ignore_errors=True)

        response.close = _wrap_close(response.close, _cleanup)
        return response
    except Exception as exc:
        shutil.rmtree(temp_dir, ignore_errors=True)
        error_msg = str(exc)
        if "empty" in error_msg.lower() or "fragment" in error_msg.lower():
            error_msg = "Video tidak dapat diunduh karena masalah dengan server YouTube atau fragments kosong. Ini adalah issue umum dengan YouTube saat ini. Coba: 1) Gunakan video YouTube yang berbeda, 2) Update yt-dlp: pip install --upgrade yt-dlp, 3) Install FFmpeg: apt-get install ffmpeg (Linux) atau brew install ffmpeg (Mac)"
        return Response({"detail": error_msg}, status=400)

