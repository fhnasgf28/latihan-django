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
            'source_type',
            'youtube_url',
            'mode',
            'interval_minutes',
            'ranges',
            'strict_1080',
            'min_height_fallback',
            'subtitle_langs',
            'burn_subtitles',
            'generate_srt',
            'auto_captions',
            'auto_caption_lang',
            'whisper_model',
            'subtitle_font',
            'subtitle_size',
            'burn_word_level',
            'orientation',
            'max_clips',
            'download_sections',
        ]

    def validate_youtube_url(self, value):
        if not value:
            return value
        # Lebih fleksibel:
        # 1. Protokol http/https opsional (^(https?://)?)
        # 2. Subdomain opsional (www, m, music, dll) (([a-zA-Z0-9-]+\.)?)
        # 3. Domain youtube.com atau youtu.be
        if not re.match(r'^(https?://)?([a-zA-Z0-9-]+\.)?(youtube\.com|youtu\.be)/', value):
            raise serializers.ValidationError('URL harus dari youtube.com atau youtu.be')
        return value

    def validate(self, data):
        source_type = data.get('source_type', 'youtube')
        mode = data.get('mode')
        interval = data.get('interval_minutes')
        ranges = data.get('ranges')
        strict_1080 = data.get('strict_1080', False)
        min_height_fallback = data.get('min_height_fallback', 720)
        subtitle_langs = data.get('subtitle_langs', ['id', 'en'])
        burn_subtitles = data.get('burn_subtitles', False)
        generate_srt = data.get('generate_srt', False)
        auto_captions = data.get('auto_captions', False)
        auto_caption_lang = data.get('auto_caption_lang', 'id')
        whisper_model = data.get('whisper_model', 'small')
        subtitle_font = (data.get('subtitle_font') or 'Arial').strip()
        subtitle_size = data.get('subtitle_size', 14)
        orientation = data.get('orientation', 'landscape')
        max_clips = data.get('max_clips', 0)
        download_sections = data.get('download_sections', False)

        if source_type not in ['youtube', 'local']:
            raise serializers.ValidationError({'source_type': 'source_type harus youtube atau local'})

        if source_type == 'local':
            raise serializers.ValidationError({'source_type': 'Untuk source local, gunakan endpoint /api/jobs/upload/ (multipart).'})

        if source_type == 'youtube' and not data.get('youtube_url'):
            raise serializers.ValidationError({'youtube_url': 'youtube_url wajib diisi untuk source youtube'})

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

        if max_clips is not None:
            if max_clips < 0:
                raise serializers.ValidationError({'max_clips': 'max_clips tidak boleh negatif'})
            if max_clips > 60:
                raise serializers.ValidationError({'max_clips': 'max_clips maksimal 10'})

        if download_sections and burn_subtitles:
            # download-sections + burn subtitles bisa lebih lambat untuk banyak clip
            pass

        if (burn_subtitles or auto_captions or generate_srt) and not subtitle_langs:
            data['subtitle_langs'] = ['id', 'en']

        if auto_captions and auto_caption_lang not in ['id', 'en']:
            raise serializers.ValidationError({'auto_caption_lang': 'auto_caption_lang harus id atau en'})

        if whisper_model not in ['tiny', 'base', 'small', 'medium']:
            raise serializers.ValidationError({'whisper_model': 'whisper_model harus tiny/base/small/medium'})

        if len(subtitle_font) < 1 or len(subtitle_font) > 100:
            raise serializers.ValidationError({'subtitle_font': 'subtitle_font harus 1-100 karakter'})

        if subtitle_size in [None, '']:
            subtitle_size = 28
        try:
            subtitle_size = int(subtitle_size)
        except (TypeError, ValueError):
            raise serializers.ValidationError({'subtitle_size': 'subtitle_size harus angka'})

        if subtitle_size < 14 or subtitle_size > 72:
            raise serializers.ValidationError({'subtitle_size': 'subtitle_size harus antara 14 sampai 72'})

        if orientation not in ['landscape', 'portrait']:
            raise serializers.ValidationError({'orientation': 'orientation harus landscape atau portrait'})

        data['subtitle_font'] = subtitle_font
        data['subtitle_size'] = subtitle_size
        return data

    def create(self, validated_data):
        if validated_data.get('burn_subtitles') or validated_data.get('auto_captions') or validated_data.get('generate_srt'):
            if 'subtitle_langs' not in validated_data or not validated_data['subtitle_langs']:
                validated_data['subtitle_langs'] = ['id', 'en']
        if 'min_height_fallback' not in validated_data:
            validated_data['min_height_fallback'] = 720
        if 'max_clips' not in validated_data:
            validated_data['max_clips'] = 0
        if 'download_sections' not in validated_data:
            validated_data['download_sections'] = False
        if 'auto_captions' not in validated_data:
            validated_data['auto_captions'] = False
        if 'generate_srt' not in validated_data:
            validated_data['generate_srt'] = False
        if 'auto_caption_lang' not in validated_data:
            validated_data['auto_caption_lang'] = 'id'
        if 'whisper_model' not in validated_data:
            validated_data['whisper_model'] = 'small'
        if 'subtitle_font' not in validated_data:
            validated_data['subtitle_font'] = 'Arial'
        if 'subtitle_size' not in validated_data:
            validated_data['subtitle_size'] = 28
        if 'orientation' not in validated_data:
            validated_data['orientation'] = 'landscape'
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
            'cancel_requested',
            'created_at',
            'results',
        ]

    def get_results(self, obj):
        from django.conf import settings
        from pathlib import Path
        import re

        job_dir = Path(settings.MEDIA_ROOT) / 'jobs' / str(obj.id)
        if not job_dir.exists():
            return []
        results = []
        max_clips = obj.max_clips or 0
        for path in sorted(job_dir.iterdir()):
            if path.is_file() and path.name != 'work':
                if max_clips > 0:
                    match = re.match(r'^clip_(\d{3})', path.name)
                    if match and int(match.group(1)) > max_clips:
                        continue
                results.append({
                    'filename': path.name,
                    'url': f"{settings.MEDIA_URL}jobs/{obj.id}/{path.name}",
                })
        return results


