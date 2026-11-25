"""
AI 추론 서버 (FastAPI) — 1단계: 뼈대

전체 흐름에서 이 서버의 위치
    [프론트(JS)] → [Django: 업로드·DB·분석요청] → ★[FastAPI: AI 추론]★
                                                       ↓
                                         { "action": "...", "confidence": 0.92 }

이 서버가 하는 일은 딱 하나:
    "동영상 파일을 받으면 → 어떤 동작인지 + 확신도를 돌려준다"

지금(1단계)은 모델 없이 '가짜 결과'를 돌려준다.
→ Django 팀이 연결 테스트를 바로 시작할 수 있게 하기 위함 (약속(계약)을 먼저, 내용은 나중에)
→ 2~4단계에서 TODO 부분을 진짜 추론 코드로 하나씩 바꿔 나간다.

실행:  uvicorn main:app --reload --port 8001
문서:  http://localhost:8001/docs   (FastAPI가 자동으로 만들어 주는 테스트 화면)
"""

import shutil
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from inference import video_to_input, rf_model

# ── 1) 앱 생성 ────────────────────────────────────────────────
app = FastAPI(title="Vision AI 추론 서버", version="0.1.0")

# 받을 수 있는 동영상 확장자 (화이트리스트 방식: 허용 목록에 있는 것만 통과)
ALLOWED_EXTS = {".mp4"}


# ── 1-1) 요청 형식 에러 처리 ───────────────────────────────────
# 에러 응답은 팀 규칙대로 {"detail": "..."} (FastAPI 기본 형식이라 HTTPException은 그대로 두면 됨)
# 단, 요청 형식 에러(예: file 없이 요청)는 FastAPI 기본값이 422라서
# 명세서의 422("사람을 인식하지 못함")와 겹친다 → 400으로 바꾼다.
# (명세서: 400 = 파일이 없거나 동영상이 아님)
@app.exception_handler(RequestValidationError)
async def validation_error_handler(request, exc):
    return JSONResponse(status_code=400, content={"detail": "file is required"})


# ── 2) 응답 모양(스키마) 정의 ─────────────────────────────────
# API 명세서의 성공 응답 { "action": "걷기", "confidence": 0.92 } 를 코드로 옮긴 것.
# response_model로 지정하면 FastAPI가 이 모양이 맞는지 검사하고 /docs에도 표시해 준다.
class PredictResponse(BaseModel):
    action: str        # 예측 동작 이름 (한글 라벨)
    confidence: float  # 확신도 0.0 ~ 1.0


# ── 3) 헬스 체크 ─────────────────────────────────────────────
# "서버 살아있어?"를 확인하는 용도. Django나 Docker가 AI 서버 상태를 볼 때 쓴다.
@app.get("/health")
def health():
    return {"status": "ok"}


# ── 4) 추론 엔드포인트 ────────────────────────────────────────
# async def 가 아니라 그냥 def 로 만든 이유:
#   나중에 들어갈 YOLO·랜덤포레스트 추론은 CPU를 오래 붙잡는 '무거운 작업'이다.
#   일반 def 로 두면 FastAPI가 별도 스레드에서 실행해 줘서,
#   추론하는 동안에도 /health 같은 다른 요청이 막히지 않는다.
@app.post("/predict", response_model=PredictResponse)
def predict(file: UploadFile = File(...)):
    # (1) 확장자 검사 → 동영상이 아니면 400
    ext = Path(file.filename or "").suffix.lower()
    if ext not in ALLOWED_EXTS:
        raise HTTPException(status_code=400, detail="invalid video file")

    # (2) 받은 파일을 임시 파일로 저장
    #     OpenCV(cv2.VideoCapture)는 '파일 경로'로 영상을 읽기 때문에 디스크에 한 번 써 둔다.
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        shutil.copyfileobj(file.file, tmp)
        video_path = Path(tmp.name)

    try:
        x = video_to_input(video_path)                 # 영상 → (1, 1140)
        if x is None:                                  # 사람이 잡힌 프레임이 10개 미만
            raise HTTPException(status_code=422, detail="no person detected")

        proba = rf_model.predict_proba(x)[0]           # 동작 6개의 확률 (rf_model.classes_ 순서)
        best = int(proba.argmax())                     # 확률이 가장 높은 칸의 위치
        return PredictResponse(action=rf_model.classes_[best], confidence=float(proba[best]))
    finally:
        # (6) 성공하든 에러가 나든 임시 파일은 반드시 지운다 (디스크가 쌓이지 않게)
        video_path.unlink(missing_ok=True)
