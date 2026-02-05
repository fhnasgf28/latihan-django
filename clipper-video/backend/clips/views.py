from rest_framework import viewsets, status, filters
from rest_framework.views import APIView
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.http import FileResponse, Http404
from .models import Video, Clip, Job
from .serializers import VideoSerializer, VideoListSerializer, ClipSerializer, JobCreateSerializer, JobDetailSerializer, LocalJobUploadSerializer
from django.db.models import Q
from django.conf import settings
from pathlib import Path
import zipfile
import tempfile

from .tasks import process_job


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
        serializer = JobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        job = serializer.save(status='queued', progress=0, message='Job queued', source_type='youtube')
        process_job.delay(str(job.id))
        return Response({'id': str(job.id), 'status': job.status}, status=status.HTTP_201_CREATED)


class LocalJobUploadView(APIView):
    permission_classes = [AllowAny]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
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
            orientation=serializer.validated_data.get('orientation', 'landscape'),
            max_clips=serializer.validated_data.get('max_clips', 0),
            download_sections=False,
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

        process_job.delay(str(job.id))
        return Response({'id': str(job.id), 'status': job.status}, status=status.HTTP_201_CREATED)


class JobDetailView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        serializer = JobDetailSerializer(job)
        return Response(serializer.data)


class JobZipView(APIView):
    permission_classes = [AllowAny]

    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id)
        job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(job.id)
        if not job_dir.exists():
            raise Http404('Job outputs not found')

        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.zip')
        with zipfile.ZipFile(temp_file.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for path in job_dir.iterdir():
                if path.is_file():
                    zipf.write(path, arcname=path.name)
        temp_file.seek(0)
        response = FileResponse(open(temp_file.name, 'rb'), as_attachment=True, filename=f'job_{job.id}.zip')
        return response
