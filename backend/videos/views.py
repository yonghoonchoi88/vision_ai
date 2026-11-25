from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Video

MAX_SIZE = 200 * 1024 * 1024

@csrf_exempt
@require_POST
def upload_video(request):
    file = request.FILES.get("file")
    if file is None:
        return JsonResponse({"detail": "file is required"}, status=400)
    if not file.name.lower().endswith(".mp4"):
        return JsonResponse({"detail": "only mp4 files are allowed"}, status=400)
    if file.size > MAX_SIZE:
        return JsonResponse({"detail": "file is too large (max 200MB)"}, status=400)
    video = Video.objects.create(file=file)
    return JsonResponse({"video_id": video.id}, status=201)