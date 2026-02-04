from rest_framework import serializers
import re

from .models import Video, Clip, Job
from django.contrib.auth.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class ClipSerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    duration = serializers.SerializerMethodField()

    class Meta:
        model = Clip
        fields = ['id', 'title', 'description', 'video', 'start_time', 'end_time', 
                  'thumbnail', 'created_by', 'created_at', 'updated_at', 'is_public', 'duration']
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']

    def get_duration(self, obj):
        return obj.end_time - obj.start_time


class VideoSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    clips = ClipSerializer(many=True, read_only=True)
    clips_count = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'video_file', 'duration', 'thumbnail',
                  'uploaded_by', 'created_at', 'updated_at', 'clips', 'clips_count']
        read_only_fields = ['id', 'created_at', 'updated_at', 'uploaded_by']

    def get_clips_count(self, obj):
        return obj.clips.count()


class VideoListSerializer(serializers.ModelSerializer):
    uploaded_by = UserSerializer(read_only=True)
    clips_count = serializers.SerializerMethodField()

    class Meta:
        model = Video
        fields = ['id', 'title', 'description', 'thumbnail', 'duration',
                  'uploaded_by', 'created_at', 'clips_count']

    def get_clips_count(self, obj):
        return obj.clips.count()


class JobCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Job
        fields = [
            'youtube_url',
            'mode',
            'interval_minutes',
            'ranges',
            'strict_1080',
            'min_height_fallback',
            'subtitle_langs',
        ]

    def validate_youtube_url(self, value):
        # Lebih fleksibel:
        # 1. Protokol http/https opsional (^(https?://)?)
        # 2. Subdomain opsional (www, m, music, dll) (([a-zA-Z0-9-]+\.)?)
        # 3. Domain youtube.com atau youtu.be
        if not re.match(r'^(https?://)?([a-zA-Z0-9-]+\.)?(youtube\.com|youtu\.be)/', value):
            raise serializers.ValidationError('URL harus dari youtube.com atau youtu.be')
        return value

    def validate(self, data):
        mode = data.get('mode')
        interval = data.get('interval_minutes')
        ranges = data.get('ranges')
        strict_1080 = data.get('strict_1080', False)
        min_height_fallback = data.get('min_height_fallback', 720)
        subtitle_langs = data.get('subtitle_langs', ['id', 'en'])

        if mode not in ['auto', 'manual']:
            raise serializers.ValidationError({'mode': 'Mode harus auto atau manual'})

        if mode == 'auto':
            # Jika interval None, kita anggap error.
            # Frontend seharusnya mengirim value default, tapi jika user mengosongkan input, bisa jadi None.
            if interval is None:
                 raise serializers.ValidationError({'interval_minutes': 'Interval wajib diisi untuk mode auto'})
            if interval < 1:
                 raise serializers.ValidationError({'interval_minutes': 'Interval minimal 1 menit'})

        else:
            if not ranges or not isinstance(ranges, list):
                raise serializers.ValidationError({'ranges': 'Ranges wajib diisi untuk mode manual'})
            if len(ranges) > 60:
                raise serializers.ValidationError({'ranges': 'Maksimum 60 range per job'})
            for item in ranges:
                if 'start' not in item or 'end' not in item:
                    raise serializers.ValidationError({'ranges': 'Setiap range butuh start dan end'})
                # Regex waktu juga sedikit dilonggarkan untuk antisipasi format lain
                if not re.match(r'^\d{1,2}:\d{2}:\d{2}(\.\d+)?$', item['start']) or not re.match(r'^\d{1,2}:\d{2}:\d{2}(\.\d+)?$', item['end']):
                    raise serializers.ValidationError({'ranges': 'Format waktu harus HH:MM:SS'})

        if not strict_1080 and min_height_fallback not in [720, 480]:
            raise serializers.ValidationError({'min_height_fallback': 'Fallback hanya 720 atau 480'})

        if not subtitle_langs:
            data['subtitle_langs'] = ['id', 'en']

        return data

    def create(self, validated_data):
        if 'subtitle_langs' not in validated_data or not validated_data['subtitle_langs']:
            validated_data['subtitle_langs'] = ['id', 'en']
        if 'min_height_fallback' not in validated_data:
            validated_data['min_height_fallback'] = 720
        return super().create(validated_data)


class JobDetailSerializer(serializers.ModelSerializer):
    results = serializers.SerializerMethodField()

    class Meta:
        model = Job
        fields = [
            'id',
            'status',
            'progress',
            'message',
            'error',
            'results',
        ]

    def get_results(self, obj):
        from django.conf import settings
        from pathlib import Path

        job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(obj.id)
        if not job_dir.exists():
            return []
        results = []
        for path in sorted(job_dir.iterdir()):
            if path.is_file() and path.name != 'work':
                results.append({
                    'filename': path.name,
                    'url': f"{settings.MEDIA_URL}jobs/{obj.id}/{path.name}",
                })
        return results
