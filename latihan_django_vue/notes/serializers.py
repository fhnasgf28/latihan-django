from rest_framework import serializers
from .models import Note

class NoteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Note
        fields = ["id", "title","body", "is_archived", "created_at", "updated_at"]

    def validate_title(self, value: str):
        v = (value or "").strip()
        if not v:
            raise serializers.ValidationError("Title cannot be empty")
        return v