class LocalJobUploadSerializer(serializers.Serializer):
    video_file = serializers.FileField()
    mode = serializers.ChoiceField(choices=['auto', 'manual'])
    interval_minutes = serializers.IntegerField(required=False, min_value=1)
    ranges = serializers.JSONField(required=False)

    strict_1080 = serializers.BooleanField(required=False, default=False)
    min_height_fallback = serializers.IntegerField(required=False, default=720)

    subtitle_langs = serializers.JSONField(required=False, default=list)
    burn_subtitles = serializers.BooleanField(required=False, default=False)
    generate_srt = serializers.BooleanField(required=False, default=False)

    auto_captions = serializers.BooleanField(required=False, default=False)
    auto_caption_lang = serializers.ChoiceField(choices=['id', 'en'], required=False, default='id')
    whisper_model = serializers.ChoiceField(choices=['tiny', 'base', 'small', 'medium'], required=False, default='tiny')
    subtitle_font = serializers.CharField(required=False, default='Arial', max_length=100)
    subtitle_size = serializers.IntegerField(required=False, default=28, min_value=14, max_value=72)
    burn_word_level = serializers.BooleanField(required=False, default=False)

    orientation = serializers.ChoiceField(choices=['landscape', 'portrait'], required=False, default='landscape')
    max_clips = serializers.IntegerField(required=False, default=0, min_value=0, max_value=60)

    def validate(self, data):
        # DRF FormParser may pass JSON fields as strings; normalize here.
        if isinstance(data.get('ranges'), str):
            import json
            try:
                data['ranges'] = json.loads(data['ranges'])
            except Exception:
                raise serializers.ValidationError({'ranges': 'ranges harus JSON array'})
        if isinstance(data.get('subtitle_langs'), str):
            import json
            try:
                data['subtitle_langs'] = json.loads(data['subtitle_langs'])
            except Exception:
                data['subtitle_langs'] = []
        if data['mode'] == 'auto':
            if data.get('interval_minutes') is None:
                raise serializers.ValidationError({'interval_minutes': 'Interval wajib diisi untuk mode auto'})
        else:
            ranges = data.get('ranges')
            if not ranges or not isinstance(ranges, list):
                raise serializers.ValidationError({'ranges': 'Ranges wajib diisi untuk mode manual'})
        return data
