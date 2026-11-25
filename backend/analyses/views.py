import json
import os

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from videos.models import Video

from .models import Analysis

# FastAPI 주소: 내 컴퓨터에서는 기본값(localhost:8001)을 쓰고,
# Docker 등 다른 환경에서는 AI_SERVICE_URL 환경변수로 바꿔서 쓴다.
AI_SERVICE_URL = os.environ.get("AI_SERVICE_URL", "http://localhost:8001")


@csrf_exempt
@require_POST
def create_analysis(request):
    # 1. 요청에서 video_id 꺼내기
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    video_id = data.get("video_id")
    if video_id is None:
        return JsonResponse({"detail": "video_id is required"}, status=400)

    # 2. Video 테이블에서 영상 찾기
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return JsonResponse({"detail": "video not found"}, status=404)

    # 3. 영상 파일을 FastAPI /predict 로 보내기
    try:
        with video.file.open("rb") as f:
            response = requests.post(
                f"{AI_SERVICE_URL}/predict",
                files={"file": (os.path.basename(video.file.name), f)},
                timeout=60,
            )
        response.raise_for_status()
        result = response.json()
    except requests.RequestException:
        return JsonResponse({"detail": "AI service error"}, status=502)

    # 4. 결과를 Analysis 테이블에 저장
    analysis = Analysis.objects.create(
        video=video,
        predicted_action=result["action"],
        confidence=result["confidence"],
    )

    # 5. 저장한 결과 돌려주기
    return JsonResponse(
        {
            "analysis_id": analysis.id,
            "video_id": video.id,
            "action": analysis.predicted_action,
            "confidence": analysis.confidence,
        },
        status=201,
    )