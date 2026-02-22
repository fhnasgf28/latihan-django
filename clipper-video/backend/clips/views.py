from datetime import timedelta,timezone, datetime
from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.core.exceptions import PermissionDenied
from django.http import FileResponse, Http404
from .models import Video, Clip, Job
from .serializers import VideoSerializer, VideoListSerializer, ClipSerializer, JobCreateSerializer, JobDetailSerializer, LocalJobUploadSerializer
from django.db.models import Q
from django.conf import settings
from pathlib import Path
from celery.result import AsyncResult
import shutil
import zipfile
import tempfile

from .tasks import process_job
import json
from pathlib import Path
from django.conf import settings

ACTIVE_JOB_LIMIT = 3
ACTIVE_JOB_STATUSES = ['queued', 'running']


def _active_job_limit_response():
    active_qs = Job.objects.filter(status__in=ACTIVE_JOB_STATUSES).order_by('created_at')
    active_count = active_qs.count()
    if active_count < ACTIVE_JOB_LIMIT:
        return None
    active_job_details = [
        {
            'id': str(job.id),
            'status': job.status,
            'progress': int(job.progress or 0),
            'message': job.message,
            'created_at': job.created_at,
        }
        for job in active_qs[:ACTIVE_JOB_LIMIT]
    ]
    return Response(
        {
            'detail': f'Maksimal {ACTIVE_JOB_LIMIT} job aktif. Tunggu salah satu job selesai dulu.',
            'active_jobs': active_count,
            'max_active_jobs': ACTIVE_JOB_LIMIT,
            'active_job_details': active_job_details,
        },
        status=status.HTTP_429_TOO_MANY_REQUESTS
    )


class VideoViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            return VideoListSerializer
        return VideoSerializer

    def get_queryset(self):
        return Video.objects.all()

    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)

    @action(detail=True, methods=['get'])
    def clips(self, request, pk=None):
        """Get all clips for a specific video"""
        video = self.get_object()
        clips = video.clips.all()
        serializer = ClipSerializer(clips, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def upload(self, request):
        """Upload a new video"""
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(uploaded_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClipViewSet(viewsets.ModelViewSet):
    permission_classes = [AllowAny]
    serializer_class = ClipSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'start_time']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = Clip.objects.all()
        video_id = self.request.query_params.get('video_id')
        if video_id:
            queryset = queryset.filter(video_id=video_id)
        return queryset

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['post'])
    def toggle_public(self, request, pk=None):
        """Toggle public status of a clip"""
        clip = self.get_object()
        clip.is_public = not clip.is_public
        clip.save()
        serializer = self.get_serializer(clip)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_clips(self, request):
        """Get clips created by current user"""
        clips = Clip.objects.filter(created_by=request.user)
        serializer = self.get_serializer(clips, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def public_clips(self, request):
        """Get all public clips"""
        clips = Clip.objects.filter(is_public=True)
        serializer = self.get_serializer(clips, many=True)
        return Response(serializer.data)


class JobCreateView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        limit_response = _active_job_limit_response()
        if limit_response:
            return limit_response
        serializer = JobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save(status='queued', progress=0, message='Job queued', source_type='youtube')
        task = process_job.delay(str(job.id))
        job.celery_task_id = task.id
        job.save(update_fields=['celery_task_id', 'updated_at'])
        return Response({
            'id': str(job.id),
            'status': job.status,
            'progress': job.progress,
            'message': job.message,
            'created_at': job.created_at,
            'access_token': job.access_token,
        }, status=status.HTTP_201_CREATED)


class LocalJobUploadView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        limit_response = _active_job_limit_response()
        if limit_response:
            return limit_response
        serializer = LocalJobUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        upload = serializer.validated_data['video_file']
        job = Job.objects.create(
            source_type='local',
            youtube_url='',
            local_video_name=getattr(upload, 'name', ''),
            mode=serializer.validated_data['mode'],
            interval_minutes=serializer.validated_data.get('interval_minutes'),
            ranges=serializer.validated_data.get('ranges'),
            strict_1080=serializer.validated_data.get('strict_1080', False),
            min_height_fallback=serializer.validated_data.get('min_height_fallback', 720),
            subtitle_langs=serializer.validated_data.get('subtitle_langs') or ['id', 'en'],
            burn_subtitles=serializer.validated_data.get('burn_subtitles', False),
            auto_captions=serializer.validated_data.get('auto_captions', False),
            auto_caption_lang=serializer.validated_data.get('auto_caption_lang', 'id'),
            whisper_model=serializer.validated_data.get('whisper_model', 'tiny'),
            subtitle_font=serializer.validated_data.get('subtitle_font', 'Arial'),
            subtitle_size=serializer.validated_data.get('subtitle_size', 14),
            orientation=serializer.validated_data.get('orientation', 'landscape'),
            max_clips=serializer.validated_data.get('max_clips', 0),
            download_sections=False,
            burn_word_level=serializer.validated_data.get('burn_word_level', False),
            status='queued',
            progress=0,
            message='Job queued',
        )

        job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id)
        work_dir = job_dir / 'work'
        work_dir.mkdir(parents=True, exist_ok=True)
        suffix = Path(upload.name).suffix or '.mp4'
        dest = work_dir / f'local_source{suffix}'
        with open(dest, 'wb') as out:
            for chunk in upload.chunks():
                out.write(chunk)

        # Store relative to MEDIA_ROOT so it works cross-platform.
        job.local_video_path = str(dest.relative_to(settings.MEDIA_ROOT))
        job.save(update_fields=['local_video_path', 'updated_at'])

        task = process_job.delay(str(job.id))
        job.celery_task_id = task.id
        job.save(update_fields=['celery_task_id', 'updated_at'])
        return Response({
            'id': str(job.id),
            'status': job.status,
            'progress': job.progress,
            'message': job.message,
            'created_at': job.created_at,
            'access_token': job.access_token,
        }, status=status.HTTP_201_CREATED)


class JobDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        serializer = JobDetailSerializer(job)
        return Response(serializer.data)

class JobCancelView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        token = (
            request.data.get('token')
            or request.GET.get('token')
            or request.headers.get('X-Job-Token')
        )
        if not token or token != job.access_token:
            raise PermissionDenied('Invalid token')

        if job.status in ['done', 'failed', 'canceled']:
            serializer = JobDetailSerializer(job)
            return Response(serializer.data)

        job.status = 'canceled'
        job.progress = 100
        job.message = 'Canceled by user'
        job.cancel_requested = True
        job.save(update_fields=['status', 'progress', 'message', 'cancel_requested', 'updated_at'])

        if job.celery_task_id:
            try:
                AsyncResult(job.celery_task_id).revoke(terminate=True, signal='SIGTERM')
            except Exception:
                pass

        job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id)
        shutil.rmtree(job_dir, ignore_errors=True)

        serializer = JobDetailSerializer(job)
        return Response(serializer.data)


class JobZipView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id)
        if not job_dir.exists():
            raise Http404('Job outputs not found')

        zip_path = job_dir / f'job_{job.id}.zip'
        source_files = [path for path in job_dir.iterdir() if path.is_file() and path.name != zip_path.name]
        latest_source_mtime = max((path.stat().st_mtime for path in source_files), default=0)
        zip_is_stale = (not zip_path.exists()) or (zip_path.stat().st_mtime < latest_source_mtime)

        if zip_is_stale:
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
            temp_zip_path = Path(temp_file.name)
            temp_file.close()
            try:
                with zipfile.ZipFile(temp_zip_path, 'w') as zipf:
                    for path in source_files:
                        # Video/audio sudah terkompres, jadi simpan tanpa kompresi ulang agar respons cepat.
                        suffix = path.suffix.lower()
                        compression = zipfile.ZIP_STORED if suffix in {'.mp4', '.mov', '.m4a', '.webm', '.mkv'} else zipfile.ZIP_DEFLATED
                        zipf.write(path, arcname=path.name, compress_type=compression)
                temp_zip_path.replace(zip_path)
            finally:
                if temp_zip_path.exists():
                    temp_zip_path.unlink(missing_ok=True)

        response = FileResponse(open(zip_path, 'rb'), as_attachment=True, filename=f'job_{job.id}.zip')
        return response

class JobViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        cutoff = timezone.now() - timedelta(hours=24)
        return Job.objects.filter(created_at__gte=cutoff)
    
    def retrieve(self, request, pk=None):
        job = self.get_object()
        token = request.GET.get('token') or request.headers.get('X-Job-Token')
        if not token or token != job.access_token:
            raise PermissionDenied('Invalid token')
        serializer = self.get_serializer(job)
        return Response(serializer.data)


class SubsWordsView(APIView):
    """Return per-word tokens JSON for a job or a specific clip.

    Paths:
      - /api/subs/<job_id>/words.json  -> returns {clip_idx: [words,...], ...}
      - /api/subs/<job_id>/<clip_idx>/words.json -> returns [words,...]
    """
    permission_classes = [AllowAny]

    def get(self, request, job_id, clip_idx=None):
        job = get_object_or_404(Job, id=job_id)
        token = request.GET.get('token') or request.headers.get('X-Job-Token')
        if not token or token != job.access_token:
            raise PermissionDenied('Invalid token')

        job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id)
        if not job_dir.exists():
            return Response({}, status=status.HTTP_404_NOT_FOUND)

        if clip_idx is not None:
            fpath = job_dir / f'clip_{int(clip_idx):03d}_words.json'
            if not fpath.exists():
                return Response([], status=status.HTTP_200_OK)
            data = json.loads(fpath.read_text(encoding='utf-8'))
            return Response(data)

        # return mapping of clip idx -> words list
        out = {}
        for path in sorted(job_dir.glob('clip_*_words.json')):
            # filename like clip_001_words.json
            name = path.name
            try:
                idx = int(name.split('_')[1])
            except Exception:
                continue
            out[idx] = json.loads(path.read_text(encoding='utf-8'))
        return Response(out)
