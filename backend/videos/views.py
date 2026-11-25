from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .models import Video


@csrf_exempt
@require_POST
def upload_video(request):
    file = request.FILES.get("file")
    if file is None:
        return JsonResponse({"detail": "file is required"}, status=400)
    video = Video.objects.create(file=file)
    return JsonResponse({"video_id": video.id}, status=201)