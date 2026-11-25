import json
import os

import requests
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from django.utils import timezone
from django.views.decorators.http import require_GET

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
    #    FastAPI 서버에 연결 자체가 안 될 때(꺼짐·시간 초과)만 502
    try:
        with video.file.open("rb") as f:
            response = requests.post(
                f"{AI_SERVICE_URL}/predict",
                files={"file": (os.path.basename(video.file.name), f)},
                timeout=60,
            )
            
    except requests.RequestException:
        return JsonResponse({"detail": "AI service error"}, status=502)

    # 4. FastAPI가 에러를 보냈으면(400 동영상 아님, 422 사람 인식 실패 등)
    #    상태 코드와 detail 을 그대로 화면에 넘긴다
    if response.status_code >= 400:
        try:
            detail = response.json().get("detail", "AI service error")
        except ValueError:
            detail = "AI service error"
        return JsonResponse({"detail": detail}, status=response.status_code)

    result = response.json()

    # 5. ★ 저장하지 않고 결과만 돌려준다 ★
    #    사용자가 화면에서 [저장]을 누르면 save_analysis 로 다시 보낸다.
    return JsonResponse(
        {
            "video_id": video.id,
            "action": result["action"],
            "confidence": result["confidence"],
        },
        status=200,
    )

@csrf_exempt
@require_POST
def save_analysis(request):
    # 1. 요청 꺼내기: { "video_id": 3, "action": "걷기", "confidence": 0.92 }
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        data = {}

    video_id = data.get("video_id")
    if video_id is None:
        return JsonResponse({"detail": "video_id is required"}, status=400)
    try:
        video = Video.objects.get(id=video_id)
    except Video.DoesNotExist:
        return JsonResponse({"detail": "video not found"}, status=404)

    # 2. 값 검사 (화면이 보낸 값을 그대로 믿지 않는다)
    action = data.get("action")
    confidence = data.get("confidence")
    if not isinstance(action, str) or not (1 <= len(action) <= 50):
        return JsonResponse({"detail": "invalid action"}, status=400)
    if isinstance(confidence, bool) or not isinstance(confidence, (int, float)) \
            or not (0.0 <= confidence <= 1.0):
        return JsonResponse({"detail": "invalid confidence"}, status=400)

    # 3. 저장
    analysis = Analysis.objects.create(
        video=video,
        predicted_action=action,
        confidence=float(confidence),
    )

    # 4. 저장한 결과 돌려주기
    return JsonResponse(
        {
            "analysis_id": analysis.id,
            "video_id": video.id,
            "action": analysis.predicted_action,
            "confidence": analysis.confidence,
        },
        status=201,
    )


@require_GET                                      # GET 만 허용 (읽기 전용이라 CSRF 필요 없음)
def list_analyses(request):
    """저장된 분석 기록 목록 (최신순). FastAPI 는 거치지 않고 DB 만 읽는다."""
    # ?limit=20 처럼 개수를 받되, 너무 많이 요청하지 못하게 최대 100
    try:
        limit = min(int(request.GET.get("limit", 20)), 100)
    except ValueError:
        limit = 20

    records = (
        Analysis.objects
        .select_related("video")                  # Video 를 한 번의 쿼리로 같이 가져옴 (N+1 방지)
        .order_by("-created_at")[:limit]          # 최신순, 최대 limit 개
    )

    items = [
        {
            "analysis_id": a.id,
            "video_id": a.video_id,
            "video_name": os.path.basename(a.video.file.name),   # "videos/test.mp4" → "test.mp4"
            "action": a.predicted_action,
            "confidence": a.confidence,
            # USE_TZ=True 라 DB 에는 UTC 로 저장됨 → 한국 시간으로 바꿔서 글자로
            "created_at": timezone.localtime(a.created_at).strftime("%Y-%m-%d %H:%M:%S"),
        }
        for a in records
    ]
    return JsonResponse({"count": len(items), "items": items})