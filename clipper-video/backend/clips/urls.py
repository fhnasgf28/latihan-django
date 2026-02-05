from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import VideoViewSet, ClipViewSet, JobCreateView, JobDetailView, JobZipView, LocalJobUploadView

router = DefaultRouter()
router.register(r'videos', VideoViewSet, basename='video')
router.register(r'clips', ClipViewSet, basename='clip')

urlpatterns = [
    path('', include(router.urls)),
    path('jobs/', JobCreateView.as_view(), name='job-create'),
    path('jobs/upload/', LocalJobUploadView.as_view(), name='job-upload'),
    path('jobs/<uuid:job_id>/', JobDetailView.as_view(), name='job-detail'),
    path('jobs/<uuid:job_id>/download-zip/', JobZipView.as_view(), name='job-zip'),
]
