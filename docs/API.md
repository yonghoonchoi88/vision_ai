# API 명세

> 마지막 수정: 2026-11-25 · 검사 기록 표 추가 + 분석 결과 자동 저장으로 변경

## 전체 흐름

```
[브라우저 JS]
   │ ① POST /api/videos/            영상 업로드 → video_id
   │ ② POST /api/analyses/          분석 요청 → 결과 + 자동 저장
   │ ③ GET  /api/analyses/history/  검사 기록 조회 → 표
   ▼
[Django :8000] ──(②일 때만)──▶ [FastAPI :8001] POST /predict
   │
   ▼
[SQLite] Video, Analysis
```

- 브라우저는 **Django(8000)에만** 요청합니다. FastAPI는 Django가 내부에서만 부릅니다.
- ③ 검사 기록 조회는 FastAPI를 거치지 않고 Django가 DB에서 바로 읽습니다.

## 한눈에 보기

| # | 메서드 | URL | 하는 일 | 성공 |
|---|---|---|---|---|
| ① | POST | `/api/videos/` | mp4 업로드, Video 저장 | 201 |
| ② | POST | `/api/analyses/` | FastAPI 추론 → **Analysis 자동 저장** | 201 |
| ③ | GET | `/api/analyses/history/` | 저장된 검사 기록 목록 | 200 |
| - | POST | `/predict` (FastAPI) | 영상 → 동작 추론 (Django 전용) | 200 |

---

## ① 영상 업로드

`POST /api/videos/`

**요청** `multipart/form-data`

| 필드 | 타입 | 필수 | 설명 |
|---|---|---|---|
| `file` | 파일 | ✅ | `.mp4`, 최대 200MB |

**응답 201**

```json
{ "video_id": 3 }
```

**에러**

| 코드 | 언제 |
|---|---|
| 400 | 파일 없음, mp4가 아님, 200MB 초과 |
| 405 | POST가 아닌 요청 |

**예시**

```bash
curl -X POST http://localhost:8000/api/videos/ -F "file=@sample.mp4"
```

---

## ② 분석 요청 (+ 자동 저장)

`POST /api/analyses/`

Django가 업로드된 영상을 FastAPI `/predict`로 보내고, 받은 결과를 **바로 Analysis 테이블에 저장**한 뒤 돌려줍니다.
브라우저가 결과를 다시 보내 저장하는 단계는 없습니다(결과 조작 방지).

**요청** `application/json`

```json
{ "video_id": 3 }
```

**응답 201**

```json
{
  "analysis_id": 6,
  "video_id": 3,
  "action": "wave",
  "confidence": 0.6512
}
```

| 필드 | 설명 |
|---|---|
| `analysis_id` | 저장된 검사 기록 번호 |
| `action` | 예측 동작 이름 |
| `confidence` | 확신도 0.0 ~ 1.0 (화면에는 % 로 표시) |

**에러** (에러가 나면 **저장하지 않습니다**)

| 코드 | 언제 | `detail` |
|---|---|---|
| 400 | `video_id` 없음 | `video_id is required` |
| 404 | 없는 `video_id` | `video not found` |
| 400 / 422 | FastAPI가 거절 (동영상 아님, 사람 인식 실패 등) | FastAPI의 `detail` 그대로 |
| 502 | FastAPI 서버 꺼짐·연결 실패·60초 초과 | `AI service error` |

**예시**

```bash
curl -X POST http://localhost:8000/api/analyses/ \
     -H "Content-Type: application/json" \
     -d '{"video_id": 3}'
```

---

## ③ 검사 기록 조회

`GET /api/analyses/history/`

**쿼리**

| 이름 | 기본값 | 설명 |
|---|---|---|
| `limit` | 20 | 가져올 개수, 최대 100. 숫자가 아니면 20 |

**응답 200** (최신순)

```json
{
  "count": 2,
  "items": [
    {
      "analysis_id": 6,
      "video_id": 3,
      "video_name": "sample.mp4",
      "action": "wave",
      "confidence": 0.6512,
      "created_at": "2026-11-25 19:24:10"
    }
  ]
}
```

- `created_at`은 한국 시간(`Asia/Seoul`), `YYYY-MM-DD HH:MM:SS`
- 기록이 없으면 `{"count": 0, "items": []}`

**예시**

```bash
curl "http://localhost:8000/api/analyses/history/?limit=5"
```

---

## (내부) FastAPI 추론

`POST http://localhost:8001/predict` · **Django만 호출합니다. 브라우저에서 부르지 마세요.**

**요청** `multipart/form-data` · `file`: 영상 파일

**응답 200**

```json
{ "action": "wave", "confidence": 0.6512 }
```

**파이프라인**: YOLO11n-pose → 프레임당 특징 38개 → 30프레임 시퀀스 → (1, 1140) → Random Forest

---

## 변경 이력

| 날짜 | 변경 |
|---|---|
| 2026-11-25 | `POST /api/analyses/` 가 다시 **자동 저장 + 201 + analysis_id** 반환 |
| 2026-11-25 | `POST /api/analyses/save/` **삭제** (클라이언트가 보낸 결과를 저장하던 경로) |
| 2026-11-25 | `GET /api/analyses/history/` 추가 |