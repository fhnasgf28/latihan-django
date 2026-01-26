from django.shortcuts import render
from rest_framework.respons import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .models import Note 
from .serializers import NoteSerializer
# Create your views here.

@api_view(["GET", "POST"])
def notes_list_create(request):
    if request.method == "GET":
        notes = Note.objects.order_by("-created_at")
        return Response(NoteSerializer(notes, many=True).data)

    serializers = NoteSerializer(data=request.data)
    if serializers.is_valid():
        serializers.save()
        return Response(serializers.data, status=staus.HTTP_201_CREATED)
    return Response(serializers.errors, status=status.HTTP_400_BAD_REQUEST)
    