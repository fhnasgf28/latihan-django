from rest_framework import viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

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

    @action(detail=True, method=["post"])
    def unarchive(self, request, pk=None):
        note = self.get_object()
        note.is_archived = False
        note.save(update_fields=["is_archived", "update_at"])
        return Response(self.get_serializer(note).data)


